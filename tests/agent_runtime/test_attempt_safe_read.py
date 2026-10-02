"""Adversarial parent reads: no seat-controlled name can expose host bytes."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime import attempt_boundary as boundary
from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters import agy
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.agent_runtime.attempt_safe_read import AttemptReadError, safe_read_attempt_file
from scripts.agent_runtime.result import ParseResult
from scripts.agent_runtime.watchdog import tail_liveness_file_for_debug

SENTINEL = b"FORBIDDEN_PARENT_READ_SENTINEL"
UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


@pytest.fixture(scope="module")
def scripts_only_tree(tmp_path_factory):
    root = tmp_path_factory.mktemp("safe-read-imports")
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    shutil.copytree(scripts, root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    return root


@pytest.mark.repo_wide
@pytest.mark.parametrize(
    "module",
    [
        "scripts.agent_runtime.attempt_safe_read",
        "scripts.agent_runtime.attempt_boundary",
        "scripts.agent_runtime.runner",
        "scripts.agent_runtime.watchdog",
        "scripts.agent_runtime.sources_read_only",
        "scripts.agent_runtime.review_mcp",
        "scripts.review.receipts.ledger",
        *[
            f"scripts.agent_runtime.adapters.{path.stem}"
            for path in sorted((Path(__file__).resolve().parents[2] / "scripts/agent_runtime/adapters").glob("*.py"))
        ],
    ],
)
def test_scripts_only_import_does_not_load_isolation(scripts_only_tree, module):
    probe = """
import importlib
import importlib.abc
import pathlib
import sys

root = pathlib.Path.cwd()
sys.path[:0] = [str(root), str(root / 'scripts')]
blocked = {'isolation', 'thread_handoff', 'task_identity'}

class RejectIsolation(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.rsplit('.', 1)[-1] in blocked:
            raise AssertionError('isolation stack imported: ' + fullname)

sys.meta_path.insert(0, RejectIsolation())
assert not (root / 'agents_extensions').exists()
module = importlib.import_module(sys.argv[1])
assert pathlib.Path(module.__file__).is_relative_to(root / 'scripts')
assert not any(name.rsplit('.', 1)[-1] in blocked for name in sys.modules)
print('scripts-only import OK')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe, module],
        cwd=scripts_only_tree,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"{module}: stdout={result.stdout!r} stderr={result.stderr!r}"
    assert result.stdout.strip() == "scripts-only import OK"


def test_boundary_reexports_leaf_helpers():
    from scripts.agent_runtime import attempt_safe_read

    for name in ("AttemptReadError", "MAX_ATTEMPT_READ_BYTES", "safe_attempt_file_size", "safe_read_attempt_file"):
        assert getattr(boundary, name) is getattr(attempt_safe_read, name)


@pytest.fixture
def files(tmp_path):
    root = tmp_path / "seat"
    root.mkdir()
    target = root / "output.txt"
    target.write_bytes(b"own return")
    forbidden = tmp_path / "forbidden"
    forbidden.write_bytes(SENTINEL)
    return root, target, forbidden


def test_safe_read_regular_offset_and_exact_bound(files):
    root, target, _ = files
    assert safe_read_attempt_file(target, trusted_root=root, max_bytes=10) == b"own return"
    assert safe_read_attempt_file(target, trusted_root=root, max_bytes=10, offset=4) == b"return"
    assert safe_read_attempt_file(target, max_bytes=10, offset=10) == b""
    target.write_bytes(b"")
    assert safe_read_attempt_file(target, max_bytes=0) == b""


@pytest.mark.parametrize(
    "attack,code",
    [
        ("symlink", "unsafe_path"),
        ("hardlink", "link_count"),
        ("fifo", "not_regular"),
        ("directory", "not_regular"),
        ("oversized", "oversized"),
        ("component", "unsafe_path"),
    ],
)
def test_safe_read_refuses_swapped_names(files, attack, code):
    root, target, forbidden = files
    target.unlink()
    if attack == "symlink":
        target.symlink_to(forbidden)
    elif attack == "hardlink":
        os.link(forbidden, target)
    elif attack == "fifo":
        os.mkfifo(target)
    elif attack == "directory":
        target.mkdir()
    elif attack == "oversized":
        target.write_bytes(b"x" * 11)
    else:
        root.rmdir()
        root.symlink_to(forbidden.parent, target_is_directory=True)
    with pytest.raises(AttemptReadError, match="attempt_read_" + code):
        safe_read_attempt_file(target, trusted_root=root, max_bytes=10)


def test_safe_read_refuses_device():
    with pytest.raises(AttemptReadError, match="not_regular"):
        safe_read_attempt_file(Path("/dev/null"))


@pytest.mark.parametrize("field,value,code", [("st_uid", -1, "wrong_owner"), ("st_nlink", 2, "link_count")])
def test_safe_read_checks_fd_owner_and_links(files, monkeypatch, field, value, code):
    _, target, _ = files
    original = os.fstat

    def fstat(fd):
        info = original(fd)
        values = list(info)
        values[4 if field == "st_uid" else 3] = value
        return os.stat_result(values)

    monkeypatch.setattr(boundary.os, "fstat", fstat)
    with pytest.raises(AttemptReadError, match=code):
        safe_read_attempt_file(target)


@pytest.mark.parametrize("attack", ["leaf", "directory"])
def test_swap_immediately_before_open_never_reads_forbidden(files, monkeypatch, attack):
    root, target, forbidden = files
    original = os.open
    swapped = False

    def open_fd(name, flags, *args, **kwargs):
        nonlocal swapped
        trigger = target.name if attack == "leaf" else root.name
        if Path(name).name == trigger and not swapped:
            swapped = True
            if attack == "leaf":
                target.unlink()
                target.symlink_to(forbidden)
            else:
                root.rename(root.with_name("old-seat"))
                root.symlink_to(forbidden.parent, target_is_directory=True)
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(boundary.os, "open", open_fd)
    with pytest.raises(AttemptReadError, match="unsafe_path"):
        safe_read_attempt_file(target, trusted_root=root)
    assert swapped


def test_swap_after_open_uses_checked_fd_only(files, monkeypatch):
    _, target, forbidden = files
    original = os.fstat
    swapped = False

    def fstat(fd):
        nonlocal swapped
        if not swapped:
            swapped = True
            target.rename(target.with_name("saved-output"))
            target.symlink_to(forbidden)
        return original(fd)

    monkeypatch.setattr(boundary.os, "fstat", fstat)
    assert safe_read_attempt_file(target) == b"own return"
    assert swapped


def test_directory_swap_after_open_cannot_redirect_dirfd(files, monkeypatch):
    root, target, forbidden = files
    original = os.open
    swapped = False

    def open_fd(name, flags, *args, **kwargs):
        nonlocal swapped
        fd = original(name, flags, *args, **kwargs)
        if Path(name).name == root.name and not swapped:
            swapped = True
            root.rename(root.with_name("saved-seat"))
            root.symlink_to(forbidden.parent, target_is_directory=True)
        return fd

    monkeypatch.setattr(boundary.os, "open", open_fd)
    assert safe_read_attempt_file(target, trusted_root=root) == b"own return"
    assert swapped


def test_growth_during_read_is_bounded(files, monkeypatch):
    _, target, _ = files
    original = os.read
    grown = False

    def read(fd, count):
        nonlocal grown
        if not grown:
            grown = True
            with target.open("ab") as writer:
                writer.write(b"extra bytes")
        return original(fd, count)

    monkeypatch.setattr(boundary.os, "read", read)
    with pytest.raises(AttemptReadError, match="oversized"):
        safe_read_attempt_file(target, max_bytes=10)


@pytest.mark.parametrize("offset", [-1, 11])
def test_invalid_offset_is_typed(files, offset):
    with pytest.raises(AttemptReadError, match="invalid_"):
        safe_read_attempt_file(files[1], offset=offset)


def test_outside_and_traversal_are_refused(files):
    root, target, forbidden = files
    for path in (forbidden, root / ".." / "forbidden", root):
        with pytest.raises(AttemptReadError, match="outside_root"):
            safe_read_attempt_file(path, trusted_root=root)
    with pytest.raises(AttemptReadError, match="invalid_bound"):
        safe_read_attempt_file(target, max_bytes=-1)
    with pytest.raises(AttemptReadError, match="outside_root"):
        safe_read_attempt_file(target, trusted_root=Path("relative"))


def test_missing_is_optional_and_refusal_closes_all_fds(files, monkeypatch):
    _, target, forbidden = files
    target.unlink()
    original_open, original_close = os.open, os.close
    active = set()

    def open_fd(*args, **kwargs):
        fd = original_open(*args, **kwargs)
        active.add(fd)
        return fd

    def close_fd(fd):
        active.remove(fd)
        original_close(fd)

    monkeypatch.setattr(boundary.os, "open", open_fd)
    monkeypatch.setattr(boundary.os, "close", close_fd)
    with pytest.raises(FileNotFoundError):
        safe_read_attempt_file(target)
    assert not active
    os.link(forbidden, target)
    with pytest.raises(AttemptReadError, match="link_count"):
        safe_read_attempt_file(target)
    assert not active


@pytest.mark.parametrize("attack", ["symlink", "hardlink", "fifo", "oversized", "component", "nul"])
def test_codex_output_swap_refuses_without_sentinel(files, attack):
    root, target, forbidden = files
    target.unlink()
    if attack == "symlink":
        target.symlink_to(forbidden)
    elif attack == "hardlink":
        os.link(forbidden, target)
    elif attack == "fifo":
        os.mkfifo(target)
    elif attack == "oversized":
        with target.open("wb") as writer:
            writer.truncate(boundary.MAX_ATTEMPT_READ_BYTES + 1)
    elif attack == "nul":
        target = root / "output\0.txt"
    else:
        root.rmdir()
        root.symlink_to(forbidden.parent, target_is_directory=True)
    result = CodexAdapter().parse_response(stdout="", stderr="", returncode=0, output_file=target)
    assert not result.ok and result.response == ""
    assert result.failure_code.startswith("attempt_read_")
    assert SENTINEL.decode() not in repr(result)


@pytest.mark.parametrize(
    "reader",
    [
        agy._read_transcript_events,
        agy._conversation_id_from_log,
        CodexAdapter()._read_rollout_segment,
        CodexAdapter._read_rollout_session_id,
    ],
)
@pytest.mark.parametrize("attack", ["symlink", "hardlink"])
def test_remaining_adapter_reads_refuse_swaps(files, reader, attack):
    _, target, forbidden = files
    target.unlink()
    if attack == "symlink":
        target.symlink_to(forbidden)
    else:
        os.link(forbidden, target)
    with pytest.raises(AttemptReadError):
        reader(target)


def test_codex_prompt_match_and_completion_do_not_swallow_refusal(files, monkeypatch):
    _, target, forbidden = files
    target.unlink()
    target.symlink_to(forbidden)
    adapter = CodexAdapter()
    plan = InvocationPlan(cmd=[], cwd=target.parent, stdin_payload="prompt")
    with pytest.raises(AttemptReadError):
        adapter._rollout_matches_plan(target, plan)
    monkeypatch.setattr(adapter, "_select_rollout_for_plan", lambda plan, **_: target)
    with pytest.raises(AttemptReadError):
        adapter._read_latest_rollout_task_complete(plan)


def test_agy_saved_result_component_swap_is_refused(tmp_path):
    conversation = tmp_path / "conversation"
    transcript = conversation / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    forbidden = tmp_path / "forbidden"
    forbidden.mkdir()
    (forbidden / "output.txt").write_bytes(SENTINEL)
    steps = conversation / "steps"
    steps.symlink_to(forbidden, target_is_directory=True)
    text = f"The output was large and was saved to: {(steps / 'output.txt').as_uri()}"
    match = agy._SAVED_OUTPUT_POINTER_RE.search(text)
    assert match, "positive control: pointer recognized"
    with pytest.raises(AttemptReadError):
        agy._inline_saved_tool_result_pointer(text, transcript_path=transcript)


@pytest.mark.parametrize("attempt", [False, True])
@pytest.mark.parametrize("component", ["step%00/output.txt", "output%00.txt"])
def test_agy_saved_result_nul_pointer_is_typed(tmp_path, monkeypatch, attempt, component):
    conversation = tmp_path / "conversation"
    transcript = conversation / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    (conversation / "steps").mkdir()
    pointer = f"{(conversation / 'steps').as_uri()}/{component}"
    text = f"The output was large and was saved to: {pointer}"
    assert agy._SAVED_OUTPUT_POINTER_RE.search(text), "positive control: pointer recognized"
    monkeypatch.setattr(boundary.os, "read", lambda *a: pytest.fail("malformed pointer must read no bytes"))
    with pytest.raises(AttemptReadError, match=r"^attempt_read_unsafe_path$"):
        agy._inline_saved_tool_result_pointer(
            text,
            transcript_path=transcript,
            trusted_root=tmp_path if attempt else Path("/"),
        )


@pytest.mark.parametrize("steps_dir", ["steps", ".system_generated/steps"])
def test_agy_saved_result_symlinked_conversation_is_refused(tmp_path, steps_dir):
    app_data = tmp_path / "app-data"
    conversation = app_data / "brain" / UUID
    conversation.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    output = outside / steps_dir / "output.txt"
    output.parent.mkdir(parents=True)
    output.write_bytes(SENTINEL)
    assert output.read_bytes() == SENTINEL  # outside-boundary positive control
    conversation.symlink_to(outside, target_is_directory=True)
    transcript = agy._brain_transcript_path(app_data, UUID)
    pointer = conversation / steps_dir / "output.txt"
    text = f"The output was large and was saved to: {pointer.as_uri()}"
    assert agy._SAVED_OUTPUT_POINTER_RE.search(text)
    with pytest.raises(AttemptReadError, match="attempt_read_unsafe_path"):
        agy._inline_saved_tool_result_pointer(text, transcript_path=transcript)


@pytest.mark.parametrize("shape", ["fifo", "step_index", "generic"])
@pytest.mark.parametrize("swap", [False, True])
def test_agy_saved_result_uses_plan_root_after_transcript_read(tmp_path, monkeypatch, shape, swap):
    import json

    root = tmp_path / "runtime"
    root.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: root / "agy.log")
    plan = agy.AgyAdapter().build_invocation(
        prompt="prompt",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"agy_home_override": str(alias / "home"), "review_write_root": str(root)},
    )
    assert plan.metadata["parent_read_root"] == str(root)
    app_data, _ = agy._transcript_read_location(plan)
    transcript = agy._brain_transcript_path(app_data, UUID)
    conversation = transcript.parent.parent.parent
    output = conversation / "steps" / "output.txt"
    output.parent.mkdir(parents=True)
    output.write_text("own saved result")
    transcript.parent.mkdir(parents=True)
    events = [
        {
            "tool_calls": [
                {
                    "name": "call_mcp_tool",
                    "args": {
                        "ServerName": "sources",
                        "ToolName": "search_text",
                        "Arguments": {},
                    },
                }
            ]
        },
        {
            "type": "GENERIC" if shape == "generic" else "MCP_TOOL",
            "content": f"The output was large and was saved to: {output.as_uri()}",
        },
    ]
    if shape != "fifo":
        for index, event in enumerate(events):
            event["step_index"] = index
    transcript.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    Path(plan.env_overrides[agy._AGY_LOG_ENV]).write_text(f"Created conversation {UUID}\n")
    outside = tmp_path / "outside"
    forbidden = outside / "steps" / "output.txt"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_bytes(SENTINEL)
    assert forbidden.read_bytes() == SENTINEL
    original = agy._read_transcript_events
    read_file = agy.safe_read_attempt_file
    saved_roots = []

    def observe_saved_root(path, **kwargs):
        if path == output:
            saved_roots.append(kwargs["trusted_root"])
        return read_file(path, **kwargs)

    def read_then_swap(*args, **kwargs):
        result = original(*args, **kwargs)
        if swap:
            conversation.rename(conversation.with_name("old-conversation"))
            conversation.symlink_to(outside, target_is_directory=True)
        return result

    monkeypatch.setattr(agy, "_read_transcript_events", read_then_swap)
    monkeypatch.setattr(agy, "safe_read_attempt_file", observe_saved_root)
    if swap:
        with pytest.raises(AttemptReadError, match="attempt_read_unsafe_path"):
            agy._parse_transcript_tool_calls(plan)
    else:
        calls = agy._parse_transcript_tool_calls(plan)
        assert calls[0]["result"] == [{"type": "text", "text": "own saved result"}]
    assert saved_roots == [root]


def test_agy_transcript_baseline_refuses_symlink(tmp_path):
    app_data = tmp_path / "app-data"
    transcript = agy._brain_transcript_path(app_data, UUID)
    transcript.parent.mkdir(parents=True)
    forbidden = tmp_path / "forbidden"
    forbidden.write_bytes(SENTINEL)
    transcript.symlink_to(forbidden)
    with pytest.raises(AttemptReadError):
        agy._transcript_baseline(app_data, UUID)


@pytest.mark.parametrize("parsed_failure", [False, True])
@pytest.mark.parametrize("attack", ["symlink", "nul"])
def test_runner_v4_origin_finalizes_refusal_without_unsafe_output(files, monkeypatch, parsed_failure, attack):
    root, target, forbidden = files
    target.unlink()
    if attack == "nul":
        target = root / "output\0.txt"
    else:
        target.symlink_to(forbidden)
    from scripts.fleet_comms.request_executor import RequestExecutor

    recorded = []
    monkeypatch.setattr(RequestExecutor, "__init__", lambda *a, **k: None)
    monkeypatch.setattr(RequestExecutor, "__enter__", lambda self: self)
    monkeypatch.setattr(RequestExecutor, "__exit__", lambda *a: None)
    monkeypatch.setattr(RequestExecutor, "finalize_v4_runner_execution", lambda self, **kw: recorded.append(kw))
    parse = ParseResult(
        ok=not parsed_failure,
        response="own" if not parsed_failure else "",
        failure_code="attempt_read_unsafe_path" if parsed_failure else None,
    )
    final_parse = runner._finalize_v4_runner_origin(
        authorization_id="fixture",
        claim={"attempt_id": "fixture"},
        plan=InvocationPlan(cmd=[], cwd=target.parent, output_file=target),
        review_cmd=[],
        stdout_text="",
        stderr_text="",
        returncode=0,
        parse=parse,
        requested_model="fixture",
    )
    assert len(recorded) == 1
    assert recorded[0]["output_bytes"] == b""
    assert recorded[0]["parse_ok"] is False and recorded[0]["parse_response"] == ""
    assert recorded[0]["stderr"] == b"attempt_read_unsafe_path"
    assert final_parse.failure_code == "attempt_read_unsafe_path"
    assert SENTINEL.decode() not in repr(recorded)


def test_runner_debug_tail_never_returns_forbidden(files):
    _, target, forbidden = files
    target.unlink()
    target.symlink_to(forbidden)
    assert tail_liveness_file_for_debug([target]) == ""


def test_runner_stdin_never_reopens_name(files):
    root, _, forbidden = files
    handle, path = runner._prepare_stdin_handle("own prompt", directory=root)
    try:
        path.unlink()
        path.symlink_to(forbidden)
        assert handle.read() == "own prompt"
    finally:
        runner._cleanup_stdin_temp(path, handle)


@pytest.mark.parametrize("loader", [CodexAdapter._tool_config_flags, agy.load_output_schema])
def test_schema_loaders_cannot_follow_seat_symlink(files, loader):
    import hashlib

    _, target, forbidden = files
    target.unlink()
    target.symlink_to(forbidden)
    with pytest.raises(AttemptReadError, match="unsafe_path"):
        loader(
            {
                "output_schema_path": str(target),
                "output_schema_sha256": hashlib.sha256(SENTINEL).hexdigest(),
            }
        )


def test_prefix_suffix_size_and_tail_ignore_unread_history(files, monkeypatch):
    root, target, _ = files
    with target.open("wb") as writer:
        writer.write(b"prefix\n")
        writer.truncate(boundary.MAX_ATTEMPT_READ_BYTES + 100)
        writer.seek(0, os.SEEK_END)
        writer.write(b"suffix")
    size = target.stat().st_size
    assert safe_read_attempt_file(target, trusted_root=root, max_bytes=7, prefix=True) == b"prefix\n"
    assert safe_read_attempt_file(target, trusted_root=root, offset=size - 6, max_bytes=6) == b"suffix"
    assert safe_read_attempt_file(target, trusted_root=root, max_bytes=6, tail=True) == b"suffix"
    with pytest.raises(AttemptReadError, match="oversized"):
        safe_read_attempt_file(target, trusted_root=root, offset=size - 6, max_bytes=5)
    with pytest.raises(AttemptReadError, match="invalid_bound"):
        safe_read_attempt_file(target, trusted_root=root, tail=True, offset=1)
    monkeypatch.setattr(boundary.os, "read", lambda *a: pytest.fail("size must not read bytes"))
    assert boundary.safe_attempt_file_size(target, trusted_root=root) == size


def test_trusted_root_allows_symlinks_above_it_but_refuses_beneath(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    root = real / "runtime"
    root.mkdir()
    target = root / "output"
    target.write_bytes(b"own return")
    # The known root is resolved before launch; no output path is resolved.
    known_root = (alias / "runtime").resolve()
    assert safe_read_attempt_file(target, trusted_root=known_root) == b"own return"
    sub = root / "sub"
    sub.symlink_to(root, target_is_directory=True)
    with pytest.raises(AttemptReadError, match="unsafe_path"):
        safe_read_attempt_file(sub / "output", trusted_root=known_root)


@pytest.mark.parametrize("returncode", [0, 1])
@pytest.mark.parametrize("large_history", [False, True])
def test_ordinary_codex_newer_huge_rollout_preserves_bound_answer(tmp_path, monkeypatch, returncode, large_history):
    import json
    import time

    home = tmp_path / "codex-home"
    directory = home / "sessions" / "day"
    directory.mkdir(parents=True)
    valid = directory / "rollout-valid.jsonl"
    valid.write_text(json.dumps({"type": "session_meta", "payload": {"id": UUID}}) + "\n")
    if large_history:
        with valid.open("ab") as writer:
            writer.truncate(boundary.MAX_ATTEMPT_READ_BYTES + 1)
    adapter = CodexAdapter()
    monkeypatch.setattr(adapter, "_candidate_rollout_dirs", lambda: [directory])
    plan = adapter.build_invocation(
        prompt="current prompt",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=UUID,
        tool_config={"codex_home_override": str(home)},
    )
    try:
        unrelated = directory / "rollout-unrelated.jsonl"
        with unrelated.open("wb") as writer:
            writer.write(
                json.dumps({"type": "session_meta", "payload": {"id": "ffffffff-bbbb-cccc-dddd-eeeeeeeeeeee"}}).encode()
                + b"\n"
            )
            writer.truncate(boundary.MAX_ATTEMPT_READ_BYTES + 1)
        os.utime(unrelated, (time.time() + 10, time.time() + 10))
        with valid.open("a") as writer:
            writer.write(
                json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": "current prompt"}})
                + "\n"
            )
            writer.write(
                json.dumps(
                    {"type": "event_msg", "payload": {"type": "task_complete", "last_agent_message": "valid answer"}}
                )
                + "\n"
            )
        plan.output_file.write_text("valid answer")
        result = adapter.parse_response(
            stdout="", stderr="", returncode=returncode, output_file=plan.output_file, plan=plan
        )
        assert result.ok and result.response == "valid answer" and result.session_id == UUID
        assert adapter._bound_rollout == valid
    finally:
        plan.output_file.unlink()


@pytest.mark.parametrize("resumed", [False, True])
def test_refused_unbound_rollout_is_nonmatch_but_bound_refusal_raises(files, monkeypatch, resumed):
    import json

    root, target, forbidden = files
    bad = root / "rollout-bad.jsonl"
    bad.symlink_to(forbidden)
    good = root / "rollout-good.jsonl"
    good.write_text(
        json.dumps({"type": "session_meta", "payload": {"id": UUID}})
        + "\n"
        + json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": "prompt"}})
        + "\n"
    )
    adapter = CodexAdapter()
    adapter._rollout_read_root = root
    adapter._resume_session_id = UUID if resumed else None
    monkeypatch.setattr(adapter, "_candidate_rollout_dirs", lambda: [root])
    plan = InvocationPlan(cmd=[], cwd=root, stdin_payload="prompt")
    assert adapter._select_rollout_for_plan(plan) == good
    good.unlink()
    good.symlink_to(forbidden)
    with pytest.raises(AttemptReadError, match="unsafe_path"):
        adapter._select_rollout_for_plan(plan)
    assert target.read_bytes() == b"own return"


def test_ordinary_codex_symlinked_temp_and_home_ancestors(tmp_path, monkeypatch):
    import json

    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    home = alias / "home"
    home.mkdir()
    adapter = CodexAdapter()
    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.tempfile.gettempdir", lambda: str(alias))
    plan = adapter.build_invocation(
        prompt="prompt",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"codex_home_override": str(home)},
    )
    try:
        directory = adapter._candidate_rollout_dirs()
        assert not directory
        from datetime import UTC, datetime

        day = datetime.now(UTC)
        directory = real / "home" / "sessions" / day.strftime("%Y/%m/%d")
        directory.mkdir(parents=True)
        rollout = directory / "rollout-own.jsonl"
        rollout.write_text(
            json.dumps({"type": "session_meta", "payload": {"id": UUID}})
            + "\n"
            + json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": "prompt"}})
            + "\n"
        )
        (alias / plan.output_file.name).write_text("valid answer")
        result = adapter.parse_response(stdout="", stderr="", returncode=0, output_file=plan.output_file, plan=plan)
        assert result.ok and result.response == "valid answer" and result.session_id == UUID
    finally:
        plan.output_file.unlink()


def test_agy_resume_baseline_and_reads_under_symlinked_ancestor(tmp_path, monkeypatch):
    import json

    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    home = alias / "home"
    app_data = home / ".gemini" / "antigravity-cli"
    transcript = agy._brain_transcript_path(app_data, UUID)
    transcript.parent.mkdir(parents=True)
    with transcript.open("wb") as writer:
        writer.truncate(boundary.MAX_ATTEMPT_READ_BYTES + 1)
    size = transcript.stat().st_size
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: alias / "agy.log")
    plan = agy.AgyAdapter().build_invocation(
        prompt="prompt",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=UUID,
        tool_config={"agy_home_override": str(home)},
    )
    assert plan.metadata[agy._TRANSCRIPT_BASELINE_KEY]["offset"] == size
    events = [{"type": "USER_INPUT", "text": "prompt"}, {"type": "PLANNER_RESPONSE", "text": "answer"}]
    with transcript.open("a") as writer:
        writer.write("\n".join(json.dumps(event) for event in events) + "\n")
    Path(plan.env_overrides[agy._AGY_LOG_ENV]).write_text(f"Created conversation {UUID}\n")
    bound = agy._invocation_transcript(plan)
    assert bound is not None and bound.events == events and bound.unreadable_lines == 0


@pytest.mark.parametrize("loader", [CodexAdapter._tool_config_flags, agy.load_output_schema])
def test_ordinary_schema_under_symlinked_ancestor(tmp_path, loader):
    import hashlib

    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    schema = alias / "schema.json"
    payload = b'{"type":"object"}'
    schema.write_bytes(payload)
    assert loader({"output_schema_path": str(schema), "output_schema_sha256": hashlib.sha256(payload).hexdigest()})


def test_debug_tail_seeks_and_bounds_read_bytes(files, monkeypatch):
    _, target, _ = files
    with target.open("wb") as writer:
        writer.truncate(boundary.MAX_ATTEMPT_READ_BYTES + 1)
        writer.seek(0, os.SEEK_END)
        writer.write(b"useful tail")
    original_read = os.read
    consumed = []

    def read(fd, count):
        data = original_read(fd, count)
        consumed.append(len(data))
        return data

    monkeypatch.setattr(boundary.os, "read", read)
    assert tail_liveness_file_for_debug([target], max_bytes=11) == "useful tail"
    assert sum(consumed) == 11


def test_agy_attempt_root_remains_enforced_if_plan_override_changes(files):
    root, _, forbidden = files
    plan = InvocationPlan(
        cmd=[],
        cwd=root,
        env_overrides={agy._AGY_APP_DATA_ENV: str(forbidden.parent)},
        metadata={
            "parent_read_root": str(root),
            "attempt_read_root": True,
            "agy_app_data_path": str(root / "app-data"),
            "agy_app_data_root": str(root / "app-data"),
        },
    )
    app_data, read_root = agy._transcript_read_location(plan)
    assert app_data == forbidden.parent and read_root == root
    with pytest.raises(AttemptReadError, match="outside_root"):
        agy._read_transcript_events(forbidden, trusted_root=read_root)
