"""Catalog rotation must update every generated seat and review-ladder row."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

tables = importlib.import_module("agents_extensions.shared.skills.drive-epic.scripts.render_catalog_tables")


def copy_catalog(tmp_path: Path) -> tuple[Path, dict]:
    data = yaml.safe_load(tables.CATALOG.read_text(encoding="utf-8"))
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path, data


def test_committed_projection_matches_live_catalog():
    assert tables.OUTPUT.read_text(encoding="utf-8") == tables.render()
    assert tables.main(["--check"]) == 0


def test_ladder_reordering_changes_projection(tmp_path):
    path, data = copy_catalog(tmp_path)
    before = tables.render(path)
    data["review_ladders"]["critical"].reverse()
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert tables.render(path) != before


def test_seat_effort_rotation_changes_projection(tmp_path):
    path, data = copy_catalog(tmp_path)
    before = tables.render(path)
    data["orchestrator_seats"]["codex"]["effort"] = "xhigh"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert tables.render(path) != before


@pytest.mark.parametrize("model", ["invented-model", "gpt-6-astra"])
def test_retired_or_unknown_seat_refuses_publication(tmp_path, model):
    path, data = copy_catalog(tmp_path)
    data["orchestrator_seats"]["codex"]["model_id"] = model
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError, match="non-active catalog model"):
        tables.render(path)


def test_check_fails_on_missing_and_drifted_output(tmp_path, monkeypatch):
    path = tmp_path / "tables.md"
    monkeypatch.setattr(tables, "OUTPUT", path)
    assert tables.main([]) == 1
    path.write_text("plausible but stale routing table\n", encoding="utf-8")
    assert tables.main(["--check"]) == 1
    assert path.read_text(encoding="utf-8") == "plausible but stale routing table\n"
    assert tables.main(["--write"]) == 0
    assert tables.main(["--check"]) == 0


def test_active_model_accepts_only_current_identity():
    catalog = {"models": {"live": {"lifecycle": "active"}, "retired": {"lifecycle": "retired"}}}
    assert tables.active_model("live", catalog) == "live"
    with pytest.raises(ValueError, match="non-active catalog model"):
        tables.active_model("retired", catalog)
