"""Human source bytes through the public CLI; no AI factory or live grants.

The nine-word excerpt is transcribed from the HTML text of Taras Shevchenko,
not OCR, generated wording, or a private teaching source:
https://uk.wikisource.org/w/index.php?title=Садок_вишневий...&oldid=712203

Permission and review records below are explicitly controlled test doubles.
They exercise production eligibility paths but grant no rights to an actual
corpus. This proves build behavior for one human excerpt, not corpus release.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.projects.open_model_data import model_view_exporter as exporter
from tests.test_open_model_view_exporter import source_payload, source_record, write_jsonl

HUMAN_TEXT = "Садок вишневий коло хати,\nХрущі над вишнями гудуть,"
SOURCE_URL = "https://uk.wikisource.org/w/index.php?title=Садок_вишневий...&oldid=712203"


def prepare_inputs(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    record = source_record(HUMAN_TEXT, record_id="record.human-excerpt", source_family="human_literature")
    record["acquisition"]["source_or_catalog_url"] = SOURCE_URL
    record["description"].update(author="Taras Shevchenko", genre="poetry", date="1847")
    record["content"]["hash_scope"] = "UTF-8 bytes of the two-line excerpt, no terminal newline"
    record["rights"]["redistribution"]["status"] = "denied"
    payload = source_payload(HUMAN_TEXT, record_id=record["record_id"])
    payload.update(origin="human_authored", test_fixture=False)
    payload["origin_evidence"]["method"] = "test-double: cited human-authored HTML excerpt, no OCR"
    return record, payload


def run_export(directory: Path, record, payload, operation="local_learning"):
    write_jsonl(directory / "sources.jsonl", [record])
    write_jsonl(directory / "payloads.jsonl", [payload])
    result = subprocess.run([
        sys.executable, "-m", "scripts.projects.open_model_data.model_view_exporter",
        "continued-pretraining", "--source-records", str(directory / "sources.jsonl"),
        "--payloads", str(directory / "payloads.jsonl"), "--origin", payload["origin"],
        "--representation-view", "faithful_literary", "--operation", operation,
        "--output", str(directory / "output.jsonl"),
        "--receipt-output", str(directory / "receipt.json"),
    ], cwd=exporter.ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def materialize_input(directory: Path, record, payload):
    write_jsonl(directory / "sources.jsonl", [record])
    (directory / "source.txt").write_bytes(payload["text"].encode("utf-8"))
    metadata = {key: value for key, value in payload.items() if key not in {"text", "text_sha256"}}
    (directory / "reviewed.json").write_text(json.dumps(metadata), encoding="utf-8")
    result = subprocess.run([
        sys.executable, "-m", "scripts.projects.open_model_data.model_view_exporter",
        "materialize-human-source", "--source-records", str(directory / "sources.jsonl"),
        "--reviewed-payload", str(directory / "reviewed.json"),
        "--source-text", str(directory / "source.txt"), "--output", str(directory / "materialized.jsonl"),
    ], cwd=exporter.ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["payloads_written"] == 1
    materialized = json.loads((directory / "materialized.jsonl").read_text())
    assert materialized == payload
    return materialized


def test_human_source_reaches_local_output_and_reproduces(tmp_path):
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    record, payload = prepare_inputs(first_dir)
    first = run_export(first_dir, record, materialize_input(first_dir, record, payload))
    prepare_inputs(second_dir)
    second = run_export(second_dir, record, materialize_input(second_dir, record, payload))
    assert first == second
    assert first["output"]["records"] == 1
    assert first["counts"]["model_training_eligible_records"] == 1
    assert first["admission"]["operation"] == "local_learning"
    assert (first_dir / "output.jsonl").read_bytes() == (second_dir / "output.jsonl").read_bytes()
    row = json.loads((first_dir / "output.jsonl").read_text())
    assert row["payload"]["text"] == HUMAN_TEXT
    assert row["payload"]["character_mask_spans"] == []
    assert row["lineage"]["source_record_id"] == record["record_id"]
    assert row["lineage"]["source_record_sha256"] == exporter.sha256_text(exporter.canonical_json(record))
    assert row["lineage"]["source_content_sha256"] == exporter.sha256_text(HUMAN_TEXT)
    assert row["origin"] == "human_authored"
    assert first["safety"]["publication_performed"] is False


def test_private_admission_cannot_be_replayed_as_public_export(tmp_path):
    record, payload = prepare_inputs(tmp_path)
    local = run_export(tmp_path, record, payload)
    assert local["output"]["records"] == 1
    public = run_export(tmp_path, record, payload, "public_redistribution")
    assert public["output"]["records"] == 0
    assert public["counts"]["excluded_source_record_not_admitted"] == 1
    assert (tmp_path / "output.jsonl").read_bytes() == b""
    # A fresh grant changes only the public operation decision.
    record["rights"]["redistribution"]["status"] = "granted"
    assert run_export(tmp_path, record, payload, "public_redistribution")["output"]["records"] == 1


@pytest.mark.parametrize("mutation,reason", [
    (lambda r, p: p.update(origin="machine_generated"), "source_origin_not_human_authored"),
    (lambda r, p: r.pop("work_id"), "source_record_not_admitted"),
    (lambda r, p: p.update(source_record_id="record.absent"), "source_record_missing"),
    (lambda r, p: r["rights"]["model_training"].update(status="denied"), "source_record_not_admitted"),
    (lambda r, p: r["review"].update(unresolved=True), "source_record_not_admitted"),
    (lambda r, p: r["usage"].update(role="evaluation_only"), "source_record_not_admitted"),
    (lambda r, p: p["language_span_review"].update(status="incomplete"), "language_span_review_incomplete"),
])
def test_human_source_negative_admission(tmp_path, mutation, reason):
    record, payload = prepare_inputs(tmp_path)
    mutation(record, payload)
    receipt = run_export(tmp_path, record, payload)
    assert receipt["output"]["records"] == 0
    assert receipt["counts"]["excluded_" + reason] == 1


def test_evaluation_text_cannot_enter_human_source_view(tmp_path):
    record, payload = prepare_inputs(tmp_path)
    text = exporter.v011_items(exporter.DEFAULT_V011_MANIFEST)[0]["source"]
    record["content"]["sha256"] = exporter.sha256_text(text)
    payload.update(text=text, text_sha256=exporter.sha256_text(text), source_content_sha256=exporter.sha256_text(text))
    payload["language_span_review"]["character_spans"][0]["end"] = len(text)
    receipt = run_export(tmp_path, record, payload)
    assert receipt["output"]["records"] == 0
    assert receipt["counts"]["excluded_evaluation_contamination_exact_normalized"] == 1


@pytest.mark.parametrize("mutation", [
    lambda r, p: p.update(origin="machine_generated"),
    lambda r, p: p["origin_evidence"].update(status="unresolved"),
    lambda r, p: r["rights"]["model_training"].update(status="denied"),
    lambda r, p: r.pop("work_id"),
    lambda r, p: p.update(source_content_sha256="0" * 64),
])
def test_materialization_denies_invalid_input_without_overwriting(tmp_path, mutation):
    record, payload = prepare_inputs(tmp_path)
    mutation(record, payload)
    write_jsonl(tmp_path / "sources.jsonl", [record])
    (tmp_path / "source.txt").write_bytes(HUMAN_TEXT.encode("utf-8"))
    (tmp_path / "reviewed.json").write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "materialized.jsonl"
    output.write_bytes(b"previous artifact\n")
    with pytest.raises(exporter.ExportError):
        exporter.materialize_human_source(
            source_records_path=tmp_path / "sources.jsonl", reviewed_payload_path=tmp_path / "reviewed.json",
            source_text_path=tmp_path / "source.txt", output=output,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST, v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )
    assert output.read_bytes() == b"previous artifact\n"
