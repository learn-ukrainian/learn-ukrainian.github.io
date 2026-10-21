"""Current producer through the real Atlas reader, separate from the frozen byte oracle (#11129)."""

import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.projects.open_model_data.word_cards import dataset_projection as projection
from tests.projects.open_model_data import test_word_card_dataset_release as release_fixtures
from tests.word_card_certification_fixtures import certification_fixture  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
release_input = release_fixtures.release_input
synthetic_mount = release_fixtures.synthetic_mount
INPUT_SHA256 = "a28725cd0f60cace922b2e9d2272a0d06121516cc9755277fbcb098c817da6af"


@pytest.fixture
def live_packages(release_input, tmp_path):
    # No live SHA pin: future producer edits must exercise their own implementation.
    assert Path(projection.__file__).resolve() == ROOT / (
        "scripts/projects/open_model_data/word_cards/dataset_projection.py"
    )
    helper = runpy.run_path(str(SITE / "tests/fixtures/word-card-preview/generate_release.py"))
    packages = Path(os.environ.get("ATLAS_LIVE_EXPORT_ROOT", tmp_path / "packages"))
    packages.mkdir(parents=True)

    def create_release(cards, **kwargs):
        # Freeze the original controlled inputs before the current producer runs.
        inputs = (json.dumps(cards, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        assert hashlib.sha256(inputs).hexdigest() == INPUT_SHA256
        (packages / f"inputs-{kwargs['format']}.json").write_bytes(inputs)
        return projection.create_release(cards, **kwargs)

    for encoding in ("json", "jsonl"):
        _, release = helper["generate"](
            release_input, packages / encoding, encoding, producer=SimpleNamespace(create_release=create_release),
        )
        assert release.manifest["input_cards_sha256"] == INPUT_SHA256
        assert (packages / encoding / f"word-cards.{encoding}").read_bytes() == release.dataset
        assert {key: release.manifest[key] for key in (
            "card_count", "certified_count", "candidate_count", "field_citation_count",
        )} == {"card_count": 2, "certified_count": 1, "candidate_count": 1, "field_citation_count": 6}
    return packages


def test_generate_live_packages(live_packages):
    """Standalone Vitest uses this entrypoint under the existing synthetic authority."""
    assert sorted(p.name for p in live_packages.iterdir()) == [
        "inputs-json.json", "inputs-jsonl.json", "json", "jsonl",
    ]


@pytest.mark.site_toolchain
def test_current_producer_through_reader(live_packages):
    """Frontend CI runs this even for producer-only changes; unavailable runtime fails."""
    result = subprocess.run(
        ["node", str(SITE / "node_modules/vitest/vitest.mjs"), "run",
         "tests/unit/word-card-live-producer.test.ts", "--maxWorkers=2", "--reporter=verbose"],
        cwd=SITE, env={**os.environ, "PYTHON": sys.executable, "ATLAS_LIVE_EXPORT_ROOT": str(live_packages)},
        text=True, capture_output=True, timeout=90,
    )
    log = result.stdout + result.stderr
    (live_packages / "reader.log").write_text(log)
    if report := os.environ.get("ATLAS_LIVE_READER_LOG"):
        Path(report).write_text(log)
    assert result.returncode == 0, log
