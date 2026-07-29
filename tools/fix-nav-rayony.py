#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix-nav-rayony.py — «Районы» вместо «ЦАО» в названии раздела навигации.

Володя на созвоне 20.07, про подвал и меню: «главные пункты там высотки,
авангард, сталинки и районы вместо ЦАО — всё должно вести на разделы».

Рита 21.07 поправила верхнее меню на части страниц, но заголовок раздела
в мегаменю остался «ЦАО» на 70 страницах, а в верхнем меню «ЦАО» уцелел
ещё на 25. Скрипт доводит до конца.

Что НЕ трогаем: ссылку «Весь ЦАО» внутри раздела — это не название раздела,
а осмысленный пункт «весь округ целиком», и округ здесь называется правильно.
Не трогаем ЦАО в текстах страниц, заголовках и микроразметке: там это
корректное название административного округа.

Usage: python tools/fix-nav-rayony.py [--dry]
"""
import os, re, sys, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEGA = ('<a href="/cao/" class="mega-h">ЦАО</a>', '<a href="/cao/" class="mega-h">Районы</a>')
TOPNAV_RX = re.compile(r'(<nav class="st-topnav">.*?)<a href="/cao/">ЦАО</a>', re.S)


def main():
    dry = "--dry" in sys.argv
    n_mega = n_top = 0
    for p in sorted(glob.glob(os.path.join(BASE, "deploy", "**", "index.html"), recursive=True)):
        s = open(p, encoding="utf-8").read()
        orig = s
        if MEGA[0] in s:
            s = s.replace(*MEGA)
            n_mega += 1
        if TOPNAV_RX.search(s):
            s = TOPNAV_RX.sub(lambda m: m.group(1) + '<a href="/cao/">Районы</a>', s, count=1)
            n_top += 1
        if s != orig and not dry:
            open(p, "w", encoding="utf-8").write(s)
    print(f"  мегаменю: {n_mega} страниц")
    print(f"  верхнее меню: {n_top} страниц")
    print(f"\n{'(DRY) ' if dry else ''}готово")
    return 0


if __name__ == "__main__":
    sys.exit(main())
