"""Portable path-resolution tests for the UNLP pedagogy dataset exporter (#6571).

The exporter reads from an external private infra repo. That root must be
supplied via ``LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT`` (env var), never a
hardcoded ``/Users/...`` operator path. When the env var is unset the export
must degrade gracefully (empty dataset) rather than crashing at import.
"""
from __future__ import annotations

from scripts.dataset import export_ukrainian_pedagogy_dataset as exporter


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
