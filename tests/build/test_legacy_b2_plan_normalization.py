from __future__ import annotations

from pathlib import Path

from scripts.build.linear_pipeline import load_plan, validate_plan


def test_load_plan_normalizes_legacy_b2_subsections_and_references(tmp_path: Path) -> None:
    plan_path = tmp_path / "legacy-b2.yaml"
    plan_path.write_text(
        """
module: b2-999
level: B2
sequence: 999
slug: legacy-b2
title: Legacy B2
subtitle: Legacy section shape
word_target: 4000
content_outline:
  - section: Legacy Section
    words: 800
    subsections: First teaching point - Second teaching point
    key_concepts:
      - регістр
      - доречність
references:
  - source: Test textbook
    pages: 10-12
    topic: Test topic
  - State Standard 2024: B2 source reference
""".strip(),
        encoding="utf-8",
    )

    plan = load_plan(plan_path)

    validate_plan(plan)
    section = plan["content_outline"][0]
    assert section["points"] == [
        "First teaching point",
        "Second teaching point",
        "Ключові поняття: регістр, доречність",
    ]
    assert plan["references"][0]["title"] == "Test textbook"
    assert plan["references"][1]["title"] == "State Standard 2024: B2 source reference"
