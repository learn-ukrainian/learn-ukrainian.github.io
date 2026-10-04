"""Strict readers retain blank-record rejection and ordinary newline handling."""

import importlib
import json

import pytest
from jsonl_reader_cases import VALUE

CASES = [
    ("scripts.projects.ua_eval_harness.run_model_batch", "_read_jsonl", "RunnerError"),
    ("scripts.projects.ua_eval_harness.build_v02_review_packet", "read_jsonl", "PacketError"),
    ("scripts.projects.ua_eval_harness.verify_release_freeze", "_read_jsonl", "FreezeError"),
    ("scripts.projects.ua_eval_harness.verify_release_freeze_v011", "_read_jsonl", "FreezeError"),
    ("scripts.ingest.owned_books_ingest", "_cached_jsonl_records", "JSONDecodeError"),
    ("scripts.verification.stress_comparison", "_replay_forms", "JSONDecodeError"),
]


@pytest.mark.parametrize("module_name, function, error", CASES)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""])
def test_strict_reader_preserves_records_and_rejects_interior_blanks(module_name, function, error, ending, tmp_path):
    module = importlib.import_module(module_name)
    fn = getattr(module, function)
    record = {"probe": VALUE, "form": VALUE}
    # Frozen release readers retain their original separator semantics. Use
    # escaped JSON for those ordinary-newline/blank-record checks; mutable
    # readers additionally preserve literal Unicode separators.
    frozen = module_name in {
        "scripts.projects.ua_eval_harness.run_model_batch",
    }
    raw = json.dumps(record, ensure_ascii=frozen)
    path = tmp_path / "fixture.jsonl"
    path.write_bytes((raw + ending).encode())
    value = raw + ending if function == "_cached_jsonl_records" else path
    assert fn(value) == ([VALUE] if function == "_replay_forms" else [record])
    path.write_bytes((raw + "\n\n" + raw + ending).encode())
    value = path.read_text() if function == "_cached_jsonl_records" else path
    error_type = json.JSONDecodeError if error == "JSONDecodeError" else getattr(module, error)
    with pytest.raises(error_type):
        fn(value)
