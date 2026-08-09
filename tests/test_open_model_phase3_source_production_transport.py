"""Hermetic tests for the Phase 3 v2.1 all-family source transport."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_source_production_transport as transport


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(transport.canonical_json(value) + "\n", encoding="utf-8")


def _jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(transport.canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _receipt(value: dict[str, object]) -> dict[str, object]:
    result = dict(value)
    result["receipt_sha256"] = transport.sha256_bytes(
        (transport.canonical_json(result) + "\n").encode()
    )
    return result


def _fixture(tmp_path: Path) -> dict[str, object]:
    inputs = tmp_path / "inputs"
    family = "school_textbooks"
    rows: list[dict[str, object]] = []
    for index in range(1, 4):
        locator = {"table": "textbooks", "row": index}
        text = f"Український навчальний текст {index}."
        rows.append(
            {
                "family_id": family,
                "unit_id": f"unit.school_textbooks.{index}",
                "unit_sha256": transport.sha256_value({"unit": index}),
                "frozen_locator": locator,
                "frozen_locator_sha256": transport.sha256_value(locator),
                "document_or_edition_identity": "doc.school_textbooks.fixture",
                "source_text": text,
                "source_text_sha256": transport.sha256_bytes(text.encode()),
                "source_record": {"kind": "fixture", "ordinal": index},
            }
        )
    materialization = inputs / "materialization.jsonl"
    _jsonl(materialization, rows)
    source_freeze = inputs / "source-freeze.json"
    _json(
        source_freeze,
        {
            "schema_version": "phase3_source_universe_freeze_v1",
            "text_free": True,
            "families": [
                {
                    "family_id": family,
                    "unit_count": 3,
                    "ledger_sha256": transport.sha256_value({"ledger": family}),
                }
            ],
        },
    )
    materialization_receipt = inputs / "materialization-receipt.json"
    materialization_value = {
        "text_free": True,
        "no_leakage": True,
        "private_record_count": 3,
        "private_jsonl_sha256": transport.sha256_file(materialization),
        "source_universe_receipt_sha256": transport.sha256_file(source_freeze),
    }
    materialization_value["receipt_sha256"] = transport.sha256_bytes(
        (transport.canonical_json(materialization_value) + "\n").encode()
    )
    _json(materialization_receipt, materialization_value)
    author = inputs / "author.jsonl"
    evaluation = inputs / "evaluation.jsonl"
    quarantine = inputs / "quarantine.jsonl"
    _jsonl(author, [{"family_id": family, "reason": "author_cleared", "unit_id": rows[0]["unit_id"], "unit_sha256": rows[0]["unit_sha256"]}])
    _jsonl(
        evaluation,
        [
            {
                "candidate_lane": "clean_modern",
                "family_id": family,
                "reason": "evaluation_only",
                "unit_id": rows[1]["unit_id"],
                "unit_sha256": rows[1]["unit_sha256"],
                "frozen_locator_sha256": rows[1]["frozen_locator_sha256"],
                "source_text_sha256": rows[1]["source_text_sha256"],
            }
        ],
    )
    _jsonl(quarantine, [{"family_id": family, "reason": "prior_exposure", "unit_id": rows[2]["unit_id"], "unit_sha256": rows[2]["unit_sha256"]}])
    partition_receipt = inputs / "partition-receipt.json"
    _json(
        partition_receipt,
        {
            "text_free": True,
            "aggregates": {
                "author_cleared_total": 1,
                "input_total": 3,
                "quarantined_total": 1,
                "sealed_evaluation_total": 1,
            },
            "artifact_hashes": {
                "author_clearance_sha256": transport.sha256_file(author),
                "partition_manifest_sha256": transport.sha256_file(evaluation),
                "quarantine_sha256": transport.sha256_file(quarantine),
            },
        },
    )
    heldout_receipt = inputs / "heldout.json"
    _json(
        heldout_receipt,
        _receipt(
            {
                "schema_version": "phase3_heldout_label_public_receipt_v1",
                "text_free": True,
                "complete": True,
                "row_count": 1,
            }
        ),
    )
    expected = {
        "family_totals": {family: 3},
        "author_totals": {family: 1},
        "evaluation_totals": {family: 1},
        "quarantine_totals": {family: 1},
        "total": 3,
        "author": 1,
        "evaluation": 1,
        "quarantine": 1,
        "heldout_labels": 1,
    }
    return {
        "rows": rows,
        "materialization_jsonl": materialization,
        "materialization_receipt_path": materialization_receipt,
        "source_freeze_receipt_path": source_freeze,
        "evaluation_partition_receipt_path": partition_receipt,
        "partition_manifest_path": evaluation,
        "author_clearance_path": author,
        "quarantine_path": quarantine,
        "heldout_label_receipt_path": heldout_receipt,
        "private_dir": tmp_path / "private",
        "expected_totals": expected,
    }


def _artifact() -> dict[str, object]:
    return {
        "phenomenon": "fixture_orthography",
        "mechanism": "orthography",
        "matcher": {"kind": "orthography", "pattern": "fixture"},
        "incorrect_pattern": "fixture",
        "replacements": ["приклад"],
        "scope": "fixture only",
        "exceptions": [],
        "controls": ["контроль"],
        "protections": ["захист"],
        "abstentions": [],
        "evidence_refs": ["attached_source_span"],
        "dissent_or_alternatives": [],
    }


def _decision(identity: dict[str, object], *, converted: bool = True) -> dict[str, object]:
    return {
        "unit_id": identity["unit_id"],
        "unit_sha256": identity["unit_sha256"],
        "disposition_code": "converted" if converted else "not_rule_bearing",
        "primary_source_role": "explicit_rule" if converted else "ordinary_narration",
        "secondary_source_roles": [],
        "claim_type": "prescriptive_rule" if converted else "attestation_only",
        "candidate_classes": ["rule_bearing"] if converted else [],
        "artifact": _artifact() if converted else None,
        "consumer_views": ["review"] if converted else [],
        "rationale": "The attached fixture directly supports this bounded decision.",
    }


def _invocation(path: Path, *, actor: dict[str, str], packet_id: str, raw: Path) -> Path:
    _json(
        path,
        {
            "schema_version": "phase3_source_production_provider_invocation_v1",
            "actor": actor,
            "packet_id": packet_id,
            "raw_sha256": transport.sha256_file(raw),
            "command_sha256": "1" * 64,
            "stdout_sha256": transport.sha256_file(raw),
            "stderr_sha256": transport.sha256_bytes(b""),
            "exit_code": 0,
            "started_at": "2026-08-09T00:00:00Z",
            "completed_at": "2026-08-09T00:00:01Z",
        },
    )
    return path


def _prepare(tmp_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    fixture = _fixture(tmp_path)
    kwargs = {key: value for key, value in fixture.items() if key != "rows"}
    manifest = transport.prepare(**kwargs)
    return fixture, manifest


def test_prepare_is_exact_private_and_excludes_sealed_source_bodies(tmp_path: Path) -> None:
    fixture, manifest = _prepare(tmp_path)
    root = fixture["private_dir"]
    assert isinstance(root, Path)
    assert len(manifest["author_packets"]) == 1
    packet = json.loads((root / "author/packets/00001.json").read_text())
    assert len(packet["items"]) == 1
    assert packet["items"][0]["identity"]["unit_id"] == fixture["rows"][0]["unit_id"]
    packet_bytes = (root / "author/packets/00001.json").read_bytes()
    assert str(fixture["rows"][1]["source_text"]).encode() not in packet_bytes
    assert str(fixture["rows"][2]["source_text"]).encode() not in packet_bytes
    assert root.stat().st_mode & 0o077 == 0
    assert all(path.stat().st_mode & 0o077 == 0 for path in root.rglob("*") if path.is_file())


def test_end_to_end_assembles_three_exact_dispositions_and_textbook_rows(tmp_path: Path) -> None:
    fixture, manifest = _prepare(tmp_path)
    root = fixture["private_dir"]
    assert isinstance(root, Path)
    identity = json.loads((root / "author/packets/00001.json").read_text())["identity_order"][0]
    author_response = {
        "schema_version": "phase3_source_production_author_response_v1",
        "packet_id": manifest["author_packets"][0]["packet_id"],
        "identity_order": [identity],
        "decisions": [_decision(identity)],
        "limitations": [],
        "parse_state": "parsed",
    }
    raw_author = tmp_path / "raw-author.json"
    _json(raw_author, author_response)
    author_invocation = _invocation(
        tmp_path / "author-invocation.json", actor=transport.AUTHOR,
        packet_id=manifest["author_packets"][0]["packet_id"], raw=raw_author,
    )
    transport.ingest_author(
        manifest_path=root / "manifest.json", packet_index=1, raw_response_path=raw_author,
        provider_invocation_receipt_path=author_invocation,
    )
    review_manifest = transport.prepare_review(manifest_path=root / "manifest.json")
    review_packet = json.loads((root / "review/packets/00001.json").read_text())
    review_response = {
        "schema_version": "phase3_source_production_review_response_v1",
        "packet_id": review_manifest["review_packets"][0]["packet_id"],
        "identity_order": [identity],
        "reviews": [
            {
                "unit_id": identity["unit_id"],
                "unit_sha256": identity["unit_sha256"],
                "outcome": "confirmed",
                "decision": review_packet["items"][0]["author_decision"],
            }
        ],
        "parse_state": "parsed",
    }
    raw_review = tmp_path / "raw-review.json"
    _json(raw_review, review_response)
    review_invocation = _invocation(
        tmp_path / "review-invocation.json", actor=transport.REVIEWER,
        packet_id=review_manifest["review_packets"][0]["packet_id"], raw=raw_review,
    )
    transport.ingest_review(
        review_manifest_path=root / "review-manifest.json", packet_index=1,
        raw_response_path=raw_review, provider_invocation_receipt_path=review_invocation,
    )
    reviewed_input = tmp_path / "output/reviewed-input.json"
    source_review = tmp_path / "output/source-review.json"
    public = tmp_path / "output/public.json"
    textbook = tmp_path / "output/textbook.jsonl"
    receipt = transport.assemble(
        review_manifest_path=root / "review-manifest.json",
        reviewed_input_path=reviewed_input,
        source_review_receipt_path=source_review,
        public_receipt_path=public,
        textbook_classifications_path=textbook,
    )
    assert receipt["denominator"] == {
        "input_total": 3,
        "author_produced_total": 1,
        "source_review_selected_total": 1,
        "source_review_revised_total": 0,
        "evaluation_only_total": 1,
        "quarantined_total": 1,
        "converted_total": 1,
    }
    rows = json.loads(reviewed_input.read_text())["families"][0]["dispositions"]
    assert [row["disposition_code"] for row in rows] == ["converted", "evaluation_only", "blocked_with_reason"]
    classifications = [json.loads(line) for line in textbook.read_text().splitlines()]
    assert len(classifications) == 3
    assert sum(bool(row["candidate_classes"]) for row in classifications) == 1
    assert b"source_text" not in public.read_bytes()
    assert json.loads(source_review.read_text())["verdict"] == "APPROVE"


def test_prepare_rejects_partition_overlap_and_prompt_drift(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    author = fixture["author_clearance_path"]
    assert isinstance(author, Path)
    evaluation = fixture["partition_manifest_path"]
    assert isinstance(evaluation, Path)
    evaluation_row = json.loads(evaluation.read_text().splitlines()[0])
    author.write_text(author.read_text() + transport.canonical_json(evaluation_row) + "\n", encoding="utf-8")
    partition_receipt = fixture["evaluation_partition_receipt_path"]
    assert isinstance(partition_receipt, Path)
    receipt = json.loads(partition_receipt.read_text())
    receipt["artifact_hashes"]["author_clearance_sha256"] = transport.sha256_file(author)
    _json(partition_receipt, receipt)
    kwargs = {key: value for key, value in fixture.items() if key != "rows"}
    with pytest.raises(transport.SourceProductionError, match=r"row totals|family counts|partition overlap"):
        transport.prepare(**kwargs)


def test_author_ingest_preserves_invalid_raw_before_rejecting(tmp_path: Path) -> None:
    fixture, _ = _prepare(tmp_path)
    root = fixture["private_dir"]
    assert isinstance(root, Path)
    raw = tmp_path / "invalid.raw"
    raw.write_text("not json", encoding="utf-8")
    invocation = _invocation(
        tmp_path / "invalid-invocation.json", actor=transport.AUTHOR,
        packet_id=json.loads((root / "manifest.json").read_text())["author_packets"][0]["packet_id"], raw=raw,
    )
    with pytest.raises(transport.SourceProductionError, match="invalid author JSON"):
        transport.ingest_author(
            manifest_path=root / "manifest.json", packet_index=1, raw_response_path=raw,
            provider_invocation_receipt_path=invocation,
        )
    assert (root / "author/raw/00001.raw").read_bytes() == b"not json"


def test_review_miss_requires_full_large_family_escalation(tmp_path: Path) -> None:
    fixture, manifest = _prepare(tmp_path)
    root = fixture["private_dir"]
    assert isinstance(root, Path)
    packet = json.loads((root / "author/packets/00001.json").read_text())
    identity = packet["identity_order"][0]
    author_response = {
        "schema_version": "phase3_source_production_author_response_v1",
        "packet_id": manifest["author_packets"][0]["packet_id"],
        "identity_order": [identity],
        "decisions": [_decision(identity, converted=False)],
        "limitations": [],
        "parse_state": "parsed",
    }
    raw_author = tmp_path / "raw-author.json"
    _json(raw_author, author_response)
    author_invocation = _invocation(
        tmp_path / "author-invocation.json", actor=transport.AUTHOR,
        packet_id=manifest["author_packets"][0]["packet_id"], raw=raw_author,
    )
    transport.ingest_author(
        manifest_path=root / "manifest.json", packet_index=1, raw_response_path=raw_author,
        provider_invocation_receipt_path=author_invocation,
    )
    review_manifest = transport.prepare_review(manifest_path=root / "manifest.json")
    revised = _decision(identity)
    review_response = {
        "schema_version": "phase3_source_production_review_response_v1",
        "packet_id": review_manifest["review_packets"][0]["packet_id"],
        "identity_order": [identity],
        "reviews": [{"unit_id": identity["unit_id"], "unit_sha256": identity["unit_sha256"], "outcome": "revised", "decision": revised}],
        "parse_state": "parsed",
    }
    raw_review = tmp_path / "raw-review.json"
    _json(raw_review, review_response)
    review_invocation = _invocation(
        tmp_path / "review-invocation.json", actor=transport.REVIEWER,
        packet_id=review_manifest["review_packets"][0]["packet_id"], raw=raw_review,
    )
    transport.ingest_review(
        review_manifest_path=root / "review-manifest.json", packet_index=1,
        raw_response_path=raw_review, provider_invocation_receipt_path=review_invocation,
    )
    with pytest.raises(transport.SourceProductionError, match="full large-family nonhit review"):
        transport.assemble(
            review_manifest_path=root / "review-manifest.json",
            reviewed_input_path=tmp_path / "reviewed.json",
            source_review_receipt_path=tmp_path / "source-review.json",
            public_receipt_path=tmp_path / "public.json",
            textbook_classifications_path=tmp_path / "textbook.jsonl",
        )


def test_schema_and_public_receipt_are_closed(tmp_path: Path) -> None:
    schema = json.loads(transport.DEFAULT_SCHEMA.read_text())
    assert schema["$defs"]["publicReceipt"]["additionalProperties"] is False
    value = copy.deepcopy(_fixture(tmp_path)["expected_totals"])
    value["unexpected"] = 1
    with pytest.raises(transport.SourceProductionError, match="override fields"):
        transport._expected(value)


def test_output_cannot_overlap_an_input(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["private_dir"] = fixture["materialization_jsonl"]
    kwargs = {key: value for key, value in fixture.items() if key != "rows"}
    with pytest.raises(transport.SourceProductionError, match="overlaps an input"):
        transport.prepare(**kwargs)


def test_resumable_run_commands_pin_gemini_and_grok(tmp_path: Path) -> None:
    fixture, _ = _prepare(tmp_path)
    root = fixture["private_dir"]
    assert isinstance(root, Path)
    commands: list[list[str]] = []

    def author_invoke(command: list[str], prompt: bytes) -> tuple[int, bytes, bytes]:
        commands.append(command)
        packet = json.loads(Path(command[command.index("--data") + 1]).read_text())
        identity = packet["identity_order"][0]
        response = {
            "schema_version": "phase3_source_production_author_response_v1",
            "packet_id": packet["packet_id"],
            "identity_order": [identity],
            "decisions": [_decision(identity)],
            "limitations": [],
            "parse_state": "parsed",
        }
        assert b"rule_author_extractor" in prompt
        assert b'"authorResponse"' in prompt
        assert b'"schema_version"' in prompt
        assert b'"packet_id"' in prompt
        assert b'"identity_order"' in prompt
        assert b'"disposition_code"' in prompt
        assert b'"additionalProperties":false' in prompt
        return 0, (transport.canonical_json(response) + "\n").encode(), b""

    first = transport.run_author(manifest_path=root / "manifest.json", invoke=author_invoke)
    second = transport.run_author(manifest_path=root / "manifest.json", invoke=author_invoke)
    assert first["completed"] == 1 and second["skipped"] == 1
    assert "ask-agy" in commands[0] and "gemini-3.6-flash-high" in commands[0]

    transport.prepare_review(manifest_path=root / "manifest.json")

    def review_invoke(command: list[str], prompt: bytes) -> tuple[int, bytes, bytes]:
        commands.append(command)
        packet = json.loads(Path(command[command.index("--data") + 1]).read_text())
        identity = packet["identity_order"][0]
        response = {
            "schema_version": "phase3_source_production_review_response_v1",
            "packet_id": packet["packet_id"],
            "identity_order": [identity],
            "reviews": [
                {
                    "unit_id": identity["unit_id"],
                    "unit_sha256": identity["unit_sha256"],
                    "outcome": "confirmed",
                    "decision": packet["items"][0]["author_decision"],
                }
            ],
            "parse_state": "parsed",
        }
        assert b"ukrainian_source_reviewer" in prompt
        assert b'"reviewResponse"' in prompt
        assert b'"reviews"' in prompt
        assert b'"outcome"' in prompt
        assert b'"additionalProperties":false' in prompt
        return 0, (transport.canonical_json(response) + "\n").encode(), b""

    result = transport.run_review(review_manifest_path=root / "review-manifest.json", invoke=review_invoke)
    assert result["completed"] == 1
    assert "ask-opencode" in commands[-1] and "grok-4.5" in commands[-1]


def test_run_rejects_transport_schema_drift_before_invocation(tmp_path: Path) -> None:
    fixture, _ = _prepare(tmp_path)
    root = fixture["private_dir"]
    assert isinstance(root, Path)
    schema = json.loads(transport.DEFAULT_SCHEMA.read_text())
    schema["title"] = "drifted after manifest freeze"
    drifted_schema = tmp_path / "drifted-schema.json"
    _json(drifted_schema, schema)
    invoked = False

    def invoke(command: list[str], prompt: bytes) -> tuple[int, bytes, bytes]:
        nonlocal invoked
        invoked = True
        return 1, b"", b"should not run"

    with pytest.raises(transport.SourceProductionError, match="transport schema hash drift"):
        transport.run_author(
            manifest_path=root / "manifest.json",
            schema_path=drifted_schema,
            invoke=invoke,
        )
    assert invoked is False
