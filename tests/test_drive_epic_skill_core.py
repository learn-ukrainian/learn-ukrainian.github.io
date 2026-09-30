"""The drive-epic core stays small enough to read in full, with its hygiene rules first.

Drivers skipped post-merge hygiene buried in a 57 KB skill (operator 2026-09-29): merged PRs
left issues open and branches without PRs piled up. The core now carries the Definition of
done as a checklist; phase detail lives in references/ loaded only when needed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1] / "agents_extensions/shared/skills/drive-epic"
CORE = SKILL_DIR / "SKILL.md"
CORE_MAX_BYTES = 12_000


def test_core_fits_the_byte_budget() -> None:
    size = CORE.stat().st_size
    assert size <= CORE_MAX_BYTES, f"drive-epic SKILL.md is {size} bytes; move phase detail to references/"


@pytest.mark.repo_wide
def test_every_reference_is_linked_from_the_core() -> None:
    core = CORE.read_text(encoding="utf-8")
    linked = set(re.findall(r"\]\((references/[^)#]+\.md)\)", core))
    present = {f"references/{path.name}" for path in (SKILL_DIR / "references").glob("*.md")}
    assert present, "drive-epic has no references/"
    assert linked == present


def test_core_leads_with_the_definition_of_done_checklist() -> None:
    core = CORE.read_text(encoding="utf-8")
    dod = core.index("## Definition of done")
    loop = core.index("## The loop")
    assert dod < loop
    checklist = core[dod:loop]
    for required in (
        "- [ ] Exact-head cross-family `VERDICT: APPROVE`",
        "- [ ] CI Gate green on that same head.",
        "`MERGED`",
        "scripts.orchestration.merge_closeout <N> --apply` exits 0",
        "Every issue the PR names is closed with evidence, or has a comment posted after",
        "what it waits on",
        "scripts.orchestration.reap_worktrees apply --terminal-dispatches --merged --preserve-then-reap",
        "scripts.hygiene.branch_sweep --json",
        "Every SKIPPED row from the reaper or `branch_sweep` gets a decision",
        "Exit 0 with skips is not done. Never force removal.",
        "Remove a review worktree as soon as its verdict is posted",
        "superseded review checkouts never wait for merge",
        "No issue in the lane has a merged PR and no disposition.",
        "An issue is never kept open as a running log",
        '"Next:"',
    ):
        assert required in checklist, required
    # Landing order: approve, then CI, then enqueue, then merged, then closeout, then issues.
    order = [
        checklist.index("VERDICT: APPROVE"),
        checklist.index("CI Gate green"),
        checklist.index("gh pr merge --squash"),
        checklist.index("shows `MERGED`"),
        checklist.index("merge_closeout"),
        checklist.index("Every issue the PR names"),
    ]
    assert order == sorted(order)


@pytest.mark.repo_wide
def test_section_citations_used_by_scripts_still_resolve() -> None:
    # scripts/ai_agent_bridge/_channels_cli.py prints "drive-epic §0a" and cites §1;
    # scripts/hygiene/branch_sweep.py cites §7a.
    core = CORE.read_text(encoding="utf-8")
    assert "**§0a Inbox drain — cycle start.**" in core
    references = "\n".join(p.read_text(encoding="utf-8") for p in (SKILL_DIR / "references").glob("*.md"))
    assert "## §1. Read topology + metrics" in references
    assert "## §7a. Post-merge cleanup is mandatory" in references
