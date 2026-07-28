from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness import verify_release_freeze as freeze_module
from scripts.projects.ua_eval_harness.verify_release_freeze import (
    DEFAULT_OUTPUT,
    FreezeError,
    build_freeze,
    validate_freeze,
    write_freeze,
)


def test_committed_release_freeze_is_complete_and_current() -> None:
    freeze = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))

    validate_freeze(freeze)

    assert freeze["release"] == {
        "id": "ua-gec-calque-grammar-public-v0",
        "issue": 4626,
        "parent_epic": 2156,
        "status": "immutable",
        "version": "0.1.0",
    }
    assert freeze["split_integrity"]["train_test_author_overlap"] == 0
    assert freeze["split_integrity"]["train_test_document_overlap"] == 0
    assert freeze["split_integrity"]["development_fixtures_in_heldout_results"] == 0
    assert len(freeze["baselines"]) == 3
    assert all(run["gold_fields_supplied"] == [] for run in freeze["baselines"])


def test_freeze_fails_closed_on_artifact_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    freeze = build_freeze()
    real_sha256 = freeze_module._sha256

    def drifted_sha256(path: Path) -> str:
        if path == freeze_module.ROOT / freeze_module.PROMPT:
            return "0" * 64
        return real_sha256(path)

    monkeypatch.setattr(freeze_module, "_sha256", drifted_sha256)

    with pytest.raises(FreezeError, match="frozen artifact hash mismatch"):
        validate_freeze(freeze)


def test_freeze_fails_closed_on_metadata_edit() -> None:
    freeze = build_freeze()
    edited = copy.deepcopy(freeze)
    edited["version_policy"]["in_place_edits"] = "allowed"

    with pytest.raises(FreezeError, match="metadata is stale"):
        validate_freeze(edited)


def test_aggregate_reports_expose_no_protected_item_fields() -> None:
    freeze = build_freeze()

    assert freeze["reporting"]["aggregate_only"] is True
    assert "source_sha256" in freeze["reporting"]["forbidden_item_fields"]
    assert "raw_response" in freeze["reporting"]["forbidden_item_fields"]
    assert freeze["reporting"]["verified_report_paths"] == [
        "data/projects/ua_eval_harness/baselines/v1/identity.report.json",
        "data/projects/ua_eval_harness/baselines/v1/fixture-rules.report.json",
        "data/projects/ua_eval_harness/baselines/v1/gpt-5.6-terra.report.json",
    ]


def test_build_freeze_rejects_report_that_declares_gold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_read_json = freeze_module._read_json

    def read_with_gold(path: Path) -> dict:
        value = real_read_json(path)
        if path.name == "identity.report.json":
            value["saved_run"]["gold_fields_supplied"] = ["target"]
        return value

    monkeypatch.setattr(freeze_module, "_read_json", read_with_gold)

    with pytest.raises(FreezeError, match="supplied gold fields"):
        build_freeze()


def test_write_freeze_refuses_in_place_release_change(tmp_path: Path) -> None:
    output = tmp_path / "v0.1.0" / "freeze_manifest.json"
    output.parent.mkdir()
    output.write_text("{}\n", encoding="utf-8")

    with pytest.raises(FreezeError, match="refusing to overwrite immutable freeze"):
        write_freeze(output, build_freeze())


def test_write_freeze_requires_matching_version_directory(tmp_path: Path) -> None:
    output = tmp_path / "v0.2.0" / "freeze_manifest.json"

    with pytest.raises(FreezeError, match="path does not match release version"):
        write_freeze(output, build_freeze())
