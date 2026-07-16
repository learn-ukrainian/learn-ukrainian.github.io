"""Bridge-facing tests: review protocol prompt loading (not FINDING text).

Structured verifier behavior lives in ``tests/test_verify_review.py`` (issue #5284).
Legacy ``FINDING:`` text is no longer accepted by ``scripts/verify_review.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ai_agent_bridge import _channels, _inbox, _prompts
from ai_agent_bridge._inbox import _ClaimedDelivery, _ClaimedThread


def test_review_protocol_is_loaded_at_call_time(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    protocol = docs / "review-protocol.md"
    protocol.write_text("PROTO v1", encoding="utf-8")
    monkeypatch.setattr(_prompts, "REPO_ROOT", tmp_path)
    msg = {
        "content": "review this",
        "data": None,
        "from": "gemini",
        "task_id": "issue-1",
        "type": "query",
    }

    first = _prompts.build_codex_prompt(msg, review=True)
    protocol.write_text("PROTO v2", encoding="utf-8")
    second = _prompts.build_codex_prompt(msg, review=True)

    assert "PROTO v1" in first
    assert "PROTO v2" in second


def test_branch_targeted_review_prompt_forbids_primary_checkout_evidence(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "review-protocol.md").write_text("PROTO", encoding="utf-8")
    monkeypatch.setattr(_prompts, "REPO_ROOT", tmp_path)

    prompt = _prompts.review_protocol_prefix(
        branch="feature/review", pr_number=5150, worktree_provisioned=False
    )

    assert "checkout may NOT be that branch" in prompt
    assert "gh pr diff 5150" in prompt
    assert "git show origin/feature/review:<path>" in prompt
    assert "Do not read files from the current checkout" in prompt


def test_build_agent_prompt_review_prefix_precedes_channel_context(monkeypatch):
    monkeypatch.setattr(_channels, "review_protocol_prefix", lambda: "PROTO\n")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "CTX\n", "revs": {}, "missing": []},
    )
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(
        _channels,
        "read",
        lambda channel, tail=10: [
            {
                "created_at": "2026-04-19T12:00:00",
                "from_agent": "user",
                "round_index": 0,
                "body": "older",
            }
        ],
    )

    prompt = _channels.build_agent_prompt("pipeline", "new", review=True)["prompt"]
    assert prompt.index("PROTO") < prompt.index("CTX") < prompt.index("older") < prompt.index("new")


def test_inbox_thread_prompt_includes_review_prefix_before_context(monkeypatch):
    monkeypatch.setattr(_inbox, "review_protocol_prefix", lambda: "PROTO\n")
    monkeypatch.setattr(
        _channels,
        "read",
        lambda channel, thread_id=None: [
            {
                "message_id": "m1",
                "from_agent": "user",
                "round_index": 0,
                "created_at": "2026-04-19T12:00:00",
                "body": "root body",
                "attachments": [{"kind": "review_protocol"}],
            }
        ],
    )
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "CTX\n", "revs": {}, "missing": []},
    )
    claimed = _ClaimedThread(
        channel="pipeline",
        thread_id="t1",
        deliveries=(
            _ClaimedDelivery(
                delivery_id="d1",
                message_id="m1",
                thread_id="t1",
                channel="pipeline",
                to_agent="codex",
                to_model=None,
                deadline_seconds=None,
                from_agent="user",
                body="root body",
                round_index=0,
                created_at="2026-04-19T12:00:00",
            ),
        ),
    )

    prompt = _inbox._build_thread_prompt("codex", claimed, has_session=False)
    assert prompt.index("PROTO") < prompt.index("CTX") < prompt.index("root body")


def test_review_protocol_doc_declares_json_contract_and_legacy_removal():
    """docs/review-protocol.md must document the #5284 JSON contract."""
    root = Path(__file__).resolve().parents[2]
    text = (root / "docs" / "review-protocol.md").read_text(encoding="utf-8")
    assert "code-review-findings.v1" in text
    assert "Legacy" in text or "legacy" in text
    assert "EXIT" in text or "exit" in text
    assert "receipt" in text.lower()
