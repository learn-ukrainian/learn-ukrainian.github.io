from __future__ import annotations

import hashlib
import logging
import sys
from importlib import import_module
from pathlib import Path

import pytest
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

alignment_manifest = import_module("build.alignment_manifest")


def _set_curriculum_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(alignment_manifest, "CURRICULUM_ROOT", curriculum_root)
    return curriculum_root


def test_canonical_plan_hash_returns_sentinel_when_plan_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _set_curriculum_root(monkeypatch, tmp_path)

    with caplog.at_level(logging.WARNING, logger="build.alignment_manifest"):
        digest = alignment_manifest._canonical_plan_hash("A1", "missing-plan")

    assert digest == alignment_manifest._EMPTY_PLAN_SENTINEL
    assert "using empty sentinel" in caplog.text


def test_canonical_plan_hash_returns_deterministic_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = _set_curriculum_root(monkeypatch, tmp_path)
    plan_path = curriculum_root / "plans" / "a1" / "demo.yaml"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(
        "title: Demo\nlevel: A1\nslug: demo\nobjectives:\n  - Test hashing.\n",
        "utf-8",
    )

    plan_data = yaml.safe_load(plan_path.read_text("utf-8"))
    canonical_yaml = yaml.safe_dump(plan_data, sort_keys=True, allow_unicode=True)
    expected = hashlib.sha256(canonical_yaml.encode("utf-8")).hexdigest()

    assert alignment_manifest._canonical_plan_hash("A1", "demo") == expected
    assert alignment_manifest._canonical_plan_hash("a1", "demo") == expected


def test_compose_manifest_uses_sentinel_when_plan_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_curriculum_root(monkeypatch, tmp_path)
    monkeypatch.setattr(alignment_manifest, "_sources_hash", lambda: "sources")
    monkeypatch.setattr(alignment_manifest, "_template_hashes", lambda: {})
    monkeypatch.setattr(alignment_manifest, "_canonical_anchor_hash", lambda: "anchors")
    monkeypatch.setattr(
        alignment_manifest,
        "_threshold_snapshot",
        lambda level: {"level": level},
    )
    monkeypatch.setattr(alignment_manifest, "_decisions_subset", lambda: [])

    manifest = alignment_manifest.compose_manifest(level="A1", slug="missing-plan")

    assert manifest["plan_hash"] == alignment_manifest._EMPTY_PLAN_SENTINEL
