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


@pytest.mark.parametrize("glosses", [["family", "seed"], ["to forge", "to cuckoo"], ["bond", "communication"]])
def test_first_polysemous_agreement_wins(glosses):
    result = sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [row(1, glosses)], payload(glosses))
    assert result.gloss == glosses[0]
    assert result.reason is None


@pytest.mark.parametrize("pos", ["noun", "verb", "adj", "adv", "numr", "part", "prep", "conj"])
@pytest.mark.parametrize("dmk", [["primary", "shared"], ["primary, shared"], ["primary; shared"]])
def test_first_dmklinger_head_stands_when_kaikki_leads_with_an_unlisted_head(pos, dmk):
    source_pos = {"numr": "num", "part": "particle"}.get(pos, pos)
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": pos},
        [row(1, dmk, pos="adjective" if pos == "adj" else pos)],
        payload(["other", "shared"], source_pos),
    )
    assert result.gloss == ("to primary" if pos == "verb" else "primary")
    assert result.source == "dmklinger_uk_en"


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


def test_kaikki_names_the_plain_head_when_it_lacks_the_dmklinger_first():
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"},
        [row(1, ["daylight (between sunrise and sunset)", "day (24 hours)"])],
        payload(["day"]),
    )
    assert (result.gloss, result.source) == ("day", "dmklinger_uk_en")


def test_disambiguating_qualifier_is_kept_and_meta_glosses_refused():
    word = {"lemma": "synthetic", "pos": "noun"}
    result = sources.select_gloss(word, [row(1, ["billion (short scale)"])], payload(["billion (short scale)"]))
    assert result.gloss == "billion (short scale)"
    result = sources.select_gloss(word, [row(1, ["alternative form of something"])], None)
    assert result.gloss is None


@pytest.mark.parametrize("value", ["x" * 61, "one two three four five six seven eight nine", "bad)", ""])
def test_bound_is_not_a_truncator(value):
    assert not sources.is_learner_gloss(value)
    result = sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [row(1, [value])], None)
    assert result.gloss is None


def test_a_long_first_meaning_yields_to_the_next_learner_head():
    long_meaning = "distinct meaning " + "qualifier " * 9
    assert sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"}, [row(1, ["short", long_meaning])], None
    ).gloss == ("short")
    assert sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"}, [row(1, [long_meaning, "short"])], None
    ).gloss == ("short")


def test_kaikki_single_sense_and_multi_pos():
    assert sources.aligned_kaikki_gloss(payload(["day"]), "noun", False) == ("day", None)
    assert sources.aligned_kaikki_gloss({"pos": ["noun", "intj"], "glosses": ["greeting"]}, "noun", False) == (
        None,
        "kaikki_multi_pos",
    )


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


def test_all_187_records_are_glossed_unless_no_source_row_aligns(a1_source_capture):
    """Nothing is withheld for polysemy or homonymy; only a missing learner head withholds."""
    records, captured = a1_source_capture
    assert len(records) == len(captured) == 187
    withheld = []
    for word in records:
        c = captured[word["id"]]
        result = sources.select_gloss(word, c["rows"], c["kaikki"], ulif_entries=c["ulif_entries"])
        pronoun = any("pron" in f.get("tags", "").split(":") for f in word.get("forms", []))
        rows = sources.filter_pronominal_gloss_rows(c["rows"], word["lemma"], word["pos"], pronoun)
        aligned, _ = sources.aligned_kaikki_senses(c["kaikki"], word["pos"], pronoun)
        if result.gloss is None:
            withheld.append(word["id"])
            # No aligned row, or only non-learner spans ("a female given name, ...").
            assert not any(sources.is_learner_gloss(c["gloss"]) for c in result.candidates), word["id"]
            assert rows or not aligned, (word["id"], result.reason)
        assert result.reason != codes.GLOSS_SENSE_UNRESOLVED
    assert len(withheld) <= 28


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
    "stored,expected", [(None, codes.GLOSS_MISSING), ("primary", None), ("shared", codes.GLOSS_MISMATCH)]
)
def test_plan_gate_keeps_the_first_head_kaikki_also_lists(
    synthetic_sources, synthetic_kaikki_side_db, stored, expected
):
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET translations=? WHERE pos='noun'", (json.dumps(["primary", "shared"]),))
    with sqlite3.connect(synthetic_kaikki_side_db) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO kaikki VALUES (?, ?)", ("synthetic", json.dumps(payload(["other", "primary"])))
        )
        conn.execute("UPDATE meta SET value='3' WHERE key='row_count'")
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
    "note",
    ["figuratively", "nonstandard", "rare", "intransitive, colloquial", "formal, transitive", "colloq."],
)
def test_register_note_requires_whole_labels(note):
    assert sources._register_note(note)


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


def test_babtsia_shaped_descriptive_note_is_not_a_register_label():
    result = sources.select_gloss(
        {"lemma": "бабця", "pos": "noun"},
        [row(1, ["granny (informal: a grandmother)", "grandmother"], word="бабця")],
        payload(["granny"]),
    )
    assert result.gloss == "granny"


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


@pytest.mark.parametrize("label", ["2nd-person familiar, singular only", "second-person plural or formal"])
def test_pronoun_person_labels_do_not_make_the_sense_restricted(label):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun", "forms": [{"tags": "noun:pron"}]},
        [row(1, ["your", "thy"], pos="pronoun")],
        payload([f"your ({label})"], "pron"),
    )
    assert result.gloss == "your"


def test_preposition_takes_the_head_kaikki_names_when_it_lacks_the_first():
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [
            row(
                1,
                ["about (in the immediate neighborhood of) (preposition)", "around (surrounding) (preposition)"],
                pos="preposition",
            )
        ],
        payload(["around (surrounding)"], "prep"),
    )
    assert result.gloss == "around"


@pytest.mark.parametrize(
    "sense",
    [
        "about (in the immediate neighborhood of) (preposition)",
        "about (in a particular place with a distinct and otherwise ambiguous meaning)",
    ],
)
def test_preposition_shows_its_head_without_the_trailing_definition(sense):
    result = sources.select_gloss({"lemma": "synthetic", "pos": "prep"}, [row(1, [sense], pos="preposition")], None)
    assert result.gloss == "about"


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


@pytest.mark.parametrize(
    "dmk,expected",
    [
        (["(rare) secondary", "primary (+ genitive)", "minority"], "primary"),
        (["primary", "minority"], "primary"),
        (["alternative form of primary", "minority"], "minority"),
        (["(rare) minority"], "minority"),
        (["primary; minority"], "primary"),
    ],
)
def test_preposition_first_unrestricted_head(dmk, expected):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, dmk, pos="preposition")],
        {"pos": ["noun", "prep"], "glosses": ["minority"]},
    )
    assert result.gloss == expected


def test_first_row_wins_over_a_later_row():
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, ["primary"], pos="preposition"), row(2, ["minority"], pos="preposition")],
        None,
    )
    assert (result.gloss, result.ref["id"]) == ("primary", 1)


def test_row_with_only_restricted_senses_yields_to_a_row_with_a_plain_one():
    rows = [
        row(1, ["(dialectal) bundle"], "зв'я́зок"),
        row(2, ["connection (point at which things are joined)"], "зв'язо́к"),
    ]
    result = sources.select_gloss({"lemma": "зв'язок", "pos": "noun"}, rows, None)
    assert (result.gloss, result.ref["id"]) == ("connection", 2)


@pytest.mark.parametrize("punctuation", ["?", "!", "?!"])
def test_terminal_punctuation_does_not_create_distinct_heads(punctuation):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"},
        [row(1, [f"who{punctuation} (interrogative pronoun)", "who (relative pronoun)"])],
        None,
    )
    assert result.gloss == "who"
    assert sources._gloss_head(f"who (interrogative pronoun){punctuation}") == "who"


@pytest.mark.parametrize(
    "sense",
    [
        "a shoe, which covers the foot and extends above the ankle",
        "Expressing pain, fear, surprise, joy, disappointment, anger, hatred, etc (interjection)",
    ],
)
def test_definition_commas_do_not_create_learner_fragments(sense):
    assert sources._sense_spans(sense) == []


def test_long_definition_with_commas_is_one_span():
    value = "used to string together sentences, or to join fragments in chronological order"
    assert sources._sense_spans(value) == [value]
    assert sources._sense_spans("(direction) home, homewards") == ["(direction) home", "homewards"]


def homonym(index, headword="synthetic", label="noun"):
    return {"id": index, "homonym_index": index, "canonical_headword": headword, "grammatical_label": label}


def test_same_spelling_homonyms_are_not_withheld():
    word = {"lemma": "synthetic", "pos": "noun", "ulif": {"key": ["synthetic", 1]}}
    result = sources.select_gloss(
        word, [row(1, ["seed", "family"])], payload(["seed", "family"]), ulif_entries=[homonym(1), homonym(2)]
    )
    assert (result.gloss, result.reason) == ("seed", None)


def test_homonym_without_a_note_takes_the_first_rows_first_meaning():
    entries = [homonym(1, "ко́са"), homonym(2, "коса́"), homonym(3, "коса́")]
    rows = [row(1, ["cockeyed person"], "ко́са"), row(2, ["braid (hairstyle)", "scythe (farm tool)"], "коса́")]
    assert sources.select_gloss({"lemma": "коса", "pos": "noun"}, rows, None, ulif_entries=entries).gloss == (
        "cockeyed person"
    )


def test_stressed_homonym_key_binds_its_row_even_against_kaikki():
    word = {"lemma": "замок", "pos": "noun", "ulif": {"key": ["замо́к", 2]}}
    entries = [homonym(1, "за́мок"), homonym(2, "замо́к"), homonym(3, "замо́к", "verb")]
    rows = [row(1, ["castle"], "за́мок"), row(2, ["lock"], "замо́к")]
    assert sources.select_gloss(word, rows, payload(["castle"]), ulif_entries=entries).gloss == "lock"
    assert sources.select_gloss(word, rows, None, ulif_entries=entries).gloss == "lock"


@pytest.mark.parametrize(
    "lemma,expected",
    [
        ("ти", "thou"),
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
        ("коло", "about"),
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
        ("привіт", "regards"),
        ("грати", "to act"),
        ("свято", "festival"),
        ("дзюрчати", "to purl"),
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


@pytest.mark.parametrize(
    "span,expected",
    [
        ("[transitive] (formal) to write", "to write"),
        ("your [belonging to you [one owner]] (determiner)", "your"),
        ("roof (cover) (noun)", "roof"),
        ("billion (long scale)", "billion (long scale)"),
    ],
)
def test_balanced_edge_annotations(span, expected):
    assert sources._gloss_head(span) == expected


def test_definition_with_short_clauses_is_not_split():
    sense = "footwear covering the foot, often for winter use"
    assert sources._sense_spans(sense) == [sense]


def test_homonym_pos_join_does_not_select_by_gender():
    word = {"lemma": "synthetic", "pos": "noun", "forms": [{"tags": "noun:f:v_naz"}]}
    entries = [homonym(1, label="іменник чоловічого або жіночого роду"), homonym(2, label="іменник жіночого роду")]
    result = sources.select_gloss(word, [row(1, ["one", "two"])], payload(["one", "two"]), ulif_entries=entries)
    assert result.gloss == "one"


# Real-shaped rows (dmklinger and Kaikki as captured for the A1 store, #9543).
MALYNA = ["raspberry (plant)", "(uncountable, collectively) raspberries (fruit)", "raspberry (fruit)"]
I_CONJ = [
    "and (used to connect two similar words, phrases, et cetera) (conjunction)",
    "and, also, even (conjunction)",
    "Augmentative particle, even, and",
    "Expressing pain, fear, surprise, joy, disappointment, anger, hatred, etc (interjection)",
]
RUKA = ["hand (part of the fore limb)", "(anatomy) hand", "arm (upper appendage from shoulder to wrist)"]
PYSATY = ["write (to form letters, etc.)", "(transitive) to write", "(transitive) to send written information to"]
KOSA = ["braid (hairstyle)", "braided hair", "scythe (farm tool)", "spit (low, narrow, sandy peninsula)"]
MY = [
    "generic we (the speaker and at least one other person, regardless of whether it's the person being addressed)",
    "we (first-person plural)",
]


@pytest.mark.parametrize(
    "lemma,pos,row_pos,dmk,kaikki,expected",
    [
        ("малина", "noun", "noun", MALYNA, payload(["raspberries (fruit)", "raspberry (plant)"]), "raspberry"),
        ("і", "conj", "particle", I_CONJ, {"pos": ["character", "conj"], "glosses": ["and, also, even"]}, "and"),
        ("рука", "noun", "noun", RUKA, payload(["hand", "arm", "hand, handwriting"]), "hand"),
        ("писати", "verb", "verb", PYSATY, payload(["to write", "to notify"], "verb"), "to write"),
        ("ми", "noun", "pronoun", MY, payload(["we (first-person plural)"], "pron"), "we"),
    ],
)
def test_plain_first_meaning_on_real_shaped_rows(lemma, pos, row_pos, dmk, kaikki, expected):
    word = {"lemma": lemma, "pos": pos}
    if row_pos == "pronoun":
        word["forms"] = [{"tags": "noun:p:v_naz:pron:pers:1"}]
    result = sources.select_gloss(word, [row(1, dmk, lemma, row_pos)], kaikki)
    assert (result.gloss, result.source, result.reason) == (expected, "dmklinger_uk_en", None)
    assert result.ref["id"] == 1


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
    "sense,expected",
    [
        ("and (used to connect two similar words, phrases, et cetera) (conjunction)", "and"),
        ("we (first-person plural)", "we"),
        ("plum (fruit of Prunus domestica)", "plum"),
    ],
)
def test_displayed_gloss_drops_the_trailing_definition(sense, expected):
    assert sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [row(1, [sense])], None).gloss == expected


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
