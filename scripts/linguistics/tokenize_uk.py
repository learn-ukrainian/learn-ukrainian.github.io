"""Ukrainian word/sentence tokenizer — vendored from lang-uk/tokenize-uk.

Upstream
--------
Repository : https://github.com/lang-uk/tokenize-uk
Version    : 0.2.0 (pushed 2023-11-01)
Authors    : (c) 2016 Vsevolod Dyomkin, (c) 2016 Dmitry Chaplinsky
License    : MIT

A verbatim copy of the MIT license is included in this repository at
``docs/third-party/tokenize-uk-LICENSE`` (added in the same commit that
introduced this vendored copy).

Rationale for vendoring (#1318)
-------------------------------
- ~3 KB single-file module; adding a PyPI dependency is overkill.
- Avoid the legacy ``six`` import path that upstream still uses.
- Let us extend :data:`ABBRS` locally with Ukrainian abbreviations
  observed in the ``curriculum/l2-uk-en/`` corpora (seminar + B1+
  address forms, bibliography initials) without forking upstream.

Local modifications
-------------------
- Dropped ``import six``: ``six.unichr`` → :func:`chr`,
  ``six.text_type`` → :class:`str`. Pure Python 3.
- Converted regex literals to raw strings (silences Python 3.12
  ``DeprecationWarning`` on invalid escape sequences; no behavior
  change — non-raw ``\\[`` still compiles to regex ``\\[``).
- Extended :data:`ABBRS` with corpus-verified entries. Each added
  entry appears at least once in our content AND would otherwise
  mis-split a real sentence. Do not add hypothetical entries —
  verify against the corpus first.

Public API
----------
- :func:`tokenize_words`
- :func:`tokenize_sents`
- :func:`tokenize_text`
- :data:`ABBRS`
"""

from __future__ import annotations

import re

# Combining acute accent (U+0301) — used as stress mark in A1 content.
ACCENT = chr(769)

WORD_TOKENIZATION_RULES = re.compile(
    r"""
[\w""" + ACCENT + r"""]+://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+
|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+
|[0-9]+-[а-яА-ЯіїІЇ'’`""" + ACCENT + r"""]+
|[+-]?[0-9](?:[0-9,.-]*[0-9])?
|[\w""" + ACCENT + r"""](?:[\w'’`-""" + ACCENT + r"""]?[\w""" + ACCENT + r"""]+)*
|[\w""" + ACCENT + r"""]\.(?:\[\w""" + ACCENT + r"""]\.)+[\w""" + ACCENT + r"""]?
|["#$%&*+,/:;<=>@^`~…\(\)⟨⟩{}\[\|\]‒–—―«»“”‘’'№]
|[.!?]+
|-+
""",
    re.X | re.U,
)

# ABBRS: abbreviations that end in '.' but are NOT sentence terminators.
#
# Each trailing '.' must be present (it's what we match against `tok`).
# The list is UNION of:
#   (a) upstream lang-uk/tokenize-uk v0.2.0 defaults
#   (b) local extensions verified by grepping curriculum/l2-uk-en/
#
# When adding a new entry, first prove it ACTUALLY occurs in our
# corpora AND that its presence mis-splits a real sentence. No
# hypothetical additions — they make the splitter permissive for
# categories we don't use, which degrades false-positive rates.
ABBRS = """
ім.
о.
вул.
просп.
бул.
пров.
пл.
г.
р.
див.
п.
с.
м.

обл.
буд.
кв.
проф.
доц.
канд.
каф.
коп.
ст.
тис.
грн.
км.
рр.
т.д.
т.п.
т.зв.
напр.
пор.
акад.
""".strip().split()

# Some Ukrainian abbreviations are ambiguous: they can be mid-sentence
# abbreviations (`у с. Вишневе`, `у 2024 р. відбулися`) or genuine
# sentence-final unit/page markers (`500 грн. Уряд`, `508 с. Наступна`).
# For these, suppressing *every* uppercase-following boundary is too blunt.
#
# The rule below allows a split when:
#   1. the abbreviation is in this context-sensitive set,
#   2. the previous token is numeric-like (digits or Roman numerals), and
#   3. the next token starts with an uppercase letter.
#
# That preserves:
#   - `у с. Вишневе`      (prev token = `у`, no split)
#   - `У 2024 р. ...`     (next token lowercase, no split)
# while fixing:
#   - `500 грн. Уряд...`
#   - `508 с. Наступна...`
_CONTEXT_SENSITIVE_ABBRS = {
    "грн.",
    "коп.",
    "км.",
    "р.",
    "рр.",
    "с.",
    "ст.",
    "тис.",
}

_NUMERIC_CONTEXT_RE = re.compile(
    r"^(?:[+-]?[0-9][0-9,.-]*|[IVXLCDM]+|[IVXLCDM]+[–-][IVXLCDM]+)$",
    re.IGNORECASE,
)


def _is_numeric_context_token(token: str) -> bool:
    """Return True when *token* looks like a numeric/unit context."""
    return bool(_NUMERIC_CONTEXT_RE.match(token.strip("()[]{}«»\"'“”‘’")))


def _blocks_sentence_break(tok_key: str, prev_tok: str, next_tok: str, tok1: str, tok: str) -> bool:
    """Return True when an abbreviation should suppress a sentence break."""
    if tok[-1] != "." or tok1[0] == "(" or tok_key not in ABBRS:
        return False
    return not (
        tok_key in _CONTEXT_SENSITIVE_ABBRS
        and next_tok
        and next_tok[0].isupper()
        and _is_numeric_context_token(prev_tok)
    )


def tokenize_words(string: str) -> list[str]:
    """Tokenize input text to words.

    Matches URLs, emails, numeric-prefixed Cyrillic suffixes (``1990-х``),
    decimals, hyphenated compounds, apostrophe forms (``м'який``),
    stress-marked words, and Ukrainian punctuation.
    """
    return re.findall(WORD_TOKENIZATION_RULES, str(string))


def tokenize_sents(string: str) -> list[str]:
    """Split text into sentences, aware of Ukrainian abbreviations.

    Algorithm (unchanged from upstream): iterate over whitespace-
    delimited spans. A span ending in ``. ! ? … »`` is a sentence
    boundary UNLESS:

    - the character before the terminator is uppercase (so ``Б.`` in
      ``вул. Б. Хмельницького`` stays attached — single-letter initials
      protection), OR
    - the character before the terminator is ``(``, OR
    - the terminator is ``.`` and the token is in :data:`ABBRS`,
      except for context-sensitive numeric/unit abbreviations like
      ``грн.`` / ``с.`` / ``ст.`` when they are sentence-final.
    """
    string = str(string)
    spans = list(re.finditer(r"[^\s]+", string))
    if not spans:
        return []

    result: list[str] = []
    offset = 0
    for i, span in enumerate(spans):
        tok = string[span.start():span.end()]
        if i == len(spans) - 1:
            result.append(string[offset:span.end()])
            continue
        if tok[-1] in (".", "!", "?", "…", "»"):
            # Upstream behavior: check the character immediately before
            # the FIRST terminator in the token (not the last). For
            # patterns like 'М.в.т.' this looks at 'М' — whose uppercase
            # flips `not tok1.isupper()` to False, keeping the token
            # attached. Mirror upstream exactly to preserve decisions
            # on multi-period tokens.
            term_match = re.search(r"[.!?…»]", tok)
            if term_match is None:  # Unreachable given tok[-1] check.
                continue
            tok1 = tok[term_match.start() - 1]
            prev_tok = string[spans[i - 1].start():spans[i - 1].end()] if i > 0 else ""
            next_tok = string[spans[i + 1].start():spans[i + 1].end()]
            # Case-insensitive ABBRS check: sentence-initial tokens like
            # 'Проф.' or 'Напр.' should match the lowercase ABBRS entries.
            # Local modification #1318; upstream compares case-sensitively.
            tok_key = tok.lower()
            if (
                next_tok[0].isupper()
                and not tok1.isupper()
                and not _blocks_sentence_break(tok_key, prev_tok, next_tok, tok1, tok)
            ):
                result.append(string[offset:span.end()])
                offset = spans[i + 1].start()

    return result


def tokenize_text(string: str) -> list[list[list[str]]]:
    """Tokenize into paragraphs → sentences → words.

    Paragraphs are separated by ``\\n`` (upstream convention). For
    blank-line-separated paragraphs in audit code, split on
    ``\\n\\s*\\n`` at the caller and feed each block here.
    """
    string = str(string)
    result: list[list[list[str]]] = []
    for part in string.split("\n"):
        paragraph = [tokenize_words(sent) for sent in tokenize_sents(part)]
        if paragraph:
            result.append(paragraph)
    return result


__all__ = ["ABBRS", "tokenize_sents", "tokenize_text", "tokenize_words"]
