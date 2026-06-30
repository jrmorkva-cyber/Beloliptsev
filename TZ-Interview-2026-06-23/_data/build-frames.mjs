// build-frames.mjs — для каждой правки из edits.json режет кадр экрана из видео интервью
// по её таймкоду (srt-сегмент == строка-якорь) + строит индекс таймкодов.
// srt-сегмент N соответствует строке N в .final.txt (1:1). Запуск: node _data/build-frames.mjs
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(readFileSync(join(ROOT, '_data/edits.json'), 'utf8'));
const VIDEO = data.meta.source_video;
const SRT = data.meta.source_srt;
const SHOTS = join(ROOT, 'screenshots');
if (!existsSync(SHOTS)) mkdirSync(SHOTS, { recursive: true });

// --- парс srt в {segNum: {tc, sec}} ---
const srt = readFileSync(SRT, 'utf8').split(/\r?\n/);
const seg = {};
for (let i = 0; i < srt.length; i++) {
  if (/^\d+$/.test(srt[i].trim()) && /-->/.test(srt[i + 1] || '')) {
    const n = parseInt(srt[i].trim(), 10);
    const m = srt[i + 1].match(/(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/);
    if (m) {
      const sec = (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]) + (+m[4]) / 1000;
      seg[n] = { tc: `${m[1]}:${m[2]}:${m[3]}.${m[4]}`, sec };
    }
  }
}
function tcForLine(line) {
  if (seg[line]) return seg[line];
  // ближайший сегмент ≤ line
  let best = null;
  for (let k = line; k >= 1; k--) { if (seg[k]) { best = seg[k]; break; } }
  return best || seg[1];
}
function hhmmss(sec) {
  const h = String(Math.floor(sec / 3600)).padStart(2, '0');
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
  const s = String(Math.floor(sec % 60)).padStart(2, '0');
  return `${h}:${m}:${s}`;
}

const rows = [];
let ok = 0, fail = 0;
for (const e of data.edits) {
  const t = tcForLine(e.line);
  const out = join(SHOTS, `${e.id}-${e.screen}.jpg`);
  try {
    execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-ss', t.tc, '-i', VIDEO,
      '-frames:v', '1', '-q:v', '3', out, '-y'], { stdio: 'pipe' });
    ok++;
    console.log(`✓ ${e.id.padEnd(4)} ${hhmmss(t.sec)}  ${e.screen.padEnd(14)} ${e.title.slice(0, 46)}`);
  } catch (err) {
    fail++;
    console.log(`✗ ${e.id} кадр не вышел: ${String(err).slice(0, 80)}`);
  }
  rows.push(`| ${e.id} | ${e.priority} | ${hhmmss(t.sec)} | ${e.screen} | ${e.title} | ${e.id}-${e.screen}.jpg |`);
}

// --- индекс таймкодов ---
const md = `# Индекс правок ↔ таймкоды видео ↔ кадры\n\n` +
  `Видео: \`${VIDEO}\`\n\nДлительность: ${hhmmss(data.meta.duration_sec)}. Таймкод = момент реплики в записи. Кадр = экран в эту секунду.\n\n` +
  `| ID | Приор. | Таймкод | Экран | Правка | Кадр |\n|---|---|---|---|---|---|\n` +
  rows.join('\n') + '\n';
writeFileSync(join(ROOT, 'transcript', 'timecodes.md'), md, 'utf8');
console.log(`\nКадров: ${ok} ок, ${fail} ошибок. Индекс → transcript/timecodes.md`);
