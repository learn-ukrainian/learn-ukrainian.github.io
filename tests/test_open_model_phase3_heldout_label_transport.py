"""Hermetic custody tests for the v2.1 heldout-label transport."""

from __future__ import annotations

import json
import os
import stat
import subprocess
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


def _cycle002_packet_fixture() -> dict[str, object]:
    source = {
        "family_id": "school_textbooks",
        "unit_id": "cycle002-unit",
        "unit_sha256": transport.sha256_value(["cycle002-unit"]),
        "document_or_edition_identity": "cycle002-document",
        "candidate_lane": "phenomenon_strata",
        "source_text": "Він прийшов додому.",
        "source_text_sha256": transport.sha256_bytes("Він прийшов додому.".encode()),
        "frozen_locator_sha256": transport.sha256_value(["cycle002-locator"]),
    }
    return {"rows": [source]}


def _cycle002_label(packet: dict[str, object], *, role: str = "positive") -> dict[str, object]:
    row = packet["rows"][0]  # type: ignore[index]
    source = row["source_text"]  # type: ignore[index]
    if role == "positive":
        gold: dict[str, object] = {
            "kind": "correction",
            "start": 0,
            "end": 3,
            "surface_sha256": transport.sha256_bytes(source[:3].encode("utf-8")),
            "expected_correction": "Вона",
            "expected_correction_sha256": transport.sha256_bytes("Вона".encode()),
        }
    else:
        gold = {"kind": "abstain", "reason": role}
    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "label_state": "supported",
        "phenomenon": "direct_address_vocative",
        "benchmark_role": role,
        "document_or_edition_identity": row["document_or_edition_identity"],
        "clean_modern_eligible": role == "acceptable_control",
        "modern_genre_id": "expository_narrative" if role == "acceptable_control" else None,
        "gold": gold,
    }


def test_cycle002_semantic_label_parser_is_closed_and_requires_explicit_abstention() -> None:
    packet = _cycle002_packet_fixture()
    valid = _cycle002_label(packet)
    parsed = transport._cycle002_parse(json.dumps({"labels": [valid]}).encode("utf-8"), packet)
    assert parsed == [valid]

    malformed = _cycle002_label(packet, role="acceptable_control")
    malformed["gold"] = {"kind": "abstain", "reason": "protected"}
    with pytest.raises(transport.HeldoutLabelTransportError, match="explicit abstention"):
        transport._cycle002_parse(json.dumps({"labels": [malformed]}).encode("utf-8"), packet)

    retargeted = _cycle002_label(packet)
    retargeted["document_or_edition_identity"] = "different-document"
    with pytest.raises(transport.HeldoutLabelTransportError, match="document identity"):
        transport._cycle002_parse(json.dumps({"labels": [retargeted]}).encode("utf-8"), packet)

    unsupported = _cycle002_label(packet)
    unsupported.update(
        {
            "label_state": "abstain",
            "phenomenon": None,
            "benchmark_role": None,
            "clean_modern_eligible": False,
            "modern_genre_id": None,
            "gold": {"kind": "abstain", "reason": "uncertain_or_unsupported"},
        }
    )
    assert transport._cycle002_parse(json.dumps({"labels": [unsupported]}).encode("utf-8"), packet) == [unsupported]


def test_cycle002_floors_fail_closed_without_resampling_or_adjudication() -> None:
    label = _cycle002_label(_cycle002_packet_fixture())
    row = {
        "document_or_edition_identity": label["document_or_edition_identity"],
        "gold": label,
        "disagreement_carrier": {"status": "agreement", "deterministic_assembly_adjudicated": False},
    }
    report = transport._cycle002_floor_report([row])
    assert report["passed"] is False
    assert report["strata"]["direct_address_vocative"]["positive"] == {
        "count": 1,
        "document_count": 1,
        "passed": False,
    }


def test_cycle002_prompt_hash_and_two_pass_contract_are_pinned() -> None:
    assert transport.sha256_file(transport.DEFAULT_CYCLE002_LABEL_PROMPT) == transport.CYCLE002_LABEL_PROMPT_SHA256
    assert transport.CYCLE002_PACKET_LIMIT == 40
    assert [actor["task_id"] for actor in transport.CYCLE002_ACTORS.values()] == [
        "phase3-v2-2-heldout-semantic-label-pass-a",
        "phase3-v2-2-heldout-semantic-label-pass-b",
    ]
    assert all(actor["exact_model"] == "gpt-5.6-sol" for actor in transport.CYCLE002_ACTORS.values())


def test_cycle002_execution_accepts_the_tracked_role_and_evaluation_contracts() -> None:
    execution, role_hash, evaluation_hash = transport._cycle002_execution(
        transport.DEFAULT_CYCLE002_ROLE_CONTRACT,
        transport.DEFAULT_CYCLE002_EVALUATION_CONTRACT,
    )
    assert [item["pass_id"] for item in execution["passes"]] == ["a", "b"]
    assert role_hash == transport.sha256_file(transport.DEFAULT_CYCLE002_ROLE_CONTRACT)
    assert evaluation_hash == transport.sha256_file(transport.DEFAULT_CYCLE002_EVALUATION_CONTRACT)


def _cycle002_runtime_fixture(monkeypatch: pytest.MonkeyPatch) -> tuple[list[dict[str, object]], dict[tuple[str, str], dict[str, object]]]:
    """Tiny hermetic population: production denominators stay enforced by the schema."""
    rows: list[dict[str, object]] = []
    materialized: dict[tuple[str, str], dict[str, object]] = {}
    for number in range(3):
        text = "Наддовгий рядок. " * 64 if number == 0 else f"Речення {number}."
        unit_sha = transport.sha256_value(["runtime", number])
        row = {
            "family_id": "school_textbooks",
            "unit_id": f"runtime-{number}",
            "unit_sha256": unit_sha,
            "reason": "evaluation_only",
            "candidate_lane": "clean_modern" if number == 0 else "phenomenon_strata",
            "source_text_sha256": transport.sha256_bytes(text.encode()),
            "frozen_locator_sha256": transport.sha256_value(["locator", number]),
        }
        source = {
            **row,
            "frozen_locator": {"fixture": number},
            "document_or_edition_identity": f"runtime-document-{number}",
            "source_text": text,
            "source_record": {"fixture": number},
        }
        rows.append(row)
        materialized[(row["unit_id"], row["unit_sha256"])] = source
    monkeypatch.setattr(transport, "CYCLE002_ROW_COUNT", 3)
    monkeypatch.setattr(transport, "_cycle002_partition", lambda _path: rows)
    monkeypatch.setattr(transport, "_cycle002_materialization", lambda _path: materialized)
    monkeypatch.setattr(transport, "_cycle002_execution", lambda *_paths: ({}, "a" * 64, "b" * 64))
    original_validate = transport._validate_schema
    monkeypatch.setattr(
        transport,
        "_validate_schema",
        lambda value, schema_path, definition: None if definition.startswith("cycle002") else original_validate(value, schema_path, definition),
    )
    return rows, materialized


def _cycle002_runtime_raw(packet: dict[str, object]) -> bytes:
    labels: list[dict[str, object]] = []
    for row in packet["rows"]:  # type: ignore[index]
        text = row["source_text"]  # type: ignore[index]
        labels.append(
            {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "label_state": "supported",
                "phenomenon": "direct_address_vocative",
                "benchmark_role": "positive",
                "document_or_edition_identity": row["document_or_edition_identity"],
                "clean_modern_eligible": False,
                "modern_genre_id": None,
                "gold": {
                    "kind": "correction",
                    "start": 0,
                    "end": 1,
                    "surface_sha256": transport.sha256_bytes(text[:1].encode()),
                    "expected_correction": "Я",
                    "expected_correction_sha256": transport.sha256_bytes("Я".encode()),
                },
            }
        )
    return json.dumps({"labels": labels}, ensure_ascii=False, separators=(",", ":")).encode()


def test_cycle002_hermetic_stages_preserve_raw_custody_and_fail_floors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _cycle002_runtime_fixture(monkeypatch)
    partition = tmp_path / "partition.jsonl"
    materialization = tmp_path / "materialization.jsonl"
    partition.write_text("fixture\n", encoding="utf-8")
    materialization.write_text("fixture\n", encoding="utf-8")
    private = tmp_path / "private"
    public_freeze = tmp_path / "public" / "freeze.json"
    freeze = transport.freeze_cycle002(
        partition_path=partition,
        materialization_jsonl=materialization,
        private_dir=private,
        public_receipt_path=public_freeze,
    )
    assert freeze["row_count"] == 3 and freeze["fresh_freeze"] is True
    assert stat.S_IMODE(public_freeze.stat().st_mode) == transport.PRIVATE_FILE_MODE
    manifest = transport.prepare_cycle002(
        freeze_manifest_path=private / "cycle002-freeze-manifest.json",
        partition_path=partition,
        materialization_jsonl=materialization,
        private_dir=private,
        packet_limit=2,
        byte_limit=512,
    )
    assert any(entry["oversize_singleton"] for entry in manifest["passes"]["a"])
    second_packet = private / "cycle002" / "packets" / "a" / "0002.json"
    original_second = second_packet.read_bytes()
    second_packet.write_bytes(b"{}\n")
    os.chmod(second_packet, 0o600)
    with pytest.raises(transport.HeldoutLabelTransportError, match="packet hash drift"):
        transport.run_cycle002(
            manifest_path=private / "cycle002" / "manifest.json",
            packet_index=2,
            pass_id="a",
            private_dir=private,
        )
    second_packet.write_bytes(original_second)
    os.chmod(second_packet, 0o600)
    packet_path = private / "cycle002" / "packets" / "a" / "0001.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    raw = _cycle002_runtime_raw(packet)

    observed: dict[str, object] = {"calls": 0}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        observed["calls"] = int(observed["calls"]) + 1
        observed["command"] = command
        assert kwargs["input"]
        stdout = b"{}" if observed["calls"] == 1 else raw
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr=b"")

    monkeypatch.setattr(transport.subprocess, "run", fake_run)
    with pytest.raises(transport.HeldoutLabelTransportError, match="reviewer response shape drift"):
        transport.run_cycle002(
            manifest_path=private / "cycle002" / "manifest.json",
            packet_index=1,
            pass_id="a",
            private_dir=private,
        )
    invalid_attempt = private / "cycle002" / "raw-attempts" / "a" / "0001" / "001.raw"
    assert invalid_attempt.read_bytes() == b"{}"
    transport.run_cycle002(
        manifest_path=private / "cycle002" / "manifest.json",
        packet_index=1,
        pass_id="a",
        private_dir=private,
    )
    assert observed["command"][2:6] == ["ask-codex", "-", "--from", "operator"]
    assert observed["command"][-4:] == ["--to-model", "gpt-5.6-sol", "--new-session", "--no-timeout"]
    assert "--effort" not in observed["command"]
    selected_attempt = private / "cycle002" / "raw-attempts" / "a" / "0001" / "002.raw"
    assert selected_attempt.read_bytes() == raw
    assert (private / "cycle002" / "raw" / "a" / "0001.raw").read_bytes() == raw
    assert stat.S_IMODE((private / "cycle002" / "raw" / "a" / "0001.raw").stat().st_mode) == 0o600
    selected_receipt = json.loads(
        (private / "cycle002" / "transports" / "a" / "0001.json").read_text(encoding="utf-8")
    )
    assert selected_receipt["raw_attempt_index"] == 2
    with pytest.raises(transport.HeldoutLabelTransportError, match="missing cycle002 transport private artifact"):
        transport.assemble_cycle002(
            manifest_path=private / "cycle002" / "manifest.json",
            private_dir=private,
            public_receipt_path=tmp_path / "public" / "early-labels.json",
        )

    for pass_id in ("a", "b"):
        for entry in manifest["passes"][pass_id]:
            index = entry["packet_index"]
            if pass_id == "a" and index == 1:
                continue
            packet = json.loads((private / "cycle002" / "packets" / pass_id / f"{index:04d}.json").read_text())
            response = tmp_path / f"{pass_id}-{index}.json"
            response.write_bytes(_cycle002_runtime_raw(packet))
            transport.ingest_cycle002(
                manifest_path=private / "cycle002" / "manifest.json",
                packet_index=index,
                pass_id=pass_id,
                raw_response_path=response,
                private_dir=private,
            )
    receipt = transport.assemble_cycle002(
        manifest_path=private / "cycle002" / "manifest.json",
        private_dir=private,
        public_receipt_path=tmp_path / "public" / "labels.json",
    )
    assert receipt["complete"] is False and receipt["author_restart_allowed"] is False


def test_cycle002_pending_runner_is_bounded_ordered_and_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private = transport._private_root(tmp_path / "private", create=True)
    manifest = {"packet_count": 3}
    monkeypatch.setattr(transport, "_cycle002_manifest", lambda *_args: (manifest, private))
    monkeypatch.setattr(transport, "_cycle002_sealed_packet", lambda *_args: [])
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        transport,
        "run_cycle002",
        lambda **kwargs: calls.append((kwargs["pass_id"], kwargs["packet_index"])),
    )
    result = transport.run_pending_cycle002(
        manifest_path=tmp_path / "manifest.json",
        private_dir=private,
        pass_ids=("b", "a"),
        max_packets=4,
    )
    assert calls == [("b", 1), ("b", 2), ("b", 3), ("a", 1)]
    assert result == {
        "requested_pass_ids": ["b", "a"],
        "completed_in_batch": 4,
        "verified_existing": 0,
        "remaining": 2,
        "all_requested_complete": False,
    }
    with pytest.raises(transport.HeldoutLabelTransportError, match="pass selection drift"):
        transport.run_pending_cycle002(
            manifest_path=tmp_path / "manifest.json",
            private_dir=private,
            pass_ids=("a", "a"),
        )
