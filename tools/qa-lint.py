#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
qa-lint.py — детерминированный линтер видимой копии сайта Белолипцева.
Две группы:
  A — типографика (прямые кавычки, дефис-как-тире, двойной пробел, число+единица без nbsp)
  B — смысл/SEO-артефакты (ЮЗАО/НЕ ЦАО, англицизмы off-market/adjacent/downgrade/HNWI/TL;DR, апарт-обрывок, F1-F5 в видимом)
Сканирует ТОЛЬКО видимый текст (между > и <), исключая <script>/<style>/комментарии и атрибуты.
Usage: python qa-lint.py            # все целевые страницы
       python qa-lint.py B          # только смысл
       python qa-lint.py <file...>  # конкретные файлы
"""
import re, glob, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # корень репо
# Рита 28.07: пути вели на старое дерево (website/ui_kits, HANDOFF-RITA/pages) —
# в этом репо их нет, линтер сканировал 0 страниц (ложный «0 находок»).
# Перенаправлено на актуальный слой PortedPage — тот же, что у test_pages.
# Прежние пути оставлены для истории:
#   os.path.join(BASE, "website", "ui_kits", "website"),
#   os.path.join(BASE, "HANDOFF-RITA", "pages"),
DIRS = [
    os.path.join(BASE, "site", "src", "data"),
]
EXCLUDE = ("_sketch", "backup", "animation-demo", "prototype",
           "_mobile-frame", "_hero-palette", "standalone")

MEANING = [
    ("гео-негатив", re.compile(r"ЮЗАО|\bне\s+ЦАО|\bвне\s+ЦАО|\bне\s+в\s+ЦАО|\bне\s+в\s+центре", re.I)),
    ("англицизм",   re.compile(r"off-?market|adjacent|downgrade|HNWI|TL;?DR|landmark|due\s*diligence", re.I)),
    ("апарт-обрывок", re.compile(r"\bапарт-(?!аменты|амента|аментов|аментами|комплекс|отел|кварт)", re.I)),
    ("SEO-сегмент F#", re.compile(r"\bF[1-5]\b")),
    ("латиница-проза", re.compile(r"\b(?!Hilton|Radisson|Collection|Hotel|Moscow|Neva|Towers?)"
                                  r"(?=[A-Za-z]*[a-z])[A-Za-z]{3,}\b")),  # строчная латиница в прозе (англицизмы), бренды/римские/аббрев. исключены
]
TYPO = [
    ("прямые кавычки",    re.compile(r'"[^"]')),
    ("дефис-как-тире",    re.compile(r"\s-\s")),
    ("двойной пробел",    re.compile(r"\S  \S")),
    ("число+ед без nbsp", re.compile(r"\d\s+(м|км|км²|м²|млн|млрд|₽|этаж|квартир|год|лет|мин|%)\b")),
]
# слова-латиница, которые допустимы в прозе (бренды/контакты/имена/домены) — не флагаем
LATIN_OK = re.compile(r"^(Hilton|Radisson|Collection|Hotel|Moscow|Neva|Towers?|UNESCO|"
                      r"mail|Telegram|Email|e-?mail|beloliptsev|solomon|estate|"
                      r"Private|Privat|Premier|VIP|"
                      r"Corbusier|Wright|Lloyd|Frank|Singer|Empire|State|Building|"
                      r"Oro|Mille|Knightsbridge|Leningradskaya|"
                      r"Cian|Avito|rgr|reestr|rosreestr|grmos|gov|fssp|mos|nalog|"
                      r"Tweaks|cookie|http|https|www|ru|com|org|"
                      # французские арх-термины (Le Corbusier) + имена ЖК + тех
                      r"Unite|Unité|Habitation|Vers|une|architecture|Weissenhof|"
                      r"Park|Snegiri|Eco|referrer|politika|konfidentsialnosti|duotone|"
                      r"Worldwide|Royal)$", re.I)

def gather():
    files = []
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        return [a for a in sys.argv[1:] if os.path.exists(a)]
    for d in DIRS:
        for f in sorted(glob.glob(os.path.join(d, "*.html"))):
            b = os.path.basename(f)
            if any(x in b for x in EXCLUDE):
                continue
            files.append(f)
    return files

def visible_parts(line):
    """Список видимых текст-фрагментов строки, HTML-сущности СОХРАНЕНЫ (для типографики)."""
    line = re.sub(r"<!--.*?-->", "", line)            # single-line comments
    parts = re.findall(r">([^<]+)(?:<|$)", line)       # text between tags
    head = re.match(r"^([^<]*)<", line)                # leading text before first tag
    if head: parts.append(head.group(1))
    return parts

def strip_ent(txt):
    return re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", txt)    # сущности → пробел (для латиница/смысл-проверок)

def main():
    only = None
    if len(sys.argv) > 1 and sys.argv[1] in ("A", "B"):
        only = sys.argv[1]
    files = gather()
    hits = []
    for f in files:
        inblock = None
        with open(f, encoding="utf-8") as fh:
            for i, raw in enumerate(fh, 1):
                low = raw.lower()
                if inblock:
                    if (inblock == "comment" and "-->" in low) or (f"</{inblock}>" in low):
                        inblock = None
                    continue
                if "<!--" in low and "-->" not in low: inblock = "comment"; continue
                if "<script" in low and "</script>" not in low: inblock = "script"; continue
                if "<style" in low and "</style>" not in low: inblock = "style"; continue
                parts = visible_parts(raw)
                vt_raw = " ".join(parts)               # сущности сохранены (для A)
                vt = strip_ent(vt_raw)                  # сущности → пробел (для B)
                if not vt.strip():
                    continue
                if only in (None, "B"):
                    for name, rx in MEANING:
                        for m in rx.finditer(vt):
                            g = m.group(0)
                            if name == "латиница-проза" and LATIN_OK.match(g):
                                continue
                            hits.append((f, i, "B/" + name, g.strip(), vt.strip()[:90]))
                if only in (None, "A"):
                    for frag in parts:                  # по фрагментам, сущности целы → нет join-артефактов
                        for name, rx in TYPO:
                            for m in rx.finditer(frag):
                                hits.append((f, i, "A/" + name, m.group(0).strip(), frag.strip()[:90]))
    # отчёт
    from collections import Counter, defaultdict
    by_kind = Counter(h[2] for h in hits)
    by_file = defaultdict(list)
    for h in hits:
        by_file[h[0]].append(h)
    print(f"=== QA-LINT: {len(files)} страниц, {len(hits)} находок ===\n")
    print("По типам:")
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {k}")
    print("\nДетально:")
    for f in sorted(by_file):
        hs = by_file[f]
        if not hs:
            continue
        print(f"\n  {os.path.basename(f)}")
        for h in hs:
            print(f"    L{h[1]:<5} {h[2]:<26} «{h[3]}»  | {h[4]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
