"""Deterministic narrowing, and only this.

(1) Candidates are the learner-usable `(record, form)` pairs of the allowlist
whose plain form spells the token, under the case rules below. (2) No
candidate is `lemma_outside_state`; the token's VESUM analyses go into the
stream so the message names the lemma the lesson needs. (3) The features
common to all candidates are recorded through `TagMapper`.

Nothing from neighbouring tokens is used. Tags cannot prove agreement or a
governed case (a preposition's VESUM tag is `prep` only), so this module does
not try.

Case rules: a lower-case token matches lower-case forms. A capitalised
sentence-initial token matches lower-case forms (first letter lowered) and
the forms of capitalised-lemma records. A capitalised token elsewhere matches
capitalised-lemma records only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.curriculum.evidence import codes as evidence_codes
from scripts.curriculum.evidence import tags

from .inputs import Allowlist
from .tokenize import Token, lookup_form


@dataclass(frozen=True)
class Candidate:
    record_id: str
    record: dict[str, Any]
    form: dict[str, Any]


def learner_usable(form: dict[str, Any]) -> bool:
    markers = {m["marker"] if isinstance(m, dict) else m for m in form.get("markers") or []}
    return form.get("learner") is True and not markers & evidence_codes.EXCLUDING_MARKERS


def capitalised_lemma(record: dict[str, Any]) -> bool:
    return str(record.get("lemma", ""))[:1].isupper()


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


class FormIndex:
    """Plain form -> candidates, in record id order then store form order."""

    def __init__(self, allowlist: Allowlist):
        self.usable: dict[str, list[Candidate]] = {}
        self.marked: dict[str, list[Candidate]] = {}
        for record_id, record in allowlist.records.items():
            for form in record.get("forms") or []:
                target = self.usable if learner_usable(form) else self.marked
                target.setdefault(lookup_form(form["form"]), []).append(Candidate(record_id, record, form))

    @staticmethod
    def _select(pool: dict[str, list[Candidate]], token: Token) -> list[Candidate]:
        if not token.capitalised:
            return [c for c in pool.get(token.lookup, []) if not capitalised_lemma(c.record)]
        found = [c for c in pool.get(token.lookup, []) if capitalised_lemma(c.record)]
        if token.sentence_initial:
            lowered = lower_first(token.lookup)
            found = [c for c in pool.get(lowered, []) if not capitalised_lemma(c.record)] + found
        return found

    def candidates(self, token: Token) -> list[Candidate]:
        return self._select(self.usable, token)

    def marked_candidates(self, token: Token) -> list[Candidate]:
        return self._select(self.marked, token)

    def capitalised_match(self, token: Token) -> bool:
        return any(capitalised_lemma(c.record) for c in self.usable.get(token.lookup, []))


def lookup_keys(token: Token) -> list[str]:
    """The spellings a VESUM analysis of this token is looked up under (for failure messages)."""
    keys = [token.lookup]
    if token.capitalised and token.sentence_initial:
        keys.append(lower_first(token.lookup))
    if token.hyphenated:
        keys.extend(part for part in token.parts if part)
        if token.capitalised and token.sentence_initial:
            keys.append(lower_first(token.parts[0]))
    return list(dict.fromkeys(keys))


def common_features(candidates: list[Candidate], mapper: tags.TagMapper) -> list[str]:
    feature_sets = [set(mapper(c.form["tags"])) for c in candidates]
    if not feature_sets:
        return []
    return sorted(set.intersection(*feature_sets))
