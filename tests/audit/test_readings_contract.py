"""Focused tests for the final, fail-closed reading-record contract."""

from __future__ import annotations

from pathlib import Path

import pytest

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


def _plan(*entries: object, version: object = 2, **overrides: object) -> dict[str, object]:
    plan: dict[str, object] = {"readings_contract_version": version, "readings": list(entries)}
    plan.update(overrides)
    return plan


def _no_readings_plan(**overrides: object) -> dict[str, object]:
    plan: dict[str, object] = {"readings_contract_version": 2}
    plan.update(overrides)
    return plan


def _codes(report: dict[str, object]) -> list[str]:
    return [diagnostic["code"] for diagnostic in report["diagnostics"]]


def _write_reading_page(directory: Path, slug: str, title: str) -> None:
    (directory / f"{slug}.mdx").write_text(f"---\ntitle: {title}\n---\nТекст\n", encoding="utf-8")


def test_v2_link_only_record_passes(tmp_path: Path) -> None:
    report = validate_readings_contract(_plan(_entry()), readings_dir=tmp_path)

    assert report["passed"] is True
    assert report["status"] == "pass"
    assert report["entry_counts"] == {"pass": 1, "unmigrated": 0, "fail": 0}
    assert report["diagnostics"] == []


def test_v2_empty_readings_list_fails_with_stable_diagnostic(tmp_path: Path) -> None:
    report = validate_readings_contract(_plan(), readings_dir=tmp_path)

    assert report["status"] == "fail"
    assert report["passed"] is False
    assert report["diagnostics"] == [{"code": "RDR_READINGS_EMPTY", "field": "readings"}]


def test_not_applicable_reading_disposition_passes_without_readings_list(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _no_readings_plan(
            reading_disposition={
                "status": "not-applicable",
                "reason": "Модуль не передбачає окремого читання.",
                "evidence_url": "https://example.test/module-rationale",
            }
        ),
        readings_dir=tmp_path,
    )

    assert report["status"] == "pass"
    assert report["passed"] is True
    assert report["entry_counts"] == {"pass": 0, "unmigrated": 0, "fail": 0}


@pytest.mark.parametrize(
    ("disposition", "diagnostic"),
    [
        (
            {"status": "not-applicable", "reason": "", "evidence_url": "https://example.test/evidence"},
            "RDR_READING_DISPOSITION_REASON",
        ),
        ({"status": "not-applicable", "reason": "TBD", "evidence_url": "https://example.test/evidence"}, "RDR_READING_DISPOSITION_REASON"),
        ({"status": "pending", "reason": "Пояснення", "evidence_url": "https://example.test/evidence"}, "RDR_READING_DISPOSITION_STATUS"),
        ({"status": "not-applicable", "reason": "Пояснення", "evidence_url": "not-a-url"}, "RDR_READING_DISPOSITION_EVIDENCE_URL"),
    ],
)
def test_not_applicable_reading_disposition_requires_reviewed_values(
    tmp_path: Path, disposition: dict[str, str], diagnostic: str
) -> None:
    report = validate_readings_contract(
        _no_readings_plan(reading_disposition=disposition),
        readings_dir=tmp_path,
    )

    assert report["status"] == "fail"
    assert diagnostic in _codes(report)


@pytest.mark.parametrize("entries", [(), (_entry(),)])
def test_reading_disposition_conflicts_with_any_readings_list(tmp_path: Path, entries: tuple[object, ...]) -> None:
    report = validate_readings_contract(
        _plan(
            *entries,
            reading_disposition={
                "status": "not-applicable",
                "reason": "Модуль не передбачає окремого читання.",
                "evidence_url": "https://example.test/module-rationale",
            },
        ),
        readings_dir=tmp_path,
    )

    assert report["status"] == "fail"
    assert "RDR_READING_DISPOSITION_CONFLICT" in _codes(report)


def test_missing_readings_without_disposition_keeps_legacy_type_diagnostic(tmp_path: Path) -> None:
    report = validate_readings_contract(_no_readings_plan(), readings_dir=tmp_path)

    assert report["status"] == "fail"
    assert report["diagnostics"] == [{"code": "RDR_READINGS_TYPE", "field": "readings"}]


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


@pytest.mark.parametrize(
    ("hosting", "basis", "expected"),
    [
        ("link-only", "external-link", True),
        ("link-only", "public-domain", False),
        ("excerpt-only", "public-domain", True),
        ("excerpt-only", "open-license", True),
        ("excerpt-only", "permission", True),
        ("excerpt-only", "approved-exception", True),
        ("excerpt-only", "fair-use", False),
        ("excerpt-only", "cc-by", False),
        ("hosted", "public-domain", True),
        ("hosted", "open-license", True),
        ("hosted", "permission", True),
        ("hosted", "approved-exception", False),
        ("hosted", "fair-use", False),
        ("hosted", "licensed-excerpt", False),
    ],
)
def test_rights_basis_is_limited_by_hosting_mode(
    tmp_path: Path, hosting: str, basis: str, expected: bool
) -> None:
    entry = _entry(hosting=hosting, rights=_rights(basis=basis))
    if hosting == "excerpt-only":
        entry["locator"] = "Розділ 2"
    elif hosting == "hosted":
        entry["reading_slug"] = "reading"
        _write_reading_page(tmp_path, "reading", str(entry["title"]))

    report = validate_readings_contract(_plan(entry), readings_dir=tmp_path)

    assert report["passed"] is expected
    if not expected:
        assert (
            "RDR_LINK_RIGHTS_BASIS" if hosting == "link-only" else f"RDR_{hosting.split('-')[0].upper()}_RIGHTS_BASIS"
        ) in _codes(report)


def test_link_only_forbids_hosting_content_fields(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _plan(_entry(reading_slug="reading", locator="Розділ 2", excerpt_locator="С. 5")),
        readings_dir=tmp_path,
    )

    diagnostics = [
        (diagnostic["code"], diagnostic["field"])
        for diagnostic in report["diagnostics"]
        if diagnostic["code"] in {"RDR_LINK_READING_SLUG", "RDR_LINK_LOCATOR"}
    ]
    assert diagnostics == [
        ("RDR_LINK_READING_SLUG", "reading_slug"),
        ("RDR_LINK_LOCATOR", "locator"),
        ("RDR_LINK_LOCATOR", "excerpt_locator"),
    ]


def test_hosted_requires_an_existing_public_page_and_matching_title(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _plan(_entry(hosting="hosted", reading_slug="missing", rights=_rights(basis="public-domain"))),
        readings_dir=tmp_path,
    )

    assert report["status"] == "fail"
    assert "RDR_HOSTED_READING_PAGE" in _codes(report)

    _write_reading_page(tmp_path, "missing", "  БІОГРАФІЧНА   ДОВІДКА  ")
    report = validate_readings_contract(
        _plan(_entry(hosting="hosted", reading_slug="missing", rights=_rights(basis="public-domain"))),
        readings_dir=tmp_path,
    )

    assert report["passed"] is True

    _write_reading_page(tmp_path, "missing", "Інша назва")
    report = validate_readings_contract(
        _plan(_entry(hosting="hosted", reading_slug="missing", rights=_rights(basis="public-domain"))),
        readings_dir=tmp_path,
    )

    assert report["status"] == "fail"
    assert "RDR_HOSTED_READING_TITLE" in _codes(report)


@pytest.mark.parametrize(
    "placeholder",
    [
        "reading-needed",
        " pending ",
        "UNRESOLVED",
        "todo",
        "tbd",
        "потрібно   уточнити",
        "ПІДЛЯГАЄ-УТОЧНЕННЮ",
        "Потрібен_матеріал",
    ],
)
def test_specified_semantic_placeholders_are_rejected_in_normalized_forms(
    tmp_path: Path, placeholder: str
) -> None:
    report = validate_readings_contract(_plan(_entry(source_name=placeholder)), readings_dir=tmp_path)

    assert report["status"] == "fail"
    assert ("RDR_PLACEHOLDER", "source_name") in [
        (diagnostic["code"], diagnostic.get("field")) for diagnostic in report["diagnostics"]
    ]


def test_free_form_caveats_are_not_scanned_for_placeholders(tmp_path: Path) -> None:
    report = validate_readings_contract(
        _plan(_entry(caveats="TODO: add teaching note")),
        readings_dir=tmp_path,
    )

    assert report["passed"] is True
