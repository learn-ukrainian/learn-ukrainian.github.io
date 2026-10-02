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


@pytest.mark.parametrize("value", ["a; b", "x" * 61, "one two three four five six seven eight nine", "bad)", ""])
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
            "fence",
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
    "label", ["obsolete", "archaic", "dated", "dialectal", "colloquial", "figurative", "technical"]
)
@pytest.mark.parametrize("edge", ["leading", "trailing"])
def test_register_marked_spans_are_only_fallback(label, edge):
    marked = f"({label}) old" if edge == "leading" else f"old ({label})"
    word = {"lemma": "synthetic", "pos": "noun"}
    result = sources.select_gloss(word, [row(1, [marked, "modern"])], payload([marked]))
    assert result.gloss == "modern"
    assert sources.select_gloss(word, [row(1, [marked])], None).gloss == "old"


@pytest.mark.parametrize(
    "sense",
    [
        "a shoe, which covers the foot and extends above the ankle",
        "Expressing pain, fear, surprise, joy, disappointment, anger, hatred, etc (interjection)",
        "boot; sturdy footwear covering the foot and extending above the ankle, often for winter use",
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
        ("тин", "fence"),
        ("мільярд", "billion (short scale)"),
        ("їжа", "food"),
        ("чобіт", "boot"),
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
