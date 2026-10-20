"""The Sources ``word_card`` lookup labels every card by a fresh certification check (#11084).

Certified status comes only from the exact-artifact boundary over a synthetic
authority (``tests.word_card_certification_fixtures``); the repository ledger
certifies no real card. Every other card is served as a labelled candidate.
"""

from __future__ import annotations

import ast
import asyncio
import importlib.util
import json
import os
import shutil
import stat
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
        "off_store_card_files": 0,
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


def test_unpaired_soviet_text_is_withheld_from_candidate_lookup(tmp_path):
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

    result = lookup("мова", store)

    assert result["cards"] == []
    assert result["card_store"]["unreadable_card_files"] == 1
    assert "imposed sense" not in json.dumps(result)


def test_complete_soviet_contrast_is_flagged_and_keeps_its_correction(tmp_path):
    card_id, sense_id = "wc_bbbbbbbbbbbb", "ws_aaaaaaaaaaaa"
    norm = fixture.card_assertion(card_id, 2, "definition_uk", "Modern correction.", source_id="sum20")
    exposed = fixture.card_assertion(card_id, 3, "russification_exposed", "pair:probe", source_id="sum11")
    for a, tier in ((norm, 1), (exposed, 0)):
        a["subject"] = {"kind": "sense", "id": sense_id}
        a["tier"] = tier
    keys = ("source_id", "snapshot_id", "locator")
    exposed["value"] = {"red_flag": True, "soviet_colonization_context": {
        "pair_id": "pair:probe", "sense_id": sense_id, "distortion_type": "synthetic_fixture",
        "imposed": {"text": "Synthetic imposed quotation.", "sovietization_risk": 1,
                    "sovietization_keywords": ["synthetic"],
                    "citation": {**{k: exposed[k] for k in keys}, "attribution": "Historical fixture"}},
        "norm": {"text": norm["value"], "assertion_id": norm["assertion_id"],
                 "citation": {**{k: norm[k] for k in keys}, "attribution": "Modern fixture"}},
    }}
    card = fixture.word_card(card_id, "мова", assertions=[norm, exposed], senses=[{
        "sense_id": sense_id, "order": 1, "state": "active", "sense_map": [],
        "fields": {"definition_uk": fixture.card_field(norm), "russification_exposed": fixture.card_field(exposed)},
    }])
    store = write_store(tmp_path / "build", card)

    [served] = lookup("мова", store)["cards"]

    field = served["senses"][0]["fields"]["russification_exposed"]
    assert field["accepted"] is False
    [citation] = field["values"][0]["citations"]
    assert citation["role"] == "soviet_colonization_context"
    assert citation["notice"] == word_card.SOVIET_CONTEXT_NOTICE
    assert citation["value"]["red_flag"] is True
    assert citation["value"]["soviet_colonization_context"]["norm"]["text"] == "Modern correction."


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


# --- Review round 1 (#11084): digest coverage, child-target locality, provenance, unreadable stores ---


_DYNAMIC_LOADERS = frozenset({"importlib", "runpy", "imp", "zipimport"})
_DYNAMIC_BUILTINS = frozenset({"exec", "eval", "compile", "__import__"})
_DYNAMIC_METHODS = frozenset({"import_module", "spec_from_file_location", "exec_module", "load_module", "run_path"})


def _dynamic_loads(source: str) -> list[str]:
    """Imports of loader modules and calls that run code no import statement names."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name.split(".")[0] in _DYNAMIC_LOADERS]
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in _DYNAMIC_LOADERS:
            found.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _DYNAMIC_BUILTINS:
                found.append(node.func.id)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in _DYNAMIC_METHODS:
                found.append(node.func.attr)
    return found


def test_server_modules_load_code_only_through_imports_the_digest_traces():
    """The review digest hashes what import statements name; a dynamic load would run unhashed code."""
    from scripts.review.render_contract import server_code_files

    traced = server_code_files(PROJECT_ROOT)
    server_dir = SERVER_PATH.parent.relative_to(PROJECT_ROOT).as_posix() + "/"
    beside = sorted(name for name in traced if name.startswith(server_dir))

    assert ".mcp/servers/sources/word_card.py" in beside
    for name in beside:
        assert _dynamic_loads((PROJECT_ROOT / name).read_text(encoding="utf-8")) == [], name


def test_editing_word_card_changes_the_digest_and_refuses_the_launch(tmp_path):
    from scripts.review.render_contract import (
        LOCK_FILE,
        SERVER_ENTRY,
        ReviewContractError,
        check_launch_contract,
        server_code,
    )

    checkout = tmp_path / "checkout"
    for relative in (SERVER_ENTRY, ".mcp/servers/sources/word_card.py", LOCK_FILE):
        (checkout / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, checkout / relative)
    before = server_code(checkout)
    interpreter = Path(sys.executable)
    contract = {
        "server_checkout": str(checkout.resolve()),
        "server_interpreter": str(interpreter),
        "server_digest": before.digest,
        "server_components": before.components(),
    }
    check_launch_contract(contract, checkout, interpreter)  # Unchanged: admitted.

    module = checkout / ".mcp/servers/sources/word_card.py"
    module.write_text(module.read_text(encoding="utf-8") + "\nCHANGED = True\n", encoding="utf-8")

    assert ".mcp/servers/sources/word_card.py" in before.files
    assert server_code(checkout).digest != before.digest
    with pytest.raises(ReviewContractError, match="review_server_changed"):
        check_launch_contract(contract, checkout, interpreter)


@pytest.fixture
def network_dir(tmp_path, monkeypatch):
    """A directory the locality check reports as network storage; nothing under it may be read."""
    from scripts.storage import topology

    network = (tmp_path / "network").resolve()
    network.mkdir()
    real = topology.is_network_filesystem_path
    monkeypatch.setattr(
        topology,
        "is_network_filesystem_path",
        lambda path: Path(path).resolve().is_relative_to(network) or real(path),
    )
    return network


def test_cards_directory_symlinked_into_network_storage_is_refused(tmp_path, network_dir):
    write_store(network_dir / "remote", candidate_card())
    root = tmp_path / "build"
    root.mkdir()
    (root / "cards").symlink_to(network_dir / "remote" / "cards", target_is_directory=True)

    result = lookup("мова", root)

    assert (result["result"], result["cards"]) == ("no_card", [])
    assert result["card_store"] == {"available": False, "reason": "locality_network"}
    assert str(tmp_path) not in json.dumps(result, ensure_ascii=False)
    assert result["per_facet_tools"] == word_card.PER_FACET_TOOLS


@pytest.mark.parametrize("name", ["ledger.json", "build-manifest.json"])
def test_ledger_or_manifest_symlinked_into_network_storage_is_refused(tmp_path, network_dir, name):
    root = write_store(tmp_path / "build", candidate_card(), ledger={})
    (network_dir / name).write_bytes((root / name).read_bytes())
    (root / name).unlink()
    (root / name).symlink_to(network_dir / name)

    result = lookup("мова", root)

    assert result["card_store"] == {"available": False, "reason": "locality_network"}


def test_dangling_child_symlink_is_refused_not_skipped(tmp_path):
    root = write_store(tmp_path / "build", candidate_card())
    (root / "ledger.json").symlink_to(tmp_path / "gone.json")

    assert lookup("мова", root)["card_store"] == {"available": False, "reason": "store_missing"}


@pytest.mark.parametrize("into", ["network", "local_outside"])
def test_card_files_resolving_outside_the_cards_directory_are_never_read(tmp_path, network_dir, into):
    root = write_store(tmp_path / "build", candidate_card())
    outside = network_dir if into == "network" else tmp_path / "elsewhere"
    outside.mkdir(exist_ok=True)
    foreign = candidate_card("wc_kkkkkkkkkkkk", "баран")
    (outside / "wc_kkkkkkkkkkkk.json").write_text(json.dumps(foreign, ensure_ascii=False), encoding="utf-8")
    (root / "cards" / "wc_kkkkkkkkkkkk.json").symlink_to(outside / "wc_kkkkkkkkkkkk.json")

    result = lookup("баран", root)

    assert (result["result"], result["card_store"]["off_store_card_files"]) == ("no_card", 1)
    assert [c["card_id"] for c in lookup("мова", root)["cards"]] == ["wc_aaaaaaaaaaaa"]


def test_a_store_file_on_another_filesystem_than_checked_is_not_read(tmp_path):
    path = tmp_path / "ledger.json"
    path.write_text("{}", encoding="utf-8")
    moved = word_card.LocalTarget(path.resolve(), path.stat().st_dev + 1)

    with pytest.raises(word_card._OffStore):
        word_card._read_checked(moved)


def _linked_cards() -> tuple[dict, dict]:
    """Two homograph cards; each states one assertion of their shared derived link, as the pilot build does."""
    left = candidate_card("wc_llllllllllll", "баран")
    right = candidate_card("wc_mmmmmmmmmmmm", "Баран", card_kind="proper_name")
    left_ref = fixture.card_assertion(left["card_id"], 11, "homograph_of", "баран")
    right_ref = fixture.card_assertion(right["card_id"], 12, "homograph_of", "Баран")
    left["assertions"].append(left_ref)
    right["assertions"].append(right_ref)
    link = {
        "link_id": "wl_" + "1" * 24,
        "type": "homograph_of",
        "endpoints": [{"id": left["card_id"]}, {"id": right["card_id"]}],
        "basis": "derived",
        "derived_by": "rules:homograph_of",
        "assertion_ids": [left_ref["assertion_id"], right_ref["assertion_id"]],
        "state": "active",
    }
    left["links"] = [link]
    right["links"] = [json.loads(json.dumps(link))]
    return left, right


def test_link_citations_include_the_assertions_stated_on_the_other_endpoint(tmp_path):
    left, right = _linked_cards()
    store = write_store(tmp_path / "build", left, right)

    served = {c["card_id"]: c for c in lookup("баран", store)["cards"]}

    [link] = served["wc_llllllllllll"]["links"]
    assert link["evidence_ids"] == right["links"][0]["assertion_ids"]
    assert [c.get("card_id") for c in link["citations"]] == [None, "wc_mmmmmmmmmmmm"]
    assert all(c["source_id"] == "ulif" and c["locator"] for c in link["citations"])
    assert (link["basis"], link["derived_by"], link["card_ids"]) == (
        "derived",
        "rules:homograph_of",
        [right["card_id"]],
    )
    assert "gaps" not in link


def _certified_parent_linked_to(certification, endpoint: dict) -> dict:
    """The fixture's certified card as «мова», with two links to ``endpoint``: one also citing itself, one not."""
    card = certification.card
    card["key_at_creation"] = {"spelling": "мова", "pos": "noun"}
    own = fixture.card_assertion(card["card_id"], 21, "homograph_of", "мова")
    [endpoint_ref] = [a for a in endpoint["assertions"] if a["field"] == "homograph_of"]
    card["assertions"] = [own]
    card["links"] = [
        {
            "link_id": "wl_" + suffix * 24,
            "type": "homograph_of",
            "endpoints": [{"id": card["card_id"]}, {"id": endpoint["card_id"]}],
            "basis": "derived",
            "derived_by": "rules:homograph_of",
            "assertion_ids": ids,
            "state": "active",
        }
        for suffix, ids in (
            ("2", [own["assertion_id"], endpoint_ref["assertion_id"]]),
            ("3", [endpoint_ref["assertion_id"]]),
        )
    ]
    certification.approve(card)
    cert.load_certified_card_for_export(card, required_approval="site")  # The fixture really certifies it.
    return card


def _linked_endpoint(card_id: str = "wc_nnnnnnnnnnnn") -> dict:
    endpoint = candidate_card(card_id, "Мова", card_kind="proper_name")
    endpoint["assertions"].append(fixture.card_assertion(card_id, 22, "homograph_of", "Мова"))
    return endpoint


def _accepted_payload(served: dict) -> bytes:
    """Everything a certified card asserts as accepted: the card without its separate candidate relations."""
    return json.dumps({k: v for k, v in served.items() if k != "candidate_links"}, sort_keys=True).encode()


def test_an_uncertified_endpoint_never_changes_a_certified_card(certification, tmp_path):
    endpoint = _linked_endpoint()
    parent = _certified_parent_linked_to(certification, endpoint)
    store = write_store(tmp_path / "build", parent, endpoint)

    [before] = [c for c in lookup("мова", store)["cards"] if c["card_id"] == parent["card_id"]]
    endpoint_ref = endpoint["assertions"][-1]
    endpoint_ref["value"] = endpoint_ref["value_norm"] = "змінено"
    endpoint_ref["locator"] = "ulif:probe:mutated"
    write_store(tmp_path / "build", endpoint)
    [after] = [c for c in lookup("мова", store)["cards"] if c["card_id"] == parent["card_id"]]

    for served in (before, after):
        assert (served["status"], served["accepted"]) == ("certified", True)
        assert served["version"]["card_version"] == parent["build"]["card_version"]
        # The certified links cite only the parent's own assertion; the endpoint's evidence id is a gap.
        [link] = served["links"]
        assert [c.get("card_id") for c in link["citations"]] == [None]
        assert link["gaps"] == [
            f"uncited_evidence {endpoint_ref['assertion_id']}: "
            "no retained source assertion on this card or its certified link endpoints"
        ]
        assert served["gaps"]["links"]["links"] == [
            {
                "link_id": "wl_" + "3" * 24,
                "type": "homograph_of",
                "disposition": "no_certified_citation_withheld",
                "evidence_ids": [endpoint_ref["assertion_id"]],
            }
        ]
        # The endpoint appears only as candidate relations, each bound to the endpoint card's own version.
        assert [c["link_id"] for c in served["candidate_links"]] == ["wl_" + "2" * 24, "wl_" + "3" * 24]
        for candidate in served["candidate_links"]:
            assert (candidate["status"], candidate["accepted"]) == ("candidate", False)
            imported = candidate["citations"][-1]
            assert (imported["card_id"], imported["card_status"], imported["card_certified_for"]) == (
                endpoint["card_id"],
                "candidate",
                [],
            )
            assert imported["card_version"] == endpoint["build"]["card_version"]
    assert _accepted_payload(after) == _accepted_payload(before)
    assert before["candidate_links"][-1]["citations"][-1]["locator"] == "ulif:probe:22"
    assert after["candidate_links"][-1]["citations"][-1]["locator"] == "ulif:probe:mutated"
    assert after["candidate_links"][-1]["citations"][-1]["value"] == "змінено"


def test_a_certified_endpoint_is_cited_with_its_bound_version(certification, tmp_path):
    endpoint = json.loads(json.dumps(certification.card))  # The fixture's certifiable shape, as a second card.
    endpoint.update(card_id="wc_0123456789ac", card_kind="proper_name")
    endpoint["key_at_creation"] = {"spelling": "Мова", "pos": "noun"}
    endpoint["assertions"] = [fixture.card_assertion(endpoint["card_id"], 22, "homograph_of", "Мова")]
    certification.approve(endpoint)
    certified_version = endpoint["build"]["card_version"]
    cert.load_certified_card_for_export(endpoint, required_approval="site")
    parent = _certified_parent_linked_to(certification, endpoint)
    store = write_store(tmp_path / "build", parent, endpoint)

    [served] = [c for c in lookup("мова", store)["cards"] if c["card_id"] == parent["card_id"]]

    assert "candidate_links" not in served and "links" not in served["gaps"]
    assert [link["link_id"] for link in served["links"]] == ["wl_" + "2" * 24, "wl_" + "3" * 24]
    imported = served["links"][-1]["citations"][-1]
    assert (imported["card_id"], imported["card_version"], imported["card_status"]) == (
        endpoint["card_id"],
        certified_version,
        "certified",
    )
    assert imported["card_certified_for"] == ["site", "dataset"]

    endpoint["assertions"][-1]["locator"] = "ulif:probe:mutated"  # The endpoint leaves its certification.
    write_store(tmp_path / "build", endpoint)
    [changed] = [c for c in lookup("мова", store)["cards"] if c["card_id"] == parent["card_id"]]

    assert changed["status"] == "certified"
    assert all(c.get("card_id") is None for link in changed["links"] for c in link["citations"])
    assert [c["link_id"] for c in changed["candidate_links"]] == ["wl_" + "2" * 24, "wl_" + "3" * 24]


def test_uncitable_link_is_a_gap_not_a_link(tmp_path):
    left, _right = _linked_cards()
    left["links"][0]["assertion_ids"] = ["wa_" + "e" * 24]
    store = write_store(tmp_path / "build", left)  # The other endpoint is not in the build either.

    [served] = lookup("баран", store)["cards"]

    assert served["links"] == []
    assert served["gaps"]["links"]["links"] == [
        {
            "link_id": "wl_" + "1" * 24,
            "type": "homograph_of",
            "disposition": "uncitable_link_withheld",
            "evidence_ids": ["wa_" + "e" * 24],
        }
    ]


def test_dangling_field_evidence_is_a_gap_never_a_value(tmp_path):
    card = candidate_card()
    dangling = "wa_" + "d" * 24
    card["fields"]["stress"]["values"].append(
        {
            "value_norm": "мова́",
            "assertion_ids": [dangling],
            "independence_groups": ["G-X"],
            "mapping_evidenced": True,
            "independence_groups_evidenced": 1,
        }
    )
    card["fields"]["cefr"]["values"][0]["assertion_ids"].append(dangling)
    card["fields"]["cefr"]["non_voting"] = [{"assertion_id": dangling, "reason": "mapping low"}]
    store = write_store(tmp_path / "build", card)

    [served] = lookup("мова", store)["cards"]

    stress = served["fields"]["stress"]
    assert [v["value"] for v in stress["values"]] == ["мо́ва"]  # The uncited value is withheld.
    assert "мова́" not in json.dumps(stress, ensure_ascii=False)
    assert (
        f"uncitable_value withheld: no retained source assertion cites it (evidence ids {dangling})" in stress["gaps"]
    )
    cefr = served["fields"]["cefr"]
    [value] = cefr["values"]
    assert value["evidence_ids"] == ["wa_000000000000000000000002"]
    assert all("missing_assertion" not in c for c in value["citations"])
    assert cefr["non_voting"] == [{"evidence_id": dangling, "reason": "mapping low"}]
    assert word_card._uncited(dangling) in cefr["gaps"]


def test_tombstoned_evidence_cites_no_source(tmp_path):
    card = candidate_card()
    stress_id = card["fields"]["stress"]["values"][0]["assertion_ids"][0]
    card["assertions"] = [
        {"assertion_id": stress_id, "status": "suppressed", "suppression_ref": "takedown:1"}
        if a["assertion_id"] == stress_id
        else a
        for a in card["assertions"]
    ]
    store = write_store(tmp_path / "build", card)

    [served] = lookup("мова", store)["cards"]

    assert served["fields"]["stress"]["values"] == []
    assert any(g.startswith("uncitable_value withheld") for g in served["fields"]["stress"]["gaps"])


def test_identity_and_sense_provenance_is_kept(tmp_path):
    card = candidate_card()
    source_key = {"source_id": "ulif", "key": "ulif:entry:1", "snapshot_id": "probe"}
    card["key_at_creation"]["source_keys"] = [source_key]
    card["identity"].update({"source_keys": [source_key], "decided_by": "rules:probe", "notes": ["n"]})
    card["senses"] = [
        {
            "sense_id": "ws_aaaaaaaaaaaa",
            "order": 1,
            "state": "unsplit",
            "sense_map": [{"source_id": "ulif", "source_sense_key": "ulif:entry:1#unsplit"}],
            "seeded_from": "ulif_sense_gloss:ulif:entry:1",
            "fields": {},
        }
    ]
    store = write_store(tmp_path / "build", card)

    [served] = lookup("мова", store)["cards"]

    identity = served["identity"]
    assert identity["source_keys"] == identity["key_source_keys"] == [source_key]
    assert (identity["decided_by"], identity["notes"]) == ("rules:probe", ["n"])
    [sense] = served["senses"]
    assert sense["sense_map"] == card["senses"][0]["sense_map"]
    assert sense["seeded_from"] == "ulif_sense_gloss:ulif:entry:1"


@pytest.fixture
def unreadable_cards(tmp_path):
    store = write_store(tmp_path / "build", candidate_card())
    cards = store / "cards"
    cards.chmod(0)
    try:
        if os.access(cards, os.R_OK):
            pytest.skip("this user reads a mode-000 directory")
        yield store
    finally:
        cards.chmod(stat.S_IRWXU)


def test_unreadable_cards_directory_is_an_explicit_unavailable_result(unreadable_cards, tmp_path):
    result = lookup("мова", unreadable_cards)

    assert (result["result"], result["cards"]) == ("no_card", [])
    assert result["card_store"] == {"available": False, "reason": "store_unavailable"}
    assert result["per_facet_tools"] == word_card.PER_FACET_TOOLS
    assert "Use the per-facet tools" in result["message"]
    assert str(tmp_path) not in json.dumps(result, ensure_ascii=False)


def test_unreadable_store_through_the_wire_handler_names_the_tools(
    server_module, unreadable_cards, tmp_path, monkeypatch
):
    monkeypatch.setenv(word_card.ENV_WORD_CARDS_DIR, str(unreadable_cards))
    monkeypatch.setattr(server_module.word_card, "_vesum_lookup", fake_vesum)

    content, is_error, _typed = asyncio.run(server_module._dispatch_tool_call("word_card", {"word": "мова"}))

    assert is_error is False
    result = json.loads(content[0].text)
    assert result["card_store"] == {"available": False, "reason": "store_unavailable"}
    assert result["per_facet_tools"]["stress"] == ["verify_stress", "query_sum20"]
    assert str(tmp_path) not in content[0].text


def test_unreadable_ledger_is_reported_not_silently_empty(tmp_path):
    store = write_store(tmp_path / "build", candidate_card(), ledger={})
    (store / "ledger.json").write_text("{broken", encoding="utf-8")

    result = lookup("мова", store)

    assert result["card_store"]["ledger"] is False and result["card_store"]["ledger_unreadable"] is True
