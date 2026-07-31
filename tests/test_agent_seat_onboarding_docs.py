"""Docs-contract tests for #6027 agent-seat onboarding and ownership surfaces.

These tests pin documentation wording only. They do not invoke ACPX, GitHub,
or network auth. Mutable live facts (plane mode, model pins) must be queried,
not hard-coded as present-tense claims in the owned docs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

ONBOARDING = REPO / "docs/runbooks/agent-seat-onboarding.md"
SCRIPTS = REPO / "docs/SCRIPTS.md"
COOPERATION = REPO / "docs/best-practices/agent-cooperation.md"
RUNTIME = REPO / "docs/agent-runtime-guide.md"
ROSTER = REPO / "docs/runbooks/epic-orchestrator-roster.md"
FLEET_COMMS = REPO / "agents_extensions/shared/rules/fleet-comms-coordination.md"

OWNED_DOCS = (
    ONBOARDING,
    SCRIPTS,
    COOPERATION,
    RUNTIME,
    ROSTER,
    FLEET_COMMS,
)

# Hard-coded present-tense plane mode claims are stale by definition.
_HARDCODED_PLANE_MODE = re.compile(
    r"""
    (?:
        currently\s+[`']?mode:\s*(?:off|shadow|dual_write)[`']?
        | \(currently\s+[`']?mode:\s*(?:off|shadow|dual_write)[`']?\)
        | plane\s+mode\s+is\s+(?:off|shadow|dual_write)\b
        | live\s+plane\s+mode\s+is\s+(?:off|shadow|dual_write)\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Bare ApacheBench footgun — allow only explicit warnings about the collision.
_BARE_AB = re.compile(r"(?<![\w/-])\bab\s+(?:ask-|post\b|p\b|discuss\b|sync\b|channel\b)")


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required doc: {path.relative_to(REPO)}"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def onboarding() -> str:
    return _read(ONBOARDING)


@pytest.fixture(scope="module")
def all_owned() -> dict[str, str]:
    return {str(p.relative_to(REPO)): _read(p) for p in OWNED_DOCS}


def test_onboarding_runbook_is_canonical_entry_point(onboarding: str, all_owned: dict[str, str]) -> None:
    assert "canonical" in onboarding.lower()
    assert "ownership matrix" in onboarding.lower()
    # Other owned surfaces must point at the onboarding contract. The roster
    # is exempt: its own onboarding pointer was reverted as a redundant
    # duplicate (fleet-comms/agent-runtime-guide/agent-cooperation/SCRIPTS
    # already carry it) — see test_roster_intentionally_left_unchanged_by_6027.
    for rel, body in all_owned.items():
        if rel.endswith("agent-seat-onboarding.md") or rel.endswith("epic-orchestrator-roster.md"):
            continue
        assert "agent-seat-onboarding.md" in body, f"{rel} must link the onboarding contract"


def test_five_ownership_surfaces(onboarding: str) -> None:
    """All five ownership surfaces are documented with distinct roles."""
    lower = onboarding.lower()
    # discuss
    assert "discuss" in lower
    assert "deliberation" in lower or "design input" in lower
    assert "not formal" in lower or ("never" in lower and "review gate" in lower)
    # delegate
    assert "delegate.py" in onboarding
    assert "dispatch" in lower
    assert "implementation" in lower or "execution" in lower
    # fleet-comms + file handoffs
    assert "fleet-comms" in lower or "fleet_comms" in onboarding
    assert "file" in lower and "authoritative" in lower
    assert "plane-status" in onboarding
    # ACPX
    assert "ACPX" in onboarding or "acpx" in lower
    assert "experimental" in lower
    assert "structured" in lower and "transport" in lower
    assert "read-only" in lower or "read only" in lower
    assert "codex" in lower
    assert "grok" in lower
    assert "feature flag" in lower or "feature-flag" in lower or "default-off" in lower
    # Buzz deferred
    assert "buzz" in lower
    assert "deferred" in lower


def test_authoritative_file_handoff_wording(all_owned: dict[str, str]) -> None:
    """File dual-write stays authoritative in every current plane mode."""
    onboarding = all_owned["docs/runbooks/agent-seat-onboarding.md"]
    fleet = all_owned["agents_extensions/shared/rules/fleet-comms-coordination.md"]
    for label, body in (
        ("onboarding", onboarding),
        ("fleet-comms", fleet),
    ):
        lower = body.lower()
        assert "authoritative" in lower, label
        assert "file" in lower, label
        assert (
            "every" in lower and ("mode" in lower or "plane" in lower)
        ) or "in every" in lower, label
        assert "dual_write" in body or "dual-write" in body or "dual write" in lower, label


def test_plane_status_is_the_live_mode_query(all_owned: dict[str, str]) -> None:
    for rel, body in all_owned.items():
        if rel in {
            "docs/runbooks/agent-seat-onboarding.md",
            "agents_extensions/shared/rules/fleet-comms-coordination.md",
            "docs/runbooks/epic-orchestrator-roster.md",
            "docs/best-practices/agent-cooperation.md",
            "docs/SCRIPTS.md",
        }:
            assert "plane-status" in body, f"{rel} must mention plane-status"


def test_no_hardcoded_live_plane_mode_claim(all_owned: dict[str, str]) -> None:
    # The roster's hard-coded "currently `mode: off`" wording predates #6027
    # and is a separate, pre-existing concern out of scope for this
    # integration — see test_roster_intentionally_left_unchanged_by_6027.
    failures: list[str] = []
    for rel, body in all_owned.items():
        if rel.endswith("epic-orchestrator-roster.md"):
            continue
        for line_no, line in enumerate(body.splitlines(), start=1):
            if _HARDCODED_PLANE_MODE.search(line):
                failures.append(f"{rel}:{line_no}: {line.strip()}")
    assert not failures, "Hard-coded live plane mode claim:\n" + "\n".join(failures)


def test_no_hardcoded_live_model_assertion_in_onboarding(onboarding: str) -> None:
    """Onboarding must not pin a live model id as current truth without query language."""
    # Forbidden present-tense hard pins that go stale (roster projection tables are elsewhere).
    forbidden = [
        re.compile(r"currently\s+uses\s+`?(?:gpt-|claude-|grok-|kimi-|gemini-)", re.I),
        re.compile(r"live\s+model\s+is\s+`?", re.I),
        re.compile(r"default\s+model\s+is\s+currently\s+", re.I),
    ]
    failures: list[str] = []
    for line_no, line in enumerate(onboarding.splitlines(), start=1):
        for pat in forbidden:
            if pat.search(line):
                failures.append(f"agent-seat-onboarding.md:{line_no}: {line.strip()}")
    assert not failures, "Hard-coded live model assertion:\n" + "\n".join(failures)


def test_formal_review_pr_and_verdict_separated_from_discuss(onboarding: str, all_owned: dict[str, str]) -> None:
    lower = onboarding.lower()
    assert "review-pr" in onboarding
    assert "publish-review-verdict" in onboarding
    assert "discuss" in lower
    assert (
        "not formal" in lower
        or "discussion is not" in lower
        or ("never" in lower and "review gate" in lower)
    )
    fleet = all_owned["agents_extensions/shared/rules/fleet-comms-coordination.md"]
    assert "review-pr" in fleet
    assert "publish-review-verdict" in fleet
    coop = all_owned["docs/best-practices/agent-cooperation.md"]
    assert "review-pr" in coop
    assert "not formal" in coop.lower() or "discussion is not" in coop.lower()


def test_no_bare_ab_command_guidance(all_owned: dict[str, str]) -> None:
    failures: list[str] = []
    for rel, body in all_owned.items():
        for line_no, line in enumerate(body.splitlines(), start=1):
            if not _BARE_AB.search(line):
                continue
            # Allow explicit warnings that bare ab is ApacheBench / forbidden.
            normalized = line.lower()
            if any(
                token in normalized
                for token in (
                    "apachebench",
                    "do not",
                    "don't",
                    "never",
                    "not",
                    "brittle",
                    "resolves to",
                    "wrong binary",
                    "no bare",
                )
            ):
                continue
            failures.append(f"{rel}:{line_no}: {line.strip()}")
    assert not failures, "Bare `ab` command guidance found:\n" + "\n".join(failures)


def test_kimicc_high_vs_native_max_distinction(onboarding: str, all_owned: dict[str, str]) -> None:
    lower = onboarding.lower()
    assert "kimicc" in lower
    assert "native" in lower and "kimi" in lower
    assert re.search(r"\bhigh\b", lower)
    assert re.search(r"max-only|max only|\bmax\b", lower)
    # KimiCC high default is stated; native remains max-only.
    assert "defaults to" in lower or "defaults to **`high`**" in onboarding or "default" in lower
    runtime = all_owned["docs/agent-runtime-guide.md"].lower()
    assert "kimicc" in runtime
    assert "max-only" in runtime or "max only" in runtime
    assert re.search(r"\bhigh\b", runtime)
    scripts = all_owned["docs/SCRIPTS.md"].lower()
    assert "kimicc" in scripts
    assert "high" in scripts
    assert "max-only" in scripts or "max only" in scripts


def test_buzz_deferral(onboarding: str, all_owned: dict[str, str]) -> None:
    lower = onboarding.lower()
    assert "buzz" in lower
    assert "deferred" in lower
    assert "relay" in lower or "authority" in lower
    scripts = all_owned["docs/SCRIPTS.md"].lower()
    assert "buzz" in scripts and "deferred" in scripts
    coop = all_owned["docs/best-practices/agent-cooperation.md"].lower()
    assert "buzz" in coop and "deferred" in coop


def test_acpx_default_off_rollback(onboarding: str, all_owned: dict[str, str]) -> None:
    lower = onboarding.lower()
    assert "rollback" in lower
    assert "feature flag" in lower or "feature-flag" in lower or "flag off" in lower
    assert "default" in lower and ("off" in lower or "default-off" in lower)
    assert "native" in lower and "transport" in lower
    # Forbidden scope claims
    for phrase in (
        "persistent",
        "backlog",
        "automatic",
        "agent-to-agent",
    ):
        assert phrase in lower, f"onboarding must document out-of-scope: {phrase}"
    runtime = all_owned["docs/agent-runtime-guide.md"].lower()
    assert "acpx" in runtime
    assert "rollback" in runtime or "flag off" in runtime or ("default" in runtime and "off" in runtime)


def test_acpx_second_pilot_grok_evidence_and_boundary(onboarding: str, all_owned: dict[str, str]) -> None:
    """#6043 — Grok second pilot: broker evidence, two seats, not a new plane."""
    lower = onboarding.lower()
    assert "acpx-codex-shadow" in onboarding
    assert "acpx-grok-shadow" in onboarding
    assert "95" in onboarding
    assert "codex 26" in lower or "codex **26**" in lower or "**codex 26**" in lower
    assert "grok-atlas" in lower
    assert "claude 22" in lower or "claude **22**" in lower or "**claude 22**" in lower
    assert "remaining **22**" in onboarding
    assert "gemini 11" in lower or "gemini **11**" in lower or "**gemini 11**" in lower
    assert "opencode 6" in lower or "opencode **6**" in lower or "**opencode 6**" in lower
    assert "glm 4" in lower or "glm **4**" in lower or "**glm 4**" in lower
    assert "agy 1" in lower or "agy **1**" in lower or "**agy 1**" in lower
    assert "grok 1" in lower or "grok **1**" in lower or "**grok 1**" in lower
    assert "broker" in lower
    assert "direct-runtime" in lower or "direct runtime" in lower
    assert "2026-07-30" in onboarding
    assert "minutes=120" in onboarding
    assert "not permanent routing weights" in lower
    assert "not a new coordination plane" in lower or "not** a new coordination plane" in lower
    assert "0.2.117" in onboarding
    assert "grok-4.5" in onboarding
    assert "--no-leader" in onboarding
    assert "--agent-profile" in onboarding
    assert "digest-checked" in lower
    assert "client flags alone do not remove native grok tools" in lower
    assert "grok-build" in lower
    assert "ACPX_AUTH_CACHED_TOKEN=1" in onboarding
    assert "scripts.agent_runtime.acpx_pilot" in onboarding
    assert "global non-blocking lock" in lower
    assert "idempotency-key digest" in lower
    assert "runtime dashboard" in lower
    assert "cannot send or control acpx traffic" in lower
    runtime = all_owned["docs/agent-runtime-guide.md"]
    assert "acpx-grok-shadow" in runtime
    assert "AcpxGrokShadowAdapter" in runtime
    assert "ACPX_AUTH_CACHED_TOKEN=1" in runtime
    assert "not a new coordination plane" in runtime.lower()
    scripts = all_owned["docs/SCRIPTS.md"].lower()
    assert "acpx-grok-shadow" in scripts or "grok second pilot" in scripts
    assert "not a new coordination plane" in scripts


def test_acpx_does_not_fabricate_cli_flags(onboarding: str) -> None:
    """Stable boundary only — no invented acpx subcommands in the onboarding contract."""
    # Live-proven non-secret selectors only. Codex ChatGPT login (#6027) and
    # Grok cached_token (#6043). Keep every other ACPX_* assignment forbidden
    # so the docs cannot grow an imagined auth surface.
    allowed_auth_selectors = (
        "ACPX_AUTH_CHAT_GPT=1",
        "ACPX_AUTH_CACHED_TOKEN=1",
    )
    forbidden_cli = re.compile(
        r"""
        (?:
            \bacpx\s+(?:invoke|run|session|chat|start|connect)\b
            | \bpython\s+-m\s+acpx\b
            | \bacpx\s+--
            | \bACPX_[A-Z0-9_]+\s*=
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    failures: list[str] = []
    for line_no, line in enumerate(onboarding.splitlines(), start=1):
        scrubbed = line
        for allowed in allowed_auth_selectors:
            scrubbed = scrubbed.replace(allowed, "")
        if forbidden_cli.search(scrubbed):
            failures.append(f"agent-seat-onboarding.md:{line_no}: {line.strip()}")
    assert not failures, "Fabricated ACPX CLI surface:\n" + "\n".join(failures)
    for allowed in allowed_auth_selectors:
        assert allowed in onboarding
    assert "do not invent" in onboarding.lower() or "do **not** invent" in onboarding.lower()


def test_onboarding_uses_real_project_entrypoints(onboarding: str) -> None:
    assert "--prompt-file" in onboarding
    assert "--brief" not in onboarding
    assert "delegate.py --agent kimi --harness kimicc" in onboarding
    assert "localhost:8765" not in onboarding


def test_fresh_agent_smoke_is_readonly_no_github(onboarding: str) -> None:
    lower = onboarding.lower()
    assert "smoke" in lower
    assert "read-only" in lower or "read only" in lower or "no writes" in lower
    assert (
        "no github" in lower
        or "must not call github" in lower
        or ("do not" in lower and "github" in lower)
        or ("must not" in lower and "github" in lower)
    )
    assert "plane-status" in onboarding
    assert "git status" in lower
    # Smoke must not instruct writeful actions as positive steps.
    # Prohibitions ("do not git commit") are allowed.
    for pattern in (
        r"(?i)(?<!do not )(?<!don't )(?<!never )gh\s+pr\s+create",
        r"(?i)(?<!do not )(?<!don't )(?<!never )git\s+commit",
        r"(?i)(?<!do not )(?<!don't )(?<!never )git\s+push",
    ):
        for line in onboarding.splitlines():
            stripped = line.strip().lstrip("#").strip().lstrip("-").strip()
            if re.search(r"(?i)\b(do not|don't|never|must not|no writes)\b", stripped):
                continue
            assert not re.search(pattern, stripped), f"writeful smoke step: {stripped}"


def test_roster_intentionally_left_unchanged_by_6027() -> None:
    """#6027's docs integration deliberately restored this file to its
    pre-integration (``origin/main``) content rather than adding an
    onboarding-contract pointer: `fleet-comms-coordination.md`,
    `agent-runtime-guide.md`, `agent-cooperation.md`, and `SCRIPTS.md` already
    link the onboarding contract, so a roster copy would be a redundant
    duplicate surface. The roster's own live-plane-mode wording is a
    separate, pre-existing concern out of scope for this integration.
    """
    body = _read(ROSTER)
    assert "plane-status" in body


def test_fleet_comms_points_to_onboarding_not_mutable_caps() -> None:
    body = _read(FLEET_COMMS)
    assert "agent-seat-onboarding.md" in body
    # Shared rules point to onboarding; they must not restate mutable caps as SSOT.
    assert re.search(r"not\s*\*?\*?duplicate|duplicate mutable", body, re.I)
    assert "plane-status" in body
    assert "review-pr" in body
    # Still must keep file-authority wording for existing launcher contract tests.
    assert "authoritative" in body.lower()


def test_budgets_and_safety_guardrails_documented(onboarding: str) -> None:
    lower = onboarding.lower()
    assert "one" in lower and "in-flight" in lower
    assert "zero" in lower and "backlog" in lower
    assert "timeout" in lower
    assert "cancel" in lower
    assert "correlation" in lower
    assert "idempoten" in lower
    assert "troubleshoot" in lower
