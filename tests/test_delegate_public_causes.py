"""#9878: every reason that can leave the machine goes through one sink and names a registered cause.

The task record's reason fields, the rescue and refusal rows and the lines
that print them accept only a cause from the closed registry
(``delegate.public_causes``) with fixed parameters. Anything else is replaced
at the sink and its text kept in the task's local diagnostic file, which is
opened without following symlinks, created 0600 and bounded.
"""

from __future__ import annotations

import json

import pytest

from tests.test_kimi_coding_only_admission import (
    _FAKE_TOKEN,
    ESCAPE_SEQUENCES,
    JSON_ESCAPED_CHARS,
    contains_link_local_ipv6,
    link_local_after_json_escapes,
    shas_after_json_escapes,
)

# A host name, a private path and two address-like tokens, with a credential, in one error.
HOSTILE_MARKERS = ("build-host", "example.internal", "/srv/", "synthetic-operator", "203.0.113.77", "eth7")
# The public reason fields and row keys this contract names, enumerated here rather than read from the module.


def _assert_no_hostile_markers(public: str) -> None:
    """``public`` holds no hostile marker, no credential and no IPv6 link-local literal."""
    for marker in (*HOSTILE_MARKERS, _FAKE_TOKEN):
        assert marker not in public, marker
    assert not contains_link_local_ipv6(public), "IPv6 link-local literal"


def test_a_commit_sha_holding_the_link_local_letters_is_no_host_detail():
    sha = "426cf32d8175a73823c18d63ca4107ebfe8007cb"
    assert "fe80" in sha
    _assert_no_hostile_markers(json.dumps({"head": sha}))


def test_the_hostile_link_local_literal_still_fails_the_public_guard():
    with pytest.raises(AssertionError, match="link-local"):
        _assert_no_hostile_markers(json.dumps({"last_error": "via [fe80::1ff:fe23:4567:890a]"}))
    with pytest.raises(AssertionError, match="link-local"):
        _assert_no_hostile_markers("via fe80::1")


@pytest.mark.parametrize("text", link_local_after_json_escapes())
def test_a_link_local_literal_behind_an_escape_still_fails_the_public_guard(text):
    with pytest.raises(AssertionError, match="link-local"):
        _assert_no_hostile_markers(text)


def test_a_commit_sha_behind_an_escape_passes_the_public_guard():
    texts = shas_after_json_escapes()
    assert len(texts) == 37 * 2 * (len(JSON_ESCAPED_CHARS) * 5 + len(ESCAPE_SEQUENCES) * 3)
    for text in texts:
        _assert_no_hostile_markers(text)


# --- the registry and the sink -------------------------------------------------------------------


# --- no record write bypasses the sink -----------------------------------------------------------


# The dead-worker markers persist the record themselves unless handed a writer.


# --- the producers the review named: injected host details never reach a public field ------------


# --- the local diagnostic file -------------------------------------------------------------------
