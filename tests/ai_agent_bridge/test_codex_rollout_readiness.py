"""Real-file, fake-process regressions for D1–D6 of #10133."""

import json
from unittest.mock import Mock

import pytest

from scripts.ai_agent_bridge import _ui_codex as ui


def event(kind, **fields):
    return json.dumps({"type": "event_msg", "payload": {"type": kind, **fields}}).encode() + b"\n"


def write(path, *records):
    path.write_bytes(b"".join(records))
    return path


def test_d1_payload_id_cannot_close_an_open_turn(tmp_path):
    path = write(tmp_path / "rollout.jsonl", event("task_started"), json.dumps({
        "type": "event_msg", "payload": {
            "id": "task_complete", "type": "agent_message", "text": "x" * (1024 * 1024 + 1),
        },
    }).encode() + b"\n")
    assert ui.rollout_is_ready(path) == (False, "start_event:task_started")


def test_d1_nested_envelope_cannot_close_an_open_turn(tmp_path):
    path = write(tmp_path / "rollout.jsonl", event("task_started"), json.dumps({
        "nested": {"type": "event_msg", "payload": {"type": "task_complete"}},
        "type": "response_item", "payload": {"text": "x" * (1024 * 1024 + 1)},
    }).encode() + b"\n")
    assert ui.rollout_is_ready(path) == (False, "start_event:task_started")


def test_d2_completion_record_over_16_mib_is_ready_with_bounded_memory(tmp_path):
    # No whole record is materialized by the reader (or by this fixture writer).
    import tracemalloc

    path = tmp_path / "rollout.jsonl"
    with path.open("wb") as stream:
        stream.write(event("task_started"))
        stream.write(b'{"type":"event_msg","payload":{"last_agent_message":"')
        for _ in range(17):
            stream.write(b"x" * (1024 * 1024))
        # Type after the huge body proves prefix scanning is insufficient.
        stream.write(b'","type":"task_complete"}}\n')
    tracemalloc.start()
    try:
        assert ui.rollout_is_ready(path) == (True, "end_event:task_complete")
        _, peak = tracemalloc.get_traced_memory()
        assert peak < 2 * 1024 * 1024
    finally:
        tracemalloc.stop()


def test_d3_append_between_read_and_final_stat_is_rescanned(tmp_path):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"))
    def append():
        with path.open("ab") as stream:
            stream.write(event("task_started"))
    hook = Mock()
    appended = False
    def race():
        nonlocal appended
        hook()
        if not appended:
            append()
            appended = True
    reader = ui.RolloutReader(after_read=race)
    assert ui.rollout_is_ready(path, reader=reader) == (False, "start_event:task_started")
    assert hook.call_count == 2


def test_d3_continuously_appending_rollout_is_busy(tmp_path):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"))
    def append():
        with path.open("ab") as stream:
            stream.write(event("task_complete"))
    hook = Mock(side_effect=append)
    reader = ui.RolloutReader(after_read=hook)
    assert ui.rollout_is_ready(path, reader=reader) == (False, "rollout_changing")
    assert hook.call_count == 3


@pytest.mark.parametrize("record,reason", [
    (b'{"n":' + b"1" * 5000 + b'}\n', "ValueError"),
    (b'{"n":' + b"[" * 2000 + b"0" + b"]" * 2000 + b'}\n', "RecursionError"),
    (b'{"text":"\xff"}\n', "UnicodeDecodeError"),
], ids=["integer", "nesting", "utf8"])
def test_d4_decoder_failure_is_typed_busy(tmp_path, record, reason):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"), record)
    assert ui.rollout_is_ready(path) == (False, f"decode_error:{reason}")


def test_d5_partial_final_line_is_busy_and_recovers_on_append(tmp_path):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"), event("task_started")[:-1])
    reader = ui.RolloutReader()
    assert ui.rollout_is_ready(path, reader=reader) == (False, "partial_final_line")
    with path.open("ab") as stream:
        stream.write(b"\n")
    assert ui.rollout_is_ready(path, reader=reader) == (False, "start_event:task_started")


def test_d5_malformed_record_before_deciding_event_is_busy(tmp_path):
    path = write(tmp_path / "rollout.jsonl", b'{"broken":}\n', event("task_complete"))
    ready, reason = ui.rollout_is_ready(path)
    assert not ready and reason.startswith("decode_error:")


def test_d5_abort_without_turn_id_closes_then_completed_restart_is_ready(tmp_path):
    path = write(tmp_path / "rollout.jsonl", event("task_started", turn_id="a"), event("turn_aborted"))
    reader = ui.RolloutReader()
    assert ui.rollout_is_ready(path, reader=reader) == (True, "end_event:turn_aborted")
    with path.open("ab") as stream:
        stream.write(event("task_started", turn_id="b") + event("task_complete", turn_id="b"))
    assert ui.rollout_is_ready(path, reader=reader) == (True, "end_event:task_complete")


def test_d6_old_unmatched_start_never_becomes_ready(tmp_path):
    path = write(tmp_path / "rollout.jsonl", b'{"timestamp":"2000-01-01T00:00:00Z","type":"event_msg","payload":{"type":"task_started"}}\n')
    import os
    os.utime(path, (1, 1))
    assert ui.rollout_is_ready(path) == (False, "start_event:task_started")


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
@pytest.mark.parametrize("chunk_size", [1, 7, 64 * 1024])
def test_chunk_boundaries_escapes_utf8_and_field_order(tmp_path, monkeypatch, newline, chunk_size):
    monkeypatch.setattr(ui, "_READ_CHUNK", chunk_size)
    record = b'{"payload":{"nested":{"type":"task_started"},"text":"' + 'ї'.encode() + b'\\\\\\\"\\u1234","t\\u0079pe":"task_complete"},"type":"event_msg"}'
    path = write(tmp_path / "rollout.jsonl", event("task_started"), record + newline)
    assert ui.rollout_is_ready(path) == (True, "end_event:task_complete")


@pytest.mark.parametrize("record", [
    b'{"type":"event_msg","type":"event_msg","payload":{"type":"task_complete"}}\n',
    b'{"type":"event_msg","payload":{"type":"task_complete","type":"agent_message"}}\n',
    b'{"type":"event_msg","payload":{"type":"task_complete"},"payload":{}}\n',
    b'{"type":"event_msg","payload":{"type":"task_complete"}} {}\n',
    b'[]\n', b'false\n', b'{"text":"bad\\z"}\n', b'{"text":"bad\\u000z"}\n',
    b'{"text":"unterminated}\n', b'{"text":"bad\x01"}\n',
    b'{"text":"' + b'x' * 300 + b'\\z"}\n',
])
def test_invalid_or_ambiguous_json_never_reports_ready(tmp_path, record):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"), record)
    ready, reason = ui.rollout_is_ready(path)
    assert not ready and reason.startswith("decode_error:")


@pytest.mark.parametrize("change", ["truncate", "rotate", "same-size-rewrite", "other-file"])
def test_incremental_reader_resets_on_replacement(tmp_path, change):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"), event("task_complete"))
    reader = ui.RolloutReader()
    assert ui.rollout_is_ready(path, reader=reader)[0]
    if change == "truncate":
        write(path, event("task_started"))
    elif change == "rotate":
        replacement = write(tmp_path / "replacement", event("task_started"))
        replacement.replace(path)
    elif change == "other-file":
        path = write(tmp_path / "other", event("task_started"))
    else:
        record = event("task_started")
        write(path, record, b" " * (reader.offset - len(record) - 1) + b"\n")
    assert ui.rollout_is_ready(path, reader=reader) == (False, "start_event:task_started")


def test_incremental_poll_reads_only_new_bytes(tmp_path, monkeypatch):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"))
    reader = ui.RolloutReader()
    assert ui.rollout_is_ready(path, reader=reader)[0]
    offset = reader.offset
    feed = Mock(side_effect=AssertionError("unchanged rollout must not be reparsed"))
    with monkeypatch.context() as scoped:
        scoped.setattr(ui._RolloutRecord, "feed", feed)
        assert ui.rollout_is_ready(path, reader=reader)[0]
    with path.open("ab") as stream:
        stream.write(event("task_started"))
    assert ui.rollout_is_ready(path, reader=reader)[0] is False
    assert reader.offset == offset + len(event("task_started"))


def test_missing_rollout_is_typed_busy(tmp_path):
    assert ui.rollout_is_ready(tmp_path / "missing") == (False, "read_error:FileNotFoundError")


def test_transient_missing_file_is_retried(tmp_path):
    path = tmp_path / "rollout.jsonl"
    reader = ui.RolloutReader()
    assert ui.rollout_is_ready(path, reader=reader) == (False, "read_error:FileNotFoundError")
    write(path, event("task_complete"))
    assert ui.rollout_is_ready(path, reader=reader) == (True, "end_event:task_complete")


def test_rotation_during_scan_rescans_new_inode(tmp_path):
    path = write(tmp_path / "rollout.jsonl", event("task_complete"))
    replacement = write(tmp_path / "replacement.jsonl", event("task_started"))
    replaced = False
    def rotate():
        nonlocal replaced
        if not replaced:
            replacement.replace(path)
            replaced = True
    assert ui.rollout_is_ready(path, reader=ui.RolloutReader(after_read=rotate)) == (False, "start_event:task_started")


def test_long_escaped_string_cannot_supply_lifecycle_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "_READ_CHUNK", 7)
    text = '"type":"event_msg","payload":{"type":"task_complete"}\\' * 20
    path = write(tmp_path / "rollout.jsonl", event("task_started"), event("agent_message", text=text))
    assert ui.rollout_is_ready(path) == (False, "start_event:task_started")


def test_unterminated_utf8_and_poisoned_history_remain_busy(tmp_path):
    path = write(tmp_path / "rollout.jsonl", b'{"text":"\xd1\n')
    reader = ui.RolloutReader()
    assert ui.rollout_is_ready(path, reader=reader) == (False, "decode_error:UnicodeDecodeError")
    with path.open("ab") as stream:
        stream.write(event("task_complete"))
    assert ui.rollout_is_ready(path, reader=reader) == (False, "decode_error:UnicodeDecodeError")
    write(path, event("task_complete"))
    assert ui.rollout_is_ready(path, reader=reader) == (True, "end_event:task_complete")
