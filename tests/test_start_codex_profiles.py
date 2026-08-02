"""Canonical-checkout and context-profile behavior for start-codex.sh."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"
_LAUNCHER_FILES = (
    Path("start-codex.sh"),
    Path("start-codex-driver.sh"),
    Path("scripts/config/context_profiles.yaml"),
    Path("scripts/lib/context_profiles.py"),
    Path("scripts/lib/deploy_extensions.sh"),
    Path("scripts/lib/fleet_comms_cold_start.sh"),
    Path("scripts/lib/handoff_identity.sh"),
    Path("scripts/lib/launcher_core.sh"),
    Path("scripts/lib/profile_resolver.sh"),
    Path("scripts/lib/session_supervisor.sh"),
    Path("scripts/lib/thread_rollover_link.sh"),
    Path("scripts/launchers/codex.sh"),
    Path("scripts/orchestration/thread_handoff.py"),
)


def _write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = (env if env is not None else os.environ).copy()
    for name in (
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_WORK_TREE",
    ):
        run_env.pop(name, None)
    return subprocess.run(
        command,
        cwd=cwd,
        env=run_env,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )


def _prepare_repo(
    tmp_path: Path, *, separate_git_dir: bool = False
) -> tuple[Path, Path]:
    primary = tmp_path / "repo"
    primary.mkdir()
    for relative in _LAUNCHER_FILES:
        destination = primary / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / relative, destination)

    venv_bin = primary / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    _write_executable(
        venv_bin / "python",
        f'''#!/usr/bin/env bash
if [[ "${{1:-}}" == */scripts/orchestration/thread_handoff.py && "$*" == *" detect "* ]]; then
  case "${{CODEX_LAUNCHER_TEST_ROLLOVER:-none}}" in
    none)
      printf '%s\\n' '{{"agent":"codex-test","status":"none"}}'
      exit 0
      ;;
    pending)
      cat <<'JSON'
{{"agent":"codex-devops","packet_agent":"codex-devops","lineage_id":"lineage-launcher-fresh","rollover_id":"rollover-launcher-fresh","status":"pending_start","identity":{{"replacement_task_id":null}},"title_transition":{{"native_title_supported":false,"state":"awaiting_replacement_binding"}}}}
JSON
      exit 0
      ;;
    resumed)
      cat <<'JSON'
{{"agent":"codex-devops","packet_agent":"codex-devops","lineage_id":"lineage-launcher-old","rollover_id":"rollover-launcher-old","status":"resumed","identity":{{"replacement_task_id":"old-task"}},"title_transition":{{"native_title_supported":false,"state":"fallback_recorded"}}}}
JSON
      exit 0
      ;;
    ambiguous)
      printf '%s\\n' '{{"error_code":"MULTIPLE_LIVE_PENDING_ROLLOVERS","status":"ambiguous","candidate_count":2}}'
      exit 2
      ;;
  esac
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.orchestration.codex_transport_health" ]]; then
  printf '%s\\n' '{{"status":"healthy","fresh":true}}'
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" ]]; then
  cat <<'JSON'
{{"identity":{{"lease":{{"session_id":"session-test","lease_id":"lease-test","generation":1,"fencing_token":1,"expires_at":"2026-07-23T00:00:00Z"}}}}}}
JSON
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "agents_extensions.shared.session_streams" ]]; then
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_canary.codex_lane" ]]; then
  exit 0
fi
exec {os.fspath(_PROJECT_PYTHON)!r} "$@"
''',
    )

    init_command = ["git", "init", "-b", "main"]
    if separate_git_dir:
        init_command.extend(
            ["--separate-git-dir", os.fspath(tmp_path / "separate-git-dir")]
        )
    assert _run(init_command, primary).returncode == 0
    assert _run(["git", "add", "."], primary).returncode == 0
    commit = _run(
        [
            "git",
            "-c",
            "user.name=Codex Launcher Test",
            "-c",
            "user.email=codex-launcher@example.invalid",
            "commit",
            "-m",
            "launcher fixture",
        ],
        primary,
    )
    assert commit.returncode == 0, commit.stderr

    linked = tmp_path / "linked"
    worktree = _run(["git", "worktree", "add", "--detach", os.fspath(linked), "HEAD"], primary)
    assert worktree.returncode == 0, worktree.stderr
    return primary, linked


def _launch(
    tmp_path: Path,
    arguments: list[str],
    *,
    driver: bool = False,
    separate_git_dir: bool = False,
    provide_canonical_root: bool = False,
    ambient_profile: tuple[str, str] | None = None,
    rollover: str = "none",
    expect_success: bool = True,
) -> tuple[dict[str, str], list[str], subprocess.CompletedProcess[str], Path, Path]:
    primary, linked = _prepare_repo(tmp_path, separate_git_dir=separate_git_dir)
    home_bin = tmp_path / "home" / ".local" / "bin"
    capture = tmp_path / "capture.txt"
    _write_executable(
        home_bin / "codex",
        """#!/usr/bin/env bash
{
    printf 'canonical=%s\n' "$CODEX_CANONICAL_REPO_ROOT"
    printf 'session=%s\n' "$CODEX_SESSION"
    printf 'profile=%s\n' "$LEARN_UKRAINIAN_PROFILE_ID"
    printf 'requested_profile=%s\n' "$LEARN_UKRAINIAN_REQUESTED_PROFILE_ID"
    printf 'transport=%s\n' "$LEARN_UKRAINIAN_TRANSPORT"
    printf 'main_model=%s\n' "$LEARN_UKRAINIAN_MAIN_MODEL_ID"
    printf 'main_window=%s\n' "$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"
    printf 'reason=%s\n' "$LEARN_UKRAINIAN_RESOLUTION_REASON"
    printf 'trusted=%s\n' "$LEARN_UKRAINIAN_TRUSTED"
    printf 'epic=%s\n' "${SESSION_EPIC:-}"
    printf 'handoff_agent=%s\n' "${SESSION_HANDOFF_AGENT:-}"
    printf 'rollover_agent=%s\n' "${CODEX_LAUNCHER_ROLLOVER_AGENT:-}"
    printf 'lineage=%s\n' "${CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID:-}"
    printf 'rollover=%s\n' "${CODEX_LAUNCHER_ROLLOVER_ID:-}"
    printf 'arg=%s\n' "$@"
} > "$CODEX_LAUNCHER_TEST_CAPTURE"
""",
    )

    env = os.environ.copy()
    for name in tuple(env):
        if name.startswith("LEARN_UKRAINIAN_") or name in {
            "CODEX_CANONICAL_REPO_ROOT",
            "CODEX_SESSION",
            "CODEX_LAUNCHER_ROLLOVER_AGENT",
            "CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID",
            "CODEX_LAUNCHER_ROLLOVER_ID",
            "SESSION_EPIC",
            "SESSION_HANDOFF_AGENT",
        }:
            env.pop(name, None)
    env.update(
        {
            "HOME": os.fspath(tmp_path / "home"),
            "PATH": f"{home_bin}:{os.environ.get('PATH', '')}",
            "CODEX_LAUNCHER_TEST_CAPTURE": os.fspath(capture),
            "CODEX_LAUNCHER_TEST_ROLLOVER": rollover,
        }
    )
    if provide_canonical_root:
        env["CODEX_CANONICAL_REPO_ROOT"] = os.fspath(primary)
    if ambient_profile is not None:
        profile_id, transport = ambient_profile
        env["LEARN_UKRAINIAN_REQUESTED_PROFILE_ID"] = profile_id
        env["LEARN_UKRAINIAN_TRANSPORT"] = transport

    before = _run(["git", "worktree", "list", "--porcelain"], primary)
    result = _run(
        [os.fspath(linked / ("start-codex-driver.sh" if driver else "start-codex.sh")), *arguments],
        linked,
        env=env,
    )
    after = _run(["git", "worktree", "list", "--porcelain"], primary)
    if expect_success:
        assert result.returncode == 0, result.stderr
    assert before.stdout == after.stdout
    assert not (primary / ".worktrees" / "codex-interactive").exists()

    if not expect_success:
        return {}, [], result, primary, linked

    lines = capture.read_text(encoding="utf-8").splitlines()
    values = dict(line.split("=", 1) for line in lines if not line.startswith("arg="))
    forwarded = [line.removeprefix("arg=") for line in lines if line.startswith("arg=")]
    return values, forwarded, result, primary, linked


def test_launcher_targets_canonical_main_without_creating_worktree(tmp_path: Path) -> None:
    values, forwarded, result, primary, linked = _launch(
        tmp_path,
        ["--model", "gpt-5.6-sol", "resume", "thread-id"],
    )

    assert linked != primary
    # Mutation guard: removing native preflight's canonical/profile exports
    # leaves the SessionStart denominator unset in this provider invocation.
    assert values == {
        "canonical": os.fspath(primary),
        "session": "1",
        "profile": "native_codex",
        "requested_profile": "native_codex",
        "transport": "native_codex",
        "main_model": "gpt-5.6-sol",
        "main_window": "272000",
        "reason": "explicit-profile",
        "trusted": "1",
        "epic": "",
        "handoff_agent": "",
        "rollover_agent": "",
        "lineage": "",
        "rollover": "",
    }
    assert forwarded == [
        "--dangerously-bypass-approvals-and-sandbox",
        "--search",
        "-c",
        'tui.status_line=["model-with-reasoning","status","context-used","context-window-size","five-hour-limit","weekly-limit","git-branch","task-progress"]',
        "-C",
        os.fspath(linked),
        "--model",
        "gpt-5.6-sol",
        "resume",
        "thread-id",
    ]
    # Mutation guard: dropping the adapter status-line config makes this exact
    # argv assertion fail before an opaque Codex TUI session can hide it.
    assert "Context profile:" not in result.stdout


def test_launcher_binds_epic_and_strips_private_flag(tmp_path: Path) -> None:
    values, forwarded, _, _, _ = _launch(
        tmp_path,
        ["--epic", "hramatka", "--model", "gpt-5.6-sol", "orchestrate this epic"],
        driver=True,
    )

    assert values["epic"] == "hramatka"
    assert values["handoff_agent"] == "codex-hramatka"
    assert "orchestrate this epic" in forwarded
    assert "--epic" not in forwarded
    assert any("already claimed the hramatka lease" in arg for arg in forwarded)


def test_launcher_binds_epic_when_no_codex_args_remain(tmp_path: Path) -> None:
    values, forwarded, _, _, _ = _launch(
        tmp_path,
        ["--epic=hramatka", "--model", "gpt-5.6-sol"],
        driver=True,
    )

    assert values["epic"] == "hramatka"
    assert values["handoff_agent"] == "codex-hramatka"
    assert forwarded[:4] == [
        "--dangerously-bypass-approvals-and-sandbox",
        "--search",
        "-c",
        'tui.status_line=["model-with-reasoning","status","context-used","context-window-size","five-hour-limit","weekly-limit","git-branch","task-progress"]',
    ]
    cd_index = forwarded.index("-C")
    assert forwarded[cd_index + 1] != values["canonical"]
    assert forwarded[cd_index + 2 : cd_index + 4] == ["--model", "gpt-5.6-sol"]
    assert any("already claimed the hramatka lease" in arg for arg in forwarded)


def test_launcher_normalizes_equals_form_epic_suffix(tmp_path: Path) -> None:
    values, forwarded, _, _, _ = _launch(
        tmp_path,
        ["--epic=atlas", "--model", "gpt-5.6-sol"],
        driver=True,
    )

    assert values["epic"] == "atlas"
    assert values["handoff_agent"] == "codex-atlas"
    assert "--epic=atlas" not in forwarded


@pytest.mark.parametrize("epic_args", [["--epic"], ["--epic="], ["--epic", "Atlas"]])
def test_launcher_rejects_missing_or_invalid_epic_before_codex_starts(
    tmp_path: Path,
    epic_args: list[str],
) -> None:
    primary, linked = _prepare_repo(tmp_path)
    home_bin = tmp_path / "home" / ".local" / "bin"
    started = tmp_path / "codex-started"
    _write_executable(
        home_bin / "codex",
        f"#!/usr/bin/env bash\ntouch {os.fspath(started)!r}\n",
    )
    env = os.environ.copy()
    env.update({"HOME": os.fspath(tmp_path / "home")})
    for name in (
        "CODEX_CANONICAL_REPO_ROOT",
        "SESSION_EPIC",
        "SESSION_HANDOFF_AGENT",
    ):
        env.pop(name, None)

    result = _run([os.fspath(linked / "start-codex-driver.sh"), *epic_args], linked, env=env)

    assert result.returncode != 0
    assert not started.exists()
    assert os.fspath(primary) not in result.stdout
    if epic_args == ["--epic", "Atlas"]:
        assert "unknown lane selector 'Atlas'" in result.stderr
    else:
        assert "--epic" in result.stderr


def test_launcher_model_mismatch_fails_closed_but_still_starts(tmp_path: Path) -> None:
    values, forwarded, result, primary, _ = _launch(
        tmp_path,
        ["--model", "gpt-5.6-terra"],
    )

    assert values["canonical"] == os.fspath(primary)
    assert values["profile"] == "fallback"
    assert values["transport"] == "unknown"
    assert values["main_window"] == "0"
    assert values["reason"] == "model-mismatch"
    assert values["trusted"] == "0"
    assert forwarded[-2:] == ["--model", "gpt-5.6-terra"]
    assert "without a fabricated context window" not in result.stderr


def test_untrusted_codex_driver_skips_lease_and_canary(tmp_path: Path) -> None:
    values, _, result, _, linked = _launch(
        tmp_path,
        ["--epic", "devops", "--model", "gpt-5.6-terra"],
        driver=True,
    )

    assert values["trusted"] == "0"
    # Mutation guard: bypassing the trusted-route gate writes this receipt and
    # starts a lease-backed driver with a fabricated context denominator.
    assert not (linked / ".claude" / "devops-epic" / "session-lease.env").exists()
    assert "Skipping stream lease and provider canary (untrusted codex route)." in result.stderr


def test_launcher_does_not_inherit_foreign_route_profile(tmp_path: Path) -> None:
    values, _, _, _, _ = _launch(
        tmp_path,
        ["--model", "gpt-5.6-sol"],
        ambient_profile=("sol_lead", "claudex"),
    )

    assert values["profile"] == "native_codex"
    assert values["requested_profile"] == "native_codex"
    assert values["transport"] == "native_codex"
    assert values["trusted"] == "1"


def test_launcher_accepts_validated_main_checkout_with_separate_git_dir(
    tmp_path: Path,
) -> None:
    values, forwarded, _, primary, _ = _launch(
        tmp_path,
        ["--model=gpt-5.6-sol"],
        separate_git_dir=True,
        provide_canonical_root=True,
    )

    assert values["canonical"] == os.fspath(primary)
    cd_index = forwarded.index("-C")
    assert forwarded[cd_index + 1] != os.fspath(primary)
    assert values["profile"] == "native_codex"


def test_launcher_rejects_canonical_root_from_another_repository(
    tmp_path: Path,
) -> None:
    primary, linked = _prepare_repo(tmp_path)
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    assert _run(["git", "init", "-b", "main"], unrelated).returncode == 0

    env = os.environ.copy()
    env["CODEX_CANONICAL_REPO_ROOT"] = os.fspath(unrelated)
    result = _run([os.fspath(linked / "start-codex.sh")], linked, env=env)

    assert result.returncode != 0
    assert "is not a checkout of this Git common directory" in result.stderr
    assert os.fspath(primary) not in result.stdout


def test_launcher_refuses_a_resolved_primary_that_is_not_on_main(tmp_path: Path) -> None:
    primary, linked = _prepare_repo(tmp_path)
    assert _run(["git", "checkout", "-qb", "wrong-primary"], primary).returncode == 0
    started = tmp_path / "codex-started"
    _write_executable(
        tmp_path / "home" / ".local" / "bin" / "codex",
        f"#!/usr/bin/env bash\ntouch {os.fspath(started)!r}\n",
    )
    env = os.environ.copy()
    env.update(
        {
            "HOME": os.fspath(tmp_path / "home"),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(primary),
        }
    )

    result = _run([os.fspath(linked / "start-codex.sh")], linked, env=env)

    assert result.returncode == 1
    assert "canonical checkout must be on main" in result.stderr
    assert not started.exists()


def test_fresh_exact_rollover_is_exported_to_new_codex_task(tmp_path: Path) -> None:
    values, _, result, _, linked = _launch(
        tmp_path,
        ["--epic", "devops", "--model", "gpt-5.6-sol"],
        driver=True,
        rollover="pending",
    )

    assert result.returncode == 0, result.stderr
    assert values["rollover_agent"] == "codex-devops"
    assert values["lineage"] == "lineage-launcher-fresh"
    assert values["rollover"] == "rollover-launcher-fresh"
    assert (linked / ".claude" / "devops-epic" / "session-lease.env").is_file()


@pytest.mark.parametrize("rollover", ["ambiguous", "resumed"])
def test_ambiguous_or_resumed_rollover_fails_before_lease_and_codex(
    tmp_path: Path, rollover: str
) -> None:
    _, _, result, _, linked = _launch(
        tmp_path,
        ["--epic", "devops", "--model", "gpt-5.6-sol"],
        driver=True,
        rollover=rollover,
        expect_success=False,
    )

    assert result.returncode == 1
    # Mutation guard: moving resolution below launcher_claim_driver_lease
    # creates this receipt before the rejection and fails the assertion.
    assert not (linked / ".claude" / "devops-epic" / "session-lease.env").exists()
    assert not (tmp_path / "capture.txt").exists()
    if rollover == "ambiguous":
        assert "MULTIPLE_LIVE_PENDING_ROLLOVERS" in result.stderr
    else:
        assert "already resumed; refusing to reuse it" in result.stderr
