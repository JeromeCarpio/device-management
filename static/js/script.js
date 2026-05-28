/* ═══════════════════════════════════════════════════════
   TechRoom Device Manager – script.js
   ═══════════════════════════════════════════════════════ */

'use strict';

// ── Theme ────────────────────────────────────────────────
const THEME_KEY = 'techroom_theme';

function getTheme() {
  return localStorage.getItem(THEME_KEY) || 'dark';
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = theme === 'dark' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
  }
  localStorage.setItem(THEME_KEY, theme);
}

function toggleTheme() {
  const current = getTheme();
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

// ── Sidebar ──────────────────────────────────────────────
function initSidebar() {
  const sidebar  = document.getElementById('sidebar');
  const toggle   = document.getElementById('sidebarToggle');
  const overlay  = document.getElementById('sidebarOverlay');

  if (!sidebar || !toggle) return;

  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', () => {
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
  });

  overlay.addEventListener('click', closeSidebar);

  // Close on ESC
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) closeSidebar();
  });
}

// ── Delete Modal ─────────────────────────────────────────
function openDeleteModal(actionUrl) {
  const modal = document.getElementById('deleteModal');
  const form  = document.getElementById('deleteForm');
  if (!modal || !form) return;
  form.action = actionUrl;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeDeleteModal() {
  const modal = document.getElementById('deleteModal');
  if (!modal) return;
  modal.classList.remove('open');
  document.body.style.overflow = '';
}

// Close modal on overlay click
document.addEventListener('click', e => {
  const modal = document.getElementById('deleteModal');
  if (e.target === modal) closeDeleteModal();
});

// Close on ESC
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDeleteModal();
});

// ── Password Toggle ──────────────────────────────────────
function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const icon = btn.querySelector('i');
  if (input.type === 'password') {
    input.type = 'text';
    if (icon) icon.className = 'fa-solid fa-eye-slash';
  } else {
    input.type = 'password';
    if (icon) icon.className = 'fa-solid fa-eye';
  }
}

// ── Flash auto-dismiss ───────────────────────────────────
function initFlashMessages() {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach((flash, i) => {
    setTimeout(() => {
      flash.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      flash.style.opacity = '0';
      flash.style.transform = 'translateY(-8px)';
      setTimeout(() => flash.remove(), 500);
    }, 4000 + i * 500);
  });
}

// ── Form Validation ──────────────────────────────────────
function initFormValidation() {
  const forms = document.querySelectorAll('form[novalidate]');
  forms.forEach(form => {
    form.addEventListener('submit', e => {
      let valid = true;
      const requiredFields = form.querySelectorAll('[required]');

      requiredFields.forEach(field => {
        clearFieldError(field);
        if (!field.value.trim()) {
          showFieldError(field, 'This field is required.');
          valid = false;
        }
      });

      // Password match check (register page)
      const pwd    = form.querySelector('#password');
      const confirm = form.querySelector('#confirm_password');
      if (pwd && confirm && pwd.value !== confirm.value) {
        showFieldError(confirm, 'Passwords do not match.');
        valid = false;
      }

      // Min length checks
      if (pwd && pwd.value && pwd.value.length < 6) {
        showFieldError(pwd, 'Password must be at least 6 characters.');
        valid = false;
      }

      const username = form.querySelector('#username');
      if (username && username.value.length > 0 && username.value.length < 3) {
        showFieldError(username, 'Username must be at least 3 characters.');
        valid = false;
      }

      if (!valid) {
        e.preventDefault();
        // Scroll to first error
        const firstError = form.querySelector('.field-error');
        if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });

    // Live validation: clear error on input
    form.querySelectorAll('.form-control').forEach(field => {
      field.addEventListener('input', () => clearFieldError(field));
    });
  });
}

function showFieldError(field, message) {
  field.style.borderColor = 'var(--danger)';
  field.style.boxShadow  = '0 0 0 3px var(--danger-dim)';
  let errorEl = field.parentElement.querySelector('.field-error');
  if (!errorEl) {
    errorEl = document.createElement('span');
    errorEl.className = 'field-error';
    errorEl.style.cssText = 'color: var(--danger); font-size: 11px; font-weight: 600; margin-top: 2px;';
    field.parentElement.appendChild(errorEl);
  }
  errorEl.textContent = message;
}

function clearFieldError(field) {
  field.style.borderColor = '';
  field.style.boxShadow   = '';
  const errorEl = field.parentElement.querySelector('.field-error');
  if (errorEl) errorEl.remove();
}

// ── Search debounce ──────────────────────────────────────
function initSearchDebounce() {
  const filterForm = document.getElementById('filterForm');
  const searchInput = filterForm?.querySelector('input[name="search"]');
  if (!searchInput) return;

  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      filterForm.submit();
    }, 500);
  });
}

// ── Loading state on form submit ─────────────────────────
function initSubmitLoading() {
  document.querySelectorAll('form:not(#deleteForm):not(#filterForm)').forEach(form => {
    form.addEventListener('submit', () => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving…';
      }
    });
  });
}

// ── Tooltip on long remarks ──────────────────────────────
function initTooltips() {
  document.querySelectorAll('.remarks-text').forEach(el => {
    el.title = el.textContent.trim();
  });
}

// ── Entry point ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Apply saved theme
  applyTheme(getTheme());

  // Theme toggle button
  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  initSidebar();
  initFlashMessages();
  initFormValidation();
  initSearchDebounce();
  initSubmitLoading();
  initTooltips();
});