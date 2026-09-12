"""Pinned, hash-checked curriculum upgrade fixtures; no Git or network at test time."""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures/curriculum_upgrade/gold.json"
BASE = "7829e74b6031cdcc4ef69895b5f42e0643569e44"
GOLD = "0801b58beece2b2b6380327fb24fd0e3ff129dd5"
ORIGINAL = "curriculum/l2-uk-en/a1-v1/things-have-gender"
UPGRADED = "curriculum/l2-uk-en/a1/things-have-gender"


@lru_cache(maxsize=1)
def load_upgrade_fixtures() -> dict:
    """Verify every verbatim file before returning the read-only fixture bundle."""
    bundle = json.loads(FIXTURE_PATH.read_text())
    for source_name, commit in (("baseline", BASE), ("gold", GOLD)):
        source = bundle["sources"][source_name]
        if source["commit"] != commit:
            raise ValueError(f"Fixture commit drift: {source_name}")
        for path, artifact in source["files"].items():
            actual = hashlib.sha256(artifact["text"].encode("utf-8")).hexdigest()
            if actual != artifact["sha256"]:
                raise ValueError(f"Fixture content drift: {source_name}/{path}")
    return bundle


def fixture_text(source: str, path: str) -> str:
    return load_upgrade_fixtures()["sources"][source]["files"][path]["text"]


def extract_upgrade_fixtures(destination: Path, source: str = "gold") -> Path:
    """Materialize fixture paths beneath a pytest temporary directory only."""
    root = destination.resolve()
    for path, artifact in load_upgrade_fixtures()["sources"][source]["files"].items():
        target = (root / path).resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"Fixture path escapes destination: {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact["text"])
    return root
