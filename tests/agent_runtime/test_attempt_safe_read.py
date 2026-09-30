"""Adversarial parent reads: no seat-controlled name can expose host bytes."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.agent_runtime import attempt_boundary as boundary
from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters import agy
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.agent_runtime.attempt_boundary import AttemptReadError, safe_read_attempt_file
from scripts.agent_runtime.result import ParseResult
from scripts.agent_runtime.watchdog import tail_liveness_file_for_debug

SENTINEL = b"FORBIDDEN_PARENT_READ_SENTINEL"
UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


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


@pytest.mark.parametrize("attack,code", [
    ("symlink", "unsafe_path"), ("hardlink", "link_count"),
    ("fifo", "not_regular"), ("directory", "not_regular"),
    ("oversized", "oversized"), ("component", "unsafe_path"),
])
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
        if name == trigger and not swapped:
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
        if name == root.name and not swapped:
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


@pytest.mark.parametrize("attack", ["symlink", "hardlink", "fifo", "oversized", "component"])
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
    else:
        root.rmdir()
        root.symlink_to(forbidden.parent, target_is_directory=True)
    result = CodexAdapter().parse_response(stdout="", stderr="", returncode=0, output_file=target)
    assert not result.ok and result.response == ""
    assert result.failure_code.startswith("attempt_read_")
    assert SENTINEL.decode() not in repr(result)


@pytest.mark.parametrize("reader", [agy._read_transcript_events, agy._conversation_id_from_log,
                                     CodexAdapter()._read_rollout_segment, CodexAdapter._read_rollout_session_id])
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
    monkeypatch.setattr(adapter, "_select_rollout_for_plan", lambda plan: target)
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


def test_agy_transcript_baseline_refuses_symlink(tmp_path):
    app_data = tmp_path / "app-data"
    transcript = agy._brain_transcript_path(app_data, UUID)
    transcript.parent.mkdir(parents=True)
    forbidden = tmp_path / "forbidden"
    forbidden.write_bytes(SENTINEL)
    transcript.symlink_to(forbidden)
    with pytest.raises(AttemptReadError):
        agy._transcript_baseline(app_data, UUID)


def test_runner_v4_origin_refuses_before_recording_output(files, monkeypatch):
    _, target, forbidden = files
    target.unlink()
    target.symlink_to(forbidden)
    from scripts.fleet_comms.request_executor import RequestExecutor

    monkeypatch.setattr(RequestExecutor, "__init__", lambda *a, **k: pytest.fail("must not record unsafe bytes"))
    with pytest.raises(AttemptReadError):
        runner._finalize_v4_runner_origin(
            authorization_id="fixture", claim={"attempt_id": "fixture"},
            plan=InvocationPlan(cmd=[], cwd=target.parent, output_file=target), review_cmd=[],
            stdout_text="", stderr_text="", returncode=0, parse=ParseResult(ok=True, response="own"),
            requested_model="fixture",
        )


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
        loader({
            "output_schema_path": str(target),
            "output_schema_sha256": hashlib.sha256(SENTINEL).hexdigest(),
        })
