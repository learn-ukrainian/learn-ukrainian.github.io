"""Load-bearing tests for hramatka QG rule set.

Each check must FIRE on its planted known-bad fixture and a clean lesson must PASS.
A green on a lesson carrying a planted fault is a test failure.

Data-dependent detectors (style_guide / PULS CEFR / ukrajinet / VESUM / heritage)
run against CONTROLLED temporary SQLite DBs — never ambient sources.db fullness.
CI and local therefore exercise the same real SQL + gate logic. Production still
gracefully degrades when tables are missing; tests never rely on that path for
load-bearing clean→PASS / planted→FAIL assertions.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.audit import hramatka_qg_rules as hq
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
HERITAGE_SAMPLE_DB = PROJECT_ROOT / "tests" / "fixtures" / "heritage_sample.db"

# Planted non-forms that must stay VESUM-absent under the controlled fixture DB.
_PLANTED_NON_VESUM = frozenset(
    {
        "зделати",
        "жмурклея",
        "ффффффф",
        "кушати",
    }
)
_OVERLEVEL_TOKEN = "чигати"

_CYR_TOKEN_RE = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ][А-Яа-яЁёІіЇїЄєҐґ'ʼ’\-]*")


def _by_id(report: dict) -> dict[str, dict]:
    return {row["id"]: row for row in report["results"]}


def _issue_ids(evidence: dict) -> set[str]:
    return {f["issue_id"] for f in all_findings(evidence)}


def _collect_fixture_tokens() -> set[str]:
    """Surface tokens from synthetic fixtures + hard-coded clean lessons in this file."""
    data = yaml.safe_load(FIXTURE_FILE.read_text(encoding="utf-8"))
    tokens: set[str] = set()
    for entry in data.get("fixtures") or []:
        lesson = entry.get("lesson_json") or {}
        adapted = adapt_lesson_json(lesson, slug=str(entry.get("id") or "x"))
        for _path, text in adapted.learner_strings:
            for tok in _CYR_TOKEN_RE.findall(text or ""):
                tokens.add(tok.casefold())
    # Hard-coded clean lessons used by CLI / dispatch / direct-scan tests.
    extras = (
        "CLI урок",
        "Ми вчимося мови.",
        "Перевірте.",
        "Ми вчимося.",
        "Диспетчер",
        "Ми читаємо.",
        "Правда",
        "Прямий скан",
        "Ми говоримо українською.",
        "Ми говоримо.",
        "Чистий",
        "Калибр",
        "Треба зделати роботу і приймати участь.",
        "Участь",
        "Студенти хочуть приймати участь у святі.",
        "Вони хочуть приймати участь.",
        # Proper-noun precision probe (must not false-positive when absent from VESUM).
        "Львів",
        "Оля",
        "НАТО",
    )
    for text in extras:
        for tok in _CYR_TOKEN_RE.findall(text):
            tokens.add(tok.casefold())
    return tokens


def _build_controlled_vesum(path: Path) -> None:
    """Minimal VESUM forms table: clean tokens present, planted non-forms absent."""
    tokens = sorted(
        t
        for t in _collect_fixture_tokens()
        if t not in _PLANTED_NON_VESUM and not re.fullmatch(r"ф+", t)
    )
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "CREATE TABLE forms (word_form TEXT NOT NULL, lemma TEXT NOT NULL, "
            "tags TEXT NOT NULL, pos TEXT NOT NULL)"
        )
        rows = [(tok, tok, "fixture:mock", "unknown") for tok in tokens]
        conn.executemany(
            "INSERT INTO forms(word_form, lemma, tags, pos) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def _build_controlled_sources(path: Path) -> None:
    """Minimal sources.db: style_guide + PULS CEFR + ukrajinet rows the fixtures need."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE style_guide (
                id INTEGER PRIMARY KEY,
                word TEXT,
                section TEXT,
                text TEXT,
                source TEXT,
                word_lower TEXT,
                excerpt_full TEXT,
                page TEXT,
                russianism_pattern TEXT
            );
            CREATE TABLE puls_cefr (
                id INTEGER PRIMARY KEY,
                word TEXT,
                guideword TEXT,
                level TEXT,
                pos TEXT,
                type TEXT,
                text TEXT,
                source TEXT
            );
            CREATE TABLE ukrajinet (
                id INTEGER PRIMARY KEY,
                synset_id TEXT,
                words TEXT,
                text TEXT,
                source TEXT
            );
            """
        )
        conn.execute(
            "INSERT INTO style_guide(word, section, text, source) VALUES (?, ?, ?, ?)",
            (
                "Приймати участь – брати участь",
                "ДІЄСЛОВА",
                "fixture calque title",
                "Antonenko-Davydovych",
            ),
        )
        # Over-level planted token (C1) + level-appropriate baselines that must NOT warn.
        cefr_rows = [
            (_OVERLEVEL_TOKEN, "c1"),
            ("речення", "a1"),
            ("хліб", "a1"),
            ("ми", "a1"),
            ("слово", "a1"),
            ("читаємо", "a1"),
            ("великий", "a2"),
            ("квартира", "a2"),
        ]
        for word, level in cefr_rows:
            conn.execute(
                "INSERT INTO puls_cefr(word, level, text, source) VALUES (?, ?, ?, ?)",
                (word, level, f"{word} ({level})", "PULS-fixture"),
            )
        conn.execute(
            "INSERT INTO ukrajinet(synset_id, words, text, source) VALUES (?, ?, ?, ?)",
            (
                "fixture-syn-1",
                json.dumps(["великий", "видатний"], ensure_ascii=False),
                "Синоніми: великий, видатний",
                "Ukrajinet-fixture",
            ),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _controlled_data_layer(monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory):
    """Point hramatka QG at controlled SQLite DBs (real SQL paths, known rows).

    Exercises the same helpers production uses — not ambient-db degradation.
    Heritage classifier uses the repo's small sample DB (table shape only);
    VESUM attestation is forced through the controlled forms table.
    """
    root = tmp_path_factory.mktemp("hramatka_qg_controlled")
    sources = root / "sources.db"
    vesum = root / "vesum.db"
    _build_controlled_sources(sources)
    _build_controlled_vesum(vesum)

    monkeypatch.setattr(hq, "_SOURCES_DB_OVERRIDE", sources)
    monkeypatch.setattr(hq, "_VESUM_DB_OVERRIDE", vesum)
    # Prefer sample heritage tables when present; else controlled sources (empty heritage).
    heritage = HERITAGE_SAMPLE_DB if HERITAGE_SAMPLE_DB.exists() else sources
    monkeypatch.setattr(hq, "_HERITAGE_DB_OVERRIDE", heritage)

    yield {
        "sources": sources,
        "vesum": vesum,
        "heritage": heritage,
    }


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


def test_controlled_sql_helpers_exercise_real_logic() -> None:
    """Prove CEFR / synonym / Antonenko hit the controlled rows (not stubs)."""
    assert hq._cefr_level_for(_OVERLEVEL_TOKEN) == "c1"
    assert hq._cefr_level_for("речення") == "a1"
    assert "видатний" in hq._synonym_lemmas("великий")
    hits = hq._antonenko_title_hit("Студенти хочуть приймати участь у святі.")
    assert hits, "controlled style_guide must flag 'приймати участь'"
    assert hq._vesum_hits("квартиру"), "controlled VESUM must attest clean tokens"
    assert not hq._vesum_hits("жмурклея"), "planted invented form must stay VESUM-absent"
    assert not hq._vesum_hits("зделати"), "planted russian-shadow form must stay VESUM-absent"


def test_proper_noun_and_capitalized_name_not_invented() -> None:
    """Invented-form must not flag place names / names (Львів-type)."""
    # Ensure these are ABSENT from controlled VESUM for this assertion.
    assert not hq._vesum_hits("Харків")  # not in fixture token set
    assert hq._is_probable_proper_noun("Львів")
    assert hq._is_probable_proper_noun("Оля")
    assert hq._is_probable_proper_noun("НАТО")
    assert not hq._is_invented_form("Львів")
    assert not hq._is_invented_form("Оля")
    assert not hq._is_invented_form("НАТО")

    evidence = scan_hramatka_lesson(
        {
            "title": "Львів",
            "level": "B1",
            "anchor": {"text": "Оля була у Львові біля парку."},
            "blocks": [
                {
                    "type": "true-false",
                    "activity": {
                        "type": "true-false",
                        "title": "Правда",
                        "payload": {
                            "type": "true-false",
                            "instruction": "Перевірте.",
                            "items": [{"statement": "Оля була у Львові.", "correct": True}],
                        },
                        "answer_key": {"items": [{"index": 0, "correct": True}]},
                    },
                    "answer_key": "1 П",
                }
            ],
        },
        slug="proper-noun-clean",
    )
    assert evidence["verdict"] == "PASS"
    assert "NON_VESUM_FORM" not in _issue_ids(evidence)


def test_cefr_only_flags_clear_overlevel_in_task_language() -> None:
    """CEFR must stay quiet for level-appropriate task words; fire only on planted C1."""
    # A1 lesson with only A1 task words → PASS (no false WARN).
    clean_a1 = scan_hramatka_lesson(
        {
            "title": "Хліб",
            "level": "A1",
            "anchor": {"text": "Я їм хліб."},
            "blocks": [
                {
                    "type": "true-false",
                    "activity": {
                        "type": "true-false",
                        "title": "Перевірка",
                        "payload": {
                            "type": "true-false",
                            "instruction": "Чи це хліб?",
                            "items": [{"statement": "Я їм хліб.", "correct": True}],
                        },
                        "answer_key": {"items": [{"index": 0, "correct": True}]},
                    },
                    "answer_key": "1 П",
                }
            ],
        },
        slug="cefr-clean-a1",
    )
    assert clean_a1["verdict"] == "PASS"
    assert "TASK_CEFR_OVERLEVEL" not in _issue_ids(clean_a1)

    # Same level with planted C1 task verb → WARN.
    over = scan_hramatka_lesson(
        {
            "title": "Просте",
            "level": "A1",
            "anchor": {"text": "Я їм хліб."},
            "blocks": [
                {
                    "type": "true-false",
                    "activity": {
                        "type": "true-false",
                        "title": "Перевірка",
                        "payload": {
                            "type": "true-false",
                            "instruction": "Чи можна чигати за дверима?",
                            "items": [{"statement": "Я їм хліб.", "correct": True}],
                        },
                        "answer_key": {"items": [{"index": 0, "correct": True}]},
                    },
                    "answer_key": "1 П",
                }
            ],
        },
        slug="cefr-over",
    )
    assert over["verdict"] == "WARN"
    assert "TASK_CEFR_OVERLEVEL" in _issue_ids(over)


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
    assert all_findings(payload) == []


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


def test_missing_style_guide_and_cefr_tables_do_not_crash(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Production robustness: missing tables → detector_unavailable, no crash.

    Load-bearing planted/clean assertions still run against controlled data
    restored after the stripped-DB probe (autouse fixture remains active for
    the suite; this test only temporarily points sources at a stripped file).
    """
    stripped = tmp_path / "sources.db"
    conn = sqlite3.connect(str(stripped))
    conn.execute("CREATE TABLE unrelated (id INTEGER)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(hq, "_SOURCES_DB_OVERRIDE", stripped)

    clean = scan_hramatka_lesson(
        {
            "title": "Чистий",
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
        slug="stripped-clean",
    )
    # VESUM still controlled → clean PASS; style_guide/CEFR mark unavailable.
    assert clean["verdict"] == "PASS"
    status = clean.get("detector_status") or {}
    assert "antonenko_style_guide" in status
    assert status["antonenko_style_guide"]["status"] == "detector_unavailable"
    assert "no such table" in status["antonenko_style_guide"]["reason"].casefold()

    assert hq._antonenko_title_hit("приймати участь у святі") == []
    assert hq._cefr_level_for(_OVERLEVEL_TOKEN) is None


def test_stripped_cefr_and_synonym_tables_mark_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Real CEFR / synonym SQL against a table-less DB records detector_unavailable."""
    stripped = tmp_path / "sources.db"
    conn = sqlite3.connect(str(stripped))
    conn.execute("CREATE TABLE unrelated (id INTEGER)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(hq, "_SOURCES_DB_OVERRIDE", stripped)

    unavailable: dict[str, str] = {}
    token = hq._ACTIVE_UNAVAILABLE.set(unavailable)
    try:
        assert hq._cefr_level_for("слово") is None
        assert hq._synonym_lemmas("великий") == set()
        assert hq._antonenko_title_hit("приймати участь") == []
    finally:
        hq._ACTIVE_UNAVAILABLE.reset(token)

    assert "puls_cefr" in unavailable
    assert "ukrajinet_synonyms" in unavailable
    assert "antonenko_style_guide" in unavailable
    for name in ("puls_cefr", "ukrajinet_synonyms", "antonenko_style_guide"):
        assert "no such table" in unavailable[name].casefold()


def test_vesum_unavailable_does_not_flood_invented_forms(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When VESUM is missing, NON_VESUM_FORM must stay quiet (cannot prove absence)."""
    missing = tmp_path / "no-vesum.db"
    # Do not create the file — verify_word raises FileNotFoundError.
    monkeypatch.setattr(hq, "_VESUM_DB_OVERRIDE", missing)

    evidence = scan_hramatka_lesson(
        {
            "title": "Чистий",
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
        slug="vesum-missing-clean",
    )
    assert evidence["verdict"] == "PASS"
    assert "NON_VESUM_FORM" not in _issue_ids(evidence)
    assert "RUSSIAN_SHADOW_RUSSICISM" not in _issue_ids(evidence)
    status = evidence.get("detector_status") or {}
    assert "vesum" in status


def test_antonenko_calque_fires_via_controlled_style_guide() -> None:
    """Deterministic Antonenko path: controlled style_guide row + real SQL helper."""
    evidence = scan_hramatka_lesson(
        {
            "title": "Участь",
            "level": "B1",
            "anchor": {"text": "Студенти хочуть приймати участь у святі."},
            "blocks": [
                {
                    "type": "true-false",
                    "activity": {
                        "type": "true-false",
                        "title": "Правда",
                        "payload": {
                            "type": "true-false",
                            "instruction": "Перевірте.",
                            "items": [{"statement": "Вони хочуть приймати участь.", "correct": True}],
                        },
                        "answer_key": {"items": [{"index": 0, "correct": True}]},
                    },
                    "answer_key": "1 П",
                }
            ],
        },
        slug="antonenko-controlled",
    )
    assert evidence["verdict"] in {"WARN", "FAIL"}
    issues = _issue_ids(evidence)
    assert "ANTONENKO_CALQUE" in issues
    assert "RUSSICISM_DETECTED" in issues or "ANTONENKO_CALQUE" in issues
