from pathlib import Path

import pytest

from scripts.audit.check_module_continuity import (
    Finding,
    Module,
    find_unsignposted_repetition,
    load_modules,
    main,
    module_order,
)


def test_repeated_concept_without_bridge_is_reported() -> None:
    modules = [
        Module(1, "m1", Path("m1"), "one vowel sound = one склад"),
        Module(2, "m2", Path("m2"), "A склад is a syllable. Count the vowels."),
    ]

    findings = find_unsignposted_repetition(modules, {"склад": ("склад",)})

    assert findings == [
        Finding(
            module_num=2,
            slug="m2",
            term="склад",
            first_seen_num=1,
            first_seen_slug="m1",
            line=1,
            snippet="A склад is a syllable. Count the vowels.",
        )
    ]


def test_repeated_concept_with_bridge_is_not_reported() -> None:
    modules = [
        Module(1, "m1", Path("m1"), "one vowel sound = one склад"),
        Module(
            2,
            "m2",
            Path("m2"),
            "You already practiced counting склади in Module 1. "
            "Now use that skill to read longer words.",
        ),
    ]

    assert find_unsignposted_repetition(modules, {"склад": ("склад", "склади")}) == []


def test_boundary_safe_matching_avoids_substring_false_positive() -> None:
    modules = [
        Module(1, "m1", Path("m1"), "A голосний is a vowel sound."),
        Module(2, "m2", Path("m2"), "A приголосний is a consonant sound."),
    ]

    assert find_unsignposted_repetition(modules, {"голосний": ("голосний",)}) == []


def test_any_bridged_occurrence_suppresses_finding() -> None:
    modules = [
        Module(1, "m1", Path("m1"), "one vowel sound = one склад"),
        Module(
            2,
            "m2",
            Path("m2"),
            "A склад is a syllable. You already practiced counting склади in Module 1.",
        ),
    ]

    assert find_unsignposted_repetition(modules, {"склад": ("склад", "склади")}) == []


def test_module_order_sorts_by_num_and_supports_single_quotes(tmp_path: Path) -> None:
    data_path = tmp_path / "site" / "src" / "data"
    data_path.mkdir(parents=True)
    (data_path / "demo-modules.ts").write_text(
        """
export const DEMO = [
  { num: 10, slug: "ten" },
  { num: 2, slug: 'two' },
];
""".strip(),
        encoding="utf-8",
    )

    curriculum_root = tmp_path / "curriculum" / "l2-uk-en" / "demo"
    for slug in ("two", "ten"):
        module_path = curriculum_root / slug
        module_path.mkdir(parents=True)
        (module_path / "module.md").write_text(f"{slug} content", encoding="utf-8")

    assert module_order("demo", tmp_path) == [(2, "two"), (10, "ten")]
    modules = load_modules("demo", root=tmp_path)
    assert [(module.num, module.slug) for module in modules] == [(2, "two"), (10, "ten")]


def test_main_errors_when_no_modules_loaded(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        "scripts.audit.check_module_continuity.load_modules",
        lambda level, first=None: [],
    )

    assert main(["--level", "a1"]) == 1
    assert "Error: no modules found for level 'a1'." in capsys.readouterr().out
