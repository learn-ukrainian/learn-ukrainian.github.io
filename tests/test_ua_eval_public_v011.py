from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness.smoke_public_v011 import run_smoke
from scripts.projects.ua_eval_harness.verify_release_freeze_v011 import (
    GEMMA_PATHS,
    V010_FREEZE_SHA256,
    V010_SPLIT_SHA256,
    FreezeError,
    _validate_aggregate_report_is_public,
)

ROOT = Path(__file__).resolve().parents[1]
HELDOUT_MANIFEST = (
    ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_public_v011_reproduces_all_saved_baselines() -> None:
    summaries = run_smoke()

    assert [summary["name"] for summary in summaries] == [
        "identity",
        "deterministic fixture rules",
        "gpt-5.6-terra saved run",
        "gemma-4-31b-it saved run",
    ]
    assert all(summary["responses"] == 677 for summary in summaries)
    assert summaries[0]["edit_f0_5"] == 0.0
    assert summaries[1]["edit_f0_5"] == 0.0
    assert summaries[2]["edit_f0_5"] == 0.24390243902439027
    assert summaries[3]["edit_f0_5"] == 0.19335142469470828
    assert summaries[3]["headline_calque_recall"] == 0.09523809523809523
    assert summaries[3]["exact_sentence_accuracy"] == 0.10782865583456426


def test_v010_release_receipts_remain_byte_identical() -> None:
    release_root = ROOT / "data/projects/ua_eval_harness/releases/v0.1.0"

    assert _sha256(release_root / "freeze_manifest.json") == (
        V010_FREEZE_SHA256
    )
    assert _sha256(release_root / "split_integrity.json") == V010_SPLIT_SHA256


def test_gemma_aggregate_report_rejects_item_content() -> None:
    heldout = json.loads(HELDOUT_MANIFEST.read_text(encoding="utf-8"))
    report_path = ROOT / GEMMA_PATHS["report"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["leak"] = {"item_id": heldout["items"][0][0]}

    with pytest.raises(
        FreezeError,
        match="aggregate report exposes item fields",
    ):
        _validate_aggregate_report_is_public(
            heldout,
            report,
            report_path=GEMMA_PATHS["report"],
        )
