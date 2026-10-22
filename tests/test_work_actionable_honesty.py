"""Static + behavioral contracts for #7084 Work dashboard actionable view honesty.

Ensures the default view=actionable explains filtered-out non-actionable items
(such as ON_TRACK + OPEN_GITHUB issues) and provides a link to view=all without
modifying the #6850 isActionable deny-list semantics.
"""

from __future__ import annotations


def test_server_ssot_deny_list_preserves_open_github():
    """#6850 deny-list still includes OPEN_GITHUB and maintains expected truth table."""
    from scripts.work.attention import NON_ACTIONABLE_ACTION_CODES, is_actionable

    assert "OPEN_GITHUB" in NON_ACTIONABLE_ACTION_CODES
    assert "INSPECT_UNKNOWN" in NON_ACTIONABLE_ACTION_CODES
    assert "NONE" in NON_ACTIONABLE_ACTION_CODES

    # ON_TRACK + OPEN_GITHUB remains non-actionable (must not be pick-list work)
    assert not is_actionable({"health": "ON_TRACK", "safe_next_action": {"code": "OPEN_GITHUB"}})
    # UNKNOWN + OPEN_GITHUB is non-actionable
    assert not is_actionable({"health": "UNKNOWN", "safe_next_action": {"code": "OPEN_GITHUB"}})
    # AT_RISK or OFF_TRACK demands attention regardless of action code
    assert is_actionable({"health": "AT_RISK", "safe_next_action": {"code": "OPEN_GITHUB"}})
    assert is_actionable({"health": "OFF_TRACK", "safe_next_action": {"code": "OPEN_GITHUB"}})
    assert is_actionable({"health": "OFF_TRACK", "safe_next_action": {"code": "NONE"}})
