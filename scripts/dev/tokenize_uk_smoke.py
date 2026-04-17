#!/usr/bin/env python3
"""Reproduce the #1318 tokenize-uk proof-point smoke test.

Prints a side-by-side comparison of the old regex-based sentence
splitter (``re.split(r'[.!?—:]', …)``) vs the vendored
``linguistics.tokenize_uk.tokenize_sents``. This is the evidence
referenced in the #1318 evaluation memo.

Usage::

    .venv/bin/python scripts/dev/tokenize_uk_smoke.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from linguistics.tokenize_uk import tokenize_sents


def old_splitter(text: str) -> list[str]:
    """The regex the audit pipeline used before #1318."""
    parts = re.split(r"[.!?—:]", text)
    return [p.strip() for p in parts if p.strip()]


SAMPLES: list[tuple[str, str]] = [
    (
        "A1 dialogue + abbreviations (the 5-sentence proof point)",
        "Київ — столиця України. Україна стала незалежною 1991 р.\n"
        "— Привіт, Олено! Як справи?\n"
        "— Дякую, добре.\n"
        "У XIX ст. у Києві жили видатні письменники: Леся Українка, Іван Франко.\n"
        "Згадаймо факти: площа країни становить 603 тис. кв. км.",
    ),
    (
        "B1 skeleton excerpt (address abbreviations)",
        "Музей розміщено в м. Києві на вул. Б. Хмельницького, 11 "
        "(ст. м. «Театральна»). У 1953 р. відбувся перехід. "
        "Проф. Іванов писав про це.",
    ),
    (
        "Seminar bibliography (surname + initial)",
        "Іванюк С. Нарис з історії. — К. : Наук. думка, 2009. — 508 с. "
        "Наступна праця виходила пізніше.",
    ),
]


def main() -> int:
    for label, text in SAMPLES:
        print(f"\n=== {label} ===")
        print("input:")
        for line in text.splitlines():
            print(f"  {line}")

        old = old_splitter(text)
        new: list[str] = []
        for paragraph in text.split("\n"):
            if paragraph.strip():
                new.extend(tokenize_sents(paragraph))

        print(f"\n  old regex splitter (re.split(r'[.!?—:]', …)) → {len(old)} fragments:")
        for i, s in enumerate(old, 1):
            print(f"    {i}. {s!r}")

        print(f"\n  vendored tokenize_sents → {len(new)} sentences:")
        for i, s in enumerate(new, 1):
            print(f"    {i}. {s!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
