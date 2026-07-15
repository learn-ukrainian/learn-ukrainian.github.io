"""Load-bearing tests for hramatka QG rule set.

Each check must FIRE on its planted known-bad fixture and a clean lesson must PASS.
A green on a lesson carrying a planted fault is a test failure.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit.curriculum_qg_harness import main as harness_main
from scripts.audit.curriculum_qg_harness import run_fixtures as harness_run_fixtures
from scripts.audit.curriculum_qg_harness import scan_curriculum_module
from scripts.audit.hramatka_qg_rules import (
    CHECKER_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    RULE_SET_ID,
    adapt_lesson_json,
    all_findings,
    checker_config_hash,
    run_fixtures,
    scan_hramatka_lesson,
    write_adapted_module_dir,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_FILE = PROJECT_ROOT / "tests" / "fixtures" / "hramatka_qg" / "fixtures.yaml"
ACTIVITY_KIT_LESSON = (
    PROJECT_ROOT / "packages" / "activity-kit" / "src" / "fixtures" / "lu.lesson.v1.fixture.json"
)


def _by_id(report: dict) -> dict[str, dict]:
    return {row["id"]: row for row in report["results"]}


def _issue_ids(evidence: dict) -> set[str]:
    return {f["issue_id"] for f in all_findings(evidence)}


def test_hramatka_fixture_suite_load_bearing() -> None:
    """Every synthetic known-bad must be caught; clean lesson must PASS."""
    report = run_fixtures(FIXTURE_FILE)

    assert report["rule_set"] == RULE_SET_ID
    assert report["summary"]["failed"] == 0, {
        row["id"]: row.get("missing_findings") or row.get("actual_verdict")
        for row in report["results"]
        if not row["passed"]
    }
    assert report["summary"]["total"] >= 10

    by_id = _by_id(report)
    assert by_id["clean-b1-lesson"]["actual_verdict"] == "PASS"
    assert by_id["planted-russianism"]["actual_verdict"] == "FAIL"
    assert by_id["planted-russian-shadow"]["actual_verdict"] == "FAIL"
    assert by_id["planted-bad-distractors"]["actual_verdict"] == "FAIL"
    assert by_id["planted-placeholder-key"]["actual_verdict"] == "FAIL"
    assert by_id["planted-broken-cloze"]["actual_verdict"] == "FAIL"
    assert by_id["planted-overlevel-task"]["actual_verdict"] == "WARN"
    assert by_id["planted-invented-form"]["actual_verdict"] == "WARN"
    assert by_id["planted-empty-surface"]["actual_verdict"] == "FAIL"
    assert by_id["planted-mc-too-few"]["actual_verdict"] == "FAIL"


def test_each_check_fires_on_planted_fault() -> None:
    report = run_fixtures(FIXTURE_FILE)
    by_id = _by_id(report)

    cases = {
        "planted-russianism": "RUSSICISM_DETECTED",
        "planted-russian-shadow": "RUSSIAN_SHADOW_RUSSICISM",
        "planted-bad-distractors": "NON_VESUM_DISTRACTOR",
        "planted-placeholder-key": "ANSWER_KEY_PLACEHOLDER",
        "planted-broken-cloze": "CLOZE_BLANK_MISMATCH",
        "planted-overlevel-task": "TASK_CEFR_OVERLEVEL",
        "planted-invented-form": "NON_VESUM_FORM",
        "planted-empty-surface": "EMPTY_LEARNER_SURFACE",
        "planted-mc-too-few": "MC_TOO_FEW_OPTIONS",
    }
    for fixture_id, issue_id in cases.items():
        evidence = by_id[fixture_id]["evidence"]
        ids = _issue_ids(evidence)
        assert issue_id in ids, f"{fixture_id} missing {issue_id}; got {sorted(ids)}"
        # Load-bearing: planted fault must not green
        assert evidence["verdict"] != "PASS", f"{fixture_id} wrongly PASSed with planted fault"


def test_synonym_collision_fires() -> None:
    report = run_fixtures(FIXTURE_FILE)
    evidence = _by_id(report)["planted-bad-distractors"]["evidence"]
    assert "SYNONYM_DISTRACTOR" in _issue_ids(evidence)


def test_clean_lesson_has_no_findings() -> None:
    report = run_fixtures(FIXTURE_FILE)
    clean = _by_id(report)["clean-b1-lesson"]
    assert clean["actual_verdict"] == "PASS"
    assert all_findings(clean["evidence"]) == []


def test_adapter_excludes_internal_fields_and_keeps_learner_surface(tmp_path: Path) -> None:
    lesson = {
        "title": "Тестовий урок",
        "level": "B1",
        "method": "ttt",
        "status": "ready",
        "anchor": {
            "text": "Текст якоря для учнів.",
            "source": "teacher-paste",
            "chars": 20,
        },
        "blocks": [
            {
                "id": "secret-id",
                "phase": 1,
                "type": "multiple-choice",
                "mark": "ok",
                "note": "teacher only note with phone 099",
                "provenance": {"source": "generated", "generator": "hramatka"},
                "activity": {
                    "type": "multiple-choice",
                    "title": "Оберіть",
                    "payload": {
                        "type": "multiple-choice",
                        "instruction": "Оберіть відповідь.",
                        "items": [
                            {
                                "prompt": "Де парк?",
                                "options": ["а) тут", "б) там"],
                            }
                        ],
                    },
                    "answer_key": {"items": [{"index": 0, "correct": "а"}]},
                    "provenance": {"source": "teacher-paste"},
                    "system_prompt": "DO NOT LEAK",
                    "rationale": "internal",
                },
                "answer_key": "1 — а",
                "hint": "підказка для учня",
            }
        ],
    }
    adapted = adapt_lesson_json(lesson, slug="adapter-test")
    write_adapted_module_dir(adapted, tmp_path / "mod")

    module_md = (tmp_path / "mod" / "module.md").read_text(encoding="utf-8")
    activities = (tmp_path / "mod" / "activities.yaml").read_text(encoding="utf-8")
    meta = json.loads((tmp_path / "mod" / "hramatka_adapter_meta.json").read_text(encoding="utf-8"))

    assert "Тестовий урок" in module_md
    assert "Текст якоря для учнів" in module_md
    assert "Оберіть відповідь" in module_md
    assert "підказка для учня" in activities or "підказка для учня" in module_md

    # Privacy / correctness exclusions
    leaked = ("provenance", "system_prompt", "DO NOT LEAK", "teacher only note", "phone 099", "rationale")
    blob = module_md + activities
    for fragment in leaked:
        assert fragment not in blob, f"internal field leaked: {fragment}"

    assert "provenance" in adapted.excluded_keys_seen
    assert "mark" in adapted.excluded_keys_seen
    assert "phase" in adapted.excluded_keys_seen
    assert adapted.level == "b1"
    assert adapted.content_hash
    assert meta["content_hash"] == adapted.content_hash
    assert meta["rule_set"] == RULE_SET_ID


def test_adapter_content_hash_stable() -> None:
    lesson = {
        "title": "Стабільний",
        "level": "A2",
        "anchor": {"text": "Ми вчимося."},
        "blocks": [],
    }
    a = adapt_lesson_json(lesson, slug="stable")
    b = adapt_lesson_json(lesson, slug="stable")
    assert a.content_hash == b.content_hash
    assert a.level == "a2"


def test_harness_rule_set_dispatch_selects_hramatka(tmp_path: Path) -> None:
    """Curriculum harness must route rule_set=hramatka to the separate module."""
    lesson = {
        "title": "Диспетчер",
        "level": "B1",
        "anchor": {"text": "Ми читаємо."},
        "blocks": [
            {
                "type": "true-false",
                "activity": {
                    "type": "true-false",
                    "title": "Правда",
                    "payload": {
                        "type": "true-false",
                        "instruction": "Перевірте.",
                        "items": [{"statement": "Ми читаємо.", "correct": True}],
                    },
                    "answer_key": {"items": [{"index": 0, "correct": True}]},
                },
                "answer_key": "1 П",
            }
        ],
    }
    adapted = adapt_lesson_json(lesson, slug="dispatch")
    module_dir = tmp_path / "dispatch"
    write_adapted_module_dir(adapted, module_dir)

    evidence = scan_curriculum_module(
        module_dir,
        level="b1",
        slug="dispatch",
        rule_set="hramatka",
    )
    assert evidence["rule_set"] == RULE_SET_ID
    assert evidence["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert evidence["checker_config"]["version"] == CHECKER_VERSION
    assert evidence["checker_config"]["config_hash"] == checker_config_hash()
    assert evidence["verdict"] == "PASS"


def test_harness_fixtures_cli_dispatches_hramatka_schema() -> None:
    report = harness_run_fixtures(FIXTURE_FILE)
    assert report["rule_set"] == RULE_SET_ID
    assert report["summary"]["failed"] == 0


def test_harness_cli_lesson_json(tmp_path: Path) -> None:
    lesson_path = tmp_path / "lesson.json"
    lesson_path.write_text(
        json.dumps(
            {
                "title": "CLI урок",
                "level": "B1",
                "anchor": {"text": "Ми вчимося мови."},
                "blocks": [
                    {
                        "type": "true-false",
                        "activity": {
                            "type": "true-false",
                            "title": "Правда",
                            "payload": {
                                "type": "true-false",
                                "instruction": "Перевірте.",
                                "items": [{"statement": "Ми вчимося.", "correct": True}],
                            },
                            "answer_key": {"items": [{"index": 0, "correct": True}]},
                        },
                        "answer_key": "1 П",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    code = harness_main(
        [
            "--lesson-json",
            str(lesson_path),
            "--format",
            "json",
            "--output",
            str(out),
        ]
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["rule_set"] == RULE_SET_ID
    assert payload["verdict"] == "PASS"


def test_curriculum_phrase_rules_do_not_rubber_stamp_hramatka_faults(tmp_path: Path) -> None:
    """Curriculum PHRASE_RULES must not be the gate for hramatka content.

    A planted russianism that curriculum phrase rules never contain would PASS
    under curriculum rules — proving why rule sets must stay separate.
    """
    lesson = {
        "title": "Калибр",
        "level": "B1",
        "anchor": {"text": "Треба зделати роботу і приймати участь."},
        "blocks": [
            {
                "type": "true-false",
                "activity": {
                    "type": "true-false",
                    "title": "Правда",
                    "payload": {
                        "type": "true-false",
                        "instruction": "Перевірте.",
                        "items": [{"statement": "Треба зделати.", "correct": True}],
                    },
                    "answer_key": {"items": [{"index": 0, "correct": True}]},
                },
                "answer_key": "1 П",
            }
        ],
    }
    adapted = adapt_lesson_json(lesson, slug="calib")
    module_dir = tmp_path / "calib"
    write_adapted_module_dir(adapted, module_dir)

    curriculum = scan_curriculum_module(module_dir, level="b1", slug="calib", rule_set="curriculum")
    hramatka = scan_curriculum_module(module_dir, level="b1", slug="calib", rule_set="hramatka")

    curriculum_issues = _issue_ids(curriculum)
    # Curriculum PHRASE_RULES are writer-failure phrases — planted hramatka faults
    # (зделати / приймати участь) are not among them.
    assert "RUSSICISM_DETECTED" not in curriculum_issues
    assert "RUSSIAN_SHADOW_RUSSICISM" not in curriculum_issues
    assert "AWKWARD_PASSIVE_RESULT_STATE" not in curriculum_issues
    # Hramatka rules must catch the planted fault.
    assert hramatka["verdict"] == "FAIL"
    assert "RUSSICISM_DETECTED" in _issue_ids(hramatka) or "RUSSIAN_SHADOW_RUSSICISM" in _issue_ids(
        hramatka
    )


def test_scan_hramatka_lesson_direct() -> None:
    evidence = scan_hramatka_lesson(
        {
            "title": "Прямий скан",
            "level": "B1",
            "anchor": {"text": "Ми говоримо українською."},
            "blocks": [
                {
                    "type": "true-false",
                    "activity": {
                        "type": "true-false",
                        "title": "Правда",
                        "payload": {
                            "type": "true-false",
                            "instruction": "Перевірте.",
                            "items": [{"statement": "Ми говоримо.", "correct": True}],
                        },
                        "answer_key": {"items": [{"index": 0, "correct": True}]},
                    },
                    "answer_key": "1 П",
                }
            ],
        },
        slug="direct",
    )
    assert evidence["verdict"] == "PASS"
    assert evidence["rule_set"] == RULE_SET_ID


def test_activity_kit_fixture_adapter_roundtrip() -> None:
    """Adapter accepts the real activity-kit lesson shape without crashing."""
    if not ACTIVITY_KIT_LESSON.exists():
        return
    lesson = json.loads(ACTIVITY_KIT_LESSON.read_text(encoding="utf-8"))
    adapted = adapt_lesson_json(lesson)
    assert adapted.title
    assert adapted.level == "b1"
    assert adapted.activities
    assert "provenance" in adapted.excluded_keys_seen
    # Must not leak teacher notes into module.md
    assert "погляньте перед заняттям" not in adapted.module_md
