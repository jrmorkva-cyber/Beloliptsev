#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gen-sitemap.py — карта сайта из фактического дерева публикации.

Зачем: robots.txt обоих деревьев обещает Sitemap: https://beloliptsev.ru/sitemap-index.xml,
но такого файла не существует нигде. Cloudflare Pages на несуществующий путь отдаёт
не 404, а HTML главной страницы — для краулера это хуже честной ошибки: по адресу,
объявленному в robots.txt, лежит невалидный XML.

Скрипт берёт URL из canonical каждой страницы (а не из имён папок — canonical
и есть заявленный адрес), пропускает noindex-страницы и пишет sitemap.xml +
sitemap-index.xml по адресу, который уже обещан в robots.txt.

Usage:
    python tools/gen-sitemap.py deploy
    python tools/gen-sitemap.py deploy --dry
"""
import os, re, sys
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://beloliptsev.ru"
EXCLUDE_DIR = ("node_modules", ".git", "_astro", ".claude")

# Приоритеты по глубине: главная → хабы разделов → страницы зданий и услуг.
PRIORITY = {0: "1.0", 1: "0.9", 2: "0.7"}


def canonical(html):
    m = (re.search(r'rel="canonical"\s+href="([^"]+)"', html)
         or re.search(r'href="([^"]+)"\s+rel="canonical"', html))
    return m.group(1) if m else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = os.path.join(BASE, args[0] if args else "deploy")
    dry = "--dry" in sys.argv
    if not os.path.isdir(root):
        print(f"нет дерева: {root}"); return 2

    urls, skipped = [], []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIR]
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dp, fn)
            html = open(p, encoding="utf-8", errors="ignore").read()
            rel = os.path.relpath(p, root).replace("\\", "/")
            if re.search(r'<meta[^>]+name="robots"[^>]+noindex', html, re.I):
                skipped.append((rel, "noindex")); continue
            u = canonical(html)
            if not u:
                skipped.append((rel, "нет canonical")); continue
            urls.append(u)

    urls = sorted(set(urls))
    today = date.today().isoformat()
    body = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod>"
        f"<priority>{PRIORITY.get(u.rstrip('/').count('/') - 2, '0.6')}</priority></url>"
        for u in urls)
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"{body}\n</urlset>\n")
    index = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             f"  <sitemap><loc>{SITE}/sitemap.xml</loc><lastmod>{today}</lastmod></sitemap>\n"
             "</sitemapindex>\n")

    print(f"=== SITEMAP: {len(urls)} адресов из {os.path.relpath(root, BASE)} ===")
    for rel, why in skipped:
        print(f"  пропущено: {rel}  ({why})")
    if dry:
        print("\n(DRY) файлы не записаны"); return 0
    open(os.path.join(root, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)
    open(os.path.join(root, "sitemap-index.xml"), "w", encoding="utf-8").write(index)
    print(f"\n✅ {root}/sitemap.xml + sitemap-index.xml записаны")
    return 0


if __name__ == "__main__":
    sys.exit(main())
