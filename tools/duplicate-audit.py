#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
duplicate-audit.py — поиск копипаста ПРОЗЫ между страницами раздела.

Зачем: 15 страниц зданий с одинаковым скелетом, написанных быстро одним
конвейером, — ровно тот профиль, который ловят Проксима (детектор AI-контента)
и Баден-Баден. Одностраничный гейт этого не видит в принципе: каждая страница
по отдельности безупречна, а вместе они штампованные.

Скрипт сравнивает прозу секций между всеми парами страниц через
difflib.SequenceMatcher и показывает пары выше порога схожести с конкретным
совпавшим фрагментом — чтобы правка была адресной, а не «перепиши всё».

Usage:
    python tools/duplicate-audit.py deploy
    python tools/duplicate-audit.py deploy --filter modernizm --threshold 0.55
    python tools/duplicate-audit.py deploy --gate        # exit 1 при находках

Коды возврата: 0 — ок · 1 — есть пары выше порога (только с --gate) · 2 — ошибка.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib.textextract import visible_text  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIR = ("node_modules", ".git", "_astro", ".claude", "deka", "otchet")
DEFAULT_THRESHOLD = 0.30   # доля: одна страница почти целиком внутри другой
DEFAULT_MIN_SHARED = 60    # абсолют: ~60 общих окон ≈ скопированный абзац
MIN_WORDS = 40             # короткие служебные страницы не сравниваем
K = 8                      # длина шингла в словах

# Шапка, подвал и мегаменю одинаковы на всех страницах по определению —
# сравниваем только содержательные секции.
SECTIONS = re.compile(r'data-screen-label="([^"]*)"(.*?)(?=data-screen-label=|<footer|\Z)', re.S)
# «Связанные объекты» — блок перекрёстных ссылок: он ОБЯЗАН быть похожим между
# страницами, это навигация, а не проза. Считать его штампом — ложный сигнал.
BOILERPLATE = re.compile(r"^(?:S\d+\s*·\s*)?(header|footer|CTA|Карта|Связанные|Смотри также)", re.I)


def page_prose(html):
    """Проза содержательных секций, без шапки/подвала/CTA/карты."""
    chunks = []
    for label, body in SECTIONS.findall(html):
        if BOILERPLATE.match(label.strip()):
            continue
        chunks.append(visible_text(body))
    if not chunks:                       # страница без разметки секций — берём всё
        chunks = [visible_text(html)]
    return re.sub(r"\s+", " ", " ".join(chunks)).strip()


def page_id(path, root):
    rel = os.path.relpath(path, root).replace("\\", "/")
    return rel[:-len("/index.html")] if rel.endswith("/index.html") else rel[:-5]


def shingles(prose):
    """Множество K-словных окон. Копипаст даёт идентичные окна, пересказ — нет."""
    w = prose.lower().split()
    return {" ".join(w[i:i + K]) for i in range(max(0, len(w) - K + 1))}


def collect(root, flt):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIR]
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dp, fn)
            pid = page_id(p, root)
            if flt and flt not in pid:
                continue
            prose = page_prose(open(p, encoding="utf-8", errors="ignore").read())
            if len(prose.split()) >= MIN_WORDS:
                out.append((pid, prose, shingles(prose)))
    return sorted(out)


def longest_run(prose, shared):
    """Самая длинная непрерывная цепочка совпавших шинглов — что именно скопировано."""
    w = prose.split()
    best_i = best_len = cur_i = cur_len = 0
    for i in range(max(0, len(w) - K + 1)):
        if " ".join(w[i:i + K]).lower() in shared:
            if cur_len == 0:
                cur_i = i
            cur_len += 1
            if cur_len > best_len:
                best_len, best_i = cur_len, cur_i
        else:
            cur_len = 0
    return " ".join(w[best_i:best_i + best_len + K - 1]) if best_len else ""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = os.path.join(BASE, args[0]) if args else os.path.join(BASE, "deploy")
    gate = "--gate" in sys.argv
    flt = sys.argv[sys.argv.index("--filter") + 1] if "--filter" in sys.argv else None
    thr = float(sys.argv[sys.argv.index("--threshold") + 1]) if "--threshold" in sys.argv else DEFAULT_THRESHOLD
    min_shared = int(sys.argv[sys.argv.index("--min-shared") + 1]) if "--min-shared" in sys.argv else DEFAULT_MIN_SHARED

    if not os.path.isdir(root):
        print(f"нет дерева: {root}"); return 2
    pages = collect(root, flt)
    if len(pages) < 2:
        print(f"нечего сравнивать: {len(pages)} страниц"); return 2

    print(f"=== DUPLICATE-AUDIT: {len(pages)} страниц · доля ≥{thr} или общих окон ≥{min_shared}"
          f" · {os.path.relpath(root, BASE)}{' · фильтр ' + flt if flt else ''} ===\n")

    hits = []
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            (ida, a, sa), (idb, b, sb) = pages[i], pages[j]
            shared = sa & sb
            if not shared:
                continue
            # Два независимых сигнала. Доля (containment, а не Jaccard) ловит
            # «страница целиком вклеена в другую». Абсолют ловит скопированный
            # абзац: на странице в 1300 слов общий абзац даёт долю всего 0.16,
            # но это ровно тот штамп, из-за которого раздел выглядит нагенеренным.
            ratio = len(shared) / max(1, min(len(sa), len(sb)))
            if ratio >= thr or len(shared) >= min_shared:
                hits.append((ratio, len(shared), ida, idb, longest_run(a, shared)))

    for ratio, nshared, ida, idb, frag in sorted(hits, key=lambda x: -x[1]):
        print(f"  ⚠️  общих окон {nshared:>4} · доля {ratio:.2f}   {ida}  ↔  {idb}")
        if frag:
            print(f"        «{frag[:190]}…»")
    print(f"\n=== пар выше порога: {len(hits)} ===")
    if not hits:
        print("✅ штампованных страниц не найдено")
    return 1 if (hits and gate) else 0


if __name__ == "__main__":
    sys.exit(main())
