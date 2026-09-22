"""Ambiguity by record, not by form.

One record whose matching forms share one stressed spelling is `resolved`,
with every matching form's tags: syncretic forms of an allowed lemma are not
a question (operator decision, 2026-09-21). Several records sharing one
stressed spelling are `stress_certain_identity_open`. Different stressed
spellings are `stress_open`, including one record whose syncretic forms
differ in stress, because the printed stress would otherwise be a guess.

The stressed spelling is copied from the word record (`stressed`,
`stress_source`). A `pending` candidate makes the token `pending_stress` when
no answer could avoid it (one record, or every reading pending); when it
competes with known stresses the token is `stress_open` (blocking), and an
answer that selects the pending reading fails `pending_stress` in receipts.py.
`verify_stress` only cross-checks trie-sourced records; it never selects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.curriculum.evidence import registry

from . import codes
from .narrow import Candidate


@dataclass(frozen=True)
class Reading:
    record_id: str
    stressed: str | None
    stress_source: str
    forms: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record": self.record_id,
            "stressed": self.stressed,
            "stress_source": self.stress_source,
            "forms": list(self.forms),
        }


@dataclass(frozen=True)
class Decision:
    klass: str
    readings: tuple[Reading, ...]
    selected: dict[str, Any] | None
    message: str | None = None
    reports: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def record_ids(self) -> list[str]:
        return list(dict.fromkeys(reading.record_id for reading in self.readings))


def readings(candidates: list[Candidate]) -> tuple[Reading, ...]:
    """Group by (record, stressed spelling); record id order, then store form order."""
    grouped: dict[tuple[str, str | None], list[Candidate]] = {}
    for candidate in sorted(candidates, key=lambda c: registry.number(c.record_id)):
        stressed = None if candidate.form["stress_source"] == "pending" else candidate.form["stressed"]
        grouped.setdefault((candidate.record_id, stressed), []).append(candidate)
    out = []
    for (record_id, stressed), members in grouped.items():
        sources = sorted({m.form["stress_source"] for m in members})
        forms = tuple(dict.fromkeys(m.form["tags"] for m in members))
        out.append(Reading(record_id, stressed, "+".join(sources), forms))
    return tuple(out)


def decide(candidates: list[Candidate], *, label: str, spelling: str) -> Decision:
    grouped = readings(candidates)
    records = list(dict.fromkeys(r.record_id for r in grouped))
    if len(records) > codes.MAX_RECORDS or len(grouped) > codes.MAX_RECORDS:
        return Decision(
            codes.TOO_MANY_CANDIDATES,
            grouped,
            None,
            f"{len(records)} records ({len(grouped)} readings) compete for {spelling!r}; the allowlist of "
            f"{label} is too permissive for that spelling",
        )
    pending = [r for r in grouped if r.stressed is None]
    if pending:
        detail = f"stress is pending in the word store for {', '.join(r.record_id for r in pending)} ({spelling!r})"
        # No answer can make a pending stress printable: fail now, before any paid question.
        if len(records) == 1 or len(pending) == len(grouped):
            return Decision(codes.PENDING_STRESS, grouped, None, detail)
        # An unknown stress competes with known ones: blocking; selecting a pending reading fails later.
        return Decision(codes.STRESS_OPEN, grouped, None, detail)
    stressed = {r.stressed for r in grouped}
    if len(grouped) == 1:
        only = grouped[0]
        return Decision(
            codes.RESOLVED,
            grouped,
            {"record": only.record_id, "forms": list(only.forms), "stressed": only.stressed},
        )
    if len(stressed) == 1:
        return Decision(codes.STRESS_CERTAIN_IDENTITY_OPEN, grouped, None)
    return Decision(codes.STRESS_OPEN, grouped, None)


class StressCrossCheck:
    """Compare trie-sourced record stress with the oracle today; report differences."""

    def __init__(self, sources: Any):
        self.sources = sources
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}

    def __call__(self, candidates: list[Candidate]) -> list[dict[str, Any]]:
        reports = []
        for candidate in candidates:
            form = candidate.form
            if form["stress_source"] != "trie":
                continue
            key = (form["form"], form["tags"])
            if key not in self._cache:
                self._cache[key] = self.sources.stress_for_form(*key).raw
            raw = self._cache[key]
            matches = raw.get("matches") or []
            today = [m.get("stressed_form") for m in matches]
            if raw.get("status") == "ok" and today == [form["stressed"]]:
                continue
            reports.append(
                {
                    "code": codes.SOURCE_CHANGED,
                    "record": candidate.record_id,
                    "form": form["form"],
                    "tags": form["tags"],
                    "stored": form["stressed"],
                    "oracle_status": raw.get("status"),
                    "oracle": today,
                }
            )
        return reports
