"""CI-collected exact-byte contract for synthetic Atlas reader fixtures (#11023)."""

import json
import os
import runpy
from pathlib import Path

import pytest

from scripts.projects.open_model_data.word_cards import dataset_projection as projection
from tests.projects.open_model_data import test_word_card_dataset_release as release_fixtures
from tests.word_card_certification_fixtures import certification_fixture  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "site/tests/fixtures/word-card-preview"
release_input = release_fixtures.release_input
synthetic_mount = release_fixtures.synthetic_mount


@pytest.mark.parametrize("format", ["jsonl", "json"])
def test_producer_generated_release(release_input, tmp_path, format):
    generator = runpy.run_path(str(FIXTURES / "generate_release.py"))
    cards, release = generator["generate"](release_input, tmp_path / "release", format)
    dataset_path = tmp_path / "release" / f"word-cards.{format}"
    manifest_path = tmp_path / "release/manifest.json"
    dataset = dataset_path.read_bytes()
    manifest = manifest_path.read_bytes()
    assert dataset == release.dataset
    assert manifest == projection.canonical(release.manifest)
    assert projection.sha256(dataset) == release.manifest["dataset_sha256"]
    rows = json.loads(dataset) if format == "json" else [json.loads(line) for line in dataset.splitlines()]
    assert [(r["card_id"], r["status"], r["card_version"]) for r in rows] == [
        ("wc_0123456789ab", "CERTIFIED", cards[0]["build"]["card_version"]),
        ("wc_0123456789ac", "CANDIDATE", "synthetic-candidate-1"),
    ]
    assert [r["fields"][0]["value"] for r in rows] == ["fixture-head", "fixture-head"]
    assert [f["value"] for f in rows[0]["fields"]] == [
        "fixture-head", "permitted-definition", "parallel-definition",
    ]
    assert {k: release.manifest[k] for k in (
        "card_count", "certified_count", "candidate_count", "field_citation_count",
    )} == {"card_count": 2, "certified_count": 1, "candidate_count": 1, "field_citation_count": 6}
    approved = FIXTURES / f"release-{format}"
    assert (approved / dataset_path.name).read_bytes() == dataset
    assert (approved / "manifest.json").read_bytes() == manifest
    receipt = {
        "provenance": "synthetic-fixture, never linguistic or publication approval",
        "producer_commit": generator["PRODUCER_COMMIT"],
        "producer_sha256": generator["PRODUCER_SHA256"],
        "inputs": cards, "input_sha256": projection.sha256(projection.canonical(cards)),
        "manifest_sha256": projection.sha256(manifest), "manifest": release.manifest,
    }
    report = os.environ.get("ATLAS_RELEASE_FREEZE_REPORT")
    if report:
        Path(report + f"-{format}.json").write_bytes(projection.canonical(receipt))
