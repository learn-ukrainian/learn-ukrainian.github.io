"""Tests for the fail-closed teacher curated-seed recovery package."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.atlas import rebuild_teacher_curated_seed as rebuild


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> dict[str, Path]:
    inventory = tmp_path / "inventory"
    decisions = tmp_path / "decisions"
    drive_source = tmp_path / "drive-source"
    _write(
        inventory / "teacher.yaml",
        """sources:
- source_family: teacher_lesson
  headwords:
  - lemma: слово
  - lemma: СЛОВО
- source_family: other
  headwords:
  - lemma: ignored
""",
    )
    _write(
        decisions / "teacher.yaml",
        """decisions:
- decision: approve_for_publish
  source_inventory:
    source_family: teacher_lesson
- decision: hold
  source_inventory:
    source_family: teacher_lesson
""",
    )
    _write(drive_source / "ulp.jsonl", "{}\n")
    cloze = _write(
        tmp_path / "cloze.json",
        json.dumps({"cloze": [{"lemma": "слово"}, {"lemma": "СЛОВО"}]}),
    )
    return {
        "source_inventory_root": inventory,
        "decision_root": decisions,
        "cloze_path": cloze,
        "drive_source_root": drive_source,
    }


def test_source_recon_counts_evidence_without_promoting_it(tmp_path: Path) -> None:
    recon = rebuild.build_source_recon(**_inputs(tmp_path))

    assert recon["original_table"] == {
        "status": "absent",
        "reason": "No authoritative curated table was found; historical sources cannot select its rows.",
    }
    assert recon["sources"]["committed_historical_inventory"] == {
        "files": 1,
        "headword_records": 2,
        "unique_lemmas": 1,
    }
    assert recon["sources"]["committed_historical_decisions"] == {
        "files": 1,
        "decision_records": 2,
        "approved_records": 1,
    }
    assert recon["sources"]["cloze_evidence_only"] == {"cards": 2, "unique_lemmas": 1}
    assert recon["sources"]["drive_curriculum"]["candidate_teacher_tables"] == 0


def test_package_refuses_a_local_only_recovery(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local-only recovery package is forbidden"):
        rebuild.build_package(package_root=tmp_path / "local", drive_root=None, **_inputs(tmp_path))

    assert not (tmp_path / "local").exists()


def test_package_is_empty_and_has_a_verified_drive_mirror(tmp_path: Path) -> None:
    local = tmp_path / "local"
    drive = tmp_path / "drive" / "teacher-seed"

    receipt = rebuild.build_package(package_root=local, drive_root=drive, **_inputs(tmp_path))

    assert receipt["package_file_count"] == 5
    assert receipt["state"] == "quarantined_missing_authoritative_table"
    assert (local / "curated-seed.jsonl").read_text(encoding="utf-8") == ""
    assert (local / "rights-ledger.jsonl").read_text(encoding="utf-8") == ""
    assert (local / "practice-admission.jsonl").read_text(encoding="utf-8") == ""
    assert rebuild._package_checksums(local) == rebuild._package_checksums(drive)
    manifest = json.loads((local / "package-manifest.json").read_text(encoding="utf-8"))
    assert manifest["row_counts"] == {"curated_seed": 0, "rights_ledger": 0, "practice_admission": 0}


def test_existing_package_requires_explicit_replacement(tmp_path: Path) -> None:
    local = tmp_path / "local"
    drive = tmp_path / "drive" / "teacher-seed"
    rebuild.build_package(package_root=local, drive_root=drive, **_inputs(tmp_path))

    with pytest.raises(ValueError, match="package root already exists"):
        rebuild.build_package(package_root=local, drive_root=drive, **_inputs(tmp_path))

    receipt = rebuild.build_package(
        package_root=local,
        drive_root=drive,
        replace_existing=True,
        **_inputs(tmp_path),
    )
    assert receipt["package_file_count"] == 5
