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


def test_scaffolding_leak_gate_allows_english_step_instructions() -> None:
    # English "Step N:" can be legitimate published pedagogical prose; only the
    # Ukrainian Крок/Урок labels and the [SN] source-marker signature indicate a
    # real wiki-scaffolding leak. (Deepseek review #2412 finding 2a.)
    text = (
        "## How to form the present tense\n\n"
        "Step 1: find the verb stem. Step 2: add the personal ending.\n"
    )

    result = _scaffolding_leak_gate(text)

    assert result == {"passed": True, "offending": []}


def test_scaffolding_leak_gate_fails_on_internal_artifact_named_in_prose() -> None:
    # The real build-#6 a1/my-morning leak: an internal pipeline artifact ("the
    # Knowledge Packet") named in learner-facing body prose. python_qg passed this
    # build; only the LLM tone reviewer caught it (tone 7.6 REVISE, 2026-05-29).
    # The gate now catches it deterministically. (#R-NO-SCAFFOLDING-LEAKS)
    text = (
        "## Pronunciation\n\n"
        "Written **-ться** is spoken as **[ц':а]**. "
        "These rules come from the Knowledge Packet’s phonetic obligations "
        "for this module.\n"
    )

    result = _scaffolding_leak_gate(text)

    assert result["passed"] is False
    assert len(result["offending"]) == 1
    assert "Knowledge Packet" in result["offending"][0]["text"]


def test_scaffolding_leak_gate_flags_implementation_map_and_wiki_manifest() -> None:
    text = (
        "## Notes\n\n"
        "Follow the implementation map for ordering.\n"
        "The wiki manifest lists every section.\n"
    )

    result = _scaffolding_leak_gate(text)

    assert result["passed"] is False
    assert [o["line"] for o in result["offending"]] == [3, 4]


def test_scaffolding_leak_gate_flags_snake_case_artifact_identifiers() -> None:
    # The artifacts carry snake_case identifier forms in the codebase
    # (knowledge_packet.md, implementation_map.json); a writer naming the
    # identifier leaks just as the spaced display form does. The [\s_-]+
    # separator catches underscore and hyphen variants too.
    # (gemini-code-assist review, PR #2417.)
    text = (
        "## Notes\n\n"
        "See knowledge_packet for the rules.\n"
        "Ordering follows the implementation-map.\n"
    )

    result = _scaffolding_leak_gate(text)

    assert result["passed"] is False
    assert [o["line"] for o in result["offending"]] == [3, 4]


def test_scaffolding_leak_gate_allows_knowledge_packet_inside_verify_comment() -> None:
    # Honest in-comment provenance citations must NOT trip the gate — VERIFY
    # comments are unrendered and are the sanctioned home for packet provenance.
    text = (
        "## Pronunciation\n\n"
        "Written **-ться** is spoken as **[ц':а]**. "
        '<!-- VERIFY: source="Knowledge Packet: Мій ранок, phon-1 phon-2" -->\n'
    )

    result = _scaffolding_leak_gate(text)

    assert result == {"passed": True, "offending": []}


def test_scaffolding_leak_gate_is_ordered_but_not_auto_corrected() -> None:
    assert PYTHON_QG_GATE_ORDER.index("formatting_standards") < PYTHON_QG_GATE_ORDER.index(
        "scaffolding_leak"
    )
    assert "scaffolding_leak" not in WRITER_CORRECTION_GATES
