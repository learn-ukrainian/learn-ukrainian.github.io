from __future__ import annotations

import json
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


def test_decision_validator_allows_general_promotion_batch_size(tmp_path: Path) -> None:
    payload = _minimal_payload()
    source_queue = payload["source_queue"]  # type: ignore[index]
    source_queue.pop("first_promotion_batch_size")  # type: ignore[attr-defined]
    source_queue["promotion_batch_size"] = 1  # type: ignore[index]
    path = tmp_path / "ok.yaml"
    _write_decision_file(path, payload)

    summary = decisions.validate_committed_decision_files([path])

    assert summary["rows"] == 1


def test_decision_validator_discovers_its_staged_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    inventory_path = "data/lexicon/source-inventory/curriculum-full-text-intake.json"
    inventory = project_root / inventory_path
    inventory.parent.mkdir(parents=True)
    inventory.write_text(
        json.dumps(
            [
                {
                    "lemma": "кіт",
                    "source_family": "curriculum",
                    "extraction_mode": "module_markdown_token",
                    "source_id": "curriculum-fixture",
                    "source_title": "Fixture curriculum",
                    "source_path": "curriculum/l2-uk-en/a1/fixture/module.md",
                    "source_locator": "curriculum/l2-uk-en/a1/fixture/module.md::module_body",
                    "count": 1,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    source_inventory = row["source_inventory"]  # type: ignore[index]
    source_inventory.update(  # type: ignore[union-attr]
        {
            "path": inventory_path,
            "locator": "curriculum/l2-uk-en/a1/fixture/module.md::module_body",
            "source_id": "curriculum-fixture",
            "source_family": "curriculum",
        }
    )
    source_inventory["key"] = decisions.source_inventory_key(  # type: ignore[index]
        lemma="ананас",
        inventory_path=inventory_path,
        locator="curriculum/l2-uk-en/a1/fixture/module.md::module_body",
    )
    row["lemma"] = "кіт"  # type: ignore[index]
    row["approved_gloss"] = "cat"  # type: ignore[index]
    path = tmp_path / "staged-ledger.yaml"
    _write_decision_file(path, payload)
    monkeypatch.setattr(decisions, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(decisions, "SOURCE_INVENTORY_DIR", inventory.parent)
    monkeypatch.setattr(decisions, "COMMITTED_SOURCE_INVENTORIES", ())
    source_inventory["key"] = decisions.source_inventory_key(  # type: ignore[index]
        lemma="кіт",
        inventory_path=inventory_path,
        locator="curriculum/l2-uk-en/a1/fixture/module.md::module_body",
    )
    _write_decision_file(path, payload)

    assert decisions.validate_committed_decision_files([path])["rows"] == 1


def test_decision_validator_rejects_missing_promotion_batch_size(tmp_path: Path) -> None:
    payload = _minimal_payload()
    source_queue = payload["source_queue"]  # type: ignore[index]
    source_queue.pop("first_promotion_batch_size")  # type: ignore[attr-defined]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="promotion batch size"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_rejects_duplicate_promotion_batch_size(tmp_path: Path) -> None:
    payload = _minimal_payload()
    source_queue = payload["source_queue"]  # type: ignore[index]
    source_queue["promotion_batch_size"] = 1  # type: ignore[index]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="promotion batch size"):
        decisions.validate_committed_decision_files([path])


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



def test_decision_accepts_surface_admission_mapping(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["decisions"][0]["surface_admission"] = {"daily": False, "practice": True, "cloze": False}
    path = tmp_path / "surface.yaml"
    _write_decision_file(path, payload)

    summary = decisions.validate_committed_decision_files([path])

    assert summary["rows"] == 1


def test_decision_rejects_invalid_surface_admission(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["decisions"][0]["surface_admission"] = {"practice": "yes"}
    path = tmp_path / "bad-surface.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match=r"surface_admission\.practice must be boolean"):
        decisions.validate_committed_decision_files([path])


def test_wrong_kind_document_fails_on_kind_not_field_noise(tmp_path):
    """A non-decision document (e.g. a grow triage ledger, #4888) dropped
    into the decisions directory must fail on `kind` — the actionable error
    pointing at the directory contract — not on a wall of unknown-field
    noise. Regression pin for the 2026-07-10 red-main incident."""
    payload = {
        "version": 1,
        "kind": "atlas_grow_automerge_triage_ledger",
        "batch_id": "grow-ledger-fixture",
        "provenance": {"input_file": "/tmp/fixture.json"},
        "decision_counts": {"approve": 1},
    }
    path = tmp_path / "2026-07-10-fixture-ledger.yaml"
    _write_decision_file(path, payload)
    with pytest.raises(SourceInventoryError, match=r"kind"):
        decisions.validate_decision_file(path)
