"""#9878: every reason that can leave the machine goes through one sink and names a registered cause.

The task record's reason fields, the rescue and refusal rows and the lines
that print them accept only a cause from the closed registry
(``delegate.public_causes``) with fixed parameters. Anything else is replaced
at the sink and its text kept in the task's local diagnostic file, which is
opened without following symlinks, created 0600 and bounded.
"""

from __future__ import annotations

import json
import re

import pytest

# A credential-shaped synthetic token: it must never reach a public reason.
_FAKE_TOKEN = "ghp_" + "Z9yX8wV7uT6sR5qP4oN3mL2kJ1iH0gF9eD8c"

# An IPv6 link-local literal (``fe80`` then colon-separated hex groups, e.g. ``fe80::1``). The bare four letters are
# no marker: a 40-hex commit SHA such as ``...ebfe8007cb`` carries them, and a SHA never carries a colon, so the
# letters count only when no hex digit precedes them. An escape sequence is never part of a hex run, yet its tail is
# often a hex digit (``\b \f \0 \x01 \u00a0``): it would hide a literal right behind it. So every escape sequence is
# first replaced by a space, which exposes the real neighbour character. The escapes differ in how many backslashes
# spell them: one in the escaped text itself (or a ``repr()``), two once ``json.dumps`` has serialized that, four after a
# second serialization; each count is read, and a plain text with no escapes is read as well.
_LINK_LOCAL_AFTER_NON_HEX = re.compile(r"(?<![0-9a-f])fe80(?::[0-9a-f]{0,4}){2,}", re.IGNORECASE)
_BACKSLASH_COUNTS = (0, 1, 2, 4)


def _without_escape_sequences(text: str, backslashes: int) -> str:
    """``text`` with each escape sequence spelled with ``backslashes`` backslashes replaced by one space."""
    if not backslashes:
        return text
    slashes = "\\\\" * backslashes  # the regex for that many literal backslashes
    escape = re.compile(slashes + r"(?:u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|x[0-9a-fA-F]{2}|[bfnrtv0a\"'/]|" + slashes + ")")
    return escape.sub(" ", text)  # left to right: an escaped backslash pair is consumed as one unit


def contains_link_local_ipv6(text: str) -> bool:
    """Whether ``text`` holds an IPv6 link-local literal, also behind a (repeatedly serialized) escape sequence."""
    return any(_LINK_LOCAL_AFTER_NON_HEX.search(_without_escape_sequences(text, count)) for count in _BACKSLASH_COUNTS)


# Characters whose escape ends in a hex digit (``\b \f \0``, ``\x01 \x1f \xa0``, ``\uXXXX``, ``\UXXXXXXXX``), as ``json.dumps``
# and ``repr()`` write them.
JSON_ESCAPED_CHARS = (
    "\b", "\f", "\n", "\r", "\t", "\v", "\0", "\x01", "\x1f", "\u00a0", "\u2028", "\u200b", "\u00ad", "\U000e0001",
)  # fmt: skip
# The same escapes as text, as they sit in a serialized record.
ESCAPE_SEQUENCES = (
    r"\b", r"\f", r"\n", r"\r", r"\t", r"\v", r"\0", r"\x01", r"\x1f", r"\xa0",
    r"\u0001", r"\u00a0", r"\u2028", r"\u200b", r"\U000e0001",
)  # fmt: skip
_LINK_LOCAL_LETTERS = "fe" + "80"  # fragments: no whole link-local literal appears in this file


def _serializations(value: str) -> list[str]:
    """``value`` as a serialized record holds it: ``repr()``, ``json.dumps`` and both, each also serialized twice."""
    return [
        repr(value),
        json.dumps(value),
        json.dumps(repr(value)),
        json.dumps(json.dumps(value)),
        json.dumps(json.dumps(repr(value))),
    ]


def _behind_escapes(payload: str) -> list[str]:
    """Serialized texts with ``payload`` right behind each escape of ``JSON_ESCAPED_CHARS`` / ``ESCAPE_SEQUENCES``."""
    texts = [form for char in JSON_ESCAPED_CHARS for form in _serializations(char + payload)]
    for sequence in ESCAPE_SEQUENCES:
        texts += [sequence + payload, json.dumps(sequence + payload), json.dumps(json.dumps(sequence + payload))]
    return texts


def link_local_after_json_escapes() -> list[str]:
    """Serialized text with a link-local literal right behind each escape."""
    return _behind_escapes(_LINK_LOCAL_LETTERS + "::1")


def shas_after_json_escapes() -> list[str]:
    """Serialized text with a 40-hex SHA, holding the link-local letters at every offset, right behind each escape."""
    texts = []
    for offset in range(0, 37):
        filler = "0123456789abcdef" * 3
        sha = (filler[:offset] + _LINK_LOCAL_LETTERS + filler)[:40]
        assert len(sha) == 40 and _LINK_LOCAL_LETTERS in sha
        texts += _behind_escapes(sha) + _behind_escapes(f"sha:{sha.upper()}")
    return texts


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
