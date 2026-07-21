"""start-kimi.sh launcher: --epic env export + supervisor claim + launch argv."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-kimi.sh"

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
      "generation": 2,
      "fencing_token": 2,
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

    _write_executable(project / "start-kimi.sh", _LAUNCHER.read_text(encoding="utf-8"))
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

    capture = tmp_path / "supervisor_capture.txt"
    _write_executable(
        venv_bin / "python",
        _supervisor_body(capture, "epic:4707", "sess-kimi-456", "lease-kimi-456"),
    )

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
    """Run start-kimi.sh with a fake kimi binary that captures env + argv."""
    project, supervisor_capture = _build_fake_project(tmp_path)
    home = tmp_path / "home"
    kimi_bin_dir = home / ".kimi-code" / "bin"
    kimi_bin_dir.mkdir(parents=True)
    capture = tmp_path / "capture.txt"

    _write_executable(
        kimi_bin_dir / "kimi",
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "--version" ]]; then
  echo "test-kimi 0.0.0"
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
  printf 'launch=%s\\n' "${{LEARN_UKRAINIAN_KIMI_LAUNCH-unset}}"
  printf 'capsule=%s\\n' "${{SESSION_SUPERVISOR_CAPSULE_PATH-unset}}"
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
        "LEARN_UKRAINIAN_KIMI_LAUNCH",
        "SESSION_SUPERVISOR_CAPSULE_PATH",
    ):
        env.pop(name, None)
    env["HOME"] = os.fspath(home)
    env["PATH"] = f"{kimi_bin_dir}:{env.get('PATH', '')}"

    result = subprocess.run(
        [os.fspath(project / "start-kimi.sh"), *arguments],
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


def test_epic_harness_exports_env_and_claims_lease(tmp_path: Path) -> None:
    values, argv_blob, result, _project, supervisor_capture = _run_launcher(
        tmp_path, ["--epic", "harness"]
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "harness"
    assert values["session_stream"] == "epic:4707"
    assert values["session_session"] == "sess-kimi-456"
    assert values["session_lease"] == "lease-kimi-456"
    assert values["session_agent"] == "kimi"
    assert values["session_harness"] == "kimi-code"
    assert values["session_instance"].startswith("kimi-")
    assert values["session_process"].isdigit()
    assert values["handoff"] == "kimi-infra"
    assert values["launch"] == "1"
    assert values["capsule"] != "unset"
    assert Path(values["capsule"]).exists()

    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert "scripts.session_supervisor" in supervisor_args
    assert "open" in supervisor_args
    assert "--role" in supervisor_args and "driver" in supervisor_args
    stream_index = supervisor_args.index("--stream")
    assert supervisor_args[stream_index + 1] == "epic:4707"
    assert supervisor_args[supervisor_args.index("--agent") + 1] == "kimi"
    assert supervisor_args[supervisor_args.index("--harness") + 1] == "kimi-code"
    assert "--task-id" in supervisor_args

    parts = [p for p in argv_blob.split("\0") if p]
    assert parts[0] == "-p"
    assert "do NOT open or resume it yourself" in parts[1]
    # No --model given: no -m at all (config.toml default_model decides).
    assert "-m" not in parts
    assert "k2.7-coding" not in parts
    # stdout is piped in tests → machine format.
    assert "--output-format" in parts
    assert "stream-json" in parts


def test_explicit_prompt_and_model_override(tmp_path: Path) -> None:
    values, argv_blob, result, _project, _supervisor_capture = _run_launcher(
        tmp_path,
        ["--epic", "atlas", "--model", "k3", "review the open PR"],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "atlas"
    parts = [p for p in argv_blob.split("\0") if p]
    assert parts[0] == "-p"
    assert parts[1] == "review the open PR"
    # Friendly alias maps to the configured config.toml alias.
    assert parts[parts.index("-m") + 1] == "kimi-code/k3"
    assert "k2.7-coding" not in parts


def test_no_epic_no_supervisor_call(tmp_path: Path) -> None:
    values, argv_blob, result, _project, supervisor_capture = _run_launcher(
        tmp_path, ["hello world"]
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "unset"
    assert not supervisor_capture.exists()
    parts = [p for p in argv_blob.split("\0") if p]
    assert parts[0] == "-p"
    assert parts[1] == "hello world"
    assert "-m" not in parts


def test_bare_launch_is_interactive_tui(tmp_path: Path) -> None:
    """No prompt and no --epic: the kimi CLI rejects an empty -p, so the
    launcher must exec the interactive TUI with no prompt/format flags."""
    values, argv_blob, result, _project, supervisor_capture = _run_launcher(tmp_path, [])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "unset"
    assert not supervisor_capture.exists()
    parts = [p for p in argv_blob.split("\0") if p]
    assert parts == []


@pytest.mark.parametrize(
    ("alias", "resolved"),
    [
        ("k2.7", "kimi-code/kimi-for-coding"),
        ("k2.7-coding", "kimi-code/kimi-for-coding"),
        ("kimi-code/kimi-for-coding", "kimi-code/kimi-for-coding"),
        ("k2.7-highspeed", "kimi-code/kimi-for-coding-highspeed"),
        ("k3", "kimi-code/k3"),
        ("kimi-code/k3", "kimi-code/k3"),
    ],
)
def test_model_alias_mapping(tmp_path: Path, alias: str, resolved: str) -> None:
    _values, argv_blob, result, _project, _supervisor_capture = _run_launcher(
        tmp_path, ["--model", alias, "hi"]
    )
    assert result.returncode == 0, result.stderr + result.stdout
    parts = [p for p in argv_blob.split("\0") if p]
    assert parts[parts.index("-m") + 1] == resolved


def test_unknown_model_rejected_before_launch(tmp_path: Path) -> None:
    _values, _argv_blob, result, _project, _supervisor_capture = _run_launcher(
        tmp_path, ["--model", "bogus-9", "hi"]
    )
    assert result.returncode == 1
    assert "unknown --model" in result.stderr
