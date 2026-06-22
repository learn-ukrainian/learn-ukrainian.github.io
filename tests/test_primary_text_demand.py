from __future__ import annotations

import json
import logging
from pathlib import Path

from scripts.readings.primary_text_demand import build_manifest, main


def test_primary_text_manifest_dedupes_primary_refs(tmp_path: Path) -> None:
    plans_dir = _write_plan_fixture(tmp_path)

    manifest = build_manifest(plans_dir)

    assert manifest["summary"] == {
        "total_distinct_works": 2,
        "total_primary_refs": 3,
        "per_track_counts": {"folk": 1, "hist": 1, "lit": 1},
        "works_taught_by_multiple_modules": 1,
    }
    works = {entry["work"]: entry for entry in manifest["entries"]}
    assert "Академічна стаття" not in works
    assert sorted(works) == ["Лісова пісня", "Руська Правда"]

    forest_song = works["Лісова пісня"]
    assert forest_song["author"] == "Ле́ся Українка"
    assert forest_song["normalized_key"] == "лісова пісня::леся українка"
    assert forest_song["note_samples"] == ["драма-феєрія", "спільний семінарний текст"]
    assert forest_song["paths"] == ["https://example.test/lisova-pisnia"]
    assert forest_song["taught_by"] == [
        {"slug": "ritual-forest", "track": "folk", "grade": "FOLK"},
        {"slug": "forest-song", "track": "lit", "grade": "LIT"},
    ]

    assert works["Руська Правда"]["author"] == "Ярославове коло"
    assert works["Руська Правда"]["taught_by"] == [
        {"slug": "ruska-pravda", "track": "hist", "grade": None}
    ]

    folk_only = build_manifest(plans_dir, track="folk")
    assert folk_only["summary"] == {
        "total_distinct_works": 1,
        "total_primary_refs": 1,
        "per_track_counts": {"folk": 1},
        "works_taught_by_multiple_modules": 0,
    }


def test_primary_text_manifest_cli_writes_json(tmp_path: Path) -> None:
    plans_dir = _write_plan_fixture(tmp_path)
    out_path = tmp_path / "demand.json"

    assert main(["--plans-dir", str(plans_dir), "--out", str(out_path)]) == 0

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total_primary_refs"] == 3
    assert len(payload["entries"]) == 2


def test_primary_text_manifest_summary_skips_file_write(tmp_path: Path, capsys) -> None:
    plans_dir = _write_plan_fixture(tmp_path)
    out_path = tmp_path / "should-not-exist.json"

    assert main(["--plans-dir", str(plans_dir), "--out", str(out_path), "--summary"]) == 0

    assert not out_path.exists()
    assert capsys.readouterr().out == (
        "Primary text demand summary\n"
        "total_distinct_works: 2\n"
        "total_primary_refs: 3\n"
        "works_taught_by_multiple_modules: 1\n"
        "per_track_counts:\n"
        "  folk: 1\n"
        "  hist: 1\n"
        "  lit: 1\n"
    )


def test_primary_text_manifest_skips_malformed_yaml(tmp_path: Path, caplog) -> None:
    plans_dir = _write_plan_fixture(tmp_path)
    (plans_dir / "lit" / "broken.yaml").write_text("references: [", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        manifest = build_manifest(plans_dir)

    assert manifest["summary"]["total_primary_refs"] == 3
    assert "malformed YAML" in caplog.text


def _write_plan_fixture(tmp_path: Path) -> Path:
    plans_dir = tmp_path / "plans"
    (plans_dir / "lit").mkdir(parents=True)
    (plans_dir / "folk").mkdir()
    (plans_dir / "hist").mkdir()
    (plans_dir / "lit" / "forest-song.yaml").write_text(
        """
level: LIT
references:
  - title: Лісова пісня
    author: Леся Українка
    type: primary
    work: Лісова пісня
    note: драма-феєрія
    path: https://example.test/lisova-pisnia
  - title: Академічна стаття
    author: Дослідник
    type: academic
    work: Академічна стаття
""",
        encoding="utf-8",
    )
    (plans_dir / "folk" / "ritual-forest.yaml").write_text(
        """
level: FOLK
references:
  - title: "«Лісова пісня»"
    author: "Ле́ся Українка"
    type: primary
    work: Лісова пісня
    note: спільний семінарний текст
""",
        encoding="utf-8",
    )
    (plans_dir / "hist" / "ruska-pravda.yaml").write_text(
        """
references:
  - title: Руська Правда
    author: Ярославове коло
    type: primary
    note: title-only fallback
""",
        encoding="utf-8",
    )
    return plans_dir
