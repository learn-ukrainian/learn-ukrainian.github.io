"""Regression proof using captured local ULIF/VESUM homograph rows (#9820)."""

import copy
import json
from pathlib import Path

import pytest

from scripts.lexicon import enrich_manifest, paradigm_stress, validate_paradigm_stress
from scripts.verification import stress, ulif_stress

FIXTURES = Path(__file__).parent / "fixtures"
CAPTURE = json.loads((FIXTURES / "stress-paradigm-homographs.json").read_text())
# суддя, голова (two ULIF homonyms plus the гол homograph) and висипатися
# (61 VESUM rows mixing both aspects under one spelling).
REVIEW = json.loads((FIXTURES / "stress-paradigm-common-gender-aspect.json").read_text())


def _install(monkeypatch, capture):
    monkeypatch.setattr(ulif_stress, "ulif_stress_rows", lambda form: capture["forms"].get(form, []))
    monkeypatch.setattr(stress, "_vesum_lookup", lambda form: capture["vesum_words"].get(form, []))
    monkeypatch.setattr(stress, "_load_trie", lambda: {})
    monkeypatch.setattr(stress, "_trie_value", lambda trie, form: None)
    monkeypatch.setattr(stress, "source_info", lambda: {"captured": True})
    monkeypatch.setattr(enrich_manifest, "verify_lemma", lambda lemma: capture["lemmas"].get(lemma, []))
    monkeypatch.setattr(validate_paradigm_stress, "verify_lemma", lambda lemma: capture["lemmas"].get(lemma, []))


@pytest.fixture
def authority(monkeypatch):
    _install(monkeypatch, CAPTURE)


@pytest.fixture
def review_authority(monkeypatch):
    _install(monkeypatch, REVIEW)


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


def review_entry(lemma):
    return {"lemma": lemma, "enrichment": {"morphology": enrich_manifest._morphology(lemma)}}


def test_common_gender_label_is_a_noun_without_gender():
    row = next(r for r in REVIEW["forms"]["судді"] if r["grammatical_tags"] == '["v_rod", "s"]')
    assert row["grammatical_label"].startswith("іменник чоловічого або жіночого роду")
    features = ulif_stress._features(row)
    assert {"upos=NOUN", "Case=Gen", "Number=Sing"} <= features
    assert not any(feature.startswith("Gender=") for feature in features)


@pytest.mark.parametrize("gender", ["m", "f"])
@pytest.mark.parametrize(
    "lemma,form,case,expected",
    [
        ("суддя", "суддя", "v_naz", "суддя́"),
        ("суддя", "суддю", "v_zna", "суддю́"),
        ("суддя", "судде", "v_kly", "су́дде"),
        ("голова", "голова", "v_naz", "голова́"),
        ("голова", "головою", "v_oru", "голово́ю"),
    ],
)
def test_common_gender_noun_binds_both_genders_to_its_ulif_entry(review_authority, gender, lemma, form, case, expected):
    tags = f"noun:anim:{gender}:{case}"
    assert paradigm_stress.resolve_paradigm_stress(lemma, form, tags, "noun") == {"form": expected, "source": "ulif"}


def test_masculine_chair_reading_never_takes_the_gol_homograph(review_authority):
    # голові: голова#2 'chair' (common gender) gives голові́; гол#1 gives го́лові.
    assert any(r["normalized_query"] == "гол" and r["form_stressed"] == "го́лові" for r in REVIEW["forms"]["голові"])
    result = paradigm_stress.resolve_paradigm_stress("голова", "голові", "noun:anim:m:v_dav", "noun")
    assert result == {"form": "голові́", "source": "ulif"}
    report = validate_paradigm_stress.validate_manifest_stress({"entries": [review_entry("голова")]})
    assert report["disagreement_count"] == 0


def test_case_shifts_stress_inside_one_spelling(review_authority):
    resolve = paradigm_stress.resolve_paradigm_stress
    assert resolve("суддя", "судді", "noun:anim:m:v_rod", "noun")["form"] == "судді́"
    assert resolve("суддя", "судді", "noun:anim:p:v_naz", "noun")["form"] == "су́дді"
    entry = review_entry("суддя")
    morphology = entry["enrichment"]["morphology"]
    rows = {r["tags"]: r.get("stress") for r in morphology["forms"] if r["form"] == "судді"}
    assert rows["noun:anim:f:v_dav"] == "судді́"
    assert rows["noun:anim:p:v_naz"] == "су́дді"
    # One spelling, two accents: the slot-free display map withholds it.
    assert "судді" not in morphology["stress"]["forms"]
    assert morphology["stress"] == {
        "source": "ulif",
        "forms": {
            "судде": "су́дде",
            "суддя": "суддя́",
            "суддею": "судде́ю",
            "суддю": "суддю́",
            "суддям": "су́ддям",
            "суддях": "су́ддях",
            "суддями": "су́ддями",
            "суддів": "су́ддів",
        },
    }
    assert validate_paradigm_stress.validate_manifest_stress({"entries": [entry]})["disagreement_count"] == 0
    morphology["stress"]["forms"]["судді"] = "судді́"
    report = validate_paradigm_stress.validate_manifest_stress({"entries": [entry]})
    assert [(d["form"], d["kind"]) for d in report["disagreements"]] == [("судді", "display_stress")]


def test_same_spelling_aspect_pair_withholds_every_shared_form(review_authority):
    resolve = paradigm_stress.resolve_paradigm_stress
    assert resolve("висипатися", "висипатися", "verb:rev:imperf:inf", "verb")["form"] == "висипа́тися"
    assert resolve("висипатися", "висипатися", "verb:rev:perf:inf", "verb")["form"] == "ви́сипатися"
    assert resolve("висипатися", "висипався", "verb:rev:perf:past:m", "verb")["form"] == "ви́сипався"
    entry = review_entry("висипатися")
    morphology = entry["enrichment"]["morphology"]
    # The forms list keeps one row per label (the imperfective), but every
    # reading still votes, so a spelling both aspects share has no single accent.
    assert [(r["tags"], r["stress"]) for r in morphology["forms"] if r["form"] == "висипатися"] == [
        ("verb:rev:imperf:inf", "висипа́тися")
    ]
    display = morphology["stress"]["forms"]
    assert "висипатися" not in display
    assert "висипався" not in display
    assert display["висипається"] == "висипа́ється"
    assert display["висиплеться"] == "ви́сиплеться"
    assert display["висипатиметься / висиплеться"] == "висипа́тиметься / ви́сиплеться"
    assert validate_paradigm_stress.validate_manifest_stress({"entries": [entry]})["disagreement_count"] == 0
    display["висипався"] = "висипа́вся"
    report = validate_paradigm_stress.validate_manifest_stress({"entries": [entry]})
    assert [(d["form"], d["kind"]) for d in report["disagreements"]] == [("висипався", "display_stress")]


def test_display_stress_past_the_row_cap_is_checked_against_the_full_paradigm(review_authority):
    entry = review_entry("висипатися")
    morphology = entry["enrichment"]["morphology"]
    assert len(REVIEW["lemmas"]["висипатися"]) == 61 > enrich_manifest._MORPHOLOGY_FORM_CAP
    assert morphology["form_count"] == len(morphology["forms"]) == enrich_manifest._MORPHOLOGY_FORM_CAP
    written = {r["form"] for r in morphology["forms"]}
    display = morphology["stress"]["forms"]
    assert sorted(f for f in display if " / " not in f and f not in written) == ["висиплеться"]
    report = validate_paradigm_stress.validate_manifest_stress({"entries": [entry]})
    # 9fce856fee reported both displays below as disagreements: it only knew the 40 written rows.
    assert report["rows"] == 40
    assert report["display_values"] == len(display)
    assert report["disagreement_count"] == 0
    display["висиплеться"] = "висипле́ться"
    report = validate_paradigm_stress.validate_manifest_stress({"entries": [entry]})
    assert [(d["form"], d["kind"]) for d in report["disagreements"]] == [("висиплеться", "display_stress")]


def test_paradigm_row_kind_matches_the_card_partition():
    kind = enrich_manifest._paradigm_row_kind
    assert kind({"word_form": "судді", "tags": "noun:anim:p:v_naz"}) == "modern"
    assert kind({"word_form": "судді", "tags": "noun:anim:p:v_zna:rare"}) == "marked"
    assert kind({"word_form": "подаваться", "tags": "verb:rev:imperf:inf"}) is None
    assert kind({"word_form": "", "tags": "noun:anim:p:v_naz"}) is None
