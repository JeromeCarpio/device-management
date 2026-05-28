from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'techroom_secret_key_2024_change_in_production'

DATABASE = 'database.db'

# ─────────────────────────────────────────────
#  Database Helpers
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    with get_db() as conn:
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
    print("Database initialized.")


# ─────────────────────────────────────────────
#  Auth Decorators
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
#  Auth Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        role     = request.form.get('role', 'user')

        errors = []
        if not username:
            errors.append('Username is required.')
        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not password:
            errors.append('Password is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if role not in ('admin', 'user'):
            role = 'user'

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html')

        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Username already taken.', 'danger')
            db.close()
            return render_template('register.html')

        hashed = generate_password_hash(password)
        db.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                   (username, hashed, role))
        db.commit()
        db.close()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()

    total_incoming = db.execute("SELECT COUNT(*) FROM devices WHERE status='incoming'").fetchone()[0]
    total_outgoing = db.execute("SELECT COUNT(*) FROM devices WHERE status='outgoing'").fetchone()[0]
    total_devices  = db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]

    recent = db.execute(
        "SELECT * FROM devices ORDER BY date DESC, id DESC LIMIT 10"
    ).fetchall()

    departments = db.execute(
        "SELECT DISTINCT department FROM devices WHERE department IS NOT NULL AND department != ''"
    ).fetchall()

    db.close()

    return render_template('dashboard.html',
                           total_incoming=total_incoming,
                           total_outgoing=total_outgoing,
                           total_devices=total_devices,
                           recent=recent,
                           departments=[d['department'] for d in departments])


# ─────────────────────────────────────────────
#  Device CRUD
# ─────────────────────────────────────────────

@app.route('/devices')
@login_required
def devices():
    db = get_db()

    search     = request.args.get('search', '').strip()
    department = request.args.get('department', '')
    status     = request.args.get('status', '')
    date_from  = request.args.get('date_from', '')
    date_to    = request.args.get('date_to', '')
    page       = int(request.args.get('page', 1))
    per_page   = 10

    query  = "SELECT * FROM devices WHERE 1=1"
    params = []

    if search:
        query += " AND (device_type LIKE ? OR brand_name LIKE ? OR serial_number LIKE ? OR department LIKE ? OR remarks LIKE ?)"
        term = f'%{search}%'
        params.extend([term, term, term, term, term])
    if department:
        query += " AND department = ?"
        params.append(department)
    if status:
        query += " AND status = ?"
        params.append(status)
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)

    total_count = db.execute(query.replace("SELECT *", "SELECT COUNT(*)"), params).fetchone()[0]
    query += " ORDER BY date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    device_list = db.execute(query, params).fetchall()
    departments = db.execute(
        "SELECT DISTINCT department FROM devices WHERE department IS NOT NULL AND department != ''"
    ).fetchall()
    db.close()

    total_pages = (total_count + per_page - 1) // per_page

    return render_template('devices.html',
                           devices=device_list,
                           departments=[d['department'] for d in departments],
                           total_count=total_count,
                           page=page,
                           total_pages=total_pages,
                           search=search,
                           department=department,
                           status=status,
                           date_from=date_from,
                           date_to=date_to)


@app.route('/devices/add', methods=['GET', 'POST'])
@login_required
def add_device():
    if session.get('role') == 'admin':
        flash('Admins cannot add records. Only users can add devices.', 'danger')
        return redirect(url_for('devices'))
    if request.method == 'POST':
        device_type   = request.form.get('device_type', '').strip()
        brand_name    = request.form.get('brand_name', '').strip()
        serial_number = request.form.get('serial_number', '').strip()
        department    = request.form.get('department', '').strip()
        status        = request.form.get('status', 'incoming')
        date          = request.form.get('date', datetime.today().strftime('%Y-%m-%d'))
        remarks       = request.form.get('remarks', '').strip()

        errors = []
        if not device_type:
            errors.append('Device type is required.')
        if not brand_name:
            errors.append('Brand name is required.')
        if not serial_number:
            errors.append('Serial number is required.')
        if not department:
            errors.append('Department is required.')
        if status not in ('incoming', 'outgoing'):
            errors.append('Invalid status.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('add_device.html')

        db = get_db()
        db.execute(
            "INSERT INTO devices (device_type, brand_name, serial_number, department, status, date, remarks) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (device_type, brand_name, serial_number, department, status, date, remarks)
        )
        db.commit()
        db.close()
        flash('Device record added successfully!', 'success')
        return redirect(url_for('devices'))

    return render_template('add_device.html')


@app.route('/devices/edit/<int:device_id>', methods=['GET', 'POST'])
@admin_required
def edit_device(device_id):
    db = get_db()
    device = db.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()
    if not device:
        db.close()
        flash('Device not found.', 'danger')
        return redirect(url_for('devices'))

    if request.method == 'POST':
        device_type   = request.form.get('device_type', '').strip()
        brand_name    = request.form.get('brand_name', '').strip()
        serial_number = request.form.get('serial_number', '').strip()
        department    = request.form.get('department', '').strip()
        status        = request.form.get('status', 'incoming')
        date          = request.form.get('date', '')
        remarks       = request.form.get('remarks', '').strip()

        errors = []
        if not device_type:
            errors.append('Device type is required.')
        if not brand_name:
            errors.append('Brand name is required.')
        if not serial_number:
            errors.append('Serial number is required.')
        if not department:
            errors.append('Department is required.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            db.close()
            return render_template('edit_device.html', device=device)

        db.execute(
            "UPDATE devices SET device_type=?, brand_name=?, serial_number=?, department=?, status=?, date=?, remarks=? WHERE id=?",
            (device_type, brand_name, serial_number, department, status, date, remarks, device_id)
        )
        db.commit()
        db.close()
        flash('Device record updated successfully!', 'success')
        return redirect(url_for('devices'))

    db.close()
    return render_template('edit_device.html', device=device)


@app.route('/devices/delete/<int:device_id>', methods=['POST'])
@admin_required
def delete_device(device_id):
    db = get_db()
    device = db.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()
    if not device:
        db.close()
        flash('Device not found.', 'danger')
        return redirect(url_for('devices'))

    db.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    db.commit()
    db.close()
    flash('Device record deleted.', 'success')
    return redirect(url_for('devices'))


# ─────────────────────────────────────────────
#  API – dashboard chart data
# ─────────────────────────────────────────────

@app.route('/api/stats')
@login_required
def api_stats():
    db = get_db()
    rows = db.execute(
        "SELECT date, status, COUNT(*) as count FROM devices GROUP BY date, status ORDER BY date DESC LIMIT 30"
    ).fetchall()
    dept_rows = db.execute(
        "SELECT department, COUNT(*) as count FROM devices GROUP BY department ORDER BY count DESC LIMIT 8"
    ).fetchall()
    db.close()
    return jsonify({
        'timeline': [dict(r) for r in rows],
        'departments': [dict(r) for r in dept_rows]
    })


@app.route('/users')
@admin_required
def manage_users():
    db = get_db()
    users = db.execute('SELECT id, username, role, created_at FROM users').fetchall()
    db.close()
    return render_template('users.html', users=users)


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    db.close()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        flash('User not found.', 'danger')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        username    = request.form.get('username', '').strip()
        role        = request.form.get('role', 'user')
        new_password = request.form.get('new_password', '').strip()
        confirm      = request.form.get('confirm_password', '').strip()

        errors = []
        if not username:
            errors.append('Username is required.')
        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if new_password and len(new_password) < 6:
            errors.append('Password must be at least 6 characters.')
        if new_password and new_password != confirm:
            errors.append('Passwords do not match.')

        # Check if username taken by another user
        existing = db.execute(
            'SELECT id FROM users WHERE username = ? AND id != ?',
            (username, user_id)
        ).fetchone()
        if existing:
            errors.append('Username already taken.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            db.close()
            return render_template('edit_user.html', user=user)

        if new_password:
            hashed = generate_password_hash(new_password)
            db.execute(
                'UPDATE users SET username = ?, role = ?, password = ? WHERE id = ?',
                (username, role, hashed, user_id)
            )
        else:
            db.execute(
                'UPDATE users SET username = ?, role = ? WHERE id = ?',
                (username, role, user_id)
            )

        db.commit()
        db.close()
        flash('User updated successfully!', 'success')
        return redirect(url_for('manage_users'))

    db.close()
    return render_template('edit_user.html', user=user)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)