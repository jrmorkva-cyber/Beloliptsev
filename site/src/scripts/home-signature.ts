/* home-signature.ts — сигнатурная анимация ТОЛЬКО главной (трек 2).
   Сдержанно (motion ≤3/5, редакторский easeOut, без баунса):
     1. Геро-H1 (.hero100__h1) — SplitText по буквам, появление снизу, мягкий stagger.
        Запуск ПОСЛЕ document.fonts.ready (иначе SplitText режет не те глифы — Anticva).
     2. Лёгкая параллакс-сцена: фон геро (.hero100__bg) чуть смещается на прокрутке (scrub).
   SEO/PRM-safe: текст H1 остаётся в статичном HTML (Яндекс видит), скрытие — только через
   GSAP autoAlpha на клиенте; prefers-reduced-motion → анимаций нет, контент сразу.
   Lenis на главной нет (1:1-порт) → ScrollTrigger на нативном скролле. */
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { SplitText } from 'gsap/SplitText';

gsap.registerPlugin(ScrollTrigger, SplitText);

let mm: ReturnType<typeof gsap.matchMedia> | null = null;
let splits: SplitText[] = [];

function cleanup() {
  splits.forEach((s) => s.revert());
  splits = [];
  mm?.revert();
  mm = null;
}

function init() {
  cleanup();
  mm = gsap.matchMedia();

  mm.add('(prefers-reduced-motion: no-preference)', () => {
    // Параллакс фона геро (десктоп-геро .hero100; на мобиле скрыт → триггер не сработает)
    const bg = document.querySelector('.hero100__bg');
    const hero = document.querySelector('.hero100');
    if (bg && hero) {
      gsap.to(bg, {
        yPercent: 10,
        ease: 'none',
        scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true },
      });
    }

    // SplitText геро-H1 — после загрузки шрифтов
    const h1 = document.querySelector<HTMLElement>('.hero100__h1');
    if (h1) {
      document.fonts.ready.then(() => {
        if (!mm || getComputedStyle(h1).display === 'none') return; // мобайл/после-свап — пропуск
        const split = new SplitText(h1, { type: 'chars,words' });
        splits.push(split);
        gsap.set(h1, { autoAlpha: 1 });
        gsap.from(split.chars, {
          yPercent: 110,
          autoAlpha: 0,
          duration: 0.62,
          ease: 'power3.out',
          stagger: 0.016,
        });
        ScrollTrigger.refresh();
      });
    }
  });
}

document.addEventListener('astro:page-load', init);
document.addEventListener('astro:before-swap', cleanup);
