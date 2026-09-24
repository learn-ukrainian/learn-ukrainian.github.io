#!/usr/bin/env python3
"""Refresh the GitHub states the OPSEC route sweep's skips depend on (#8542).

The sweep (``tests/api/opsec_sweep``) must stay hermetic, so it reads issue
states from the committed ``tracking_issues.toml`` instead of calling GitHub.
This CLI is the only code that asks GitHub: it collects every issue that an
OPSEC mutation skip or known-leak row cites, reads each state with ``gh``, and
either reports drift (default) or rewrites the snapshot (``--write``).

Run it whenever a skip or known-leak row is added or renewed; the sweep fails
a renewal whose snapshot predates the renewal window, and fails any row whose
cited issue the snapshot records as closed.

Usage:
    .venv/bin/python scripts/audit/refresh_opsec_tracking_issues.py          # check only
    .venv/bin/python scripts/audit/refresh_opsec_tracking_issues.py --write  # rewrite snapshot
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SWEEP_DIR = _REPO_ROOT / "tests" / "api" / "opsec_sweep"
TRACKING_PATH = SWEEP_DIR / "tracking_issues.toml"
KNOWN_LEAKS_PATH = SWEEP_DIR / "known_leaks.toml"
GH_TIMEOUT_SECONDS = 30

_HEADER = """\
# GitHub state of every issue an OPSEC sweep skip or known-leak row cites.
#
# Tests never call GitHub. Refresh this file with the non-test CLI, which is
# the only thing allowed to run `gh`:
#   .venv/bin/python scripts/audit/refresh_opsec_tracking_issues.py --write
# `build_registry` and the known-leak check fail when a cited issue is missing
# here or is "closed", and when `checked_on` predates the renewal window of a
# cited row (so every renewal must refresh these states).
"""


def cited_issues() -> set[int]:
    """Every issue a mutation skip or a known-leak row cites."""
    from tests.api.opsec_sweep.registry import MUTATION_SKIPS  # lazy-ok: imports the Monitor app

    cited = {skip.issue for skip in MUTATION_SKIPS.values()}
    rows = tomllib.loads(KNOWN_LEAKS_PATH.read_text(encoding="utf-8")).get("known_leaks", [])
    cited.update(int(row["issue"]) for row in rows if "issue" in row)
    return cited


def fetch_state(issue: int) -> str:
    completed = subprocess.run(
        ["gh", "issue", "view", str(issue), "--json", "state"],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"gh issue view {issue} failed: {completed.stderr.strip()}")
    return str(json.loads(completed.stdout)["state"]).lower()


def render(states: dict[int, str], checked_on: date) -> str:
    lines = [_HEADER + f'checked_on = "{checked_on.isoformat()}"', "", "[issues]"]
    lines.extend(f'{issue} = "{state}"' for issue, state in sorted(states.items()))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="rewrite tracking_issues.toml with live states")
    args = parser.parse_args(argv)

    states = {issue: fetch_state(issue) for issue in sorted(cited_issues())}
    closed = sorted(issue for issue, state in states.items() if state != "open")
    for issue, state in sorted(states.items()):
        print(f"#{issue}: {state}")

    if args.write:
        TRACKING_PATH.write_text(render(states, date.today()), encoding="utf-8")
        print(f"wrote {TRACKING_PATH.relative_to(_REPO_ROOT)}")
    else:
        committed = tomllib.loads(TRACKING_PATH.read_text(encoding="utf-8")).get("issues", {})
        if {int(issue): str(state) for issue, state in committed.items()} != states:
            print("tracking_issues.toml is out of date; rerun with --write", file=sys.stderr)
            return 1

    if closed:
        print(
            "cited issues are closed: "
            + ", ".join(f"#{issue}" for issue in closed)
            + "; fix those routes/leaks or cite an open issue",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
