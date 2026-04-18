from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import verify_review
from ai_agent_bridge import _channels, _inbox, _prompts
from ai_agent_bridge._inbox import _ClaimedDelivery, _ClaimedThread


def _finding(path: str, line: int, quote: str, *, include_fix: bool = True) -> str:
    parts = [
        "FINDING:",
        f"FILE:LINE: {path}:{line}",
        "CURRENT CODE (verbatim from branch):",
        "```",
        quote,
        "```",
        "WHY WRONG:",
        "This is wrong.",
    ]
    if include_fix:
        parts.extend(["FIX:", "Replace it."])
    parts.extend(["SEVERITY: major", "SOURCE: none"])
    return "\n".join(parts)


def test_verify_review_outcomes(monkeypatch):
    files = {
        "main:ok.py": "a = 1\nb = 2\n",
        "main:mismatch.py": "x = 0\nvalue = 2\n",
        "main:missing.py": "z = 9\n",
    }
    monkeypatch.setattr(verify_review, "_run", lambda cmd, input_text=None: files[cmd[-1]])
    review = "\n\n".join(
        [
            _finding("ok.py", 2, "b = 2"),
            _finding("mismatch.py", 1, "value = 2"),
            _finding("missing.py", 1, "value = 2"),
        ]
    )

    results = [
        verify_review._verify_finding(
            verify_review._parse_finding(match.group("body"), idx),
            "main",
        )
        for idx, match in enumerate(
            verify_review.FINDING_RE.finditer(review), start=1
        )
    ]

    assert [result["outcome"] for result in results] == [
        "verified",
        "line_mismatch",
        "quote_missing",
    ]


def test_malformed_finding_is_discarded_with_reason():
    result = verify_review._parse_finding(
        _finding("bad.py", 1, "value = 2", include_fix=False),
        7,
    )
    assert result["outcome"] == "discarded"
    assert result["reason"] == "missing_fields:fix"


def test_issue_mode_reads_latest_comment_and_posts_summary(
    monkeypatch, capsys
):
    review = _finding("ok.py", 2, "b = 2")
    calls: list[list[str]] = []

    def _fake_run(cmd, input_text=None):
        calls.append(cmd)
        if cmd[:3] == ["gh", "issue", "view"]:
            return json.dumps({"comments": [{"body": "old"}, {"body": review}]})
        if cmd[:2] == ["git", "show"]:
            return "a = 1\nb = 2\n"
        if cmd[:3] == ["gh", "issue", "comment"]:
            return ""
        raise AssertionError(cmd)

    monkeypatch.setattr(verify_review, "_run", _fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["verify_review.py", "--issue", "1331", "--branch", "main", "--post-comment"],
    )

    assert verify_review.main() == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert json.loads(out[0])["outcome"] == "verified"
    assert calls[-1][:3] == ["gh", "issue", "comment"]


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
        lambda channel, tail=10: [{"created_at": "2026-04-19T12:00:00", "from_agent": "user", "round_index": 0, "body": "older"}],
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
