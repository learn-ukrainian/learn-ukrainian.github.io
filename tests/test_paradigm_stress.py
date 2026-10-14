"""Regression proof using captured local ULIF/VESUM homograph rows (#9820)."""

import copy
import json
from pathlib import Path

import pytest

from scripts.lexicon import enrich_manifest, paradigm_stress, validate_paradigm_stress
from scripts.verification import stress, ulif_stress

CAPTURE = json.loads((Path(__file__).parent / "fixtures/stress-paradigm-homographs.json").read_text())


@pytest.fixture
def authority(monkeypatch):
    monkeypatch.setattr(ulif_stress, "ulif_stress_rows", lambda form: CAPTURE["forms"].get(form, []))
    monkeypatch.setattr(stress, "_vesum_lookup", lambda form: CAPTURE["vesum_words"].get(form, []))
    monkeypatch.setattr(stress, "_load_trie", lambda: {})
    monkeypatch.setattr(stress, "_trie_value", lambda trie, form: None)
    monkeypatch.setattr(stress, "source_info", lambda: {"captured": True})
    monkeypatch.setattr(enrich_manifest, "verify_lemma", lambda lemma: CAPTURE["lemmas"].get(lemma, []))
    monkeypatch.setattr(validate_paradigm_stress, "verify_lemma", lambda lemma: CAPTURE["lemmas"].get(lemma, []))


@pytest.mark.parametrize(
    "lemma,form,expected",
    [
        ("показник", "показникові", "пока́зникові"),
        ("випадок", "випадкові", "ви́падкові"),
        ("виняток", "виняткові", "ви́няткові"),
    ],
)
def test_noun_dative_uses_its_ulif_slot(authority, lemma, form, expected):
    result = paradigm_stress.resolve_paradigm_stress(lemma, form, "noun:inanim:m:v_dav", "noun")
    assert result == {"form": expected, "source": "ulif"}
    assert any(row["form_stressed"] == expected for row in CAPTURE["forms"][form])


def test_missing_locative_does_not_borrow_dative_or_adjective_stress(authority):
    assert paradigm_stress.resolve_paradigm_stress("показник", "показникові", "noun:inanim:m:v_mis", "noun") is None


def test_tagged_oracle_fallback_receives_lemma_and_row_tags(authority, monkeypatch):
    result = stress.verify_stress("випадкові", lemma="випадок", tags="noun:inanim:m:v_dav")
    calls = []
    monkeypatch.setattr(paradigm_stress, "readings", lambda *args, **kwargs: [])

    def oracle(word, **kwargs):
        calls.append((word, kwargs))
        return result

    monkeypatch.setattr(paradigm_stress, "verify_stress", oracle)
    assert paradigm_stress.resolve_paradigm_stress("випадок", "випадкові", "noun:inanim:m:v_dav", "noun") == {
        "form": "ви́падкові",
        "source": "ulif",
    }
    assert calls == [("випадкові", {"lemma": "випадок", "tags": "noun:inanim:m:v_dav"})]


@pytest.mark.parametrize("failure", ["ambiguous", "pending", "untagged", "wrong_lemma"])
def test_oracle_cannot_supply_an_unbound_reading(authority, monkeypatch, failure):
    result = stress.verify_stress("випадкові", lemma="випадок", tags="noun:inanim:m:v_dav")
    if failure in {"ambiguous", "pending"}:
        result["status"] = failure
    elif failure == "untagged":
        result["matches"][0]["required_tags"] = []
    else:
        result["matches"][0]["vesum_analyses"] = CAPTURE["vesum_words"]["показникові"]
    monkeypatch.setattr(paradigm_stress, "readings", lambda *args, **kwargs: [])
    monkeypatch.setattr(paradigm_stress, "verify_stress", lambda *args, **kwargs: result)
    assert paradigm_stress.resolve_paradigm_stress("випадок", "випадкові", "noun:inanim:m:v_dav", "noun") is None


def test_conflicting_ulif_stresses_are_withheld_without_fallback(authority, monkeypatch):
    correct = ulif_stress.readings(
        "випадкові",
        supplied={"upos=NOUN", "Case=Dat", "Number=Sing"},
        lemma="випадок",
        vesum=CAPTURE["vesum_words"]["випадкові"],
    )
    adjective = next(r for r in CAPTURE["forms"]["випадкові"] if r["normalized_query"] == "випадковий")
    conflict = {**correct[0], "stressed_form": adjective["form_stressed"]}
    monkeypatch.setattr(paradigm_stress, "readings", lambda *args, **kwargs: [*correct, conflict])
    monkeypatch.setattr(paradigm_stress, "verify_stress", lambda *args, **kwargs: pytest.fail("conflict fell back"))
    assert paradigm_stress.resolve_paradigm_stress("випадок", "випадкові", "noun:inanim:m:v_dav", "noun") is None


def candidate():
    return {
        "entries": [
            {"lemma": lemma, "enrichment": {"morphology": enrich_manifest._morphology(lemma)}}
            for lemma in CAPTURE["lemmas"]
        ]
    }


def test_morphology_never_calls_untagged_stress_in_any_slot(authority, monkeypatch):
    monkeypatch.setattr(enrich_manifest, "_stress_display_form", lambda *args: pytest.fail("untagged stress"))
    monkeypatch.setattr(enrich_manifest, "_stress_word", lambda *args: pytest.fail("untagged Stressifier"))
    manifest = candidate()
    morphology = manifest["entries"][0]["enrichment"]["morphology"]
    assert [(r["tags"], r.get("stress")) for r in morphology["forms"] if r["form"] == "показникові"] == [
        ("noun:inanim:m:v_dav", "пока́зникові"),
        ("noun:inanim:m:v_mis", None),
    ]
    assert "показникові" not in morphology.get("stress", {}).get("forms", {})
    report = validate_paradigm_stress.validate_manifest_stress(manifest)
    assert report["disagreement_count"] == 0
    assert report["rows"] == sum(len(v) for v in CAPTURE["lemmas"].values())
    assert report["stressed_rows"] == 5


def test_validator_rejects_adjective_stress_and_cross_slot_display(authority):
    manifest = candidate()
    morphology = manifest["entries"][0]["enrichment"]["morphology"]
    row = next(r for r in morphology["forms"] if r["tags"].endswith("v_dav") and r["form"].endswith("ові"))
    adjective = next(r for r in CAPTURE["forms"][row["form"]] if r["normalized_query"] == "показниковий")
    row["stress"] = adjective["form_stressed"]
    morphology.setdefault("stress", {"forms": {}})["forms"][row["form"]] = "пока́зникові"
    report = validate_paradigm_stress.validate_manifest_stress(manifest)
    assert report["disagreement_count"] == 2
    assert report["disagreements"][0]["expected"] == ["пока́зникові"]
    assert report["disagreements"][1]["kind"] == "display_stress"


def test_validator_authenticates_legacy_labels_and_rejects_false_tags(authority):
    manifest = candidate()
    for entry in manifest["entries"]:
        for row in entry["enrichment"]["morphology"]["forms"]:
            row.pop("tags")
    assert validate_paradigm_stress.validate_manifest_stress(manifest)["disagreement_count"] == 0
    row = next(r for r in manifest["entries"][0]["enrichment"]["morphology"]["forms"] if r.get("stress"))
    row["tags"] = "adj:p:v_naz"
    assert validate_paradigm_stress.validate_manifest_stress(manifest)["disagreement_count"] == 1


def test_separate_unresolved_marked_row_does_not_veto_modern_display(authority):
    manifest = candidate()
    morphology = manifest["entries"][1]["enrichment"]["morphology"]
    row = next(r for r in morphology["forms"] if r.get("stress"))
    marked = {**row, "tags": row["tags"] + ":rare", "marker": "rare"}
    marked.pop("stress")
    marked.pop("stress_source")
    morphology["marked_forms"] = [marked]
    report = validate_paradigm_stress.validate_manifest_stress(manifest)
    assert report["disagreement_count"] == 0
    assert report["unresolved_rows"] > 0
    marked["stress"] = row["stress"]
    assert validate_paradigm_stress.validate_manifest_stress(manifest)["disagreement_count"] == 1


def test_validator_cli_reports_denominator_and_failure(authority, tmp_path, capsys):
    path = tmp_path / "candidate.json"
    manifest = candidate()
    path.write_text(json.dumps(manifest, ensure_ascii=False))
    before = path.read_bytes()
    assert validate_paradigm_stress.main(["--manifest", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["stressed_rows"] == 5
    assert path.read_bytes() == before
    bad = copy.deepcopy(manifest)
    bad["entries"][0]["enrichment"]["morphology"].setdefault("stress", {"forms": {}})["forms"]["unknown"] = "unknown"
    path.write_text(json.dumps(bad, ensure_ascii=False))
    assert validate_paradigm_stress.main(["--manifest", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["disagreement_count"] == 1
    path.write_text('{"entries": []}')
    assert validate_paradigm_stress.main(["--manifest", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["rows"] == 0
