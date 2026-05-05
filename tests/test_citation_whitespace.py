from __future__ import annotations

from typing import Any

from scripts.build import linear_pipeline


def _result(source_ref: str, title: str = "Караман Grade 10, p.176") -> dict[str, Any]:
    return linear_pipeline._citation_gate(
        [{"source_ref": source_ref}],
        {"references": [{"title": title}]},
    )


def test_citation_gate_normalizes_page_reference_whitespace() -> None:
    assert _result("Караман Grade 10, p. 176")["passed"] is True
    assert _result("Караман Grade 10, p.176")["passed"] is True
    assert _result("Караман Grade 10, p.  176")["passed"] is True


def test_citation_gate_normalizes_plan_page_reference_whitespace() -> None:
    assert _result("Караман Grade 10, p.176", "Караман Grade 10, p. 176")[
        "passed"
    ] is True
