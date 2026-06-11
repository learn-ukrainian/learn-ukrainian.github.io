from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRITER_PROMPT = PROJECT_ROOT / "scripts/build/phases/linear-write.md"
B1_M01_PLAN = PROJECT_ROOT / "curriculum/l2-uk-en/plans/b1/b1-baseline-past-present.yaml"

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
            "A1/A2 audience language — ULP immersion",
            "Ukrainian-first, em-dash gloss",
            "`прокидаюся — I wake up`",
            "`<DialogueBox uk=\"...\" en=\"...\" />`",
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


def _render_b1_m01_generated_prompt() -> str:
    plan_content = B1_M01_PLAN.read_text(encoding="utf-8")
    plan = yaml.safe_load(plan_content)
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_content,
        knowledge_packet="## Knowledge Packet\n\nTest packet for prompt contract rendering.",
        writer="claude-tools",
        use_generator=True,
    )


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


def test_writer_prompt_contains_seminar_folk_qg_hardening() -> None:
    prompt = _prompt()
    normalized = _normalize(prompt)

    required = (
        "For seminar tracks, especially `LEVEL=folk`, treat the wiki `[S#]` registry",
        "`citations_resolve` hard-rejects unresolved citations",
        "When `{WORD_TARGET}=5000`, the 92% tolerance still requires about 4600 accepted words",
        "call `mcp__sources__check_russian_shadow` and `mcp__sources__search_style_guide`",
        "Use `аранжування`, not `<!-- bad -->аранжировку<!-- /bad -->`",
        "Put those fragments in blockquotes or the module's verbatim-quote convention",
        "bare unattested archaic/dialectal folk forms in exposition fail",
        "authentic regional and archaic variants are ENCOURAGED",
    )

    for anchor in required:
        assert _normalize(anchor) in normalized


def test_writer_prompt_carries_b1_full_ukrainian_ulp_method() -> None:
    prompt = _prompt()
    normalized = _normalize(prompt)

    required = (
        "B1+ body text outside Tab 2 is Ukrainian only",
        "Anna Ohoiko / Ukrainian Lessons Podcast pedagogy as method",
        "teach Ukrainian through Ukrainian",
        "micro-situations, recall questions, dialogues",
        "Prefer Ukrainian paraphrase/definition over English glosses outside Tab 2",
        "do not quote English phrases, English sentence patterns",
        "Show the Ukrainian mistake pattern with `<!-- bad -->...<!-- /bad -->` only when",
    )

    for anchor in required:
        assert _normalize(anchor) in normalized

    forbidden = (
        "Write the A1 module",
        "one-sentence English scaffold",
        "If a row cannot fit A1 scope",
        "immersion ratio from the Immersion Rule",
    )
    for phrase in forbidden:
        assert phrase not in prompt


def test_generated_b1_writer_prompt_is_ukrainian_immersive() -> None:
    prompt = _render_b1_m01_generated_prompt()
    normalized = _normalize(prompt)

    required = (
        "B1+ body text outside Tab 2 is Ukrainian only",
        "Anna Ohoiko / Ukrainian Lessons Podcast pedagogy as method",
        "teach Ukrainian through Ukrainian",
        "Prefer Ukrainian paraphrase/definition over English glosses outside Tab 2",
        "At B1+, use Ukrainian paraphrase, definition, contrast, or micro-situation",
        "do not quote English phrases, English sentence patterns",
        "`<register>` (level audience-language contract + how preserved)",
    )
    for anchor in required:
        assert _normalize(anchor) in normalized

    forbidden = (
        "English scaffold glosses",
        "inline English gloss",
        "within 8 tokens",
        "**lemma** *(gloss)*",
        "immersion ratio + how preserved",
    )
    for phrase in forbidden:
        assert phrase not in prompt


def test_generated_writer_prompt_carries_group_sort_shape_contract() -> None:
    prompt = _render_b1_m01_generated_prompt()
    normalized = _normalize(prompt)

    required = (
        "group-sort",
        "groups is a list of objects with label/name + items",
        "Use `groups` as a list of objects",
        "Do NOT emit a mapping object",
        "top-level `items`, `key`, or `{word, group}` pairs",
    )
    for anchor in required:
        assert _normalize(anchor) in normalized
