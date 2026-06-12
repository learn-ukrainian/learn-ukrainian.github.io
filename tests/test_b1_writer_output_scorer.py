from __future__ import annotations

import json
from pathlib import Path

from scripts.bakeoff.score_b1_writer_output import (
    _check_source_tool_evidence,
    score_writer_output,
)


def _manifest() -> dict:
    steps = [
        ("step-1", "Теперішній час: дієвідміни", "пишуть бачать основа"),
        ("step-2", "Теперішній час: дієвідміни", "дієвідміна теперіш е и"),
        (
            "step-3",
            "Минулий час: утворення і вживання",
            "основа інфінітива -в -л переміг",
        ),
        (
            "step-4",
            "Вид дієслова: доконаний і недоконаний",
            "недоконаний доконаний читав прочитав",
        ),
        (
            "step-5",
            "Вид у розповіді: послідовність і тло",
            "дієприслівник читаючи сказавши",
        ),
        (
            "step-6",
            "Підсумок: від знання до вживання",
            "дієприкметник -вш -ший -лий",
        ),
    ]
    return {
        "slug": "b1-baseline-past-present",
        "sequence_steps": [
            {
                "id": obligation_id,
                "heading": heading,
                "required_claim": required_claim,
            }
            for obligation_id, heading, required_claim in steps
        ],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
    }


def _resources() -> list[dict]:
    return [
        {
            "title": f"Підручник {index}",
            "role": "textbook",
            "packet_chunk_id": f"7-klas-ukrmova-fixture_s00{index}",
            "notes": "source-ref",
        }
        for index in range(1, 6)
    ]


def _activities() -> list[dict]:
    return [
        {
            "id": "act-1",
            "type": "quiz",
            "title": "Час",
            "items": [
                {
                    "question": "Яка форма теперішнього часу?",
                    "options": [
                        {"text": "пишу", "correct": True},
                        {"text": "написав", "correct": False},
                    ],
                    "explanation": "Форма пишу триває тепер.",
                }
            ],
        },
        {
            "id": "act-2",
            "type": "translate",
            "title": "Переклад",
            "items": [
                {
                    "source": "I write.",
                    "options": [{"text": "Я пишу.", "correct": True}],
                    "explanation": "Українська форма вже містить особу.",
                }
            ],
        },
        {
            "id": "act-3",
            "type": "fill-in",
            "title": "Форма",
            "items": [{"sentence": "Вона ___ лист.", "answer": "написала"}],
        },
        {
            "id": "act-4",
            "type": "match-up",
            "title": "Вид",
            "pairs": [{"left": "писати", "right": "написати"}],
        },
        {
            "id": "act-5",
            "type": "error-correction",
            "title": "Редагування",
            "items": [
                {
                    "sentence": "Вона сказав.",
                    "error": "сказав",
                    "correction": "сказала",
                }
            ],
        },
    ]


def _module(meta_phrase: str = "", marker: str = "act-5") -> str:
    filler = " ".join(["форма"] * 3700)
    return f"""# Минуле і теперішнє

{meta_phrase}

## Теперішній час: дієвідміни
<!-- VERIFY: source="fixture" chunk="7-klas-ukrmova-fixture_s001" -->
Ти бачиш, як працює форма: **пишу**, **пишеш**, **пише**, **пишуть**.
Порівняй **бачать** і **шукають**: основа теперішнього часу показує дієвідміна, е і и.
Тому українська фраза працює без зайвої зв'язки, бо форма сама показує особу.
<!-- INJECT_ACTIVITY: act-1 -->

## Минулий час: утворення і вживання
<!-- VERIFY: source="fixture" chunk="7-klas-ukrmova-fixture_s002" -->
Пам'ятай: основа інфінітива бере **-в** і **-л**, а **переміг** показує нульовий суфікс.
Тобі важливо бачити рід і число: **читав**, **читала**, **читали**.
<!-- INJECT_ACTIVITY: act-2 -->

## Вид дієслова: доконаний і недоконаний
<!-- VERIFY: source="fixture" chunk="7-klas-ukrmova-fixture_s003" -->
Недоконаний вид показує процес: **читав**, **писав**. Доконаний вид показує межу:
**прочитав**, **написав**. Саме тому зараз кажемо **пишу**, а завтра **напишу**.
<!-- INJECT_ACTIVITY: act-3 -->

## Вид у розповіді: послідовність і тло
<!-- VERIFY: source="fixture" chunk="7-klas-ukrmova-fixture_s004" -->
Візьми розповідь: тло триває, а послідовність дій рухає події. Дієприслівник
допомагає стисло поєднати дії: **читаючи**, **сказавши**.
<!-- INJECT_ACTIVITY: act-4 -->

## Дієслова на -ся: зворотні дієслова в повторенні
<!-- VERIFY: source="fixture" chunk="7-klas-ukrmova-fixture_s005" -->
Зверни увагу на **вчуся**, **вчишся**, **вчиться**. Ці форми показують постфікс
і допомагають твоєму мовленню звучати природно.
<!-- INJECT_ACTIVITY: {marker} -->

## Підсумок: від знання до вживання
<!-- VERIFY: source="fixture" chunk="7-klas-ukrmova-fixture_s006" -->
Дієприкметник потребує деколонізаційного контролю: <!-- bad -->посинівший<!-- /bad -->
не є моделлю; потрібна форма **посинілий**, підрядне **дівчина, яка читала**,
або конструкція **той, що переміг**. Калька і суржик не мають ставати правилом.
Спробуй пояснити правило своїми словами. {filler}
"""


def _raw_writer_output(module: str, activities: object | None = None) -> str:
    activities_payload = activities if activities is not None else _activities()
    map_rows = "\n".join(
        f'<row obligation_id="step-{index}" artifact="module.md" '
        f'location="§{heading}" treatment="covered in prose" />'
        for index, heading in enumerate(
            [
                "Теперішній час: дієвідміни",
                "Теперішній час: дієвідміни",
                "Минулий час: утворення і вживання",
                "Вид дієслова: доконаний і недоконаний",
                "Вид у розповіді: послідовність і тло",
                "Підсумок: від знання до вживання",
            ],
            start=1,
        )
    )
    return f"""<plan_reasoning><verification_trace>verify_words search_text</verification_trace></plan_reasoning>
<implementation_map>
{map_rows}
</implementation_map>
<implementation_map_audit>manifest_obligations=6 covered_in_map=6 missing=[]</implementation_map_audit>

````markdown file=module.md
{module}
````

```json file=activities.yaml
{json.dumps(activities_payload, ensure_ascii=False)}
```

```json file=vocabulary.yaml
{json.dumps([{"lemma": "дієвідміна", "translation": "conjugation", "pos": "noun", "usage": "term"}], ensure_ascii=False)}
```

```json file=resources.yaml
{json.dumps(_resources(), ensure_ascii=False)}
```
"""


def _write_candidate(tmp_path: Path, raw: str) -> Path:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "writer_output.md").write_text(raw, encoding="utf-8")
    (candidate / "wiki_manifest.json").write_text(
        json.dumps(_manifest(), ensure_ascii=False),
        encoding="utf-8",
    )
    return candidate


def _checks_by_name(report: dict) -> dict[str, dict]:
    return {item["name"]: item for item in report["checks"]}


def test_scorer_reports_strict_parse_failure_for_inline_workbook_root(tmp_path: Path) -> None:
    candidate = _write_candidate(
        tmp_path,
        _raw_writer_output(_module(), activities={"inline": [], "workbook": []}),
    )

    report = score_writer_output(
        level="b1",
        slug="b1-baseline-past-present",
        writer_output_path=candidate / "writer_output.md",
        candidate_dir=candidate,
        wiki_manifest_path=candidate / "wiki_manifest.json",
    )

    checks = _checks_by_name(report)
    assert report["summary"]["passed"] is False
    assert checks["parse_writer_output"]["passed"] is False
    assert "root must be list" in checks["parse_writer_output"]["details"]["error"]


def test_scorer_flags_meta_voice_and_activity_marker_mismatch(tmp_path: Path) -> None:
    candidate = _write_candidate(
        tmp_path,
        _raw_writer_output(_module("Цей модуль допомагає повторити часи.", marker="act-99")),
    )

    report = score_writer_output(
        level="b1",
        slug="b1-baseline-past-present",
        writer_output_path=candidate / "writer_output.md",
        candidate_dir=candidate,
        wiki_manifest_path=candidate / "wiki_manifest.json",
    )

    checks = _checks_by_name(report)
    assert checks["parse_writer_output"]["passed"] is True
    assert checks["forbidden_meta_voice"]["passed"] is False
    assert checks["inline_activity_markers"]["passed"] is False
    assert checks["inline_activity_markers"]["details"]["missing_activity_ids"] == ["act-99"]


def test_scorer_accepts_core_shape_for_candidate(tmp_path: Path) -> None:
    candidate = _write_candidate(tmp_path, _raw_writer_output(_module()))

    report = score_writer_output(
        level="b1",
        slug="b1-baseline-past-present",
        writer_output_path=candidate / "writer_output.md",
        candidate_dir=candidate,
        wiki_manifest_path=candidate / "wiki_manifest.json",
    )

    checks = _checks_by_name(report)
    assert checks["parse_writer_output"]["passed"] is True
    assert checks["expected_b1_m01_sections"]["passed"] is True
    assert checks["activity_parser_schema"]["passed"] is True
    assert checks["inline_activity_markers"]["passed"] is True
    assert checks["resources_source_honesty"]["passed"] is True
    assert checks["verify_source_comments"]["passed"] is True
    assert checks["bad_form_marker_discipline"]["passed"] is True
    assert checks["vesum_word_verification_evidence"]["passed"] is True


def test_scorer_accepts_schema_text_field_for_cloze(tmp_path: Path) -> None:
    activities = [
        *_activities(),
        {
            "type": "cloze",
            "title": "Текст",
            "instruction": "Заповніть пропуск.",
            "text": "Я [1] текст.",
            "blanks": [
                {
                    "id": 1,
                    "answer": "читаю",
                    "options": ["читаю", "читав"],
                }
            ],
        },
    ]
    candidate = _write_candidate(tmp_path, _raw_writer_output(_module(), activities=activities))

    report = score_writer_output(
        level="b1",
        slug="b1-baseline-past-present",
        writer_output_path=candidate / "writer_output.md",
        candidate_dir=candidate,
        wiki_manifest_path=candidate / "wiki_manifest.json",
    )

    checks = _checks_by_name(report)
    assert checks["parse_writer_output"]["passed"] is True
    assert checks["activity_parser_schema"]["passed"] is True


def test_scorer_reads_sources_mcp_tool_call_names() -> None:
    report = _check_source_tool_evidence(
        "",
        [
            {"name": "mcp__sources__search_text"},
            {"name": "mcp__sources__verify_words"},
        ],
    )

    assert report["telemetry_tools"] == ["search_text", "verify_words"]
    assert report["verify_words_telemetry_calls"] == 1
