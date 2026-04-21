from __future__ import annotations

import sys
from pathlib import Path

from ruamel.yaml import YAML

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from tools.fix_plan_latin_refs import fix_plan_file, replace_latin_module_refs


def test_replace_latin_module_refs_handles_prepositions_and_dash_contexts() -> None:
    cases = {
        "з M48": "з модуля 48",
        "із M48": "із модуля 48",
        "в M48": "у модулі 48",
        "У M48": "У модулі 48",
        "до M48": "до модуля 48",
        "про M48": "про модуль 48",
        "Числа — M10": "Числа — модуль №10",
    }

    for source, expected in cases.items():
        assert replace_latin_module_refs(source) == expected


def test_replace_latin_module_refs_formats_ranges_and_lists() -> None:
    assert replace_latin_module_refs("M28-M32") == "№28–32"
    assert replace_latin_module_refs("M16-17") == "№16–17"
    assert replace_latin_module_refs("від M27-M35") == "від модулів 27–35"


def test_replace_latin_module_refs_leaves_cefr_labels_untouched() -> None:
    source = "Говорити, звідки ви (A1.1) та що ви робите (A1.3)"
    assert replace_latin_module_refs(source) == source


def test_replace_latin_module_refs_handles_mixed_parenthetical_lists() -> None:
    source = "(Числа — M10, покупки — M37)"
    expected = "(Числа — модуль №10, покупки — модуль №37)"
    assert replace_latin_module_refs(source) == expected


def test_fix_plan_file_skips_module_and_external_resource_titles(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "\n".join(
            [
                "module: a1-001",
                "version: 1.5.2",
                "subtitle: Перевірка M01-M05",
                "grammar:",
                "  - Повторення з M48",
                "references:",
                '  - title: "Synthesis of M22-M26 content"',
                "    notes: Практика з M22-M26.",
                "external_resources:",
                '  - title: "ULP Season 1, Episode 6"',
                "    url: https://www.ukrainianlessons.com/episode6/",
                "",
            ]
        ),
        encoding="utf-8",
    )

    changes, old_version, new_version = fix_plan_file(plan_path, write=True)

    assert changes == 3
    assert (old_version, new_version) == ("1.5.2", "1.5.3")

    yaml = YAML(typ="safe")
    updated = yaml.load(plan_path.read_text("utf-8"))
    assert updated["module"] == "a1-001"
    assert updated["subtitle"] == "Перевірка №1–5"
    assert updated["grammar"] == ["Повторення з модуля 48"]
    assert updated["references"][0]["title"] == "Synthesis of M22-M26 content"
    assert updated["references"][0]["notes"] == "Практика з модулів 22–26."
    assert updated["external_resources"][0]["title"] == "ULP Season 1, Episode 6"


def test_fix_plan_file_is_idempotent(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "\n".join(
            [
                "module: a1-055",
                "version: '1.3.1'",
                "content_outline:",
                "  - section: Ранок",
                "    points:",
                "      - '(Числа — M10, покупки — M37)'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    first_changes, first_old, first_new = fix_plan_file(plan_path, write=True)
    second_changes, second_old, second_new = fix_plan_file(plan_path, write=True)

    assert (first_changes, first_old, first_new) == (1, "1.3.1", "1.3.2")
    assert (second_changes, second_old, second_new) == (0, None, None)

    final_text = plan_path.read_text("utf-8")
    assert "модуль №10" in final_text
    assert "модуль №37" in final_text
    assert "version: '1.3.2'" in final_text
