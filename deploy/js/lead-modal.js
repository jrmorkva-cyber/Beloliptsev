/* lead-modal.js — поп-ап с короткой формой (Имя+Телефон). Перехватывает CTA-кнопки,
   которые раньше прыгали на форму у подвала (href="#cta"/"#form") и .svc-b «Подробнее».
   Внутренние ссылки (на /uslugi/, /premium/ и т.д.) НЕ трогаются. G06 + V03. */
(function () {
  function injectOnce() {
    if (document.getElementById('lead-modal-css')) return;
    var s = document.createElement('style'); s.id = 'lead-modal-css';
    s.textContent =
      '#leadModal{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;background:rgba(20,24,34,.62);backdrop-filter:blur(4px)}' +
      '#leadModal.open{display:flex}' +
      '#leadModal .lm-card{background:var(--Color-5,#EDECEB);max-width:440px;width:92%;padding:42px 36px;position:relative;box-shadow:0 30px 80px rgba(0,0,0,.45)}' +
      '#leadModal .lm-close{position:absolute;top:12px;right:16px;font-size:28px;line-height:1;cursor:pointer;color:var(--Color,#272F42);background:none;border:0;padding:4px}' +
      '#leadModal h3{font-family:var(--font-display,"Anticva","Prata",Georgia,serif);font-size:30px;line-height:1.05;color:var(--Color,#272F42);margin:0 0 8px;text-transform:uppercase;letter-spacing:.01em}' +
      '#leadModal .lm-sub{color:var(--Color,#272F42);opacity:.65;font-size:15px;margin:0 0 22px;line-height:1.45}' +
      '#leadModal input[type=text],#leadModal input[type=tel]{width:100%;box-sizing:border-box;height:52px;padding:0 16px;margin-bottom:12px;border:1px solid rgba(39,47,66,.25);background:#fff;font-size:16px;font-family:inherit;color:var(--Color,#272F42)}' +
      '#leadModal input:focus{outline:none;border-color:var(--Color-3,#BB5C3C)}' +
      '#leadModal .lm-consent{display:flex;align-items:flex-start;gap:8px;font-size:12.5px;color:var(--Color,#272F42);opacity:.7;margin:6px 0 18px;cursor:pointer}' +
      '#leadModal .lm-submit{width:100%;height:54px;border:0;cursor:pointer;background:var(--Color-3,#BB5C3C);color:#fff;font-size:17px;letter-spacing:.02em}' +
      '#leadModal .lm-submit:hover{background:var(--c2,#AC5336)}' +
      '#leadModal .lm-ok{display:none}#leadModal.done .lm-form{display:none}#leadModal.done .lm-ok{display:block}';
    document.head.appendChild(s);
    var m = document.createElement('div'); m.id = 'leadModal'; m.setAttribute('aria-hidden', 'true');
    m.innerHTML =
      '<div class="lm-card" role="dialog" aria-modal="true" aria-label="Оставить заявку">' +
      '<button class="lm-close" aria-label="Закрыть">×</button>' +
      '<div class="lm-form">' +
      '<h3>Бесплатная консультация</h3><div class="lm-sub">30 минут · без обязательств.<br>Перезвоню лично в течение рабочего дня.</div>' +
      '<input type="text" name="name" placeholder="Как к вам обращаться?" autocomplete="name">' +
      '<input type="tel" name="phone" placeholder="+7 (___) ___-__-__" autocomplete="tel" inputmode="tel">' +
      '<label class="lm-consent"><input type="checkbox" checked> Соглашаюсь с <a href="/politika-konfidentsialnosti/" style="color:inherit;text-decoration:underline">политикой конфиденциальности</a> и обработкой персональных данных.</label>' +
      '<button class="lm-submit" type="button">Отправить заявку</button>' +
      '</div>' +
      '<div class="lm-ok"><h3>Спасибо</h3><div class="lm-sub">Заявка принята — свяжусь с вами лично.</div></div>' +
      '</div>';
    document.body.appendChild(m);
    function close() { m.classList.remove('open'); m.setAttribute('aria-hidden', 'true'); }
    function open() { m.classList.remove('done'); m.classList.add('open'); m.setAttribute('aria-hidden', 'false'); var i = m.querySelector('input[name=name]'); if (i) setTimeout(function () { i.focus(); }, 60); }
    m.querySelector('.lm-close').addEventListener('click', close);
    m.addEventListener('click', function (e) { if (e.target === m) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    m.querySelector('.lm-submit').addEventListener('click', function () {
      var ph = m.querySelector('input[name=phone]');
      if (!ph.value.trim()) { ph.focus(); return; }
      m.classList.add('done');
    });
    window.__leadOpen = open;
  }
  function bind() {
    injectOnce();
    var sel = 'a[href="#cta"], a[href="#form"], a[href="#zayavka"], a[href="#kontakt"], .svc-b, [data-lead]';
    [].forEach.call(document.querySelectorAll(sel), function (el) {
      if (el.__leadBound) return; el.__leadBound = true;
      el.addEventListener('click', function (e) { e.preventDefault(); if (window.__leadOpen) window.__leadOpen(); });
    });
  }
  if (!window.__leadModalBound) { window.__leadModalBound = true; document.addEventListener('astro:page-load', bind); bind(); }
})();
