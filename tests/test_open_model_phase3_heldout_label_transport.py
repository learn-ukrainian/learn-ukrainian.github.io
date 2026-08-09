"""Hermetic custody tests for the v2.1 heldout-label transport."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as roles
from scripts.projects.open_model_data import phase3_heldout_label_transport as transport


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )


def _row(number: int) -> dict[str, object]:
    text = f"fixture text {number}"
    return {
        "family_id": "school_textbooks",
        "unit_id": f"unit-{number:05d}",
        "unit_sha256": transport.sha256_value(["unit", number]),
        "frozen_locator": {"number": number},
        "frozen_locator_sha256": transport.sha256_value(["locator", number]),
        "document_or_edition_identity": f"document-{number // 10}",
        "source_text": text,
        "source_record": {"text": text},
        "source_text_sha256": transport.sha256_bytes(text.encode()),
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    rows = [_row(number) for number in range(transport.MATERIALIZATION_COUNT)]
    materialization = tmp_path / "inputs" / "source.jsonl"
    materialization.parent.mkdir(parents=True)
    materialization.write_bytes(b"".join((transport.canonical_json(row) + "\n").encode() for row in rows))
    materialization_receipt = tmp_path / "inputs" / "materialization-receipt.json"
    _write(
        materialization_receipt,
        {
            "schema_version": "phase3_source_unit_materialization_receipt_v1",
            "private_record_count": transport.MATERIALIZATION_COUNT,
            "private_jsonl_sha256": transport.sha256_file(materialization),
        },
    )
    selected = rows[: transport.ROW_COUNT]
    partition_rows = [
        {
            "family_id": row["family_id"],
            "unit_id": row["unit_id"],
            "unit_sha256": row["unit_sha256"],
            "reason": "evaluation_only",
            "candidate_lane": "clean_modern" if number < transport.ROW_COUNT else "phenomenon_strata",
            "source_text_sha256": row["source_text_sha256"],
            "frozen_locator_sha256": row["frozen_locator_sha256"],
        }
        for number, row in enumerate(rows[:9392])
    ]
    assert len(selected) == transport.ROW_COUNT and len(partition_rows) == 9392
    partition = tmp_path / "inputs" / "partition.jsonl"
    partition.write_bytes(b"".join((transport.canonical_json(row) + "\n").encode() for row in partition_rows))
    freeze_receipt = tmp_path / "inputs" / "freeze-receipt.json"
    _write(
        freeze_receipt,
        {
            "schema_version": "phase3_evaluation_partition_receipt_v1",
            "input_bindings": {
                "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-001",
                "source_materialization_jsonl_sha256": transport.sha256_file(materialization),
            },
            "artifact_hashes": {"partition_manifest_sha256": transport.sha256_file(partition)},
        },
    )
    return partition, materialization, materialization_receipt, freeze_receipt, tmp_path / "private"


def _prepare(tmp_path: Path, *, packet_size: int = 1000) -> tuple[dict[str, object], Path, Path]:
    partition, source, materialization_receipt, freeze_receipt, private = _inputs(tmp_path)
    manifest = transport.prepare(
        partition_path=partition,
        materialization_jsonl=source,
        materialization_receipt_path=materialization_receipt,
        evaluation_freeze_receipt_path=freeze_receipt,
        private_dir=private,
        packet_size=packet_size,
    )
    return manifest, private, partition


def _raw(packet: dict[str, object]) -> bytes:
    labels = [
        {
            "unit_id": row["unit_id"],
            "unit_sha256": row["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
        }
        for row in packet["rows"]
    ]  # type: ignore[index]
    return json.dumps({"labels": labels}, ensure_ascii=False, separators=(",", ":")).encode()


def _ingest_all(manifest: dict[str, object], private: Path, tmp_path: Path) -> None:
    for packet_index in range(1, manifest["packet_count"] + 1):  # type: ignore[operator]
        packet = json.loads((private / "packets" / f"{packet_index:04d}.json").read_text())
        raw = tmp_path / f"reviewer-{packet_index}.json"
        raw.write_bytes(_raw(packet))
        transport.ingest(
            manifest_path=private / "manifest.json",
            packet_index=packet_index,
            raw_response_path=raw,
            private_dir=private,
        )


def test_prepare_ingest_assemble_exact_clean_modern_fixture_and_text_free_receipt(tmp_path: Path) -> None:
    manifest, private, _ = _prepare(tmp_path)
    assert manifest["row_count"] == 2000 and manifest["packet_count"] == 2
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in private.rglob("*.json"))
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o700 for path in private.rglob("*") if path.is_dir())
    _ingest_all(manifest, private, tmp_path)
    receipt = transport.assemble(
        manifest_path=private / "manifest.json",
        private_dir=private,
        public_receipt_path=tmp_path / "public" / "receipt.json",
    )
    assert receipt["complete"] is True and receipt["row_count"] == 2000 and receipt["text_free"] is True
    assert receipt["bindings"]["label_prompt_sha256"] == transport.LABEL_PROMPT_SHA256
    serialized = json.dumps(receipt, sort_keys=True)
    assert all(token not in serialized for token in ('"unit_id"', '"label"', '"source_text"', '"packet_id"'))
    schema = json.loads(transport.DEFAULT_SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(
        {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/publicReceipt"}
    ).validate(receipt)


def test_exact_two_thousand_and_frozen_partition_denominators_fail_closed(tmp_path: Path) -> None:
    partition, source, materialization_receipt, freeze_receipt, private = _inputs(tmp_path)
    rows = partition.read_text().splitlines()
    changed = json.loads(rows[0])
    changed["candidate_lane"] = "phenomenon_strata"
    rows[0] = transport.canonical_json(changed)
    partition.write_text("\n".join(rows) + "\n")
    _write(
        freeze_receipt,
        {
            "schema_version": "phase3_evaluation_partition_receipt_v1",
            "input_bindings": {
                "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-001",
                "source_materialization_jsonl_sha256": transport.sha256_file(source),
            },
            "artifact_hashes": {"partition_manifest_sha256": transport.sha256_file(partition)},
        },
    )
    with pytest.raises(transport.HeldoutLabelTransportError, match="2,000"):
        transport.prepare(
            partition_path=partition,
            materialization_jsonl=source,
            materialization_receipt_path=materialization_receipt,
            evaluation_freeze_receipt_path=freeze_receipt,
            private_dir=private,
        )


@pytest.mark.parametrize(
    "actor",
    [
        {"provider": "google", "model_family": "gemini", "harness": "agy", "exact_model": "gemini-3.6-flash-high"},
        {"provider": "xai", "model_family": "xai", "harness": "grok", "exact_model": "grok-4.5"},
        {
            "role_id": "rule_author_extractor",
            "task_id": "phase3-v2-1-rule-author-extraction",
            "provider": "openai",
            "model_family": "openai",
            "harness": "codex",
            "exact_model": "gpt-5.6-sol",
        },
    ],
)
def test_gemini_grok_and_author_routes_rejected_before_prepare(tmp_path: Path, actor: dict[str, str]) -> None:
    partition, source, materialization_receipt, freeze_receipt, private = _inputs(tmp_path)
    with pytest.raises(transport.HeldoutLabelTransportError, match="only OpenAI"):
        transport.prepare(
            partition_path=partition,
            materialization_jsonl=source,
            materialization_receipt_path=materialization_receipt,
            evaluation_freeze_receipt_path=freeze_receipt,
            private_dir=private,
            actor=actor,
        )
    assert not private.exists()


def test_stale_role_cycle_and_model_are_rejected(tmp_path: Path) -> None:
    partition, source, materialization_receipt, freeze_receipt, private = _inputs(tmp_path)
    role = json.loads(roles.LEDGER_PATH.read_text())
    next(item for item in role["functional_roles"] if item["role_id"] == transport.ROLE_ID)["exact_model"] = "gpt-other"
    role_path = tmp_path / "inputs" / "role.json"
    _write(role_path, role)
    with pytest.raises(transport.HeldoutLabelTransportError, match=r"schema violation|binding drift"):
        transport.prepare(
            partition_path=partition,
            materialization_jsonl=source,
            materialization_receipt_path=materialization_receipt,
            evaluation_freeze_receipt_path=freeze_receipt,
            private_dir=private,
            role_contract_path=role_path,
        )
    freeze = json.loads(freeze_receipt.read_text())
    freeze["input_bindings"]["evaluation_cycle_id"] = "stale"
    _write(freeze_receipt, freeze)
    with pytest.raises(transport.HeldoutLabelTransportError, match="cycle"):
        transport.prepare(
            partition_path=partition,
            materialization_jsonl=source,
            materialization_receipt_path=materialization_receipt,
            evaluation_freeze_receipt_path=freeze_receipt,
            private_dir=private,
        )


def test_prompt_hash_drift_fails_before_private_packet_creation(tmp_path: Path) -> None:
    partition, source, materialization_receipt, freeze_receipt, private = _inputs(tmp_path)
    stale_prompt = tmp_path / "inputs" / "stale-prompt.md"
    stale_prompt.write_text("stale\n", encoding="utf-8")
    with pytest.raises(transport.HeldoutLabelTransportError, match="prompt hash drift"):
        transport.prepare(
            partition_path=partition,
            materialization_jsonl=source,
            materialization_receipt_path=materialization_receipt,
            evaluation_freeze_receipt_path=freeze_receipt,
            label_prompt_path=stale_prompt,
            private_dir=private,
        )
    assert not private.exists()


def test_flat_response_schema_and_semantics_are_closed(tmp_path: Path) -> None:
    _manifest, private, _ = _prepare(tmp_path)
    packet = json.loads((private / "packets" / "0001.json").read_text())
    valid = json.loads(_raw(packet))
    first = valid["labels"][0]
    invalid_labels = []
    extra = dict(first)
    extra["unexpected"] = True
    invalid_labels.append(extra)
    missing = dict(first)
    missing.pop("modern_genre_id")
    invalid_labels.append(missing)
    unknown = dict(first)
    unknown["decision_code"] = "unknown"
    invalid_labels.append(unknown)
    inconsistent_agree = dict(first)
    inconsistent_agree["clean_modern_standard_prose"] = False
    invalid_labels.append(inconsistent_agree)
    inconsistent_reject = dict(first)
    inconsistent_reject["decision_code"] = "reject_mixed_or_uncertain"
    inconsistent_reject["modern_genre_id"] = "scientific_expository"
    invalid_labels.append(inconsistent_reject)
    for number, invalid in enumerate(invalid_labels, start=1):
        response = {"labels": [invalid, *valid["labels"][1:]]}
        raw = tmp_path / f"invalid-{number}.json"
        raw.write_text(json.dumps(response, separators=(",", ":")), encoding="utf-8")
        with pytest.raises(transport.HeldoutLabelTransportError, match=r"label shape|label semantics"):
            transport.ingest(
                manifest_path=private / "manifest.json",
                packet_index=1,
                raw_response_path=raw,
                private_dir=private,
            )


def test_alias_permissions_tamper_and_output_inside_input_fail_closed(tmp_path: Path) -> None:
    manifest, private, partition = _prepare(tmp_path)
    os.chmod(private / "manifest.json", 0o400)
    with pytest.raises(transport.HeldoutLabelTransportError, match="mode drift"):
        transport.ingest(
            manifest_path=private / "manifest.json",
            packet_index=1,
            raw_response_path=tmp_path / "missing",
            private_dir=private,
        )
    os.chmod(private / "manifest.json", 0o600)
    os.symlink(private / "manifest.json", private / "alias")
    with pytest.raises(transport.HeldoutLabelTransportError, match="symlink"):
        transport.assemble(
            manifest_path=private / "manifest.json", private_dir=private, public_receipt_path=tmp_path / "receipt.json"
        )
    assert manifest["row_count"] == 2000

    tampered, second_private, _ = _prepare(tmp_path / "tampered")
    packet_path = second_private / "packets" / "0001.json"
    packet_path.write_text("{}\n", encoding="utf-8")
    os.chmod(packet_path, 0o600)
    raw = tmp_path / "tampered-raw.json"
    raw.write_bytes(b'{"labels":[]}')
    with pytest.raises(transport.HeldoutLabelTransportError, match="packet hash drift"):
        transport.ingest(
            manifest_path=second_private / "manifest.json",
            packet_index=1,
            raw_response_path=raw,
            private_dir=second_private,
        )
    assert tampered["row_count"] == 2000
    with pytest.raises(transport.HeldoutLabelTransportError, match="inside an input"):
        transport.prepare(
            partition_path=partition,
            materialization_jsonl=partition,
            materialization_receipt_path=partition,
            evaluation_freeze_receipt_path=partition,
            private_dir=partition / "nested",
        )
    with pytest.raises(transport.HeldoutLabelTransportError, match="inside an input"):
        transport.prepare(
            partition_path=partition,
            materialization_jsonl=partition,
            materialization_receipt_path=partition,
            evaluation_freeze_receipt_path=partition,
            private_dir=partition.parent,
        )


def test_incomplete_assembly_and_valid_first_retry_are_rejected(tmp_path: Path) -> None:
    _manifest, private, _ = _prepare(tmp_path)
    packet = json.loads((private / "packets" / "0001.json").read_text())
    raw = tmp_path / "valid.json"
    raw.write_bytes(_raw(packet))
    with pytest.raises(transport.HeldoutLabelTransportError, match="retry forbidden"):
        transport.ingest(
            manifest_path=private / "manifest.json",
            packet_index=1,
            raw_response_path=raw,
            private_dir=private,
            attempt_kind="retry-01",
            invalid_first_raw_path=raw,
        )
    transport.ingest(
        manifest_path=private / "manifest.json", packet_index=1, raw_response_path=raw, private_dir=private
    )
    with pytest.raises(transport.HeldoutLabelTransportError, match="missing transport receipt"):
        transport.assemble(
            manifest_path=private / "manifest.json", private_dir=private, public_receipt_path=tmp_path / "receipt.json"
        )


def test_retry_receipt_distinguishes_semantic_failure_from_identity_failure(tmp_path: Path) -> None:
    _manifest, private, _ = _prepare(tmp_path)
    packet = json.loads((private / "packets" / "0001.json").read_text())
    valid = json.loads(_raw(packet))
    invalid = json.loads(_raw(packet))
    invalid["labels"][0]["decision_code"] = "not-a-code"
    invalid["labels"][0]["clean_modern_standard_prose"] = False
    invalid["labels"][0]["modern_genre_id"] = None
    invalid_path = tmp_path / "invalid-semantic.json"
    invalid_path.write_text(json.dumps(invalid, separators=(",", ":")), encoding="utf-8")
    retry_path = tmp_path / "retry.json"
    retry_path.write_text(json.dumps(valid, separators=(",", ":")), encoding="utf-8")
    transport.ingest(
        manifest_path=private / "manifest.json",
        packet_index=1,
        raw_response_path=retry_path,
        private_dir=private,
        attempt_kind="retry-01",
        invalid_first_raw_path=invalid_path,
    )
    receipt = json.loads((private / "transports" / "0001.json").read_text())
    assert receipt["invalid_first_failure"] == "label_schema_or_semantics"
