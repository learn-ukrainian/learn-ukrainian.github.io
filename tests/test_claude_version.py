"""Unit tests for scripts/utils/claude_version.py — version gate helper.

Covers:
- Semver parsing edge cases (bare, noisy output, v-prefix, invalid)
- Support detection (true, false old version, false on exception)
- Cache behavior (scoped by prefix, hits on repeat)

Issue: #1179
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from utils.claude_version import (
    _parse_claude_semver,
    _reset_cache_for_tests,
    supports_exclude_dynamic_system_prompt_sections,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset the per-prefix cache before every test to prevent cross-test leaks."""
    _reset_cache_for_tests()
    yield
    _reset_cache_for_tests()


# ---------------------------------------------------------------------------
# _parse_claude_semver — pure function, no subprocess
# ---------------------------------------------------------------------------

def test_parse_semver_basic():
    """Bare 'X.Y.Z' string parses."""
    assert _parse_claude_semver("2.1.98") == (2, 1, 98)


def test_parse_semver_with_noise():
    """Version surrounded by parenthetical noise still parses."""
    assert _parse_claude_semver("2.1.98 (Claude Code)") == (2, 1, 98)
    assert _parse_claude_semver("Claude Code v2.1.98 (build abc123)") == (2, 1, 98)


def test_parse_semver_v_prefix():
    """Leading 'v' is stripped."""
    assert _parse_claude_semver("v2.1.98") == (2, 1, 98)


def test_parse_semver_invalid():
    """Unparsable input returns None, not a crash."""
    assert _parse_claude_semver("") is None
    assert _parse_claude_semver("not a version") is None
    assert _parse_claude_semver("1.2") is None  # too few parts
    assert _parse_claude_semver("abc.def.ghi") is None


def test_parse_semver_rejects_four_part_version():
    """Four-part versions like '2.1.98.1' must NOT match as (2,1,98) — the
    regex enforces word boundaries so 1.2.3.4 is not a valid 3-part semver.
    This prevents ambiguous parses."""
    assert _parse_claude_semver("2.1.98.1") is None


def test_parse_semver_rejects_ip_address():
    """IP address '192.168.1.1' must not be parsed as version (1,1,1)
    or anything else. Four segments — regex rejects."""
    assert _parse_claude_semver("host: 192.168.1.1") is None


def test_parse_semver_skips_npm_notice():
    """Gemini finding #2: npm update notices must NOT fool the parser.

    The line 'npm notice New minor version of npm available! 10.2.4 -> 10.8.1'
    contains valid-looking semvers but is not the Claude Code version.
    """
    noisy = (
        "npm notice New minor version of npm available! 10.2.4 -> 10.8.1\n"
        "2.1.98 (Claude Code)\n"
    )
    assert _parse_claude_semver(noisy) == (2, 1, 98)


def test_parse_semver_skips_arrow_lines():
    """Lines containing '->' (version-bump arrows) are treated as noise."""
    assert _parse_claude_semver("3.0.0 -> 4.0.0") is None


def test_parse_semver_only_noise_returns_none():
    """If every line is noise, return None."""
    noisy = (
        "npm notice New version 10.2.4 -> 10.8.1\n"
        "npm warn deprecated foo@1.0.0\n"
    )
    assert _parse_claude_semver(noisy) is None


def test_parse_semver_empty_input():
    """Empty / whitespace-only input returns None safely."""
    assert _parse_claude_semver("") is None
    assert _parse_claude_semver("   \n  \n") is None


# ---------------------------------------------------------------------------
# Gemini finding #1: combine stdout + stderr explicitly
# ---------------------------------------------------------------------------

def test_supports_reads_stderr_when_stdout_is_just_newline():
    """Gemini finding #1: if stdout is '\\n' (truthy but blank), we must
    still check stderr. Previous implementation with 'result.stdout or
    result.stderr' would short-circuit because '\\n' is truthy.
    """
    with patch(
        "utils.claude_version.subprocess.run",
        return_value=_mock_run(stdout="\n", stderr="2.1.98"),
    ):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is True


# ---------------------------------------------------------------------------
# Gemini finding #3: bare string defensive handling
# ---------------------------------------------------------------------------

def test_supports_handles_bare_string_prefix():
    """Gemini finding #3: passing a bare string 'claude' instead of ['claude']
    must NOT unpack into individual characters and try to exec binary 'c'.
    """
    with patch(
        "utils.claude_version.subprocess.run",
        return_value=_mock_run(stdout="2.1.98"),
    ) as mock:
        result = supports_exclude_dynamic_system_prompt_sections("claude")
        assert result is True
        # Verify subprocess was called with ["claude", "--version"] not
        # ["c", "l", "a", "u", "d", "e", "--version"]
        call_args = mock.call_args[0][0]
        assert call_args[0] == "claude"
        assert call_args[-1] == "--version"
        assert len(call_args) == 2


# ---------------------------------------------------------------------------
# Gemini residual risk: no caching of transient failures
# ---------------------------------------------------------------------------

def test_timeout_failure_not_cached():
    """Gemini residual: TimeoutExpired must NOT be cached permanently.

    A slow npx probe on first call should not disable the optimization
    for the lifetime of the process. A later call should be able to retry.
    """
    timeout_mock = MagicMock(side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5))
    with patch("utils.claude_version.subprocess.run", timeout_mock):
        result1 = supports_exclude_dynamic_system_prompt_sections(["claude"])
        assert result1 is False

    # Now the network is back. A retry should re-probe, not return the
    # cached False from the timeout.
    success_mock = MagicMock(return_value=_mock_run(stdout="2.1.98"))
    with patch("utils.claude_version.subprocess.run", success_mock):
        result2 = supports_exclude_dynamic_system_prompt_sections(["claude"])
        assert result2 is True, "timeout should not poison cache permanently"
        assert success_mock.call_count == 1


def test_file_not_found_is_cached():
    """FileNotFoundError (binary genuinely missing) IS a definitive outcome
    and should be cached to avoid re-probing repeatedly."""
    missing_mock = MagicMock(side_effect=FileNotFoundError("claude not found"))
    with patch("utils.claude_version.subprocess.run", missing_mock):
        supports_exclude_dynamic_system_prompt_sections(["claude"])
        supports_exclude_dynamic_system_prompt_sections(["claude"])
    assert missing_mock.call_count == 1, "FileNotFoundError should be cached"


# ---------------------------------------------------------------------------
# supports_exclude_dynamic_system_prompt_sections — subprocess-backed
# ---------------------------------------------------------------------------

def _mock_run(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Build a MagicMock that mimics subprocess.CompletedProcess."""
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


def test_supports_true_on_minimum_version():
    """Exactly 2.1.98 returns True."""
    with patch("utils.claude_version.subprocess.run", return_value=_mock_run(stdout="2.1.98")):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is True


def test_supports_true_on_newer_version():
    """Versions > 2.1.98 return True."""
    with patch("utils.claude_version.subprocess.run", return_value=_mock_run(stdout="2.2.0 (Claude Code)")):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is True


def test_supports_false_old_version():
    """Versions < 2.1.98 return False (no flag appended)."""
    with patch("utils.claude_version.subprocess.run", return_value=_mock_run(stdout="2.1.97")):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is False


def test_supports_false_exception():
    """Any exception from subprocess.run falls back to False safely."""
    with patch("utils.claude_version.subprocess.run", side_effect=FileNotFoundError("claude not found")):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is False


def test_supports_false_timeout():
    """Subprocess timeout falls back to False."""
    with patch(
        "utils.claude_version.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5),
    ):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is False


def test_supports_false_unparsable_output():
    """Version output that can't be parsed falls back to False."""
    with patch("utils.claude_version.subprocess.run", return_value=_mock_run(stdout="garbage output")):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is False


def test_supports_reads_stderr_when_stdout_empty():
    """Some CLIs print version to stderr; parser checks both."""
    with patch("utils.claude_version.subprocess.run", return_value=_mock_run(stdout="", stderr="2.1.98")):
        assert supports_exclude_dynamic_system_prompt_sections(["claude"]) is True


# ---------------------------------------------------------------------------
# Cache behavior
# ---------------------------------------------------------------------------

def test_cache_hits_on_repeat():
    """Second call with same prefix does NOT re-invoke subprocess.run."""
    mock = MagicMock(return_value=_mock_run(stdout="2.1.98"))
    with patch("utils.claude_version.subprocess.run", mock):
        supports_exclude_dynamic_system_prompt_sections(["claude"])
        supports_exclude_dynamic_system_prompt_sections(["claude"])
        supports_exclude_dynamic_system_prompt_sections(["claude"])
    assert mock.call_count == 1, "cache should have prevented duplicate probes"


def test_cache_scoped_by_prefix():
    """Different prefixes get independent cache entries — each probed once."""
    mock = MagicMock(return_value=_mock_run(stdout="2.1.98"))
    with patch("utils.claude_version.subprocess.run", mock):
        supports_exclude_dynamic_system_prompt_sections(["claude"])
        supports_exclude_dynamic_system_prompt_sections(["npx", "@anthropic-ai/claude-code@latest"])
        supports_exclude_dynamic_system_prompt_sections(["/usr/local/bin/claude"])
    assert mock.call_count == 3, "each unique prefix should be probed exactly once"


def test_cache_tuple_equality():
    """A list and a tuple with the same contents hit the same cache entry."""
    mock = MagicMock(return_value=_mock_run(stdout="2.1.98"))
    with patch("utils.claude_version.subprocess.run", mock):
        supports_exclude_dynamic_system_prompt_sections(["claude"])
        supports_exclude_dynamic_system_prompt_sections(("claude",))  # same entries, tuple form
    assert mock.call_count == 1, "list and tuple with same contents should share cache entry"


def test_reset_cache_clears_all_entries():
    """_reset_cache_for_tests actually clears the cache (used by autouse fixture)."""
    mock = MagicMock(return_value=_mock_run(stdout="2.1.98"))
    with patch("utils.claude_version.subprocess.run", mock):
        supports_exclude_dynamic_system_prompt_sections(["claude"])
        _reset_cache_for_tests()
        supports_exclude_dynamic_system_prompt_sections(["claude"])
    assert mock.call_count == 2, "reset should force a re-probe"
