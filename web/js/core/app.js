/* =============================================================
   GETITRIGHT -- Core Application Engine
   Handles: icon injection, sidebar, modals, toasts, routing
   ============================================================= */

const App = {
  // -- Initialize everything --
  init() {
    this.injectIcons();
    this.initSidebar();
    this.initModals();
    this.initScrollEffects();
    this.initSearch();
    this.logInit();
  },

  // -- Inject SVG icons into all [data-icon] elements --
  injectIcons() {
    const targets = document.querySelectorAll('[data-icon]');
    targets.forEach(el => {
      const iconName = el.getAttribute('data-icon');
      if (Icons && Icons[iconName]) {
        el.innerHTML = Icons[iconName];
      }
    });
  },

  // -- Sidebar toggle (mobile) --
  initSidebar() {
    const toggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const shell = document.getElementById('app-shell');

    if (!toggle || !sidebar) return;

    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (sidebar.classList.contains('open')) {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.id = 'sidebar-overlay';
        overlay.style.cssText = `
          position:fixed;inset:0;background:rgba(0,0,0,0.5);
          z-index:199;backdrop-filter:blur(4px);
        `;
        overlay.addEventListener('click', () => {
          sidebar.classList.remove('open');
          overlay.remove();
        });
        document.body.appendChild(overlay);
      } else {
        const overlay = document.getElementById('sidebar-overlay');
        if (overlay) overlay.remove();
      }
    });
  },

  // -- Modal system --
  initModals() {
    // Create modal
    const fab = document.getElementById('fab-create');
    const modal = document.getElementById('create-modal');
    const modalClose = document.getElementById('modal-close');

    if (fab && modal) {
      fab.addEventListener('click', () => modal.classList.add('active'));
    }

    if (modalClose && modal) {
      modalClose.addEventListener('click', () => modal.classList.remove('active'));
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('active');
      });
    }

    // Generic modal triggers
    document.querySelectorAll('[data-modal-target]').forEach(trigger => {
      trigger.addEventListener('click', () => {
        const target = document.getElementById(trigger.dataset.modalTarget);
        if (target) target.classList.add('active');
      });
    });

    document.querySelectorAll('[data-modal-dismiss]').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal-backdrop');
        if (modal) modal.classList.remove('active');
      });
    });
  },

  // -- Scroll effects (sticky nav, etc) --
  initScrollEffects() {
    const nav = document.querySelector('.landing-nav');
    if (!nav) return;

    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          if (window.scrollY > 40) {
            nav.classList.add('scrolled');
          } else {
            nav.classList.remove('scrolled');
          }
          ticking = false;
        });
        ticking = true;
      }
    });
  },

  // -- Search --
  initSearch() {
    const searchInput = document.getElementById('global-search');
    if (!searchInput) return;

    let debounce;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        const query = e.target.value.trim().toLowerCase();
        if (query.length > 0) {
          console.log('[Search] Query:', query);
        }
      }, 300);
    });
  },

  // -- Toast notifications --
  showToast(message, type) {
    type = type || 'success';
    const container = document.getElementById('toast-container');
    if (!container) return;

    const iconMap = {
      success: Icons.checkCircle,
      error: Icons.alertCircle,
      info: Icons.alertCircle,
    };

    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.innerHTML = `
      <span class="toast-icon">${iconMap[type] || iconMap.info}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-dismiss btn btn-ghost btn-icon" style="width:28px;height:28px;">${Icons.close}</button>
    `;

    const dismiss = toast.querySelector('.toast-dismiss');
    dismiss.addEventListener('click', () => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 200);
    });

    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentNode) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 200);
      }
    }, 4000);
  },

  // -- Startup log (no emojis) --
  logInit() {
    console.log('[Getitright] App initialized');
    console.log('[Getitright] Icons injected:', document.querySelectorAll('[data-icon]').length, 'targets');
  },
};

// -- Poll interaction handler --
const PollInteraction = {
  init() {
    document.querySelectorAll('.poll-option').forEach(option => {
      option.addEventListener('click', () => {
        const pollCard = option.closest('.poll-card');
        if (!pollCard) return;

        pollCard.querySelectorAll('.poll-option').forEach(o => {
          o.classList.remove('selected');
        });
        option.classList.add('selected');

        App.showToast('Vote recorded', 'success');
      });
    });
  },
};

// -- Role-based redirect --
const AuthRedirect = {
  getRole() {
    return localStorage.getItem('gir_role') || null;
  },
  setRole(role) {
    localStorage.setItem('gir_role', role);
  },
  isLoggedIn() {
    return localStorage.getItem('gir_logged_in') === 'true';
  },
  login(role) {
    localStorage.setItem('gir_logged_in', 'true');
    localStorage.setItem('gir_role', role);
  },
  logout() {
    localStorage.removeItem('gir_logged_in');
    localStorage.removeItem('gir_role');
    window.location.href = '/';
  },
  redirect() {
    const role = this.getRole();
    if (!this.isLoggedIn()) return;
    if (role === 'org') {
      window.location.href = 'console/dashboard.html';
    } else {
      window.location.href = 'pages/vote.html';
    }
  },
};

// -- Tab switching --
const TabSystem = {
  init() {
    document.querySelectorAll('.tabs').forEach(tabGroup => {
      const tabs = tabGroup.querySelectorAll('.tab');
      tabs.forEach(tab => {
        tab.addEventListener('click', () => {
          tabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');

          const target = tab.dataset.tab;
          if (target) {
            const parent = tabGroup.closest('.dashboard-section') || tabGroup.parentElement;
            parent.querySelectorAll('.tab-content').forEach(content => {
              content.style.display = 'none';
            });
            const active = parent.querySelector('[data-tab-content="' + target + '"]');
            if (active) active.style.display = 'block';
          }
        });
      });
    });
  },
};

// Boot
document.addEventListener('DOMContentLoaded', () => {
  App.init();
  PollInteraction.init();
  TabSystem.init();
});
