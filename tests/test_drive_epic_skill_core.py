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
        checklist.index("scripts.publish pr-merge --number <N>"),
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


@pytest.mark.repo_wide
@pytest.mark.parametrize(
    ("reference", "heading", "instruction"),
    [
        ("queue-and-capacity.md", "## §2.", "one consolidated comment per cycle"),
        ("queue-and-capacity.md", "## §2.", "latest operator directive"),
        ("routing-and-dispatch.md", "## §3a.", "A FAIL blocks dispatch"),
        ("routing-and-dispatch.md", "## §4.", "brief's actual worktree path"),
        ("routing-and-dispatch.md", "## §4.", "pytest basetemp, probe copies, and report copies"),
        ("routing-and-dispatch.md", "## §5.", "reminders are wakeups, not stop conditions"),
        ("review-merge-cleanup.md", "## §6.", "Label a source-only review static"),
    ],
)
def test_measured_behaviors_bind_once_at_their_loop_step(
    reference: str,
    heading: str,
    instruction: str,
) -> None:
    bodies = {
        path.name: " ".join(path.read_text(encoding="utf-8").split())
        for path in (CORE, *sorted((SKILL_DIR / "references").glob("*.md")))
    }
    body = (SKILL_DIR / "references" / reference).read_text(encoding="utf-8")
    section = body[body.index(heading) :].split("\n## ", 1)[0]
    assert instruction in " ".join(section.split())
    assert " ".join(bodies.values()).count(instruction) == 1


def test_friction_report_and_directive_reconciliation_keep_safety_fields() -> None:
    body = " ".join((SKILL_DIR / "references/queue-and-capacity.md").read_text().split())
    for required in (
        "After checking the lane's actual work",
        "existing owner's public issue",
        "affected outcome",
        "sanitized evidence",
        "known or unknown cause",
        "measured waste only when measured",
        "working path",
        "smallest correction",
        "accountable owner",
        "falsifiable DoD",
        "Write NONE only after that check",
        "Keep sensitive evidence in private operational evidence",
        "Do not create a channel",
        "do not post one report per message",
        "an explicit operator pause requires explicit operator release",
    ):
        assert required in body, required


def test_prompt_dispatch_and_scratch_contracts_preserve_failure_gates() -> None:
    body = " ".join((SKILL_DIR / "references/routing-and-dispatch.md").read_text().split())
    for required in (
        "checklist verdict",
        "finding reconciliation",
        "frozen prompt SHA-256",
        "fresh critique of that revision before dispatch",
        "After two FAIL rounds",
        "Keep the denominator and every valid gate",
        "owned paths against the dispatch target",
        "through the §4a inbox drain",
        "unknown queue state remain unresolved",
        "empty projection",
        "managed scratch directory outside the worktree",
        "`$TMPDIR`",
        "empty `git status --porcelain`",
        "`untracked_inputs`",
        "untracked or ignored",
        "`*.py`",
        "`*.pth`",
        "`pytest.ini`",
        "`tox.ini`",
        "`setup.cfg`",
        "`pyproject.toml`",
        "Tracked dirt is `dirty_tree`",
        "an explicit operator pause",
        "seat's handoff signal",
    ):
        assert required in body, required


def test_review_labels_and_pre_enqueue_drain_preserve_existing_execution_steps() -> None:
    body = " ".join((SKILL_DIR / "references/review-merge-cleanup.md").read_text().split())
    for required in (
        "unverified execution behavior",
        "[model-deltas](model-deltas.md)",
        "do not request an executing review solely because a path is integration code",
        "Never record an APPROVE over a pipeline `CHANGES_REQUESTED`",
        "fresh exact-head review after any content change",
        "Immediately before enqueue, run the [core inbox drain]",
        "Before opening a PR that touches launchers or hooks, run every real-launcher test",
    ):
        assert required in body, required
    model_deltas = (SKILL_DIR / "references/model-deltas.md").read_text()
    assert "execution-dependent reviews to Opus 5.5 or Sol 6.1" in model_deltas


@pytest.mark.repo_wide
def test_reduced_packet_keeps_nine_behavior_denominator_and_owned_residuals() -> None:
    handoff = " ".join((SKILL_DIR / "references/handoff.md").read_text().split())
    residuals = handoff.split("## Scoped residuals from #10439", 1)[1].split("## Fleet-comms", 1)[0]
    for required in (
        "denominator remains nine behaviors",
        "Behaviors 2-8 and the scratch half of 9",
        "Behavior 1",
        "Owner: infra/harness",
        "`fleet-comms-coordination.md`",
        "seat-onboarding live-delivery paragraph",
        "in their own change",
        "legacy counts stay exactly as they are",
        "Behavior 9's executing-review-at-first-push half",
        "Owner: harness lane",
        "Reopen when the review-route policy names it",
    ):
        assert required in residuals, required
    all_text = "\n".join(path.read_text() for path in (CORE, *sorted((SKILL_DIR / "references").glob("*.md"))))
    assert "deliveries claim" not in all_text
    assert all_text.count("`date -u`") == 1
    core = CORE.read_text()
    assert "Every timestamp in reports, issue comments, receipts, and" in core
    assert "never from memory or a clock guess" in core
    assert core.index("**Evidence hygiene.**") < core.index("## The loop")
