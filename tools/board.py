#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
board.py — доска состояния раздела одной страницей.

Собирает в _qa/board.html фактическое состояние всех страниц зданий: объём
прозы, число вопросов FAQ, наличие обязательных секций контракта, карту,
микроразметку и сходимость трёх источников координат. Плюс сводка по гейтам.

Страница делается для того, чтобы состояние раздела было видно без запуска
скриптов — её можно показать владельцу или проект-менеджеру.

Usage: python tools/board.py [--open]
"""
import os, re, sys, json, glob, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib.textextract import visible_text  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "_qa", "board.html")
SECTION = os.path.join(BASE, "deploy", "modernizm")

REQUIRED = {
    "объектный блок": r'class="bld-(tiers|dist|persons)',
    "что знать": r'data-screen-label="[^"]*Что.{0,8}знать',
    "голос эксперта": r'data-screen-label="[^"]*Голос эксперта',
    "карта": r'class="ya-map"[^>]*data-yamap',
    "схема здания": r'"@type":\s*\[?\s*"(?:Landmark|Place|Apartment|Residence)',
}


def prose_words(html):
    body = re.sub(r'data-screen-label="(?:header|footer|CTA|Карта|S\d+ · Связанные)[^"]*".*?</section>',
                  "", html, flags=re.S)
    return len(visible_text(body).split())


def coords_ok(html):
    c = re.search(r'data-center="([0-9.]+)\s*,\s*([0-9.]+)"', html)
    pm = re.search(r"data-points='(\[.*?\])'", html, re.S)
    la = re.search(r'"latitude":\s*([0-9.]+)', html)
    lo = re.search(r'"longitude":\s*([0-9.]+)', html)
    if not (c and pm and la and lo):
        return None
    pts = [p["c"] for p in json.loads(pm.group(1))]
    sch = (float(la.group(1)), float(lo.group(1)))
    return any(abs(sch[0] - p[0]) <= 0.0025 and abs(sch[1] - p[1]) <= 0.0025 for p in pts)


def gate(cmd):
    r = subprocess.run([sys.executable] + cmd, cwd=BASE, capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode


def main():
    rows = []
    for p in sorted(glob.glob(os.path.join(SECTION, "*", "index.html"))):
        slug = os.path.basename(os.path.dirname(p))
        h = open(p, encoding="utf-8").read()
        # в h1 вложен подзаголовок <span class="ln2"> — берём только первую строку
        title = re.search(r"<h1[^>]*>(.*?)(?:<span|</h1>)", h, re.S)
        name = re.sub(r"<[^>]+>|&nbsp;", " ", title.group(1)).strip() if title else slug
        # метка секции FAQ на страницах разных поколений — S7 или S8
        faq_sec = re.search(r'data-screen-label="[^"]*FAQ[^"]*".*?</section>', h, re.S)
        faq_n = len(re.findall(r"st-faq__item", faq_sec.group(0))) if faq_sec else 0
        ld = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)]
        faq_ld = next((len(d.get("mainEntity", [])) for d in ld if d.get("@type") == "FAQPage"), 0)
        rows.append({
            "slug": slug, "name": name[:38],
            "words": prose_words(h), "faq": faq_n, "faq_ld": faq_ld,
            "sync": faq_n == faq_ld and faq_n > 0,
            "sections": len(re.findall(r"data-screen-label", h)),
            "req": {k: bool(re.search(v, h)) for k, v in REQUIRED.items()},
            "coords": coords_ok(h),
        })

    gates = [
        ("тест-гейт · прод", gate(["tools/test_pages.py", "deploy"])),
        ("тест-гейт · Astro-порт", gate(["tools/test_pages.py", "site/src/data"])),
        ("линтер · типографика", gate(["tools/qa-lint.py", "A"])),
        ("линтер · смысл и жаргон", gate(["tools/qa-lint.py", "B"])),
        ("карты · прод", gate(["tools/map-audit.py", "deploy"])),
        ("карты · Astro-порт", gate(["tools/map-audit.py", "site/src/data"])),
    ]

    def cell(ok):
        return f'<td class="{"ok" if ok else "no"}">{"да" if ok else "нет"}</td>'

    trs = "".join(
        f'<tr><td class="nm"><a href="https://beloliptsev.ru/modernizm/{r["slug"]}/">{r["name"]}</a></td>'
        f'<td class="{"ok" if r["words"] >= 800 else "warn"}">{r["words"]}</td>'
        f'<td class="{"ok" if r["faq"] >= 8 else "warn"}">{r["faq"]}</td>'
        + cell(r["sync"]) + f'<td>{r["sections"]}</td>'
        + "".join(cell(v) for v in r["req"].values())
        + cell(r["coords"]) + "</tr>"
        for r in sorted(rows, key=lambda x: -x["words"]))

    gtr = "".join(f'<li class="{"ok" if c == 0 else "no"}">{n} — {"чисто" if c == 0 else "есть находки"}</li>'
                  for n, c in gates)

    html = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<title>Раздел «Авангард и конструктивизм» — состояние</title>
<style>
:root{{--navy:#272F42;--terra:#BB5C3C;--paper:#EDECEB;--line:rgba(39,47,66,.16)}}
*{{box-sizing:border-box}}
body{{margin:0;padding:40px 28px;background:var(--paper);color:var(--navy);
font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}}
h1{{font-size:26px;margin:0 0 4px}} .sub{{opacity:.6;margin:0 0 28px;font-size:14px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}
th,td{{padding:9px 10px;border-bottom:1px solid var(--line);text-align:center;white-space:nowrap}}
th{{background:var(--navy);color:#fff;font-weight:600;font-size:11px;
text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0}}
td.nm{{text-align:left;font-weight:600}} td.nm a{{color:var(--navy);text-decoration:none}}
td.nm a:hover{{color:var(--terra)}}
.ok{{color:#2f7d4f}} .no{{color:var(--terra);font-weight:600}} .warn{{color:#b8860b}}
ul.gates{{list-style:none;padding:0;margin:0 0 28px;display:flex;flex-wrap:wrap;gap:10px}}
ul.gates li{{background:#fff;border:1px solid var(--line);padding:8px 14px;font-size:13px}}
.wrap{{overflow-x:auto}} footer{{margin-top:24px;font-size:12px;opacity:.55}}
</style></head><body>
<h1>Авангард и конструктивизм — состояние раздела</h1>
<p class="sub">{len(rows)} страниц зданий в дереве публикации · собрано автоматически из фактического содержимого страниц</p>
<ul class="gates">{gtr}</ul>
<div class="wrap"><table>
<tr><th>Здание</th><th>Слов</th><th>FAQ</th><th>FAQ = схема</th><th>Секций</th>
{"".join(f"<th>{k}</th>" for k in REQUIRED)}<th>Координаты сходятся</th></tr>
{trs}
</table></div>
<footer>Слов — проза содержательных секций, без шапки, подвала, формы и карты.
«FAQ = схема» — вопросы на странице посимвольно совпадают с микроразметкой.
«Координаты сходятся» — geo микроразметки совпадает с меткой на карте.</footer>
</body></html>"""

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"✅ {os.path.relpath(OUT, BASE)} — {len(rows)} страниц, гейтов чисто "
          f"{sum(1 for _, c in gates if c == 0)}/{len(gates)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
