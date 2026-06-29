from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.audit.checks.b2_rebuild_contract import check_b2_rebuild_contract


def _activities_file(tmp_path: Path, payload: Any) -> Path:
    path = tmp_path / "activities.yaml"
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _inline_activity(activity_id: str) -> dict[str, Any]:
    return {
        "id": activity_id,
        "type": "quiz",
        "title": f"Practice {activity_id}",
        "instruction": "Оберіть точний варіант.",
        "items": [
            {
                "question": "Що точніше?",
                "options": ["але", "і", "або"],
                "correct": 0,
            }
        ],
    }


def _valid_activities() -> dict[str, Any]:
    return {
        "version": "1.0",
        "module": "advanced-conjunctions-rebuild",
        "level": "b2",
        "inline": [_inline_activity(f"act-{idx}") for idx in range(1, 5)],
        "workbook": [_inline_activity("workbook-1")],
    }


def _valid_module_text(extra: str = "") -> str:
    return f"""---
title: "Advanced conjunctions rebuild"
level: B2
focus: grammar
slug: advanced-conjunctions-rebuild
---
# Сполучники в аргументі

## Вибір зв'язку

| Форма | Сигнал |
| --- | --- |
| але | обмеження |
| зате | компенсація |

Почніть з прикладу: **план короткий, але переконливий**. Потім перевірте, чи
друга частина обмежує першу, додає компенсацію або відкриває альтернативу.

<!-- INJECT_ACTIVITY: act-1 -->

Коли зв'язок уже видно, правило стає коротким: не перекладайте English
“but” одним словом щоразу; перевіряйте смислову роль.

<!-- INJECT_ACTIVITY: act-2 -->

## Пунктуаційне рішення

Якщо частини рівноправні, то обирайте сурядний зв'язок і перевіряйте кому.

<!-- INJECT_ACTIVITY: act-3 -->

Порівняйте два речення і виправте зайву кому перед одиничним **і**.

<!-- INJECT_ACTIVITY: act-4 -->

> [!note] Коротке правило після прикладів легше застосувати в редагуванні.

{extra}
"""


def _finding_types(findings: list[dict[str, Any]]) -> set[str]:
    return {finding["type"] for finding in findings}


def test_valid_b2_rebuild_contract_passes(tmp_path: Path) -> None:
    findings = check_b2_rebuild_contract(
        _valid_module_text(),
        _activities_file(tmp_path, _valid_activities()),
        meta_data={"level": "B2", "focus": "grammar", "slug": "advanced-conjunctions-rebuild"},
    )

    assert [finding for finding in findings if finding["blocking"]] == []


def test_inline_empty_and_workbook_marker_fail(tmp_path: Path) -> None:
    activities = {
        "version": "1.0",
        "module": "advanced-conjunctions-rebuild",
        "level": "b2",
        "inline": [],
        "workbook": [_inline_activity("workbook-1")],
    }
    text = _valid_module_text().replace("INJECT_ACTIVITY: act-1", "INJECT_ACTIVITY: workbook-1")

    findings = check_b2_rebuild_contract(
        text,
        _activities_file(tmp_path, activities),
        meta_data={"level": "B2", "focus": "grammar", "slug": "advanced-conjunctions-rebuild"},
    )

    types = _finding_types(findings)
    assert "B2_INLINE_ACTIVITY_FLOOR" in types
    assert "B2_INJECT_MARKER_OUTSIDE_INLINE" in types
    assert all(finding["blocking"] for finding in findings if finding["severity"] == "error")


def test_no_inject_markers_fail(tmp_path: Path) -> None:
    findings = check_b2_rebuild_contract(
        _valid_module_text().replace("INJECT_ACTIVITY", "OMIT_ACTIVITY"),
        _activities_file(tmp_path, _valid_activities()),
        meta_data={"level": "B2", "focus": "grammar", "slug": "advanced-conjunctions-rebuild"},
    )

    assert "B2_INJECT_MARKERS_MISSING" in _finding_types(findings)


def test_long_h2_exposition_before_practice_fails(tmp_path: Path) -> None:
    long_exposition = " ".join(["пояснення"] * 901)
    text = _valid_module_text(
        extra=f"""
## Надто довгий концепт

| Роль | Форма |
| --- | --- |
| вибір | або |

{long_exposition}

<!-- INJECT_ACTIVITY: act-4 -->
"""
    )

    findings = check_b2_rebuild_contract(
        text,
        _activities_file(tmp_path, _valid_activities()),
        meta_data={"level": "B2", "focus": "grammar", "slug": "advanced-conjunctions-rebuild"},
    )

    assert "B2_LONG_EXPOSITION_BEFORE_PRACTICE" in _finding_types(findings)


def test_structured_contrast_required_for_prose_only_grammar(tmp_path: Path) -> None:
    text = """---
title: "Synonymy and register"
level: B2
focus: grammar
slug: synonymy-register
---
# Синонімія і регістр

## Регістровий вибір

Книжне слово й розмовний відповідник не є автоматичними дублетами.
<!-- INJECT_ACTIVITY: act-1 -->
Треба бачити жанр, адресата і ступінь офіційності.
<!-- INJECT_ACTIVITY: act-2 -->
Порівняйте два варіанти і виправте невдалий регістр.
<!-- INJECT_ACTIVITY: act-3 -->
Після цього перенесіть правило в короткий службовий лист.
<!-- INJECT_ACTIVITY: act-4 -->
"""

    findings = check_b2_rebuild_contract(
        text,
        _activities_file(tmp_path, _valid_activities()),
        meta_data={"level": "B2", "focus": "grammar", "slug": "synonymy-register"},
    )

    assert "B2_STRUCTURED_CONTRAST_MISSING" in _finding_types(findings)


def test_raw_callout_syntax_fails_for_b2(tmp_path: Path) -> None:
    findings = check_b2_rebuild_contract(
        _valid_module_text(extra="[!note] Raw callout is not accepted here."),
        _activities_file(tmp_path, _valid_activities()),
        meta_data={"level": "B2", "focus": "grammar", "slug": "advanced-conjunctions-rebuild"},
    )

    assert "B2_MALFORMED_CALLOUT" in _finding_types(findings)


def test_raw_callout_inside_fenced_code_is_allowed(tmp_path: Path) -> None:
    findings = check_b2_rebuild_contract(
        _valid_module_text(
            extra="""```markdown
[!note] This is an example of malformed syntax, not learner-facing callout prose.
```"""
        ),
        _activities_file(tmp_path, _valid_activities()),
        meta_data={"level": "B2", "focus": "grammar", "slug": "advanced-conjunctions-rebuild"},
    )

    assert "B2_MALFORMED_CALLOUT" not in _finding_types(findings)


def test_explicit_exemption_is_auditable_nonblocking(tmp_path: Path) -> None:
    findings = check_b2_rebuild_contract(
        "# Контроль\n\nNo activities.",
        _activities_file(tmp_path, {"inline": []}),
        meta_data={
            "level": "B2",
            "focus": "checkpoint",
            "b2_rebuild_contract_exemption": {"reason": "checkpoint module uses workbook-only synthesis"},
        },
    )

    assert findings == [
        {
            "type": "B2_REBUILD_EXEMPTION",
            "severity": "info",
            "blocking": False,
            "issue": "B2 rebuild contract explicitly exempted: checkpoint module uses workbook-only synthesis",
            "fix": "Review the exemption before accepting rebuilt B2 output.",
        }
    ]


def test_non_b2_modules_are_ignored(tmp_path: Path) -> None:
    findings = check_b2_rebuild_contract(
        "# B1 lesson\n\n[!note] Legacy raw callout.",
        _activities_file(tmp_path, {"inline": []}),
        meta_data={"level": "B1", "focus": "grammar"},
    )

    assert findings == []
