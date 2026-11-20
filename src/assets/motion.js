(() => {
  'use strict';
  const root = document.documentElement;
  const toggle = document.querySelector('[data-motion-toggle]');
  if (!toggle || !window.matchMedia) return;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const wide = window.matchMedia('(min-width: 901px) and (min-height: 680px)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const nativeScroll = window.CSS && CSS.supports('animation-timeline: scroll()');
  const revealed = new WeakSet();
  let paused = false;
  let cleanup = () => {};
  try { paused = window.localStorage.getItem('ud-motion') === 'off'; } catch (_) { /* Storage is optional. */ }

  function startMotion() {
    const disposers = [];
    const animations = new Set();
    const hero = document.querySelector('.hero');
    const art = document.querySelector('.hero-art');
    const progress = document.querySelector('.page-progress');
    const story = document.querySelector('[data-story]');
    const stage = document.querySelector('[data-story-stage]');
    const chapters = Array.from(document.querySelectorAll('[data-chapter]'));
    const scenes = Array.from(document.querySelectorAll('[data-scene]'));
    const dots = Array.from(document.querySelectorAll('[data-story-dot]'));
    const studio = document.querySelector('.studio-illustration');
    let frame = 0;
    let disposed = false;
    let heroVisible = true;
    let storyVisible = false;
    let studioVisible = false;
    let active = -1;
    let documentHeight = document.documentElement.scrollHeight;

    function listen(target, name, callback, options) {
      target.addEventListener(name, callback, options);
      disposers.push(() => target.removeEventListener(name, callback, options));
    }
    function animate(element, delay = 0) {
      if (disposed || revealed.has(element) || !element.animate) return;
      revealed.add(element);
      const animation = element.animate([
        {opacity: 0, translate: '0 25px'}, {opacity: 1, translate: '0 0'}
      ], {duration: 750, delay, fill: 'backwards', easing: 'cubic-bezier(.22,1,.36,1)'});
      animations.add(animation);
      animation.finished.catch(() => {}).finally(() => animations.delete(animation));
    }
    function setScene(index, amount) {
      if (active !== index) {
        active = index;
        scenes.forEach((scene, i) => scene.classList.toggle('is-active', i === index));
        stage.dataset.active = String(index);
      }
      scenes[index].style.setProperty('--chapter-progress', amount.toFixed(3));
      dots.forEach((dot, i) => dot.style.setProperty('--scene-fill', i < index ? '1' : i === index ? String(amount) : '0'));
    }
    const clamp = value => Math.max(0, Math.min(1, value));
    function draw() {
      frame = 0;
      if (disposed || document.hidden) return;
      const viewport = window.innerHeight;
      if (!nativeScroll) {
        progress.style.setProperty('--page-progress', clamp(window.scrollY / Math.max(1, documentHeight - viewport)).toFixed(4));
      }
      if (heroVisible) {
        const rect = hero.getBoundingClientRect();
        art.style.setProperty('--hero-scroll', clamp(-rect.top / rect.height).toFixed(3));
      }
      if (storyVisible && wide.matches) {
        const bounds = stage.getBoundingClientRect();
        const target = bounds.top + bounds.height / 2;
        let closest = 0;
        let distance = Infinity;
        const rectangles = chapters.map(chapter => chapter.getBoundingClientRect());
        rectangles.forEach((rect, index) => {
          const gap = Math.abs(rect.top + rect.height / 2 - target);
          if (gap < distance) { distance = gap; closest = index; }
        });
        const rect = rectangles[closest];
        setScene(closest, clamp((target - rect.top) / rect.height));
      }
      if (studioVisible && !nativeScroll) {
        const rect = studio.getBoundingClientRect();
        studio.style.rotate = `${-17 + clamp((viewport - rect.top) / (viewport + rect.height)) * 39}deg`;
      }
    }
    function schedule() {
      if (!disposed && !frame && !document.hidden) frame = window.requestAnimationFrame(draw);
    }
    function resize() {
      story.classList.toggle('story-enhanced', wide.matches);
      documentHeight = document.documentElement.scrollHeight;
      schedule();
    }

    root.classList.toggle('native-scroll', !!nativeScroll);
    hero.classList.add('hero-in-view');
    const initial = hero.getBoundingClientRect();
    if (initial.bottom > 0 && initial.top < window.innerHeight) {
      hero.querySelectorAll('.eyebrow, .hero-line, .hero-description, .hero-actions, .hero-note').forEach((el, i) => animate(el, i * 70));
    }

    if ('IntersectionObserver' in window) {
      const entering = new IntersectionObserver(entries => {
        const visible = entries.filter(entry => entry.isIntersecting);
        visible.forEach((entry, index) => {
          animate(entry.target, Math.min(index, 3) * 70);
          entering.unobserve(entry.target);
        });
      }, {threshold: .06});
      document.querySelectorAll('[data-reveal]').forEach(element => entering.observe(element));
      disposers.push(() => entering.disconnect());

      const visibility = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.target === hero) {
            heroVisible = entry.isIntersecting;
            hero.classList.toggle('hero-in-view', heroVisible);
          }
          if (entry.target === story) storyVisible = entry.isIntersecting;
          if (entry.target === studio) studioVisible = entry.isIntersecting;
        });
        schedule();
      }, {rootMargin: '80px 0px'});
      [hero, story, studio].forEach(element => visibility.observe(element));
      disposers.push(() => visibility.disconnect());
    } else {
      // The document is still complete when observers are unavailable.
      storyVisible = studioVisible = true;
    }

    if (finePointer.matches) {
      let artBounds;
      listen(art, 'pointerenter', () => { artBounds = art.getBoundingClientRect(); });
      listen(art, 'pointermove', event => {
        if (!artBounds) return;
        art.style.setProperty('--hero-rx', `${(0.5 - (event.clientY - artBounds.top) / artBounds.height) * 5}deg`);
        art.style.setProperty('--hero-ry', `${((event.clientX - artBounds.left) / artBounds.width - 0.5) * 5}deg`);
      });
      listen(art, 'pointerleave', () => { art.style.removeProperty('--hero-rx'); art.style.removeProperty('--hero-ry'); });
      document.querySelectorAll('.app-card').forEach(card => {
        let bounds;
        listen(card, 'pointerenter', () => { bounds = card.getBoundingClientRect(); });
        listen(card, 'pointermove', event => {
          if (!bounds) return;
          const x = (event.clientX - bounds.left) / bounds.width;
          const y = (event.clientY - bounds.top) / bounds.height;
          card.style.setProperty('--card-rx', `${(0.5 - y) * 3}deg`);
          card.style.setProperty('--card-ry', `${(x - 0.5) * 3}deg`);
          card.style.setProperty('--card-x', `${x * 100}%`);
          card.style.setProperty('--card-y', `${y * 100}%`);
        });
        const reset = () => ['--card-rx', '--card-ry', '--card-x', '--card-y'].forEach(name => card.style.removeProperty(name));
        listen(card, 'pointerleave', reset);
        disposers.push(reset);
      });
    }
    listen(window, 'scroll', schedule, {passive: true});
    listen(window, 'resize', resize, {passive: true});
    listen(wide, 'change', resize);
    listen(document, 'visibilitychange', () => {
      root.classList.toggle('motion-suspended', document.hidden);
      if (document.hidden) { cancelAnimationFrame(frame); frame = 0; } else schedule();
    });
    chapters.forEach((chapter, index) => listen(chapter, 'focusin', () => setScene(index, .5)));
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(() => { documentHeight = document.documentElement.scrollHeight; schedule(); });
      observer.observe(document.body);
      disposers.push(() => observer.disconnect());
    }
    resize();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      disposers.forEach(dispose => dispose());
      animations.forEach(animation => animation.cancel());
      story.classList.remove('story-enhanced');
      hero.classList.remove('hero-in-view');
      root.classList.remove('native-scroll', 'motion-suspended');
      ['--hero-scroll', '--hero-rx', '--hero-ry'].forEach(name => art.style.removeProperty(name));
      progress.style.removeProperty('--page-progress');
      studio.style.removeProperty('rotate');
    };
  }

  function configure() {
    cleanup();
    const enabled = !paused && !reduced.matches;
    root.classList.toggle('motion-enabled', enabled);
    root.dataset.motion = enabled ? 'on' : 'off';
    toggle.hidden = false;
    toggle.disabled = reduced.matches;
    toggle.setAttribute('aria-pressed', String(enabled));
    toggle.title = reduced.matches ? toggle.dataset.reduced : enabled ? toggle.dataset.pause : toggle.dataset.resume;
    cleanup = enabled ? startMotion() : () => {};
  }
  toggle.addEventListener('click', () => {
    paused = !paused;
    try { window.localStorage.setItem('ud-motion', paused ? 'off' : 'on'); } catch (_) { /* Optional. */ }
    configure();
  });
  reduced.addEventListener('change', configure);
  configure();
})();
