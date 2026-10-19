"""The Sources ``word_card`` lookup labels every card by a fresh certification check (#11084).

Certified status comes only from the exact-artifact boundary over a synthetic
authority (``tests.word_card_certification_fixtures``); the repository ledger
certifies no real card. Every other card is served as a labelled candidate.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

from scripts.atlas import word_card_certification as cert
from tests.word_card_certification_fixtures import certification_fixture  # noqa: F401

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"
MODULE_PATH = SERVER_PATH.with_name("word_card.py")

sys.path.insert(0, str(Path(__file__).parent))
try:
    import sources_probe_fixture as fixture
finally:
    sys.path.remove(str(Path(__file__).parent))

_spec = importlib.util.spec_from_file_location("word_card_under_test", MODULE_PATH)
word_card = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = word_card
_spec.loader.exec_module(word_card)

VESUM = {
    "мова": [{"lemma": "мова", "pos": "noun", "tags": "noun:inanim:f:v_naz"}],
    "мови": [{"lemma": "мова", "pos": "noun", "tags": "noun:inanim:f:v_rod"}],
    "являється": [{"lemma": "являтися", "pos": "verb", "tags": "verb:imperf:pres:s:3"}],
    "баран": [{"lemma": "баран", "pos": "noun", "tags": "noun:anim:m:v_naz"}],
}


def fake_vesum(word: str) -> list[dict]:
    return VESUM.get(word, [])


def write_store(root: Path, *cards: dict, ledger: dict | None = None) -> Path:
    (root / "cards").mkdir(parents=True, exist_ok=True)
    for card in cards:
        (root / "cards" / f"{card['card_id']}.json").write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
    if ledger is not None:
        (root / "ledger.json").write_text(json.dumps({"cards": ledger}, ensure_ascii=False), encoding="utf-8")
    (root / "build-manifest.json").write_text(json.dumps({"build_id": "fixture-build@1"}), encoding="utf-8")
    return root


def lookup(word, store: Path | None, vesum=fake_vesum) -> dict:
    env = {} if store is None else {word_card.ENV_WORD_CARDS_DIR: str(store)}
    return word_card.lookup_word_card(word, env=env, vesum_lookup=vesum)


def candidate_card(card_id: str = "wc_aaaaaaaaaaaa", spelling: str = "мова", **kwargs) -> dict:
    stress = fixture.card_assertion(card_id, 1, "stress", "мо́ва")
    cefr = fixture.card_assertion(card_id, 2, "cefr", "A1", source_id="puls")
    return fixture.word_card(
        card_id,
        spelling,
        fields={"stress": fixture.card_field(stress), "cefr": fixture.card_field(cefr)},
        assertions=[stress, cefr],
        **kwargs,
    )


def test_certified_card_is_returned_as_certified(certification, tmp_path):
    card = certification.card
    card["key_at_creation"] = {"spelling": "мова", "pos": "noun"}
    stress = fixture.card_assertion(card["card_id"], 1, "stress", "мо́ва")
    card["assertions"] = [stress]
    card["fields"] = {"stress": fixture.card_field(stress)}
    certification.approve(card)
    cert.load_certified_card_for_export(card, required_approval="site")  # The fixture really certifies it.
    store = write_store(tmp_path / "build", card)

    result = lookup("мова", store)

    assert (result["result"], result["status"]) == ("card_found", "certified")
    [served] = result["cards"]
    assert served["status"] == "certified" and served["accepted"] is True
    assert served["certified_for"] == ["site", "dataset"]
    assert "certification_refusal" not in served
    assert served["notice"] == word_card.CERTIFIED_NOTICE
    assert served["version"]["card_version"] == card["build"]["card_version"]
    assert served["evidence_ids"] == [stress["assertion_id"]]
    [value] = served["fields"]["stress"]["values"]
    assert served["fields"]["stress"]["accepted"] is True
    assert value["value"] == "мо́ва" and value["selected"] is True
    assert value["citations"][0]["locator"] == stress["locator"]
    assert value["citations"][0]["source_id"] == "ulif"


def test_a_changed_certified_card_is_served_as_candidate(certification, tmp_path):
    card = certification.card
    card["key_at_creation"] = {"spelling": "мова", "pos": "noun"}
    certification.approve(card)
    card["key_at_creation"]["pos"] = "verb"  # Any byte change leaves the exact-artifact certification.
    store = write_store(tmp_path / "build", card)

    [served] = lookup("мова", store)["cards"]

    assert served["status"] == "candidate" and served["accepted"] is False
    assert set(served["certification_refusal"]) == {"site", "dataset"}


def test_uncertified_card_is_labelled_candidate_with_citations_and_gaps(tmp_path):
    card = candidate_card()
    ledger = {
        card["card_id"]: {
            "fields": {
                "stress": {"disposition": "asserted"},
                "aspect": {"disposition": "not_applicable", "reason": "not a verb"},
                "definition_uk": {"disposition": "source_absent", "reason": "no СУМ-20 article"},
            }
        }
    }
    store = write_store(tmp_path / "build", card, ledger=ledger)

    result = lookup("мова", store)

    assert (result["result"], result["status"]) == ("card_found", "candidate")
    [served] = result["cards"]
    assert served["status"] == "candidate" and served["accepted"] is False
    assert served["notice"] == word_card.CANDIDATE_NOTICE
    assert served["certified_for"] == []
    assert set(served["certification_refusal"]) == {"site", "dataset"}
    assert all(field["accepted"] is False for field in served["fields"].values())
    assert served["fields"]["cefr"]["values"][0]["citations"][0]["source_id"] == "puls"
    assert served["fields"]["stress"]["gaps"] == ["single_source: one independence group, not corroborated"]
    assert served["gaps"]["definition_uk"] == {"disposition": "source_absent", "reason": "no СУМ-20 article"}
    assert "aspect" not in served["gaps"]
    assert served["gaps"]["examples"] == {"disposition": "absent_from_card"}
    assert result["card_store"] == {
        "available": True,
        "build_id": "fixture-build@1",
        "card_files": 1,
        "unreadable_card_files": 0,
        "ledger": True,
    }
    assert served["version"] == {
        "card_version": "cv_probe",
        "build_id": "probe-build",
        "rules_version": "rules-v1-draft",
    }


def test_a_card_claiming_review_is_still_a_candidate(tmp_path):
    card = candidate_card()
    card["quality"]["linguistic_review"] = {
        "status": "reviewed",
        "record": "self-claimed",
        "lane": "author",
        "approved_for": ["site", "dataset"],
    }
    store = write_store(tmp_path / "build", card)

    [served] = lookup("мова", store)["cards"]

    assert served["status"] == "candidate"


def test_russianism_evidence_keeps_soviet_text_as_colonization_context(tmp_path):
    card_id = "wc_bbbbbbbbbbbb"
    exposed = fixture.card_assertion(card_id, 3, "russification_exposed", "imposed sense", source_id="sum11")
    card = fixture.word_card(
        card_id,
        "мова",
        assertions=[exposed],
        senses=[
            {
                "sense_id": "ws_aaaaaaaaaaaa",
                "order": 1,
                "state": "active",
                "sense_map": [],
                "fields": {"russification_exposed": fixture.card_field(exposed)},
            }
        ],
    )
    store = write_store(tmp_path / "build", card)

    [served] = lookup("мова", store)["cards"]

    field = served["senses"][0]["fields"]["russification_exposed"]
    assert field["accepted"] is False
    [citation] = field["values"][0]["citations"]
    assert citation["role"] == "soviet_colonization_context"
    assert citation["notice"] == word_card.SOVIET_CONTEXT_NOTICE


def test_known_russianism_without_a_card_names_the_russianism_tools(tmp_path):
    store = write_store(tmp_path / "build", candidate_card())

    result = lookup("являється", store)

    assert (result["result"], result["status"], result["cards"]) == ("no_card", "no_card", [])
    assert result["vesum"] == {"available": True, "attested": True, "lemmas": ["являтися"]}
    assert "check_russian_shadow" in result["per_facet_tools"]["russianism_and_calque"]
    assert "search_style_guide" in result["per_facet_tools"]["russianism_and_calque"]
    assert "No word card (certified or candidate)" in result["message"]


def test_word_not_in_vesum(tmp_path):
    mwe = candidate_card("wc_cccccccccccc", "вряди-годи", card_kind="mwe")
    store = write_store(tmp_path / "build", candidate_card(), mwe)

    absent = lookup("фывапр", store)
    assert (absent["result"], absent["vesum"]) == ("no_card", {"available": True, "attested": False, "lemmas": []})

    # A card is served on its own spelling even when VESUM does not attest it.
    found = lookup("вряди-годи", store)
    assert found["vesum"]["attested"] is False
    assert [c["card_id"] for c in found["cards"]] == ["wc_cccccccccccc"]
    assert found["cards"][0]["matched_by"] == "spelling"


@pytest.mark.parametrize(
    ("word", "reason"),
    [
        ("", "word is empty"),
        ("   ", "word is empty"),
        ("language", word_card.SHAPE_REASON),
        ("мова; DROP TABLE", word_card.SHAPE_REASON),
        ("'-", word_card.SHAPE_REASON),
        ("м" * 101, "word is longer than 100 characters"),
        (None, "word must be a string"),
        (42, "word must be a string"),
    ],
)
def test_garbage_input_is_an_explicit_invalid_result(tmp_path, word, reason):
    calls = []
    result = lookup(word, write_store(tmp_path / "build", candidate_card()), vesum=calls.append)

    assert (result["result"], result["status"], result["reason"], result["cards"]) == (
        "invalid_input",
        "invalid_input",
        reason,
        [],
    )
    assert calls == []  # Nothing is looked up for an unusable query.


def test_stress_marks_and_apostrophes_are_normalised(tmp_path):
    card = candidate_card("wc_dddddddddddd", "п'ять")
    store = write_store(tmp_path / "build", candidate_card(), card)

    assert lookup("мо́ва", store)["normalized"] == "мова"
    assert [c["card_id"] for c in lookup("п’ять", store)["cards"]] == ["wc_dddddddddddd"]


def test_stored_spellings_outside_the_query_shape_are_still_indexed(tmp_path):
    card = candidate_card("wc_jjjjjjjjjjjj", "Ой, лишенько!", card_kind="mwe")
    store = write_store(tmp_path / "build", card, candidate_card())

    result = lookup("Ой,  ли́шенько!", store)

    assert result["normalized"] == "Ой, лишенько!"
    assert [c["card_id"] for c in result["cards"]] == ["wc_jjjjjjjjjjjj"]


def test_inflected_form_finds_the_card_by_vesum_lemma(tmp_path):
    store = write_store(tmp_path / "build", candidate_card())

    [served] = lookup("мови", store)["cards"]

    assert served["matched_by"] == "vesum_lemma"


def test_homographs_are_all_returned_exact_case_first(tmp_path):
    lexeme = candidate_card("wc_eeeeeeeeeeee", "баран")
    proper = candidate_card("wc_ffffffffffff", "Баран", card_kind="proper_name")
    store = write_store(tmp_path / "build", proper, lexeme)

    assert [c["card_id"] for c in lookup("баран", store)["cards"]] == ["wc_eeeeeeeeeeee", "wc_ffffffffffff"]
    assert [c["card_id"] for c in lookup("Баран", store)["cards"]] == ["wc_ffffffffffff", "wc_eeeeeeeeeeee"]


def test_mixed_status_is_never_collapsed(certification, tmp_path):
    card = certification.card
    card["key_at_creation"] = {"spelling": "мова", "pos": "noun"}
    certification.approve(card)
    store = write_store(tmp_path / "build", card, candidate_card("wc_gggggggggggg", "Мова", card_kind="proper_name"))

    result = lookup("мова", store)

    assert result["status"] == "mixed"
    assert [c["status"] for c in result["cards"]] == ["certified", "candidate"]


@pytest.mark.parametrize(
    ("configured", "reason"),
    [
        (None, "not_configured"),
        ("", "empty_override"),
        ("relative/build", "relative_override"),
        ("file:///build", "uri_override"),
        ("{tmp}/missing", "store_missing"),
        ("{tmp}/file.json", "not_a_directory"),
    ],
)
def test_unavailable_store_is_explicit_and_path_free(tmp_path, configured, reason):
    (tmp_path / "file.json").write_text("{}", encoding="utf-8")
    env = {} if configured is None else {word_card.ENV_WORD_CARDS_DIR: configured.format(tmp=tmp_path)}

    result = word_card.lookup_word_card("мова", env=env, vesum_lookup=fake_vesum)

    assert (result["result"], result["card_store"]) == ("no_card", {"available": False, "reason": reason})
    assert str(tmp_path) not in json.dumps(result, ensure_ascii=False)
    assert result["per_facet_tools"] == word_card.PER_FACET_TOOLS


def test_unreachable_vesum_is_reported_not_guessed(tmp_path):
    def broken(_word):
        raise OSError("vesum.db is unavailable")

    result = lookup("мова", write_store(tmp_path / "build", candidate_card()), vesum=broken)

    assert result["vesum"] == {"available": False, "reason": "OSError"}
    assert [c["card_id"] for c in result["cards"]] == ["wc_aaaaaaaaaaaa"]


def test_store_changes_are_seen_and_unreadable_cards_are_counted(tmp_path):
    store = write_store(tmp_path / "build", candidate_card())
    assert lookup("баран", store)["result"] == "no_card"

    write_store(store, candidate_card("wc_hhhhhhhhhhhh", "баран"))
    (store / "cards" / "wc_broken00000.json").write_text("{not json", encoding="utf-8")
    result = lookup("баран", store)

    assert [c["card_id"] for c in result["cards"]] == ["wc_hhhhhhhhhhhh"]
    assert result["card_store"]["unreadable_card_files"] == 1


def test_a_card_rewritten_for_another_word_is_not_served(tmp_path):
    store = write_store(tmp_path / "build", candidate_card())
    assert lookup("мова", store)["result"] == "card_found"

    path = store / "cards" / "wc_aaaaaaaaaaaa.json"
    mtime = store.joinpath("cards").stat().st_mtime_ns
    path.write_text(json.dumps(candidate_card(spelling="хата"), ensure_ascii=False), encoding="utf-8")
    os.utime(store / "cards", ns=(mtime, mtime))  # In-place rewrite: the cached index is reused.

    assert lookup("мова", store)["result"] == "no_card"


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server_word_card", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tool_is_listed_read_only_and_dispatched(server_module, tmp_path, monkeypatch):
    tools = {tool.name: tool for tool in asyncio.run(server_module.list_tools())}
    tool = tools["word_card"]
    assert tool.annotations.read_only_hint is True and tool.annotations.destructive_hint is False
    assert tool.input_schema["required"] == ["word"]
    assert "candidate" in tool.description and "certified" in tool.description

    monkeypatch.setenv(word_card.ENV_WORD_CARDS_DIR, str(write_store(tmp_path / "build", candidate_card())))
    monkeypatch.setattr(server_module.word_card, "_vesum_lookup", fake_vesum)
    content, is_error, _typed = asyncio.run(server_module._dispatch_tool_call("word_card", {"word": "мова"}))

    assert is_error is False
    result = json.loads(content[0].text)
    assert (result["status"], result["cards"][0]["card_id"]) == ("candidate", "wc_aaaaaaaaaaaa")
    garbage, is_error, _typed = asyncio.run(server_module._dispatch_tool_call("word_card", {"word": "<b>"}))
    assert is_error is False and json.loads(garbage[0].text)["result"] == "invalid_input"
