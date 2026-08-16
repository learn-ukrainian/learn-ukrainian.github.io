"""Drivers must be onboarded onto the Work API and grok-bot QA findings.

Issue #6851: every start-*.sh launch injects a driver instruction naming the
Work API as an orientation surface and grok-bot QA issues as a queue input;
the deployed skill teaches the projection endpoint's attention/health
semantics and grok-bot's hard exclusions.
"""

from __future__ import annotations

from pathlib import Path

from tests.test_launcher_contract import PUBLIC as PUBLIC_LAUNCHERS

REPO = Path(__file__).resolve().parents[1]
LAUNCHER_CORE = REPO / "scripts/lib/launcher_core.sh"
SKILL = REPO / "agents_extensions/shared/skills/drive-epic/SKILL.md"

# All 12 start-*.sh launchers source launcher_core.sh; PUBLIC_LAUNCHERS is
# imported from test_launcher_contract.py's PUBLIC tuple (the allowlist SSOT,
# guarded there by test_root_launcher_allowlist_is_exact) so the two lists
# cannot silently drift. This test guards the one LC_DRIVER_PROMPT string
# they all forward.


def test_all_public_launchers_source_launcher_core() -> None:
    for name in PUBLIC_LAUNCHERS:
        path = REPO / name
        assert path.is_file(), f"missing launcher {name}"
        assert "launcher_core.sh" in path.read_text(encoding="utf-8")


def test_driver_prompt_names_work_api_and_grok_bot_queue_input() -> None:
    core = LAUNCHER_CORE.read_text(encoding="utf-8")
    # Isolate the LC_DRIVER_PROMPT assignment line itself, not just the file,
    # so the guard fails if the sentence moves out of the injected prompt.
    prompt_line = next(
        line for line in core.splitlines() if line.strip().startswith("LC_DRIVER_PROMPT=")
    )
    assert "http://127.0.0.1:8765/api/work/v1/projection" in prompt_line
    assert "grok-bot" in prompt_line
    assert "queue input" in prompt_line
    # Golden rule: launcher stays a thin pointer — no roster/routing data inline.
    assert "codex" not in prompt_line.lower()
    assert "capacity" not in prompt_line.lower()


def test_skill_teaches_work_api_projection_semantics() -> None:
    body = SKILL.read_text(encoding="utf-8")
    assert "http://127.0.0.1:8765/api/work/v1/projection" in body
    for term in ("health", "attention_rank", "safe_next_action"):
        assert term in body, f"skill must document {term!r} from the projection response"


def test_skill_teaches_grok_bot_with_hard_exclusions() -> None:
    body = SKILL.read_text(encoding="utf-8")
    assert "docs/runbooks/grok-bot-qa-observer.md" in body
    assert "external QA observer" in body
    # Hard exclusions preserved verbatim in meaning from the runbook.
    assert "--agent grok-bot" in body
    assert "ask-grok-bot" in body
    assert "never" in body.lower() and "dispatch target" in body
    assert "same-family Grok must not CF" in body


def test_skill_teaches_the_full_health_enum() -> None:
    from scripts.work.attention import HEALTH_RANK

    body = SKILL.read_text(encoding="utf-8")
    # The taught enum must match HEALTH_RANK exactly, not a stale 3-state subset
    # (UNKNOWN is authority-missing/stale, pairs with the INSPECT_UNKNOWN safe
    # action) — assert against the source of truth so this cannot silently drift.
    for state in HEALTH_RANK:
        assert f"`{state}`" in body, f"skill must teach health state {state!r}"
    assert "INSPECT_UNKNOWN" in body


def test_no_launcher_prompt_branch_names_review_pr() -> None:
    # Sealed formal review-pr is retired (operator 2026-08-07; the CLI fails
    # closed) — no LC_DRIVER_PROMPT / fleet_clause branch a driver could be
    # launched down may still instruct it.
    core = LAUNCHER_CORE.read_text(encoding="utf-8")
    cold_start = (REPO / "scripts/lib/fleet_comms_cold_start.sh").read_text(encoding="utf-8")
    assert "review-pr" not in core
    # The richer clause is allowed to name the retired command only to say
    # "do not use" — never as an instruction to run it.
    assert "RETIRED — do not use" in cold_start
