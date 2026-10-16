"""Claude route-key accounts for tests (#10630).

Production builds a :class:`ClaudeAccount` only in ``scripts.fleet.claude_account_lane``
(``resolve_route_account``, ``account_from_record``, ``no_claude_account``). Tests that call a
routing or admission function directly name the account the same way a dispatch would.
"""

from __future__ import annotations

from scripts.fleet.claude_account_lane import UNRESOLVED_SOURCE, ClaudeAccount

# What a dispatch without a default-account file resolves: the built-in default, which reads the lane row.
HOST_ACCOUNT = ClaudeAccount("a", "builtin")


def account(label: str, source: str = "explicit") -> ClaudeAccount:
    """A resolved account, as ``resolve_route_account`` returns it after binding."""
    return ClaudeAccount(label, source)


def unresolved(code: str) -> ClaudeAccount:
    """An account that could not be resolved or bound, with its refusal code."""
    return ClaudeAccount(None, UNRESOLVED_SOURCE, code)
