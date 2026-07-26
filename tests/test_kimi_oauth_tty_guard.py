"""A live OAuth token must never land in a terminal by accident.

Printing the credential IS this command's contract — it is Claude Code's
`apiKeyHelper`, the same shape as `gh auth token`, and the launchd refresher sends
stdout to /dev/null. Both automated consumers pipe, so neither is affected.

The exposure is the operator running it by hand: the token then sits in scrollback
and shell history long after its ~15-minute life, somewhere nobody thinks to clear.
CodeQL flags it (`py/clear-text-logging-sensitive-data`) and is right to.

This test module verifies both P1-a (no escape hatch printing to terminal, optional 0600 file delivery)
and P1-b (all error paths, HTTP error bodies, and exceptions redacted by token shape).
"""

from __future__ import annotations

import importlib.util
import io
import stat
import sys
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = REPO_ROOT / "scripts" / "lib" / "kimi_coding_oauth.py"

spec = importlib.util.spec_from_file_location("kimi_oauth_under_test", MODULE)
assert spec and spec.loader
oauth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oauth)

TOKEN = "sk-live-do-not-leak-me-1234567890"


class _Stdout(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_refuses_to_print_into_a_terminal(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.delenv(oauth._OUT_FILE_ENV, raising=False)
    monkeypatch.delenv(oauth._OUT_FILE_ENV_ALT, raising=False)

    rc = oauth._emit_token(TOKEN)

    assert rc == 3
    assert TOKEN not in sys.stdout.getvalue(), "the token was written to a terminal"


def test_refusal_explains_how_to_deliver_safely(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.delenv(oauth._OUT_FILE_ENV, raising=False)
    monkeypatch.delenv(oauth._OUT_FILE_ENV_ALT, raising=False)

    oauth._emit_token(TOKEN)

    err = capsys.readouterr().err
    assert "scrollback" in err, "say WHY, not just no"
    assert "Pipe it" in err
    assert oauth._OUT_FILE_ENV in err, "the file output option must be discoverable"
    assert "KIMI_OAUTH_ALLOW_TTY" not in err, "the deprecated dangerous flag must not be suggested"
    assert TOKEN not in err, "the refusal must not leak the token it is protecting"


def test_env_override_allow_tty_is_ignored_and_still_refuses(monkeypatch, capsys):
    """An opt-in flag that prints a live token to a TTY is forbidden (P1-a)."""
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.setenv("KIMI_OAUTH_ALLOW_TTY", "1")
    monkeypatch.delenv(oauth._OUT_FILE_ENV, raising=False)
    monkeypatch.delenv(oauth._OUT_FILE_ENV_ALT, raising=False)

    rc = oauth._emit_token(TOKEN)

    assert rc == 3
    assert TOKEN not in sys.stdout.getvalue()
    assert TOKEN not in capsys.readouterr().err


def test_pipes_normally_when_stdout_is_not_a_terminal(monkeypatch):
    """The apiKeyHelper and launchd paths both pipe — they must be untouched."""
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=False))
    monkeypatch.delenv(oauth._OUT_FILE_ENV, raising=False)

    rc = oauth._emit_token(TOKEN)

    assert rc == 0
    assert sys.stdout.getvalue().strip() == TOKEN


def test_out_file_delivers_token_securely_mode_0600(tmp_path: Path, monkeypatch, capsys):
    """Operator can deliver token to a file with 0600 permissions instead of printing to TTY."""
    out_file = tmp_path / "tokens" / "secret_token.txt"
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.setenv(oauth._OUT_FILE_ENV, str(out_file))

    rc = oauth._emit_token(TOKEN)

    assert rc == 0
    assert out_file.is_file()
    assert out_file.read_text(encoding="utf-8").strip() == TOKEN
    assert stat.S_IMODE(out_file.stat().st_mode) == 0o600
    assert TOKEN not in sys.stdout.getvalue()
    err = capsys.readouterr().err
    assert "token written to" in err
    assert TOKEN not in err


def test_out_file_alt_env_var_works(tmp_path: Path, monkeypatch):
    out_file = tmp_path / "secret_alt.txt"
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.setenv(oauth._OUT_FILE_ENV_ALT, str(out_file))

    rc = oauth._emit_token(TOKEN)

    assert rc == 0
    assert out_file.is_file()
    assert out_file.read_text(encoding="utf-8").strip() == TOKEN
    assert stat.S_IMODE(out_file.stat().st_mode) == 0o600


def test_refresh_failed_error_redacts_http_400_body_tokens(monkeypatch):
    """OAuth error bodies in HTTP 400 responses must be redacted by token shape (P1-b)."""
    synthetic_body = (
        '{"error": "invalid_grant", "received_access_token": "sk-synthetic-live-token-12345678901234567890"}'
    )
    fp = io.BytesIO(synthetic_body.encode("utf-8"))
    exc = urllib.error.HTTPError("http://auth.kimi.com/api/oauth/token", 400, "Bad Request", {}, fp)  # type: ignore[arg-type]

    def _mock_urlopen(*args, **kwargs):
        raise exc

    monkeypatch.setattr(urllib.request, "urlopen", _mock_urlopen)

    data = {"refresh_token": "r-synthetic-refresh-1234567890"}
    with pytest.raises(oauth.RefreshFailedError) as exc_info:
        oauth._refresh(data)
    err_msg = str(exc_info.value)
    assert "sk-synthetic-live-token" not in err_msg, "synthetic token leaked in exception message"
    assert "[REDACTED_SECRET]" in err_msg, "expected redaction placeholder in exception message"


def test_refresh_failed_error_redacts_unanticipated_nested_keys(monkeypatch):
    """Redaction must be by token SHAPE, not key name, for provider-controlled bodies."""
    unanticipated_body = (
        '{"error": "invalid", "provider_unanticipated_key": "sk-synthetic-secret-token-99999999999"}'
    )
    fp = io.BytesIO(unanticipated_body.encode("utf-8"))
    exc = urllib.error.HTTPError("http://auth.kimi.com/api/oauth/token", 400, "Bad Request", {}, fp)  # type: ignore[arg-type]

    def _mock_urlopen(*args, **kwargs):
        raise exc

    monkeypatch.setattr(urllib.request, "urlopen", _mock_urlopen)

    data = {"refresh_token": "r-synthetic-refresh-1234567890"}
    with pytest.raises(oauth.RefreshFailedError) as exc_info:
        oauth._refresh(data)
    err_msg = str(exc_info.value)
    assert "sk-synthetic-secret-token" not in err_msg
    assert "[REDACTED_SECRET]" in err_msg


def test_exception_init_redacts_token_in_message():
    raw_msg = "Refresh failed for token sk-synthetic-secret-1234567890123456"
    err = oauth.RefreshFailedError(raw_msg)
    assert "sk-synthetic-secret" not in str(err)
    assert "[REDACTED_SECRET]" in str(err)

    no_cred_err = oauth.NoCredentialsError(raw_msg)
    assert "sk-synthetic-secret" not in str(no_cred_err)
    assert "[REDACTED_SECRET]" in str(no_cred_err)


def test_print_err_redacts_token_shapes(capsys):
    raw_msg = "kimi-coding-oauth: failed with token sk-synthetic-secret-1234567890123456"
    oauth._print_err(raw_msg)

    err = capsys.readouterr().err
    assert "sk-synthetic-secret" not in err
    assert "[REDACTED_SECRET]" in err


def test_every_token_emission_path_goes_through_the_guard():
    """The sibling-path check.

    A guard on one of three print sites is not a guard. `cmd_token` has two exits
    that produce a token (cached and post-refresh) and `cmd_refresh` has a third;
    all must route through `_emit_token`, or the protection is bypassed by simply
    taking another branch.
    """
    source = MODULE.read_text(encoding="utf-8")
    assert source.count("print(token)") == 1, (
        "exactly one bare `print(token)` may exist, inside _emit_token; "
        "another emission path would bypass the TTY guard"
    )
    emit_def = source.index("def _emit_token")
    next_def = source.index("\ndef ", emit_def + 1)
    assert "print(token)" in source[emit_def:next_def], "the surviving print must be the guarded one"


@pytest.mark.parametrize(
    "response_body",
    [
        '{"error": "invalid_grant", "error_description": "token 9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c is expired"}',
        '{"detail": "refresh failed for 9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c"}',
        'refresh failed: 9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c rejected',
    ],
)
def test_refresh_failed_error_redacts_opaque_synthetic_tokens(monkeypatch, response_body):
    """Held credentials (opaque, non-prefixed) must be redacted by exact value on provider error text."""
    opaque_token = "9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c"
    fp = io.BytesIO(response_body.encode("utf-8"))
    exc = urllib.error.HTTPError("http://auth.kimi.com/api/oauth/token", 400, "Bad Request", {}, fp)  # type: ignore[arg-type]

    def _mock_urlopen(*args, **kwargs):
        raise exc

    monkeypatch.setattr(urllib.request, "urlopen", _mock_urlopen)

    data = {"refresh_token": opaque_token}
    with pytest.raises(oauth.RefreshFailedError) as exc_info:
        oauth._refresh(data)
    err_msg = str(exc_info.value)
    assert opaque_token not in err_msg, f"opaque synthetic token leaked in exception message: {err_msg}"
    assert "[REDACTED_SECRET]" in err_msg, f"expected redaction placeholder in exception message: {err_msg}"


def test_refresh_failed_error_redacts_token_straddling_truncation_boundary(monkeypatch):
    """Token straddling 200-byte truncation boundary must be redacted before truncation."""
    opaque_token = "6f1d2a9c7b8e9f0a1b2c3d4e5f6a7b8c"
    # Position token so it starts at offset 190, straddling the 200-byte boundary.
    padding_before = "x" * 190
    padding_after = "y" * 50
    response_body = f"{padding_before}{opaque_token}{padding_after}"

    fp = io.BytesIO(response_body.encode("utf-8"))
    exc = urllib.error.HTTPError("http://auth.kimi.com/api/oauth/token", 400, "Bad Request", {}, fp)  # type: ignore[arg-type]

    def _mock_urlopen(*args, **kwargs):
        raise exc

    monkeypatch.setattr(urllib.request, "urlopen", _mock_urlopen)

    data = {"refresh_token": opaque_token}
    with pytest.raises(oauth.RefreshFailedError) as exc_info:
        oauth._refresh(data)
    err_msg = str(exc_info.value)

    # Assert no prefix of length >= 8 of the secret appears in the output
    for i in range(8, len(opaque_token) + 1):
        prefix = opaque_token[:i]
        assert prefix not in err_msg, f"secret prefix {prefix!r} leaked in exception message: {err_msg}"


