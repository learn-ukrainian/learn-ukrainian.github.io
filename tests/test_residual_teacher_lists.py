"""Residual teacher-practice lists reuse the existing atlas admission classifier (#6064)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.atlas import residual_teacher_lists as residual


def _manifest(path: Path, entries: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    return path


def _seed_row(
    seed_row: int,
    lemma: str,
    *,
    status: str = "has_candidates",
    practice: bool = True,
    mode: str = "local_practice_private_teacher",
    reason: str = "private_local_teacher_material_local_practice_only",
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "seedRow": seed_row,
        "lemma": lemma,
        "gloss": "gloss",
        "sentenceStatus": status,
        "admission": {"practice": practice, "mode": mode, "reason": reason},
    }
    if extra:
        row.update(extra)
    return row


def _write_jsonl_file(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return path


def test_classify_residuals_splits_missing_route_and_no_cefr(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [
            {"lemma": "Справедливий", "url_slug": "справедливий", "pos": "adj", "enrichment": {"cefr": {"level": "B1", "source": "PULS"}}},
            {"lemma": "Витерти", "url_slug": "витерти", "pos": "verb"},
        ],
    )
    rows = [
        _seed_row(1, "Справедливий"),  # clean: route + cefr
        _seed_row(2, "Оренда"),  # no manifest entry at all
        _seed_row(3, "Витерти"),  # route but no cefr block
    ]

    result = residual.classify_residuals(rows, manifest)

    assert result["missing_route"] == [{"seedRow": 2, "lemma": "оренда", "mode": "local_practice_private_teacher"}]
    assert result["no_cefr"] == [{"seedRow": 3, "lemma": "витерти", "url_slug": "витерти"}]
    assert result["summary"]["counts"]["missing_route"] == 1
    assert result["summary"]["counts"]["no_cefr"] == 1
    assert result["summary"]["counts"]["input_rows"] == 3
    assert result["summary"]["counts"]["practice_admitted_rows"] == 1
    assert "other_atlas_failures" not in result["summary"]


def test_classify_residuals_ignores_rows_not_admitted_to_practice(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path / "manifest.json", [])
    rows = [
        _seed_row(
            1,
            "Незрозуміле",
            status="no_hit_strict_vesum",
            practice=False,
            mode="quarantined_no_document_hit",
            reason="no_document_hit_vesum_forms",
        )
    ]

    result = residual.classify_residuals(rows, manifest)

    assert result["missing_route"] == []
    assert result["no_cefr"] == []
    assert result["summary"]["counts"]["missing_route"] == 0
    assert result["summary"]["counts"]["practice_admitted_rows"] == 0


def test_classify_residuals_buckets_non_route_failures_separately(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [{"lemma": "Слово", "url_slug": "слово", "pos": "noun", "enrichment": {"cefr": {"level": "A1", "source": "PULS"}}}],
    )
    # sentenceStatus=ok + a non-local admission mode requires attestation;
    # this row has a route + CEFR but no example/provenance, so it fails for a
    # different reason than a missing route.
    rows = [_seed_row(1, "Слово", status="ok", mode="admitted", reason="rights_cleared")]

    result = residual.classify_residuals(rows, manifest)

    assert result["missing_route"] == []
    assert result["summary"]["counts"]["other_atlas_failures"] == 1
    assert result["summary"]["other_atlas_failures"] == [
        {"seedRow": 1, "lemma": "слово", "reason": "ok_row_missing_attestation"}
    ]


def test_write_residual_reports_writes_three_files(tmp_path: Path) -> None:
    result = {
        "missing_route": [{"seedRow": 2, "lemma": "оренда", "mode": "local_practice_private_teacher"}],
        "no_cefr": [{"seedRow": 3, "lemma": "витерти", "url_slug": "витерти"}],
        "summary": {"schema": residual.SUMMARY_SCHEMA, "counts": {"missing_route": 1, "no_cefr": 1}},
    }
    output_dir = tmp_path / "residual"

    residual.write_residual_reports(result, output_dir)

    missing_route_lines = (output_dir / "missing_route.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in missing_route_lines] == result["missing_route"]
    no_cefr_lines = (output_dir / "no_cefr.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in no_cefr_lines] == result["no_cefr"]
    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary == result["summary"]


def test_load_package_rows_missing_seed_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match=r"curated-seed\.jsonl not found"):
        residual.load_package_rows(tmp_path)


def test_load_package_rows_missing_admission_file_raises(tmp_path: Path) -> None:
    _write_jsonl_file(tmp_path / "curated-seed.jsonl", [_seed_row(1, "Справедливий")])

    with pytest.raises(FileNotFoundError, match=r"practice-admission\.jsonl not found"):
        residual.load_package_rows(tmp_path)


def test_load_package_rows_accepts_agreeing_package(tmp_path: Path) -> None:
    seed_rows = [_seed_row(1, "Справедливий"), _seed_row(2, "Оренда", practice=False, mode="quarantined_no_document_hit")]
    _write_jsonl_file(tmp_path / "curated-seed.jsonl", seed_rows)
    _write_jsonl_file(
        tmp_path / "practice-admission.jsonl",
        [
            {"seedRow": 1, "lemma": "Справедливий", "practice": True, "mode": "local_practice_private_teacher"},
            {"seedRow": 2, "lemma": "Оренда", "practice": False, "mode": "quarantined_no_document_hit"},
        ],
    )

    rows = residual.load_package_rows(tmp_path)

    assert [row["seedRow"] for row in rows] == [1, 2]


def test_load_package_rows_detects_practice_flag_drift(tmp_path: Path) -> None:
    _write_jsonl_file(tmp_path / "curated-seed.jsonl", [_seed_row(1, "Справедливий", practice=True)])
    _write_jsonl_file(
        tmp_path / "practice-admission.jsonl",
        [{"seedRow": 1, "lemma": "Справедливий", "practice": False, "mode": "local_practice_private_teacher"}],
    )

    with pytest.raises(ValueError, match="practice flag disagrees"):
        residual.load_package_rows(tmp_path)


def test_load_package_rows_detects_mode_drift(tmp_path: Path) -> None:
    _write_jsonl_file(tmp_path / "curated-seed.jsonl", [_seed_row(1, "Справедливий", mode="local_practice_private_teacher")])
    _write_jsonl_file(
        tmp_path / "practice-admission.jsonl",
        [{"seedRow": 1, "lemma": "Справедливий", "practice": True, "mode": "some_other_mode"}],
    )

    with pytest.raises(ValueError, match="admission mode disagrees"):
        residual.load_package_rows(tmp_path)


def test_verify_admission_consistency_detects_duplicate_admission_rows() -> None:
    seed_rows = [_seed_row(1, "Справедливий")]
    admission_rows = [
        {"seedRow": 1, "lemma": "Справедливий", "practice": True, "mode": "local_practice_private_teacher"},
        {"seedRow": 1, "lemma": "Справедливий", "practice": True, "mode": "local_practice_private_teacher"},
    ]

    with pytest.raises(ValueError, match="duplicate seedRow"):
        residual.verify_admission_consistency(seed_rows, admission_rows)
