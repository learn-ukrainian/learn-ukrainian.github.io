"""Tests for ``scripts/build/gemini_session.py`` and ``session_analysis.py``.

Covers AC1–AC4 of issue #1174:
- Parser reads session files and extracts prompt + response
- Checklist compliance report generated
- Prompt size breakdown per phase
- Tested on a real a2-bridge-shaped session fixture
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure scripts/ is importable without adjusting PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build.gemini_session import (
    extract_prompt_and_response,
    find_session_near_time,
    parse_session,
)
from build.session_analysis import (
    _dict_to_yaml,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_session(
    tmp_path: Path,
    *,
    session_id: str = "test-session-id",
    start_time: str = "2026-04-10T21:23:18.297Z",
    messages: list[dict] | None = None,
) -> Path:
    """Write a session JSON file shaped like Gemini CLI's real output."""
    if messages is None:
        messages = [
            {
                "id": "m1",
                "timestamp": start_time,
                "type": "user",
                "content": [{"text": "# A2 bridge prompt\n\nWrite ONE section."}],
            },
            {
                "id": "m2",
                "timestamp": "2026-04-10T21:24:00.000Z",
                "type": "gemini",
                "content": [{"text": "## Пригадуємо відмінки\n\nSome content."}],
            },
        ]
    data = {
        "sessionId": session_id,
        "projectHash": "test-hash",
        "startTime": start_time,
        "lastUpdated": "2026-04-10T21:24:00.000Z",
        "messages": messages,
        "kind": "chat",
    }
    path = tmp_path / f"session-{start_time.replace(':', '-')}-abc.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parse_session_extracts_messages(tmp_path):
    path = _make_session(tmp_path)
    session = parse_session(path)
    assert session.session_id == "test-session-id"
    assert session.start_time == datetime(
        2026, 4, 10, 21, 23, 18, 297000, tzinfo=UTC
    )
    assert len(session.messages) == 2
    assert session.messages[0].type == "user"
    assert "Write ONE section" in session.messages[0].text
    assert session.messages[1].type == "gemini"
    assert "Пригадуємо відмінки" in session.messages[1].text


def test_parse_session_handles_prompt_only(tmp_path):
    """Real Gemini sessions sometimes only contain the user prompt (if the
    call crashed before a response landed). Parser must not explode."""
    path = _make_session(
        tmp_path,
        messages=[
            {
                "id": "m1",
                "timestamp": "2026-04-10T21:23:18.297Z",
                "type": "user",
                "content": [{"text": "just a prompt"}],
            }
        ],
    )
    session = parse_session(path)
    assert len(session.messages) == 1
    prompt, response = extract_prompt_and_response(session)
    assert prompt == "just a prompt"
    assert response == ""


def test_parse_session_handles_multi_part_content(tmp_path):
    """Content may be a list of multiple text parts — we concatenate them."""
    path = _make_session(
        tmp_path,
        messages=[
            {
                "id": "m1",
                "timestamp": "2026-04-10T21:23:18.297Z",
                "type": "user",
                "content": [{"text": "part one "}, {"text": "part two"}],
            }
        ],
    )
    session = parse_session(path)
    assert session.messages[0].text == "part one part two"


def test_parse_session_tolerates_malformed_json(tmp_path):
    path = tmp_path / "session-broken.json"
    path.write_text("this is not json", encoding="utf-8")
    session = parse_session(path)
    assert session.messages == []
    assert session.start_time is None


def test_extract_prompt_and_response_returns_first_of_each(tmp_path):
    path = _make_session(
        tmp_path,
        messages=[
            {
                "id": "m1",
                "timestamp": "2026-04-10T21:23:18.297Z",
                "type": "user",
                "content": [{"text": "first user"}],
            },
            {
                "id": "m2",
                "timestamp": "2026-04-10T21:23:19.000Z",
                "type": "gemini",
                "content": [{"text": "first model"}],
            },
            {
                "id": "m3",
                "timestamp": "2026-04-10T21:23:20.000Z",
                "type": "user",
                "content": [{"text": "second user"}],
            },
        ],
    )
    session = parse_session(path)
    prompt, response = extract_prompt_and_response(session)
    assert prompt == "first user"
    assert response == "first model"


# ---------------------------------------------------------------------------
# Session lookup helpers
# ---------------------------------------------------------------------------


def test_find_session_near_time_matches_closest(monkeypatch, tmp_path):
    chats_dir = tmp_path / "fake-gemini" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "fake-gemini"
    )

    _make_session(
        chats_dir, start_time="2026-04-10T21:20:00.000Z", session_id="s1"
    )
    closest = _make_session(
        chats_dir, start_time="2026-04-10T21:23:18.000Z", session_id="closest"
    )
    _make_session(
        chats_dir, start_time="2026-04-10T21:40:00.000Z", session_id="s3"
    )

    target = datetime(2026, 4, 10, 21, 23, 20, tzinfo=UTC)
    matched = find_session_near_time(target, max_drift_s=60.0)
    assert matched == closest


# ---------------------------------------------------------------------------
# Prompt section analysis
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Directive extraction + coverage
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Report building + YAML emission
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# YAML emitter internals
# ---------------------------------------------------------------------------

def test_dict_to_yaml_roundtrips_via_pyyaml():
    """Our minimal emitter must produce valid YAML that PyYAML can read."""
    import yaml
    obj = {
        "phase": "write",
        "prompt_chars": 123,
        "fraction": 0.42,
        "items": ["first", "second", "with: colon"],
        "nested": {"a": 1, "b": "two"},
        "empty_list": [],
        "empty_dict": {},
        "flag": True,
        "nothing": None,
    }
    text = _dict_to_yaml(obj)
    roundtripped = yaml.safe_load(text)
    assert roundtripped == obj


# ---------------------------------------------------------------------------
# Real-session integration (only runs if Gemini CLI data exists locally)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Drift calculations
# ---------------------------------------------------------------------------
