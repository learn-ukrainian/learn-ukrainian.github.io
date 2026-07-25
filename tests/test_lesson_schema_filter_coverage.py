"""Guard for the Lesson Schema Drift gate (#5351).

The committed schema's input fingerprints must match a recomputation, so any
PR touching a generator input surfaces staleness. This is independent of CI
wiring: as of the CI reboot (#5762), `contracts` in ci.yml regenerates the
schema and diffs it on every run — unconditionally, not path-filtered — so
the sibling coverage test that used to guard the `lesson_schema` path filter
was deleted (that filter no longer gates anything).

This test derives its expectations FROM the generator module, so moving or
adding an input without updating `generate_lesson_schema.py` fails pytest.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(_REPO_ROOT))
from scripts.build import generate_lesson_schema as gen


def test_committed_lesson_schema_fingerprints_are_fresh() -> None:
    """Recompute the generator's input hashes (pure Python — no node
    extraction) and compare with the committed ``generated_from`` block.
    Mismatch == the exact drift the CI gate reds on (#5351)."""
    committed = yaml.safe_load(gen.OUTPUT_PATH.read_text(encoding="utf-8"))
    generated_from = committed["generated_from"]
    expected = {
        "components_sha256": gen._hash_files(gen.discover_components(gen.COMPONENTS_DIR)),
        "config_tables_sha256": gen._hash_file(gen.CONFIG_TABLES_PATH),
        "lesson_contract_sha256": gen._hash_file(gen.LESSON_CONTRACT_PATH),
    }
    stale = {
        key: (generated_from.get(key), value)
        for key, value in expected.items()
        if generated_from.get(key) != value
    }
    assert not stale, (
        f"docs/lesson-schema.yaml is stale vs its inputs: {stale}. "
        "Run: .venv/bin/python scripts/build/generate_lesson_schema.py"
    )
