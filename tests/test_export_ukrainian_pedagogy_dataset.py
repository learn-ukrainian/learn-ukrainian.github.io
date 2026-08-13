"""Portable path-resolution tests for the UNLP pedagogy dataset exporter (#6571).

The exporter reads from an external private infra repo. That root must be
supplied via ``LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT`` (env var), never a
hardcoded ``/Users/...`` operator path. When the env var is unset the export
must degrade gracefully (empty dataset) rather than crashing at import.
"""
from __future__ import annotations

import os
from pathlib import Path

from scripts.dataset import export_ukrainian_pedagogy_dataset as exporter


def test_source_has_no_hardcoded_operator_path() -> None:
    src = Path(exporter.__file__).read_text(encoding="utf-8")
    assert "/Users/krisztiankoos/projects/learn-ukrainian-infra-private" not in src
    assert "/Users/krisztiankoos" not in src


def test_project_root_resolves_from_file_location() -> None:
    # scripts/dataset/export_ukrainian_pedagogy_dataset.py -> parents[2] is repo root
    assert Path(__file__).resolve().parents[1] == exporter.REPO_ROOT


def test_export_degrades_gracefully_without_private_root(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT", raising=False)
    monkeypatch.setattr(exporter, "DATASET_DIR", tmp_path)
    # Reload PRIVATE_ROOT semantics: the module reads the env var at import, so
    # point it at a clearly empty dir to force the .exists() guards off.
    monkeypatch.setattr(exporter, "PRIVATE_ROOT", tmp_path / "does-not-exist")

    result = exporter.export_pedagogy_dataset()

    assert result["status"] == "ok"
    assert result["records_exported"] == 0
    assert (tmp_path / "hramatka_uk_pedagogy_v1.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "README.md").exists()


def test_export_uses_env_var_private_root(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT", str(tmp_path / "custom-private"))
    assert os.environ["LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT"] == str(tmp_path / "custom-private")
