"""start-claude.sh PR-J2: supervisor claim on --epic (isolated tmp project)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-claude.sh"
_GIT_REDIRECT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    }
)


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT}


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


@pytest.mark.parametrize(
    ("selector", "canonical_lane", "stream", "handoff"),
    [
        ("harness", "harness", "epic:4707", "claude-infra"),
        ("practice-hub", "atlas", "epic:4387", "claude-atlas"),
        ("seminars-folk", "folk", "epic:2836", "claude-folk"),
        ("seminars-bio", "bio", "epic:4431", "claude-bio"),
    ],
)
def test_epic_selector_claims_supervisor_and_strips_flag(
    tmp_path: Path, selector: str, canonical_lane: str, stream: str, handoff: str
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    lib = project / "scripts" / "lib"
    lib.mkdir(parents=True)
    venv_bin = project / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    home = tmp_path / "home"
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    capture = tmp_path / "claude_capture.txt"
    supervisor_capture = tmp_path / "supervisor_capture.txt"

    _write_executable(project / "start-claude.sh", _LAUNCHER.read_text(encoding="utf-8"))
    for name in ("handoff_identity.sh", "session_supervisor.sh"):
        (lib / name).write_text(
            (_REPO_ROOT / "scripts" / "lib" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (lib / "deploy_extensions.sh").write_text(
        "deploy_agent_extensions() { return 0; }\n",
        encoding="utf-8",
    )
    (lib / "profile_resolver.sh").write_text(
        "resolve_context_profile() {\n"
        "  export LEARN_UKRAINIAN_PROFILE_ID=test\n"
        "  export LEARN_UKRAINIAN_MAIN_MODEL_ID=m\n"
        "  export LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS=1\n"
        "  export LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS=1\n"
        "  export LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS=1\n"
        "  export LEARN_UKRAINIAN_RESOLUTION_REASON=test\n"
        "}\n",
        encoding="utf-8",
    )

    _write_executable(
        venv_bin / "python",
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" && "${{3:-}}" == "open" ]]; then
  printf '%s\\n' "$@" > "{supervisor_capture}"
  cat <<'JSON'
{{
  "schema": "session-supervisor-bootstrap.v1",
  "identity": {{
    "role": "driver",
    "stream_id": "{stream}",
    "lease": {{
      "session_id": "sess-claude-j2",
      "lease_id": "lease-claude-j2",
      "generation": 1,
      "fencing_token": 1,
      "expires_at": "2026-07-21T12:00:00Z"
    }},
    "lease_credentials_exported": false
  }},
  "rollover": null,
  "digest": {{}},
  "dual_write": {{}},
  "diagnostics": {{}}
}}
JSON
  exit 0
fi
if [[ "${{1:-}}" == "-" ]]; then
  shift
  exec /usr/bin/env python3 - "$@"
fi
if [[ "${{1:-}}" == "-c" ]]; then
  shift
  exec /usr/bin/env python3 -c "$@"
fi
echo "unexpected python: $*" >&2
exit 1
""",
    )

    _write_executable(
        bin_dir / "claude",
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "--version" ]]; then
  echo "test-claude"
  exit 0
fi
{{
  printf 'epic=%s\\n' "${{SESSION_EPIC-unset}}"
  printf 'stream=%s\\n' "${{SESSION_STREAM_ID-unset}}"
  printf 'session=%s\\n' "${{SESSION_STREAM_SESSION_ID-unset}}"
  printf 'lease=%s\\n' "${{SESSION_STREAM_LEASE_ID-unset}}"
  printf 'handoff=%s\\n' "${{SESSION_HANDOFF_AGENT-unset}}"
  printf 'argv='
  printf '%s\\0' "$@"
  printf '\\n'
}} > "{capture}"
""",
    )

    env = _clean_env()
    for name in list(env):
        if name.startswith("SESSION_") or name.startswith("LEARN_UKRAINIAN_"):
            env.pop(name, None)
    env["HOME"] = str(home)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

    subprocess.run(["git", "init", "--quiet", str(project)], check=True, env=env)
    subprocess.run(
        ["git", "-C", str(project), "config", "user.email", "t@example.com"],
        check=True,
        env=env,
    )
    subprocess.run(
        ["git", "-C", str(project), "config", "user.name", "t"],
        check=True,
        env=env,
    )
    (project / "README.md").write_text("t\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(project), "add", "."], check=True, env=env)
    subprocess.run(
        ["git", "-C", str(project), "commit", "--quiet", "-m", "init"],
        check=True,
        env=env,
    )
    subprocess.run(["git", "-C", str(project), "branch", "-M", "main"], check=True, env=env)

    result = subprocess.run(
        [str(project / "start-claude.sh"), "--epic", selector],
        cwd=project,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert supervisor_capture.exists(), result.stderr + result.stdout
    sup = supervisor_capture.read_text(encoding="utf-8")
    assert "scripts.session_supervisor" in sup
    assert "open" in sup
    assert "claude" in sup
    assert "claude-code" in sup
    assert stream in sup

    raw = capture.read_text(encoding="utf-8")
    assert f"epic={canonical_lane}" in raw
    assert f"stream={stream}" in raw
    assert "session=sess-claude-j2" in raw
    assert "lease=lease-claude-j2" in raw
    assert f"handoff={handoff}" in raw
    assert "--epic" not in raw.split("argv=", 1)[-1]
