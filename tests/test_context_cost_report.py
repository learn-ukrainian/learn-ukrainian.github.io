"""Synthetic fixtures only. Never copy a real session into this test file."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta

import pytest

from scripts.ops import context_cost_report as c


def transcript(tmp_path, harness, records, name="synthetic.jsonl"):
    path = tmp_path / name
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    return path


def call(harness, identity, name="Bash", arguments=None):
    arguments = arguments or {"command": "git status"}
    if harness == "claude":
        return {
            "type": "assistant",
            "message": {
                "model": "claude-synthetic",
                "content": [{"type": "tool_use", "id": identity, "name": name, "input": arguments}],
            },
        }
    return {
        "type": "response_item",
        "payload": {"type": "custom_tool_call", "call_id": identity, "name": name, "arguments": json.dumps(arguments)},
    }


def result(harness, identity, body):
    if harness == "claude":
        return {
            "type": "user",
            "message": {"content": [{"type": "tool_result", "tool_use_id": identity, "content": body}]},
        }
    return {
        "type": "response_item",
        "payload": {"type": "custom_tool_call_output", "call_id": identity, "output": body},
    }


def pair(harness, identity, body="abc", name="Bash", arguments=None):
    return [call(harness, identity, name, arguments), result(harness, identity, body)]


def metadata(harness):
    if harness == "codex":
        return {"type": "turn_context", "payload": {"model": "gpt-synthetic"}}
    return {"type": "assistant", "message": {"model": "claude-synthetic", "content": []}}


def marker(harness):
    return {"type": "compacted"} if harness == "codex" else {"type": "system", "subtype": "compact_boundary"}


def request(harness, n=10):
    usage = {k: n + i for i, k in enumerate(c.TOKENS)}
    if harness == "codex":
        return {"type": "event_msg", "payload": {"type": "token_count", "info": {"last_token_usage": usage}}}
    return {"type": "assistant", "message": {"model": "claude-synthetic", "usage": usage, "content": []}}


def attachment(kind, text):
    return {"type": "attachment", "attachment": {"type": kind, "content": text}}


def metrics(tmp_path, harness, rows):
    return c.parse_session(transcript(tmp_path, harness, [metadata(harness), *rows]), harness)["metrics"]


def amount(m, name):
    return m[name]["bytes"]["value"]


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_cold_start(tmp_path, harness):
    pre = (
        {"type": "session_meta", "payload": {"base_instructions": {"text": "synthetic"}}}
        if harness == "codex"
        else {"type": "system", "systemPrompt": "synthetic"}
    )
    rows = [pre, *pair(harness, "a"), pre, request(harness)]
    m = c.parse_session(transcript(tmp_path, harness, rows), harness)["metrics"]
    assert amount(m, "cold_start") == len(json.dumps(pre, ensure_ascii=False).encode())
    assert m["totals"]["first_call_uncached_input"] == c.value(10)
    absent = metrics(tmp_path, harness, pair(harness, "a"))
    assert absent["cold_start"]["bytes"] == c.unknown("field_absent")


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_hook_reinjection_across_calls(tmp_path, harness):
    rows = [
        attachment("hook_additional_context", "é"),
        request(harness),
        attachment("hook_additional_context", "é"),
        attachment("hook_additional_context", "é"),
        request(harness),
        attachment("hook_additional_context", "different"),
        request(harness),
        attachment("hook_success", "ignored"),
    ]
    m = metrics(tmp_path, harness, rows)
    assert amount(m, "per_call_reinjection") == 2
    assert amount(m, "reminder_attachments") == (0 if harness == "claude" else "unknown")


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_repeated_reads_normalization_and_changed_content(tmp_path, harness):
    rows = [
        *pair(harness, "a", "abc", "Read", {"file_path": "/synthetic/a/../file/"}),
        *pair(harness, "b", "abc", "Read", {"file_path": "/synthetic/file"}),
        *pair(harness, "c", "different", "Read", {"file_path": "/synthetic/file"}),
    ]
    m = metrics(tmp_path, harness, rows)
    assert amount(m, "repeated_reads") == 3
    assert m["changed_reread"] == {"bytes": c.value(9), "count": c.value(1)}
    assert amount(m, "unchanged_polls") == 0


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_url_and_shape_series_stay_separate(tmp_path, harness):
    url = "https://synthetic.invalid/resource?one=secret#fragment"
    rows = [
        *pair(harness, "a", "abc", "WebFetch", {"url": url}),
        *pair(harness, "b", "abc", "WebFetch", {"url": url.replace("one=secret", "two=secret")}),
        *pair(harness, "c", "abc", "Bash", {"command": "cat /synthetic/file"}),
        *pair(harness, "d", "abc", "Bash", {"command": "rg needle /synthetic/file"}),
        *pair(harness, "e", "abc", "Bash", {"command": "cat /synthetic/file"}),
        *pair(harness, "f", "abc", "Bash", {"command": "rg needle /synthetic/file"}),
    ]
    m = metrics(tmp_path, harness, rows)
    assert amount(m, "repeated_reads") == 9
    assert amount(m, "unchanged_polls") == 0
    assert url not in json.dumps(m)


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_raw_payload_and_unpaired_result(tmp_path, harness):
    rows = [
        *pair(harness, "a", "x" * 20_001),
        *pair(harness, "b", "x" * 20_001),
        result(harness, "unpaired-synthetic", "four"),
    ]
    m = metrics(tmp_path, harness, rows)
    assert m["raw_tool_payload"] == {
        "bytes": c.value(40_006),
        "count": c.value(2),
        "share": c.value(1.0),
        "top_shapes": [{"shape": "git-status", "bytes": 40_002}, {"shape": "other", "bytes": 4}],
    }
    assert amount(m, "unchanged_polls") == 0
    assert m["totals"]["paired_tool_calls"] == c.value(2)
    assert m["counters"]["unpaired"] == 1


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_unchanged_polls_and_argument_free_keys(tmp_path, harness):
    rows = [
        *pair(harness, "a", "abc", arguments={"command": "gh pr view 1"}),
        *pair(harness, "b", "abc", arguments={"command": "gh pr view 2 --json state"}),
        *pair(harness, "c", "different", arguments={"command": "gh pr view 2"}),
        *pair(harness, "d", "abc", arguments={"command": "unknown --anything"}),
        *pair(harness, "e", "abc", arguments={"command": "unknown --anything"}),
    ]
    m = metrics(tmp_path, harness, rows)
    assert amount(m, "unchanged_polls") == 3
    assert amount(m, "repeated_reads") == 0


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_rehydration_twenty_tool_calls_and_disjointness(tmp_path, harness):
    rows = pair(harness, "before", "abc", "Read", {"file_path": "/synthetic/file"})
    rows += [marker(harness)]
    rows += pair(harness, "after", "abc", "Read", {"file_path": "/synthetic/file"})
    for i in range(19):
        rows += pair(harness, f"poll{i}", "abc")
    rows += pair(harness, "outside", "abc", "Read", {"file_path": "/synthetic/file"})
    m = metrics(tmp_path, harness, rows)
    assert amount(m, "post_compaction_rehydration") == 3
    assert amount(m, "repeated_reads") == 3
    assert amount(m, "unchanged_polls") == 54
    absent = metrics(tmp_path, harness, pair(harness, "a"))
    assert absent["post_compaction_rehydration"]["bytes"] == c.unknown("no_marker")


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_totals_separate_categories(tmp_path, harness):
    start = metadata(harness) | {"timestamp": "2026-10-01T00:00:00Z"}
    end = request(harness, 20) | {"timestamp": "2026-10-01T00:01:00Z"}
    m = c.parse_session(transcript(tmp_path, harness, [start, request(harness), *pair(harness, "a"), end]), harness)[
        "metrics"
    ]
    assert m["totals"]["wall_seconds"] == c.value(60)
    assert m["totals"]["paired_tool_calls"] == c.value(1)
    assert m["totals"]["model_calls"] == c.value(2)
    assert m["totals"]["provider_tokens"]["input_tokens"] == c.value(30)
    assert m["totals"]["provider_tokens"]["cache_creation_input_tokens"] == c.value(32)
    assert m["totals"]["provider_tokens"]["cache_read_input_tokens"] == c.value(34)
    assert m["totals"]["provider_tokens"]["output_tokens"] == c.value(36)
    assert m["totals"]["first_call_cache_creation"] == c.value(11)


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_reminders_differing_size_and_exclusions(tmp_path, harness):
    rows = []
    for kind in c.REMINDERS:
        rows += [attachment(kind, "initial"), attachment(kind, "é"), attachment(kind, "xyz")]
    rows += [attachment("hook_success", "ignored"), attachment("unknown-type", "ignored")]
    m = metrics(tmp_path, harness, rows)
    assert amount(m, "reminder_attachments") == (20 if harness == "claude" else "unknown")
    assert m["counters"]["other"] == (1 if harness == "claude" else 13)


def test_codex_negative_delta_and_identical_keys_only(tmp_path):
    def usage(total):
        return {
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {"total_token_usage": {"input_tokens": total, "cached_input_tokens": total // 2}},
            },
        }

    m = metrics(tmp_path, "codex", [usage(100), usage(140), marker("codex"), usage(20)])
    assert m["totals"]["provider_tokens"]["input_tokens"] == c.value(160)
    assert m["totals"]["provider_tokens"]["cached_input_tokens"] == c.value(80)
    assert m["totals"]["provider_tokens"]["cache_read_input_tokens"] == c.unknown("field_absent")
    assert m["totals"]["model_calls"] == c.value(3)


def test_function_call_sibling_and_out_of_order_join(tmp_path):
    # function_call is a Codex sibling; Claude uses tool_use, never guessed siblings.
    a, b = pair("codex", "a")
    a["payload"]["type"] = "function_call"
    b["payload"]["type"] = "function_call_output"
    m = metrics(tmp_path, "codex", [b, a, *pair("codex", "b")])
    assert m["totals"]["paired_tool_calls"] == c.value(2)
    assert amount(m, "unchanged_polls") == 3
    fake = {"type": "assistant", "message": {"content": [{"type": "function_call", "id": "fake"}]}}
    assert c.paired_count(transcript(tmp_path, "claude", [fake]), "claude") == 0


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_canonical_object_body_and_utf8(tmp_path, harness):
    m = metrics(tmp_path, harness, [*pair(harness, "a", {"z": "é", "a": 1}), *pair(harness, "b", {"a": 1, "z": "é"})])
    assert amount(m, "unchanged_polls") == len('{"a":1,"z":"é"}'.encode())


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_malformed_truncated_oversized_and_unknown(tmp_path, harness):
    path = transcript(tmp_path, harness, [metadata(harness), {"type": "unknown-event"}, *pair(harness, "a")])
    with path.open("ab") as f:
        f.write(b"x" * (c.MAX_LINE + 77) + b"\n")
        f.write(b'{"type":')
    m = c.parse_session(path, harness)["metrics"]
    assert m["counters"]["oversized_line"] == 1
    assert m["counters"]["malformed_line"] == 1
    assert m["counters"]["truncated_line"] == 1
    assert m["counters"]["other"] == 1
    assert amount(m, "raw_tool_payload") == c.MAX_LINE + 78
    assert m["raw_tool_payload"]["top_shapes"] == [{"shape": "other", "bytes": c.MAX_LINE + 78}]
    assert m["totals"]["paired_tool_calls"] == c.value(1)


def frozen_sample(tmp_path, floor=20):
    root = tmp_path / "codex"
    root.mkdir()
    rows = [metadata("codex")]
    for i in range(floor):
        rows += pair("codex", f"raw-synthetic-id-{i}", "abc", arguments={"command": "cat /synthetic/private-file"})
    path = transcript(root, "codex", rows, "rollout-raw-synthetic-session.jsonl")
    start = datetime.now(UTC) + timedelta(seconds=1)
    manifest = tmp_path / "manifest.json"
    summary = c.freeze(manifest, roots={"codex": root}, run_start=start)
    return manifest, path, summary


def test_freeze_floor_window_exclusions_and_privacy(tmp_path, capsys):
    manifest, path, summary = frozen_sample(tmp_path)
    assert summary["sessions"] == 1
    assert manifest.stat().st_mode & 0o777 == 0o600
    assert summary["manifest_sha256"] == c.hashlib.sha256(manifest.read_bytes()).hexdigest()
    out = c.report(manifest)
    assert out["harnesses"]["codex"]["sessions"] == 1
    assert out["harnesses"]["claude"] == {"status": "unavailable", "reason": "no_eligible_session"}
    for harness in ("grok", "agy", "gemini", "kimi", "cursor"):
        assert out["harnesses"][harness] == {"status": "unavailable", "reason": "no_documented_root"}
    assert c.main(["report", "--manifest", str(manifest)]) == 0
    assert c.main(["report", "--manifest", str(manifest), "--text"]) == 0
    printed = capsys.readouterr()
    for secret in (str(path), "raw-synthetic-session", "/synthetic/private-file", "raw-synthetic-id"):
        assert secret not in printed.out + printed.err + json.dumps(out)
    assert out["sessions"][0]["digest"] == c.digest(str(path))[:16]
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    below = transcript(
        empty_root, "codex", [r for i in range(19) for r in pair("codex", str(i))], "rollout-below.jsonl"
    )
    old = transcript(empty_root, "codex", [r for i in range(20) for r in pair("codex", str(i))], "rollout-old.jsonl")
    future = transcript(empty_root, "codex", [], "rollout-future.jsonl")
    sub = empty_root / "subagents"
    sub.mkdir()
    transcript(sub, "codex", [r for i in range(20) for r in pair("codex", str(i))], "rollout-child.jsonl")
    start = datetime.now(UTC)
    os.utime(old, (start.timestamp() - 8 * 86400,) * 2)
    os.utime(future, (start.timestamp() + 100,) * 2)
    os.utime(below, (start.timestamp() - 1,) * 2)
    summary = c.freeze(manifest, roots={"codex": empty_root}, run_start=start)
    assert summary["sessions"] == 0
    assert summary["excluded"]["below_paired_floor"] == 1


@pytest.mark.parametrize("mutation", ["size", "mtime"])
def test_stale_manifest_never_rescans(tmp_path, mutation):
    manifest, path, _ = frozen_sample(tmp_path)
    frozen_digest = c.digest(str(path))[:16]
    if mutation == "size":
        path.write_text(path.read_text() + "{}\n")
    else:
        st = path.stat()
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1))
    new = path.parent / "rollout-new.jsonl"
    new.write_bytes(path.read_bytes())
    out = c.report(manifest)
    assert out["sessions"] == []
    assert out["skipped"] == [{"digest": frozen_digest, "reason": "stale_session"}]


def test_error_redaction(tmp_path, capsys):
    path = tmp_path / "raw-private-session.json"
    assert c.main(["report", "--manifest", str(path)]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.err) == {"error": "io_error", "digest": c.digest(str(path))[:16]}
    assert str(path) not in captured.err
    path.write_text('{"secret-url":"https://private.invalid/path?secret"}')
    assert c.main(["report", "--manifest", str(path)]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.err)["error"] == "invalid_manifest"
    assert "https://" not in captured.err
    assert "raw-private-session" not in captured.err
    with pytest.raises(SystemExit):
        c.main(["report", "--private-url", "https://private.invalid/path"])
    assert "https://" not in capsys.readouterr().err


@pytest.mark.parametrize(
    ("command", "shape"),
    [
        ("git status --short", "git-status"),
        ("git diff --stat", "git-diff"),
        ("git log -1", "git-log"),
        ("gh pr view 3", "gh-pr-view"),
        ("gh pr diff 3", "gh-pr-diff"),
        ("cat /synthetic/file", "file-read"),
        ("head -n 2 /synthetic/file", "file-read"),
        ("sed -n '1,2p' /synthetic/file", "file-read"),
        ("rg needle /synthetic/file", "file-search"),
        ("pytest test_synthetic.py", "pytest"),
        ("curl http://localhost/api?secret=yes", "curl-local-api"),
        ("git status; cat /synthetic/file", "other"),
        ("git status && gh pr view 3", "other"),
        ("git statusx", "other"),
        ("unknown secret", "other"),
    ],
)
def test_closed_command_shapes(command, shape):
    assert c.command_shape(command, "")[0] == shape


def test_js_wrapper_and_help(capsys):
    shape = c.call_shape("functions.exec", 'await tools.exec_command({cmd: "cat /synthetic/file"})', "")
    assert shape == ("file-read", c.digest("/synthetic/file"), "path")
    assert c.call_shape("functions.exec", 'cmd: "git status", cmd: "git log"', "") == ("other", None, None)
    with pytest.raises(SystemExit) as ex:
        c.main(["report", "--help"])
    assert ex.value.code == 0
    help_text = capsys.readouterr().out
    for section in ("Outputs:", "Exit codes:", "Related:", "--manifest", "--text"):
        assert section in help_text


def test_aggregate_unknown_and_weighted_share():
    assert c.aggregate([c.value(2), c.unknown("field_absent")]) == c.unknown("field_absent")
    assert c.normalize_path("x/../file/", "/synthetic") == c.normalize_path("/synthetic/file", "")
    assert c.normalize_path("/synthetic/link/file", "") != c.normalize_path("/synthetic/target/file", "")
    a, b = c.fresh_metrics(), c.fresh_metrics()
    a["raw_tool_payload"]["bytes"] = c.value(20_001)
    a["totals"]["tool_result_bytes"] = c.value(20_001)
    b["totals"]["tool_result_bytes"] = c.value(3)
    combined = c.aggregate([a, b])
    assert combined["raw_tool_payload"]["share"] == c.value(20_001 / 20_004)


def test_revisited_hash_series_and_large_read_precedence(tmp_path):
    rows = []
    for i, body in enumerate(("abc", "different", "abc")):
        rows += pair("codex", str(i), body, "Read", {"file_path": "/synthetic/file"})
    for i, body in enumerate(("abc", "different", "abc")):
        rows += pair("codex", f"poll{i}", body)
    rows += pair("codex", "large", "x" * 20_001, "Read", {"file_path": "/synthetic/large"})
    rows += [marker("codex")]
    rows += pair("codex", "large2", "x" * 20_001, "Read", {"file_path": "/synthetic/large"})
    m = metrics(tmp_path, "codex", rows)
    assert amount(m, "repeated_reads") == 3
    assert amount(m, "unchanged_polls") == 3
    assert amount(m, "raw_tool_payload") == 40_002
    assert amount(m, "post_compaction_rehydration") == 0
    assert m["changed_reread"]["count"] == c.value(1)


def test_per_model_attribution_and_partial_categories(tmp_path):
    rows = [metadata("codex"), request("codex", 10), *pair("codex", "first")]
    rows += [{"type": "turn_context", "payload": {"model": "gpt-other"}}]
    rows += [request("codex", 20), *pair("codex", "second")]
    parsed = c.parse_session(transcript(tmp_path, "codex", rows), "codex")
    assert parsed["models"]["gpt-synthetic"]["totals"]["provider_tokens"]["input_tokens"] == c.value(10)
    assert parsed["models"]["gpt-other"]["totals"]["provider_tokens"]["input_tokens"] == c.value(20)
    assert parsed["metrics"]["totals"]["provider_tokens"]["input_tokens"] == c.value(30)
    assert parsed["models"]["gpt-other"]["totals"]["paired_tool_calls"] == c.value(1)
    missing = {
        "type": "event_msg",
        "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": 1}}},
    }
    m = metrics(tmp_path, "codex", [request("codex"), missing])
    assert m["totals"]["provider_tokens"]["input_tokens"] == c.value(11)
    assert m["totals"]["provider_tokens"]["cache_read_input_tokens"] == c.unknown("field_absent")


def test_claude_freeze_excludes_agent_files(tmp_path):
    root = tmp_path / "claude"
    root.mkdir()
    rows = [r for i in range(20) for r in pair("claude", f"synthetic-{i}")]
    transcript(root, "claude", rows, "synthetic-session.jsonl")
    transcript(root, "claude", rows, "agent-synthetic.jsonl")
    manifest = tmp_path / "manifest.json"
    summary = c.freeze(manifest, roots={"claude": root}, run_start=datetime.now(UTC) + timedelta(seconds=1))
    assert summary["sessions"] == 1
    assert c.report(manifest)["harnesses"]["claude"]["sessions"] == 1


def test_manifest_error_fields_cannot_echo_text(tmp_path, capsys):
    manifest, _, _ = frozen_sample(tmp_path)
    payload = json.loads(manifest.read_text())
    payload["errors"] = [{"digest": "raw-private-id", "reason": "https://private.invalid/secret"}]
    manifest.write_text(json.dumps(payload))
    assert c.main(["report", "--manifest", str(manifest)]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.err)["error"] == "invalid_manifest"
    assert "private.invalid" not in captured.err
    assert "raw-private-id" not in captured.err


def test_read_failures_redacted_and_known_wrapper_variants(tmp_path, capsys):
    manifest, path, _ = frozen_sample(tmp_path)
    path.unlink()
    out = c.report(manifest)
    assert out["skipped"] == [{"digest": c.digest(str(path))[:16], "reason": "io_error"}]
    assert c.main(["report", "--manifest", str(manifest), "--text"]) == 0
    assert str(path) not in capsys.readouterr().out
    assert c.command_shape("git -C /synthetic --no-pager status", "")[0] == "git-status"
    assert c.command_shape("/synthetic/python -m pytest test_synthetic.py", "")[0] == "pytest"
    assert c.call_shape("Read", {"file_path": "/synthetic/file"}, "")[0] == "file-read"
    assert c.call_shape("Read", {}, "") == ("file-read", None, "path")
    assert c.url_identity("http://[") is None


def test_missing_read_identity_is_unknown_not_zero(tmp_path):
    m = metrics(tmp_path, "codex", [*pair("codex", "a", "abc", "Read", {"offset": 1}), marker("codex")])
    assert m["repeated_reads"]["bytes"] == c.unknown("field_absent")
    assert m["post_compaction_rehydration"]["bytes"] == c.unknown("field_absent")
    assert m["counters"]["read_identity_absent"] == 1
    assert amount(m, "unchanged_polls") == 0
    assert c.call_shape("functions.exec", 'await tools.exec_command({"cmd": "git status"})', "")[0] == "git-status"
    mixed = 'await tools.exec_command({cmd: "git status"}); await tools.some_tool({})'
    assert c.call_shape("functions.exec", mixed, "") == ("other", None, None)


def test_sha_metadata_is_validated_and_absent_is_unknown(tmp_path):
    manifest, _, _ = frozen_sample(tmp_path)
    sha = "a" * 40
    assert c.report(manifest, tool_sha=sha)["tool_sha"] == sha
    assert c.report(manifest)["tool_sha"] == "unknown"
    with pytest.raises(ValueError, match="invalid_manifest"):
        c.report(manifest, tool_sha="private-path-or-invalid-sha")


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_invalid_discriminator_shapes_are_tolerated(tmp_path, harness):
    rows = [
        {"type": []},
        {"type": "event_msg", "payload": {"type": {}}},
        {"type": "attachment", "attachment": {"type": []}},
        *pair(harness, "valid"),
    ]
    m = metrics(tmp_path, harness, rows)
    assert m["counters"]["malformed_line"] == 3
    assert m["totals"]["paired_tool_calls"] == c.value(1)


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_wall_time_requires_two_endpoints_in_event_order(tmp_path, harness):
    first = metadata(harness) | {"timestamp": "2026-10-01T00:01:00Z"}
    rows = [first, *pair(harness, "a")]
    m = c.parse_session(transcript(tmp_path, harness, rows), harness)["metrics"]
    assert m["totals"]["wall_seconds"] == c.unknown("field_absent")
    rows += [{"type": "system", "timestamp": "2026-10-01T00:00:00Z"}]
    m = c.parse_session(transcript(tmp_path, harness, rows), harness)["metrics"]
    assert m["totals"]["wall_seconds"] == c.value(-60)


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_unpaired_small_result_adds_bytes_but_not_large_count(tmp_path, harness):
    m = metrics(tmp_path, harness, [result(harness, "synthetic-unpaired", "four")])
    assert m["raw_tool_payload"]["bytes"] == c.value(4)
    assert m["raw_tool_payload"]["count"] == c.value(0)
    assert m["raw_tool_payload"]["top_shapes"] == [{"shape": "other", "bytes": 4}]
