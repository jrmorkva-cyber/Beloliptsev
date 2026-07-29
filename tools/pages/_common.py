# -*- coding: utf-8 -*-
"""
Общая машинерия сборки прод-страниц зданий раздела «Авангард и конструктивизм».

Донор обвязки — deploy/modernizm/dom-isakova/index.html: шапка, подвал, мегаменю,
скрипты и набор из 11 секций там соответствуют канону раздела. Сборка меняет
голову и содержимое секций; разметку не изобретаем.

На каждое здание нужны два файла рядом:
  <slug>.py             — конфиг: голова, координаты, FAQ
  <slug>.sections.html  — проза секций, разделённая маркерами <!--§Название-->

Текст отделён от кода намеренно: правка копии не должна требовать трогать скрипт.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
DONOR = os.path.join(BASE, "deploy", "modernizm", "dom-isakova", "index.html")

# Донорские метки секций — по ним ищем, что заменить.
DONOR_LABELS = {
    "hero":     "S1 · Геро",
    "istoriya": "S2 · История",
    "arh":      "S3 · Архитектура",
    "okr":      "S4 · Премиум-окружение",
    "golos":    "S5 · Голос эксперта",
    "kontekst": "S6 · Модерн в&nbsp;контексте авангарда",
    "znat":     "S7 · Что&nbsp;знать",
    "faq":      "S8 · FAQ",
    "svyaz":    "S10 · Связанные объекты",
}

SHORT = ("в во на за по до от из с со к о об у и а но не ни что как для при без над под про через "
         "это его её их том той тех").split()
UNITS = ("млн|млрд|тыс|м²|км²|км|м|лет|мин|год\\w*|этаж\\w*|квартир\\w*|мест|₽|%")


def _nb_text(t):
    t = re.sub(r"(?<![\w&;])(%s)\s+(?=[«\w])" % "|".join(SHORT), r"\1&nbsp;", t, flags=re.I)
    return re.sub(r"(\d)\s(%s)\b" % UNITS, r"\1&nbsp;\2", t)


def nb(html):
    """§8: неразрывный пробел после коротких слов и в связке «число + единица».

    Работает ТОЛЬКО по текстовым узлам. Раньше применялось ко всей строке разом
    и портило атрибуты: data-screen-label="S7 · Что знать" превращался
    в "Что&nbsp;знать", из-за чего секцию потом было не найти по метке.

    Голая строка без тегов (вопрос и ответ FAQ приходят именно такими)
    обрабатывается целиком — иначе типографика к ней просто не применялась бы.
    """
    if "<" not in html:
        return _nb_text(html)
    return re.sub(r">([^<]+)<", lambda m: ">" + _nb_text(m.group(1)) + "<", html)


def esc(s):
    return s.replace('"', '\\"')


def faq_section(faq, building_name):
    items = "".join(
        '      <div class="st-faq__item">\n'
        '        <button class="st-faq__q"><span class="st-spark"></span><h4>%s</h4>'
        '<span class="st-faq__chev"><svg><use href="#i-arr"></use></svg></span></button>\n'
        '        <div class="st-faq__body"><div class="st-faq__inner"><p>%s</p></div></div>\n'
        '      </div>\n' % (nb(q), nb(a)) for q, a in faq)
    return ('<section class="st-section st-section--paper" data-screen-label="S8 · FAQ" style="padding-top:0">\n'
            '  <div class="st-wrap st-pad">\n    <div class="st-secthead reveal">\n'
            '      <span class="st-eyebrow">Люди также спрашивают</span>\n'
            '      <h2 class="st-h2">%s</h2>\n    </div>\n    <div class="st-faq reveal">\n'
            % nb("Частые вопросы: " + building_name) + items + '    </div>\n  </div>\n</section>')


def jsonld(cfg):
    faq = ",\n    ".join(
        '{ "@type": "Question", "name": "%s", "acceptedAnswer": { "@type": "Answer", "text": "%s" } }'
        % (esc(q), esc(a)) for q, a in cfg["faq"])
    arch = ""
    if cfg.get("architect"):
        a = cfg["architect"]
        arch = (',\n  "architect": { "@type": "Person", "name": "%s"%s%s }'
                % (a["name"],
                   ', "birthDate": "%s"' % a["born"] if a.get("born") else "",
                   ', "deathDate": "%s"' % a["died"] if a.get("died") else ""))
    return """<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Главная", "item": "https://beloliptsev.ru/" },
    { "@type": "ListItem", "position": 2, "name": "Авангард и конструктивизм", "item": "https://beloliptsev.ru/modernizm/" },
    { "@type": "ListItem", "position": 3, "name": "%(name)s", "item": "%(url)s" }
  ]
}</script>
<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": ["LandmarkOrHistoricalBuilding", "Place"],
  "name": "%(name)s",
  "description": "%(schema_desc)s",
  "url": "%(url)s",
  "address": { "@type": "PostalAddress", "streetAddress": "%(street)s", "addressLocality": "Москва", "addressRegion": "%(region)s", "addressCountry": "RU" },
  "geo": { "@type": "GeoCoordinates", "latitude": %(lat)s, "longitude": %(lon)s },
  "yearBuilt": "%(year)s"%(arch)s
}</script>
<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    %(faq)s
  ]
}</script>""" % dict(cfg, faq=faq, arch=arch)


def load_sections(slug):
    raw = open(os.path.join(HERE, slug + ".sections.html"), encoding="utf-8").read()
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
    rx = re.compile(r'<section[^>]*data-screen-label="' + re.escape(label) + r'".*?</section>', re.S)
    if not rx.search(html):
        raise SystemExit(f"донор: секция «{label}» не найдена — сборка остановлена")
    return rx.sub(lambda _: new_html, html, count=1)


def build(cfg, dry=False):
    slug = cfg["slug"]
    s = open(DONOR, encoding="utf-8").read()

    s = re.sub(r"<!-- @dsCard.*?-->", lambda _: cfg["dscard"], s, count=1, flags=re.S)
    s = re.sub(r"<title>.*?</title>", lambda _: "<title>%s</title>" % cfg["title"], s, count=1, flags=re.S)
    for attr, val in (('<meta name="description" content="', cfg["desc"]),
                      ('<meta property="og:title" content="', cfg["title"]),
                      ('<meta property="og:description" content="', cfg["og_desc"]),
                      ('<meta property="og:url" content="', cfg["url"]),
                      ('<link rel="canonical" href="', cfg["url"])):
        s = re.sub(re.escape(attr) + r'[^"]*"', lambda _, a=attr, v=val: a + v + '"', s, count=1)
    s = s.replace("/ui_kits/website/modernizm--dom-isakova.css", "/ui_kits/website/modernizm--section.css")

    first = s.find('<script type="application/ld+json">')
    last = s.rfind("</script>", 0, s.find("<script src=")) + len("</script>")
    if first < 0 or last <= first:
        raise SystemExit("не нашёл блок JSON-LD в доноре")
    s = s[:first] + jsonld(cfg) + s[last:]

    sec = load_sections(slug)
    for key, label in DONOR_LABELS.items():
        if key == "faq":
            s = replace_section(s, label, faq_section(cfg["faq"], cfg["name"]))
        else:
            if key not in sec:
                raise SystemExit(f"{slug}: в файле секций нет блока «{key}»")
            s = replace_section(s, label, nb(sec[key]))

    s = re.sub(r'<div class="ya-map"[^>]*>',
               '<div class="ya-map" data-yamap data-center="%s,%s" data-zoom="16" '
               'data-points=\'[{"c":[%s,%s],"t":"%s"}]\'>'
               % (cfg["lat"], cfg["lon"], cfg["lat"], cfg["lon"], cfg["map_label"]), s, count=1)

    out = os.path.join(BASE, "deploy", "modernizm", slug, "index.html")
    if dry:
        print(f"(DRY) {slug}: {len(s)} символов"); return s
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(s)
    print(f"✅ deploy/modernizm/{slug}/index.html — {len(s)} символов")
    return s
