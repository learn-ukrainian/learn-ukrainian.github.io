"""Tests for plan hashing."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.io_utils import plan_hash


def test_plan_hash_changes_when_plan_file_changes(tmp_path: Path) -> None:
    plan_path = tmp_path / "demo.yaml"
    plan_path.write_text("title: Demo\nversion: '1.0'\n", "utf-8")

    first_hash = plan_hash(plan_path)

    plan_path.write_text("title: Demo updated\nversion: '1.1'\n", "utf-8")

    assert plan_hash(plan_path) != first_hash
