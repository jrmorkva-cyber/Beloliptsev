/* Прозрачная шапка над full-bleed геро → navy после геро,
   + медленный зум фонового фото при скролле (Ken Burns, motion ≤2/5).
   Реюз на всех страницах с .hp-hero. */
(function () {
  var h = document.querySelector('.st-topbar--solid'),
      s = document.querySelector('.hp-hero');
  if (!s) return;

  var img = s.querySelector('img.hp-hero__img');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) img = null;                 // reduced-motion → фото статично
  if (img) img.style.willChange = 'transform';

  var ticking = false;
  function u() {
    ticking = false;
    if (h) h.classList.toggle('is-solid', window.scrollY > (s.offsetHeight - h.offsetHeight - 10));
    if (img) {
      var t = -s.getBoundingClientRect().top / window.innerHeight;   // 0 в топе → 1 через экран
      t = t < 0 ? 0 : (t > 1 ? 1 : t);
      img.style.transform = 'scale(' + (1 + t * 0.12).toFixed(4) + ')';  // 1.00 → 1.12
    }
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(u); } }

  u();
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll);
})();
