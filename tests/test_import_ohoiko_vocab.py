"""Tests for the Ohoiko/Oho!/ULP lexdata L1 parsers (design r3 §10 (a)/(b), OO-38).

Covers ``scripts/lexicon/import_ohoiko_vocab.py``, ``ulp_glossary_parse.py`` and
``oho_workbook_glossary_parse.py``: L1 record conservation, no L0 write
(read-only handle, selection digest and file bytes unchanged), an exact no-op
rerun (parser digests and a two-build ``build_store`` reuse), raw provenance
and the §7.2 input classes that apply at L1.

Every fixture is SYNTHETIC: invented entries laid out like the books, the
workbook and the lesson notes, including their OCR damage (an acute printed
on the next line, a headword wrapped beside the gloss column). No Ohoiko or ULP text is committed. Stress
marks were checked with the sources MCP stress oracle (``verify_stresses``).
Lives outside ``tests/lexicon/``, which skips in sparse worktrees.
"""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.lexdata import build_store, transforms
from scripts.lexdata import records as rec
from scripts.lexicon import import_ohoiko_vocab as imp
from scripts.lexicon import oho_workbook_glossary_parse as oho
from scripts.lexicon import ulp_glossary_parse as gp
from scripts.lexicon.ohoiko_quality_enrichment import (
    extract_1000_words_example,
    iter_1000_words_examples,
    normalize_chunk_lines,
)
from scripts.storage import topology

WORDS = "anna-ohoiko-1000-words-2nd-ed"
VERBS = "anna-ohoiko-500-verbs"
ULP6 = "ulp-6-00-lesson-notes"
ULP1 = "ulp-1-00-lesson-notes"
LATIN_A = "a"
LATIN_C = "C"

WORD_CHUNKS = {
    1: "1. ключ  1) key; 2) clue\nДе мій ключ?                       Where is my key?\n",
    2: "2. ха́та = буди́нок (2)  1) house; 2) building\nЦя ха́та ду́же стара́.              This house is very old.\n",
    3: (
        "3. чита́ти, прочита́ти  to read\n"
        "(imperfective, perfective)\n"
        "Учо́ра я прочита́в ціка́ву           Yesterday I read an interesting\n"
        "кни́жку.                             book.\n"
        "Учо́ра я прочита́в листа́.           Yesterday I read a letter.\n"
    ),
    4: "4. бу́ ти, побу́ ти  to be (imperfective, perfective)\n",
    5: "5. робота  work\n",  # printed without stress: accepted, stress absent
    6: f"6. ха́т{LATIN_A}  hut\n",  # Latin homoglyph: refused homoglyph_mixed_script
    # OCR put the acute and the word's tail on the next line, after a vowel and after a consonant.
    7: "7. ха\ń та  hut\n",
    8: "8. проєк\ń т = за́дум  project\n",
    # The headword wraps beside the gloss column.
    9: "9. сло́во = вислів =  word, expression\nте́рмін\n",
}

VERB_PAGE = "\n".join([
    "писа́ти | написа́ти                                Present / Future Stems: пиш- | напиш-",
    "to write                                                     Conjugation: 1st (-уть)",
    "      ОСОБА                НЕДОКОНАНИЙ ВИД                                 ДОКОНАНИЙ ВИД",
    "                       ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE",
    " я                   пишу́",
    " ти                  пи́шеш",
    "                       МИНУЛИЙ ЧАС ― PAST TENSE",
    " він (я, ти)         писа́в                                          написа́в",
    "                       НАКАЗОВИЙ СПОСІБ ― IMPERATIVE MOOD",
    " ти                  пиши́ напиши́",
    "+ accusative:",
    "Я пишу́ листа́.                                 I am writing a letter.",
])

OHO_PAGE = "\n".join([
    "200",
    "Inspiring resources for learning Ukrainian",
    "Back to Contents",
    "Словничок",
    "Vocabulary",
    "    ч.   ",
    "masculine gender",
    "Скорочення",
    "Abbreviations",
    "студе́нт, ч., студе́нтка, ж., student",
    "шу́ба, ж., fur coat",
    "жи́ти (я живу́), недок., to live",
    "(I live)",
    "Бува́й!, Bye!",
    f"{LATIN_C}паси́бі, thank you",
    "вікно́, с., window",
    "",
    "Урок 02",
    "Урок 01",
])
OHO_OTHER_PAGE = "199\nInspiring resources for learning Ukrainian\nBack to Contents\nВідповіді\nAnswer Key\n1\n"

ULP6_LESSON = "\n".join([
    "Lesson 201: Синтетичний урок",
    "",
    "                                                Словничок",
    "",
    "   ха́та                                          house",
    "   сло́во                                         word",
    "",
    "                              Синтетичний урок",
    "",
    "Це звичайний текст уроку без наголосів.                                           те́ма ― topic",
    "Ще одне речення про заняття тут.                                                  заня́ття ― lesson,",
    "Третє речення уроку.                                                              class",
    "",
    "                              Словничок (з прикладами)",
    "",
    "чита́ти, прочита́ти                                           to read",
    "                                                              (imperfective, perfective)",
    "  • Учо́ра я прочита́в ціка́ву кни́жку.                        • Yesterday I read an interesting book.",
    "",
    "ха́та                                                         house",
    "  • Ця ха́та ду́же стара́.                                     • This house is very old.",
    "",
    "                                                          Вправи",
    "   Перекладіть українською мовою слова зі словника.",
])
ULP1_LESSON = "\n".join([
    "Lesson 1: Synthetic lesson",
    "",
    "                                           Key Vocabulary 1-01",
    "              сло́во                                           word",
    "              уро́к                                            lesson",
    "              до́бре                                           well, fine (adverb)",
    "              робота і навчання                                work and study",
])


def make_sources(path: Path) -> Path:
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript(
            """
            CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT, source_file TEXT);
            CREATE TABLE textbook_sections (section_id INTEGER PRIMARY KEY, source_file TEXT, grade INTEGER,
                section_title TEXT, section_number TEXT, chunk_count INTEGER, full_text TEXT);
            """
        )
        for number, text in WORD_CHUNKS.items():
            conn.execute("INSERT INTO textbooks (chunk_id, title, text, source_file) VALUES (?, '', ?, ?)",
                         (f"{WORDS}_e{number:04d}", text, WORDS))
        for number in (1, 2):  # verb 2 has no page: truncated_source
            conn.execute("INSERT INTO textbooks (chunk_id, title, text, source_file) VALUES (?, '', ?, ?)",
                         (f"{VERBS}_e{number:04d}", "\n".join(VERB_PAGE.splitlines()[:2]), VERBS))
        sections = [
            (VERBS, "Verb 1", "1", VERB_PAGE),
            ("owned-oho-a1-workbook", "Reference 200", "200", OHO_OTHER_PAGE),
            ("owned-oho-a1-workbook", "Reference 201", "201", OHO_PAGE),
            (ULP6, "Lesson 201: Синтетичний урок", "201", ULP6_LESSON),
            (ULP1, "Lesson 1: Synthetic lesson", "1", ULP1_LESSON),
        ]
        for source_file, title, number, text in sections:
            conn.execute("INSERT INTO textbook_sections (source_file, grade, section_title, section_number, "
                         "chunk_count, full_text) VALUES (?, 0, ?, ?, 1, ?)", (source_file, title, number, text))
        conn.commit()
    return path


FIXTURE_UNITS = {imp.WORDS_SOURCE_ID: 9, imp.VERBS_SOURCE_ID: 2, imp.OHO_SOURCE_ID: 1, imp.ULP_SOURCE_ID: 2}


@pytest.fixture
def sources_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # resolve_store refuses stores inside a linked worktree; run from the fixture root.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(imp, "EXPECTED_UNITS", dict(FIXTURE_UNITS))
    return make_sources(tmp_path / "sources.db")


@pytest.fixture
def runs(sources_db: Path) -> dict[str, imp.SourceRun]:
    with closing(sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)) as conn:
        return imp.run_all(conn)


def _unit(runs: dict[str, imp.SourceRun], source: str, suffix: str) -> rec.ParsedUnit:
    return next(u for u in runs[source].units if u.unit.l0_locator.endswith(suffix))


def _leaves(unit: rec.ParsedUnit) -> dict[str, tuple[rec.LexItemRecord, dict]]:
    return {item.local_id: (item, fields)
            for item, fields in zip(unit.ordered_items(), imp.derived_rows(unit), strict=True)}


# --- 1000 words -----------------------------------------------------------


def test_equals_member_is_equivalent_lexeme_with_shared_sense_binding(runs) -> None:
    leaves = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0002"))
    assert [(k, i.role, i.raw_span) for k, (i, _) in leaves.items()] == [
        ("entry", "headword", "ха́та = буди́нок (2)"),
        ("entry.m1", "headword", "ха́та"),
        ("entry.m2", "equivalent_lexeme", "буди́нок"),
    ]
    house, building = leaves["entry.m1"][0], leaves["entry.m2"][0]
    assert [(s.sense_no, s.gloss_raw, s.applies_to) for s in house.senses] == [
        (1, "house", "all_members"), (2, "building", "all_members")]
    assert [(s.sense_no, s.gloss_raw) for s in building.senses] == [(2, "building")]
    assert not leaves["entry"][0].senses  # the shared gloss never sits on one item alone
    assert [(e.uk_raw, e.en_raw) for e in leaves["entry"][0].examples] == [
        ("Ця ха́та ду́же стара́.", "This house is very old.")]


def test_comma_members_are_variants_and_aspect_note_is_grammar(runs) -> None:
    leaves = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0003"))
    assert [(i.role, i.raw_span) for k, (i, _) in leaves.items() if k != "entry"] == [
        ("headword", "чита́ти"), ("variant", "прочита́ти")]
    top = leaves["entry"][0]
    assert top.grammar_raw == "imperfective, perfective"
    assert [(e.uk_raw, e.en_raw) for e in top.examples] == [
        ("Учо́ра я прочита́в ціка́ву кни́жку.", "Yesterday I read an interesting book."),
        ("Учо́ра я прочита́в листа́.", "Yesterday I read a letter."),
    ]
    single = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0001"))["entry"][0]
    assert [(s.gloss_raw, s.applies_to) for s in single.senses] == [("key", "self"), ("clue", "self")]


def test_repairs_are_proposals_and_raw_spans_stay_as_printed(runs) -> None:
    split = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0004"))["entry.m1"]
    assert split[0].raw_span == "бу́ ти" and split[1]["key_stressed"] == "бу́ ти"
    assert [r.as_json() for r in split[0].proposed_repairs] == [
        {"kind": "ocr_split_joined", "proposed": "бу́ти", "proposer": imp.PROPOSER_JOIN}]
    homoglyph = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0006"))["entry"]
    assert homoglyph[0].raw_span == f"ха́т{LATIN_A}"
    assert homoglyph[1]["refusal_code"] == "homoglyph_mixed_script" and homoglyph[1]["key_stressed"] is None
    assert {p["proposed"] for p in json.loads(homoglyph[1]["proposed_repairs"])} == {"ха́та"}


def test_entry_printed_without_stress_is_accepted_with_stress_absent(runs) -> None:
    item, fields = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0005"))["entry"]
    assert (item.raw_span, fields["refusal_code"], fields["key_stressed"], fields["key_fold"]) == (
        "робота", None, "робота", "робота")
    assert item.parser_refusal is None and not item.proposed_repairs
    assert gp.stress_errors("робота") == ["unstressed_polysyllable:робота"]  # a diagnostic, not a refusal


def test_displaced_acute_keeps_the_printed_span_and_only_proposes_the_rejoin(runs) -> None:
    vowel = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0007"))["entry"]
    assert (vowel[0].raw_span, vowel[0].span_start, vowel[0].span_end) == ("ха\ń та", 3, 10)
    assert WORD_CHUNKS[7][3:10] == vowel[0].raw_span  # byte for byte
    assert (vowel[1]["refusal_code"], vowel[1]["key_stressed"]) == ("stress_invalid", None)
    assert json.loads(vowel[1]["proposed_repairs"]) == [
        {"kind": "displaced_acute_rejoined", "proposed": "ха́та", "proposer": imp.PROPOSER_REJOIN}]
    consonant = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0008"))
    assert [(k, i.raw_span, f["refusal_code"]) for k, (i, f) in consonant.items()] == [
        ("entry", "проєк\ń т = за́дум", "stress_invalid"),
        ("entry.m1", "проєк\ń т", "stress_invalid"),
        ("entry.m2", "за́дум", None)]
    assert [(r.kind, r.proposed) for r in consonant["entry.m1"][0].proposed_repairs] == [
        ("displaced_acute_rejoined", "проєќт"),
        ("precomposed_acute_respelled+stress_moved_to_vowel", "проє́кт")]


def test_wrapped_headword_keeps_the_line_break_and_leaves_the_gloss_column_out(runs) -> None:
    leaves = _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0009"))
    assert [(k, i.raw_span) for k, (i, _) in leaves.items()] == [
        ("entry", "сло́во = вислів =\nте́рмін"), ("entry.m1", "сло́во"), ("entry.m2", "вислів"),
        ("entry.m3", "те́рмін")]
    parent = leaves["entry"]
    assert WORD_CHUNKS[9][parent[0].span_start:parent[0].span_end] == "сло́во = вислів =  word, expression\nте́рмін"
    assert parent[1]["key_stressed"] == "сло́во = вислів = те́рмін"  # the normalizer collapses the break
    assert leaves["entry.m2"][1]["refusal_code"] is None  # unstressed member: accepted


def test_locate_span_returns_none_for_text_that_is_not_printed() -> None:
    assert imp.locate_span("1. ха́та  house\n", 3, "буди́нок") is None
    with pytest.raises(imp.ParseFailure, match="raw_span_not_located"):
        imp.entry_items("entry", imp.EntryShape("буди́нок", [imp.Member("буди́нок", "headword")]),
                        join_splits=False, printed=imp.PrintedText("1. ха́та  house\n", 3))


def test_entry_number_mismatch_stops_instead_of_guessing() -> None:
    with pytest.raises(imp.ParseFailure, match="entry_number_mismatch"):
        imp.parse_word_chunk(f"{WORDS}_e0009", "8. вікно́  window\n")


def test_ocr_gloss_tail_truncated_but_accented_english_kept() -> None:
    assert imp.parse_word_chunk(f"{WORDS}_e0001", "1. ха́та  café, house\n").shape.senses == ["café, house"]
    tail = imp.parse_word_chunk(f"{WORDS}_e0002", "2. ха́та  house, houseś ця ха́та?\n")
    assert tail.shape.senses == ["house, houses"] and "gloss_ocr_tail_truncated" in tail.parse_notes


# --- 500 verbs ------------------------------------------------------------


def test_verb_page_pair_stems_table_government_examples(runs) -> None:
    leaves = _leaves(_unit(runs, imp.VERBS_SOURCE_ID, "_e0001"))
    assert [(i.role, i.raw_span) for k, (i, _) in leaves.items() if k != "entry"] == [
        ("headword", "писа́ти"), ("aspect_partner", "написа́ти")]
    top = leaves["entry"][0]
    assert top.grammar_raw == "Conjugation: 1st (-уть)"
    assert [g.pattern_raw for g in top.governments] == ["+ accusative"]
    assert [(e.uk_raw, e.en_raw) for e in top.examples] == [("Я пишу́ листа́.", "I am writing a letter.")]
    assert [(f.aspect, f.tense, f.person_number, f.form_raw) for f in top.verb_forms] == [
        ("imperfective", "present_stem", None, "пиш-"),
        ("perfective", "future_stem", None, "напиш-"),
        ("imperfective", "present", "я", "пишу́"),
        ("imperfective", "present", "ти", "пи́шеш"),
        ("imperfective", "past", "він (я, ти)", "писа́в"),
        ("perfective", "past", "він (я, ти)", "написа́в"),
        ("imperfective", "imperative", "ти", "пиши́"),  # single-space tight row, assigned by count
        ("perfective", "imperative", "ти", "напиши́"),
    ]


def test_verb_without_its_page_is_refused_truncated_source(runs) -> None:
    unit = _unit(runs, imp.VERBS_SOURCE_ID, "_e0002")
    assert (unit.disposition, unit.items) == ("refused:truncated_source", ())
    assert [row.locator.split(":")[1] for row in unit.unit.l0_rows] == ["textbooks"]


def test_table_cells_keep_multiword_cells_and_ocr_splits_together() -> None:
    # Synthetic OCR damage of "пи́шеш": a displaced acute, then a lone acute between two spaces.
    line = " ти        бу́деш писа́ти пишу́, пи́шеш   пиш́ еш   пи ́ шеш"
    cells = imp.table_cells(line, 3)
    assert [line[a:b] for _, a, b in cells] == ["бу́деш писа́ти", "пишу́, пи́шеш", "пиш́ еш", "пи ́ шеш"]
    tail = " він (я, ти)  писа́в [ся]/писа́ла [ся] би [б]"
    assert [tail[a:b] for _, a, b in imp.table_cells(tail, 13)] == ["писа́в [ся]/писа́ла [ся] би [б]"]


# --- Oho! A1 workbook Словничок -----------------------------------------


def test_oho_page_dispositions_members_labels_and_spans(runs) -> None:
    unit = _unit(runs, imp.OHO_SOURCE_ID, "")
    assert [line.disposition for line in unit.lines] == (
        ["page_furniture"] * 5 + ["abbreviation_key"] * 4 + ["entry"] * 3 + ["continuation"]
        + ["entry"] * 3 + ["page_furniture"] + ["lesson_heading"] * 2)
    leaves = _leaves(unit)
    lines = OHO_PAGE.splitlines()
    for item, _ in leaves.values():
        assert lines[item.line_no][item.span_start:item.span_end] == item.raw_span
    pair = [leaves[k][0] for k in ("l9", "l9.m1", "l9.m2")]
    assert [(i.role, i.raw_span, i.grammar_labels) for i in pair] == [
        ("headword", "студе́нт, ч., студе́нтка, ж.", ()), ("headword", "студе́нт", ("ч.",)),
        ("variant", "студе́нтка", ("ж.",))]
    live = leaves["l11"][0]
    assert (live.raw_span, live.grammar_raw, live.grammar_labels) == ("жи́ти", "(я живу́), недок.", ("недок.",))
    assert [s.gloss_raw for s in live.senses] == ["to live (I live)"]  # continuation joined
    assert oho.is_vocabulary_page(OHO_PAGE) and not oho.is_vocabulary_page(OHO_OTHER_PAGE)


def test_oho_rejects_a_line_outside_the_grammar() -> None:
    with pytest.raises(oho.OhoLineError):
        oho.parse_page("1\nbanner\nBack\nСловничок\nVocabulary\nstray English before any entry\n")


# --- ULP lesson notes -----------------------------------------------------


def test_ulp_every_line_has_one_disposition(runs) -> None:
    unit = next(u for u in runs[imp.ULP_SOURCE_ID].units if u.unit.payload["source_file"] == ULP6)
    dispositions = [line.disposition for line in unit.lines]
    assert len(dispositions) == len(ULP6_LESSON.splitlines())
    assert dispositions[0] == "heading" and dispositions[2] == dispositions[13] == "heading"
    assert dispositions[4:6] == ["zone_entry", "zone_entry"]
    assert dispositions[9:12] == ["margin_entry"] * 3
    assert dispositions[7] == dispositions[22] == dispositions[23] == "prose_excluded"
    assert dispositions[1] == "furniture"
    heads = [(i.raw_span, i.line_no) for i in unit.ordered_items() if i.parent is None]
    assert heads == [("ха́та", 4), ("сло́во", 5), ("те́ма", 9), ("заня́ття", 10),
                     ("чита́ти, прочита́ти", 15), ("ха́та", 19)]
    lines = ULP6_LESSON.splitlines()
    for item in unit.items:
        assert lines[item.line_no][item.span_start:item.span_end] == item.raw_span  # line-relative spans
    lesson = next(i for i in unit.items if i.raw_span == "заня́ття")
    assert [s.gloss_raw for s in lesson.senses] == ["lesson, class"]  # wrapped margin gloss joined


def test_unstressed_vocabulary_entry_is_a_zone_entry_and_accepted(runs) -> None:
    unit = next(u for u in runs[imp.ULP_SOURCE_ID].units if u.unit.payload["source_file"] == ULP1)
    assert [line.disposition for line in unit.lines] == ["heading", "furniture", "heading"] + ["zone_entry"] * 4
    item, fields = next((i, f) for i, f in _leaves(unit).values() if i.line_no == 6)
    assert (item.raw_span, fields["refusal_code"], fields["key_stressed"]) == (
        "робота і навчання", None, "робота і навчання")
    # The reviewer's replay: an unstressed multiword entry right under the zone heading.
    zone = "Lesson synthetic\n      Словничок\n      робота і навчання                    work and study\n"
    parsed = gp.parse_lesson(zone)
    assert [e.headword_raw for e in parsed.entries] == ["робота і навчання"]
    assert gp.line_dispositions(zone.splitlines(), parsed) == ["heading", "heading", "zone_entry"]


def _zone(*body: str) -> list[str]:
    return ["Lesson 3: Title", "", f"{'':40}Key Vocabulary 3-01", *body]


def test_zone_ends_at_layout_headings_never_at_a_missing_stress_mark() -> None:
    lines = _zone(
        f"{'':14}{'кáфедра':49}department",  # Latin á: no U+0301 anywhere, still an entry
        f"{'':14}{'Генеральна рада':49}General Council",
        "",
        f"{'':19}Title",  # the lesson title repeated as a running page head
        "",
        f"{'':14}{'сло́во':49}word",  # the zone goes on after a running page header
        "",
        f"{'':40}Відповіді на вправи",
        f"{'':14}{'1. так':49}yes",  # an answer key laid out like an entry: not a zone line
    )
    assert gp.find_vocab_sections(lines) == [("Key Vocabulary 3-01", 3, 10)]
    assert [e.headword_raw for e in gp.parse_lesson("\n".join(lines)).entries] == [
        "кáфедра", "Генеральна рада", "сло́во"]
    english = _zone(f"{'':14}{'ха́та':49}house", f"{'':12}Bonus Exercises 1-20{'':40}3", "1.   їсти   B. to eat")
    assert gp.find_vocab_sections(english) == [("Key Vocabulary 3-01", 3, 4)]


def test_zone_rejoins_a_displaced_acute_into_one_entry() -> None:
    lines = _zone(f"{'':14}{'Ду́же приє́мно!':49}Nice to meet you!", f"{'':14}Взаєм",
                  f"{'':18}́ но!{'':40}Me too!")
    entries = gp.parse_lesson("\n".join(lines)).entries
    assert [(e.headword_raw, e.english_gloss, e.line_indices) for e in entries] == [
        ("Ду́же приє́мно!", "Nice to meet you!", [3]), ("Взаєм́но!", "Me too!", [4, 5])]


def test_margin_cells_tables_wraps_and_fragments() -> None:
    prose = f"{'Текст уроку.':<60}"
    lines = [
        "Lesson 4: Title",
        f"{'писа́ти':<30}{'вони пи́шуть':<30}Пиши́! — Write!",  # a table row: only the last cell
        "",
        f"{prose}на відмі́ну від",  # a head wrapped mid-phrase
        f"{prose}(+ родовий відмінок) — unlike",
        "",
        f"{prose}підприєм",  # a displaced acute in the margin
        f"{prose}́ ець — entrepreneur",
        "",
        f"{prose}Є) Її звати Марина. А це — (його, її)",  # an exercise item
        "",
        f"{prose}ліворуч — informal).",  # the tail of a parenthetical
        "",
        f"{prose}приє́днуватися,     приєдна́тися      ―   to   join",  # justified text keeps its words
    ]
    entries, _, _ = gp.parse_margin_glosses(lines, [])
    kept = [(e.line_index, e.headword_raw, e.english_gloss) for e in entries if not e.errors]
    assert kept == [(1, "Пиши́!", "Write!"), (3, "на відмі́ну від (+ родовий відмінок)", "unlike"),
                    (6, "підприєм́ець", "entrepreneur"), (13, "приє́днуватися, приєдна́тися", "to join")]
    assert [(e.line_index, e.errors) for e in entries if e.errors] == [
        (9, ["exercise_item"]), (11, ["margin_fragment"])]


def test_margin_prose_with_a_long_head_is_excluded_not_emitted() -> None:
    long_head = " ".join(["слово"] * 11)
    lines = ["Lesson 2: Title", f"{'Текст.':<60}{long_head} — words"]
    parse = gp.parse_lesson("\n".join(lines))
    assert parse.entries[0].errors == ["margin_head_too_long"]
    assert gp.line_dispositions(lines, parse) == ["heading", "prose_excluded"]


def test_margin_run_with_two_glosses_is_split() -> None:
    lines = [f"{'Текст уроку без наголосів тут.':<60}ха́та — house сло́во — word"]
    entries, non_gloss, _ = gp.parse_margin_glosses(lines, [])
    assert [(e.forms[0].raw, e.english_gloss) for e in entries] == [("ха́та", "house"), ("сло́во", "word")]
    assert non_gloss == 0


# --- conservation, no L0 write, no-op rerun, provenance -------------------


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_conservation_and_refusals_by_code(runs) -> None:
    report = imp.build_report(runs)
    assert report["ok"] is True
    for source, expected in FIXTURE_UNITS.items():
        entry = report["sources"][source]
        assert entry["units"] == expected
        assert all(v for k, v in entry["conservation"].items() if k != "lines")
    assert report["sources"][imp.OHO_SOURCE_ID]["conservation"]["lines"] == len(OHO_PAGE.splitlines())
    assert report["refusals_by_code"] == {"homoglyph_mixed_script": 2, "refused:truncated_source": 1,
                                          "stress_invalid": 3}
    # ключ (a monosyllable), робота, вислів
    assert report["sources"][imp.WORDS_SOURCE_ID]["leaves_accepted_without_stress_mark"] == 3


def test_no_l0_write_and_exact_noop_rerun(sources_db: Path) -> None:
    before = _sha(sources_db)
    reports = []
    for _ in range(2):
        with closing(sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)) as conn:
            runs = imp.run_all(conn)
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                conn.execute("CREATE TABLE probe (x)")
        reports.append(imp.build_report(runs))
        assert all(run.snapshot_before == run.snapshot_after for run in runs.values())
    assert _sha(sources_db) == before
    assert reports[0]["digest"] == reports[1]["digest"]
    assert {s: r["snapshot"] for s, r in reports[0]["sources"].items()} == {
        s: r["snapshot"] for s, r in reports[1]["sources"].items()}


def test_build_store_generation_twice_reuses_every_unit(sources_db: Path, tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "data").mkdir()
    target = build_store.writer_target(test_data_dir=root / "data")
    # verify enforces each source's denominator; bind the fixture's.
    binding = transforms.TransformBinding(sources={
        s: replace(spec, expected_units=FIXTURE_UNITS[s]) for s, spec in transforms.OHOIKO_SOURCES.items()})
    stores = {"sources": topology.StoreBinding("sources", sources_db)}
    before = _sha(sources_db)
    no_budget = build_store.Admission(peak_budget_bytes=0, reserve_bytes=0)
    first = build_store.build(target, binding=binding, stores=stores, repository_root=root, admission=no_budget)
    assert first.verify_receipt["ok"] is True
    with closing(sqlite3.connect(f"file:{first.published}?mode=ro", uri=True)) as conn:
        rows_first = conn.execute("SELECT * FROM l1_lex_item ORDER BY item_id").fetchall()
        lines = conn.execute("SELECT u.l0_locator, l.line_no, l.raw_line_sha256 FROM l1_line l "
                             "JOIN l1_source_unit u USING (unit_id) WHERE u.source_id = ?",
                             (imp.OHO_SOURCE_ID,)).fetchall()
    assert [sha for _, _, sha in sorted(lines, key=lambda r: r[1])] == [
        hashlib.sha256(line.encode()).hexdigest() for line in OHO_PAGE.splitlines()]
    second = build_store.build(target, binding=binding, stores=stores, repository_root=root, admission=no_budget)
    assert {s: (d["reused_units"], d["reparsed_units"]) for s, d in second.diff["sources"].items()} == {
        s: (n, 0) for s, n in FIXTURE_UNITS.items()}
    with closing(sqlite3.connect(f"file:{second.published}?mode=ro", uri=True)) as conn:
        assert conn.execute("SELECT * FROM l1_lex_item ORDER BY item_id").fetchall() == rows_first
    assert _sha(sources_db) == before


def _printed(text: str, item: rec.LexItemRecord) -> str:
    """The source region an item's span covers (its offsets count from line ``line_no`` when set)."""
    origin = sum(len(line) for line in text.splitlines(keepends=True)[:item.line_no or 0])
    return text[origin + item.span_start:origin + item.span_end]


def test_raw_spans_are_verbatim_source_text(runs) -> None:
    """Each raw span is its printed region, byte for byte; a wrapped one keeps its line break."""
    texts = {f"_e{n:04d}": t for n, t in WORD_CHUNKS.items()}
    checked = 0
    for source in imp.SOURCE_IDS:
        for unit in runs[source].units:
            payload = unit.unit.payload
            if not unit.items:
                continue  # refused truncated_source: nothing printed to check
            text = (texts[unit.unit.l0_locator[-6:]] if source == imp.WORDS_SOURCE_ID
                    else payload["pages"][0]["full_text"] if source == imp.VERBS_SOURCE_ID
                    else payload["full_text"])
            if "full_text" in payload:
                assert [line.raw_line for line in unit.lines] == text.splitlines()
            for item in unit.items:
                region = _printed(text, item)
                fragments = item.raw_span.split("\n")
                assert region.startswith(fragments[0]) and region.endswith(fragments[-1]), item.raw_span
                assert all(fragment in region for fragment in fragments), item.raw_span
                assert len(fragments) > 1 or region == item.raw_span, item.raw_span
                checked += 1
    assert checked == sum(len(u.items) for run in runs.values() for u in run.units) > 30


def test_l1_input_classes(runs) -> None:
    """§7.2 classes that are decided at L1 (the rest belong to the slice (e) resolver)."""
    oho_leaves = _leaves(_unit(runs, imp.OHO_SOURCE_ID, ""))
    initial_cap = oho_leaves["l13"][1]  # sentence-initial capital: a case signal, not a proper name
    assert (initial_cap["key_stressed"], initial_cap["case_signal"]) == ("Бува́й", "initial_cap")
    lower = oho_leaves["l10"][1]
    assert (lower["key_fold"], lower["case_signal"]) == ("шуба", "lower")
    mixed = oho_leaves["l14"][1]
    assert mixed["refusal_code"] == "homoglyph_mixed_script"
    assert {p["kind"] for p in json.loads(mixed["proposed_repairs"])} >= {"latin_lookalike"}
    unmapped = json.loads(oho_leaves["l11"][1]["grammar_parsed"])
    assert unmapped["unmapped"] == ["недок."]
    gender = json.loads(oho_leaves["l9.m2"][1]["grammar_parsed"])
    assert gender["fields"] == {"gender": "feminine", "pos": "noun"}
    roles = {i.role for i, _ in _leaves(_unit(runs, imp.WORDS_SOURCE_ID, "_e0002")).values()}
    assert "equivalent_lexeme" in roles  # an = pair
    assert all(i.parent == "l9" for k, (i, _) in oho_leaves.items() if k.startswith("l9.m"))  # a list


# --- registry, samples, CLI ----------------------------------------------


def test_parsers_are_registered_and_their_imports_closed() -> None:
    binding = transforms.TransformBinding(sources=transforms.OHOIKO_SOURCES)
    assert transforms.undeclared_imports(binding) == {}
    assert set(transforms.OHOIKO_SOURCES) == set(imp.SOURCE_IDS)
    for source_id, spec in transforms.OHOIKO_SOURCES.items():
        assert spec.adapter.split(":")[1] == imp.ADAPTERS[source_id].__name__
        assert spec.expected_units == imp.EXPECTED_UNITS[source_id]
        assert len(transforms.transform_digest(source_id, binding)) == 64


def test_samples_are_seeded_and_drawn_from_all_lines(runs) -> None:
    first = imp.draw_samples(runs, "seed-a")
    assert first == imp.draw_samples(runs, "seed-a")
    assert len(first["ohoiko_entries"]) == 11 and len(first["oho_lines"]) == len(OHO_PAGE.splitlines())
    dispositions = {row["disposition"] for row in first["ulp_lines"]}
    assert "prose_excluded" in dispositions and "zone_entry" in dispositions
    assert [r["unit"] for r in first["ohoiko_entries"]] != [r["unit"] for r in imp.draw_samples(runs, "b")[
        "ohoiko_entries"]]


def test_cli_dry_run_and_arguments(sources_db: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = _sha(sources_db)
    assert imp.main(["--db", str(sources_db), "--report", str(tmp_path / "r.json")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True and json.loads((tmp_path / "r.json").read_text()) == report
    assert _sha(sources_db) == before
    assert imp.main(["--db", "sources.db"]) == 2
    assert imp.main(["--db", str(sources_db), "--sample-out", str(tmp_path / "s.json")]) == 2
    seed = tmp_path / "seed"
    seed.write_text("s", encoding="utf-8")
    assert imp.main(["--db", str(sources_db), "--sample-seed-file", str(seed),
                     "--sample-out", str(tmp_path / "s.json")]) == 0
    assert set(json.loads((tmp_path / "s.json").read_text())) == {"ohoiko_entries", "oho_lines", "ulp_lines"}
    with pytest.raises(SystemExit) as exc:
        imp.main(["--help"])
    assert exc.value.code == 0
    assert "Exit codes:" in capsys.readouterr().out


def test_cli_refuses_an_output_that_aliases_an_input_or_a_store_before_opening_anything(
        sources_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def no_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("opened a store")

    monkeypatch.setattr(imp, "open_readonly", no_open)
    before = _sha(sources_db)
    (tmp_path / "link.db").symlink_to(sources_db)
    (tmp_path / "sub").mkdir()
    (tmp_path / "hard.db").hardlink_to(sources_db)
    seed = tmp_path / "seed"
    seed.write_text("s", encoding="utf-8")
    lexdata = tmp_path / "lexdata-store.db"  # a registered store that does not exist yet
    monkeypatch.setenv(topology.ENV_LEXDATA_DB, str(lexdata))
    db = ["--db", str(sources_db)]
    refused = [
        [*db, "--report", str(sources_db)],  # the same path
        [*db, "--report", str(tmp_path / "link.db")],  # a symlink to it
        [*db, "--report", f"{tmp_path}/sub/../sources.db"],  # a relative alias
        [*db, "--report", str(tmp_path / "hard.db")],  # a hard link
        [*db, "--report", f"{sources_db}-wal"],  # its SQLite sidecar
        [*db, "--report", str(lexdata)],  # another registered store
        [*db, "--sample-seed-file", str(seed), "--sample-out", str(seed)],  # the seed input
        [*db, "--sample-seed-file", str(seed), "--sample-out", str(tmp_path / "s.json"),
         "--report", str(tmp_path / "s.json")],  # the other output
    ]
    for argv in refused:
        assert imp.main(argv) == 2, argv
        assert "names an input, a registered store or another output" in capsys.readouterr().err
    assert imp.main([*db, "--report", "sources.db"]) == 2  # a relative path: refused too
    assert _sha(sources_db) == before and seed.read_text(encoding="utf-8") == "s"
    assert not lexdata.exists() and not (tmp_path / "s.json").exists()


# --- headword primitives --------------------------------------------------


def test_repair_proposer_codes() -> None:
    assert gp.repair_ukrainian("уроќ") == ("уро́к", ["precomposed_acute_respelled", "stress_moved_to_vowel"])
    assert gp.repair_ukrainian(f"ха́т{LATIN_A}") == ("ха́та", ["latin_homoglyph"])
    assert gp.repair_ukrainian("ха́́та") == ("ха́та", ["doubled_stress"])


def test_split_headword_members_refs_notes_and_separators() -> None:
    parsed = gp.split_headword("писа́ти, написа́ти (1) = ми́ти (2) (verb)")
    assert [(f.raw, f.group, f.separator, f.senses, f.notes) for f in parsed.forms] == [
        ("писа́ти", 0, None, (), ()), ("написа́ти", 0, ",", (1,), ()), ("ми́ти", 1, "=", (2,), ("verb",))]
    assert [f.notes for f in gp.split_headword("сло́во (1943)").forms] == [("1943",)]
    only_note = gp.split_headword("(diminutive of ха́та)").forms
    assert [(f.raw, f.notes) for f in only_note] == [("", ("diminutive of ха́та",))]


def test_split_senses_and_stress_diagnostic() -> None:
    assert gp.split_senses("1) more; 2) anymore") == ["more", "anymore"]
    assert gp.split_senses("1) more; 3) anymore") is None
    assert gp.stress_errors("коли-не́будь") == [] and gp.stress_errors("ключ") == []
    assert gp.stress_errors("коли-небудь") == ["unstressed_polysyllable:коли-небудь"]


def test_iter_examples_first_matches_legacy_single_example() -> None:
    lines = normalize_chunk_lines(WORD_CHUNKS[3])
    examples = [example for _, example in iter_1000_words_examples(lines, start_i=2)]
    assert len(examples) == 2
    assert extract_1000_words_example(lines, start_i=2) == examples[0]


# ---------------------------------------------------------------------------
# r4 review fixes (OO-38): resolved input sidecars, verbatim wrapped spans, exercise headings
# ---------------------------------------------------------------------------


def test_resolved_input_and_its_sidecars_are_protected_when_db_is_a_symlink(tmp_path: Path) -> None:
    source = tmp_path / "input.db"
    source.write_text("synthetic marker, not a database", encoding="utf-8")
    link = tmp_path / "link.db"
    link.symlink_to(source)
    protected = imp._protected_paths(link, None)
    for option in ("report", "sample-out"):
        for suffix in ("", "-wal", "-shm", "-journal"):
            assert imp.output_collision({option: source.with_name(source.name + suffix)}, protected) == option
    assert imp.output_collision({"report": tmp_path / "elsewhere.json"}, protected) is None


@pytest.mark.parametrize("text", [
    "1. сло́во\n\n   те́рмін  word\n",  # a blank line and an indented continuation
    "1. сло́во\r\n\r\n   те́рмін  word\r\n",  # CR characters
    "1. сло́во   \n\t\n  те́рмін\n",  # trailing whitespace, a tab-only line
])
def test_wrapped_raw_span_is_the_source_region_byte_for_byte(text: str) -> None:
    entry = imp.parse_word_chunk("synthetic_e0001", text)
    item, = imp.entry_items("entry", entry.shape, join_splits=True, printed=imp.PrintedText(text, 3))
    assert item.raw_span == text[item.span_start:item.span_end]
    assert "\n" in item.raw_span


def test_wrapped_raw_span_leaves_out_only_the_other_column_text() -> None:
    text = "1. сло́во = вислів =  word, expression\n\n   те́рмін\n"
    entry = imp.parse_word_chunk("synthetic_e0001", text)
    parent = next(i for i in imp.entry_items("entry", entry.shape, join_splits=True,
                                             printed=imp.PrintedText(text, 3)) if i.parent is None)
    assert parent.raw_span == "сло́во = вислів =\n\n   те́рмін"


def test_r2_3_reviewers_reproducer_exercise_heading_with_matching_columns() -> None:
    """The r3 review's synthetic reproducer, verbatim: entry-shaped lines under "Bonus Exercises" are not vocabulary."""
    lines = ["Lesson synthetic", "", " " * 40 + "Key Vocabulary 1-01",
             f"{'':14}{'сло́во':49}word", "",
             " " * 40 + "Bonus Exercises 1-20",
             f"{'':14}{'так':49}yes"]
    parsed = gp.parse_lesson("\n".join(lines))
    assert [entry.headword_raw for entry in parsed.entries] == ["сло́во"]
    assert parsed.sections == [("Key Vocabulary 1-01", 3, 5)]


@pytest.mark.parametrize("heading", [
    "Bonus Exercises 1-20", "Exercises", "Answer Key",  # the old deny-list
    "Grammar Notes", "Homework", "Review", "Dialogue", "Extra Practice 3",  # English headings it never named
    "Вправи", "Додаткові вправи", "Відповіді на вправи", "Культурна довідка",  # Ukrainian headings
])
def test_r2_3_zone_ends_at_any_heading_that_is_not_a_vocabulary_heading(heading: str) -> None:
    lines = ["Lesson synthetic", "", " " * 40 + "Key Vocabulary 1-01",
             f"{'':14}{'сло́во':49}word", "",
             " " * 40 + heading,
             f"{'':14}{'так':49}yes",
             f"{'':14}{'ні':49}no"]
    assert gp.find_vocab_sections(lines) == [("Key Vocabulary 1-01", 3, 5)], heading
    assert [e.headword_raw for e in gp.parse_lesson("\n".join(lines)).entries] == ["сло́во"], heading


def test_r2_3_a_following_vocabulary_heading_starts_the_next_zone() -> None:
    lines = ["Lesson synthetic", "", " " * 40 + "Key Vocabulary 1-01", f"{'':14}{'сло́во':49}word", "",
             " " * 40 + "Exercises", f"{'':14}{'так':49}yes", "",
             " " * 40 + "Bonus Vocabulary", f"{'':14}{'ха́та':49}house"]
    assert gp.find_vocab_sections(lines) == [("Key Vocabulary 1-01", 3, 5), ("Bonus Vocabulary", 9, 10)]
    assert [e.headword_raw for e in gp.parse_lesson("\n".join(lines)).entries] == ["сло́во", "ха́та"]


@pytest.mark.parametrize(("title", "line", "expected"), [
    ("Lesson 201: Синтетичний урок", "Синтетичний урок", True),  # Season 6: the title after "Lesson N:"
    ("Lesson 83: Знайомство Meeting a roommate Prefixes до-", "Meeting a roommate. Prefixes до-", True),  # 1-3
    ("Lesson 3: Title", "Title", True),
    ("Lesson 3: Title", "Exercises", False),
    ("Lesson 3: Title", "Title and more words than the title", False),
    ("Lesson 3: Знайомство Meeting a roommate", "Знайомство", False),  # the head of the title, not its end
    ("Lesson 3: Title", "", False),
    ("", "Title", False),
])
def test_r2_3_only_the_repeated_lesson_title_is_a_running_head(title: str, line: str, expected: bool) -> None:
    assert gp.is_running_title(line, title) is expected


def test_r2_3_running_title_keeps_the_zone_only_when_entries_follow() -> None:
    body = [f"{'':14}{'сло́во':49}word", "", f"{'':19}Title", ""]
    lines = ["Lesson 3: Title", "", " " * 40 + "Key Vocabulary 3-01", *body, f"{'':14}{'ха́та':49}house"]
    assert gp.find_vocab_sections(lines) == [("Key Vocabulary 3-01", 3, len(lines))]
    assert gp.find_vocab_sections([*lines[:-1], f"{'':14}Not an entry line"]) == [("Key Vocabulary 3-01", 3, 5)]


# --- R2-2: every raw_span is its source region ----------------------------


def _source_text(source: str, unit: rec.ParsedUnit) -> str:
    payload = unit.unit.payload
    if source == imp.WORDS_SOURCE_ID:
        return WORD_CHUNKS[int(unit.unit.l0_locator[-4:])]
    return payload["pages"][0]["full_text"] if source == imp.VERBS_SOURCE_ID else payload["full_text"]


@pytest.mark.parametrize("source", imp.SOURCE_IDS)
def test_r2_2_every_span_producer_raw_span_equals_the_source_bytes_at_its_offsets(runs, source: str) -> None:
    """A span on one line is ``text[start:end]``; a wrapped one keeps its line breaks and drops only other columns."""
    checked = 0
    for unit in runs[source].units:
        if not unit.items:
            continue  # refused truncated_source: nothing printed
        text = _source_text(source, unit)
        for item in unit.items:
            region = _printed(text, item)
            if "\n" not in region:
                assert item.raw_span == region, item.raw_span
            else:
                raw_lines, region_lines = item.raw_span.split("\n"), region.split("\n")
                assert len(raw_lines) == len(region_lines), item.raw_span
                assert region_lines[0].startswith(raw_lines[0]) and region_lines[-1].endswith(raw_lines[-1])
                assert all(raw in line for raw, line in zip(raw_lines, region_lines, strict=True)), item.raw_span
            checked += 1
    assert checked > 0


WRAPS = ("\n", "\n\n", "\r\n", "\r\n\r\n", "\n   ", "\n\n\t ", " \n", "\t\n  ", "\n \n   ", "\r\n  \r\n\t")


def test_r2_2_property_wrapped_word_spans_are_the_source_bytes_without_another_column() -> None:
    """Seeded generative check (1000-words producer): no other column in the span, so raw == text[start:end]."""
    rng = random.Random(20261020)
    heads = ("сло́во", "те́рмін", "ха́та", "кни́жка", "вислів", "пра́вда", "ми́ля")
    for _ in range(300):
        first, second = rng.sample(heads, 2)
        wrap = rng.choice(WRAPS)
        text = f"1. {first}{wrap}{second}{rng.choice(('', '  word'))}\n"
        entry = imp.parse_word_chunk("synthetic_e0001", text)
        item, = imp.entry_items("entry", entry.shape, join_splits=True, printed=imp.PrintedText(text, 3))
        assert item.raw_span == text[item.span_start:item.span_end] == f"{first}{wrap}{second}", repr(text)


def test_r2_2_property_wrapped_zone_spans_are_the_source_bytes_without_another_column() -> None:
    """Seeded generative check (ULP producer): a headword with a displaced acute on the next line."""
    rng = random.Random(20261020)
    for _ in range(100):
        indent = rng.randint(0, 6)
        pad = " " * rng.randint(0, 3)
        lines = _zone(f"{'':14}Взаєм", f"{'':{18 + indent}}{pad}́ но!{'':40}Me too!")
        newline = rng.choice(("\n", "\r\n"))
        text = newline.join(lines)
        locator = "sources:textbook_sections:section_id=1"
        unit = rec.UnitInput(imp.ULP_SOURCE_ID, locator, "section", (rec.L0Row(locator, "0" * 64),),
                             payload={"full_text": text})
        item, = imp.UlpAdapter().parse(unit).items
        origin = sum(len(line) for line in text.splitlines(keepends=True)[:item.line_no])
        assert item.raw_span == text[origin + item.span_start:origin + item.span_end], repr(text)
        assert item.raw_span.startswith("Взаєм") and "\n" in item.raw_span


# --- R2-1: every output alias of an input (one test per sibling) -------------

REFUSAL = "names an input, a registered store or another output"
SIDECARS = ("-wal", "-shm", "-journal")


@pytest.fixture
def alias_world(sources_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """The db with its three sidecars, a symlink to it, a symlinked directory and a seed file."""
    for suffix in SIDECARS:
        sources_db.with_name(sources_db.name + suffix).write_bytes(b"sidecar bytes")
    (tmp_path / "link.db").symlink_to(sources_db)
    (tmp_path / "sub").mkdir()
    (tmp_path / "dirlink").symlink_to(tmp_path, target_is_directory=True)
    seed = tmp_path / "seed"
    seed.write_text("s", encoding="utf-8")

    def no_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("opened a store")

    monkeypatch.setattr(imp, "open_readonly", no_open)
    return SimpleNamespace(root=tmp_path, db=sources_db, seed=seed)


def _argv(db: Path, option: str, out: Path, seed: Path) -> list[str]:
    if option == "report":
        return ["--db", str(db), "--report", str(out)]
    return ["--db", str(db), "--sample-seed-file", str(seed), "--sample-out", str(out)]


def _assert_refused(world: SimpleNamespace, db: Path, out: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Both output options refuse ``out`` with exit 2 before a store is opened; no input changes a byte."""
    guarded = [path for path in world.root.iterdir() if path.is_file()]
    before = {path: _sha(path) for path in guarded}
    for option in ("report", "sample-out"):
        assert imp.main(_argv(db, option, out, world.seed)) == 2, (option, out)
        assert REFUSAL in capsys.readouterr().err
    assert {path: _sha(path) for path in guarded} == before


def _alias(world: SimpleNamespace, kind: str, target: Path, name: str) -> Path:
    """A path naming ``target`` as ``kind`` (``target`` may not exist: SQLite creates a sidecar lazily)."""
    if kind == "same":
        return target
    if kind == "symlink":
        (world.root / name).symlink_to(target)
        return world.root / name
    if kind == "hardlink":
        (world.root / name).hardlink_to(target)
        return world.root / name
    if kind == "dotdot":
        return world.root / "sub" / ".." / target.name
    if kind == "dirlink":
        return world.root / "dirlink" / target.name
    raise AssertionError(kind)


def test_r2_1_symlink_to_db_is_refused(alias_world: SimpleNamespace, capsys: pytest.CaptureFixture[str]) -> None:
    out = _alias(alias_world, "symlink", alias_world.db, "out-sym.json")
    for db in (alias_world.db, alias_world.root / "link.db"):
        _assert_refused(alias_world, db, out, capsys)
    _assert_refused(alias_world, alias_world.db, alias_world.root / "link.db", capsys)  # the --db symlink itself


def test_r2_1_hardlink_to_db_is_refused(alias_world: SimpleNamespace, capsys: pytest.CaptureFixture[str]) -> None:
    out = _alias(alias_world, "hardlink", alias_world.db, "out-hard.json")
    for db in (alias_world.db, alias_world.root / "link.db"):
        _assert_refused(alias_world, db, out, capsys)


@pytest.mark.parametrize("suffix", SIDECARS)
@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink", "dotdot", "dirlink"])
def test_r2_1_sidecar_of_the_resolved_db_is_refused_however_db_is_named(
        alias_world: SimpleNamespace, capsys: pytest.CaptureFixture[str], suffix: str, alias: str) -> None:
    """SQLite names ``-wal``/``-shm``/``-journal`` after the resolved file, also when --db is a symlink."""
    target = alias_world.db.with_name(alias_world.db.name + suffix)
    out = _alias(alias_world, alias, target, f"out{suffix}.json")
    for db in (alias_world.db, alias_world.root / "link.db"):
        _assert_refused(alias_world, db, out, capsys)


@pytest.mark.parametrize("suffix", SIDECARS)
@pytest.mark.parametrize("alias", ["same", "symlink", "dotdot", "dirlink"])
def test_r2_1_sidecar_of_the_unresolved_symlinked_db_is_refused(
        alias_world: SimpleNamespace, capsys: pytest.CaptureFixture[str], suffix: str, alias: str) -> None:
    """The sidecar named after the symlink itself (it does not exist, so no hard link to it is possible)."""
    link = alias_world.root / "link.db"
    target = link.with_name(link.name + suffix)
    assert not target.exists()
    out = _alias(alias_world, alias, target, f"out-unresolved{suffix}.json")
    _assert_refused(alias_world, link, out, capsys)


def test_r2_1_relative_and_absolute_forms_name_one_file(alias_world: SimpleNamespace,
                                                         capsys: pytest.CaptureFixture[str]) -> None:
    """A relative path is refused as such; its ``..`` and symlinked-directory forms are refused as the db."""
    assert imp.main(["--db", str(alias_world.db), "--report", alias_world.db.name]) == 2  # cwd holds the db
    assert "must be an absolute path" in capsys.readouterr().err
    for suffix in ("", *SIDECARS):
        target = alias_world.db.with_name(alias_world.db.name + suffix)
        for alias in ("dotdot", "dirlink"):
            _assert_refused(alias_world, alias_world.db, _alias(alias_world, alias, target, "unused"), capsys)


def test_r2_1_an_unrelated_output_is_not_refused(alias_world: SimpleNamespace) -> None:
    """The guard is not a blanket refusal: names that are none of the aliases pass it."""
    protected = imp._protected_paths(alias_world.root / "link.db", alias_world.seed)
    for name in ("report.json", "sources.db.bak", "sources.dbx-wal", "link.db-wal.json"):
        assert imp.output_collision({"report": alias_world.root / name}, protected) is None, name


@pytest.mark.parametrize("suffix", ("", *SIDECARS))
def test_r2_1_sidecar_of_a_registered_store_behind_a_symlink_is_refused(
        alias_world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        suffix: str) -> None:
    """A store registered by an override that is a symlink to a file not built yet: its resolved name is protected."""
    real = alias_world.root / "built-later.db"
    (alias_world.root / "lexdata-link.db").symlink_to(real)
    monkeypatch.setenv(topology.ENV_LEXDATA_DB, str(alias_world.root / "lexdata-link.db"))
    assert not real.exists()
    _assert_refused(alias_world, alias_world.db, real.with_name(real.name + suffix), capsys)
