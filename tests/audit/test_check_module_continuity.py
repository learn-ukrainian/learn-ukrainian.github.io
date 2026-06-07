from pathlib import Path

from scripts.audit.check_module_continuity import (
    Finding,
    Module,
    find_unsignposted_repetition,
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
