"""Source-bound phrase rules for Антоненко-Давидович «Як ми говоримо».

The data lives beside the matcher so additions require code review. ``pos=lemma``
atoms use VESUM analyses, never suffix guesses; other atoms are exact spellings.
Findings cite the book's prose chunk, not a morphological or shadow heuristic.
Unresolvable sense distinctions are documented in antonenko_residuals.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from scripts.curriculum.resolver.tokenize import Token
from scripts.verification.antonenko_data import PATTERN_ROWS

BOOK = "Антоненко-Давидович «Як ми говоримо»"
SOURCE_FILE = "antonenko-davydovych-yak-my-hovorymo"


@dataclass(frozen=True)
class PhrasePattern:
    id: str
    atoms: tuple[str, ...]
    recommended: str
    page: int
    positive: str
    negative: str
    context: str = ""

    @property
    def chunk_id(self) -> str:
        return f"{SOURCE_FILE}_p{self.page:03d}"


PATTERNS = tuple(PhrasePattern(*row) for row in PATTERN_ROWS)
_FORM_STARTS: dict[str, set[int]] = {}
_LEMMA_STARTS: dict[tuple[str, str], set[int]] = {}
for _index, _pattern in enumerate(PATTERNS):
    _pos, _equals, _values = _pattern.atoms[0].partition("=")
    if _equals:
        for _lemma in _values.split("|"):
            _LEMMA_STARTS.setdefault((_pos, _lemma), set()).add(_index)
    else:
        for _form in _pos.split("|"):
            _FORM_STARTS.setdefault(_form, set()).add(_index)
_TIME_UNITS = frozenset({"рік", "місяць", "тиждень", "день", "доба", "година", "хвилина", "секунда", "століття"})


def _analyses(token: Token, morphology: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return morphology.get(token.lookup.lower(), []) or morphology.get(token.lookup, [])


def _matches(atom: str, token: Token, morphology: dict[str, list[dict[str, Any]]]) -> bool:
    if token.kind != "cyrillic":
        return False
    readings = _analyses(token, morphology)
    # A proper-name reading is not evidence for a lexical calque.
    if any(set(r.get("tags", "").split(":")) & {"prop", "fname", "lname", "pname"} for r in readings):
        return False
    if token.capitalised and not token.sentence_initial:
        return False
    if "=" not in atom:
        return token.lookup.lower() in atom.split("|")
    pos, lemmas = atom.split("=", 1)
    return any(r.get("pos") == pos and r.get("lemma") in lemmas.split("|") for r in readings)


def _temporal_end(tokens: list[Token], end: int, morphology: dict[str, list[dict[str, Any]]]) -> int | None:
    """Require a following genitive duration; draughts alone never match."""
    for i in range(end, len(tokens)):
        token = tokens[i]
        readings = _analyses(token, morphology)
        if any(r.get("lemma") in _TIME_UNITS and "v_rod" in r.get("tags", "").split(":") for r in readings):
            return i + 1
        if token.kind == "digits" or any(r.get("pos") in {"adj", "numr"} for r in readings):
            continue
        return None
    return None


def find_book_calques(
    text: str, tokens: list[Token], morphology: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Match contiguous source-bound phrases, retaining exact input offsets.

    Whitespace is the only transparent separator. Punctuation, sentence breaks,
    unrelated words, skipped token kinds and item boundaries cannot manufacture
    a phrase. Participation permits intervening VESUM adjectives (e.g. активну).
    """
    findings = []
    for start, token in enumerate(tokens):
        candidates = set(_FORM_STARTS.get(token.lookup.lower(), ()))
        for reading in _analyses(token, morphology):
            candidates.update(_LEMMA_STARTS.get((reading.get("pos", ""), reading.get("lemma", "")), ()))
        for pattern_index in sorted(candidates):
            pattern = PATTERNS[pattern_index]
            if not _matches(pattern.atoms[0], token, morphology):
                continue
            end = start + 1
            for atom in pattern.atoms[1:]:
                if pattern.context == "participation" and atom == "участь":
                    while end < len(tokens) and any(r.get("pos") == "adj" for r in _analyses(tokens[end], morphology)):
                        end += 1
                if end >= len(tokens) or not _matches(atom, tokens[end], morphology):
                    break
                end += 1
            else:
                if pattern.context == "feigning":
                    if end == len(tokens) or tokens[end].lookup.lower() not in {"що", "ніби", "наче", "немов"}:
                        continue
                    if text[tokens[end - 1].end : tokens[end].start].strip() not in {"", ","}:
                        continue
                if pattern.context == "parenthetical" and not text[tokens[end - 1].end :].lstrip().startswith(","):
                    continue
                if pattern.context == "duration":
                    duration_end = _temporal_end(tokens, end, morphology)
                    if duration_end is None:
                        continue
                    end = duration_end
                span = tokens[start:end]
                if any(
                    not text[a.end : b.start].isspace()
                    and not (
                        pattern.context == "matter"
                        and b.lookup.lower() == "що"
                        and text[a.end : b.start].strip() == ","
                    )
                    for a, b in pairwise(span)
                ):
                    continue
                findings.append(
                    {
                        "form": text[span[0].start : span[-1].end],
                        "start": span[0].start,
                        "end": span[-1].end,
                        "detail": {
                            "status": "documented_calque",
                            "pattern_id": pattern.id,
                            "ukrainian_alternative": pattern.recommended,
                            "evidence": {"source": BOOK, "source_file": SOURCE_FILE, "chunk_id": pattern.chunk_id},
                        },
                    }
                )
    return findings
