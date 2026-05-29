from __future__ import annotations

from scripts.build.linear_pipeline import (
    PYTHON_QG_GATE_ORDER,
    WRITER_CORRECTION_GATES,
    _scaffolding_leak_gate,
)


def test_scaffolding_leak_gate_fails_on_step_labels_and_source_markers() -> None:
    text = (
        "## Дієслова на -ся\n\n"
        "A reflexive verb adds -ся. Крок 2: use прокидатися [S3, S6].\n"
    )

    result = _scaffolding_leak_gate(text)

    assert result["passed"] is False
    assert result["offending"] == [
        {
            "line": 3,
            "text": "A reflexive verb adds -ся. Крок 2: use прокидатися [S3, S6].",
        }
    ]


def test_scaffolding_leak_gate_ignores_comments_and_fenced_code() -> None:
    text = """## Notes

<!-- VERIFY: source="wiki step-1 [S3]" Крок 2: -->

```md
Крок 2: use прокидатися [S3, S6]
```

Чистий текст без службових міток.
"""

    result = _scaffolding_leak_gate(text)

    assert result == {"passed": True, "offending": []}


def test_scaffolding_leak_gate_does_not_blind_after_single_line_backticks() -> None:
    text = """## Notes

```print("hello")```

Крок 3: leaked prose [S4]
"""

    result = _scaffolding_leak_gate(text)

    assert result["passed"] is False
    assert result["offending"] == [{"line": 5, "text": "Крок 3: leaked prose [S4]"}]


def test_scaffolding_leak_gate_passes_on_clean_a1_prose() -> None:
    text = (
        "## Мій ранок\n\n"
        "Я прокидаюся о сьомій. Потім умиваюся і одягаюся.\n"
        "Ти прокидаєшся рано? Я дивлюся в дзеркало.\n"
    )

    result = _scaffolding_leak_gate(text)

    assert result == {"passed": True, "offending": []}


def test_scaffolding_leak_gate_is_ordered_but_not_auto_corrected() -> None:
    assert PYTHON_QG_GATE_ORDER.index("formatting_standards") < PYTHON_QG_GATE_ORDER.index(
        "scaffolding_leak"
    )
    assert "scaffolding_leak" not in WRITER_CORRECTION_GATES
