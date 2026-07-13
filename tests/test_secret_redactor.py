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

    with patch("ai_agent_bridge._messaging.get_db", side_effect=_fresh_conn):
        yield db_path


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


def test_redact_text_leaves_benign_code_with_secret_named_lhs_untouched():
    # Regression for the 2026-07-12 diff-corruption burn: a secret-*named*
    # identifier on the LHS must not nuke a benign code RHS (function call, list
    # comprehension, set literal). These must survive byte-identical.
    lines = [
        "token_verdicts = vesum_gate.check_tokens(sentence)",
        "tokens = [t for t in words if len(t) > 1]",
        "secret_keys = set(pairwise(parts))",
    ]

    for line in lines:
        assert redact_text(line) == line, line

    joined = "\n".join(lines)
    assert redact_text(joined) == joined
    assert REDACTION not in redact_text(joined)


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


def test_redact_text_redacts_unquoted_passphrase_but_not_code():
    # Documented narrow allowance: a bare whitespace-separated passphrase assigned
    # to a secret-named key is redacted (fail-closed), while code expressions —
    # which always carry () [] {} , . operators — pass through.
    redacted = redact_text("PASSWORD=correct horse battery staple")
    assert "correct horse" not in redacted
    assert REDACTION in redacted

    code = "secret = compute(a, b) + other[0]"
    assert redact_text(code) == code


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
    text = """before
-----BEGIN OPENSSH PRIVATE KEY-----
abc
def
-----END OPENSSH PRIVATE KEY-----
after"""

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


def test_github_comment_redacts_body_before_subprocess():
    from ai_agent_bridge._github import _gh_comment

    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        assert _gh_comment(
            123,
            "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456",
        ) is True

    posted_body = mock_run.call_args.kwargs["input"]
    assert "sk-" not in posted_body
    assert REDACTION in posted_body


def test_send_message_redacts_content_and_data(msg_db):
    from ai_agent_bridge._messaging import send_message

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


def test_read_message_redacts_existing_unredacted_rows(msg_db):
    from ai_agent_bridge._messaging import read_message

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
