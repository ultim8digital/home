(() => {
  'use strict';
  const root = document.documentElement;
  const button = document.querySelector('.ap-motion');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = false;
  try { paused = localStorage.getItem('anypractice-motion') === 'paused'; } catch (_) {}
  const update = () => {
    const enabled = !paused && !reduced.matches;
    root.classList.toggle('ap-motion-on', enabled);
    if (button) {
      button.hidden = reduced.matches;
      button.setAttribute('aria-pressed', String(paused));
      button.setAttribute('aria-label', paused ? button.dataset.resume : button.dataset.pause);
      button.querySelector('[data-pause]').style.display = paused ? 'none' : '';
      button.querySelector('[data-play]').style.display = paused ? '' : 'none';
    }
  };
  button?.addEventListener('click', () => {
    paused = !paused;
    try { localStorage.setItem('anypractice-motion', paused ? 'paused' : 'running'); } catch (_) {}
    update();
  });
  reduced.addEventListener('change', update);
  update();
  const picker = document.querySelector('.language-picker');
  if (picker) {
    document.addEventListener('click', event => { if (!picker.contains(event.target)) picker.open = false; });
    picker.addEventListener('keydown', event => { if (event.key === 'Escape') { picker.open = false; picker.querySelector('summary').focus(); } });
    picker.addEventListener('focusout', event => { if (event.relatedTarget instanceof Node && !picker.contains(event.relatedTarget)) picker.open = false; });
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) root.classList.remove('ap-motion-on'); else update();
  });
  if ('IntersectionObserver' in window && !reduced.matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        if (!paused && !reduced.matches) entry.target.animate([{opacity:.4,transform:'translateY(16px)'},{opacity:1,transform:'translateY(0)'}], {duration:650,easing:'cubic-bezier(.2,.7,.2,1)'});
        observer.unobserve(entry.target);
      });
    }, {threshold:.08});
    document.querySelectorAll('[data-ap-reveal]').forEach(element => observer.observe(element));
  }
})();
