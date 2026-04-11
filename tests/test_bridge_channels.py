"""Tests for the channel-based AI agent bridge primitives."""

from __future__ import annotations

import sqlite3
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _channels, _db


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    """Ensure every test runs against a clean, isolated SQLite database."""
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), \
         patch("ai_agent_bridge._db.DB_PATH", db_file):
        _db.init_db()
        yield db_file


# 1. Channel CRUD

def test_create_channel_basic():
    """Verify a new channel can be created and retrieved."""
    ch = _channels.create_channel("my-topic", description="A test topic")
    assert ch["name"] == "my-topic"
    assert ch["description"] == "A test topic"

    listed = _channels.list_channels()
    assert len(listed) == 1
    assert listed[0]["name"] == "my-topic"

def test_create_channel_duplicate_exist_ok_returns_existing():
    """Verify idempotent creation returns the existing channel unmodified."""
    _channels.create_channel("topic", description="original")
    ch = _channels.create_channel("topic", description="new", exist_ok=True)
    assert ch["description"] == "original"  # Existing row is returned

def test_create_channel_duplicate_exist_ok_false_raises():
    """Verify duplicate creation raises ValueError if exist_ok=False."""
    _channels.create_channel("topic")
    with pytest.raises(ValueError, match="already exists"):
        _channels.create_channel("topic", exist_ok=False)

def test_create_channel_with_include_and_subscribers():
    """Verify list fields round-trip correctly."""
    ch = _channels.create_channel(
        "topic",
        include=["shared", "other"],
        subscribers=["claude", "gemini"]
    )
    assert ch["include"] == ["shared", "other"]
    assert ch["subscribers"] == ["claude", "gemini"]

    fetched = _channels.get_channel("topic")
    assert fetched["include"] == ["shared", "other"]
    assert fetched["subscribers"] == ["claude", "gemini"]

def test_create_channel_invalid_name_raises():
    """Verify invalid channel names are rejected."""
    for bad_name in ["", "   ", "My Topic", "my topic"]:
        with pytest.raises(ValueError):
            _channels.create_channel(bad_name)

def test_get_channel_nonexistent_returns_none():
    """Verify getting a nonexistent channel returns None."""
    assert _channels.get_channel("nope") is None

def test_list_channels_ordered_by_creation():
    """Verify list_channels sorts by creation time ascending."""
    _channels.create_channel("topic-a")
    _channels.create_channel("topic-b")
    listed = _channels.list_channels()
    assert listed[0]["name"] == "topic-a"
    assert listed[1]["name"] == "topic-b"

# 2. Posting (origin)

def test_post_to_nonexistent_channel_raises_valueerror():
    """Verify posting requires the channel to exist."""
    with pytest.raises(ValueError, match="does not exist"):
        _channels.post("nope", "gemini", "hello")

def test_post_origin_self_references_thread_id():
    """Verify a root post has thread_id equal to its message_id."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello")
    assert res["thread_id"] == res["message_id"]

def test_post_origin_round_index_is_zero():
    """Verify a root post starts at round_index 0."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello")
    assert res["round_index"] == 0

def test_post_with_attachments_roundtrip_json():
    """Verify attachments are stored and parsed correctly."""
    _channels.create_channel("topic")
    atts = [{"name": "file.txt", "content": "data"}]
    _channels.post("topic", "gemini", "hello", attachments=atts)

    msg = _channels.read("topic")[0]
    assert msg["attachments"] == atts

def test_post_with_monitor_snapshot_roundtrip():
    """Verify monitor_state_snapshot is stored and parsed correctly."""
    _channels.create_channel("topic")
    snap = {"state": "good", "count": 42}
    _channels.post("topic", "gemini", "hello", monitor_state_snapshot=snap)

    msg = _channels.read("topic")[0]
    assert msg["monitor_state_snapshot"] == snap

def test_post_creates_delivery_row_per_recipient():
    """Verify posting creates one delivery row per specified recipient."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello", to_agents=["claude", "codex", "user"])
    assert len(res["delivery_ids"]) == 3

    dlvs = _channels.deliveries_for_message(res["message_id"])
    assert len(dlvs) == 3
    assert {d["to_agent"] for d in dlvs} == {"claude", "codex", "user"}
    assert all(d["status"] == "pending" for d in dlvs)

def test_post_with_zero_recipients_no_deliveries():
    """Verify posting without recipients creates no delivery rows."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello")
    assert res["delivery_ids"] == []

    dlvs = _channels.deliveries_for_message(res["message_id"])
    assert len(dlvs) == 0

def test_post_invalid_from_agent_raises():
    """Verify posting requires a valid from_agent."""
    _channels.create_channel("topic")
    with pytest.raises(ValueError, match="Unknown agent"):
        _channels.post("topic", "invalid", "hello")

def test_post_invalid_kind_raises():
    """Verify posting requires a valid kind."""
    _channels.create_channel("topic")
    with pytest.raises(ValueError, match="Unknown kind"):
        _channels.post("topic", "gemini", "hello", kind="invalid")

# 3. Replies (threading)

def test_reply_inherits_parent_thread_id():
    """Verify a reply shares the thread_id of its parent."""
    _channels.create_channel("topic")
    parent = _channels.post("topic", "gemini", "hello")
    reply = _channels.post("topic", "claude", "hi", parent_id=parent["message_id"])
    assert reply["thread_id"] == parent["thread_id"]

def test_reply_increments_round_index():
    """Verify a reply has a round_index one greater than its parent."""
    _channels.create_channel("topic")
    parent = _channels.post("topic", "gemini", "hello")
    reply = _channels.post("topic", "claude", "hi", parent_id=parent["message_id"])
    assert reply["round_index"] == 1

def test_reply_nonexistent_parent_raises():
    """Verify replying to an unknown message raises ValueError."""
    _channels.create_channel("topic")
    with pytest.raises(ValueError, match="not found"):
        _channels.post("topic", "claude", "hi", parent_id="nope")

def test_nested_reply_round_index_chain():
    """Verify nested replies correctly increment round_index."""
    _channels.create_channel("topic")
    p0 = _channels.post("topic", "gemini", "p0")
    p1 = _channels.post("topic", "claude", "p1", parent_id=p0["message_id"])
    p2 = _channels.post("topic", "gemini", "p2", parent_id=p1["message_id"])
    assert p0["round_index"] == 0
    assert p1["round_index"] == 1
    assert p2["round_index"] == 2
    assert p0["thread_id"] == p1["thread_id"] == p2["thread_id"]

# 4. Reading

def test_read_empty_channel_returns_empty_list():
    """Verify reading an empty channel returns [] rather than None/error."""
    _channels.create_channel("topic")
    assert _channels.read("topic") == []

def test_read_tail_respects_limit():
    """Verify read(tail=N) returns at most N messages in chronological order."""
    _channels.create_channel("topic")
    for i in range(5):
        _channels.post("topic", "gemini", f"msg{i}")

    msgs = _channels.read("topic", tail=3)
    assert len(msgs) == 3
    assert msgs[0]["body"] == "msg2"
    assert msgs[2]["body"] == "msg4"

def test_read_thread_returns_all_messages_in_order():
    """Verify reading a thread returns all messages sorted by round_index."""
    _channels.create_channel("topic")
    p0 = _channels.post("topic", "gemini", "p0")
    p1 = _channels.post("topic", "claude", "p1", parent_id=p0["message_id"])
    p2 = _channels.post("topic", "gemini", "p2", parent_id=p1["message_id"])

    msgs = _channels.read("topic", thread_id=p0["thread_id"])
    assert len(msgs) == 3
    assert msgs[0]["message_id"] == p0["message_id"]
    assert msgs[1]["message_id"] == p1["message_id"]
    assert msgs[2]["message_id"] == p2["message_id"]

def test_read_thread_filters_by_channel():
    """Verify thread reads don't leak across channels if IDs accidentally match."""
    _channels.create_channel("topic1")
    _channels.create_channel("topic2")
    p0 = _channels.post("topic1", "gemini", "p0")
    # Manually insert a matching thread_id in another channel
    conn = _db.get_db()
    conn.execute(
        "INSERT INTO channel_messages (message_id, channel, thread_id, round_index, from_agent, body, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("fake", "topic2", p0["thread_id"], 0, "claude", "fake", "2000-01-01")
    )
    conn.commit()
    conn.close()

    msgs = _channels.read("topic1", thread_id=p0["thread_id"])
    assert len(msgs) == 1
    assert msgs[0]["message_id"] == p0["message_id"]

# 5. Deliveries (outbound state machine)

def test_mark_delivery_dispatched_sets_timestamp():
    """Verify marking as dispatched updates status and dispatched_at."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello", to_agents=["claude"])
    dlv_id = res["delivery_ids"][0]

    _channels.mark_delivery(dlv_id, "dispatched")
    dlvs = _channels.deliveries_for_message(res["message_id"])
    assert dlvs[0]["status"] == "dispatched"
    assert dlvs[0]["dispatched_at"] is not None

def test_mark_delivery_delivered_sets_delivered_at():
    """Verify marking as delivered updates status and delivered_at."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello", to_agents=["claude"])
    dlv_id = res["delivery_ids"][0]

    _channels.mark_delivery(dlv_id, "delivered")
    dlvs = _channels.deliveries_for_message(res["message_id"])
    assert dlvs[0]["status"] == "delivered"
    assert dlvs[0]["delivered_at"] is not None

def test_mark_delivery_failed_stores_error():
    """Verify marking as failed updates status and error message."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello", to_agents=["claude"])
    dlv_id = res["delivery_ids"][0]

    _channels.mark_delivery(dlv_id, "failed", error="timeout")
    dlvs = _channels.deliveries_for_message(res["message_id"])
    assert dlvs[0]["status"] == "failed"
    assert dlvs[0]["error"] == "timeout"

def test_mark_delivery_invalid_status_raises():
    """Verify updating to an unknown status raises ValueError."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello", to_agents=["claude"])
    with pytest.raises(ValueError, match="invalid delivery status"):
        _channels.mark_delivery(res["delivery_ids"][0], "magic")

def test_deliveries_for_message_returns_all_recipients():
    """Verify deliveries_for_message lists all intended recipients."""
    _channels.create_channel("topic")
    res = _channels.post("topic", "gemini", "hello", to_agents=["claude", "codex"])
    dlvs = _channels.deliveries_for_message(res["message_id"])
    assert len(dlvs) == 2
    assert {d["to_agent"] for d in dlvs} == {"claude", "codex"}

def test_pending_deliveries_for_agent_filters_by_agent():
    """Verify agent queues only return their own pending deliveries."""
    _channels.create_channel("topic")
    _channels.post("topic", "gemini", "msg", to_agents=["claude", "codex"])

    claude_q = _channels.pending_deliveries_for("claude")
    codex_q = _channels.pending_deliveries_for("codex")
    gemini_q = _channels.pending_deliveries_for("gemini")

    assert len(claude_q) == 1
    assert len(codex_q) == 1
    assert len(gemini_q) == 0

def test_pending_deliveries_for_agent_ordered_oldest_first():
    """Verify the pending queue orders by oldest message first."""
    _channels.create_channel("topic")
    _channels.post("topic", "gemini", "msg1", to_agents=["claude"])
    _channels.post("topic", "gemini", "msg2", to_agents=["claude"])

    q = _channels.pending_deliveries_for("claude")
    assert len(q) == 2
    assert q[0]["body"] == "msg1"
    assert q[1]["body"] == "msg2"

# 6. Concurrency

def test_concurrent_post_no_data_loss(isolate_db):
    """Verify multiple threads can post simultaneously without locking errors."""
    _channels.create_channel("topic")

    threads = []
    barrier = threading.Barrier(5)

    def worker(i):
        barrier.wait()
        _channels.post("topic", "gemini", f"body{i}", to_agents=["claude", "codex", "user"])

    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Verify via direct sqlite3 connection
    conn = sqlite3.connect(isolate_db)
    cursor = conn.cursor()
    msgs = cursor.execute("SELECT message_id FROM channel_messages WHERE channel='topic'").fetchall()
    dlvs = cursor.execute("SELECT delivery_id FROM deliveries").fetchall()
    conn.close()

    assert len(msgs) == 5
    assert len(set(msgs)) == 5  # No duplicates
    assert len(dlvs) == 15      # 5 messages * 3 recipients

def test_concurrent_reply_to_same_parent():
    """Verify multiple threads can reply to the same parent safely."""
    _channels.create_channel("topic")
    parent = _channels.post("topic", "gemini", "parent")

    threads = []
    barrier = threading.Barrier(3)

    def worker(i):
        barrier.wait()
        _channels.post("topic", "claude", f"reply{i}", parent_id=parent["message_id"])

    for i in range(3):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    msgs = _channels.read("topic", thread_id=parent["thread_id"])
    assert len(msgs) == 4
    # The parent is 0, the replies should all be round_index 1
    round_indices = [m["round_index"] for m in msgs]
    assert round_indices == [0, 1, 1, 1]

# 7. context_sha256 helper

def test_context_sha256_existing_file(tmp_path):
    """Verify sha256 computes correctly for an existing file."""
    f = tmp_path / "context.md"
    f.write_text("hello world")
    import hashlib
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert _channels.context_sha256(f) == expected

def test_context_sha256_missing_file_returns_empty_string(tmp_path):
    """Verify missing files return empty string rather than raising."""
    f = tmp_path / "nope.md"
    assert _channels.context_sha256(f) == ""
