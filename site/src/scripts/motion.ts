/* ============================================================================
   motion.ts — порт js/motion.js на Astro-lifecycle (astro:page-load / before-swap).
   Тиры (см. исходный движок Design System v1 §4):
     S1 Lenis smooth-scroll
     S2/S3 IntersectionObserver reveals (.reveal / .mask-reveal / .split-mask)
     A1 счётчики ([data-count]) · A2 диагональные хайрлайны (.divider-diagonal)
     A3 каскад сеток (.reveal-stagger > *) · B2 магнитные CTA (.btn--magnetic)
     B3 параллакс (.parallax-y · data-speed)
   prefers-reduced-motion / ?motion=off → reveals показываются сразу, A/B выключены.
   GSAP-сигнатуры (SplitText / ScrollTrigger) подключаются отдельным модулем.
   ----------------------------------------------------------------------------
   View-Transitions-safe: per-страничные слушатели через AbortController,
   рубятся на astro:before-swap; Lenis создаётся один раз (глобальный smooth-scroll).
   ========================================================================== */
import Lenis from 'lenis';

const PRM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const isCoarse = window.matchMedia('(pointer: coarse)').matches;
const motionLevel = new URLSearchParams(location.search).get('motion') || 'full'; // full | reduced | off

let lenis: Lenis | null = null;
let perPage: AbortController | null = null;
let observers: IntersectionObserver[] = [];

// ── S1. Lenis (один раз) ─────────────────────────────────────────────────────
function initLenis(): void {
  if (PRM || motionLevel !== 'full' || lenis) return;
  lenis = new Lenis({
    duration: 1.2,
    easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
  });
  const raf = (time: number) => {
    lenis?.raf(time);
    requestAnimationFrame(raf);
  };
  requestAnimationFrame(raf);
}

// ── S2 + S3 + A3. Reveals ────────────────────────────────────────────────────
function initReveals(): void {
  if (motionLevel === 'off') {
    document
      .querySelectorAll('.reveal, .mask-reveal, .split-mask, .reveal-stagger > *')
      .forEach((el) => el.classList.add('is-in'));
    return;
  }
  document.querySelectorAll<HTMLElement>('.reveal-stagger').forEach((container) => {
    const stride = parseInt(container.dataset.stride || '90', 10);
    const start = parseInt(container.dataset.start || '0', 10);
    Array.from(container.children).forEach((child, i) => {
      child.classList.add('reveal');
      (child as HTMLElement).style.transitionDelay = `${start + i * stride}ms`;
    });
  });

  const all = Array.from(
    document.querySelectorAll<HTMLElement>('.reveal, .mask-reveal, .split-mask'),
  );
  const vh = window.innerHeight || document.documentElement.clientHeight;
  // На загрузке: то, что уже в экране — показываем сразу (без гонки со скриншотом).
  all.forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.top < vh && r.bottom > 0) el.classList.add('is-in');
  });
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    },
    { rootMargin: '0px 0px -8% 0px', threshold: 0.06 },
  );
  all.forEach((el) => {
    if (!el.classList.contains('is-in')) io.observe(el);
  });
  observers.push(io);
}

// ── A1. Счётчики ─────────────────────────────────────────────────────────────
function initCounters(): void {
  const counters = Array.from(document.querySelectorAll<HTMLElement>('[data-count]'));
  if (motionLevel === 'off' || PRM) {
    counters.forEach((el) => {
      el.textContent = el.getAttribute('data-count');
    });
    return;
  }
  const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
  const animate = (el: HTMLElement) => {
    const target = parseFloat(el.getAttribute('data-count') || '0');
    const duration = parseInt(el.getAttribute('data-duration') || '1800', 10);
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const v = target * easeOut(t);
      el.textContent = Number.isInteger(target)
        ? Math.round(v).toLocaleString('ru-RU')
        : v.toFixed(1);
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          animate(e.target as HTMLElement);
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.4 },
  );
  const vh = window.innerHeight || document.documentElement.clientHeight;
  counters.forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.top < vh && r.bottom > 0) animate(el);
    else io.observe(el);
  });
  observers.push(io);
}

// ── Состояние шапки при прокрутке ────────────────────────────────────────────
function initNavScroll(signal: AbortSignal): void {
  const nav = document.querySelector('.nav');
  if (!nav) return;
  const onScroll = () => nav.classList.toggle('nav--scrolled', window.scrollY > 80);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true, signal });
}

// ── B2. Магнитные CTA ────────────────────────────────────────────────────────
function initMagnetic(signal: AbortSignal): void {
  if (motionLevel !== 'full' || PRM || isCoarse) return;
  document.querySelectorAll<HTMLElement>('.btn--magnetic').forEach((btn) => {
    const strength = parseFloat(btn.dataset.magnetic || '0.28');
    btn.addEventListener(
      'mousemove',
      (e) => {
        const r = btn.getBoundingClientRect();
        const x = (e.clientX - (r.left + r.width / 2)) * strength;
        const y = (e.clientY - (r.top + r.height / 2)) * strength;
        btn.style.transform = `translate(${x}px, ${y}px)`;
      },
      { signal },
    );
    btn.addEventListener('mouseleave', () => { btn.style.transform = ''; }, { signal });
  });
}

// ── B3. Параллакс ────────────────────────────────────────────────────────────
function initParallax(signal: AbortSignal): void {
  if (motionLevel !== 'full' || PRM) return;
  const els = Array.from(document.querySelectorAll<HTMLElement>('.parallax-y')).map((el) => ({
    el,
    speed: parseFloat(el.dataset.speed || '0.15'),
    baseTop: el.getBoundingClientRect().top + window.scrollY,
  }));
  if (!els.length) return;
  let ticking = false;
  const update = () => {
    const y = window.scrollY;
    const vh = window.innerHeight;
    els.forEach(({ el, speed, baseTop }) => {
      const delta = (y + vh / 2 - baseTop) * speed;
      el.style.transform = `translate3d(0, ${delta * -1}px, 0)`;
    });
    ticking = false;
  };
  window.addEventListener(
    'scroll',
    () => {
      if (!ticking) {
        requestAnimationFrame(update);
        ticking = true;
      }
    },
    { passive: true, signal },
  );
  update();
}

// ── A2. Диагональные хайрлайны ───────────────────────────────────────────────
function initDiagonal(): void {
  const els = document.querySelectorAll('.divider-diagonal');
  if (motionLevel === 'off' || PRM) {
    els.forEach((el) => el.classList.add('is-in'));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.5 },
  );
  els.forEach((el) => io.observe(el));
  observers.push(io);
}

// ── Tweak-relay (дев-панель design-canvas) — одноразовый слушатель ───────────
window.addEventListener('message', (e: MessageEvent) => {
  const d = e.data;
  if (!d || typeof d !== 'object' || d.type !== '__belolipcev_tweaks') return;
  const root = document.documentElement;
  Object.entries(d.vars || {}).forEach(([k, v]) => root.style.setProperty(k, String(v)));
  if (d.motion) root.dataset.motion = String(d.motion);
});

// ── Lifecycle ────────────────────────────────────────────────────────────────
function resetPerPage(): void {
  perPage?.abort();
  observers.forEach((o) => o.disconnect());
  observers = [];
}

function boot(): void {
  resetPerPage();
  perPage = new AbortController();
  const { signal } = perPage;
  initLenis();
  initReveals();
  initCounters();
  initNavScroll(signal);
  initMagnetic(signal);
  initParallax(signal);
  initDiagonal();
}

document.addEventListener('astro:page-load', boot);
document.addEventListener('astro:before-swap', resetPerPage);
