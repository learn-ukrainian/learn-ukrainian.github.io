"""Cursor driver launcher seat + lifecycle tests (#6956)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.review.model_catalog import load_model_catalog
from tests.test_launcher_contract import REPO, run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

DRIVER = "start-cursor-driver.sh"
RETIRED_MODEL_IDS = {
    model_id for model_id, entry in load_model_catalog()["models"].items()
    if entry["lifecycle"] == "retired"
}


def test_cursor_driver_wrapper_calls_launcher_main_cursor() -> None:
    text = (REPO / DRIVER).read_text(encoding="utf-8")
    assert "launcher_core.sh" in text
    assert "launcher_main cursor driver" in text
    assert (REPO / DRIVER).stat().st_mode & 0o111


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

    result = run_launcher(DRIVER, "--epic", "infra", env={"PATH": probe_path})
    assert result.returncode == 0, result.stderr
    assert "would exec agent" not in result.stdout
    assert "would require binary cursor-agent" in result.stdout
    assert "would exec cursor-agent" in result.stdout


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
    assert "Cursor agent executable (cursor-agent) is unavailable." in result.stderr
    assert not marker.exists()
    assert "ran" not in result.stdout


def test_cursor_driver_requires_epic_fail_closed() -> None:
    """Launching without --epic must not silently claim main orchestrator."""
    missing = run_launcher(DRIVER)
    assert missing.returncode == 2, missing.stderr
    assert "driver launch requires --epic" in missing.stderr


@pytest.mark.parametrize("selector", ("infra", "devops", "atlas", "corpus"))
def test_cursor_driver_claims_lease_for_supported_selectors(selector: str) -> None:
    result = run_launcher(DRIVER, "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    assert "cursor adapter: provider canary: not run" in result.stdout
    assert "ran its provider canary" not in result.stdout
    assert "would bind drive-epic" in result.stdout
    assert "would heartbeat observer presence agent=cursor" in result.stdout
    assert "would renew observer presence while the driver session runs" in result.stdout
    assert "--model grok-4.7-high" in result.stdout


@pytest.mark.parametrize(
    "selector, slot", (("folk", "cursor-folk"), ("seminars-bio", "cursor-bio"), ("hramatka", "cursor-hramatka"))
)
def test_cursor_driver_refuses_ukrainian_content_slots(selector: str, slot: str) -> None:
    result = run_launcher(DRIVER, "--epic", selector)
    assert result.returncode == 2, result.stdout + result.stderr
    assert slot in result.stderr
    assert "operator order 2026-09-27" in result.stderr
    assert "would claim lease" not in result.stdout


def test_cursor_driver_rejects_uncertified_model_and_foreign_harness() -> None:
    uncertified = run_launcher(DRIVER, "--epic", "devops", "--model", "cursor-unknown")
    harness = run_launcher(DRIVER, "--epic", "devops", "--harness", "agy")
    assert uncertified.returncode == 4
    assert "not certified" in uncertified.stderr
    assert harness.returncode == 2
    assert "only --harness cursor-agent" in harness.stderr


@pytest.mark.parametrize("model", ["grok-4.6", "grok-4.6[context=500k,reasoning_effort=high]"])
def test_cursor_driver_rejects_retired_grok_before_lease(model: str) -> None:
    result = run_launcher(DRIVER, "--epic", "devops", "--model", model)
    assert result.returncode == 2
    assert "is retired in the model catalog" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout


@pytest.mark.parametrize(
    "model",
    (
        "grok-4.7",
        "composer-2.5",
        "grok-4.7-high",
        "composer-2.5[fast=false]",
    ),
)
def test_cursor_driver_accepts_allowlisted_models(model: str) -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--model", model)
    assert result.returncode == 0, result.stderr
    # Dry-run prints the argv with shell quoting, so brackets and commas are escaped.
    quoted = model.replace("[", r"\[").replace("]", r"\]").replace(",", r"\,")
    assert f"--model {quoted}" in result.stdout


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
        if model.partition("[")[0] in RETIRED_MODEL_IDS:
            assert result.returncode == 2, result.stdout + result.stderr
            assert "is retired in the model catalog" in result.stderr
            assert model in result.stderr
        else:
            assert result.returncode == 4, result.stdout + result.stderr
            assert "not certified for the cursor driver" in result.stderr
            if model.startswith("grok-4.7"):
                assert "is an unattested variant" in result.stderr
                assert "CURSOR_UNATTESTED_GROK_VARIANT" in result.stderr
            else:
                assert "CURSOR_MODEL_NOT_APPROVED" in result.stderr
        assert "would claim lease" not in result.stdout
        assert "would exec" not in result.stdout


def test_cursor_driver_refuses_an_empty_model() -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--model=")
    assert result.returncode == 4, result.stdout + result.stderr
    assert "requires a concrete model" in result.stderr
    assert "would exec" not in result.stdout


def test_cursor_driver_empty_env_model_falls_back_to_the_pin() -> None:
    result = run_launcher(DRIVER, "--epic", "infra", env={"LAUNCHER_MODEL": ""})
    assert result.returncode == 0, result.stderr
    assert "--model grok-4.7-high" in result.stdout


@pytest.mark.parametrize(
    "forwarded",
    (("--model", "auto"), ("--model=auto",), ("--model", "grok-4.7-high"), ("--model=Auto",)),
)
def test_cursor_driver_refuses_a_forwarded_provider_model(forwarded: tuple[str, ...]) -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--", *forwarded)
    assert result.returncode == 4, result.stdout + result.stderr
    assert "not from forwarded" in result.stderr
    assert "would exec" not in result.stdout


def test_cursor_driver_forwards_other_provider_args() -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--", "--print-models")
    assert result.returncode == 0, result.stderr
    assert "--model grok-4.7-high" in result.stdout
    assert "--print-models" in result.stdout


def test_observer_heartbeat_is_cursor_gated_in_launcher_core() -> None:
    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "launcher_cursor_observer_presence" in core
    assert "launcher_cursor_observer_renew_loop" in core
    assert '[ "$LC_PROVIDER" = "cursor" ] || return 0' in core


def test_cursor_seat_enumerated_in_launcher_core_and_public_estate() -> None:
    """Seat hooks live as case arms (no separate seat list) next to sibling drivers."""
    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "cursor)" in core
    assert "handoff_identity_for_cursor_epic" in core
    assert "launcher_cursor_model_certified" in core
    assert Path(REPO / "scripts/launchers/cursor.sh").is_file()
    assert DRIVER in {path.name for path in REPO.glob("start-*-driver.sh") if path.parent == REPO}


# Interactive Cursor sessions (#9274): no public start-cursor.sh exists, but
# launcher_main cursor interactive is reachable, and it is not a typed
# implementation dispatch, so it pins a concrete model like the driver seat.
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


def _run_interactive(tmp_path: Path, *args: str, env: dict[str, str] | None = None):
    """Run launcher_main cursor interactive with a mock cursor-agent that records its argv."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    argv_file = tmp_path / "cursor-agent.argv"
    mock = bin_dir / "cursor-agent"
    mock.write_text(f"#!/bin/sh\nprintf '%s\\0' \"$@\" > '{argv_file}'\n", encoding="utf-8")
    mock.chmod(0o755)
    launch_env = os.environ.copy()
    launch_env.update(
        {
            "LAUNCHER_DRY_RUN": "0",
            "LC_TEST_REPO": str(REPO),
            "LU_SKIP_PLANE_TUNNEL_CHECK": "1",
            "PATH": f"{bin_dir}{os.pathsep}{launch_env['PATH']}",
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
    argv = argv_file.read_text(encoding="utf-8").split("\0")[:-1] if argv_file.exists() else None
    return result, argv


def test_cursor_seat_pin_matches_the_catalog_seat() -> None:
    """The launcher pin is orchestrator_seats.cursor model_id at its effort."""
    seat = load_model_catalog()["orchestrator_seats"]["cursor"]
    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert f"LC_CURSOR_SEAT_PIN={seat['model_id']}-{seat['effort']}\n" in core


def test_cursor_interactive_defaults_to_the_concrete_pin(tmp_path: Path) -> None:
    result, argv = _run_interactive(tmp_path, env={"LAUNCHER_MODEL": ""})
    assert result.returncode == 0, result.stdout + result.stderr
    assert argv is not None and argv[:2] == ["--model", "grok-4.7-high"]


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
    result, argv = _run_interactive(tmp_path, *selection)
    if selection[0] == "--model" and selection[1].partition("[")[0] in RETIRED_MODEL_IDS:
        assert result.returncode == 2, result.stdout + result.stderr
        assert "is retired in the model catalog" in result.stderr
        assert selection[1] in result.stderr
    else:
        assert result.returncode == 4, result.stdout + result.stderr
        assert "cursor interactive session" in result.stderr
        assert "grok-4.7-high or composer-2.5" in result.stderr
        model = selection[-1] if selection else ""
        if model.startswith("grok-4.7"):
            assert "is an unattested variant" in result.stderr
            assert "CURSOR_UNATTESTED_GROK_VARIANT" in result.stderr
        elif selection[0] != "--" and model in {"auto", "--model=Auto", "cursor:auto", "composer-2.5[fast=true]"}:
            assert "CURSOR_MODEL_NOT_APPROVED" in result.stderr
    assert argv is None
    assert "mock deploy" not in result.stdout


@pytest.mark.parametrize("model", ("auto", "grok-4.7-high-fast"))
def test_cursor_interactive_refuses_auto_and_fast_from_the_environment(tmp_path: Path, model: str) -> None:
    result, argv = _run_interactive(tmp_path, env={"LAUNCHER_MODEL": model})
    assert result.returncode == 4, result.stdout + result.stderr
    assert "not certified for the cursor interactive session" in result.stderr
    assert "grok-4.7-high or composer-2.5" in result.stderr
    if model.startswith("grok-4.7"):
        assert "is an unattested variant" in result.stderr
        assert "CURSOR_UNATTESTED_GROK_VARIANT" in result.stderr
    else:
        assert "CURSOR_MODEL_NOT_APPROVED" in result.stderr
    assert argv is None


@pytest.mark.parametrize("model", ("composer-2.5", "grok-4.7", "grok-4.7-high"))
def test_cursor_interactive_executes_an_explicit_approved_pin(tmp_path: Path, model: str) -> None:
    result, argv = _run_interactive(tmp_path, "--model", model)
    assert result.returncode == 0, result.stdout + result.stderr
    expected_model = "grok-4.7-high" if model == "grok-4.7" else model
    assert argv is not None and argv[:2] == ["--model", expected_model]

def test_cursor_rewrites_bare_grok_4_7_to_high() -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--model", "grok-4.7")
    assert result.returncode == 0, result.stderr
    assert "--model grok-4.7-high" in result.stdout

def test_cursor_refuses_claude_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure native claude CLI is "found" by creating a dummy in tmp_path and putting it in PATH
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    claude_bin = bin_dir / "claude"
    claude_bin.write_text("#!/bin/sh\nexit 0", encoding="utf-8")
    claude_bin.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

    result = run_launcher(DRIVER, "--epic", "infra", "--model", "claude-opus-5-5", env=env)
    assert result.returncode == 4, result.stdout + result.stderr
    assert "CURSOR_CLAUDE_REFUSED" in result.stderr

def test_cursor_claude_refusal_does_not_trip_for_non_claude() -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--model", "composer-2.5")
    assert result.returncode == 0, result.stderr
    assert "--model composer-2.5" in result.stdout

@pytest.mark.parametrize("model", ["opus", "sonnet", "haiku", "haiku-5-5", "claude-3-5-sonnet-20241022", "claude-fable-5-1"])
def test_cursor_driver_refuses_claude_models(model: str, tmp_path: Path) -> None:
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    result = run_launcher(
        DRIVER, "--epic", "infra", "--model", model,
        env={"PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}"},
    )
    assert result.returncode == 4, result.stderr
    assert "CURSOR_CLAUDE_REFUSED" in result.stderr
    assert "native Claude CLI" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout
