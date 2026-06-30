/* ya-map.js — интерактивные Яндекс.Карты (JS API 2.1) на районных страницах и зданиях.
   Контейнер: <div class="ya-map" data-yamap data-center="lat,lng" data-zoom="14"
                   data-points='[{"c":[lat,lng],"t":"Подпись"}]'></div>
   Ленивая загрузка API при входе в экран; терракотовые метки; scroll-zoom выключен
   (страница не «залипает»). Ключ — публичный клиентский (ограничен по домену в кабинете). */
(function () {
  var KEY = 'ea259b35-dffd-4e79-a0e6-8eb27cdb6c18';
  var loading = false, ready = false, queue = [];

  function injectCss() {
    if (document.getElementById('ya-map-css')) return;
    var s = document.createElement('style'); s.id = 'ya-map-css';
    s.textContent =
      '.ya-map{width:100%;height:100%;min-height:380px;background:var(--pear-ink,#1B2230);' +
      'border:1px solid var(--line,rgba(39,47,66,.2));position:relative}' +
      '.ya-map::after{content:"Карта загружается…";position:absolute;inset:0;display:flex;' +
      'align-items:center;justify-content:center;font-family:var(--font-mono,monospace);' +
      'font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--on-dark-70,#bbb);' +
      'pointer-events:none}.ya-map.is-ready::after,.ya-map:has(ymaps)::after{display:none}' +
      '.ya-map ymaps{filter:saturate(.82) contrast(1.02)}';
    document.head.appendChild(s);
  }

  function loadApi() {
    if (loading || ready) return;
    loading = true;
    var s = document.createElement('script');
    s.src = 'https://api-maps.yandex.ru/2.1/?apikey=' + KEY + '&lang=ru_RU';
    s.onload = function () { window.ymaps.ready(function () { ready = true; queue.splice(0).forEach(build); }); };
    s.onerror = function () { loading = false; };
    document.head.appendChild(s);
  }

  function build(el) {
    if (el.__ymInit) return; el.__ymInit = true;
    var c = (el.getAttribute('data-center') || '55.751,37.618').split(',').map(Number);
    var zoom = parseInt(el.getAttribute('data-zoom') || '14', 10);
    var pts = []; try { pts = JSON.parse(el.getAttribute('data-points') || '[]'); } catch (e) {}
    var map = new window.ymaps.Map(el, { center: c, zoom: zoom, controls: ['zoomControl'] },
      { suppressMapOpenBlock: true, yandexMapDisablePoiInteractivity: true });
    map.behaviors.disable('scrollZoom');
    pts.forEach(function (p) {
      map.geoObjects.add(new window.ymaps.Placemark(p.c, { hintContent: p.t, balloonContent: p.t },
        { preset: 'islands#dotIcon', iconColor: '#BB5C3C' }));
    });
    if (pts.length > 1) { try { map.setBounds(map.geoObjects.getBounds(), { checkZoomRange: true, zoomMargin: 40 }); } catch (e) {} }
    el.classList.add('is-ready');
  }

  function init() {
    var maps = [].slice.call(document.querySelectorAll('[data-yamap]'));
    if (!maps.length) return;
    injectCss();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        if (ready) build(e.target); else { queue.push(e.target); loadApi(); }
      });
    }, { rootMargin: '200px' });
    maps.forEach(function (m) { io.observe(m); });
  }

  if (!window.__yaMapBound) {
    window.__yaMapBound = true;
    document.addEventListener('astro:page-load', init);
    init();
  }
})();
