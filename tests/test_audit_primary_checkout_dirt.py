"""Primary-checkout dirt audit (#11253): detect, attribute and clean script writes.

``guard-primary-checkout-write.py`` reads only the text of a Bash command, so a
launched script that ``cd``s into the primary checkout and redirects to a
relative path writes there unseen. The audit hook snapshots the primary
checkout's ``git status`` before and after every shell call and attributes any
new entry to the call; ``scripts.hygiene.primary_dirt_cleanup`` removes exactly
the untracked files an attribution record proves a session created.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.guardrails import primary_dirt_audit as audit
from scripts.hygiene import primary_dirt_cleanup as cleanup

REPO = Path(__file__).resolve().parent.parent
HOOKS = REPO / "agents_extensions/shared/hooks"
GUARD = HOOKS / "guard-primary-checkout-write.py"
AUDIT = HOOKS / "audit-primary-checkout-dirt.py"
SETTINGS = REPO / "agents_extensions/shared/settings.json"
CODEX_ENTRY = REPO / "scripts/agent_runtime/codex_hook_entry.sh"
CODEX_POLICY = REPO / "scripts/agent_runtime/codex_hook_policy.py"
DEPLOYED_AUDIT = "$CLAUDE_PROJECT_DIR/.claude/hooks/audit-primary-checkout-dirt.py"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, timeout=30).stdout


def _make_primary(tmp_path: Path) -> Path:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "config", "user.email", "t@example.invalid")
    _git(primary, "config", "user.name", "t")
    (primary / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    (primary / ".gitignore").write_text("ignored/\n*.log\n", encoding="utf-8")
    _git(primary, "add", "tracked.txt", ".gitignore")
    _git(primary, "commit", "-q", "-m", "init")
    return primary


def _env(tmp_path: Path, primary: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["XDG_STATE_HOME"] = str(tmp_path / "state")
    env["CLAUDE_PROJECT_DIR"] = str(primary)
    return env


def _state(tmp_path: Path) -> Path:
    return audit.state_dir({"XDG_STATE_HOME": str(tmp_path / "state")})


def _payload(
    event: str, command: str, cwd: Path, *, session: str = "sess-a", tool_use: str = "toolu_1", **extra
) -> str:
    return json.dumps(
        {
            "hook_event_name": event,
            "session_id": session,
            "tool_use_id": tool_use,
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(cwd),
            **extra,
        }
    )


def _hook(hook: Path, payload: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(hook)], input=payload, capture_output=True, text=True, env=env, check=False, timeout=60
    )


def _run_bash(command: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", command], cwd=cwd, capture_output=True, text=True, env=env, check=False, timeout=60
    )


def _script(scratch: Path, body: str, name: str = "job.sh") -> Path:
    scratch.mkdir(exist_ok=True)
    script = scratch / name
    script.write_text("#!/bin/bash\n" + body, encoding="utf-8")
    return script


def _call(
    tmp_path: Path,
    primary: Path,
    command: str,
    *,
    session: str = "sess-a",
    tool_use: str = "toolu_1",
    post_event: str = "PostToolUse",
) -> subprocess.CompletedProcess[str]:
    """One shell tool call wrapped by the audit hook, as the harness runs it."""
    scratch = tmp_path / "scratch"
    scratch.mkdir(exist_ok=True)
    env = _env(tmp_path, primary)
    pre = _hook(AUDIT, _payload("PreToolUse", command, scratch, session=session, tool_use=tool_use), env)
    assert pre.returncode == 0 and not pre.stdout and not pre.stderr, pre
    _run_bash(command, scratch, env)
    return _hook(AUDIT, _payload(post_event, command, scratch, session=session, tool_use=tool_use), env)


def _records(tmp_path: Path, session: str = "sess-a") -> list[dict]:
    return [record for _, record in audit.iter_records(_state(tmp_path)) if record["session_id"] == session]


def _write_in_primary(tmp_path: Path, relpath: str, body: str = "x") -> str:
    """A launched script that cds into the primary (its first argument) and writes relatively."""
    script = _script(tmp_path / "scratch", f'cd "$1" || exit 1\nprintf %s {shlex.quote(body)} > {relpath}\n')
    return f"bash {script} {tmp_path / 'primary'}"


def _cleanup_cli(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.hygiene.primary_dirt_cleanup", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=60,
    )


def _outcomes(report: dict) -> dict[str, str]:
    return {result["path"]: result["outcome"] for result in report["results"]}


# ---------------------------------------------------------------------------
# AC-01 / AC-02: detection and attribution
# ---------------------------------------------------------------------------


def test_ac01_script_relative_write_after_cd_is_detected_and_attributed(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    scratch = tmp_path / "scratch"
    script = _script(
        scratch,
        'cd "$1" || exit 1\nbrief="$2"\nsed "s/@@HEAD@@/abc/g" "$brief" > "$brief.resolved"\n',
        name="refresh-and-push.sh",
    )
    env = _env(tmp_path, primary)
    command = f"bash {script} {primary} brief-review-10952.tmpl"

    # The static guard cannot see the redirect executed inside the script.
    guard = _hook(GUARD, _payload("PreToolUse", command, scratch), env)
    assert guard.returncode == 0, guard.stderr

    pre = _hook(AUDIT, _payload("PreToolUse", command, scratch), env)
    assert pre.returncode == 0, pre.stderr
    ran = _run_bash(command, scratch, env)
    assert ran.returncode != 0  # sed fails on the missing relative brief ...
    assert (primary / "brief-review-10952.tmpl.resolved").exists()  # ... but the redirect wrote

    # Claude routes a non-zero Bash exit to PostToolUseFailure.
    post = _hook(AUDIT, _payload("PostToolUseFailure", command, scratch), env)
    assert post.returncode == 2, post.stderr
    assert "?? brief-review-10952.tmpl.resolved" in post.stderr
    assert f"command: {command}" in post.stderr
    (record,) = _records(tmp_path)
    assert record["command"] == command and record["tool_use_id"] == "toolu_1"
    assert [entry["path"] for entry in record["entries"]] == ["brief-review-10952.tmpl.resolved"]
    assert record["record_id"] in post.stderr

    # AC-03: the printed command clears exactly this file, without any override.
    (line,) = [text for text in post.stderr.splitlines() if "scripts.hygiene.primary_dirt_cleanup" in text]
    argv = shlex.split(line.replace("[--apply]", ""))
    assert argv[:3] == [".venv/bin/python", "-m", "scripts.hygiene.primary_dirt_cleanup"]
    dry = _cleanup_cli(*argv[3:], env=env)
    assert dry.returncode == 0, dry.stdout
    assert _outcomes(json.loads(dry.stdout)) == {"brief-review-10952.tmpl.resolved": "removable"}
    assert (primary / "brief-review-10952.tmpl.resolved").exists()
    applied = _cleanup_cli(*argv[3:], "--apply", env=env)
    assert applied.returncode == 0, applied.stdout
    assert _outcomes(json.loads(applied.stdout)) == {"brief-review-10952.tmpl.resolved": "removed"}
    assert _git(primary, "status", "--porcelain", "--untracked-files=all") == ""
    receipts = (_state(tmp_path) / "cleanup.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["outcome"] for line in receipts] == ["removed"]


def test_absolute_path_write_built_at_run_time_is_attributed(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    script = _script(tmp_path / "scratch", 'target="$1/run-time"\nmkdir -p "$target"\necho x > "$target/abs.txt"\n')
    post = _call(tmp_path, primary, f"bash {script} {primary}")
    assert post.returncode == 2, post.stderr
    assert "?? run-time/abs.txt" in post.stderr


def test_git_ignored_writes_do_not_trigger(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    script = _script(tmp_path / "scratch", 'cd "$1"\nmkdir -p ignored\necho x > ignored/state.json\necho y > run.log\n')
    post = _call(tmp_path, primary, f"bash {script} {primary}")
    assert (primary / "ignored/state.json").exists() and (primary / "run.log").exists()
    assert post.returncode == 0 and post.stderr == ""
    assert _records(tmp_path) == []


def test_clean_call_is_silent_and_consumes_its_snapshot(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    post = _call(tmp_path, primary, "true")
    assert post.returncode == 0 and post.stderr == "" and post.stdout == ""
    assert list((_state(tmp_path) / "snapshots").iterdir()) == []


def test_pre_existing_dirt_is_never_attributed(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    (primary / "old.txt").write_text("operator scratch\n", encoding="utf-8")
    (primary / "tracked.txt").write_text("operator edit\n", encoding="utf-8")
    script = _script(
        tmp_path / "scratch", 'cd "$1"\necho more >> old.txt\necho more >> tracked.txt\necho new > new.txt\n'
    )
    post = _call(tmp_path, primary, f"bash {script} {primary}")
    assert post.returncode == 2
    assert "?? new.txt" in post.stderr
    assert "old.txt" not in post.stderr and "tracked.txt" not in post.stderr
    (record,) = _records(tmp_path)
    assert [entry["path"] for entry in record["entries"]] == ["new.txt"]

    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_OK and _outcomes(report) == {"new.txt": "removed"}
    assert (primary / "old.txt").read_text(encoding="utf-8") == "operator scratch\nmore\n"
    assert _git(primary, "status", "--porcelain").splitlines() == [" M tracked.txt", "?? old.txt"]


def test_tracked_modification_is_attributed_but_never_removed(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    post = _call(tmp_path, primary, _write_in_primary(tmp_path, "tracked.txt", "agent edit"))
    assert post.returncode == 2
    assert " M tracked.txt" in post.stderr and "Tracked changes are not removed" in post.stderr
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED
    assert _outcomes(report) == {"tracked.txt": "refused:tracked_entry"}
    assert (primary / "tracked.txt").read_text(encoding="utf-8") == "agent edit"


def test_snapshot_never_rewrites_the_primary_index(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    index = primary / ".git" / "index"
    # A stat-only change makes the index entry stale, so a plain `git status`
    # would refresh it and rewrite the index under an optional lock.
    stamp = time.time() + 5
    os.utime(primary / "tracked.txt", (stamp, stamp))
    before = (index.stat().st_mtime_ns, hashlib.sha256(index.read_bytes()).hexdigest())

    post = _call(tmp_path, primary, "true")
    assert post.returncode == 0, post.stderr
    assert (index.stat().st_mtime_ns, hashlib.sha256(index.read_bytes()).hexdigest()) == before

    # Control: the same status without GIT_OPTIONAL_LOCKS=0 does rewrite it.
    _git(primary, "status", "--porcelain")
    assert hashlib.sha256(index.read_bytes()).hexdigest() != before[1]


def test_missing_pre_snapshot_reports_the_call_as_unaudited(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    (primary / "stray.txt").write_text("x", encoding="utf-8")
    post = _hook(AUDIT, _payload("PostToolUse", "true", tmp_path), _env(tmp_path, primary))
    assert post.returncode == 1
    assert "pre-call snapshot missing" in post.stderr
    assert _records(tmp_path) == []


@pytest.mark.parametrize(
    "overrides",
    [{"tool_name": "Write"}, {"tool_use_id": ""}, {"session_id": None}, {"hook_event_name": "Stop"}],
)
def test_non_shell_or_unkeyed_payloads_are_ignored(tmp_path: Path, overrides: dict) -> None:
    primary = _make_primary(tmp_path)
    payload = {**json.loads(_payload("PreToolUse", "true", tmp_path)), **overrides}
    pre = _hook(AUDIT, json.dumps(payload), _env(tmp_path, primary))
    assert pre.returncode == 0 and pre.stderr == ""
    assert not (_state(tmp_path) / "snapshots").exists()


def test_stale_snapshots_are_collected(tmp_path: Path) -> None:
    state = _state(tmp_path)
    snapshots = state / "snapshots"
    snapshots.mkdir(parents=True)
    stale, fresh = snapshots / "stale.json", snapshots / "fresh.json"
    stale.write_text("{}", encoding="utf-8")
    fresh.write_text("{}", encoding="utf-8")
    old = time.time() - audit.SNAPSHOT_TTL_S - 60
    os.utime(stale, (old, old))
    assert audit.collect_stale_snapshots(state) == 1
    assert not stale.exists() and fresh.exists()


def test_overlapping_calls_both_record_the_new_path(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    env = _env(tmp_path, primary)
    command = _write_in_primary(tmp_path, "shared.txt")
    for session in ("sess-a", "sess-b"):
        _hook(AUDIT, _payload("PreToolUse", command, tmp_path, session=session), env)
    _run_bash(command, tmp_path, env)
    for session in ("sess-a", "sess-b"):
        post = _hook(AUDIT, _payload("PostToolUse", command, tmp_path, session=session), env)
        assert post.returncode == 2 and "?? shared.txt" in post.stderr
    assert len(_records(tmp_path, "sess-a")) == len(_records(tmp_path, "sess-b")) == 1


# ---------------------------------------------------------------------------
# AC-03: the cleanup scope rule
# ---------------------------------------------------------------------------


def test_cleanup_without_a_record_removes_nothing(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    assert _call(tmp_path, primary, _write_in_primary(tmp_path, "mine.txt")).returncode == 2
    state = _state(tmp_path)
    for session, records in (("sess-nobody", []), ("sess-a", ["no-such-record"])):
        code, report = cleanup.run(state, session, records, apply=True)
        assert code == cleanup.EXIT_NO_RECORD and report["error"] == "no_attribution_record"
    assert (primary / "mine.txt").exists()


def test_cleanup_refuses_another_sessions_record(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    assert _call(tmp_path, primary, _write_in_primary(tmp_path, "mine.txt"), session="sess-a").returncode == 2
    (record,) = _records(tmp_path, "sess-a")
    code, _ = cleanup.run(_state(tmp_path), "sess-b", [record["record_id"]], apply=True)
    assert code == cleanup.EXIT_NO_RECORD
    assert (primary / "mine.txt").exists()


def test_cleanup_refuses_a_file_another_session_also_claims(tmp_path: Path) -> None:
    test_overlapping_calls_both_record_the_new_path(tmp_path)
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED
    assert _outcomes(report) == {"shared.txt": "refused:claimed_by_other_session"}
    assert (tmp_path / "primary" / "shared.txt").exists()


def test_cleanup_refuses_a_session_mismatch_inside_its_own_record_directory(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    assert _call(tmp_path, primary, _write_in_primary(tmp_path, "mine.txt")).returncode == 2
    ((path, record),) = list(audit.iter_records(_state(tmp_path)))
    path.write_text(json.dumps({**record, "session_id": "sess-other"}), encoding="utf-8")
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED and _outcomes(report) == {"mine.txt": "refused:session_mismatch"}
    assert (primary / "mine.txt").exists()


@pytest.mark.parametrize("change", ["append", "same_size_same_mtime"])
def test_cleanup_refuses_a_file_modified_after_attribution(tmp_path: Path, change: str) -> None:
    primary = _make_primary(tmp_path)
    assert _call(tmp_path, primary, _write_in_primary(tmp_path, "mine.txt", "agent")).returncode == 2
    target = primary / "mine.txt"
    info = target.stat()
    if change == "append":
        target.write_text("agent + operator", encoding="utf-8")
    else:
        target.write_text("OTHER", encoding="utf-8")
        os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns))
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED and _outcomes(report) == {"mine.txt": "refused:modified_since_attribution"}
    assert target.exists()


def test_cleanup_refuses_a_file_that_became_tracked(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    assert _call(tmp_path, primary, _write_in_primary(tmp_path, "mine.txt")).returncode == 2
    _git(primary, "add", "mine.txt")
    _git(primary, "commit", "-q", "-m", "adopt")
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED and _outcomes(report) == {"mine.txt": "refused:tracked"}
    assert (primary / "mine.txt").exists()


def _forge_entry(tmp_path: Path, relpath: str, fingerprint: dict, **record_overrides) -> None:
    """Rewrite the session's only record to claim ``relpath`` with ``fingerprint``."""
    ((path, record),) = list(audit.iter_records(_state(tmp_path)))
    entry = {"path": relpath, "xy": "??", "kind": "untracked", "fingerprint": fingerprint}
    path.write_text(json.dumps({**record, "entries": [entry], **record_overrides}), encoding="utf-8")


def _outside_victim(tmp_path: Path) -> tuple[Path, dict]:
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.txt"
    victim.write_text("not yours\n", encoding="utf-8")
    fingerprint = audit.fingerprint(outside, "victim.txt")
    assert fingerprint and fingerprint["kind"] == "file" and fingerprint["sha256"]
    return victim, fingerprint


def test_cleanup_refuses_a_symlinked_directory_escape(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    victim, fingerprint = _outside_victim(tmp_path)
    command = f"ln -s {victim.parent} {primary}/link"
    assert _call(tmp_path, primary, command).returncode == 2
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert _outcomes(report) == {"link": "refused:not_a_fingerprinted_regular_file"}
    _forge_entry(tmp_path, "link/victim.txt", fingerprint)
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED
    assert _outcomes(report) == {"link/victim.txt": "refused:symlink_or_non_directory_in_path"}
    assert victim.exists() and (primary / "link").is_symlink()


def test_cleanup_refuses_a_final_component_symlink(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    victim, fingerprint = _outside_victim(tmp_path)
    assert _call(tmp_path, primary, f"ln -s {victim} {primary}/alias").returncode == 2
    _forge_entry(tmp_path, "alias", fingerprint)
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED and _outcomes(report) == {"alias": "refused:symlink"}
    assert victim.exists() and (primary / "alias").is_symlink()


@pytest.mark.parametrize("relpath", ["../outside/victim.txt", "/abs/victim.txt", ".git/config", "a//b", ""])
def test_cleanup_refuses_paths_that_could_leave_the_root(tmp_path: Path, relpath: str) -> None:
    primary = _make_primary(tmp_path)
    victim, fingerprint = _outside_victim(tmp_path)
    assert _call(tmp_path, primary, _write_in_primary(tmp_path, "mine.txt")).returncode == 2
    _forge_entry(tmp_path, relpath, fingerprint)
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED and _outcomes(report) == {relpath: "refused:invalid_path"}
    assert victim.exists() and (primary / ".git/config").exists()


def test_cleanup_refuses_a_record_whose_root_is_not_the_primary(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    victim, fingerprint = _outside_victim(tmp_path)
    assert _call(tmp_path, primary, _write_in_primary(tmp_path, "mine.txt")).returncode == 2
    _forge_entry(tmp_path, "victim.txt", fingerprint, primary_root=str(victim.parent))
    code, report = cleanup.run(_state(tmp_path), "sess-a", [], apply=True)
    assert code == cleanup.EXIT_REFUSED and _outcomes(report) == {"victim.txt": "refused:primary_root_invalid"}
    assert victim.exists()


def test_cleanup_help_meets_the_cli_standard() -> None:
    completed = _cleanup_cli("--help", env=dict(os.environ))
    assert completed.returncode == 0
    for text in ("--session", "--record", "--apply", "Exit codes:", "Outputs:", "Related:", "#11253"):
        assert text in completed.stdout


# ---------------------------------------------------------------------------
# wiring: Claude settings, Claude workers, Codex policy and entry
# ---------------------------------------------------------------------------


def test_claude_settings_wire_the_audit_around_every_bash_call() -> None:
    hooks = json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"]
    for event in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        wired = [
            (group.get("matcher"), hook)
            for group in hooks[event]
            for hook in group["hooks"]
            if hook["command"] == DEPLOYED_AUDIT
        ]
        assert [matcher for matcher, _ in wired] == ["Bash"], event
        (_, hook) = wired[0]
        # Observational: a failing audit must never refuse or stall a call.
        assert "onFailure" not in hook and not hook.get("async") and hook["timeout"] >= 10


def test_claude_workers_do_not_get_an_unpaired_snapshot() -> None:
    from scripts.agent_runtime.adapters import claude

    settings = json.loads(claude._worker_guard_settings())
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert commands and not any("audit-primary-checkout-dirt" in command for command in commands)
    assert any(command.endswith("guard-primary-checkout-write.py") for command in commands)


def _stub_hooks(tmp_path: Path, refusing: str | None) -> tuple[Path, Path]:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    marker = tmp_path / "snapshot-ran"
    names = [
        "heal-core-bare.py",
        "guard-branch-switch-in-main.py",
        "guard-secret-print.py",
        "guard-primary-checkout-write.py",
        "guard-admin-merge.py",
        "guard-pr-merge.py",
    ]
    for name in names:
        (hooks / name).write_text(f"import sys\nsys.exit({2 if name == refusing else 0})\n", encoding="utf-8")
    (hooks / "enforce-venv.sh").write_text("exit 0\n", encoding="utf-8")
    (hooks / "audit-primary-checkout-dirt.py").write_text(
        f"import sys\nopen({str(marker)!r}, 'w').write(sys.stdin.read())\nprint('stdout must not leak')\n",
        encoding="utf-8",
    )
    return hooks, marker


@pytest.mark.parametrize("refusing", [None, "guard-primary-checkout-write.py", "guard-pr-merge.py"])
def test_codex_policy_snapshots_only_calls_every_guard_allowed(tmp_path: Path, refusing: str | None) -> None:
    hooks, marker = _stub_hooks(tmp_path, refusing)
    payload = _payload("PreToolUse", "true", tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(CODEX_POLICY),
            "--python-bin",
            sys.executable,
            "--hooks-dir",
            str(hooks),
            "--canonical-root",
            str(REPO),
        ],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if refusing is None:
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout == ""
        assert json.loads(marker.read_text(encoding="utf-8")) == json.loads(payload)
    else:
        assert completed.returncode == 2
        assert not marker.exists()


def test_codex_entry_post_tool_use_reports_attributed_dirt(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    env = _env(tmp_path, primary)
    command = _write_in_primary(tmp_path, "codex.txt")
    pre = _hook(AUDIT, _payload("PreToolUse", command, tmp_path, turn_id="t1"), env)
    assert pre.returncode == 0
    _run_bash(command, tmp_path, env)
    completed = subprocess.run(
        ["bash", str(CODEX_ENTRY), "post-tool-use"],
        cwd=tmp_path,
        input=_payload("PostToolUse", command, tmp_path, turn_id="t1", tool_response={"exit_code": 0}),
        capture_output=True,
        text=True,
        env={**env, "TMPDIR": str(tmp_path)},
        check=False,
        timeout=60,
    )
    assert completed.returncode == 2, completed.stderr
    assert "?? codex.txt" in completed.stderr and "scripts.hygiene.primary_dirt_cleanup" in completed.stderr
