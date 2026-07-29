# -*- coding: utf-8 -*-
"""
Сборка прод-страниц зданий раздела.

Usage:
    python tools/pages/build.py dk_zueva [dom_artistov_mhat ...]
    python tools/pages/build.py --all
    python tools/pages/build.py --all --dry

Конфиг каждого здания — модуль <имя>.py со словарём CFG, проза — <slug>.sections.html.
"""
import os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _common import build  # noqa: E402


def load_cfg(mod_name):
    path = os.path.join(HERE, mod_name + ".py")
    if not os.path.exists(path):
        raise SystemExit(f"нет конфига: {path}")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CFG


def main():
    dry = "--dry" in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        names = sorted(f[:-3] for f in os.listdir(HERE)
                       if f.endswith(".py") and f not in ("_common.py", "build.py", "__init__.py"))
    if not names:
        raise SystemExit("укажи имя конфига или --all")
    for n in names:
        build(load_cfg(n), dry=dry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
