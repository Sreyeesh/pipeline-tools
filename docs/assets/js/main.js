const applyTheme = (value) => {
  document.documentElement.setAttribute('data-theme', value);
  localStorage.setItem('pipely-theme', value);
  const toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    const icon = toggle.querySelector('.theme-icon');
    if (icon) {
      icon.innerHTML = value === 'dark'
        ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4.75V2m0 20v-2.75M19.25 12H22m-20 0H4.75M17.78 6.22l1.59-1.59M4.63 19.37l1.59-1.59M17.78 17.78l1.59 1.59M4.63 4.63l1.59 1.59M12 7.25a4.75 4.75 0 100 9.5 4.75 4.75 0 000-9.5z\"/></svg>'
        : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.02 14.6a7.5 7.5 0 01-10.62-10 8.75 8.75 0 1010.62 10z\"/></svg>';
    }
    toggle.setAttribute('aria-pressed', value === 'dark' ? 'true' : 'false');
  }
};

const initTheme = () => {
  const saved = localStorage.getItem('pipely-theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved || (prefersDark ? 'dark' : 'light'));
};

const bindThemeToggle = () => {
  const toggle = document.querySelector('.theme-toggle');
  if (!toggle) return;
  toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });
};

const reveal = () => {
  const nodes = document.querySelectorAll('.feature, .install-card, .flow-step, .doc-card');
  const trigger = window.innerHeight * 0.85;
  nodes.forEach((node) => {
    const rect = node.getBoundingClientRect();
    if (rect.top < trigger) {
      node.classList.add('is-visible');
    }
  });
};

window.addEventListener('scroll', reveal, { passive: true });
window.addEventListener('load', () => {
  initTheme();
  bindThemeToggle();
  reveal();
});
