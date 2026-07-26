"""A live OAuth token must never land in a terminal by accident.

Printing the credential IS this command's contract — it is Claude Code's
`apiKeyHelper`, the same shape as `gh auth token`, and the launchd refresher sends
stdout to /dev/null. Both automated consumers pipe, so neither is affected.

The exposure is the operator running it by hand: the token then sits in scrollback
and shell history long after its ~15-minute life, somewhere nobody thinks to clear.
CodeQL flags it (`py/clear-text-logging-sensitive-data`) and is right to.

Operator chose this over suppressing the alert (2026-07-25).
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = REPO_ROOT / "scripts" / "lib" / "kimi_coding_oauth.py"

spec = importlib.util.spec_from_file_location("kimi_oauth_under_test", MODULE)
assert spec and spec.loader
oauth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oauth)

TOKEN = "sk-live-do-not-leak-me"


class _Stdout(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_refuses_to_print_into_a_terminal(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.delenv(oauth._FORCE_TTY_ENV, raising=False)

    rc = oauth._emit_token(TOKEN)

    assert rc == 3
    assert TOKEN not in sys.stdout.getvalue(), "the token was written to a terminal"


def test_refusal_explains_the_two_ways_forward(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.delenv(oauth._FORCE_TTY_ENV, raising=False)

    oauth._emit_token(TOKEN)

    err = capsys.readouterr().err
    assert "scrollback" in err, "say WHY, not just no"
    assert "Pipe it" in err
    assert oauth._FORCE_TTY_ENV in err, "the override must be discoverable"
    assert TOKEN not in err, "the refusal must not leak the token it is protecting"


def test_pipes_normally_when_stdout_is_not_a_terminal(monkeypatch):
    """The apiKeyHelper and launchd paths both pipe — they must be untouched."""
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=False))
    monkeypatch.delenv(oauth._FORCE_TTY_ENV, raising=False)

    rc = oauth._emit_token(TOKEN)

    assert rc == 0
    assert sys.stdout.getvalue().strip() == TOKEN


def test_explicit_override_is_honoured(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.setenv(oauth._FORCE_TTY_ENV, "1")

    rc = oauth._emit_token(TOKEN)

    assert rc == 0
    assert sys.stdout.getvalue().strip() == TOKEN


def test_override_must_be_exactly_1(monkeypatch):
    """A stray truthy value must not disable a credential guard."""
    monkeypatch.setattr(sys, "stdout", _Stdout(tty=True))
    monkeypatch.setenv(oauth._FORCE_TTY_ENV, "true")

    assert oauth._emit_token(TOKEN) == 3


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
