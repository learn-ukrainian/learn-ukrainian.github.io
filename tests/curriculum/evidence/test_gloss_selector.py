"""Learner-sense selection: source spans, stress collisions and typed gaps."""

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import codes, lock, sources, verify, words


def row(row_id, translations, word="synthetic", pos="noun"):
    return {"id": row_id, "word": word, "pos": pos, "translations": json.dumps(translations)}


def payload(glosses, pos="noun"):
    return {"pos": [pos], "glosses": glosses}


def test_stress_index_preserves_rows_and_hashes(synthetic_sources):
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            "INSERT INTO dmklinger_uk_en VALUES (?,?,?,?,?,?)",
            (8228, "приві́т", "noun", '["greeting"]', "", "captured spelling"),
        )
        conn.execute(
            "INSERT INTO dmklinger_uk_en VALUES (?,?,?,?,?,?)",
            (21536, "приві́т", "particle", '["hello (informal) (interjection)"]', "", "captured spelling"),
        )
    with sources.Sources(sources_db=synthetic_sources) as api:
        rows = api.gloss_rows([("привіт", "noun")]).raw["привіт", "noun"]
        assert rows[0]["word"] == "приві́т"
        original = dict(api._db().execute("SELECT * FROM dmklinger_uk_en WHERE id=8228").fetchone())
        assert rows == [original]
        assert sources.row_digest(rows[0]) == sources.row_digest(original)
        assert [r["id"] for r in api.gloss_rows([("привіт", "part")]).raw["привіт", "part"]] == [21536]
        assert api.gloss_rows([("приві", "noun")]).raw["приві", "noun"] == []


def test_collision_takes_the_first_row_unless_a_ulif_key_pins_another():
    rows = [row(1, ["castle"], "за́мок"), row(2, ["lock"], "замо́к")]
    word = {"lemma": "замок", "pos": "noun"}
    first = sources.select_gloss(word, rows, payload(["castle"]))
    assert (first.gloss, first.ref["id"], first.reason) == ("castle", 1, None)
    assert [c["id"] for c in first.candidates] == [1, 2, None]
    word["ulif"] = {"key": ["замо́к", 2]}
    pinned = sources.select_gloss(word, rows, payload(["castle"]))
    assert (pinned.gloss, pinned.ref["id"]) == ("lock", 2)


def test_pinned_vesum_entry_binds_the_row_by_its_stressed_lemma():
    rows = [row(1, ["castle"], "за́мок"), row(2, ["lock"], "замо́к")]
    word = {
        "lemma": "замок",
        "pos": "noun",
        "forms": [{"form": "замок", "stressed": "замо́к", "tags": "noun:inanim:m:v_naz"}],
    }
    assert sources.select_gloss(word, rows, None).gloss == "lock"


@pytest.mark.parametrize(
    "dmk,kaikki,expected",
    [
        # Kaikki does not list "primary" and leads with another head of the row.
        (["primary", "shared"], ["shared"], "shared"),
        (["primary", "shared"], ["other", "primary", "shared"], "primary"),
        (["(rare) old; primary", "shared"], ["other", "primary"], "primary"),
        (["alternative form of primary", "shared"], ["alternative form of other", "shared"], "shared"),
        (["malformed)", "shared"], ["other", "shared"], "shared"),
        (["primary; shared"], [], "primary"),
        (["primary, shared"], [], "primary"),
        (["primary; primary"], [], "primary"),
        (["primary"], ["other"], "primary"),
        (["primary"], ["alternative form of other"], "primary"),
    ],
)
def test_plain_first_meaning_and_kaikki_tiebreak(dmk, kaikki, expected):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"}, [row(1, dmk)], payload(kaikki) if kaikki else None
    )
    assert result.gloss == expected
    assert result.reason is None


@pytest.mark.parametrize(
    "sense,parts,spans",
    [
        (
            "so that, in order that; in order to",
            ["so that, in order that", "in order to"],
            ["so that", "in order that", "in order to"],
        ),
        ("your (singular; one owner)", ["your (singular; one owner)"], ["your (singular; one owner)"]),
        (
            "first [note (nested; note)]; second",
            ["first [note (nested; note)]", "second"],
            ["first [note (nested; note)]", "second"],
        ),
        ("bad); second", [], []),
        (
            "boot; sturdy footwear covering the foot, often for winter use",
            ["boot", "sturdy footwear covering the foot, often for winter use"],
            ["boot", "sturdy footwear covering the foot, often for winter use"],
        ),
    ],
)
def test_sub_senses_split_only_outer_semicolons(sense, parts, spans):
    assert sources._sub_senses(sense) == parts
    assert sources._sense_spans(sense) == spans


def test_disambiguating_qualifier_is_kept_and_meta_glosses_refused():
    word = {"lemma": "synthetic", "pos": "noun"}
    result = sources.select_gloss(word, [row(1, ["billion (short scale)"])], payload(["billion (short scale)"]))
    assert result.gloss == "billion (short scale)"
    result = sources.select_gloss(word, [row(1, ["alternative form of something"])], None)
    assert result.gloss is None


def test_a_long_first_meaning_yields_to_the_next_learner_head():
    long_meaning = "distinct meaning " + "qualifier " * 9
    assert sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"}, [row(1, ["short", long_meaning])], None
    ).gloss == ("short")
    assert sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"}, [row(1, [long_meaning, "short"])], None
    ).gloss == ("short")


@pytest.fixture(scope="module")
def a1_source_capture():
    root = Path(__file__).resolve().parents[3]
    records = yaml.safe_load((root / "curriculum/l2-uk-en/evidence/a1/_words.yaml").read_text())["words"]
    # Captured source bytes keep these checks runnable in CI without corpus DBs.
    captured = json.loads((Path(__file__).parent / "fixtures/a1_gloss_candidates.json").read_text())["records"]
    return records, captured


def test_current_a1_selection_and_source_span_property(a1_source_capture):
    records, captured = a1_source_capture
    assert {w["id"] for w in records} == set(captured)
    rows = {(entry["lemma"], entry["pos"]): entry["rows"] for entry in captured.values()}
    kaikki = {entry["lemma"]: entry["kaikki"] for entry in captured.values()}
    for word in records:
        matched = rows[word["lemma"], word["pos"]]
        builder = sources.select_gloss(
            word, matched, kaikki[word["lemma"]], ulif_entries=captured[word["id"]]["ulif_entries"]
        )
        if builder.gloss is None:
            assert builder.reason
            continue
        assert sources.is_learner_gloss(builder.gloss), word["id"]
        if builder.source == sources.MEANING_SOURCE:
            # The request's ULIF/VESUM-checked meaning names a sense no open dictionary spells.
            assert builder.gloss == word["meaning"], word["id"]
            continue
        if builder.ref:
            cited = next(r for r in matched if r["id"] == builder.ref["id"])
            assert builder.ref["row_sha256"] == sources.row_digest(cited)
            spans = json.loads(cited["translations"])
        else:
            spans = kaikki[word["lemma"]]["glosses"]
        shown = builder.gloss.removeprefix("to ") if word["pos"] == "verb" else builder.gloss
        assert any(shown in span for span in spans), word["id"]
    for lemma, pos, expected in [("добрий", "adj", "good"), ("день", "noun", "day")]:
        word = next(w for w in records if (w["lemma"], w["pos"]) == (lemma, pos))
        assert sources.select_gloss(word, rows[lemma, pos], kaikki[lemma]).gloss == expected


@pytest.mark.parametrize("provider", ["dmk", "kaikki"])
@pytest.mark.parametrize("glosses", [["one", "one"], ["one; one"], ["one, one"], ["one", "(rare) two"], ["one", "two"]])
def test_sole_source_gives_its_first_plain_head(provider, glosses):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"},
        [row(1, glosses)] if provider == "dmk" else [],
        payload(glosses) if provider == "kaikki" else None,
    )
    assert result.gloss == "one"
    assert result.source == ("dmklinger_uk_en" if provider == "dmk" else "kaikki_wiktionary")


def test_cited_ids_exclude_incidental_mentions_and_include_uses():
    plan = {
        "note": "W-999",
        "lessons": [
            {
                "inventory": {
                    "vocabulary": {
                        "core": [{"evidence": "W-001"}],
                        "incidental": [{"evidence": "W-002"}],
                        "recycled": ["W-003"],
                    }
                },
                "steps": [{"uses": {"vocabulary": ["W-004"]}}],
            }
        ],
    }
    assert verify.cited_gloss_ids(plan) == {"W-001", "W-002", "W-003", "W-004"}


@pytest.mark.parametrize(
    "forms,exempt", [([], False), ([{"tags": "noun:prop"}], True), ([{"tags": "noun:prop"}, {"tags": "noun"}], False)]
)
def test_plan_gate_missing_and_proper_name(synthetic_sources, forms, exempt):
    word = {"id": "W-001", "lemma": "synthetic", "pos": "noun", "forms": forms}
    with sources.Sources(sources_db=synthetic_sources) as api:
        errors = verify.verify_plan_glosses({"core": ["W-001"]}, {"words": [word]}, "a1/test-mod", api)
    assert bool(errors) is not exempt
    if errors:
        assert codes.GLOSS_MISSING in errors[0]
        assert "a1/test-mod W-001 (synthetic)" in errors[0]
        assert "builder reason=" in errors[0]


def test_plan_gate_bound_and_mismatch(synthetic_sources):
    word = {"id": "W-001", "lemma": "synthetic", "pos": "noun", "gloss_en": "seed; family"}
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET translations=? WHERE pos='noun'", (json.dumps(["seed", "family"]),))
    with sources.Sources(sources_db=synthetic_sources) as api:
        errors = verify.verify_plan_glosses({"uses": ["W-001"]}, {"words": [word]}, "a1/test-mod", api)
    assert any(codes.GLOSS_NOT_LEARNER_SENSE in error for error in errors)
    assert any(codes.GLOSS_MISMATCH in error for error in errors)
    assert not any(codes.GLOSS_SENSE_UNRESOLVED in error for error in errors)


@pytest.mark.parametrize(
    "stored,expected", [(None, codes.GLOSS_MISSING), ("seed", None), ("family", codes.GLOSS_MISMATCH)]
)
def test_polysemous_row_gates_on_its_first_meaning(synthetic_sources, stored, expected):
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET translations=? WHERE pos='noun'", (json.dumps(["seed", "family"]),))
    word = {"id": "W-001", "lemma": "synthetic", "pos": "noun"}
    if stored:
        word["gloss_en"] = stored
    with sources.Sources(sources_db=synthetic_sources) as api:
        errors = verify.verify_plan_glosses({"uses": ["W-001"]}, {"words": [word]}, "a1/test-mod", api)
    assert [error.split(":", 1)[0] for error in errors] == ([expected] if expected else [])


@pytest.mark.parametrize(
    "dmk,kaikki,pos,expected",
    [
        (["(transitive) to write", "to notify"], ["write", "to notify"], "verb", "to write"),
        (["your (belonging to you (singular; one owner)) (determiner)", "thy"], ["your", "thy"], "adj", "your"),
        (["roof (the cover at the top of a building)"], [], "noun", "roof"),
        (
            ["fence made out of vines and branches; wattle", "fence (barrier)"],
            ["fence made out of vines and branches; wattle"],
            "noun",
            "fence made out of vines and branches",
        ),
    ],
)
def test_normalized_heads(dmk, kaikki, pos, expected):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": pos},
        [row(1, dmk, pos="adjective" if pos == "adj" else pos)],
        payload(kaikki, pos) if kaikki else None,
    )
    assert result.gloss == expected


@pytest.mark.parametrize(
    "label",
    [
        "obsolete",
        "obsolescent",
        "obsolescence",
        "archaic",
        "dated",
        "dialectal",
        "dialect",
        "colloquial",
        "colloquially",
        "colloq.",
        "colloqiual",
        "colloqual",
        "figurative",
        "figuratively",
        "technical",
        "informal",
        "rare",
        "rarely",
        "historic",
        "historical",
        "nonstandard",
        "non-standard",
        "slang",
        "vulgar",
        "formal",
        "literary",
        "poetic",
        "poetical",
        "derogatory",
        "pejorative",
        "offensive",
        "euphemistic",
        "humorous",
        "regional",
        "familiar",
        "childish",
        "endearing",
        "endearment",
        "ironic",
        "ironically",
        "proscribed",
        "uncommon",
        "rude",
        "taboo",
        "jocular",
        "polite",
        "psychology",
        "chemistry",
        "anatomy",
        "linguistics",
    ],
)
@pytest.mark.parametrize("edge", ["leading", "trailing", "nested", "square"])
def test_register_marked_spans_yield_to_the_plain_meaning(label, edge):
    marked = {
        "leading": f"({label}) old",
        "trailing": f"old ({label})",
        "nested": f"old (sense ({label}))",
        "square": f"[{label}] old",
    }[edge]
    word = {"lemma": "synthetic", "pos": "noun"}
    result = sources.select_gloss(word, [row(1, [marked, "modern"])], payload([marked]))
    # Preserve the complete label matrix: nested descriptive notes keep their
    # head; an outer register-only note is passed over for the plain meaning.
    assert result.gloss == ("old" if edge == "nested" else "modern")
    # A row with only a restricted sense still gives its head, without the label.
    assert sources.select_gloss(word, [row(1, [marked])], None).gloss == "old"


@pytest.mark.parametrize(
    "sense,expected",
    [
        ("dad (informal: a father)", "dad"),
        ("mum (mother (informal, familiar))", "mum"),
        ("kid (child (colloq.))", "kid"),
        ("thanks (a polite reaction to help)", "thanks"),
        ("old (sense (rare))", "old"),
    ],
)
def test_descriptive_and_nested_register_notes_do_not_restrict(sense, expected):
    assert not any(sources._register_note(note) for note in sources._outer_notes(sense))
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"}, [row(1, [sense, "modern"])], payload([expected])
    )
    assert result.gloss == expected
    assert sources._gloss_head(sense, keep_qualifiers=True) == sense


@pytest.mark.parametrize("note", ["+ instrumental", "+ genitive", "+ instrumental or more rarely genitive"])
def test_government_note_is_grammar_and_does_not_restrict(note):
    assert not sources._register_note(note)
    assert sources._GRAMMATICAL_LABEL.fullmatch(note)
    assert sources._gloss_head(f"between ({note})", keep_qualifiers=True) == "between"
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, [f"between ({note})", "elsewhere"], pos="preposition")],
        payload(["between"], "prep"),
    )
    assert result.gloss == "between"


@pytest.mark.parametrize("qualifier", ["Beta vulgaris", "archaeology", "information"])
def test_register_stems_do_not_match_unrelated_words(qualifier):
    marked = f"old ({qualifier})"
    result = sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [row(1, [marked, "modern"])], payload(["old"]))
    assert result.gloss == "old"


@pytest.mark.parametrize(
    "glosses",
    [
        ["circle", "about (in the immediate neighborhood of)"],
        ["circle", "around (surrounding)"],
        ["around (surrounding)", "malformed)"],
    ],
)
def test_mixed_pos_kaikki_entry_neither_glosses_nor_reorders(glosses):
    """Its glosses are not split by POS, so a noun sense could pose as the preposition."""
    mixed = {"pos": ["noun", "prep"], "glosses": glosses}
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, ["about (in the immediate neighborhood of), around (surrounding) (preposition)"], pos="preposition")],
        mixed,
    )
    assert (result.gloss, result.source) == ("about", "dmklinger_uk_en")
    alone = sources.select_gloss({"lemma": "synthetic", "pos": "prep"}, [], mixed)
    assert (alone.gloss, alone.reason) == (None, "kaikki_multi_pos")


def test_row_with_only_restricted_senses_yields_to_a_row_with_a_plain_one():
    rows = [
        row(1, ["(dialectal) bundle"], "зв'я́зок"),
        row(2, ["connection (point at which things are joined)"], "зв'язо́к"),
    ]
    result = sources.select_gloss({"lemma": "зв'язок", "pos": "noun"}, rows, None)
    assert (result.gloss, result.ref["id"]) == ("connection", 2)


@pytest.mark.parametrize(
    "sense",
    [
        "a shoe, which covers the foot and extends above the ankle",
        "Expressing pain, fear, surprise, joy, disappointment, anger, hatred, etc (interjection)",
    ],
)
def test_definition_commas_do_not_create_learner_fragments(sense):
    assert sources._sense_spans(sense) == []


def homonym(index, headword="synthetic", label="noun"):
    return {"id": index, "homonym_index": index, "canonical_headword": headword, "grammatical_label": label}


def test_same_spelling_homonyms_are_not_withheld():
    word = {"lemma": "synthetic", "pos": "noun", "ulif": {"key": ["synthetic", 1]}}
    result = sources.select_gloss(
        word, [row(1, ["seed", "family"])], payload(["seed", "family"]), ulif_entries=[homonym(1), homonym(2)]
    )
    assert (result.gloss, result.reason) == ("seed", None)


@pytest.mark.parametrize(
    "lemma,expected",
    [
        # The request's meaning is the lesson's sense (ULIF займенник; "thou" is the archaic row head).
        ("ти", "you"),
        ("поки", "as"),
        ("писати", "to write"),
        ("твій", "your"),
        ("радіти", "to rejoice"),
        ("додому", "home"),
        ("малина", "raspberry"),
        ("я", "I"),
        ("вона", "she"),
        ("і", "and"),
        ("читати", "to read"),
        ("пити", "to drink"),
        ("бачити", "to see"),
        ("чути", "to hear"),
        ("рука", "hand"),
        ("єнот", "raccoon"),
        ("дах", "roof"),
        ("алфавіт", "alphabet"),
        ("люпин", "lupin"),
        ("тин", "fence made out of vines and branches"),
        ("мільярд", "billion (short scale)"),
        ("їжа", "food"),
        ("чобіт", "boot"),
        ("чай", "tea"),
        # ULIF коло 2 (прийменник) is «біля» first; no open dictionary spells "near".
        ("коло", "near"),
        ("до", "before"),
        ("перед", "before"),
        ("між", "between"),
        ("хто", "who"),
        ("що", "what"),
        ("ґрунт", "ground"),
        ("маля", "infant"),
        ("мама", "mama"),
        ("тато", "dad"),
        ("од", "from"),
        ("щоб", "so that"),
        ("щоби", "so that"),
        ("день", "day"),
        ("зо", "with"),
        ("кувати", "to forge"),
        # The request note's lead clause names the primer's meaning.
        ("коса", "braid"),
        ("сім'я", "family"),
        ("зв'язок", "connection"),
        # The request meaning: ULIF lists привіт (фам.) among greetings on meeting.
        ("привіт", "hi"),
        ("грати", "to act"),
        ("свято", "festival"),
        # ВТС: дзюрчати is flowing water's monotone babble; себе refers to the subject in any person.
        ("дзюрчати", "to gurgle"),
        ("себе", "oneself"),
        ("хліб", "bread"),
    ],
)
def test_reviewer_examples_from_captured_sources(lemma, expected, a1_source_capture):
    records, captured = a1_source_capture
    word = next(w for w in records if w["lemma"] == lemma)
    c = captured[word["id"]]
    result = sources.select_gloss(word, c["rows"], c["kaikki"], ulif_entries=c["ulif_entries"])
    assert result.gloss == expected
    assert result.reason is None


def test_builder_store_verifier_round_trip_and_mutation(synthetic_sources, synthetic_vesum, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_indices": [0],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            "UPDATE dmklinger_uk_en SET translations=? WHERE pos='noun'",
            (json.dumps(["first translation (explanation with nested (annotations))"]),),
        )
    req = tmp_path / "req.yaml"
    req.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {"lemma": "synthetic", "pos": "noun", "want": "new", "entry": {"source": "vesum", "entry_id": 10}},
                ],
            }
        )
    )
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        built = words.build_words("a1", req, evidence_dir=tmp_path, sources_instance=api, mcp_commit="a" * 40)
        assert built["store"]["words"][0]["gloss_en"] == "first translation"
        checked = verify.verify_words_store("a1", evidence_dir=tmp_path, sources_instance=api)
        assert checked["errors"] == []
        assert checked["warnings"] == []
        assert checked["status"] == "ok"
        path = tmp_path / "_words.yaml"
        mutated = yaml.safe_load(path.read_text())
        mutated["words"][0]["gloss_en"] = "wrong learner head"
        lock.write(path, lock.yaml_bytes(mutated))
        checked = verify.verify_words_store("a1", evidence_dir=tmp_path, sources_instance=api)
        assert any(codes.GLOSS_MISMATCH in error for error in checked["errors"])
        assert checked["status"] == "failed"


def test_homonym_pos_join_does_not_select_by_gender():
    word = {"lemma": "synthetic", "pos": "noun", "forms": [{"tags": "noun:f:v_naz"}]}
    entries = [homonym(1, label="іменник чоловічого або жіночого роду"), homonym(2, label="іменник жіночого роду")]
    result = sources.select_gloss(word, [row(1, ["one", "two"])], payload(["one", "two"]), ulif_entries=entries)
    assert result.gloss == "one"
KOSA = ["braid (hairstyle)", "braided hair", "scythe (farm tool)", "spit (low, narrow, sandy peninsula)"]
@pytest.mark.parametrize(
    "note,expected",
    [
        ("Braid (hair, as in the primer sentence «Поліна помила коси»): decodable noun", "braid"),
        ("Scythe: harvest picture", "scythe"),
        ("Decodable noun with letter K from primer page 81", "braid"),
        (None, "braid"),
    ],
)
def test_request_note_lead_names_the_lessons_meaning(note, expected):
    word = {"lemma": "коса", "pos": "noun", "note": note}
    entries = [homonym(4, "коса́"), homonym(5, "коса́"), homonym(6, "коса́")]
    payload_mixed = {"pos": ["adj", "noun"], "glosses": ["A standard, three-strand hair braid", "scythe"]}
    result = sources.select_gloss(word, [row(10065, KOSA, "коса́")], payload_mixed, ulif_entries=entries)
    assert (result.gloss, result.reason) == (expected, None)


def test_note_is_matched_only_in_its_lead_clause_and_as_a_whole_word():
    rows = [row(1, ["at (time)", "on (surface)"], "synthetic", "preposition")]
    word = {"lemma": "synthetic", "pos": "prep", "note": "closed class: taught at position 28; on the page"}
    assert sources.select_gloss(word, rows, None).gloss == "at"
    word["note"] = "Ontology: no whole-word match"
    assert sources.select_gloss(word, rows, None).gloss == "at"
    word["note"] = "On: surface sense"
    assert sources.select_gloss(word, rows, None).gloss == "on"


@pytest.mark.parametrize(
    "left,right,same",
    [("raspberry", "raspberries", True), ("braid", "braids", True), ("box", "boxes", True), ("hand", "arm", False)],
)
def test_plural_variants_are_one_head(left, right, same):
    assert sources._same_head(left, right) is same
    assert sources._same_head(right, left) is same


def test_no_dictionary_row_is_the_only_withholding():
    result = sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [], None)
    assert (result.gloss, result.reason) == (None, "kaikki_absent")


def test_request_meaning_cites_the_candidate_spelled_the_same():
    word = {"lemma": "synthetic", "pos": "noun", "meaning": "you"}
    result = sources.select_gloss(word, [row(1, ["thou", "you"])], None)
    assert (result.gloss, result.source, result.ref["id"], result.reason) == ("you", "dmklinger_uk_en", 1, None)


def test_request_meaning_no_dictionary_spells_is_the_gloss():
    word = {"lemma": "synthetic", "pos": "prep", "meaning": "near"}
    result = sources.select_gloss(word, [row(1, ["about", "around"], pos="preposition")], None)
    assert (result.gloss, result.source, result.ref) == ("near", sources.MEANING_SOURCE, None)
    # A word no open dictionary has at all still takes its request meaning.
    assert sources.select_gloss({**word, "meaning": "feather"}, [], None).gloss == "feather"


def test_request_meaning_precedes_note_and_reference_and_must_be_a_learner_gloss():
    word = {"lemma": "synthetic", "pos": "noun", "meaning": "plait", "note": "Braid: primer picture"}
    rows = [row(1, ["braid", "scythe"])]
    reference = {"gloss": "scythe", "match": "dictionary"}
    result = sources.select_gloss(word, rows, None, reference=reference)
    assert (result.gloss, result.by_reference) == ("plait", False)
    too_long = sources.select_gloss({**word, "meaning": "one two three four five six seven eight nine"}, rows, None)
    assert (too_long.gloss, too_long.reason) == (None, codes.GLOSS_NOT_LEARNER_SENSE)


def test_reference_dictionary_match_chooses_the_candidate():
    rows = [row(1, ["positioned at the upper surface of", "to, toward"], pos="preposition")]
    word = {"lemma": "synthetic", "pos": "prep"}
    plain = sources.select_gloss(word, rows, None)
    assert plain.gloss == "positioned at the upper surface of"
    result = sources.select_gloss(word, rows, None, reference={"gloss": "to", "match": "dictionary"})
    assert (result.gloss, result.ref["id"], result.by_reference) == ("to", 1, True)
    # A dictionary match the rows no longer contain is a stale binding, never a silent fallback.
    stale = sources.select_gloss(word, rows, None, reference={"gloss": "onto", "match": "dictionary"})
    assert (stale.gloss, stale.reason) == (None, "reference_binding_invalid")


def test_reference_book_gloss_stands_only_without_an_equal_candidate_or_ulif_pin():
    word = {"lemma": "synthetic", "pos": "prep"}
    rows = [row(1, ["upon"], pos="preposition")]
    book = {"gloss": "on", "match": "book"}
    result = sources.select_gloss(word, rows, None, reference=book)
    assert (result.gloss, result.source, result.ref, result.by_reference) == ("on", "ohoiko_reference", None, True)
    assert sources.select_gloss(word, [], None, reference=book).gloss == "on"
    # Her gloss equal to a candidate cites the candidate.
    cited = sources.select_gloss(word, [row(1, ["upon", "on"], pos="preposition")], None, reference=book)
    assert (cited.gloss, cited.source, cited.ref["id"]) == ("on", "dmklinger_uk_en", 1)
    assert sources.select_gloss(word, rows, None, reference={"gloss": "x" * 61, "match": "book"}).reason == (
        "reference_binding_invalid"
    )
    pinned = {"lemma": "замок", "pos": "noun", "ulif": {"key": ["замо́к", 2]}}
    homonyms = [row(1, ["castle"], "за́мок"), row(2, ["lock"], "замо́к")]
    pool, ulif_pinned = sources.reference_pool(pinned, homonyms, None)
    assert ([c["span"] for c in pool], ulif_pinned) == (["lock"], True)
    assert sources.select_gloss(pinned, homonyms, None, reference={"gloss": "fort", "match": "book"}).reason == (
        "reference_binding_invalid"
    )
    assert sources.select_gloss(
        pinned, homonyms, None, reference={"gloss": "castle", "match": "dictionary"}
    ).reason == ("reference_binding_invalid")


def test_note_lead_precedes_the_reference():
    word = {"lemma": "коса", "pos": "noun", "note": "Braid (hair): primer picture"}
    rows = [row(1, ["scythe (farm tool)", "braid (hairstyle)"], "коса́")]
    result = sources.select_gloss(word, rows, None, reference={"gloss": "scythe", "match": "dictionary"})
    assert (result.gloss, result.by_reference) == ("braid", False)


def test_request_meaning_is_copied_to_the_store_and_verified(synthetic_sources, synthetic_vesum, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [{"stressed_form": w, "unstressed_form": w, "vowel_indices": [0], "override_applied": False}],
            "source": {"digest": "t" * 64},
        },
    )
    request = tmp_path / "request.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {"lemma": "synthetic", "pos": "verb", "want": "new", "meaning": "to synthesize"},
                ],
            }
        )
    )
    evidence = tmp_path / "evidence"
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words(
            "a1", request, evidence_dir=evidence, plans_dir=tmp_path, sources_instance=api, mcp_commit="a" * 40
        )
        store = yaml.safe_load((evidence / "_words.yaml").read_text())
        record = store["words"][0]
        assert (record["meaning"], record["gloss_en"], record["gloss_source"]) == (
            "to synthesize",
            "to synthesize",
            sources.MEANING_SOURCE,
        )
        assert "gloss_ref" not in record
        result = verify.verify_words_store("a1", evidence_dir=evidence, plans_dir=tmp_path, sources_instance=api)
        assert not result["errors"], result["errors"]
        # A changed meaning is a gloss mismatch, not a silently accepted value.
        record["meaning"] = "to make"
        lock.write(evidence / "_words.yaml", lock.yaml_bytes(store))
        checked = verify.verify_words_store("a1", evidence_dir=evidence, plans_dir=tmp_path, sources_instance=api)
        assert any(codes.GLOSS_MISMATCH in error for error in checked["errors"])
