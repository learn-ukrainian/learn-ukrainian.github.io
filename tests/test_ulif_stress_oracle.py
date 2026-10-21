"""ULIF-first policy pinned to captured source rows; production DB stays read-only."""

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.verification import stress, stress_comparison
from scripts.wiki import sources_db

CAPTURE = json.loads((Path(__file__).parent / "fixtures/stress-ulif-forms.json").read_text())
IDENTITY = json.loads((Path(__file__).parent / "fixtures/stress-identity-join.json").read_text())


@pytest.fixture
def captured_db(tmp_path, monkeypatch):
    path = tmp_path / "captured.sqlite"
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Capture column names and values without bootstrapping the entire source schema.
    for table, rows in [
        ("ulif_forms_build", [CAPTURE["build"]]),
        ("ulif_forms", CAPTURE["forms"]),
        ("ulif_dictua_entries", CAPTURE["entries"]),
    ]:
        keys = list(rows[0])
        conn.execute(f"CREATE TABLE {table} ({','.join(keys)})")
        conn.executemany(
            f"INSERT INTO {table} VALUES ({','.join('?' for _ in keys)})", [list(row.values()) for row in rows]
        )
    conn.commit()
    # Captured analyses pin the identity join without a mutable live VESUM DB.
    monkeypatch.setattr(stress, "_vesum_lookup", lambda form: [dict(v) for v in IDENTITY["vesum"].get(form, [])])
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    yield conn
    conn.close()


def test_rule_1_unchecked_entry_never_evidence(captured_db):
    # Synthetic linkage, explicitly named: real form values attached to the
    # real unchecked legacy entry. There are no unchecked forms in the live build.
    unchecked = CAPTURE["unchecked_entry"]
    captured_db.execute(
        "INSERT INTO ulif_dictua_entries VALUES (" + ",".join("?" for _ in unchecked) + ")", list(unchecked.values())
    )
    captured_db.execute("UPDATE ulif_forms SET entry_id=1 WHERE form_unstressed='бачу'")
    assert sources_db.ulif_stress_rows("бачу") == []
    result = stress.verify_stress("бачу")
    assert result["stress_source"] == "trie"
    assert all(m["source"] == "trie" for m in result["matches"])


def test_rule_2_agreeing_readings_keep_all_ids(captured_db):
    result = stress.verify_stress("село")
    assert result["status"] == "ok"
    assert result["stress_source"] == "ulif"
    (match,) = result["matches"]
    assert match["stressed_form"] == "село́"
    assert {r["id"] for r in match["evidence"]} == {r["id"] for r in CAPTURE["forms"] if r["form_unstressed"] == "село"}
    assert all(r["entry_id"] == 213324 for r in match["evidence"])


def test_rule_3_homographs_never_first(captured_db):
    result = stress.verify_stress("замок")
    assert result["status"] == "ambiguous"
    assert {m["stressed_form"] for m in result["matches"]} == {"за́мок", "замо́к"}
    assert all(m["grammatical_tags"] and m["evidence"] for m in result["matches"])
    assert stress.verify_stress("замок", pos="NOUN")["status"] == "ambiguous"
    assert stress.verify_stress("замок", lemma="замок")["status"] == "ambiguous"
    assert stress.verify_stress("замок", lemma="за́мок")["matches"][0]["stressed_form"] == "за́мок"
    assert stress.verify_stress("замок", lemma="замо́к")["matches"][0]["stressed_form"] == "замо́к"
    verb = stress.verify_stress("замок", pos="VERB")
    assert verb["status"] == "ok"
    # VESUM attests замокти, not the ULIF synonym замокнути.
    assert {e["entry_id"] for e in verb["matches"][0]["evidence"]} == {76803}


def test_rule_3_case_and_vesum_join(captured_db):
    plural = stress.verify_stress("вікна", tags="noun:n:p:v_naz")
    genitive = stress.verify_stress("вікна", lemma="вікно", tags="noun:n:v_rod")
    assert plural["status"] == genitive["status"] == "ok"
    assert plural["matches"][0]["stressed_form"] == "ві́кна"
    assert genitive["matches"][0]["stressed_form"] == "вікна́"
    vesum = [{"lemma": "вікно", "pos": "noun", "tags": "noun:inanim:n:p:v_naz"}]
    with patch.object(stress, "_vesum_lookup", return_value=vesum):
        assert stress.verify_stress("вікна", tags="noun:n:p:v_naz")["matches"][0]["vesum"] == vesum[0]
    assert stress.verify_stress("вікна", tags="Case=Dat")["status"] == "pending"
    assert stress.verify_stress("Київ")["matches"][0]["stressed_form"] == "Ки́їв"
    assert stress.verify_stress("київ", lemma="Київ")["matches"][0]["stressed_form"] == "ки́їв"


def test_rule_4_dual_variants_do_not_relabel_generated_choice(captured_db):
    result = stress.verify_stress("розбір")
    (match,) = result["matches"]
    assert result["status"] == "ok"
    assert match["dual_stress"]
    assert match["variants"] == ["ро́збір", "розбі́р"]
    assert "pedagogical_stressed_form" not in match
    assert stress.pedagogical_stressed_form(match) == "ро́збі́р"
    assert stress.spoken_stressed_form(match) is None
    for variant in match["variants"]:
        assert stress.verify_stress(variant)["matches"][0]["input_mismatch"] is False


@pytest.mark.parametrize("caller", ["opus", "slice"])
@pytest.mark.parametrize(
    "form,expected",
    [
        ("село", "село́"),
        ("воно", "воно́"),
        ("любов", "любо́в"),
        ("Київ", "ки́їв"),
    ],
)
def test_audio_callers_use_attested_choice(captured_db, caller, form, expected):
    from scripts.audio.batch_synthesize_opus import resolve_stress
    from scripts.audio.generate_pronunciation import select_slice

    if caller == "opus":
        text, reason = resolve_stress(form, None, stress.verify_stress)
        assert reason is None
    else:
        selected, excluded = select_slice(
            {"deckVersion": "captured", "lexemes": [{"lemmaPlain": form}]}, 1, stress.verify_stress
        )
        assert excluded == []
        text = selected[0]["text"]
    assert text == expected.lower()
    assert text.count("\u0301") == 1


@pytest.mark.parametrize("caller", ["opus", "slice"])
@pytest.mark.parametrize(
    "form,reason",
    [("замок", "ambiguous"), ("розбір", "unresolved_dual_stress"), ("квазюрап", "pending"), ("вона", "pending")],
)
def test_audio_callers_withhold_unresolved_readings(captured_db, caller, form, reason):
    from scripts.audio.batch_synthesize_opus import resolve_stress
    from scripts.audio.generate_pronunciation import select_slice

    captured_db.execute("UPDATE ulif_forms SET pedagogical_stressed_form='' WHERE form_unstressed='розбір'")
    if caller == "opus":
        assert resolve_stress(form, "NOUN", stress.verify_stress) == (None, reason)
    else:
        selected, excluded = select_slice(
            {
                "deckVersion": "captured",
                "lexemes": [
                    {"lemmaPlain": form, "pos": "NOUN"},
                    {"lemmaPlain": "так"},
                ],
            },
            1,
            stress.verify_stress,
        )
        assert selected == [{"lemma": "так", "text": "так"}]
        assert excluded == [{"lemma": form, "reason": reason}]


@pytest.mark.parametrize("choice", ["", "ро́збі́р", "розбір", "ко́рисний", "розб́ір"])
def test_spoken_choice_rejects_unsupported_teaching_form(captured_db, choice):
    (match,) = stress.verify_stress("розбір")["matches"]
    match["pedagogical_source"] = [{"dictionary": "explicit synthetic source fixture"}]
    match["pedagogical_stressed_form"] = choice
    assert stress.spoken_stressed_form(match) is None


def test_spoken_choice_rejects_conflict_and_unlabelled_packed_trie(captured_db):
    (match,) = stress.verify_stress("розбір")["matches"]
    assert stress.spoken_stressed_form({**match, "pedagogical_conflict": True}) is None
    assert stress.spoken_stressed_form({**match, "source": "trie"}) is None
    assert stress.spoken_stressed_form({**match, "override_applied": True}) == match["stressed_form"]


def test_rule_2_teaching_choice_case_agrees_but_positions_conflict(captured_db):
    captured_db.execute(
        "UPDATE ulif_forms SET pedagogical_stressed_form='Розбі́р' WHERE id=(SELECT min(id) FROM ulif_forms WHERE form_unstressed='розбір')"
    )
    (match,) = stress.verify_stress("розбір")["matches"]
    assert not match.get("pedagogical_conflict")
    assert "pedagogical_stressed_form" not in match
    assert stress.spoken_stressed_form(match) is None
    captured_db.execute("UPDATE ulif_forms SET pedagogical_stressed_form='ро́збір' WHERE form_unstressed='розбір'")
    (changed,) = stress.verify_stress("розбір")["matches"]
    assert changed == match  # Neither generated heuristic is a source choice.


def test_rule_5_only_fallback_pending_and_override(captured_db):
    ulif = stress.verify_stress(CAPTURE["ulif_only_form"])
    assert ulif["status"] == "ok" and ulif["stress_source"] == "ulif"
    assert stress._trie_value(stress._load_trie(), CAPTURE["ulif_only_form"]) is None
    trie = stress.verify_stress(CAPTURE["trie_only_form"])
    assert trie["stress_source"] == "trie"
    assert stress.verify_stress("квазюрап")["status"] == "pending"
    with patch.object(stress, "_load_overrides", return_value={"село": "село́"}):
        override = stress.verify_stress("село")
        assert override["stress_source"] == override["matches"][0]["source"] == "override"
        assert override["matches"][0]["override_applied"]
    with patch.object(stress, "pending_stress_reason", return_value="source unavailable"):
        assert stress.verify_stress("село")["status"] == "pending"


def test_rule_6_both_digests_invalidate_receipts(captured_db):
    original = stress.source_info()
    assert original["ulif"]["build"] == CAPTURE["build"]
    assert original["trie_digest"] == stress._trie_digest()
    captured_db.execute("UPDATE ulif_forms_build SET source_fingerprint='synthetic-new-build'")
    changed = stress.source_info()
    assert original["digest"] != changed["digest"]
    assert original["ulif"]["digest"] != changed["ulif"]["digest"]
    with patch.object(stress, "_trie_digest", return_value="synthetic-new-trie"):
        assert stress.source_info()["digest"] != changed["digest"]


def test_incomplete_build_is_not_evidence(captured_db):
    captured_db.execute("UPDATE ulif_forms_build SET state='building'")
    assert sources_db.ulif_stress_rows("село") == []
    assert stress.verify_stress("село")["stress_source"] == "trie"
    captured_db.execute("UPDATE ulif_forms_build SET state='complete',parser_version='synthetic-old-parser'")
    assert sources_db.ulif_stress_rows("село") == []


def test_batch_preserves_source_evidence_and_variants(captured_db):
    batch = stress.verify_stresses(["село", "розбір", "замок", CAPTURE["trie_only_form"], "любов"])
    assert [r["source"] for r in batch["words"]] == ["ulif", "ulif", "ulif", "trie", "override"]
    assert batch["words"][0]["readings"][0]["evidence"]
    assert batch["words"][1]["readings"][0]["variants"] == ["ро́збір", "розбі́р"]
    assert batch["words"][0]["readings"][0]["vesum_analyses"]
    assert batch["words"][2]["status"] == "ambiguous"


def test_batch_keeps_teaching_conflict(captured_db):
    single = stress.verify_stress("розбір")["matches"][0]
    single["pedagogical_conflict"] = True
    compact = stress._compact_stress_reading(single)
    assert compact["pedagogical_conflict"] is True
    assert "pedagogical_stressed_form" not in compact
    assert compact["variants"] == single["variants"]
    assert stress.verify_stresses(["вікна"], tags="noun:n:p:v_naz")["words"][0]["status"] == "ok"


def test_comparison_preserves_corpus_case_and_samples_actual_disagreements(tmp_path, captured_db):
    root = tmp_path / "corpus"
    store = root / "curriculum/l2-uk-en/evidence/a1/_words.yaml"
    store.parent.mkdir(parents=True)
    store.write_text("words: [{forms: [{form: село}, {form: вікна}]}]")
    for track in ("a1", "a1-v1"):
        page = root / "site/src/content/docs" / track / "one.mdx"
        page.parent.mkdir(parents=True)
        page.write_text("Ки́їв село́")
    forms, inputs = stress_comparison.corpus_forms(root)
    assert forms == ["Київ", "вікна", "село"]
    assert len(inputs) == 3
    summary = stress_comparison.write_report(root, tmp_path / "report")
    assert summary["denominator"] == 3
    assert sum(summary["counts"][k] for k in ("agree", "disagree", "ulif_only", "trie_only", "neither")) == 3
    assert summary["sample_size"] == min(60, summary["counts"]["disagree"])


def test_annotator_refuses_meaning_guess_and_joins_context(captured_db, monkeypatch):
    from scripts.pipeline import stress_annotator as annotator

    monkeypatch.setattr(annotator, "_get_stressifier", lambda: object())
    assert annotator.annotate_stress("замок")[0] == "замок"
    assert annotator.annotate_stress("за́мок")[0] == "замок"
    assert annotator._oracle_choice("вікна", lemma="вікно", pos="NOUN", tags="Number=Plur|Case=Nom") == "ві́кна"
    assert annotator._oracle_choice("село́") == "село́"
    assert annotator._oracle_choice("розбір") == "ро́збі́р"


def test_context_model_loading_is_offline(monkeypatch):
    import sys
    from types import SimpleNamespace

    from scripts.pipeline import stress_annotator as annotator

    calls = []

    def pipeline(*args, **kwargs):
        calls.append(kwargs)
        if "lemma" in kwargs["processors"]:
            raise FileNotFoundError("synthetic missing lemma model")
        return "synthetic morphology parser"

    monkeypatch.setitem(sys.modules, "stanza", SimpleNamespace(Pipeline=pipeline))
    assert annotator._load_context_parser() == "synthetic morphology parser"
    assert all(call["download_method"] is None for call in calls)


def test_sentence_context_uses_morphology_not_trie_accent(captured_db, monkeypatch):
    from types import SimpleNamespace

    from scripts.pipeline import stress_annotator as annotator

    token = SimpleNamespace(
        start_char=0,
        end_char=5,
        to_dict=lambda: [
            {"text": "вікна", "lemma": "вікно", "upos": "NOUN", "feats": "Number=Plur|Case=Nom|Gender=Neut"}
        ],
    )
    parsed = SimpleNamespace(iter_tokens=lambda: iter([token]))
    monkeypatch.setattr(annotator, "_get_stressifier", lambda: SimpleNamespace(nlp=lambda _: parsed))
    assert annotator.annotate_stress("вікна") == ("ві́кна", 1)
    token.to_dict = lambda: [
        {"text": "вікна", "lemma": "вікно", "upos": "NOUN", "feats": "Number=Sing|Case=Gen|Gender=Neut"}
    ]
    assert annotator.annotate_stress("вікна") == ("вікна́", 1)


def test_dual_without_teaching_choice_never_invents_one(captured_db):
    from scripts.curriculum.evidence.words import packed_stress_reason
    from scripts.pipeline import stress_annotator as annotator

    captured_db.execute("UPDATE ulif_forms SET pedagogical_stressed_form='' WHERE form_unstressed='розбір'")
    (match,) = stress.verify_stress("розбір")["matches"]
    assert stress.pedagogical_stressed_form(match) == "ро́збі́р"
    assert annotator._oracle_choice("розбір") == "ро́збі́р"
    assert annotator._oracle_choice("розбі́р") == "розбі́р"
    assert packed_stress_reason(match) == "multiple_stressed_vowels"


def test_read_helpers_never_initialize_missing_tables(tmp_path, monkeypatch):
    conn = sqlite3.connect(tmp_path / "synthetic-empty.db")
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    assert sources_db.ulif_stress_build()["state"] == "missing_table"
    assert sources_db.ulif_stress_rows("село") == []
    assert conn.execute("SELECT name FROM sqlite_master").fetchall() == []
    conn.close()

    def unavailable():
        raise FileNotFoundError("synthetic unavailable source")

    monkeypatch.setattr(sources_db, "_get_conn", unavailable)
    assert sources_db.ulif_stress_build()["state"] == "unavailable"


def test_comparison_cli_help_has_side_effects_and_exit_codes(capsys):
    with pytest.raises(SystemExit) as exc:
        stress_comparison.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "Outputs:" in help_text and "Exit codes:" in help_text and "--seed" in help_text


def test_live_trie_replacement_changes_reading_and_receipt(captured_db, tmp_path, monkeypatch):
    import marisa_trie

    path = tmp_path / "synthetic-trie"
    # Packed bytes copied from the live trie's source-attested readings.
    first = stress._trie_value(stress._load_trie(), "воно")
    second = stress._trie_value(stress._load_trie(), "розбір")
    marisa_trie.BytesTrie([("воно", first)]).save(str(path))
    monkeypatch.setattr(stress, "_trie_path", lambda: path)
    original = stress.source_info()
    assert stress._trie_value(stress._load_trie(), "воно") == first
    marisa_trie.BytesTrie([("воно", second)]).save(str(path))
    changed = stress.source_info()
    assert original["trie_digest"] != changed["trie_digest"]
    assert original["digest"] != changed["digest"]
    assert stress._trie_value(stress._load_trie(), "воно") == second


def test_annotator_does_not_borrow_sole_reading_from_another_lexeme(captured_db, monkeypatch):
    from scripts.pipeline import stress_annotator as annotator

    analyses = [{"lemma": "вона", "pos": "noun", "tags": "noun:unanim:f:v_naz:pron:pers:3"}]
    monkeypatch.setattr(stress, "_vesum_lookup", lambda _: analyses)
    monkeypatch.setattr(annotator, "_get_stressifier", lambda: object())
    assert stress.verify_stress("вона")["matches"][0]["stressed_form"] == "вона́"
    assert annotator.annotate_stress("вона") == ("вона́", 1)
    assert annotator._oracle_choice("вона", pos="PRON") == "вона́"


@pytest.fixture
def identity_db(captured_db):
    for table in ("ulif_forms", "ulif_dictua_entries"):
        rows = IDENTITY["forms" if table == "ulif_forms" else "entries"]
        captured_db.executemany(
            f"INSERT INTO {table} VALUES ({','.join('?' for _ in rows[0])})",
            [list(row.values()) for row in rows],
        )
    return captured_db


@pytest.mark.parametrize("word,expected", [("вона", "вона́"), ("вони", "вони́")])
def test_rule_2_pronoun_never_uses_other_lemma(identity_db, word, expected):
    from scripts.verification.ulif_stress import readings

    # Real entry 9434 is the noun вон; it cannot attest these pronouns.
    assert readings(word, supplied=set(), lemma=None, vesum=IDENTITY["vesum"][word]) == []
    for context in ({}, {"lemma": word}, {"pos": "PRON"}, {"tags": IDENTITY["vesum"][word][0]["tags"]}):
        result = stress.verify_stress(word, **context)
        assert result["status"] == "ok" and result["stress_source"] == "trie"
        assert {m["stressed_form"] for m in result["matches"]} == {expected}
        assert all(not m.get("evidence") and m["source"] == "trie" for m in result["matches"])


def test_rule_2_same_lemma_wrong_pos_is_not_a_join(identity_db):
    from scripts.verification.ulif_stress import joined_analyses

    pronoun = IDENTITY["vesum"]["себе"]
    row = sources_db.ulif_stress_rows("себе")[0]
    # Synthetic POS conflict with identical lemma; pronouns must not join nouns.
    assert joined_analyses({**row, "grammatical_label": "іменник чоловічого роду"}, pronoun) == []
    assert joined_analyses({**row, "grammatical_label": "synthetic-unknown-pos"}, pronoun) == []
    assert joined_analyses(row, pronoun) == pronoun


def test_rule_2_reflexive_and_age_join_all_source_alternatives(identity_db):
    reflexive = stress.verify_stress("себе")
    assert reflexive["status"] == "ambiguous" and reflexive["stress_source"] == "ulif"
    assert {m["stressed_form"] for m in reflexive["matches"]} == {"се́бе", "себе́"}
    assert all({e["entry_id"] for e in m["evidence"]} == {212855} for m in reflexive["matches"])
    genitive = stress.verify_stress("себе", tags="Case=Gen")
    assert genitive["status"] == "ok" and genitive["matches"][0]["stressed_form"] == "себе́"
    age = stress.verify_stress("віку")
    assert age["status"] == "ambiguous" and age["stress_source"] == "ulif"
    assert {m["stressed_form"] for m in age["matches"]} == {"ві́ку", "віку́"}
    assert stress.verify_stress("віку", lemma="віко")["matches"][0]["stressed_form"] == "ві́ку"
    assert stress.verify_stress("віку", tags="Case=Gen")["status"] == "ok"


def test_rule_2_partial_coverage_uses_trie_only_for_uncovered_analyses(identity_db):
    # Retain the real masculine вік rows; the real neuter віко analysis lacks ULIF.
    identity_db.execute("DELETE FROM ulif_forms WHERE entry_id=43407")
    result = stress.verify_stress("віку")
    assert result["status"] == "ambiguous" and result["stress_source"] == "mixed"
    assert {m["source"] for m in result["matches"]} == {"ulif", "trie"}
    (fallback,) = [m for m in result["matches"] if m["source"] == "trie"]
    assert fallback["stressed_form"] == "ві́ку"
    assert {r["source"] for r in fallback["supporting_readings"]} == {"ulif", "trie"}
    assert all(v["lemma"] == "віко" for v in fallback["supporting_readings"][1]["vesum_analyses"])
    covered = stress.verify_stress("віку", lemma="вік", tags="Case=Gen")
    assert covered["status"] == "ok" and covered["stress_source"] == "ulif"
    uncovered = stress.verify_stress("віку", lemma="віко")
    assert uncovered["status"] == "ok" and uncovered["stress_source"] == "trie"
    assert uncovered["matches"][0]["stressed_form"] == "ві́ку"


def test_rule_2_missing_fallback_cannot_promote_covered_reading(identity_db, monkeypatch):
    identity_db.execute("DELETE FROM ulif_forms WHERE entry_id=43407")
    monkeypatch.setattr(stress, "_trie_value", lambda *args: None)
    result = stress.verify_stress("віку")
    assert result["status"] == "ambiguous"
    assert {m["stressed_form"] for m in result["matches"]} == {"ві́ку", "віку́"}
    assert result["uncovered_vesum_analyses"]
    assert stress.verify_stress("віку", lemma="вік")["status"] == "ambiguous"


def test_rule_2_missing_vesum_never_admits_unjoined_rows(identity_db, monkeypatch):
    assert stress.verify_stress(IDENTITY["unjoined_ulif_only_form"])["status"] == "pending"
    monkeypatch.setattr(stress, "_vesum_lookup", lambda _: [])
    result = stress.verify_stress("село")
    assert result["stress_source"] == "trie"
    assert all(not m.get("evidence") for m in result["matches"])


def test_comparison_excludes_foreign_lemma_and_preserves_raw_evidence(identity_db):
    record = stress_comparison.compare_form("вона")
    assert record["category"] == "trie_only" and record["ulif"] == []
    assert {r["entry_id"] for r in record["unjoined_ulif"]} == {9434}
    assert record["uncovered_vesum"] == IDENTITY["vesum"]["вона"]


def test_rule_2_partial_agreement_is_one_choice_with_fallback_provenance(identity_db):
    identity_db.execute("DELETE FROM ulif_forms WHERE entry_id=43407 OR id=646599")
    result = stress.verify_stress("віку")
    assert result["status"] == "ok" and result["stress_source"] == "trie"
    (match,) = result["matches"]
    assert match["stressed_form"] == "ві́ку"
    assert {v["lemma"] for v in match["vesum_analyses"]} == {"вік", "віко"}
    assert stress._compact_stress_reading(match)["supporting_readings"] == match["supporting_readings"]


def test_rule_2_partial_packed_agreement_never_borrows_teaching_choice(captured_db, monkeypatch):
    from scripts.pipeline import stress_annotator as annotator

    # Synthetic additional analysis; real розбір rows and trie pack dual positions.
    analyses = IDENTITY["vesum"]["розбір"] + [{"lemma": "synthetic-uncovered", "pos": "noun", "tags": "noun:m:v_naz"}]
    monkeypatch.setattr(stress, "_vesum_lookup", lambda _: analyses)
    result = stress.verify_stress("розбір")
    assert result["status"] == "ok" and result["stress_source"] == "trie"
    (match,) = result["matches"]
    assert match["pedagogical_conflict"] is True
    assert stress.spoken_stressed_form(match) is None
    assert annotator._oracle_choice("розбір") is None


@pytest.mark.parametrize("word", ["тисяча", "тисячу"])
def test_rule_2_nominal_numeral_uses_vesum_noun_pos(identity_db, word):
    from scripts.verification.ulif_stress import analysis_features

    (analysis,) = IDENTITY["vesum"][word]
    assert {t for t in analysis_features(analysis) if t.startswith("upos=")} == {"upos=NOUN"}
    result = stress.verify_stress(word, tags=analysis["tags"])
    assert result["status"] == "ok" and result["stress_source"] == "ulif"
    record = stress_comparison.compare_form(word)
    assert record["category"] == "agree" and record["uncovered_vesum"] == []


def test_multivalued_features_never_depend_on_set_iteration_order():
    from scripts.verification.ulif_stress import compatible

    assert compatible({"upos=NOUN"}, {"upos=NOUN", "upos=NUM"})
    assert compatible({"Case=Gen"}, {"Case=Gen", "Case=Acc"})
