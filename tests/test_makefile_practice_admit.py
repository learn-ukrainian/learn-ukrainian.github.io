"""The local curated admission refreshes every word-page practice surface."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_curated_admit_dry_run_refreshes_practice_api_and_atlas_runtime() -> None:
    result = subprocess.run(
        ["make", "-n", "practice-admit-curated-seed"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout
    deck = output.index("generate_practice_deck.py --practice-seed")
    hydrate = output.index("hydrate-lexicon-api-shards.ts")
    export = output.index("scripts.atlas.export_runtime_shards")
    assert deck < hydrate < export
