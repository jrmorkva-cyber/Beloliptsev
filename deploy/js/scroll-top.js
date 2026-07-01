(function(){
  var btn=document.querySelector('.st-scroll-top');
  if(!btn)return;
  function upd(){btn.classList.toggle('visible',window.scrollY>300);}
  window.addEventListener('scroll',upd,{passive:true});
  btn.addEventListener('click',function(e){
    e.preventDefault();
    window.scrollTo({top:0,behavior:'smooth'});
  });
  upd();
})();