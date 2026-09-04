"""Regression cases for wrong-lemma teacher answers and multi-blank frames."""

import json
import sqlite3

from scripts.lexicon import build_teacher_deck_cloze as builder
from scripts.lexicon.build_teacher_deck_cloze import find_cloze_sentence


def test_does_not_treat_prefixed_verb_as_target_lemma():
    # VESUM: пробігти → пробігти, not бігти (teacher_cloze_265).
    assert find_cloze_sentence(["Треба пробігти до школи."], {"бігти"}) is None


def test_does_not_treat_adjective_as_noun():
    # VESUM: вечірній → вечірній, not вечір (teacher_cloze_367).
    assert find_cloze_sentence(["Настав вечірній час."], {"вечір"}) is None


def test_accepts_attested_inflection_and_preserves_surface():
    assert find_cloze_sentence(["Я бачу нову бібліотеку."], {"бібліотека", "бібліотеку"}) == (
        "Я бачу нову _____.", "бібліотеку",
    )


def test_blanks_one_token_without_modifying_other_occurrences():
    assert find_cloze_sentence(["Вечір, вечірній час, вечір."], {"вечір"}) == (
        "_____, вечірній час, вечір.", "Вечір",
    )


def test_accepts_apostrophe_variants():
    assert find_cloze_sentence(["Він працює на комп’ютерах."], {"комп'ютерах"}) == (
        "Він працює на _____.", "комп’ютерах",
    )


def test_stress_mark_stays_with_answer_not_blank():
    assert find_cloze_sentence(["Я бачу нову бібліоте́ку."], {"бібліотеку"}) == (
        "Я бачу нову _____.", "бібліоте́ку",
    )


def test_no_attested_context_means_no_invented_frame():
    assert find_cloze_sentence(["Це зовсім інше речення."], {"бібліотеку"}) is None


def test_rejects_source_sentence_with_existing_blanks():
    assert find_cloze_sentence(["Вечір настав у _____ місті."], {"вечір"}) is None


def test_rejects_hyphenated_compound_and_truncated_ocr_token():
    assert find_cloze_sentence(["Ось слово-асоціація у тексті."], {"асоціація"}) is None
    assert find_cloze_sentence(["У тексті наведено абсурд- слово."], {"абсурд"}) is None


def test_builder_omits_unsourced_cards_and_keeps_ids(tmp_path, monkeypatch):
    intake = tmp_path / "intake.json"
    intake.write_text(json.dumps({"auto_merge": [{"lemma": "бігти"}, {"lemma": "вечір"}]}))
    sources = tmp_path / "sources.db"
    with sqlite3.connect(sources) as conn:
        conn.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(text)")
        conn.executemany("INSERT INTO textbooks_fts VALUES (?)", [
            ("Треба пробігти до школи.",), ("Настав тихий вечір.",),
        ])
    vesum = tmp_path / "vesum.db"
    with sqlite3.connect(vesum) as conn:
        conn.execute("CREATE TABLE forms (lemma, word_form, pos, tags)")
        conn.executemany("INSERT INTO forms VALUES (?, ?, ?, ?)", [
            ("бігти", "бігти", "verb", "verb:imperf:inf"),
            ("вечір", "вечір", "noun", "noun:inanim:m:v_naz"),
        ])
    monkeypatch.setattr(builder, "INTAKE_JSON", intake)
    public = tmp_path / "public.json"
    source = tmp_path / "source.json"
    monkeypatch.setattr(builder, "OUTPUT_PUBLIC_JSON", public)
    monkeypatch.setattr(builder, "OUTPUT_SRC_JSON", source)
    monkeypatch.setattr("sys.argv", ["build", "--sources-db", str(sources), "--vesum-db", str(vesum)])
    builder.main()
    cards = json.loads(public.read_text())["cloze"]
    assert public.read_bytes() == source.read_bytes()
    assert len(cards) == 1
    assert cards[0]["clozeId"] == "teacher_cloze_2"
    assert cards[0]["sentence"] == "Настав тихий _____."
    assert cards[0]["form"] == "вечір"
