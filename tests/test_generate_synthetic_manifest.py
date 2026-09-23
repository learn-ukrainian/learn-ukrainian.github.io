"""Tests for the deterministic synthetic Atlas manifest fixture generator (#8307)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.atlas import atlas_db
from scripts.atlas.export_runtime_shards import export_runtime_shards
from scripts.benchmarks.generate_synthetic_manifest import (
    DEFAULT_MIN_DISK_GB,
    DEFAULT_SOURCE,
    MIN_CLI_DISK_GB,
    MIN_DISK_GB,
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

    with (
        patch("os.statvfs", return_value=FakeStat()),
        pytest.raises(RuntimeError, match="Insufficient free disk space"),
    ):
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


def test_source_and_output_equality_rejected(sample_source_manifest: Path) -> None:
    """Verify specifying the same path for --source and --output is refused and leaves source intact."""
    initial_bytes = sample_source_manifest.read_bytes()

    # Direct programmatic call must raise ValueError
    with pytest.raises(ValueError, match="Refusing to overwrite source manifest"):
        generate_synthetic_manifest(
            source_path=sample_source_manifest,
            output_path=sample_source_manifest,
            count=10,
            quiet=True,
        )

    # Bytes must remain strictly unmodified
    assert sample_source_manifest.read_bytes() == initial_bytes


def test_cli_source_and_output_equality_refused(
    sample_source_manifest: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify CLI refuses source/output equality with clear error and exit code 1."""
    initial_bytes = sample_source_manifest.read_bytes()

    exit_code = main(
        [
            "--source",
            str(sample_source_manifest),
            "--output",
            str(sample_source_manifest),
            "--quiet",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Refusing to overwrite source manifest" in captured.err
    assert sample_source_manifest.read_bytes() == initial_bytes


def test_midstream_failure_preserves_existing_output_and_cleans_temp(
    sample_source_manifest: Path,
    tmp_path: Path,
) -> None:
    """Verify mid-stream streaming failure preserves existing output file and cleans sibling temp."""
    out_file = tmp_path / "destination-manifest.json"
    sentinel_content = b'{"sentinel": "previous-valid-manifest-do-not-clobber"}\n'
    out_file.write_bytes(sentinel_content)

    # Simulate an error during streaming (after writing header)
    def _exploding_stream(*args: object, **kwargs: object):
        yield {"lemma": "test", "url_slug": "test"}
        raise RuntimeError("Simulated failure mid-stream")

    with (
        patch(
            "scripts.benchmarks.generate_synthetic_manifest.generate_entry_stream",
            side_effect=_exploding_stream,
        ),
        pytest.raises(RuntimeError, match="Simulated failure mid-stream"),
    ):
        generate_synthetic_manifest(
            source_path=sample_source_manifest,
            output_path=out_file,
            count=5,
            quiet=True,
        )

    # Destination file must be completely intact with existing sentinel content
    assert out_file.exists()
    assert out_file.read_bytes() == sentinel_content

    # No leftover sibling temp files should remain in destination directory
    leftover_temps = list(tmp_path.glob(".*.tmp"))
    assert leftover_temps == []


@pytest.mark.parametrize(
    ("cli_args", "expected_fragment"),
    [
        (["--min-disk-gb", "0"], "(got 0.0)"),
        (["--min-disk-gb", "24.9"], "(got 24.9)"),
        (["--min-disk-gb", "nan"], "(got nan)"),
        (["--min-disk-gb", "inf"], "(got inf)"),
        (["--min-disk-gb=-inf"], "(got -inf)"),
    ],
)
def test_cli_min_disk_floor_enforced(
    sample_source_manifest: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    cli_args: list[str],
    expected_fragment: str,
) -> None:
    """Verify CLI strictly enforces 25 GB minimum disk floor and refuses non-finite or low values (#8307)."""
    out = tmp_path / "test-floor.json"

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--source",
                str(sample_source_manifest),
                "--output",
                str(out),
                *cli_args,
            ]
        )
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "--min-disk-gb cannot be set below 25.0 GB floor" in captured.err
    assert expected_fragment in captured.err
    assert not out.exists()
    assert list(tmp_path.glob(".*.tmp")) == []


@pytest.mark.parametrize(
    "invalid_gb",
    [
        1.0,
        0.0,
        24.9,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_programmatic_min_disk_floor_enforced(
    sample_source_manifest: Path,
    tmp_path: Path,
    invalid_gb: float,
) -> None:
    """Verify generate_synthetic_manifest rejects <25 GB or non-finite min_disk_gb without writing output."""
    out = tmp_path / "out-invalid-floor.json"

    with pytest.raises(ValueError, match=r"min_disk_gb cannot be set below 25\.0 GB floor"):
        generate_synthetic_manifest(
            source_path=sample_source_manifest,
            output_path=out,
            count=2,
            min_disk_gb=invalid_gb,
            quiet=True,
        )
    assert not out.exists()
    assert list(tmp_path.glob(".*.tmp")) == []


def test_programmatic_valid_min_disk_floor_accepted(
    sample_source_manifest: Path,
    tmp_path: Path,
) -> None:
    """Verify valid 25.0 GB floor is accepted and generates output (mocking disk sensor at boundary)."""
    out = tmp_path / "out-valid-floor.json"

    class FakeStatSufficient:
        f_bavail = 50 * (1024**3) // 4096
        f_frsize = 4096

    assert MIN_DISK_GB == 25.0
    assert MIN_CLI_DISK_GB == 25.0
    assert DEFAULT_MIN_DISK_GB == 25.0

    with patch("os.statvfs", return_value=FakeStatSufficient()):
        res = generate_synthetic_manifest(
            source_path=sample_source_manifest,
            output_path=out,
            count=2,
            min_disk_gb=25.0,
            quiet=True,
        )
    assert res["outcome"] == "success"
    assert out.exists()


@pytest.mark.parametrize(
    "invalid_gb",
    [1.0, 0.0, 24.9, float("nan"), float("inf"), float("-inf")],
)
def test_check_free_disk_space_floor_enforced(tmp_path: Path, invalid_gb: float) -> None:
    """Verify check_free_disk_space rejects non-finite or <25 GB thresholds before directory creation."""
    target = tmp_path / "never_created_dir" / "target.json"
    with pytest.raises(ValueError, match=r"min_disk_gb cannot be set below 25\.0 GB floor"):
        check_free_disk_space(target, min_gb=invalid_gb)
    assert not target.parent.exists()


def test_real_manifest_integration_small_scale(tmp_path: Path) -> None:
    """Integration test: sample from the real public manifest and verify atlas_db compatibility."""
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
