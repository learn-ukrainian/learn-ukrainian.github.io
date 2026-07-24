"""start-gemini.sh launcher: --epic env export + supervisor claim + cold-start prompt."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-gemini.sh"

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

    _write_executable(project / "start-gemini.sh", _LAUNCHER.read_text(encoding="utf-8"))
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
        _supervisor_body(capture, "epic:4387", "sess-gemini-123", "lease-gemini-123"),
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
    """Run start-gemini.sh with a fake agy binary that captures env + argv."""
    project, supervisor_capture = _build_fake_project(tmp_path)
    home = tmp_path / "home"
    agy_bin_dir = home / ".local" / "bin"
    agy_bin_dir.mkdir(parents=True)
    capture = tmp_path / "capture.txt"

    _write_executable(
        agy_bin_dir / "agy",
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "--version" ]]; then
  echo "test-agy 1.1.5"
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
  printf 'launch=%s\\n' "${{LEARN_UKRAINIAN_AGY_LAUNCH-unset}}"
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
        "LEARN_UKRAINIAN_AGY_LAUNCH",
        "SESSION_SUPERVISOR_CAPSULE_PATH",
    ):
        env.pop(name, None)
    env["HOME"] = os.fspath(home)
    env["PATH"] = f"{agy_bin_dir}:{env.get('PATH', '')}"

    result = subprocess.run(
        [os.fspath(project / "start-gemini.sh"), *arguments],
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
    assert values["session_session"] == "sess-gemini-123"
    assert values["session_lease"] == "lease-gemini-123"
    assert values["session_agent"] == "gemini"
    assert values["session_harness"] == "agy"
    assert values["session_instance"].startswith("gemini-")
    assert values["session_process"].isdigit()
    assert values["handoff"] == "gemini-atlas"
    assert values["launch"] == "1"
    assert values["capsule"] != "unset"
    assert Path(values["capsule"]).exists()

    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert "scripts.session_supervisor" in supervisor_args
    assert "open" in supervisor_args
    assert "--role" in supervisor_args and "driver" in supervisor_args
    assert "--stream" in supervisor_args and "epic:4387" in supervisor_args
    assert "--agent" in supervisor_args and "gemini" in supervisor_args
    assert "--harness" in supervisor_args and "agy" in supervisor_args
    assert "--task-id" in supervisor_args

    parts = [p for p in argv_blob.split("\0") if p]
    assert parts, "expected agy argv"
    assert "-i" in parts
    i_idx = parts.index("-i")
    prompt = parts[i_idx + 1]
    assert "Gemini" in prompt and "orchestrator" in prompt
    assert ".agent/gemini-atlas-thread-handoff.md" in prompt
    assert "codexbar usage" in prompt
    assert "--model" in parts
    assert "gemini-3.6-flash-high" in parts
    assert "--dangerously-skip-permissions" in parts


@pytest.mark.parametrize("arguments", [["--epic", "atlas.epic"], ["--epic=atlas.epic"]])
def test_legacy_epic_suffix_normalizes_to_atlas(tmp_path: Path, arguments: list[str]) -> None:
    values, _argv_blob, result, _project, supervisor_capture = _run_launcher(tmp_path, arguments)
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "atlas"
    assert values["session_stream"] == "epic:4387"
    assert values["handoff"] == "gemini-atlas"
    assert supervisor_capture.exists()


@pytest.mark.parametrize(
    ("selector", "canonical_lane", "stream", "handoff"),
    [
        ("devops", "devops", "epic:5703", "gemini-devops"),
        ("practice-hub", "atlas", "epic:4387", "gemini-atlas"),
        ("seminars-folk", "folk", "epic:2836", "gemini-folk"),
        ("seminars-bio", "bio", "epic:4431", "gemini-bio"),
        ("corpus-channels", "corpus", "epic:4706", "gemini-corpus"),
    ],
)
def test_alias_normalizes_to_canonical_lane(
    tmp_path: Path, selector: str, canonical_lane: str, stream: str, handoff: str
) -> None:
    values, _argv_blob, result, _project, supervisor_capture = _run_launcher(tmp_path, ["--epic", selector])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == canonical_lane
    assert values["session_stream"] == stream
    assert values["handoff"] == handoff
    assert supervisor_capture.exists()
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    stream_index = supervisor_args.index("--stream")
    assert supervisor_args[stream_index + 1] == stream


def test_epic_harness_derives_gemini_infra_handoff(tmp_path: Path) -> None:
    values, argv_blob, result, _project, _supervisor_capture = _run_launcher(tmp_path, ["--epic", "harness"])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "harness"
    assert values["handoff"] == "gemini-infra"
    parts = [p for p in argv_blob.split("\0") if p]
    i_idx = parts.index("-i")
    prompt = parts[i_idx + 1]
    assert ".agent/gemini-infra-thread-handoff.md" in prompt


def test_dot_notation_infra_devops_uses_canonical_stream_and_handoff(tmp_path: Path) -> None:
    values, _argv_blob, result, _project, supervisor_capture = _run_launcher(
        tmp_path, ["--epic", "infra.devops"]
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "devops"
    assert values["handoff"] == "gemini-devops"
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    stream_index = supervisor_args.index("--stream")
    assert supervisor_args[stream_index + 1] == "epic:5703"


def test_unknown_epic_selector_fails_closed_with_help(tmp_path: Path) -> None:
    _values, _argv_blob, result, _project, supervisor_capture = _run_launcher(
        tmp_path, ["--epic", "unknown"]
    )
    assert result.returncode == 1
    assert not supervisor_capture.exists()
    assert "unknown lane selector 'unknown'" in result.stderr
    assert "Valid lane selectors:" in result.stderr


def test_epic_equals_form_and_explicit_prompt_uses_interactive_prompt(tmp_path: Path) -> None:
    values, argv_blob, result, _project, _supervisor_capture = _run_launcher(
        tmp_path,
        ["--epic=atlas", "only check issue streams"],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "atlas"
    parts = [p for p in argv_blob.split("\0") if p]
    assert "-i" in parts
    i_idx = parts.index("-i")
    assert parts[i_idx + 1] == "only check issue streams"


def test_no_epic_no_supervisor_call(tmp_path: Path) -> None:
    values, argv_blob, result, _project, supervisor_capture = _run_launcher(tmp_path, [])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "unset"
    assert values["session_stream"] == "unset"
    assert not supervisor_capture.exists()
    parts = [p for p in argv_blob.split("\0") if p]
    assert "--model" in parts
    assert "gemini-3.6-flash-high" in parts


def test_stream_override_is_used_by_supervisor(tmp_path: Path) -> None:
    _values, _argv_blob, result, _project, supervisor_capture = _run_launcher(
        tmp_path,
        ["--epic", "atlas", "--stream", "epic:4707"],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    stream_index = supervisor_args.index("--stream")
    assert supervisor_args[stream_index + 1] == "epic:4707"
