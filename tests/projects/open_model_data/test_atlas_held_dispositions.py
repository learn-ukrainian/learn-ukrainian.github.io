"""Prevent omitted cards, invented pairings and uncited identities in #11361 data."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RELEASE = ROOT / "data/datasets/word-cards/releases/v0.1.0-pilot"


def test_held_dispositions_do_not_omit_duplicate_or_promote_release_cards() -> None:
    original = json.loads((RELEASE / "pairing-atlas0.json").read_text())
    document = json.loads((RELEASE / "pairing-atlas0-held43.json").read_text())
    held = {e["card_id"] for e in original["entries"] if e["status"] != "paired"}
    entries = document["entries"]
    assert len(entries) == len(held) == 43
    assert {e["card_id"] for e in entries} == held
    assert Counter(e["status"] for e in entries) == {"no_counterpart": 33, "held_ambiguous": 10}
    assert document["counts"] == {
        "examined": 43,
        "paired": 0,
        "no_counterpart": 33,
        "held_ambiguous": 10,
        "previously_paired_unchanged": 107,
        "release_total_conserved": 150,
    }
    for entry in entries:
        # Candidate metadata must never become an admitted top-level relation.
        assert "atlas0_slug" not in entry
        assert "pilot_card_id" not in entry
        assert entry["reason"] and entry["source_fields"]
        assert entry["release_condition"]


def test_homonyms_and_mixed_pages_do_not_gain_spelling_only_relations() -> None:
    document = json.loads((RELEASE / "pairing-atlas0-held43.json").read_text())
    entries = {e["card_id"]: e for e in document["entries"]}
    # Literal source IDs distinguish animal, device, building, six senses, spring,
    # two pronouns, restaurant, adverb, and personal name. None is a page-wide ID.
    expected = {
        "wc_02a5cjxcpbcf": 22123,
        "wc_bgr5q9c06wxg": 76793,
        "wc_cvkw5nzdg00n": 76792,
        "wc_h509ejs613sy": 3,
        "wc_p646xsqq40xt": 98008,
        "wc_gbh31d6zptnx": 210201,
        "wc_k45tstzkx2b6": 15,
        "wc_wmyzn565rxp4": 22087,
        "wc_0c2c6k5nrw0n": 266758,
        "wc_fvxestgxf73d": 11,
    }
    for cid, ulif_id in expected.items():
        entry = entries[cid]
        assert entry["status"] == "held_ambiguous"
        assert [e["entry_id"] for e in entry["ulif_entries"]] == [ulif_id]
        assert len(entry["candidate_pages"]) == 1
        assert entry["residual_owner"] == "Data"
    for entry in document["entries"]:
        if entry["status"] != "no_counterpart":
            continue
        if entry["candidate_pages"]:
            assert entry["card_kind"] == "proper_name"
            assert entry["reason_code"] == "proper_name_distinct_from_current_lexeme"
        else:
            assert not any(entry["search"][key] for key in [
                "active_atlas0_matches", "site_index_matches", "public_article_matches",
                "public_alias_matches", "site_alias_matches",
            ])


def test_disposition_citations_cannot_drift_from_tracked_source_identities() -> None:
    document = json.loads((RELEASE / "pairing-atlas0-held43.json").read_text())
    inputs = document["inputs"]
    tracked = {}
    for key, source in inputs.items():
        if key == "cards":
            # Release bytes are gitignored. The tracked original pairing pins them.
            original = json.loads((RELEASE / "pairing-atlas0.json").read_text())
            assert source["sha256"] == original["cards_sha256"]
            continue
        raw = (ROOT / source["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]
        tracked[key] = json.loads(raw)
    for entry in document["entries"]:
        source = entry["producer_identity_evidence"]
        identity = tracked["registry"]["entries"][int(source["pointer"].split("/")[-1])]
        assert identity["card_id"] == entry["card_id"]
        assert identity["card_kind"] == entry["card_kind"]
        for ulif in entry["ulif_entries"]:
            pointer = ulif["evidence"]["pointer"]
            selected = tracked["pilot"]["selection"]["source_records"][int(pointer.split("/")[3])]
            assert selected["raw_row"]["id"] == ulif["entry_id"]
            for field in ["canonical_headword", "grammatical_label", "sense_gloss"]:
                assert selected["raw_row"][field] == ulif[field]
        for candidate in entry["candidate_pages"]:
            pointer = candidate["registry_evidence"]["pointer"]
            current = tracked["registry"]["entries"][int(pointer.split("/")[-1])]
            assert current["state"] == "active"
            assert current["card_id"] == candidate["pilot_card_id"]
            assert {"source_id": "atlas0", "key": candidate["atlas0_slug"]} in current["key_at_creation"]["source_keys"]
