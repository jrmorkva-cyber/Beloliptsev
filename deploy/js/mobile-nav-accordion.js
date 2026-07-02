/* Мобильное меню-оверлей (#overlay .mega) и подвал (.st-foot__cols) —
   на ≤760px превращаем колонки в аккордеон вместо тесной 2-колоночной
   сетки/обрезанного текста. Десктоп (>760px) не трогаем: разметка
   переставляется в те же обёртки, но спецстили аккордеона живут только
   внутри @media(max-width:760px), поэтому на десктопе визуально ничего
   не меняется. Раскрытие — через max-height (JS считает scrollHeight),
   а не grid-template-rows: 0fr/1fr — в связке #overlay(flex, margin:auto 0
   на .mega) вложенный grid-трюк не разворачивался ни при какой специфичности. */
(function(){
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }

  ready(function(){
    var css = ''
      + '#overlay .mega-chev,.st-foot__cols .ft-chev{display:none}'
      + '@media (max-width:760px){'
      +   '#overlay{padding:20px 22px 32px!important}'
      +   '#overlay .mega{display:block!important;margin:16px 0 0!important;width:auto!important}'
      +   '#overlay .mega-col{border-top:1px solid rgba(237,236,235,.18)}'
      +   '#overlay .mega-col:last-child{border-bottom:1px solid rgba(237,236,235,.18)}'
      +   '#overlay .mega-row{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:18px 0}'
      +   '#overlay .mega-h{min-height:0!important;margin:0!important;font-size:19px!important}'
      +   '#overlay .mega-chev{display:flex;align-items:center;justify-content:center;flex:none;width:14px;height:14px;position:relative;background:none;border:0;padding:12px;margin:-12px;cursor:pointer;appearance:none;-webkit-appearance:none}'
      +   '#overlay .mega-chev::before,#overlay .mega-chev::after{content:"";position:absolute;background:#BB5C3C;transition:transform .3s ease}'
      +   '#overlay .mega-chev::before{left:12px;top:18px;width:14px;height:2px}'
      +   '#overlay .mega-chev::after{left:18px;top:12px;width:2px;height:14px}'
      +   '#overlay .mega-col.is-open .mega-chev::after{transform:scaleY(0)}'
      +   '#overlay .mega-sub{overflow:hidden;max-height:0;transition:max-height .4s cubic-bezier(.22,.61,.36,1)}'
      +   '#overlay .mega-s{display:block!important;margin-top:0!important;padding:6px 0!important;font-size:15px!important;line-height:1.6!important}'
      +   '#overlay .mega-sub>.mega-s:last-child{padding-bottom:16px!important}'
      +   '#overlay .mega-sep{display:none!important}'
      +   '.st-foot__cols{display:block!important;margin-top:8px!important}'
      +   '.st-foot__cols>div{border-top:1px solid rgba(237,236,235,.18)}'
      +   '.st-foot__cols>div:last-child{border-bottom:1px solid rgba(237,236,235,.18)}'
      +   '.st-foot__cols .ft-row{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:18px 0;cursor:pointer}'
      +   '.st-foot__cols h4{margin:0!important}'
      +   '.st-foot__cols .ft-chev{display:flex;align-items:center;justify-content:center;flex:none;width:14px;height:14px;position:relative;background:none;border:0;padding:12px;margin:-12px;cursor:pointer;appearance:none;-webkit-appearance:none}'
      +   '.st-foot__cols .ft-chev::before,.st-foot__cols .ft-chev::after{content:"";position:absolute;background:#BB5C3C;transition:transform .3s ease}'
      +   '.st-foot__cols .ft-chev::before{left:12px;top:18px;width:14px;height:2px}'
      +   '.st-foot__cols .ft-chev::after{left:18px;top:12px;width:2px;height:14px}'
      +   '.st-foot__cols>div.is-open .ft-chev::after{transform:scaleY(0)}'
      +   '.st-foot__cols .ft-sub{overflow:hidden;max-height:0;transition:max-height .4s cubic-bezier(.22,.61,.36,1)}'
      +   '.st-foot__cols a{display:block!important;margin-bottom:0!important;padding:6px 0!important}'
      +   '.st-foot__cols .ft-sub>a:last-child{padding-bottom:16px!important}'
      + '}';
    var styleEl = document.createElement('style');
    styleEl.textContent = css;
    document.head.appendChild(styleEl);

    function toggle(col, sub){
      var open = col.classList.toggle('is-open');
      sub.style.maxHeight = open ? (sub.scrollHeight + 'px') : '0px';
    }

    function makeAccordion(col, headingSelector, rowClass, chevClass, subClass, chevLabel){
      var h = col.querySelector(headingSelector);
      if(!h) return;
      var rest = Array.prototype.slice.call(col.children).filter(function(el){ return el!==h; });
      if(!rest.length) return;
      var row = document.createElement('div'); row.className = rowClass;
      h.parentNode.insertBefore(row, h);
      row.appendChild(h);
      var chev = document.createElement('button');
      chev.type = 'button'; chev.className = chevClass;
      if(chevLabel) chev.setAttribute('aria-label', chevLabel);
      row.appendChild(chev);
      var sub = document.createElement('div'); sub.className = subClass;
      rest.forEach(function(el){ sub.appendChild(el); });
      col.appendChild(sub);
      chev.addEventListener('click', function(){ toggle(col, sub); });
    }

    document.querySelectorAll('#overlay .mega-col').forEach(function(col){
      makeAccordion(col, '.mega-h', 'mega-row', 'mega-chev', 'mega-sub', 'Показать список');
    });
    document.querySelectorAll('.st-foot__cols > div').forEach(function(col){
      makeAccordion(col, 'h4', 'ft-row', 'ft-chev', 'ft-sub', 'Показать список');
    });

    // при ресайзе с мобильного на десктоп и обратно снимаем инлайновый max-height,
    // чтобы десктопная раскладка не унаследовала «залипший» px-хайт с мобилки
    var mq = window.matchMedia('(max-width:760px)');
    function clearInlineMaxHeight(){
      document.querySelectorAll('.mega-sub, .ft-sub').forEach(function(el){ el.style.maxHeight=''; });
    }
    if (mq.addEventListener) mq.addEventListener('change', clearInlineMaxHeight);
  });
})();
