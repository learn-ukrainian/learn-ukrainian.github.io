"""Quote-host byte checks (issue #9487 gate C12), shared by plan-validate and the fresh preflight.

The engine prints a quote record's bytes exactly (writer contract §1), so a quote host whose bytes
carry OCR damage reaches the learner as "the textbook". Four classes are decided from the bytes:

  private_use           a private-use code point (Unicode category Co, every plane): a glyph only
                        the source PDF's font could draw
  transcription_symbol  inside a transcription bracket (a ``[…]`` holding a Cyrillic letter), a
                        character that is not a Cyrillic letter, a combining mark, white space, a
                        prime or apostrophe, ``|``, ``-`` or a length mark; a bracket without a
                        Cyrillic letter is a primer scheme (``[ = • – ]``) and is not read
  watermark             a web address (``http…``, ``www.…`` or a dotted name ending in a top-level
                        domain), such as a publisher's page watermark
  not_in_vesum          a word of the quote, outside brackets, that is neither a spelling of a
                        word-store record nor a VESUM word form

How exact ``not_in_vesum`` is: a primer prints letters and syllables, which are not words, so a token
with at most one vowel letter is not looked up. A hyphenated token whose parts each hold at most
one vowel is a word printed with its syllables divided (``ма-ма``); it passes when the joined
spelling is a word. A word hyphenated at a line end is joined first: that is the page's typesetting. Stress marks (U+0301, U+0300) are removed before the lookup; apostrophes are
normalised to one spelling, as the word store and VESUM do. The lookup is the existing
verification path (``scripts.verification.vesum.verify_words``) after the word store; when VESUM
is unavailable the class is not decided and the caller reports that.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from scripts.practice.euphony_stem_engine import VOWELS as VOWEL_LETTERS

from .scope import CYRILLIC_LETTER_CLASS

PRIVATE_USE = "private_use"
TRANSCRIPTION_SYMBOL = "transcription_symbol"
WATERMARK = "watermark"
NOT_IN_VESUM = "not_in_vesum"

_BRACKET = re.compile(r"\[([^\[\]]*)\]")
_CYRILLIC = re.compile(f"[{CYRILLIC_LETTER_CLASS}]")
_TOKEN = re.compile(f"[{CYRILLIC_LETTER_CLASS}]+(?:['’ʼ-][{CYRILLIC_LETTER_CLASS}]+)*")
#: A word the page hyphenated at a line end (``предме-\nтів``): one word, as printed.
_LINE_BREAK_HYPHEN = re.compile(f"([{CYRILLIC_LETTER_CLASS}])-[ \t]*\n[ \t]*([{CYRILLIC_LETTER_CLASS}])")
_WEB_ADDRESS = re.compile(
    r"(?i)\bhttps?://\S+|\bwww\.\S+|\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:com|net|org|info|edu|gov|biz|ua|ru|io)\b"
)
#: Characters a transcription may carry besides Cyrillic letters, combining marks and white space.
_TRANSCRIPTION_MARKS = frozenset("′ʹ'’ʼ|-:ː")
_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'"})
_STRESS = str.maketrans({"́": None, "̀": None})


class VesumUnavailable(Exception):
    """The VESUM database cannot be read, so not_in_vesum is not decided."""


@dataclass(frozen=True)
class QuoteDefect:
    kind: str
    detail: str


@dataclass(frozen=True)
class WordToken:
    """A word of a quote: as printed, and the spellings any one of which makes it a word."""

    surface: str
    spellings: tuple[str, ...]


def _is_transcription_character(char: str) -> bool:
    if char.isspace() or char in _TRANSCRIPTION_MARKS:
        return True
    category = unicodedata.category(char)
    if category.startswith("M"):
        return True
    return category.startswith("L") and unicodedata.name(char, "").startswith("CYRILLIC")


def byte_defects(text: str) -> list[QuoteDefect]:
    """The private_use, transcription_symbol and watermark defects of a quote's bytes."""
    defects: list[QuoteDefect] = []
    private = sorted({f"U+{ord(char):04X}" for char in text if unicodedata.category(char) == "Co"})
    if private:
        defects.append(QuoteDefect(PRIVATE_USE, ", ".join(private)))
    for bracket in _BRACKET.finditer(text):
        body = bracket.group(1)
        if not _CYRILLIC.search(body):
            continue  # a primer scheme, not a transcription
        foreign = sorted({char for char in body if not _is_transcription_character(char)})
        if foreign:
            shown = ", ".join(f"{char!r} (U+{ord(char):04X})" for char in foreign)
            defects.append(QuoteDefect(TRANSCRIPTION_SYMBOL, f"{bracket.group(0)!r} holds {shown}"))
    addresses = list(dict.fromkeys(match.group(0) for match in _WEB_ADDRESS.finditer(text)))
    if addresses:
        defects.append(QuoteDefect(WATERMARK, ", ".join(repr(address) for address in addresses)))
    return defects


def _vowels(text: str) -> int:
    return sum(1 for char in text.casefold() if char in VOWEL_LETTERS)


def _spelling(text: str) -> str:
    return text.translate(_STRESS).translate(_APOSTROPHES)


def word_tokens(text: str) -> list[WordToken]:
    """The words of a quote outside brackets that need a lookup, in order, once each."""
    outside = _LINE_BREAK_HYPHEN.sub(r"\1\2", _BRACKET.sub(" ", text.translate(_STRESS)))
    tokens: dict[str, WordToken] = {}
    for match in _TOKEN.finditer(outside):
        surface = match.group(0)
        parts = re.split(r"-", surface)
        if "-" in surface and all(_vowels(part) <= 1 for part in parts):
            joined = "".join(parts)
            if _vowels(joined) <= 1:
                continue
            spellings = (_spelling(joined), _spelling(surface))
        elif _vowels(surface) <= 1:
            continue  # a letter or a syllable, as a primer prints them
        else:
            spellings = (_spelling(surface),)
        tokens.setdefault(surface, WordToken(surface, spellings))
    return list(tokens.values())


def _variants(spelling: str) -> tuple[str, str]:
    return spelling, spelling.casefold()


def unknown_words(tokens: Iterable[WordToken], known: set[str], lookup: Callable[[list[str]], set[str]]) -> list[str]:
    """Surfaces of tokens that are no word-store spelling (known: case-folded) and no VESUM form.

    Raises VesumUnavailable when a lookup is needed and VESUM cannot be read."""
    pending = [token for token in tokens if not any(spelling.casefold() in known for spelling in token.spellings)]
    keys = sorted({key for token in pending for spelling in token.spellings for key in _variants(spelling)})
    found = lookup(keys) if keys else set()
    return [
        token.surface
        for token in pending
        if not any(key in found for spelling in token.spellings for key in _variants(spelling))
    ]


def vesum_lookup(words: list[str]) -> set[str]:
    """The words VESUM lists as a form, through the existing verification path."""
    import sqlite3

    from scripts.verification.vesum import verify_words

    try:
        matches = verify_words(words)
    except (FileNotFoundError, sqlite3.Error) as error:
        raise VesumUnavailable(str(error)) from error
    return {word for word, rows in matches.items() if rows}


def known_spellings(spellings: Iterable[str]) -> set[str]:
    """The word-store spellings, normalised for unknown_words."""
    return {_spelling(spelling).casefold() for spelling in spellings}
