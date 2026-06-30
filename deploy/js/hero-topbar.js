/* Прозрачная шапка над full-bleed геро → navy после геро. Реюз на всех страницах с .hp-hero. */
(function () {
  var h = document.querySelector('.st-topbar--solid'),
      s = document.querySelector('.hp-hero');
  if (!h || !s) return;
  function u() {
    h.classList.toggle('is-solid', window.scrollY > (s.offsetHeight - h.offsetHeight - 10));
  }
  u();
  addEventListener('scroll', u, { passive: true });
  addEventListener('resize', u);
})();
