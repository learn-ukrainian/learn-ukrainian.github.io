"""The one lexdata normalizer (design r3 §4 "Normalizer steps"; r1 §L1).

Steps, in order, each recorded in ``norm_flags`` when it changes something:

1. ``html.unescape`` (``html_unescaped``). An entity that survives one pass is
   double escaping and is refused (``html_entity_residual``).
2. NFC. The result is ``surface``; ``nfc_changed`` when it differs.
3. Apostrophe unification to the VESUM convention (``scripts/verification/
   vesum.py`` ``_normalize_apostrophes``: U+2019 and U+02BC become U+0027).
   Keys only; ``surface`` keeps the original character (``apostrophe_unified``).
4. Mixed-script refusal: Cyrillic letters together with Latin or Greek letters
   are ``homoglyph_mixed_script``. The lookalike table may only *propose* a
   repair; nothing is repaired. Letters of any other script, or no Cyrillic
   letter at all, are ``foreign_script``.
5. Strip edge punctuation and whitespace (``edge_punctuation_stripped``).
6. Collapse whitespace runs to one space (``whitespace_collapsed``).
7. Keys (``scripts/lexdata/stress.py``): ``key_stressed`` keeps U+0301,
   ``key_unstressed`` drops U+0301 and U+0300, ``key_fold`` is its casefold.
   Letters are never folded together (Ґ/г, і/и, є/е, ї/і stay distinct).

The normalizer never splits lists: list grammars split before it runs, per
child (§4). A refused span keeps ``surface`` and has NULL keys.
"""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass

from scripts.lexdata import stress
from scripts.lexdata.case_signal import derive_case_signal

NORMALIZER_VERSION = "1"
NORMALIZER_ID = "lexdata.normalize"

APOSTROPHES: dict[str, str] = {"’": "'", "ʼ": "'"}
EDGE_PUNCTUATION = frozenset(
    "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "«»„“”‘’‚‹›"  # « » „ “ ” ‘ ’ ‚ ‹ ›
    "…–—‐‑‒―·•¡¿§"  # … – — ‐ ‑ ‒ ― · • ¡ ¿ §
)
# Latin/Greek lookalikes of Cyrillic letters, used only to propose a repair
# (binding policy #6370; same Latin pairs as ohoiko_paired_headword_split).
HOMOGLYPHS: dict[str, str] = {
    "a": "а", "c": "с", "e": "е", "i": "і", "o": "о", "p": "р", "x": "х", "y": "у",
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "I": "І", "K": "К", "M": "М",
    "O": "О", "P": "Р", "T": "Т", "X": "Х",
    "ο": "о", "Ο": "О", "α": "а", "Α": "А",  # Greek omicron, alpha
}
ENTITY_RE = re.compile(r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class Normalized:
    surface: str
    key_stressed: str | None
    key_unstressed: str | None
    key_fold: str | None
    case_signal: str | None
    norm_flags: tuple[str, ...]
    refusal_code: str | None
    proposed_repairs: tuple[dict[str, str], ...] = ()

    @property
    def accepted(self) -> bool:
        return self.refusal_code is None


def letter_script(char: str) -> str:
    name = unicodedata.name(char, "")
    for script in ("CYRILLIC", "LATIN", "GREEK"):
        if name.startswith(script):
            return script.lower()
    return "other"


def _refused(surface: str, flags: list[str], code: str, repairs: tuple[dict[str, str], ...] = ()) -> Normalized:
    return Normalized(surface, None, None, None, None, tuple(flags), code, repairs)


def _strip_edges(text: str) -> str:
    start, end = 0, len(text)
    while start < end and (text[start] in EDGE_PUNCTUATION or text[start].isspace()):
        start += 1
    while end > start and (text[end - 1] in EDGE_PUNCTUATION or text[end - 1].isspace()):
        end -= 1
    return text[start:end]


def normalize_span(raw_span: str) -> Normalized:
    """Normalize one already-split dictionary span into its L1 fields."""
    flags: list[str] = []
    unescaped = html.unescape(raw_span)
    if unescaped != raw_span:
        flags.append("html_unescaped")
    surface = unicodedata.normalize("NFC", unescaped)
    if surface != unescaped:
        flags.append("nfc_changed")
    if not surface.strip():
        return _refused(surface, flags, "empty_span")
    if ENTITY_RE.search(surface):
        return _refused(surface, flags, "html_entity_residual")

    text = surface.translate(str.maketrans(APOSTROPHES))
    if text != surface:
        flags.append("apostrophe_unified")

    scripts = {letter_script(char) for char in text if char.isalpha()}
    if "cyrillic" in scripts and scripts & {"latin", "greek"}:
        repairs: tuple[dict[str, str], ...] = ()
        foreign = [char for char in text if char.isalpha() and letter_script(char) != "cyrillic"]
        if foreign and all(char in HOMOGLYPHS for char in foreign):
            proposal = "".join(HOMOGLYPHS.get(char, char) for char in surface)
            repairs = ({"kind": "latin_lookalike", "proposed": proposal, "proposer": NORMALIZER_ID},)
        return _refused(surface, flags, "homoglyph_mixed_script", repairs)
    if scripts - {"cyrillic"}:
        return _refused(surface, flags, "foreign_script")

    stripped = _strip_edges(text)
    if stripped != text:
        flags.append("edge_punctuation_stripped")
    collapsed = WHITESPACE_RE.sub(" ", stripped)
    if collapsed != stripped:
        flags.append("whitespace_collapsed")
    if not any(char.isalpha() for char in collapsed):
        return _refused(surface, flags, "no_letter")
    if not stress.stress_is_valid(collapsed):
        return _refused(surface, flags, "stress_invalid")

    key_stressed = stress.stressed_key(collapsed)
    if key_stressed != unicodedata.normalize("NFC", collapsed):
        flags.append("grave_removed")
    key_unstressed = stress.unstressed_key(collapsed)
    return Normalized(
        surface=surface,
        key_stressed=key_stressed,
        key_unstressed=key_unstressed,
        key_fold=key_unstressed.casefold(),
        case_signal=derive_case_signal(key_unstressed),
        norm_flags=tuple(flags),
        refusal_code=None,
    )


def table_contents() -> dict[str, object]:
    """Content-hashed normalizer tables (§6.1 "Normalizer")."""
    return {
        "apostrophes": {f"U+{ord(k):04X}": v for k, v in sorted(APOSTROPHES.items())},
        "edge_punctuation": sorted(f"U+{ord(c):04X}" for c in EDGE_PUNCTUATION),
        "homoglyphs": {f"U+{ord(k):04X}": v for k, v in sorted(HOMOGLYPHS.items())},
        "entity_pattern": ENTITY_RE.pattern,
        "whitespace_pattern": WHITESPACE_RE.pattern,
    }
