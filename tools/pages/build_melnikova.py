# -*- coding: utf-8 -*-
"""
Сборка прод-страницы «Дом Мельникова».

Донор обвязки — deploy/modernizm/dom-isakova/index.html: шапка, подвал, мегаменю,
скрипты и набор из 11 секций там соответствуют канону раздела. Меняем голову и
содержимое секций; разметку не изобретаем.

Запуск:  python tools/pages/build_melnikova.py [--dry]

Контент секций S4/S5/S6/S7/S9 лежит рядом в dom-melnikova.sections.html —
текст отделён от кода, чтобы правки копии не требовали трогать скрипт.
Геро, «История» и «Архитектура» собираются здесь же, потому что в них
подставляются проверенные числа из досье.

Фактура — из ресёрча с источниками. Что сознательно НЕ утверждаем (в прежней
версии страницы это было неверно):
  · дом НЕ в списке ЮНЕСКО — в 2019 ИКОМОС лишь поддержал инициативу номинации;
    в 2006 дом был в World Monuments Watch, это фонд WMF, а не ЮНЕСКО;
  · Мельников не относил себя к конструктивистам — пишем «авангард»;
  · число окон источники дают от 38 до 200 — берём счёт самого архитектора
    (124 проёма, 64 остеклены) и прямо указываем, что счёт его собственный;
  · «РГР Топ-4» публично не подтверждается — формулировка как в проде.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
DONOR = os.path.join(BASE, "deploy", "modernizm", "dom-isakova", "index.html")
SECTIONS_FILE = os.path.join(HERE, "dom-melnikova.sections.html")
OUT = os.path.join(BASE, "deploy", "modernizm", "dom-melnikova", "index.html")

TITLE = "Дом Мельникова в Кривоарбатском переулке — квартиры рядом | Белолипцев"
DESC = ("Дом Мельникова, Кривоарбатский переулок, 10: дом-мастерская архитектора 1927–1929, "
        "два врезанных цилиндра, памятник федерального значения. Сам дом — музей, квартиры "
        "подбираю в арбатских переулках. Аттестованный риэлтор-эксперт РГР →")
OG_DESC = ("Дом Мельникова: дом-мастерская Константина Мельникова 1927–1929, два врезанных "
           "цилиндра, памятник авангарда федерального значения. Квартиры — в переулках вокруг.")
URL = "https://beloliptsev.ru/modernizm/dom-melnikova/"
LAT, LON = 55.748066, 37.589448
DSCARD = ('<!-- @dsCard group="Brand" name="modernizm–dom-melnikova" subtitle="Дом Мельникова&nbsp;— '
          'F1: дом-мастерская 1927–1929, премиум-окружение арбатских переулков, FAQ" -->')

FAQ = [
    ("Где находится Дом Мельникова?",
     "Кривоарбатский переулок, дом 10, район Арбат, ЦАО. Ближайшие станции метро — «Смоленская» "
     "и «Арбатская». Это дом-музей, а не жилой дом: квартир в нём нет."),
    ("Кто и когда построил Дом Мельникова?",
     "Архитектор Константин Степанович Мельников (1890–1974) построил его для себя и своей семьи. "
     "Проект утверждён в июне 1927 года, строительство шло в 1927–1929 годах, семья въехала в ноябре 1929-го."),
    ("Это конструктивизм?",
     "Специалисты относят дом к русскому авангарду. Сам Мельников не входил ни в одну архитектурную "
     "группу и сознательно держал дистанцию от конструктивистов — Весниных и Гинзбурга. Определение "
     "«конструктивизм» встречается в популярных источниках, но специалисты его оспаривают."),
    ("В чём уникальность конструкции?",
     "Два вертикальных цилиндра одного диаметра и разной высоты врезаны друг в друга — план получается "
     "в форме восьмёрки, ориентированной с севера на юг. Перекрытия мембранные: поставленные на ребро "
     "доски пересекаются под прямым углом с ячейкой полметра на полметра, без единой колонны и балки."),
    ("Сколько в доме шестиугольных окон?",
     "Единого общепринятого числа нет — источники называют от нескольких десятков до двух сотен. "
     "По собственному счёту Мельникова в наружных стенах было устроено 124 шестиугольных проёма, "
     "из них 64 стали окнами и нишами, остальные заложены кирпичом."),
    ("Какой у дома охранный статус?",
     "Объект культурного наследия федерального значения — статус присвоен распоряжением Правительства "
     "России в марте 2014 года, официальная формулировка «Экспериментальный жилой дом». До этого, "
     "с 1987 года, дом был памятником регионального значения."),
    ("Дом входит в список ЮНЕСКО?",
     "Нет. В феврале 2019 года Совет российского национального комитета ИКОМОС поддержал инициативу "
     "подготовить номинацию, но в Список всемирного наследия дом не включён. С этим часто путают "
     "другой факт: в 2006 году дом попал в перечень ста памятников мира под угрозой, который ведёт "
     "Всемирный фонд памятников — частная организация, к ЮНЕСКО отношения не имеющая."),
    ("Кому принадлежит дом?",
     "Три четверти — Российской Федерации, по одной восьмой — двум внучкам архитектора как обязательным "
     "наследницам. Оперативное управление с 2011 года у Государственного музея архитектуры имени Щусева, "
     "филиал-музей учреждён в 2014 году."),
    ("Что сейчас с реставрацией?",
     "Интерьеры закрыты для посетителей с октября 2022 года, двор — с ноября 2023-го. Работы начались "
     "в декабре 2023 года, генеральный проектировщик — бюро «Рождественка». К весне 2026 года основные "
     "работы завершены, открытие после реставрации музей планирует на осень 2026-го."),
    ("Можно ли купить квартиру в самом доме?",
     "Нет. Дом находится в долевой собственности государства и наследниц и работает как музей — жилых "
     "помещений в нём нет. Покупают рядом: в Кривоарбатском, Плотниковом, Спасопесковском, "
     "Староконюшенном и Денежном переулках."),
    ("Что покупают в арбатских переулках вокруг дома?",
     "Преобладают доходные дома рубежа XIX–XX веков и дворянские особняки, есть точечные советские "
     "вставки 1930-х и несколько современных клубных домов в габаритах исторической застройки. "
     "Охранный режим здесь устанавливается по каждому зданию отдельно, а не единым списком на квартал, — "
     "это первое, что я проверяю по конкретному адресу."),
]

SHORT = ("в во на за по до от из с со к о об у и а но не ни что как для при без над под про через "
         "это его её их том той тех").split()


def nb(t):
    """§8: неразрывный пробел после коротких слов и в связке «число + единица»."""
    t = re.sub(r"(?<![\w&;])(%s)\s+(?=[«\w])" % "|".join(SHORT), r"\1&nbsp;", t, flags=re.I)
    return re.sub(r"(\d)\s(млн|млрд|тыс|м²|км²|км|м|лет|мин|год\w*|этаж\w*|квартир\w*|₽|%)\b",
                  r"\1&nbsp;\2", t)


def esc(s):
    return s.replace("«", "«").replace('"', '\\"')


def head_jsonld():
    faq = ",\n    ".join(
        '{ "@type": "Question", "name": "%s", "acceptedAnswer": { "@type": "Answer", "text": "%s" } }'
        % (esc(q), esc(a)) for q, a in FAQ)
    return """<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Главная", "item": "https://beloliptsev.ru/" },
    { "@type": "ListItem", "position": 2, "name": "Авангард и конструктивизм", "item": "https://beloliptsev.ru/modernizm/" },
    { "@type": "ListItem", "position": 3, "name": "Дом Мельникова", "item": "%(url)s" }
  ]
}</script>
<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": ["LandmarkOrHistoricalBuilding", "Place"],
  "name": "Дом Мельникова",
  "alternateName": "Дом-мастерская К. С. Мельникова",
  "description": "Дом-мастерская архитектора Константина Мельникова, 1927–1929. Два врезанных друг в друга цилиндра с шестиугольными проёмами. Объект культурного наследия федерального значения, филиал Государственного музея архитектуры имени Щусева.",
  "url": "%(url)s",
  "address": { "@type": "PostalAddress", "streetAddress": "Кривоарбатский переулок, 10", "addressLocality": "Москва", "addressRegion": "Арбат, ЦАО", "postalCode": "119002", "addressCountry": "RU" },
  "geo": { "@type": "GeoCoordinates", "latitude": %(lat)s, "longitude": %(lon)s },
  "yearBuilt": "1929",
  "architect": { "@type": "Person", "name": "Константин Степанович Мельников", "birthDate": "1890", "deathDate": "1974" }
}</script>
<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    %(faq)s
  ]
}</script>""" % {"url": URL, "lat": LAT, "lon": LON, "faq": faq}


HERO = """<section class="hp-hero hp-hero--building" data-screen-label="S1 · Геро">
  <div class="hp-hero__img" style="background:#1B2230"></div>
  <img src="/assets/logo-seal-light.svg" alt="" aria-hidden="true" style="position:absolute;right:-70px;top:50%;transform:translateY(-50%);width:560px;max-width:60vw;opacity:.06;pointer-events:none">
  <div class="hp-hero__scrim"></div>
  <span class="hp-year">1929</span>
  <span class="hp-spine">Кривоарбатский переулок 10 · Арбат, ЦАО</span>
  <div class="hp-plate">
    <nav class="hp-crumbs" aria-label="Хлебные крошки">
      <a href="/">Главная</a><span class="sep">→</span><a href="/modernizm/">Авангард и конструктивизм</a><span class="sep">→</span><span>Дом Мельникова</span>
    </nav>
    <p class="hp-eyebrow">Дом-мастерская архитектора · памятник федерального значения</p>
    <h1 class="hp-h1">Дом Мельникова<span class="ln2">единственный частный дом эпохи авангарда</span></h1>
    <p class="hp-desc">Два врезанных друг в друга цилиндра, которые Константин Мельников построил для себя и семьи в 1927–1929 годах. Сегодня это музей — квартиры покупают в арбатских переулках вокруг него.</p>
    <div class="hp-chips"><span>1927–1929</span><span>Константин Мельников</span><span>памятник федерального значения</span><span>музей</span></div>
    <a class="st-btn st-btn--orange hp-cta" href="#cta"><span class="st-btn__lab">Подобрать квартиру в арбатских переулках</span><span class="st-btn__cap"><svg><use href="#i-arr"></use></svg></span></a>
  </div>
</section>"""

ISTORIYA = """<section class="st-section st-section--paper" data-screen-label="S2 · История">
  <div class="st-wrap st-pad">
    <div class="st-secthead reveal">
      <span class="st-eyebrow">02 · Разрешение на частный дом в эпоху обобществлённого жилья — исключение, которого не получил больше никто</span>
      <h2 class="st-h2">Дом, который архитектор построил для самого себя</h2>
    </div>
    <div class="st-def">
      <div class="st-def__cols reveal" style="border-top:0;margin-top:0">
        <p>Константин Степанович Мельников (1890–1974) к концу 1920-х был архитектором с мировым именем: павильон СССР на парижской выставке 1925 года принёс ему известность за пределами страны. В 1927 году он получил разрешение построить в Кривоарбатском переулке собственный дом — редчайший случай для времени, когда жильё строили обобществлённым.</p>
        <p>Проект утвердили в июне 1927 года, строительство заняло два года, и в ноябре 1929-го семья переехала сюда из коммунальной квартиры, где жила с 1918 года. Мельников работал и жил в этом доме до конца жизни, до 1974 года.</p>
      </div>
      <div class="st-def__cols reveal" style="margin-top:34px;border-top:0">
        <p>Дальше началась история, которая для покупателя памятников поучительнее любой архитектурной лекции. Раздел дома между детьми архитектора занял восемь лет судов, с 1988 по 1996 год. Затем спор перешёл в следующее поколение и окончательно прекратился только в марте 2017-го. Половину дома в 2010 году выкупил и передал государству частный владелец, ещё четверть осталась у наследниц.</p>
        <p>Для рынка недвижимости Кривоарбатский переулок — это соседство с постройкой, которую знают по мировым учебникам архитектуры. Сам дом не продаётся никогда, но адрес работает на весь квартал арбатских переулков.</p>
      </div>
      <div class="mz-epoch reveal" style="margin-top:50px">
        <div class="mz-epoch__row"><div class="mz-epoch__year">1925</div><div><p class="mz-epoch__note">Павильон СССР в Париже приносит Мельникову международную известность.</p></div></div>
        <div class="mz-epoch__row"><div class="mz-epoch__year">1927</div><div><p class="mz-epoch__note">В июне утверждён проект дома-мастерской в Кривоарбатском переулке.</p></div></div>
        <div class="mz-epoch__row"><div class="mz-epoch__year">1929</div><div><p class="mz-epoch__note">В ноябре семья переезжает в новый дом из коммунальной квартиры.</p></div></div>
        <div class="mz-epoch__row"><div class="mz-epoch__year">1974</div><div><p class="mz-epoch__note">Архитектор умирает в доме, где прожил и проработал сорок пять лет.</p></div></div>
        <div class="mz-epoch__row"><div class="mz-epoch__year">1987</div><div><p class="mz-epoch__note">Дом получает статус памятника регионального значения.</p></div></div>
        <div class="mz-epoch__row"><div class="mz-epoch__year">2006</div><div><p class="mz-epoch__note">Попадает в перечень ста памятников мира под угрозой Всемирного фонда памятников.</p></div></div>
        <div class="mz-epoch__row"><div class="mz-epoch__year">2014</div><div><p class="mz-epoch__note">Статус памятника федерального значения; учреждён филиал-музей.</p></div></div>
        <div class="mz-epoch__row"><div class="mz-epoch__year">2023</div><div><p class="mz-epoch__note">Начинается первая полноценная научная реставрация здания.</p></div></div>
      </div>
    </div>
  </div>
</section>"""

ARHITEKTURA = """<section class="st-section st-section--dark" data-screen-label="S3 · Архитектура">
  <div class="st-wrap st-pad">
    <div class="st-secthead reveal">
      <span class="st-eyebrow">03 · Два цилиндра, шестиугольные проёмы и перекрытия, в которых нет ни одной балки</span>
      <h2 class="st-h2">Конструкция без единой внутренней опоры</h2>
    </div>
    <div class="bld-stat3 reveal">
      <div class="bld-stat3__c"><div class="bld-stat3__n">2</div><div class="bld-stat3__t">Врезанных цилиндра</div><div class="bld-stat3__d">Одного диаметра и разной высоты — план в форме восьмёрки, ориентированной с севера на юг.</div></div>
      <div class="bld-stat3__c"><div class="bld-stat3__n" data-no-countup>124 / 64</div><div class="bld-stat3__t">Проёмов устроено и остеклено</div><div class="bld-stat3__d">Счёт самого Мельникова: из 124 шестиугольных проёмов 64 стали окнами и нишами, остальные заложены кирпичом.</div></div>
      <div class="bld-stat3__c"><div class="bld-stat3__n" data-no-countup>0,5 м</div><div class="bld-stat3__t">Ячейка перекрытия</div><div class="bld-stat3__d">Поставленные на ребро доски пересекаются под прямым углом — мембрана без колонн и балок.</div></div>
    </div>
    <div class="bld-cols-dark reveal">
      <p>Кирпичная кладка с шестиугольными проёмами работает как несущий каркас: нагрузка распределяется по всей плоскости стены, поэтому внутри нет ни одной опоры и пространство остаётся свободным. Верхний уровень — мастерская со сплошным остеклением, дающим ровный рассеянный свет для работы. Сколько в доме этажей, вопрос открытый: уровни цилиндров смещены относительно друг друга, и сам архитектор шутил, что даст премию тому, кто их сосчитает.</p>
      <p>Стиль дома принято называть авангардом. Мельников не входил ни в одну архитектурную группировку и сознательно держал дистанцию от конструктивистов — Весниных и Гинзбурга, хотя популярные источники до сих пор по инерции пишут «конструктивизм». Разница не формальная: она объясняет, почему дом не похож ни на одну другую постройку эпохи.</p>
    </div>
  </div>
</section>"""


def faq_section():
    items = "".join(
        '      <div class="st-faq__item">\n'
        '        <button class="st-faq__q"><span class="st-spark"></span><h4>%s</h4>'
        '<span class="st-faq__chev"><svg><use href="#i-arr"></use></svg></span></button>\n'
        '        <div class="st-faq__body"><div class="st-faq__inner"><p>%s</p></div></div>\n'
        '      </div>\n' % (nb(q), nb(a)) for q, a in FAQ)
    return ('<section class="st-section st-section--paper" data-screen-label="S8 · FAQ" style="padding-top:0">\n'
            '  <div class="st-wrap st-pad">\n'
            '    <div class="st-secthead reveal">\n'
            '      <span class="st-eyebrow">Люди также спрашивают</span>\n'
            '      <h2 class="st-h2">Частые вопросы о&nbsp;Доме Мельникова</h2>\n'
            '    </div>\n    <div class="st-faq reveal">\n' + items +
            '    </div>\n  </div>\n</section>')


def load_sections():
    raw = open(SECTIONS_FILE, encoding="utf-8").read()
    out, cur, buf = {}, None, []
    for line in raw.splitlines():
        m = re.match(r"<!--§(.+?)-->", line.strip())
        if m:
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        elif cur:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return out


def replace_section(html, label, new_html):
    """Меняет секцию целиком по её data-screen-label."""
    rx = re.compile(r'<section[^>]*data-screen-label="' + re.escape(label) + r'".*?</section>', re.S)
    if not rx.search(html):
        raise SystemExit(f"донор: секция «{label}» не найдена — сборка остановлена")
    return rx.sub(lambda _: new_html, html, count=1)


def main():
    dry = "--dry" in sys.argv
    s = open(DONOR, encoding="utf-8").read()

    # ── голова ──
    s = re.sub(r"<!-- @dsCard.*?-->", lambda _: DSCARD, s, count=1, flags=re.S)
    s = re.sub(r"<title>.*?</title>", lambda _: f"<title>{TITLE}</title>", s, count=1, flags=re.S)
    s = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + DESC + m.group(2), s, count=1)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + TITLE + m.group(2), s, count=1)
    s = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + OG_DESC + m.group(2), s, count=1)
    s = re.sub(r'(<meta property="og:url" content=")[^"]*(")', lambda m: m.group(1) + URL + m.group(2), s, count=1)
    s = re.sub(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + URL + m.group(2), s, count=1)
    s = s.replace("/ui_kits/website/modernizm--dom-isakova.css", "/ui_kits/website/modernizm--section.css")

    # все блоки микроразметки донора заменяем своими
    first = s.find('<script type="application/ld+json">')
    last = s.rfind("</script>", 0, s.find("<script src=")) + len("</script>")
    if first < 0 or last <= first:
        raise SystemExit("не нашёл блок JSON-LD в доноре")
    s = s[:first] + head_jsonld() + s[last:]

    # ── секции ──
    sec = load_sections()
    s = replace_section(s, "S1 · Геро", nb(HERO))
    s = replace_section(s, "S2 · История", nb(ISTORIYA))
    s = replace_section(s, "S3 · Архитектура", nb(ARHITEKTURA))
    s = replace_section(s, "S4 · Премиум-окружение", nb(sec["S4 · Премиум-окружение"]))
    s = replace_section(s, "S5 · Голос эксперта", nb(sec["S5 · Голос эксперта"]))
    s = replace_section(s, "S6 · Модерн в&nbsp;контексте авангарда", nb(sec["S6 · Авангард в контексте"]))
    s = replace_section(s, "S7 · Что&nbsp;знать", nb(sec["S7 · Что знать"]))
    s = replace_section(s, "S8 · FAQ", faq_section())
    s = replace_section(s, "S10 · Связанные объекты", nb(sec["S9 · Связанные объекты"]))

    # ── карта: три источника координат обязаны совпасть ──
    s = re.sub(r'<div class="ya-map"[^>]*>',
               '<div class="ya-map" data-yamap data-center="%s,%s" data-zoom="16" '
               'data-points=\'[{"c":[%s,%s],"t":"Дом Мельникова · Кривоарбатский переулок, 10"}]\'>'
               % (LAT, LON, LAT, LON), s, count=1)

    if dry:
        print(f"(DRY) собрано {len(s)} символов, файл не записан"); return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(s)
    print(f"✅ {os.path.relpath(OUT, BASE)} — {len(s)} символов")
    return 0


if __name__ == "__main__":
    sys.exit(main())
