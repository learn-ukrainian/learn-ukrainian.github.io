"""#9125: real target diffs reach the production parser and admission entry point."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from tests.claude_route_accounts import HOST_ACCOUNT
from tests.helpers.review_scope import ordinary_review_scope as ordinary_review_scope


@pytest.mark.parametrize("as_request", [False, True])
def test_uninjected_routing_snapshot_fails_before_network(as_request):
    url = "https://example.invalid/api/state/routing-budget?fresh_codexbar=true"
    request = urllib.request.Request(url) if as_request else url
    with pytest.raises(pytest.fail.Exception, match="live reviewer routing snapshot read: inject a fixed snapshot"):
        urllib.request.urlopen(request, timeout=1)


def test_admission_does_not_call_a_ukrainian_path_collector():
    from scripts.agent_runtime.target_admission import resolve_and_admit

    def unexpected_paths():
        raise AssertionError("Ukrainian admission must not read code/infra scope")

    (target,) = resolve_and_admit(
        ("claude",),
        model="claude-sonnet-5-5",
        mode="read-only",
        review_dispatch=True,
        review_profile="ukrainian",
        review_attempt=True,
        review_changed_paths=unexpected_paths,
        claude_account=HOST_ACCOUNT,
    )
    assert (target.recipient, target.model) == ("claude", "claude-sonnet-5-5")
