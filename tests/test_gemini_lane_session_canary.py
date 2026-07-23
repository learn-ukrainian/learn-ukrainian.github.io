"""Regression coverage for the Gemini session-canary command parser."""

from __future__ import annotations

import pytest

from scripts.session_canary import gemini_lane


@pytest.mark.parametrize("subcommand", ["mint", "bootstrap", "protocol", "status"])
def test_subcommands_accept_missing_stream_argument(
    subcommand: str,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Commands without ``--stream`` must not access a missing Namespace attribute."""
    monkeypatch.setattr(gemini_lane, "ROOT", tmp_path)

    assert gemini_lane.main([subcommand, "--epic", "harness"]) == 0
