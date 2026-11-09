"""Claude route-key accounts for tests (#10630).

Production builds a :class:`ClaudeAccount` only in ``scripts.fleet.claude_account_lane``
(``resolve_route_account``, ``account_from_record``, ``no_claude_account``). Tests that call a
routing or admission function directly name the account the same way a dispatch would, and a
test that hands a raw routing-budget fixture straight to a decision helper binds it first
(:func:`bound`), as the helper's production boundary does (#10770).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scripts.fleet.claude_account_lane import UNRESOLVED_SOURCE, AccountSnapshot, ClaudeAccount, bind_snapshot

# What a dispatch without a default-account file resolves: the built-in default, which reads the lane row.
HOST_ACCOUNT = ClaudeAccount("a", "builtin")


def account(label: str, source: str = "explicit") -> ClaudeAccount:
    """A resolved account, as ``resolve_route_account`` returns it after binding."""
    return ClaudeAccount(label, source)


def unresolved(code: str) -> ClaudeAccount:
    """An account that could not be resolved or bound, with its refusal code."""
    return ClaudeAccount(None, UNRESOLVED_SOURCE, code)


def bound(payload: Mapping[str, Any], account: ClaudeAccount = HOST_ACCOUNT) -> AccountSnapshot:
    """``payload`` bound to ``account`` (the host's default account unless named)."""
    return bind_snapshot(payload, account=account)
