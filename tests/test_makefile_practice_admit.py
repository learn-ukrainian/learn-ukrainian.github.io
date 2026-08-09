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
        text=True, timeout=30,
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


def test_gold_slice_dry_run_uses_bounded_local_static_shards_without_cloze() -> None:
    result = subprocess.run(
        ["make", "-n", "practice-gold-curated-seed"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True, timeout=30,
    )

    output = result.stdout
    assert 'test "40" -ge 32' in output
    assert 'test "40" -le 50' in output
    assert 'site/public/lexicon' in output
    assert '--target "40"' in output
    assert "--seed-selection representative" in output
    assert "--disable-cloze" in output
    assert '--vesum-db "data/vesum.db"' in output
    assert "practice-deck-publish" not in output
    assert "atlas-local-practice-refresh" not in output
