"""Offline walkthrough for detached formal review (#9663).

Actual dispatch stdout and task-record producer evidence is covered by
tests/test_delegate.py::test_dispatch_generates_and_persists_run_nonce.
"""

from __future__ import annotations

import io
import json
import os
import re
import shlex
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from scripts import delegate
from scripts.ai_agent_bridge import _cli
from scripts.ai_agent_bridge import _dispatch_wrappers as wrappers
from scripts.review import record_cf_verdict as recorder

REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "agents_extensions/shared/skills/drive-epic/references/review-merge-cleanup.md"
)
HEAD = "a" * 40
NONCE = "run-nonce-fixture"


def _canonical_review_asks():
    """Extract executable ask recipes across the original shared instruction scope."""
    shared = REFERENCE.parents[3]
    recipes = []
    for root in (shared / "skills", shared / "rules"):
        for path in sorted(root.rglob("*.md")):
            body = path.read_text(encoding="utf-8")
            for block in re.findall(r"^```[^\n]*\n(.*?)^```", body, re.M | re.S):
                for line in block.replace("\\\n", " ").splitlines():
                    if "scripts/ai_agent_bridge/__main__.py ask-" not in line:
                        continue
                    command = line.split("scripts/ai_agent_bridge/__main__.py ", 1)[1]
                    argv = shlex.split(command.replace("ask-<lane>", "ask-claude"))
                    if "--review" in argv or ("--type" in argv and argv[argv.index("--type") + 1] == "review"):
                        recipes.append(pytest.param(argv, id=str(path.relative_to(shared))))
    assert recipes, "canonical formal-review launch inventory must not be empty"
    return recipes


@pytest.mark.parametrize("argv", _canonical_review_asks())
def test_canonical_review_ask_recipes_reach_branch_pin_admission(argv, monkeypatch, tmp_path, capsys):
    """Exercise parser → handler → wrapper → delegate admission, with real Git targets."""
    from tests.test_authoring_review_feasibility import SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    head = repo.commit(SOL)
    repo.publish()
    monkeypatch.setattr(delegate, "_local_repo_root", repo.root)
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    argv = ["feature" if arg == "<branch>" else arg for arg in argv]
    args = _cli._build_parser().parse_args(argv)
    assert args.branch == "feature", "formal review must target the pushed author branch"
    assert args.pr is None
    monkeypatch.setattr(_cli, "require_core_or_exit", lambda _name: None)
    monkeypatch.setattr(_cli.sys, "stdin", io.StringIO("Review the pushed branch."))

    @contextmanager
    def prompt_directory():
        yield tmp_path

    monkeypatch.setattr(wrappers, "_prompt_directory", prompt_directory)
    real_run = subprocess.run
    commands = []
    reply = tmp_path / "review.result"
    reply.write_text("VERDICT: APPROVE\n", encoding="utf-8")

    def native_boundary(command, **kwargs):
        if "scripts/delegate.py" not in command:
            return real_run(command, **kwargs)
        commands.append(command)
        if "dispatch" in command:
            launch = delegate.build_parser().parse_args(command[2:])
            # The wrapper passes no explicit branch pin; the real admission
            # callback must set it before reviewer route evaluation.
            assert launch.pinned_head is None
            refusal, target = delegate._admit_dispatch_target(launch, agent=launch.agent, trees=None)
            assert refusal is None and target is not None
            assert launch.pinned_head == launch._review_target.head_sha == head
            base = delegate._resolve_worktree_base_sha(
                agent=launch.agent,
                task_id=launch.task_id,
                base="main",
                branch="feature",
                pinned_head_sha=launch.pinned_head,
                validated_path=tmp_path / "checkout",
            )
            assert base == head
            # The remote moves AFTER admission while the tracking ref is old.
            # Actual checkout preparation fetches and refuses the new SHA.
            repo.advance_remote("feature", SOL)
            with pytest.raises(RuntimeError, match="differs from the pinned head SHA"):
                delegate._resolve_worktree_base_sha(
                    agent=launch.agent,
                    task_id=launch.task_id,
                    base="main",
                    branch="feature",
                    pinned_head_sha=launch.pinned_head,
                    validated_path=tmp_path / "checkout",
                )
            return subprocess.CompletedProcess(command, 0, f"{launch.task_id}\n{NONCE}\n", "")
        assert "wait" in command and "--run-nonce" not in command
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(
                {
                    "status": "done",
                    "result_file": str(reply),
                    "worktree_base_sha": head,
                }
            ),
            "",
        )

    monkeypatch.setattr(wrappers.subprocess, "run", native_boundary)
    _cli._handle_acp_compat(args, "claude")
    assert len(commands) == 2
    assert capsys.readouterr().out.strip() == "VERDICT: APPROVE"  # reply, not SHA


def test_detached_exact_head_review_launch_settle_and_publication_guards(monkeypatch, tmp_path, capsys):
    """Retired ask background fails; native dispatch settles by nonce and rejects bad evidence."""
    # Reproduce the formerly documented command through the real ask parser and
    # handler. Refusal occurs before any provider, task, or GitHub boundary.
    ask = _cli._build_parser().parse_args(["ask-codex", "-", "--task-id", "review-fixture", "--background"])
    monkeypatch.setattr(_cli, "require_core_or_exit", lambda _name: None)
    with pytest.raises(SystemExit, match="legacy ask --background is retired"):
        _cli._handle_acp_compat(ask, "codex")
    reference = REFERENCE.read_text(encoding="utf-8")
    assert "`--background` flag is rejected" in reference
    assert "requires_silence_timeout" in reference
    assert "Only terminal task-record" in reference

    # Parse the documented producer with delegate's real CLI. Its public
    # contract is detached dispatch. Task fixtures below exercise settlement,
    # not production: run the actual cmd_dispatch nonce-producer test separately.
    launch = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "claude",
            "--model",
            "claude-opus-5-5",
            "--effort",
            "high",
            "--mode",
            "read-only",
            "--worktree",
            "--task-id",
            "review-fixture",
            "--prompt-file",
            str(tmp_path / "review.md"),
            "--branch",
            "codex/author",
            "--pinned-head",
            HEAD,
            "--require-review-verdict",
            "--review-profile",
            "code",
            "--review-author-model",
            "gpt-6.1-sol",
            "--review-risk",
            "medium",
        ]
    )
    assert launch.func is delegate.cmd_dispatch
    assert launch.agent == "claude"
    assert launch.mode == "read-only"
    assert launch.worktree == "auto"
    assert launch.branch == "codex/author"
    assert launch.pinned_head == HEAD
    assert launch.require_review_verdict
    assert launch.review_profile == "code"
    assert launch.review_author_model == "gpt-6.1-sol"
    assert launch.review_risk == "medium"

    task_root = tmp_path / "tasks"
    task_root.mkdir()
    task_path = task_root / "review-fixture.json"
    task = {
        "task_id": "review-fixture",
        "run_nonce": NONCE,
        "status": "running",
        "agent": "claude",
        "model": "claude-opus-5-5",
        "worktree_branch": "codex/author",
        "worktree_base_sha": HEAD,
        "repository": "owner/repo",
        "started_at": "2026-10-08T00:00:00+00:00",
    }
    task_path.write_text(json.dumps(task), encoding="utf-8")
    (task_root / "review-fixture.result").write_text("VERDICT: APPROVE\n", encoding="utf-8")
    # The existing producer regression runs cmd_dispatch --dry-run and checks
    # its actual two-line task-id/run-nonce stdout against the persisted record.
    review_task, review_nonce = "review-fixture", NONCE
    assert json.loads(task_path.read_text(encoding="utf-8"))["status"] == "running"

    # A client wait deadline can expire while task state remains running. Its
    # 124 result is not settlement; re-arm the same parsed wait/nonce.
    wait = delegate.build_parser().parse_args(["wait", review_task, "--run-nonce", review_nonce, "--timeout", "1"])
    assert wait.run_nonce == NONCE
    assert wait.func is delegate.cmd_wait

    def read_task(_task_id):
        return task_path, json.loads(task_path.read_text(encoding="utf-8"))

    clock = [0.0]
    monkeypatch.setattr(delegate.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(delegate, "_read_state_or_archived", read_task)
    monkeypatch.setattr(delegate, "_heal_dead_task", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: clock.__setitem__(0, 2.0))
    assert delegate.cmd_wait(wait) == 124
    expired = json.loads(capsys.readouterr().err)
    assert expired["last_known_status"] == "running"
    assert json.loads(task_path.read_text(encoding="utf-8"))["run_nonce"] == review_nonce

    # Re-arm the same task/run nonce; the worker fixture now reaches terminal
    # done, after which the task record and actual reply can be checked.
    wait.timeout = 10
    clock[0] = 0.0

    def settle(_seconds):
        current = json.loads(task_path.read_text(encoding="utf-8"))
        current["status"] = "done"
        current["result_file"] = str(task_root / "review-fixture.result")
        current["resolved_model"] = "claude-opus-5-5"
        task_path.write_text(json.dumps(current), encoding="utf-8")

    monkeypatch.setattr(delegate.time, "sleep", settle)
    assert delegate.cmd_wait(wait) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "done"

    completed, reply = recorder._task(review_task, task_root)
    assert completed["run_nonce"] == review_nonce
    assert completed["resolved_model"] == "claude-opus-5-5"
    assert recorder.normalize_verdict(reply) == "APPROVED"

    # Publication is permitted only after the PR still names the reviewed
    # branch and SHA. Stub the GitHub lookup at that boundary and prove a moved
    # head prevents the publisher from running.
    monkeypatch.setattr(
        recorder,
        "_pr",
        lambda *_args, **_kwargs: {
            "number": 7,
            "headRefName": "codex/author",
            "headRefOid": "b" * 40,
            "state": "OPEN",
        },
    )
    monkeypatch.setattr(
        recorder,
        "post_commit_status",
        lambda *_args, **_kwargs: pytest.fail("moved head must not publish"),
    )
    with pytest.raises(recorder.RecordError, match="PR head moved since review"):
        recorder.record(
            review_task,
            pr_number=7,
            task_root=task_root,
            lock_root=tmp_path / "locks",
        )

    # A completed record without its reply is not publishable evidence.
    reply_path = task_path.with_suffix(".result")
    missing_reply = task_root / "missing.reply"
    reply_path.rename(missing_reply)
    with pytest.raises(recorder.RecordError, match="record or reply unavailable"):
        recorder._task(review_task, task_root)
    missing_reply.rename(reply_path)

    # Terminal failure wins over approval-looking reply text.
    failed = dict(completed, status="failed")
    task_path.write_text(json.dumps(failed), encoding="utf-8")
    with pytest.raises(recorder.RecordError, match="review task is not done"):
        recorder._task(review_task, task_root)


@pytest.mark.parametrize(
    "scenario,expected_rc,wait_count",
    [
        ("done", 0, 1),
        ("running_expiry", 0, 2),
        ("spawning_expiry_twice", 0, 3),
        ("done_racing_expiry", 0, 2),
        ("terminal_timeout", 124, 1),
        ("terminal_timeout_racing_expiry", 124, 2),
        ("cancelled_racing_expiry", 1, 2),
        ("cancelled", 1, 1),
        ("stale_nonce", 1, 1),
        ("nonce_drift_after_expiry", 1, 1),
    ],
)
def test_documented_shell_continues_only_same_nonce_wait(tmp_path, scenario, expected_rc, wait_count):
    """Execute the whole fence under set -e, with real cmd_wait/status and offline launch."""
    body = REFERENCE.read_text(encoding="utf-8")
    recipe = next(
        block for block in re.findall(r"^```bash\n(.*?)^```", body, re.M | re.S) if "dispatch_result=" in block
    )
    # Replace only the interpreter boundary; keep the documented shell, parser,
    # flags, stdout capture and continuation logic intact.
    recipe = recipe.replace('PY="$PRIMARY_REPO/.venv/bin/python"', 'PY="$RECIPE_PY"')
    helper = tmp_path / "native_boundary.py"
    helper.write_text(
        """import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, os.environ['RECIPE_REPO'])
from scripts import delegate

argv = sys.argv[1:]
if argv[0] == '-c':
    raise SystemExit(subprocess.run([sys.executable, *argv], check=False).returncode)
assert argv.pop(0) == 'scripts/delegate.py'
args = delegate.build_parser().parse_args(argv)
path = Path(os.environ['RECIPE_CALLS'])
calls = json.loads(path.read_text()) if path.exists() else []
calls.append(argv)
path.write_text(json.dumps(calls))
nonce = 'run-nonce-fixture'
if args.command == 'dispatch':
    assert args.pinned_head == 'a' * 40 and args.branch == 'codex/author'
    assert args.require_review_verdict and args.worktree == 'auto'
    print(args.task_id)
    print(nonce)
    raise SystemExit(0)  # launch boundary only; real producer is tested separately

assert args.task_id == 'review-fixture' and args.run_nonce == nonce
scenario = os.environ['RECIPE_SCENARIO']
waits = sum(command[0] == 'wait' for command in calls)
state = {'task_id': args.task_id, 'run_nonce': nonce, 'status': 'done'}
if scenario in ('terminal_timeout', 'cancelled') or (scenario in ('terminal_timeout_racing_expiry', 'cancelled_racing_expiry') and waits > 1):
    state['status'] = 'timeout' if scenario.startswith('terminal_timeout') else 'cancelled'
elif scenario == 'stale_nonce':
    state['run_nonce'] = 'another-run'
elif scenario in ('running_expiry', 'done_racing_expiry', 'nonce_drift_after_expiry', 'terminal_timeout_racing_expiry', 'cancelled_racing_expiry') and waits == 1:
    state['status'] = 'running'
elif scenario == 'spawning_expiry_twice' and waits <= 2:
    state['status'] = 'spawning'
if args.command == 'status':
    if scenario == 'done_racing_expiry':
        state['status'] = 'done'
    if scenario == 'terminal_timeout_racing_expiry':
        state['status'] = 'timeout'
    if scenario == 'cancelled_racing_expiry':
        state['status'] = 'cancelled'
    if scenario == 'nonce_drift_after_expiry':
        state['run_nonce'] = 'another-run'
clock = [0.0]
delegate._read_state_or_archived = lambda task: (path, state)
delegate._heal_dead_task = lambda *a, **kw: None
delegate.time.monotonic = lambda: clock[0]
delegate.time.sleep = lambda seconds: clock.__setitem__(0, args.timeout + 1)
raise SystemExit(args.func(args))
""",
        encoding="utf-8",
    )
    executable = tmp_path / "fixture-python"
    executable.write_text(
        f'#!/bin/bash\nexec {shlex.quote(sys.executable)} {shlex.quote(str(helper))} "$@"\n',
        encoding="utf-8",
    )
    executable.chmod(0o700)
    call_file = tmp_path / "calls.json"
    result = subprocess.run(
        ["bash", "-c", recipe],
        cwd=REFERENCE.parents[5],
        capture_output=True,
        text=True,
        timeout=45,
        env={
            **os.environ,
            "RECIPE_PY": str(executable),
            "RECIPE_REPO": str(REFERENCE.parents[5]),
            "RECIPE_CALLS": str(call_file),
            "RECIPE_SCENARIO": scenario,
            "REVIEW_AGENT": "claude",
            "REVIEW_MODEL": "claude-opus-5-5",
            "REVIEW_TASK": "review-fixture",
            "REVIEW_BRIEF": str(tmp_path / "brief.md"),
            "AUTHOR_BRANCH": "codex/author",
            "HEAD_SHA": HEAD,
            "AUTHOR_MODEL": "gpt-6.1-sol",
            "REVIEW_RISK": "medium",
        },
    )
    assert result.returncode == expected_rc, result.stderr
    calls = json.loads(call_file.read_text(encoding="utf-8"))
    assert sum(command[0] == "dispatch" for command in calls) == 1
    waits = [command for command in calls if command[0] == "wait"]
    assert len(waits) == wait_count
    assert all(
        command[1] == "review-fixture" and command[command.index("--run-nonce") + 1] == NONCE for command in waits
    )
    if expected_rc == 0:
        assert json.loads(result.stdout)["status"] == "done"
    elif scenario.startswith("terminal_timeout"):
        assert json.loads(result.stdout)["status"] == "timeout"
    elif scenario in ("stale_nonce", "nonce_drift_after_expiry"):
        assert "stale_run_nonce" in result.stderr


@pytest.mark.parametrize(
    "scenario,expected_rc,recovery_waits",
    [
        ("running", 0, 2),
        ("spawning", 0, 2),
        ("done", 0, 1),
        ("drift_after_lookup", 1, 1),
        ("drift_after_expiry", 1, 1),
        ("missing_record", 1, 0),
        ("empty_nonce", 1, 0),
        ("non_string_nonce", 1, 0),
        ("wrong_task_id", 1, 0),
    ],
)
def test_ask_expiry_lookup_and_documented_same_task_continuation(
    monkeypatch, tmp_path, scenario, expected_rc, recovery_waits
):
    """Real ask parsing/expiry → documented status lookup → nonce-bound wait, offline."""
    from contextlib import redirect_stderr, redirect_stdout

    task_path = tmp_path / "review-fixture.json"
    call_file = tmp_path / "calls.json"
    calls = []
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path)
    # Test-owned records have no native worker; only its liveness boundary is replaced.
    monkeypatch.setattr(delegate, "_heal_dead_task", lambda *_a, **_kw: None)
    clock = [0.0]
    monkeypatch.setattr(delegate.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: clock.__setitem__(0, 2.0))

    @contextmanager
    def prompt_directory():
        yield tmp_path

    monkeypatch.setattr(wrappers, "_prompt_directory", prompt_directory)

    def native_boundary(command, **kwargs):
        assert "scripts/delegate.py" in command
        args = delegate.build_parser().parse_args(command[2:])
        calls.append(command[2:])
        if args.command == "dispatch":
            task_path.write_text(
                json.dumps({"task_id": args.task_id, "run_nonce": NONCE, "status": "running"}),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, f"{args.task_id}\n{NONCE}\n", "")
        assert args.command == "wait" and args.run_nonce is None
        monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: clock.__setitem__(0, args.timeout + 1))
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            rc = args.func(args)
        assert rc == 124 and stdout.getvalue() == ""
        assert json.loads(stderr.getvalue())["last_known_status"] == "running"
        return subprocess.CompletedProcess(command, rc, stdout.getvalue(), stderr.getvalue())

    observed = []
    real_ask = wrappers.run_ask_review_dispatch

    def observe_ask(*args, **kwargs):
        result = real_ask(*args, **kwargs)
        observed.append(result)
        return result

    # Limit these patches to the initial synchronous ask; shell recovery runs real subprocesses.
    with monkeypatch.context() as initial:
        initial.setattr(wrappers.subprocess, "run", native_boundary)
        initial.setattr(wrappers, "run_ask_review_dispatch", observe_ask)
        initial.setattr(_cli, "require_core_or_exit", lambda _name: None)
        initial.setattr(_cli.sys, "stdin", io.StringIO("Review the pushed branch."))
        args = _cli._build_parser().parse_args(
            ["ask-codex", "-", "--review", "--task-id", "review-fixture", "--branch", "codex/author"]
        )
        with pytest.raises(SystemExit) as expiry:
            _cli._handle_acp_compat(args, "codex")
    signal = "ask-codex review dispatch did not complete: status=None"
    assert expiry.value.code == signal  # ask exposes a failure message, not wait's rc 124
    assert observed == [{"response": "", "ok": False, "stderr_excerpt": signal}]
    assert json.loads(task_path.read_text())["run_nonce"] == NONCE
    assert [command[0] for command in calls] == ["dispatch", "wait"]
    call_file.write_text(json.dumps(calls), encoding="utf-8")

    state = json.loads(task_path.read_text())
    if scenario in ("spawning", "done"):
        state["status"] = scenario
    elif scenario == "empty_nonce":
        state["run_nonce"] = ""
    elif scenario == "non_string_nonce":
        state["run_nonce"] = 7
    elif scenario == "wrong_task_id":
        state["task_id"] = "unrelated-task"
    task_path.write_text(json.dumps(state), encoding="utf-8")
    if scenario == "missing_record":
        task_path.rename(tmp_path / "unavailable.json")

    helper = tmp_path / "recovery_boundary.py"
    helper.write_text(
        """import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, os.environ['RECIPE_REPO'])
from scripts import delegate
argv = sys.argv[1:]
if argv[0] == '-c':
    raise SystemExit(subprocess.run([sys.executable, *argv], check=False).returncode)
assert argv.pop(0) == 'scripts/delegate.py'
args = delegate.build_parser().parse_args(argv)
assert args.command in ('status', 'wait'), 'recovery must never dispatch'
root = Path(os.environ['RECIPE_ROOT'])
path = root / 'review-fixture.json'
call_file = root / 'calls.json'
calls = json.loads(call_file.read_text())
calls.append(argv)
call_file.write_text(json.dumps(calls))
delegate.tasks_dir = lambda: root
# Offline native worker liveness boundary only; record reading/status/wait stay real.
delegate._heal_dead_task = lambda *a, **kw: None
scenario = os.environ['RECIPE_SCENARIO']
waits = sum(command[0] == 'wait' for command in calls) - 1
if args.command == 'wait':
    assert args.task_id == 'review-fixture' and args.run_nonce == 'run-nonce-fixture'
    state = json.loads(path.read_text())
    if scenario == 'drift_after_lookup':
        state['run_nonce'] = 'another-run'
    elif waits > 1:
        state['status'] = 'done'  # settlement only, never an approval/reply fixture
    path.write_text(json.dumps(state))
elif args.run_nonce is not None and scenario == 'drift_after_expiry':
    state = json.loads(path.read_text())
    state['run_nonce'] = 'another-run'
    path.write_text(json.dumps(state))
clock = [0.0]
delegate.time.monotonic = lambda: clock[0]
delegate.time.sleep = lambda seconds: clock.__setitem__(0, args.timeout + 1)
raise SystemExit(args.func(args))
""",
        encoding="utf-8",
    )
    executable = tmp_path / "fixture-python"
    executable.write_text(
        f'#!/bin/bash\nexec {shlex.quote(sys.executable)} {shlex.quote(str(helper))} "$@"\n',
        encoding="utf-8",
    )
    executable.chmod(0o700)
    blocks = re.findall(r"^```bash\n(.*?)^```", REFERENCE.read_text(), re.M | re.S)
    launch = next(block for block in blocks if "dispatch_result=" in block)
    lookup = next(block for block in blocks if 'status "$REVIEW_TASK")' in block)
    # Execute the documented initialization, recovery fence and existing loop verbatim;
    # substitute only the interpreter boundary, never initialize REVIEW_NONCE in the test.
    initialization = launch.split("# If requires_silence_timeout", 1)[0]
    initialization = initialization.replace('PY="$PRIMARY_REPO/.venv/bin/python"', 'PY="$RECIPE_PY"')
    loop = "while true; do" + launch.split("while true; do", 1)[1]
    env = {key: value for key, value in os.environ.items() if key != "REVIEW_NONCE"}
    result = subprocess.run(
        ["bash", "-c", initialization + lookup + loop],
        cwd=REFERENCE.parents[5],
        capture_output=True,
        text=True,
        timeout=45,
        env={
            **env,
            "RECIPE_PY": str(executable),
            "RECIPE_REPO": str(REFERENCE.parents[5]),
            "RECIPE_ROOT": str(tmp_path),
            "RECIPE_SCENARIO": scenario,
            "REVIEW_TASK": "review-fixture",
        },
    )
    assert result.returncode == expected_rc, result.stderr
    calls = json.loads(call_file.read_text())
    assert sum(command[0] == "dispatch" for command in calls) == 1
    assert calls[2] == ["status", "review-fixture"]  # live lookup before any continuation
    waits = [command for command in calls[2:] if command[0] == "wait"]
    assert len(waits) == recovery_waits
    assert all(command[command.index("--run-nonce") + 1] == NONCE for command in waits)
    if expected_rc == 0:
        settled = json.loads(result.stdout)
        assert settled == {"task_id": "review-fixture", "run_nonce": NONCE, "status": "done"}
    elif scenario.startswith("drift_"):
        assert "stale_run_nonce" in result.stderr
        assert json.loads(task_path.read_text())["run_nonce"] == "another-run"
    elif scenario == "missing_record":
        assert result.stdout == ""
    else:
        assert "invalid task identity/nonce" in result.stderr
