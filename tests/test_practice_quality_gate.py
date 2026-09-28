"""Unit tests for Practice Quality Gate (Issue #7944)."""

import json
from pathlib import Path

import pytest

from scripts.audit.practice_quality_gate import (
    DEFAULT_SOURCES_DB,
    VOLUME_THRESHOLDS,
    audit_card_ambiguity,
    audit_error_correction_deck,
    audit_practice_shards,
    audit_sentence_inventory,
    audit_teacher_cloze_deck,
    run_all_practice_audits,
)


def test_audit_teacher_cloze_validates_blank_count(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "good_1",
                "sentence": "Це гарне _____ речення.",
                "form": "гарне",
                "options": [{"label": "гарне", "kind": "answer"}, {"label": "погане", "kind": "distractor"}],
            },
            {
                "clozeId": "bad_multi",
                "sentence": "Перше _____ і друге _____ речення.",
                "form": "гарне",
                "options": [{"label": "гарне", "kind": "answer"}, {"label": "погане", "kind": "distractor"}],
            },
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "INVALID_BLANK_COUNT" and v["item"] == "bad_multi" for v in violations)
    assert not any(v["item"] == "good_1" for v in violations)


def test_audit_teacher_cloze_detects_intentional_error_leak(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "leaked_1",
                "sentence": "НЕПРАВИЛЬНО ПРАВИЛЬНО _____ рішення зволікати з рішенням",
                "form": "затягувати",
                "options": [{"label": "затягувати", "kind": "answer"}, {"label": "робити", "kind": "distractor"}],
            }
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "INTENTIONAL_ERROR_LEAK" for v in violations)


def test_audit_teacher_cloze_detects_duplicate_options(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "dup_opt",
                "sentence": "Я читаю цікаву _____ увечері.",
                "form": "книгу",
                "options": [
                    {"label": "книгу", "kind": "answer"},
                    {"label": "книгу", "kind": "distractor"},
                ],
            }
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "DUPLICATE_OPTIONS" for v in violations)


def test_audit_error_correction_validates_contract(tmp_path: Path):
    valid_deck = {
        "drills": [
            {
                "id": "drill_good",
                "sentence": "Він приймав участь у зборах.",
                "errorWord": "приймав участь",
                "correctForm": "брав участь",
                "options": ["брав участь", "приймав участь"],
                "explanation": "Калька з російської мови.",
                "sourceRef": {
                    "rowId": "textbooks:1",
                    "errorSpan": [0, 14],
                    "correctSpan": [15, 26],
                    "direction": "error_first",
                },
            },
            {
                "id": "drill_missing_target",
                "sentence": "Він прийшов додому вчасно.",
                "errorWord": "приймав участь",
                "correctForm": "брав участь",
                "options": ["брав участь", "приймав участь"],
                "explanation": "Калька з російської мови.",
            },
            {
                "id": "drill_missing_in_options",
                "sentence": "У нього був високий авторитет.",
                "errorWord": "авторитет",
                "correctForm": "престиж",
                "options": ["повага", "визнання"],
                "explanation": "Стилістична заміна.",
            },
        ]
    }
    violations = _audit_error_corrections(tmp_path, valid_deck["drills"])
    assert any(v["type"] == "ERROR_TARGET_NOT_IN_SENTENCE" and v["item"] == "drill_missing_target" for v in violations)
    assert any(
        v["type"] == "CORRECT_TARGET_MISSING_IN_OPTIONS" and v["item"] == "drill_missing_in_options" for v in violations
    )
    assert not any(v["item"] == "drill_good" for v in violations)


def test_audit_sentence_inventory_intentional_errors(tmp_path: Path):
    inv = {
        "rows": [
            {"lemma": "тест", "sentence": "Це звичайне речення."},
            {"lemma": "помилка", "sentence": "Помилку допущено у варіанті А."},
        ]
    }
    inv_path = tmp_path / "inv.json"
    inv_path.write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")

    violations = audit_sentence_inventory(inv_path)
    assert len(violations) == 1
    assert violations[0]["type"] == "INTENTIONAL_ERROR_LEAK"


def test_audit_error_correction_vesum_attestation(tmp_path: Path, monkeypatch):
    """Verify that unattested Ukrainian words in error-correction drills are flagged by VESUM."""
    from scripts.audit import practice_quality_gate

    deck = {
        "drills": [
            {
                "id": "drill_valid",
                "sentence": "Він брав участь у зборах.",
                "errorWord": "приймав участь",
                "correctForm": "брав",
                "options": ["брав", "приймав"],
                "explanation": "Калька.",
            },
            {
                "id": "drill_unattested",
                "sentence": "Це неіснуючеслово речення.",
                "errorWord": "помилка",
                "correctForm": "неіснуючеслово",
                "options": ["неіснуючеслово", "варіант"],
                "explanation": "Неіснуюче слово.",
            },
        ]
    }
    deck_path = tmp_path / "ec.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    def mock_verify_word(word: str, db_path=None):
        return word == "брав"

    monkeypatch.setattr(practice_quality_gate, "verify_word", mock_verify_word)
    fake_db = tmp_path / "mock_vesum.db"
    fake_db.touch()

    violations = audit_error_correction_deck(deck_path, vesum_db=fake_db)
    assert any(v["type"] == "VESUM_UNATTESTED" and v["item"] == "drill_unattested" for v in violations), (
        f"Expected VESUM_UNATTESTED violation, got: {violations}"
    )


def _error_correction_deck(tmp_path: Path, drills: list[dict], evidence: dict | None = None) -> Path:
    """Write a deck and its evidence snapshot (by default: one matching entry per bound drill)."""
    deck_path = tmp_path / "ec.json"
    deck_path.write_text(json.dumps({"drills": drills}, ensure_ascii=False), encoding="utf-8")
    if evidence is None:
        evidence = {
            d["id"]: {
                "rowId": d["sourceRef"]["rowId"],
                "rowSha256": "0" * 64,
                "error": d["errorWord"],
                "correct": d["correctForm"],
            }
            for d in drills
            if isinstance(d.get("sourceRef"), dict)
        }
    (tmp_path / "ec-evidence.json").write_text(json.dumps({"drills": evidence}, ensure_ascii=False), encoding="utf-8")
    return deck_path


def _audit_error_corrections(tmp_path: Path, drills: list[dict], evidence: dict | None = None, **kwargs):
    """Audit ``drills`` against their snapshot; CI mode (no sources.db, no VESUM) unless overridden."""
    kwargs.setdefault("vesum_db", None)
    kwargs.setdefault("sources_db", None)
    return audit_error_correction_deck(
        _error_correction_deck(tmp_path, drills, evidence), evidence_path=tmp_path / "ec-evidence.json", **kwargs
    )


def _drill(item_id: str, error: str, correct: str, options: list[str] | None = None, **extra) -> dict:
    """A drill bound to a one-line horizontal table row "<error> <correct>"."""
    return {
        "id": item_id,
        "sentence": f"Уважно прочитайте: «{error}» — тут допущено помилку.",
        "errorWord": error,
        "correctForm": correct,
        "options": options or sorted([correct, error]),
        "explanation": f"Правильно вживати «{correct}» замість помилкового «{error}».",
        "source": "Textbook Gr 10 (glazova)",
        "sourceRef": {
            "rowId": "textbooks:1",
            "errorSpan": [0, len(error)],
            "correctSpan": [len(error) + 1, len(error) + 1 + len(correct)],
            "direction": "error_first",
        },
        **extra,
    }


def _fixture_vesum(tmp_path: Path, forms: list[tuple[str, str]], marked: tuple[str, ...] = ()) -> Path:
    """Minimal VESUM file: (word form, part of speech); ``marked`` forms carry a ``bad`` marker."""
    import sqlite3

    vesum_path = tmp_path / "vesum.db"
    conn = sqlite3.connect(vesum_path)
    conn.execute(
        "CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER, word_form TEXT, lemma TEXT,"
        " pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT)"
    )
    conn.execute("CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT)")
    conn.execute("CREATE VIEW forms AS SELECT word_form, lemma, tags, pos FROM forms_all")
    for form_id, (form, pos) in enumerate(forms, 1):
        conn.execute(
            "INSERT INTO forms_all (id, entry_id, word_form, lemma, pos, tags, source_location)"
            " VALUES (?, 1, ?, ?, ?, ?, '')",
            (form_id, form, form, pos, pos),
        )
        if form in marked:
            conn.execute("INSERT INTO form_markers VALUES (?, 'bad', 'tag', 'invalid')", (form_id,))
    conn.commit()
    conn.close()
    return vesum_path


def _fixture_sources(tmp_path: Path, textbooks: list[tuple[int, str, str]]) -> Path:
    """Minimal sources.db: (grade, author, text) textbook rows and an empty style guide."""
    import sqlite3

    sources_path = tmp_path / "sources.db"
    conn = sqlite3.connect(sources_path)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, grade INTEGER, author TEXT, title TEXT, text TEXT)")
    conn.execute("CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, section TEXT, text TEXT)")
    conn.executemany("INSERT INTO textbooks (grade, author, title, text) VALUES (?, ?, 'Сторінка 1', ?)", textbooks)
    conn.commit()
    conn.close()
    return sources_path


def test_audit_error_correction_flags_register_label_distractors(tmp_path: Path):
    """#8723: the old builder padded every drill with "(розм.)"/"(застаріле)" copies."""
    planted = _drill(
        "err_labelled",
        "природній",
        "природний",
        ["природний", "природний (застаріле)", "природній", "природній (розм.)"],
    )
    violations = _audit_error_corrections(tmp_path, [planted, _drill("err_clean", "природній", "природний")])
    assert [(v["type"], v["item"]) for v in violations] == [("REGISTER_LABEL_DISTRACTOR", "err_labelled")]


def test_audit_error_correction_flags_unevidenced_pairs(tmp_path: Path):
    """#8723 err_0013/0021/0203/0001: pairs the source does not support fail the gate."""
    vesum_path = _fixture_vesum(
        tmp_path,
        [
            ("побудували", "verb"),
            ("цегляний", "adj"),
            ("україномовний", "adj"),
            ("українськомовний", "adj"),
            ("влучний", "adj"),
            ("вираз", "noun"),
            ("вислів", "noun"),
        ],
    )

    drills = [
        _drill("err_initial", "О.", "Теліга"),
        _drill("err_names", "Петро Чайковський", "Марія Заньковецька"),
        _drill("err_fragment", "побудували", "цегляний"),
        _drill("err_contested", "україномовний", "українськомовний"),
        _drill("err_good", "влучний вираз", "влучний вислів"),
    ]
    violations = _audit_error_corrections(tmp_path, drills, vesum_db=vesum_path)
    flagged = {v["item"] for v in violations if v["type"] == "UNEVIDENCED_ERROR_CORRECTION_PAIR"}
    assert flagged == {"err_initial", "err_names", "err_fragment", "err_contested"}
    assert not any(v["item"] == "err_good" for v in violations)


# Real VESUM (data/vesum.db, 2026-09-28): брати/купити/приймати/участь are standard;
# «протирічить» carries a VESUM error marker.
_PARTICIPATION_FORMS = [
    ("брати", "verb"),
    ("купити", "verb"),
    ("приймати", "verb"),
    ("участь", "noun"),
    ("не", "part"),
    ("протирічить", "verb"),
    ("суперечить", "verb"),
    ("суті", "noun"),
]


# ---------------------------------------------------------------------------
# Review round 4 (#8723): every drill is bound to its exact source row
# ---------------------------------------------------------------------------

# Real sources.db row textbooks:72208 (Glazova, grade 10): a column-block
# "Неправильно Правильно" table, the source of committed err_0003..err_0005.
_GLAZOVA_TABLE = (
    "Слідуючий оратор уже жде свого часу! (З Інтернету)\nПІДКАЗКА\nНеправильно Правильно\n"
    "нетактична поведінка\nпроявляти недостатки\nпредставляти інтерес\n"
    "нетактовна поведінка\nвиявляти недоліки\nстановити інтерес\n"
)
# Real VESUM (data/vesum.db, 2026-09-28): «недостатки» is a noun carrying the `bad`
# error marker, «нетактична» is not in VESUM; the other words are standard.
_GLAZOVA_FORMS = [
    ("недостатки", "noun"),
    ("проявляти", "verb"),
    ("представляти", "verb"),
    ("становити", "verb"),
    ("виявляти", "verb"),
    ("інтерес", "noun"),
    ("недоліки", "noun"),
    ("нетактовна", "adj"),
    ("поведінка", "noun"),
]


def _extracted_glazova_deck(tmp_path: Path) -> tuple[dict, dict, Path, Path]:
    """The extractor's deck and evidence snapshot for the Glazova table, with its fixture databases."""
    import sqlite3

    from scripts.practice.extract_textbook_error_corrections import (
        VesumLookup,
        build_evidence_snapshot,
        extract_error_correction_deck,
    )

    vesum_path = _fixture_vesum(tmp_path, _GLAZOVA_FORMS, marked=("недостатки",))
    sources_path = _fixture_sources(tmp_path, [(10, "glazova", _GLAZOVA_TABLE)])
    conn = sqlite3.connect(sources_path)
    deck = extract_error_correction_deck(conn, VesumLookup(vesum_path), log=lambda _msg: None)
    evidence = build_evidence_snapshot(deck, conn)["drills"]
    conn.close()
    return deck, evidence, sources_path, vesum_path


def _by_error(deck: dict) -> dict[str, dict]:
    return {drill["errorWord"]: drill for drill in deck["drills"]}


def _recombined(drill: dict, donor: dict, item_id: str) -> dict:
    """``drill``'s error with ``donor``'s correction, the correction span taken from ``donor``."""
    correct = donor["correctForm"]
    return {
        **drill,
        "id": item_id,
        "correctForm": correct,
        "options": sorted([correct, drill["errorWord"]]),
        "answers": [correct],
        "explanation": f"Правильно вживати «{correct}» замість помилкового «{drill['errorWord']}».",
        "sourceRef": {**drill["sourceRef"], "correctSpan": donor["sourceRef"]["correctSpan"]},
    }


def _forged_entry(drill: dict, evidence: dict, like: str) -> dict:
    """A snapshot entry forged to agree with ``drill`` (row SHA-256 copied from a genuine entry)."""
    return {**evidence[like], "error": drill["errorWord"], "correct": drill["correctForm"]}


def test_extracted_drills_are_bound_to_their_source_row(tmp_path: Path):
    deck, evidence, sources_path, vesum_path = _extracted_glazova_deck(tmp_path)
    assert [(d["errorWord"], d["correctForm"], d["sourceRef"]["rowId"]) for d in deck["drills"]] == [
        ("нетактична поведінка", "нетактовна поведінка", "textbooks:1"),
        ("проявляти недостатки", "виявляти недоліки", "textbooks:1"),
        ("представляти інтерес", "становити інтерес", "textbooks:1"),
    ]
    assert _audit_error_corrections(tmp_path, deck["drills"], evidence) == []
    assert (
        _audit_error_corrections(tmp_path, deck["drills"], evidence, vesum_db=vesum_path, sources_db=sources_path) == []
    )


def test_one_rows_error_with_another_rows_correction_fails(tmp_path: Path):
    """Round 4 probe 1: err_0005's error with err_0004's correction passed — both phrases occur in the source text."""
    deck, evidence, sources_path, vesum_path = _extracted_glazova_deck(tmp_path)
    drills = _by_error(deck)
    probe = _recombined(drills["представляти інтерес"], drills["проявляти недостатки"], "err_probe")

    # CI mode: the committed snapshot binds each drill id to its own pair.
    ci = _audit_error_corrections(tmp_path, [probe], {"err_probe": evidence["err_0003"]})
    assert [(v["item"], v["type"]) for v in ci] == [("err_probe", "EVIDENCE_SNAPSHOT_MISMATCH")]

    # Database mode: even a snapshot forged to agree, over real spans of the real row,
    # fails — the extractor never pairs those two cells.
    forged = {"err_probe": _forged_entry(probe, evidence, "err_0003")}
    db = _audit_error_corrections(tmp_path, [probe], forged, vesum_db=vesum_path, sources_db=sources_path)
    assert [(v["item"], v["type"]) for v in db] == [("err_probe", "SOURCE_PAIR_NOT_DERIVED")]


def test_a_marked_error_word_does_not_license_an_unrelated_replacement(tmp_path: Path):
    """Round 4 probe 2: «проявляти недостатки → становити інтерес» passed without a source row.

    VESUM marks «недостатки» as an error, and that one word accepted the whole edit.
    """
    deck, evidence, sources_path, vesum_path = _extracted_glazova_deck(tmp_path)
    genuine = _by_error(deck)["проявляти недостатки"]
    unbound = _drill("err_unbound", "проявляти недостатки", "становити інтерес")
    del unbound["sourceRef"]
    borrowed = {**unbound, "id": "err_borrowed", "sourceRef": genuine["sourceRef"]}
    snapshot = {"err_borrowed": evidence["err_0002"]}

    for mode in ({}, {"vesum_db": vesum_path, "sources_db": sources_path}):
        violations = _audit_error_corrections(tmp_path, [unbound, borrowed], snapshot, **mode)
        assert sorted((v["item"], v["type"]) for v in violations) == [
            ("err_borrowed", "EVIDENCE_SNAPSHOT_MISMATCH"),
            ("err_unbound", "MISSING_SOURCE_REF"),
        ]

    # A snapshot forged to agree: the row reads «виявляти недоліки» at the correction span.
    forged = {"err_borrowed": _forged_entry(borrowed, evidence, "err_0002")}
    violations = _audit_error_corrections(tmp_path, [borrowed], forged, vesum_db=vesum_path, sources_db=sources_path)
    assert [(v["item"], v["type"]) for v in violations] == [("err_borrowed", "SOURCE_SPAN_MISMATCH")]


def test_fabricated_source_binding_fails_without_sources_db(tmp_path: Path):
    """Round 4 CI hole: a fabricated `sourceRow` passed when sources.db was absent."""
    legacy = _drill("err_legacy_row", "брати участь", "купити участь", sourceRow="брати участь купити участь")
    del legacy["sourceRef"]
    fabricated = _drill("err_fabricated_ref", "брати участь", "купити участь")
    fabricated["sourceRef"]["rowId"] = "textbooks:999999"
    reversed_ref = _drill("err_reversed", "приймати участь", "брати участь")
    reversed_ref["sourceRef"]["direction"] = "correct_first"
    # The edit replaces one occurrence of the bound error span; a repeated error is ambiguous.
    repeated = _drill("err_repeated", "приймати участь", "брати участь")
    repeated["sentence"] = "«приймати участь» чи «приймати участь»?"
    snapshot = {
        "err_reversed": {"rowId": "textbooks:1", "error": "приймати участь", "correct": "брати участь"},
        "err_repeated": {"rowId": "textbooks:1", "error": "приймати участь", "correct": "брати участь"},
    }

    violations = _audit_error_corrections(tmp_path, [legacy, fabricated, reversed_ref, repeated], snapshot)
    assert sorted((v["item"], v["type"]) for v in violations) == [
        ("err_fabricated_ref", "EVIDENCE_SNAPSHOT_MISSING"),
        ("err_legacy_row", "MISSING_SOURCE_REF"),
        ("err_repeated", "ERROR_TARGET_AMBIGUOUS"),
        ("err_reversed", "MISSING_SOURCE_REF"),
    ]


def test_database_mode_reverifies_the_snapshot(tmp_path: Path):
    """With sources.db a snapshot entry must name a real row whose text still hashes to it."""
    deck, evidence, sources_path, vesum_path = _extracted_glazova_deck(tmp_path)
    drill = _by_error(deck)["проявляти недостатки"]
    missing_row = {**drill, "id": "err_missing_row", "sourceRef": {**drill["sourceRef"], "rowId": "textbooks:999"}}
    changed = {**drill, "id": "err_changed"}
    snapshot = {
        "err_missing_row": {**evidence["err_0002"], "rowId": "textbooks:999"},
        "err_changed": {**evidence["err_0002"], "rowSha256": "f" * 64},
    }
    violations = _audit_error_corrections(
        tmp_path, [missing_row, changed], snapshot, vesum_db=vesum_path, sources_db=sources_path
    )
    assert sorted((v["item"], v["type"]) for v in violations) == [
        ("err_changed", "SOURCE_ROW_CHANGED"),
        ("err_missing_row", "SOURCE_ROW_MISSING"),
    ]


@pytest.mark.skipif(not DEFAULT_SOURCES_DB.exists(), reason="Requires the local sources.db")
def test_reviewer_probe_on_the_committed_deck_and_real_sources_db(tmp_path: Path):
    """The exact round 4 probe: committed err_0005's error with err_0004's correction, snapshot forged to agree."""
    from scripts.audit.practice_quality_gate import PROJECT_ROOT
    from scripts.practice.extract_textbook_error_corrections import load_evidence_snapshot

    deck = json.loads((PROJECT_ROOT / "site/src/data/practice-error-corrections.json").read_text(encoding="utf-8"))
    evidence = load_evidence_snapshot()
    drills = {d["id"]: d for d in deck["drills"]}
    assert (drills["err_0004"]["errorWord"], drills["err_0005"]["errorWord"]) == (
        "проявляти недостатки",
        "представляти інтерес",
    )
    probe = _recombined(drills["err_0005"], drills["err_0004"], "err_0005")
    violations = _audit_error_corrections(
        tmp_path, [probe], {"err_0005": _forged_entry(probe, evidence, "err_0005")}, sources_db=DEFAULT_SOURCES_DB
    )
    assert [(v["item"], v["type"]) for v in violations] == [("err_0005", "SOURCE_PAIR_NOT_DERIVED")]


def test_audit_error_correction_checks_typed_answers(tmp_path: Path):
    """#8723 round 3 probe: an error added to `answers` still passed; the site accepts every answer."""
    vesum_path = _fixture_vesum(tmp_path, [*_PARTICIPATION_FORMS, ("узяти", "verb")])
    good = ["брати (узяти) участь", "брати участь", "узяти участь"]
    drills = [
        _drill("err_accepts_error", "приймати участь", "брати участь", answers=["брати участь", "Приймати  участь."]),
        _drill("err_omits_correction", "приймати участь", "брати участь", answers=["участь"]),
        _drill("err_foreign_answer", "приймати участь", "брати участь", answers=["брати участь", "купити участь"]),
        _drill("err_good", "приймати участь", "брати (узяти) участь", answers=good),
        _drill("err_default", "приймати участь", "брати участь"),
    ]
    violations = _audit_error_corrections(tmp_path, drills, vesum_db=vesum_path)
    assert sorted((v["item"], v["type"]) for v in violations) == [
        ("err_accepts_error", "ANSWERS_ACCEPT_ERROR"),
        ("err_accepts_error", "ANSWER_NOT_A_SOURCE_READING"),
        ("err_foreign_answer", "ANSWER_NOT_A_SOURCE_READING"),
        ("err_omits_correction", "ANSWERS_OMIT_CORRECTION"),
        ("err_omits_correction", "ANSWER_NOT_A_SOURCE_READING"),
    ]


def test_production_culture_deck_passes_error_correction_gate():
    """The bundled Culture-of-Speech deck is what learners play; audit it directly."""
    from scripts.audit.practice_quality_gate import DEFAULT_VESUM_DB, PROJECT_ROOT

    vesum_db = DEFAULT_VESUM_DB if Path(DEFAULT_VESUM_DB).exists() else None
    violations = audit_error_correction_deck(
        PROJECT_ROOT / "site/src/data/practice-error-corrections.json", vesum_db=vesum_db
    )
    assert violations == []


def test_audit_practice_shards_volume_thresholds(tmp_path: Path):
    """Verify that thin-mode volume thresholds (paronym>=250, homonym>=150, heritage>=250) are enforced."""
    # Under-threshold paronym shard (only 2 items)
    paronym_data = {
        "paronym": [
            {
                "paronymId": f"par_{i}",
                "prompt": "Сьогодні він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Бігти vs бігати.",
            }
            for i in range(2)
        ]
    }
    shard_file = tmp_path / "practice-paronym.A1.json"
    shard_file.write_text(json.dumps(paronym_data, ensure_ascii=False), encoding="utf-8")

    counts, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=True, verify_vesum=False, modes=["paronym"]
    )
    assert counts["paronym"] == 2
    assert any(v["type"] == "VOLUME_BELOW_THRESHOLD" and v["item"] == "paronym" for v in violations)


def test_audit_practice_shards_blank_syntax(tmp_path: Path):
    """Verify that fill-in blank modes must contain exactly 1 blank (___)."""
    shard_data = {
        "paronym": [
            {
                "paronymId": "p_bad_no_blank",
                "prompt": "Він бігає у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Різниця значень.",
            },
            {
                "paronymId": "p_bad_two_blanks",
                "prompt": "Він ___ у парку і ___ на стадіоні.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Різниця значень.",
            },
            {
                "paronymId": "p_good",
                "prompt": "Він ___ у парку щоранку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Різниця значень.",
            },
        ]
    }
    shard_file = tmp_path / "practice-paronym.A1.json"
    shard_file.write_text(json.dumps(shard_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    bad_items = [v["item"] for v in violations if v["type"] == "INVALID_BLANK_COUNT"]
    assert any("p_bad_no_blank" in item for item in bad_items)
    assert any("p_bad_two_blanks" in item for item in bad_items)
    assert not any("p_good" in item for item in bad_items)


def test_audit_practice_shards_options_and_homonym_rule(tmp_path: Path):
    """Verify option count >= 2, no duplicates (except homonym mode where forms are homonymous)."""
    # Paronym with duplicate options -> violation
    par_data = {
        "paronym": [
            {
                "paronymId": "p_dup",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "бігає"}],
                "distinction_gloss_uk": "Різниця значень.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    # Homonym with homonymous options -> allowed
    hom_data = {
        "homonym": [
            {
                "homonymId": "h_ok",
                "prompt": "Старенька ___ спекла пиріг.",
                "answer": "баба",
                "options": [{"label": "баба"}, {"label": "баба"}],
                "distinction_gloss_uk": "Омоніми баба.",
            }
        ]
    }
    (tmp_path / "practice-homonym.A1.json").write_text(json.dumps(hom_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym", "homonym"]
    )
    assert any(v["type"] == "DUPLICATE_OPTIONS" and "p_dup" in v["item"] for v in violations)
    assert not any("h_ok" in v["item"] for v in violations)


def test_audit_practice_shards_target_in_options(tmp_path: Path):
    """Verify target answer must be present in options list."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_missing_ans",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "гуляє"}, {"label": "сидить"}],
                "distinction_gloss_uk": "Різниця значень.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "ANSWER_NOT_IN_OPTIONS" and "p_missing_ans" in v["item"] for v in violations)


def test_audit_practice_shards_metadata_required(tmp_path: Path):
    """Verify that pedagogical explanation metadata is required."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_no_meta",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MISSING_EXPLANATION" and "p_no_meta" in v["item"] for v in violations)


def test_audit_practice_shards_vesum_attestation(tmp_path: Path, monkeypatch):
    """Verify that target answers not attested in VESUM trigger VESUM_UNATTESTED."""
    from scripts.audit import practice_quality_gate

    par_data = {
        "paronym": [
            {
                "paronymId": "p_unattested",
                "prompt": "Він ___ у парку.",
                "answer": "неіснуючеслово",
                "options": [{"label": "неіснуючеслово"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    def mock_verify(word: str, db_path=None):
        return False

    monkeypatch.setattr(practice_quality_gate, "verify_word", mock_verify)
    fake_db = tmp_path / "mock_vesum.db"
    fake_db.touch()

    _, violations = audit_practice_shards(
        shards_dir=tmp_path,
        vesum_db=fake_db,
        check_volume=False,
        verify_vesum=True,
        modes=["paronym"],
    )
    assert any(v["type"] == "VESUM_UNATTESTED" and "p_unattested" in v["item"] for v in violations)


def test_audit_card_ambiguity_mocked(tmp_path: Path):
    """Verify audit_card_ambiguity with mock TypeSafe System One responses."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_test",
                "prompt": "Вранці він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    mock_resp = {
        "model": "mock-jev",
        "answers": {
            "distractor_plausibility": {"score": 1.8, "confidence": 0.95},
            "is_unambiguous": {"noul": 0.92},
            "anti_calque_yield": {"noul": 0.10},
            "card_quality": {"choice": "pass", "confidence": 0.95},
        },
    }

    verdicts, violations = audit_card_ambiguity(
        shards_dir=tmp_path,
        sample_size=1,
        mock_response=mock_resp,
        strict_ambiguity=True,
    )
    assert len(verdicts) == 1
    assert verdicts[0]["verdict"] == "pass"
    assert len(violations) == 0


def test_audit_practice_shards_missing_vesum_db_fails_closed(tmp_path: Path):
    """Finding 3: missing VESUM database must fail closed with VESUM_DB_MISSING violation."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_1",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    nonexistent_db = tmp_path / "nonexistent_vesum.db"
    _, violations = audit_practice_shards(
        shards_dir=tmp_path,
        vesum_db=nonexistent_db,
        check_volume=False,
        verify_vesum=True,
        modes=["paronym"],
    )
    assert any(v["type"] == "VESUM_DB_MISSING" for v in violations)


def test_audit_practice_shards_requires_prompt_and_options(tmp_path: Path):
    """Finding 2: required card fields (prompt, options) and answer count must be enforced."""
    # Card missing prompt
    bad_prompt_data = {
        "paronym": [
            {
                "paronymId": "p_no_prompt",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(
        json.dumps(bad_prompt_data, ensure_ascii=False), encoding="utf-8"
    )

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MISSING_PROMPT" and "p_no_prompt" in v["item"] for v in violations)

    # Card missing options list
    bad_opt_data = {
        "paronym": [
            {
                "paronymId": "p_no_opts",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(bad_opt_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MISSING_OPTIONS" and "p_no_opts" in v["item"] for v in violations)

    # Card with marked options but zero correct answers
    zero_ans_data = {
        "cloze": [
            {
                "clozeId": "c_zero_ans",
                "sentence": "Це гарне _____ речення.",
                "form": "гарне",
                "options": [
                    {"label": "гарне", "kind": "distractor"},
                    {"label": "погане", "kind": "distractor"},
                ],
                "caseRule": "правило",
            }
        ]
    }
    (tmp_path / "practice-cloze.A1.json").write_text(json.dumps(zero_ans_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["cloze"])
    assert any(v["type"] == "WRONG_ANSWER_COUNT" and "c_zero_ans" in v["item"] for v in violations)


def test_audit_card_ambiguity_offline_strict_fails(tmp_path: Path, monkeypatch):
    """Finding 1: offline ambiguity validation in strict mode must report unavailable and not fabricate a pass."""
    from scripts.practice import typesafe_distractor_validator

    par_data = {
        "paronym": [
            {
                "paronymId": "p_test",
                "prompt": "Вранці він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    mock_vesum = tmp_path / "mock_vesum.db"
    mock_vesum.touch()

    monkeypatch.setattr(typesafe_distractor_validator, "resolve_api_key", lambda: None)
    monkeypatch.setattr(
        typesafe_distractor_validator,
        "ground_with_sources",
        lambda target, distractors, vesum_db_path=None: {
            "target": {"in_vesum": True},
            "distractors": {d: {"in_vesum": True} for d in distractors},
        },
    )

    verdicts, violations = audit_card_ambiguity(
        shards_dir=tmp_path,
        sample_size=1,
        vesum_db=mock_vesum,
        mock_response=None,
        strict_ambiguity=True,
        client=None,
    )
    assert len(verdicts) == 1
    assert verdicts[0]["verdict"] == "unverified_offline"
    assert verdicts[0]["model"] == "deterministic-vesum-grounding"
    assert verdicts[0]["unambiguous_prob"] is None
    assert any("morphological attestation verified via VESUM" in f for f in verdicts[0]["findings"])
    assert any(v["type"] == "AMBIGUITY_VALIDATION_UNAVAILABLE" for v in violations)


def test_audit_card_ambiguity_missing_vesum_reports_unavailable(tmp_path: Path, monkeypatch):
    """P2 regression: missing VESUM database must report morphological verification as unavailable."""
    from scripts.practice import typesafe_distractor_validator

    par_data = {
        "paronym": [
            {
                "paronymId": "p_test",
                "prompt": "Вранці він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(typesafe_distractor_validator, "resolve_api_key", lambda: None)

    nonexistent_db = tmp_path / "nonexistent.db"
    assert not nonexistent_db.exists()

    verdicts, violations = audit_card_ambiguity(
        shards_dir=tmp_path,
        sample_size=1,
        vesum_db=nonexistent_db,
        mock_response=None,
        strict_ambiguity=False,
        client=None,
    )
    assert len(verdicts) == 1
    v = verdicts[0]
    assert v["verdict"] == "unverified_offline"
    assert v["model"] == "unavailable"
    assert any("morphological verification unavailable" in f.lower() for f in v["findings"])
    assert not any("verified via vesum" in f.lower() for f in v["findings"])
    assert violations == []


def test_audit_card_ambiguity_honors_sample_size(tmp_path: Path):
    """Finding 4: candidate sampling must collect requested sample_size cards across modes."""
    par_data = {
        "paronym": [
            {
                "paronymId": f"p_{i}",
                "prompt": f"Він ___ у парку {i}.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
            }
            for i in range(10)
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    mock_resp = {
        "model": "mock-jev",
        "answers": {
            "distractor_plausibility": {"score": 1.8, "confidence": 0.95},
            "is_unambiguous": {"noul": 0.92},
            "anti_calque_yield": {"noul": 0.10},
            "card_quality": {"choice": "pass", "confidence": 0.95},
        },
    }

    verdicts, violations = audit_card_ambiguity(
        shards_dir=tmp_path,
        sample_size=8,
        mock_response=mock_resp,
        strict_ambiguity=False,
    )
    assert len(verdicts) == 8
    assert len(violations) == 0


def test_audit_practice_shards_marked_answer_must_match_target(tmp_path: Path):
    """R2 Finding 1: Option marked as answer must match target form or accepted answers."""
    mismatched_card_data = {
        "paronym": [
            {
                "paronymId": "p_mismatched",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [
                    {"label": "бігає", "kind": "distractor"},
                    {"label": "біжить", "kind": "answer"},
                ],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(
        json.dumps(mismatched_card_data, ensure_ascii=False), encoding="utf-8"
    )

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MARKED_ANSWER_MISMATCH" and "p_mismatched" in v["item"] for v in violations)


def test_audit_practice_shards_empty_option_label_fails(tmp_path: Path):
    """R2 Finding 2: Missing, empty, or whitespace-only option labels must be rejected."""
    empty_label_data = {
        "paronym": [
            {
                "paronymId": "p_empty_label",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [
                    {"label": "бігає"},
                    {"label": "   "},
                ],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(
        json.dumps(empty_label_data, ensure_ascii=False), encoding="utf-8"
    )

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "EMPTY_OPTION_LABEL" and "p_empty_label" in v["item"] for v in violations)


def test_production_practice_quality_gate_passes():
    """Verify that current repository practice datasets pass with 0 violations."""
    results = run_all_practice_audits()
    total_violations = sum(len(v) for v in results.values())
    assert total_violations == 0, f"Practice Quality Gate failed with violations: {results}"


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or not Path("site/public/lexicon/practice-index.A1.json").exists(),
    reason="Requires local data/vesum.db and generated practice shards in site/public/lexicon/",
)
def test_production_practice_shards_all_modes_gate_passes():
    """Verify that all practice shards across all modes satisfy volume thresholds and linguistic gates."""
    results = run_all_practice_audits(all_modes=True, verify_vesum=True)
    total_violations = sum(len(v) for v in results.values())
    assert total_violations == 0, f"Practice Shards Quality Gate failed with violations: {results}"

    # Assert volume thresholds
    assert results.shard_counts.get("paronym", 0) >= VOLUME_THRESHOLDS["paronym"]
    assert results.shard_counts.get("homonym", 0) >= VOLUME_THRESHOLDS["homonym"]
    assert results.shard_counts.get("heritage", 0) >= VOLUME_THRESHOLDS["heritage"]


def test_audit_error_correction_flags_reviewed_withheld_pairs(tmp_path: Path):
    """#8723 language review: a withheld pair must not return with a regenerated deck."""
    drills = [
        _drill("err_contested", "відпочивати на морі", "відпочивати біля моря"),
        _drill("err_good", "влучний вираз", "влучний вислів"),
    ]
    violations = _audit_error_corrections(tmp_path, drills)
    assert [(v["type"], v["item"]) for v in violations] == [("REVIEWED_WITHHELD_PAIR", "err_contested")]
