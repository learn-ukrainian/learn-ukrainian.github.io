from __future__ import annotations

import re

from scripts.build.linear_pipeline import assemble_mdx

_ACTIVITY_COMPONENT_RE = re.compile(
    r"<(?:Quiz|FillIn|MatchUp|TrueFalse|GroupSort|Unjumble|Observe|Order)\b"
)


def _tab_item(mdx: str, label: str) -> str:
    start = mdx.index(f'<TabItem label="{label}">')
    end = mdx.index("</TabItem>", start)
    return mdx[start:end]


def test_assemble_mdx_v7_sources_render_four_tabs(tmp_path):
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    plan_path = tmp_path / "plan.yaml"
    out_path = tmp_path / "out.mdx"

    plan_path.write_text(
        """
module: 1
level: a1
sequence: 1
slug: my-morning
title: Мій ранок
subtitle: Test
word_target: 100
content_outline:
  - section: Діалоги
    words: 50
    points: [Test]
references:
  - title: Караман Grade 10, p.176
""",
        encoding="utf-8",
    )
    (module_dir / "module.md").write_text(
        """# Мій ранок

**Діалог 1 — Будній ранок**

> **Ліна:** Коли ти прокидаєшся?
> **Настя:** Я прокидаюся о сьомій.

<!-- INJECT_ACTIVITY: act-1 -->

<!-- INJECT_ACTIVITY: act-3 -->
""",
        encoding="utf-8",
    )
    (module_dir / "activities.yaml").write_text(
        """
- id: act-1
  type: observe
  title: Inline observe
  instruction: Notice the pattern.
  prompt: What changes?
  examples:
    - text: мию → миюся
    - text: одягаю → одягаюся
- id: act-2
  type: order
  title: Workbook order
  instruction: Put the actions in order.
  items: [прокидатися, вмиватися, снідати]
  correct_order: [0, 1, 2]
- id: act-3
  type: true-false
  title: Inline true false
  items:
    - statement: Настя прокидається о сьомій.
      correct: true
- id: act-4
  type: match-up
  title: Workbook match
  pairs:
    - left: прокидатися
      right: to wake up
- id: act-5
  type: fill-in
  title: Workbook fill
  items:
    - sentence: Я ___ о сьомій.
      answer: прокидаюся
""",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text(
        """
- lemma: прокидатися
  translation: to wake up
  pos: verb
  usage: Я прокидаюся о сьомій.
""",
        encoding="utf-8",
    )
    (module_dir / "resources.yaml").write_text(
        """
- title: Караман Grade 10, p.176
  source_ref: Караман Grade 10, p.176
  author: Караман
  pages: "176"
  description: Reflexive verbs with -ся.
  role: textbook
""",
        encoding="utf-8",
    )

    mdx = assemble_mdx(module_dir, out_path, plan_path)

    assert "<DialogueBox" in mdx
    assert "<VocabCard" in mdx
    assert "<FlashcardDeck" in mdx
    assert mdx.index("<VocabCard") < mdx.index("<FlashcardDeck")

    lesson_tab = _tab_item(mdx, "Lesson")
    activities_tab = _tab_item(mdx, "Activities")
    assert len(_ACTIVITY_COMPONENT_RE.findall(lesson_tab)) == 2
    assert len(_ACTIVITY_COMPONENT_RE.findall(activities_tab)) == 5
    assert "<Observe" in lesson_tab
    assert "<TrueFalse" in lesson_tab
    assert "<Observe" in activities_tab
    assert "<TrueFalse" in activities_tab
    assert "<Order" in activities_tab
    assert "<MatchUp" in activities_tab
    assert "<FillIn" in activities_tab
    assert "Inline observe" in activities_tab
    assert "Inline true false" in activities_tab
    assert activities_tab.count("*(see lesson)*") == 2
    assert "INJECT_ACTIVITY" not in mdx
    assert "by Unknown" not in mdx
    assert "Караман" in mdx
