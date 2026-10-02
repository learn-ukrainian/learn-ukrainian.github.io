"""Learner-sense selection: source spans, stress collisions and typed gaps."""

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import codes, sources, verify, words


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
def test_distinct_agreements_remain_unresolved(glosses):
    result = sources.select_gloss({"lemma": "synthetic", "pos": "noun"}, [row(1, glosses)], payload(glosses))
    assert result.gloss is None
    assert result.reason == codes.GLOSS_SENSE_UNRESOLVED
    assert {c["gloss"] for c in result.candidates} == set(glosses)


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


def test_current_a1_builder_verifier_selection_and_source_span_property():
    root = Path(__file__).resolve().parents[3]
    records = yaml.safe_load((root / "curriculum/l2-uk-en/evidence/a1/_words.yaml").read_text())["words"]
    # Captured source bytes keep this property test runnable in CI, which has
    # no corpus DB. No predicted glosses are stored in the fixture.
    captured = json.loads((Path(__file__).parent / "fixtures/a1_gloss_candidates.json").read_text())["records"]
    assert {w["id"] for w in records} == set(captured)
    rows = {(entry["lemma"], entry["pos"]): entry["rows"] for entry in captured.values()}
    kaikki = {entry["lemma"]: entry["kaikki"] for entry in captured.values()}
    for word in records:
        matched = rows[word["lemma"], word["pos"]]
        builder = words.sources.select_gloss(word, matched, kaikki[word["lemma"]])
        verifier = verify.sources.select_gloss(word, matched, kaikki[word["lemma"]])
        assert builder == verifier, word["id"]
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
    with sources.Sources(sources_db=synthetic_sources) as api:
        errors = verify.verify_plan_glosses({"uses": ["W-001"]}, {"words": [word]}, "a1/test-mod", api)
    assert any(codes.GLOSS_NOT_LEARNER_SENSE in error for error in errors)
