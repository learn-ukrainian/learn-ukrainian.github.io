"""Hermetic issue-state check for OPSEC sweep skips and known-leak rows.

A skip or known-leak row must cite the GitHub issue that owns its burn-down.
The row fails once that issue is closed, so the forcing function is tied to the
issue and not only to the calendar.  Issue states come from the committed
``tracking_issues.toml`` snapshot; ``scripts/audit/refresh_opsec_tracking_issues.py``
is the only code that asks GitHub, and it never runs inside pytest.
"""

from __future__ import annotations

import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

TRACKING_ISSUES_PATH = Path(__file__).with_name("tracking_issues.toml")
RENEWAL_WINDOW = timedelta(days=30)
REFRESH_COMMAND = ".venv/bin/python scripts/audit/refresh_opsec_tracking_issues.py --write"


@dataclass(frozen=True)
class TrackingIssues:
    checked_on: date
    states: Mapping[int, str]


def load_tracking_issues(path: Path | None = None) -> TrackingIssues:
    path = path or TRACKING_ISSUES_PATH
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    raw_states = payload.get("issues", {})
    assert isinstance(raw_states, dict), "tracking_issues.toml needs an [issues] table"
    states = {int(number): str(state) for number, state in raw_states.items()}
    assert set(states.values()) <= {"open", "closed"}, f"unknown issue state in {path.name}: {states}"
    return TrackingIssues(checked_on=date.fromisoformat(str(payload["checked_on"])), states=states)


def assert_cites_open_issue(
    label: str,
    issue: object,
    expiry: str,
    tracking: TrackingIssues,
) -> None:
    """Fail unless ``issue`` is a tracked, open issue refreshed for this renewal."""
    assert isinstance(issue, int) and not isinstance(issue, bool) and issue > 0, (
        f"{label} must cite its tracking issue number"
    )
    state = tracking.states.get(issue)
    assert state is not None, f"{label} cites #{issue}, which tracking_issues.toml does not list; run {REFRESH_COMMAND}"
    assert state == "open", f"{label} cites closed issue #{issue}; fix the route or cite an open issue"
    renewal_floor = date.fromisoformat(expiry) - RENEWAL_WINDOW
    assert tracking.checked_on >= renewal_floor, (
        f"{label} was renewed after tracking_issues.toml was last checked "
        f"({tracking.checked_on.isoformat()}); run {REFRESH_COMMAND}"
    )


def assert_no_dead_entries(cited: Iterable[int], tracking: TrackingIssues) -> None:
    dead = sorted(set(tracking.states) - set(cited))
    assert not dead, f"tracking_issues.toml lists issues no skip or known-leak row cites: {dead}"
