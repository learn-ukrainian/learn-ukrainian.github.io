"""Executable regressions for the Claude statusline account and rate-limit segments (#10644).

Every case runs the real script with synthetic status JSON in an isolated
environment, so the host's ``CLAUDE_CONFIG_DIR`` can never leak in.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATUSLINE = PROJECT_ROOT / "agents_extensions/shared/statusline/statusline.sh"

ANSI = re.compile(r"\x1b\[[0-9;]*m")
RED = "\x1b[31m"
YELLOW = "\x1b[33m"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="statusline needs jq")


def _run(tmp_path: Path, payload: dict[str, object], config_dir: str | None = None) -> str:
    env = {"PATH": os.environ["PATH"], "HOME": os.fspath(tmp_path)}
    if config_dir is not None:
        env["CLAUDE_CONFIG_DIR"] = config_dir
    payload = {"model": {"display_name": "Opus"}, "workspace": {"current_dir": os.fspath(tmp_path)}, **payload}
    completed = subprocess.run(
        [os.fspath(STATUSLINE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=env,
        timeout=30,
    )
    assert completed.stderr == ""
    return completed.stdout


def _limits(five: object = None, seven: object = None) -> dict[str, object]:
    limits: dict[str, object] = {}
    if five is not None:
        limits["five_hour"] = {"used_percentage": five}
    if seven is not None:
        limits["seven_day"] = {"used_percentage": seven}
    return {"rate_limits": limits}


@pytest.mark.parametrize(
    ("config_dir", "expected"),
    [
        (None, "[acct: A]"),
        ("", "[acct: A]"),
        ("/home/someone/.claude", "[acct: A]"),
        ("/home/someone/.claude/", "[acct: A]"),
        ("/home/someone/.claude-b", "[acct: B]"),
        ("/home/someone/.claude-b/", "[acct: B]"),
    ],
)
def test_account_segment_follows_config_dir(tmp_path: Path, config_dir: str | None, expected: str) -> None:
    out = ANSI.sub("", _run(tmp_path, {}, config_dir))
    assert out.startswith(f"[Opus] {expected} ")
    assert out.count("[acct:") == 1


@pytest.mark.parametrize("config_dir", ["/srv/secret-place/.claude-work", "/", "/home/x/claude", "/home/x/.claude-bb"])
def test_unknown_config_dir_omits_segment_and_never_prints_path(tmp_path: Path, config_dir: str) -> None:
    out = ANSI.sub("", _run(tmp_path, {}, config_dir))
    assert "[acct:" not in out
    assert "secret-place" not in out
    assert ".claude-work" not in out
    assert out.startswith("[Opus] ")


def test_account_segment_sits_between_model_and_context(tmp_path: Path) -> None:
    payload = {"context_window": {"context_window_size": 200_000, "total_input_tokens": 50_000}}
    out = ANSI.sub("", _run(tmp_path, payload, "/h/.claude-b"))
    assert out.startswith("[Opus] [acct: B] [ctx: ")


def test_both_windows_present_are_always_shown(tmp_path: Path) -> None:
    out = ANSI.sub("", _run(tmp_path, _limits(five=10, seven=25)))
    assert "[5h: 90% left]" in out
    assert "[7d: 75% left]" in out
    assert out.index("[5h:") < out.index("[7d:")


def test_only_one_window_present(tmp_path: Path) -> None:
    only_five = ANSI.sub("", _run(tmp_path, _limits(five=30)))
    assert "[5h: 70% left]" in only_five
    assert "[7d:" not in only_five
    only_seven = ANSI.sub("", _run(tmp_path, _limits(seven=30)))
    assert "[7d: 70% left]" in only_seven
    assert "[5h:" not in only_seven


@pytest.mark.parametrize(
    ("used", "left"),
    [(0, 100), (100, 0), (59.6, 40), (59.4, 41), (99.6, 0), (0.4, 100), (-5, 100), (150, 0), (100.2, 0)],
)
def test_remaining_is_rounded_and_clamped(tmp_path: Path, used: float, left: int) -> None:
    out = ANSI.sub("", _run(tmp_path, _limits(five=used)))
    assert f"[5h: {left}% left]" in out


@pytest.mark.parametrize(
    ("used", "colour"),
    [(81, RED), (80.6, RED), (100, RED), (80, YELLOW), (79, YELLOW), (61, YELLOW), (60, None), (59.4, None), (0, None)],
)
def test_colour_by_remaining_room(tmp_path: Path, used: float, colour: str | None) -> None:
    out = _run(tmp_path, _limits(seven=used))
    match = re.search(r"(\x1b\[[0-9;]*m)?\[7d: \d+% left\]", out)
    assert match is not None
    assert match.group(1) == colour


@pytest.mark.parametrize("bad", ["abc", "", None, True, [], {}, "59.6"])
def test_non_numeric_value_omits_segment_without_error(tmp_path: Path, bad: object) -> None:
    payload = {"rate_limits": {"five_hour": {"used_percentage": bad}, "seven_day": {"used_percentage": bad}}}
    out = ANSI.sub("", _run(tmp_path, payload))
    assert "[5h:" not in out
    assert "[7d:" not in out
    assert out.startswith("[Opus] [acct: A] ")


@pytest.mark.parametrize("limits", [{}, {"five_hour": {}}, {"five_hour": None}, "nope", None, []])
def test_missing_or_malformed_rate_limits_object(tmp_path: Path, limits: object) -> None:
    out = ANSI.sub("", _run(tmp_path, {"rate_limits": limits}))
    assert "[5h:" not in out
    assert "[7d:" not in out
    assert "[acct: A]" in out


def test_no_rate_limits_key_at_all(tmp_path: Path) -> None:
    out = ANSI.sub("", _run(tmp_path, {}))
    assert "[5h:" not in out
    assert "[7d:" not in out
