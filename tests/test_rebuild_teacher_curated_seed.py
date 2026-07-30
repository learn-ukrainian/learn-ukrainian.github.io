"""Tests for the fail-closed teacher curated-seed recovery package."""

from __future__ import annotations

import json
import shutil
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


def test_classify_rights_admission_is_explicit_and_fail_closed() -> None:
    rights, admission = rebuild.classify_rights_admission("no_hit_strict_vesum", None)

    assert rights == {
        "status": "private_local",
        "redistributable": False,
        "reason": "no_document_hit_vesum_forms",
    }
    assert admission == {
        "practice": False,
        "mode": "quarantined_no_document_hit",
        "reason": "no_document_hit_vesum_forms",
    }

    rights, admission = rebuild.classify_rights_admission("has_candidates", "source/chunk/1")

    assert rights["status"] == "private_local"
    assert rights["redistributable"] is False
    assert admission["mode"] == "pending_operator_redistribution_go"
    assert admission["practice"] is False

    rights, admission = rebuild.classify_rights_admission("ok", "source/chunk/1")

    assert rights["status"] == "quarantined_unreviewed_sentence_status"
    assert admission["mode"] == "quarantined_unreviewed_sentence_status"


def test_classify_rights_admission_quarantines_missing_locator() -> None:
    rights, admission = rebuild.classify_rights_admission("has_candidates", None)

    assert rights["status"] == "quarantined_missing_document_locator"
    assert admission == {
        "practice": False,
        "mode": "quarantined_missing_document_locator",
        "reason": "has_candidates_without_document_locator",
    }


def test_refresh_rights_ledger_mirrors_explicit_states(tmp_path: Path) -> None:
    package = tmp_path / "package"
    mirror = tmp_path / "drive" / "teacher-seed"
    package.mkdir()
    mirror.parent.mkdir(parents=True)
    seed_rows = [
        {"seedRow": 1, "lemma": "слово", "sentenceStatus": "has_candidates"},
        {"seedRow": 2, "lemma": "інше", "sentenceStatus": "no_hit_strict_vesum"},
    ]
    ledger_rows = [
        {"seedRow": 1, "lemma": "слово", "sentenceStatus": "has_candidates", "locator": "chunk/1"},
        {"seedRow": 2, "lemma": "інше", "sentenceStatus": "no_hit_strict_vesum", "locator": None},
    ]
    for name, rows in (("curated-seed.jsonl", seed_rows), ("rights-ledger.jsonl", ledger_rows)):
        _write(package / name, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    _write(package / "practice-admission.jsonl", "")
    _write(package / "package-manifest.json", json.dumps({"schema": "teacher-curated-seed-recovery-v1"}))
    _write(package / "source-recon.json", "{}")
    shutil.copytree(package, mirror)

    receipt = rebuild.refresh_rights_ledger(package_root=package, drive_root=mirror)

    refreshed_seed = [json.loads(line) for line in (package / "curated-seed.jsonl").read_text(encoding="utf-8").splitlines()]
    refreshed_admission = [json.loads(line) for line in (package / "practice-admission.jsonl").read_text(encoding="utf-8").splitlines()]
    assert refreshed_seed[0]["rights"]["status"] == "private_local"
    assert refreshed_seed[0]["admission"]["mode"] == "pending_operator_redistribution_go"
    assert refreshed_seed[1]["admission"]["reason"] == "no_document_hit_vesum_forms"
    assert refreshed_admission[0]["practice"] is False
    assert receipt["practice_admitted"] == 0
    assert rebuild._tree_checksums(package) == rebuild._tree_checksums(mirror)


def test_refresh_rights_ledger_rejects_duplicate_curated_seed_rows(tmp_path: Path) -> None:
    package = tmp_path / "package"
    mirror = tmp_path / "drive" / "teacher-seed"
    package.mkdir()
    mirror.parent.mkdir(parents=True)
    seed_rows = [
        {"seedRow": 1, "lemma": "слово", "sentenceStatus": "has_candidates"},
        {"seedRow": 1, "lemma": "інше", "sentenceStatus": "no_hit_strict_vesum"},
    ]
    ledger_rows = [
        {"seedRow": 1, "lemma": "слово", "sentenceStatus": "has_candidates", "locator": "chunk/1"},
        {"seedRow": 2, "lemma": "інше", "sentenceStatus": "no_hit_strict_vesum", "locator": None},
    ]
    for name, rows in (("curated-seed.jsonl", seed_rows), ("rights-ledger.jsonl", ledger_rows)):
        _write(package / name, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    _write(package / "practice-admission.jsonl", "")
    _write(package / "package-manifest.json", json.dumps({"schema": "teacher-curated-seed-recovery-v1"}))
    _write(package / "source-recon.json", "{}")
    shutil.copytree(package, mirror)

    with pytest.raises(ValueError, match="curated seed contains duplicate seedRow values"):
        rebuild.refresh_rights_ledger(package_root=package, drive_root=mirror)


def test_refresh_rights_ledger_rolls_back_both_copies_after_post_sync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "package"
    mirror = tmp_path / "drive" / "teacher-seed"
    package.mkdir()
    mirror.parent.mkdir(parents=True)
    seed_row = {"seedRow": 1, "lemma": "слово", "sentenceStatus": "has_candidates"}
    ledger_row = {
        "seedRow": 1,
        "lemma": "слово",
        "sentenceStatus": "has_candidates",
        "locator": "chunk/1",
    }
    _write(package / "curated-seed.jsonl", json.dumps(seed_row, ensure_ascii=False) + "\n")
    _write(package / "rights-ledger.jsonl", json.dumps(ledger_row, ensure_ascii=False) + "\n")
    _write(package / "practice-admission.jsonl", "")
    _write(package / "package-manifest.json", json.dumps({"schema": "teacher-curated-seed-recovery-v1"}))
    _write(package / "source-recon.json", "{}")
    shutil.copytree(package, mirror)
    package_before = {path.relative_to(package): path.read_bytes() for path in package.rglob("*") if path.is_file()}
    mirror_before = {path.relative_to(mirror): path.read_bytes() for path in mirror.rglob("*") if path.is_file()}

    original_sync_tree = rebuild._sync_tree
    sync_calls = 0

    def fail_after_drive_sync(source: Path, destination: Path) -> None:
        nonlocal sync_calls
        sync_calls += 1
        if sync_calls == 2:
            raise OSError("simulated local package sync failure")
        original_sync_tree(source, destination)

    monkeypatch.setattr(rebuild, "_sync_tree", fail_after_drive_sync)

    with pytest.raises(OSError, match="simulated local package sync failure"):
        rebuild.refresh_rights_ledger(package_root=package, drive_root=mirror)

    assert {
        path.relative_to(package): path.read_bytes() for path in package.rglob("*") if path.is_file()
    } == package_before
    assert {
        path.relative_to(mirror): path.read_bytes() for path in mirror.rglob("*") if path.is_file()
    } == mirror_before


def test_has_locator_rejects_empty_mapping_values() -> None:
    from scripts.atlas.rebuild_teacher_curated_seed import _has_locator, classify_rights_admission

    assert _has_locator({"source_file": None, "offset": None}) is False
    assert _has_locator({"note": ""}) is False
    assert _has_locator({"locator": "teacher_doc_paragraphs:1"}) is True
    rights, admission = classify_rights_admission("has_candidates", {"source_file": None})
    assert rights["status"] == "quarantined_missing_document_locator"
    assert admission.get("practice") is False
