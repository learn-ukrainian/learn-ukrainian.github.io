"""scripts/lib/session_supervisor.sh: claim env + capsule writing."""

from __future__ import annotations

import contextlib
import json
import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.fleet_comms.authority import AuthorityService
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


def test_wake_owner_reads_delivery_after_path_unlinked(tmp_path: Path) -> None:
    """The watcher writes to an open file after a sibling removes its name."""
    lib = tmp_path / "scripts/lib"
    lib.mkdir(parents=True)
    (lib / "session_supervisor.sh").write_text((_REPO_ROOT / "scripts/lib/session_supervisor.sh").read_text())
    watcher = tmp_path / "scripts/ai_agent_bridge/inbox_watch.sh"
    watcher.parent.mkdir()
    _write_executable(watcher, '#!/usr/bin/env bash\nread -r _ < "$TEST_GATE"\nprintf "delivery-test\\n"\nexit 75\n')
    script = f"""
set -euo pipefail
source {shlex.quote(str(lib / "session_supervisor.sh"))}
LC_PROVIDER=codex
export TEST_GATE={shlex.quote(str(tmp_path / "gate"))}
mkfifo "$TEST_GATE"
session_supervisor_start_inbox_watch
rm -f "$LC_SUPERVISORY_WAKE_FILE"
[ ! -e "$LC_SUPERVISORY_WAKE_FILE" ]
printf 'go\\n' > "$TEST_GATE"
session_supervisor_read_wake
printf 'DELIVERY:%s\\n' "$LC_SUPERVISORY_DELIVERY"
# Cleanup cannot own a sibling's replacement at the unlinked name.
printf 'replacement\\n' > "$LC_SUPERVISORY_WAKE_FILE"
replacement="$LC_SUPERVISORY_WAKE_FILE"
session_supervisor_stop_inbox_watch
[ "$(cat "$replacement")" = replacement ]
rm -f "$replacement"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        env={**_clean_environ(), "FLEET_COMMS_ROOT": str(tmp_path / "plane")},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "DELIVERY:delivery-test\n"


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

    # session_supervisor.sh resolves its state root through project_interpreter.sh (#9121).
    for name in ("session_supervisor.sh", "project_interpreter.sh"):
        (lib_dir / name).write_text(
            (_REPO_ROOT / "scripts" / "lib" / name).read_text(encoding="utf-8"),
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


def _live_session_fake_python(capture: Path, counter: Path) -> str:
    ok = (
        '{"schema":"session-supervisor-bootstrap.v1","identity":{"role":"driver",'
        '"stream_id":"epic:9999","lease":{"session_id":"sess-shell-790",'
        '"lease_id":"lease-shell-790","generation":4,"fencing_token":4,'
        '"expires_at":"2026-07-21T03:00:00Z"}},"rollover":null,"digest":{},'
        '"dual_write":{},"diagnostics":{}}'
    )
    return f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.api.occupancy_local" && "${{3:-}}" == "resolve-host-id" ]]; then
  printf '%s\\n' "host-job"
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" ]]; then
  printf '%s\\n' "CMD:$3" >> "{capture}"
  printf '%s\\n' -- "$@" >> "{capture}"
  printf '%s\\n' "---" >> "{capture}"
  if [[ "$3" == "release" ]]; then
    printf '%s\\n' '{{"outcome":"force_released"}}'
    exit 0
  fi
  if [[ "$3" == "open" ]]; then
    count=0
    if [[ -f "{counter}" ]]; then
      count=$(cat "{counter}")
    fi
    count=$((count + 1))
    printf '%s' "$count" > "{counter}"
    if [[ "$count" -eq 1 ]]; then
      echo "stream epic:9999 already has live session sess-held (open)" >&2
      exit 1
    fi
    printf '%s\\n' '{ok}'
    exit 0
  fi
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


def test_claim_without_force_prints_monitor_expiry_hint(tmp_path: Path) -> None:
    project, _capture = _build_fake_project(tmp_path)
    capture = tmp_path / "live_capture.txt"
    counter = tmp_path / "open_count.txt"
    _write_executable(project / ".venv" / "bin" / "python", _live_session_fake_python(capture, counter))
    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "test-task" "test-instance" "{project}" "start-grok-driver.sh" "infra"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=_clean_environ(),
    )
    assert result.returncode == 1, result.stderr + result.stdout
    assert "already has live session" in result.stderr
    assert "handoff-status --stream epic:9999" in result.stderr
    assert "retry the Monitor claim after expiry" in result.stderr
    assert "--force" not in result.stderr
    log = capture.read_text(encoding="utf-8")
    assert "CMD:release" not in log
    assert log.count("CMD:open") == 1


def test_claim_with_force_releases_then_opens(tmp_path: Path) -> None:
    project, _capture = _build_fake_project(tmp_path)
    capture = tmp_path / "force_capture.txt"
    counter = tmp_path / "open_count.txt"
    _write_executable(project / ".venv" / "bin" / "python", _live_session_fake_python(capture, counter))
    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
LC_DRIVER_FORCE=1
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "test-task" "test-instance" "{project}" "start-grok-driver.sh" "infra"
printf 'SESSION=%s\\n' "$SESSION_STREAM_SESSION_ID"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=_clean_environ(),
    )
    assert result.returncode == 0, result.stderr + result.stdout + "\n" + capture.read_text(encoding="utf-8")
    assert "SESSION=sess-shell-790" in result.stdout
    assert "attributed --force release" in result.stderr
    log = capture.read_text(encoding="utf-8")
    assert log.count("CMD:open") == 2
    assert log.count("CMD:release") == 1
    assert "--reason" in log
    assert "operator force takeover via start-grok-driver.sh (#8229)" in log
    assert "--actor-agent" in log
    assert "test-agent" in log


def test_claim_force_is_ignored_on_supervisory_wake(tmp_path: Path) -> None:
    project, _capture = _build_fake_project(tmp_path)
    capture = tmp_path / "wake_capture.txt"
    counter = tmp_path / "open_count.txt"
    _write_executable(project / ".venv" / "bin" / "python", _live_session_fake_python(capture, counter))
    watch_dir = project / "scripts" / "ai_agent_bridge"
    watch_dir.mkdir(parents=True)
    _write_executable(
        watch_dir / "inbox_watch.sh",
        '#!/usr/bin/env bash\nprintf \'%s\\n\' \'{"session_id":"sess-wake","generation":4}\'\n',
    )
    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
LC_DRIVER_FORCE=1
SESSION_SUPERVISOR_WAKE_DELIVERY=delivery-wake-1
SESSION_SUPERVISOR_WAKE_STREAM=epic:9999
claim_session_supervisor_env "epic:9999" "test-agent" "test-harness" "test-task" "test-instance" "{project}" "start-grok-driver.sh" "infra"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=_clean_environ(),
    )
    assert result.returncode == 1, result.stderr + result.stdout
    assert "already has live session" in result.stderr
    assert "supervisory successor launches cannot --force" in result.stderr
    log = capture.read_text(encoding="utf-8")
    assert "CMD:release" not in log
    assert log.count("CMD:open") == 1


def test_launcher_drops_force_from_successor_args() -> None:
    script = f"""
set -euo pipefail
source "{_REPO_ROOT}/scripts/lib/launcher_core.sh"
LC_DRIVER_ORIGINAL_ARGS=(--epic infra --force --model grok-4.7 -- --force)
launcher_drop_force_from_successor_args
printf 'COUNT=%s\\n' "${{#LC_DRIVER_ORIGINAL_ARGS[@]}}"
printf 'ARGS=%s\\n' "${{LC_DRIVER_ORIGINAL_ARGS[*]}}"
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
    assert "COUNT=6" in result.stdout
    assert "ARGS=--epic infra --model grok-4.7 -- --force" in result.stdout


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
    tmp_path: Path,
    scenario: str,
    *,
    widen_wait_window: bool = False,
    timeout: int = 45,
    extra_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], list[str], float]:
    import shlex
    import sys
    import time

    root = tmp_path / scenario
    lib = root / "scripts" / "lib"
    lib.mkdir(parents=True)
    for name in ("launcher_core.sh", "session_supervisor.sh"):
        body = (_REPO_ROOT / "scripts" / "lib" / name).read_text()
        if scenario == "wake_file_missing" and name == "session_supervisor.sh":
            body = body.replace("session_supervisor_read_wake()", "session_supervisor_read_wake_original()")
        (lib / name).write_text(body)
    watcher = root / "scripts" / "ai_agent_bridge" / "inbox_watch.sh"
    watcher.parent.mkdir()
    log = root / "events"
    provider_pid = root / "provider-pid"
    wait_window = root / "wait-window"
    _write_executable(
        watcher,
        f"""#!/usr/bin/env bash
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
""",
    )
    provider = root / "provider.py"
    provider.write_text(f"""import os, signal, time
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
""")
    successor = root / "start-codex-driver.sh"
    _write_executable(
        successor,
        f"""#!/usr/bin/env bash
[ "$SESSION_SUPERVISOR_WAKE_DELIVERY" = delivery-test ] || exit 41
[ "$SESSION_SUPERVISOR_WAKE_STREAM" = epic:9999 ] || exit 42
[ -z "${{SESSION_STREAM_LEASE_ID:-}}" ] || exit 43
[ "$#" = 2 ] && [ "$1" = '--fixture' ] && [ "$2" = 'two words' ] || exit 44
printf 'successor\\n' >> {shlex.quote(str(log))}
""",
    )
    script = f"""
set -euo pipefail
source {shlex.quote(str(lib / "launcher_core.sh"))}
source {shlex.quote(str(lib / "session_supervisor.sh"))}
LC_ROOT={shlex.quote(str(root))}
LC_MODE=driver LC_PROVIDER=codex LC_DRIVER_LEASE_CLAIMED=1 LC_DRY_RUN=0
LC_DRIVER_ORIGINAL_ARGS=(--fixture 'two words')
export SESSION_STREAM_ID=epic:9999 SESSION_STREAM_LEASE_ID=lease-test SESSION_STREAM_GENERATION=30
launcher_driver_renew_loop() {{ :; }}
launcher_cursor_observer_renew_loop() {{ :; }}
if [ '{widen_wait_window}' = True ]; then
  launcher_driver_wait_hook() {{ touch {shlex.quote(str(wait_window))}; sleep 0.3 || true; }}
fi
if [ '{scenario}' = wake_file_missing ]; then
  session_supervisor_read_wake() {{ exec 216<&-; session_supervisor_read_wake_original; }}
fi
launcher_close_driver_lease() {{
  if kill -0 "$(cat {shlex.quote(str(provider_pid))})" 2>/dev/null; then return 45; fi
  printf 'close\\n' >> {shlex.quote(str(log))}
  [ '{scenario}' != close_failure ] || return 1
  LC_DRIVER_LEASE_CLOSED=1
}}
launcher_exec_command {shlex.quote(sys.executable)} {shlex.quote(str(provider))}
"""
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
        env={**_clean_environ(), "FLEET_COMMS_ROOT": str(root / "fleet-plane"), **(extra_env or {})},
    ) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            raise subprocess.TimeoutExpired(process.args, timeout, output=stdout, stderr=stderr) from None
    result = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    return result, log.read_text().splitlines(), time.monotonic() - started


def _failure_publication_fixture(tmp_path: Path, *, seed_channel: bool) -> dict[str, str]:
    """Real Fleet CLI in a test-owned plane; the interpreter records its argv."""
    root = tmp_path / "failure-helper"
    bindir = root / ".venv/bin"
    bindir.mkdir(parents=True)
    plane = tmp_path / "failure-plane"
    with AuthorityService(root=plane) as service:
        if seed_channel:
            service.create_channel("cto")
    _write_executable(
        bindir / "python",
        f"""#!/usr/bin/env bash
if [ "$1" = -m ]; then
  printf '%s\\n' "$*" >> "$TEST_PUBLISH_ARGS"
  [ "$2" = scripts.fleet_comms ] || exit 91
  if [ -n "${{TEST_CLOSE_EVENTS:-}}" ]; then
    [ "$(tail -n 1 "$TEST_CLOSE_EVENTS")" = close ] || exit 92
  fi
fi
cd {shlex.quote(str(_REPO_ROOT))} || exit 93
exec {shlex.quote(sys.executable)} "$@"
""",
    )
    return {
        "LC_DURABLE_HELPER_ROOT": str(root),
        "FLEET_COMMS_ROOT": str(plane),
        "SESSION_HANDOFF_AGENT": "fixture-driver",
        "TEST_PUBLISH_ARGS": str(tmp_path / "publish-args"),
    }


def _assert_failure_publication(env: dict[str, str], reason: str, *, published: bool) -> None:
    """Assert exact body, identity, key and one attempt, including failed sends."""
    calls = Path(env["TEST_PUBLISH_ARGS"]).read_text().splitlines()
    assert calls == [
        "-m scripts.fleet_comms channel publish cto - --sender fixture-driver --kind status "
        f"--idempotency-key epic:9999-30-{reason}"
    ]
    with AuthorityService(root=Path(env["FLEET_COMMS_ROOT"])) as service:
        rows = service.store.connection.execute("SELECT message_id FROM comms_messages").fetchall()
        assert len(rows) == int(published)
        if published:
            message = service.get_message(rows[0][0])
            assert message.sender == "fixture-driver" and message.kind == "status"
            assert json.loads(service.read_message_body(message.message_id)) == {
                "stream": "epic:9999",
                "generation": 30,
                "reason": reason,
            }
        else:
            assert service.store.connection.execute("SELECT COUNT(*) FROM authority_channels").fetchone()[0] == 0


@pytest.mark.parametrize(
    "reason,scenario",
    [
        ("wake-file-missing", "wake_file_missing"),
        ("watcher-failed", "watcher_failure"),
    ],
)
@pytest.mark.parametrize("publish_ok", [True, False])
def test_failed_wake_publishes_after_close_and_preserves_exit(
    tmp_path: Path,
    reason: str,
    scenario: str,
    publish_ok: bool,
) -> None:
    env = _failure_publication_fixture(tmp_path, seed_channel=publish_ok)
    env["TEST_CLOSE_EVENTS"] = str(tmp_path / scenario / "events")
    result, events, _ = _run_launcher_wake_scenario(tmp_path, scenario, extra_env=env)
    assert result.returncode == 1, result.stderr
    assert events == ["stopped", "close"]
    _assert_failure_publication(env, reason, published=publish_ok)


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
