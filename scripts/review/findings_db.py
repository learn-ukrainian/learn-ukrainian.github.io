"""The review findings database (#8430 r4, R2b-A): one SQLite file per level.

``batch_state/review-findings/<level>.sqlite``, tables ``attempts``, ``findings``,
``budgets``, ``settle_items``, ``agreement``, the measurement tables ``seed_results``,
``clean_results`` and ``seed_identities`` (R3), and ``schema_version``, created with
``CREATE TABLE IF NOT EXISTS``. The record is lossless: an attempt keeps the
validator's rejection codes and the dispatch's task id, a finding keeps every
receipt it cites and the whole finding as the reviewer returned it.

``schema_version`` is checked on every open. A file at ``SCHEMA_VERSION`` opens as is. A file at
a version listed in ``MIGRATIONS`` (today: 2) is upgraded in one transaction that only adds tables,
so every existing row is kept; a file at any other version, or with tables and no version, is
refused, never guessed at.

Unrelated to ``scripts/review/findings.py`` (the closeout code-review ledger).

A settle item is **open** while ``outcome IS NULL``. An item the settle seat closed as
``source_conflict`` or ``unresolved`` is marked ``needs_operator`` and still holds the
module until the operator's decision is recorded (``operator_decided_at``). An item whose lesson
was reviewed again on a newer manifest is closed by ``record`` as ``moot_superseded`` (the
superseding attempt is kept in ``superseded_by``); it is not a settle decision and holds nothing.

The database is the source of truth. ``attempts.seq`` is a monotonic sequence (never reused: the
column is AUTOINCREMENT), and "latest" always means the highest ``seq``, never wall time. The
verdict files the landing reads are projections of :func:`latest_accepted`.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.common.repo_root import main_checkout_root

REPO_ROOT = Path(__file__).resolve().parents[2]
PARAMETERS_PATH = REPO_ROOT / "scripts" / "config" / "review_parameters.yaml"
SCHEMA_VERSION = 3
DB_DIRECTORY = ("batch_state", "review-findings")
LEVEL_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,31}\Z")

VERDICTS = ("APPROVE", "REVISE", "REJECTED", "FAILED")
ROLES = ("first", "second")
SETTLE_KINDS = ("unsupported_by_source", "second_seat_disagreement")
MOOT_SUPERSEDED = "moot_superseded"
SEAT_OUTCOMES = ("supported_defect", "refuted", "source_conflict", "unresolved")  # what the settle seat may decide
SETTLE_OUTCOMES = (*SEAT_OUTCOMES, MOOT_SUPERSEDED)  # ``moot_superseded`` is written only by ``record``
OPERATOR_OUTCOMES = frozenset({"source_conflict", "unresolved"})
BUDGET_FIELDS = ("revise_rounds", "regenerations", "review_failures")
PLAN_LESSON_N = 0  # the budgets row of a module's plan review

_TABLES = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS attempts (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('plan', 'lesson')),
    level TEXT NOT NULL,
    slug TEXT NOT NULL,
    lesson_n INTEGER,
    manifest_sha256 TEXT NOT NULL,
    reviewer_model TEXT NOT NULL,
    reviewer_family TEXT NOT NULL,
    harness TEXT NOT NULL,
    prompt_sha256 TEXT,
    verdict TEXT NOT NULL CHECK (verdict IN ('APPROVE', 'REVISE', 'REJECTED', 'FAILED')),
    validated_at TEXT NOT NULL,
    rejection_codes_json TEXT,
    task_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'first' CHECK (role IN ('first', 'second')),
    seed_id TEXT,
    writer_family TEXT,
    return_sha256 TEXT,
    failure_reason TEXT,
    UNIQUE (review_id, attempt_id)
);
CREATE TABLE IF NOT EXISTS findings (
    review_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    status TEXT NOT NULL,
    dimension TEXT NOT NULL,
    sub_dimension TEXT,
    severity TEXT NOT NULL,
    claim TEXT NOT NULL,
    evidence_kind TEXT NOT NULL CHECK (evidence_kind IN ('evidence', 'unsupported_by_source', 'source_conflict')),
    receipts_json TEXT NOT NULL,
    locations_json TEXT NOT NULL,
    could_be_a_gate TEXT,
    layer TEXT,
    seed_id TEXT,
    finding_json TEXT NOT NULL,
    PRIMARY KEY (review_id, attempt_id, finding_id),
    FOREIGN KEY (review_id, attempt_id) REFERENCES attempts (review_id, attempt_id)
);
CREATE TABLE IF NOT EXISTS budgets (
    level TEXT NOT NULL,
    slug TEXT NOT NULL,
    lesson_n INTEGER NOT NULL,
    revise_rounds INTEGER NOT NULL DEFAULT 0,
    regenerations INTEGER NOT NULL DEFAULT 0,
    review_failures INTEGER NOT NULL DEFAULT 0,
    disputed TEXT,
    PRIMARY KEY (level, slug, lesson_n)
);
CREATE TABLE IF NOT EXISTS settle_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_ref TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('unsupported_by_source', 'second_seat_disagreement')),
    level TEXT NOT NULL,
    slug TEXT NOT NULL,
    lesson_n INTEGER,
    manifest_sha256 TEXT,
    opened_at TEXT NOT NULL,
    outcome TEXT CHECK (outcome IS NULL OR outcome IN
        ('supported_defect', 'refuted', 'source_conflict', 'unresolved', 'moot_superseded')),
    receipts_json TEXT,
    decided_by TEXT,
    decided_at TEXT,
    needs_operator INTEGER NOT NULL DEFAULT 0,
    operator_decision TEXT,
    operator_decided_at TEXT,
    superseded_by TEXT,
    UNIQUE (finding_ref, kind)
);
CREATE TABLE IF NOT EXISTS agreement (
    level TEXT NOT NULL,
    slug TEXT NOT NULL,
    lesson_n INTEGER NOT NULL,
    attempt_a TEXT NOT NULL,
    attempt_b TEXT NOT NULL,
    agreed INTEGER NOT NULL CHECK (agreed IN (0, 1)),
    disagreed_json TEXT NOT NULL,
    PRIMARY KEY (level, slug, lesson_n, attempt_a, attempt_b)
);
"""

# Added by the migration from version 2 (R3): the measurement tables. Nothing above changes.
_TABLES_V3 = """
CREATE TABLE IF NOT EXISTS seed_identities (
    seed_id TEXT PRIMARY KEY,
    writer_family TEXT NOT NULL,
    planter_model TEXT,
    planter_family TEXT,
    gold_checker_model TEXT,
    gold_checker_family TEXT,
    gold_verdict TEXT NOT NULL CHECK (gold_verdict IN ('pass', 'fail', 'not_applicable'))
);
CREATE TABLE IF NOT EXISTS seed_results (
    seed_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    planted_found INTEGER NOT NULL CHECK (planted_found IN (0, 1)),
    planted_blocking INTEGER NOT NULL CHECK (planted_blocking IN (0, 1)),
    mapping_json TEXT NOT NULL,
    adjudicator_model TEXT NOT NULL,
    adjudicator_family TEXT NOT NULL,
    PRIMARY KEY (review_id, attempt_id),
    FOREIGN KEY (review_id, attempt_id) REFERENCES attempts (review_id, attempt_id)
);
CREATE TABLE IF NOT EXISTS clean_results (
    clean_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    false_findings INTEGER NOT NULL CHECK (false_findings >= 0),
    falsely_blocked INTEGER NOT NULL CHECK (falsely_blocked IN (0, 1)),
    mapping_json TEXT NOT NULL,
    adjudicator_model TEXT NOT NULL,
    adjudicator_family TEXT NOT NULL,
    PRIMARY KEY (review_id, attempt_id),
    FOREIGN KEY (review_id, attempt_id) REFERENCES attempts (review_id, attempt_id)
);
"""
_TABLE_NAMES = (
    "attempts",
    "findings",
    "budgets",
    "settle_items",
    "agreement",
    "seed_results",
    "clean_results",
    "seed_identities",
)


class FindingsDbError(Exception):
    """The database cannot be opened or written safely."""


class VersionMismatch(FindingsDbError):
    """The file's schema_version is not the one this code writes."""


class SettleAlreadyDecided(FindingsDbError):
    """A settle item takes exactly one outcome; a second one is refused."""


def now_iso(moment: datetime | None = None) -> str:
    return (moment or datetime.now(UTC)).astimezone(UTC).isoformat(timespec="seconds")


def batch_root(repo_root: Path | None = None) -> Path:
    """Where ``batch_state`` lives: the primary checkout, never a worktree copy."""
    return main_checkout_root(Path(repo_root if repo_root is not None else REPO_ROOT).resolve())


def db_path(level: str, repo_root: Path | None = None) -> Path:
    if not LEVEL_RE.fullmatch(level):
        raise FindingsDbError(f"level {level!r} is not a level token")
    return batch_root(repo_root).joinpath(*DB_DIRECTORY, f"{level}.sqlite")


def connect(path: Path) -> sqlite3.Connection:
    """Open (creating when new) the database at ``path``; refuse a foreign schema_version.

    The connection is in autocommit mode: writers use :func:`transaction`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        _ensure_schema(conn, path)
    except BaseException:
        conn.close()
        raise
    return conn


_V3_TABLE_NAMES = ("seed_results", "clean_results", "seed_identities")


def _statements(script: str) -> list[str]:
    return [statement for statement in script.split(";") if statement.strip()]


def _migrate_2_to_3(conn: sqlite3.Connection, tables: set[str]) -> None:
    """Version 2 to 3: add the three measurement tables. Existing tables are not touched, so no row moves."""
    present = sorted(tables & set(_V3_TABLE_NAMES))
    if present:
        raise VersionMismatch(f"a version 2 database already has {present}; refusing to guess what they hold")
    for statement in _statements(_TABLES_V3):
        conn.execute(statement)


# from schema_version -> the function that upgrades a file at that version to the next one
MIGRATIONS: dict[int, Callable[[sqlite3.Connection, set[str]], None]] = {2: _migrate_2_to_3}


def _ensure_schema(conn: sqlite3.Connection, path: Path) -> None:
    """Create the schema, or bring an older known version up to ``SCHEMA_VERSION``, or refuse.

    One ``BEGIN IMMEDIATE`` transaction holds the write lock from the version check to the last change,
    so two processes opening an old file cannot both migrate it and a refused file is never touched.
    """
    with transaction(conn):
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "schema_version" not in tables:
            if tables & set(_TABLE_NAMES):
                raise VersionMismatch(f"{path}: tables exist without a schema_version; refusing to open it")
            for statement in (*_statements(_TABLES), *_statements(_TABLES_V3)):
                conn.execute(statement)
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            return
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_version")]
        if len(versions) != 1 or (versions[0] != SCHEMA_VERSION and versions[0] not in MIGRATIONS):
            raise VersionMismatch(
                f"{path}: schema_version {versions} is not {SCHEMA_VERSION} (or a version that migrates to it: "
                f"{sorted(MIGRATIONS)}); refusing to open it"
            )
        version = versions[0]
        while version != SCHEMA_VERSION:
            MIGRATIONS[version](conn, tables)
            version += 1
            conn.execute("UPDATE schema_version SET version = ?", (version,))
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# --- attempts and findings ----------------------------------------------------------------

_ATTEMPT_COLUMNS = (
    "review_id",
    "attempt_id",
    "kind",
    "level",
    "slug",
    "lesson_n",
    "manifest_sha256",
    "reviewer_model",
    "reviewer_family",
    "harness",
    "prompt_sha256",
    "verdict",
    "validated_at",
    "rejection_codes_json",
    "task_id",
    "role",
    "seed_id",
    "writer_family",
    "return_sha256",
    "failure_reason",
)


def get_attempt(conn: sqlite3.Connection, review_id: str, attempt_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM attempts WHERE review_id = ? AND attempt_id = ?", (review_id, attempt_id)
    ).fetchone()


def insert_attempt(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    values = {column: row.get(column) for column in _ATTEMPT_COLUMNS}
    values["role"] = values["role"] or "first"
    conn.execute(
        f"INSERT INTO attempts ({', '.join(_ATTEMPT_COLUMNS)}) VALUES ({', '.join('?' for _ in _ATTEMPT_COLUMNS)})",
        tuple(values[column] for column in _ATTEMPT_COLUMNS),
    )


def finding_ref(review_id: str, attempt_id: str, finding_id: str) -> str:
    return f"{review_id}/{attempt_id}/{finding_id}"


def evidence_kind(finding: dict[str, Any]) -> str:
    for key in ("evidence", "unsupported_by_source", "source_conflict"):
        if key in finding:
            return key
    raise FindingsDbError(f"finding {finding.get('id')!r} carries no evidence branch")


def cited_receipts(finding: dict[str, Any]) -> list[str]:
    """Every receipt id a finding cites, in the order the finding lists them."""
    kind = evidence_kind(finding)
    branch = finding[kind]
    if kind == "evidence":
        return [branch["receipt"]]
    if kind == "source_conflict":
        return [branch["a"]["receipt"], branch["b"]["receipt"]]
    return [search["receipt"] for search in branch["searches"]]


def insert_finding(
    conn: sqlite3.Connection,
    review_id: str,
    attempt_id: str,
    finding: dict[str, Any],
    *,
    layer: str | None,
    seed_id: str | None,
) -> None:
    conn.execute(
        "INSERT INTO findings (review_id, attempt_id, finding_id, status, dimension, sub_dimension, severity, claim,"
        " evidence_kind, receipts_json, locations_json, could_be_a_gate, layer, seed_id, finding_json)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            review_id,
            attempt_id,
            finding["id"],
            finding["status"],
            finding["dimension"],
            finding.get("sub_dimension"),
            finding["severity"],
            finding["claim"],
            evidence_kind(finding),
            dumps(cited_receipts(finding)),
            dumps(finding.get("locations", [])),
            finding.get("could_be_a_gate"),
            layer,
            seed_id,
            dumps(finding),
        ),
    )


def count_findings(conn: sqlite3.Connection, review_id: str, attempt_id: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM findings WHERE review_id = ? AND attempt_id = ?", (review_id, attempt_id)
    ).fetchone()[0]


def module_attempts(
    conn: sqlite3.Connection,
    level: str,
    slug: str,
    *,
    role: str | None = "first",
    verdicts: tuple[str, ...] = ("APPROVE", "REVISE"),
) -> list[sqlite3.Row]:
    """Accepted, non-seeded attempts of a module in recording order (seeded lessons never reach the loop)."""
    marks = ", ".join("?" for _ in verdicts)
    query = f"SELECT * FROM attempts WHERE level = ? AND slug = ? AND seed_id IS NULL AND verdict IN ({marks})"
    args: list[Any] = [level, slug, *verdicts]
    if role is not None:
        query += " AND role = ?"
        args.append(role)
    return conn.execute(query + " ORDER BY seq", args).fetchall()


def latest_accepted(
    conn: sqlite3.Connection, level: str, slug: str, kind: str, lesson_n: int | None
) -> sqlite3.Row | None:
    """The latest accepted first-seat, non-seeded attempt for one manifest target (a lesson, or the plan).

    "Latest" is the highest ``seq``. The verdict file of the target is a projection of this row.
    """
    return conn.execute(
        "SELECT * FROM attempts WHERE level = ? AND slug = ? AND kind = ? AND lesson_n IS ? AND role = 'first'"
        " AND seed_id IS NULL AND verdict IN ('APPROVE', 'REVISE') ORDER BY seq DESC LIMIT 1",
        (level, slug, kind, lesson_n),
    ).fetchone()


def accepted_attempt_on(
    conn: sqlite3.Connection, level: str, slug: str, kind: str, lesson_n: int | None, manifest_sha256: str
) -> sqlite3.Row | None:
    """The latest accepted first-seat, non-seeded attempt of the target that reviewed exactly ``manifest_sha256``."""
    return conn.execute(
        "SELECT * FROM attempts WHERE level = ? AND slug = ? AND kind = ? AND lesson_n IS ? AND role = 'first'"
        " AND seed_id IS NULL AND verdict IN ('APPROVE', 'REVISE') AND manifest_sha256 = ? ORDER BY seq DESC LIMIT 1",
        (level, slug, kind, lesson_n, manifest_sha256),
    ).fetchone()


def module_findings(conn: sqlite3.Connection, level: str, slug: str) -> list[sqlite3.Row]:
    """Findings of every accepted, non-seeded first-seat attempt of the module, with the attempt's lesson."""
    return conn.execute(
        "SELECT f.*, a.lesson_n AS lesson_n, a.kind AS kind, a.manifest_sha256 AS manifest_sha256,"
        " a.role AS role, a.level AS level, a.slug AS slug"
        " FROM findings f JOIN attempts a ON a.review_id = f.review_id AND a.attempt_id = f.attempt_id"
        " WHERE a.level = ? AND a.slug = ? AND a.seed_id IS NULL AND a.verdict IN ('APPROVE', 'REVISE')"
        " AND a.role = 'first' ORDER BY a.seq, f.rowid",
        (level, slug),
    ).fetchall()


# --- budgets ----------------------------------------------------------------------------


def bump_budget(conn: sqlite3.Connection, level: str, slug: str, lesson_n: int, field: str) -> int:
    """Add one to a counter of the ``(level, slug, lesson_n)`` row and return its new value."""
    if field not in BUDGET_FIELDS:
        raise FindingsDbError(f"unknown budget field {field!r}")
    conn.execute("INSERT OR IGNORE INTO budgets (level, slug, lesson_n) VALUES (?, ?, ?)", (level, slug, lesson_n))
    conn.execute(
        f"UPDATE budgets SET {field} = {field} + 1 WHERE level = ? AND slug = ? AND lesson_n = ?",
        (level, slug, lesson_n),
    )
    return conn.execute(
        f"SELECT {field} FROM budgets WHERE level = ? AND slug = ? AND lesson_n = ?", (level, slug, lesson_n)
    ).fetchone()[0]


def module_budgets(conn: sqlite3.Connection, level: str, slug: str) -> dict[int, dict[str, Any]]:
    """The budget rows of a module by lesson number (0 is the plan review); absent rows are all zero."""
    rows = conn.execute(
        "SELECT * FROM budgets WHERE level = ? AND slug = ? ORDER BY lesson_n", (level, slug)
    ).fetchall()
    return {row["lesson_n"]: {name: row[name] for name in (*BUDGET_FIELDS, "disputed")} for row in rows}


def mark_disputed(conn: sqlite3.Connection, level: str, slug: str, lesson_n: int, reason: str) -> None:
    conn.execute("INSERT OR IGNORE INTO budgets (level, slug, lesson_n) VALUES (?, ?, ?)", (level, slug, lesson_n))
    conn.execute(
        "UPDATE budgets SET disputed = ? WHERE level = ? AND slug = ? AND lesson_n = ?", (reason, level, slug, lesson_n)
    )


# --- settle items -----------------------------------------------------------------------


def open_settle_item(
    conn: sqlite3.Connection,
    *,
    ref: str,
    kind: str,
    level: str,
    slug: str,
    lesson_n: int | None,
    manifest_sha256: str | None,
    opened_at: str,
) -> int:
    """Open the one settle item of a finding; a finding that already has one keeps it."""
    if kind not in SETTLE_KINDS:
        raise FindingsDbError(f"unknown settle item kind {kind!r}")
    conn.execute(
        "INSERT OR IGNORE INTO settle_items (finding_ref, kind, level, slug, lesson_n, manifest_sha256, opened_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ref, kind, level, slug, lesson_n, manifest_sha256, opened_at),
    )
    return conn.execute("SELECT item_id FROM settle_items WHERE finding_ref = ? AND kind = ?", (ref, kind)).fetchone()[
        0
    ]


def record_settle_outcome(
    conn: sqlite3.Connection,
    item_id: int,
    outcome: str,
    receipts: list[str],
    decided_by: str,
    *,
    decided_at: str | None = None,
) -> None:
    """Close an open item with one outcome. ``source_conflict`` and ``unresolved`` mark it for the operator.

    Raises SettleAlreadyDecided when the item has an outcome already: there is no second round.
    """
    if outcome not in SEAT_OUTCOMES:
        raise FindingsDbError(f"unknown settle outcome {outcome!r}")
    with transaction(conn):
        changed = conn.execute(
            "UPDATE settle_items SET outcome = ?, receipts_json = ?, decided_by = ?, decided_at = ?, needs_operator = ?"
            " WHERE item_id = ? AND outcome IS NULL",
            (outcome, dumps(receipts), decided_by, decided_at or now_iso(), int(outcome in OPERATOR_OUTCOMES), item_id),
        ).rowcount
        if not changed:
            exists = conn.execute("SELECT 1 FROM settle_items WHERE item_id = ?", (item_id,)).fetchone()
            raise (
                SettleAlreadyDecided(f"settle item {item_id} is already decided")
                if exists
                else FindingsDbError(f"no settle item {item_id}")
            )


def record_operator_decision(
    conn: sqlite3.Connection, item_id: int, decision: str, *, decided_at: str | None = None
) -> None:
    """The operator's decision on an item the settle seat sent to them; it releases the module's hold."""
    with transaction(conn):
        changed = conn.execute(
            "UPDATE settle_items SET operator_decision = ?, operator_decided_at = ?"
            " WHERE item_id = ? AND needs_operator = 1 AND operator_decided_at IS NULL",
            (decision, decided_at or now_iso(), item_id),
        ).rowcount
        if not changed:
            raise FindingsDbError(f"settle item {item_id} is not waiting for the operator")


def module_settle_items(conn: sqlite3.Connection, level: str, slug: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM settle_items WHERE level = ? AND slug = ? ORDER BY item_id", (level, slug)
    ).fetchall()


def close_superseded_items(
    conn: sqlite3.Connection,
    *,
    level: str,
    slug: str,
    lesson_n: int | None,
    current_manifest_sha256: str,
    superseded_by: str,
    decided_at: str,
) -> list[int]:
    """Close, as ``moot_superseded``, every open item of the target raised against an older manifest.

    Runs inside the caller's transaction, when an attempt on ``current_manifest_sha256`` is accepted. The
    item's claim is about a manifest that is no longer the target's current one, so it holds nothing;
    a claim the new attempt raises again opens its own item on the new manifest. Returns the item ids.
    """
    rows = conn.execute(
        "SELECT item_id FROM settle_items WHERE level = ? AND slug = ? AND lesson_n IS ? AND outcome IS NULL"
        " AND manifest_sha256 IS NOT ? ORDER BY item_id",
        (level, slug, lesson_n, current_manifest_sha256),
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE settle_items SET outcome = ?, decided_by = 'record', decided_at = ?, needs_operator = 0,"
            " receipts_json = '[]', superseded_by = ? WHERE item_id = ?",
            (MOOT_SUPERSEDED, decided_at, superseded_by, row["item_id"]),
        )
    return [row["item_id"] for row in rows]


def is_open(item: sqlite3.Row) -> bool:
    return item["outcome"] is None


def is_waiting_for_operator(item: sqlite3.Row) -> bool:
    return item["outcome"] is not None and bool(item["needs_operator"]) and item["operator_decided_at"] is None


# --- agreement --------------------------------------------------------------------------


def insert_agreement(
    conn: sqlite3.Connection,
    *,
    level: str,
    slug: str,
    lesson_n: int,
    attempt_a: str,
    attempt_b: str,
    agreed: bool,
    disagreed: list[dict[str, Any]],
) -> None:
    conn.execute(
        "INSERT INTO agreement (level, slug, lesson_n, attempt_a, attempt_b, agreed, disagreed_json)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (level, slug, lesson_n, attempt_a, attempt_b, int(agreed), dumps(disagreed)),
    )


def has_agreement_on(conn: sqlite3.Connection, level: str, slug: str, lesson_n: int, manifest_sha256: str) -> bool:
    """Whether a second-seat comparison exists whose first-seat attempt reviewed exactly ``manifest_sha256``."""
    return (
        conn.execute(
            "SELECT 1 FROM agreement g JOIN attempts a ON a.attempt_id = g.attempt_a AND a.level = g.level"
            " AND a.slug = g.slug AND a.lesson_n = g.lesson_n"
            " WHERE g.level = ? AND g.slug = ? AND g.lesson_n = ? AND a.role = 'first' AND a.manifest_sha256 = ?"
            " LIMIT 1",
            (level, slug, lesson_n, manifest_sha256),
        ).fetchone()
        is not None
    )


# --- measurement (R3): identities, adjudicated results ------------------------------------------

_SEED_IDENTITY_COLUMNS = (
    "seed_id",
    "writer_family",
    "planter_model",
    "planter_family",
    "gold_checker_model",
    "gold_checker_family",
    "gold_verdict",
)


def get_seed_identity(conn: sqlite3.Connection, seed_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM seed_identities WHERE seed_id = ?", (seed_id,)).fetchone()


def record_seed_identity(conn: sqlite3.Connection, identity: dict[str, Any]) -> bool:
    """Write the identities a seed was planted under; True when the row is new.

    A seed's identities are facts of how it was made and never change: a second write with different
    values is refused, the same values again change nothing.
    """
    values = {column: identity.get(column) for column in _SEED_IDENTITY_COLUMNS}
    existing = get_seed_identity(conn, values["seed_id"])
    if existing is not None:
        if {column: existing[column] for column in _SEED_IDENTITY_COLUMNS} != values:
            raise FindingsDbError(f"seed {values['seed_id']} is already recorded with different identities")
        return False
    conn.execute(
        f"INSERT INTO seed_identities ({', '.join(_SEED_IDENTITY_COLUMNS)})"
        f" VALUES ({', '.join('?' for _ in _SEED_IDENTITY_COLUMNS)})",
        tuple(values[column] for column in _SEED_IDENTITY_COLUMNS),
    )
    return True


def attempt_findings(conn: sqlite3.Connection, review_id: str, attempt_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM findings WHERE review_id = ? AND attempt_id = ? ORDER BY rowid", (review_id, attempt_id)
    ).fetchall()


def measurement_attempts(conn: sqlite3.Connection, unit_id: str) -> list[sqlite3.Row]:
    """Every first-seat attempt on a seeded or clean measurement lesson, in recording order (``seq``)."""
    return conn.execute(
        "SELECT * FROM attempts WHERE seed_id = ? AND role = 'first' ORDER BY seq", (unit_id,)
    ).fetchall()


def get_seed_result(conn: sqlite3.Connection, review_id: str, attempt_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM seed_results WHERE review_id = ? AND attempt_id = ?", (review_id, attempt_id)
    ).fetchone()


def get_clean_result(conn: sqlite3.Connection, review_id: str, attempt_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM clean_results WHERE review_id = ? AND attempt_id = ?", (review_id, attempt_id)
    ).fetchone()


def insert_seed_result(
    conn: sqlite3.Connection,
    *,
    seed_id: str,
    review_id: str,
    attempt_id: str,
    planted_found: bool,
    planted_blocking: bool,
    mapping: list[dict[str, Any]],
    adjudicator_model: str,
    adjudicator_family: str,
) -> None:
    conn.execute(
        "INSERT INTO seed_results (seed_id, review_id, attempt_id, planted_found, planted_blocking, mapping_json,"
        " adjudicator_model, adjudicator_family) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            seed_id,
            review_id,
            attempt_id,
            int(planted_found),
            int(planted_blocking),
            dumps(mapping),
            adjudicator_model,
            adjudicator_family,
        ),
    )


def insert_clean_result(
    conn: sqlite3.Connection,
    *,
    clean_id: str,
    review_id: str,
    attempt_id: str,
    false_findings: int,
    falsely_blocked: bool,
    mapping: list[dict[str, Any]],
    adjudicator_model: str,
    adjudicator_family: str,
) -> None:
    conn.execute(
        "INSERT INTO clean_results (clean_id, review_id, attempt_id, false_findings, falsely_blocked, mapping_json,"
        " adjudicator_model, adjudicator_family) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            clean_id,
            review_id,
            attempt_id,
            false_findings,
            int(falsely_blocked),
            dumps(mapping),
            adjudicator_model,
            adjudicator_family,
        ),
    )


# --- parameters -------------------------------------------------------------------------

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
# Positive integers. The first six are the R2b keys every existing caller reads; they keep their names and values.
_INT_PARAMETERS = (
    "second_seat_divisor",
    "max_revise_rounds",
    "regeneration_factor",
    "review_failures_terminal_at",
    "unsupported_claim_lessons_to_operator",
    "settle_call_budget",
    "min_planted_per_dimension",
    "min_clean_lessons",
    "rolling_one_in",
    "interval_confidence_percent",
)
# Strings drawn from the methods the scorer implements; any other value is refused, never silently ignored.
_CHOICE_PARAMETERS: dict[str, frozenset[str]] = {
    "interval_method_proportion": frozenset({"wilson"}),
    "interval_method_rate": frozenset({"poisson_exact"}),
    "paired_test": frozenset({"mcnemar_exact"}),
}
_PATTERN_PARAMETERS = ("gate_candidate_pattern",)
# Numbers that stay null until the operator writes them: a fraction in (0, 1], or null.
_NULLABLE_FRACTION_PARAMETERS = ("admission_threshold",)
_MAX_CONFIDENCE_PERCENT = 99


def _check_entry(name: str, entry: Any) -> Any:
    if not isinstance(entry, dict) or set(entry) != {"value", "decided", "basis"}:
        raise FindingsDbError(f"review_parameters.yaml: {name} must be {{value, decided, basis}}")
    if not isinstance(entry["decided"], str) or not _DATE_RE.fullmatch(entry["decided"]):
        raise FindingsDbError(f"review_parameters.yaml: {name}.decided must be a YYYY-MM-DD date string")
    if not isinstance(entry["basis"], str) or not entry["basis"].strip():
        raise FindingsDbError(f"review_parameters.yaml: {name}.basis is empty")
    return entry["value"]


def load_parameters(path: Path | None = None) -> dict[str, Any]:
    """The review parameters by name (values only), validated: each has a decision date and basis.

    Typed: positive integers (``_INT_PARAMETERS``, the R2b keys unchanged), strings from a fixed set of
    methods, a regular expression, and nullable fractions (``admission_threshold``: ``None`` until the operator
    writes it; a caller that needs it refuses to run while it is ``None``).
    """
    document = yaml.safe_load(Path(path or PARAMETERS_PATH).read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("parameters_schema") != 1:
        raise FindingsDbError("review_parameters.yaml: parameters_schema must be 1")
    values: dict[str, Any] = {}
    for name in (*_INT_PARAMETERS, *_CHOICE_PARAMETERS, *_PATTERN_PARAMETERS, *_NULLABLE_FRACTION_PARAMETERS):
        value = _check_entry(name, document.get(name))
        if name in _INT_PARAMETERS and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
            raise FindingsDbError(f"review_parameters.yaml: {name}.value must be a positive integer")
        if name == "interval_confidence_percent" and value > _MAX_CONFIDENCE_PERCENT:
            raise FindingsDbError(f"review_parameters.yaml: {name}.value must be at most {_MAX_CONFIDENCE_PERCENT}")
        if name in _CHOICE_PARAMETERS and value not in _CHOICE_PARAMETERS[name]:
            raise FindingsDbError(
                f"review_parameters.yaml: {name}.value must be one of {sorted(_CHOICE_PARAMETERS[name])}"
            )
        if name in _PATTERN_PARAMETERS:
            try:
                re.compile(value)
            except (re.error, TypeError) as error:
                raise FindingsDbError(f"review_parameters.yaml: {name}.value is not a regular expression") from error
        if (
            name in _NULLABLE_FRACTION_PARAMETERS
            and value is not None
            and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 1)
        ):
            raise FindingsDbError(f"review_parameters.yaml: {name}.value must be null or a fraction in (0, 1]")
        values[name] = value
    return values
