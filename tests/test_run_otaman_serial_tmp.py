"""Exercise serial log destinations without invoking any provider or real bridge."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_otaman_serial_12_15.sh"


@pytest.fixture
def serial_environment(tmp_path):
    checkout = tmp_path / "synthetic checkout"
    script = checkout / "scripts" / SCRIPT.name
    fake_bridge = checkout / ".venv/bin/python"
    fake_sleep = checkout / "bin/sleep"
    for path in (script, fake_bridge, fake_sleep):
        path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, script)
    fake_bridge.write_text(
        r'''#!/bin/bash
printf '%s\0' "$@" >> "$FAKE_ARGV"
module=""
for argument in "$@"; do
  case "$argument" in otaman-a1-*) module="${argument##*-}" ;; esac
done
printf 'stdout %s\r\n\000tail\n' "$module"
printf 'stderr %s\r\n' "$module" >&2
if [[ "$module" == "${FAIL_MODULE:-}" ]]; then exit 23; fi
''',
        encoding="utf-8",
    )
    fake_sleep.write_text(
        '#!/bin/bash\nprintf "%s\\n" "$@" >> "$FAKE_SLEEPS"\n',
        encoding="utf-8",
    )
    fake_bridge.chmod(0o700)
    fake_sleep.chmod(0o700)
    override = tmp_path / "override logs with spaces"
    scratch = tmp_path / "existing task scratch"
    override.mkdir()
    scratch.mkdir()
    env = os.environ.copy()
    env.update(
        PATH=f"{fake_sleep.parent}:{env['PATH']}",
        TMPDIR=str(override),
        LU_TASK_SCRATCH_DIR=str(scratch),
        FAKE_ARGV=str(tmp_path / "argv"),
        FAKE_SLEEPS=str(tmp_path / "sleeps"),
    )
    env.pop("FAIL_MODULE", None)
    return checkout, script, env, override, scratch


@pytest.mark.parametrize("root_kind", ["override", "scratch", "empty_override"])
@pytest.mark.parametrize("fail_module", [None, 12, 13, 14, 15])
def test_serial_logs_and_exit_behavior(serial_environment, root_kind, fail_module):
    checkout, script, env, override, scratch = serial_environment
    if root_kind == "scratch":
        env.pop("TMPDIR")
    elif root_kind == "empty_override":
        env["TMPDIR"] = ""
    root = override if root_kind == "override" else scratch
    unused_root = scratch if root_kind == "override" else override
    for module in range(12, 16):
        (root / f"otaman-a1-{module}-serial.log").write_bytes(b"previous log\n")
    if fail_module is not None:
        env["FAIL_MODULE"] = str(fail_module)
    result = subprocess.run(
        ["bash", str(script)], cwd=checkout, env=env, capture_output=True, timeout=10,
    )
    assert result.returncode == (0 if fail_module is None else 23)
    assert result.stderr == b""
    attempted = range(12, (fail_module or 15) + 1)
    completed = range(12, fail_module or 16)
    expected_stdout = "Starting serial otaman execution for A1 modules 12-15\n"
    for module in attempted:
        expected_stdout += f"--- Processing Module {module} ---\n"
        if module in completed:
            expected_stdout += f"Module {module} completed successfully.\n"
        assert (root / f"otaman-a1-{module}-serial.log").read_bytes() == (
            f"stdout {module}\r\n\0tail\nstderr {module}\r\n".encode()
        )
    if fail_module is None:
        expected_stdout += "Serial execution completed.\n"
    else:
        for module in range(fail_module + 1, 16):
            assert (root / f"otaman-a1-{module}-serial.log").read_bytes() == b"previous log\n"
    assert result.stdout == expected_stdout.encode()
    assert list(unused_root.iterdir()) == []
    assert sorted(path.name for path in root.iterdir()) == [
        f"otaman-a1-{module}-serial.log" for module in range(12, 16)
    ]
    expected_argv = []
    for module in attempted:
        expected_argv.extend([
            "scripts/ai_agent_bridge/__main__.py", "ask-gemini",
            "Activate skill otaman. Read and execute the instructions at "
            f"{checkout}/.gemini/skills/otaman/SKILL.md to process a1 {module}",
            "--task-id", f"otaman-a1-{module}", "--allow-write", "--model",
            "gemini-3.8-flash-high",
        ])
    assert Path(env["FAKE_ARGV"]).read_bytes() == (
        "\0".join(expected_argv) + "\0"
    ).encode()
    sleeps = Path(env["FAKE_SLEEPS"])
    assert (sleeps.read_bytes() if sleeps.exists() else b"") == b"10\n" * len(completed)


@pytest.mark.parametrize("root_kind", ["override", "scratch", "empty_override"])
def test_diagnostic_uses_the_resolved_log_path(serial_environment, root_kind):
    # set -e normally exits before the legacy failure diagnostic. Exercise its
    # original shell statement separately without changing that exit behavior.
    checkout, script, env, override, scratch = serial_environment
    if root_kind == "scratch":
        env.pop("TMPDIR")
    elif root_kind == "empty_override":
        env["TMPDIR"] = ""
    root = override if root_kind == "override" else scratch
    statements = script.read_text(encoding="utf-8").splitlines()
    root_assignment = next(line for line in statements if line.startswith("LOG_ROOT="))
    log_assignment = next(line.strip() for line in statements if line.strip().startswith("log_file="))
    diagnostic = next(line.strip() for line in statements if "failed. Check log:" in line)
    result = subprocess.run(
        ["bash", "-c", f"set -e\n{root_assignment}\ni=14\n{log_assignment}\n{diagnostic}"],
        cwd=checkout, env=env, capture_output=True, timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == f"Module 14 failed. Check log: {root}/otaman-a1-14-serial.log\n".encode()
    assert result.stderr == b""


def test_missing_task_root_does_not_invoke_bridge(serial_environment):
    checkout, script, env, override, scratch = serial_environment
    env.pop("TMPDIR")
    env.pop("LU_TASK_SCRATCH_DIR")
    result = subprocess.run(
        ["bash", str(script)], cwd=checkout, env=env, capture_output=True, timeout=10,
    )
    assert result.returncode != 0
    assert b"Set TMPDIR or LU_TASK_SCRATCH_DIR" in result.stderr
    assert not Path(env["FAKE_ARGV"]).exists()
    assert list(override.iterdir()) == list(scratch.iterdir()) == []


@pytest.mark.parametrize("root_kind", ["override", "scratch"])
def test_invalid_selected_root_does_not_fall_back(serial_environment, root_kind):
    checkout, script, env, override, scratch = serial_environment
    root = override if root_kind == "override" else scratch
    unused_root = scratch if root_kind == "override" else override
    if root_kind == "scratch":
        env.pop("TMPDIR")
    root.rmdir()
    root.write_bytes(b"not a directory\n")
    result = subprocess.run(
        ["bash", str(script)], cwd=checkout, env=env, capture_output=True, timeout=10,
    )
    assert result.returncode != 0
    assert result.stdout == (
        b"Starting serial otaman execution for A1 modules 12-15\n"
        b"--- Processing Module 12 ---\n"
    )
    assert b"otaman-a1-12-serial.log" in result.stderr
    assert not Path(env["FAKE_ARGV"]).exists()
    assert not Path(env["FAKE_SLEEPS"]).exists()
    assert root.read_bytes() == b"not a directory\n"
    assert list(unused_root.iterdir()) == []
