"""The Cursor judge calibration never runs Auto or an unapproved model (#9274)."""

from __future__ import annotations

import sys

import pytest

from scripts.audit import cursor_judge_calibration as calibration


@pytest.mark.parametrize(
    ("model", "code"),
    [
        ("auto", "cursor_no_approved_model_pin"),
        ("Auto", "cursor_no_approved_model_pin"),
        ("cursor:auto", "cursor_no_approved_model_pin"),
        ("composer-2.5-fast", "CURSOR_MODEL_NOT_APPROVED"),
        ("", "cursor_no_approved_model_pin"),
    ],
)
def test_call_cursor_refuses_before_spawn(monkeypatch, model, code):
    monkeypatch.setattr(
        calibration.subprocess, "run", lambda *_a, **_k: pytest.fail("spawned the provider before refusing")
    )
    code_pattern = rf"\({code}\)" if code.startswith("cursor_") else rf"{code}: model"
    with pytest.raises(SystemExit, match=rf"^cursor_judge_calibration: refused: .*{code_pattern}"):
        calibration.call_cursor("judge this", model)


def test_main_refuses_auto_before_loading_cases(monkeypatch):
    monkeypatch.setattr(calibration, "pull_calibration_cases", lambda: pytest.fail("loaded cases before refusing"))
    monkeypatch.setattr(sys, "argv", ["cursor_judge_calibration.py", "--model", "auto", "--dry-run"])
    with pytest.raises(SystemExit, match=r"\(cursor_no_approved_model_pin\)"):
        calibration.main()


def test_call_cursor_runs_a_concrete_pin(monkeypatch):
    pin = "stand-in-cursor-pin-high"
    monkeypatch.setattr("lu_machinery.review.model_catalog.CURSOR_APPROVED_WIRE_PINS", frozenset({pin}))
    monkeypatch.setattr("lu_machinery.review.model_catalog.cursor_pinned_models", lambda catalog=None: (pin,))
    captured: list[list[str]] = []

    class _Proc:
        returncode = 0
        stdout = '{"verdict": "clean"}'
        stderr = ""

    monkeypatch.setattr(calibration.subprocess, "run", lambda argv, **_k: captured.append(argv) or _Proc())
    monkeypatch.setattr(calibration, "parse_json_verdict", lambda stdout, duration_s: {"verdict": "clean"})

    assert calibration.call_cursor("judge this", pin) == {"verdict": "clean"}
    assert captured[0][captured[0].index("--model") + 1] == pin
