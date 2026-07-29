#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix-schema-gaps.py — два дефекта микроразметки, найденные доской состояния.

Ни один из прежних гейтов их не ловил: JSON-LD валиден, страница на месте,
формально всё зелено. Увидела только доска, которая сравнивает содержимое
страницы с её же микроразметкой.

1. Дом Наркомфина: на странице пять вопросов FAQ, а в разметке FAQPage —
   четыре. Вопрос «Когда реставрировали Дом Наркомфина?» виден пользователю,
   но не виден поисковику. Добавляем его в разметку с текстом ответа
   со страницы, дословно.

2. Мантулинская 9: микроразметки самого здания нет вообще — только хлебные
   крошки и FAQ. Для страницы здания это потеря: поисковик не связывает
   адрес, год и координаты с объектом. Добавляем блок по образцу раздела.

Usage: python tools/fix-schema-gaps.py [--dry]
"""
import os, re, sys, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NARKOMFIN_Q = "Когда реставрировали Дом Наркомфина?"

MANTULINSKAYA = """<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": ["LandmarkOrHistoricalBuilding", "Place"],
  "name": "Мантулинская, 9 — Дом ВЦСПС",
  "description": "Жилой комплекс 1930-х годов на Мантулинской улице, Пресненский район ЦАО. Постройка эпохи авангарда и раннего постконструктивизма.",
  "url": "https://beloliptsev.ru/modernizm/mantulinskaya-9/",
  "address": { "@type": "PostalAddress", "streetAddress": "Мантулинская улица, 9", "addressLocality": "Москва", "addressRegion": "Пресненский, ЦАО", "addressCountry": "RU" },
  "geo": { "@type": "GeoCoordinates", "latitude": %(lat)s, "longitude": %(lon)s },
  "yearBuilt": "1930"
}</script>
"""


def visible_faq(html):
    sec = re.search(r'data-screen-label="[^"]*FAQ[^"]*".*?</section>', html, re.S)
    if not sec:
        return []
    out = []
    for item in re.findall(r'<div class="st-faq__item">(.*?)</div>\s*</div>\s*</div>', sec.group(0), re.S):
        q = re.search(r"<h4>(.*?)</h4>", item, re.S)
        a = re.search(r'<div class="st-faq__inner"><p>(.*?)</p>', item, re.S)
        if q and a:
            clean = lambda t: re.sub(r"<[^>]+>", "", t).replace("&nbsp;", " ").strip()
            out.append((clean(q.group(1)), clean(a.group(1))))
    return out


def fix_narkomfin(dry):
    p = os.path.join(BASE, "deploy", "modernizm", "dom-narkomfina", "index.html")
    s = open(p, encoding="utf-8").read()
    faq = visible_faq(s)
    missing = [(q, a) for q, a in faq if NARKOMFIN_Q.rstrip("?") in q]
    if not missing:
        print("  Наркомфин: вопрос на странице не найден — пропуск"); return 0
    q, a = missing[0]
    m = re.search(r'(<script type="application/ld\+json">\{[^<]*?"@type":\s*"FAQPage".*?)(\n?\s*\]\s*\}</script>)', s, re.S)
    if not m:
        print("  Наркомфин: блок FAQPage не найден"); return 0
    ins = (',\n    { "@type": "Question", "name": "%s", "acceptedAnswer": '
           '{ "@type": "Answer", "text": "%s" } }' % (q, a.replace('"', '\\"')))
    s2 = s[:m.end(1)] + ins + s[m.end(1):]
    try:
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s2, re.S)
        for b in blocks:
            json.loads(b)
    except Exception as e:
        print(f"  Наркомфин: после правки JSON-LD не парсится ({e}) — откат"); return 0
    if not dry:
        open(p, "w", encoding="utf-8").write(s2)
    print(f"  ✅ Наркомфин: вопрос «{q}» добавлен в микроразметку")
    return 1


def fix_mantulinskaya(dry):
    p = os.path.join(BASE, "deploy", "modernizm", "mantulinskaya-9", "index.html")
    s = open(p, encoding="utf-8").read()
    if re.search(r'"@type":\s*\[?\s*"(?:Landmark|Place)', s):
        print("  Мантулинская: схема здания уже есть — пропуск"); return 0
    c = re.search(r'data-center="([0-9.]+)\s*,\s*([0-9.]+)"', s)
    if not c:
        print("  Мантулинская: координат на странице нет — пропуск"); return 0
    block = MANTULINSKAYA % {"lat": c.group(1), "lon": c.group(2)}
    i = s.find('<script type="application/ld+json">')
    s2 = s[:i] + block + s[i:]
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s2, re.S):
        json.loads(b)
    if not dry:
        open(p, "w", encoding="utf-8").write(s2)
    print(f"  ✅ Мантулинская: добавлена схема здания, координаты {c.group(1)},{c.group(2)}")
    return 1


def main():
    dry = "--dry" in sys.argv
    n = fix_narkomfin(dry) + fix_mantulinskaya(dry)
    print(f"\n{'(DRY) ' if dry else ''}исправлено страниц: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
