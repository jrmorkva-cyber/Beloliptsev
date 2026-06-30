/* motion-plus.js — лёгкий моушн-слой:
   1) count-up чисел-сигнатур при появлении (SEO/PRM-safe: финал = исходный текст);
   2) параллакс фото-геро (.hp-hero__img) на десктопе.
   Всё под prefers-reduced-motion, только transform/opacity, без бесконечных циклов.
   Перезапуск count-up на каждый astro:page-load (SPA ClientRouter); scroll-слушатель один. */
(function () {
  function PRM() { return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

  /* ── 1 · COUNT-UP ────────────────────────────────────────────── */
  function countUp(el) {
    if (el.__cuDone) return;
    el.__cuDone = true;
    var raw = el.textContent;
    var m = raw.match(/\d+/);
    if (!m) return;
    var target = parseInt(m[0], 10);
    if (!isFinite(target) || target <= 1) return;
    var prefix = raw.slice(0, m.index);
    var suffix = raw.slice(m.index + m[0].length);
    var DUR = Math.min(1100, 420 + target * 1.1);
    el.setAttribute('data-countup-active', '');
    var startTs = null;
    function frame(ts) {
      if (startTs === null) startTs = ts;
      var p = Math.min(1, (ts - startTs) / DUR);
      el.textContent = prefix + Math.round(easeOut(p) * target) + suffix;
      if (p < 1) requestAnimationFrame(frame);
      else { el.textContent = raw; el.removeAttribute('data-countup-active'); }
    }
    requestAnimationFrame(frame);
  }
  function initCountUp() {
    if (!('IntersectionObserver' in window) || PRM()) return;
    var sel = '.bld-compare__y,.bld-stat3__n,.om2-stat__n,.hp-stats b,.hp-stat__n,' +
      '.st-stat__n,.st-hstat__n,.vh-fact__num,.mz-epoch__year';
    var els = [].slice.call(document.querySelectorAll(sel)).filter(function (el) { return !el.__cuDone; });
    if (!els.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { countUp(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.6 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ── 2 · ПАРАЛЛАКС ФОТО-ГЕРО (десктоп; мобайл геро relative — пропускаем) ─ */
  var pTick = false;
  function parallaxFrame() {
    pTick = false;
    if (PRM() || window.innerWidth <= 860) return;
    var vh = window.innerHeight;
    var imgs = document.querySelectorAll('.hp-hero__img');
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i], hero = img.parentElement;
      if (!hero) continue;
      var r = hero.getBoundingClientRect();
      if (r.bottom < 0 || r.top > vh || !r.height) { continue; }
      var prog = (vh - r.top) / (vh + r.height);          // 0..1 прохождение через экран
      var shift = (prog - 0.5) * r.height * 0.12;          // ±6% высоты (масштаб 1.12 кроет щели)
      img.style.transform = 'translate3d(0,' + shift.toFixed(1) + 'px,0) scale(1.12)';
      img.style.willChange = 'transform';
    }
  }
  function onScroll() { if (!pTick) { requestAnimationFrame(parallaxFrame); pTick = true; } }

  function init() { initCountUp(); parallaxFrame(); }

  if (!window.__motionPlusBound) {
    window.__motionPlusBound = true;
    document.addEventListener('astro:page-load', init);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    init();
  }
})();
