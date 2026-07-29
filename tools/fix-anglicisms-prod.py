#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix-anglicisms-prod.py — точечная зачистка англицизмов, найденных в проде
после того, как qa-lint научился видеть дерево deploy/.

Почему отдельный скрипт, а не rita-patch.py: «family offices» стоит в трёх
разных падежных позициях, и одна литеральная замена на всё дерево сломала бы
грамматику («каналы между брокерами и семейные офисы»). Здесь замены привязаны
к контексту, каждая пара проверяется на согласование отдельно.

Usage: python tools/fix-anglicisms-prod.py deploy [--dry]
"""
import os, sys

# (что искать, на что заменить) — контекст включён в ключ, чтобы падеж совпал
PAIRS = [
    # подпись интерактивной карты районов ЦАО (10 страниц)
    ("метки&nbsp;— premium-адреса", "метки&nbsp;— премиальные адреса"),
    # голос эксперта, творительный падеж: «между брокерами и …»
    ("между частными брокерами и&nbsp;family offices",
     "между частными брокерами и&nbsp;семейными офисами"),
    # родительный падеж: «сеть брокеров и …»
    ("сеть частных брокеров и&nbsp;family offices",
     "сеть частных брокеров и&nbsp;семейных офисов"),
    # home-staging (страница продажи премиум) — «предпродажная подготовка» на этой
    # же странице уже занята как название этапа, поэтому берём «оформление»
    ("лёгкий home-staging", "лёгкое предпродажное оформление"),
    ("Лёгкий home-staging", "Лёгкое предпродажное оформление"),
    ("потенциала home-staging", "потенциала предпродажного оформления"),
    ("Бюджетный home-staging", "Бюджетное предпродажное оформление"),
    # инвест-жаргон
    ("самостоятельный investment-актив", "самостоятельный инвестиционный актив"),
]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = args[0] if args else "deploy"
    dry = "--dry" in sys.argv
    if not os.path.isdir(root):
        print(f"нет дерева: {root}"); return 2

    changed = total = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in (".git", ".claude", "node_modules")]
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dp, fn)
            s = open(p, encoding="utf-8").read()
            n = 0
            for a, b in PAIRS:
                c = s.count(a)
                if c:
                    s = s.replace(a, b); n += c
            if n:
                if not dry:
                    open(p, "w", encoding="utf-8").write(s)
                changed += 1; total += n
                print(f"  {os.path.relpath(p, root):<50} {n} замен")
    print(f"\n{'(DRY) ' if dry else ''}ИТОГО: {changed} файлов, {total} замен")
    return 0


if __name__ == "__main__":
    sys.exit(main())
