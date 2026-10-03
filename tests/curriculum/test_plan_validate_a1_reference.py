"""C29 membership and exceptions; strings are letter-arithmetic fixtures."""

import json
import sqlite3
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
        "level": level,
        "arc_ref": {"position": 1},
        "lessons": [
            {
                "n": 1,
                "inventory": {"vocabulary": {"core": [], "incidental": [], "recycled": ["W-999"]}},
                "steps": [
                    {"id": "s1", "introduces": {"letters": ["ґ"], "vocabulary": ["W-001"]}},
                    {"id": "s2", "introduces": {"letters": ["а"], "vocabulary": []}},
                ],
            }
        ],
    }
    plan["lessons"][0]["inventory"]["vocabulary"][field] = [item]
    record = WordRecord("W-001", lemma, frozenset({tags}))
    result = ReviewGates(
        Report(level, "fixture"),
        plan,
        level,
        WordStore(Path("unused"), {record.id: record}),
        [SimpleNamespace(position=1, letters=["ґ", "а"])],
        None,
        Path("unused"),
        pack=None,
    )
    return result


@pytest.mark.parametrize(
    "spelling,expected",
    [
        ("До́брий день!...", "добрий день"),
        ("п'ять", "п’ять"),
        ("пʼять", "п’ять"),
        ("и\u0306", "й"),
        ("  Мене́  зва́ти... ", "мене звати"),
    ],
)
def test_normalization(spelling, expected):
    assert a1_reference.normalize(spelling) == expected


def test_inventory_members_variants_pairs_and_phrase():
    members, words = a1_reference.reference_spellings()
    assert {"мій", "моя", "моє", "мої", "вдягнути", "вдягти", "добрий день"} <= members
    assert "добрий день" not in words
    assert "контрольна робота" not in members  # a variant on a single-word row is not a phrase entry


@pytest.mark.parametrize("field", ["core", "incidental"])
@pytest.mark.parametrize(
    "lemma,missing",
    [("моя", False), ("До́брий день!", False), ("п'ять", False), ("мама день", True), ("неінвентарне", True)],
)
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


@pytest.mark.parametrize(
    "lemma,valid", [(term, True) for term in sorted(config.A1_REFERENCE_PHONETICS_TERMS)] + [("склад", False)]
)
def test_closed_phonetics_allowlist(lemma, valid):
    g = gates(lemma, {"class": "phonetics_term"})
    g.check_a1_reference()
    assert bool(g.report.notes) != valid


@pytest.mark.parametrize(
    "lemma,step,letter,expected",
    [
        ("ґанок", "s1", "ґ", None),  # only ґ taught: no readable reference alternative
        ("ґанок", "s9", "ґ", "does not exist"),
        ("ґанок", "s2", "ґ", "does not introduce"),
        ("ганок", "s1", "ґ", "does not contain"),
    ],
)
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
    assert loaded["lessons"][0]["inventory"]["vocabulary"]["core"][0]["a1_reference_exception"] == {
        "class": "phonetics_term"
    }
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


@pytest.mark.parametrize(
    "value,valid",
    [
        ({"class": "phonetics_term"}, True),
        ({"class": "letter_example_no_a1_word", "letter": "ґ", "step": "s3"}, True),
        ({"class": "unknown"}, False),
        ({"class": "phonetics_term", "letter": "ґ"}, False),
        ({"class": "letter_example_no_a1_word", "letter": "ґ"}, False),
        ({"class": "letter_example_no_a1_word", "letter": "ab", "step": "s3"}, False),
    ],
)
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
    g = gates("не", tags="part")
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
        codes.A1_REFERENCE_WORD_MISSING,
        codes.A1_REFERENCE_EXCEPTION_INVALID,
        codes.A1_REFERENCE_INVALID,
        codes.A1_REFERENCE_CLOSED_CLASS_A1,
    }


def test_changed_inventory_bytes_invalidate_membership_cache(tmp_path):
    import yaml

    path = tmp_path / "reference.yaml"

    def write(lemma):
        path.write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "kind": "atlas_source_inventory",
                    "sources": [
                        {
                            "id": "fixture",
                            "source_family": "ohoiko",
                            "extraction_mode": "curated_key_word",
                            "headwords": [{"lemma": lemma, "kind": "word"}],
                        }
                    ],
                },
                allow_unicode=True,
            )
        )

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
        _quote(
            "звук",
            {
                "id": "b4",
                "type": "quiz",
                "placement": "workbook",
                "focus": "Read the source.",
                "learner_reads": ["T-002"],
            },
        )(plan, pack, words, prior)

    report = validate_plan(LEVEL, SLUG, plan_path=_world(tmp_path, mutate))
    failures = {o.code for o in report.failures}
    assert {
        codes.STEP_WORD_NOT_DECODABLE,
        codes.CHOICE_OPTION_NOT_DECODABLE,
        codes.MODELED_PRINT_NOT_DECODABLE,
    } <= failures
    assert codes.A1_REFERENCE_EXCEPTION_INVALID not in report.codes()


@pytest.mark.parametrize(
    "lemma,tags,eligible",
    [
        ("я", "noun:anim:pron:pers", True),
        ("не", "part", True),
        ("а", "conj:coord", True),
        ("а", "part", False),
        ("що", "noun:inanim:pron:int:rel", True),
        ("що", "conj:subord", False),
        ("над", "prep", False),
        ("і", "conj:coord", True),
        ("й", "conj:coord", True),
        ("в", "prep", True),
        ("у", "prep", True),
        ("ой", "intj", False),
        ("я", "noun", False),
        ("мама", "noun", False),
        ("не", "adv", False),
        ("два", "numr", False),
        ("аби", "conj", False),
    ],
)
@pytest.mark.parametrize("mode", ["advisory", "failure"])
def test_closed_class_exemption_inventory_absent(monkeypatch, lemma, tags, eligible, mode):
    monkeypatch.setattr(a1_reference, "reference_spellings", lambda *args: (frozenset(), frozenset()))
    monkeypatch.setattr(config, "A1_REFERENCE_ENFORCEMENT", mode)
    g = gates(lemma, tags=tags)
    g.check_a1_reference()
    assert (codes.A1_REFERENCE_CLOSED_CLASS_A1 in g.report.codes()) == eligible
    assert (codes.A1_REFERENCE_WORD_MISSING in g.report.codes()) != eligible
    assert bool(g.report.failures) == (mode == "failure" and not eligible)
    assert a1_reference.CLOSED_CLASS_PATH.relative_to(REPO_ROOT).as_posix() in g.report.inputs


@pytest.mark.parametrize("lemma,tags", [("що", "conj:subord"), ("та", "conj"), ("та", "part")])
def test_membership_precedes_class_exemption(lemma, tags):
    g = gates(lemma, tags=tags)  # membership (including той's variant та) still passes
    g.check_a1_reference()
    assert not g.report.notes and not g.report.failures


def test_mixed_closed_class_record_requires_each_selected_class(monkeypatch):
    monkeypatch.setattr(a1_reference, "reference_spellings", lambda *args: (frozenset(), frozenset()))
    g = gates("що")
    g.store.records["W-001"] = WordRecord("W-001", "що", frozenset({"conj:subord", "noun:pron"}))
    g.check_a1_reference()
    assert codes.A1_REFERENCE_WORD_MISSING in g.report.codes()
    g.store.records["W-001"] = WordRecord("W-001", "що", frozenset({"noun:pron", "noun"}))
    assert not a1_reference.eligible_closed_class(
        "що", g.store.records["W-001"].form_tags, a1_reference.closed_class_a1()
    )


@pytest.mark.parametrize(
    "row",
    [
        {"lemma": "Ґданськ", "kind": "word"},
        {"lemma": "ґданськ", "kind": "word", "vesum_tags": ["noun:inanim:m:v_naz:prop:geo"]},
        {"lemma": "ґданськ тут", "kind": "phrase", "tokens": [{"form": "ґданськ", "vesum": "found"}]},
    ],
)
def test_proper_and_phrase_rows_members_but_never_alternatives(tmp_path, monkeypatch, row):
    import yaml

    path = tmp_path / "inventory.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "kind": "atlas_source_inventory",
                "sources": [
                    {
                        "id": "fixture",
                        "source_family": "ohoiko",
                        "extraction_mode": "curated_key_word",
                        "headwords": [row],
                    }
                ],
            },
            allow_unicode=True,
        )
    )
    members, alternatives = a1_reference.reference_spellings(path)
    assert a1_reference.normalize(row["lemma"]) in members and not alternatives
    monkeypatch.setattr(a1_reference, "reference_spellings", lambda *args: (members, alternatives))
    g = gates("ґанок", {"class": "letter_example_no_a1_word", "letter": "ґ", "step": "s1"})
    g.plan["lessons"][0]["steps"][0]["introduces"]["letters"] += list("данськтут")
    g.check_a1_reference()
    assert not g.report.notes  # even a decodable proper name cannot block this exception
    g = gates(row["lemma"])
    g.check_a1_reference()
    assert not g.report.notes


def test_closed_class_exemption_keeps_c10_c18_c21_failures(tmp_path, monkeypatch):
    from scripts.curriculum.validate.validate import validate_plan
    from tests.curriculum.test_plan_validate_review_gates import _quote

    monkeypatch.setattr(a1_reference, "reference_spellings", lambda *args: (frozenset(), frozenset()))
    monkeypatch.setattr(quote_bytes, "vesum_lookup", lambda words: set(words))

    def mutate(plan, pack, words, prior):
        item = plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]
        item["lemma"] = "не"
        record = next(w for w in words["words"] if w["id"] == item["evidence"])
        record["lemma"] = "не"
        for form in record["forms"]:
            form.update(form="не", tags="part")
        plan["lessons"][0]["activities"][0]["options"] = ["не"]
        _quote(
            "не",
            {
                "id": "b4",
                "type": "quiz",
                "placement": "workbook",
                "focus": "Read the source.",
                "learner_reads": ["T-002"],
            },
        )(plan, pack, words, prior)

    report = validate_plan(LEVEL, SLUG, plan_path=_world(tmp_path, mutate))
    failures = {o.code for o in report.failures}
    assert {
        codes.STEP_WORD_NOT_DECODABLE,
        codes.CHOICE_OPTION_NOT_DECODABLE,
        codes.MODELED_PRINT_NOT_DECODABLE,
    } <= failures
    assert codes.A1_REFERENCE_CLOSED_CLASS_A1 in report.codes()


def test_unavailable_closed_class_list_fails(monkeypatch):
    monkeypatch.setattr(a1_reference, "CLOSED_CLASS_PATH", Path("missing-closed.yaml"))
    g = gates("не", tags="part")
    g.check_a1_reference()
    assert g.report.failures[0].code == codes.A1_REFERENCE_INVALID


def test_teaching_replacements_same_pos_open_class_readable_and_both_outcomes(tmp_path):
    import yaml

    rows = [
        {"lemma": "мама", "kind": "word", "pos": "noun"},
        {"lemma": "тато", "kind": "word", "pos": "unlabelled", "vesum_pos": ["noun"]},
        {"lemma": "читати", "kind": "word", "pos": "verb"},
        {"lemma": "Іван", "kind": "word", "pos": "noun"},
        {"lemma": "іван", "kind": "word", "pos": "noun", "vesum_tags": ["noun:prop"]},
        {"lemma": "дві мами", "kind": "phrase", "pos": "unlabelled"},
        {"lemma": "я", "kind": "word", "pos": "noun"},
        {"lemma": "вона", "kind": "word", "pos": "unlabelled", "vesum_pos": ["noun"]},
        {"lemma": "сам", "kind": "word", "pos": "unlabelled", "vesum_pos": ["adj"]},
        {"lemma": "де", "kind": "word", "pos": "adv"},
        {"lemma": "аж", "kind": "word", "pos": "part"},
        {"lemma": "з", "kind": "word", "pos": "prep"},
    ]
    path = tmp_path / "inventory.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "kind": "atlas_source_inventory",
                "sources": [
                    {
                        "id": "fixture",
                        "source_family": "ohoiko",
                        "extraction_mode": "curated_key_word",
                        "headwords": rows,
                    }
                ],
            },
            allow_unicode=True,
        )
    )

    def tags(w):
        return {"adj:pron"} if w == "сам" else {"verb:inf"} if w == "читати" else {"noun"}

    def suggest(selected, readable, path):
        return a1_reference.teaching_replacements(selected, readable, tags, path)

    assert suggest(frozenset({"noun:inanim"}), lambda w: w == "мама", path) == ("мама",)
    assert suggest(frozenset({"noun"}), lambda w: True, path) == ("мама", "тато")
    assert suggest(frozenset({"verb:inf"}), lambda w: True, path) == ("читати",)
    assert suggest(frozenset({"adv"}), lambda w: True, path) == ()  # report: no replacement found
    assert suggest(frozenset({"noun"}), lambda w: False, path) == ()
    assert suggest(frozenset({"tag-a"}), lambda w: True, tmp_path / "absent.yaml") == ()
    assert suggest(frozenset(), lambda w: True, tmp_path / "absent.yaml") == ()

    assert a1_reference.teaching_replacement_text(frozenset({"noun"}), lambda w: True, tags, path) == "мама, тато"
    assert (
        a1_reference.teaching_replacement_text(frozenset({"adv"}), lambda w: True, tags, path) == "no replacement found"
    )
    assert suggest(frozenset({"adj"}), lambda w: True, path) == ()  # VESUM pronoun, even absent from A1 PULS


@pytest.mark.parametrize("mode", ["advisory", "failure"])
@pytest.mark.parametrize("step,expected", [("s1", "no replacement found"), ("s2", "мама")])
@pytest.mark.parametrize("location", ["core", "incidental_teach", "incidental_uses", "incidental_activity"])
def test_all_cli_replacements_use_introducing_step_letters(
    tmp_path, monkeypatch, capsys, mode, step, expected, location
):
    from tests.curriculum.test_plan_validate_mechanical import MANA

    monkeypatch.setattr(config, "A1_REFERENCE_ENFORCEMENT", mode)
    monkeypatch.setattr(quote_bytes, "vesum_lookup", lambda words: set(words))
    monkeypatch.setattr(a1_reference, "lemma_form_tags", lambda word: frozenset({"noun"}))

    def mutate(plan, pack, words, prior):
        lesson = plan["lessons"][0]
        item = next(item for item in lesson["inventory"]["vocabulary"]["core"] if item["evidence"] == MANA)
        item["forms"] = ["noun"]
        record = next(record for record in words["words"] if record["id"] == MANA)
        record["forms"][0]["tags"] = "noun"
        if location != "core":
            lesson["inventory"]["vocabulary"]["core"].remove(item)
            item.pop("forms")
            lesson["inventory"]["vocabulary"]["incidental"].append(item)
            lesson["steps"][1]["introduces"]["vocabulary"].remove(MANA)
            at = next(s for s in lesson["steps"] if s["id"] == step)
            if location == "incidental_teach":
                at["teach"] += f" Incidental {MANA}."
            elif location == "incidental_uses":
                at["uses"]["vocabulary"].append(MANA)
            else:
                activity = next(a for a in lesson["activities"] if a["id"] == at["practice"][0])
                activity["targets"] = [MANA]
        elif step == "s1":
            lesson["steps"][1]["introduces"]["vocabulary"].remove(MANA)
            lesson["steps"][0]["introduces"]["vocabulary"].append(MANA)

    path = _world(tmp_path, mutate)
    main([LEVEL, "--all", "--level-dir", str(path.parent), "--json"])
    payload = json.loads(capsys.readouterr().out)
    report = next(report for report in payload["plans"] if report["slug"] == SLUG)
    findings = report["notes" if mode == "advisory" else "failures"]
    (finding,) = [
        finding
        for finding in findings
        if finding["code"] == codes.A1_REFERENCE_WORD_MISSING and f"{MANA} " in finding["message"]
    ]
    assert finding["step"] == step
    assert f"teaching replacements: {expected} (#9582" in finding["message"]
    # Later steps and lessons teach А, Н and О; they cannot supply letters retroactively.
    assert "тато" not in finding["message"]
    assert not any(
        finding["code"] == codes.A1_REFERENCE_WORD_MISSING
        for finding in report["failures" if mode == "advisory" else "notes"]
    )


def test_replacement_tags_are_lemma_bound(monkeypatch):
    from scripts.verification import vesum

    monkeypatch.setattr(
        vesum,
        "verify_word",
        lambda word: [
            {"lemma": "п'ять", "tags": "numr"},
            {"lemma": "п'ята", "tags": "noun"},
        ],
    )
    assert a1_reference.lemma_form_tags("п’ять") == frozenset({"numr"})


@pytest.mark.parametrize("error", [FileNotFoundError, sqlite3.OperationalError])
def test_failed_replacement_lookup_is_unavailable(monkeypatch, error):
    from scripts.verification import vesum

    def unavailable(word):
        raise error("fixture")

    monkeypatch.setattr(vesum, "verify_word", unavailable)
    with pytest.raises(quote_bytes.VesumUnavailable):
        a1_reference.lemma_form_tags("мама")
    g = gates("неінвентарне")
    g.plan["lessons"][0]["steps"][0]["introduces"]["letters"] += ["м", "а"]
    g.check_a1_reference()
    assert "teaching replacements unavailable: VESUM lookup failed" in g.report.notes[0].message
    assert "no replacement found" not in g.report.notes[0].message


@pytest.mark.parametrize("missing", ["arc", "step"])
def test_replacements_require_known_introducing_step_state(missing):
    g = gates("неінвентарне")
    if missing == "arc":
        g.arc = None
    else:
        g.plan["lessons"][0]["steps"][0]["introduces"]["vocabulary"] = []
    g.check_a1_reference()
    assert "introducing-step letter state is unavailable" in g.report.notes[0].message
    assert "no replacement found" not in g.report.notes[0].message
