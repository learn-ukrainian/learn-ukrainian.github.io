"""start-grok.sh launcher: --epic env export + supervisor claim + cold-start prompt."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-grok.sh"

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


def _supervisor_body(capture: Path, stream_id: str, session_id: str, lease_id: str) -> str:
    return f"""#!/usr/bin/env bash
if [[ "$1" == *"assert_primary_on_main.py" ]]; then
  exit 0
fi
if [[ "$1" == *"check_core_bare.py" ]]; then
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
    "stream_id": "{stream_id}",
    "lease": {{
      "session_id": "{session_id}",
      "lease_id": "{lease_id}",
      "generation": 1,
      "fencing_token": 1,
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
    """Create a self-contained fake project root with launcher, helpers, and fake python."""
    project = tmp_path / "project"
    project.mkdir()
    venv_bin = project / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    lib_dir = project / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    guard_dir = project / "scripts" / "guardrails"
    guard_dir.mkdir(parents=True)

    # Copy launcher and shell helpers so PROJECT_DIR resolution stays inside the fake root.
    _write_executable(project / "start-grok.sh", _LAUNCHER.read_text(encoding="utf-8"))
    (lib_dir / "session_supervisor.sh").write_text(
        (_REPO_ROOT / "scripts" / "lib" / "session_supervisor.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (lib_dir / "handoff_identity.sh").write_text(
        (_REPO_ROOT / "scripts" / "lib" / "handoff_identity.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (guard_dir / "assert_primary_on_main.py").write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n")
    (guard_dir / "assert_primary_on_main.py").chmod(0o755)
    audit_dir = project / "scripts" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "check_core_bare.py").write_text(
        "#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8"
    )

    capture = tmp_path / "supervisor_capture.txt"
    _write_executable(
        venv_bin / "python",
        _supervisor_body(capture, "epic:4387", "sess-grok-123", "lease-grok-123"),
    )

    # Git repo so session_supervisor.sh can resolve a canonical state root.
    env = _clean_environ()
    subprocess.run(["git", "init", "--quiet", str(project)], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "config", "user.email", "test@example.com"], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True, env=env)
    (project / "README.md").write_text("# test", encoding="utf-8")
    subprocess.run(["git", "-C", str(project), "add", "."], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "commit", "--quiet", "-m", "init"], check=True, env=env)
    subprocess.run(["git", "-C", str(project), "branch", "-m", "main"], check=True, env=env)

    return project, capture


def _run_launcher(
    tmp_path: Path,
    arguments: list[str],
) -> tuple[dict[str, str], str, subprocess.CompletedProcess[str], Path, Path]:
    """Run start-grok.sh with a fake grok binary that captures env + argv."""
    project, supervisor_capture = _build_fake_project(tmp_path)
    home = tmp_path / "home"
    grok_bin_dir = home / ".grok" / "bin"
    grok_bin_dir.mkdir(parents=True)
    capture = tmp_path / "capture.txt"

    _write_executable(
        grok_bin_dir / "grok",
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "--version" ]]; then
  echo "test-grok 0.0.0"
  exit 0
fi
{{
  printf 'session_epic=%s\\n' "${{SESSION_EPIC-unset}}"
  printf 'session_stream=%s\\n' "${{SESSION_STREAM_ID-unset}}"
  printf 'session_session=%s\\n' "${{SESSION_STREAM_SESSION_ID-unset}}"
  printf 'session_lease=%s\\n' "${{SESSION_STREAM_LEASE_ID-unset}}"
  printf 'session_agent=%s\\n' "${{SESSION_STREAM_AGENT-unset}}"
  printf 'session_harness=%s\\n' "${{SESSION_STREAM_HARNESS-unset}}"
  printf 'session_instance=%s\\n' "${{SESSION_STREAM_INSTANCE_ID-unset}}"
  printf 'session_process=%s\\n' "${{SESSION_STREAM_PROCESS_ID-unset}}"
  printf 'handoff=%s\\n' "${{SESSION_HANDOFF_AGENT-unset}}"
  printf 'launch=%s\\n' "${{LEARN_UKRAINIAN_GROK_LAUNCH-unset}}"
  printf 'capsule=%s\\n' "${{SESSION_SUPERVISOR_CAPSULE_PATH-unset}}"
  printf 'plane_mode=%s\\n' "${{FLEET_COMMS_PLANE_MODE-unset}}"
  printf 'argv='
  printf '%s\\0' "$@"
  printf '\\n'
}} > "{capture}"
""",
    )

    env = _clean_environ()
    for name in (
        "SESSION_EPIC",
        "SESSION_STREAM_ID",
        "SESSION_STREAM_SESSION_ID",
        "SESSION_STREAM_LEASE_ID",
        "SESSION_STREAM_AGENT",
        "SESSION_STREAM_HARNESS",
        "SESSION_STREAM_INSTANCE_ID",
        "SESSION_STREAM_PROCESS_ID",
        "SESSION_HANDOFF_AGENT",
        "LEARN_UKRAINIAN_GROK_LAUNCH",
        "SESSION_SUPERVISOR_CAPSULE_PATH",
        "FLEET_COMMS_PLANE_MODE",
        "FLEET_COMMS_MESSAGE_PLANE",
    ):
        env.pop(name, None)
    env["HOME"] = os.fspath(home)
    env["PATH"] = f"{grok_bin_dir}:{env.get('PATH', '')}"

    result = subprocess.run(
        [os.fspath(project / "start-grok.sh"), *arguments],
        cwd=project,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    raw = capture.read_text(encoding="utf-8") if capture.exists() else ""
    values: dict[str, str] = {}
    argv_blob = ""
    for line in raw.splitlines():
        if line.startswith("argv="):
            argv_blob = line[len("argv=") :]
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            values[k] = v
    return values, argv_blob, result, project, supervisor_capture


def test_epic_atlas_exports_env_and_claims_lease(tmp_path: Path) -> None:
    values, argv_blob, result, _project, supervisor_capture = _run_launcher(tmp_path, ["--epic", "atlas"])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "atlas"
    assert values["session_stream"] == "epic:4387"
    assert values["session_session"] == "sess-grok-123"
    assert values["session_lease"] == "lease-grok-123"
    assert values["session_agent"] == "grok"
    assert values["session_harness"] == "grok-tui"
    assert values["session_instance"].startswith("grok-")
    assert values["session_process"].isdigit()
    assert values["handoff"] == "grok-atlas"
    assert values["launch"] == "1"
    assert values["capsule"] != "unset"
    assert Path(values["capsule"]).exists()
    # Mid-cutover fail-open: plane mode resolves to off when fleet_comms is absent.
    assert values["plane_mode"] == "off"

    # Supervisor was invoked for the expected stream/agent/harness.
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert "scripts.session_supervisor" in supervisor_args
    assert "open" in supervisor_args
    assert "--role" in supervisor_args and "driver" in supervisor_args
    assert "--stream" in supervisor_args and "epic:4387" in supervisor_args
    assert "--agent" in supervisor_args and "grok" in supervisor_args
    assert "--harness" in supervisor_args and "grok-tui" in supervisor_args
    assert "--task-id" in supervisor_args

    # Compact banner: no multi-line folklore dump; dual-aware fleet-comms line present.
    out = result.stdout + result.stderr
    assert "Starting Grok in Learn Ukrainian project..." not in out
    assert "Launching Grok Build TUI..." not in out
    assert "plane=off" in out
    assert "fleet-comms" in out.lower()
    assert "review-pr" in out

    # Null-separated argv from fake grok; last non-empty token is the prompt.
    parts = [p for p in argv_blob.split("\0") if p]
    assert parts, "expected grok argv"
    prompt = parts[-1]
    assert "ATLAS" in prompt or "atlas" in prompt.lower()
    assert "TAKEOVER-PROMPT.md" in prompt
    assert "epic:4387" in prompt
    assert "open/resume lease" not in prompt.lower()
    assert "do NOT open or resume it yourself" in prompt
    # Dual-aware: plane + CF surfaces preferred; file dual-write is fallback.
    assert "Fleet-comms" in prompt or "fleet-comms" in prompt.lower() or "#5512" in prompt
    assert "plane-status" in prompt
    assert "review-pr" in prompt
    assert "publish-review-verdict" in prompt
    assert "dual-write" in prompt.lower() or "dual write" in prompt.lower()
    assert "--model" in parts
    assert "grok-4.5" in parts
    assert "--always-approve" in parts


def test_epic_equals_form_and_explicit_prompt_skips_inject(tmp_path: Path) -> None:
    values, argv_blob, result, _project, _supervisor_capture = _run_launcher(
        tmp_path,
        ["--epic=atlas", "only do the cloze batch"],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "atlas"
    parts = [p for p in argv_blob.split("\0") if p]
    # Grok launcher keeps the single explicit prompt as argv[-1].
    assert parts[-1] == "only do the cloze batch"
    assert "TAKEOVER-PROMPT.md" not in parts[-1]


def test_no_epic_no_supervisor_call(tmp_path: Path) -> None:
    values, argv_blob, result, _project, supervisor_capture = _run_launcher(tmp_path, [])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "unset"
    assert values["session_stream"] == "unset"
    assert not supervisor_capture.exists()
    parts = [p for p in argv_blob.split("\0") if p]
    # Flags only — no free-text cold-start prompt.
    assert all(p.startswith("-") or p in {"grok-4.5", "high"} or Path(p).is_absolute() for p in parts)


def test_stream_override_is_used_by_supervisor(tmp_path: Path) -> None:
    _values, _argv_blob, result, _project, supervisor_capture = _run_launcher(
        tmp_path,
        ["--epic", "atlas", "--stream", "epic:4707"],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    stream_index = supervisor_args.index("--stream")
    assert supervisor_args[stream_index + 1] == "epic:4707"


def test_epic_harness_cold_prompt_is_fleet_comms_dual_aware(tmp_path: Path) -> None:
    values, argv_blob, result, _project, _supervisor_capture = _run_launcher(
        tmp_path,
        ["--epic", "harness"],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "harness"
    assert values["handoff"] == "grok-infra"
    assert values["plane_mode"] == "off"
    parts = [p for p in argv_blob.split("\0") if p]
    prompt = parts[-1]
    assert "INFRA" in prompt or "harness" in prompt.lower()
    assert "do NOT open or resume it yourself" in prompt
    assert "plane-status" in prompt
    assert "review-pr" in prompt
    assert "publish-review-verdict" in prompt
    assert "session_canary.grok_lane mint --epic harness" in prompt
    # File dual-write remains the mid-cutover fallback, not the only coordination path.
    assert "DRIVER-HANDOFF" in prompt or "dual-write" in prompt.lower()
    out = result.stdout
    assert "Starting Grok in Learn Ukrainian project..." not in out
    assert "plane=off" in out
