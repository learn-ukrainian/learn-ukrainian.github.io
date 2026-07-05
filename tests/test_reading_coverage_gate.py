from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.build.linear_pipeline import PYTHON_QG_GATE_ORDER, _reading_coverage_gate


def _run_fixture_gate(tmp_path: Path, plan: dict[str, Any], module_text: str) -> dict[str, Any]:
    plan_path = tmp_path / "plan.yaml"
    module_path = tmp_path / "module.md"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    module_path.write_text(module_text, encoding="utf-8")
    loaded_plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    return _reading_coverage_gate(module_path.read_text(encoding="utf-8"), loaded_plan)


def _primary_reading_block(title: str, slug: str | None = None) -> str:
    attrs = f'{{reading="{slug}"}}' if slug else ""
    return f""":::primary-reading{attrs}
> Рядок першоджерела.

— Народна творчість, {title}
:::
"""


def _module_with_four_blocks(
    first_title: str = "«Інший текст»",
    first_slug: str = "pershyi-tekst",
) -> str:
    return "\n".join(
        [
            _primary_reading_block(first_title, first_slug),
            _primary_reading_block("«Другий текст»", "druhyi-tekst"),
            _primary_reading_block("«Третій текст»", "tretii-tekst"),
            _primary_reading_block("«Четвертий текст»", "chetvertyi-tekst"),
        ]
    )


def test_reading_coverage_gate_registered_in_python_qg_order() -> None:
    assert PYTHON_QG_GATE_ORDER.index("resource_coverage") < PYTHON_QG_GATE_ORDER.index("reading_coverage")
    assert PYTHON_QG_GATE_ORDER.index("reading_coverage") < PYTHON_QG_GATE_ORDER.index("resources_url_resolve")


def test_hard_pass_when_host_reading_is_structured_on_site_excerpt(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {"title": "«Ой весна»", "hosting": "host", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, _module_with_four_blocks('"Ой весна"', "oi-vesna"))

    assert result["passed"] is True
    assert result["missing_hosted_readings"] == []
    assert result["structured_on_site_readings"] == 4
    assert "warning" not in result


def test_hard_fail_when_host_reading_has_only_bare_external_link(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {"title": "«Ой весна»", "hosting": "host", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, "Read the hosted source at /readings/oi-vesna/.")

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["structured_on_site_readings"] == 0
    assert result["missing_hosted_readings"] == [
        {"title": "«Ой весна»", "reading_slug": "oi-vesna"},
    ]
    assert result["missing_on_site_reading"]["severity"] == "HARD"
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

    result = _run_fixture_gate(tmp_path, plan, _module_with_four_blocks("„думи нічні“", "dumy-nichni"))

    assert result["passed"] is True
    assert result["missing_hosted_readings"] == []


def test_linked_only_reading_omission_is_failure_for_folk(tmp_path: Path) -> None:
    plan = {
        "level": "folk",
        "readings": [
            {"title": "«Ой весна»", "hosting": "linked-only", "reading_slug": "oi-vesna"},
        ],
    }

    result = _run_fixture_gate(tmp_path, plan, "")

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["checked"] == 0
    assert result["missing_hosted_readings"] == []
    assert result["missing_on_site_reading"]["severity"] == "HARD"


def test_orphan_inline_snippets_do_not_count_as_folk_on_site_reading(tmp_path: Path) -> None:
    plan = {"level": "folk", "readings": []}
    module_text = "\n".join([_primary_reading_block("«Один»"), _primary_reading_block("«Два»")])

    result = _run_fixture_gate(tmp_path, plan, module_text)

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["surfaced_primary_readings"] == 2
    assert result["structured_on_site_readings"] == 0
    assert result["unstructured_primary_readings"] == 2
    assert result["missing_on_site_reading"]["severity"] == "HARD"


def test_floor_warning_is_advisory_and_exception_suppresses_it(tmp_path: Path) -> None:
    plan = {"level": "folk", "readings": []}
    module_text = "\n".join(
        [
            _primary_reading_block("«Один»", "odyn"),
            _primary_reading_block("«Два»", "dva"),
        ]
    )

    warning_result = _run_fixture_gate(tmp_path, plan, module_text)
    assert warning_result["passed"] is True
    assert warning_result["structured_on_site_readings"] == 2
    assert "missing_on_site_reading" not in warning_result
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
    assert "missing_on_site_reading" not in exception_result
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
    ("plan", "module_text", "expect_floor_warning"),
    [
        pytest.param(
            {
                "level": "folk",
                "readings": [
                    {
                        "title": "«Ой весна»",
                        "hosting": "host",
                        "reading_slug": "oi-vesna",
                    },
                ],
            },
            _module_with_four_blocks("«Ой весна»", "oi-vesna"),
            False,
            id="hosted-title-attribution",
        ),
        pytest.param(
            {
                "level": "folk",
                "readings": [
                    {
                        "title": "«Гей, соколи»",
                        "hosting": "hosted",
                        "reading_slug": "hei-sokoly",
                    },
                ],
            },
            _module_with_four_blocks("«Гей, соколи»", "hei-sokoly"),
            False,
            id="hosted-alias-attribution",
        ),
        pytest.param(
            {
                "level": "folk",
                "readings": [
                    {
                        "title": "«Дума про втечу трьох братів з Азова»",
                        "hosting": "host",
                        "reading_slug": "duma-pro-vtechu-trokh-brativ-z-azova",
                    },
                ],
            },
            _module_with_four_blocks(
                "«Дума про втечу трьох братів з Азова»",
                "duma-pro-vtechu-trokh-brativ-z-azova",
            ),
            False,
            id="long-hosted-title-attribution",
        ),
        pytest.param(
            {
                "level": "folk",
                "readings": [
                    {
                        "title": "«Щедрий вечір»",
                        "hosting": "host",
                        "reading_slug": "shchedryi-vechir",
                    },
                ],
            },
            _module_with_four_blocks("«Щедрий вечір»", "shchedryi-vechir"),
            False,
            id="hosted-title-no-floor-warning",
        ),
    ],
)
def test_fixture_folk_modules_all_pass_reading_coverage(
    plan: dict[str, Any], module_text: str, expect_floor_warning: bool
) -> None:
    result = _reading_coverage_gate(module_text, plan)

    assert result["passed"] is True
    assert result["missing_hosted_readings"] == []
    assert result["structured_on_site_readings"] == 4
    if expect_floor_warning:
        assert result["warning"]["severity"] == "WARNING"
    else:
        assert "warning" not in result
