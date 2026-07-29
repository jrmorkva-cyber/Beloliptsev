#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix-coords.py — свод трёх источников координат к выверенному значению.

Володя на созвоне 20.07: «карты везде очень сильно врут — точки находятся
вообще не там», пример — Дом Моссельпрома. Проверка подтвердила и усугубила:
у Моссельпрома неверны ОБА значения на сайте (карта промахивалась на ~200 м,
микроразметка на ~330 м), у Дома Жолтовского — тоже оба (на 300 м и на 920 м),
причём страница района Тверской ставила Моховую, 13 почти на километр южнее,
чем собственная страница здания.

Координаты ниже подтверждены по 2–3 независимым источникам на каждый адрес
(карточка Википедии, OpenStreetMap/Nominatim, 2ГИС); расхождение между
источниками — единицы-десятки метров.

Правило: на странице одного здания data-center, data-points[0] и geo
в микроразметке обязаны совпадать. На странице с несколькими метками центр —
это центр области, и совпадать с первой меткой он не обязан.

Usage: python tools/fix-coords.py [--dry]
"""
import os, re, sys, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# адрес → (широта, долгота), выверено по независимым источникам
CANON = {
    "narkomfina":      (55.7570, 37.5812),   # Новинский бульвар, 25
    "mosselproma":     (55.7539, 37.6025),   # Калашный переулок, 2/10
    "zholtovskogo":    (55.7562, 37.6132),   # Моховая улица, 13
    "kotelnicheskaya": (55.7471, 37.6428),   # Котельническая набережная, 1/15
}

# страницы одного здания: сводим все три источника
SINGLE = [
    ("deploy/modernizm/dom-narkomfina/index.html", "narkomfina"),
    ("deploy/modernizm/dom-mosselproma/index.html", "mosselproma"),
    ("deploy/visotki/kotelnicheskaya/index.html", "kotelnicheskaya"),
    ("site/src/data/modernizm--dom-narkomfina.html", "narkomfina"),
    ("site/src/data/visotki--kotelnicheskaya.html", "kotelnicheskaya"),
]

# страницы, где надо поправить конкретную метку в наборе (по подстроке подписи)
MARKERS = [
    ("deploy/modernizm/dom-zholtovskogo/index.html", "Моховой", "zholtovskogo"),
    ("deploy/cao/tverskoy/index.html", "Жолтовского", "zholtovskogo"),
    ("deploy/cao/tagansky/index.html", "Котельническая", "kotelnicheskaya"),
]


def set_center(s, lat, lon):
    return re.sub(r'data-center="[^"]*"', 'data-center="%s,%s"' % (lat, lon), s, count=1)


def set_schema(s, lat, lon):
    s = re.sub(r'("latitude":\s*)[0-9.]+', lambda m: m.group(1) + str(lat), s, count=1)
    return re.sub(r'("longitude":\s*)[0-9.]+', lambda m: m.group(1) + str(lon), s, count=1)


def patch_points(s, lat, lon, match=None):
    """Правит первую метку либо метку, чья подпись содержит match."""
    m = re.search(r"data-points='(\[.*?\])'", s, re.S)
    if not m:
        return s, False
    pts = json.loads(m.group(1))
    hit = False
    for p in pts:
        if match is None or match.lower() in p.get("t", "").lower():
            p["c"] = [lat, lon]
            hit = True
            if match is None:
                break
    if not hit:
        return s, False
    new = json.dumps(pts, ensure_ascii=False, separators=(",", ":"))
    return s[:m.start(1)] + new + s[m.end(1):], True


def centroid_center(s):
    """Для страницы с несколькими метками центр — среднее по меткам."""
    m = re.search(r"data-points='(\[.*?\])'", s, re.S)
    pts = json.loads(m.group(1))
    lat = round(sum(p["c"][0] for p in pts) / len(pts), 4)
    lon = round(sum(p["c"][1] for p in pts) / len(pts), 4)
    return set_center(s, lat, lon), lat, lon


def main():
    dry = "--dry" in sys.argv
    touched = 0

    for rel, key in SINGLE:
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            print(f"  пропуск, нет файла: {rel}"); continue
        lat, lon = CANON[key]
        s = open(p, encoding="utf-8").read()
        s2 = set_center(s, lat, lon)
        s2, _ = patch_points(s2, lat, lon)
        s2 = set_schema(s2, lat, lon)
        if s2 != s:
            if not dry:
                open(p, "w", encoding="utf-8").write(s2)
            touched += 1
            print(f"  ✅ {rel} → {lat},{lon} (центр + метка + микроразметка)")

    for rel, match, key in MARKERS:
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            print(f"  пропуск, нет файла: {rel}"); continue
        lat, lon = CANON[key]
        s = open(p, encoding="utf-8").read()
        s2, hit = patch_points(s, lat, lon, match)
        if not hit:
            print(f"  ⚠️  {rel}: метка «{match}» не найдена"); continue
        n_pts = len(json.loads(re.search(r"data-points='(\[.*?\])'", s2, re.S).group(1)))
        if n_pts == 1:
            s2 = set_center(s2, lat, lon)
            note = "центр + метка"
        else:
            s2, cl, cn = centroid_center(s2)
            note = f"метка + центр по среднему ({cl},{cn})"
        # Микроразметка описывает САМО здание страницы, а не облако меток,
        # поэтому geo ставим по зданию независимо от числа точек на карте.
        if '"latitude"' in s2:
            s2 = set_schema(s2, lat, lon)
        if s2 != s:
            if not dry:
                open(p, "w", encoding="utf-8").write(s2)
            touched += 1
            print(f"  ✅ {rel} → метка «{match}» {lat},{lon} · {note}")

    print(f"\n{'(DRY) ' if dry else ''}страниц поправлено: {touched}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
