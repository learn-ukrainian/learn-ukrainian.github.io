"""Resolve logical freeze receipts to release-owned, byte-preserved sources.

Logical paths and hashes in the immutable manifests remain unchanged. There is
no live-source fallback for an archived artifact, including a missing copy.
"""

from pathlib import Path

RELEASE_DIR = Path("data/projects/ua_eval_harness/releases/v0.1.1")
FROZEN_SOURCES = {
    Path("scripts/config/vesum_source.lock.json"): RELEASE_DIR / "vesum_source.lock.json",
    Path("scripts/rag/vesum_reingest.py"): RELEASE_DIR / "vesum_reingest.py",
    Path("scripts/projects/ua_eval_harness/build_scoring_dispositions.py"):
        RELEASE_DIR / "build_scoring_dispositions.py",
}


def frozen_source_path(root: Path, logical: Path) -> Path:
    """Resolve a pinned logical source without reading today's replacement."""
    return root / FROZEN_SOURCES.get(logical, logical)
