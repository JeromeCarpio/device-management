CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    NOT NULL UNIQUE,
    password TEXT    NOT NULL,
    role     TEXT    NOT NULL DEFAULT 'user' CHECK(role IN ('admin','user')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS devices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type   TEXT NOT NULL,
    brand_name    TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    department    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'incoming' CHECK(status IN ('incoming','outgoing')),
    date          TEXT NOT NULL,
    remarks       TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO users (username, password, role)
VALUES ('admin', 'pbkdf2:sha256:260000$rQkHpkP6YH7eFJjT$c5d8e6b3a2f1d4c9e8b7a6d5c4b3a2f1d4c9e8b7a6d5c4b3a2f1d4c9e8b7a600', 'admin');