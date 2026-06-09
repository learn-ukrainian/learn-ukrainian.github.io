from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from scripts.build.activity_renderer import render_activity_to_jsx
from scripts.build.linear_pipeline import assemble_mdx
from scripts.generate_mdx import (
    FormulaItem,
    MotifFormulaData,
    PerformanceData,
    RitualSequencingData,
    VariantComparisonData,
    VariantComparisonVariant,
    motif_formula_to_jsx,
    performance_to_jsx,
    ritual_sequencing_to_jsx,
    variant_comparison_to_jsx,
)
from scripts.generate_mdx.core import backfill_missing_activity_ids
from scripts.yaml_activities import ActivityParser

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _folk_activity_yaml() -> str:
    return """
- id: act-ritual
  type: ritual-sequencing
  title: Віднови послідовність обряду
  instruction: Розташуйте етапи Щедрого вечора.
  steps:
    - Гурт збирається, обирає Маланку й Василя
    - Обхід дворів, спів щедрівок під вікнами
    - Величання господаря, побажання достатку
    - Господар обдаровує щедрувальників
  correct_order: [0, 1, 2, 3]
- type: variant-comparison
  title: Порівняй регіональні варіанти
  instruction: Заповніть таблицю ознак.
  variants:
    - label: Наддніпрянський
      region: Наддніпрянщина
      text: Добрий вечір тобі, пане господарю.
    - label: Карпатський
      region: Карпати
      text: Ой радуйся, земле.
  features:
    - Образ-рефрен
    - Персонажі дійства
  prompt: Порівняйте сталі образи.
- id: act-motif
  type: motif-formula
  title: Знайди обрядову формулу
  instruction: Клацніть сталу формулу.
  passage: "Добрий вечір тобі, пане господарю! Застеляйте столи."
  formulas:
    - text: Добрий вечір тобі, пане господарю
      label: величальна формула
      explanation: Формула звертається до господаря й відкриває обрядову дію.
- type: performance
  title: Заспівай / продекламуй
  prompt: Виконайте фрагмент уголос і звірте дикцію.
  fragment: Добрий вечір тобі, пане господарю!
  self_check:
    - Чітко вимовлено звертання.
    - Збережено урочистий темп.
  show_record_button: true
"""


def test_folk_activity_parser_round_trip_and_converter_snapshots(tmp_path):
    activities_path = tmp_path / "activities.yaml"
    activities_path.write_text(_folk_activity_yaml(), encoding="utf-8")

    parser = ActivityParser()
    activities = parser.parse(activities_path)

    assert [activity.type for activity in activities] == [
        "ritual-sequencing",
        "variant-comparison",
        "motif-formula",
        "performance",
    ]
    assert activities[0].correct_order == [0, 1, 2, 3]
    assert activities[1].variants[0].label == "Наддніпрянський"
    assert activities[2].formulas[0].text == "Добрий вечір тобі, пане господарю"
    assert activities[3].self_check == ["Чітко вимовлено звертання.", "Збережено урочистий темп."]

    mdx = parser.to_mdx(activities, is_ukrainian_forced=True)
    assert "<RitualSequencing client:only='react'" in mdx
    assert "correctOrder={JSON.parse" in mdx
    assert "<VariantComparison client:only='react'" in mdx
    assert "variants={JSON.parse" in mdx
    assert "<MotifFormula client:only='react'" in mdx
    assert "formulas={JSON.parse" in mdx
    assert "<PerformanceActivity client:only='react'" in mdx
    assert "showRecordButton={true}" in mdx

    snapshots = [
        ritual_sequencing_to_jsx(
            RitualSequencingData(steps=["збір", "обхід"], correctOrder=[0, 1], instruction="Упорядкуйте."),
            "Ritual",
            True,
        ),
        variant_comparison_to_jsx(
            VariantComparisonData(
                variants=[VariantComparisonVariant("A"), VariantComparisonVariant("B")],
                features=["рефрен"],
                prompt="Порівняйте.",
            ),
            "Variant",
            True,
        ),
        motif_formula_to_jsx(
            MotifFormulaData(
                passage="Добрий вечір тобі!",
                formulas=[FormulaItem("Добрий вечір", "вітання")],
            ),
            "Motif",
            True,
        ),
        performance_to_jsx(
            PerformanceData(prompt="Продекламуйте.", fragment="Добрий вечір.", selfCheck=["дикція"]),
            "Performance",
            True,
        ),
    ]
    assert [snapshot.splitlines()[2] for snapshot in snapshots] == [
        "<RitualSequencing client:only='react'",
        "<VariantComparison client:only='react'",
        "<MotifFormula client:only='react'",
        "<PerformanceActivity client:only='react'",
    ]


def test_folk_activity_schema_accepts_new_types():
    schema = json.loads((PROJECT_ROOT / "schemas/activity-v2.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    doc = {
        "version": "1.0",
        "module": "folk-demo",
        "level": "folk",
        "workbook": [
            {
                "type": "ritual-sequencing",
                "steps": ["збір", "обхід"],
                "correct_order": [0, 1],
            },
            {
                "type": "variant-comparison",
                "variants": [{"label": "A"}, {"label": "B"}],
                "features": ["рефрен"],
            },
            {
                "type": "motif-formula",
                "passage": "Добрий вечір тобі!",
                "formulas": [{"text": "Добрий вечір"}],
            },
            {
                "type": "performance",
                "prompt": "Продекламуйте фрагмент.",
                "self_check": ["дикція"],
            },
        ],
    }

    assert validator.is_valid(doc)


def test_ritual_sequencing_normalizes_one_based_order_and_rejects_bounds(tmp_path):
    activities_path = tmp_path / "activities.yaml"
    activities_path.write_text(
        """
- type: ritual-sequencing
  title: Обряд
  steps: [збір, обхід]
  correct_order: [1, 2]
""",
        encoding="utf-8",
    )

    parsed = ActivityParser().parse(activities_path)
    assert parsed[0].correct_order == [0, 1]

    jsx = render_activity_to_jsx({
        "type": "ritual-sequencing",
        "title": "Обряд",
        "steps": ["збір", "обхід"],
        "correct_order": [1, 2],
    })
    assert "correctOrder={[0, 1]}" in jsx

    try:
        render_activity_to_jsx({
            "type": "ritual-sequencing",
            "title": "Обряд",
            "steps": ["збір", "обхід"],
            "correct_order": [0, 2],
        })
    except ValueError as exc:
        assert "index out of bounds" in str(exc)
    else:
        raise AssertionError("out-of-bounds ritual order should fail before JSX rendering")


def test_folk_fixture_assembles_text_layer_without_deferred_surfaces(tmp_path):
    module_dir = tmp_path / "folk-module"
    module_dir.mkdir()
    plan_path = tmp_path / "plan.yaml"
    out_path = tmp_path / "out.mdx"

    plan_path.write_text(
        """
module: 1
level: folk
sequence: 1
slug: koliadky-shchedrivky
title: Колядки і щедрівки
subtitle: Test
word_target: 100
content_outline:
  - section: Обряд
    words: 50
    points: [Test]
references:
  - title: Folk dossier
""",
        encoding="utf-8",
    )
    (module_dir / "module.md").write_text(
        """# Колядки і щедрівки

## Обряд

:::myth-box
claim: "«Carol of the Bells» — не українська традиція."
truth: "Насправді світовий мотив іде від українського «Щедрика» в обробці Леонтовича."
claim_source: "популярний міф"
truth_source: "Folk dossier"
:::

:::high-culture-bridge
nodes:
  - "народна щедрівка"
  - "Леонтович «Щедрик»"
  - "Carol of the Bells"
note: "Фольклорна формула переходить у концертну й масову культуру."
:::

<!-- INJECT_ACTIVITY: act-ritual -->

<!-- INJECT_ACTIVITY: act-motif -->
""",
        encoding="utf-8",
    )
    (module_dir / "activities.yaml").write_text(_folk_activity_yaml(), encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text(
        """
- lemma: щедрівка
  translation: shchedrivka
  pos: noun
  usage: Співати щедрівки.
""",
        encoding="utf-8",
    )
    (module_dir / "resources.yaml").write_text(
        """
- title: Folk dossier
  role: wiki
  description: Grounding source.
  url: https://example.com/folk
""",
        encoding="utf-8",
    )

    normalized = backfill_missing_activity_ids(ActivityParser().parse(module_dir / "activities.yaml"))
    assert [activity.id for activity in normalized] == ["act-ritual", "act-2", "act-motif", "act-4"]

    mdx = assemble_mdx(module_dir, out_path, plan_path)

    assert "<MythBuster" in mdx
    assert "<HighCultureBridge" in mdx
    assert "<RitualSequencing" in mdx
    assert "<VariantComparison" in mdx
    assert "<MotifFormula" in mdx
    assert "<PerformanceActivity" in mdx
    assert "audio-block" not in mdx
    assert "symbolic-decode" not in mdx
    assert "aural-genre-id" not in mdx
    assert out_path.exists()


def test_writer_and_archetype_require_folk_text_layer():
    prompt = (PROJECT_ROOT / "scripts/build/phases/linear-write.md").read_text(encoding="utf-8")
    archetype = (PROJECT_ROOT / "scripts/pipeline/module_archetypes.py").read_text(encoding="utf-8")

    for required in (
        ":::myth-box",
        ":::high-culture-bridge",
    ):
        assert required in prompt

    for required in (
        "myth-box",
        "ritual-sequencing",
        "variant-comparison",
        "motif-formula",
        "performance",
    ):
        assert required in prompt
        assert required in archetype

    assert "high-culture-bridge" in prompt
    assert "high-culture bridge" in archetype

    assert "Do NOT emit `audio-block`, `symbolic-decode`, or `aural-genre-id`" in prompt
    assert "audio-block, symbolic-decode, and aural genre-ID absent" in archetype
