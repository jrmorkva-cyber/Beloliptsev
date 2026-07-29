#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tree-diff.py — детерминированное сравнение двух деревьев сайта.

Зачем: в репозитории два независимо редактируемых дерева — `deploy/` (уезжает
в прод) и `site/src/data` (Astro-порт). Автоматической связи между ними нет,
и они молча разъезжаются: 15 страниц авангарда есть только в site/, 11 страниц
только в deploy/, а формулировка «РГР Топ-3» живёт в 26 файлах site/ при том,
что в проде её сознательно убрали. Ни один из прежних инструментов этого не
видел — они смотрели внутрь одной страницы, а не между деревьями.

Матчинг идёт по НОРМАЛИЗОВАННОМУ canonical-URL, а не по имени файла:
`site/src/data/avangard--dom-melnikova.html` и
`deploy/modernizm/dom-melnikova/index.html` по путям непохожи, а по canonical
сопоставимы. Побочный эффект намеренный — расхождение неймспейсов
/avangard/ vs /modernizm/ становится находкой, а не молчаливым промахом.

Usage:
    python tools/tree-diff.py
    python tools/tree-diff.py --left deploy --right site/src/data
    python tools/tree-diff.py --mode gate --allowlist tools/tree-diff-allowlist.json
    python tools/tree-diff.py --phrase-forbid "РГР Топ-3" --phrase-forbid "РГР Топ-4"
    python tools/tree-diff.py --phrase-drift "аттестованный риэлтор-эксперт"
    python tools/tree-diff.py --only left-only,right-only
    python tools/tree-diff.py --csv tree-diff.csv

Коды возврата:
    0 — ок (в режиме report всегда, в режиме gate — если находок вне allowlist нет)
    1 — гейт не пройден
    2 — ошибка использования / деревья не найдены
"""
import os, re, sys, json, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib.textextract import visible_text  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIR = ("node_modules", ".git", "_astro", ".claude")
EXCLUDE_FILE = ("_sketch", "backup", "animation-demo", "prototype",
                "_mobile-frame", "_hero-palette", "standalone")


# ── извлечение полей ─────────────────────────────────────────────────────────
def canonical_path(html):
    m = (re.search(r'rel="canonical"\s+href="([^"]+)"', html)
         or re.search(r'href="([^"]+)"\s+rel="canonical"', html))
    if not m:
        return None
    url = re.sub(r"^https?://[^/]+", "", m.group(1))
    if not url.startswith("/"):
        url = "/" + url
    if not url.endswith("/"):
        url += "/"
    return url.lower()


def field(html, rx, group=1):
    m = re.search(rx, html, re.S)
    return m.group(group).strip() if m else None


def read_page(path, root):
    html = open(path, encoding="utf-8", errors="ignore").read()
    rel = os.path.relpath(path, root).replace("\\", "/")
    h1 = field(html, r"<h1[^>]*>(.*?)</h1>")
    return {
        "path": rel,
        "canonical": canonical_path(html),
        "title": field(html, r"<title>(.*?)</title>"),
        "desc": field(html, r'<meta\s+name="description"\s+content="([^"]*)"'),
        "h1": re.sub(r"<[^>]+>", " ", h1).strip() if h1 else None,
        "words": len(visible_text(html).split()),
        "html": html,
    }


def collect(root):
    pages = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIR]
        for fn in fns:
            if fn.endswith(".html") and not any(x in fn for x in EXCLUDE_FILE):
                pages.append(read_page(os.path.join(dp, fn), root))
    return pages


# ── сравнение ────────────────────────────────────────────────────────────────
def compare(lp, rp, phrase_drift, word_pct):
    """Возвращает список причин расхождения; пустой список = страницы совпадают."""
    why = []
    for key, label in (("title", "title"), ("desc", "meta description"), ("h1", "h1")):
        if (lp[key] or "") != (rp[key] or ""):
            why.append(f"{label}: «{(lp[key] or '—')[:48]}» ≠ «{(rp[key] or '—')[:48]}»")
    lo, ro = lp["words"], rp["words"]
    if max(lo, ro) and abs(lo - ro) * 100.0 / max(lo, ro) > word_pct:
        why.append(f"объём: {lo} слов ≠ {ro} слов")
    for ph in phrase_drift:
        if (ph in lp["html"]) != (ph in rp["html"]):
            side = "слева" if ph in lp["html"] else "справа"
            why.append(f"фраза «{ph}» только {side}")
    return why


def load_allowlist(path):
    if not path or not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {(e["key"], e.get("side", "")) for e in json.load(fh)}


def argval(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def argall(flag):
    return [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == flag and i + 1 < len(sys.argv)]


def main():
    left_dir = os.path.join(BASE, argval("--left", "deploy"))
    right_dir = os.path.join(BASE, argval("--right", os.path.join("site", "src", "data")))
    mode = argval("--mode", "report")
    word_pct = float(argval("--word-diff-pct", "25"))
    phrase_forbid = argall("--phrase-forbid")
    phrase_drift = argall("--phrase-drift")
    only = set((argval("--only") or "").split(",")) - {""}
    allow = load_allowlist(argval("--allowlist", os.path.join(BASE, "tools", "tree-diff-allowlist.json")))

    for d in (left_dir, right_dir):
        if not os.path.isdir(d):
            print(f"нет дерева: {d}"); return 2

    L, R = collect(left_dir), collect(right_dir)
    if not L and not R:
        print("обе стороны пусты"); return 2

    lmap = {p["canonical"]: p for p in L if p["canonical"]}
    rmap = {p["canonical"]: p for p in R if p["canonical"]}
    no_canon = [("left", p) for p in L if not p["canonical"]] + \
               [("right", p) for p in R if not p["canonical"]]

    rows, left_only, right_only, diffs, ok = [], [], [], [], []
    for key in sorted(set(lmap) | set(rmap)):
        lp, rp = lmap.get(key), rmap.get(key)
        if lp and not rp:
            left_only.append((key, lp)); rows.append((key, "LEFT_ONLY", lp["path"], "", ""))
        elif rp and not lp:
            right_only.append((key, rp)); rows.append((key, "RIGHT_ONLY", "", rp["path"], ""))
        else:
            why = compare(lp, rp, phrase_drift, word_pct)
            if why:
                diffs.append((key, lp, rp, why))
                rows.append((key, "DIFF", lp["path"], rp["path"], " · ".join(why)))
            else:
                ok.append(key); rows.append((key, "OK", lp["path"], rp["path"], ""))

    forbidden = []
    for side, pages in (("left", L), ("right", R)):
        for p in pages:
            for ph in phrase_forbid:
                if ph in p["html"]:
                    forbidden.append((side, p["path"], ph))

    csv_path = argval("--csv")
    if csv_path:
        with open(csv_path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["canonical", "статус", "слева", "справа", "почему"])
            w.writerows(rows)
        print(f"CSV: {csv_path}")

    print(f"=== TREE-DIFF ===\n  слева : {os.path.relpath(left_dir, BASE)} — {len(L)} страниц")
    print(f"  справа: {os.path.relpath(right_dir, BASE)} — {len(R)} страниц\n")
    print(f"  совпадают          {len(ok)}")
    print(f"  только слева       {len(left_only)}")
    print(f"  только справа      {len(right_only)}")
    print(f"  расходятся         {len(diffs)}")
    print(f"  без canonical      {len(no_canon)}")
    if phrase_forbid:
        print(f"  запрещённых фраз   {len(forbidden)}")

    def show(title, items, fmt):
        if not items or (only and title not in only):
            return
        print(f"\n── {title} ──")
        for it in items:
            print(fmt(it))

    show("left-only", left_only, lambda x: f"  ◀ {x[0]:<44} {x[1]['path']}")
    show("right-only", right_only, lambda x: f"  ▶ {x[0]:<44} {x[1]['path']}")
    if diffs and (not only or "diff" in only):
        print("\n── diff ──")
        for key, lp, rp, why in diffs:
            print(f"  ≠ {key}")
            for w in why:
                print(f"      {w}")
    if no_canon and (not only or "no-canonical" in only):
        print("\n── без canonical ──")
        for side, p in no_canon:
            print(f"  ? [{side}] {p['path']}")
    if forbidden:
        print("\n── запрещённые фразы ──")
        for side, path, ph in forbidden:
            print(f"  ✖ [{side}] {path}  «{ph}»")

    if mode != "gate":
        return 0
    blocking = ([x for x in left_only if (x[0], "left_only") not in allow]
                + [x for x in right_only if (x[0], "right_only") not in allow]
                + [x for x in diffs if (x[0], "diff") not in allow])
    fail = len(blocking) + len(forbidden)
    print(f"\n{'❌ ГЕЙТ НЕ ПРОЙДЕН' if fail else '✅ ГЕЙТ ПРОЙДЕН'} — блокирующих находок {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
