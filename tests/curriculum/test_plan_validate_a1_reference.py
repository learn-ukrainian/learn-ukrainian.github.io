"""C29 membership and exceptions; strings are letter-arithmetic fixtures."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from scripts.curriculum.validate import a1_reference, codes, config, quote_bytes
from scripts.curriculum.validate.loader import REPO_ROOT, load_plan
from scripts.curriculum.validate.pack import WordRecord, WordStore
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.review_gates import ReviewGates
from scripts.curriculum.validate.validate import main
from tests.curriculum.test_plan_validate import LEVEL, SLUG
from tests.curriculum.test_plan_validate_review_gates import _world

pytestmark = pytest.mark.reads_content


def gates(lemma, exception=None, *, field="core", tags="noun", level="a1"):
    item = {"lemma": lemma, "evidence": "W-001"}
    if exception is not None:
        item["a1_reference_exception"] = exception
    plan = {
        "level": level, "arc_ref": {"position": 1},
        "lessons": [{"n": 1, "inventory": {"vocabulary": {"core": [], "incidental": [], "recycled": ["W-999"]}},
                     "steps": [{"id": "s1", "introduces": {"letters": ["ґ"], "vocabulary": ["W-001"]}},
                               {"id": "s2", "introduces": {"letters": ["а"], "vocabulary": []}}]}],
    }
    plan["lessons"][0]["inventory"]["vocabulary"][field] = [item]
    record = WordRecord("W-001", lemma, frozenset({tags}))
    result = ReviewGates(Report(level, "fixture"), plan, level, WordStore(Path("unused"), {record.id: record}),
                         [SimpleNamespace(position=1, letters=["ґ", "а"])], None, Path("unused"), pack=None)
    return result


@pytest.mark.parametrize("spelling,expected", [
    ("До́брий день!...", "добрий день"), ("п'ять", "п’ять"), ("пʼять", "п’ять"),
    ("и\u0306", "й"), ("  Мене́  зва́ти... ", "мене звати"),
])
def test_normalization(spelling, expected):
    assert a1_reference.normalize(spelling) == expected


def test_inventory_members_variants_pairs_and_phrase():
    members, words = a1_reference.reference_spellings()
    assert {"мій", "моя", "моє", "мої", "вдягнути", "вдягти", "добрий день"} <= members
    assert "добрий день" not in words
    assert "контрольна робота" not in members  # a variant on a single-word row is not a phrase entry


@pytest.mark.parametrize("field", ["core", "incidental"])
@pytest.mark.parametrize("lemma,missing", [("моя", False), ("До́брий день!", False), ("п'ять", False),
                                           ("мама день", True), ("неінвентарне", True)])
def test_membership_only_introduced_words(field, lemma, missing):
    g = gates(lemma, field=field)
    g.check_a1_reference()
    assert bool(g.report.notes) == missing
    assert not g.report.failures
    if missing:
        assert g.report.notes[0].code == codes.A1_REFERENCE_WORD_MISSING
    assert a1_reference.INVENTORY_PATH.relative_to(REPO_ROOT).as_posix() in g.report.inputs


@pytest.mark.parametrize("tags,exempt", [("noun:prop:fname", True), ("noun", False), ("", False)])
def test_proper_names(tags, exempt):
    g = gates("неінвентарне", tags=tags)
    g.check_a1_reference()
    assert bool(g.report.notes) != exempt


def test_mixed_proper_paradigm_is_checked():
    g = gates("неінвентарне")
    g.store.records["W-001"] = WordRecord("W-001", "неінвентарне", frozenset({"noun:prop", "noun"}))
    g.check_a1_reference()
    assert g.report.notes


@pytest.mark.parametrize("level", ["a2", "b1"])
def test_non_a1_does_not_load_reference(monkeypatch, level):
    monkeypatch.setattr(a1_reference, "reference_spellings", lambda *args: pytest.fail("non-A1 read"))
    g = gates("неінвентарне", level=level)
    g.check_a1_reference()
    assert not g.report.notes and not g.report.inputs


@pytest.mark.parametrize("lemma,valid", [(term, True) for term in config.A1_REFERENCE_PHONETICS_TERMS]
                         + [("склад", False)])
def test_closed_phonetics_allowlist(lemma, valid):
    g = gates(lemma, {"class": "phonetics_term"})
    g.check_a1_reference()
    assert bool(g.report.notes) != valid


@pytest.mark.parametrize("lemma,step,letter,expected", [
    ("ґанок", "s1", "ґ", None),  # only ґ taught: no readable reference alternative
    ("ґанок", "s9", "ґ", "does not exist"),
    ("ґанок", "s2", "ґ", "does not introduce"),
    ("ганок", "s1", "ґ", "does not contain"),
])
def test_letter_exception_conditions(lemma, step, letter, expected):
    g = gates(lemma, {"class": "letter_example_no_a1_word", "letter": letter, "step": step})
    g.check_a1_reference()
    assert bool(g.report.notes) == bool(expected)
    if expected:
        assert expected in g.report.notes[0].message
        assert g.report.notes[0].step == step


def test_exception_names_decodable_alternatives_and_includes_current_step():
    g = gates("ґанок", {"class": "letter_example_no_a1_word", "letter": "ґ", "step": "s1"})
    g.plan["lessons"][0]["steps"][0]["introduces"]["letters"] += list("удзик")
    g.check_a1_reference()
    assert "ґудзик" in g.report.notes[0].message
    assert "decodable inventory alternatives" in g.report.notes[0].message


def test_exception_unknown_state_cannot_pass():
    g = gates("ґанок", {"class": "letter_example_no_a1_word", "letter": "ґ", "step": "s1"})
    g.arc = None
    g.check_a1_reference()
    assert "unavailable" in g.report.notes[0].message


@pytest.mark.parametrize("mode", ["advisory", "failure"])
def test_public_cli_modes_and_loader_roundtrip(tmp_path, monkeypatch, capsys, mode):
    monkeypatch.setattr(config, "A1_REFERENCE_ENFORCEMENT", mode)
    monkeypatch.setattr(quote_bytes, "vesum_lookup", lambda words: set())
    def mutate(plan, pack, words, prior):
        plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["a1_reference_exception"] = {"class": "phonetics_term"}
    path = _world(tmp_path, mutate)
    loaded = load_plan(path)
    assert loaded["lessons"][0]["inventory"]["vocabulary"]["core"][0]["a1_reference_exception"] == {"class": "phonetics_term"}
    rc = main([LEVEL, SLUG, "--plan", str(path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert a1_reference.INVENTORY_PATH.relative_to(REPO_ROOT).as_posix() in data["inputs"]
    findings = data["notes" if mode == "advisory" else "failures"]
    assert any(o["code"] == codes.A1_REFERENCE_EXCEPTION_INVALID for o in findings)
    assert any(o["code"] == codes.A1_REFERENCE_WORD_MISSING for o in findings)
    assert rc == (0 if mode == "advisory" else 1)


@pytest.mark.parametrize("mode", ["typo", "off"])
def test_bad_config_fails_even_in_staged_rollout(monkeypatch, mode):
    monkeypatch.setattr(config, "A1_REFERENCE_ENFORCEMENT", mode)
    g = gates("мама")
    g.check_a1_reference()
    assert g.report.failures[0].code == codes.A1_REFERENCE_INVALID


def test_reference_unavailable_fails(monkeypatch):
    monkeypatch.setattr(a1_reference, "INVENTORY_PATH", Path("does-not-exist.yaml"))
    g = gates("мама")
    g.check_a1_reference()
    assert g.report.failures[0].code == codes.A1_REFERENCE_INVALID


@pytest.mark.parametrize("value,valid", [
    ({"class": "phonetics_term"}, True),
    ({"class": "letter_example_no_a1_word", "letter": "ґ", "step": "s3"}, True),
    ({"class": "unknown"}, False), ({"class": "phonetics_term", "letter": "ґ"}, False),
    ({"class": "letter_example_no_a1_word", "letter": "ґ"}, False),
    ({"class": "letter_example_no_a1_word", "letter": "ab", "step": "s3"}, False),
])
def test_typed_exception_schema(value, valid):
    schema = json.loads((REPO_ROOT / "schemas/module-plan-v2.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/a1ReferenceException", "$defs": schema["$defs"]})
    assert validator.is_valid(value) == valid


def test_step_without_introduces_is_valid_input():
    g = gates("неінвентарне")
    del g.plan["lessons"][0]["steps"][0]["introduces"]
    g.check_a1_reference()
    assert g.report.notes[0].step is None


def test_exception_does_not_disable_print_decodability():
    g = gates("ґанок", {"class": "letter_example_no_a1_word", "letter": "ґ", "step": "s1"})
    g.check_a1_reference()
    assert not g.report.notes
    assert not g._readable("ґанок", g._taught_at_steps(g.plan["lessons"][0])["s1"])


def test_step_and_recycled_lists_are_not_separate_checked_sets():
    g = gates("неінвентарне")
    g.plan["lessons"][0]["inventory"]["vocabulary"]["core"] = []
    g.check_a1_reference()
    assert not g.report.notes


def test_letter_exception_is_case_insensitive():
    g = gates("Ґанок", {"class": "letter_example_no_a1_word", "letter": "Ґ", "step": "s1"})
    g.check_a1_reference()
    assert not g.report.notes


def test_malformed_reference_is_a_typed_failure(tmp_path, monkeypatch):
    path = tmp_path / "invalid.yaml"
    path.write_text("sources: [invalid")
    monkeypatch.setattr(a1_reference, "INVENTORY_PATH", path)
    g = gates("мама")
    g.check_a1_reference()
    assert g.report.failures[0].code == codes.A1_REFERENCE_INVALID


def produced_a1_reference_codes():
    """Exercise all C29 outcome classes for the validator's registry coverage gate."""
    produced = set()
    for exception in [None, {"class": "phonetics_term"}]:
        g = gates("неінвентарне", exception)
        g.check_a1_reference()
        produced |= g.report.codes()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(config, "A1_REFERENCE_ENFORCEMENT", "invalid")
        g = gates("мама")
        g.check_a1_reference()
        produced |= g.report.codes()
    return produced


def test_produced_a1_reference_codes():
    assert produced_a1_reference_codes() == {
        codes.A1_REFERENCE_WORD_MISSING, codes.A1_REFERENCE_EXCEPTION_INVALID, codes.A1_REFERENCE_INVALID,
    }


def test_changed_inventory_bytes_invalidate_membership_cache(tmp_path):
    import yaml

    path = tmp_path / "reference.yaml"
    def write(lemma):
        path.write_text(yaml.safe_dump({"version": 1, "kind": "atlas_source_inventory", "sources": [
            {"id": "fixture", "source_family": "ohoiko", "extraction_mode": "curated_key_word",
             "headwords": [{"lemma": lemma, "kind": "word"}]}
        ]}, allow_unicode=True))
    write("мама")
    old, _ = a1_reference.reference_spellings(path)
    assert old == {"мама"} and isinstance(old, frozenset)
    assert a1_reference.reference_spellings(path)[0] is old
    write("тато")
    new, _ = a1_reference.reference_spellings(path)
    assert new == {"тато"} and old == {"мама"}


def test_valid_exception_keeps_c10_c18_c21_failures(tmp_path, monkeypatch):
    from scripts.curriculum.validate.validate import validate_plan
    from tests.curriculum.test_plan_validate_review_gates import _quote

    monkeypatch.setattr(quote_bytes, "vesum_lookup", lambda words: set(words))
    def mutate(plan, pack, words, prior):
        item = plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]
        item.update(lemma="звук", a1_reference_exception={"class": "phonetics_term"})
        record = next(w for w in words["words"] if w["id"] == item["evidence"])
        record["lemma"] = "звук"
        for form in record["forms"]:
            form["form"] = "звук"
        plan["lessons"][0]["activities"][0]["options"] = ["звук"]
        _quote("звук", {"id": "b4", "type": "quiz", "placement": "workbook", "focus": "Read the source.",
                         "learner_reads": ["T-002"]})(plan, pack, words, prior)
    report = validate_plan(LEVEL, SLUG, plan_path=_world(tmp_path, mutate))
    failures = {o.code for o in report.failures}
    assert {codes.STEP_WORD_NOT_DECODABLE, codes.CHOICE_OPTION_NOT_DECODABLE,
            codes.MODELED_PRINT_NOT_DECODABLE} <= failures
    assert codes.A1_REFERENCE_EXCEPTION_INVALID not in report.codes()
