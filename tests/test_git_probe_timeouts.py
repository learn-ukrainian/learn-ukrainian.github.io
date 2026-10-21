"""Timeout contracts for the six git-probe subprocess sites (#7213 slice 17).

Every site below previously ran ``subprocess.run`` unbounded and now must:
1. pass ``timeout=30`` to every call, and
2. map ``subprocess.TimeoutExpired`` onto its existing fail-closed /
   non-zero / falsy shape (these run in hooks and CLI lanes, so a raw
   TimeoutExpired traceback must never escape).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.session_canary import grok_lane


def _raise_timeout(calls: list[dict[str, Any]]) -> Any:
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append(kwargs)
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


# --- scripts/pre_commit/check_plan_immutability.py ---------------------------


# --- scripts/session_canary/grok_lane.py -------------------------------------


def _score_args(tmp_path: Path, out_dir: Path, answers: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo=tmp_path,
        epic="probe-epic",
        out_dir=str(out_dir),
        answers=str(answers),
        context_tokens=1234,
        model="test-model",
        pass_ratio=grok_lane.DEFAULT_PASS_RATIO,
        threshold=grok_lane.DEFAULT_SIM_THRESHOLD,
        handoff=None,
        next_drive="",
        pins="",
        open_prs="",
        hands_off="",
        pending_user="",
        worktrees="",
        no_hydrate=True,
        preferred=None,
    )


def test_grok_lane_cmd_score_timeout_maps_to_fail_handoff_and_124(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(grok_lane.subprocess, "run", _raise_timeout(calls))
    out_dir = tmp_path / "canary"
    out_dir.mkdir()
    (out_dir / "probe.json").write_text(json.dumps({"anchors": []}), encoding="utf-8")
    answers = tmp_path / "answers.json"
    answers.write_text("{}", encoding="utf-8")

    rc = grok_lane.cmd_score(_score_args(tmp_path, out_dir, answers))

    assert rc == 124
    assert calls[0]["timeout"] == grok_lane._CANARY_TIMEOUT_SECONDS == 30
    verdict = json.loads((out_dir / "last_verdict.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "FAIL-HANDOFF"
    assert verdict["rc"] == 124


# --- scripts/hygiene/lane_disk_retention.py ----------------------------------


# --- scripts/hygiene/root_entry_guard.py -------------------------------------
