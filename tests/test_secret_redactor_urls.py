"""URL credentials and ordinary-text compatibility for #9948.

Every credential-shaped fixture is assembled from parts at runtime. Corpus
inputs are public working-tree documents and frozen synthetic messages, never
stored message bodies. No reference implementation or Git history is needed.
"""


import pytest

from scripts.secret_redactor import REDACTION, redact_text, redact_url_authority, redact_value

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


@pytest.mark.parametrize("prefix", ["12345", ""])
@pytest.mark.parametrize("joiner", [",", ";", "?next=", "/archive/", "#next="])
def test_nested_url_does_not_turn_numeric_or_empty_port_into_userinfo(prefix, joiner):
    outer = "".join(("https://outer.invalid:", prefix, "/api", joiner))
    raw = outer + credential_url("nextCanary")
    expected = outer + credential_url(REDACTION)
    assert redact_text(raw) == expected
    assert redact_text(expected) == expected


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


def test_nonnumeric_colon_prefix_uses_round_a_fallback_across_nested_scheme():
    # This invalid port also has the round-a shape of malformed userinfo.
    raw = "".join(("https://outer.invalid:", "opaque/path?next=https://source.invalid/a", "@", "b"))
    expected = "".join(("https://outer.invalid:", REDACTION, "@", "b"))
    assert redact_text(raw) == expected
    assert "".join(redact_url_authority(raw)) == expected
    assert redact_text(expected) == expected
