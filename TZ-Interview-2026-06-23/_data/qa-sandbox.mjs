// qa-sandbox.mjs — ВИРТУАЛИЗАЦИЯ: копирует src/data в изолированную песочницу, прогоняет
// безопасные сквозные замены и проверяет, что разметка не ломается (баланс тегов) и цели
// вычищены. РЕАЛЬНЫЙ src НЕ ТРОГАЕТСЯ. Запуск: node _data/qa-sandbox.mjs
import { readFileSync, writeFileSync, readdirSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = 'C:/Users/dataris 2/cowork/NICK-DAVID-AI-SEO-DEV/DAN COWORK/БЕЛОПИЛЕЦЕВ/01-Site/Белолипцев (2)/Белолипцев/astro/src/data';
const SB = join(ROOT, '_data', '_sandbox');
if (existsSync(SB)) rmSync(SB, { recursive: true, force: true });
mkdirSync(SB, { recursive: true });

// безопасные сквозные замены (naive — год/рейтинг, без падежей)
const SWEEPS = [
  { name: '2003 → 2004', find: /2003/g, repl: '2004' },
  { name: 'Топ-4 → Топ-3 (в траст-строках)', find: /(Топ|топ|ТОП)([\s\-–—  ]?)4/g, repl: '$1$23' },
];

const files = readdirSync(SRC).filter(f => f.endsWith('.html'));
let totReplaced = 0, brokeMarkup = 0, leftover = 0;
const rows = [];
for (const f of files) {
  let html = readFileSync(join(SRC, f), 'utf8');
  const ltBefore = (html.match(/</g) || []).length, gtBefore = (html.match(/>/g) || []).length;
  let replaced = 0;
  for (const s of SWEEPS) { const n = (html.match(s.find) || []).length; html = html.replace(s.find, s.repl); replaced += n; }
  // валидация
  const ltAfter = (html.match(/</g) || []).length, gtAfter = (html.match(/>/g) || []).length;
  const tagsOk = (ltBefore === ltAfter && gtBefore === gtAfter);
  const stillHas2003 = /2003/.test(html);
  if (!tagsOk) brokeMarkup++;
  if (stillHas2003) leftover++;
  totReplaced += replaced;
  writeFileSync(join(SB, f), html, 'utf8');
  if (replaced > 0) rows.push(`  ${f.padEnd(42)} замен:${String(replaced).padStart(3)}  теги:${tagsOk ? 'OK' : 'СЛОМАНЫ!'}  2003-остаток:${stillHas2003 ? 'ДА!' : 'нет'}`);
}
console.log('=== ВИРТУАЛИЗАЦИЯ: сквозные замены в песочнице (прод не тронут) ===\n');
rows.forEach(r => console.log(r));
console.log(`\nВсего замен: ${totReplaced}. Файлов с поломанной разметкой: ${brokeMarkup}. С остатком «2003»: ${leftover}.`);
console.log(`Песочница: _data/_sandbox/ (${files.length} файлов). Реальный src/data НЕ изменялся.`);
console.log(brokeMarkup === 0 && leftover === 0
  ? '\n✅ ВЕРДИКТ: сквозные замены применяются чисто, разметка цела, цели вычищены.'
  : '\n⚠️ ВЕРДИКТ: есть проблемы — см. строки выше.');
