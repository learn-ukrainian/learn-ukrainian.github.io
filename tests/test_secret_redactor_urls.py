"""URL credentials and ordinary-text compatibility for #9948.

Every credential-shaped fixture is assembled from parts at runtime. Corpus
inputs are public repository documents and synthetic messages, never stored
message bodies. The reference executes the actual origin/main helper.
"""

import io
import re
import subprocess
import tarfile
import types
from pathlib import Path

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


def test_ordinary_repository_corpus_matches_actual_origin_main_redactor():
    repo = Path(__file__).resolve().parents[1]
    base = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=repo, text=True, timeout=30).strip()
    source = subprocess.check_output(["git", "show", base + ":scripts/secret_redactor.py"], cwd=repo, text=True, timeout=30)
    baseline = types.ModuleType("baseline_secret_redactor")
    exec(compile(source, "origin/main:scripts/secret_redactor.py", "exec"), baseline.__dict__)
    archive = subprocess.check_output(
        ["git", "archive", base, "docs/best-practices", "docs/runbooks", "agents_extensions/shared/rules"],
        cwd=repo,
        timeout=30,
    )
    documents = []
    excluded = 0
    # Independently exclude whole documents containing ANY URL token with @,
    # including username-only URLs. No new parser/detector defines this corpus.
    url_with_at = re.compile(r"[^\s]*://[^\s]*@[^\s]*")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for member in tree:
            if member.isfile() and member.name.endswith(".md"):
                text = tree.extractfile(member).read().decode("utf-8")
                if url_with_at.search(text):
                    excluded += 1
                else:
                    documents.append(text)
    messages = [
        "Review complete; the tests passed. Please read scripts/api/lane_health.py.",
        "Budget ~500K/1M, fraction ~2/3; codes ENOTFOUND EAI_AGAIN.",
        *SAFE_URLS,
        "Retry GET " + SAFE_URLS[0] + " 404; next " + SAFE_URLS[1],
        "token_verdicts = vesum_gate.check_tokens(sentence)",
    ]
    assert len(documents) >= 100
    for text in documents + messages:
        # Counts only on failure: no repository bodies or synthetic secrets.
        assert redact_text(text) == baseline.redact_text(text), "corpus output differs"
    print(f"corpus: {len(documents)} documents, {len(messages)} synthetic bodies, {excluded} excluded; differences=0; base={base}")
