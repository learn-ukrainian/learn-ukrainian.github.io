"""Tests for the deterministic synthetic Atlas manifest fixture generator (#8307)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.atlas import atlas_db
from scripts.atlas.export_runtime_shards import export_runtime_shards
from scripts.benchmarks.generate_synthetic_manifest import (
    SYNTHETIC_SLUG_SUFFIX,
    check_free_disk_space,
    generate_synthetic_manifest,
    main,
)


@pytest.fixture
def sample_source_manifest(tmp_path: Path) -> Path:
    """Fixture with a small, realistic Atlas manifest containing varied entries."""
    entries = [
        {
            "lemma": "вода",
            "url_slug": "вода",
            "gloss": "water",
            "pos": "noun",
            "primary_source": "curriculum",
            "heritage_status": {"classification": "standard"},
            "enrichment": {
                "cefr": {"level": "A1"},
                "meaning": {"definitions": ["прозора рідина"], "source": "СУМ"},
            },
            "pronunciation": {"ipa": "[woˈda]"},
        },
        {
            "lemma": "сонце",
            "url_slug": "сонце",
            "gloss": "sun",
            "pos": "noun",
            "primary_source": "curriculum",
            "enrichment": {"cefr": {"level": "A1"}},
        },
        {
            "lemma": "земля",
            "url_slug": "земля",
            "gloss": "earth, ground",
            "pos": "noun",
            "primary_source": "curriculum",
            "enrichment": {"cefr": {"level": "A1"}},
        },
        {
            "lemma": "сліпа зона",
            "url_slug": "сліпа-зона",
            "gloss": "blind spot",
            "pos": "noun",
            "primary_source": "teacher_lesson",
            "source_provenance": [{"source_family": "teacher_lesson", "extraction_mode": "manual"}],
        },
        # form_of entry pointing to an article in the manifest
        {
            "lemma": "води",
            "url_slug": "води",
            "pos": "noun",
            "form_of": {"lemma": "вода", "url_slug": "вода"},
        },
    ]
    manifest_path = tmp_path / "source-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "generated_at": "2026-09-11T10:12:36+00:00",
                "entries": entries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI --help meets repository standard and exits 0."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Generate a deterministic, synthetic 410,000-scale Atlas manifest fixture" in captured.out
    assert "--source" in captured.out
    assert "--output" in captured.out
    assert "--count" in captured.out
    assert "--seed" in captured.out
    assert "Examples:" in captured.out
    assert "Outputs:" in captured.out
    assert "Exit codes:" in captured.out
    assert "#8307" in captured.out


def test_same_seed_byte_identity(sample_source_manifest: Path, tmp_path: Path) -> None:
    """Verify identical seed + count produces byte-for-byte identical output files."""
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    res1 = generate_synthetic_manifest(sample_source_manifest, out1, count=15, seed=42, quiet=True)
    res2 = generate_synthetic_manifest(sample_source_manifest, out2, count=15, seed=42, quiet=True)

    assert res1["sha256"] == res2["sha256"]
    assert res1["bytes_written"] == res2["bytes_written"]
    assert out1.read_bytes() == out2.read_bytes()


def test_different_seed_variation(sample_source_manifest: Path, tmp_path: Path) -> None:
    """Verify different seeds produce different outputs and vary entry selection."""
    out_a = tmp_path / "out_a.json"
    out_b = tmp_path / "out_b.json"

    res_a = generate_synthetic_manifest(sample_source_manifest, out_a, count=3, seed=42, quiet=True)
    res_b = generate_synthetic_manifest(sample_source_manifest, out_b, count=3, seed=99, quiet=True)

    assert res_a["sha256"] != res_b["sha256"]
    data_a = json.loads(out_a.read_text(encoding="utf-8"))
    data_b = json.loads(out_b.read_text(encoding="utf-8"))
    slugs_a = [e["url_slug"] for e in data_a["entries"]]
    slugs_b = [e["url_slug"] for e in data_b["entries"]]
    assert slugs_a != slugs_b


def test_slug_uniqueness_and_synthetic_markers(sample_source_manifest: Path, tmp_path: Path) -> None:
    """Verify all generated route slugs are unique and marked synthetic."""
    out = tmp_path / "synthetic.json"
    total_target = 18
    res = generate_synthetic_manifest(sample_source_manifest, out, count=total_target, seed=42, quiet=True)

    assert res["count"] == total_target
    assert res["base_entries"] == 5
    assert res["resampled_copies"] == 13

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["synthetic"] is True
    assert data["dataset_kind"] == "synthetic-resample"
    assert data["entries_count"] == total_target
    assert len(data["entries"]) == total_target

    slugs = [e["url_slug"] for e in data["entries"]]
    assert len(slugs) == len(set(slugs)), "Every generated slug must be unique"

    # Base entries preserve canonical slug
    base_slugs = slugs[:5]
    assert base_slugs == ["вода", "води", "земля", "сліпа-зона", "сонце"]

    # Resampled copies have synthetic suffix
    for copy_idx, entry in enumerate(data["entries"][5:], start=1):
        expected_suffix = SYNTHETIC_SLUG_SUFFIX.format(index=copy_idx)
        assert entry["url_slug"].endswith(expected_suffix)
        assert entry.get("synthetic") is True
        prov = entry.get("source_provenance", [])
        assert any(p.get("source_family") == "synthetic_resample" for p in prov)


def test_atlas_db_pipeline_compatibility(sample_source_manifest: Path, tmp_path: Path) -> None:
    """Verify generated synthetic manifest is accepted by scripts.atlas.atlas_db without alias errors."""
    out_manifest = tmp_path / "synthetic-manifest.json"
    db_path = tmp_path / "atlas.db"

    # Generate 25 entries (5 base + 20 copies)
    generate_synthetic_manifest(sample_source_manifest, out_manifest, count=25, seed=42, quiet=True)

    counts = atlas_db.migrate_manifest(out_manifest, db_path)
    assert counts["articles"] > 0
    assert counts["payloads"] == 25

    # Validate alias integrity
    validation = atlas_db.validate_alias_targets(db_path)
    assert validation["failures"] == 0
    assert validation["distinct_public_targets"] > 0


def test_export_runtime_shards_compatibility(sample_source_manifest: Path, tmp_path: Path) -> None:
    """Verify export_runtime_shards succeeds on a DB built from the synthetic manifest."""
    out_manifest = tmp_path / "synthetic-manifest.json"
    db_path = tmp_path / "atlas.db"
    shards_dir = tmp_path / "shards"

    generate_synthetic_manifest(sample_source_manifest, out_manifest, count=12, seed=42, quiet=True)
    atlas_db.migrate_manifest(out_manifest, db_path)

    summary = export_runtime_shards(
        db_path=db_path,
        out_dir=shards_dir,
        base_path="atlas",
        include_decks=False,
        verify=True,
    )
    assert summary["counts"]["articles"] > 0
    assert len(summary["entryShardIds"]) > 0


def test_free_disk_space_guard(tmp_path: Path) -> None:
    """Verify check_free_disk_space halts if free disk falls below threshold."""

    # Mock statvfs to return 10 GB free (< 25 GB threshold)
    class FakeStat:
        f_bavail = 10 * (1024**3) // 4096
        f_frsize = 4096

    with patch("os.statvfs", return_value=FakeStat()):
        with pytest.raises(RuntimeError, match="Insufficient free disk space"):
            check_free_disk_space(tmp_path / "test.json", min_gb=25.0)


def test_cli_main_success(sample_source_manifest: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI main entry point executes successfully and prints valid JSON summary."""
    out = tmp_path / "cli-out.json"
    exit_code = main(
        [
            "--source",
            str(sample_source_manifest),
            "--output",
            str(out),
            "--count",
            "10",
            "--seed",
            "123",
            "--quiet",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["outcome"] == "success"
    assert payload["count"] == 10
    assert payload["seed"] == 123
    assert out.exists()


def test_real_manifest_integration_small_scale(tmp_path: Path) -> None:
    """Integration test: sample from the real public manifest and verify atlas_db compatibility."""
    from scripts.benchmarks.generate_synthetic_manifest import DEFAULT_SOURCE

    if not DEFAULT_SOURCE.exists():
        pytest.skip(f"Default source manifest not present at {DEFAULT_SOURCE}")

    out_manifest = tmp_path / "real-sampled-synthetic.json"
    db_path = tmp_path / "real-sampled.db"

    summary = generate_synthetic_manifest(
        source_path=DEFAULT_SOURCE,
        output_path=out_manifest,
        count=30,
        seed=42,
        quiet=True,
    )
    assert summary["outcome"] == "success"
    assert summary["count"] == 30
    assert summary["base_entries"] == 30

    counts = atlas_db.migrate_manifest(out_manifest, db_path)
    assert counts["payloads"] == 30
    assert counts["articles"] > 0

    validation = atlas_db.validate_alias_targets(db_path)
    assert validation["failures"] == 0
