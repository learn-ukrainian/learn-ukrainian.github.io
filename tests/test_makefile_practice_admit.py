"""The local curated admission refreshes every word-page practice surface."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_curated_admit_dry_run_consumes_only_the_local_practice_overlay() -> None:
    result = subprocess.run(
        ["make", "-n", "practice-admit-curated-seed"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout
    assert "generate_practice_deck.py --manifest site/src/data/lexicon-manifest.json --local-practice-seed" in output
    assert "--allow-missing-routes" in output
    assert '--target "700"' in output
    assert 'batch_state/curated-v5-local-practice' in output
    assert "promote_grow_candidates" not in output
    assert "enrich_manifest.py --write" not in output
    assert "atlas:build-db" not in output
    assert "atlas-local-practice-refresh" not in output
