"""Cursor driver launcher seat + lifecycle tests (#6956)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.review.model_catalog import load_model_catalog
from tests.launcher_sandbox import launcher_environment
from tests.test_launcher_contract import REPO, run_launcher
from tests.test_launcher_driver_scope import manager_guard

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

DRIVER = "start-cursor-driver.sh"
RETIRED_MODEL_IDS = {
    model_id for model_id, entry in load_model_catalog()["models"].items()
    if entry["lifecycle"] == "retired"
}
# The launcher's seat pin. Every Grok model is retired (GROK-CANCEL-1110), so a launch that
# falls back to this pin is refused before any other gate runs.
RETIRED_SEAT_PIN = "grok-4.7-high"
# A non-retired model that is not an approved Cursor pin: it passes the retired-model check, so
# the launcher's later gates (epic, content slots, forwarded models) stay reachable in tests.
UNAPPROVED_MODEL = "cursor-unknown"


def _assert_retired_pin_refused(result) -> None:
    assert result.returncode == 2, result.stdout + result.stderr
    assert f"model '{RETIRED_SEAT_PIN}' is retired in the model catalog" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout


def test_cursor_driver_help_mentions_epic() -> None:
    result = run_launcher(DRIVER, "--help")
    assert result.returncode == 0, result.stderr
    assert "--epic" in result.stdout
    assert "Usage:" in result.stdout
    assert "./start-cursor-driver.sh" in result.stdout
    assert "start-cursor.sh" not in result.stdout


def test_cursor_driver_rejects_dummy_agent_on_path(tmp_path: Path) -> None:
    """CF #6969: a bare ``agent`` on PATH must not claim the Cursor seat.

    Reviewer probe: with only a dummy ``agent`` executable visible, the
    launcher previously dry-ran ``would exec agent`` while leasing as
    ``agent=cursor harness=cursor-agent``. Require ``cursor-agent``.
    """
    shell = shutil.which("bash")
    assert shell is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "bash").symlink_to(shell)
    dummy_agent = bin_dir / "agent"
    dummy_agent.write_text("#!/bin/sh\necho impostor-agent\n", encoding="utf-8")
    dummy_agent.chmod(0o755)
    probe_path = f"{bin_dir}{os.pathsep}{os.defpath}"
    assert shutil.which("agent", path=probe_path) == str(dummy_agent)
    assert shutil.which("cursor-agent", path=probe_path) is None

    # The retired seat pin refuses the launch before any binary is chosen, so no agent runs.
    result = run_launcher(DRIVER, "--epic", "infra", env={"PATH": probe_path})
    _assert_retired_pin_refused(result)
    assert "would exec agent" not in result.stdout


def test_cursor_launcher_refuses_decoy_agent_when_cursor_agent_is_missing(tmp_path: Path) -> None:
    """A live launch with only a decoy ``agent`` exits non-zero and never runs it.

    ``scripts/launchers/cursor.sh`` is the shell-side exception to
    ``resolve_cursor_agent_binary``: it still requires exactly ``cursor-agent``.
    """
    shell = shutil.which("bash")
    assert shell is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "bash").symlink_to(shell)
    marker = tmp_path / "decoy-ran"
    dummy_agent = bin_dir / "agent"
    dummy_agent.write_text("#!/bin/sh\nprintf '%s\\n' ran >> \"$DECOY_RAN\"\n", encoding="utf-8")
    dummy_agent.chmod(0o755)
    probe_path = f"{bin_dir}{os.pathsep}{os.defpath}"
    assert shutil.which("agent", path=probe_path) == str(dummy_agent)
    assert shutil.which("cursor-agent", path=probe_path) is None

    result = run_launcher(
        DRIVER,
        "--epic",
        "infra",
        env={"PATH": probe_path, "DECOY_RAN": str(marker)},
        dry_run=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert f"model '{RETIRED_SEAT_PIN}' is retired in the model catalog" in result.stderr
    assert not marker.exists()
    assert "ran" not in result.stdout


def test_cursor_driver_requires_epic_fail_closed() -> None:
    """Launching without --epic must not silently claim main orchestrator."""
    missing = run_launcher(DRIVER, "--model", UNAPPROVED_MODEL)
    assert missing.returncode == 2, missing.stderr
    assert "driver launch requires --epic" in missing.stderr


@pytest.mark.parametrize("selector", ("infra", "devops", "atlas", "corpus"))
def test_cursor_driver_claims_lease_for_supported_selectors(selector: str) -> None:
    """With no approved Cursor pin (GROK-CANCEL-1110), no selector claims a lease."""
    result = run_launcher(DRIVER, "--epic", selector)
    _assert_retired_pin_refused(result)
    assert "would bind drive-epic" not in result.stdout


@pytest.mark.parametrize(
    "selector, slot", (("folk", "cursor-folk"), ("seminars-bio", "cursor-bio"), ("hramatka", "cursor-hramatka"))
)
def test_cursor_driver_refuses_ukrainian_content_slots(selector: str, slot: str) -> None:
    result = run_launcher(DRIVER, "--epic", selector, "--model", UNAPPROVED_MODEL)
    assert result.returncode == 2, result.stdout + result.stderr
    assert slot in result.stderr
    assert "operator order 2026-09-27" in result.stderr
    assert "would claim lease" not in result.stdout


def test_cursor_driver_rejects_uncertified_model_and_foreign_harness() -> None:
    uncertified = run_launcher(DRIVER, "--epic", "devops", "--model", "cursor-unknown")
    harness = run_launcher(DRIVER, "--epic", "devops", "--harness", "agy")
    assert uncertified.returncode == 4
    assert "not certified" in uncertified.stderr
    assert "cursor_no_approved_model_pin" in uncertified.stderr
    # The retired seat pin refuses the launch before the harness check is reached.
    _assert_retired_pin_refused(harness)


def test_cursor_launcher_pin_list_matches_python_admission() -> None:
    from scripts.review.model_catalog import CURSOR_APPROVED_WIRE_PINS, apply_cursor_model_pins, cursor_pinned_models

    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    function = re.search(r"launcher_cursor_model_certified\(\) \{(.*?)\n\}", core, re.DOTALL)
    assert function is not None
    assert 'case "$model" in' in function[1]
    case_arms = re.findall(r"^\s*(.*?)\) return 0 ;;", function[1], re.MULTILINE)
    shell_pins = {pin.replace("\\", "") for arm in case_arms for pin in arm.split("|")}
    expected = CURSOR_APPROVED_WIRE_PINS | {apply_cursor_model_pins(pin) for pin in cursor_pinned_models()}
    assert shell_pins == expected
    # The retired former pin is certified on neither side (GROK-CANCEL-1110).
    assert RETIRED_SEAT_PIN not in expected
    retired = subprocess.run(
        ["bash", "-c", 'source "$1"; launcher_cursor_model_certified "$2"', "pin-check",
         str(REPO / "scripts/lib/launcher_core.sh"), RETIRED_SEAT_PIN],
        capture_output=True, text=True, check=False, timeout=10,
        env=launcher_environment(),
    )
    assert retired.returncode == 1, retired.stderr
    # Execute the case arm as well as inspecting its declared pins.
    for pin in sorted(expected):
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; launcher_cursor_model_certified "$2"', "pin-check",
             str(REPO / "scripts/lib/launcher_core.sh"), pin],
            capture_output=True, text=True, check=False, timeout=10,
            env=launcher_environment(),
        )
        assert result.returncode == 0, (pin, result.stderr)
        assert apply_cursor_model_pins(pin) == pin


@pytest.mark.parametrize(
    "model",
    (
        "grok-4.7",
        "grok-4.7-high",
    ),
)
def test_cursor_driver_refuses_the_retired_former_pins(model: str) -> None:
    """The former Grok pins are retired (GROK-CANCEL-1110) and never launch."""
    result = run_launcher(DRIVER, "--epic", "infra", "--model", model)
    assert result.returncode == 2, result.stdout + result.stderr
    assert f"model '{model}' is retired in the model catalog" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout


@pytest.mark.parametrize(
    "model",
    (
        "auto",
        "Auto",
        "AUTO",
        "cursor:auto",
        "default",
        "grok-4.7-fast",
        "grok-4.7-low",
        "grok-4.7-medium",
        "grok-4.7-xhigh",
        "grok-4.7[context=500k]",
        "grok-4.7[fast=false]",
        "grok-4.7-high-fast",
        "composer-2.5",
        "composer-2.5[fast=false]",
        "composer-2.5-fast",
        "composer-2.5[fast=true]",
        "grok-4.7[context=500k,fast=true]",
        "grok-4.7[fast=true,reasoning_effort=high]",
        "grok-4.7[fast=1]",
        "grok-4.6",
        "grok-4.6[fast=false]",
        "grok-4.5",
    ),
)
def test_cursor_driver_refuses_auto_fast_and_previous_generation_pins(model: str) -> None:
    """#9274: the Cursor driver seat never runs Auto, a Fast variant, or a previous generation."""
    for result in (
        run_launcher(DRIVER, "--epic", "infra", "--model", model),
        run_launcher(DRIVER, "--epic", "infra", env={"LAUNCHER_MODEL": model}),
    ):
        # Every Grok variant names a retired catalog model or a retired prefix (GROK-CANCEL-1110).
        if model.partition("[")[0] in RETIRED_MODEL_IDS or model.startswith(("composer-2.5", "grok-")):
            assert result.returncode == 2, result.stdout + result.stderr
            assert "is retired in the model catalog" in result.stderr
            assert model in result.stderr
        else:
            assert result.returncode == 4, result.stdout + result.stderr
            assert "not certified for the cursor driver" in result.stderr
            assert "CURSOR_MODEL_NOT_APPROVED" in result.stderr
        assert "would claim lease" not in result.stdout
        assert "would exec" not in result.stdout


def test_cursor_driver_refuses_an_empty_model() -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--model=")
    assert result.returncode == 4, result.stdout + result.stderr
    assert "requires a concrete model" in result.stderr
    assert "would exec" not in result.stdout


def test_cursor_driver_empty_env_model_falls_back_to_the_pin() -> None:
    """An empty LAUNCHER_MODEL falls back to the seat pin, which is retired and refused."""
    result = run_launcher(DRIVER, "--epic", "infra", env={"LAUNCHER_MODEL": ""})
    _assert_retired_pin_refused(result)


@pytest.mark.parametrize(
    "forwarded",
    (("--model", "auto"), ("--model=auto",), ("--model", "grok-4.7-high"), ("--model=Auto",)),
)
def test_cursor_driver_refuses_a_forwarded_provider_model(forwarded: tuple[str, ...]) -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--model", UNAPPROVED_MODEL, "--", *forwarded)
    assert result.returncode == 4, result.stdout + result.stderr
    assert "not from forwarded" in result.stderr
    assert "would exec" not in result.stdout


# Interactive Cursor sessions (#9274): no public start-cursor.sh exists, but
# launcher_main cursor interactive is reachable, and it is not a typed
# implementation dispatch, so it pins a concrete model like the driver seat.
# Admission runs first; a live launch from this untracked caller is then refused
# at scope entry (#9624), so an admitted pin is proven on the argv the dry run
# prints, which the live exec passes unchanged.
_INTERACTIVE = r"""
source() {
  builtin source "$@" || return
  case "$1" in
    # Mock the agent-extensions deploy so the exec path runs hermetically.
    */deploy_extensions.sh) deploy_agent_extensions() { echo 'mock deploy'; } ;;
  esac
}
source "$LC_TEST_REPO/scripts/lib/launcher_core.sh"
launcher_main cursor interactive "$@"
"""


def _run_interactive(tmp_path: Path, *args: str, env: dict[str, str] | None = None, dry_run: bool = False):
    """Run launcher_main cursor interactive with a mock cursor-agent that records its argv.

    Stand-ins for the user manager fail the test on any call (#9624).
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    argv_file = tmp_path / "cursor-agent.argv"
    mock = bin_dir / "cursor-agent"
    mock.write_text(f"#!/bin/sh\nprintf '%s\\0' \"$@\" > '{argv_file}'\n", encoding="utf-8")
    mock.chmod(0o755)
    guard = manager_guard(tmp_path / "manager-guard-bin")
    contact = tmp_path / "real-manager-contact"
    launch_env = launcher_environment()
    launch_env.update(
        {
            "LAUNCHER_DRY_RUN": "1" if dry_run else "0",
            "LC_TEST_REPO": str(REPO),
            "LU_SKIP_PLANE_TUNNEL_CHECK": "1",
            "LU_TEST_REAL_MANAGER_CONTACT": str(contact),
            "PATH": f"{bin_dir}{os.pathsep}{guard}{os.pathsep}{launch_env['PATH']}",
        }
    )
    launch_env.pop("LAUNCHER_MODEL", None)
    launch_env.update(env or {})
    result = subprocess.run(
        ["bash", "-c", _INTERACTIVE, "cursor-interactive-test", *args],
        cwd=REPO,
        env=launch_env,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert not contact.exists(), f"the launcher reached for the real user manager: {contact.read_text()}"
    argv = argv_file.read_text(encoding="utf-8").split("\0")[:-1] if argv_file.exists() else None
    return result, argv


def test_cursor_interactive_defaults_to_the_concrete_pin(tmp_path: Path) -> None:
    """The interactive default is the seat pin; it is retired, so neither run starts cursor-agent."""
    for name, dry_run in (("dry", True), ("live", False)):
        result, argv = _run_interactive(tmp_path / name, env={"LAUNCHER_MODEL": ""}, dry_run=dry_run)
        assert result.returncode == 2, result.stdout + result.stderr
        assert f"model '{RETIRED_SEAT_PIN}' is retired in the model catalog" in result.stderr
        assert "would exec" not in result.stdout
        assert argv is None
        assert "mock deploy" not in result.stdout


@pytest.mark.parametrize(
    "selection",
    (
        ("--model", "auto"),
        ("--model=Auto",),
        ("--model", "cursor:auto"),
        ("--model=",),
        ("--model", "grok-4.7-fast"),
        ("--model", "composer-2.5[fast=true]"),
        ("--model", "grok-4.6"),
        ("--", "--model", "auto"),
        ("--", "--model=grok-4.7-high"),
    ),
)
def test_cursor_interactive_refuses_auto_empty_fast_and_forwarded_models(
    tmp_path: Path, selection: tuple[str, ...]
) -> None:
    # A forwarded model needs a non-retired launcher model, or the retired seat pin refuses first.
    args = ("--model", UNAPPROVED_MODEL, *selection) if selection[0] == "--" else selection
    result, argv = _run_interactive(tmp_path, *args)
    if selection[0] == "--model" and (
        selection[1].partition("[")[0] in RETIRED_MODEL_IDS or selection[1].startswith("grok-")
    ):
        assert result.returncode == 2, result.stdout + result.stderr
        assert "is retired in the model catalog" in result.stderr
        assert selection[1] in result.stderr
    else:
        assert result.returncode == 4, result.stdout + result.stderr
        assert "cursor interactive session" in result.stderr
        model = selection[-1] if selection else ""
        if selection[0] == "--":
            assert "not from forwarded" in result.stderr
        elif model in {"auto", "--model=Auto", "cursor:auto", "composer-2.5[fast=true]"}:
            assert "CURSOR_MODEL_NOT_APPROVED" in result.stderr
    assert argv is None
    assert "mock deploy" not in result.stdout


@pytest.mark.parametrize("model", ("auto", "grok-4.7-high-fast"))
def test_cursor_interactive_refuses_auto_and_fast_from_the_environment(tmp_path: Path, model: str) -> None:
    result, argv = _run_interactive(tmp_path, env={"LAUNCHER_MODEL": model})
    if model.startswith("grok-"):
        # A Grok variant names a retired prefix (GROK-CANCEL-1110).
        assert result.returncode == 2, result.stdout + result.stderr
        assert "is retired in the model catalog" in result.stderr
    else:
        assert result.returncode == 4, result.stdout + result.stderr
        assert "not certified for the cursor interactive session" in result.stderr
        assert "CURSOR_MODEL_NOT_APPROVED" in result.stderr
    assert argv is None


@pytest.mark.parametrize("model", ["opus", "sonnet", "haiku", "haiku-5-5", "claude-3-5-sonnet-20241022", "claude-fable-5-1"])
def test_cursor_driver_refuses_claude_models(model: str, tmp_path: Path) -> None:
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    result = run_launcher(
        DRIVER, "--epic", "infra", "--model", model,
        env={"PATH": f"{tmp_path}{os.pathsep}{os.defpath}"},
    )
    assert result.returncode == 4, result.stderr
    assert "CURSOR_CLAUDE_REFUSED" in result.stderr
    assert "native Claude CLI" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout


def test_cursor_driver_refuses_retired_fable_5_before_the_claude_gate(tmp_path: Path) -> None:
    """The retired Fable 5 predecessor fails before the Claude transport guard."""
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    result = run_launcher(
        DRIVER, "--epic", "infra", "--model", "claude-fable-5",
        env={"PATH": f"{tmp_path}{os.pathsep}{os.defpath}"},
    )
    assert result.returncode == 2, result.stderr
    assert "is retired in the model catalog" in result.stderr
    assert "claude-fable-5-1" in result.stderr
    assert "would exec" not in result.stdout
