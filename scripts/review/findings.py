"""Findings ledger: append-only record of every finding raised during a
closeout review, its adjudication(s), and whether it was applied.

The ledger never overwrites or removes an entry — every ``raise_finding`` /
``adjudicate`` / ``apply`` / ``skip`` call appends a new event. A finding
that a challenger never got to stays visibly ``unadjudicated`` instead of
disappearing, and :meth:`FindingsLedger.apply` structurally cannot fire on
anything that wasn't adjudicated to ``in_scope_blocker`` — there is no path
in this API to apply a finding "as-is."
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

Disposition = Literal["in_scope_blocker", "follow_up", "stop_and_escalate"]
EventKind = Literal["raised", "adjudicated", "applied", "skipped"]


class FindingsLedgerError(RuntimeError):
    """An operation would violate the append-only / explicit-adjudication contract."""


@dataclass(frozen=True)
class FindingEvent:
    finding_id: str
    event: EventKind
    summary: str | None = None
    source: str | None = None
    disposition: Disposition | None = None
    rationale: str | None = None


class FindingsLedger:
    def __init__(self) -> None:
        self._events: list[FindingEvent] = []

    @classmethod
    def from_events(cls, events: Iterable[FindingEvent]) -> FindingsLedger:
        """Rehydrate a ledger from a previously persisted event list.

        Used to round-trip a ledger through a JSON state file across CLI
        invocations without re-deriving history — every event is replayed
        verbatim, so nothing is silently dropped on reload either.
        """
        ledger = cls()
        ledger._events = list(events)
        return ledger

    def events(self) -> tuple[FindingEvent, ...]:
        return tuple(self._events)

    def all_finding_ids(self) -> tuple[str, ...]:
        ids: list[str] = []
        for event in self._events:
            if event.event == "raised" and event.finding_id not in ids:
                ids.append(event.finding_id)
        return tuple(ids)

    def _history(self, finding_id: str) -> list[FindingEvent]:
        return [e for e in self._events if e.finding_id == finding_id]

    def _require_raised(self, finding_id: str) -> None:
        if not any(e.event == "raised" for e in self._history(finding_id)):
            raise FindingsLedgerError(f"finding {finding_id!r} was never raised")

    def latest_disposition(self, finding_id: str) -> Disposition | None:
        for event in reversed(self._history(finding_id)):
            if event.event == "adjudicated":
                return event.disposition
        return None

    def is_applied(self, finding_id: str) -> bool:
        return any(e.event == "applied" for e in self._history(finding_id))

    def raise_finding(self, finding_id: str, *, summary: str, source: str) -> None:
        """Record a new finding. Duplicate ids are rejected — re-raising the
        same id would silently merge two distinct findings' histories."""
        if any(e.event == "raised" for e in self._history(finding_id)):
            raise FindingsLedgerError(f"finding {finding_id!r} was already raised")
        self._events.append(FindingEvent(finding_id, "raised", summary=summary, source=source))

    def adjudicate(self, finding_id: str, *, disposition: Disposition, rationale: str) -> None:
        """Record an adjudication. Callable more than once (e.g. a later
        review cycle re-adjudicates); every prior adjudication stays in the
        event log, so nothing is silently overwritten."""
        self._require_raised(finding_id)
        if not rationale.strip():
            raise FindingsLedgerError(f"finding {finding_id!r}: adjudication requires a non-empty rationale")
        self._events.append(
            FindingEvent(finding_id, "adjudicated", disposition=disposition, rationale=rationale)
        )

    def apply(self, finding_id: str) -> None:
        """Record that the accountable agent applied this finding's fix.

        Requires the *latest* adjudication to be ``in_scope_blocker``. There
        is no way to reach this state without an explicit adjudication —
        an unadjudicated finding (challenger unavailable, review skipped)
        cannot be applied "as-is."
        """
        self._require_raised(finding_id)
        disposition = self.latest_disposition(finding_id)
        if disposition is None:
            raise FindingsLedgerError(
                f"finding {finding_id!r} is unadjudicated — cannot apply without adjudication"
            )
        if disposition != "in_scope_blocker":
            raise FindingsLedgerError(
                f"finding {finding_id!r} is adjudicated as {disposition!r}, not in_scope_blocker — "
                "re-adjudicate before applying"
            )
        self._events.append(FindingEvent(finding_id, "applied"))

    def skip(self, finding_id: str, *, rationale: str) -> None:
        """Record an explicit, rationale-carrying decision not to apply a finding."""
        self._require_raised(finding_id)
        if not rationale.strip():
            raise FindingsLedgerError(f"finding {finding_id!r}: skip requires a non-empty rationale")
        self._events.append(FindingEvent(finding_id, "skipped", rationale=rationale))

    def unadjudicated(self) -> tuple[str, ...]:
        """Findings that were raised but never adjudicated — e.g. the
        challenger/reviewer was unavailable. Surfaced explicitly rather
        than silently dropped from the report."""
        return tuple(fid for fid in self.all_finding_ids() if self.latest_disposition(fid) is None)

    def render_report(self) -> str:
        """Every finding and its full event history — nothing dropped."""
        lines = []
        for finding_id in self.all_finding_ids():
            history = self._history(finding_id)
            raised = next(e for e in history if e.event == "raised")
            lines.append(f"## {finding_id}: {raised.summary} (source: {raised.source})")
            for event in history[1:]:
                if event.event == "adjudicated":
                    lines.append(f"  - adjudicated: {event.disposition} — {event.rationale}")
                elif event.event == "applied":
                    lines.append("  - applied")
                elif event.event == "skipped":
                    lines.append(f"  - skipped: {event.rationale}")
            if len(history) == 1:
                lines.append("  - UNADJUDICATED (no reviewer/challenger verdict recorded)")
        return "\n".join(lines) if lines else "(no findings raised)"
