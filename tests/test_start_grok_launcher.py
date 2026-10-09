"""Grok adapter and driver lifecycle tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.rules_core_view import rules_core_absent_when_marked  # noqa: F401  (autouse: serves @rules_core_absent)
from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


def test_grok_interactive_defaults_to_native_harness_and_rejects_epic() -> None:
    interactive = run_launcher("start-grok.sh")
    epic = run_launcher("start-grok.sh", "--epic", "atlas")
    assert interactive.returncode == 0, interactive.stderr
    assert "would exec grok" in interactive.stdout
    assert "--model grok-4.5" not in interactive.stdout
    assert "--model" not in interactive.stdout
    assert "--reasoning-effort" not in interactive.stdout
    assert "--effort" not in interactive.stdout
    assert epic.returncode == 2
    assert "interactive launchers reject --epic" in epic.stderr


def test_grok_explicit_retired_model_is_refused() -> None:
    """#6870: interactive start-grok.sh must refuse retired grok-4.5."""
    result = run_launcher("start-grok.sh", "--model", "grok-4.5")
    assert result.returncode == 2, result.stderr
    assert "is retired in the model catalog" in result.stderr
    assert "grok-4.5" in result.stderr
    assert "--model grok-4.5" not in result.stdout


def test_grok_explicit_certified_model_still_pins() -> None:
    result = run_launcher("start-grok.sh", "--model", "grok-4.7")
    assert result.returncode == 0, result.stderr
    assert "--model grok-4.7" in result.stdout


def test_grok_effort_injects_reasoning_effort_only_when_set() -> None:
    with_effort = run_launcher("start-grok.sh", "--effort", "high")
    without = run_launcher("start-grok.sh")
    assert with_effort.returncode == 0, with_effort.stderr
    assert "--reasoning-effort high" in with_effort.stdout
    assert without.returncode == 0, without.stderr
    assert "--reasoning-effort" not in without.stdout
    assert "--effort" not in without.stdout


@pytest.mark.parametrize("selector", ("atlas", "practice", "infra.devops", "infra"))
def test_grok_driver_claims_a_lease_for_supported_selectors(selector: str) -> None:
    result = run_launcher("start-grok-driver.sh", "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    assert "would run provider canary" in result.stdout
    assert "would bind drive-epic" in result.stdout
    assert "--model grok-4.5" not in result.stdout
    assert "--model" not in result.stdout


@pytest.mark.parametrize(
    "selector, slot", (("seminars-folk", "grok-folk"), ("bio", "grok-bio"), ("hramatka", "grok-hramatka"))
)
def test_grok_driver_refuses_ukrainian_content_slots(selector: str, slot: str) -> None:
    result = run_launcher("start-grok-driver.sh", "--epic", selector)
    assert result.returncode == 2, result.stdout + result.stderr
    assert slot in result.stderr
    assert "operator order 2026-09-27" in result.stderr
    assert "would claim lease" not in result.stdout


def test_grok_driver_rejects_uncertified_model_and_non_grok_harness() -> None:
    uncertified = run_launcher("start-grok-driver.sh", "--epic", "devops", "--model", "grok-unknown")
    harness = run_launcher("start-grok.sh", "--harness", "agy")
    assert uncertified.returncode == 4
    assert harness.returncode == 2
    assert "only --harness grok" in harness.stderr


def test_grok_forwards_provider_arguments_only_after_separator() -> None:
    result = run_launcher("start-grok.sh", "--", "--reasoning", "high")
    assert result.returncode == 0, result.stderr
    assert "--reasoning high" in result.stdout


def _run_grok_driver_adapter(flag: str) -> subprocess.CompletedProcess[str]:
    script = """
set -euo pipefail
source scripts/launchers/grok.sh
LC_HARNESS=grok LC_MODE=driver LC_ROOT="$PWD"
LC_DURABLE_HELPER_ROOT="$FIXTURE_HELPER_ROOT"
LC_MODEL='' LC_EFFORT='' LC_RULES_CORE='' LC_DRY_RUN=0
LC_FORWARD_ARGS=("$1")
launcher_error() { echo "$*" >&2; }
launcher_exec_command() { printf 'would exec '; printf '%s ' "$@"; }
launcher_adapter_validate
launcher_adapter_exec
"""
    return subprocess.run(
        ["bash", "-c", script, "fixture", flag], cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "FIXTURE_HELPER_ROOT": str(Path(sys.executable).parents[2])},
        capture_output=True, text=True, timeout=15,
    )


@pytest.mark.parametrize(
    "flag",
    (
        "--cwd", "-w", "--worktree", "--worktree-ref", "--ref", "--leader",
        "--leader-socket", "--session-id", "--unknown-driver-option",
        "--cwd=nested", "-w=nested", "-wnested", "--worktree=nested",
        "--worktree-ref=main", "--ref=main", "--leader=true",
        "--leader-socket=socket", "--session-id=other", "--unknown-driver-option=value",
        "--agent=custom", "--agents={}", "--fullscreen=true", "--", "leader",
    ),
)
def test_grok_driver_forwarded_arguments_fail_closed(flag: str) -> None:
    result = _run_grok_driver_adapter(flag)
    assert result.returncode == 2, result.stdout + result.stderr
    name = flag.split("=", 1)[0] if flag.startswith("--") else flag[:2] if flag.startswith("-") else "subcommand"
    assert name in result.stderr
    assert "not allowlisted" in result.stderr
    assert "launcher-bound" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout


@pytest.mark.parametrize("flag", ["--unknown-driver-option=private-fixture-value", "-sprivate-fixture-value", "private-fixture-value"])
def test_grok_driver_refusal_does_not_echo_values(flag: str) -> None:
    result = _run_grok_driver_adapter(flag)
    assert result.returncode == 2
    assert "not allowlisted" in result.stderr
    assert "private-fixture-value" not in result.stderr


@pytest.mark.parametrize(
    "flag",
    ("--debug", "--fullscreen", "--minimal", "--no-alt-screen", "--disable-web-search", "--no-subagents"),
)
def test_grok_driver_allowlisted_arguments_launch(flag: str) -> None:
    result = _run_grok_driver_adapter(flag)
    assert result.returncode == 0, result.stdout + result.stderr
    command = result.stdout.split("would exec grok", 1)[1]
    assert flag in command
    assert "--no-leader" in command


@pytest.mark.parametrize("deploy_failed", [False, True])
def test_grok_driver_deploy_precedes_preflight(tmp_path, deploy_failed: bool) -> None:
    """Run the startup sequence, stopping before any lease or provider session."""
    root = Path(__file__).resolve().parents[1]
    checkout = tmp_path / "checkout"
    for relative in ("scripts/lib/launcher_core.sh", "scripts/lib/handoff_identity.sh", "scripts/launchers/grok.sh"):
        target = checkout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / relative).read_bytes())
    (checkout / "scripts/lib/driver_scope.sh").write_text("launcher_enter_driver_scope() { return 0; }\n")
    (checkout / "scripts/lib/deploy_extensions.sh").write_text(
        'deploy_agent_extensions() { echo DEPLOY; return "$FIXTURE_DEPLOY_RC"; }\n'
    )
    script = """
set -euo pipefail
source "$1/scripts/lib/launcher_core.sh"
launcher_defaults() {
  LC_DRY_RUN=0 LC_HARNESS=grok LC_ENDPOINT='' LC_ISOLATE_CONFIG=0
  LC_DURABLE_HELPER_ROOT="$FIXTURE_HELPER_ROOT"
  LC_FORWARD_ARGS=()
}
for function in launcher_clear_foreign_route_state launcher_parse \
  launcher_refuse_uncertified_gemini_driver launcher_drop_force_from_successor_args \
  launcher_normalize_effort launcher_resolve_roots launcher_publication_path \
  launcher_normalize_model launcher_validate_mode launcher_validate_driver_certification \
  launcher_load_rules_core launcher_export_git_identity; do
  eval "$function() { return 0; }"
done
launcher_require_binary() { return 0; }
grok() { echo INSPECT >&2; return 1; }
launcher_main grok driver
"""
    result = subprocess.run(
        ["bash", "-c", script, "fixture", str(checkout)], cwd=checkout,
        env={**os.environ, "FIXTURE_DEPLOY_RC": "1" if deploy_failed else "0", "FIXTURE_HELPER_ROOT": str(root)},
        capture_output=True, text=True, timeout=15,
    )
    assert "DEPLOY" in result.stdout, result.stdout + result.stderr
    if deploy_failed:
        assert result.returncode == 1
        assert "deploy failed" in result.stderr
        assert "INSPECT" not in result.stderr
    else:
        assert result.returncode == 2
        assert "INSPECT" in result.stderr
        assert "grok inspect --json failed" in result.stderr


@pytest.mark.rules_core_absent
def test_grok_hermes_opt_in_pins_route_and_reuses_driver_lifecycle(tmp_path) -> None:
    from tests.test_launcher_contract import hermes_stub_env

    result = run_launcher(
        "start-grok-driver.sh", "--epic", "devops", "--harness", "hermes", "--effort", "high",
        env=hermes_stub_env(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    assert "agent=grok harness=hermes" in result.stdout
    assert "would exec hermes chat --cli --provider xai-oauth --model grok-4.7" in result.stdout
    assert "--reasoning high" in result.stdout
    assert result.stdout.index("would claim lease") < result.stdout.index("would run provider canary")
    assert result.stdout.index("would run provider canary") < result.stdout.index("would bind drive-epic")
    assert "Load\\ agents_extensions/shared/skills/drive-epic/SKILL.md" in result.stdout
    assert "--query" in result.stdout


def test_grok_hermes_omitted_effort_is_not_attested(tmp_path) -> None:
    from tests.test_launcher_contract import hermes_stub_env

    result = run_launcher("start-grok.sh", "--harness=hermes", env=hermes_stub_env(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "requested_effort=default" in result.stdout
    assert "--reasoning" not in result.stdout


def test_grok_hermes_refuses_unsupported_model_and_effort() -> None:
    model = run_launcher("start-grok.sh", "--harness", "hermes", "--model", "openai-codex")
    effort = run_launcher("start-grok.sh", "--harness", "hermes", "--effort", "max")
    assert model.returncode == 4
    assert effort.returncode == 2
    assert "supports only low|medium|high" in effort.stderr
