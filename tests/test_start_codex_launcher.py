"""start-codex.sh stream-lease and canary wiring."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"
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
    return {key: value for key, value in os.environ.items() if key not in _GIT_REDIRECT_VARS}


def _write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _build_project(tmp_path: Path) -> tuple[Path, Path, Path]:
    project = tmp_path / "project"
    project.mkdir()
    for relative in (
        "start-codex.sh",
        "scripts/config/context_profiles.yaml",
        "scripts/lib/context_profiles.py",
        "scripts/lib/handoff_identity.sh",
        "scripts/lib/profile_resolver.sh",
        "scripts/lib/session_supervisor.sh",
        "scripts/lib/thread_rollover_link.sh",
        "scripts/orchestration/thread_handoff.py",
        "scripts/session_canary/codex_lane.py",
    ):
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / relative, target)
    _write_executable(
        project / "scripts" / "lib" / "deploy_extensions.sh",
        "#!/usr/bin/env bash\ndeploy_agent_extensions() { return 0; }\n",
    )
    supervisor_capture = tmp_path / "supervisor.txt"
    canary_capture = tmp_path / "canary.txt"
    lease_closed = tmp_path / "lease-closed"
    _write_executable(
        project / ".venv" / "bin" / "python",
        f'''#!/usr/bin/env bash
if [[ "${{1:-}}" == */scripts/orchestration/thread_handoff.py && "$*" == *" detect "* ]]; then
  case "${{CODEX_LAUNCHER_TEST_ROLLOVER:-none}}" in
    none)
      printf '%s\\n' '{{"agent":"codex-infra","status":"none"}}'
      exit 0
      ;;
    pending)
      cat <<'JSON'
{{"agent":"codex-infra","packet_agent":"codex-infra","lineage_id":"lineage-launcher-fresh","rollover_id":"rollover-launcher-fresh","status":"pending_start","identity":{{"replacement_task_id":null}},"title_transition":{{"native_title_supported":false,"state":"awaiting_replacement_binding"}}}}
JSON
      exit 0
      ;;
    resumed)
      cat <<'JSON'
{{"agent":"codex-infra","packet_agent":"codex-infra","lineage_id":"lineage-launcher-old","rollover_id":"rollover-launcher-old","status":"resumed","identity":{{"replacement_task_id":"old-task"}},"title_transition":{{"native_title_supported":false,"state":"fallback_recorded"}}}}
JSON
      exit 0
      ;;
    ambiguous)
      printf '%s\\n' '{{"error_code":"MULTIPLE_LIVE_PENDING_ROLLOVERS","status":"ambiguous","candidate_count":2}}'
      exit 2
      ;;
  esac
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" ]]; then
  printf '%s\\n' "$@" > {os.fspath(supervisor_capture)!r}
  cat <<'JSON'
{{"identity":{{"lease":{{"session_id":"sess-codex","lease_id":"lease-codex","generation":1,"fencing_token":1,"expires_at":"2026-07-23T00:00:00Z"}}}}}}
JSON
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_canary.codex_lane" ]]; then
  printf '%s\\n' "$@" >> {os.fspath(canary_capture)!r}
  if [[ "${{CODEX_LAUNCHER_TEST_CANARY_FAIL:-}}" == "1" ]]; then
    exit 1
  fi
  if [[ "${{3:-}}" == "bootstrap" ]]; then
    mkdir -p ".claude/${{SESSION_EPIC}}-epic"
    : > ".claude/${{SESSION_EPIC}}-epic/CODEX-COLD-START.md"
    echo "Bootstrapped Codex cold-start board: .claude/${{SESSION_EPIC}}-epic/CODEX-COLD-START.md"
  fi
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "agents_extensions.shared.session_streams" ]]; then
  touch {os.fspath(lease_closed)!r}
  exit 0
fi
exec {os.fspath(_PROJECT_PYTHON)!r} "$@"
''',
    )
    codex_capture = tmp_path / "codex.txt"
    _write_executable(
        tmp_path / "home" / ".local" / "bin" / "codex",
        f'''#!/usr/bin/env bash
printf 'stream=%s\\nagent=%s\\nharness=%s\\n' \\
  "${{SESSION_STREAM_ID:-unset}}" "${{SESSION_STREAM_AGENT:-unset}}" \\
  "${{SESSION_STREAM_HARNESS:-unset}}" > {os.fspath(codex_capture)!r}
printf 'rollover_agent=%s\\nlineage=%s\\nrollover=%s\\n' \\
  "${{CODEX_LAUNCHER_ROLLOVER_AGENT:-unset}}" \\
  "${{CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID:-unset}}" \\
  "${{CODEX_LAUNCHER_ROLLOVER_ID:-unset}}" >> {os.fspath(codex_capture)!r}
''',
    )
    git_env = _clean_environ()
    subprocess.run(["git", "init", "-q", "-b", "main", os.fspath(project)], check=True, env=git_env)
    subprocess.run(
        ["git", "-C", os.fspath(project), "config", "user.email", "test@example.com"],
        check=True,
        env=git_env,
    )
    subprocess.run(
        ["git", "-C", os.fspath(project), "config", "user.name", "Test"],
        check=True,
        env=git_env,
    )
    subprocess.run(["git", "-C", os.fspath(project), "add", "."], check=True, env=git_env)
    subprocess.run(["git", "-C", os.fspath(project), "commit", "-qm", "init"], check=True, env=git_env)
    return project, supervisor_capture, canary_capture


def _run(
    project: Path,
    tmp_path: Path,
    *arguments: str,
    canary_fail: bool = False,
    rollover: str = "none",
) -> subprocess.CompletedProcess[str]:
    env = _clean_environ()
    env["HOME"] = os.fspath(tmp_path / "home")
    env["PATH"] = f"{tmp_path / 'home' / '.local' / 'bin'}:{env.get('PATH', '')}"
    for key in tuple(env):
        if key.startswith("SESSION_") or key.startswith("LEARN_UKRAINIAN_") or key in {
            "CODEX_CANONICAL_REPO_ROOT",
            "CODEX_SESSION",
            "CODEX_LAUNCHER_ROLLOVER_AGENT",
            "CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID",
            "CODEX_LAUNCHER_ROLLOVER_ID",
        }:
            env.pop(key, None)
    env["CODEX_LAUNCHER_TEST_ROLLOVER"] = rollover
    if canary_fail:
        env["CODEX_LAUNCHER_TEST_CANARY_FAIL"] = "1"
    return subprocess.run(
        [os.fspath(project / "start-codex.sh"), *arguments],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_trusted_epic_claims_codex_lease_then_runs_canary_steps(tmp_path: Path) -> None:
    project, supervisor_capture, canary_capture = _build_project(tmp_path)

    result = _run(project, tmp_path, "--epic", "devops", "--model", "gpt-5.6-sol")

    assert result.returncode == 0, result.stderr + result.stdout
    supervisor_args = supervisor_capture.read_text(encoding="utf-8").splitlines()
    assert supervisor_args[supervisor_args.index("--agent") + 1] == "codex"
    assert supervisor_args[supervisor_args.index("--harness") + 1] == "codex-cli"
    assert supervisor_args[supervisor_args.index("--stream") + 1] == "epic:5703"
    assert canary_capture.read_text(encoding="utf-8").splitlines() == [
        "-m",
        "scripts.session_canary.codex_lane",
        "mint",
        "--epic",
        "devops",
        "-m",
        "scripts.session_canary.codex_lane",
        "bootstrap",
        "--epic",
        "devops",
    ]
    assert "CODEX-COLD-START.md" in result.stdout


def test_untrusted_route_skips_lease_and_canary(tmp_path: Path) -> None:
    project, supervisor_capture, canary_capture = _build_project(tmp_path)

    result = _run(project, tmp_path, "--epic", "harness", "--model", "gpt-5.6-terra")

    assert result.returncode == 0, result.stderr + result.stdout
    assert not supervisor_capture.exists()
    assert not canary_capture.exists()
    assert "Skipping stream lease (untrusted Codex route)." in result.stderr


def test_canary_failure_closes_lease_and_refuses_trusted_launch(tmp_path: Path) -> None:
    project, supervisor_capture, canary_capture = _build_project(tmp_path)

    result = _run(project, tmp_path, "--epic", "harness", "--model", "gpt-5.6-sol", canary_fail=True)

    assert result.returncode == 1
    assert supervisor_capture.exists()
    assert canary_capture.read_text(encoding="utf-8").splitlines() == [
        "-m",
        "scripts.session_canary.codex_lane",
        "mint",
        "--epic",
        "infra",
    ]
    assert "Codex canary mint failed; refusing" in result.stderr
    assert (tmp_path / "lease-closed").is_file()
    assert not (tmp_path / "codex.txt").exists()


def test_fresh_exact_rollover_is_exported_to_new_codex_task(tmp_path: Path) -> None:
    project, supervisor_capture, _ = _build_project(tmp_path)

    result = _run(
        project,
        tmp_path,
        "--epic",
        "devops",
        "--model",
        "gpt-5.6-sol",
        rollover="pending",
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert supervisor_capture.exists()
    assert (tmp_path / "codex.txt").read_text(encoding="utf-8").splitlines()[-3:] == [
        "rollover_agent=codex-infra",
        "lineage=lineage-launcher-fresh",
        "rollover=rollover-launcher-fresh",
    ]


@pytest.mark.parametrize("rollover", ["ambiguous", "resumed"])
def test_ambiguous_or_resumed_rollover_fails_before_lease_and_codex(
    tmp_path: Path, rollover: str
) -> None:
    project, supervisor_capture, canary_capture = _build_project(tmp_path)

    result = _run(
        project,
        tmp_path,
        "--epic",
        "devops",
        "--model",
        "gpt-5.6-sol",
        rollover=rollover,
    )

    assert result.returncode == 1
    assert not supervisor_capture.exists()
    assert not canary_capture.exists()
    assert not (tmp_path / "codex.txt").exists()
    if rollover == "ambiguous":
        assert "MULTIPLE_LIVE_PENDING_ROLLOVERS" in result.stderr
    else:
        assert "already resumed; refusing to reuse it" in result.stderr
