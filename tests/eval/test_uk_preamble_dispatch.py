"""DelegateDispatcher against a fake delegate.py script (#9623); no network, no workers."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import scripts.delegate as delegate
from scripts.eval.uk_preamble import dispatch as dispatch_module
from scripts.eval.uk_preamble.common import SEATS, sha256_text
from scripts.eval.uk_preamble.dispatch import (
    DelegateDispatcher,
    DispatchError,
    condition_problems,
    workspace_fingerprint,
)

FAKE_DELEGATE = textwrap.dedent(
    """
    import hashlib, json, sys, time
    from pathlib import Path

    state_dir = Path(__file__).parent / "state"
    state_dir.mkdir(exist_ok=True)
    args = sys.argv[1:]
    (state_dir / "calls.jsonl").open("a").write(json.dumps(args) + "\\n")
    command, task_id = args[0], (args[args.index("--task-id") + 1] if "--task-id" in args else args[1])
    record = state_dir / f"{task_id}.json"
    if command == "dispatch":
        if "--dry-run" in args:
            print(task_id); print("dry-nonce"); sys.exit(0)
        prompt = Path(args[args.index("--prompt-file") + 1]).read_text()
        result = state_dir / f"{task_id}.result"
        answer = '{"items": []}'
        result.write_text(answer)
        digest = hashlib.sha256(answer.encode()).hexdigest()
        if "tamper" in task_id:
            result.write_text("changed after the fact")
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        record.write_text(json.dumps({
            "status": "done", "agent": args[args.index("--agent") + 1], "model": args[args.index("--model") + 1],
            "substitution": None, "result_file": str(result), "result_sha256": digest, "run_nonce": "n1",
            "prompt_sha256": prompt_sha, "effective_prompt_sha256": prompt_sha, "prompt_blocks": [],
            "cwd": args[args.index("--cwd") + 1], "mode": args[args.index("--mode") + 1], "worktree_path": None,
            "dispatch_args_sha256": "recorded-args", "cli_version": "1.2.3", "effort": "high",
        }))
        print(task_id); print("n1"); sys.exit(0)
    if command == "wait":
        if "slow" in task_id:
            time.sleep(30)
        sys.exit(0)
    if command == "status":
        if not record.exists():
            print(json.dumps({"error": "no state file"})); sys.exit(1)
        print(record.read_text()); sys.exit(0)
    sys.exit(2)
    """
)


@pytest.fixture
def fake(tmp_path: Path) -> tuple[DelegateDispatcher, Path, Path]:
    script = tmp_path / "delegate.py"
    script.write_text(FAKE_DELEGATE, encoding="utf-8")
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Завдання.\n", encoding="utf-8")
    worker = tmp_path / "worker"
    worker.mkdir()
    dispatcher = DelegateDispatcher(python=sys.executable, delegate=script, cwd=worker, hard_timeout=600)
    return dispatcher, prompt, tmp_path / "state"


def _calls(state: Path) -> list[list[str]]:
    return [json.loads(line) for line in (state / "calls.jsonl").read_text().splitlines()]


def test_dispatch_wait_attributes_the_answer_and_its_conditions(fake):
    dispatcher, prompt, state = fake
    assert dispatcher.known("t-sol") is False
    nonce = dispatcher.dispatch("t-sol", SEATS["gpt-6.1-sol"], "review", prompt, force_new=False)
    assert nonce == "n1" and dispatcher.known("t-sol") is True
    outcome = dispatcher.wait("t-sol", nonce)
    assert (outcome.status, outcome.agent, outcome.model) == ("done", "codex", "gpt-6.1-sol")
    assert outcome.response_text == '{"items": []}'
    assert outcome.identity_problem(SEATS["gpt-6.1-sol"], sha256_text("Завдання.\n")) is None
    assert outcome.identity_problem(SEATS["claude-opus-5-5"], sha256_text("Завдання.\n"))
    assert outcome.conditions["effective_prompt_sha256"] == sha256_text("Завдання.\n")
    assert outcome.conditions["prompt_blocks"] == [] and outcome.conditions["cli_version"] == "1.2.3"
    dispatch_args = next(call for call in _calls(state) if call[0] == "dispatch")
    for flag in ("--mode", "read-only", "--language-lane", "--cwd", str(dispatcher.cwd), "--rules-seat", "core"):
        assert flag in dispatch_args
    assert dispatch_args[dispatch_args.index("--effort") + 1] == "high"
    # No flag that makes delegate append context outside the hashed prompt.
    assert not any(arg.startswith("--research") or arg in {"--worktree", "--lifecycle-file"} for arg in dispatch_args)


def test_flash_dispatch_carries_no_effort(fake):
    dispatcher, prompt, state = fake
    dispatcher.dispatch("t-flash", SEATS["gemini-3.8-flash-high"], "writing", prompt, force_new=True)
    args = _calls(state)[-1]
    assert "--effort" not in args and "--force-new" in args
    assert args[args.index("--agent") + 1] == "agy"


def test_expected_args_hash_is_the_delegate_parser_hash_of_the_built_dispatch(fake):
    dispatcher, prompt, _ = fake
    seat = SEATS["claude-opus-5-5"]
    built = dispatcher._dispatch_args("t-opus", seat, prompt)
    expected = delegate.dispatch_args_sha256(delegate.build_parser().parse_args(built))
    assert dispatcher.expected_args_sha256("t-opus", seat, prompt) == expected
    with_extra = delegate.dispatch_args_sha256(delegate.build_parser().parse_args([*built, "--research-role", "x"]))
    assert with_extra != expected  # an extra flag would show in the recorded hash
    forced = delegate.dispatch_args_sha256(delegate.build_parser().parse_args([*built, "--force-new"]))
    assert forced == expected  # delegate excludes --force-new, so a retry keeps the same hash


def test_condition_problems_name_every_departure(tmp_path: Path):
    cwd = tmp_path
    good = {
        "effective_prompt_sha256": "p",
        "prompt_blocks": [],
        "research": None,
        "mode": "read-only",
        "worktree_path": None,
        "cwd": str(cwd),
        "dispatch_args_sha256": "a",
    }
    assert condition_problems(good, prompt_sha256="p", cwd=cwd, args_sha256="a") == []
    bad = {
        **good,
        "effective_prompt_sha256": "q",
        "prompt_blocks": ["rules_core", "research"],
        "research": {"pointer_ids": ["r"]},
        "mode": "danger",
        "worktree_path": "/w",
        "cwd": "/elsewhere",
        "dispatch_args_sha256": "b",
    }
    assert len(condition_problems(bad, prompt_sha256="p", cwd=cwd, args_sha256="a")) == 7
    missing = condition_problems({}, prompt_sha256="p", cwd=cwd, args_sha256="a")
    assert len(missing) == 5  # an old record without the fields is never accepted


def test_workspace_fingerprint_tracks_commit_changes_and_instruction_files(tmp_path: Path):
    repo = tmp_path / "checkout"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.email=t@example.invalid", "-c", "user.name=t"]
    subprocess.run([*git, "init", "-q"], check=True, timeout=30)
    (repo / "AGENTS.md").write_text("rules\n", encoding="utf-8")
    subprocess.run([*git, "add", "AGENTS.md"], check=True, timeout=30)
    subprocess.run([*git, "commit", "-q", "-m", "init"], check=True, timeout=30)
    first = workspace_fingerprint(repo)
    assert first["head"] and first["files"]["AGENTS.md"] and first["files"][".mcp.json"] is None
    assert workspace_fingerprint(repo) == first
    (repo / ".mcp.json").write_text("{}", encoding="utf-8")  # untracked tool configuration still counts
    second = workspace_fingerprint(repo)
    assert second != first and second["head"] == first["head"]
    (repo / "AGENTS.md").write_text("other rules\n", encoding="utf-8")
    third = workspace_fingerprint(repo)
    assert third["tracked_changes_sha256"] != second["tracked_changes_sha256"]
    assert workspace_fingerprint(tmp_path / "not-a-checkout-yet")["head"] is None


def test_result_digest_mismatch_is_refused(fake):
    dispatcher, prompt, _ = fake
    dispatcher.dispatch("t-tamper", SEATS["claude-opus-5-5"], "review", prompt, force_new=False)
    with pytest.raises(DispatchError, match="digest"):
        dispatcher.wait("t-tamper", "n1")


def test_preflight_uses_dry_run(fake):
    dispatcher, prompt, state = fake
    dispatcher.preflight("t-pre", SEATS["claude-opus-5-5"], "judge", prompt)
    assert "--dry-run" in _calls(state)[-1]


def test_wait_timeout_becomes_dispatch_error(fake, monkeypatch: pytest.MonkeyPatch):
    dispatcher, prompt, _ = fake
    dispatcher.dispatch("t-slow", SEATS["claude-opus-5-5"], "review", prompt, force_new=False)
    monkeypatch.setattr(dispatch_module, "CONTROL_TIMEOUT", 1)
    dispatcher.wait_timeout = 1
    with pytest.raises(DispatchError, match="timed out"):
        dispatcher.wait("t-slow", "n1")
