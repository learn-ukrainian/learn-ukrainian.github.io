"""Contracts for the Codex-specific lifecycle-hook manifest and entry point."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from scripts.agent_runtime import codex_hook_policy
from scripts.agent_runtime.codex_hook_policy import (
    ENFORCE_VENV_TIMEOUT,
    LOCAL_BASH_GUARDS,
    MERGE_GUARDS,
    PRIMARY_WRITE_GUARD,
    _result_code,
    _run_enforce_venv,
    run_guard,
)
from tests.helpers.python import project_python

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

REPO_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_ROOT = Path(
    subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        text=True, timeout=30,
    ).strip()
).parent
HOOKS_CONFIG = REPO_ROOT / "agents_extensions" / "codex" / "hooks.json"
PROJECT_CONFIG = REPO_ROOT / "agents_extensions" / "codex" / "config.toml"
ENTRY = REPO_ROOT / "scripts" / "agent_runtime" / "codex_hook_entry.sh"
VENV_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "enforce-venv.sh"
INBOX_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "check-agent-inbox.sh"
SESSION_SETUP_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "session-setup.sh"
POST_COMPACT_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "post-compact.sh"


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )


def _make_exact_python_checkout(root: Path, *, delegate: Path | None = None) -> None:
    python = root / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    script = "#!/bin/bash\nprintf 'Python 3.12.15\\n'\n"
    if delegate is not None:
        script = (
            "#!/bin/bash\n"
            "if [ \"${1:-}\" = \"--version\" ]; then\n"
            "  printf 'Python 3.12.15\\n'\n"
            "  exit 0\n"
            "fi\n"
            f"exec {shlex.quote(os.fspath(delegate))} \"$@\"\n"
        )
    python.write_text(script, encoding="utf-8")
    python.chmod(0o755)
    (root / ".python-version").write_text("3.12.15\n", encoding="utf-8")


def _make_linked_worktree(tmp_path: Path) -> tuple[Path, Path]:
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees/dispatch/codex/hooks-test"
    primary.mkdir()
    _run(["git", "init", "-b", "main"], cwd=primary)
    _run(["git", "config", "user.email", "hooks@example.invalid"], cwd=primary)
    _run(["git", "config", "user.name", "Hook Tests"], cwd=primary)
    (primary / "README.md").write_text("hook test\n", encoding="utf-8")
    _make_exact_python_checkout(
        primary,
        delegate=Path(project_python()),
    )
    _run(["git", "add", "README.md"], cwd=primary)
    _run(["git", "commit", "-m", "test fixture"], cwd=primary)
    _run(["git", "worktree", "add", "-b", "codex/hooks-test", str(worktree)], cwd=primary)
    return primary, worktree


def _manifest() -> dict:
    return json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))


def test_grok_post_compact_reminder_pins_c2903_author_reviewer_pairs(tmp_path: Path) -> None:
    result = subprocess.run(
        ["bash", str(POST_COMPACT_HOOK)], cwd=tmp_path,
        env={**os.environ, "GROK_AGENT": "grok", "SESSION_EPIC": "", "CODEX_COMPACT_SESSION_START": ""},
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["additionalContext"]
    assert "default code author = Claude (Sonnet 5.5; Opus 5.5 for hard or security work), reviewed by Sol 6.1" in context
    assert "Ukrainian content authored by Sol 6.1; review seats are Gemini (AGY) and Sol, Gemini (AGY) alone for an OpenAI author, Sol alone for a Google author, and no Claude seat" in context
    assert "explicit Luna/Flash bounded routes require a Sol advisory envelope" in context
    assert "default bounded work = Sol advisory envelope" not in context


def test_codex_manifest_uses_only_supported_result_event() -> None:
    hooks = _manifest()["hooks"]

    assert "PostToolUse" in hooks
    assert "PostToolUseFailure" not in hooks


def test_codex_project_config_leaves_root_model_user_selectable() -> None:
    config = tomllib.loads(PROJECT_CONFIG.read_text(encoding="utf-8"))

    assert "model" not in config
    assert "model_reasoning_effort" not in config
    assert config["features"] == {
        "hooks": True,
        "multi_agent": True,
        "memories": False,
        "multi_agent_v2": {
            "enabled": True,
            "hide_spawn_agent_metadata": False,
            "tool_namespace": "agents",
        },
    }
    assert config["agents"] == {
        "enabled": True,
        "max_concurrent_threads_per_session": 3,
        "default_subagent_model": "gpt-6.1-terra",
        "default_subagent_reasoning_effort": "high",
        "interrupt_message": True,
    }


def test_codex_compaction_has_one_bounded_hydration_path() -> None:
    hooks = _manifest()["hooks"]
    session_groups = hooks["SessionStart"]
    session_group, compact_group = session_groups

    assert session_group["matcher"] == "startup|resume|clear"
    assert session_group["hooks"][0]["additionalContextLimit"] == 1200
    assert compact_group["matcher"] == "compact"
    assert "CODEX_COMPACT_SESSION_START=1" in compact_group["hooks"][0]["command"]
    assert 'post-compact.sh"' in compact_group["hooks"][0]["command"]
    assert compact_group["hooks"][0]["timeout"] == 15
    assert compact_group["hooks"][0]["additionalContextLimit"] == 800
    assert "PostCompact" not in hooks


def test_ordinary_codex_start_is_concise_and_compact_session_start_is_silent(
    tmp_path: Path,
) -> None:
    deployed_hooks = tmp_path / ".codex" / "hooks"
    deployed_hooks.mkdir(parents=True)
    session_hook = deployed_hooks / "session-setup.sh"
    compact_hook = deployed_hooks / "post-compact.sh"
    shutil.copy2(SESSION_SETUP_HOOK, session_hook)
    shutil.copy2(POST_COMPACT_HOOK, compact_hook)

    environment = os.environ.copy()
    for key in tuple(environment):
        if (
            key.startswith("LEARN_UKRAINIAN_")
            or key.startswith("CODEX_")
            or key.startswith("SESSION_")
            or key == "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS"
        ):
            environment.pop(key, None)
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(PRIMARY_ROOT),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(PRIMARY_ROOT),
            "CLAUDE_PROFILE_RESOLVER_SH": os.fspath(REPO_ROOT / "scripts/lib/profile_resolver.sh"),
            "CLAUDE_PROFILE_RESOLVER_PY": os.fspath(REPO_ROOT / "scripts/lib/context_profiles.py"),
            "HOME": os.fspath(tmp_path / "home"),
        }
    )
    started = subprocess.run(
        ["bash", os.fspath(session_hook)],
        input=json.dumps({"source": "startup", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=30,
    )

    assert started.returncode == 0, started.stderr
    context = json.loads(started.stdout)["hookSpecificOutput"]["additionalContext"]
    # This start reads the real checkout and PATH, so a tool cache at its root
    # and a missing Codex CLI can both add a notice; both must still fit (#10952).
    assert len(context.encode()) < 500
    assert "profile=native_codex" in context
    assert "Native compaction is runtime-owned" in context
    if "ROOT HYGIENE" in context:
        assert context.endswith(_ROOT_DETAIL)
    assert "NO EPIC ASSIGNED" not in context
    assert "THREAD ROLLOVER" not in context
    assert "MEMORY.md" not in context

    compacted = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        input=json.dumps({"source": "compact", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment | {"CODEX_COMPACT_SESSION_START": "1"},
        timeout=10,
    )
    assert compacted.returncode == 0, compacted.stderr
    assert compacted.stdout == ""


# A real Codex session id is a UUID; it lands in the capsule's orientation
# URL, so the byte budget is measured with one rather than an empty id.
_CODEX_SESSION_ID = "0199a5c1-1234-7abc-8def-0123456789ab"
_SYNTHETIC_ROOT_GUARD = (
    "import json\n"
    "import pathlib\n"
    "report = pathlib.Path(__file__).with_name('report.json').read_text(encoding='utf-8')\n"
    "print(json.dumps(json.loads(report), indent=2))\n"
)
_ROOT_DETAIL = "Detail: .venv/bin/python -m scripts.hygiene.root_entry_guard"
# The lane self-test's literal verdict when the probed CLI is not on PATH.
_CLI_MISSING_REASON = "FileNotFoundError while building or spawning the adapter"
_CODEX_CLI_MISSING = f"DISPATCH LANE SELF-TEST FAILED for codex: {_CLI_MISSING_REASON}"
# The hook's own text when run_bounded's outer bound exits 124 (#12725).
_LANE_PROBE_TIMEOUT_REASON = "probe timed out after 3 s"
# Stands in for scripts.agent_runtime.bounded_command only for the lane probe.
# Every other bounded command is the real runner, so root hygiene still runs.
_LANE_PROBE_RUNNER = """\
import os
import sys

command = sys.argv[1:]
if command[:1] == ["--timeout"]:
    command = command[2:]
if command[:1] == ["--"]:
    command = command[1:]
if "scripts.agent_runtime.lane_probe" in command:
    outcome = os.environ.get("LANE_PROBE_OUTCOME", "")
    if outcome == "timeout":
        raise SystemExit(124)
    if outcome == "missing":
        sys.stdout.write(os.environ["LANE_PROBE_RESULT_JSON"])
        raise SystemExit(1)
    if outcome == "healthy":
        raise SystemExit(0)
    sys.stderr.write("unexpected LANE_PROBE_OUTCOME\\n")
    raise SystemExit(2)
os.execv(sys.executable, [sys.executable, os.environ["LANE_PROBE_REAL_RUNNER"], *sys.argv[1:]])
"""


def _path_without(executable: str) -> str:
    """The inherited PATH minus every directory that provides ``executable``."""
    return os.pathsep.join(
        directory
        for directory in os.environ.get("PATH", "").split(os.pathsep)
        if directory and not os.access(os.path.join(directory, executable), os.X_OK)
    )


def _start_with_root_names(
    tmp_path: Path,
    names: list[str],
    *,
    synthetic: bool,
    lane_cli: bool = True,
    agent: str = "codex",
    probe_outcome: str | None = None,
) -> tuple[subprocess.CompletedProcess[bytes], Path, dict[str, str]]:
    """Run ordinary SessionStart with ``names`` as unexpected root entries.

    ``agent`` is ``codex`` (deployed under ``.codex``) or ``claude``.
    The lane probe does not run the real interpreter: a bounded-runner double
    returns the outcome immediately, so the contract does not depend on runner
    speed. ``lane_cli`` selects a completed healthy probe or a completed
    CLI-missing result. ``probe_outcome="timeout"`` is the outer-bound exit
    (124, no JSON). Returns the hook result, the fixture checkout and the
    hook environment.
    """
    project = tmp_path / "primary"
    project.mkdir()
    _run(["git", "init", "-b", "main"], cwd=project)
    _run(["git", "config", "user.email", "hooks@example.invalid"], cwd=project)
    _run(["git", "config", "user.name", "Hook Tests"], cwd=project)
    (project / ".gitignore").write_text(".venv\nscripts\n", encoding="utf-8")
    (project / ".python-version").write_text(
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n",
        encoding="utf-8",
    )
    (project / "README.md").write_text("hook test\n", encoding="utf-8")
    (project / ".venv").symlink_to(PRIMARY_ROOT / ".venv")
    (project / "scripts").symlink_to(REPO_ROOT / "scripts")
    _run(["git", "add", ".gitignore", ".python-version", "README.md"], cwd=project)
    _run(["git", "commit", "-m", "fixture"], cwd=project)
    hook_cwd = project
    if synthetic:
        # ``python -m`` puts its cwd first on sys.path. This shadow package
        # serves only scripts.hygiene.root_entry_guard and resolves every
        # other scripts.* module from the real tree.
        hook_cwd = tmp_path / "shadow"
        shadow_hygiene = hook_cwd / "scripts" / "hygiene"
        shadow_hygiene.mkdir(parents=True)
        (hook_cwd / "scripts" / "__init__.py").write_text(
            f"__path__.append({os.fspath(REPO_ROOT / 'scripts')!r})\n", encoding="utf-8"
        )
        (shadow_hygiene / "__init__.py").write_text("", encoding="utf-8")
        (shadow_hygiene / "root_entry_guard.py").write_text(_SYNTHETIC_ROOT_GUARD, encoding="utf-8")
        report = {
            "repo_root": os.fspath(project),
            "unexpected_count": len(names),
            "unexpected": [{"name": name, "kind": "dir", "git_invisible": True} for name in names],
        }
        (shadow_hygiene / "report.json").write_text(json.dumps(report), encoding="utf-8")
    else:
        for name in names:
            (project / name).mkdir()

    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    if lane_cli:
        (stub_bin / agent).write_text(f"#!/bin/sh\necho '{agent} 0.0.0-test'\n", encoding="utf-8")
        (stub_bin / agent).chmod(0o755)

    deployed = tmp_path / f".{agent}" / "hooks"
    deployed.mkdir(parents=True)
    session_hook = deployed / "session-setup.sh"
    shutil.copy2(SESSION_SETUP_HOOK, session_hook)
    shutil.copy2(POST_COMPACT_HOOK, deployed / "post-compact.sh")
    environment = os.environ.copy()
    for key in tuple(environment):
        if (
            key.startswith("LEARN_UKRAINIAN_")
            or key.startswith("CODEX_")
            or key.startswith("SESSION_")
            or key == "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS"
        ):
            environment.pop(key, None)
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(project),
            "CLAUDE_PROFILE_RESOLVER_SH": os.fspath(REPO_ROOT / "scripts/lib/profile_resolver.sh"),
            "CLAUDE_PROFILE_RESOLVER_PY": os.fspath(REPO_ROOT / "scripts/lib/context_profiles.py"),
            "HOME": os.fspath(tmp_path / "home"),
            "PATH": os.fspath(stub_bin) + os.pathsep + _path_without(agent),
        }
    )
    if probe_outcome is None:
        probe_outcome = "healthy" if lane_cli else "missing"
    runner = tmp_path / "lane_probe_runner.py"
    runner.write_text(_LANE_PROBE_RUNNER, encoding="utf-8")
    environment["SESSION_BOUNDED_RUNNER"] = os.fspath(runner)
    environment["LANE_PROBE_REAL_RUNNER"] = os.fspath(
        REPO_ROOT / "scripts/agent_runtime/bounded_command.py"
    )
    environment["LANE_PROBE_OUTCOME"] = probe_outcome
    environment["LANE_PROBE_RESULT_JSON"] = json.dumps(
        {"probes": [{"agent": agent, "reason": _CLI_MISSING_REASON}]}
    )
    model = "gpt-6.1-sol"
    if agent == "codex":
        environment["CODEX_CANONICAL_REPO_ROOT"] = os.fspath(project)
    else:
        environment["CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS"] = "32000"
        model = "claude-opus-5-5"
    started = subprocess.run(
        ["bash", os.fspath(session_hook)],
        cwd=hook_cwd,
        input=json.dumps({"source": "startup", "model": model, "session_id": _CODEX_SESSION_ID}).encode(),
        capture_output=True,
        check=False,
        env=environment,
        timeout=60,
    )
    return started, project, environment


_ROOT_NAME_CASES = [
    pytest.param(["n" * 139], False, "1", None, id="real-139-byte-name"),
    pytest.param(["nnnnnnn€nnnn"], False, "1", None, id="three-byte-char-straddles-old-cut"),
    pytest.param(["nnnnnn😀nnn"], False, "1", None, id="four-byte-emoji-straddles-old-cut"),
    *(
        pytest.param(["n" * offset + "é" + "nnnn"], False, "1", None, id=f"e-acute-at-byte-{offset}")
        for offset in range(5, 10)
    ),
    pytest.param(["x\x1b[2J\x1b[H"], False, "1", None, id="terminal-clear-and-home"),
    pytest.param(["a\nb"], False, "1", None, id="newline"),
    pytest.param(["bell\x07"], False, "1", None, id="control-character"),
    pytest.param([".mypy_cache"], False, "1", ".mypy_cache", id="observed-ci-tool-cache"),
    pytest.param(["abcd", "efghi"], False, "2", "abcd, efghi", id="exactly-at-limit"),
    pytest.param(["abcd", "efghij"], False, "2", None, id="one-over-limit"),
    pytest.param([f"garbage-{index:04d}" for index in range(1000)], True, "99+", None, id="1000-entries"),
]


@pytest.mark.parametrize("lane_cli", [True, False], ids=["codex-cli", "no-codex-cli"])
@pytest.mark.parametrize(("names", "synthetic", "shown_count", "inline"), _ROOT_NAME_CASES)
def test_ordinary_codex_start_bounds_root_hygiene_names(
    tmp_path: Path,
    names: list[str],
    synthetic: bool,
    shown_count: str,
    inline: str | None,
    lane_cli: bool,
) -> None:
    """Root-entry names are unbounded and attacker-shaped (#6863).

    The ordinary SessionStart context must stay strictly under 500 bytes and
    valid UTF-8 for any names, also when the dispatch-lane self-test fails
    beside it because the probe completed without the Codex CLI (#10952).
    The probe outcome is fixed by the test, so a slow runner cannot turn a
    completed miss into a timeout. Names appear inline only as a whole
    printable ASCII list of at most 11 bytes; otherwise the Detail command
    lists them and stderr gets every name on one escaped line. A synthetic
    guard report stands in for 1,000 real directories, which the guard cannot
    scan inside its deadline.
    """
    started, project, environment = _start_with_root_names(tmp_path, names, synthetic=synthetic, lane_cli=lane_cli)

    assert started.returncode == 0, started.stderr
    context = json.loads(started.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    assert len(context.encode("utf-8")) < 500
    assert _CODEX_SESSION_ID in context
    assert "profile=native_codex" in context
    assert "Native compaction is runtime-owned" in context
    assert "SESSION SETUP CHECK" not in context
    if lane_cli:
        assert "DISPATCH LANE SELF-TEST FAILED" not in context
    else:
        assert f"\n- {_CODEX_CLI_MISSING}\n" in context
    root_line = (
        f"\n- ROOT HYGIENE: {shown_count} unexpected primary-checkout root entries"
        f"{f' ({inline})' if inline else ''}; manual removal only (#6863). {_ROOT_DETAIL}"
    )
    assert context.endswith(root_line)
    escaped_line = b"ROOT HYGIENE unexpected entries (escaped): " + ascii(names).encode() + b"\n"
    if inline is None:
        assert all(name not in context for name in names)
        assert escaped_line in started.stderr
    else:
        assert escaped_line not in started.stderr
    for raw in (b"\x1b", b"\x07"):
        assert raw not in started.stderr
    for name in names:
        if not (name.isascii() and name.isprintable()):
            assert name.encode() not in started.stderr
    if not synthetic:
        assert all((project / name).is_dir() for name in names), "the canary never deletes"

    compacted = subprocess.run(
        ["bash", os.fspath(tmp_path / ".codex" / "hooks" / "post-compact.sh")],
        input=json.dumps({"source": "compact", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment | {"CODEX_COMPACT_SESSION_START": "1"},
        timeout=10,
    )
    assert compacted.returncode == 0, compacted.stderr
    assert compacted.stdout == ""


def test_ordinary_codex_start_names_a_timed_out_lane_probe(tmp_path: Path) -> None:
    """A probe killed at the outer bound names that timeout and still returns (#12725).

    The bounded-runner double exits 124 with no JSON, which is what
    ``run_bounded`` does when the 3s bound fires before the probe prints.
    SessionStart stays advisory: exit 0, valid UTF-8, under 500 bytes, with
    the root-hygiene line still present. The CLI-missing reason is only for a
    probe that completes.
    """
    started, project, _environment = _start_with_root_names(
        tmp_path, [".mypy_cache"], synthetic=False, probe_outcome="timeout"
    )

    assert started.returncode == 0, started.stderr
    context = json.loads(started.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    assert len(context.encode("utf-8")) < 500
    assert _CODEX_SESSION_ID in context
    assert f"\n- DISPATCH LANE SELF-TEST FAILED for codex: {_LANE_PROBE_TIMEOUT_REASON}\n" in context
    assert _CLI_MISSING_REASON not in context
    assert context.endswith(
        "\n- ROOT HYGIENE: 1 unexpected primary-checkout root entries (.mypy_cache); "
        f"manual removal only (#6863). {_ROOT_DETAIL}"
    )
    assert (project / ".mypy_cache").is_dir()


@pytest.mark.parametrize("lane_cli", [True, False], ids=["codex-cli", "no-codex-cli"])
def test_empty_name_list_is_an_unchanged_control(tmp_path: Path, lane_cli: bool) -> None:
    """An empty name list must still print no root-hygiene notice."""
    started, _, _ = _start_with_root_names(tmp_path, [], synthetic=False, lane_cli=lane_cli)

    assert started.returncode == 0, started.stderr
    context = json.loads(started.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    assert len(context.encode("utf-8")) < 500
    assert _CODEX_SESSION_ID in context
    assert "profile=native_codex" in context
    assert "Native compaction is runtime-owned" in context
    assert ("DISPATCH LANE SELF-TEST FAILED" in context) is not lane_cli
    assert "ROOT HYGIENE" not in context
    assert b"ROOT HYGIENE" not in started.stderr


@pytest.mark.parametrize(
    ("names", "shown_names"),
    [
        pytest.param([".mypy_cache"], ".mypy_cache", id="inline"),
        pytest.param(["n" * 139], "names on stderr", id="withheld"),
    ],
)
def test_claude_session_start_keeps_full_notice_layout(tmp_path: Path, names: list[str], shown_names: str) -> None:
    """The issue formatter is shared; only ordinary Codex is compacted (#10952)."""
    started, _, _ = _start_with_root_names(tmp_path, names, synthetic=False, lane_cli=False, agent="claude")

    assert started.returncode == 0, started.stderr
    context = json.loads(started.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    assert "\n\nSESSION SETUP CHECK:\nISSUES:\n  - " in context
    assert "\n  - DISPATCH LANE SELF-TEST FAILED for claude (handoff identity claude): " in context
    assert (
        f"\n  - ROOT HYGIENE: 1 unexpected primary-checkout root entries ({shown_names}). "
        f"Remove manually; never auto-deleted (#6863). {_ROOT_DETAIL}\n"
    ) in context
    assert "\nINFO:\n  - Orientation diagnostics: " in context


def test_explicit_non_driver_codex_compact_session_start_is_silent(tmp_path: Path) -> None:
    compact_hook = tmp_path / ".codex" / "hooks" / "post-compact.sh"
    compact_hook.parent.mkdir(parents=True)
    shutil.copy2(POST_COMPACT_HOOK, compact_hook)
    environment = os.environ.copy()
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(tmp_path),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(tmp_path),
            "SESSION_HANDOFF_AGENT": "codex",
        }
    )
    environment.pop("SESSION_EPIC", None)

    completed = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        input=json.dumps({"source": "compact", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment | {"CODEX_COMPACT_SESSION_START": "1"},
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""


def _run_bound_codex_compact(tmp_path: Path, *, block_hydration_import: bool = False) -> str:
    """Exercise the real bounded runner and canary handoff resolver."""
    (tmp_path / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    compact_hook = tmp_path / ".codex" / "hooks" / "post-compact.sh"
    compact_hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(POST_COMPACT_HOOK, compact_hook)
    fake_python = tmp_path / "fake-python"
    selection_guard = ""
    if block_hydration_import:
        # Selection must not pay the unrelated hydration runtime's import cost.
        guarded_selection = (
            "import sys; sys.modules['scripts.session_canary.shared_hydration'] = None; "
            "exec(sys.argv.pop(1))"
        )
        selection_guard = (
            "if [ \"${1:-}\" = '-c' ]; then\n"
            "  shift\n"
            f"  exec {shlex.quote(sys.executable)} -c {shlex.quote(guarded_selection)} \"$@\"\n"
            "fi\n"
        )
    fake_python.write_text(
        "#!/bin/bash\n"
        "if [ \"${1:-}\" = '-m' ]; then\n"
        "  printf '%s\\n' '{\"schema_name\":\"HydrationCapsuleV1\",\"execution_allowed\":true}'\n"
        "  exit 0\n"
        "fi\n"
        + selection_guard
        + f"exec {shlex.quote(sys.executable)} \"$@\"\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(tmp_path),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(tmp_path),
            "SESSION_HANDOFF_AGENT": "codex-devops",
            "SESSION_EPIC": "devops",
            "THREAD_ROLLOVER_PYTHON": os.fspath(fake_python),
            "SESSION_BOUNDED_RUNNER": os.fspath(REPO_ROOT / "scripts/agent_runtime/bounded_command.py"),
            "CODEX_COMPACT_SESSION_START": "1",
        }
    )
    completed = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        input=json.dumps({"source": "compact", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        cwd=tmp_path.parent,
        env=environment,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "SessionStart"
    legacy = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        input=json.dumps({"hook_event_name": "PostCompact", "model": "claude-sonnet-5"}),
        text=True,
        capture_output=True,
        check=False,
        cwd=tmp_path.parent,
        env={key: value for key, value in environment.items() if key != "CODEX_COMPACT_SESSION_START"},
        timeout=10,
    )
    assert legacy.returncode == 0, legacy.stderr
    legacy_output = json.loads(legacy.stdout)
    assert "hookSpecificOutput" not in legacy_output
    assert legacy_output["additionalContext"] == output["additionalContext"]
    return output["additionalContext"]


def test_bound_codex_driver_hydrates_exact_stream_and_points_to_shadow_diary(
    tmp_path: Path,
) -> None:
    diary = tmp_path / ".claude" / "devops-epic" / "CODEX-DRIVER-HANDOFF.md"
    diary.parent.mkdir(parents=True)
    diary.write_text("# durable driver state\n", encoding="utf-8")
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION" in context
    assert '"schema_name":"HydrationCapsuleV1"' in context
    assert ".claude/devops-epic/CODEX-DRIVER-HANDOFF.md" in context
    assert "continue only from the capsule's next_drive_boundary" in context


def test_lane_goal_file_outranks_capsule_boundary(tmp_path: Path) -> None:
    epic_dir = tmp_path / ".claude" / "devops-epic"
    epic_dir.mkdir(parents=True)
    (epic_dir / "CODEX-DRIVER-HANDOFF.md").write_text("# durable driver state\n", encoding="utf-8")
    (epic_dir / "DRIVER-STATE.md").write_text("# goal\n", encoding="utf-8")
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" not in context
    assert "Lane goal file: .claude/devops-epic/DRIVER-STATE.md." in context
    assert "outranks the capsule's next_drive_boundary" in context
    assert "continue only from the capsule's next_drive_boundary" not in context


def test_first_codex_driver_uses_existing_shared_handoff(
    tmp_path: Path,
) -> None:
    fallback = tmp_path / ".claude" / "devops-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    fallback.parent.mkdir(parents=True)
    fallback.write_text("# shared driver state\n", encoding="utf-8")
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION" in context
    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" not in context
    assert ".claude/devops-epic/CLAUDE-DRIVER-HANDOFF.md" in context


def test_bound_codex_driver_without_any_handoff_blocks(tmp_path: Path) -> None:
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" in context
    assert "No Codex/shared driver handoff selected" in context


def test_shared_handoff_selection_does_not_import_hydration_runtime(tmp_path: Path) -> None:
    fallback = tmp_path / ".claude" / "devops-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    fallback.parent.mkdir(parents=True)
    fallback.write_text("# shared driver state\n", encoding="utf-8")

    context = _run_bound_codex_compact(tmp_path, block_hydration_import=True)

    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" not in context
    assert '\"schema_name\":\"HydrationCapsuleV1\"' in context
    assert ".claude/devops-epic/CLAUDE-DRIVER-HANDOFF.md" in context


def test_codex_tool_events_run_the_policy_and_result_hooks() -> None:
    hooks = _manifest()["hooks"]

    pre_groups = hooks["PreToolUse"]
    assert len(pre_groups) == 1
    assert pre_groups[0]["matcher"] == "^(Bash|Write|Edit|MultiEdit|apply_patch)$"
    assert len(pre_groups[0]["hooks"]) == 1
    pre_hook = pre_groups[0]["hooks"][0]
    from scripts.agent_runtime.agy_hook_config import native_hook_command

    assert pre_hook["command"] == native_hook_command("codex-pre-tool-use")
    assert pre_hook["timeout"] == 45

    post_groups = hooks["PostToolUse"]
    assert len(post_groups) == 1
    assert len(post_groups[0]["hooks"]) == 1
    assert post_groups[0]["hooks"][0]["command"] == native_hook_command("codex-post-tool-use")
    assert hooks["UserPromptSubmit"][0]["hooks"][0]["command"] == native_hook_command("codex-user-prompt-submit")


def test_codex_policy_preserves_tool_scopes_and_per_guard_deadlines() -> None:
    assert ENFORCE_VENV_TIMEOUT == 3
    assert LOCAL_BASH_GUARDS == (
        ("heal-core-bare.py", 3),
        ("guard-branch-switch-in-main.py", 3),
        ("guard-secret-print.py", 5),
    )
    assert PRIMARY_WRITE_GUARD == ("guard-primary-checkout-write.py", 5)
    assert MERGE_GUARDS == (
        ("guard-admin-merge.py", 20),
        ("guard-pr-merge.py", 20),
    )


def test_codex_policy_guard_timeout_fails_closed(tmp_path: Path) -> None:
    guard = tmp_path / "slow_guard.py"
    guard.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")

    result = run_guard(
        Path(project_python()),
        guard,
        "{}",
        timeout_seconds=0.01,
    )

    assert result.returncode == 2
    assert result.timed_out is True
    assert "blocking the tool call fail-closed" in result.stderr


def test_non_rewrite_guard_stdout_fails_closed(
    tmp_path: Path,
    capsys,
) -> None:
    guard = tmp_path / "noisy_guard.py"
    guard.write_text("print('not-json')\n", encoding="utf-8")
    result = run_guard(
        Path(project_python()),
        guard,
        "{}",
        timeout_seconds=1,
    )

    assert _result_code([result]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unexpected stdout" in captured.err
    assert "not-json" in captured.err


def test_codex_policy_venv_guard_timeout_fails_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    guard = tmp_path / "enforce-venv.sh"
    guard.write_text("#!/bin/bash\nsleep 5\n", encoding="utf-8")
    monkeypatch.setattr(codex_hook_policy, "ENFORCE_VENV_TIMEOUT", 0.01)

    result = _run_enforce_venv(tmp_path, tmp_path, "{}")

    assert result.returncode == 2
    assert result.timed_out is True
    assert "enforce-venv.sh exceeded 0.01s" in result.stderr
    assert "blocking the tool call fail-closed" in result.stderr


def test_codex_entry_rejects_bare_python_from_worktree_with_copyable_command(
    tmp_path: Path,
) -> None:
    primary, worktree = _make_linked_worktree(tmp_path)
    assert not (worktree / ".venv").exists()

    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(primary),
        "tool_name": "Bash",
        "tool_input": {
            "command": 'python3 -c "print(1)"',
            "workdir": str(worktree),
        },
    }
    completed = subprocess.run(
        ["bash", str(ENTRY), "pre-tool-use"],
        cwd=worktree,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
        env=_stamp_environment(tmp_path),
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "Unqualified interpreter blocked" in completed.stderr
    assert f'{primary}/.venv/bin/python -c "print(1)"' in completed.stderr


def test_claude_bare_python_is_rejected_without_rewrite_output(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": "python --version"},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical)
    environment.pop("LEARN_UK_HOOK_PROVIDER", None)

    completed = subprocess.run(
        ["bash", str(VENV_HOOK)],
        cwd=REPO_ROOT,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert f"{canonical}/.venv/bin/python --version" in completed.stderr


def test_python_rejection_shell_quotes_checkout_path_metacharacters(tmp_path: Path) -> None:
    canonical = tmp_path / "checkout&pipe|root"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": 'python3 -c "print(1)"'},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical)
    environment["LEARN_UK_HOOK_PROVIDER"] = "codex"

    completed = subprocess.run(
        ["bash", str(VENV_HOOK)],
        cwd=canonical,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert r'checkout\&pipe\|root/.venv/bin/python -c "print(1)"' in completed.stderr


def test_qualified_project_python_passes_without_output(tmp_path: Path) -> None:
    canonical = tmp_path / "checkout"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": ".venv/bin/python --version"},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical)

    completed = subprocess.run(
        ["bash", str(VENV_HOOK)],
        cwd=canonical,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_bare_python_rejection_blocks_a_canonical_version_mismatch(tmp_path: Path) -> None:
    canonical = tmp_path / "checkout"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
    (canonical / ".python-version").write_text("3.12.7\n", encoding="utf-8")
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": "python --version"},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical)
    environment["LEARN_UK_HOOK_PROVIDER"] = "codex"

    completed = subprocess.run(
        ["bash", str(VENV_HOOK)],
        cwd=canonical,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 2
    assert "expected Python 3.12.7" in completed.stderr


def _make_fake_inbox_python(tmp_path: Path) -> tuple[Path, Path]:
    """Create a project interpreter that exposes only the live inbox CLI shape."""
    _run(["git", "init", "-q", "-b", "main"], cwd=tmp_path)
    python = tmp_path / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True, exist_ok=True)
    fixtures = tmp_path / "inbox-fixtures"
    fixtures.mkdir()
    args_log = tmp_path / "inbox-cli-args.log"
    python.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "-I" ]; then shift; fi\n'
        "if [ \"$#\" -ne 5 ] || [ \"$1\" != \"-m\" ] || [ \"$2\" != \"lu_machinery.ai_agent_bridge\" ] || [ \"$3\" != \"inbox\" ] || [ \"$4\" != \"--for\" ]; then\n"
        "  exit 64\n"
        "fi\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_INBOX_ARGS\"\n"
        "cat \"$FAKE_INBOX_FIXTURES/$5.txt\"\n",
        encoding="utf-8",
    )
    python.chmod(0o755)
    return fixtures, args_log


def _write_inbox_fixture(fixtures: Path, recipient: str, preview: str, *, message_id: int = 101) -> None:
    (fixtures / f"{recipient}.txt").write_text(
        f"📬 Inbox for {recipient}: 1 unread | 0 read-but-not-live-consumed | 0 live-consumed\n\n"
        f"  [{message_id}] [unread] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        f"      {preview}\n",
        encoding="utf-8",
    )


def test_inbox_hook_targets_requested_provider(tmp_path: Path) -> None:
    fixtures, args_log = _make_fake_inbox_python(tmp_path)
    _write_inbox_fixture(fixtures, "codex", "codex-only message")
    _write_inbox_fixture(fixtures, "claude", "claude-only message")
    environment = _stamp_environment(tmp_path)
    environment.pop("AB_DB_PATH", None)
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": str(tmp_path),
            "LU_PRODUCT_ROOT": str(tmp_path),
            "LEARN_UKRAINIAN_PYTHON": str(tmp_path / ".venv/bin/python"),
            "LEARN_UK_HOOK_RECIPIENT": "codex",
            "FAKE_INBOX_FIXTURES": str(fixtures),
            "FAKE_INBOX_ARGS": str(args_log),
        }
    )

    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    context = json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 1 unread message" in context
    assert "codex-only message" in context
    assert "claude-only message" not in context
    assert args_log.read_text(encoding="utf-8").strip() == "-m lu_machinery.ai_agent_bridge inbox --for codex"


def test_inbox_dedupes_by_recipient_and_native_session_and_reemits_new_ids(
    tmp_path: Path,
) -> None:
    fixtures, args_log = _make_fake_inbox_python(tmp_path)
    _write_inbox_fixture(fixtures, "codex", "codex-only message")
    _write_inbox_fixture(fixtures, "claude", "claude-only message")
    environment = _stamp_environment(tmp_path)
    environment.pop("AB_DB_PATH", None)
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": str(tmp_path),
            "LU_PRODUCT_ROOT": str(tmp_path),
            "LEARN_UKRAINIAN_PYTHON": str(tmp_path / ".venv/bin/python"),
            "LEARN_UK_HOOK_RECIPIENT": "codex",
            "CODEX_THREAD_ID": "codex-native-session",
            "FAKE_INBOX_FIXTURES": str(fixtures),
            "FAKE_INBOX_ARGS": str(args_log),
        }
    )

    first = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=environment, timeout=10,
    )
    second = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=environment, timeout=10,
    )
    assert first.returncode == second.returncode == 0
    assert "CODEX INBOX: 1 unread message" in first.stdout
    assert second.stdout == ""

    (fixtures / "codex.txt").write_text(
        "📬 Inbox for codex: 2 unread | 0 read-but-not-live-consumed | 0 live-consumed\n\n"
        "  [101] [unread] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        "      codex-only message\n"
        "  [103] [unread] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        "      new codex message\n",
        encoding="utf-8",
    )
    third = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=environment, timeout=10,
    )
    assert third.returncode == 0
    third_context = json.loads(third.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 2 unread message(s)" in third_context
    assert "new codex message" in third_context

    claude_environment = environment | {"LEARN_UK_HOOK_RECIPIENT": "claude"}
    provider_isolation = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=claude_environment, timeout=10,
    )
    assert provider_isolation.returncode == 0
    provider_context = json.loads(provider_isolation.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CLAUDE INBOX: 1 unread message(s)" in provider_context

    new_session_environment = environment | {"CODEX_THREAD_ID": "another-codex-session"}
    session_isolation = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=new_session_environment, timeout=10,
    )
    assert session_isolation.returncode == 0
    session_context = json.loads(session_isolation.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 2 unread message(s)" in session_context
    assert "new codex message" in session_context

    state_files = list((tmp_path / ".agent" / "runtime").glob("inbox-*.ids"))
    assert len(state_files) == 3
    assert all(len(path.stem.removeprefix("inbox-")) == 64 for path in state_files)
    assert all("message" not in path.read_text(encoding="utf-8") for path in state_files)
    assert args_log.read_text(encoding="utf-8").splitlines() == [
        "-m lu_machinery.ai_agent_bridge inbox --for codex",
        "-m lu_machinery.ai_agent_bridge inbox --for codex",
        "-m lu_machinery.ai_agent_bridge inbox --for codex",
        "-m lu_machinery.ai_agent_bridge inbox --for claude",
        "-m lu_machinery.ai_agent_bridge inbox --for codex",
    ]


def _load_pytest_stamp_module():
    """Import the stamp helper by path; it has no package context of its own."""
    import importlib.machinery
    import importlib.util
    import sys

    helper = REPO_ROOT / ".githooks" / "pytest_stamp.py"
    spec = importlib.util.spec_from_loader(
        "pytest_stamp",
        importlib.machinery.SourceFileLoader("pytest_stamp", str(helper)),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _post_tool_use_pytest_payload(worktree: Path, tool_name: str) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "cwd": str(worktree),
        "tool_name": tool_name,
        "tool_input": {
            "command": ".venv/bin/python -m pytest tests/test_example.py -q",
            "workdir": str(worktree),
        },
        "duration_ms": 120,
        "tool_response": {"stdout": "1 passed in 0.10s\n"},
    }


def _stamp_environment(stamps: Path) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    for name in ("LU_PRODUCT_ROOT", "CLAUDE_PROJECT_DIR", "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT", "LEARN_UKRAINIAN_STATE_ROOT", "LEARN_UKRAINIAN_PYTHON"):
        environment.pop(name, None)
    environment["TMPDIR"] = str(stamps)
    return environment


def test_codex_entry_post_tool_use_stamps_bash_pytest_payload(tmp_path: Path) -> None:
    _, worktree = _make_linked_worktree(tmp_path)
    stamps = tmp_path / "stamps"
    stamps.mkdir()
    stamp_module = _load_pytest_stamp_module()
    identity = stamp_module.stamp_identity(worktree)
    assert identity is not None
    marker = stamp_module.marker_path(identity, {"TMPDIR": str(stamps)})

    completed = subprocess.run(
        ["bash", str(ENTRY), "post-tool-use"],
        cwd=worktree,
        input=json.dumps(_post_tool_use_pytest_payload(worktree, "Bash")),
        text=True,
        capture_output=True,
        check=False,
        env=_stamp_environment(stamps),
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert marker.read_text(encoding="utf-8").strip() == identity.key


def test_codex_entry_post_tool_use_skips_stamp_for_non_bash_payload(tmp_path: Path) -> None:
    """pytest_stamp only inspects a Bash command; other tools never invoke it (#8529)."""
    _, worktree = _make_linked_worktree(tmp_path)
    stamps = tmp_path / "stamps"
    stamps.mkdir()
    stamp_module = _load_pytest_stamp_module()
    identity = stamp_module.stamp_identity(worktree)
    assert identity is not None
    marker = stamp_module.marker_path(identity, {"TMPDIR": str(stamps)})

    completed = subprocess.run(
        ["bash", str(ENTRY), "post-tool-use"],
        cwd=worktree,
        input=json.dumps(_post_tool_use_pytest_payload(worktree, "Edit")),
        text=True,
        capture_output=True,
        check=False,
        env=_stamp_environment(stamps),
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert not marker.exists()


def test_compact_hydrate_bound_fits_its_retries() -> None:
    source = (REPO_ROOT / "agents_extensions/shared/hooks/post-compact.sh").read_text(encoding="utf-8")
    assert 'HYDRATION=$(run_bounded 6 "$BOUNDED_PYTHON"' in source
    hooks = json.loads((REPO_ROOT / "agents_extensions/codex/hooks.json").read_text(encoding="utf-8"))
    compact = [
        hook
        for group in hooks["hooks"]["SessionStart"]
        if group.get("matcher") == "compact"
        for hook in group["hooks"]
    ]
    # Selector (2 s) + stream (2 s) + hydrate (6 s) must fit inside the hook timeout.
    assert compact and compact[0]["timeout"] > 2 + 2 + 6


@pytest.mark.parametrize("implementation", ["source", "installed"])
@pytest.mark.parametrize("defect_class", ["S1", "S2", "S3", "S4", "S5", "S6"])
def test_hook_context_prevents_worktree_interpreter_and_missing_root_fail_open(
    tmp_path: Path, implementation: str, defect_class: str,
) -> None:
    """Reject untrusted interpreters, validator drift and missing-root native allow.

    Exercise missing product/state bootstrap separately from transport errors.
    Both layouts use a real primary and linked worktree, genuine secret detection,
    raw deployment and known body-free inbox state.
    """
    from tests.helpers.agy_inbox_fixtures import BODY_MARKER, add_authority, add_legacy

    primary, worktree = _make_linked_worktree(tmp_path)
    # No inherited task, interpreter, product, state or Git context may select a
    # checkout outside this fixture. Native Git created the backlink above.
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(tmp_path),
           "TMPDIR": str(tmp_path), "LANG": "C.UTF-8", "XDG_STATE_HOME": str(tmp_path / "state")}
    hooks_dir = worktree / "agents_extensions/shared/hooks"
    shutil.copytree(REPO_ROOT / "agents_extensions/shared/hooks", hooks_dir)
    marker = worktree / "curriculum/l2-uk-en/curriculum.yaml"
    marker.parent.mkdir(parents=True)
    marker.write_text("levels: []\n")
    if implementation == "source":
        (worktree / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    prefix = "scripts" if implementation == "source" else "lu_machinery"

    def module(name: str, *args: str) -> list[str]:
        if implementation == "source":
            return [str(primary / ".venv/bin/python"), "-I", "-c",
                    f"import sys,runpy; sys.path.insert(0,{str(worktree)!r}); "
                    f"sys.argv[0]={prefix + '.' + name!r}; runpy.run_module({prefix + '.' + name!r},run_name='__main__')",
                    *args]
        return [str(primary / ".venv/bin/python"), "-I", "-m", prefix + "." + name, *args]

    def run(command: list[str], payload: dict | None = None, *, extra: dict | None = None,
            cwd: Path = worktree) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, cwd=cwd, env=env | (extra or {}),
                              input=json.dumps(payload or {}), text=True, capture_output=True, timeout=45)

    def native(mode: str) -> list[str]:
        if implementation == "installed":
            from lu_machinery.agent_runtime.agy_hook_config import native_hook_command
            return ["/bin/bash", "-c", native_hook_command(mode)]
        if mode in {"agy-secret-print", "agy-primary-write"}:
            from scripts.agent_runtime.agy_hook_config import native_hook_command
            return ["/bin/bash", "-c", native_hook_command(mode)]
        if mode.startswith("codex-"):
            return ["/bin/bash", str(ENTRY), mode.removeprefix("codex-")]
        if mode == "agy-pending-orders":
            return ["/bin/bash", str(REPO_ROOT / "scripts/agy_hooks/pending_orders_inject.sh")]
        return ["/bin/bash", str(REPO_ROOT / "scripts/agy_hooks/driver_state_inject.sh"), mode]

    if defect_class == "S1":
        sentinel = tmp_path / "planted-executed"
        planted = worktree / ".venv/bin/python"
        planted.parent.mkdir(parents=True)
        planted.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(sentinel))}\nprintf '%s\\n' '{{\"decision\":\"allow\"}}'\n")
        planted.chmod(0o755)
        commands = [("printf safe", False), ("echo $OPENAI_API_KEY", True)]
        commands.extend(
            (shlex.join([str(primary / ".venv/bin/python"), "-I", "-m", name, "worker-env", "--all"]), True)
            for name in ("lu_machinery.session_supervisor",)
        )
        legacy_worker_env = shlex.join([
            str(primary / ".venv/bin/python"), "-I", "-m", "scripts.session_supervisor", "worker-env", "--all",
        ])
        for root_env in ({}, {"LU_PRODUCT_ROOT": str(worktree)}):
            for text, blocked in [*commands, (legacy_worker_env, True)]:
                payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": text}}}
                result = run(native("agy-secret-print"), payload, extra=root_env)
                assert result.returncode == 0, result.stderr
                answer = json.loads(result.stdout)
                assert answer["decision"] == ("deny" if blocked else "allow"), result
                if blocked:
                    assert "BLOCKED by guard-secret-print" in answer["reason"]
                    assert "unavailable" not in answer["reason"]
            for target, blocked in [(worktree / "README.md", False), (primary / "README.md", True)]:
                payload = {"cwd": str(worktree), "toolCall": {"name": "write_file", "args": {"Path": str(target)}}}
                result = run(native("agy-primary-write"), payload, extra=root_env)
                assert result.returncode == 0, result
                if blocked:
                    answer = json.loads(result.stdout)
                    assert answer["decision"] == "deny" and "worktree" in answer["reason"], result
                    assert "HOOK-BOOTSTRAP-FAILED" not in answer["reason"]
                else:
                    assert result.stdout == "", result
            for text, blocked in commands:
                payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(worktree),
                           "tool_input": {"command": text, "workdir": str(worktree)}}
                result = run(native("codex-pre-tool-use"), payload, extra=root_env)
                assert result.returncode == (2 if blocked else 0), f"{shlex.split(text)[-4:]}: {result}"
                if blocked:
                    assert "BLOCKED by guard-secret-print" in result.stderr
            assert not sentinel.exists(), "a worktree-controlled interpreter executed"
        admin = Path((worktree / ".git").read_text().strip().removeprefix("gitdir: "))
        common = (admin / "commondir").read_text()
        (admin / "commondir").write_text(str(tmp_path / "decoy.git"))
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "printf safe"}}}
        result = run(native("agy-secret-print"), payload)
        assert result.returncode == 0 and json.loads(result.stdout)["decision"] == "allow", result
        assert not sentinel.exists()
        (admin / "commondir").write_text(common)
        backlink = (admin / "gitdir").read_text()
        (admin / "gitdir").write_text(str(primary / ".git"))
        result = run(native("agy-secret-print"), payload)
        assert json.loads(result.stdout)["decision"] == "deny", result
        assert not sentinel.exists()
        (admin / "gitdir").write_text(backlink)
    elif defect_class == "S2":
        raw_overlay = (REPO_ROOT / "agents_extensions/agy/hooks.json").read_bytes()
        overlay = json.loads(raw_overlay)
        product_overlay = worktree / "agents_extensions/agy/hooks.json"
        product_overlay.parent.mkdir(parents=True)
        product_overlay.write_bytes(raw_overlay)
        path = worktree / ".agents/hooks.json"
        path.parent.mkdir()
        path.write_bytes(raw_overlay)
        code = (f"from pathlib import Path; from {prefix}.agent_runtime.agy_hook_config import check_hook_config; "
                f"r=check_hook_config((Path({str(path)!r}),)); print(r.status); raise SystemExit(0 if r.passed else 2)")
        command = module("agent_runtime.agy_hook_config")
        # Evaluate the public API in the same isolated source/installed layout.
        if implementation == "source":
            command = [str(primary / ".venv/bin/python"), "-I", "-c",
                       f"import sys; sys.path.insert(0,{str(worktree)!r}); " + code]
        else:
            command = [str(primary / ".venv/bin/python"), "-I", "-c", code]
        result = run(command)
        assert (result.returncode, result.stdout.strip()) == (0, "PASS"), result
        preflight_code = (f"from pathlib import Path; from {prefix}.agent_runtime.agy_hook_config import require_dispatch_guards; "
                          f"require_dispatch_guards(Path({str(worktree)!r}),Path({str(tmp_path)!r})); print('PASS')")
        if implementation == "source":
            preflight_code = f"import sys; sys.path.insert(0,{str(worktree)!r}); " + preflight_code
        preflight = [str(primary / ".venv/bin/python"), "-I", "-c", preflight_code]
        result = run(preflight)
        assert (result.returncode, result.stdout.strip()) == (0, "PASS"), result
        assert path.read_bytes() == raw_overlay, "startup rewrote the raw deployment"
        original = overlay["shell-secret-print-guard"]["PreToolUse"][0]["hooks"][0]["command"]
        for tampered in [original + " ; true", original.replace("/bin/bash", "/bin/sh", 1),
                         '"/bin/bash" -c "$(printf bypass)" lu-machinery-hook-v1 agy-secret-print']:
            overlay["shell-secret-print-guard"]["PreToolUse"][0]["hooks"][0]["command"] = tampered
            path.write_text(json.dumps(overlay))
            assert run(command).returncode == 2
        overlay["shell-secret-print-guard"]["PreToolUse"][0]["hooks"][0]["command"] = original
        primary_hook = overlay["primary-checkout-write-guard"]["PreToolUse"][0]["hooks"][0]
        primary_hook["command"] += " ; true"
        path.write_text(json.dumps(overlay))
        invalid_overlay = path.read_bytes()
        result = run(preflight)
        assert result.returncode != 0 and "primary_guard_mismatch" in result.stderr, result
        assert path.read_bytes() == invalid_overlay, "startup repaired an invalid existing guard"
    elif defect_class == "S3":
        state = primary / ".claude/infra-epic/DRIVER-STATE.md"
        state.parent.mkdir(parents=True)
        state.write_text("# Driver state: infra\n\n## Epic\n- Stream: infra\n\n## Current goals\n1. fixture\n\n## Next step\n- fixture\n")
        (primary / "batch_state/tasks").mkdir(parents=True)
        extra = {"LU_DRIVER_STATE_FILE": str(state), "SESSION_EPIC": "infra",
                 "SESSION_HANDOFF_AGENT": "gemini-infra", "LU_DRIVER_MIN_WORKERS": "2"}
        payload = {"conversationId": "fixture", "workspacePaths": [str(primary)], "fullyIdle": True}
        for command in [native("agy-stop-hook"), module("driver_state", "agy-stop-hook")]:
            result = run(command, payload, extra=extra)
            assert result.returncode == 0, result.stderr
            answer = json.loads(result.stdout)
            assert answer["decision"] == "continue", result
            assert "BOOTSTRAP" not in answer.get("reason", ""), result
            assert "workers are below" in answer["reason"] and "unknown" not in answer["reason"], result
        for invalid in [{"LEARN_UKRAINIAN_PYTHON": str(tmp_path / "absent")},
                        {"LU_PRODUCT_ROOT": str(tmp_path / "absent")}]:
            result = run(native("agy-stop-hook"), payload, extra=extra | invalid)
            assert json.loads(result.stdout)["decision"] == "continue", result
        ordinary = run(native("agy-stop-hook"), payload)
        assert json.loads(ordinary.stdout) == {"decision": "allow"}, ordinary
        cancelled = run(native("agy-stop-hook"), payload | {"terminationReason": "ERROR"}, extra=extra)
        assert json.loads(cancelled.stdout) == {"decision": "allow"}, cancelled
    elif defect_class == "S4":
        import sqlite3

        from lu_machinery.fleet_comms.migrations import apply_migrations

        # Known populated stores and a registered recipient, not an empty-store
        # unknown result. Registration uses the existing shipped infra roster.
        legacy = tmp_path / "messages.db"
        plane = tmp_path / "plane"
        plane.mkdir()
        with sqlite3.connect(legacy) as connection:
            connection.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY, to_llm TEXT, acknowledged INTEGER, consumed_by_live_driver INTEGER, content TEXT)")
        with sqlite3.connect(plane / "comms.sqlite3") as connection:
            apply_migrations(connection)
        add_legacy(legacy, recipient="gemini-infra")
        add_authority(plane / "comms.sqlite3", recipient="gemini-infra")
        extra = {"AB_DB_PATH": str(legacy), "FLEET_COMMS_ROOT": str(plane),
                 "FLEET_COMMS_ALLOW_LOCAL_SHADOW": "1", "SESSION_HANDOFF_AGENT": "gemini-infra"}
        store_bytes = (legacy.read_bytes(), (plane / "comms.sqlite3").read_bytes())
        result = run(native("agy-pending-orders"), extra=extra)
        assert (legacy.read_bytes(), (plane / "comms.sqlite3").read_bytes()) == store_bytes
        assert result.returncode == 0, result.stderr
        notice = json.loads(result.stdout)["injectSteps"][0]["ephemeralMessage"]
        assert "PENDING ORDERS: 2" in notice and "unknown" not in notice, result
        assert BODY_MARKER not in result.stdout
        writer = worktree / "audit-writer.sh"
        writer.write_text(f"#!/bin/bash\ncd -- {shlex.quote(str(primary))}\nprintf fixture >created-by-call.txt\n")
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(worktree),
                   "session_id": "e3a-fixture", "tool_use_id": "call-1", "tool_input": {"command": "bash audit-writer.sh"}}
        from lu_machinery.common.repo_root import machinery_path
        audit = machinery_path("agents_extensions/shared/hooks/audit-primary-checkout-dirt.py") if implementation == "installed" else REPO_ROOT / "agents_extensions/shared/hooks/audit-primary-checkout-dirt.py"
        before = run([str(primary / ".venv/bin/python"), "-I", str(audit)], payload)
        assert before.returncode == 0, before.stderr
        effect = run(["/bin/bash", "-c", payload["tool_input"]["command"]])
        assert effect.returncode == 0, effect
        payload["hook_event_name"] = "PostToolUse"
        result = run(native("codex-post-tool-use"), payload)
        assert result.returncode == 2, result
        assert "PRIMARY CHECKOUT DIRTIED" in result.stdout + result.stderr
        assert "created-by-call.txt" in result.stdout + result.stderr
        import importlib
        audit_reader = importlib.import_module(prefix + ".guardrails.primary_dirt_audit")
        records = list(audit_reader.iter_records(audit_reader.state_dir(env)))
        assert len(records) == 1
        record = records[0][1]
        assert record["session_id"] == "e3a-fixture"
        assert record["tool_use_id"] == "call-1"
        assert record["command"] == "bash audit-writer.sh"
        assert record["primary_root"] == str(primary)
    elif defect_class == "S5":
        relative = tmp_path / "relative-python"
        sentinel = tmp_path / "relative-executed"
        relative.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(sentinel))}\nexit 0\n")
        relative.chmod(0o755)
        outside = tmp_path / "outside"
        outside.mkdir()
        no_wheel = tmp_path / "no-wheel"
        created = subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(no_wheel)],
                                 text=True, capture_output=True, timeout=30)
        assert created.returncode == 0, created.stderr
        for invalid, cwd in [({"LEARN_UKRAINIAN_PYTHON": "relative-python", "PATH": str(tmp_path) + ":/usr/bin:/bin"}, worktree),
                             ({"LEARN_UKRAINIAN_PYTHON": str(tmp_path / "missing")}, worktree),
                             ({"LU_PRODUCT_ROOT": str(tmp_path / "missing")}, worktree),
                             ({"LEARN_UKRAINIAN_PYTHON": str(no_wheel / "bin/python")}, worktree), ({}, outside)]:
            for mode in ["agy-secret-print", "agy-primary-write", "agy-pretool-hook", "codex-pre-tool-use"]:
                # The generated boundary validates interpreter selection before
                # Python starts; source generation must carry identical bytes.
                if implementation == "source":
                    from scripts.agent_runtime.agy_hook_config import native_hook_command as writer
                else:
                    from lu_machinery.agent_runtime.agy_hook_config import native_hook_command as writer
                result = run(["/bin/bash", "-c", writer(mode)], extra=invalid, cwd=cwd)
                if mode.startswith("agy-"):
                    assert result.returncode == 0 and json.loads(result.stdout)["decision"] == "deny", result
                else:
                    assert result.returncode == 2 and result.stdout == "", result
                assert "HOOK-BOOTSTRAP-FAILED" in result.stderr
        assert not sentinel.exists(), "relative interpreter was looked up through PATH"
    else:
        tests = worktree / "tests"
        tests.mkdir()
        target = tests / "existing_target.py"
        target.write_text("VALUE = 1\n")
        code = (f"from pathlib import Path; from {prefix}.ci.pytest_dispatch_cap import path_covers_full_suite; "
                "print(path_covers_full_suite('tests/existing_target.py',invocation_dir=Path.cwd())); "
                "print(path_covers_full_suite('tests',invocation_dir=Path.cwd()))")
        command = [str(primary / ".venv/bin/python"), "-I", "-c", code]
        if implementation == "source":
            command[-1] = f"import sys; sys.path.insert(0,{str(worktree)!r}); " + code
        result = run(command)
        assert result.returncode == 0 and result.stdout.splitlines() == ["False", "True"], result
        collect = [str(primary / ".venv/bin/python"), "-I", "-m", "pytest"]
        if implementation == "source":
            collect = [str(primary / ".venv/bin/python"), "-I", "-c",
                       f"import sys,runpy; sys.path.insert(0,{str(worktree)!r}); runpy.run_module('pytest',run_name='__main__')"]
        result = run([*collect, "--collect-only", "--noconftest",
                      "-p", prefix + ".ci.pytest_dispatch_cap", str(target)],
                     extra={"LEARN_UKRAINIAN_DISPATCH_TASK_ID": "fixture-worker"})
        assert result.returncode == 5 and "no tests collected" in result.stdout, result
        outside = tmp_path / "outside"
        outside.mkdir()
        refusal = code.replace("print(path_covers_full_suite('tests/existing_target.py',invocation_dir=Path.cwd())); ", "")
        refusal = refusal.replace("print(path_covers_full_suite", "import os; os.environ.pop('LU_PRODUCT_ROOT',None); os.environ.pop('LEARN_UKRAINIAN_PRIMARY_REPO_ROOT',None); print(path_covers_full_suite", 1)
        command[-1] = (f"import sys; sys.path.insert(0,{str(worktree)!r}); " if implementation == "source" else "") + refusal
        result = run(command, cwd=outside)
        assert result.returncode != 0 and "no product checkout" in result.stderr, result
        assert "ProductRootError" not in result.stderr, result
