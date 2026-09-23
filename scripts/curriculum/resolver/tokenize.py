"""Character-class tokenizer: deterministic and dictionary-independent.

A word run is a maximal run of letters, digits and combining marks, joined by
an apostrophe or a hyphen only when both neighbours are letters. A Cyrillic
token is a run whose letters are all Cyrillic: `по-українськи` is one token,
and so is `будь-ласка` (the resolver fails it whole, it does not split it).
Unlike `scripts/pipeline/stress_annotator.py`, hyphenated compounds are never
split. Apostrophe spellings are normalised to `'` for lookup
(`sources.normalize_spelling`); the original bytes and offsets into the
unit's text are kept.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from scripts.curriculum.evidence import sources

APOSTROPHES = frozenset("'’ʼ`‘")
HYPHENS = frozenset("-‐‑")
SENTENCE_END = frozenset(".!?…")
# Skipped when deciding whether a token opens a sentence: space, quotes, brackets, dashes.
TRANSPARENT = frozenset(" \t\r\n \"'«»„“”‘’()[]{}—–-*")
ACCENTS = frozenset("́̀")
_HYPHEN_MAP = str.maketrans({ch: "-" for ch in HYPHENS})


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    kind: str  # cyrillic | latin | digits | mixed
    lookup: str
    sentence_initial: bool
    parts: tuple[str, ...]

    @property
    def end(self) -> int:
        return self.start + len(self.text)

    @property
    def capitalised(self) -> bool:
        return self.lookup[:1].isupper()

    @property
    def hyphenated(self) -> bool:
        return len(self.parts) > 1


def is_cyrillic(ch: str) -> bool:
    return "Ѐ" <= ch <= "ԯ"


def has_accent(text: str) -> bool:
    return any(ch in ACCENTS for ch in unicodedata.normalize("NFD", text))


def _word_char(ch: str) -> bool:
    return unicodedata.category(ch)[0] in "LMN"


def _letter(ch: str) -> bool:
    return unicodedata.category(ch)[0] in "LM"


def _kind(run: str) -> str:
    letters = [ch for ch in run if unicodedata.category(ch)[0] == "L" and ch not in APOSTROPHES]
    digits = any(unicodedata.category(ch) == "Nd" for ch in run)
    if not letters:
        return "digits" if digits else "mixed"
    if all(is_cyrillic(ch) for ch in letters):
        return "mixed" if digits else "cyrillic"
    if all("a" <= ch.lower() <= "z" for ch in letters):
        return "latin"
    return "mixed"


def lookup_form(text: str) -> str:
    normalised = sources.normalize_spelling(text).translate(_HYPHEN_MAP)
    return unicodedata.normalize("NFC", normalised)


def _sentence_initial(text: str, start: int) -> bool:
    i = start - 1
    while i >= 0 and text[i] in TRANSPARENT:
        i -= 1
    return i < 0 or text[i] in SENTENCE_END


def tokenize(text: str) -> list[Token]:
    """Every word run of `text`, in order. Punctuation and whitespace are not tokens."""
    tokens: list[Token] = []
    i, n = 0, len(text)
    while i < n:
        if not _word_char(text[i]):
            i += 1
            continue
        start = i
        while i < n:
            if _word_char(text[i]) or (
                (text[i] in APOSTROPHES or text[i] in HYPHENS)
                and i + 1 < n
                and _letter(text[i - 1])
                and _letter(text[i + 1])
            ):
                i += 1
            else:
                break
        run = text[start:i]
        lookup = lookup_form(run)
        parts = tuple(lookup.split("-"))
        tokens.append(Token(run, start, _kind(run), lookup, _sentence_initial(text, start), parts))
    return tokens
