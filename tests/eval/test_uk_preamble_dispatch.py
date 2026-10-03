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
from scripts.eval.uk_preamble.common import SEATS, ResultsDir, read_json, sha256_text
from scripts.eval.uk_preamble.dispatch import (
    DelegateComposer,
    DelegateDispatcher,
    DispatchError,
    TaskOutcome,
    condition_problems,
    frame,
    workspace_fingerprint,
    workspace_probe,
)
from scripts.eval.uk_preamble.runner import Executor, TaskSpec, composition_frame, raw_path, render, rules_block

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
    expected = {
        "effective_prompt_sha256": "p",
        "prompt_blocks": ["rules_core", "worktree"],
        "cwd": str(tmp_path),
        "worktree_path": str(tmp_path),
    }
    good = {
        "effective_prompt_sha256": "p",
        "prompt_blocks": ["rules_core", "worktree"],
        "research": None,
        "mode": "read-only",
        "worktree_path": str(tmp_path),
        "cwd": str(tmp_path),
        "dispatch_args_sha256": "a",
    }
    assert condition_problems(good, expected=expected, args_sha256="a") == []
    bad = {
        **good,
        "effective_prompt_sha256": "q",
        "prompt_blocks": ["rules_core", "worktree", "research"],
        "research": {"pointer_ids": ["r"]},
        "mode": "danger",
        "worktree_path": None,
        "cwd": "/elsewhere",
        "dispatch_args_sha256": "b",
    }
    assert len(condition_problems(bad, expected=expected, args_sha256="a")) == 7
    missing = condition_problems({}, expected=expected, args_sha256="a")
    assert len(missing) == 6  # an old record without the fields is never accepted
    unwrapped = {**expected, "prompt_blocks": [], "worktree_path": None}
    assert len(condition_problems(good, expected=unwrapped, args_sha256="a")) == 2


# --------------------------------------------------------------------------- delegate's real composition


def _git(repo: Path, *args: str) -> None:
    base = ["git", "-C", str(repo), "-c", "user.email=t@example.invalid", "-c", "user.name=t"]
    subprocess.run([*base, *args], check=True, timeout=60, capture_output=True)


@pytest.fixture
def linked_worktree(tmp_path: Path) -> Path:
    """A registered linked worktree whose tree has the trees delegate's sparse profile excludes."""
    main = tmp_path / "main"
    for rel in (
        "scripts/a.py",
        "curriculum/l2-uk-en/x.md",
        "wiki/y.md",
        "data/projects/p.txt",
        "data/other/o.txt",
        "registry/projects/r.txt",
        "registry/lexicon/l.txt",
    ):
        (main / rel).parent.mkdir(parents=True, exist_ok=True)
        (main / rel).write_text("x\n", encoding="utf-8")
    _git(main.parent, "init", "-q", str(main))
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")
    linked = tmp_path / "linked"
    _git(main, "worktree", "add", "-q", "-b", "eval", str(linked))
    return linked.resolve()


def _delegate_record(cwd: Path, prompt: str, args_sha256: str) -> dict[str, object]:
    """The task-record conditions delegate's read-only ``--cwd`` dispatch writes, built step by step as
    ``cmd_dispatch`` does: cwd validation, the registered-worktree lookup, the sparse checkout really applied,
    then ``_compose_dispatch_prompt`` (no provider is called)."""
    validated, error = delegate._validate_caller_path("--cwd", str(cwd), resolve=delegate._resolve_cwd_path)
    assert error is None
    worktree = delegate._resolve_verified_worktree_path(validated)
    sparse = None
    if worktree is not None:
        includes = delegate._infer_sparse_include(None, owned_paths=None, prompt_text=prompt)
        sparse = delegate._apply_dispatch_sparse_checkout(worktree, full_checkout=False, sparse_include=includes)
    blocks: list[str] = []
    composed = delegate._compose_dispatch_prompt(
        prompt,
        worktree_path=worktree,
        mode="read-only",
        sparse_telemetry=sparse,
        delegate_commits=False,
        research_block="",
        advisory_block="",
        advisory_block_kind=None,
        rules_seat="core",
        blocks=blocks,
    )
    return {
        "effective_prompt_sha256": sha256_text(composed),
        "prompt_blocks": blocks,
        "cwd": str(worktree or validated),
        "worktree_path": str(worktree) if worktree else None,
        "mode": "read-only",
        "dispatch_args_sha256": args_sha256,
        "worktree_sparse": sparse,
    }


PROMPT = render("# Task: proofreading\nЗавдання.\n", rules_block())


def test_reviewer_probe_real_worktree_dispatch_is_wrapped_and_the_harness_expects_it(linked_worktree: Path):
    """Round 2 probe: a real ``--cwd`` worktree dispatch gave source != effective, blocks rules_core+worktree."""
    expected = DelegateComposer(delegate, linked_worktree).compose(PROMPT)
    assert expected["effective_prompt_sha256"] != sha256_text(PROMPT)
    assert expected["prompt_blocks"] == ["rules_core", "worktree"]
    assert expected["worktree_path"] == str(linked_worktree) and expected["cwd"] == str(linked_worktree)
    record = _delegate_record(linked_worktree, PROMPT, "a")
    assert record["worktree_sparse"]["excluded"] == ["curriculum", "data/projects", "registry/projects", "wiki"]
    assert condition_problems(record, expected=expected, args_sha256="a") == []
    # A prompt naming an excluded tree is framed differently (its sparse note changes): never paired.
    named = render("# Task: proofreading\nДив. curriculum/l2-uk-en.\n", rules_block())
    assert frame(DelegateComposer(delegate, linked_worktree).compose(named)) != frame(expected)
    assert condition_problems(_delegate_record(linked_worktree, named, "a"), expected=expected, args_sha256="a")


def test_real_composition_outside_a_worktree_adds_no_block(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    expected = DelegateComposer(delegate, plain).compose(PROMPT)
    assert expected["prompt_blocks"] == [] and expected["worktree_path"] is None
    assert expected["effective_prompt_sha256"] == sha256_text(PROMPT)  # the rendered core is not repeated
    assert condition_problems(_delegate_record(plain, PROMPT, "a"), expected=expected, args_sha256="a") == []
    bare = DelegateComposer(delegate, plain).compose("Завдання без ядра.\n")
    assert bare["prompt_blocks"] == ["rules_core"]


class SimulatedDelegate(DelegateDispatcher):
    """DelegateDispatcher whose dispatch writes the record delegate's real composition path produces."""

    def __init__(self, cwd: Path) -> None:
        super().__init__(python=sys.executable, delegate=Path(delegate.__file__), cwd=cwd)
        self.outcomes: dict[str, TaskOutcome] = {}

    def known(self, task_id: str) -> bool:
        return task_id in self.outcomes

    def dispatch(self, task_id, seat, kind, prompt_path: Path, *, force_new: bool) -> str:
        prompt = prompt_path.read_text(encoding="utf-8")
        record = _delegate_record(self.cwd, prompt, self.expected_args_sha256(task_id, seat, prompt_path))
        response = json.dumps({"items": [{"id": "W1", "text": "Текст."}]}, ensure_ascii=False)
        conditions = {key: record.get(key) for key in dispatch_module.CONDITION_FIELDS}
        self.outcomes[task_id] = TaskOutcome(
            task_id,
            "done",
            seat.agent,
            seat.model,
            None,
            response,
            sha256_text(response),
            "n",
            sha256_text(prompt),
            conditions=conditions,
        )
        return "n"

    def wait(self, task_id: str, run_nonce: str | None) -> TaskOutcome:
        return self.outcomes[task_id]


def test_task_dispatched_through_real_composition_is_accepted(linked_worktree: Path, outside_dir: Path):
    dispatcher = SimulatedDelegate(linked_worktree)
    seat = SEATS["gpt-6.1-sol"]
    tasks = [
        TaskSpec(f"uk9623-t-sol-{label}-r1-writing-00", seat, "writing", label, 1, ("W1",), prompt)
        for label, prompt in (
            ("none", PROMPT),
            ("adapted-v2", render("Преамбула.\n\n" + PROMPT[len(rules_block()) + 2 :], rules_block())),
        )
    ]
    plan_frame = composition_frame(dispatcher, tasks)
    assert plan_frame["prompt_blocks"] == ["rules_core", "worktree"]
    results = ResultsDir(outside_dir / "results")
    executor = Executor(
        dispatcher,
        results,
        worker_cwd=linked_worktree,
        workspace=workspace_probe(linked_worktree),
        frame=plan_frame,
        max_parallel=1,  # delegate serialises dispatches into one worktree with its worktree lock
        spawn_interval=0,
    )
    summary = executor.run(tasks)
    assert summary.accepted == 2 and summary.complete
    for task in tasks:
        raw = read_json(raw_path(results, task.task_id))
        assert raw["accepted"] is True and raw["condition_problem"] is None
        assert frame(raw["composition"]) == plan_frame


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
