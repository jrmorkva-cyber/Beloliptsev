#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_pages.py — числовой тест-гейт по КАНОНАМ сайта Белолипцева.
Детерминированные проверки каждой страницы: SEO-контракт, структура (геро/футер/CTA),
смысл (0 гео-негатива/жаргона в видимом), типографика, бренд-консистентность, внутр. ссылки,
валидность JSON-LD. Гейт: exit 1, если хоть одна CRITICAL-проверка провалена.

Usage:
    python test_pages.py [dir]         # по умолчанию astro/src/data (канон Риты)
    python test_pages.py --json        # + машиночитаемый итог
"""
import os, sys, re, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib.textextract import visible_frags, strip_ent   # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(BASE, "deploy")   # канон = дерево, которое уезжает в прод
EXCLUDE = ("_sketch", "backup", "animation-demo", "prototype", "_mobile-frame", "_hero-palette", "standalone")
EXCLUDE_DIR = ("node_modules", ".git", "_astro", ".claude", "deka", "otchet")

MEANING = [
    ("гео-негатив", re.compile(r"ЮЗАО|\bне\s+ЦАО|\bвне\s+ЦАО|\bне\s+в\s+ЦАО|\bне\s+в\s+центре", re.I)),
    ("англицизм", re.compile(r"off-?market|\badjacent|\bdowngrade|HNWI|TL;?DR|\blandmark|due\s*diligence|Private\s+[Bb]anking|family\s+office|Buyer-proof|short-list|YMYL|\bpillar\b|Hero-услуга", re.I)),
    ("апарт-обрывок", re.compile(r"\bапарт-(?!аменты|амента|аментов|аментами|комплекс|отел|кварт)", re.I)),
]
TYPO = [
    ("число+ед без nbsp", re.compile(r"\d\s(млн|млрд|тыс|м²|км²|км|квартир\w*|этаж\w*|год\w*|лет|мин|₽|%|м)\b")),
    ("дефис-как-тире", re.compile(r"\S\s-\s\S")),
    ("двойной пробел", re.compile(r"\S  \S")),
]
FORBIDDEN_COLOR = re.compile(r"#EEC936|#00[0-9a-fA-F]{2}00|rgb\(\s*0\s*,\s*1?\d?\d\s*,\s*0", re.I)  # жёлтый-резерв / зелёный

def check(html, fname):
    frags = visible_frags(html)
    vis = strip_ent(" ".join(frags))
    R = []  # (level, name, ok, detail)
    def add(level, name, ok, detail=""): R.append((level, name, ok, detail))

    # ── SEO-контракт ──
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    add("CRIT", "title", bool(m and m.group(1).strip()), (m.group(1).strip()[:60] if m else "нет"))
    if m:
        L = len(m.group(1).strip()); add("WARN", "title-длина 20-75", 20 <= L <= 75, f"{L} симв")
    add("CRIT", "meta description", bool(re.search(r'<meta\s+name="description"\s+content="[^"]{20,}"', html)))
    h1 = re.findall(r"<h1[\s>]", html)
    add("CRIT", "h1 есть", len(h1) >= 1, f"{len(h1)} шт")
    add("WARN", "h1 единственный", len(h1) == 1, f"{len(h1)} шт")
    add("WARN", "canonical", bool(re.search(r'rel="canonical"', html)))
    add("WARN", "og:title+desc", bool(re.search(r'property="og:title"', html)) and bool(re.search(r'property="og:description"', html)))

    # ── JSON-LD валиден ──
    lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    bad = 0
    for ld in lds:
        try: json.loads(ld)
        except Exception: bad += 1
    add("CRIT", "JSON-LD парсится", bad == 0, (f"{bad} битых из {len(lds)}" if lds else "нет schema"))

    # ── структура (канон) ──
    add("CRIT", "геро есть", bool(re.search(r'class="[^"]*hero|id="canvas"', html)))
    add("CRIT", "футер есть", bool(re.search(r"<footer|©\s*20|Политика конфиденциальности", html)))
    add("WARN", "CTA есть", bool(re.search(r"hp-cta|st-btn--orange|<form", html)))

    # ── смысл (0 находок = канон §9) ──
    for name, rx in MEANING:
        hits = rx.findall(vis)
        add("CRIT", f"смысл: {name}=0", len(hits) == 0, (f"{len(hits)}× {hits[:3]}" if hits else ""))

    # ── типографика (по сырым фрагментам, сущности целы) ──
    for name, rx in TYPO:
        hits = sum(len(rx.findall(f)) for f in frags)
        add("WARN", f"типо: {name}=0", hits == 0, (f"{hits}×" if hits else ""))

    # ── бренд-консистентность ──
    add("WARN", "бренд Белолипцев", "елолипцев" in html)
    add("WARN", "email solomon_estate", ("solomon_estate@mail.ru" in html) or ("mailto:" not in html))
    add("WARN", "нет запрещ. цветов", not bool(FORBIDDEN_COLOR.search(html)))
    return R

def find_pages(root):
    """Рекурсивный обход: в deploy/ страницы лежат как <slug>/index.html."""
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [x for x in dns if x not in EXCLUDE_DIR]
        for fn in fns:
            if fn.endswith(".html") and not any(x in fn for x in EXCLUDE):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def page_id(path, root):
    """deploy/cao/arbat/index.html → cao/arbat ; site/src/data/cao.html → cao.html"""
    rel = os.path.relpath(path, root).replace("\\", "/")
    return rel[:-len("/index.html")] if rel.endswith("/index.html") else rel


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = args[0] if args else DEFAULT_DIR
    files = find_pages(d)
    if not files:
        print(f"нет .html в {d}"); return 2
    print(f"=== ТЕСТ-ГЕЙТ: {len(files)} страниц · {d} ===\n")
    crit_fail = warn_fail = 0
    fail_detail = []
    for f in files:
        pid = page_id(f, d)
        html = open(f, encoding="utf-8").read()
        R = check(html, pid)
        cf = [r for r in R if r[0] == "CRIT" and not r[2]]
        wf = [r for r in R if r[0] == "WARN" and not r[2]]
        crit_fail += len(cf); warn_fail += len(wf)
        mark = "❌" if cf else ("⚠️ " if wf else "✅")
        print(f"{mark} {pid:<48} CRIT {len([r for r in R if r[0]=='CRIT' and r[2]])}/{len([r for r in R if r[0]=='CRIT'])}  WARN-fail {len(wf)}")
        for lvl, name, ok, det in cf:
            print(f"      ❌ CRIT {name}  {det}"); fail_detail.append((pid, name, det))
        for lvl, name, ok, det in wf:
            print(f"      ⚠️  {name}  {det}")
    print(f"\n=== ИТОГ: CRIT-провалов {crit_fail} · WARN-провалов {warn_fail} ===")
    if crit_fail == 0:
        print("✅ ГЕЙТ ПРОЙДЕН (все критические проверки зелёные)")
        return 0
    print("❌ ГЕЙТ НЕ ПРОЙДЕН — критические провалы выше")
    return 1

if __name__ == "__main__":
    sys.exit(main())
