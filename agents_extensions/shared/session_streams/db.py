"""SQLite connection, migration, and canonical-path management."""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .model import isoformat_z, utc_now

DEFAULT_RELATIVE_DATABASE = Path(".agent/session-streams/v1/session-streams.sqlite3")
MIGRATIONS_DIR = Path(__file__).with_name("migrations")
BUSY_TIMEOUT_MS = 5_000


class SessionStreamDatabaseError(RuntimeError):
    """Base error for a database that cannot safely serve session streams."""


class MigrationError(SessionStreamDatabaseError):
    """Raised when a schema receipt or migration is inconsistent."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str
    sha256: str


def canonical_state_root(repo_root: Path | None = None) -> Path:
    """Resolve the primary checkout shared by every linked worktree."""
    active_root = (repo_root or Path.cwd()).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=active_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    common_dir_text = result.stdout.strip()
    if result.returncode != 0 or not common_dir_text:
        detail = result.stderr.strip() or "git did not report a common directory"
        raise SessionStreamDatabaseError(f"cannot resolve canonical state root: {detail}")
    common_dir = Path(common_dir_text)
    if not common_dir.is_absolute() or common_dir.name != ".git":
        raise SessionStreamDatabaseError(
            f"cannot derive primary checkout from Git common directory: {common_dir_text!r}"
        )
    return common_dir.parent.resolve()


def default_database_path(repo_root: Path | None = None) -> Path:
    return canonical_state_root(repo_root) / DEFAULT_RELATIVE_DATABASE


def load_migrations() -> tuple[Migration, ...]:
    migrations: list[Migration] = []
    for path in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        prefix, _, _ = path.name.partition("_")
        version = int(prefix)
        sql = path.read_text(encoding="utf-8")
        migrations.append(
            Migration(
                version=version,
                name=path.name,
                sql=sql,
                sha256=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            )
        )
    if not migrations:
        raise MigrationError(f"no session-stream migrations found under {MIGRATIONS_DIR}")
    versions = [migration.version for migration in migrations]
    if versions != list(range(1, len(versions) + 1)):
        raise MigrationError(f"migration versions must be contiguous from 1; got {versions}")
    return tuple(migrations)


class SessionStreamDatabase:
    """Open configured SQLite connections and verify forward-only migrations."""

    def __init__(self, path: Path | str | None = None, *, repo_root: Path | None = None) -> None:
        self.path = Path(path).resolve() if path is not None else default_database_path(repo_root)

    def connect(self, *, read_only: bool = False, now: datetime | None = None) -> sqlite3.Connection:
        if read_only:
            if not self.path.is_file():
                raise SessionStreamDatabaseError(f"session-stream database does not exist: {self.path}")
            connection = sqlite3.connect(
                f"file:{self.path}?mode=ro",
                uri=True,
                isolation_level=None,
                timeout=BUSY_TIMEOUT_MS / 1000,
            )
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(
                self.path,
                isolation_level=None,
                timeout=BUSY_TIMEOUT_MS / 1000,
            )
        connection.row_factory = sqlite3.Row
        try:
            self._configure(connection, read_only=read_only)
            if read_only:
                self._verify_migrations(connection)
                connection.execute("PRAGMA query_only = ON")
            else:
                self._apply_migrations(connection, now=now or utc_now())
            return connection
        except Exception:
            connection.close()
            raise

    @staticmethod
    def _configure(connection: sqlite3.Connection, *, read_only: bool) -> None:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        connection.execute("PRAGMA synchronous = FULL")
        if not read_only:
            journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower()
            if journal_mode != "wal":
                raise SessionStreamDatabaseError(f"WAL mode required, SQLite returned {journal_mode!r}")
        foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        if foreign_keys != 1:
            raise SessionStreamDatabaseError("foreign_keys pragma did not remain enabled")
        if synchronous != 2:
            raise SessionStreamDatabaseError(f"FULL synchronous mode required, SQLite returned {synchronous}")

    @staticmethod
    def _has_migration_table(connection: sqlite3.Connection) -> bool:
        return (
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
            ).fetchone()
            is not None
        )

    @staticmethod
    def _non_internal_tables(connection: sqlite3.Connection) -> list[str]:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [str(row[0]) for row in rows]

    def _apply_migrations(self, connection: sqlite3.Connection, *, now: datetime) -> None:
        migrations = load_migrations()
        connection.execute("BEGIN IMMEDIATE")
        try:
            if not self._has_migration_table(connection):
                unexpected_tables = self._non_internal_tables(connection)
                if unexpected_tables:
                    raise MigrationError(
                        "refusing to initialize an unmanaged non-empty database: "
                        + ", ".join(unexpected_tables)
                    )
                self._apply_one_locked(connection, migrations[0], now=now)
            self._verify_migrations(connection)
            applied_versions = {
                int(row[0])
                for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
            }
            for migration in migrations:
                if migration.version not in applied_versions:
                    self._apply_one_locked(connection, migration, now=now)
            self._verify_migrations(connection)
            connection.execute("COMMIT")
        except Exception:
            with suppress(sqlite3.Error):
                connection.execute("ROLLBACK")
            raise

    def _verify_migrations(self, connection: sqlite3.Connection) -> None:
        if not self._has_migration_table(connection):
            raise MigrationError("schema_migrations table is missing")
        expected = {migration.version: migration for migration in load_migrations()}
        rows = connection.execute(
            "SELECT version, name, ddl_sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
        for row in rows:
            version = int(row["version"])
            migration = expected.get(version)
            if migration is None:
                raise MigrationError(f"database schema version {version} is newer than this runtime")
            if row["name"] != migration.name or row["ddl_sha256"] != migration.sha256:
                raise MigrationError(f"migration fingerprint mismatch at version {version}")
        applied = [int(row["version"]) for row in rows]
        if applied != list(range(1, len(applied) + 1)):
            raise MigrationError(f"applied migration versions are not contiguous: {applied}")

    @staticmethod
    def _apply_one_locked(connection: sqlite3.Connection, migration: Migration, *, now: datetime) -> None:
        try:
            for statement in _split_sql_statements(migration.sql):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations(version, name, ddl_sha256, applied_at) VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, migration.sha256, isoformat_z(now)),
            )
        except sqlite3.Error as exc:
            raise MigrationError(f"migration {migration.name} failed: {exc}") from exc


def _split_sql_statements(sql: str) -> tuple[str, ...]:
    """Split trusted migration SQL while preserving trigger BEGIN/END bodies."""
    statements: list[str] = []
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                statements.append(statement)
            buffer = ""
    if buffer.strip():
        raise MigrationError("migration SQL ended with an incomplete statement")
    return tuple(statements)
