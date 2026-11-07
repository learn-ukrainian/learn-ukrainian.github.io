"""Launcher tests and provider children must not inherit another seat's defaults."""

from __future__ import annotations

import ast
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from tests.helpers import machinery_package
from tests.launcher_sandbox import (
    LAUNCHER_TEST_FILES,
    POLLUTED_PARENT_TESTS,
    SEAT_CONTAMINATION,
    launcher_environment,
    tracked_launcher_wrappers,
)


def _child_environment(path: Path) -> dict[str, str]:
    return dict(entry.split("=", 1) for entry in path.read_text().split("\0") if entry)


def test_session_scratch_avoids_long_unix_socket_paths_per_worker(tmp_path: Path) -> None:
    """A long basetemp must not force socket consumers over the AF_UNIX limit."""
    source = Path(__file__).with_name("conftest.py").read_text()
    hook = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "pytest_sessionstart_runtime_scratch"
    )
    suite = tmp_path / "socket-probe"
    suite.mkdir()
    (suite / "pytest.ini").write_text("[pytest]\n")
    (suite / "test_empty.py").write_text("")
    # Load the real seam without the repository's unrelated fixture/guard graph.
    (suite / "scratch_probe.py").write_text(
        "import json, os, shutil, stat, tempfile\n"
        "from pathlib import Path\n"
        "import pytest\n"
        '@pytest.hookimpl(specname="pytest_sessionstart", tryfirst=True)\n'
        + ast.get_source_segment(source, hook)
        + '\n@pytest.hookimpl(specname="pytest_sessionstart", trylast=True)\n'
        "def pytest_sessionstart_observe(session):\n"
        '    root = Path(os.environ["LU_SCRATCH_ROOT"])\n'
        '    assert os.environ["LU_SCRATCH_SCAN_ROOT"] == str(root)\n'
        '    worker = os.environ.get("PYTEST_XDIST_WORKER", "controller")\n'
        '    row = {"root": str(root), "mode": stat.S_IMODE(root.stat().st_mode)}\n'
        '    Path(worker + ".json").write_text(json.dumps(row))\n'
    )
    basetemp = suite / ("long-basetemp-" + "x" * 160)
    assert len(os.fsencode(basetemp)) > 160
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(suite / "pytest.ini"),
            "-p",
            "xdist.plugin",
            "-p",
            "scratch_probe",
            "-n",
            "2",
            "--dist=worksteal",
            "--basetemp=" + str(basetemp),
        ],
        cwd=suite,
        env=launcher_environment(
            tmp_path=tmp_path,
            PYTHONPATH=str(suite),
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        ),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == pytest.ExitCode.NO_TESTS_COLLECTED, result.stdout + result.stderr
    observations = [json.loads((suite / f"{worker}.json").read_text()) for worker in ("controller", "gw0", "gw1")]
    roots = [Path(row["root"]) for row in observations]
    assert len(set(roots)) == 3
    assert all(row["mode"] == 0o700 for row in observations)
    assert all(len(os.fsencode(root / "pg-XXXXXXXX" / ".s.PGSQL.65535")) <= 103 for root in roots)
    assert all(not root.exists() for root in roots)


def test_environment_builder_isolates_seat_state_and_preserves_explicit_inputs(monkeypatch) -> None:
    for name, value in SEAT_CONTAMINATION.items():
        monkeypatch.setenv(name, value)
    first = launcher_environment()
    second = launcher_environment({"LAUNCHER_MODEL": "intentional", "GIT_DIR": "/hostile"})
    assert not set(first).intersection(SEAT_CONTAMINATION)
    assert first["HOME"] != second["HOME"]
    assert Path(first["HOME"]).is_dir()
    assert Path(first["TMPDIR"]).is_dir()
    assert first["LU_MONITOR_LOOPBACK"] == "http://127.0.0.1:1"
    assert second["LAUNCHER_MODEL"] == "intentional"
    assert second["GIT_DIR"] == "/hostile"


@pytest.mark.parametrize(
    ("wrapper", "default_model", "override_model", "cli_model", "args"),
    (
        ("start-claude-cto.sh", "claude-sonnet-5-5", "claude-sonnet-5-5", "claude-opus-5-5", ()),
        ("start-codex-cto.sh", "gpt-6.1-sol", "gpt-6.1-sol", "gpt-6.1-sol", ()),
        (
            f"{machinery_package()}/start-kube-dojo-driver.sh",
            "claude-sonnet-5-5",
            "claude-sonnet-5-5",
            "claude-sonnet-5-5",
            (),
        ),
        ("start-codex.sh", "gpt-6.1-sol", "gpt-6.1-sol", "gpt-6.1-sol", ()),
        ("start-codex-driver.sh", "gpt-6.1-sol", "gpt-6.1-sol", "gpt-6.1-sol", ("--epic", "devops")),
    ),
)
@pytest.mark.parametrize("selection", ("default", "environment", "cli"))
def test_provider_child_drops_launcher_controls_after_scope_reentry(
    tmp_path: Path,
    wrapper: str,
    default_model: str,
    override_model: str,
    cli_model: str,
    args: tuple[str, ...],
    selection: str,
) -> None:
    from tests.test_launcher_interactive_scope import _checkout, _identity, _launch, _lines

    root, env = _checkout(tmp_path)
    extra = {
        "LAUNCHER_SEAT_SENTINEL": "must-not-reach-provider",
        "LAUNCHER_INVALID-NAME": "must-not-reach-provider",
        "LAUNCHER_NEWLINE\nNAME": "must-not-reach-provider",
    }
    expected_model, expected_effort = default_model, "high"
    if selection != "default":
        extra.update(LAUNCHER_MODEL=override_model, LAUNCHER_EFFORT="medium")
        expected_model, expected_effort = override_model, "medium"
    if selection == "cli":
        extra["LAUNCHER_MODEL"] = "not-certified"
        args = (*args, "--model", cli_model, "--effort", "high")
        expected_model, expected_effort = cli_model, "high"
    result = _launch(root, env, wrapper, *args, **extra)
    assert result.returncode == 42, result.stdout + result.stderr
    identity = _identity(env)
    assert (identity["model"], identity["effort"]) == (expected_model, expected_effort)
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    assert result.stderr.count("DRIVER_SCOPE_VERIFIED") == 2
    child = _child_environment(Path(env["TEST_PROVIDER_ENV"]))
    assert not [name for name in child if name.startswith("LAUNCHER_")]
    assert child["LU_DRIVER_SCOPE_UNIT"] == identity["unit"]
    if identity["mode"] == "driver":
        assert child["SESSION_HANDOFF_AGENT"]


def test_direct_exec_without_credential_helper_still_drops_launcher_controls(tmp_path: Path) -> None:
    core = Path(__file__).resolve().parents[1] / machinery_package() / "lib/launcher_core.sh"
    capture = tmp_path / "child-env"
    script = f"""
set -euo pipefail
source {shlex.quote(str(core))}
LC_MODE=interactive LC_PROVIDER=claude LC_DURABLE_HELPER_ROOT=''
launcher_exec_command /bin/sh -c 'env -0 > "$TEST_CHILD_ENV"'
"""
    result = subprocess.run(
        ["bash", "-c", script],
        env=launcher_environment(
            {"LAUNCHER_INVALID-NAME": "sentinel", "LAUNCHER_NEWLINE\nNAME": "sentinel"},
            LAUNCHER_MODEL="claude-sonnet-5-5",
            LAUNCHER_EFFORT="medium",
            LAUNCHER_UNKNOWN="sentinel",
            TEST_CHILD_ENV=str(capture),
        ),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    child = _child_environment(capture)
    assert not [name for name in child if name.startswith("LAUNCHER_")]


@pytest.mark.parametrize(
    "wrapper",
    ("start-codex-cto.sh", f"{machinery_package()}/start-kube-dojo-driver.sh", "start-codex-driver.sh"),
)
def test_successor_replay_keeps_supervisor_defaults_but_cleans_both_provider_children(
    tmp_path: Path,
    wrapper: str,
) -> None:
    from tests.test_launcher_interactive_scope import _checkout, _identity, _launch, _lines

    root, env = _checkout(tmp_path)
    provider = Path(env["TEST_PROVIDER"])
    provider.write_text("""#!/usr/bin/env bash
if [ -z "${SESSION_SUPERVISOR_WAKE_DELIVERY:-}" ]; then
  env -0 > "$TEST_FIRST_ENV"
  trap 'exit 0' TERM
  touch "$TEST_FIRST_READY"
  while :; do sleep 0.01; done
else
  env -0 > "$TEST_SECOND_ENV"
  exit 42
fi
""")
    watcher = root / machinery_package() / "ai_agent_bridge/inbox_watch.sh"
    watcher.write_text("""#!/usr/bin/env bash
if [ "${2:-}" = --launch-plan ]; then
  printf '%s\\n' '{"session_id":"session-test","generation":1}'
  exit 0
fi
if [ -n "${SESSION_SUPERVISOR_WAKE_DELIVERY:-}" ]; then exec sleep 300; fi
while [ ! -f "$TEST_FIRST_READY" ]; do sleep 0.01; done
printf 'fixture-delivery\\n'
# The production loop also observes watcher exit without a notification.
exit 75
""")
    first, second = tmp_path / "first-env", tmp_path / "second-env"
    model = "gpt-6.1-sol" if "codex" in wrapper else "claude-sonnet-5-5"
    args = ("--epic", "devops") if wrapper == "start-codex-driver.sh" else ()
    result = _launch(
        root,
        env,
        wrapper,
        *args,
        LAUNCHER_MODEL=model,
        LAUNCHER_EFFORT="medium",
        LAUNCHER_UNKNOWN="sentinel",
        TEST_FIRST_ENV=str(first),
        TEST_SECOND_ENV=str(second),
        TEST_FIRST_READY=str(tmp_path / "first-ready"),
    )
    assert result.returncode == 42, result.stdout + result.stderr
    assert _identity(env)["model"] == model
    assert _identity(env)["effort"] == "medium"
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    for capture in (first, second):
        child = _child_environment(capture)
        assert not [name for name in child if name.startswith("LAUNCHER_")]
        assert child["SESSION_HANDOFF_AGENT"]


def test_tracked_wrapper_coverage_cannot_silently_shrink() -> None:
    from tests.test_launcher_interactive_scope import DRIVERS, INTERACTIVE

    assert {node.split("::")[0] for node in POLLUTED_PARENT_TESTS} | {
        "tests/test_launcher_env_hermetic.py"
    } == set(LAUNCHER_TEST_FILES)
    retired = {"start-kimi.sh", "start-kimicc.sh"}
    public_only = {"start-muse-driver.sh"}
    assert set(tracked_launcher_wrappers()) == set(DRIVERS) | set(INTERACTIVE) | retired | public_only
