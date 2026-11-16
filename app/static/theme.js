(() => {
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let preference;
  try { preference = localStorage.getItem('daily-java-theme'); } catch (_) {}
  if (preference !== 'light' && preference !== 'dark') preference = null;

  function apply(theme) {
    root.dataset.theme = theme;
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      const dark = theme === 'dark';
      toggle.hidden = false;
      toggle.setAttribute('aria-pressed', String(dark));
      toggle.textContent = dark ? 'Dark mode: on' : 'Dark mode: off';
    }
  }

  apply(preference || (system.matches ? 'dark' : 'light'));
  system.addEventListener('change', () => {
    if (!preference) apply(system.matches ? 'dark' : 'light');
  });
  document.addEventListener('DOMContentLoaded', () => {
    apply(root.dataset.theme);
    document.getElementById('theme-toggle').addEventListener('click', () => {
      preference = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('daily-java-theme', preference); } catch (_) {}
      apply(preference);
    });
  });
})();
