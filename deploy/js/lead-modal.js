/* lead-modal.js — split-попап (левая оранжевая декоративная + правая форма).
   Перехватывает CTA: href="#cta"/"#form"/"#zayavka"/"#kontakt" + .svc-b + [data-lead].
   Внутренние ссылки (на /uslugi/ и т.д.) НЕ трогаются. G06 + V03. */
(function () {
  function injectOnce() {
    if (document.getElementById('lead-modal-css')) return;
    var s = document.createElement('style'); s.id = 'lead-modal-css';
    s.textContent =
      /* overlay */
      '#leadModal{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;background:rgba(20,24,34,.62);backdrop-filter:blur(4px);padding:16px}' +
      '#leadModal.open{display:flex}' +
      /* split card */
      '#leadModal .lm-card{display:flex;max-width:820px;width:100%;position:relative;box-shadow:0 30px 80px rgba(0,0,0,.5)}' +
      /* left panel — orange + pattern */
      '#leadModal .lm-left{width:260px;flex:none;background:#BB5C3C;position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end;padding:40px 32px}' +
      '#leadModal .lm-left::before{content:"";position:absolute;inset:0;background:url("/assets/img/pattern-waves.png") center/420px;opacity:.07;filter:invert(1);pointer-events:none}' +
      '#leadModal .lm-brand{position:relative;z-index:1}' +
      '#leadModal .lm-brand img{height:34px;width:auto;display:block}' +
      '#leadModal .lm-brand p{margin:16px 0 0;color:rgba(237,236,235,.82);font-size:14px;line-height:1.55}' +
      /* right panel — form */
      '#leadModal .lm-right{flex:1;background:#EDECEB;padding:42px 36px 40px;position:relative;min-width:0}' +
      '#leadModal .lm-close{position:absolute;top:14px;right:16px;font-size:26px;line-height:1;cursor:pointer;color:#272F42;background:none;border:0;padding:4px;z-index:2}' +
      '#leadModal h3{font-family:var(--font-display,"Anticva","Prata",Georgia,serif);font-size:28px;line-height:1.05;color:#272F42;margin:0 0 8px;text-transform:uppercase;letter-spacing:.01em}' +
      '#leadModal .lm-sub{color:#272F42;opacity:.65;font-size:14px;margin:0 0 20px;line-height:1.45}' +
      '#leadModal input[type=text],#leadModal input[type=tel]{width:100%;box-sizing:border-box;height:50px;padding:0 14px;margin-bottom:10px;border:1px solid rgba(39,47,66,.25);background:#fff;font-size:15px;font-family:inherit;color:#272F42;border-radius:0}' +
      '#leadModal input:focus{outline:none;border-color:#BB5C3C}' +
      '#leadModal .lm-consent{display:flex;align-items:flex-start;gap:8px;font-size:12px;color:#272F42;opacity:.65;margin:4px 0 16px;cursor:pointer;line-height:1.4}' +
      '#leadModal .lm-submit{width:100%;height:52px;border:0;cursor:pointer;background:#BB5C3C;color:#fff;font-size:16px;letter-spacing:.02em;font-family:inherit;border-radius:0}' +
      '#leadModal .lm-submit:hover{background:#AC5336}' +
      '#leadModal .lm-ok{display:none;padding-top:40px}' +
      '#leadModal.done .lm-form{display:none}' +
      '#leadModal.done .lm-ok{display:block}' +
      /* mobile — hide left panel */
      '@media(max-width:640px){#leadModal .lm-left{display:none}#leadModal .lm-right{padding:36px 24px 32px}}';
    document.head.appendChild(s);

    var m = document.createElement('div'); m.id = 'leadModal'; m.setAttribute('aria-hidden', 'true');
    m.innerHTML =
      '<div class="lm-card" role="dialog" aria-modal="true" aria-label="Оставить заявку">' +
        '<div class="lm-left">' +
          '<div class="lm-brand">' +
            '<img src="/assets/logo-full-light.svg" alt="Белолипцев Владимир">' +
            '<p>Частный риэлтор&#8209;эксперт.<br>Премиум-вторичка ЦАО.<br>23&nbsp;года, 500+ сделок.</p>' +
          '</div>' +
        '</div>' +
        '<div class="lm-right">' +
          '<button class="lm-close" aria-label="Закрыть">&#215;</button>' +
          '<div class="lm-form">' +
            '<h3>Бесплатная консультация</h3>' +
            '<div class="lm-sub">30 минут · без обязательств.<br>Перезвоню лично в течение рабочего дня.</div>' +
            '<input type="text" name="name" placeholder="Как к вам обращаться?" autocomplete="name">' +
            '<input type="tel" name="phone" placeholder="+7 (___) ___-__-__" autocomplete="tel" inputmode="tel">' +
            '<label class="lm-consent"><input type="checkbox" checked> Соглашаюсь с <a href="/politika-konfidentsialnosti/" style="color:inherit;text-decoration:underline">политикой конфиденциальности</a> и обработкой персональных данных.</label>' +
            '<button class="lm-submit" type="button">Отправить заявку</button>' +
          '</div>' +
          '<div class="lm-ok"><h3>Спасибо</h3><div class="lm-sub">Заявка принята — свяжусь с вами лично.</div></div>' +
        '</div>' +
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
