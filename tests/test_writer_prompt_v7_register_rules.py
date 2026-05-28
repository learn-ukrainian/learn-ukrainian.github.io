from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRITER_PROMPT = PROJECT_ROOT / "scripts/build/phases/linear-write.md"

WRITER_RULE_ANCHORS = (
    (
        "#R-SINGLE-VOICE-A1",
        (
            "One teacher voice across the whole module",
            "third-person framing of the learner",
            "`the student`, `студента`, `the reader`, `учня`",
        ),
    ),
    (
        "#R-AUDIENCE-LANGUAGE-A1",
        (
            "A1 explanation prose stays in English",
            "Ukrainian appears only as TARGET",
            "`Контролюй чистоту словника`, `Рішуче відкидай`, `Запам'ятай...`",
        ),
    ),
    (
        "#R-NO-CHILDREN-PRIMARY-QUOTES",
        (
            "No `>` blockquotes from textbooks at Grade 1, 2, or 3 levels "
            "in the published module body",
            "Grade 1-3 RAG hits can still ground lexical choices",
            "`<Author>, Grade 1, p.<P>`",
        ),
    ),
    (
        "#R-NO-SCAFFOLDING-LEAKS",
        (
            "Writer-side scaffolding never appears in module body",
            "Krok-N labels (`Крок 5:`, `Step 5:`)",
            "obligation names from the wiki_coverage manifest (`ban-4`, `step-5`, ...)",
        ),
    ),
    (
        "#R-GRAMMAR-TERMS-A1",
        (
            "Use proper grammatical terminology in English explanations",
            "`a thing`, `an action`, `a word for`, `a doing-word`, `the X-form of Y`",
            "Adult learners benefit from real grammar terms",
        ),
    ),
    (
        "#R-PROSE-FLOOR-A1",
        (
            "Prose words only — section budget",
            "count PROSE only",
            "Structural elements are *bonus density*",
            "Reach the prose floor BEFORE you optimize",
        ),
    ),
    (
        "#R-CLEAN-TABLES",
        (
            "Tables: bold ONLY the target Ukrainian forms",
            "Pronoun columns (`я`, `ти`, ...), English headers, and English glosses",
            "я / ти / він,вона,воно / ми / ви / вони",
        ),
    ),
)


def _prompt() -> str:
    return WRITER_PROMPT.read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.parametrize(("rule_id", "anchors"), WRITER_RULE_ANCHORS)
def test_writer_prompt_contains_v7_register_rule(
    rule_id: str,
    anchors: tuple[str, ...],
) -> None:
    prompt = _prompt()
    normalized = _normalize(prompt)

    assert f"rule_id: {rule_id}" in prompt
    for anchor in anchors:
        assert _normalize(anchor) in normalized
