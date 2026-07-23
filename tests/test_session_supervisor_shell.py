"""scripts/lib/session_supervisor.sh: claim env + capsule writing."""

from __future__ import annotations

import os
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
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" && "${{3:-}}" == "open" ]]; then
  {{
    printf '%s\\n' "$@" > "{capture}"
    cat <<'JSON'
{{
  "schema": "session-supervisor-bootstrap.v1",
  "identity": {{
    "role": "driver",
    "stream_id": "epic:4542",
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
    subprocess.run(["git", "init", "--quiet", str(project)], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "config", "user.email", "test@example.com"], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True, env=env)
    (project / "README.md").write_text("# test", encoding="utf-8")
    subprocess.run(["git", "-C", str(project), "add", "."], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "commit", "--quiet", "-m", "init"], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "branch", "-m", "main"], check=True, env=env)

    return project, capture


def test_claim_exports_all_session_stream_variables_and_writes_capsule(tmp_path: Path) -> None:
    project, supervisor_capture = _build_fake_project(tmp_path)

    script = f"""
set -euo pipefail
source "{project}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env "epic:4542" "test-agent" "test-harness" "test-task" "test-instance" "{project}" "test-launcher.sh" "hramatka"
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
    assert lines["STREAM"] == "epic:4542"
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
    assert '"stream_id": "epic:4542"' in capsule
    assert '"launcher": "test-launcher.sh"' in capsule
    assert '"epic": "hramatka"' in capsule
    assert '"agent": "test-agent"' in capsule
    assert '"harness": "test-harness"' in capsule
    assert '"task_id": "test-task"' in capsule

    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert supervisor_args[supervisor_args.index("--stream") + 1] == "epic:4542"
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
        "SESSION_STREAM_ID": "epic:4542",
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
claim_session_supervisor_env "epic:4542" "test-agent" "test-harness" "" "" "{project}" "test-launcher.sh" "hramatka"
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
claim_session_supervisor_env "epic:4542" "test-agent" "test-harness" "" "" "{project}" "test-launcher.sh" "hramatka" || exit 42
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
claim_session_supervisor_env "epic:4542" "test-agent" "test-harness" "" "" "{project}" "test-launcher.sh" "hramatka" || exit 43
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
