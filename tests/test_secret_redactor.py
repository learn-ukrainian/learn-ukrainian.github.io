import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from secret_redactor import REDACTION, redact_text, redact_value


@pytest.fixture
def msg_db(tmp_path):
    db_path = tmp_path / "msg.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT, from_llm TEXT NOT NULL, to_llm TEXT NOT NULL,
        message_type TEXT DEFAULT 'message', content TEXT NOT NULL,
        data TEXT, timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending'
    )""")
    conn.commit()
    conn.close()

    def _fresh_conn():
        return sqlite3.connect(str(db_path))

    with patch("scripts.ai_agent_bridge._messaging.get_db", side_effect=_fresh_conn):
        yield db_path


@pytest.mark.parametrize("key", ["PASSWORD", "PASS", "SECRET_KEY", "API_TOKEN", "ACCESS_KEY", "API_KEY"])
@pytest.mark.parametrize("key_quote", ["", "'", '"'])
@pytest.mark.parametrize(
    ("quote", "variant"),
    [
        (quote, variant)
        for quote in ("", "'", '"')
        for variant in ("plain", "embedded_quote", "trailing_backslash", "multiline", "continued", "unterminated")
        if quote or variant in {"plain", "embedded_quote", "trailing_backslash"}
    ],
)
@pytest.mark.parametrize("prefix", ["", "status: pending ", "https://"])
def test_yaml_key_value_secret_masked_quoted_and_unquoted(key, key_quote, quote, prefix, variant):
    value = _OPAQUE_TOKEN[:12]
    if variant == "embedded_quote":
        value += ("''" if quote == "'" else '\\"') + _OPAQUE_TOKEN[:12]
    elif variant == "trailing_backslash":
        value += "\\\\" if quote == '"' else "\\"
    elif variant in {"multiline", "continued"}:
        value = value[:6] + ("\\" if variant == "continued" else "") + "\n" + value[6:]
    closing = "" if variant == "unterminated" else quote
    prefix += f"{key_quote}{key}{key_quote}: "
    raw = f"{prefix}{quote}{value}{closing}"
    expected = f"{prefix}{quote}{REDACTION}{closing}"
    assert redact_text(raw) == expected


@pytest.mark.parametrize("punctuation", ["()", "[]", "{}", ","])
@pytest.mark.parametrize("prefix", ["", "count = 1 ", "'", '"'])
def test_spaced_assignment_with_code_punctuation_masked(punctuation, prefix):
    value = punctuation[0] + _OPAQUE_TOKEN[:12] + punctuation[-1]
    closing = prefix if prefix in {"'", '"'} else ""
    assert redact_text(f"{prefix}PASS = {value}{closing}") == f"{prefix}PASS = {REDACTION}"


@pytest.mark.parametrize("text", ["Warning: provider failed", "The lesson: ordinary prose.", "status: pending", "time: 12:30"])
def test_prose_with_colon_unchanged(text):
    assert redact_text(text) == text


def test_redact_text_handles_env_dump_and_known_token_shapes():
    text = "\n".join(
        [
            "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890",
            "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456",
            "GOOGLE_API_KEY=AIzaabcdefghijklmnopqrstuvwxyz123456",
            "normal text",
        ]
    )

    redacted = redact_text(text)

    assert "ghp_" not in redacted
    assert "sk-" not in redacted
    assert "AIza" not in redacted
    assert redacted.count(REDACTION) == 3
    assert "normal text" in redacted


@pytest.mark.parametrize(
    "cursor_key",
    ["key_" + "0" * 64, "key_" + "aB09" * 16, "crsr_" + "a0" * 20, "crsr_" + "Z9" * 32],
)
def test_redact_text_redacts_cursor_keys_in_worker_output(cursor_key):
    assert redact_text(f"worker output: '{cursor_key}' rejected") == (
        f"worker output: '{REDACTION}' rejected"
    )


@pytest.mark.parametrize(
    "text",
    [
        "key_" + "0" * 63,
        "key_" + "0" * 65,
        "key_" + "g" * 64,
        "crsr_" + "a" * 39,
        "key_name crsr_status",
    ],
)
def test_redact_text_preserves_non_cursor_key_shapes(text):
    assert redact_text(text) == text


def test_redact_text_masks_spaced_code_with_secret_named_lhs():
    lines = [
        "token_verdicts = vesum_gate.check_tokens(sentence)",
        "tokens = [t for t in words if len(t) > 1]",
        "secret_keys = set(pairwise(parts))",
    ]

    for line in lines:
        expected = line.split(" = ")[0] + " = " + REDACTION if line != lines[1] else line
        assert redact_text(line) == expected, line

    joined = "\n".join(lines)
    assert redact_text(joined) == "\n".join([f"token_verdicts = {REDACTION}", lines[1], f"secret_keys = {REDACTION}"])


def test_redact_text_still_redacts_real_secret_shaped_assignments():
    cases = {
        "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890": "ghp_",
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY": "wJalrXUtn",
    }

    for line, marker in cases.items():
        redacted = redact_text(line)
        assert marker not in redacted, line
        assert REDACTION in redacted, line


def test_redact_text_still_redacts_quoted_and_json_secret_values():
    assert "sk-ant-" not in redact_text("api_key = 'sk-ant-abcdefghijklmnop1234'")
    assert REDACTION in redact_text('{"password": "hunter2secret"}')
    assert "hunter2secret" not in redact_text('{"password": "hunter2secret"}')


def test_redact_text_still_redacts_known_token_shapes_anywhere():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123def456"
    assert "eyJ" not in redact_text(f"the token is {jwt} in prose")
    assert REDACTION in redact_text(f"the token is {jwt} in prose")


_OPAQUE_TOKEN = "9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c"


@pytest.mark.parametrize(
    ("prose", "opaque_token"),
    [
        ('{"detail": "refresh failed for ' + _OPAQUE_TOKEN + '"}', _OPAQUE_TOKEN),
        ('{"error_description": "token ' + _OPAQUE_TOKEN + ' is expired"}', _OPAQUE_TOKEN),
        ('{"message": "bad token ' + _OPAQUE_TOKEN + '"}', _OPAQUE_TOKEN),
        ("refresh failed: " + _OPAQUE_TOKEN + " rejected", _OPAQUE_TOKEN),
        (
            "provider returned bW9ja1Rva2VuQWxwaGE5ODc2NTQzMjEwQmV0YQ== in an error",
            "bW9ja1Rva2VuQWxwaGE5ODc2NTQzMjEwQmV0YQ==",
        ),
        (
            "provider returned AbCdEfGhIjKlMnOpQrSt/UvWxYz0123456789abcdef in an error",
            "AbCdEfGhIjKlMnOpQrSt/UvWxYz0123456789abcdef",
        ),
        (
            "provider returned aBqLmNwErTyUiOpAsDfGhJkLzXcVbNmQ in an error",
            "aBqLmNwErTyUiOpAsDfGhJkLzXcVbNmQ",
        ),
    ],
)
def test_redact_text_redacts_opaque_high_entropy_tokens_embedded_in_prose(prose, opaque_token):
    """Regression for #5825: unrecognised opaque values must not leak in prose."""
    redacted = redact_text(prose)

    assert REDACTION in redacted
    assert opaque_token not in redacted


def test_redact_text_preserves_natural_language_and_low_entropy_identifiers():
    text = (
        "The pneumonoultramicroscopicsilicovolcanoconiosis lesson covers "
        "release-2026-08-production-candidate, chapter-2026-08-Production-Candidate, "
        "and abcabcabcabcabcabcabcabc1234."
    )

    assert redact_text(text) == text


def test_redact_text_redacts_unquoted_passphrase_and_secret_named_code():
    redacted = redact_text("PASSWORD=correct horse battery staple")
    assert "correct horse" not in redacted
    assert REDACTION in redacted

    code = "secret = compute(a, b) + other[0]"
    assert redact_text(code) == f"secret = {REDACTION}"


@pytest.mark.parametrize(
    "line",
    [
        # Findings 1-3: tight env secrets with @ / $ / ! that the old shape
        # allowlist let leak — must be redacted again.
        "POSTGRES_PASSWORD=p@ssw0rdwithat123456",
        "DB_PASS=my$uper$ecretlongvalue1234",
        "FOO_TOKEN=verylongwith!exclaim12345",
        # Finding: tight passphrase with a trailing comment / double spaces.
        "PASSWORD=correct horse battery staple # production",
        "MY_SECRET=word1  word2 word3",
        # Finding 6-ish: spaced INI-style bare value (no code punctuation) stays
        # redacted — correct side of the trade for a security control.
        "password = hunter2captain",
    ],
)
def test_redact_text_still_redacts_secret_assignments(line):
    redacted = redact_text(line)
    assert REDACTION in redacted, line
    # The secret material must be gone.
    for leak in ("p@ssw0rd", "my$uper", "!exclaim", "correct horse", "word1", "hunter2"):
        assert leak not in redacted, line


@pytest.mark.parametrize(
    "code",
    [
        "token_verdicts = vesum_gate.check_tokens(sentence)",
        "tokens = [t for t in words if len(t) > 1]",
        "secret_keys = set(pairwise(parts))",
        "secret = compute(a, b) + other[0]",
        "tokens = {t: 1 for t in words}",
    ],
)
def test_redact_text_masks_secret_named_spaced_code_expressions(code):
    key = code.split(" = ")[0]
    expected = code if key == "tokens" else f"{key} = {REDACTION}"
    assert redact_text(code) == expected


def test_redact_text_expected_fail_closed_over_redacts_spaced_dotted_ref():
    # EXPECTED FAIL-CLOSED: a spaced bare dotted reference assigned to a
    # secret-named key has no code punctuation (() [] {} ,), so it cannot be told
    # apart from an INI-style secret value. We accept the over-redaction — a rare
    # mangled code line beats a leaked secret.
    line = "token_fn = vesum_gate.check_tokens"
    redacted = redact_text(line)
    assert REDACTION in redacted
    assert "vesum_gate" not in redacted


def test_redact_value_recursively_redacts_secret_keys_and_values():
    value = {
        "nested": {
            "OPENAI_API_KEY": "sk-abcdefghijklmnopqrstuvwxyz123456",
            "note": "token github_pat_abcdefghijklmnopqrstuvwxyz1234567890",
        }
    }

    redacted = redact_value(value)

    assert redacted["nested"]["OPENAI_API_KEY"] == REDACTION
    assert "github_pat_" not in redacted["nested"]["note"]


def test_redact_value_does_not_redact_pass_substrings_or_status_flags():
    value = {
        "bypass_validation": True,
        "compass_heading": "north",
        "api_key_present": False,
        "DB_PASSWORD": "secret",
    }

    redacted = redact_value(value)

    assert redacted["bypass_validation"] is True
    assert redacted["compass_heading"] == "north"
    assert redacted["api_key_present"] is False
    assert redacted["DB_PASSWORD"] == REDACTION


def test_redact_text_redacts_private_key_blocks():
    ssh_header = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
    ssh_footer = "-----END " + "OPENSSH PRIVATE KEY-----"
    text = f"before\n{ssh_header}\nabc\ndef\n{ssh_footer}\nafter"

    redacted = redact_text(text)

    assert "OPENSSH PRIVATE KEY" not in redacted
    assert "abc" not in redacted
    assert REDACTION in redacted


def test_redact_text_handles_quoted_and_spaced_assignments():
    text = "\n".join(
        [
            "DB_PASSWORD = hunter2 with spaces",
            'OPENAI_API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"',
        ]
    )

    redacted = redact_text(text)

    assert "hunter2" not in redacted
    assert "sk-" not in redacted
    assert redacted.count(REDACTION) == 2


def test_github_comment_redacts_body_before_subprocess(monkeypatch):
    from scripts.ai_agent_bridge import _github
    from scripts.publish.github import request_run

    posted = []
    def send(args, **kwargs):
        body = Path(args[args.index("--body-file") + 1]).read_text()
        assert "sk-" not in body
        assert REDACTION in body
        posted.append(body)
        return MagicMock(returncode=0)

    def bridge(request, **kwargs):
        assert "sk-" not in request.fields["body"]
        assert REDACTION in request.fields["body"]
        return request_run(request, runner=send, **kwargs)

    monkeypatch.setattr(_github, "request_run", bridge)
    assert _github._gh_comment(123, "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456") is True
    assert len(posted) == 1
    assert "sk-" not in posted[0]
    assert REDACTION in posted[0]


def test_send_message_redacts_content_and_data(msg_db):
    from scripts.ai_agent_bridge._messaging import send_message

    with patch("subprocess.run"):
        msg_id = send_message(
            "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890",
            data=json.dumps(
                {
                    "OPENAI_API_KEY": "sk-abcdefghijklmnopqrstuvwxyz123456",
                    "note": "AIzaabcdefghijklmnopqrstuvwxyz123456",
                }
            ),
            quiet=True,
        )

    conn = sqlite3.connect(str(msg_db))
    row = conn.execute(
        "SELECT content, data FROM messages WHERE id = ?",
        (msg_id,),
    ).fetchone()
    conn.close()

    assert "ghp_" not in row[0]
    assert REDACTION in row[0]
    parsed = json.loads(row[1])
    assert parsed["OPENAI_API_KEY"] == REDACTION
    assert "AIza" not in parsed["note"]


@pytest.mark.parametrize("password", [
    "canary?tail#end",
    *("".join(("beforeCanary", delimiter, "https", "://", "afterCanary")) for delimiter in (":", "/", "?", "#", ",", ";")),
])
def test_send_message_redacts_malformed_url_password_before_storage(msg_db, password):
    from scripts.ai_agent_bridge._messaging import send_message

    raw = "".join(("https", "://", "u:", password, "@", "host.invalid", "/api"))
    expected = "".join(("https", "://", "u:", REDACTION, "@", "host.invalid", "/api"))
    with patch("subprocess.run"):
        send_message(raw, data=json.dumps({"detail": raw}), quiet=True)
    with sqlite3.connect(str(msg_db)) as conn:
        content, data = conn.execute("SELECT content, data FROM messages").fetchone()
    assert content == expected
    assert json.loads(data) == {"detail": expected}


def test_read_message_redacts_existing_unredacted_rows(msg_db):
    from scripts.ai_agent_bridge._messaging import read_message

    conn = sqlite3.connect(str(msg_db))
    conn.execute(
        """
        INSERT INTO messages (
            task_id, from_llm, to_llm, message_type, content, data, timestamp, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "t1",
            "gemini",
            "claude",
            "response",
            "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456",
            '{"GITHUB_TOKEN": "ghp_abcdefghijklmnopqrstuvwxyz1234567890"}',
            "2026-01-01T00:00:00+00:00",
            "pending",
        ),
    )
    msg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    msg = read_message(msg_id, quiet=True)

    assert "sk-" not in msg["content"]
    assert "ghp_" not in msg["data"]
    assert REDACTION in msg["content"]
    assert REDACTION in msg["data"]


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")
