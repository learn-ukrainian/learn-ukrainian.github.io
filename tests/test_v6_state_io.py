"""Tests for v6_build state.json read/write helpers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build import v6_build


def test_save_v6_state_uses_atomic_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    plan_path = curriculum_root / "plans" / "a2" / "a2-bridge.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("module: a2-bridge\nlevel: A2\ncontent_outline: []\n", "utf-8")

    replace_calls: list[tuple[Path, Path]] = []
    real_replace = os.replace

    def track_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        replace_calls.append((Path(src), Path(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(v6_build.os, "replace", track_replace)

    v6_build._save_v6_state("a2", "a2-bridge", "check")

    state_path = curriculum_root / "a2" / "orchestration" / "a2-bridge" / "state.json"
    state = json.loads(state_path.read_text("utf-8"))

    assert state["mode"] == "v6"
    assert state["phases"]["check"]["status"] == "complete"
    assert replace_calls == [(replace_calls[0][0], state_path)]
    assert replace_calls[0][0].parent == state_path.parent
    assert replace_calls[0][0].suffix == ".tmp"
    assert not list(state_path.parent.glob("*.tmp"))


def test_save_v6_state_stores_plan_hash_for_tracked_writer_phases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    plan_path = curriculum_root / "plans" / "a2" / "a2-bridge.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "module: a2-bridge\nlevel: A2\ncontent_outline:\n  - section: Intro\n    words: 100\n",
        "utf-8",
    )

    v6_build._save_v6_state("a2", "a2-bridge", "write")
    state_path = curriculum_root / "a2" / "orchestration" / "a2-bridge" / "state.json"
    state = json.loads(state_path.read_text("utf-8"))

    assert state["phases"]["write"]["status"] == "complete"
    assert state["phases"]["write"]["plan_hash"] == v6_build._current_plan_hash("a2", "a2-bridge")


def test_save_v6_state_raises_on_corrupt_existing_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    state_path = curriculum_root / "a2" / "orchestration" / "a2-bridge" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{broken json", "utf-8")

    with pytest.raises(v6_build.V6StateError, match=r"Corrupt state\.json"):
        v6_build._save_v6_state("a2", "a2-bridge", "check")

    assert state_path.read_text("utf-8") == "{broken json"
