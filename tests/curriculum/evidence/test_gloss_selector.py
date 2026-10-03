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


def test_collision_requires_exact_ulif_key_and_does_not_fall_back():
    rows = [row(1, ["castle"], "за́мок"), row(2, ["lock"], "замо́к")]
    word = {"lemma": "замок", "pos": "noun"}
    missing = sources.select_gloss(word, rows, payload(["castle"]))
    assert missing.gloss is None
    assert missing.reason == codes.GLOSS_SENSE_UNRESOLVED
    assert len(missing.candidates) == 2
    word["ulif"] = {"key": ["замо́к", 2]}
    result = sources.select_gloss(word, rows, payload(["castle"]))
    assert (result.gloss, result.ref["id"]) == ("lock", 2)
    assert result.ref["row_sha256"] == sources.row_digest(rows[1])


@pytest.mark.parametrize("glosses", [["family", "seed"], ["to forge", "to cuckoo"], ["bond", "communication"]])
def test_first_polysemous_agreement_wins(glosses):
    result = sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [row(1, glosses)], payload(glosses))
    assert result.gloss == glosses[0]
    assert result.reason is None


@pytest.mark.parametrize("pos", ["noun", "verb", "adj", "adv", "numr", "part", "prep", "conj"])
@pytest.mark.parametrize("dmk", [["primary", "shared"], ["primary, shared"], ["primary; shared"]])
def test_agreement_cannot_promote_a_head_that_is_first_in_neither_source(pos, dmk):
    source_pos = {"numr": "num", "part": "particle"}.get(pos, pos)
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": pos},
        [row(1, dmk, pos="adjective" if pos == "adj" else pos)],
        payload(["other", "shared"], source_pos),
    )
    assert result.gloss is None
    assert result.reason == codes.GLOSS_SENSE_UNRESOLVED


@pytest.mark.parametrize(
    "dmk,kaikki,expected",
    [
        (["primary", "shared"], ["shared"], "shared"),
        (["primary", "shared"], ["other", "primary", "shared"], "primary"),
        (["(rare) old; primary", "shared"], ["other", "primary"], "primary"),
        (["alternative form of primary", "shared"], ["alternative form of other", "shared"], None),
        (["malformed)", "shared"], ["other", "shared"], None),
        (["primary; shared"], [], None),
        (["primary, shared"], [], None),
        (["primary; primary"], [], "primary"),
        (["primary"], ["other"], None),
        (["primary"], ["alternative form of other"], None),
    ],
)
def test_anchor_agreement_and_single_source_rules(dmk, kaikki, expected):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"}, [row(1, dmk)], payload(kaikki) if kaikki else None
    )
    assert result.gloss == expected
    if expected is None:
        assert result.reason == codes.GLOSS_SENSE_UNRESOLVED


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


def test_synonym_group_can_agree_without_treating_shortness_as_meaning():
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "noun"},
        [row(1, ["daylight (between sunrise and sunset)", "day (24 hours)"])],
        payload(["day"]),
    )
    assert result.gloss == "day"
    assert result.ref["id"] == 1


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


def test_length_cannot_remove_a_competing_meaning():
    long_meaning = "distinct meaning " + "qualifier " * 9
    result = sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [row(1, ["short", long_meaning])], None)
    assert result.reason == codes.GLOSS_SENSE_UNRESOLVED
    assert result.gloss is None


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
        assert any(builder.gloss in span for span in spans), word["id"]
    for lemma, pos, expected in [("добрий", "adj", "good"), ("день", "noun", "day")]:
        word = next(w for w in records if (w["lemma"], w["pos"]) == (lemma, pos))
        assert sources.select_gloss(word, rows[lemma, pos], kaikki[lemma]).gloss == expected


def test_all_187_records_corroboration_never_selects_a_nonfirst_sense(a1_source_capture):
    records, captured = a1_source_capture
    assert len(records) == len(captured) == 187
    glossed = mixed_checked = corroborated = 0

    def first_raw_head(raw_senses, pos):
        # Independent oracle for the captured corpus: strip balanced notes
        # with plain strings and split only at outer commas/semicolons. Never
        # search later senses for the emitted value or use selector helpers.
        register_labels = {
            "archaic",
            "colloquial",
            "dated",
            "dialectal",
            "figurative",
            "formal",
            "historical",
            "informal",
            "obsolete",
            "nonstandard",
            "non-standard",
            "rare",
            "slang",
            "technical",
        }
        for raw in raw_senses:
            parts, notes, note, depth, head = [], [], "", 0, ""
            for char in raw:
                if char in "([":
                    depth += 1
                    if depth > 1:
                        note += char
                elif char in ")]":
                    depth -= 1
                    if depth:
                        note += char
                    else:
                        notes.append(note.strip())
                        if note.strip() in {"short scale", "long scale"}:
                            head += f"({note.strip()})"
                        note = ""
                elif depth:
                    note += char
                elif char == ";":
                    parts.append((head, notes))
                    head, notes = "", []
                elif char == ",":
                    # Keep the first alternative only, but finish reading
                    # notes to determine register restriction of the sense.
                    if "\0" not in head:
                        head += "\0"
                else:
                    head += char
            parts.append((head, notes))
            for head, notes in parts:
                if any(n.casefold() in register_labels for n in notes):
                    continue
                head = head.split("\0", 1)[0].strip().rstrip("?!").rstrip()
                return head.removeprefix("to ") if pos == "verb" else head
        return None

    for word in records:
        c = captured[word["id"]]
        result = sources.select_gloss(word, c["rows"], c["kaikki"], ulif_entries=c["ulif_entries"])
        mixed = c["kaikki"]
        is_mixed = word["pos"] == "prep" and mixed and len(mixed["pos"]) > 1 and mixed["glosses"]
        mixed_checked += bool(is_mixed)
        if result.gloss is None:
            if is_mixed:
                assert result.reason == codes.GLOSS_SENSE_UNRESOLVED, word["id"]
            continue
        glossed += 1
        raw_dmk = [s for r in c["rows"] for s in json.loads(r["translations"])]
        raw_kaikki = mixed["glosses"] if mixed else []
        first_heads = {first_raw_head(raw_dmk, word["pos"]), first_raw_head(raw_kaikki, word["pos"])}
        emitted_head = first_raw_head([result.gloss], word["pos"])
        assert emitted_head in first_heads, (word["id"], result, first_heads)
        if not is_mixed:
            continue
        # Independent corpus oracle: every applicable captured first sense is
        # unrestricted. Read its first head directly, without selector helpers
        # or searching later senses for a matching candidate.
        first_sense = json.loads(c["rows"][0]["translations"])[0]
        assert not first_sense.startswith(("(", "[")), word["id"]
        first_head = first_sense.split(" (", 1)[0].split(", ", 1)[0]
        assert result.gloss == first_head, (word["id"], first_sense, result)
        assert result.source == "dmklinger_uk_en"
        assert result.ref["id"] == c["rows"][0]["id"]
        corroborated += 1
    assert mixed_checked > corroborated > 0
    assert glossed > 100


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


def test_plan_gate_ambiguity_and_bound(synthetic_sources):
    word = {"id": "W-001", "lemma": "synthetic", "pos": "noun", "gloss_en": "seed; family"}
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET translations=? WHERE pos='noun'", (json.dumps(["seed", "family"]),))
    with sources.Sources(sources_db=synthetic_sources) as api:
        errors = verify.verify_plan_glosses({"uses": ["W-001"]}, {"words": [word]}, "a1/test-mod", api)
    assert any(codes.GLOSS_NOT_LEARNER_SENSE in error for error in errors)

    assert any(codes.GLOSS_SENSE_UNRESOLVED in error for error in errors)


@pytest.mark.parametrize("stored", [None, "seed"])
def test_unresolved_gap_is_reported_once(synthetic_sources, stored):
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET translations=? WHERE pos='noun'", (json.dumps(["seed", "family"]),))
    word = {"id": "W-001", "lemma": "synthetic", "pos": "noun"}
    if stored:
        word["gloss_en"] = stored
    with sources.Sources(sources_db=synthetic_sources) as api:
        errors = verify.verify_plan_glosses({"uses": ["W-001"]}, {"words": [word]}, "a1/test-mod", api)
    assert len(errors) == 1
    assert errors[0].startswith(codes.GLOSS_SENSE_UNRESOLVED + ":")


@pytest.mark.parametrize("stored", [None, "shared"])
def test_plan_gate_refuses_nonfirst_agreement_even_when_stored(synthetic_sources, synthetic_kaikki_side_db, stored):
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET translations=? WHERE pos='noun'", (json.dumps(["primary", "shared"]),))
    with sqlite3.connect(synthetic_kaikki_side_db) as conn:
        conn.execute("INSERT INTO kaikki VALUES (?, ?)", ("synthetic", json.dumps(payload(["other", "shared"]))))
        conn.execute("UPDATE meta SET value='3' WHERE key='row_count'")
    word = {"id": "W-001", "lemma": "synthetic", "pos": "noun"}
    if stored:
        word["gloss_en"] = stored
    with sources.Sources(sources_db=synthetic_sources) as api:
        errors = verify.verify_plan_glosses({"uses": ["W-001"]}, {"words": [word]}, "a1/test-mod", api)
    assert len(errors) == 1
    assert errors[0].startswith(codes.GLOSS_SENSE_UNRESOLVED + ":")


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
def test_register_marked_spans_cannot_anchor(label, edge):
    marked = {
        "leading": f"({label}) old",
        "trailing": f"old ({label})",
        "nested": f"old (sense ({label}))",
        "square": f"[{label}] old",
    }[edge]
    word = {"lemma": "synthetic", "pos": "noun"}
    result = sources.select_gloss(word, [row(1, [marked, "modern"])], payload([marked]))
    # Preserve the complete label matrix: nested descriptive notes now keep
    # their agreed head; outer register-only notes cannot anchor a gloss.
    assert result.gloss == ("old" if edge == "nested" else None)
    if edge != "nested":
        assert result.reason == codes.GLOSS_SENSE_UNRESOLVED
    sole = sources.select_gloss(word, [row(1, [marked])], None)
    assert sole.gloss == ("old" if edge == "nested" else None)
    if edge != "nested":
        assert sole.reason == codes.GLOSS_SENSE_UNRESOLVED


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


def test_preposition_prefers_agreed_head_to_qualified_unagreed_head():
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


def test_preposition_keeps_qualifier_without_admissible_agreement():
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, ["about (in the immediate neighborhood of) (preposition)"], pos="preposition")],
        None,
    )
    assert result.gloss == "about (in the immediate neighborhood of)"


def test_preposition_qualifier_cannot_be_dropped_to_pass_the_length_gate():
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, ["about (in a particular place with a distinct and otherwise ambiguous meaning)"], pos="preposition")],
        None,
    )
    assert result.gloss is None
    assert result.reason == codes.GLOSS_MISSING


@pytest.mark.parametrize(
    "glosses,expected",
    [
        (["circle", "about (in the immediate neighborhood of)"], "about"),
        (["circle", "around (surrounding)"], None),
        (["circle", "about"], None),
        (["circle", "about (concerning)"], None),
        (["around (surrounding)", "malformed)"], None),
    ],
)
def test_mixed_pos_can_only_corroborate_first_head_with_identical_qualifiers(glosses, expected):
    mixed = {"pos": ["noun", "prep"], "glosses": glosses}
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, ["about (in the immediate neighborhood of), around (surrounding) (preposition)"], pos="preposition")],
        mixed,
    )
    assert result.gloss == expected
    if expected:
        assert result.source == "dmklinger_uk_en"
    else:
        assert result.reason == codes.GLOSS_SENSE_UNRESOLVED
    assert sources.select_gloss({"lemma": "synthetic", "pos": "prep"}, [], mixed).gloss is None


@pytest.mark.parametrize(
    "dmk,kaikki,expected",
    [
        (["(rare) secondary", "primary (+ genitive)", "minority"], ["primary (+ genitive)"], "primary"),
        (["(rare) secondary", "primary (+ genitive)", "minority"], ["minority"], None),
        (["primary", "minority"], ["minority"], None),
        (["alternative form of primary", "minority"], ["minority"], None),
        (["(rare) minority"], ["minority"], None),
        (["primary; minority"], ["primary; other"], "primary"),
    ],
)
def test_mixed_pos_corroboration_cannot_promote_a_later_sense(dmk, kaikki, expected):
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, dmk, pos="preposition")],
        {"pos": ["noun", "prep"], "glosses": kaikki},
    )
    assert result.gloss == expected
    if expected is None:
        assert result.reason == codes.GLOSS_SENSE_UNRESOLVED


def test_mixed_pos_corroboration_cannot_promote_a_later_row():
    result = sources.select_gloss(
        {"lemma": "synthetic", "pos": "prep"},
        [row(1, ["primary"], pos="preposition"), row(2, ["minority"], pos="preposition")],
        {"pos": ["noun", "prep"], "glosses": ["minority"]},
    )
    assert result.gloss is None
    assert result.reason == codes.GLOSS_SENSE_UNRESOLVED


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


def test_same_spelling_homonyms_cannot_bind_by_key_or_agreement():
    word = {"lemma": "synthetic", "pos": "noun", "ulif": {"key": ["synthetic", 1]}}
    result = sources.select_gloss(
        word, [row(1, ["seed", "family"])], payload(["seed", "family"]), ulif_entries=[homonym(1), homonym(2)]
    )
    assert result.reason == codes.GLOSS_SENSE_UNRESOLVED


def test_stressed_homonym_binding_is_unique_and_pos_scoped():
    word = {"lemma": "замок", "pos": "noun", "ulif": {"key": ["замо́к", 2]}}
    entries = [homonym(1, "за́мок"), homonym(2, "замо́к"), homonym(3, "замо́к", "verb")]
    rows = [row(1, ["castle"], "за́мок"), row(2, ["lock"], "замо́к")]
    assert sources.select_gloss(word, rows, payload(["castle"]), ulif_entries=entries).gloss == "lock"
    word["ulif"]["key"][1] = 99
    assert sources.select_gloss(word, rows, None, ulif_entries=entries).reason == codes.GLOSS_SENSE_UNRESOLVED


@pytest.mark.parametrize(
    "lemma,expected",
    [
        ("писати", "to write"),
        ("твій", "your"),
        ("радіти", "to rejoice"),
        ("додому", "home"),
        ("малина", "raspberry"),
        ("я", "I"),
        ("вона", "she"),
        ("і", None),
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
        ("коло", None),
        ("до", None),
        ("перед", None),
        ("між", "between"),
        ("хто", "who"),
        ("що", None),
        ("ґрунт", "ground"),
        ("маля", "infant"),
        ("мама", "mama"),
        ("тато", "dad"),
        ("од", None),
        ("щоб", "so that"),
        ("щоби", "so that"),
        ("день", "day"),
        ("зо", "with (in the company of)"),
        ("кувати", None),
        ("коса", None),
        ("сім'я", None),
        ("зв'язок", None),
        ("привіт", None),
        ("грати", None),
        ("свято", None),
        ("дзюрчати", None),
        # Live ULIF lists two noun homonyms; W-110's binding is pending.
        ("хліб", None),
    ],
)
def test_reviewer_examples_from_captured_sources(lemma, expected, a1_source_capture):
    records, captured = a1_source_capture
    word = next(w for w in records if w["lemma"] == lemma)
    c = captured[word["id"]]
    result = sources.select_gloss(word, c["rows"], c["kaikki"], ulif_entries=c["ulif_entries"])
    assert result.gloss == expected
    if expected is None:
        assert result.reason == codes.GLOSS_SENSE_UNRESOLVED


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
    assert result.reason == codes.GLOSS_SENSE_UNRESOLVED
