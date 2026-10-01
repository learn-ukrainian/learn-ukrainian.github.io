"""A1 media-backed choices: admission, key mutations, and rendered pack URLs."""

from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.build.fresh import assemble, runner
from scripts.build.fresh.draft_schema import validate_draft
from scripts.build.fresh.listening import choice_error, model_target
from scripts.curriculum.resolver.inputs import Allowlist
from tests.build.test_fresh_assemble import make_text_record, make_video_record, make_word_record
from tests.build.test_fresh_runner import _fixture, _run_contract
from tests.curriculum.resolver.evidence_helpers import receipt_sources  # noqa: F401


def _listening_fixture(*, letter: bool = False):
    draft, plan, pack, words = _fixture()
    value, target = ("Д", "T-1") if letter else ("слово", "W-1")
    pack["videos"] = [
        make_video_record(
            1,
            "https://www.youtube.com/watch?v=g4Bh-lqzd48",
            "Ukrainian Lessons Podcast",
            use=f"Pronunciation model for {value} before its rows.",
        )
    ]
    lesson = plan["lessons"][0]
    lesson["videos"] = [{"evidence": "V-1", "use": "Listen before choosing."}]
    lesson["steps"][0]["evidence"].append("V-1")
    lesson["steps"][0]["practice"] = ["a1"]
    lesson["activities"] = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Listen and choose."}]
    draft["steps"][0]["blocks"] += [{"kind": "video", "ref": "V-1"}, {"kind": "activity", "ref": "a1"}]
    if letter:
        pack["texts"] = [make_text_record(1, "Д д")]
        lesson["steps"][0]["evidence"].append("T-1")
        draft["steps"][0]["blocks"][0]["explains"].append("T-1")
        lesson["inventory"]["phonetics"] = {"letters": ["Д", "З", "Б"], "sounds": []}
        options = ["Д", "З", "Б"]
    else:
        other = make_word_record(2, "книга", gloss_en="book")
        words["words"].append(other)
        lesson["inventory"]["vocabulary"]["core"].append(
            {"lemma": other["lemma"], "evidence": other["id"], "forms": [other["forms"][0]["tags"]]}
        )
        draft["steps"][0]["blocks"][0]["text"] += "книга"
        options = ["слово", "книга"]
    item = {
        "kind": "listening",
        "question": "Listen, then choose.",
        "options": options,
        "correct": 0,
        "target_record": target,
        "host": {"kind": "video", "ref": "V-1"},
        "explanation": "Choose the printed model you heard.",
        "option_why": ["This matches the model.", *["This differs from the model."] * (len(options) - 1)],
    }
    if not letter:
        item["option_records"] = ["W-1", "W-2"]
    draft["activities"] = [{"id": "a1", "instruction": "Listen and choose.", "items": [item]}]
    return draft, plan, pack, words


def _check(tmp_path, fixture):
    draft, plan, pack, words = fixture
    lesson = plan["lessons"][0]
    allowlist = Allowlist.from_records(
        words["words"], letters=set(lesson["inventory"].get("phonetics", {}).get("letters", []))
    )
    return runner.check_7_a1_choices(
        draft,
        lesson,
        words,
        SimpleNamespace(tokens=[]),
        state_dir=tmp_path,
        lesson_n=1,
        pack=pack,
        allowlist=allowlist,
        vesum_lookup=lambda forms: {form: [] for form in forms},
    )


@pytest.mark.parametrize("letter", [False, True])
def test_listening_word_and_primer_letter_are_admitted(tmp_path, letter):
    fixture = _listening_fixture(letter=letter)
    draft = fixture[0]
    assert not validate_draft(draft, "a1", activity_types={"a1": "quiz"})
    assert _check(tmp_path, fixture)["status"] == "passed"


@pytest.mark.parametrize(
    ("mutation", "code", "layer"),
    [
        ("wrong_key", "listening_key_not_unique", "writer"),
        ("duplicate_target", "listening_key_not_unique", "writer"),
        ("unlisted", "listening_host_ineligible", "writer"),
        ("late", "listening_host_ineligible", "writer"),
        ("absent", "listening_host_ineligible", "writer"),
        ("wrong_ref", "listening_host_ineligible", "writer"),
        ("untaught", "listening_letter_not_taught", "writer"),
        ("wrong_model", "listening_model_unverified", "pack"),
        ("missing_video", "listening_video_missing", "pack"),
        ("unplanned_target", "listening_target_not_planned", "writer"),
    ],
)
def test_listening_refuses_mutations(tmp_path, mutation, code, layer):
    fixture = _listening_fixture(letter=True)
    draft, plan, pack, _words = fixture
    lesson, item, blocks = plan["lessons"][0], draft["activities"][0]["items"][0], draft["steps"][0]["blocks"]
    if mutation == "wrong_key":
        item["correct"] = 1
    elif mutation == "duplicate_target":
        item["options"][1] = item["options"][0].lower()
    elif mutation == "unlisted":
        lesson["videos"] = []
    elif mutation == "late":
        blocks[1], blocks[2] = blocks[2], blocks[1]
    elif mutation == "absent":
        blocks.pop(1)
    elif mutation == "wrong_ref":
        item["host"]["ref"] = "V-2"
    elif mutation == "untaught":
        item["options"][1] = "Ж"
    elif mutation == "wrong_model":
        pack["videos"][0]["use"] = "Pronunciation model for З before its rows."
    elif mutation == "missing_video":
        pack["videos"] = []
    elif mutation == "unplanned_target":
        lesson["steps"][0]["evidence"].remove("T-1")
    result = _check(tmp_path, fixture)
    assert (result["code"], result["layer"]) == (code, layer)


@pytest.mark.parametrize("workbook", [False, True])
def test_host_order_and_consolidation(tmp_path, workbook):
    fixture = _listening_fixture(letter=True)
    draft, plan, _pack, _words = fixture
    if workbook:
        plan["lessons"][0]["activities"][0]["placement"] = "workbook"
        plan["lessons"][0]["steps"][0]["practice"] = []
        plan["lessons"][0]["consolidation"] = ["a1"]
        draft["consolidation"]["activities"] = ["a1"]
        draft["steps"][0]["blocks"].pop()
    assert _check(tmp_path, fixture)["status"] == "passed"


@pytest.mark.parametrize("mutation", ["bindings", "untaught", "mismatch", "invalid_form"])
def test_listening_word_options_are_bound_to_taught_records(tmp_path, mutation):
    fixture = _listening_fixture()
    item = fixture[0]["activities"][0]["items"][0]
    if mutation == "bindings":
        item.pop("option_records")
    elif mutation == "untaught":
        item["option_records"][1] = "W-999"
    elif mutation == "mismatch":
        fixture[3]["words"].append({**copy.deepcopy(fixture[3]["words"][0]), "id": "W-3"})
        item["option_records"][0] = "W-3"
    elif mutation == "invalid_form":
        item["options"][1] = "book"
    assert _check(tmp_path, fixture)["status"] == "failed"


def test_video_opening_requires_attested_word_model():
    draft, plan, pack, words = _listening_fixture()
    draft["steps"][0]["blocks"][1]["target_record"] = "W-1"
    assert not validate_draft(draft, "a1", activity_types={"a1": "quiz"})
    row, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack, level="a1")
    assert row["status"] == "passed"
    pack["videos"][0]["use"] = "Season 1 story, heard by ear."
    row, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack, level="a1")
    assert (row["code"], row["layer"]) == ("listening_model_unverified", "pack")


@pytest.mark.parametrize("target", [None, "W-999", "T-999"])
def test_missing_model_target_stays_a_pack_gap(target):
    _, _, pack, words = _listening_fixture()
    assert model_target(target, "V-1", pack, words) == (None, "listening_target_invalid")


def test_nontext_listening_option_is_refused():
    assert (
        choice_error({"target_record": "T-1"}, [None], 0, "Д", {}, letters={"Д"}, record_ids=set())
        == "listening_option_invalid"
    )


@pytest.mark.parametrize("key", [-1, 1])
def test_listening_key_must_be_an_option_index(key):
    assert (
        choice_error({"target_record": "T-1"}, ["Д"], key, "Д", {}, letters={"Д"}, record_ids=set())
        == "listening_key_not_unique"
    )


@pytest.mark.parametrize("field", ["target_record", "host"])
def test_listening_schema_requires_bindings(field):
    draft, _, _, _ = _listening_fixture()
    draft["activities"][0]["items"][0].pop(field)
    assert validate_draft(draft, "a1", activity_types={"a1": "quiz"})


@pytest.mark.parametrize("mutation", ["url", "target_form", "description"])
def test_model_metadata_does_not_admit_unproved_words(mutation):
    _, _, pack, words = _listening_fixture()
    if mutation == "url":
        pack["videos"][0].pop("url")
    elif mutation == "target_form":
        words["words"][0]["forms"][0]["learner"] = False
    else:
        pack["videos"][0]["use"] = "Story about a word: слово."
    assert model_target("W-1", "V-1", pack, words)[1]


def test_unlisted_video_is_typed_before_generic_evidence_arithmetic():
    draft, plan, _, _ = _listening_fixture(letter=True)
    plan["lessons"][0]["videos"] = []
    assert runner.check_3_structure(draft, plan["lessons"][0])["code"] == "listening_host_ineligible"


def test_listening_renderer_keeps_host_beside_options_and_is_shippable(tmp_path: Path, monkeypatch):
    draft, plan, pack, words = _listening_fixture()
    (tmp_path / "sample-slug.yaml").write_text(yaml.safe_dump(plan, allow_unicode=True))

    def render_fixture(level, slug, **kwargs):
        # The fixture proves island props through real Node evaluation. A full
        # repository Astro build is reserved for CI and the requested live rebuild.
        return assemble.check_11_render(level, slug, **{**kwargs, "astro_build": False})

    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, render_check=render_fixture)
    assert report["passed"] is True, report
    assert report["checks"][-1]["details"]["verify_shippable"]["shippable"] is True
    mdx = (tmp_path / "site" / "1.mdx").read_text()
    # Both the step's model and the quiz's item host resolve to the locked media URL.
    assert '<YouTubeVideo client:only="react" url="https://www.youtube.com/watch?v=g4Bh-lqzd48"' in mdx
    assert '"host": {"kind": "video", "ref": "V-1", "url": "https://www.youtube.com/watch?v=g4Bh-lqzd48"' in mdx
    assert '"target_record": "W-1"' in mdx
