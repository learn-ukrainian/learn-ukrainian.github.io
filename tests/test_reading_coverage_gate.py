from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.build.linear_pipeline import PYTHON_QG_GATE_ORDER, _reading_coverage_gate

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_fixture_gate(tmp_path: Path, plan: dict[str, Any], module_text: str) -> dict[str, Any]:
    plan_path = tmp_path / "plan.yaml"
    module_path = tmp_path / "module.md"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    module_path.write_text(module_text, encoding="utf-8")
    loaded_plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    return _reading_coverage_gate(module_path.read_text(encoding="utf-8"), loaded_plan)


def _primary_reading_block(title: str) -> str:
    return f""":::primary-reading
> Рядок першоджерела.

— Народна творчість, {title}
:::
"""


def _module_with_four_blocks(first_title: str = "«Інший текст»") -> str:
    return "\n".join(
        [
            _primary_reading_block(first_title),
            _primary_reading_block("«Другий текст»"),
            _primary_reading_block("«Третій текст»"),
            _primary_reading_block("«Четвертий текст»"),
        ]
    )


def test_reading_coverage_gate_registered_in_python_qg_order() -> None:
    assert PYTHON_QG_GATE_ORDER.index("resource_coverage") < PYTHON_QG_GATE_ORDER.index("reading_coverage")
    assert PYTHON_QG_GATE_ORDER.index("reading_coverage") < PYTHON_QG_GATE_ORDER.index("resources_url_resolve")


def test_hard_pass_when_host_reading_title_is_in_primary_reading_attribution(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {"title": "«Ой весна»", "hosting": "host", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, _module_with_four_blocks('"Ой весна"'))

    assert result["passed"] is True
    assert result["missing_hosted_readings"] == []
    assert "warning" not in result


def test_hard_pass_when_host_reading_slug_link_is_in_module(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {"title": "«Ой весна»", "hosting": "host", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, "Read the hosted source at /readings/oi-vesna/.")

    assert result["passed"] is True
    assert result["missing_hosted_readings"] == []
    assert result["warning"]["severity"] == "WARNING"


def test_hard_fail_when_host_reading_is_omitted(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {"title": "«Ой весна»", "hosting": "host", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, _module_with_four_blocks())

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["missing_hosted_readings"] == [
        {"title": "«Ой весна»", "reading_slug": "oi-vesna"},
    ]


def test_title_normalization_matches_quote_glyphs_case_and_whitespace(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {
                "title": "«  Думи   нічні  »",
                "hosting": "hosted",
                "reading_slug": "dumy-nichni",
            },
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, _module_with_four_blocks("„думи нічні“"))

    assert result["passed"] is True
    assert result["missing_hosted_readings"] == []


def test_linked_only_reading_omission_is_not_a_failure(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {"title": "«Ой весна»", "hosting": "linked-only", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, _module_with_four_blocks())

    assert result["passed"] is True
    assert result["checked"] == 0
    assert result["missing_hosted_readings"] == []


def test_floor_warning_is_advisory_and_exception_suppresses_it(tmp_path: Path) -> None:
    plan = {"level": "folk", "readings": []}
    module_text = "\n".join([_primary_reading_block("«Один»"), _primary_reading_block("«Два»")])

    warning_result = _run_fixture_gate(tmp_path, plan, module_text)
    assert warning_result["passed"] is True
    assert warning_result["warning"] == {
        "severity": "WARNING",
        "message": (
            "fewer than 4 primary-reading blocks surfaced; floor is advisory "
            "and does not affect gate pass/fail"
        ),
        "surfaced": 2,
        "expected_minimum": 4,
    }

    exception_plan = {
        "level": "folk",
        "readings": [],
        "reading_coverage_exception": "corpus acquisition blocked",
    }
    exception_result = _run_fixture_gate(tmp_path, exception_plan, module_text)
    assert exception_result["passed"] is True
    assert "warning" not in exception_result


def test_non_seminar_level_is_skipped(tmp_path: Path) -> None:
    plan = {
        "level": "a1",
        "readings": [
            {"title": "«Ой весна»", "hosting": "host", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, "")

    assert result == {"passed": True, "skipped": "non-seminar"}


@pytest.mark.parametrize(
    ("slug", "expect_floor_warning"),
    [
        ("koliadky-shchedrivky", False),
        ("kalendarna-obriadovist-zvychai", False),
        ("narodna-kultura-yak-systema", False),
        ("dumy-nevilnytski-lytsarski", False),
        ("narodni-viruvannia-mifolohiia-demonolohiia", True),
        ("zamovliannia-zaklynannia-prymovky", True),
    ],
)
def test_real_built_folk_modules_all_pass_reading_coverage(slug: str, expect_floor_warning: bool) -> None:
    plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / "folk" / f"{slug}.yaml"
    module_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "folk" / slug / "module.md"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    module_text = module_path.read_text(encoding="utf-8")

    result = _reading_coverage_gate(module_text, plan)

    assert result["passed"] is True
    assert result["missing_hosted_readings"] == []
    if expect_floor_warning:
        assert result["warning"]["severity"] == "WARNING"
    else:
        assert "warning" not in result
