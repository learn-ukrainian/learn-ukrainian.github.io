"""Drivers must be onboarded onto the Work API and grok-bot QA findings.

Issue #6851: every start-*.sh launch injects a driver instruction naming the
Work API as an orientation surface and grok-bot QA issues as a queue input;
the deployed skill teaches the projection endpoint's attention/health
semantics and grok-bot's hard exclusions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_launcher_contract import PUBLIC as PUBLIC_LAUNCHERS
from tests.test_launcher_contract import run_launcher

REPO = Path(__file__).resolve().parents[1]
LAUNCHER_CORE = REPO / "scripts/lib/launcher_core.sh"
SKILL_DIR = REPO / "agents_extensions/shared/skills/drive-epic"


def _skill_text() -> str:
    """The drive-epic core plus its phase references (the skill is split)."""
    paths = [SKILL_DIR / "SKILL.md", *sorted((SKILL_DIR / "references").glob("*.md"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)

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


@pytest.mark.repo_wide
def test_skill_teaches_work_api_projection_semantics() -> None:
    body = _skill_text()
    assert "http://127.0.0.1:8765/api/work/v1/projection" in body
    for term in ("health", "attention_rank", "safe_next_action"):
        assert term in body, f"skill must document {term!r} from the projection response"


@pytest.mark.repo_wide
def test_skill_teaches_grok_bot_with_hard_exclusions() -> None:
    body = _skill_text()
    assert "docs/runbooks/grok-bot-qa-observer.md" in body
    assert "external QA observer" in body
    # Hard exclusions preserved verbatim in meaning from the runbook.
    assert "--agent grok-bot" in body
    assert "ask-grok-bot" in body
    assert "never" in body.lower() and "dispatch target" in body
    assert "same-family Grok must not CF" in body


@pytest.mark.repo_wide
def test_skill_teaches_the_full_health_enum() -> None:
    from scripts.work.attention import HEALTH_RANK

    body = _skill_text()
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


QUICK_FIX_RULE = "agents_extensions/shared/rules/workflow.md"
QUICK_FIX_POINTER = f"{QUICK_FIX_RULE} § Quick-fix path"
DRIVER_LAUNCHERS = tuple(name for name in PUBLIC_LAUNCHERS if name.endswith("-driver.sh"))
# AGY/Gemini is not a driver seat; its driver launcher refuses before any lease.
REFUSING_DRIVER_LAUNCHERS = ("start-gemini-driver.sh",)


def _argv(path: Path) -> list[str]:
    return [arg for arg in path.read_bytes().decode("utf-8").split("\0") if arg]


@pytest.mark.parametrize("launcher", [name for name in DRIVER_LAUNCHERS if name not in REFUSING_DRIVER_LAUNCHERS])
def test_driver_start_delivers_quick_fix_pointer_after_lease_and_canary(launcher: str, tmp_path: Path) -> None:
    argv_file = tmp_path / "argv"

    result = run_launcher(launcher, "--epic", "devops", env={"LAUNCHER_DRY_RUN_ARGV_FILE": str(argv_file)})

    assert result.returncode == 0, result.stderr
    out = result.stdout
    claim = out.index("would claim lease")
    canary = out.index("provider canary", claim)
    bind = out.index("would bind drive-epic after lease and provider canary")
    assert claim < canary < bind < out.index("would exec")
    argv = _argv(argv_file)
    carriers = [arg for arg in argv if QUICK_FIX_POINTER in arg]
    assert len(carriers) == 1, "one shared injection reaches the provider"
    prompt = carriers[0]
    assert prompt.count(QUICK_FIX_POINTER) == 1
    assert "drive-epic/SKILL.md" in prompt and "do not claim, renew, or reopen the lease" in prompt
    assert "independent cross-family review" in prompt
    assert "authority, security or architecture" in prompt
    assert "### Quick-fix path" in (REPO / QUICK_FIX_RULE).read_text(encoding="utf-8")


@pytest.mark.parametrize("launcher", REFUSING_DRIVER_LAUNCHERS)
def test_non_driver_seat_still_refuses_before_lease(launcher: str, tmp_path: Path) -> None:
    result = run_launcher(launcher, "--epic", "devops", env={"LAUNCHER_DRY_RUN_ARGV_FILE": str(tmp_path / "argv")})

    assert result.returncode != 0
    assert "would claim lease" not in result.stdout
    assert not (tmp_path / "argv").exists()


@pytest.mark.parametrize("launcher", ["start-claude.sh", "start-codex.sh"])
def test_interactive_start_is_not_bound_to_a_driver_prompt(launcher: str, tmp_path: Path) -> None:
    argv_file = tmp_path / "argv"

    result = run_launcher(launcher, env={"LAUNCHER_DRY_RUN_ARGV_FILE": str(argv_file)})

    assert result.returncode == 0, result.stderr
    assert "would claim lease" not in result.stdout
    assert "would bind drive-epic" not in result.stdout
    assert not any(QUICK_FIX_POINTER in arg for arg in _argv(argv_file))


def test_fleet_clause_does_not_contradict_the_quick_fix_path() -> None:
    cold_start = (REPO / "scripts/lib/fleet_comms_cold_start.sh").read_text(encoding="utf-8")
    assert "except a driver-verified quick fix, workflow.md § Quick-fix path" in cold_start


def test_seat_onboarding_teaches_work_authority_failures() -> None:
    body = (REPO / "docs/runbooks/agent-seat-onboarding.md").read_text(encoding="utf-8")
    for term in (
        "/api/work/v1/projection",
        "/api/work/v1/next?stream=<your-stream>",
        "attention_rank",
        "safe_next_action",
        "INSPECT_UNKNOWN",
        "503 building",
        "retry_after_s",
        "valid_streams",
        "queue input",
    ):
        assert term in body
