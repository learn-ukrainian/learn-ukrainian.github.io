"""URL credentials and ordinary-text compatibility for #9948.

Every credential-shaped fixture is assembled from parts at runtime. Corpus
inputs are public working-tree documents and frozen synthetic messages, never
stored message bodies. No reference implementation or Git history is needed.
"""

import subprocess
from pathlib import Path

import pytest

from scripts.secret_redactor import REDACTION, iter_url_matches, redact_text, redact_url_authority, redact_value

PASSWORDS = (
    "Ab3dE/fG",
    "Ab3dE+fG",
    "Ab3dE=fG",
    "Ab3dE?fG",
    "Ab3dE#fG",
    "Ab3dE%2FfG%2B%3D%3F%23",
    "Ab3dE/fG+h9=?tail#end",
    "12345",
    "Alpha!Beta$",
    "first:second",
)


def credential_url(password, *, username="u", host="host.invalid:443", suffix="/api?part=2#tail", scheme="https"):
    return "".join((scheme, "://", username, ":", password, "@", host, suffix))


@pytest.mark.parametrize("password", PASSWORDS)
@pytest.mark.parametrize("username", ["u", "", "bot%2Dname"])
@pytest.mark.parametrize("host", ["host.invalid:443", "[2001:db8::7]:443"])
def test_url_password_characters_are_redacted_without_normalizing_bytes(password, username, host):
    raw = credential_url(password, username=username, host=host)
    expected = credential_url(REDACTION, username=username, host=host)
    assert redact_text(raw) == expected
    assert "".join(redact_url_authority(raw)) == expected
    assert redact_text(expected) == expected
    assert password not in expected


SAFE_URLS = (
    "http://localhost:5173/@vite/client",
    "http://localhost:4873/@scope/pkg",
    "https://example.invalid:443/@user/post",
    "https://example.invalid:443/a/b?email=user@other.invalid#tail",
    "https://example.invalid:443?email=user@other.invalid",
    "https://example.invalid:443#user@other.invalid",
    "https://example.invalid:/@scope/pkg",
    "https://example.invalid:?email=user@other.invalid",
    "https://example.invalid/path?email=user@other.invalid",
    "https://example.invalid?next=http://other.invalid/a@b",
    "".join(("https://example.invalid/#", "u:", "p", "@", "other.invalid")),
    "https://[2001:db8::7]:443/@scope/pkg?email=user@other.invalid",
    "file:///root/@scope/pkg",
    "https://example.invalid/%2f/@user/post?part=%2B+&next=%2Ffixture#tail",
)


@pytest.mark.parametrize("raw", SAFE_URLS)
def test_path_query_and_fragment_at_signs_are_not_userinfo(raw):
    assert redact_text(raw) == raw
    assert "".join(redact_url_authority(raw)) == raw


@pytest.mark.parametrize("delimiter", ["/", "?", "#"])
@pytest.mark.parametrize("prefix", ["12345", ""])
def test_ambiguous_numeric_or_empty_password_prefix_stays_a_port(delimiter, prefix):
    raw = credential_url(prefix + delimiter + "tail")
    assert redact_text(raw) == raw


@pytest.mark.parametrize("delimiter", ["/", "?", "#"])
def test_malformed_fallback_cannot_cross_whitespace_or_text_delimiters(delimiter):
    raw = "".join(("https", "://", "u:", "canary", delimiter, "tail"))
    for boundary in (" ", "\n", "\t", '"', "<", ">", "`"):
        text = raw + boundary + "user@host.invalid"
        assert redact_text(text) == text


def test_username_only_and_schemeless_userinfo_stay_unchanged():
    username_only = "".join(("ssh", "://", "git", "@", "host.invalid/repo"))
    schemeless = "".join(("u:", "canary", "@", "host.invalid"))
    assert redact_text(username_only) == username_only
    assert redact_text(schemeless) == schemeless


def test_multiple_urls_and_nested_values_redact_only_password_bytes():
    first = credential_url("canary?one")
    second = credential_url("canary/two", scheme="postgres")
    raw = "before " + first + " and " + SAFE_URLS[0] + " then " + second + " after"
    expected = "before " + credential_url(REDACTION) + " and " + SAFE_URLS[0]
    expected += " then " + credential_url(REDACTION, scheme="postgres") + " after"
    assert redact_text(raw) == expected
    assert redact_value({"body": [raw, (first,)], "attempt": 3}) == {
        "body": [expected, (credential_url(REDACTION),)], "attempt": 3,
    }


@pytest.mark.parametrize("delimiter", [":", "/", "?", "#", ",", ";"])
@pytest.mark.parametrize("username", ["u", "", "bot%2Dname"])
@pytest.mark.parametrize("joiner", [",", ";", "?next=", "/archive/", "#next="])
def test_embedded_scheme_cannot_split_an_unclosed_password(delimiter, username, joiner):
    left, right = "beforeCanary", "afterCanary"
    password = "".join((left, delimiter, "https", "://", right))
    first = credential_url(password, username=username)
    second = credential_url("nextCanary", scheme="postgres")
    expected = credential_url(REDACTION, username=username) + joiner + credential_url(REDACTION, scheme="postgres")
    raw = first + joiner + second
    redacted = redact_text(raw)
    assert redacted == expected
    assert left not in redacted and right not in redacted and "nextCanary" not in redacted
    assert redact_text(redacted) == redacted
    assert redact_value({"body": [raw]}) == {"body": [expected]}


@pytest.mark.parametrize("password", [
    "".join(("https", "://", "afterCanary")),
    "".join(("beforeCanary/https", "://", "nested/path?tail#afterCanary")),
    "".join(("beforeCanary?https", "://", "nested;postgres", "://", "afterCanary")),
    *("".join(("12345", delimiter, "https", "://", "afterCanary")) for delimiter in (",", ";")),
])
def test_entire_embedded_url_remains_password_until_userinfo_closes(password):
    raw = credential_url(password)
    expected = credential_url(REDACTION)
    assert redact_text(raw) == expected
    assert redact_text(expected) == expected


@pytest.mark.parametrize("prefix", ["12345", ""])
@pytest.mark.parametrize("joiner", [",", ";", "?next=", "/archive/", "#next="])
def test_nested_url_does_not_turn_numeric_or_empty_port_into_userinfo(prefix, joiner):
    outer = "".join(("https://outer.invalid:", prefix, "/api", joiner))
    raw = outer + credential_url("nextCanary")
    expected = outer + credential_url(REDACTION)
    assert redact_text(raw) == expected
    assert redact_text(expected) == expected


@pytest.mark.parametrize("password", PASSWORDS)
@pytest.mark.parametrize("joiner", [",", ";", "?next=", "/archive/", "#next="])
@pytest.mark.parametrize("suffix", ["", "/api"])
def test_every_url_in_one_token_redacts_its_own_password(password, joiner, suffix):
    first = credential_url(password, host="first.invalid:443", suffix=suffix)
    second = credential_url(password, username="", host="[2001:db8::7]:443", suffix=suffix, scheme="postgres")
    third = credential_url(password, username="bot%2Dname", host="third.invalid", suffix=suffix)
    expected = joiner.join((
        credential_url(REDACTION, host="first.invalid:443", suffix=suffix),
        credential_url(REDACTION, username="", host="[2001:db8::7]:443", suffix=suffix, scheme="postgres"),
        credential_url(REDACTION, username="bot%2Dname", host="third.invalid", suffix=suffix),
    ))
    raw = joiner.join((first, second, third))
    assert redact_text(raw) == expected
    assert redact_text(expected) == expected
    assert redact_value({"body": [raw]}) == {"body": [expected]}


@pytest.mark.parametrize("password", PASSWORDS)
@pytest.mark.parametrize("outer", [
    "https://outer.invalid/redirect?next=",
    "https://archive.invalid/20261007/",
    "https://outer.invalid:443/@scope/pkg?next=",
    "https://",
])
def test_credentialless_outer_url_does_not_hide_inner_credentials(password, outer):
    raw = outer + credential_url(password)
    expected = outer + credential_url(REDACTION)
    assert redact_text(raw) == expected
    assert redact_text(expected) == expected


@pytest.mark.parametrize("raw", [
    "https://archive.invalid/20261007/https://source.invalid/path",
    "https://outer.invalid?next=https://source.invalid:443/@scope/pkg",
    "https://first.invalid,https://second.invalid;file:///root/@scope/pkg",
])
def test_credentialless_nested_and_joined_urls_stay_byte_identical(raw):
    assert redact_text(raw) == raw


def test_nonnumeric_colon_prefix_uses_round_a_fallback_across_nested_scheme():
    # This invalid port also has the round-a shape of malformed userinfo.
    raw = "".join(("https://outer.invalid:", "opaque/path?next=https://source.invalid/a", "@", "b"))
    expected = "".join(("https://outer.invalid:", REDACTION, "@", "b"))
    assert redact_text(raw) == expected
    assert "".join(redact_url_authority(raw)) == expected
    assert redact_text(expected) == expected


FROZEN_NEGATIVES = (
    *SAFE_URLS,
    "Review complete; the tests passed. Please read scripts/api/lane_health.py.",
    "Budget ~500K/1M, fraction ~2/3; codes ENOTFOUND EAI_AGAIN.",
    "Retry GET " + SAFE_URLS[0] + " 404; next " + SAFE_URLS[1],
    "token_verdicts = vesum_gate.check_tokens(sentence)",
    "https://archive.invalid/20261007/https://source.invalid/path",
    "https://outer.invalid?next=https://source.invalid:443/@scope/pkg",
    "https://first.invalid,https://second.invalid;file:///root/@scope/pkg",
    "https://archive.invalid/20261007/https://source.invalid:443/@scope/pkg",
    "https://outer.invalid:443/@scope/pkg?next=https://source.invalid/a@b#user@other.invalid",
    "https://outer.invalid/redirect?next=https://source.invalid/path?email=user@other.invalid",
)


def url_pass(text):
    """Apply just the production URL iterator and authority redaction pass."""
    parts = []
    cursor = 0
    for match in iter_url_matches(text):
        parts.append(text[cursor:match.start()])
        parts.extend(redact_url_authority(match.group()))
        cursor = match.end()
    parts.append(text[cursor:])
    return "".join(parts)


@pytest.mark.parametrize("raw", FROZEN_NEGATIVES)
def test_frozen_ordinary_messages_stay_byte_identical(raw):
    assert url_pass(raw).encode("utf-8") == raw.encode("utf-8")
    assert redact_text(raw).encode("utf-8") == raw.encode("utf-8")


@pytest.mark.repo_wide
def test_ordinary_repository_corpus_is_unchanged_by_url_pass():
    repo = Path(__file__).resolve().parents[1]
    # The local index supplies names only; all bytes come from the working tree.
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "docs", "agents_extensions/shared/rules", "AGENTS.md", "CLAUDE.md", "GEMINI.md"],
        cwd=repo,
        timeout=30,
    ).decode("utf-8").split("\0")
    documents = [name for name in tracked if name.endswith((".md", ".mdx", ".yaml", ".yml", ".txt", ".html"))]
    assert len(documents) >= 100
    for name in documents:
        original = (repo / name).read_bytes()
        # Stronger than filtering out userinfo: the entire ordinary corpus must
        # stay identical. Never let the redactor decide which inputs to exclude.
        unchanged = url_pass(original.decode("utf-8")).encode("utf-8") == original
        assert unchanged, f"URL pass changed document: {name}"
    print(f"corpus: {len(documents)} working-tree documents, 0 excluded; differences=0")
