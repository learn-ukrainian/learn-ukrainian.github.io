"""DelegateDispatcher against a fake dispatch.py script (#9623); no network, no workers."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import textwrap
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path

import pytest

import scripts.delegate as delegate
from scripts.agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.dispatcher.cli import build_parser
from scripts.eval.uk_preamble import dispatch as dispatch_module
from scripts.eval.uk_preamble.__main__ import make_dispatcher
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
from scripts.eval.uk_preamble.runner import (
    Executor,
    TaskSpec,
    composition_frame,
    load_raw,
    prompt_path,
    raw_path,
    render,
    rules_block,
)

CALLER = "harness"


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
        if record.exists():
            status = json.loads(record.read_text()).get("status")
            print(
                f"task_id {task_id!r} is already {status}. Dispatch refuses to reuse a task-id in any state. "
                "--force-new can archive only the caller's own terminal record+result.",
                file=sys.stderr,
            )
            sys.exit(2)
        if "--dry-run" in args:
            print(json.dumps({"argv": args})); sys.exit(0)
        prompt_file = Path(args[args.index("--prompt-file") + 1])
        prompt = prompt_file.read_bytes()
        result = state_dir / f"{task_id}.result"
        answer = '{"items": []}'
        result.write_text(answer)
        digest = hashlib.sha256(answer.encode()).hexdigest()
        if "tamper" in task_id:
            result.write_text("changed after the fact")
        prompt_sha = hashlib.sha256(prompt).hexdigest()
        worktree = str(Path(__file__).parent / ".worktrees" / "dispatch" / args[args.index("--agent") + 1] / task_id)
        record.write_text(json.dumps({
            "schema_version": 2, "task_id": task_id, "prompt_file": str(prompt_file),
            "research_task_family": args[args.index("--research-task-family") + 1],
            "status": "done", "agent": args[args.index("--agent") + 1], "model": args[args.index("--model") + 1],
            "substitution": None, "result_file": str(result), "result_sha256": digest, "run_nonce": "n1",
            "prompt_sha256": prompt_sha,
            "cwd": worktree, "mode": args[args.index("--mode") + 1], "worktree_path": worktree,
            "effort": "high",
        }))
        print(task_id); print("n1"); sys.exit(0)
    if command == "wait":
        if "slow" in task_id:
            time.sleep(30)
        sys.exit(0)
    if command == "status":
        if "unreadable" in task_id:
            print("NOT-JSON"); sys.exit(1)
        if not record.exists():
            print("dispatcher: task not found", file=sys.stderr); sys.exit(2)
        print(record.read_text()); sys.exit(0)
    sys.exit(2)
    """
)


@pytest.fixture
def fake(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, linked_worktree: Path
) -> tuple[DelegateDispatcher, Path, Path]:
    monkeypatch.setattr(dispatch_module, "caller_initiator", lambda: CALLER)
    script = tmp_path / "dispatch.py"
    script.write_text(FAKE_DELEGATE.replace("__CALLER__", CALLER), encoding="utf-8")
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Завдання.\n", encoding="utf-8")
    worker = linked_worktree
    dispatcher = DelegateDispatcher(python=sys.executable, dispatch_script=script, cwd=worker, hard_timeout=600)
    return dispatcher, prompt, tmp_path / "state"


def _calls(state: Path) -> list[list[str]]:
    return [json.loads(line) for line in (state / "calls.jsonl").read_text().splitlines()]


@pytest.mark.parametrize(
    "seat_key,pin,display_label,backend_id",
    [
        (
            "gemini-3.8-flash-high",
            "gemini-3.8-flash-high",
            "Gemini 3.8 Flash (High)",
            "gemini-3-flash-preview",
        ),
        (
            "claude-opus-5-5",
            "claude-opus-5-5-high",
            "Claude Opus 5.5 (High)",
            "claude-opus-5-5-high",
        ),
        (
            "claude-opus-5-5",
            "claude-sonnet-5-5-high",
            "Claude Sonnet 5.5 (High)",
            "claude-sonnet-5-5-high",
        ),
    ],
)
@pytest.mark.parametrize("shape", ["nested", "top-level"])
@pytest.mark.parametrize("reported_form", ["absent", "pin", "display", "backend"])
def test_matching_agy_parse_passes_eval_identity_check(
    tmp_path: Path, seat_key: str, pin: str, display_label: str, backend_id: str, reported_form: str, shape: str
):
    seat = replace(SEATS[seat_key], agent="agy", model=pin)
    reported_model = {"absent": None, "pin": pin, "display": display_label, "backend": backend_id}[reported_form]
    conversation_id = "7cd3ba85-817f-4a03-8223-1ff39ca42419"
    app_data = tmp_path / "agy-data"
    transcript = app_data / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "agy" / "verify_words_transcript.jsonl"
    transcript.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    log_file = tmp_path / "agy.log"
    log_file.write_text(f"Print mode: conversation={conversation_id}, sending message\n", encoding="utf-8")
    prompt_digest = sha256_text("planned prompt\n")
    plan = InvocationPlan(
        cmd=["agy", "--output-format", "stream-json", "--model", seat.model],
        cwd=tmp_path,
        stdin_payload="",
        output_file=None,
        env_overrides={"AGY_RUNTIME_LOG_FILE": str(log_file), "AGY_APP_DATA_DIR": str(app_data)},
        env_unsets=(),
        liveness_paths=(log_file,),
        metadata={"entire_fleet": {"requested_model": seat.model}},
    )
    init = {"event": "init", "conversation_id": conversation_id}
    if reported_model is not None:
        init.update({"init": {"model": reported_model}} if shape == "nested" else {"model": reported_model})
    stdout = "\n".join(
        [
            json.dumps(init),
            json.dumps(
                {
                    "event": "result",
                    "result": {
                        "status": "SUCCESS",
                        "conversation_id": conversation_id,
                        "response": "READY",
                    },
                }
            ),
        ]
    )
    parsed = AgyAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan)
    claude_pin = pin in {"claude-opus-5-5-high", "claude-sonnet-5-5-high"}
    if claude_pin and reported_model is None:
        # Absent Claude runtime identity is refused, never a matching successful worker.
        assert parsed.ok is False
        assert parsed.stderr_excerpt == "agy_model_identity_missing"
        assert parsed.response == ""
        assert parsed.substitution is None
        assert parsed.model_identity is None
        return
    assert parsed.ok is True and parsed.response == "READY"
    if claude_pin:
        assert parsed.model_identity == {
            "actual_model": reported_model,
            "actual_model_known": True,
            "source": "provider-init",
            "substituted": False,
        }
    outcome = TaskOutcome(
        task_id="agy-matching-model",
        status="done",
        agent=seat.agent,
        model=seat.model,
        substitution=parsed.substitution,
        response_text=parsed.response,
        result_sha256=sha256_text(parsed.response),
        run_nonce="fixture",
        prompt_sha256=prompt_digest,
    )
    assert outcome.identity_problem(seat, prompt_digest) is None
    assert parsed.substitution is None


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
    assert replace(outcome, conditions={**outcome.conditions, "effort": "low"}).identity_problem(
        SEATS["gpt-6.1-sol"], sha256_text("Завдання.\n")
    )
    assert outcome.conditions["stored_prompt_sha256"] == sha256_text("Завдання.\n")
    assert outcome.conditions["schema_version"] == 2 and outcome.conditions["prompt_blocks"] is None
    for call in _calls(state)[-2:]:
        assert call[call.index("--run-nonce") + 1] == "n1"
    dispatch_args = next(call for call in _calls(state) if call[0] == "dispatch")
    for flag in ("--mode", "read-only", "--language-lane", "--pinned-head", "ukrainian"):
        assert flag in dispatch_args
    assert dispatch_args[dispatch_args.index("--effort") + 1] == "high"
    # The family classifies the task. Pointer-selecting research flags, and flags that add other context, stay off.
    assert dispatch_args[dispatch_args.index("--research-task-family") + 1] == "ukrainian-review"
    assert [arg for arg in dispatch_args if arg.startswith("--research")] == ["--research-task-family"]
    assert "--advisory-task" not in dispatch_args and "--force-new" not in dispatch_args
    assert not any(arg in {"--cwd", "--lifecycle-file"} for arg in dispatch_args)


def test_review_profile_types_review_tasks_only_and_default_is_unchanged(fake):
    dispatcher, prompt, _state = fake
    seat = SEATS["gemini-3.8-flash-high"]
    plain = dispatcher._dispatch_args("t-flash", seat, "review", prompt)
    assert "--review-profile" not in plain and "--require-review-verdict" not in plain
    dispatcher.review_profile = "ukrainian"
    review = dispatcher._dispatch_args("t-flash", seat, "review", prompt)
    assert review == [*plain, "--review-profile", "ukrainian"]
    for kind in ("writing", "judge"):
        other = dispatcher._dispatch_args("t-flash", seat, kind, prompt)
        assert "--review-profile" not in other and "--require-review-verdict" not in other
    parsed = build_parser().parse_args(review)
    assert parsed.review_profile == "ukrainian" and parsed.language_lane == "ukrainian"
    assert parsed.branch is None
    assert dispatcher.expected_args_sha256("t-flash", seat, "review", prompt) != sha256_text(json.dumps(plain))


def test_flash_dispatch_carries_no_effort(fake):
    dispatcher, prompt, state = fake
    with pytest.raises(DispatchError, match="new evaluation run tag"):
        dispatcher.dispatch("t-flash", SEATS["gemini-3.8-flash-high"], "writing", prompt, force_new=True)
    dispatcher.dispatch("t-flash", SEATS["gemini-3.8-flash-high"], "writing", prompt, force_new=False)
    args = _calls(state)[-1]
    assert "--effort" not in args and "--force-new" not in args
    assert args[args.index("--agent") + 1] == "agy"
    assert args[args.index("--research-task-family") + 1] == "ukrainian-authoring"


def test_expected_args_hash_is_the_delegate_parser_hash_of_the_built_dispatch(fake):
    dispatcher, prompt, state = fake
    seat = SEATS["claude-opus-5-5"]
    dispatcher.dispatch("t-opus", seat, "review", prompt, force_new=False)
    sent = next(call for call in _calls(state) if call[0] == "dispatch")
    expected = sha256_text(json.dumps(sent, ensure_ascii=False))
    assert dispatcher.expected_args_sha256("t-opus", seat, "review", prompt) == expected
    built = dispatcher._dispatch_args("t-opus", seat, "review", prompt)
    assert built == sent
    parsed = build_parser().parse_args(sent)
    assert parsed.language_lane == "ukrainian" and parsed.mode == "read-only"
    writing = dispatcher._dispatch_args("t-opus", seat, "writing", prompt)
    assert sha256_text(json.dumps(writing, ensure_ascii=False)) != expected
    assert writing[writing.index("--research-task-family") + 1] == "ukrainian-authoring"
    canonical = DelegateDispatcher(
        python=sys.executable,
        dispatch_script=Path(__file__).resolve().parents[2] / "scripts" / "dispatch.py",
        cwd=dispatcher.cwd,
    )
    assert canonical.dispatch_script.name == "dispatch.py"
    entrypoint = make_dispatcher(Namespace(python=sys.executable, hard_timeout=600), dispatcher.cwd)
    assert entrypoint.dispatch_script == Path(dispatch_module.__file__).resolve().parents[2] / "dispatch.py"
    assert entrypoint._dispatch_args("t-opus", seat, "review", prompt) == sent


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

    # The same departures fail closed for v2 without inventing legacy attestations.
    v2_expected = {**expected, "schema_version": 2, "prompt_blocks": []}
    v2_good = {
        **good,
        "schema_version": 2,
        "effective_prompt_sha256": None,
        "prompt_blocks": None,
        "dispatch_args_sha256": None,
        "prompt_sha256": "p",
        "stored_prompt_sha256": "p",
    }
    assert condition_problems(v2_good, expected=v2_expected, args_sha256="a") == []
    v2_bad = {**bad, "schema_version": 2, "prompt_sha256": "q", "stored_prompt_sha256": "q"}
    assert len(condition_problems(v2_bad, expected=v2_expected, args_sha256="a")) == 7
    assert condition_problems({"schema_version": 2}, expected=v2_expected, args_sha256="a")
    assert condition_problems(v2_good, expected=expected, args_sha256="a")


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
    linked = main / ".worktrees" / "dispatch" / "codex" / "linked"
    linked.parent.mkdir(parents=True)
    _git(main, "worktree", "add", "-q", "-b", "eval", str(linked))
    return linked.resolve()


def _delegate_record(cwd: Path, prompt: str, args_sha256: str, evidence_dir: Path | None = None) -> dict[str, object]:
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
        # A real dispatch always exports its evidence directory (#11342).
        evidence_dir=evidence_dir or cwd.parent / "runtime" / "evidence",
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
    assert expected["prompt_blocks"] == ["rules_core", "worktree", "evidence"]
    assert expected["worktree_path"] == str(linked_worktree) and expected["cwd"] == str(linked_worktree)
    record = _delegate_record(linked_worktree, PROMPT, "a")
    assert record["worktree_sparse"]["excluded"] == ["curriculum", "data/projects", "registry/projects", "wiki"]
    assert condition_problems(record, expected=expected, args_sha256="a") == []
    # A prompt naming an excluded tree is framed differently (its sparse note changes): never paired.
    named = render("# Task: proofreading\nДив. curriculum/l2-uk-en.\n", rules_block())
    assert frame(DelegateComposer(delegate, linked_worktree).compose(named)) != frame(expected)
    assert condition_problems(_delegate_record(linked_worktree, named, "a"), expected=expected, args_sha256="a")


def test_eval_composer_accepts_a_real_dispatch_composition_with_the_evidence_block(linked_worktree: Path):
    """#11342 R3: the live evaluation caller must accept the block delegate now always appends.

    A real ``cmd_dispatch`` records ``['rules_core', 'worktree', 'evidence']`` and a
    prompt hash that includes the evidence block. The evaluation composer predicts
    the same because the block is path-free, so ``condition_problems`` accepts it.
    """
    expected = DelegateComposer(delegate, linked_worktree).compose(PROMPT)
    assert expected["prompt_blocks"] == ["rules_core", "worktree", "evidence"]
    for evidence_dir in (
        linked_worktree.parent / "lease-one" / "evidence",
        linked_worktree.parent / "other" / "evidence",
    ):
        record = _delegate_record(linked_worktree, PROMPT, "a", evidence_dir=evidence_dir)
        assert condition_problems(record, expected=expected, args_sha256="a") == []
        # A task-specific evidence directory does not change the prompt suffix, so
        # paired arms still share one frozen frame.
        assert record["effective_prompt_sha256"] == expected["effective_prompt_sha256"]
        assert record["prompt_blocks"] == expected["prompt_blocks"]


@pytest.mark.parametrize("spelling", ["absolute", "relative"])
def test_primary_readonly_cwd_is_refused_before_dispatch(tmp_path: Path, monkeypatch, spelling: str):
    """Paired runs cannot freeze a primary cwd that delegate redirects per task."""
    monkeypatch.chdir(tmp_path)
    cwd = tmp_path if spelling == "absolute" else Path(".")
    dispatcher = DelegateDispatcher(
        python=sys.executable, dispatch_script=Path(__file__).resolve().parents[2] / "scripts" / "dispatch.py", cwd=cwd
    )
    monkeypatch.setattr(dispatcher, "_run", lambda *_a, **_k: pytest.fail("must refuse before a worker call"))
    with pytest.raises(DispatchError, match="pass an existing isolated Git worktree"):
        dispatcher.compose(PROMPT)


@pytest.mark.parametrize("relative", [False, True])
def test_legacy_composer_resolves_registered_worktree_without_cli_helpers(linked_worktree, monkeypatch, relative):
    nested = linked_worktree / "scripts"
    monkeypatch.chdir(linked_worktree)
    composer = DelegateComposer(object(), Path("scripts") if relative else nested)
    assert composer.cwd == str(linked_worktree)
    assert composer.worktree == linked_worktree


@pytest.mark.parametrize("char", ["\n", "\u202e", "\ud800", "\u2028", "\u2029"])
def test_legacy_composer_refuses_unsafe_raw_paths(tmp_path, char):
    with pytest.raises(DispatchError, match="control or format"):
        DelegateComposer(object(), tmp_path / f"unsafe{char}path")


def test_legacy_composer_refuses_unsafe_symlink_target(tmp_path):
    link = tmp_path / "safe-name"
    link.symlink_to(tmp_path / "unsafe\u202epath")
    with pytest.raises(DispatchError, match="control or format"):
        DelegateComposer(object(), link)


def test_legacy_composer_does_not_fall_back_from_first_acp_match(linked_worktree, monkeypatch):
    candidate = linked_worktree / ".worktrees" / "dispatch" / "acp" / "nested"
    candidate.parent.mkdir(parents=True)
    _git(linked_worktree, "worktree", "add", "-q", "-b", "nested-acp", str(candidate))
    main = linked_worktree.parents[3]
    monkeypatch.setattr(
        dispatch_module.worktree_containment, "registered_worktrees", lambda _root: [main, candidate, linked_worktree]
    )
    assert delegate._resolve_verified_worktree_path(candidate) is None
    with pytest.raises(DispatchError, match="isolated Git worktree"):
        DelegateComposer(object(), candidate)


@pytest.mark.parametrize("kind", ["primary", "unregistered", "acp"])
def test_legacy_composer_refuses_unowned_worktrees(linked_worktree, kind):
    main = linked_worktree.parents[3]
    candidate = main
    if kind != "primary":
        candidate = main / ".worktrees" / "dispatch" / ("acp" if kind == "acp" else "codex") / kind
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if kind == "acp":
            _git(main, "worktree", "add", "-q", "-b", "acp", str(candidate))
        else:
            candidate.mkdir()
    with pytest.raises(DispatchError, match="isolated Git worktree"):
        DelegateComposer(object(), candidate)


def test_v2_eval_arguments_keep_manifest_hash_without_loading_legacy_runtime(linked_worktree, tmp_path):
    probe = """
import json, sys
from pathlib import Path
from scripts.eval.uk_preamble.common import SEATS, sha256_text
from scripts.eval.uk_preamble.dispatch import DelegateDispatcher
from scripts.eval.uk_preamble.__main__ import make_dispatcher
from argparse import Namespace
d = make_dispatcher(Namespace(python=sys.executable, hard_timeout=3600), Path(sys.argv[1]))
path = Path(sys.argv[2])
argv = d._dispatch_args('probe', SEATS['gpt-6.1-sol'], 'review', path)
assert d.expected_args_sha256('probe', SEATS['gpt-6.1-sol'], 'review', path) == sha256_text(json.dumps(argv, ensure_ascii=False))
assert d.dispatch_script.name == 'dispatch.py'
assert 'scripts.delegate' not in sys.modules
"""
    proc = subprocess.run(
        [sys.executable, "-c", probe, str(linked_worktree), str(tmp_path / "prompt.md")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr


class SimulatedDelegate(DelegateDispatcher):
    """Run the real v2 CLI in-process; only provider execution is stubbed."""

    def __init__(self, cwd: Path) -> None:
        super().__init__(
            python=sys.executable,
            dispatch_script=Path(__file__).resolve().parents[2] / "scripts" / "dispatch.py",
            cwd=cwd,
        )

    def _run(self, *args: str, **kwargs):
        from scripts.dispatcher import cli

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(args))
        return subprocess.CompletedProcess(args, code, out.getvalue(), err.getvalue())


@pytest.mark.parametrize("status", ["failed", "timeout", "crashed", "cancelled"])
def test_failed_terminal_v2_is_recorded_as_failed_not_not_run_and_retry_gets_fresh_id(
    linked_worktree, outside_dir, monkeypatch, status
):
    from scripts.dispatcher import git, store, worker

    tasks_dir = outside_dir / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    monkeypatch.setattr(
        git, "resolve_repo", lambda key: (linked_worktree.parents[3], {"key": "public", "github": "example/public"})
    )
    started = []

    def finish(spec, record, prompt, hard_timeout):
        store.create(record, prompt)
        started.append(spec.task_id)
        if len(started) <= 2:
            record.update(status=status, error="provider failure evidence")
        else:
            spec.final_file.write_text('{"items": []}')
            record.update(status="done", result_sha256=sha256_text('{"items": []}'))
        store.replace(record)

    monkeypatch.setattr(worker, "start", finish)
    dispatcher = SimulatedDelegate(linked_worktree)
    task = TaskSpec("retry-seat", SEATS["gpt-6.1-sol"], "review", "none", 1, ("W1",), PROMPT)
    results = ResultsDir(outside_dir / "results")
    executor = Executor(
        dispatcher, results, worker_cwd=linked_worktree, workspace=workspace_probe(linked_worktree), spawn_interval=0
    )
    first = executor.run([task])
    raw = load_raw(results, task.task_id)
    assert first.failed == [task.task_id] and first.not_run == []
    assert raw["status"] == status and raw["accepted"] is False
    assert raw["detail"]["error"] == "provider failure evidence"
    original = (tasks_dir / f"{task.task_id}.json").read_bytes()
    original_raw = raw_path(results, task.task_id).read_bytes()
    assert executor.run([task]).failed == [task.task_id]
    executor.retry_failed = True
    second = executor.run([task])
    assert second.failed == ["retry-seat-attempt-1"] and second.not_run == []
    previous = (tasks_dir / "retry-seat-attempt-1.json").read_bytes()
    wait = dispatcher.wait

    def interrupted_wait(*args):
        raise DispatchError("collection interrupted")

    monkeypatch.setattr(dispatcher, "wait", interrupted_wait)
    assert executor.run([task]).not_run == ["retry-seat-attempt-2"]
    monkeypatch.setattr(dispatcher, "wait", wait)
    third = executor.run([task])
    assert third.accepted == 1 and third.complete
    assert started == ["retry-seat", "retry-seat-attempt-1", "retry-seat-attempt-2"]
    accepted = load_raw(results, task.task_id)
    assert accepted["task_id"] == "retry-seat-attempt-2" and accepted["accepted"] is True
    assert accepted["identity_problem"] is None and accepted["condition_problem"] is None
    assert len({read_json(tasks_dir / f"{tid}.json")["run_nonce"] for tid in started}) == 3
    assert (tasks_dir / f"{task.task_id}.json").read_bytes() == original
    assert raw_path(results, task.task_id).read_bytes() == original_raw
    assert (tasks_dir / "retry-seat-attempt-1.json").read_bytes() == previous
    assert executor.run([task]).skipped_accepted == 1


@pytest.mark.parametrize(
    "schema,status", [(None, "done"), (None, "failed"), (None, "running"), (2, "done"), (2, "running")]
)
def test_done_with_error_is_refused_and_legacy_error_behavior_is_unchanged(fake, schema, status):
    dispatcher, prompt, state = fake
    nonce = dispatcher.dispatch("error-seat", SEATS["gpt-6.1-sol"], "review", prompt, force_new=False)
    path = state / "error-seat.json"
    record = json.loads(path.read_text())
    record.update(schema_version=schema, status=status, error="provider error")
    path.write_text(json.dumps(record))
    with pytest.raises(DispatchError, match="provider error"):
        dispatcher.wait("error-seat", nonce)


def test_three_seat_shared_cwd_refusal_uses_real_dispatch_worktree_layout(
    linked_worktree: Path, outside_dir: Path, monkeypatch
):
    from scripts.dispatcher import git, providers, store, worker

    monkeypatch.setenv("LU_TASKS_DIR", str(outside_dir / "tasks"))
    monkeypatch.setattr(
        git, "resolve_repo", lambda key: (linked_worktree.parents[3], {"key": "public", "github": "example/public"})
    )

    def finish(spec, record, prompt, hard_timeout):
        # The provider builder must receive exactly the bytes stored by the real CLI.
        submitted = providers.load(spec.agent).build(spec, {}).stdin
        if spec.agent == "agy":
            submitted = json.loads(submitted)["message"]["content"][0]["text"].encode()
        assert submitted == prompt
        store.create(record, prompt)
        response = json.dumps({"items": [{"id": "W1", "text": "Текст."}]}, ensure_ascii=False)
        spec.final_file.write_text(response, encoding="utf-8")
        record.update(status="done", result_sha256=sha256_text(response))
        store.replace(record)

    monkeypatch.setattr(worker, "start", finish)
    dispatcher = SimulatedDelegate(linked_worktree)
    tasks = [
        TaskSpec(f"uk9623-t-{seat.agent}-{label}-r1-writing-00", seat, "writing", label, 1, ("W1",), prompt)
        for seat in SEATS.values()
        for label, prompt in (
            ("none", PROMPT),
            ("adapted-v2", render("Преамбула.\n\n" + PROMPT[len(rules_block()) + 2 :], rules_block())),
        )
    ]
    plan_frame = composition_frame(dispatcher, tasks)
    assert plan_frame["prompt_blocks"] == []
    results = ResultsDir(outside_dir / "results")
    executor = Executor(
        dispatcher,
        results,
        worker_cwd=linked_worktree,
        workspace=workspace_probe(linked_worktree),
        frame=plan_frame,
        max_parallel=1,  # the in-process CLI redirects process-global stdout
        spawn_interval=0,
    )
    summary = executor.run(tasks)
    assert summary.accepted == 6 and summary.complete and not summary.not_run
    for task in tasks:
        raw = read_json(raw_path(results, task.task_id))
        assert raw["accepted"] is True and raw["condition_problem"] is None
        actual = Path(raw["conditions"]["cwd"])
        assert actual == linked_worktree.parents[1] / task.seat.agent / task.task_id
        assert raw["composition"]["worktree_path"] == str(actual)
        assert raw["workspace"] == raw["workspace_after"] == workspace_fingerprint(actual)
        args = dispatcher._dispatch_args(task.task_id, task.seat, task.kind, prompt_path(results, task.task_id))
        assert "--cwd" not in args
        assert frame(raw["composition"]) == plan_frame
        assert raw["conditions"]["stored_prompt_sha256"] == task.prompt_sha256
        assert raw["conditions"]["effective_prompt_sha256"] is None
        assert raw["conditions"]["dispatch_args_sha256"] is None
        resumed = SimulatedDelegate(linked_worktree).wait(task.task_id, raw["run_nonce"])
        assert resumed.identity_problem(task.seat, task.prompt_sha256) is None
        assert (
            condition_problems(
                resumed.conditions,
                expected=raw["composition"],
                args_sha256=dispatcher.expected_args_sha256(
                    task.task_id, task.seat, task.kind, prompt_path(results, task.task_id)
                ),
            )
            == []
        )


@pytest.mark.parametrize("tamper", [None, "dispatch_args_sha256", "effective_prompt_sha256", "prompt_blocks"])
def test_legacy_resume_accepts_faithful_record_and_refuses_tampering(linked_worktree, outside_dir, monkeypatch, tamper):
    from scripts.eval.uk_preamble.common import write_private_json
    from scripts.storage.topology import StoreBinding

    monkeypatch.delenv("LU_SOURCES_DB", raising=False)
    monkeypatch.delenv("LU_VESUM_DB", raising=False)

    def resolve_legacy_store(store, root):
        path = delegate._primary_database_path(root, f"{store}.db")
        assert dispatch_module.legacy_codec._primary_database_connect_code(path) == (
            f"sqlite3.connect('{root.as_uri()}/data/{store}.db?mode=ro', uri=True)"
        )
        return StoreBinding(store, path, provenance="injected")

    monkeypatch.setattr(dispatch_module.legacy_codec, "resolve_store", resolve_legacy_store)

    tasks_dir = outside_dir / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    dispatcher = SimulatedDelegate(linked_worktree)
    results = ResultsDir(outside_dir / "results")
    seat = SEATS["gpt-6.1-sol"]
    task = TaskSpec("legacy-resume", seat, "review", "none", 1, ("W1",), PROMPT)
    path = prompt_path(results, task.task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PROMPT)
    argv = ["dispatch", "--agent", seat.agent, "--model", seat.model, "--task-id", task.task_id]
    argv += ["--prompt-file", str(path), "--mode", "read-only", "--language-lane", "--cwd", str(linked_worktree)]
    argv += ["--rules-seat", "core", "--hard-timeout", "3600", "--research-task-family", "ukrainian-review"]
    argv += ["--effort", "high"]
    args_hash = delegate.dispatch_args_sha256(delegate.build_parser().parse_args(argv))
    record = _delegate_record(linked_worktree, PROMPT, args_hash)
    dispatcher.legacy_resume = True
    assert dispatcher.expected_args_sha256(task.task_id, seat, task.kind, path) == args_hash
    assert dispatcher.compose(PROMPT)["effective_prompt_sha256"] == record["effective_prompt_sha256"]
    result = tasks_dir / "legacy.result"
    result.write_text('{"items": []}')
    record.update(
        task_id=task.task_id,
        status="done",
        run_nonce="n1",
        agent=seat.agent,
        model=seat.model,
        prompt_sha256=task.prompt_sha256,
        result_file=str(result),
        result_sha256=sha256_text(result.read_text()),
    )
    if tamper:
        record[tamper] = ["unexpected"] if tamper == "prompt_blocks" else "tampered"
    write_private_json(tasks_dir / f"{task.task_id}.json", record)
    write_private_json(
        results.path("raw", f"{task.task_id}.pending.json"),
        {
            "run_nonce": "n1",
            "prompt_sha256": task.prompt_sha256,
            "workspace": workspace_fingerprint(linked_worktree),
        },
    )
    executor = Executor(
        dispatcher, results, worker_cwd=linked_worktree, workspace=workspace_probe(linked_worktree), spawn_interval=0
    )
    summary = executor.run([task])
    raw = read_json(raw_path(results, task.task_id))
    assert raw["accepted"] is (tamper is None)
    assert summary.accepted == (1 if tamper is None else 0)
    assert not summary.not_run


@pytest.mark.parametrize("store", ["sources", "vesum"])
@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("empty", "empty_override"),
        ("whitespace", "empty_override"),
        ("relative", "relative_override"),
        ("uri", "uri_override"),
        ("missing", "store_missing"),
        ("unset", "store_missing"),
        ("directory", "not_a_file"),
        ("network", "locality_network"),
        ("unknown", "locality_unknown"),
    ],
)
def test_legacy_resume_refuses_unresolvable_read_stores(linked_worktree, tmp_path, monkeypatch, store, kind, reason):
    """Historical verification must not accept arbitrary paths or unavailable stores."""
    from scripts.storage import topology

    local = tmp_path / "fixture.sqlite"
    local.write_bytes(b"fixture")
    monkeypatch.setenv("LU_SOURCES_DB", str(local))
    monkeypatch.delenv("LU_VESUM_DB", raising=False)
    key = f"LU_{store.upper()}_DB"
    if kind == "unset":
        monkeypatch.delenv(key, raising=False)
    else:
        override = {
            "empty": "",
            "whitespace": " \t",
            "relative": "relative.sqlite",
            "uri": local.as_uri(),
            "missing": str(tmp_path / "missing.sqlite"),
            "directory": str(tmp_path),
            "network": str(local),
            "unknown": str(local),
        }[kind]
        monkeypatch.setenv(key, override)
    if kind in {"network", "unknown"}:
        monkeypatch.setattr(topology, "_store_locality", lambda _path: kind)
        # Keep the preceding sources resolution valid when testing VESUM.
        if store == "vesum":
            sources = tmp_path / "sources-fixture.sqlite"
            sources.write_bytes(b"fixture")
            monkeypatch.setenv("LU_SOURCES_DB", str(sources))
            monkeypatch.setattr(topology, "_store_locality", lambda path: kind if path == local else "local")
    if store == "vesum" and kind not in {"empty", "unset"}:
        reason = "legacy_override_unsupported"
    with pytest.raises(DispatchError, match=f"{store} read store refused: {reason}"):
        DelegateComposer(dispatch_module.legacy_codec, linked_worktree).compose(PROMPT)


def test_legacy_resume_refuses_valid_vesum_override_that_changes_historical_hash(
    linked_worktree, tmp_path, monkeypatch
):
    """A valid VESUM override must fail verification instead of changing frozen prompt bytes."""
    local = tmp_path / "override.sqlite"
    local.write_bytes(b"fixture")
    monkeypatch.setenv("LU_SOURCES_DB", str(local))
    monkeypatch.setenv("LU_VESUM_DB", str(local))
    with pytest.raises(DispatchError, match="vesum read store refused: legacy_override_unsupported"):
        DelegateComposer(dispatch_module.legacy_codec, linked_worktree).compose(PROMPT)


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


def test_caller_initiator_matches_delegate_attribution():
    from scripts.agent_runtime.attribution import resolve_invocation_attribution

    assert dispatch_module.caller_initiator() == resolve_invocation_attribution().initiator


def test_preflight_dry_run_is_idempotent_and_a_real_dispatch_still_refuses_reuse(fake):
    """No record omits --force-new. This caller's terminal dry_run passes it. A real id is not reused."""
    dispatcher, prompt, state = fake
    seat = SEATS["claude-opus-5-5"]
    dispatcher.preflight("t-pre", seat, "judge", prompt)
    dispatcher.preflight("t-pre", seat, "judge", prompt)  # the first dry run left a terminal dry_run record
    assert [call[0] for call in _calls(state)] == ["status", "dispatch", "status", "dispatch"]
    dry_calls = [call for call in _calls(state) if "--dry-run" in call]
    assert len(dry_calls) == 2
    assert "--force-new" not in dry_calls[0]
    assert "--force-new" not in dry_calls[1]
    for call in dry_calls:
        assert call[call.index("--research-task-family") + 1] == "ukrainian-review"
    assert not (state / "t-pre.json").exists()
    dispatcher.dispatch("t-real", seat, "writing", prompt, force_new=False)
    with pytest.raises(DispatchError, match="already"):
        dispatcher.dispatch("t-real", seat, "writing", prompt, force_new=False)


@pytest.mark.parametrize(
    ("task_id", "record", "token"),
    [
        ("t-done", {"status": "done", "initiator": CALLER, "task_id": "t-done"}, "status 'done'"),
        ("t-running", {"status": "running", "initiator": CALLER, "task_id": "t-running"}, "status 'running'"),
        ("t-other", {"status": "dry_run", "initiator": "other-owner", "task_id": "t-other"}, "initiator 'other-owner'"),
        ("t-unreadable", None, "output is unreadable"),
    ],
)
def test_preflight_refuses_anything_but_our_terminal_dry_run(fake, task_id: str, record: dict | None, token: str):
    """Each colliding state is refused before dispatch, so the existing record is not archived."""
    dispatcher, prompt, state = fake
    state.mkdir(parents=True, exist_ok=True)
    path = state / f"{task_id}.json"
    before = None
    if record is not None:
        path.write_text(json.dumps(record), encoding="utf-8")
        before = path.read_text(encoding="utf-8")
    with pytest.raises(DispatchError, match="Nothing was archived") as caught:
        dispatcher.preflight(task_id, SEATS["claude-opus-5-5"], "review", prompt)
    assert token in str(caught.value)
    calls = _calls(state)
    assert calls and calls[0][0] == "status"
    assert not any(call[0] == "dispatch" for call in calls)
    if before is None:
        assert not path.exists()
    else:
        assert path.read_text(encoding="utf-8") == before


def test_unknown_kind_is_not_dispatched(fake):
    dispatcher, prompt, state = fake
    with pytest.raises(DispatchError, match="no Ukrainian task family"):
        dispatcher.dispatch("t-essay", SEATS["claude-opus-5-5"], "essay", prompt, force_new=False)
    assert not (state / "calls.jsonl").exists()
