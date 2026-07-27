"""Formal ``review-pr`` lifecycle records regressions (#5900)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge import _ask_lifecycle as lifecycle
from scripts.ai_agent_bridge import _codex, _review_pr
from scripts.ai_agent_bridge._db import init_db
from scripts.ai_agent_bridge._messaging import send_message


@pytest.fixture
def bridge_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "messages.db"
    monkeypatch.setattr("scripts.ai_agent_bridge._config.DB_PATH", db_path)
    monkeypatch.setattr("scripts.ai_agent_bridge._db.DB_PATH", db_path)
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    conn = init_db()
    conn.close()
    return db_path


def _args(*, background: bool) -> SimpleNamespace:
    return SimpleNamespace(
        pr="5900",
        reviewer="codex",
        claude_available=None,
        model=None,
        effort=None,
        extra=None,
        task_id=None,
        dry_run=False,
        from_llm="claude",
        background=background,
        no_timeout=False,
    )


def _review_ask() -> int:
    message_id = send_message(
        "Review the PR.",
        "review-pr-5900",
        "review",
        from_llm="claude",
        to_llm="codex",
        quiet=True,
    )
    lifecycle.register_ask(message_id)
    return message_id


def test_review_pr_spawn_failure_writes_terminal_cause(
    bridge_db: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failure after sending the review ask is durable rather than silent."""

    def failed_spawn(*_args, on_message_created, **_kwargs):
        on_message_created(_review_ask())
        raise OSError("sealed snapshot runner unavailable")

    monkeypatch.setattr(_codex, "ask_codex", failed_spawn)

    with pytest.raises(OSError, match="sealed snapshot runner unavailable"):
        _review_pr.handle_review_pr(_args(background=True))

    terminal = json.loads(
        (tmp_path / "batch_state" / "asks" / "review-pr-5900" / "terminal.json").read_text()
    )
    assert terminal["rc_or_signal"] == 1
    assert terminal["stage"] == "spawn-failure"
    assert terminal["cause"] == "OSError: sealed snapshot runner unavailable"


def test_review_pr_sync_success_writes_terminal_record(
    bridge_db: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A completed formal review receives the same durable success receipt."""

    def successful_review(*_args, on_message_created, **_kwargs):
        message_id = _review_ask()
        on_message_created(message_id)
        reply_id = send_message(
            '{"schema_version":"code-review-findings.v1"}',
            "review-pr-5900",
            "response",
            from_llm="codex",
            to_llm="claude",
            quiet=True,
        )
        assert lifecycle.record_ask_reply(message_id, reply_id) is True
        return message_id

    monkeypatch.setattr(_codex, "ask_codex", successful_review)

    assert _review_pr.handle_review_pr(_args(background=False)) == 0

    terminal = json.loads(
        (tmp_path / "batch_state" / "asks" / "review-pr-5900" / "terminal.json").read_text()
    )
    assert terminal["rc_or_signal"] == 0
    assert terminal["stage"] == "success"
    assert "cause" not in terminal


def test_review_pr_sync_exception_writes_terminal_record(
    bridge_db: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An adapter exception after send cannot leave a formal review unaccounted."""

    def failed_review(*_args, on_message_created, **_kwargs):
        on_message_created(_review_ask())
        raise RuntimeError("sealed runner crashed")

    monkeypatch.setattr(_codex, "ask_codex", failed_review)

    with pytest.raises(RuntimeError, match="sealed runner crashed"):
        _review_pr.handle_review_pr(_args(background=False))

    terminal = json.loads(
        (tmp_path / "batch_state" / "asks" / "review-pr-5900" / "terminal.json").read_text()
    )
    assert terminal["stage"] == "exception"
    assert terminal["cause"] == "RuntimeError: sealed runner crashed"


def test_review_pr_sync_timeout_writes_terminal_record(
    bridge_db: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A timeout reported by an adapter remains visibly terminal."""

    def timed_out_review(*_args, on_message_created, **_kwargs):
        message_id = _review_ask()
        on_message_created(message_id)
        lifecycle.record_ask_failure(message_id, "Codex hard timeout: 900s")
        return message_id

    monkeypatch.setattr(_codex, "ask_codex", timed_out_review)

    assert _review_pr.handle_review_pr(_args(background=False)) == 0

    terminal = json.loads(
        (tmp_path / "batch_state" / "asks" / "review-pr-5900" / "terminal.json").read_text()
    )
    assert terminal["stage"] == "timeout"
    assert terminal["cause"] == "failed:Codex hard timeout: 900s"


def test_review_pr_background_worker_records_failed_status_as_cause(
    bridge_db: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The detached path preserves the root cause in its terminal receipt."""
    message_id = _review_ask()
    monkeypatch.setattr(
        lifecycle,
        "_background_options",
        lambda *_args: {"review_pr_lifecycle": True},
    )
    monkeypatch.setattr(
        lifecycle,
        "_process_target",
        lambda *_args: lifecycle.record_ask_failure(message_id, "remote_oid_mismatch:head changed"),
    )

    lifecycle.process_background_ask(message_id, "codex")

    terminal = json.loads(
        (tmp_path / "batch_state" / "asks" / "review-pr-5900" / "terminal.json").read_text()
    )
    assert terminal["stage"] == "failed"
    assert terminal["cause"] == "failed:remote_oid_mismatch:head changed"
