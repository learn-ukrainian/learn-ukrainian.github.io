"""Focused tests for the deterministic BIO catalog-source structural readiness audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.audit import bio_catalog_source_readiness as readiness


def _write_manifest(root: Path, slugs: list[str]) -> None:
    path = root / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"levels": {"bio": {"modules": slugs}}}), encoding="utf-8")


def _write_plan(root: Path, slug: str, *, readings: bool = True) -> Path:
    path = root / "curriculum" / "l2-uk-en" / "plans" / "bio" / f"{slug}.yaml"
    path.parent.mkdir(parents=True)
    plan = {
        "module": "bio-001",
        "level": "BIO",
        "sequence": 1,
        "slug": slug,
        "title": "Іван Франко",
        "subtitle": "Біографічний семінар",
        "content_outline": [{"section": "Вступ", "words": 100, "points": ["Ключова теза."]}],
        "word_target": 100,
        "references": [{"title": "Джерело"}],
    }
    if readings:
        plan["readings"] = [{"title": "Читання", "source_url": "https://example.test/reading"}]
    path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _write_complete_wiki_pair(root: Path, slug: str) -> tuple[Path, Path]:
    wiki_path = root / "wiki" / "figures" / f"{slug}.md"
    source_path = wiki_path.with_suffix(".sources.yaml")
    wiki_path.parent.mkdir(parents=True)
    long_body = "Перевірений зміст. " * 750
    wiki_path.write_text(
        f"""# Біографія: Іван Франко: Семінар

<!-- wiki-meta
slug: {slug}
-->

## Короткий зміст

Коротка перевірена довідка [S1].

## Основний зміст

Розгорнута довідка [S2]. {long_body}

## Ключові терміни

Термін — пояснення.

## Мовні зразки

Мовний зразок.

## Деколонізаційна перспектива

Критичне прочитання імперського привласнення.

## Пов'язані статті

- Пов'язаний матеріал.
""",
        encoding="utf-8",
    )
    source_path.write_text(
        """sources:
- id: S1
  file: https://example.test/one
  type: external
  url: https://example.test/one
- id: S2
  file: https://example.test/two
  type: external
  url: https://example.test/two
""",
        encoding="utf-8",
    )
    return wiki_path, source_path


def _write_complete_catalog(root: Path, slug: str = "known") -> None:
    _write_manifest(root, [slug])
    dossier = root / "docs" / "research" / "bio" / f"{slug}.md"
    dossier.parent.mkdir(parents=True)
    dossier.write_text("# Дослідницьке досьє\n", encoding="utf-8")
    _write_plan(root, slug)
    _write_complete_wiki_pair(root, slug)


def test_structurally_complete_row_uses_only_deterministic_artifact_gates(tmp_path: Path) -> None:
    _write_complete_catalog(tmp_path)

    report = readiness.build_catalog_readiness(root=tmp_path)

    assert report["summary"]["catalog_source_structural_complete_rows"] == 1
    row = report["rows"][0]
    assert row["slug"] == "known"
    assert row["catalog_source_structural_complete"] is True
    assert row["blocker_codes"] == []
    assert set(row["gates"]) == set(readiness.CATALOG_GATES)
    assert row["gates"]["source_registry"]["status"] == "pass"
    assert row["gates"]["dossier"]["evidence_paths"] == ["docs/research/bio/known.md"]


def test_missing_artifacts_are_explicit_fail_closed_blockers(tmp_path: Path) -> None:
    _write_manifest(tmp_path, ["missing"])

    report = readiness.build_catalog_readiness(root=tmp_path)

    row = report["rows"][0]
    assert row["catalog_source_structural_complete"] is False
    assert {
        "DOSSIER_MISSING",
        "PLAN_MISSING",
        "READING_PACKET_MISSING",
        "WIKI_PAIR_MISSING",
        "SOURCE_REGISTRY_INVALID",
    } <= set(row["blocker_codes"])
    assert row["gates"]["plan_check"]["status"] == "fail"
    assert row["gates"]["wiki_completeness"]["status"] == "fail"


def test_empty_readings_and_invalid_sibling_registry_are_reported_separately(tmp_path: Path) -> None:
    _write_complete_catalog(tmp_path)
    plan_path = tmp_path / "curriculum" / "l2-uk-en" / "plans" / "bio" / "known.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan["readings"] = []
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    source_path = tmp_path / "wiki" / "figures" / "known.sources.yaml"
    source_path.write_text(
        """sources:
- id: S1
  file: https://example.test/one
  type: external
  url: https://example.test/one
""",
        encoding="utf-8",
    )

    report = readiness.build_catalog_readiness(root=tmp_path)

    row = report["rows"][0]
    assert row["gates"]["readings"]["status"] == "fail"
    assert row["gates"]["source_registry"]["status"] == "fail"
    assert "Missing registry entry for citation S2" in row["gates"]["source_registry"]["detail"]
    assert {"READING_PACKET_MISSING", "SOURCE_REGISTRY_INVALID"} <= set(row["blocker_codes"])


def test_duplicate_source_registry_key_is_rejected(tmp_path: Path) -> None:
    _write_complete_catalog(tmp_path)
    source_path = tmp_path / "wiki" / "figures" / "known.sources.yaml"
    source_path.write_text(
        """sources:
- id: S1
  id: S2
  file: https://example.test/one
  type: external
""",
        encoding="utf-8",
    )

    report = readiness.build_catalog_readiness(root=tmp_path)

    gate = report["rows"][0]["gates"]["source_registry"]
    assert gate["status"] == "fail"
    assert "duplicate YAML key" in gate["detail"]


def test_wiki_quality_failure_is_a_separate_catalog_blocker(tmp_path: Path) -> None:
    _write_complete_catalog(tmp_path)
    wiki_path = tmp_path / "wiki" / "figures" / "known.md"
    wiki_path.write_text(wiki_path.read_text(encoding="utf-8") + "\nTODO\n", encoding="utf-8")

    report = readiness.build_catalog_readiness(root=tmp_path)

    row = report["rows"][0]
    assert row["gates"]["wiki_quality"]["status"] == "fail"
    assert "PLACEHOLDER_TEXT" in row["gates"]["wiki_quality"]["detail"]
    assert "WIKI_QUALITY_FAIL" in row["blocker_codes"]


def test_cli_json_emits_one_manifest_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    _write_complete_catalog(tmp_path)
    monkeypatch.setattr(readiness, "PROJECT_ROOT", tmp_path)

    assert readiness.main(["--format", "json"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["manifest_rows"] == 1
    assert [row["slug"] for row in report["rows"]] == ["known"]
