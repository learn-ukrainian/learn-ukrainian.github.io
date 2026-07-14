"""Regression test for the agy bridge model-selection bug.

`ask-agy --to-model "Gemini 3.1 Pro (High)"` silently ran flash because
`_extract_target_model` queried a `to_model` COLUMN that never existed in the
`messages` schema. `send_message` stores `to_model` inside the `data` JSON blob,
so the read must come from there (ported from kubedojo's fixed bridge).
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.result import Result
from ai_agent_bridge._agy import _extract_target_model, process_for_agy
from ai_agent_bridge._config import REPO_ROOT
from ai_agent_bridge._review_worktree import ProvisionedReviewWorktree


def test_pro_slug_round_trips_from_data_blob():
    msg = {"id": 1, "data": json.dumps({"to_model": "gemini-3.1-pro-high"})}
    assert _extract_target_model(msg) == "gemini-3.1-pro-high"


def test_display_label_round_trips():
    msg = {"id": 2, "data": json.dumps({"to_model": "Gemini 3.1 Pro (High)"})}
    assert _extract_target_model(msg) == "Gemini 3.1 Pro (High)"


def test_data_with_other_keys_but_no_to_model_returns_none():
    msg = {"id": 3, "data": json.dumps({"from_model": "claude"})}
    assert _extract_target_model(msg) is None


def test_missing_or_empty_data_returns_none():
    assert _extract_target_model({"id": 4, "data": None}) is None
    assert _extract_target_model({"id": 5, "data": ""}) is None
    assert _extract_target_model({"id": 6}) is None


def test_malformed_json_returns_none_not_raise():
    assert _extract_target_model({"id": 7, "data": "{not json"}) is None


def test_empty_to_model_value_returns_none():
    msg = {"id": 8, "data": json.dumps({"to_model": ""})}
    assert _extract_target_model(msg) is None


def test_agy_bridge_records_unsandboxed_repo_read_mode(monkeypatch):
    """#4837: AGY has opt-in ``--sandbox`` only, so bridge Q&A is danger mode."""
    msg = {
        "id": 8,
        "task_id": "bridge-read",
        "from": "codex",
        "to": "agy",
        "type": "query",
        "content": "Read the named file.",
        "data": None,
    }
    captured: dict[str, object] = {}

    monkeypatch.setattr("ai_agent_bridge._agy._fetch_agy_message", lambda _id: msg)
    monkeypatch.setattr("ai_agent_bridge._agy.acknowledge", lambda _id: None)
    monkeypatch.setattr("ai_agent_bridge._agy.send_message", lambda **_kwargs: 9)
    monkeypatch.setattr("ai_agent_bridge._agy.record_ask_reply", lambda *_args: None)

    def fake_invoke(*_args, **kwargs):
        captured.update(kwargs)
        return Result(
            ok=True,
            agent="agy",
            model="gemini-3.5-flash-high",
            mode="danger",
            response="reply",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    monkeypatch.setattr("ai_agent_bridge._agy.agent_runner.invoke", fake_invoke)

    assert process_for_agy(8, stdout_only=True) == "reply"
    assert captured["mode"] == "danger"
    assert captured["tool_config"] == {
        "bridge_repo_read": True,
        "repo_read_root": str(REPO_ROOT),
    }
    # Regression (post-#4841): a danger-mode spawn whose cwd is the primary
    # checkout is refused by the worktree containment guard (#4444), which
    # broke every `ask-agy` run from repo root. The bridge must spawn from an
    # out-of-tree scratch cwd and grant repo READ access via repo_read_root
    # (--add-dir) instead.
    spawn_cwd = Path(str(captured["cwd"])).resolve()
    repo_root = Path(str(REPO_ROOT)).resolve()
    assert spawn_cwd != repo_root
    assert not spawn_cwd.is_relative_to(repo_root)
    assert spawn_cwd.is_dir()


def test_agy_branch_review_grants_only_the_provisioned_worktree(monkeypatch, tmp_path):
    checkout = ProvisionedReviewWorktree(
        path=tmp_path / "review-checkout",
        branch="feature/review",
        sha="a" * 40,
    )
    checkout.path.mkdir()
    msg = {
        "id": 9,
        "task_id": "branch-review",
        "from": "codex",
        "to": "agy",
        "type": "query",
        "content": "Review the branch.",
        "data": json.dumps({"review_target": {"branch": "feature/review"}}),
    }
    captured: dict[str, object] = {}

    @contextmanager
    def fake_checkout(*_args, **_kwargs):
        yield checkout

    monkeypatch.setattr("ai_agent_bridge._agy._fetch_agy_message", lambda _id: msg)
    monkeypatch.setattr("ai_agent_bridge._agy.provision_review_worktree", fake_checkout)
    monkeypatch.setattr("ai_agent_bridge._agy.acknowledge", lambda _id: None)
    monkeypatch.setattr("ai_agent_bridge._agy.send_message", lambda **_kwargs: 10)
    monkeypatch.setattr("ai_agent_bridge._agy.record_ask_reply", lambda *_args: None)
    monkeypatch.setattr(
        "ai_agent_bridge._agy.agent_runner.invoke",
        lambda *_args, **kwargs: captured.update(kwargs)
        or Result(
            ok=True,
            agent="agy",
            model="gemini-3.5-flash-high",
            mode="danger",
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

    assert process_for_agy(9, review=True, stdout_only=True) == "reply"
    assert captured["cwd"] != checkout.path
    assert captured["tool_config"] == {
        "bridge_repo_read": True,
        "repo_read_root": str(checkout.path),
    }
