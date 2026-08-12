from __future__ import annotations

import json
import stat
import subprocess
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_ua_gec_complete_context as context

ANNOTATED_TEXT = (
    "Св. Петро {дякував брата=>дякував братові:::error_type=G/Case}. "
    "Він {допоміг сестра=>допоміг сестрі:::error_type=G/Case}."
)
TARGET_TEXT = "Св. Петро дякував братові.\nВін допоміг сестрі.\n"


def _fixture_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "ua-gec"
    annotated = checkout / "data/gec-only/train/annotated/0001.a1.ann"
    source = checkout / "data/gec-only/train/source-sentences/0001.src.txt"
    target = checkout / "data/gec-only/train/target-sentences/0001.a1.txt"
    annotated.parent.mkdir(parents=True)
    source.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    annotated.write_text(ANNOTATED_TEXT, encoding="utf-8")
    source.write_text("Св. Петро дякував брата.\nВін допоміг сестра.\n", encoding="utf-8")
    target.write_text(TARGET_TEXT, encoding="utf-8")
    return checkout


def _fixture_rows() -> list[dict[str, object]]:
    return [
        {
            "unit_id": "ua-gec:test:1",
            "source_record": {
                "partition": "gec-only/train",
                "doc_id": "0001",
                "annotator_id": "1",
                "error_type": "G/Case",
                "error": "дякував брата",
                "correct": "дякував братові",
            },
        },
        {
            "unit_id": "ua-gec:test:2",
            "source_record": {
                "partition": "gec-only/train",
                "doc_id": "0001",
                "annotator_id": "1",
                "error_type": "G/Case",
                "error": "допоміг сестра",
                "correct": "допоміг сестрі",
            },
        },
    ]


def _patch_fixture_denominator(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(context, "EXPECTED_TAG_COUNTS", {"G/Case": 2})
    monkeypatch.setattr(context, "EXPECTED_UNIT_COUNT", 2)
    monkeypatch.setattr(context, "_checkout_commit", lambda _checkout: context.UA_GEC_COMMIT)
    monkeypatch.setattr(context, "_load_v2_units", lambda _source_universe, _database: _fixture_rows())


def _valid_receipt() -> dict[str, object]:
    sha = "a" * 64
    receipt: dict[str, object] = {
        "schema_version": context.SCHEMA_VERSION,
        "implementation_version": context.IMPLEMENTATION_VERSION,
        "text_free": True,
        "provider_calls": False,
        "started_at": "2026-08-12T00:00:00Z",
        "completed_at": "2026-08-12T00:01:00Z",
        "bindings": {
            "phase3_reboot_prompt_v3_sha256": context.PHASE3_REBOOT_V3_SHA256,
            "phase3_recovery_prompt_v2_sha256": context.PHASE3_RECOVERY_V2_SHA256,
            "implementation_sha256": sha,
            "receipt_schema_sha256": sha,
            "representation_implementation_sha256": sha,
            "representation_schema_sha256": sha,
            "v2_source_universe_receipt_sha256": sha,
            "v2_ua_gec_ledger_sha256": sha,
            "sources_database_sha256": sha,
            "ua_gec_repository": context.UA_GEC_REPOSITORY,
            "ua_gec_commit": context.UA_GEC_COMMIT,
            "ua_gec_license": context.UA_GEC_LICENSE,
        },
        "denominator": {
            "v2_ua_gec_unit_count": 8937,
            "v2_tag_counts": {
                "F/Calque": 2397,
                "F/Collocation": 459,
                "G/Case": 5024,
                "G/Gender": 1057,
            },
            "all_v2_units_mapped": True,
        },
        "complete_context": {
            "annotated_document_count": 4162,
            "source_document_count_with_eligible_context": 1,
            "target_document_count_with_eligible_context": 1,
            "eligible_context_record_count": 1,
            "eligible_v2_unit_count": 8936,
            "excluded_context_candidate_count_by_reason": {"target_sentence_not_exactly_aligned": 1},
            "excluded_v2_unit_count_by_reason": {"target_sentence_not_exactly_aligned": 1},
            "all_eligible_records_validate": True,
            "private_jsonl_sha256": sha,
            "private_jsonl_bytes": 1,
            "private_exclusions_jsonl_sha256": sha,
            "private_exclusions_jsonl_bytes": 1,
            "private_exclusions_jsonl_rows": 1,
        },
        "gates": {
            "complete_context_materialization_ready": True,
            "semantic_labels_present": False,
            "cycle002_labels_diagnostic_only": True,
            "source_authoring_blocked": True,
            "evaluation_partition_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    receipt["receipt_sha256"] = context.sha256_bytes(context.canonical_bytes(receipt))
    return receipt


def test_target_sentence_alignment_does_not_split_ukrainian_abbreviation() -> None:
    parsed = context.parse_annotated_document(ANNOTATED_TEXT)
    sentences = context._target_sentences(parsed, TARGET_TEXT)
    source_sentences = context._source_sentences(parsed, "Св. Петро дякував брата.\nВін допоміг сестра.\n")
    first = context._sentence_for_annotation(parsed.annotations[0], sentences)

    assert first is not None
    window = context._context_window(parsed, first, source_sentences)
    assert window is not None
    assert parsed.source_text[window.source_start : window.source_end].startswith("Св. Петро")
    assert parsed.corrected_text[window.target_start : window.target_end] == "Св. Петро дякував братові."


def test_reconstructs_full_context_and_maps_every_frozen_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = _fixture_checkout(tmp_path)
    _patch_fixture_denominator(monkeypatch)

    records, accounting = context.reconstruct(
        checkout=checkout,
        database=tmp_path / "unused.db",
        source_universe=tmp_path / "unused-universe",
    )

    assert len(records) == 2
    assert accounting["eligible_v2_unit_count"] == 2
    assert accounting["excluded_v2_unit_count_by_reason"] == {}
    assert accounting["all_v2_units_mapped"] is True
    assert records[0]["provider_calls"] is False
    assert records[0]["classification"]["consumer_views"] == ["research_only"]
    assert all(record["source"]["complete_text"] != "брата" for record in records)
    assert any(record["source"]["complete_text"].startswith("Св. Петро") for record in records)


def test_unaligned_target_sentence_is_excluded_not_repaired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = _fixture_checkout(tmp_path)
    target = checkout / "data/gec-only/train/target-sentences/0001.a1.txt"
    target.write_text("Непов'язаний текст.\n", encoding="utf-8")
    _patch_fixture_denominator(monkeypatch)

    records, accounting = context.reconstruct(
        checkout=checkout,
        database=tmp_path / "unused.db",
        source_universe=tmp_path / "unused-universe",
    )

    assert records == []
    assert accounting["excluded_v2_unit_count_by_reason"] == {"target_sentence_not_exactly_aligned": 2}
    assert accounting["all_v2_units_mapped"] is True


def test_source_target_sentence_boundary_mismatch_is_excluded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = _fixture_checkout(tmp_path)
    annotated = checkout / "data/gec-only/train/annotated/0001.a1.ann"
    source = checkout / "data/gec-only/train/source-sentences/0001.src.txt"
    target = checkout / "data/gec-only/train/target-sentences/0001.a1.txt"
    annotated.write_text("Перше{.=>:::error_type=G/Case} Друге.", encoding="utf-8")
    source.write_text("Перше.\nДруге.\n", encoding="utf-8")
    target.write_text("Перше Друге.\n", encoding="utf-8")
    monkeypatch.setattr(context, "EXPECTED_TAG_COUNTS", {"G/Case": 1})
    monkeypatch.setattr(context, "EXPECTED_UNIT_COUNT", 1)
    monkeypatch.setattr(context, "_checkout_commit", lambda _checkout: context.UA_GEC_COMMIT)
    monkeypatch.setattr(
        context,
        "_load_v2_units",
        lambda _source_universe, _database: [
            {
                "unit_id": "ua-gec:test:boundary",
                "source_record": {
                    "partition": "gec-only/train",
                    "doc_id": "0001",
                    "annotator_id": "1",
                    "error_type": "G/Case",
                    "error": ".",
                    "correct": "",
                },
            }
        ],
    )

    records, accounting = context.reconstruct(
        checkout=checkout,
        database=tmp_path / "unused.db",
        source_universe=tmp_path / "unused-universe",
    )

    assert records == []
    assert accounting["excluded_v2_unit_count_by_reason"] == {"source_target_sentence_boundary_mismatch": 1}
    assert accounting["excluded_v2_units"] == [
        {"unit_id": "ua-gec:test:boundary", "reason": "source_target_sentence_boundary_mismatch"}
    ]


def test_missing_pinned_annotation_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = _fixture_checkout(tmp_path)
    annotated = checkout / "data/gec-only/train/annotated/0001.a1.ann"
    annotated.write_text("Св. Петро {дякував брата=>дякував братові:::error_type=G/Case}.", encoding="utf-8")
    _patch_fixture_denominator(monkeypatch)

    with pytest.raises(context.UaGecCompleteContextError, match="missing from the pinned checkout"):
        context.reconstruct(
            checkout=checkout,
            database=tmp_path / "unused.db",
            source_universe=tmp_path / "unused-universe",
        )


def test_checkout_commit_rejects_modified_tracked_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = tmp_path / "ua-gec"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    tracked = checkout / "tracked.txt"
    tracked.write_text("pinned\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(checkout), "add", "tracked.txt"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "-c",
            "user.name=Phase3 Test",
            "-c",
            "user.email=phase3@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(context, "UA_GEC_COMMIT", commit)

    assert context._checkout_commit(checkout) == commit
    tracked.write_text("modified\n", encoding="utf-8")
    with pytest.raises(context.UaGecCompleteContextError, match="modified tracked files"):
        context._checkout_commit(checkout)


def test_receipt_is_closed_text_free_and_preserves_blocking_gates() -> None:
    receipt = _valid_receipt()

    assert context.validate_receipt(receipt) == receipt

    unexpected = dict(receipt)
    unexpected["source_text"] = "must never appear"
    with pytest.raises(context.UaGecCompleteContextError, match="receipt schema violation"):
        context.validate_receipt(unexpected)

    weakened = json.loads(json.dumps(receipt))
    weakened["gates"]["source_authoring_blocked"] = False
    weakened["receipt_sha256"] = context.sha256_bytes(
        context.canonical_bytes({key: value for key, value in weakened.items() if key != "receipt_sha256"})
    )
    with pytest.raises(context.UaGecCompleteContextError, match="receipt schema violation"):
        context.validate_receipt(weakened)


def test_receipt_rejects_unit_accounting_drift() -> None:
    receipt = _valid_receipt()
    receipt["complete_context"]["eligible_v2_unit_count"] = 8935  # type: ignore[index]
    receipt["receipt_sha256"] = context.sha256_bytes(
        context.canonical_bytes({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    )

    with pytest.raises(context.UaGecCompleteContextError, match="unit accounting drift"):
        context.validate_receipt(receipt)


def test_private_output_uses_restricted_permissions(tmp_path: Path) -> None:
    output = tmp_path / "private" / "records.jsonl"
    context._prepare_private_output(output)
    context._atomic_write(output, b"{}\n", context.PRIVATE_FILE_MODE)

    assert stat.S_IMODE(output.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
