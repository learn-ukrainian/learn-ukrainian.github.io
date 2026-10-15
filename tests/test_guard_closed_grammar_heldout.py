"""Held-out closed-grammar corpus against origin/main's frozen decisions (#10521).

`main` in the fixture is origin/main's decision on each synthetic row, measured by
`scripts/hooks/guard_main_parity.py generate` in the bash_oracle probe. Here the
BRANCH hooks run in-process in that same probe:

- AC-02: every main BLOCK stays blocked;
- the over-refusal budget: the main ALLOWs the branch blocks are exactly the
  fixture's enumerated `over_refusals`, each attributed to a ruling item;
- read-only forms and quoted data mentions are never triggers (ruling item 7).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.hooks import guard_main_parity as parity

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/guard_closed_grammar_heldout.json"


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def branch(corpus) -> dict[str, parity.Run]:
    """One probe for the module: every row through the branch hook's main()."""
    return parity.branch_runs(corpus["rows"])


def _describe(corpus: dict, ids) -> str:
    rows = {row["id"]: row for row in corpus["rows"]}
    return "\n".join(f"{row_id} [{rows[row_id]['cwd']}] {rows[row_id]['command']!r}" for row_id in sorted(ids))


def test_fixture_is_well_formed(corpus) -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", corpus["main_sha"])
    rows = corpus["rows"]
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert len({(row["hook"], row["cwd"], row["command"]) for row in rows}) == len(rows)
    for row in rows:
        assert row["hook"] in parity.HOOK_FILES, row
        assert row["cwd"] in {"primary", "worktree"}, row
        assert row["main"] in {"block", "allow"}, row
        assert row["class"] in parity.RULING_BY_CLASS, row
        assert (row["main"] == "block") == (row["main_observed"]["exit"] == 2), row
    allowed = {row["id"] for row in rows if row["main"] == "allow"}
    listed = [entry["id"] for entry in corpus["over_refusals"]]
    assert len(listed) == len(set(listed))
    assert set(listed) <= allowed, sorted(set(listed) - allowed)
    for entry in corpus["over_refusals"]:
        assert entry["ruling_item"] in parity.RULING_ITEMS, entry
        assert entry["why"], entry


def test_ac02_every_main_block_stays_blocked(corpus, branch) -> None:
    violations = [row["id"] for row in corpus["rows"] if row["main"] == "block" and branch[row["id"]].exit != 2]
    assert not violations, "AC-02: main BLOCK rows the branch lets through:\n" + _describe(corpus, violations)


def test_over_refusals_equal_the_enumerated_budget(corpus, branch) -> None:
    measured = set(parity.over_refusal_ids(corpus["rows"], branch))
    listed = {entry["id"] for entry in corpus["over_refusals"]}
    new = measured - listed
    removed = listed - measured
    assert not new and not removed, (
        "over-refusal budget drifted.\nNew (branch blocks a main ALLOW, not enumerated):\n"
        + _describe(corpus, new)
        + "\nRemoved (enumerated, but the branch now allows):\n"
        + _describe(corpus, removed)
    )


def test_read_only_forms_and_data_mentions_are_allowed(corpus, branch) -> None:
    blocked = [
        row["id"] for row in corpus["rows"] if row["class"] in parity.MUST_ALLOW_CLASSES and branch[row["id"]].exit != 0
    ]
    assert not blocked, "read-only or data-mention rows blocked:\n" + _describe(corpus, blocked)
