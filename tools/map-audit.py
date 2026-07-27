#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
map-audit.py — детерминированный аудит карт (Т-3 плана 20.07).

Володя: «карты везде очень сильно врут — точки находятся вообще не там».
Скрипт извлекает по каждой странице: адрес (schema streetAddress) ↔ координаты
(data-center / data-points / schema geo) и ловит РАСХОЖДЕНИЯ машинно:

  ❌ CRIT  data-center ≠ data-points   — карта центрируется не на метке
  ❌ CRIT  schema geo ≠ data-center     — микроразметка и карта спорят
  ❌ CRIT  дубль координат              — два разных здания в одной точке (copy-paste)
  ❌ CRIT  координаты вне Москвы        — за боксом 55.55–55.95 / 37.30–37.90
  ⚠️ WARN  есть адрес, но нет карты
  ⚠️ WARN  подпись метки не совпадает с адресом страницы

Usage:
    python tools/map-audit.py deploy          # по живой раздаче
    python tools/map-audit.py site/src/data   # по исходнику
    python tools/map-audit.py deploy --csv    # выгрузка таблицы для ручной сверки в картах
"""
import os, re, sys, json
from collections import defaultdict

MOSCOW = (55.55, 55.95, 37.30, 37.90)   # lat_min, lat_max, lon_min, lon_max
TOL = 0.0025                             # ~250 м — допуск между источниками координат

def find_pages(root):
    out = []
    for dp, _, fns in os.walk(root):
        if any(x in dp for x in ("node_modules", ".git", "_astro", "assets", "fonts")):
            continue
        for fn in fns:
            if fn.endswith(".html"):
                out.append(os.path.join(dp, fn))
    return sorted(out)

def page_id(p, root):
    rel = os.path.relpath(p, root).replace("\\", "/")
    return rel[:-len("/index.html")] if rel.endswith("/index.html") else rel[:-5]

def grab(s):
    d = {}
    m = re.search(r'data-center="([0-9.]+)\s*,\s*([0-9.]+)"', s)
    if m: d["center"] = (float(m.group(1)), float(m.group(2)))
    m = re.search(r"data-points='(\[.*?\])'", s, re.S)
    if m:
        try:
            pts = json.loads(m.group(1))
            d["points"] = [(float(p["c"][0]), float(p["c"][1]), p.get("t", "")) for p in pts if "c" in p]
        except Exception:
            d["points_broken"] = True
    la = re.search(r'"latitude":\s*([0-9.]+)', s); lo = re.search(r'"longitude":\s*([0-9.]+)', s)
    if la and lo: d["schema"] = (float(la.group(1)), float(lo.group(1)))
    a = re.search(r'"streetAddress":\s*"([^"]*)"', s)
    if a: d["addr"] = a.group(1)
    return d

def far(a, b):
    return abs(a[0] - b[0]) > TOL or abs(a[1] - b[1]) > TOL

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    as_csv = "--csv" in sys.argv
    pages = find_pages(root)
    rows, crit, warn = [], [], []
    seen = defaultdict(list)

    for p in pages:
        s = open(p, encoding="utf-8", errors="ignore").read()
        d = grab(s)
        if not any(k in d for k in ("center", "points", "schema", "addr")):
            continue
        pid = page_id(p, root)
        c, pts, sch, addr = d.get("center"), d.get("points"), d.get("schema"), d.get("addr", "")
        label = pts[0][2] if pts else ""
        rows.append((pid, addr, c, pts[0][:2] if pts else None, sch, label))

        if d.get("points_broken"):
            crit.append(f"{pid}: data-points не парсится (сломанный JSON)")
        if c and pts and far(c, pts[0][:2]):
            crit.append(f"{pid}: центр карты ≠ метка ({c} vs {pts[0][:2]})")
        if c and sch and far(c, sch):
            crit.append(f"{pid}: schema geo ≠ карта ({sch} vs {c})")
        for tag, xy in (("center", c), ("schema", sch)):
            if xy and not (MOSCOW[0] <= xy[0] <= MOSCOW[1] and MOSCOW[2] <= xy[1] <= MOSCOW[3]):
                crit.append(f"{pid}: {tag} вне Москвы — {xy}")
        if c: seen[c].append(pid)
        if addr and not c and not pts:
            warn.append(f"{pid}: есть адрес «{addr}», но карты нет")
        if addr and label:
            head = re.split(r"[,\d]", addr)[0].strip().lower()
            if head and len(head) > 4 and head not in label.lower():
                warn.append(f"{pid}: подпись метки «{label}» не бьётся с адресом «{addr}»")

    for xy, ids in seen.items():
        if len(ids) > 1:
            crit.append(f"дубль координат {xy}: {', '.join(ids)}")

    if as_csv:
        print("page;address;center;point;schema;label")
        for r in rows:
            print(";".join(str(x) if x is not None else "" for x in r))
        return 0

    print(f"=== MAP-AUDIT: {root} — карт/адресов на {len(rows)} страницах ===\n")
    for pid, addr, c, pt, sch, label in rows:
        flag = "✅" if c else "⚠️ "
        print(f"{flag} {pid:<42} {str(c or '—'):<22} {addr[:44]}")
    print(f"\n--- CRIT: {len(crit)} · WARN: {len(warn)} ---")
    for x in crit: print("  ❌", x)
    for x in warn: print("  ⚠️ ", x)
    print("\nРучная сверка (то, что машина проверить не может):")
    print("  открой каждую пару адрес↔координаты в Яндекс.Картах и убедись, что точка на здании.")
    print("  Быстрый способ: python tools/map-audit.py <root> --csv > maps.csv → таблица.")
    return 1 if crit else 0

if __name__ == "__main__":
    sys.exit(main())
