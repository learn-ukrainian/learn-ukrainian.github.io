"""scripts/lib/session_supervisor.sh: claim env + capsule writing."""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
from pathlib import Path

from scripts.session_canary import codex_lane, gemini_lane

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Git redirection variables inherited from the outer test runner (e.g. a git
# hook) must not leak into the temporary repos created by these tests.
_GIT_REDIRECT_VARS = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_WORK_TREE",
    }
)


def _clean_environ() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT_VARS}


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _supervisor_ok_body(capture: Path) -> str:
    return f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.api.occupancy_local" && "${{3:-}}" == "resolve-host-id" ]]; then
  if [[ "${{FAKE_RESOLVER_FAILURE:-0}}" == "1" ]]; then
    echo "resolver unavailable" >&2
    exit 1
  fi
  printf '%s\\n' "${{FAKE_RESOLVED_HOST_ID:-local}}"
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" && "${{3:-}}" == "open" ]]; then
  {{
    printf '%s\\n' "$@" > "{capture}"
    cat <<'JSON'
{{
  "schema": "session-supervisor-bootstrap.v1",
  "identity": {{
    "role": "driver",
    "stream_id": "epic:9999",
    "lease": {{
      "session_id": "sess-shell-789",
      "lease_id": "lease-shell-789",
      "generation": 3,
      "fencing_token": 3,
      "expires_at": "2026-07-21T03:00:00Z"
    }},
    "lease_credentials_exported": false
  }},
  "rollover": null,
  "digest": {{}},
  "dual_write": {{}},
  "diagnostics": {{}}
}}
JSON
  }}
  exit 0
fi
if [[ "$1" == "-c" ]]; then
  shift
  exec /usr/bin/env python3 -c "$@"
fi
if [[ "$1" == "-" ]]; then
  shift
  exec /usr/bin/env python3 - "$@"
fi
echo "unexpected python args: $*" >&2
exit 1
"""


def _build_fake_project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    project.mkdir()
    venv_bin = project / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    lib_dir = project / "scripts" / "lib"
    lib_dir.mkdir(parents=True)

    (lib_dir / "session_supervisor.sh").write_text(
        (_REPO_ROOT / "scripts" / "lib" / "session_supervisor.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    capture = tmp_path / "supervisor_capture.txt"
    _write_executable(venv_bin / "python", _supervisor_ok_body(capture))

    env = _clean_environ()
    subprocess.run(["git", "init", "--quiet", str(project)], check=True, env=env, timeout=30)
    subprocess.run(
        ["git", "-C", str(project), "config", "user.email", "test@example.com"], check=True, env=env, timeout=30
    )
    subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True, env=env, timeout=30)
    (project / "README.md").write_text("# test", encoding="utf-8")
    subprocess.run(["git", "-C", str(project), "add", "."], check=True, env=env, timeout=30)
    subprocess.run(["git", "-C", str(project), "commit", "--quiet", "-m", "init"], check=True, env=env, timeout=30)
    subprocess.run(["git", "-C", str(project), "branch", "-m", "main"], check=True, env=env, timeout=30)

    return project, capture


def test_claim_exports_all_session_stream_variables_and_writes_capsule(tmp_path: Path) -> None:
    project, supervisor_capture = _build_fake_project(tmp_path)

    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "test-task" "test-instance" "{project}" "test-launcher.sh" "hramatka"
printf 'STREAM=%s\\n' "$SESSION_STREAM_ID"
printf 'SESSION=%s\\n' "$SESSION_STREAM_SESSION_ID"
printf 'LEASE=%s\\n' "$SESSION_STREAM_LEASE_ID"
printf 'AGENT=%s\\n' "$SESSION_STREAM_AGENT"
printf 'HARNESS=%s\\n' "$SESSION_STREAM_HARNESS"
printf 'INSTANCE=%s\\n' "$SESSION_STREAM_INSTANCE_ID"
printf 'PROCESS=%s\\n' "$SESSION_STREAM_PROCESS_ID"
printf 'GENERATION=%s\\n' "$SESSION_STREAM_GENERATION"
printf 'FENCING=%s\\n' "$SESSION_STREAM_FENCING_TOKEN"
printf 'CAPSULE=%s\\n' "$SESSION_SUPERVISOR_CAPSULE_PATH"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=_clean_environ(),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    lines = {k: v for k, v in (line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)}
    assert lines["STREAM"] == "epic:9999"
    assert lines["SESSION"] == "sess-shell-789"
    assert lines["LEASE"] == "lease-shell-789"
    assert lines["AGENT"] == "test-agent"
    assert lines["HARNESS"] == "test-harness"
    assert lines["INSTANCE"] == "test-instance"
    assert lines["PROCESS"].isdigit()
    assert lines["GENERATION"] == "3"
    assert lines["FENCING"] == "3"
    capsule_path = Path(lines["CAPSULE"])
    assert capsule_path.exists()

    capsule = capsule_path.read_text(encoding="utf-8")
    assert '"schema_version": 1' in capsule
    assert '"stream_id": "epic:9999"' in capsule
    assert '"launcher": "test-launcher.sh"' in capsule
    assert '"epic": "hramatka"' in capsule
    assert '"agent": "test-agent"' in capsule
    assert '"harness": "test-harness"' in capsule
    assert '"task_id": "test-task"' in capsule

    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert supervisor_args[supervisor_args.index("--stream") + 1] == "epic:9999"
    assert supervisor_args[supervisor_args.index("--agent") + 1] == "test-agent"
    assert supervisor_args[supervisor_args.index("--harness") + 1] == "test-harness"
    assert supervisor_args[supervisor_args.index("--instance-id") + 1] == "test-instance"
    assert supervisor_args[supervisor_args.index("--task-id") + 1] == "test-task"
    assert supervisor_args[supervisor_args.index("--role") + 1] == "driver"
    assert "scripts.session_supervisor" in supervisor_args
    assert "open" in supervisor_args

    receipt_path = project / ".claude" / "hramatka-epic" / "session-lease.env"
    assert receipt_path.is_file()
    expected_receipt = {
        "SESSION_STREAM_ID": "epic:9999",
        "SESSION_STREAM_SESSION_ID": "sess-shell-789",
        "SESSION_STREAM_LEASE_ID": "lease-shell-789",
        "SESSION_STREAM_AGENT": "test-agent",
        "SESSION_STREAM_HARNESS": "test-harness",
        "SESSION_STREAM_INSTANCE_ID": "test-instance",
        "SESSION_STREAM_GENERATION": "3",
        "SESSION_STREAM_FENCING_TOKEN": "3",
    }
    assert {key: gemini_lane._read_lease_environment(receipt_path)[key] for key in expected_receipt} == expected_receipt
    assert {key: codex_lane._read_lease_environment(receipt_path)[key] for key in expected_receipt} == expected_receipt


def test_claim_uses_default_instance_id_when_empty(tmp_path: Path) -> None:
    project, supervisor_capture = _build_fake_project(tmp_path)

    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "" "" "{project}" "test-launcher.sh" "hramatka"
printf 'INSTANCE=%s\\n' "$SESSION_STREAM_INSTANCE_ID"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=_clean_environ(),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    lines = {k: v for k, v in (line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)}
    assert lines["INSTANCE"].startswith("test-agent-")

    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert supervisor_args[supervisor_args.index("--instance-id") + 1].startswith("test-agent-")


def test_claim_resolves_unset_host_id_and_preserves_explicit_override(tmp_path: Path) -> None:
    project, supervisor_capture = _build_fake_project(tmp_path)
    env = _clean_environ()
    env.pop("LU_MONITOR_HOST_ID", None)
    env["FAKE_RESOLVED_HOST_ID"] = "host-job"

    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "" "" "{project}" "test-launcher.sh" "hramatka"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert supervisor_args[supervisor_args.index("--host-id") + 1] == "host-job"

    env["LU_MONITOR_HOST_ID"] = "host-explicit"
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert supervisor_args[supervisor_args.index("--host-id") + 1] == "host-explicit"

    env.pop("LU_MONITOR_HOST_ID")
    env["FAKE_RESOLVER_FAILURE"] = "1"
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stderr == ""
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert supervisor_args[supervisor_args.index("--host-id") + 1] == "local"


def test_claim_fails_closed_on_missing_required_fields(tmp_path: Path) -> None:
    project, _supervisor_capture = _build_fake_project(tmp_path)
    # Replace fake python with one that returns an incomplete lease.
    _write_executable(
        project / ".venv" / "bin" / "python",
        """#!/usr/bin/env bash
if [[ "${1:-}" == "-m" && "${2:-}" == "scripts.session_supervisor" && "${3:-}" == "open" ]]; then
  cat <<'JSON'
{
  "identity": {
    "lease": {
      "session_id": "sess-shell-789"
    }
  }
}
JSON
  exit 0
fi
if [[ "$1" == "-c" ]]; then
  shift
  exec /usr/bin/env python3 -c "$@"
fi
if [[ "$1" == "-" ]]; then
  shift
  exec /usr/bin/env python3 - "$@"
fi
echo "unexpected python args: $*" >&2
exit 1
""",
    )

    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "" "" "{project}" "test-launcher.sh" "hramatka" || exit 42
exit 0
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=_clean_environ(),
    )
    assert result.returncode == 42, result.stderr + result.stdout
    assert "missing required SESSION_STREAM_* fields" in result.stderr


def test_claim_fails_closed_on_supervisor_error(tmp_path: Path) -> None:
    project, _supervisor_capture = _build_fake_project(tmp_path)
    _write_executable(
        project / ".venv" / "bin" / "python",
        """#!/usr/bin/env bash
echo "supervisor refused" >&2
exit 1
""",
    )

    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "" "" "{project}" "test-launcher.sh" "hramatka" || exit 43
exit 0
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=_clean_environ(),
    )
    assert result.returncode == 43, result.stderr + result.stdout
    assert "session supervisor failed" in result.stderr


def _run_launcher_wake_scenario(
    tmp_path: Path, scenario: str, *, widen_wait_window: bool = False, timeout: int = 45,
) -> tuple[subprocess.CompletedProcess[str], list[str], float]:
    import shlex
    import sys
    import time

    root = tmp_path / scenario
    lib = root / "scripts" / "lib"
    lib.mkdir(parents=True)
    for name in ("launcher_core.sh", "session_supervisor.sh"):
        (lib / name).write_text((_REPO_ROOT / "scripts" / "lib" / name).read_text())
    watcher = root / "scripts" / "ai_agent_bridge" / "inbox_watch.sh"
    watcher.parent.mkdir()
    log = root / "events"
    provider_pid = root / "provider-pid"
    wait_window = root / "wait-window"
    _write_executable(watcher, f'''#!/usr/bin/env bash
while [ ! -f {shlex.quote(str(provider_pid))} ]; do sleep 0.01; done
if [ '{widen_wait_window}' = True ]; then
  while [ ! -f {shlex.quote(str(wait_window))} ]; do sleep 0.01; done
fi
if [ '{scenario}' = normal_exit ]; then exec sleep 30; fi
if [ '{scenario}' = watcher_ignores_term ]; then trap '' TERM; exec sleep 30; fi
printf 'delivery-test\\n'
kill -USR1 "$PPID"
if [ '{scenario}' = watcher_failure ]; then exit 2; fi
exit 75
''')
    provider = root / "provider.py"
    provider.write_text(f'''import os, signal, time
from pathlib import Path
log = Path({str(log)!r})
def stop(*args):
    with log.open("a") as f: f.write("stopped\\n")
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
Path({str(provider_pid)!r}).write_text(str(os.getpid()))
if {scenario!r} in ("normal_exit", "watcher_ignores_term"):
    time.sleep(0.1)
    stop()
while True: time.sleep(0.01)
''')
    successor = root / "start-codex-driver.sh"
    _write_executable(successor, f'''#!/usr/bin/env bash
[ "$SESSION_SUPERVISOR_WAKE_DELIVERY" = delivery-test ] || exit 41
[ "$SESSION_SUPERVISOR_WAKE_STREAM" = epic:9999 ] || exit 42
[ -z "${{SESSION_STREAM_LEASE_ID:-}}" ] || exit 43
[ "$#" = 2 ] && [ "$1" = '--fixture' ] && [ "$2" = 'two words' ] || exit 44
printf 'successor\\n' >> {shlex.quote(str(log))}
''')
    script = f'''
set -euo pipefail
source {shlex.quote(str(lib / 'launcher_core.sh'))}
source {shlex.quote(str(lib / 'session_supervisor.sh'))}
LC_ROOT={shlex.quote(str(root))}
LC_MODE=driver LC_PROVIDER=codex LC_DRIVER_LEASE_CLAIMED=1 LC_DRY_RUN=0
LC_DRIVER_ORIGINAL_ARGS=(--fixture 'two words')
export SESSION_STREAM_ID=epic:9999 SESSION_STREAM_LEASE_ID=lease-test
launcher_driver_renew_loop() {{ :; }}
launcher_cursor_observer_renew_loop() {{ :; }}
if [ '{widen_wait_window}' = True ]; then
  launcher_driver_wait_hook() {{ touch {shlex.quote(str(wait_window))}; sleep 0.3 || true; }}
fi
launcher_close_driver_lease() {{
  if kill -0 "$(cat {shlex.quote(str(provider_pid))})" 2>/dev/null; then return 45; fi
  printf 'close\\n' >> {shlex.quote(str(log))}
  [ '{scenario}' != close_failure ] || return 1
  LC_DRIVER_LEASE_CLOSED=1
}}
launcher_exec_command {shlex.quote(sys.executable)} {shlex.quote(str(provider))}
'''
    started = time.monotonic()
    # A provider or watcher can retain the pipes after bash exits. Kill the
    # entire process group on timeout so communicate can reach EOF, and surface
    # the first failure without retrying the scenario.
    with subprocess.Popen(
        ["bash", "-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            raise subprocess.TimeoutExpired(
                process.args, timeout, output=stdout, stderr=stderr
            ) from None
    result = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    return result, log.read_text().splitlines(), time.monotonic() - started


def test_launcher_wake_process_lifecycle(tmp_path: Path) -> None:
    """A real watcher signal reaps the provider before exact close and exec."""
    for scenario in ("wake", "watcher_failure", "close_failure", "normal_exit", "watcher_ignores_term"):
        result, events, _ = _run_launcher_wake_scenario(tmp_path, scenario)
        assert result.returncode == (1 if scenario in ("watcher_failure", "close_failure") else 0), result.stderr
        expected = ["stopped", "close"]
        if scenario == "wake":
            expected.append("successor")
        assert events == expected


def test_launcher_wake_survives_signal_between_check_and_wait(tmp_path: Path) -> None:
    """Deliver USR1 inside the widened check-to-wait window, without retries."""
    result, events, elapsed = _run_launcher_wake_scenario(tmp_path, "wake", widen_wait_window=True)
    assert result.returncode == 0, result.stderr
    assert events == ["stopped", "close", "successor"]
    assert elapsed < 5, f"Supervisory wake took {elapsed:.3f}s"
