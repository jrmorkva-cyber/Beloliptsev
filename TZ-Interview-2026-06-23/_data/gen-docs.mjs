// gen-docs.mjs — генерит человекочитаемое ТЗ из edits.json (+ таймкоды из srt).
// Эмитит 01-TZ-MASTER.md и 03-edits-by-screen/<screen>.md. Запуск: node _data/gen-docs.mjs
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(readFileSync(join(ROOT, '_data/edits.json'), 'utf8'));

// таймкоды из srt
const srt = readFileSync(data.meta.source_srt, 'utf8').split(/\r?\n/);
const seg = {};
for (let i = 0; i < srt.length; i++) {
  if (/^\d+$/.test(srt[i].trim()) && /-->/.test(srt[i + 1] || '')) {
    const n = +srt[i].trim();
    const m = srt[i + 1].match(/(\d{2}):(\d{2}):(\d{2})/);
    if (m) seg[n] = `${m[1]}:${m[2]}:${m[3]}`;
  }
}
const tc = (line) => { for (let k = line; k >= 1; k--) if (seg[k]) return seg[k]; return '00:00:00'; };

const SCREENS = [
  ['GLOBAL', 'СКВОЗНЫЕ (применять на ВСЕХ страницах)'],
  ['glavnaya', 'ГЛАВНАЯ'],
  ['vysotki-hub', 'ВЫСОТКИ — хаб'],
  ['vysotki-doma', 'ВЫСОТКИ — страницы домов'],
  ['modernizm', 'МОДЕРНИЗМ'],
  ['uslugi', 'УСЛУГИ'],
  ['o-sebe', 'О СЕБЕ'],
  ['stalinki', 'СТАЛИНКИ'],
  ['cao-rayony', 'ЦАО / РАЙОНЫ'],
  ['footer', 'ПОДВАЛ'],
];
const PR = { P0: '🔴 P0', P1: '🟡 P1', P2: '🟢 P2' };

function renderEdit(e) {
  return `#### ${PR[e.priority]} · \`${e.id}\` — ${e.title}\n` +
    `- **Что:** ${e.change}\n` +
    `- **Почему:** ${e.why}\n` +
    `- **Тайм-код:** ⏱ ${tc(e.line)} · **Кадр:** \`screenshots/${e.id}-${e.screen}.jpg\` · _${e.confidence}_\n`;
}

const byScreen = {};
for (const e of data.edits) (byScreen[e.screen] ||= []).push(e);
const order = { P0: 0, P1: 1, P2: 2 };
for (const k in byScreen) byScreen[k].sort((a, b) => order[a.priority] - order[b.priority]);

// ---- 01-TZ-MASTER.md ----
const counts = data.edits.reduce((a, e) => (a[e.priority]++, a), { P0: 0, P1: 0, P2: 0 });
let m = `# ТЗ — правки сайта Белолипцева по интервью 23.06.2026\n\n` +
  `> Источник: видео-созвон с клиентом (Владимир Белолипцев) + расшифровка. Каждая правка привязана к тайм-коду записи и кадру экрана в этот момент.\n\n` +
  `**Всего правок: ${data.edits.length}** — ${counts.P0} × 🔴 P0, ${counts.P1} × 🟡 P1, ${counts.P2} × 🟢 P2.\n\n` +
  `## Легенда\n- 🔴 **P0** — контент/SEO/баг, в первую очередь. 🟡 **P1** — визуал/вёрстка/UX. 🟢 **P2** — на будущее / сперва проверить SEO-вес.\n` +
  `- _verbatim_ — дословная просьба клиента; _interpreted_ — восстановлено из контекста (возможен шум расшифровки → перепроверить по кадру).\n\n` +
  `## Целевой кодабейз\n` +
  `На записи клиент в основном разбирал версию на \`astro-seven-delta.vercel.app\` (PortedPage-копия: \`01-Site/Белолипцев (2)/Белолипцев/astro/\`). Правки применять туда. ⚠️ На проекте есть вторая копия (\`01-Site-Astro/\`, компонентная) — НЕ деплоить из неё параллельно (перебивает прод). Финальный канон подтвердить у Ника.\n\n` +
  `## Сводка по приоритету (что делать первым)\n\n| ID | Приор. | Экран | Правка |\n|---|---|---|---|\n` +
  data.edits.slice().sort((a, b) => order[a.priority] - order[b.priority] || a.id.localeCompare(b.id))
    .map(e => `| \`${e.id}\` | ${PR[e.priority]} | ${e.screen} | ${e.title} |`).join('\n') + '\n\n---\n\n';

for (const [key, label] of SCREENS) {
  if (!byScreen[key]?.length) continue;
  m += `## ${label}\n\n` + byScreen[key].map(renderEdit).join('\n') + '\n---\n\n';
}
writeFileSync(join(ROOT, '01-TZ-MASTER.md'), m, 'utf8');

// ---- 03-edits-by-screen/<screen>.md ----
const dir = join(ROOT, '03-edits-by-screen');
if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
let idx = 1;
for (const [key, label] of SCREENS) {
  if (!byScreen[key]?.length) continue;
  const fname = `${String(idx).padStart(2, '0')}-${key}.md`;
  const body = `# ${label}\n\nПравок: ${byScreen[key].length}. Кадры — в \`../screenshots/\`.\n\n` +
    byScreen[key].map(renderEdit).join('\n');
  writeFileSync(join(dir, fname), body, 'utf8');
  idx++;
}
console.log(`01-TZ-MASTER.md + ${idx - 1} файлов по экранам сгенерированы (${data.edits.length} правок).`);
