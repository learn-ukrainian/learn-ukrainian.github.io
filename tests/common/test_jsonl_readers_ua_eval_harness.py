"""Unicode boundary regressions through real ua_eval_harness readers (#9556)."""

import json

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.projects.ua_eval_harness.analyze_v011_evidence", "read_jsonl", 64),
        ("scripts.projects.ua_eval_harness.build_v02_review_packet", "read_jsonl", 64),
        ("scripts.projects.ua_eval_harness.run_codex_baseline", "_read_jsonl", 45),
        ("scripts.projects.ua_eval_harness.verify_release_freeze", "_read_jsonl", 131),
        ("scripts.projects.ua_eval_harness.verify_release_freeze_v011", "_read_jsonl", 194),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r", ""])
def test_frozen_successor_readers_preserve_unicode_field_text(separator, ending, tmp_path):
    from scripts.projects.ua_eval_harness import evaluate_model, run_model_batch

    record = {"text": f"before{separator}after"}
    raw = json.dumps(record, ensure_ascii=False)
    path = tmp_path / "records.jsonl"
    path.write_bytes((raw + (ending or "\n") + raw + ending).encode())
    assert evaluate_model._read_jsonl(path) == [record, record]
    assert run_model_batch._read_jsonl(path) == [record, record]
    event = {"type": "text", "part": {"type": "text", "text": record["text"]}}
    stream = json.dumps(event, ensure_ascii=False) + ending
    assert run_model_batch._ndjson_assistant_text(stream) == record["text"]
