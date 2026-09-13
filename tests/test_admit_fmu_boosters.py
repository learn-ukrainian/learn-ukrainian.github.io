"""Regression tests for Anna Ohoiko FMU Vocabulary Booster intake (#7454)."""

import json
from pathlib import Path

import yaml

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import validate_decision_file
from scripts.verification.vesum import verify_word

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INV_PATH = PROJECT_ROOT / "data/lexicon/source-inventory/ohoiko-fmu-booster-vocabulary.yaml"
DECISIONS_PATH = (
    PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions/2026-09-13-ohoiko-fmu-booster-approve.yaml"
)
POINTER_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.pointer.json"
FINGERPRINT_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"


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


def test_fmu_booster_all_single_words_vesum_attested():
    records = read_source_inventory(INV_PATH, project_root=PROJECT_ROOT)
    for r in records:
        if " " not in r.lemma:
            forms = verify_word(r.lemma)
            assert bool(forms), f"Lemma {r.lemma} is not attested in VESUM"


def test_fmu_booster_manifest_pointer_and_fingerprint():
    assert POINTER_PATH.is_file()
    assert FINGERPRINT_PATH.is_file()

    pointer = json.loads(POINTER_PATH.read_text(encoding="utf-8"))
    from scripts.lexicon.manifest_fingerprint import build_fingerprint

    bf = build_fingerprint(PROJECT_ROOT)

    assert pointer["manifest_fingerprint"] == bf["fingerprint"]
    assert (
        "fmu" in pointer["richness_gate"]["override_reason"].lower()
        or "booster" in pointer["richness_gate"]["override_reason"].lower()
    )
