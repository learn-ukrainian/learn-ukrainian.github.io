from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.result import Result
from ai_agent_bridge import _claude
from ai_agent_bridge._review_worktree import ProvisionedReviewWorktree


def test_claude_branch_review_invokes_from_provisioned_checkout(monkeypatch, tmp_path):
    checkout = ProvisionedReviewWorktree(
        path=tmp_path / "review-checkout",
        branch="feature/review",
        sha="a" * 40,
    )
    checkout.path.mkdir()
    captured: dict[str, object] = {}
    msg = {
        "id": 9,
        "task_id": "branch-review",
        "from": "codex",
        "to": "claude",
        "type": "query",
        "content": "Review the branch.",
        "data": json.dumps({"review_target": {"branch": "feature/review"}}),
    }

    @contextmanager
    def fake_checkout(*_args, **_kwargs):
        yield checkout

    monkeypatch.setattr(_claude, "_is_task_locked", lambda *_args: False)
    monkeypatch.setattr(_claude, "_write_pid_file", lambda *_args: None)
    monkeypatch.setattr(_claude, "_remove_pid_file", lambda *_args: None)
    monkeypatch.setattr(_claude.atexit, "register", lambda *_args: None)
    monkeypatch.setattr(_claude, "set_session", lambda *_args: None)
    monkeypatch.setattr(_claude, "provision_review_worktree", fake_checkout)
    monkeypatch.setattr(
        ProvisionedReviewWorktree,
        "review_prompt_evidence",
        lambda self, engine: "\nSEALED_DOSSIER",
    )
    monkeypatch.setattr(
        ProvisionedReviewWorktree,
        "isolation_tool_config",
        lambda self, engine: {"review_isolation": True},
    )
    monkeypatch.setattr(
        ProvisionedReviewWorktree,
        "bind_review_result",
        lambda self, result, engine: None,
    )
    monkeypatch.setattr(_claude, "send_message", lambda **_kwargs: 10)
    monkeypatch.setattr(_claude, "acknowledge", lambda *_args: None)
    monkeypatch.setattr(_claude, "record_ask_reply", lambda *_args: None)
    monkeypatch.setattr(
        _claude,
        "runtime_invoke",
        lambda *args, **kwargs: captured.update({"prompt": args[1], **kwargs})
        or Result(
            ok=True,
            agent="claude",
            model="claude-opus-4-8",
            mode="read-only",
            response="reply",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        ),
    )

    _claude._run_claude_sync_via_runtime(msg, 9, None, no_timeout=False, review=True)

    assert captured["cwd"] == checkout.path
    assert str(captured["prompt"]).endswith("SEALED_DOSSIER")
