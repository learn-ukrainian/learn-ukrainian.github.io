from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import SourceInventoryError

FIRST_BATCH = (
    decisions.DEFAULT_DECISION_DIR / "2026-06-29-first-approved-publish-batch.yaml"
)


def _write_decision_file(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _minimal_payload() -> dict[str, object]:
    source_inventory = {
        "path": "data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml",
        "locator": "letters[А].key_word",
    }
    source_inventory["key"] = decisions.source_inventory_key(
        lemma="ананас",
        inventory_path=str(source_inventory["path"]),
        locator=str(source_inventory["locator"]),
    )
    source_inventory["source_id"] = "ohoiko-abetka-1-keywords"
    source_inventory["source_family"] = "ohoiko"
    return {
        "version": decisions.DECISION_VERSION,
        "kind": decisions.DECISION_KIND,
        "batch_id": "fixture-batch",
        "batch_label": "fixture",
        "reviewer": "test",
        "reviewed_at": "2026-06-29",
        "source_queue": {
            "workflow": decisions.QUEUE_WORKFLOW,
            "generated_from_pr": 4021,
            "total_queue_rows": 1,
            "approved_in_queue": 1,
            "first_promotion_batch_size": 1,
        },
        "production_outputs_updated": [],
        "decisions": [
            {
                "lemma": "ананас",
                "decision": "approve_for_publish",
                "approved_pos": "noun",
                "approved_gloss": "pineapple",
                "sense_note": "fixture",
                "source_inventory": source_inventory,
                "evidence_refs": ["fixture"],
                "review_queue_reasons": [
                    "grow_needs_review:heritage_status flags russian_shadow"
                ],
            }
        ],
    }


def test_committed_first_source_inventory_review_batch_validates() -> None:
    summary = decisions.validate_committed_decision_files([FIRST_BATCH])

    assert summary == {
        "files": 1,
        "rows": 20,
        "decision_counts": {"approve_for_publish": 20},
    }


def test_default_committed_decision_files_validate() -> None:
    summary = decisions.validate_committed_decision_files()

    assert summary["files"] >= 1
    assert summary["rows"] >= 20
    assert summary["decision_counts"]["approve_for_publish"] >= 20


def test_decision_validator_rejects_bad_source_key(tmp_path: Path) -> None:
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    row["source_inventory"]["key"] = "badbadbadbadbad1"  # type: ignore[index]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="does not match"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_requires_approved_gloss(tmp_path: Path) -> None:
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    row["approved_gloss"] = ""  # type: ignore[index]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="approved_gloss"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_allows_clean_rows_without_flags(tmp_path: Path) -> None:
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    row.pop("review_queue_reasons")  # type: ignore[attr-defined]
    path = tmp_path / "ok.yaml"
    _write_decision_file(path, payload)

    summary = decisions.validate_committed_decision_files([path])

    assert summary["rows"] == 1


def test_decision_validator_rejects_duplicate_source_key(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["decisions"].append(dict(payload["decisions"][0]))  # type: ignore[index, union-attr]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match=r"duplicate source_inventory\.key"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_rejects_production_outputs(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["production_outputs_updated"] = ["site/src/data/lexicon-manifest.json"]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match=r"production_outputs_updated must be \[\]"):
        decisions.validate_committed_decision_files([path])
