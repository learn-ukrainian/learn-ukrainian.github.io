"""Golden tests for fill-in activity MDX rendering without and with mode."""

from pathlib import Path

import yaml

from scripts.generate_mdx.dsl_to_mdx import _convert_v6_fill_in
from scripts.yaml_activities import ActivityParser, FillInActivity, FillInItem

GOLDEN_FILL_IN_MDX = (
    "### Заповніть пропуски\n\n"
    "<FillIn client:only='react' items={JSON.parse(`["
    '{"sentence": "Я вже ___ цю книгу.", "answer": "прочитав", "options": ["прочитав", "читав", "читаю", "прочитаю"]}, '
    '{"sentence": "Вона ___ лист учора.", "answer": "написала", "options": ["написала", "писала", "пише", "напише"]}, '
    '{"sentence": "Ми ___ обід о другій.", "answer": "з\'їли", "options": ["з\'їли", "їли", "їмо", "з\'їмо"]}, '
    '{"sentence": "Він ___ каву вранці.", "answer": "випив", "options": ["випив", "пив", "п\'є", "вип\'є"]}, '
    '{"sentence": "Вони ___ фільм учора.", "answer": "подивились", "options": ["подивились", "дивились", "дивляться", "подивляться"]}, '
    '{"sentence": "Я ___ домашнє завдання.", "answer": "зробив", "options": ["зробив", "робив", "роблю", "зроблю"]}, '
    '{"sentence": "Вона ___ нові слова.", "answer": "вивчила", "options": ["вивчила", "вчила", "вчить", "вивчить"]}, '
    '{"sentence": "Ми ___ друзів у парку.", "answer": "побачили", "options": ["побачили", "бачили", "бачимо", "побачимо"]}'
    "]`)} isUkrainian={false} />"
)


def test_existing_fill_in_without_mode_matches_golden_string():
    """Existing modules without mode must produce byte-identical MDX."""
    fixture_path = Path("tests/fixtures/sample.activities.yaml")
    with open(fixture_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    fill_act_data = next(a for a in data if a.get("type") == "fill-in")
    parser = ActivityParser()
    act = parser._parse_activity(fill_act_data)

    rendered = parser._fill_in_to_mdx(act)
    assert rendered == GOLDEN_FILL_IN_MDX, "Rendered MDX must match golden string byte for byte"


def test_fill_in_modes_in_items():
    """Items with mode emit mode prop in JSON payload; items without mode omit it."""
    act = FillInActivity(
        title="Fill In Test",
        instruction="Choose forms",
        items=[
            FillInItem(
                sentence="Це ____.",
                answer="слово",
                options=["слово", "слова"],
                explanation="Виберіть форму.",
                mode="form-choice",
            ),
            FillInItem(
                sentence="М____ясо.",
                answer="'",
                options=["'", ""],
                explanation="Правопис апострофа.",
                mode="orthography",
            ),
            FillInItem(
                sentence="Звичайне ____.",
                answer="речення",
                options=["речення"],
                explanation=None,
                mode=None,
            ),
        ],
    )
    parser = ActivityParser()
    mdx = parser._fill_in_to_mdx(act)
    assert '"mode": "form-choice"' in mdx
    assert '"mode": "orthography"' in mdx
    # The third item must NOT contain "mode"
    assert mdx.count('"mode"') == 2


def test_dsl_to_mdx_fill_in_mode():
    """DSL fill-in converter preserves mode when present and omits when absent."""
    dsl_without_mode = """title: Practice
---
- sentence: "Hello ___"
  answer: "world"
"""
    res_no_mode = _convert_v6_fill_in(dsl_without_mode)
    assert res_no_mode == '<FillIn client:only="react" instruction={"Practice"} items={[{"sentence": "Hello ___", "answer": "world"}]} />'

    dsl_with_mode = """title: Practice
---
- sentence: "Hello ___"
  answer: "world"
  mode: form-choice
"""
    res_mode = _convert_v6_fill_in(dsl_with_mode)
    assert res_mode == '<FillIn client:only="react" instruction={"Practice"} items={[{"sentence": "Hello ___", "answer": "world", "mode": "form-choice"}]} />'
