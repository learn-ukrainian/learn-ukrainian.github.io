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


def _run(
    tmp_path: Path,
    payload: dict[str, object],
    config_dir: str | None = None,
    capacity_file: Path | str | None = None,
) -> str:
    env = {"PATH": os.environ["PATH"], "HOME": os.fspath(tmp_path)}
    if config_dir is not None:
        env["CLAUDE_CONFIG_DIR"] = config_dir
    if capacity_file is not None:
        env["LU_STATUSLINE_CAPACITY_FILE"] = os.fspath(capacity_file)
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
def test_unknown_config_dir_shows_question_mark_and_never_prints_path(tmp_path: Path, config_dir: str) -> None:
    out = ANSI.sub("", _run(tmp_path, {}, config_dir))
    assert out.startswith("[Opus] [acct: ?] ")
    assert out.count("[acct:") == 1
    assert "secret-place" not in out
    assert ".claude-work" not in out
    assert "/home/x" not in out


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


# ── Capacity-file fallback ─────────────────────────────────────

CONFIG_A = "/h/.claude"
CONFIG_B = "/h/.claude-b"


def _rows(path: Path, *rows: object) -> Path:
    path.write_text("".join((r if isinstance(r, str) else json.dumps(r)) + "\n" for r in rows))
    return path


def _plain(tmp_path: Path, payload: dict[str, object], config_dir: str | None, cap: Path | str | None) -> str:
    return ANSI.sub("", _run(tmp_path, payload, config_dir, cap))


def test_fallback_fills_both_missing_windows(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": 62, "seven_day_left_pct": 35})
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h: 62% left]" in out
    assert "[7d: 35% left]" in out


def test_fallback_fills_only_the_missing_window(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": 62, "seven_day_left_pct": 35})
    out = _plain(tmp_path, _limits(five=10), CONFIG_A, cap)
    assert "[5h: 90% left]" in out
    assert "[7d: 35% left]" in out


def test_claude_code_field_wins_over_file(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": 5, "seven_day_left_pct": 6})
    out = _plain(tmp_path, _limits(five=10, seven=20), CONFIG_A, cap)
    assert "[5h: 90% left]" in out
    assert "[7d: 80% left]" in out


def test_fallback_colours_follow_thresholds(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": 19, "seven_day_left_pct": 39})
    out = _run(tmp_path, {}, CONFIG_A, cap)
    assert f"{RED}[5h: 19% left]" in out
    assert f"{YELLOW}[7d: 39% left]" in out


def test_account_b_row_selected(tmp_path: Path) -> None:
    cap = _rows(
        tmp_path / "cap.jsonl",
        {"account": "a", "five_hour_left_pct": 11, "seven_day_left_pct": 12},
        {"account": "b", "five_hour_left_pct": 71, "seven_day_left_pct": 72},
    )
    assert "[5h: 71% left]" in _plain(tmp_path, {}, CONFIG_B, cap)
    assert "[5h: 11% left]" in _plain(tmp_path, {}, CONFIG_A, cap)


def test_last_matching_row_wins_and_other_account_rows_are_ignored(tmp_path: Path) -> None:
    cap = _rows(
        tmp_path / "cap.jsonl",
        {"account": "a", "five_hour_left_pct": 90, "seven_day_left_pct": 91},
        {"account": "a", "five_hour_left_pct": 50, "seven_day_left_pct": 51},
        {"account": "b", "five_hour_left_pct": 1, "seven_day_left_pct": 2},
    )
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h: 50% left]" in out
    assert "[7d: 51% left]" in out


@pytest.mark.parametrize("label", ["A", "a", "claude:a", "Claude:A", "CLAUDE:a"])
def test_account_label_is_case_insensitive_with_optional_prefix(tmp_path: Path, label: str) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": label, "five_hour_left_pct": 44})
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h: 44% left]" in out
    assert "[7d:" not in out


def test_unset_config_dir_uses_account_a_rows(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "b", "five_hour_left_pct": 1}, {"account": "a", "five_hour_left_pct": 77})
    assert "[5h: 77% left]" in _plain(tmp_path, {}, None, cap)


def test_one_absent_value_in_row_shows_only_the_other(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "seven_day_left_pct": 33})
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[7d: 33% left]" in out
    assert "[5h:" not in out


def test_unknown_account_does_not_use_file(tmp_path: Path) -> None:
    cap = _rows(
        tmp_path / "cap.jsonl",
        {"account": "a", "five_hour_left_pct": 62, "seven_day_left_pct": 35},
        {"account": "?", "five_hour_left_pct": 63, "seven_day_left_pct": 36},
    )
    out = _plain(tmp_path, {}, "/srv/elsewhere/.claude-work", cap)
    assert "[acct: ?]" in out
    assert "[5h:" not in out
    assert "[7d:" not in out


def test_unknown_account_still_shows_claude_code_fields(tmp_path: Path) -> None:
    out = _plain(tmp_path, _limits(five=10), "/srv/elsewhere/.claude-work", tmp_path / "missing")
    assert "[acct: ?]" in out
    assert "[5h: 90% left]" in out


def test_env_variable_unset_shows_nothing(tmp_path: Path) -> None:
    _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": 62})
    out = _plain(tmp_path, {}, CONFIG_A, None)
    assert "[5h:" not in out


def test_env_variable_empty_shows_nothing(tmp_path: Path) -> None:
    out = _plain(tmp_path, {}, CONFIG_A, "")
    assert "[5h:" not in out


def test_missing_file_shows_nothing(tmp_path: Path) -> None:
    out = _plain(tmp_path, {}, CONFIG_A, tmp_path / "nope.jsonl")
    assert "[5h:" not in out
    assert "[7d:" not in out


def test_empty_file_shows_nothing(tmp_path: Path) -> None:
    cap = tmp_path / "cap.jsonl"
    cap.write_text("")
    assert "[5h:" not in _plain(tmp_path, {}, CONFIG_A, cap)


def test_directory_in_place_of_file_shows_nothing(tmp_path: Path) -> None:
    assert "[5h:" not in _plain(tmp_path, {}, CONFIG_A, tmp_path)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file modes")
def test_unreadable_file_shows_nothing(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": 62})
    cap.chmod(0)
    try:
        out = _plain(tmp_path, {}, CONFIG_A, cap)
    finally:
        cap.chmod(0o600)
    assert "[5h:" not in out
    assert "[acct: A]" in out


def test_malformed_lines_are_skipped_and_earlier_good_row_still_used(tmp_path: Path) -> None:
    cap = _rows(
        tmp_path / "cap.jsonl",
        {"account": "a", "five_hour_left_pct": 62, "seven_day_left_pct": 35},
        "{not json",
        "[1, 2, 3]",
        '"a string"',
        "42",
        "null",
        "",
        '{"account": "a", "five_hour_left_pct": ',
    )
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h: 62% left]" in out
    assert "[7d: 35% left]" in out


def test_file_of_only_garbage_shows_nothing_and_no_error(tmp_path: Path) -> None:
    cap = tmp_path / "cap.jsonl"
    cap.write_bytes(b"\xff\xfe\x00garbage\n{\n}}}\n")
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h:" not in out
    assert "[7d:" not in out
    assert out.startswith("[Opus] [acct: A] ")


@pytest.mark.parametrize("bad", ["50", "abc", None, True, [], {}, -1, 101, 100.5, -0.1])
def test_non_numeric_or_out_of_range_values_show_nothing(tmp_path: Path, bad: object) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": bad, "seven_day_left_pct": bad})
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h:" not in out
    assert "[7d:" not in out


@pytest.mark.parametrize(("value", "shown"), [(0, 0), (100, 100), (59.6, 60), (0.4, 0)])
def test_boundary_values_are_shown_rounded(tmp_path: Path, value: float, shown: int) -> None:
    cap = _rows(tmp_path / "cap.jsonl", {"account": "a", "five_hour_left_pct": value})
    assert f"[5h: {shown}% left]" in _plain(tmp_path, {}, CONFIG_A, cap)


def test_bad_value_in_last_row_is_not_replaced_by_older_row(tmp_path: Path) -> None:
    cap = _rows(
        tmp_path / "cap.jsonl",
        {"account": "a", "five_hour_left_pct": 80, "seven_day_left_pct": 81},
        {"account": "a", "five_hour_left_pct": "x", "seven_day_left_pct": 40},
    )
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h:" not in out
    assert "[7d: 40% left]" in out


def test_non_object_account_values_do_not_match(tmp_path: Path) -> None:
    cap = _rows(
        tmp_path / "cap.jsonl",
        {"account": 1, "five_hour_left_pct": 10},
        {"account": ["a"], "five_hour_left_pct": 20},
        {"five_hour_left_pct": 30},
        {"account": "claude:", "five_hour_left_pct": 40},
    )
    assert "[5h:" not in _plain(tmp_path, {}, CONFIG_A, cap)


def test_huge_file_is_read_by_tail_only(tmp_path: Path) -> None:
    """A matching row beyond the last 64 KiB is invisible; the tail row is used."""
    cap = tmp_path / "cap.jsonl"
    filler = json.dumps({"account": "b", "five_hour_left_pct": 1, "note": "x" * 900}) + "\n"
    with cap.open("w") as handle:
        handle.write(json.dumps({"account": "a", "five_hour_left_pct": 99, "seven_day_left_pct": 98}) + "\n")
        handle.write(filler * (3 * 1024 * 1024 // len(filler)))
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h:" not in out
    assert "[7d:" not in out

    with cap.open("a") as handle:
        handle.write(json.dumps({"account": "a", "five_hour_left_pct": 45, "seven_day_left_pct": 46}) + "\n")
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "[5h: 45% left]" in out
    assert "[7d: 46% left]" in out


def test_row_cut_by_tail_window_is_not_misread(tmp_path: Path) -> None:
    cap = tmp_path / "cap.jsonl"
    long_row = json.dumps({"account": "a", "five_hour_left_pct": 77, "note": "y" * 70_000})
    cap.write_text(long_row + "\n")
    assert "[5h:" not in _plain(tmp_path, {}, CONFIG_A, cap)


def test_capacity_path_is_never_printed(tmp_path: Path) -> None:
    cap = _rows(tmp_path / "secret-capacity-dir-cap.jsonl", {"account": "a", "five_hour_left_pct": 62})
    out = _plain(tmp_path, {}, CONFIG_A, cap)
    assert "secret-capacity-dir" not in out
