"""Claude route-key accounts for tests (#10630).

Held A3 subjects require their own :class:`ClaudeAccount` identity until they migrate.
Tests that call a routing or admission function directly name the account the same way a
dispatch would. A test that hands a raw routing-budget fixture straight to a decision helper
binds it first
(:func:`bound`), as the helper's production boundary does (#10770).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scripts.fleet.claude_account_lane import (  # TRANSITIONAL-PKG3-B2: A3 subjects require these exact types.
    UNRESOLVED_SOURCE,
    AccountSnapshot,
    ClaudeAccount,
    bind_snapshot,
)

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
