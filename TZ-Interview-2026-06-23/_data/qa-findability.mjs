// qa-findability.mjs — READ-ONLY QA: для каждой контентной правки проверяет, что её цель
// реально есть в целевом кодабейзе (src/data/*.html) → ТЗ исполнимо. Прод НЕ трогается.
// Запуск: node _data/qa-findability.mjs
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const SRC = 'C:/Users/dataris 2/cowork/NICK-DAVID-AI-SEO-DEV/DAN COWORK/БЕЛОПИЛЕЦЕВ/01-Site/Белолипцев (2)/Белолипцев/astro/src/data';
const files = readdirSync(SRC).filter(f => f.endsWith('.html'));
const docs = files.map(f => ({ f, t: readFileSync(join(SRC, f), 'utf8') }));

// проба: { id, re, safety }  safety: naive=безопасная замена | case=нужны падежи/регистр | visual=нет текст-якоря, сверять по кадру
const probes = [
  { id: 'G01', re: /2003/g, safety: 'naive' },
  { id: 'G02', re: /Владимир\s+Белолипцев/gi, safety: 'case' },
  { id: 'G03', re: /₽/g, safety: 'case' },
  { id: 'G04', re: /(РГР[^<]{0,8})?(Топ|топ)[\s\-–—]?4/g, safety: 'naive' },
  { id: 'G05', re: /брокер/gi, safety: 'case' },
  { id: 'H01', re: /коллег/gi, safety: 'case' },
  { id: 'H04', re: /верифиц|30[\s\S]{0,12}сек/gi, safety: 'naive' },
  { id: 'H05', re: /сест[её]р/gi, safety: 'naive' },
  { id: 'H06', re: /сегмент/gi, safety: 'case' },
  { id: 'H08', re: /под\s*ключ|под&nbsp;ключ/gi, safety: 'naive' },
  { id: 'U02', re: /премиум[\s\S]{0,8}объект/gi, safety: 'naive' },
  { id: 'U03', re: /\b2[.,]?5?\s*%|два\s+процент/gi, safety: 'case' },
  { id: 'U04', re: /бер[ёе]т/gi, safety: 'naive' },
  { id: 'U08', re: /сосед/gi, safety: 'case' },
  { id: 'V05', re: /пентхаус/gi, safety: 'naive' },
  { id: 'V08', re: /культурн[\s\S]{0,6}насле|ОКН/gi, safety: 'case' },
  { id: 'P01', re: /революцион/gi, safety: 'case' },
];

console.log('=== QA findability (read-only) — цель правки есть в src/data? ===\n');
let actionable = 0, missing = 0;
const report = [];
for (const p of probes) {
  let total = 0; const hits = [];
  for (const d of docs) { const m = d.t.match(p.re); if (m) { total += m.length; hits.push(`${d.f}:${m.length}`); } }
  const ok = total > 0;
  if (ok) actionable++; else missing++;
  const mark = ok ? '✅' : '⚠️ НЕ НАЙДЕНО';
  console.log(`${mark} ${p.id}  ${String(total).padStart(3)} вхожд. [${p.safety}]  ${hits.slice(0, 4).join(', ')}`);
  report.push({ id: p.id, total, safety: p.safety, files: hits.length, ok });
}
console.log(`\nИтог: ${actionable} правок исполнимы (цель найдена), ${missing} требуют ручной сверки по кадру.`);
console.log('Визуальные/структурные правки (justify, ховер, параллакс, поп-ап, симметрия, хедер, контакты-в-подвал) текст-якоря не имеют — сверять по кадрам, не грепом.');
