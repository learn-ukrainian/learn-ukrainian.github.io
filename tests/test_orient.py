"""Small acceptance-path checks for the #4728 orient section."""

from __future__ import annotations

import scripts.api.main as api_main


def test_idle_prs_are_full_orient_only_by_default():
    assert "idle_prs" in api_main.ORIENT_SECTION_KEYS
    assert "idle_prs" not in api_main.LEAN_ORIENT_SECTIONS
    assert api_main._parse_orient_sections(None, lean=False)[0:3] == ["git", "issues", "idle_prs"]
