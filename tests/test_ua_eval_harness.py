from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness.evaluate_model import (
    EvaluationError,
    generate_baseline,
    import_model_responses,
    load_manifest,
    load_saved_responses,
    prepare_requests,
)
from scripts.projects.ua_eval_harness.run_codex_baseline import (
    RunnerError,
    _child_environment,
    _load_source_only_requests,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_prepare_requests_contains_source_only_and_complete_coverage() -> None:
    _, items = load_manifest()
    rows = prepare_requests()

    assert rows[0]["gold_fields_supplied"] == []
    assert rows[0]["request_count"] == 677
    assert rows[0]["prompt_path"] == "data/projects/ua_eval_harness/minimal_edit_prompt_v1.txt"
    assert len(rows) == len(items) + 1
    assert set(rows[1]) == {
        "type",
        "item_id",
        "source",
        "source_sha256",
        "prompt_sha256",
        "request_sha256",
    }
    assert not {"target", "references", "edits"} & set(rows[1])


def test_identity_baseline_round_trips_saved_response_contract(tmp_path: Path) -> None:
    rows = generate_baseline("identity")
    output = tmp_path / "identity.jsonl"
    _write_jsonl(output, rows)
    manifest, items = load_manifest()

    header, responses = load_saved_responses(output, manifest=manifest, items=items)

    assert header["model"] == "identity-v1"
    assert header["gold_fields_supplied"] == []
    assert len(responses) == 677


def test_saved_response_tampering_fails_closed(tmp_path: Path) -> None:
    rows = generate_baseline("identity")
    rows[1]["raw_response"] += " змінено"
    output = tmp_path / "tampered.jsonl"
    _write_jsonl(output, rows)
    manifest, items = load_manifest()

    with pytest.raises(EvaluationError, match="response hash mismatch"):
        load_saved_responses(output, manifest=manifest, items=items)


def test_import_model_responses_requires_exact_source_only_coverage(tmp_path: Path) -> None:
    requests = prepare_requests()
    requests_path = tmp_path / "requests.jsonl"
    outputs_path = tmp_path / "outputs.jsonl"
    metadata_path = tmp_path / "metadata.json"
    _write_jsonl(requests_path, requests)
    _write_jsonl(
        outputs_path,
        [{"item_id": row["item_id"], "raw_response": row["source"]} for row in requests[1:]],
    )
    metadata_path.write_text(
        json.dumps(
            {
                "run_id": "real-test",
                "provider": "provider",
                "model": "model",
                "model_version": "version",
                "decoding": {"temperature": 0},
                "runner_version": "runner-version",
            }
        ),
        encoding="utf-8",
    )

    rows = import_model_responses(
        requests_path=requests_path,
        model_output_path=outputs_path,
        metadata_path=metadata_path,
    )

    assert rows[0]["generator_kind"] == "model"
    assert rows[0]["gold_fields_supplied"] == []
    assert len(rows) == 678


def test_import_rejects_gold_shaped_model_output(tmp_path: Path) -> None:
    requests = prepare_requests()
    requests_path = tmp_path / "requests.jsonl"
    outputs_path = tmp_path / "outputs.jsonl"
    metadata_path = tmp_path / "metadata.json"
    _write_jsonl(requests_path, requests)
    outputs = [{"item_id": row["item_id"], "raw_response": row["source"]} for row in requests[1:]]
    outputs[0]["target"] = "forbidden"
    _write_jsonl(outputs_path, outputs)
    metadata_path.write_text(
        json.dumps(
            {
                "run_id": "real-test",
                "provider": "provider",
                "model": "model",
                "model_version": "version",
                "decoding": {},
                "runner_version": "runner-version",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvaluationError, match="unsupported fields"):
        import_model_responses(
            requests_path=requests_path,
            model_output_path=outputs_path,
            metadata_path=metadata_path,
        )


def test_saved_run_rejects_manifest_hash_drift(tmp_path: Path) -> None:
    rows = generate_baseline("identity")
    drifted = copy.deepcopy(rows)
    drifted[0]["manifest_payload_sha256"] = "0" * 64
    output = tmp_path / "drifted.jsonl"
    _write_jsonl(output, drifted)
    manifest, items = load_manifest()

    with pytest.raises(EvaluationError, match="manifest payload mismatch"):
        load_saved_responses(output, manifest=manifest, items=items)


def test_codex_runner_accepts_only_frozen_source_request_fields(tmp_path: Path) -> None:
    requests = prepare_requests()
    path = tmp_path / "requests.jsonl"
    _write_jsonl(path, requests)

    header, rows = _load_source_only_requests(path)

    assert header["gold_fields_supplied"] == []
    assert len(rows) == 677
    assert set(rows[0]) == {"item_id", "source"}


def test_codex_runner_rejects_gold_in_request_row(tmp_path: Path) -> None:
    requests = prepare_requests()
    requests[1]["target"] = "forbidden"
    path = tmp_path / "requests.jsonl"
    _write_jsonl(path, requests)

    with pytest.raises(RunnerError, match="non-contract fields"):
        _load_source_only_requests(path)


def test_codex_runner_does_not_forward_unrelated_environment_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UA_EVAL_TEST_SECRET", "must-not-leak")
    monkeypatch.setenv("PATH", "/bin")

    child_environment = _child_environment()

    assert child_environment["PATH"] == "/bin"
    assert "UA_EVAL_TEST_SECRET" not in child_environment
