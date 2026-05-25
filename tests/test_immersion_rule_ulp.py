from __future__ import annotations

from scripts import config

ULP_KEYWORDS = (
    "em-dash",
    "side-by-side",
    "stress marks",
    "UK-first",
    "named persona",
)


def _keyword_hits(rule: str) -> int:
    lowered = rule.lower()
    return sum(1 for keyword in ULP_KEYWORDS if keyword.lower() in lowered)


def test_a1_letter_module_gets_ulp_practices() -> None:
    rule = config.get_immersion_rule("a1", 4)

    assert "ULP Presentation Pattern" in rule
    assert _keyword_hits(rule) >= 2


def test_a1_m20_gets_ulp_practices() -> None:
    rule = config.get_immersion_rule("a1", 20)

    assert "ULP Presentation Pattern" in rule
    assert _keyword_hits(rule) >= 2


def test_a1_late_module_does_not_get_s1_ulp_practices() -> None:
    rule = config.get_immersion_rule("a1", 50)

    assert "ULP Presentation Pattern" not in rule
    assert _keyword_hits(rule) == 0


def test_c1_module_does_not_get_a1_ulp_practices() -> None:
    rule = config.get_immersion_rule("c1", 50)

    assert "ULP Presentation Pattern" not in rule
    assert _keyword_hits(rule) == 0
