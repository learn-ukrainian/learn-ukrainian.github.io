from __future__ import annotations

from typing import Any

from scripts.audit.wiki_coverage_gate import check_wiki_coverage
from scripts.build.phases.implementation_map import seed_implementation_map

BAN_1_RULE = (
    "При викладанні теми «Мій ранок» та семантики зворотних дієслів категорично заборонено "
    "використовувати будь-які російськомовні пояснення, паралелі чи фонетичні порівняння. "
    "Це абсолютна вимога деколонізованої педагогіки [S9]."
)
BAN_4_RULE = (
    "У лексичному наповненні теми ранкової рутини слід рішуче відкидати русизми, суржик "
    "та кальки, які можуть випадково просочитися в тексти. Слід суворо контролювати чистоту "
    "словника: використовуємо виключно «рушник» (не «полотенце»), «сніданок» (не «завтрак»), "
    "«одягатися» (не «одіватися») [S2, S3]. Процес навчання має занурювати студента в "
    "автентичний простір, де панує українська мова без сторонніх домішок [S3]. Будь-які "
    "конструкції, що вказують на вік, на кшталт «Я маю N років» (калька) беззастережно "
    "замінюються на питомо українські: «Мені N років» [S8, S9]."
)


def _ban_manifest(rule: str) -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [
            {
                "id": "ban-1",
                "rule": rule,
                "source_lines": "50",
            }
        ],
        "external_resources": [],
    }


def _claim() -> dict[str, dict[str, str]]:
    return {
        "ban-1": {
            "artifact": "module.md",
            "location": "whole file",
            "treatment": "decolonization ban treatment",
        }
    }


def _ban_result(report: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in report["obligations"] if item["obligation_id"] == "ban-1")


def test_decolonization_ban_substance_required_passes_when_pair_present() -> None:
    manifest = _ban_manifest(BAN_4_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md=(
            "Use «рушник» (не «полотенце»), «сніданок» (не «завтрак»), "
            "and «одягатися» (не «одіватися»). Prefer «Мені N років» over "
            "the calque «Я маю N років»."
        ),
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    result = _ban_result(report)
    assert report["passed"] is True
    assert result["status"] == "PASS"
    assert result["reason"] == "ban_substance_present"
    assert result["subtype"] == "substance_required"


def test_decolonization_ban_substance_required_fails_when_pair_missing() -> None:
    manifest = _ban_manifest(BAN_4_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md="This paragraph is present but does not include the lexical substitutions.",
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    result = _ban_result(report)
    assert report["passed"] is False
    assert result["status"] == "FAIL"
    assert result["reason"] == "ban_substance_missing"
    assert result["subtype"] == "substance_required"


def test_decolonization_ban_absence_required_passes_automatically() -> None:
    manifest = _ban_manifest(BAN_1_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md="This module teaches the Ukrainian morning routine with Ukrainian-only framing.",
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    result = _ban_result(report)
    assert report["passed"] is True
    assert result["status"] == "PASS"
    assert result["reason"] == "absence_obligation_assumed_satisfied"
    assert result["subtype"] == "absence_required"


def test_decolonization_ban_legacy_manifest_without_subtype_field() -> None:
    manifest = _ban_manifest(BAN_1_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md="This module avoids the prohibited framing.",
        activities_yaml="[]",
    )

    result = _ban_result(report)
    assert report["passed"] is False
    assert result["status"] == "FAIL"
    assert result["reason"] == "ban_substance_missing"
    assert "subtype" not in result
