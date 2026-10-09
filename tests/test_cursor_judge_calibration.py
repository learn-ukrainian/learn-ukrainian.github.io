"""The Cursor judge calibration never runs Auto or an unapproved model (#9274)."""

from __future__ import annotations

import sys

import pytest

from scripts.audit import cursor_judge_calibration as calibration


@pytest.mark.parametrize("model", ["auto", "Auto", "cursor:auto", "composer-2.5-fast", ""])
def test_call_cursor_refuses_before_spawn(monkeypatch, model):
    monkeypatch.setattr(
        calibration.subprocess, "run", lambda *_a, **_k: pytest.fail("spawned the provider before refusing")
    )
    with pytest.raises(SystemExit, match=r"cursor_judge_calibration: refused: .*CURSOR_"):
        calibration.call_cursor("judge this", model)


def test_main_refuses_auto_before_loading_cases(monkeypatch):
    monkeypatch.setattr(calibration, "pull_calibration_cases", lambda: pytest.fail("loaded cases before refusing"))
    monkeypatch.setattr(sys, "argv", ["cursor_judge_calibration.py", "--model", "auto", "--dry-run"])
    with pytest.raises(SystemExit, match=r"\(cursor_auto_outside_coding_task\)"):
        calibration.main()


def test_call_cursor_runs_a_concrete_pin(monkeypatch):
    captured: list[list[str]] = []

    class _Proc:
        returncode = 0
        stdout = '{"verdict": "clean"}'
        stderr = ""

    monkeypatch.setattr(calibration.subprocess, "run", lambda argv, **_k: captured.append(argv) or _Proc())
    monkeypatch.setattr(calibration, "parse_json_verdict", lambda stdout, duration_s: {"verdict": "clean"})

    assert calibration.call_cursor("judge this", "composer-2.5") == {"verdict": "clean"}
    assert captured[0][captured[0].index("--model") + 1] == "composer-2.5"
