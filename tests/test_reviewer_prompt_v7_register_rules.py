from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEWER_PROMPT = PROJECT_ROOT / "scripts/build/phases/linear-review-dim.md"

REVIEWER_RULE_ANCHORS = (
    (
        "#R-SINGLE-VOICE-A1",
        (
            "REJECT mid-module register shifts",
            "third-person framing of the learner",
            "`the student`, `студента`, `the reader`, `учня`",
        ),
    ),
    (
        "#R-AUDIENCE-LANGUAGE-A1",
        (
            "REJECT Ukrainian metalanguage TO the A1 learner",
            "A1 explanation prose stays in English",
            "`Контролюй чистоту словника`, `Рішуче відкидай`, `Запам'ятай...`",
        ),
    ),
    (
        "#R-NO-CHILDREN-PRIMARY-QUOTES",
        (
            "REJECT `>` blockquotes from textbooks at Grade 1, 2, or 3 levels "
            "in the published module body",
            "Grade 1-3 RAG hits can still ground lexical choices",
            "`Захарійчук, Grade 1, p.24`",
        ),
    ),
    (
        "#R-NO-SCAFFOLDING-LEAKS",
        (
            "REJECT writer-side scaffolding leaks",
            "Writer-side scaffolding never appears in module body",
            "obligation names from the wiki_coverage manifest (`ban-4`, `step-5`, ...)",
        ),
    ),
    (
        "#R-GRAMMAR-TERMS-A1",
        (
            "Use proper grammatical terminology in English explanations",
            "REJECT folksy paraphrase",
            "`a thing`, `an action`, `a word for`, `a doing-word`, `the X-form of Y`",
        ),
    ),
    (
        "#R-CLEAN-TABLES",
        (
            "REJECT bold-everywhere tables",
            "Tables: bold ONLY the target Ukrainian forms",
            "я / ти / він,вона,воно / ми / ви / вони",
        ),
    ),
)


def _prompt() -> str:
    return REVIEWER_PROMPT.read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.parametrize(("rule_id", "anchors"), REVIEWER_RULE_ANCHORS)
def test_reviewer_prompt_mirrors_v7_register_rule(
    rule_id: str,
    anchors: tuple[str, ...],
) -> None:
    prompt = _prompt()
    normalized = _normalize(prompt)

    assert f"Mirrors `{rule_id}`" in prompt
    for anchor in anchors:
        assert _normalize(anchor) in normalized
