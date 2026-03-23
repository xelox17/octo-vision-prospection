// ── Toast notifications ──────────────────────────────────────────────────────
function showToast(message, type = 'default', duration = 3000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(10px)';
    toast.style.transition = 'opacity .3s, transform .3s';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Animate stat counters on page load ──────────────────────────────────────
function animateCounters() {
  document.querySelectorAll('.stat-value[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target);
    if (isNaN(target) || target === 0) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 30));
    el.textContent = '0';
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString('fr-FR');
      if (current >= target) clearInterval(timer);
    }, 20);
  });
}

// ── Animate score bars on page load ─────────────────────────────────────────
function animateScoreBars() {
  document.querySelectorAll('.score-bar').forEach(bar => {
    const w = bar.style.width;
    bar.style.width = '0';
    requestAnimationFrame(() => {
      setTimeout(() => { bar.style.width = w; }, 100);
    });
  });
}

// ── Auto-highlight overdue follow-ups ───────────────────────────────────────
function highlightOverdue() {
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('.follow-up-badge').forEach(badge => {
    const dateText = badge.textContent.trim().replace(/^\S+\s/, '');
    if (dateText && dateText <= today) {
      badge.classList.add('overdue');
    }
  });
}

// ── Keyboard shortcut: / to focus search ────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {
    e.preventDefault();
    const search = document.getElementById('searchInput');
    if (search) { search.focus(); search.select(); }
  }
  if (e.key === 'Escape') {
    const modal = document.getElementById('aiModal');
    if (modal && modal.style.display !== 'none') {
      modal.style.display = 'none';
    }
  }
});

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  animateCounters();
  animateScoreBars();
  highlightOverdue();
});
