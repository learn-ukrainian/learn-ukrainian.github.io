"""Focused tests for the final, fail-closed reading-record contract."""

from __future__ import annotations

from pathlib import Path

from scripts.audit.readings_contract import validate_readings_contract


def _rights(*, basis: str = "external-link", evidence_url: str = "https://example.test/reading") -> dict[str, str]:
    return {"basis": basis, "evidence_url": evidence_url, "note": "Відомості про права перевірено."}


def _entry(**overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "title": "Біографічна довідка",
        "source_name": "Перевірене джерело",
        "source_url": "https://example.test/reading",
        "language": "uk",
        "hosting": "link-only",
        "learner_task": "Виписати ключові факти та звірити їх із модулем.",
        "rights": _rights(),
    }
    entry.update(overrides)
    return entry


def _plan(*entries: object, version: object = 2) -> dict[str, object]:
    return {"readings_contract_version": version, "readings": list(entries)}


def _codes(report: dict[str, object]) -> list[str]:
    return [diagnostic["code"] for diagnostic in report["diagnostics"]]


def test_v2_link_only_record_passes(tmp_path: Path) -> None:
    report = validate_readings_contract(_plan(_entry()), readings_dir=tmp_path)

    assert report["passed"] is True
    assert report["status"] == "pass"
    assert report["entry_counts"] == {"pass": 1, "unmigrated": 0, "fail": 0}
    assert report["diagnostics"] == []


def test_legacy_aliases_are_normalized_for_diagnostics_but_never_pass(tmp_path: Path) -> None:
    legacy = _entry()
    legacy.pop("source_name")
    legacy.pop("source_url")
    legacy.pop("learner_task")
    legacy.update({"source": "https://example.test/reading", "url": "https://example.test/reading", "task": "Прочитати."})

    report = validate_readings_contract(_plan(legacy, version=1), readings_dir=tmp_path)

    assert report["passed"] is False
    assert report["status"] == "unmigrated"
    assert report["entry_counts"]["unmigrated"] == 1
    assert {"RDR_VERSION_UNSUPPORTED", "RDR_LEGACY_FIELD", "RDR_REQUIRED"} <= set(_codes(report))


def test_normalizer_reports_conflicting_legacy_aliases(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _plan(_entry(url="https://elsewhere.test/reading")),
        readings_dir=tmp_path,
    )

    assert report["passed"] is False
    assert report["status"] == "unmigrated"
    assert "RDR_NORMALIZATION_CONFLICT" in _codes(report)


def test_normalizer_maps_non_url_source_and_task_without_silent_acceptance(tmp_path: Path) -> None:
    legacy = _entry()
    legacy.pop("source_name")
    legacy.pop("learner_task")
    legacy.update({"source": "Енциклопедія України", "task": "Прочитати матеріал."})

    report = validate_readings_contract(_plan(legacy, version=1), readings_dir=tmp_path)

    assert report["status"] == "unmigrated"
    assert report["entry_counts"]["unmigrated"] == 1
    assert "RDR_REQUIRED" not in _codes(report)
    assert [diagnostic["field"] for diagnostic in report["diagnostics"] if diagnostic["code"] == "RDR_LEGACY_FIELD"] == [
        "source",
        "task",
    ]


def test_excerpt_requires_locator_and_explicit_content_rights_basis(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _plan(_entry(hosting="excerpt-only", rights=_rights(basis="external-link"))),
        readings_dir=tmp_path,
    )

    assert report["status"] == "fail"
    assert {"RDR_EXCERPT_LOCATOR", "RDR_EXCERPT_RIGHTS_BASIS"} <= set(_codes(report))


def test_hosted_requires_an_existing_public_page(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _plan(_entry(hosting="hosted", reading_slug="missing", rights=_rights(basis="public-domain"))),
        readings_dir=tmp_path,
    )

    assert report["status"] == "fail"
    assert "RDR_HOSTED_READING_PAGE" in _codes(report)

    (tmp_path / "missing.mdx").write_text("---\ntitle: Читання\n---\nТекст\n", encoding="utf-8")
    report = validate_readings_contract(
        _plan(_entry(hosting="hosted", reading_slug="missing", rights=_rights(basis="public-domain"))),
        readings_dir=tmp_path,
    )

    assert report["passed"] is True


def test_placeholders_are_rejected_only_in_contract_semantic_fields(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _plan(_entry(source_name="TBD", caveats="TODO: add teaching note")),
        readings_dir=tmp_path,
    )

    fields = [
        diagnostic.get("field")
        for diagnostic in report["diagnostics"]
        if diagnostic["code"] == "RDR_PLACEHOLDER"
    ]
    assert fields == ["source_name"]
