#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix-hub.py — прошивка новых зданий в хаб раздела и сведение счётчиков.

Володя на созвоне 20.07: в слайдере семь плиток, часть из них не авангард,
на кнопке написано одно число, в тексте другое. «Всякие хуеплеты накидают
в панамку, зачем вы сюда это поставили».

Проверка показала, что расхождение больше заявленного: на кнопке и в заголовке
списка стояло «11 адресов», в описании, og-теге и двух ответах FAQ — «13 знаковых
адресов», а фактически в хабе было 7 плиток и 4 капсулы при 18 существующих
страницах зданий. Семь страниц не были прошиты в хаб вообще — включая две
старые, Дом писателей и Дом полярников: они существовали, но кликом до них
было не дойти.

Скрипт добавляет плитки новым зданиям, капсулы забытым и приводит ВСЕ счётчики
к одному числу — фактическому количеству страниц зданий в разделе.

Usage: python tools/fix-hub.py [--dry]
"""
import os, re, sys, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = os.path.join(BASE, "deploy", "modernizm", "index.html")

# новые плитки: slug, годы, название, адрес, описание, чипы
TILES = [
    ("dom-melnikova", "1927–1929", "Дом Мельникова", "Кривоарбатский, 10 · Арбат",
     "Дом-мастерская Константина Мельникова: два врезанных друг в&nbsp;друга цилиндра "
     "с&nbsp;шестиугольными проёмами и&nbsp;перекрытиями без&nbsp;единой балки. Единственный "
     "частный дом эпохи авангарда; сегодня музей.", ["Мельников", "ОКН ФЗ"]),
    ("dk-zueva", "1927–1929", "ДК имени Зуева", "Лесная, 18 · Тверской",
     "Рабочий клуб Ильи Голосова со&nbsp;стеклянным цилиндром, прошивающим здание "
     "насквозь. Самая известная постройка архитектора и&nbsp;один из&nbsp;самых узнаваемых "
     "памятников конструктивизма.", ["Голосов", "ОКН РЗ"]),
    ("dom-artistov-mhat", "1927–1928", "Дом артистов МХАТ", "Брюсов переулок, 17 · ЦАО",
     "Жилищный кооператив Художественного театра по&nbsp;проекту Алексея Щусева. Здесь жили "
     "Москвин, Качалов, Леонидов; сам архитектор занимал в&nbsp;доме квартиру-мастерскую. "
     "Один из&nbsp;немногих адресов раздела с&nbsp;квартирами в&nbsp;продаже.",
     ["Щусев", "ОКН ФЗ", "жилой"]),
    ("dom-centrosoyuza", "1928–1936", "Здание Центросоюза", "Мясницкая, 39 · ЦАО",
     "Единственная реализованная в&nbsp;России постройка Ле&nbsp;Корбюзье. Опоры-столбы, "
     "сплошное остекление, розовый артикский туф; реализация под&nbsp;руководством "
     "Николая Колли.", ["Ле Корбюзье", "ОКН РЗ"]),
    ("zdanie-narkomzema", "1928–1933", "Здание Наркомзема", "Садовая-Спасская, 11/1 · ЦАО",
     "Алексей Щусев в&nbsp;нехарактерном для&nbsp;себя языке: три корпуса вокруг "
     "трапециевидного двора на&nbsp;целый квартал, полуцилиндрический ризалит "
     "и&nbsp;первые в&nbsp;Москве лифты непрерывного действия.", ["Щусев", "ОКН РЗ"]),
    ("dom-dinamo", "1928–1931", "Дом общества «Динамо»", "Большая Лубянка, 12 · ЦАО",
     "Иван Фомин и&nbsp;Аркадий Лангман на&nbsp;переломе эпох: упрощённая классика "
     "со&nbsp;спаренными колоннами по&nbsp;Большой Лубянке и&nbsp;конструктивистская "
     "башня по&nbsp;Фуркасовскому переулку.", ["Фомин", "Лангман", "ОКН РЗ"]),
]

# забытые страницы — добавляем капсулами в индекс «другие адреса»
CAPS = [
    ("dom-pisateley", "Дом писателей", "Лаврушинский пер., 17 · 1930-е"),
    ("dom-polyarnikov", "Дом полярников", "Никитский бульвар · 1937"),
]


def tile(slug, years, name, addr, arch, chips):
    ch = "".join("<span>%s</span>" % c for c in chips)
    return (
        '      <a class="vh-card" href="/modernizm/%s/">\n'
        '        <span class="vh-card__photo" style="background:#1B2230"></span>\n'
        '        <span class="vh-card__body">\n'
        '          <span class="vh-card__no">%s</span>\n'
        '          <span class="vh-card__name">%s</span>\n'
        '          <span class="vh-card__addr">%s</span>\n'
        '          <span class="vh-card__arch">%s</span>\n'
        '          <span class="vh-card__spec">%s</span>\n'
        '          <span class="vh-card__link">Подробно про&nbsp;%s <svg><use href="#i-arr"></use></svg></span>\n'
        '        </span>\n      </a>\n' % (slug, years, name, addr, arch, ch, name))


def cap(slug, name, addr):
    return ('        <a class="mz-cap" href="/modernizm/%s/"><span class="nm">%s</span>'
            '<span class="ad">%s</span></a>\n' % (slug, name, addr))


def main():
    dry = "--dry" in sys.argv
    s = open(HUB, encoding="utf-8").read()
    before = s

    # 1. плитки — в конец ленты mz-grid-lane
    lane_end = s.find("</div><!-- /mz-grid-lane -->")
    if lane_end < 0:
        lane_end = s.find('<div class="mz-index"')
        lane_end = s.rfind("</div>", 0, lane_end)
    added_tiles = []
    for t in TILES:
        if 'href="/modernizm/%s/"' % t[0] in s:
            continue
        s = s[:lane_end] + tile(*t) + s[lane_end:]
        lane_end += len(tile(*t))
        added_tiles.append(t[0])

    # 2. капсулы — в индекс «другие адреса»
    added_caps = []
    m = re.search(r'<div class="mz-index__list">', s)
    if m:
        pos = m.end()
        for c in CAPS:
            if 'href="/modernizm/%s/"' % c[0] in s:
                continue
            s = s[:pos] + "\n" + cap(*c) + s[pos:]
            added_caps.append(c[0])

    # 3. счётчики → фактическое число страниц зданий раздела
    n = len([p for p in glob.glob(os.path.join(BASE, "deploy", "modernizm", "*", "index.html"))])
    s = re.sub(r"\d{1,2}(&nbsp;|\s)адресов авангарда",
               lambda mm: "%d%sадресов авангарда" % (n, mm.group(1)), s)
    s = re.sub(r"\d{1,2}(&nbsp;|\s)знаковых адресов",
               lambda mm: "%d%sзнаковых адресов" % (n, mm.group(1)), s)

    print(f"  плиток добавлено: {len(added_tiles)} {added_tiles}")
    print(f"  капсул добавлено: {len(added_caps)} {added_caps}")
    print(f"  счётчики сведены к {n}")
    if s == before:
        print("\nбез изменений"); return 0
    if not dry:
        open(HUB, "w", encoding="utf-8").write(s)
    print(f"\n{'(DRY) ' if dry else ''}хаб обновлён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
