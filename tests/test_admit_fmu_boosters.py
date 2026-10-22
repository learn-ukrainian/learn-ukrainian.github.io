"""Regression tests for Anna Ohoiko FMU Vocabulary Booster intake (#7454)."""

import json
from pathlib import Path

import pytest
import yaml

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import validate_decision_file
from scripts.verification.vesum import verify_word

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INV_PATH = PROJECT_ROOT / "registry/lexicon/source-inventory/ohoiko-fmu-booster-vocabulary.yaml"
DECISIONS_PATH = (
    PROJECT_ROOT / "registry/lexicon/source-inventory-review-decisions/2026-09-13-ohoiko-fmu-booster-approve.yaml"
)
POINTER_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.pointer.json"
FINGERPRINT_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"


def test_booster_translation_credit_is_bound_to_declared_episode_and_each_term():
    """Missing per-term provenance must not erase an explicitly declared episode."""
    from scripts.lexicon.admit_fmu_boosters import EPISODES_DATA, build_new_atlas_entry

    for episode in EPISODES_DATA:
        entry = build_new_atlas_entry("fixture phrase", "noun", "first / second", episode)
        translation = entry["enrichment"]["translation"]
        assert translation["en"] == ["first", "second"]
        assert translation["attributions"] == [
            {"text": term, "source": "Anna Ohoiko", "source_title": episode["title"],
             "source_url": episode["url"], "locator": f"fmu-booster-ep-{episode['num']}"}
            for term in ["first", "second"]
        ]
        assert build_new_atlas_entry("fixture phrase", "noun", "first / second", episode) == entry


@pytest.mark.parametrize("gloss", ["", " / , ; "])
def test_booster_unsplittable_gloss_keeps_exact_text_and_episode_credit(gloss):
    """Empty split results must retain the original gloss and its own provenance."""
    from scripts.lexicon.admit_fmu_boosters import EPISODES_DATA, build_new_atlas_entry

    entry = build_new_atlas_entry("fixture phrase", "noun", gloss, EPISODES_DATA[0])
    translation = entry["enrichment"]["translation"]
    assert translation["en"] == [gloss]
    assert translation["terms"] == [gloss]
    assert translation["gloss"] == gloss
    assert translation["attributions"] == [{
        "text": gloss, "source": "Anna Ohoiko",
        "source_title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 4: Means of Transport",
        "source_url": "https://www.ukrainianlessons.com/fmu4/", "locator": "fmu-booster-ep-04",
    }]


@pytest.mark.parametrize("missing", ["num", "url", "title"])
def test_booster_missing_episode_metadata_cannot_invent_provenance(missing):
    """Absent authoritative fields must fail instead of synthesizing credit."""
    from scripts.lexicon.admit_fmu_boosters import EPISODES_DATA, build_new_atlas_entry

    episode = {key: value for key, value in EPISODES_DATA[0].items() if key != missing}
    with pytest.raises(KeyError, match=missing):
        build_new_atlas_entry("fixture phrase", "noun", "first", episode)


def test_fmu_booster_inventory_is_valid():
    assert INV_PATH.is_file(), f"Missing inventory file: {INV_PATH}"
    records = read_source_inventory(INV_PATH, project_root=PROJECT_ROOT)
    assert len(records) == 308, f"Expected 308 inventory records, got {len(records)}"

    sources = {r.source_id for r in records}
    assert len(sources) == 13, f"Expected 13 booster episodes, got {len(sources)}"
    assert all(s.startswith("ohoiko-fmu-booster-ep-") for s in sources)

    families = {r.source_family for r in records}
    assert families == {"ohoiko"}

    modes = {r.extraction_mode for r in records}
    assert modes == {"curated_headword"}


def test_fmu_booster_decisions_are_valid():
    assert DECISIONS_PATH.is_file(), f"Missing decisions file: {DECISIONS_PATH}"
    validate_decision_file(DECISIONS_PATH)

    data = yaml.safe_load(DECISIONS_PATH.read_text(encoding="utf-8"))
    decisions = data.get("decisions", [])
    assert len(decisions) == 308, f"Expected 308 decisions, got {len(decisions)}"
    assert all(d.get("decision") == "approve_for_publish" for d in decisions)
    assert all(d.get("approved_pos") for d in decisions)
    assert all(d.get("approved_gloss") for d in decisions)


def test_fmu_booster_all_single_words_vesum_attested(requires_vesum_db):
    records = read_source_inventory(INV_PATH, project_root=PROJECT_ROOT)
    for r in records:
        if " " not in r.lemma:
            forms = verify_word(r.lemma)
            assert bool(forms), f"Lemma {r.lemma} is not attested in VESUM"


@pytest.mark.needs_sparse_tree("site/src/data")
def test_fmu_booster_manifest_pointer_and_fingerprint():
    assert POINTER_PATH.is_file()
    assert FINGERPRINT_PATH.is_file()

    pointer = json.loads(POINTER_PATH.read_text(encoding="utf-8"))
    from scripts.lexicon.check_manifest_freshness import check_freshness
    from scripts.lexicon.manifest_fingerprint import build_fingerprint, sidecar_payload

    # Sidecar tracks lexicon-code bytes. The pointer digest pins the published
    # release asset and must not be rewritten on script-only CI fixes.
    assert check_freshness(root=PROJECT_ROOT, fingerprint_path=FINGERPRINT_PATH) == 0
    sidecar = json.loads(FINGERPRINT_PATH.read_text(encoding="utf-8"))
    assert sidecar == sidecar_payload(build_fingerprint(PROJECT_ROOT))
    assert pointer["manifest_fingerprint"]
    assert len(pointer["manifest_fingerprint"]) == 64
    assert (
        "fmu" in pointer["richness_gate"]["override_reason"].lower()
        or "booster" in pointer["richness_gate"]["override_reason"].lower()
    )


def test_fmu_booster_unsupported_attribution_rejected():
    from scripts.lexicon.admit_fmu_boosters import EPISODES_DATA, build_new_atlas_entry

    ep = EPISODES_DATA[0]
    entry = build_new_atlas_entry("будинок на колесах", "noun", "RV / camper", ep)

    # Reject fake VTS attribution and mirror URLs
    for card in entry.get("definition_cards", []):
        assert card["source_dict"] != "vts", "Curated FMU definitions must not claim VTS source_dict"
        assert "slovnyk.me" not in card.get("source_url", ""), "Mirror URLs are forbidden"
        assert card["source_dict"] == "ohoiko"
        assert card["source_url"].startswith("https://www.ukrainianlessons.com/")

    meaning = entry.get("enrichment", {}).get("meaning", {})
    assert meaning.get("source") != "vts"
    assert "slovnyk.me" not in meaning.get("source_url", "")


def test_fmu_booster_phrases_not_vesum_attested(monkeypatch):
    from scripts.lexicon import admit_fmu_boosters as admit

    def fake_verify_word(lemma: str, *args, **kwargs):
        return [{"lemma": lemma, "pos": "noun", "tags": ""}] if " " not in lemma else []

    monkeypatch.setattr(admit, "verify_word", fake_verify_word)

    ep = admit.EPISODES_DATA[0]
    phrase_entry = admit.build_new_atlas_entry("будинок на колесах", "noun", "camper", ep)
    assert phrase_entry["heritage_status"]["vesum_attested"] is False
    assert phrase_entry["entry_type"] == "phrase"

    word_entry = admit.build_new_atlas_entry("менеджерка", "noun", "manager", ep)
    assert word_entry["heritage_status"]["vesum_attested"] is True
    assert word_entry["entry_type"] == "lemma"


def test_fmu_booster_dry_run_preserves_files():
    from scripts.lexicon.build_fmu_booster_inventory import build_inventory_and_decisions

    inv_bytes_before = INV_PATH.read_bytes()
    dec_bytes_before = DECISIONS_PATH.read_bytes()

    inv_doc, dec_doc = build_inventory_and_decisions(dry_run=True)
    assert len(inv_doc["sources"]) == 13
    assert len(dec_doc["decisions"]) == 308

    assert INV_PATH.read_bytes() == inv_bytes_before
    assert DECISIONS_PATH.read_bytes() == dec_bytes_before


def test_release_publication_freezes_binary_and_scans_text(tmp_path, synthetic_opsec, publisher_transport, monkeypatch):
    import subprocess

    import pytest

    from scripts.lexicon.admit_fmu_boosters import _publish_asset
    from scripts.opsec import prepublish
    from tests.opsec_fixtures import CATALOG, TOKEN

    monkeypatch.setattr(prepublish, "catalog", lambda: CATALOG)
    monkeypatch.setenv("GH_REPO", "unit/public")
    asset = tmp_path / "unit.gz"
    asset.write_bytes(b"\xffunit")
    calls = []

    def send(args, **kwargs):
        calls.append(Path(args[-1]).read_bytes())
        assert kwargs["timeout"] == 120 and kwargs["check"] is True
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", send)
    _publish_asset(asset)
    assert calls == [b"\xffunit"]
    asset.write_text(TOKEN)
    with pytest.raises(prepublish.PublishBlocked):
        _publish_asset(asset)
    assert calls == [b"\xffunit"]
