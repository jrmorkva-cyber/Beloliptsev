# -*- coding: utf-8 -*-
"""
textextract.py — ЕДИНСТВЕННАЯ реализация «видимого текста» страницы.

До этого модуля логика была скопирована в test_pages.py и qa-lint.py двумя
слегка разными копиями — и обе несли один и тот же баг:

    if "<style" in low and "</style>" not in low: inblock = "style"; continue

Флаг блока ставился ТОЛЬКО когда открывающий и закрывающий теги на РАЗНЫХ
строках. Если <style>…</style> или <script>…</script> помещались в одну строку
(так свёрстаны все 15 страниц авангарда, строка 51), блок не помечался, и
regex r">([^<]+)<" вытаскивал весь CSS/JS как «видимый текст». Результат —
82 ложные находки «латиница в прозе» на токенах backdrop, webkit,
addEventListener и т.п.

Фикс: полностью-однострочные блоки и комментарии вырезаются regex-проходом
ДО посимвольного автомата.

Экспорт:
    visible_frags(html) -> list[str]   фрагменты, HTML-сущности СОХРАНЕНЫ
                                       (нужно для типографики: &nbsp; значим)
    strip_ent(text)     -> str         сущности → пробелы
    visible_text(html)  -> str         всё видимое одной строкой, без сущностей
    word_count(html)    -> int         число видимых слов длиннее 1 символа
"""
import re

# Полностью-однострочные <script>…</script> и <style>…</style>.
# .*? нежадный — две пары в одной строке не схлопнутся в одну.
SAME_LINE_BLOCK = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.I | re.S)
SAME_LINE_COMMENT = re.compile(r"<!--.*?-->", re.S)
ENTITY = re.compile(r"&[a-zA-Z]+;|&#\d+;")


def strip_same_line_blocks(line):
    """Убирает из строки целиком помещающиеся в неё script/style/комментарии."""
    line = SAME_LINE_BLOCK.sub(" ", line)
    return SAME_LINE_COMMENT.sub(" ", line)


def visible_frags(html):
    """Видимые текст-фрагменты. Сущности сохранены — типографике они нужны."""
    out, inblock = [], None
    for raw in html.splitlines():
        raw = strip_same_line_blocks(raw)          # ← фикс однострочных блоков
        low = raw.lower()
        if inblock:
            if (inblock == "comment" and "-->" in low) or (f"</{inblock}>" in low):
                inblock = None
            continue
        if "<!--" in low and "-->" not in low:
            inblock = "comment"; continue
        if "<script" in low and "</script>" not in low:
            inblock = "script"; continue
        if "<style" in low and "</style>" not in low:
            inblock = "style"; continue
        parts = re.findall(r">([^<]+)(?:<|$)", raw)
        head = re.match(r"^([^<]*)<", raw)
        if head:
            parts.append(head.group(1))
        out.extend(p for p in parts if p.strip())
    return out


def visible_parts_line(line):
    """Видимые фрагменты ОДНОЙ строки (для построчных линтеров с номерами строк).
    Однострочные script/style/комментарии вырезаются здесь же."""
    line = strip_same_line_blocks(line)
    parts = re.findall(r">([^<]+)(?:<|$)", line)
    head = re.match(r"^([^<]*)<", line)
    if head:
        parts.append(head.group(1))
    return parts


def strip_ent(text):
    return ENTITY.sub(" ", text)


def visible_text(html):
    return strip_ent(" ".join(visible_frags(html)))


def word_count(html):
    return len([w for w in visible_text(html).split() if len(w) > 1])
