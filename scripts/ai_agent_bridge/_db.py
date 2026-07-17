"""Database initialization and session management.

The broker DB stores two subsystems:

**Legacy 1:1 message bus** (``messages``, ``sessions``) — used by the
``ask-claude``/``ask-gemini``/``ask-codex`` commands. Stays unchanged
while the channel bridge (#1190) is being rolled out.

**Channel bridge** (``channels``, ``channel_messages``, ``deliveries``) —
the new multi-agent primitive. A post = 1 ``channel_messages`` row +
N ``deliveries`` rows (one per recipient). Replies are just new
``channel_messages`` rows with ``parent_id`` pointing at the original;
they do NOT update the delivery row — delivery tracks outbound
routing state only (pending → dispatched → delivered → failed), not
inbound response content. This separation was Gemini's #1 correction
in the B.1 design round (task bridge-b1-schema-design, 2026-04-11).
"""

import sqlite3
from datetime import UTC, datetime
from importlib import util as importlib_util
from pathlib import Path

from ._config import DB_PATH

# ── Schema definitions ─────────────────────────────────────────────────
# Kept at module scope so tests and tooling can import them.

_LEGACY_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    from_llm TEXT NOT NULL,
    to_llm TEXT NOT NULL,
    message_type TEXT DEFAULT 'message',
    content TEXT NOT NULL,
    data TEXT,
    timestamp TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_messages_task_id
    ON messages(task_id, id);
CREATE INDEX IF NOT EXISTS idx_messages_acknowledged
    ON messages(acknowledged, id);
CREATE INDEX IF NOT EXISTS idx_messages_message_type
    ON messages(message_type, id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp
    ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_from_llm
    ON messages(from_llm, id);
CREATE INDEX IF NOT EXISTS idx_messages_to_llm
    ON messages(to_llm, id);

CREATE TABLE IF NOT EXISTS sessions (
    task_id TEXT PRIMARY KEY,
    claude_session_id TEXT,
    gemini_session_id TEXT,
    codex_session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# ── Channel bridge tables (#1190 Phase B.1) ───────────────────────────
#
# Design decisions locked in after Gemini critique:
# 1. BEGIN IMMEDIATE for fanout inserts (queues writers gracefully on
#    the 5000ms busy_timeout instead of deadlocking)
# 2. Replies = new channel_messages rows with parent_id, NOT updates
#    to deliveries — deliveries is strictly an outbound state machine
# 3. thread_id defaults to message_id for originating posts
#    (self-reference → no NULL edge cases in thread queries)
# 4. context_rev_* stored as TEXT sha256 hex (auto-computed, no manual
#    counters to forget, survives git pulls across machines)
# 5. monitor_state_snapshot stays as plain TEXT JSON — debuggable,
#    supports SQLite's json_extract() later
# 6. correlation_id kept separate from thread_id to trace system-level
#    fanout events (e.g. "these N dispatches came from one ab discuss")
_CHANNELS_SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    name TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    description TEXT DEFAULT '',
    include TEXT DEFAULT '',          -- comma-sep channels to auto-include (e.g. "shared")
    subscribers TEXT DEFAULT '',      -- comma-sep agents (e.g. "claude,gemini,codex")
    context_sha256 TEXT DEFAULT '',   -- last-seen sha256 of {channel}/context.md
    max_age_hours INTEGER DEFAULT 24  -- TTL for pending deliveries before auto-expire
);

CREATE TABLE IF NOT EXISTS channel_messages (
    message_id TEXT PRIMARY KEY,          -- uuid4 hex
    channel TEXT NOT NULL,
    thread_id TEXT NOT NULL,              -- defaults to message_id for origins
    parent_id TEXT,                       -- nullable, reply threading
    correlation_id TEXT,                  -- nullable, fanout event ID
    round_index INTEGER DEFAULT 0,        -- 0 = origin, 1+ = replies
    from_agent TEXT NOT NULL,             -- claude/gemini/codex/user
    from_model TEXT,                      -- exact model ID
    kind TEXT DEFAULT 'post',             -- post/reply/system/fanout_start/fanout_end
    priority TEXT DEFAULT 'fyi',          -- fyi/action_required — drives delivery TTL (#4837)
    body TEXT NOT NULL,
    attachments TEXT,                     -- JSON array
    context_rev_shared TEXT,              -- sha256 hex of shared/context.md at post-time
    context_rev_channel TEXT,             -- sha256 hex of {channel}/context.md at post-time
    monitor_state_snapshot TEXT,          -- JSON blob from /api/state/summary
    created_at TEXT NOT NULL,
    FOREIGN KEY (channel) REFERENCES channels(name),
    FOREIGN KEY (parent_id) REFERENCES channel_messages(message_id)
);

CREATE INDEX IF NOT EXISTS idx_channel_messages_channel_time
    ON channel_messages(channel, created_at);
CREATE INDEX IF NOT EXISTS idx_channel_messages_thread
    ON channel_messages(thread_id, round_index);
CREATE INDEX IF NOT EXISTS idx_channel_messages_correlation
    ON channel_messages(correlation_id);
CREATE INDEX IF NOT EXISTS idx_channel_messages_parent
    ON channel_messages(parent_id);

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id TEXT PRIMARY KEY,         -- uuid4 hex
    message_id TEXT NOT NULL,             -- FK → channel_messages.message_id
    to_agent TEXT NOT NULL,               -- claude/gemini/codex
    to_model TEXT,                        -- target model (nullable)
    status TEXT DEFAULT 'pending',        -- pending/processing/dispatched/delivered/failed/expired
    dispatched_at TEXT,
    delivered_at TEXT,
    error TEXT,
    lease_until TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    retry_after TEXT,
    last_error_kind TEXT,
    mode TEXT DEFAULT 'read-only',        -- read-only/workspace-write/danger
    deadline_seconds INTEGER,             -- optional hard-timeout override
    FOREIGN KEY (message_id) REFERENCES channel_messages(message_id)
);

CREATE INDEX IF NOT EXISTS idx_deliveries_message
    ON deliveries(message_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_agent_queue
    ON deliveries(to_agent, status, dispatched_at);
CREATE INDEX IF NOT EXISTS idx_deliveries_claim
    ON deliveries(to_agent, status, retry_after, lease_until);

CREATE TABLE IF NOT EXISTS channel_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id TEXT,                     -- nullable for thread-level events
    thread_id TEXT NOT NULL,
    event TEXT NOT NULL,
    payload_json TEXT,                    -- event-specific JSON payload
    ts TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_channel_events_thread_event
    ON channel_events(thread_id, event_id);
"""


def _tune_connection(conn: sqlite3.Connection) -> None:
    """Apply PRAGMAs needed by both legacy and channel paths.

    WAL mode is essential for the channel bridge: it allows concurrent
    readers while a writer is active, so ``ab p`` and ``ab r`` don't
    block each other. ``busy_timeout`` gives writers up to 5 seconds
    to queue on contended inserts before raising ``SQLITE_BUSY``.

    Row factory is ``sqlite3.Row`` — supports both integer-index access
    (for legacy messages queries that use ``row[0]``) AND dict-style
    access (``row["name"]``) for channel queries. Ported on Gemini's
    B.1 review recommendation (task bridge-b1-review) to eliminate
    tuple-index fragility in the ``_row_to_*`` helpers.
    """
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA cache_size=-20000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.row_factory = sqlite3.Row


def _apply_broker_index_migration(conn: sqlite3.Connection) -> None:
    """Apply the standalone broker-index migration from scripts/migrations."""
    existing_indexes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    }
    existing_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    required_by_table = {
        "messages": {
            "idx_messages_to_agent_created",
            "idx_messages_from_agent_created",
            "idx_messages_task_id",
        },
        "channel_messages": {
            "idx_channel_messages_channel_created",
            "idx_channel_messages_thread_id",
        },
        "deliveries": {"idx_deliveries_to_agent_status"},
    }
    if all(
        required_by_table[table].issubset(existing_indexes)
        for table in required_by_table
        if table in existing_tables
    ):
        return

    migration_path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "2026-05-06-broker-indexes.py"
    )
    if not migration_path.exists():
        return
    spec = importlib_util.spec_from_file_location("broker_indexes_20260506", migration_path)
    if spec is None or spec.loader is None:
        return
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply(conn)


def init_db():
    """Initialize database if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    _tune_connection(conn)
    conn.executescript(_LEGACY_SCHEMA)
    conn.executescript(_CHANNELS_SCHEMA)
    _apply_broker_index_migration(conn)
    conn.commit()
    return conn


def _ensure_legacy_indexes(conn: sqlite3.Connection) -> None:
    """Create legacy message indexes needed by dashboard polling paths."""
    conn.executescript("""
    CREATE INDEX IF NOT EXISTS idx_messages_task_id
        ON messages(task_id, id);
    CREATE INDEX IF NOT EXISTS idx_messages_acknowledged
        ON messages(acknowledged, id);
    CREATE INDEX IF NOT EXISTS idx_messages_message_type
        ON messages(message_type, id);
    CREATE INDEX IF NOT EXISTS idx_messages_timestamp
        ON messages(timestamp);
    CREATE INDEX IF NOT EXISTS idx_messages_from_llm
        ON messages(from_llm, id);
    CREATE INDEX IF NOT EXISTS idx_messages_to_llm
        ON messages(to_llm, id);
    """)


def _add_column_racesafe(conn: sqlite3.Connection, ddl: str) -> None:
    """Run an ``ALTER TABLE ... ADD COLUMN``, tolerating the concurrent-
    migration race (review-4897 F1).

    ``get_db()`` runs its migration block on every bridge operation, and
    multiple agent CLIs regularly open the same messages.db within the
    same second. Two processes can both observe a column as missing and
    both issue the ALTER; SQLite raises ``duplicate column name`` in the
    loser. That outcome means the column now exists — the migration's
    goal — so it is swallowed. Every other OperationalError re-raises.
    """
    try:
        conn.execute(ddl)
    except sqlite3.OperationalError as exc:
        if "duplicate column name" not in str(exc):
            raise


def get_db():
    """Get database connection with auto-migration (#604, #1190)."""
    if not DB_PATH.exists():
        return init_db()
    conn = sqlite3.connect(DB_PATH)
    _tune_connection(conn)

    try:
        cursor = conn.cursor()

        # --- Legacy messages table migration (#604) ---
        cursor.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]
        if not columns:
            # Table doesn't exist yet — create everything from scratch
            conn.executescript(_LEGACY_SCHEMA)
        elif "status" not in columns:
            print("🔧 Migrating database: adding 'status' column to 'messages' table")
            _add_column_racesafe(conn, "ALTER TABLE messages ADD COLUMN status TEXT DEFAULT 'pending'")
        _ensure_legacy_indexes(conn)

        # --- Sessions table migration (#604) ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                task_id TEXT PRIMARY KEY,
                claude_session_id TEXT,
                gemini_session_id TEXT,
                codex_session_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("PRAGMA table_info(sessions)")
        session_columns = [row[1] for row in cursor.fetchall()]
        if "codex_session_id" not in session_columns:
            print("🔧 Migrating database: adding 'codex_session_id' column to 'sessions' table")
            _add_column_racesafe(conn, "ALTER TABLE sessions ADD COLUMN codex_session_id TEXT")

        # --- Channel bridge tables (#1190) ---
        # GATED by table-existence check. Running executescript() on
        # every connection — even with IF NOT EXISTS — parses the DDL
        # and bumps SQLite's schema cookie, which invalidates cached
        # prepared statements across ALL open connections and crashes
        # concurrent readers with "database schema has changed". This
        # was Gemini's #1 blocker in the B.1 adversarial review
        # (task bridge-b1-review). Same mitigation pattern as the
        # legacy messages-table migration above.
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='channels'"
        )
        if not cursor.fetchone():
            conn.executescript(_CHANNELS_SCHEMA)
        else:
            cursor.execute("PRAGMA table_info(channels)")
            channel_columns = [row[1] for row in cursor.fetchall()]
            if "max_age_hours" not in channel_columns:
                _add_column_racesafe(
                    conn, "ALTER TABLE channels ADD COLUMN max_age_hours INTEGER DEFAULT 24"
                )

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='channel_messages'"
            )
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(channel_messages)")
                channel_message_columns = [row[1] for row in cursor.fetchall()]
                if "priority" not in channel_message_columns:
                    _add_column_racesafe(
                        conn, "ALTER TABLE channel_messages ADD COLUMN priority TEXT DEFAULT 'fyi'"
                    )

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='deliveries'"
            )
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(deliveries)")
                delivery_columns = [row[1] for row in cursor.fetchall()]

                if "lease_until" not in delivery_columns:
                    _add_column_racesafe(conn, "ALTER TABLE deliveries ADD COLUMN lease_until TEXT")
                if "attempt_count" not in delivery_columns:
                    _add_column_racesafe(
                        conn, "ALTER TABLE deliveries ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0"
                    )
                if "retry_after" not in delivery_columns:
                    _add_column_racesafe(conn, "ALTER TABLE deliveries ADD COLUMN retry_after TEXT")
                if "last_error_kind" not in delivery_columns:
                    _add_column_racesafe(
                        conn, "ALTER TABLE deliveries ADD COLUMN last_error_kind TEXT"
                    )
                if "deadline_seconds" not in delivery_columns:
                    _add_column_racesafe(
                        conn, "ALTER TABLE deliveries ADD COLUMN deadline_seconds INTEGER"
                    )

                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_deliveries_claim'"
                )
                if not cursor.fetchone():
                    conn.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_deliveries_claim
                        ON deliveries(to_agent, status, retry_after, lease_until)
                        """
                    )

                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='channel_events'"
                )
                if not cursor.fetchone():
                    conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS channel_events (
                            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            delivery_id TEXT,
                            thread_id TEXT NOT NULL,
                            event TEXT NOT NULL,
                            payload_json TEXT,
                            ts TEXT NOT NULL
                        )
                        """
                    )

                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_channel_events_thread_event'"
                )
                if not cursor.fetchone():
                    conn.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_channel_events_thread_event
                        ON channel_events(thread_id, event_id)
                        """
                    )

        _apply_broker_index_migration(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return conn


def get_session(task_id: str) -> dict:
    """Get session IDs for a task."""
    if not task_id:
        return {"claude": None, "gemini": None, "codex": None}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT claude_session_id, gemini_session_id, codex_session_id FROM sessions WHERE task_id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"claude": row[0], "gemini": row[1], "codex": row[2]}
    return {"claude": None, "gemini": None, "codex": None}


# Agents whose sessions are PERSISTED for resumption. These are exactly the
# columns `get_session` reads back.
_SESSION_COLUMNS = {
    "claude": "claude_session_id",
    "gemini": "gemini_session_id",
    "codex": "codex_session_id",
}

# Always-fresh agents (resume_policy="never"): their runs never resume, so their
# session id is intentionally NOT persisted. Listed explicitly so set_session stays
# silent for them while still flagging a genuinely-unknown agent (e.g. a new
# resumable agent whose _SESSION_COLUMNS entry was forgotten — that would otherwise
# silently never persist).
_ALWAYS_FRESH_AGENTS = frozenset(
    {
        "grok",  # canonical native seat
        "grok-build",  # permanent alias — keep dual-READ for set_session
        "grok-hermes",
        "kimi",
        "agy",
        "cursor",
        "hermes",
        "deepseek-v4-pro",
        "qwen",
        "opencode",
        "pool",
        "glm",
    }
)


def _session_column(agent: str) -> str | None:
    """Map a resumable agent to its session column, or None for always-fresh agents."""
    return _SESSION_COLUMNS.get(agent)


def set_session(task_id: str, agent: str, session_id: str):
    """Persist an agent's session id for later resumption.

    No-op for always-fresh agents (those without a session column): their runs
    never resume, so nothing reads the id back. Previously this raised
    ``ValueError: Unknown session agent`` and crashed ``ask-grok-build`` after a
    successful run (grok-build is resume_policy="never" yet returns a session id).
    """
    if not task_id:
        return

    column = _session_column(agent)
    if column is None:
        # No session column => always-fresh agent, nothing to persist. Stay silent
        # for the known set; warn for a genuinely-unknown agent so a forgotten
        # _SESSION_COLUMNS entry doesn't fail silently.
        if agent not in _ALWAYS_FRESH_AGENTS:
            print(
                f"⚠️  set_session: no session column for agent '{agent}'; not persisting. "
                "Add it to _SESSION_COLUMNS (resumable) or _ALWAYS_FRESH_AGENTS (always-fresh)."
            )
        return

    conn = get_db()
    cursor = conn.cursor()
    timestamp = datetime.now(UTC).isoformat()

    # Upsert session
    cursor.execute("SELECT task_id FROM sessions WHERE task_id = ?", (task_id,))
    if cursor.fetchone():
        cursor.execute(
            f"UPDATE sessions SET {column} = ?, updated_at = ? WHERE task_id = ?",
            (session_id, timestamp, task_id),
        )
    else:
        cursor.execute(
            f"INSERT INTO sessions (task_id, {column}, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (task_id, session_id, timestamp, timestamp),
        )

    conn.commit()
    conn.close()
    print(f"📌 Stored {agent} session: {session_id[:8]}... for task {task_id}")
