"""Classification before resolution: by the unit's role first, then by surface.

The engine assigns roles from the activity schemas and block kinds; this
module never reads an activity schema. Only `sentence_token` and
`proper_noun` tokens go on to narrowing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import codes
from .inputs import Allowlist, Unit
from .tokenize import Token, tokenize

GLOSS_ID_RE = re.compile(r"W-[0-9]*[1-9][0-9]*")


@dataclass(frozen=True)
class Classified:
    unit: Unit
    token: Token
    surface: str
    # A final class when no narrowing applies; None for sentence tokens.
    final: str | None = None
    message: str | None = None

    @property
    def needs_lookup(self) -> bool:
        return self.final is None


def _gloss_token(unit: Unit, match: re.Match) -> Token:
    return Token(match.group(0), match.start(), "gloss_id", match.group(0), False, (match.group(0),))


def classify_unit(unit: Unit, allowlist: Allowlist) -> list[Classified]:
    if unit.role == "gloss_ref":
        return _gloss_refs(unit, allowlist)
    out = []
    for token in tokenize(unit.text):
        if unit.role in codes.SKIPPED_ROLES:
            out.append(Classified(unit, token, codes.SKIPPED, codes.skipped(unit.role)))
        elif token.kind in codes.SKIPPED_KINDS:
            out.append(Classified(unit, token, codes.SKIPPED, codes.skipped(token.kind)))
        elif token.kind != "cyrillic":
            message = f"mixed-script or unknown letters in {token.text!r}"
            out.append(Classified(unit, token, codes.SENTENCE_TOKEN, codes.UNCLASSIFIABLE, message))
        elif unit.role == "phonetics":
            outside = sorted({ch for ch in token.lookup.lower() if ch.isalpha()} - allowlist.letters)
            if outside:
                out.append(
                    Classified(
                        unit,
                        token,
                        codes.LETTER_OR_SYLLABLE,
                        codes.LETTER_OUTSIDE_STATE,
                        f"letters {outside} are not among the lesson's letters",
                    )
                )
            else:
                out.append(Classified(unit, token, codes.LETTER_OR_SYLLABLE, codes.LETTER_OR_SYLLABLE))
        else:
            out.append(Classified(unit, token, codes.SENTENCE_TOKEN))
    return out


def _gloss_refs(unit: Unit, allowlist: Allowlist) -> list[Classified]:
    matches = list(GLOSS_ID_RE.finditer(unit.text))
    if not matches:
        token = Token(unit.text, 0, "gloss_id", unit.text, False, (unit.text,))
        return [Classified(unit, token, codes.GLOSS_REF, codes.UNCLASSIFIABLE, "a gloss_ref unit names no W- id")]
    out = []
    for match in matches:
        token = _gloss_token(unit, match)
        if token.lookup in allowlist.gloss_ids and token.lookup in allowlist.records:
            out.append(Classified(unit, token, codes.GLOSS_REF, codes.RESOLVED))
        else:
            out.append(
                Classified(
                    unit,
                    token,
                    codes.GLOSS_REF,
                    codes.GLOSS_OUTSIDE_LESSON,
                    f"{token.lookup} is not in this lesson's core or incidental ({allowlist.label})",
                )
            )
    return out


def is_proper_noun(token: Token, *, capitalised_record_match: bool, name_match: bool) -> bool:
    """Capitalised and not sentence-initial; or sentence-initial with a capitalised-lemma
    allowlist record that spells it; or a plan speaker/place. `український` stays ordinary."""
    if name_match:
        return True
    if not token.capitalised:
        return False
    return (not token.sentence_initial) or capitalised_record_match
