from __future__ import annotations

from scripts.build import linear_pipeline


def test_formatting_standards_accepts_valid_callouts() -> None:
    report = linear_pipeline._formatting_standards_gate(
        "## Практика\n\n> [!model-answer]\n> Я прокидаюся о сьомій.\n"
    )

    assert report["passed"] is True
    assert report["malformed_callouts"] == []
    assert report["missing_mandatory_callouts"] == []


def test_formatting_standards_rejects_bare_callout_marker() -> None:
    report = linear_pipeline._formatting_standards_gate(
        "## Практика\n\n[!model-answer]\nЯ прокидаюся о сьомій.\n"
    )

    assert report["passed"] is False
    assert report["malformed_callouts"][0]["line"] == 3
    assert report["missing_mandatory_callouts"] == ["> [!model-answer]"]
