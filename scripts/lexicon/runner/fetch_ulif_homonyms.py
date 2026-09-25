#!/usr/bin/env python3
"""Resumable targeted ULIF fetch with homonym fan-out (#8400 step c).

One spelling is one unit of work. ``tsearch`` positions the register, every
matching row is opened from that page's pristine view state, and each tab
present on the entry is fetched from the entry response — never by chaining
tab postbacks. Response bodies and redacted request payloads are stored
before parsing. ``parse`` is a separate offline pass over those bodies.

The declared user agent is ``DictUAClient`` in ``fetch_ulif_20k.py``. Raw
bodies use the ``ulif_dictua_raw_responses`` table: sha256 of the bytes,
uncompressed, the same content-addressing ``store_ulif_dictua_entry`` already
uses. View-state fields are replaced by their sha256 in the stored payload.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import itertools
import json
import math
import os
import shlex
import signal
import sqlite3
import stat
import sys
import threading
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from scripts.lexicon.runner.fetch_ulif_20k import ULIF_URL, DictUAClient
from scripts.lexicon.runner.ulif_dictua_parse import (
    ULIF_PARSER_VERSION,
    normalize_ulif_spelling,
    parse_register_list,
    parse_ulif_entry,
    parse_ulif_paradigm,
    parse_ulif_relation_groups,
)

MIN_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30
MAX_HTTP_ATTEMPTS = 5
MAX_UNIT_RESEEDS = 3
CONSECUTIVE_RETRY_STOP = 3
REGISTER_PAGE_SIZE = 25
LOCK_NAME = "runner.lock"
PROGRESS_INTERVAL_ENV = "ULIF_PROGRESS_INTERVAL_SECONDS"
DEFAULT_PROGRESS_INTERVAL_SECONDS = 60.0

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_RETRY_STORM = 2
EXIT_FORBIDDEN = 3
EXIT_INTERRUPTED = 4

VIEWSTATE_FIELDS = ("__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR")
GRID_TARGET = "ctl00$ContentPlaceHolder1$dgv"
TSEARCH_FIELD = "ctl00$ContentPlaceHolder1$tsearch"
SEARCH_BUTTON = "ctl00$ContentPlaceHolder1$search"
PAGE_BUTTONS = {
    "back": "ctl00$ContentPlaceHolder1$backpage",
    "next": "ctl00$ContentPlaceHolder1$nextpage",
}
TAB_BUTTONS = (
    ("paradigm", "ctl00$ContentPlaceHolder1$par"),
    ("synonyms", "ctl00$ContentPlaceHolder1$syn"),
    ("phraseology", "ctl00$ContentPlaceHolder1$phras"),
    ("antonyms", "ctl00$ContentPlaceHolder1$ant"),
)
KNOWN_PLACEHOLDER_CONTROLS = frozenset(
    {"search", "par", "syn", "phras", "ant", "nextpage", "backpage", "artnext", "artback"}
)
TERMINAL_STATES = ("stored", "absent_from_ulif", "retry_scheduled", "error")
COMPLETE_STATES = ("stored", "absent_from_ulif")
_VALIDATION_MARKERS = (
    "validation of viewstate mac failed",
    "invalid viewstate",
    "event validation",
)

SleepFn = Callable[[float], None]
ClockFn = Callable[[], float]
Scanner = Callable[[], bool | None]
Transport = Callable[[str, dict[str, str] | None], "HttpResult"]
HeartbeatFn = Callable[[str], float | None]


class InterruptedByOperator(KeyboardInterrupt):
    """SIGINT or SIGTERM received."""


def declared_user_agent() -> str:
    """The user agent already declared by the 20k DictUA client."""
    return DictUAClient(
        delay_seconds=MIN_DELAY_SECONDS,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    ).headers["User-Agent"]


class Forbidden(Exception):
    """HTTP 403. The run stops."""


class RequestExhausted(Exception):
    """429 or 5xx persisted for five attempts."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class SessionInvalid(Exception):
    """500 or an event-validation failure. The unit must be re-seeded."""


class ResumeMismatchError(Exception):
    """Landed register page does not match expected page boundary headwords."""


class RequestCap(Exception):
    """The invocation's request ceiling was reached before this send."""


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    text: str
    headers: Mapping[str, str]


@dataclass(frozen=True)
class UnitOutcome:
    state: str
    entry_count: int
    straddled: bool


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_private_dir(path: Path) -> None:
    """Create *path* (and missing parents) mode ``0o700``; never re-chmod existing.

    If *path* already exists and is group- or world-accessible, print one warning
    naming the path and mode, then continue without changing it.
    """
    if path.exists():
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            print(
                f"warning: existing directory {path} has mode {oct(mode)}; leaving unchanged",
                file=sys.stderr,
            )
        return
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    for directory in reversed(missing):
        if directory.exists():
            mode = stat.S_IMODE(directory.stat().st_mode)
            if mode & 0o077:
                print(
                    f"warning: existing directory {directory} has mode {oct(mode)}; leaving unchanged",
                    file=sys.stderr,
                )
            continue
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            mode = stat.S_IMODE(directory.stat().st_mode)
            if mode & 0o077:
                print(
                    f"warning: existing directory {directory} has mode {oct(mode)}; leaving unchanged",
                    file=sys.stderr,
                )
            continue
        os.chmod(directory, 0o700)


def _ensure_private_file(path: Path) -> None:
    """Narrow a runner-created file to owner-only read/write.

    Call only for files this runner just created. Never call for pre-existing paths.
    """
    os.chmod(path, 0o600)


def _default_sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def _pid_alive(pid: int) -> bool | None:
    """True when *pid* is alive, False when it is not, None when unsure."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def scan_for_legacy_crawler() -> bool | None:
    """True when a live process command line contains ``dump_ulif.py``.

    ``None`` means the scan itself failed. Callers refuse to start on ``None``.
    """
    proc = Path("/proc")
    if not proc.is_dir():
        return None
    try:
        entries = list(proc.iterdir())
    except OSError:
        return None
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        text = raw.replace(b"\x00", b" ").decode("utf-8", "replace")
        if "dump_ulif.py" in text:
            return True
    return False


class RunnerLock:
    """PID lock under the runner state directory.

    A lock whose pid is not alive is stale: it is reported and left in place
    unless ``break_stale`` is set. A live pid, an unreadable lock, or any
    doubt about a legacy ``dump_ulif.py`` process refuses the start.
    """

    def __init__(self, state_dir: Path, *, break_stale: bool, scanner: Scanner) -> None:
        self.path = state_dir / LOCK_NAME
        self.break_stale = break_stale
        self.scanner = scanner
        self._held = False

    def acquire(self) -> None:
        _ensure_private_dir(self.path.parent)
        legacy = self.scanner()
        if legacy is None:
            raise SystemExit("refusing to start: could not scan process command lines for dump_ulif.py")
        if legacy:
            raise SystemExit("refusing to start: dump_ulif.py is running")
        if self.path.exists():
            pid, started, _raw = _read_lock(self.path)
            alive = None if pid is None else _pid_alive(pid)
            if pid is None or alive is None:
                raise SystemExit(f"refusing to start: lock {self.path} is unreadable or its pid is uncertain")
            if alive:
                raise SystemExit(f"refusing to start: runner lock held by live pid {pid} since {started} ({self.path})")
            print(
                f"stale lock: pid {pid} is not alive (started {started}) at {self.path}",
                file=sys.stderr,
            )
            if not self.break_stale:
                raise SystemExit("refusing to start: stale lock; pass --break-stale-lock")
            self.path.unlink()
        payload = f"{os.getpid()}\n{_now_iso()}\n"
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise SystemExit(f"refusing to start: lock appeared at {self.path}") from exc
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            self._held = True
        except BaseException:
            with contextlib.suppress(OSError):
                self.path.unlink()
            raise

    def release(self) -> None:
        if not self._held or not self.path.exists():
            return
        for _ in range(3):
            try:
                pid, _started, _raw = _read_lock(self.path)
                if pid == os.getpid() or not _raw.strip():
                    with contextlib.suppress(OSError):
                        self.path.unlink()
                self._held = False
                break
            except (KeyboardInterrupt, InterruptedByOperator, BaseException):
                with contextlib.suppress(OSError):
                    self.path.unlink()
                self._held = False
                raise


def _read_lock(path: Path) -> tuple[int | None, str, str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None, "", ""
    lines = raw.splitlines()
    if not lines:
        return None, "", raw
    try:
        pid = int(lines[0].strip())
    except ValueError:
        return None, "", raw
    started = lines[1].strip() if len(lines) > 1 else ""
    return pid, started, raw


class SpellingLedger:
    """Per-spelling states: pending, stored, absent_from_ulif, retry_scheduled, error."""

    def __init__(self, path: Path) -> None:
        _ensure_private_dir(path.parent)
        self.path = path
        created = not path.exists()
        self.conn = sqlite3.connect(path)
        if created:
            _ensure_private_file(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS spellings (
                spelling TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                entry_count INTEGER NOT NULL DEFAULT 0,
                error TEXT NOT NULL DEFAULT '',
                straddled_boundary INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0,
                duplicate_content INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY,
                spelling TEXT NOT NULL,
                role TEXT NOT NULL,
                homonym_index INTEGER,
                tab_kind TEXT NOT NULL DEFAULT '',
                register_position TEXT NOT NULL DEFAULT '',
                response_sha256 TEXT NOT NULL,
                request_sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_ulif_responses_position
                ON responses (spelling, register_position, role, id);
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS register_pages (
                page_num INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                start_headword TEXT NOT NULL DEFAULT '',
                end_headword TEXT NOT NULL DEFAULT '',
                row_count INTEGER NOT NULL DEFAULT 0,
                register_size INTEGER,
                error TEXT NOT NULL DEFAULT '',
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS register_rows (
                page_num INTEGER NOT NULL,
                row_index INTEGER NOT NULL,
                select_arg TEXT NOT NULL,
                stressed_headword TEXT NOT NULL,
                normalized_spelling TEXT NOT NULL,
                state TEXT NOT NULL,
                entry_sha256 TEXT NOT NULL DEFAULT '',
                homonym_index INTEGER,
                unknown_controls TEXT NOT NULL DEFAULT '',
                paradigm_source TEXT NOT NULL DEFAULT '',
                error TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (page_num, row_index)
            );
            CREATE INDEX IF NOT EXISTS register_rows_normalized_spelling
                ON register_rows (normalized_spelling);
            """
        )
        self.conn.commit()
        self._ensure_duplicate_content_column()

    def _ensure_duplicate_content_column(self) -> None:
        columns = {str(row[1]) for row in self.conn.execute("PRAGMA table_info(spellings)")}
        if "duplicate_content" not in columns:
            self.conn.execute("ALTER TABLE spellings ADD COLUMN duplicate_content INTEGER NOT NULL DEFAULT 0")
            self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def ensure(self, spelling: str) -> None:
        self.conn.execute(
            """
            INSERT INTO spellings (spelling, state, updated_at)
            VALUES (?, 'pending', ?)
            ON CONFLICT(spelling) DO NOTHING
            """,
            (spelling, _now_iso()),
        )
        self.conn.commit()

    def state_of(self, spelling: str) -> str | None:
        row = self.conn.execute("SELECT state FROM spellings WHERE spelling = ?", (spelling,)).fetchone()
        return None if row is None else str(row["state"])

    def mark(
        self,
        spelling: str,
        state: str,
        *,
        entry_count: int = 0,
        error: str = "",
        straddled: bool = False,
        duplicate_content: bool | None = None,
    ) -> None:
        if duplicate_content is None:
            self.conn.execute(
                """
                UPDATE spellings
                SET state = ?, entry_count = ?, error = ?, straddled_boundary = ?,
                    attempts = attempts + 1, updated_at = ?
                WHERE spelling = ?
                """,
                (state, entry_count, error, 1 if straddled else 0, _now_iso(), spelling),
            )
        else:
            self.conn.execute(
                """
                UPDATE spellings
                SET state = ?, entry_count = ?, error = ?, straddled_boundary = ?,
                    duplicate_content = ?, attempts = attempts + 1, updated_at = ?
                WHERE spelling = ?
                """,
                (
                    state,
                    entry_count,
                    error,
                    1 if straddled else 0,
                    1 if duplicate_content else 0,
                    _now_iso(),
                    spelling,
                ),
            )
        self.conn.commit()

    def set_duplicate_content(self, spelling: str, duplicate_content: bool) -> None:
        self.conn.execute(
            """
            UPDATE spellings
            SET duplicate_content = ?, updated_at = ?
            WHERE spelling = ?
            """,
            (1 if duplicate_content else 0, _now_iso(), spelling),
        )
        self.conn.commit()

    def record_response(
        self,
        *,
        spelling: str,
        role: str,
        response_sha256: str,
        request_sha256: str,
        homonym_index: int | None = None,
        tab_kind: str = "",
        register_position: str = "",
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO responses (
                spelling, role, homonym_index, tab_kind, register_position,
                response_sha256, request_sha256, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spelling,
                role,
                homonym_index,
                tab_kind,
                register_position,
                response_sha256,
                request_sha256,
                _now_iso(),
            ),
        )
        self.conn.commit()

    def clear_responses(self, spelling: str) -> None:
        self.conn.execute("DELETE FROM responses WHERE spelling = ?", (spelling,))
        self.conn.commit()

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    def meta(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return default if row is None else str(row["value"])

    def record_printed_mismatch(
        self,
        normalized_spelling: str,
        register: Sequence[int],
        printed: Sequence[int | None],
    ) -> None:
        """Atomically record printed number mismatch error and increment counter in one transaction."""
        try:
            already_recorded = bool(
                self.conn.execute(
                    "SELECT 1 FROM register_rows WHERE normalized_spelling = ? AND error LIKE 'printed_number_mismatch%' LIMIT 1",
                    (normalized_spelling,),
                ).fetchone()
            )
            if not already_recorded:
                cur_mismatch = int(self.meta("mismatch_groups", "0") or "0")
                self.conn.execute(
                    "INSERT INTO meta (key, value) VALUES ('mismatch_groups', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (str(cur_mismatch + 1),),
                )
            self.conn.execute(
                "UPDATE register_rows SET error = ? WHERE normalized_spelling = ?",
                (f"printed_number_mismatch register={list(register)} printed={list(printed)}", normalized_spelling),
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def add_requests(self, count: int) -> None:
        current = int(self.meta("requests_made", "0") or "0")
        self.set_meta("requests_made", str(current + count))

    def set_requests_made(self, count: int) -> None:
        self.set_meta("requests_made", str(count))

    def counts(self) -> dict[str, int]:
        rows = self.conn.execute("SELECT state, COUNT(*) AS n FROM spellings GROUP BY state").fetchall()
        found = {str(row["state"]): int(row["n"]) for row in rows}
        total = sum(found.values())
        entries = self.conn.execute(
            "SELECT COALESCE(SUM(entry_count), 0) FROM spellings WHERE state = 'stored'"
        ).fetchone()
        return {
            "spellings_total": total,
            "stored": found.get("stored", 0),
            "absent_from_ulif": found.get("absent_from_ulif", 0),
            "retry_scheduled": found.get("retry_scheduled", 0),
            "error": found.get("error", 0),
            "pending": found.get("pending", 0),
            "entries_stored": int(entries[0]),
        }

    def entry_responses(self, spelling: str) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT * FROM responses
                WHERE spelling = ? AND role = 'entry'
                ORDER BY homonym_index, id
                """,
                (spelling,),
            )
        )

    def stored_spellings(self) -> set[str]:
        rows = self.conn.execute("SELECT spelling FROM spellings WHERE state = 'stored'")
        return {str(row["spelling"]) for row in rows}

    def ensure_page(
        self,
        page_num: int,
        *,
        start_headword: str = "",
        end_headword: str = "",
        row_count: int = 0,
        register_size: int | None = None,
        state: str = "in_progress",
    ) -> None:
        now = _now_iso()
        self.conn.execute(
            """
            INSERT INTO register_pages (
                page_num, state, start_headword, end_headword, row_count, register_size, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(page_num) DO UPDATE SET
                start_headword = CASE WHEN excluded.start_headword != '' THEN excluded.start_headword ELSE register_pages.start_headword END,
                end_headword = CASE WHEN excluded.end_headword != '' THEN excluded.end_headword ELSE register_pages.end_headword END,
                row_count = CASE WHEN excluded.row_count > 0 THEN excluded.row_count ELSE register_pages.row_count END,
                register_size = COALESCE(excluded.register_size, register_pages.register_size),
                updated_at = excluded.updated_at
            """,
            (page_num, state, start_headword, end_headword, row_count, register_size, now, now),
        )
        self.conn.commit()

    def mark_page(self, page_num: int, state: str, *, error: str = "") -> None:
        self.conn.execute(
            """
            UPDATE register_pages
            SET state = ?, error = ?, attempts = attempts + 1, updated_at = ?
            WHERE page_num = ?
            """,
            (state, error, _now_iso(), page_num),
        )
        self.conn.commit()

    def get_page(self, page_num: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM register_pages WHERE page_num = ?", (page_num,)).fetchone()

    def first_unfinished_page(self) -> int | None:
        row = self.conn.execute(
            "SELECT page_num FROM register_pages WHERE state != 'completed' ORDER BY page_num LIMIT 1"
        ).fetchone()
        if row is not None:
            return int(row["page_num"])
        max_row = self.conn.execute("SELECT MAX(page_num) FROM register_pages").fetchone()
        if max_row is not None and max_row[0] is not None:
            return int(max_row[0]) + 1
        return None

    def ensure_row(
        self,
        page_num: int,
        row_index: int,
        *,
        select_arg: str,
        stressed_headword: str,
        normalized_spelling: str,
    ) -> None:
        now = _now_iso()
        self.conn.execute(
            """
            INSERT INTO register_rows (
                page_num, row_index, select_arg, stressed_headword, normalized_spelling, state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            ON CONFLICT(page_num, row_index) DO NOTHING
            """,
            (page_num, row_index, select_arg, stressed_headword, normalized_spelling, now, now),
        )
        self.conn.commit()

    def mark_row(
        self,
        page_num: int,
        row_index: int,
        state: str,
        *,
        entry_sha256: str = "",
        homonym_index: int | None = None,
        unknown_controls: str = "",
        paradigm_source: str = "",
        error: str = "",
    ) -> None:
        self.conn.execute(
            """
            UPDATE register_rows
            SET state = ?, entry_sha256 = ?, homonym_index = ?, unknown_controls = ?, paradigm_source = ?, error = ?, updated_at = ?
            WHERE page_num = ? AND row_index = ?
            """,
            (
                state,
                entry_sha256,
                homonym_index,
                unknown_controls,
                paradigm_source,
                error,
                _now_iso(),
                page_num,
                row_index,
            ),
        )
        self.conn.commit()

    def page_rows(self, page_num: int) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                "SELECT * FROM register_rows WHERE page_num = ? ORDER BY row_index",
                (page_num,),
            )
        )

    def completed_rows_for_spelling(self, normalized_spelling: str) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT * FROM register_rows
                WHERE normalized_spelling = ? AND state = 'completed'
                ORDER BY page_num, row_index
                """,
                (normalized_spelling,),
            )
        )

    def walk_counts(self) -> dict[str, Any]:
        pages_done = self.conn.execute("SELECT COUNT(*) FROM register_pages WHERE state = 'completed'").fetchone()[0]
        entries_stored = self.conn.execute("SELECT COUNT(*) FROM register_rows WHERE state = 'completed'").fetchone()[0]
        spellings = self.conn.execute(
            "SELECT COUNT(DISTINCT normalized_spelling) FROM register_rows WHERE state = 'completed'"
        ).fetchone()[0]
        multi_row = self.conn.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT normalized_spelling FROM register_rows
                WHERE state = 'completed'
                GROUP BY normalized_spelling
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        par_entry = self.conn.execute(
            "SELECT COUNT(*) FROM register_rows WHERE paradigm_source = 'entry' AND state = 'completed'"
        ).fetchone()[0]
        par_req = self.conn.execute(
            "SELECT COUNT(*) FROM register_rows WHERE paradigm_source = 'tab' AND state = 'completed'"
        ).fetchone()[0]
        unknown_ctrl = self.conn.execute(
            "SELECT COUNT(*) FROM register_rows WHERE unknown_controls != '' AND state = 'completed'"
        ).fetchone()[0]

        reg_size_raw = self.meta("register_size")
        reg_size = int(reg_size_raw) if reg_size_raw and reg_size_raw.isdigit() else None
        pages_total = (reg_size + REGISTER_PAGE_SIZE - 1) // REGISTER_PAGE_SIZE if reg_size else 0

        return {
            "pages_done": int(pages_done),
            "pages_total": pages_total,
            "entries_stored": int(entries_stored),
            "spellings": int(spellings),
            "multi_entry_spellings": int(multi_row),
            "paradigm_from_entry": int(par_entry),
            "paradigm_requested": int(par_req),
            "unknown_control_entries": int(unknown_ctrl),
            "register_size": reg_size_raw or "unknown",
            "differing_groups": int(self.meta("differing_groups", "0") or "0"),
            "register_size_changes": int(self.meta("register_size_changes_count", "0") or "0"),
        }


def status_text(
    ledger: SpellingLedger,
    *,
    delay_seconds: float,
    state_dir: Path | None = None,
    mode: str = "auto",
) -> str:
    has_walk_pages = False
    with contextlib.suppress(Exception):
        r = ledger.conn.execute("SELECT COUNT(*) FROM register_pages").fetchone()
        if r and r[0] > 0:
            has_walk_pages = True
    is_walk = (mode == "walk") or (mode == "auto" and (ledger.meta("mode") == "walk" or has_walk_pages))

    dir_path = state_dir or ledger.path.parent
    lock_path = dir_path / LOCK_NAME
    if lock_path.exists():
        pid, started, _ = _read_lock(lock_path)
        alive = None if pid is None else _pid_alive(pid)
        if alive is True:
            runner_str = f"running pid={pid} since={started}"
        elif alive is False:
            runner_str = f"stale_lock pid={pid}"
        else:
            runner_str = f"stale_lock pid={pid if pid is not None else 'unknown'}"
    else:
        runner_str = "not_running"

    if is_walk:
        w_counts = ledger.walk_counts()
        requests_made = int(ledger.meta("requests_made", "0") or "0")
        pages_done = w_counts["pages_done"]
        pages_total = w_counts["pages_total"]
        entries_stored = w_counts["entries_stored"]
        spellings = w_counts["spellings"]
        multi_entry = w_counts["multi_entry_spellings"]
        par_entry = w_counts["paradigm_from_entry"]
        par_req = w_counts["paradigm_requested"]
        unknown_ctrl = w_counts["unknown_control_entries"]
        differing_groups = w_counts["differing_groups"]
        reg_changes = w_counts["register_size_changes"]
        reg_size = w_counts["register_size"]

        mean_req = (requests_made / entries_stored) if entries_stored > 0 else 0.0

        timed_pages = int(ledger.meta("cumulative_timed_pages", "0") or "0")
        wall_seconds = float(ledger.meta("cumulative_page_wall_seconds", "0.0") or "0.0")
        remaining_pages = max(0, pages_total - pages_done) if pages_total else 0
        if remaining_pages == 0 and pages_total > 0:
            eta: str | float = 0
        elif timed_pages == 0:
            eta = "unknown"
        else:
            mean_wall = wall_seconds / timed_pages
            eta = round(remaining_pages * mean_wall, 1)

        if pages_total == 0 and pages_done == 0:
            complete = "not_started"
        elif pages_total > 0 and pages_done >= pages_total:
            complete = "yes"
        else:
            complete = "no"

        row = ledger.conn.execute("SELECT MAX(updated_at) FROM register_pages").fetchone()
        last_update = str(row[0]) if row is not None and row[0] else "none"
        if last_update != "none":
            try:
                dt = datetime.fromisoformat(last_update)
                secs = int(max(0.0, (datetime.now(UTC) - dt).total_seconds()))
                seconds_since = str(secs)
            except Exception:
                seconds_since = "unknown"
        else:
            seconds_since = "unknown"

        lines = [
            f"pages_done={pages_done}",
            f"pages_total={pages_total}",
            f"entries_stored={entries_stored}",
            f"spellings={spellings}",
            f"multi_entry_spellings={multi_entry}",
            f"paradigm_from_entry={par_entry}",
            f"paradigm_requested={par_req}",
            f"unknown_control_entries={unknown_ctrl}",
            f"requests_made={requests_made}",
            f"mean_requests_per_entry={mean_req:.2f}",
            f"estimated_time_remaining_seconds={eta}",
            f"register_size={reg_size}",
            f"register_size_changes={reg_changes}",
            f"differing_groups={differing_groups}",
            f"complete={complete}",
            f"runner={runner_str}",
            f"last_update={last_update}",
            f"seconds_since_last_update={seconds_since}",
        ]
        return "\n".join(lines)

    counts = ledger.counts()
    requests_made = int(ledger.meta("requests_made", "0") or "0")
    finished = counts["stored"] + counts["absent_from_ulif"] + counts["retry_scheduled"] + counts["error"]
    mean = (requests_made / finished) if finished else 0.0
    remaining = counts["pending"] + counts["retry_scheduled"] + counts["error"]

    timed_units = int(ledger.meta("cumulative_timed_units", "0") or "0")
    wall_seconds = float(ledger.meta("cumulative_wall_seconds", "0.0") or "0.0")
    if remaining == 0:
        eta = 0
    elif timed_units == 0:
        eta = "unknown"
    else:
        mean_wall = wall_seconds / timed_units
        eta = round(remaining * mean_wall, 1)

    register = ledger.meta("register_size", "") or "unknown"
    if counts["spellings_total"] == 0:
        complete = "not_started"
    elif counts["pending"] == 0 and counts["retry_scheduled"] == 0 and counts["error"] == 0:
        complete = "yes"
    else:
        complete = "no"

    differing = ledger.meta("differing_content_hashes", "0")

    row = ledger.conn.execute("SELECT MAX(updated_at) FROM spellings").fetchone()
    last_update = str(row[0]) if row is not None and row[0] else "none"
    if last_update != "none":
        try:
            dt = datetime.fromisoformat(last_update)
            secs = int(max(0.0, (datetime.now(UTC) - dt).total_seconds()))
            seconds_since = str(secs)
        except Exception:
            seconds_since = "unknown"
    else:
        seconds_since = "unknown"

    lines = [
        f"spellings_total={counts['spellings_total']}",
        f"stored={counts['stored']}",
        f"absent_from_ulif={counts['absent_from_ulif']}",
        f"retry_scheduled={counts['retry_scheduled']}",
        f"error={counts['error']}",
        f"entries_stored={counts['entries_stored']}",
        f"requests_made={requests_made}",
        f"mean_requests_per_spelling={mean:.2f}",
        f"estimated_time_remaining_seconds={eta}",
        f"register_size={register}",
        f"complete={complete}",
        f"differing_content_hashes={differing}",
        f"runner={runner_str}",
        f"last_update={last_update}",
        f"seconds_since_last_update={seconds_since}",
    ]
    return "\n".join(lines)


def _tokens(html: str) -> dict[str, str] | None:
    return DictUAClient._tokens(html)


def _register_size(html: str) -> int | None:
    soup = BeautifulSoup(html, "html.parser")
    node = soup.find(id="ContentPlaceHolder1_rlength")
    if node is None:
        return None
    digits = "".join(char for char in node.get_text(" ", strip=True) if char.isdigit())
    return int(digits) if digits else None


def _has_control(html: str, name: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("input", attrs={"name": name}) is not None


def _present_tabs(html: str) -> list[tuple[str, str]]:
    return [(kind, name) for kind, name in TAB_BUTTONS if _has_control(html, name)]


def find_unknown_controls(html: str) -> list[str]:
    """Identify image or submit controls inside content placeholder not in known set."""
    soup = BeautifulSoup(html, "html.parser")
    unknown: list[str] = []
    for inp in soup.find_all("input"):
        inp_type = str(inp.get("type") or "").lower()
        if inp_type in ("image", "submit"):
            name = str(inp.get("name") or "")
            if "ContentPlaceHolder1" in name or name.startswith("ctl00$"):
                short = name.split("$")[-1].lower()
                if short not in KNOWN_PLACEHOLDER_CONTROLS and short not in unknown:
                    unknown.append(short)
    return unknown


def _validation_failure(html: str) -> bool:
    folded = html.casefold()
    return any(marker in folded for marker in _VALIDATION_MARKERS)


def _redact_payload(fields: Mapping[str, str] | None, *, method: str) -> bytes:
    if fields is None:
        body = {"method": method, "url": ULIF_URL}
    else:
        body = {"method": method, "url": ULIF_URL}
        for key, value in fields.items():
            if key in VIEWSTATE_FIELDS:
                body[key] = hashlib.sha256(value.encode("utf-8")).hexdigest()
            else:
                body[key] = value
    return json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _store_blob(conn: sqlite3.Connection, digest: str, body: bytes, content_type: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO ulif_dictua_raw_responses
            (response_sha256, body, content_type, stored_at)
        VALUES (?, ?, ?, ?)
        """,
        (digest, body, content_type, _now_iso()),
    )


def _retry_after_seconds(headers: Mapping[str, str], attempt: int) -> float:
    exponential = min(120.0, float(2 ** (attempt - 1)))
    raw = ""
    for key, value in headers.items():
        if key.lower() == "retry-after":
            raw = value.strip()
            break
    if not raw:
        return exponential
    try:
        return max(exponential, float(raw))
    except ValueError:
        return exponential


class PoliteClient:
    """One session, one request at a time, delay configurable only upward of 1s."""

    def __init__(
        self,
        transport: Transport,
        *,
        delay_seconds: float,
        sleep: SleepFn = _default_sleep,
        clock: ClockFn = time.monotonic,
        max_requests: int | None = None,
        heartbeat: HeartbeatFn | None = None,
        on_request: Callable[[int], None] | None = None,
    ) -> None:
        if delay_seconds < MIN_DELAY_SECONDS:
            raise ValueError(f"delay must be >= {MIN_DELAY_SECONDS}, got {delay_seconds}")
        self.transport = transport
        self.delay_seconds = delay_seconds
        self.sleep = sleep
        self.clock = clock
        self.max_requests = max_requests
        self.heartbeat = heartbeat
        self.on_request = on_request
        self.requests_made = 0
        self._last_at = 0.0

    def _record_request(self) -> None:
        self.requests_made += 1
        self._last_at = self.clock()
        if self.on_request is not None:
            with contextlib.suppress(Exception):
                self.on_request(self.requests_made)

    def _sleep_with_heartbeat(self, seconds: float, msg_fn: Callable[[float], str]) -> None:
        if seconds <= 0:
            return
        if self.heartbeat is None:
            self.sleep(seconds)
            return
        rem = seconds
        while rem > 0:
            until_due = self.heartbeat(msg_fn(rem))
            if until_due is None or until_due <= 0:
                until_due = 60.0
            if rem <= until_due:
                self.sleep(rem)
                break
            self.sleep(until_due)
            rem -= until_due

    def exchange(self, method: str, fields: dict[str, str] | None) -> tuple[str, bytes]:
        """Return ``(body, redacted_request)``. Raises on 403, exhaustion, or a dead session."""
        import requests

        redacted = _redact_payload(fields, method=method)
        last_code = "http_error"
        for attempt in range(1, MAX_HTTP_ATTEMPTS + 1):
            self._wait_turn()
            if self.max_requests is not None and self.requests_made >= self.max_requests:
                raise RequestCap(str(self.max_requests))
            if self.heartbeat is not None:
                self.heartbeat("waiting for response")
            try:
                try:
                    result = self.transport(method, fields)
                finally:
                    self._record_request()
            except requests.RequestException:
                last_code = "transport_error"
                if attempt == MAX_HTTP_ATTEMPTS:
                    raise RequestExhausted(last_code) from None
                wait_sec = _retry_after_seconds({}, attempt)
                self._sleep_with_heartbeat(
                    wait_sec,
                    lambda rem, att=attempt: f"waiting for back-off: {rem:.0f}s remaining (attempt {att})",
                )
                continue
            code = result.status_code
            if code == 403:
                raise Forbidden("http_403")
            if code == 500 or (code == 200 and _validation_failure(result.text)):
                raise SessionInvalid(f"http_{code}" if code != 200 else "event_validation")
            if code == 429 or code >= 500:
                last_code = f"http_{code}"
                if attempt == MAX_HTTP_ATTEMPTS:
                    raise RequestExhausted(last_code)
                wait_sec = _retry_after_seconds(result.headers, attempt)
                self._sleep_with_heartbeat(
                    wait_sec,
                    lambda rem, att=attempt: f"waiting for back-off: {rem:.0f}s remaining (attempt {att})",
                )
                continue
            if code != 200:
                last_code = f"http_{code}"
                if attempt == MAX_HTTP_ATTEMPTS:
                    raise RequestExhausted(last_code)
                wait_sec = _retry_after_seconds(result.headers, attempt)
                self._sleep_with_heartbeat(
                    wait_sec,
                    lambda rem, att=attempt: f"waiting for back-off: {rem:.0f}s remaining (attempt {att})",
                )
                continue
            return result.text, redacted
        raise RequestExhausted(last_code)

    def _wait_turn(self) -> None:
        if not self._last_at:
            return
        elapsed = self.clock() - self._last_at
        if elapsed < self.delay_seconds:
            self._sleep_with_heartbeat(self.delay_seconds - elapsed, lambda _rem: "waiting for response")


def _form_fields(
    tokens: Mapping[str, str],
    *,
    spelling: str,
    event_target: str = "",
    event_argument: str = "",
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    fields = {
        "__VIEWSTATE": tokens["__VIEWSTATE"],
        "__EVENTVALIDATION": tokens["__EVENTVALIDATION"],
        "__VIEWSTATEGENERATOR": tokens.get("__VIEWSTATEGENERATOR", ""),
        "__EVENTTARGET": event_target,
        "__EVENTARGUMENT": event_argument,
        TSEARCH_FIELD: spelling,
    }
    if extra:
        fields.update(extra)
    return fields


def _image_click(control: str) -> dict[str, str]:
    return {f"{control}.x": "10", f"{control}.y": "10"}


class HomonymFetcher:
    def __init__(self, client: PoliteClient, ledger: SpellingLedger, cache: sqlite3.Connection) -> None:
        self.client = client
        self.ledger = ledger
        self.cache = cache

    def fetch(self, spelling: str) -> UnitOutcome:
        last: SessionInvalid | None = None
        for _attempt in range(MAX_UNIT_RESEEDS):
            try:
                return self._once(spelling)
            except SessionInvalid as exc:
                last = exc
        assert last is not None
        raise last

    def _once(self, spelling: str) -> UnitOutcome:
        self.ledger.clear_responses(spelling)
        seed_html, seed_request = self.client.exchange("GET", None)
        self._keep(spelling, "seed", seed_html, seed_request)
        seed_tokens = _tokens(seed_html)
        if seed_tokens is None:
            raise SessionInvalid("seed_missing_viewstate")
        search_fields = _form_fields(
            seed_tokens,
            spelling=spelling,
            extra=_image_click(SEARCH_BUTTON),
        )
        search_html, search_request = self.client.exchange("POST", search_fields)
        self._keep(spelling, "tsearch", search_html, search_request)
        search_tokens = _tokens(search_html)
        if search_tokens is None or _validation_failure(search_html):
            raise SessionInvalid("tsearch_missing_viewstate")
        if "ContentPlaceHolder1_dgv" not in search_html:
            raise SessionInvalid("tsearch_missing_register")
        rows = parse_register_list(search_html)
        matches = _matching(rows, spelling)
        straddled = False
        before: list[dict[str, Any]] = []
        after: list[dict[str, Any]] = []
        page_tokens = {"0": search_tokens}
        if len(rows) >= REGISTER_PAGE_SIZE and matches:
            indexes = {int(row["row_index"]) for row in matches}
            if rows[0]["row_index"] in indexes and _has_control(search_html, PAGE_BUTTONS["back"]):
                straddled = True
                before, back_tokens = self._adjacent(spelling, search_tokens, "back", -1)
                if back_tokens is not None:
                    page_tokens["-1"] = back_tokens
            if rows[-1]["row_index"] in indexes and _has_control(search_html, PAGE_BUTTONS["next"]):
                straddled = True
                after, next_tokens = self._adjacent(spelling, search_tokens, "next", 1)
                if next_tokens is not None:
                    page_tokens["1"] = next_tokens
        ordered = _dedupe_register_rows([*before, *({**row, "page_delta": 0} for row in matches), *after])
        if not ordered:
            return UnitOutcome("absent_from_ulif", 0, straddled)
        for index, row in enumerate(ordered, start=1):
            row["homonym_index"] = index
            delta = str(row["page_delta"])
            tokens = page_tokens.get(delta, search_tokens)
            self._open_entry(spelling, tokens, row)
        return UnitOutcome("stored", len(ordered), straddled)

    def _adjacent(
        self,
        spelling: str,
        pristine: Mapping[str, str],
        direction: str,
        page_delta: int,
    ) -> tuple[list[dict[str, Any]], dict[str, str] | None]:
        fields = _form_fields(pristine, spelling=spelling, extra=_image_click(PAGE_BUTTONS[direction]))
        html, request = self.client.exchange("POST", fields)
        self._keep(spelling, f"page:{direction}", html, request)
        tokens = _tokens(html)
        if tokens is None:
            raise SessionInvalid(f"{direction}_missing_viewstate")
        matched = _matching(parse_register_list(html), spelling)
        return [{**row, "page_delta": page_delta} for row in matched], tokens

    def _open_entry(self, spelling: str, pristine: Mapping[str, str], row: Mapping[str, Any]) -> None:
        fields = _form_fields(
            pristine,
            spelling=spelling,
            event_target=GRID_TARGET,
            event_argument=str(row["select"]),
        )
        html, request = self.client.exchange("POST", fields)
        position = f"{row['page_delta']}:{row['row_index']}"
        homonym_index = int(row["homonym_index"])
        self._keep(
            spelling,
            "entry",
            html,
            request,
            homonym_index=homonym_index,
            register_position=position,
        )
        entry_tokens = _tokens(html)
        if entry_tokens is None:
            raise SessionInvalid("entry_missing_viewstate")
        for kind, control in _present_tabs(html):
            tab_fields = _form_fields(
                entry_tokens,
                spelling=spelling,
                extra=_image_click(control),
            )
            tab_html, tab_request = self.client.exchange("POST", tab_fields)
            self._keep(
                spelling,
                "tab",
                tab_html,
                tab_request,
                homonym_index=homonym_index,
                tab_kind=kind,
                register_position=position,
            )

    def _keep(
        self,
        spelling: str,
        role: str,
        html: str,
        request: bytes,
        *,
        homonym_index: int | None = None,
        tab_kind: str = "",
        register_position: str = "",
    ) -> None:
        body = html.encode("utf-8")
        response_sha = _sha256(body)
        request_sha = _sha256(request)
        _store_blob(self.cache, response_sha, body, "text/html; charset=utf-8")
        _store_blob(self.cache, request_sha, request, "application/json")
        self.cache.commit()
        self.ledger.record_response(
            spelling=spelling,
            role=role,
            response_sha256=response_sha,
            request_sha256=request_sha,
            homonym_index=homonym_index,
            tab_kind=tab_kind,
            register_position=register_position,
        )
        size = _register_size(html)
        if size is not None:
            prior = self.ledger.meta("register_size")
            self.ledger.set_meta("register_size", str(size))
            if not prior:
                print(f"discovered register size: {size}", file=sys.stderr, flush=True)


def _matching(rows: Sequence[Mapping[str, Any]], spelling: str) -> list[dict[str, Any]]:
    target = normalize_ulif_spelling(spelling)
    return [dict(row) for row in rows if normalize_ulif_spelling(str(row["unstressed"])) == target]


def _dedupe_register_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Keep register order; drop only a repeated physical row identity.

    Identity is ``(page_delta, select)`` — the page fork plus the ``Select$N``
    postback ``_open_entry`` sends. Display text is never a key: same-stress
    homonyms share stressed spelling but have different ``select`` values.
    Adjacent pages observed so far do not repeat a row; this still collapses
    a duplicated identity if page composition ever overlapped.
    """
    seen: set[tuple[int, str]] = set()
    ordered: list[dict[str, Any]] = []
    for row in rows:
        key = (int(row["page_delta"]), str(row["select"]))
        if key in seen:
            continue
        seen.add(key)
        ordered.append(dict(row))
    return ordered


def _load_body(cache: sqlite3.Connection, digest: str) -> str:
    row = cache.execute(
        "SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256 = ?",
        (digest,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing raw response {digest}")
    body = bytes(row[0])
    return body.decode("utf-8")


def _ledger_data_mode(ledger: SpellingLedger) -> str | None:
    """Identify one ledger's fetch mode; reject evidence from both modes."""
    declared = ledger.meta("mode")
    has_walk = declared == "walk" or bool(
        ledger.conn.execute("SELECT 1 FROM register_pages UNION ALL SELECT 1 FROM register_rows LIMIT 1").fetchone()
    )
    has_run = declared == "run" or bool(
        ledger.conn.execute(
            "SELECT 1 FROM responses WHERE role IN ('seed', 'tsearch', 'page:back', 'page:next') LIMIT 1"
        ).fetchone()
    )
    if not has_walk and ledger.conn.execute("SELECT 1 FROM spellings LIMIT 1").fetchone():
        has_run = True  # Legacy targeted ledgers did not record a mode.
    if (
        has_walk
        and ledger.conn.execute(
            "SELECT 1 FROM spellings AS s WHERE NOT EXISTS "
            "(SELECT 1 FROM register_rows AS r WHERE r.normalized_spelling = s.spelling) LIMIT 1"
        ).fetchone()
    ):
        has_run = True
    if has_walk and has_run:
        raise ValueError("mixed targeted run and walk data in --state-dir; use separate state directories")
    return "walk" if has_walk else "run" if has_run else None


def _tabs_for_entry_attempt(
    ledger: SpellingLedger, spelling: str, register_position: str, entry_sha: str
) -> list[sqlite3.Row]:
    """Tabs after the completed entry response, before any later attempt at its position."""
    entry = ledger.conn.execute(
        "SELECT id FROM responses WHERE spelling = ? AND role = 'entry' "
        "AND register_position = ? AND response_sha256 = ? ORDER BY id DESC LIMIT 1",
        (spelling, register_position, entry_sha),
    ).fetchone()
    if entry is None:
        raise RuntimeError(f"completed entry response missing for {spelling} at {register_position}")
    entry_id = int(entry["id"])
    next_entry = ledger.conn.execute(
        "SELECT MIN(id) FROM responses WHERE spelling = ? AND role = 'entry' AND register_position = ? AND id > ?",
        (spelling, register_position, entry_id),
    ).fetchone()[0]
    return list(
        ledger.conn.execute(
            "SELECT * FROM responses WHERE spelling = ? AND role = 'tab' "
            "AND register_position = ? AND id > ? AND (? IS NULL OR id < ?) ORDER BY id",
            (spelling, register_position, entry_id, next_entry, next_entry),
        )
    )


def parse_stored(ledger: SpellingLedger, cache: sqlite3.Connection) -> int:
    """Parse one-mode stored bodies offline; reject mixed run/walk ledgers."""
    from scripts.wiki.sources_db import store_ulif_dictua_entry

    mode = _ledger_data_mode(ledger)
    differing = 0
    spellings = [
        str(row["spelling"])
        for row in ledger.conn.execute("SELECT spelling FROM spellings WHERE state = 'stored' ORDER BY spelling")
    ]
    total_spellings = len(spellings)
    # Walk ledgers bind each entry to a completed register row.
    walk_mode = mode == "walk"
    entries_written = 0
    skipped_positions = 0
    mismatch_errors = 0

    for idx, spelling in enumerate(spellings, start=1):
        if idx % 500 == 0:
            pct = (idx / total_spellings * 100.0) if total_spellings else 100.0
            print(
                f"[parse] {idx}/{total_spellings} spellings parsed ({pct:.1f}%)",
                file=sys.stderr,
                flush=True,
            )
        parsed_rows: list[dict[str, Any]] = []
        section_sets: list[dict[str, object]] = []
        raw_sets: list[dict[str, str]] = []
        if walk_mode:
            completed_rows = ledger.completed_rows_for_spelling(spelling)
            completed_positions = {f"{row['page_num']}:{row['row_index']}" for row in completed_rows}
            response_positions = {str(entry["register_position"]) for entry in ledger.entry_responses(spelling)}
            skipped_positions += len(response_positions - completed_positions)
            entries = [
                (index, f"{row['page_num']}:{row['row_index']}", str(row["entry_sha256"]))
                for index, row in enumerate(completed_rows, start=1)
            ]
        else:
            entries = [
                (int(entry["homonym_index"]), str(entry["register_position"]), str(entry["response_sha256"]))
                for entry in ledger.entry_responses(spelling)
            ]
        if not entries:
            continue
        for homonym_index, register_position, entry_sha in entries:
            html = _load_body(cache, entry_sha)
            parsed = parse_ulif_entry(
                html,
                homonym_index=homonym_index,
                register_position=register_position,
            )
            sections: dict[str, object] = {}
            raw: dict[str, str] = {}
            for tab in _tabs_for_entry_attempt(ledger, spelling, register_position, entry_sha):
                kind = str(tab["tab_kind"])
                tab_html = _load_body(cache, str(tab["response_sha256"]))
                raw[kind] = tab_html
                if kind == "paradigm":
                    paradigm = parse_ulif_paradigm(tab_html)
                    if paradigm is not None:
                        sections["paradigm"] = paradigm
                elif kind in {"synonyms", "antonyms", "phraseology"}:
                    groups = parse_ulif_relation_groups(tab_html, kind)
                    if groups:
                        sections[kind] = groups
            parsed_rows.append(parsed)
            section_sets.append(sections)
            raw_sets.append(raw)
        _record_printed_numbers(ledger, spelling, parsed_rows)
        mismatch = _printed_number_mismatch(parsed_rows)
        if mismatch is not None:
            mismatch_errors += 1
            register, printed = mismatch
            row = ledger.conn.execute(
                "SELECT entry_count, straddled_boundary FROM spellings WHERE spelling = ?",
                (spelling,),
            ).fetchone()
            ledger.mark(
                spelling,
                "error",
                entry_count=int(row["entry_count"]) if row is not None else len(parsed_rows),
                straddled=bool(row["straddled_boundary"]) if row is not None else False,
                error=(f"printed_number_mismatch register={list(register)} printed={list(printed)}"),
            )
            continue
        differing += _write_group(cache, spelling, parsed_rows, section_sets, raw_sets, store_ulif_dictua_entry)
        entries_written += len(parsed_rows)
        ledger.set_duplicate_content(spelling, _duplicate_content(parsed_rows))
    ledger.set_meta("differing_content_hashes", str(differing))
    print(
        f"parse complete: {total_spellings} spellings parsed, {entries_written} entries written, "
        f"{differing} groups differed, {mismatch_errors} printed_number_mismatch errors, "
        f"positions skipped: {skipped_positions}",
        file=sys.stderr,
        flush=True,
    )
    return differing


def _printed_number_mismatch(
    parsed_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[int], list[int]] | None:
    """When every entry prints a number, it must equal register-order indexes."""
    if not parsed_rows:
        return None
    printed_raw = [row.get("printed_homonym_number") for row in parsed_rows]
    if any(value is None or str(value).strip() == "" for value in printed_raw):
        return None
    register = [int(row["homonym_index"]) for row in parsed_rows]
    printed = [int(str(value)) for value in printed_raw]
    if printed == register:
        return None
    return register, printed


def _record_printed_numbers(
    ledger: SpellingLedger,
    spelling: str,
    parsed_rows: Sequence[Mapping[str, Any]],
) -> None:
    """Persist printed numbers in the ledger; ``ulif_dictua_entries`` has no column."""
    payload = {
        "register": [int(row["homonym_index"]) for row in parsed_rows],
        "printed": [
            None if row.get("printed_homonym_number") is None else str(row["printed_homonym_number"])
            for row in parsed_rows
        ],
    }
    ledger.set_meta(
        f"printed_homonym_numbers:{normalize_ulif_spelling(spelling)}",
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
    )


def _duplicate_content(parsed_rows: Sequence[Mapping[str, Any]]) -> bool:
    """True when two entries share both sense_gloss and content_sha256."""
    seen: set[tuple[str, str]] = set()
    for row in parsed_rows:
        key = (str(row.get("sense_gloss", "")), str(row.get("content_sha256", "")))
        if key in seen:
            return True
        seen.add(key)
    return False


def _write_group(
    cache: sqlite3.Connection,
    spelling: str,
    parsed_rows: list[dict[str, Any]],
    section_sets: list[dict[str, object]],
    raw_sets: list[dict[str, str]],
    store,
) -> int:
    normalized = normalize_ulif_spelling(spelling)
    existing = list(
        cache.execute(
            """
            SELECT homonym_index, content_sha256
            FROM ulif_dictua_entries
            WHERE normalized_query = ?
            ORDER BY homonym_index
            """,
            (normalized,),
        )
    )
    differing = 0
    if existing:
        same_count = len(existing) == len(parsed_rows)
        same_hashes = same_count and all(
            str(ex[1] or "") == str(pr["content_sha256"]) and str(ex[1] or "") != ""
            for ex, pr in zip(existing, parsed_rows, strict=True)
        )
        if same_hashes:
            cache.execute(
                """
                UPDATE ulif_dictua_entries
                SET homonym_checked = 1
                WHERE normalized_query = ?
                """,
                (normalized,),
            )
            cache.commit()
            return 0
        differing = 1
    keep = {int(row["homonym_index"]) for row in parsed_rows}
    stale_ids = [
        int(row[0])
        for row in cache.execute(
            "SELECT id, homonym_index FROM ulif_dictua_entries WHERE normalized_query = ?",
            (normalized,),
        )
        if int(row[1]) not in keep
    ]
    try:
        if stale_ids:
            marks = ",".join("?" for _ in stale_ids)
            cache.execute(f"DELETE FROM ulif_dictua_sections WHERE entry_id IN ({marks})", stale_ids)
            cache.execute(f"DELETE FROM ulif_dictua_entries WHERE id IN ({marks})", stale_ids)
        for parsed, sections, raw in zip(parsed_rows, section_sets, raw_sets, strict=True):
            store(
                word=normalized,
                canonical_headword=str(parsed["canonical_headword"]),
                sections=sections,
                raw_responses=raw,
                retrieved_at=_now_iso(),
                parser_version=ULIF_PARSER_VERSION,
                status="ok",
                homonym_index=int(parsed["homonym_index"]),
                grammatical_label=str(parsed["grammatical_label"]),
                sense_gloss=str(parsed["sense_gloss"]),
                register_position=str(parsed["register_position"]),
                homonym_checked=1,
                content_sha256=str(parsed["content_sha256"]),
                db_path=_db_path(cache),
                conn=cache,
            )
        cache.commit()
    except Exception:
        cache.rollback()
        raise
    return differing


def _db_path(conn: sqlite3.Connection) -> str:
    row = conn.execute("PRAGMA database_list").fetchone()
    if row is None or not row[2]:
        raise RuntimeError("cache connection has no file path")
    return str(row[2])


def prepare_database(db_path: Path) -> sqlite3.Connection:
    """Open the cache, creating the current schema, or raise before any DDL on an old one."""
    from scripts.wiki.sources_db import _ulif_dictua_conn

    if not db_path.parent.exists():
        _ensure_private_dir(db_path.parent)
    created = not db_path.exists()
    conn = _ulif_dictua_conn(db_path, create=True)
    assert conn is not None
    if created:
        _ensure_private_file(db_path)
    # The walk is the writer that needs concurrency: evidence readers pin one
    # snapshot per session, which only WAL lets coexist with commits (#8527).
    # WAL is a persistent file property, so this is a no-op on an already-WAL
    # file and a loud failure when SQLite cannot honour it.
    try:
        mode = str(conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
    except sqlite3.Error:
        conn.close()
        raise
    if mode != "wal":
        conn.close()
        raise RuntimeError(
            f"{db_path} is in journal_mode={mode!r}, expected 'wal'; the walk must not "
            "run in a mode where pinned readers block its commits"
        )
    return conn


def _spellings_from_file(path: Path) -> list[str]:
    found: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.split("\t", 1)[0].strip()
        if not text or text.startswith("#"):
            continue
        found.append(text)
    return found


def _requests_transport(user_agent: str) -> Transport:
    import requests

    session = requests.Session()
    session.headers["User-Agent"] = user_agent

    def send(method: str, data: dict[str, str] | None) -> HttpResult:
        response = session.request(method, ULIF_URL, data=data, timeout=REQUEST_TIMEOUT_SECONDS)
        return HttpResult(response.status_code, response.text, dict(response.headers))

    return send


def resolve_progress_interval(explicit: float | None = None) -> float:
    """Flag wins. Otherwise ``ULIF_PROGRESS_INTERVAL_SECONDS``, else 60s."""
    if explicit is None:
        raw = os.environ.get(PROGRESS_INTERVAL_ENV, "").strip()
        if not raw:
            return DEFAULT_PROGRESS_INTERVAL_SECONDS
        try:
            explicit = float(raw)
        except ValueError as exc:
            raise ValueError(f"{PROGRESS_INTERVAL_ENV} must be a positive finite number, got {raw!r}") from exc
    if not math.isfinite(explicit) or explicit <= 0:
        raise ValueError(f"progress interval must be a finite number > 0, got {explicit}")
    return explicit


def _immediate_operator_message(what: str) -> bool:
    """Back-off text bypasses the progress rate limit.

    ``PoliteClient`` only sends ``waiting for back-off`` and ``waiting for response``.
    """
    return what.startswith("waiting for back-off")


def format_periodic_progress(
    *,
    kind: str,
    done: int,
    total: int,
    requests_made: int,
    process_requests: int,
    elapsed_seconds: float,
    eta_seconds: float | None,
) -> str:
    """``requests=`` is the cumulative ledger count. ``rate=`` is this process only."""
    rate = (process_requests / elapsed_seconds) if elapsed_seconds > 0 else 0.0
    eta = "unknown" if eta_seconds is None else f"{eta_seconds:.0f}s"
    return f"progress: {kind}={done}/{total} requests={requests_made} rate={rate:.3f}/s eta={eta}"


def _eta_seconds(remaining: int, timed_units: int, wall_seconds: float) -> float | None:
    if remaining <= 0:
        return 0.0
    if timed_units <= 0 or wall_seconds <= 0:
        return None
    return remaining * (wall_seconds / timed_units)


class OperatorProgress:
    """At most one progress line per interval. A failed line never aborts the walk.

    Liveness is the ledger's per-request ``requests_made`` update and ``updated_at``.
    The callback return value is still the delay until the next wake, which
    ``PoliteClient._sleep_with_heartbeat`` uses to slice long waits.
    """

    def __init__(
        self,
        *,
        interval: float,
        clock: ClockFn,
        emit: Callable[[], None],
    ) -> None:
        self.interval = interval
        self.clock = clock
        self.emit = emit
        self._last_emit = clock()
        self._warned_at = -(interval)

    def note_progress(self) -> None:
        self._last_emit = self.clock()

    def __call__(self, what: str) -> float:
        now = self.clock()
        if _immediate_operator_message(what):
            print(f"heartbeat: {what}", file=sys.stderr, flush=True)
            return self.interval
        due_in = self.interval - (now - self._last_emit)
        if due_in <= 0.0:
            try:
                self.emit()
            except Exception as exc:
                if now - self._warned_at >= self.interval:
                    print(f"warning: progress line failed: {exc}", file=sys.stderr, flush=True)
                    self._warned_at = now
            self._last_emit = now
            return self.interval
        return due_in


def _keep_walk(
    ledger: SpellingLedger,
    cache: sqlite3.Connection,
    spelling: str,
    role: str,
    html: str,
    request: bytes,
    *,
    homonym_index: int | None = None,
    tab_kind: str = "",
    register_position: str = "",
    current_page: int | None = None,
) -> None:
    body = html.encode("utf-8")
    response_sha = _sha256(body)
    request_sha = _sha256(request)
    _store_blob(cache, response_sha, body, "text/html; charset=utf-8")
    _store_blob(cache, request_sha, request, "application/json")
    cache.commit()
    ledger.record_response(
        spelling=spelling,
        role=role,
        response_sha256=response_sha,
        request_sha256=request_sha,
        homonym_index=homonym_index,
        tab_kind=tab_kind,
        register_position=register_position,
    )
    size = _register_size(html)
    if size is not None:
        prior_str = ledger.meta("register_size")
        if not prior_str:
            ledger.set_meta("register_size", str(size))
            print(f"discovered register size: {size}", file=sys.stderr, flush=True)
        elif prior_str.isdigit():
            prior = int(prior_str)
            if size != prior:
                ledger.set_meta("register_size", str(size))
                p_num = current_page if current_page is not None else 0
                changes_raw = ledger.meta("register_size_changes", "[]")
                try:
                    changes = json.loads(changes_raw)
                except Exception:
                    changes = []
                changes.append({"page": p_num, "old": prior, "new": size, "recorded_at": _now_iso()})
                ledger.set_meta("register_size_changes", json.dumps(changes))
                ledger.set_meta("register_size_changes_count", str(len(changes)))
                print(f"warning: register size changed on page {p_num}: {prior} -> {size}", file=sys.stderr, flush=True)


def _commit_spelling_group(
    ledger: SpellingLedger,
    cache: sqlite3.Connection,
    normalized_spelling: str,
) -> int:
    """Atomically persist a completed spelling group from walk ledger into cache."""
    completed_rows = ledger.completed_rows_for_spelling(normalized_spelling)
    if not completed_rows:
        return 0

    if ledger.state_of(normalized_spelling) == "stored":
        return 0

    parsed_rows: list[dict[str, Any]] = []
    section_sets: list[dict[str, object]] = []
    raw_sets: list[dict[str, str]] = []

    for homonym_index, r in enumerate(completed_rows, start=1):
        p_num = int(r["page_num"])
        r_idx = int(r["row_index"])
        reg_pos = f"{p_num}:{r_idx}"

        ledger.conn.execute(
            "UPDATE register_rows SET homonym_index = ? WHERE page_num = ? AND row_index = ?",
            (homonym_index, p_num, r_idx),
        )
        ledger.conn.execute(
            "UPDATE responses SET homonym_index = ? WHERE spelling = ? AND register_position = ?",
            (homonym_index, normalized_spelling, reg_pos),
        )

        entry_html = _load_body(cache, str(r["entry_sha256"]))
        parsed = parse_ulif_entry(entry_html, homonym_index=homonym_index, register_position=reg_pos)

        sections: dict[str, object] = {}
        raw: dict[str, str] = {}
        for tab in _tabs_for_entry_attempt(ledger, normalized_spelling, reg_pos, str(r["entry_sha256"])):
            kind = str(tab["tab_kind"])
            tab_html = _load_body(cache, str(tab["response_sha256"]))
            raw[kind] = tab_html
            if kind == "paradigm":
                paradigm = parse_ulif_paradigm(tab_html)
                if paradigm is not None:
                    sections["paradigm"] = paradigm
            elif kind in {"synonyms", "antonyms", "phraseology"}:
                groups = parse_ulif_relation_groups(tab_html, kind)
                if groups:
                    sections[kind] = groups

        parsed_rows.append(parsed)
        section_sets.append(sections)
        raw_sets.append(raw)

    ledger.conn.commit()

    from scripts.wiki.sources_db import store_ulif_dictua_entry

    differing = _write_group(cache, normalized_spelling, parsed_rows, section_sets, raw_sets, store_ulif_dictua_entry)
    if differing > 0:
        cur_diff = int(ledger.meta("differing_groups", "0") or "0")
        ledger.set_meta("differing_groups", str(cur_diff + differing))

    _record_printed_numbers(ledger, normalized_spelling, parsed_rows)
    mismatch = _printed_number_mismatch(parsed_rows)
    if mismatch is not None:
        register, printed = mismatch
        ledger.record_printed_mismatch(normalized_spelling, register, printed)

    pages_seen = {int(r["page_num"]) for r in completed_rows}
    straddled = len(pages_seen) > 1

    ledger.ensure(normalized_spelling)
    ledger.mark(normalized_spelling, "stored", entry_count=len(parsed_rows), straddled=straddled)
    ledger.set_duplicate_content(normalized_spelling, _duplicate_content(parsed_rows))
    return differing


def _print_start_banner(
    *,
    raw_count: int,
    distinct_count: int,
    dup_count: int,
    already_finished: int,
    to_do: int,
    delay_seconds: float,
    state_dir: Path,
    db_path: Path,
    register_size: str,
) -> None:
    print("=== ULIF Homonym Fetch Runner ===", file=sys.stderr)
    print(f"Spellings in file:             {raw_count}", file=sys.stderr)
    if dup_count > 0:
        print(f"Distinct after normalisation:  {distinct_count} ({dup_count} duplicates)", file=sys.stderr)
    else:
        print(f"Distinct after normalisation:  {distinct_count}", file=sys.stderr)
    print(f"Already finished (skipped):    {already_finished}", file=sys.stderr)
    print(f"To do in this run:             {to_do}", file=sys.stderr)
    print(f"Delay between requests:        {delay_seconds:.1f}s", file=sys.stderr)
    print(f"State directory:               {state_dir}", file=sys.stderr)
    print(f"Database path:                 {db_path}", file=sys.stderr)
    print(f"Register size:                 {register_size}", file=sys.stderr)
    print("=================================", file=sys.stderr, flush=True)


def _format_progress_line(
    *,
    finished_count: int,
    total_count: int,
    state: str,
    entry_count: int,
    req_count: int,
    total_req: int,
    err_count: int,
    retry_count: int,
    elapsed_seconds: float,
    eta_str: str,
    spelling: str,
) -> str:
    pct = (finished_count / total_count * 100.0) if total_count else 0.0
    h = int(elapsed_seconds // 3600)
    m = int((elapsed_seconds % 3600) // 60)
    s = int(elapsed_seconds % 60)
    elapsed_str = f"{h}:{m:02d}:{s:02d}"

    state_str = f"{state:<13}" if len(state) <= 13 else f"{state} "

    return (
        f"[{finished_count:5d}/{total_count:<5d} {pct:5.1f}%] {state_str}"
        f"entries={entry_count} req={req_count}  "
        f"total_req={total_req} err={err_count} retry={retry_count}  "
        f"elapsed={elapsed_str}  eta={eta_str}  "
        f"{spelling}"
    )


def _print_stop_summary(
    *,
    reason: str,
    ledger: SpellingLedger | None = None,
    requests_in_process: int,
    elapsed_seconds: float,
    resume_cmd: str,
) -> None:
    if ledger is not None:
        counts = ledger.counts()
    else:
        counts = {
            "spellings_total": 0,
            "stored": 0,
            "absent_from_ulif": 0,
            "retry_scheduled": 0,
            "error": 0,
            "pending": 0,
            "entries_stored": 0,
        }
    h = int(elapsed_seconds // 3600)
    m = int((elapsed_seconds % 3600) // 60)
    s = int(elapsed_seconds % 60)
    elapsed_str = f"{h}:{m:02d}:{s:02d}"
    print("=== ULIF Fetch Stop Summary ===", file=sys.stderr)
    print(f"Reason:               {reason}", file=sys.stderr)
    print(f"Spellings total:      {counts['spellings_total']}", file=sys.stderr)
    print(f"Stored:               {counts['stored']}", file=sys.stderr)
    print(f"Absent from ULIF:     {counts['absent_from_ulif']}", file=sys.stderr)
    print(f"Retry scheduled:      {counts['retry_scheduled']}", file=sys.stderr)
    print(f"Errors:               {counts['error']}", file=sys.stderr)
    print(f"Pending:              {counts['pending']}", file=sys.stderr)
    print(f"Entries stored:       {counts['entries_stored']}", file=sys.stderr)
    print(f"Requests in run:      {requests_in_process}", file=sys.stderr)
    print(f"Elapsed time:         {elapsed_str}", file=sys.stderr)
    print(f"Resume command:       {resume_cmd}", file=sys.stderr)
    print("===============================", file=sys.stderr, flush=True)


def _print_walk_start_banner(
    *,
    start_page: int,
    pages_done: int,
    pages_total: int,
    to_do_pages: int,
    delay_seconds: float,
    state_dir: Path,
    db_path: Path,
    register_size: str,
) -> None:
    print("=== ULIF Register Walk Runner ===", file=sys.stderr)
    print(f"Starting page:                 {start_page}", file=sys.stderr)
    print(f"Already finished pages:        {pages_done}", file=sys.stderr)
    print(f"Total pages in register:       {pages_total if pages_total else 'unknown'}", file=sys.stderr)
    print(f"Pages to do in this run:       {to_do_pages}", file=sys.stderr)
    print(f"Delay between requests:        {delay_seconds:.1f}s", file=sys.stderr)
    print(f"State directory:               {state_dir}", file=sys.stderr)
    print(f"Database path:                 {db_path}", file=sys.stderr)
    print(f"Register size:                 {register_size}", file=sys.stderr)
    print("=================================", file=sys.stderr, flush=True)


def _format_walk_progress_line(
    *,
    pages_done: int,
    pages_total: int,
    entries_stored: int,
    page_req: int,
    total_req: int,
    err_count: int,
    retry_count: int,
    elapsed_seconds: float,
    eta_str: str,
    page_num: int,
) -> str:
    pct = (pages_done / pages_total * 100.0) if pages_total else 0.0
    h = int(elapsed_seconds // 3600)
    m = int((elapsed_seconds % 3600) // 60)
    s = int(elapsed_seconds % 60)
    elapsed_str = f"{h}:{m:02d}:{s:02d}"
    return (
        f"[{pages_done:5d}/{pages_total:<5d} {pct:5.1f}%] page_completed "
        f"entries={entries_stored} req={page_req}  "
        f"total_req={total_req} err={err_count} retry={retry_count}  "
        f"elapsed={elapsed_str}  eta={eta_str}  "
        f"page={page_num}"
    )


def _print_walk_stop_summary(
    *,
    reason: str,
    ledger: SpellingLedger | None = None,
    requests_in_process: int,
    elapsed_seconds: float,
    resume_cmd: str,
) -> None:
    if ledger is not None:
        counts = ledger.walk_counts()
    else:
        counts = {
            "pages_done": 0,
            "pages_total": 0,
            "entries_stored": 0,
            "spellings": 0,
            "multi_entry_spellings": 0,
            "differing_groups": 0,
        }
    h = int(elapsed_seconds // 3600)
    m = int((elapsed_seconds % 3600) // 60)
    s = int(elapsed_seconds % 60)
    elapsed_str = f"{h}:{m:02d}:{s:02d}"
    print("=== ULIF Walk Stop Summary ===", file=sys.stderr)
    print(f"Reason:                 {reason}", file=sys.stderr)
    print(f"Pages done / total:     {counts['pages_done']} / {counts['pages_total']}", file=sys.stderr)
    print(f"Entries stored:         {counts['entries_stored']}", file=sys.stderr)
    print(f"Spellings:              {counts['spellings']}", file=sys.stderr)
    print(f"Multi-entry spellings:  {counts['multi_entry_spellings']}", file=sys.stderr)
    print(f"Differing groups:       {counts['differing_groups']}", file=sys.stderr)
    print(f"Requests in run:        {requests_in_process}", file=sys.stderr)
    print(f"Elapsed time:           {elapsed_str}", file=sys.stderr)
    print(f"Resume command:         {resume_cmd}", file=sys.stderr)
    print("==============================", file=sys.stderr, flush=True)


def _restore_pending(ledger: SpellingLedger, spelling: str) -> None:
    """Safely restore a spelling to pending and clear partial responses across interrupts."""
    interrupted = False
    for _ in range(3):
        try:
            ledger.clear_responses(spelling)
            ledger.mark(spelling, "pending")
            break
        except (KeyboardInterrupt, InterruptedByOperator):
            interrupted = True
        except Exception:
            break
    if interrupted:
        raise InterruptedByOperator()


def run_fetch(
    *,
    spellings: Sequence[str],
    state_dir: Path,
    db_path: Path,
    delay_seconds: float = MIN_DELAY_SECONDS,
    max_spellings: int | None = None,
    max_requests: int | None = None,
    refetch: bool = False,
    break_stale_lock: bool = False,
    quiet: bool = False,
    spellings_file: Path | None = None,
    resume_cmd: str | None = None,
    transport: Transport | None = None,
    sleep: SleepFn = _default_sleep,
    clock: ClockFn = time.monotonic,
    scanner: Scanner = scan_for_legacy_crawler,
    progress_interval: float | None = None,
) -> int:
    if resume_cmd:
        resolved_resume_cmd = resume_cmd
    else:
        cmd_parts = [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.fetch_ulif_homonyms",
            "run",
            "--state-dir",
            str(state_dir),
            "--db",
            str(db_path),
            "--delay",
            f"{delay_seconds:g}",
        ]
        if spellings_file:
            cmd_parts.extend(["--spellings-file", str(spellings_file)])
        if max_spellings is not None:
            cmd_parts.extend(["--max-spellings", str(max_spellings)])
        if max_requests is not None:
            cmd_parts.extend(["--max-requests", str(max_requests)])
        if refetch:
            cmd_parts.append("--refetch")
        if break_stale_lock:
            cmd_parts.append("--break-stale-lock")
        if quiet:
            cmd_parts.append("--quiet")
        if progress_interval is not None:
            cmd_parts.extend(["--progress-interval", f"{progress_interval:g}"])
        resolved_resume_cmd = shlex.join(cmd_parts)

    try:
        progress_every = resolve_progress_interval(progress_interval)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    if delay_seconds < MIN_DELAY_SECONDS:
        print(f"delay must be >= {MIN_DELAY_SECONDS}", file=sys.stderr)
        _print_stop_summary(
            reason=f"delay must be >= {MIN_DELAY_SECONDS}",
            ledger=None,
            requests_in_process=0,
            elapsed_seconds=0.0,
            resume_cmd=resolved_resume_cmd,
        )
        return EXIT_USAGE

    stop_reason = "finished"
    return_code = EXIT_OK
    start_time = clock()
    base_requests = 0
    process_units_finished = 0
    process_wall_time = 0.0

    lock: RunnerLock | None = None
    ledger: SpellingLedger | None = None
    cache: sqlite3.Connection | None = None
    client: PoliteClient | None = None

    old_sigterm = None
    if threading.current_thread() is threading.main_thread():

        def _on_sigterm(signum: int, frame: Any) -> None:
            raise InterruptedByOperator("SIGTERM")

        with contextlib.suppress(ValueError, OSError):
            old_sigterm = signal.signal(signal.SIGTERM, _on_sigterm)

    def _emit_fetch_progress() -> None:
        if ledger is None:
            return
        counts = ledger.counts()
        finished = counts["stored"] + counts["absent_from_ulif"] + counts["retry_scheduled"] + counts["error"]
        process_requests = client.requests_made if client is not None else 0
        requests_made = base_requests + process_requests
        timed = int(ledger.meta("cumulative_timed_units", "0") or "0")
        wall = float(ledger.meta("cumulative_wall_seconds", "0.0") or "0.0")
        remaining = counts["pending"] + counts["retry_scheduled"] + counts["error"]
        line = format_periodic_progress(
            kind="spellings",
            done=finished,
            total=counts["spellings_total"],
            requests_made=requests_made,
            process_requests=process_requests,
            elapsed_seconds=clock() - start_time,
            eta_seconds=_eta_seconds(remaining, timed, wall),
        )
        print(line, file=sys.stderr, flush=True)

    on_heartbeat = OperatorProgress(
        interval=progress_every,
        clock=clock,
        emit=_emit_fetch_progress,
    )

    try:
        try:
            _ensure_private_dir(state_dir)
            lock = RunnerLock(state_dir, break_stale=break_stale_lock, scanner=scanner)
            lock.acquire()

            try:
                cache = prepare_database(db_path)
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                return_code = EXIT_USAGE
                stop_reason = f"database error: {exc}"
            else:
                ledger = SpellingLedger(state_dir / "ledger.sqlite")
                try:
                    existing_mode = _ledger_data_mode(ledger)
                    if existing_mode == "walk":
                        raise ValueError("walk data in --state-dir; targeted run requires a separate state directory")
                except ValueError as exc:
                    print(f"refusing to start: {exc}", file=sys.stderr)
                    return EXIT_USAGE
                ledger.set_meta("mode", "run")
                ledger.set_meta("delay_seconds", str(delay_seconds))
                base_requests = int(ledger.meta("requests_made", "0") or "0")

                raw_count = len(spellings)
                normalized_list: list[str] = []
                seen: set[str] = set()
                dup_count = 0
                for s in spellings:
                    key = normalize_ulif_spelling(s)
                    if not key:
                        continue
                    if key in seen:
                        dup_count += 1
                        continue
                    seen.add(key)
                    normalized_list.append(key)
                distinct_count = len(normalized_list)

                for spelling in normalized_list:
                    ledger.ensure(spelling)

                already_finished = 0
                for spelling in normalized_list:
                    st = ledger.state_of(spelling)
                    if st in COMPLETE_STATES and not refetch:
                        already_finished += 1
                to_do = distinct_count - already_finished
                if max_spellings is not None:
                    to_do = min(to_do, max_spellings)

                register_size_str = ledger.meta("register_size", "") or "unknown"
                _print_start_banner(
                    raw_count=raw_count,
                    distinct_count=distinct_count,
                    dup_count=dup_count,
                    already_finished=already_finished,
                    to_do=to_do,
                    delay_seconds=delay_seconds,
                    state_dir=state_dir,
                    db_path=db_path,
                    register_size=register_size_str,
                )

                def _on_request(req_in_proc: int) -> None:
                    if ledger is not None:
                        with contextlib.suppress(Exception):
                            ledger.set_requests_made(base_requests + req_in_proc)

                client = PoliteClient(
                    transport or _requests_transport(declared_user_agent()),
                    delay_seconds=delay_seconds,
                    sleep=sleep,
                    clock=clock,
                    max_requests=max_requests,
                    heartbeat=on_heartbeat,
                    on_request=_on_request,
                )
                fetcher = HomonymFetcher(client, ledger, cache)
                consecutive_retries = 0
                processed = 0

                for spelling in normalized_list:
                    state = ledger.state_of(spelling)
                    if state in COMPLETE_STATES and not refetch:
                        continue
                    if max_spellings is not None and processed >= max_spellings:
                        stop_reason = "max spellings"
                        break

                    unit_start_clock = clock()
                    unit_start_requests = client.requests_made
                    outcome: UnitOutcome | None = None
                    unit_state = ""

                    try:
                        if refetch and state in COMPLETE_STATES:
                            _restore_pending(ledger, spelling)
                        try:
                            outcome = fetcher.fetch(spelling)
                            unit_state = outcome.state
                            ledger.mark(
                                spelling,
                                outcome.state,
                                entry_count=outcome.entry_count,
                                straddled=outcome.straddled,
                            )
                        except RequestCap:
                            _restore_pending(ledger, spelling)
                            stop_reason = "request cap"
                            break
                        except Forbidden:
                            ledger.mark(spelling, "error", error="http_403")
                            unit_state = "error"
                            stop_reason = "HTTP 403"
                            return_code = EXIT_FORBIDDEN
                            print("stopping: HTTP 403 from ULIF", file=sys.stderr)
                        except RequestExhausted as exc:
                            unit_state = "retry_scheduled"
                            ledger.mark(spelling, "retry_scheduled", error=exc.code)
                        except SessionInvalid as exc:
                            unit_state = "retry_scheduled"
                            ledger.mark(spelling, "retry_scheduled", error=str(exc))
                    except (KeyboardInterrupt, InterruptedByOperator):
                        with contextlib.suppress(BaseException):
                            _restore_pending(ledger, spelling)
                        stop_reason = "interrupted by operator"
                        return_code = EXIT_INTERRUPTED
                        break
                    except Exception as exc:
                        with contextlib.suppress(BaseException):
                            _restore_pending(ledger, spelling)
                        stop_reason = str(exc)
                        return_code = EXIT_INTERRUPTED
                        print(f"interrupted on {spelling}: {exc}", file=sys.stderr)
                        break

                    if stop_reason == "request cap":
                        break

                    unit_wall = clock() - unit_start_clock
                    process_wall_time += unit_wall
                    process_units_finished += 1
                    processed += 1

                    if client.requests_made > 0:
                        ledger.set_requests_made(base_requests + client.requests_made)

                    cum_wall = float(ledger.meta("cumulative_wall_seconds", "0.0") or "0.0") + unit_wall
                    cum_units = int(ledger.meta("cumulative_timed_units", "0") or "0") + 1
                    ledger.set_meta("cumulative_wall_seconds", str(cum_wall))
                    ledger.set_meta("cumulative_timed_units", str(cum_units))

                    if not quiet:
                        counts = ledger.counts()
                        finished_total = (
                            counts["stored"] + counts["absent_from_ulif"] + counts["retry_scheduled"] + counts["error"]
                        )
                        total_planned = counts["spellings_total"]
                        unit_req = client.requests_made - unit_start_requests
                        tot_req = base_requests + client.requests_made
                        if process_units_finished < 5:
                            eta_s = "?"
                        else:
                            rem_units = max(0, to_do - process_units_finished)
                            if rem_units == 0:
                                eta_s = "0:00:00"
                            else:
                                mean_w = process_wall_time / process_units_finished
                                eta_sec = rem_units * mean_w
                                eh = int(eta_sec // 3600)
                                em = int((eta_sec % 3600) // 60)
                                es = int(eta_sec % 60)
                                eta_s = f"{eh}:{em:02d}:{es:02d}"

                        line = _format_progress_line(
                            finished_count=finished_total,
                            total_count=total_planned,
                            state=unit_state,
                            entry_count=outcome.entry_count if outcome else 0,
                            req_count=unit_req,
                            total_req=tot_req,
                            err_count=counts["error"],
                            retry_count=counts["retry_scheduled"],
                            elapsed_seconds=clock() - start_time,
                            eta_str=eta_s,
                            spelling=spelling,
                        )
                        print(line, file=sys.stderr, flush=True)
                        on_heartbeat.note_progress()

                    if unit_state == "retry_scheduled":
                        consecutive_retries += 1
                        if consecutive_retries >= CONSECUTIVE_RETRY_STOP:
                            stop_reason = "retry storm"
                            return_code = EXIT_RETRY_STORM
                            print(
                                "stopping: three consecutive spellings ended retry_scheduled",
                                file=sys.stderr,
                            )
                            break
                    elif unit_state in COMPLETE_STATES:
                        consecutive_retries = 0

                    if return_code != EXIT_OK:
                        break

        except SystemExit as exc:
            stop_reason = str(exc)
            summary_printed = False
            for _ in range(3):
                try:
                    _print_stop_summary(
                        reason=stop_reason,
                        ledger=ledger,
                        requests_in_process=client.requests_made if client else 0,
                        elapsed_seconds=clock() - start_time,
                        resume_cmd=resolved_resume_cmd,
                    )
                    summary_printed = True
                    break
                except (KeyboardInterrupt, InterruptedByOperator):
                    pass
            if not summary_printed:
                with contextlib.suppress(Exception):
                    sys.stderr.write(
                        f"=== ULIF Fetch Stop Summary ===\nReason:               {stop_reason}\nResume command:       {resolved_resume_cmd}\n===============================\n"
                    )
                    sys.stderr.flush()
            raise
        except (KeyboardInterrupt, InterruptedByOperator):
            stop_reason = "interrupted by operator"
            return_code = EXIT_INTERRUPTED
        except Exception as exc:
            stop_reason = str(exc)
            return_code = EXIT_INTERRUPTED
            print(f"interrupted: {exc}", file=sys.stderr)

        if client is not None and ledger is not None:
            written = False
            for _ in range(5):
                try:
                    ledger.set_requests_made(base_requests + client.requests_made)
                    written = True
                    break
                except (KeyboardInterrupt, InterruptedByOperator):
                    stop_reason = "interrupted by operator"
                    return_code = EXIT_INTERRUPTED
                except Exception as exc:
                    print(
                        f"warning: failed to persist final requests_made ({base_requests + client.requests_made}): {exc}",
                        file=sys.stderr,
                    )
                    break
            if not written:
                try:
                    ledger.conn.execute(
                        "INSERT INTO meta (key, value) VALUES ('requests_made', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (str(base_requests + client.requests_made),),
                    )
                    ledger.conn.commit()
                except (KeyboardInterrupt, InterruptedByOperator):
                    stop_reason = "interrupted by operator"
                    return_code = EXIT_INTERRUPTED
                except Exception as exc:
                    print(
                        f"warning: direct execute failed to persist requests_made ({base_requests + client.requests_made}): {exc}",
                        file=sys.stderr,
                    )
                    if stop_reason == "finished":
                        stop_reason = f"persistence error: {exc}"
                    if return_code == EXIT_OK:
                        return_code = EXIT_INTERRUPTED

        summary_printed = False
        for _ in range(3):
            try:
                _print_stop_summary(
                    reason=stop_reason,
                    ledger=ledger,
                    requests_in_process=client.requests_made if client else 0,
                    elapsed_seconds=clock() - start_time,
                    resume_cmd=resolved_resume_cmd,
                )
                summary_printed = True
                break
            except (KeyboardInterrupt, InterruptedByOperator):
                stop_reason = "interrupted by operator"
                return_code = EXIT_INTERRUPTED

        if not summary_printed:
            with contextlib.suppress(BaseException):
                lines = [
                    "=== ULIF Fetch Stop Summary ===",
                    f"Reason:               {stop_reason}",
                    f"Resume command:       {resolved_resume_cmd}",
                    "===============================",
                ]
                print("\n".join(lines), file=sys.stderr, flush=True)
    finally:
        try:
            if cache is not None:
                with contextlib.suppress(Exception):
                    cache.close()
        except (KeyboardInterrupt, InterruptedByOperator):
            return_code = EXIT_INTERRUPTED
            with contextlib.suppress(Exception):
                if cache is not None:
                    cache.close()

        try:
            if ledger is not None:
                with contextlib.suppress(Exception):
                    ledger.close()
        except (KeyboardInterrupt, InterruptedByOperator):
            return_code = EXIT_INTERRUPTED
            with contextlib.suppress(Exception):
                if ledger is not None:
                    ledger.close()

        if lock is not None:
            for _ in range(5):
                try:
                    lock.release()
                    break
                except (KeyboardInterrupt, InterruptedByOperator):
                    return_code = EXIT_INTERRUPTED
                    if lock.path.exists() and lock._held:
                        with contextlib.suppress(OSError):
                            lock.path.unlink()
                        lock._held = False
                    break

        if old_sigterm is not None:
            with contextlib.suppress(ValueError, OSError):
                signal.signal(signal.SIGTERM, old_sigterm)

    return return_code


def _fast_forward_to_page(
    client: PoliteClient,
    ledger: SpellingLedger,
    cache: Any,
    seed_tokens: dict[str, str],
    start_headword: str,
    target_page: int,
    *,
    quiet: bool = False,
) -> tuple[str, list[dict[str, Any]]]:
    """Fast-forward ASPX GridView from page 1 to target_page via canonical nextpage pagination."""
    if not quiet:
        print(
            f"resuming: fast-forwarding from page 1 to page {target_page} via canonical pagination...",
            file=sys.stderr,
            flush=True,
        )
    search_fields = _form_fields(
        seed_tokens,
        spelling=start_headword,
        extra=_image_click(SEARCH_BUTTON),
    )
    current_html, current_req = client.exchange("POST", search_fields)
    _keep_walk(ledger, cache, "", f"tsearch:ff:1:{target_page}", current_html, current_req, current_page=1)

    for ff_page in range(1, target_page):
        tokens = _tokens(current_html)
        if tokens is None or _validation_failure(current_html):
            raise SessionInvalid(f"ff_page_{ff_page}_viewstate")
        rows = parse_register_list(current_html)
        if not rows:
            raise SessionInvalid(f"ff_page_{ff_page}_empty")
        next_fields = _form_fields(
            tokens,
            spelling=str(rows[-1]["unstressed"]),
            extra=_image_click(PAGE_BUTTONS["next"]),
        )
        current_html, next_req = client.exchange("POST", next_fields)
        _keep_walk(
            ledger, cache, "", f"page:ff:{ff_page + 1}:{target_page}", current_html, next_req, current_page=ff_page + 1
        )
        if not quiet and ((ff_page + 1) % 25 == 0 or (ff_page + 1) == target_page):
            print(
                f"fast-forwarding: reached page {ff_page + 1}/{target_page}...",
                file=sys.stderr,
                flush=True,
            )

    landed_rows = parse_register_list(current_html)
    if not landed_rows:
        raise SessionInvalid(f"ff_target_page_{target_page}_empty")
    return current_html, landed_rows


def _listing_rows(ledger: SpellingLedger, page_num: int) -> dict[int, str]:
    """Headwords safe to align a resume window against.

    ``ensure_row`` writes the register listing once, as ``pending``. ``mark_row``
    only moves that row to ``completed``; it does not rewrite the headword.
    Pending and completed rows are the same listing evidence, so both are
    trustworthy. No other row state is written.

    ``start_headword`` is the listing headword of row 0 when the page boundary
    was stored without a row record. A stored row 0 wins over that boundary.
    """
    if page_num < 1:
        return {}
    rows = {int(row["row_index"]): str(row["stressed_headword"]) for row in ledger.page_rows(page_num)}
    page = ledger.get_page(page_num)
    if page is not None and page["start_headword"] and 0 not in rows:
        rows[0] = str(page["start_headword"])
    return rows


def verify_ledger_continuity(path: Path, *, warn_on_overlap: bool = False) -> int:
    """Read only: check recorded page geometry and entry-position evidence.

    The ledger stores entry response hashes and their page/row positions, but
    the response bodies and page-listing HTML live in the separate blob cache.
    This check can compare recorded spellings with entry response metadata; it
    cannot independently reconstruct ULIF's listing or verify response bytes.
    """
    with contextlib.closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        pages = conn.execute("SELECT * FROM register_pages ORDER BY page_num").fetchall()
        entry_positions: dict[str, list[str]] = {}
        for response in conn.execute(
            "SELECT register_position, spelling FROM responses WHERE role = 'entry' AND register_position != ''"
        ):
            position = str(response["register_position"])
            # An interrupted row can have several entry clicks before its tabs
            # finish and mark_row commits completion. Every attempt must still
            # agree with the listing spelling at this position.
            entry_positions.setdefault(position, []).append(str(response["spelling"]))
        initial_search_recorded = (
            conn.execute("SELECT 1 FROM responses WHERE role = 'tsearch:start' LIMIT 1").fetchone() is not None
        )
        checked = 0
        previous_completed_rows: list[sqlite3.Row] | None = None
        for page in pages:
            number = int(page["page_num"])
            if number != checked + 1:
                raise ResumeMismatchError(f"page {number}: ledger page sequence has a gap before this page")
            rows = conn.execute(
                "SELECT row_index, stressed_headword, normalized_spelling, state FROM register_rows "
                "WHERE page_num = ? ORDER BY row_index",
                (number,),
            ).fetchall()
            indexes = [int(row["row_index"]) for row in rows]
            if indexes != list(range(len(rows))):
                raise ResumeMismatchError(f"page {number}: ledger rows are not contiguous from row 0")
            words = [str(row["stressed_headword"]) for row in rows]
            if len(rows) > REGISTER_PAGE_SIZE:
                raise ResumeMismatchError(f"page {number}: row count exceeds page size {REGISTER_PAGE_SIZE}")
            # The first page can be a short search landing (22 rows in the
            # live walk); later nonterminal next-page windows have 25.
            if (
                page["state"] == "completed"
                and 0 < len(rows) < REGISTER_PAGE_SIZE
                and number != len(pages)
                and (number != 1 or not initial_search_recorded)
            ):
                raise ResumeMismatchError(f"page {number}: short page before the last page")
            if words and page["start_headword"] != words[0]:
                raise ResumeMismatchError(f"page {number}: start headword does not match row 0")
            if page["state"] == "completed":
                if words and page["end_headword"] != words[-1]:
                    raise ResumeMismatchError(f"page {number}: end headword does not match last row")
                if int(page["row_count"]) != len(rows):
                    raise ResumeMismatchError(f"page {number}: row count does not match recorded rows")
                if not words or not page["end_headword"]:
                    raise ResumeMismatchError(f"page {number}: completed page lacks listing boundaries")
                if previous_completed_rows is not None:
                    try:
                        _verify_register_continuity(previous_completed_rows, rows, number)
                    except SessionInvalid as exc:
                        message = (
                            f"pages {number - 1} and {number}: suspect cross-page overlap ({exc}); verify manually"
                        )
                        if warn_on_overlap:
                            print(f"ledger continuity warning: {message}", file=sys.stderr)
                        else:
                            raise ResumeMismatchError(message) from exc
                previous_completed_rows = rows
            else:
                if page["row_count"] and len(rows) > int(page["row_count"]):
                    raise ResumeMismatchError(f"page {number}: recorded rows exceed page row count")
                previous_completed_rows = None
            for row in rows:
                index = int(row["row_index"])
                position = f"{number}:{index}"
                if normalize_ulif_spelling(str(row["stressed_headword"])) != row["normalized_spelling"]:
                    raise ResumeMismatchError(f"page {number} row {index}: headword differs from normalized spelling")
                if any(
                    str(row["normalized_spelling"]) != response_spelling
                    for response_spelling in entry_positions.get(position, ())
                ):
                    raise ResumeMismatchError(f"page {number} row {index}: spelling differs from entry response")
            checked += 1
        orphan = conn.execute(
            "SELECT MIN(r.page_num) FROM register_rows r LEFT JOIN register_pages p ON p.page_num = r.page_num "
            "WHERE p.page_num IS NULL"
        ).fetchone()[0]
        if orphan is not None:
            raise ResumeMismatchError(f"page {orphan}: ledger rows have no page record")
    return checked


def align_resume_window(
    headwords: Sequence[str],
    *,
    page_size: int,
    target_rows: Mapping[int, str],
    previous_rows: Mapping[int, str] | None = None,
    page_row_count: int | None = None,
    end_headword: str | None = None,
    target_page: int = 1,
    nonterminal_page: bool = False,
) -> int | None:
    """Return where ``headwords[0]`` sits relative to the target page's row 0.

    The return value is that absolute start. ``0`` is the first row of the
    target page, a negative start is on the previous page, and a positive start
    is a landing inside the target page. ``None`` means more than one start is
    consistent: the caller fast-forwards.

    A start is consistent when every window row that overlaps a trustworthy
    recorded row matches it, and the window fits a known page length and end
    headword. A short window (shorter than ``page_size``) on a page whose row
    count is known is the tail of the register, so it must end on the last row.
    When the recorded page precedes the terminal page, a short window can cross
    its boundary; ``nonterminal_page`` permits that crossing.
    A full window may cross onto the next page; those rows are not an input.

    ``ResumeMismatchError`` is raised only when no start is consistent and some
    geometrically possible start overlaps a recorded row. Page 1 has no
    previous page; ``target_page`` also names mismatched rows.
    """
    if page_size < 1:
        raise ValueError(f"page_size must be positive, got {page_size}")
    if not headwords:
        return None
    previous = previous_rows or {}
    known_count = page_row_count if page_row_count and page_row_count > 0 else None
    limit = known_count if known_count is not None else page_size
    short = len(headwords) < page_size
    end = end_headword or None
    consistent: list[int] = []
    saw_overlap = False
    best: tuple[tuple[int, int, int], str] | None = None

    for origin in range(-page_size if target_page > 1 else 0, limit):
        last = origin + len(headwords) - 1
        if short and known_count is not None and not nonterminal_page and last != known_count - 1:
            continue
        if last >= limit and (
            not nonterminal_page and (short or (known_count is not None and known_count < page_size))
        ):
            continue
        overlaps = 0
        mismatch_count = 0
        mismatch: tuple[str, int, str, str] | None = None
        for index, word in enumerate(headwords):
            coord = origin + index
            if coord < 0:
                prev_index = page_size + coord
                expected = previous.get(prev_index)
                if expected is None:
                    continue
                overlaps += 1
                if expected != word:
                    mismatch_count += 1
                    if mismatch is None:
                        mismatch = ("previous", prev_index, expected, word)
            elif coord < limit:
                expected = target_rows.get(coord)
                if expected is None:
                    continue
                overlaps += 1
                if expected != word:
                    mismatch_count += 1
                    if mismatch is None:
                        mismatch = ("target", coord, expected, word)
        if end is not None and origin <= limit - 1 <= last and headwords[limit - 1 - origin] != end:
            mismatch_count += 1
            if mismatch is None:
                mismatch = ("target", limit - 1, end, headwords[limit - 1 - origin])
        if overlaps:
            saw_overlap = True
        if mismatch_count == 0:
            consistent.append(origin)
            continue
        assert mismatch is not None
        where, row_index, expected, landed = mismatch
        page = target_page if where == "target" else target_page - 1
        message = f"page {page} row {row_index}: expected {expected}, landed {landed}"
        # The closest failed placement is the one with the fewest disagreements.
        rank = (mismatch_count, 0 if where == "target" else 1, -overlaps)
        if best is None or rank < best[0]:
            best = (rank, message)

    if len(consistent) == 1:
        return consistent[0]
    if not consistent and saw_overlap and best is not None and not (nonterminal_page and short):
        raise ResumeMismatchError(best[1])
    return None


def _resume_window_offset(
    ledger: SpellingLedger,
    rows: list[dict[str, Any]],
    *,
    target_page: int,
    anchor_headword: str,
    anchor_page: int,
    anchor_index: int,
    nonterminal_page: bool = False,
) -> int | None:
    """Return how many rows the window starts before the target page, or None.

    This is the ledger adapter for :func:`align_resume_window`. The returned
    offset is the negation of that function's absolute start, which is what
    ``start_global = target_global - offset`` expects. The anchor arguments
    name the search that produced the window; they do not vote on the start.
    """
    del anchor_headword, anchor_page, anchor_index
    if not rows:
        return None
    page = ledger.get_page(target_page)
    row_count = int(page["row_count"]) if page is not None and page["row_count"] else None
    end = str(page["end_headword"]) if page is not None and page["end_headword"] else None
    origin = align_resume_window(
        [str(row["stressed"]) for row in rows],
        page_size=REGISTER_PAGE_SIZE,
        target_rows=_listing_rows(ledger, target_page),
        previous_rows=_listing_rows(ledger, target_page - 1),
        page_row_count=row_count,
        end_headword=end,
        target_page=target_page,
        nonterminal_page=nonterminal_page,
    )
    if origin is None:
        return None
    return -origin


def _verify_known_window_rows(ledger: SpellingLedger, rows: list[dict[str, Any]], start_global: int) -> None:
    """Reject drift at every canonical position already recorded in the ledger."""
    drift = _known_window_drift(ledger, rows, start_global)
    if drift is not None:
        raise ResumeMismatchError(drift)


def _known_window_drift(ledger: SpellingLedger, rows: list[dict[str, Any]], start_global: int) -> str | None:
    """Describe the first known ledger row the window disagrees with, or None."""
    listing: dict[int, dict[int, str]] = {}
    recorded_norm: dict[int, dict[int, str]] = {}
    for index, row in enumerate(rows):
        page_num, row_index = divmod(start_global + index, REGISTER_PAGE_SIZE)
        page_num += 1
        if page_num < 1:
            continue
        if page_num not in listing:
            listing[page_num] = _listing_rows(ledger, page_num)
            recorded_norm[page_num] = {
                int(item["row_index"]): str(item["normalized_spelling"]) for item in ledger.page_rows(page_num)
            }
        expected = listing[page_num].get(row_index)
        if expected is not None and row["stressed"] != expected:
            return f"page {page_num} row {row_index}: expected {expected}, landed {row['stressed']}"
        norm = recorded_norm[page_num].get(row_index)
        if norm is not None and normalize_ulif_spelling(str(row["unstressed"])) != norm:
            return f"page {page_num} row {row_index}: expected {expected}, landed {row['stressed']}"
        if row_index == REGISTER_PAGE_SIZE - 1:
            page = ledger.get_page(page_num)
            end = str(page["end_headword"]) if page is not None and page["end_headword"] else ""
            if end and row["stressed"] != end:
                return f"page {page_num} end_headword: expected {end}, landed {row['stressed']}"
    return None


def _verify_register_continuity(
    preceding: Sequence[Mapping[str, Any] | sqlite3.Row], following: Sequence[Mapping[str, Any]], page_num: int
) -> None:
    """Reject a repeated multi-row window before row writes."""
    if not preceding or not following:
        raise SessionInvalid(f"page_{page_num}_missing_continuity_anchor")

    def headword(row: Mapping[str, Any] | sqlite3.Row) -> str:
        try:
            return str(row["stressed"])
        except (KeyError, IndexError):
            return str(row["stressed_headword"])

    if len(following) >= 2:
        # Repeated homonyms can legitimately straddle a window. Two different
        # spellings repeating together are an overlap; a uniform run needs a
        # longer exact match to distinguish repetition from a reset.
        overlap_size = (
            2
            if normalize_ulif_spelling(headword(following[0])) != normalize_ulif_spelling(headword(following[1]))
            else 6
        )
        if len(following) < overlap_size:
            return
        first_rows = tuple(normalize_ulif_spelling(headword(row)) for row in following[:overlap_size])
        previous = [normalize_ulif_spelling(headword(row)) for row in preceding]
        if any(
            tuple(previous[index : index + overlap_size]) == first_rows
            for index in range(len(previous) - overlap_size + 1)
        ):
            raise SessionInvalid(f"page_{page_num}_register_overlap")


def _verify_first_unrecorded_page(ledger: SpellingLedger, rows: list[dict[str, Any]], start_global: int) -> None:
    """Check each new page's first row against its immediate predecessor."""
    for index in range(len(rows)):
        page_zero, row_index = divmod(start_global + index, REGISTER_PAGE_SIZE)
        if page_zero < 1 or row_index != 0 or ledger.page_rows(page_zero + 1):
            continue
        if index:
            preceding: Sequence[Mapping[str, Any] | sqlite3.Row] = rows[:index]
        else:
            preceding = ledger.page_rows(page_zero)
        _verify_register_continuity(preceding, rows[index:], page_zero + 1)


def _reseed_to_page(
    client: PoliteClient,
    ledger: SpellingLedger,
    cache: sqlite3.Connection | None,
    *,
    target_page: int,
    start_headword: str,
    quiet: bool = False,
    marker_prefix: str = "reseed",
) -> tuple[str, list[dict[str, Any]], int]:
    """Fetch a fresh seed and navigate to target_page, raising SessionInvalid on network/validation errors
    or ResumeMismatchError if register boundaries do not match."""
    seed_html, seed_req = client.exchange("GET", None)
    _keep_walk(ledger, cache, "", f"seed:{marker_prefix}:{target_page}", seed_html, seed_req)
    seed_tokens = _tokens(seed_html)
    if seed_tokens is None:
        raise SessionInvalid(f"{marker_prefix}_seed_missing_viewstate")

    p_rec = ledger.get_page(target_page)
    exp_start = str(p_rec["start_headword"]) if p_rec and p_rec["start_headword"] else None
    exp_end = str(p_rec["end_headword"]) if p_rec and p_rec["end_headword"] else None

    target_rows = ledger.page_rows(target_page)
    target_complete = bool(
        p_rec and p_rec["row_count"] and p_rec["end_headword"] and len(target_rows) == int(p_rec["row_count"])
    )
    # An incomplete target cannot rule out starts beyond its recorded prefix.
    # Search the last completed page's end instead and align against its full listing.
    anchor_page = target_page
    if target_page > 1 and not target_complete:
        previous = ledger.get_page(target_page - 1)
        if previous is not None and previous["state"] == "completed" and previous["end_headword"]:
            anchor_page = target_page - 1
    anchor_record = ledger.get_page(anchor_page)
    search_target = (
        str(anchor_record["end_headword"])
        if anchor_page != target_page and anchor_record is not None
        else exp_start or (start_headword if target_page == 1 else None)
    )
    landed: list[dict[str, Any]] = []
    search_html = ""
    if search_target is not None:
        search_fields = _form_fields(seed_tokens, spelling=search_target, extra=_image_click(SEARCH_BUTTON))
        search_html, search_req = client.exchange("POST", search_fields)
        _keep_walk(
            ledger,
            cache,
            "",
            f"tsearch:{marker_prefix}:{target_page}",
            search_html,
            search_req,
            current_page=target_page,
        )
        landed = parse_register_list(search_html)
        if not landed:
            raise SessionInvalid(f"{marker_prefix}_missing_register")

    if landed:
        anchor_offset = _resume_window_offset(
            ledger,
            landed,
            target_page=anchor_page,
            anchor_headword=search_target or "",
            anchor_page=anchor_page,
            anchor_index=0,
            nonterminal_page=anchor_page != target_page,
        )
        offset = (
            anchor_offset + REGISTER_PAGE_SIZE
            if anchor_offset is not None and anchor_page != target_page
            else anchor_offset
        )
        if anchor_page != target_page and offset is not None:
            first = str(landed[0]["stressed"])
            # A boundary homonym can make a target-page row look like the last
            # completed page's suffix. The continuity check rules out a repeated
            # distinct pair (or six identical rows), but shorter uniform runs
            # cannot distinguish the two pages without a known target start.
            suffix = [str(row["stressed_headword"]) for row in ledger.page_rows(anchor_page)[-offset:]]
            distinct_pair = len(suffix) >= 2 and normalize_ulif_spelling(suffix[0]) != normalize_ulif_spelling(
                suffix[1]
            )
            if (not exp_start or first == exp_start) and not (distinct_pair or len(suffix) >= 6):
                offset = None
        # An aligned window that ends before the target page does not locate it.
        if offset is not None and offset < len(landed):
            if not quiet:
                print(f"resuming: direct search page {target_page}, k={offset}", file=sys.stderr, flush=True)
            return search_html, landed, offset
    if target_page == 1 and not exp_start and not exp_end:
        return search_html, landed, 0

    if target_page > 1:
        if not quiet:
            print(
                f"resuming: direct searches could not locate page {target_page}; using fast-forward",
                file=sys.stderr,
                flush=True,
            )
        ff_html, ff_rows = _fast_forward_to_page(
            client,
            ledger,
            cache,
            seed_tokens,
            start_headword,
            target_page,
            quiet=quiet,
        )
        if exp_start and exp_end and (ff_rows[0]["stressed"] != exp_start or ff_rows[-1]["stressed"] != exp_end):
            raise ResumeMismatchError(
                f"expected {exp_start}..{exp_end}, landed {ff_rows[0]['stressed']}..{ff_rows[-1]['stressed']}"
            )
        _verify_known_window_rows(ledger, ff_rows, (target_page - 1) * REGISTER_PAGE_SIZE)
        return ff_html, ff_rows, 0

    if exp_start and exp_end:
        raise ResumeMismatchError(
            f"expected {exp_start}..{exp_end}, landed {landed[0]['stressed']}..{landed[-1]['stressed']}"
        )

    if target_page == 1 and exp_start:
        raise ResumeMismatchError("page 1 recorded start has no unique resume alignment")

    raise SessionInvalid(f"{marker_prefix}_unable_to_reach_page_{target_page}")


def _process_walk_rows(
    client: PoliteClient,
    ledger: SpellingLedger,
    cache: sqlite3.Connection,
    rows: list[dict[str, Any]],
    page_tokens: Mapping[str, str],
    positions: list[tuple[int, int] | None],
) -> None:
    """Fetch entries using server row controls and record canonical positions."""
    pages = {page for position in positions if position is not None for page in [position[0]]}
    existing_rows = {(page, int(row["row_index"])): row for page in pages for row in ledger.page_rows(page)}
    for i, r in enumerate(rows):
        position = positions[i]
        if position is None:
            continue
        row_page, r_idx = position
        r_norm = normalize_ulif_spelling(str(r["unstressed"]))
        ex = existing_rows.get((row_page, r_idx))
        if ex is not None and str(ex["state"]) == "completed":
            if i < len(rows) - 1 and normalize_ulif_spelling(str(rows[i + 1]["unstressed"])) != r_norm:
                _commit_spelling_group(ledger, cache, r_norm)
            continue

        entry_fields = _form_fields(
            page_tokens,
            spelling=str(r["unstressed"]),
            event_target=GRID_TARGET,
            event_argument=str(r["select"]),
        )
        entry_html, entry_req = client.exchange("POST", entry_fields)
        entry_sha = _sha256(entry_html.encode("utf-8"))
        _keep_walk(
            ledger,
            cache,
            r_norm,
            "entry",
            entry_html,
            entry_req,
            register_position=f"{row_page}:{r_idx}",
            current_page=row_page,
        )

        unknowns = find_unknown_controls(entry_html)
        unknown_str = ",".join(unknowns) if unknowns else ""

        paradigm = parse_ulif_paradigm(entry_html)
        if paradigm is not None:
            paradigm_source = "entry"
            ledger.record_response(
                spelling=r_norm,
                role="tab",
                response_sha256=entry_sha,
                request_sha256=_sha256(entry_req),
                tab_kind="paradigm",
                register_position=f"{row_page}:{r_idx}",
            )
        else:
            if _has_control(entry_html, "ctl00$ContentPlaceHolder1$par"):
                paradigm_source = "tab"
                par_tokens = _tokens(entry_html)
                if par_tokens is None:
                    raise SessionInvalid("entry_tokens_missing")
                tab_fields = _form_fields(
                    par_tokens,
                    spelling=str(r["unstressed"]),
                    extra=_image_click("ctl00$ContentPlaceHolder1$par"),
                )
                tab_html, tab_req = client.exchange("POST", tab_fields)
                _keep_walk(
                    ledger,
                    cache,
                    r_norm,
                    "tab",
                    tab_html,
                    tab_req,
                    tab_kind="paradigm",
                    register_position=f"{row_page}:{r_idx}",
                    current_page=row_page,
                )
            else:
                paradigm_source = ""

        entry_tokens = _tokens(entry_html)
        if entry_tokens is not None:
            for kind, control in (
                ("synonyms", "ctl00$ContentPlaceHolder1$syn"),
                ("phraseology", "ctl00$ContentPlaceHolder1$phras"),
                ("antonyms", "ctl00$ContentPlaceHolder1$ant"),
            ):
                if _has_control(entry_html, control):
                    tab_fields = _form_fields(
                        entry_tokens,
                        spelling=str(r["unstressed"]),
                        extra=_image_click(control),
                    )
                    tab_html, tab_req = client.exchange("POST", tab_fields)
                    _keep_walk(
                        ledger,
                        cache,
                        r_norm,
                        "tab",
                        tab_html,
                        tab_req,
                        tab_kind=kind,
                        register_position=f"{row_page}:{r_idx}",
                        current_page=row_page,
                    )

        ledger.mark_row(
            row_page,
            r_idx,
            "completed",
            entry_sha256=entry_sha,
            unknown_controls=unknown_str,
            paradigm_source=paradigm_source,
        )

        if i < len(rows) - 1 and normalize_ulif_spelling(str(rows[i + 1]["unstressed"])) != r_norm:
            _commit_spelling_group(ledger, cache, r_norm)


def _walk_shifted_windows(
    client: PoliteClient,
    ledger: SpellingLedger,
    cache: sqlite3.Connection,
    *,
    first_page: int,
    first_html: str,
    offset: int,
    start_headword: str,
    max_pages: int | None,
    quiet: bool,
    base_requests: int,
    started_at: float,
    clock: ClockFn,
) -> tuple[int, str, int]:
    """Walk canonical pages through search windows offset from the 25-row grid."""
    html = first_html
    start_global = (first_page - 1) * REGISTER_PAGE_SIZE - offset
    completed = 0
    target_page = first_page
    failures = 0
    page_started = clock()
    page_reqs = client.requests_made

    while True:
        if max_pages is not None and completed >= max_pages:
            return EXIT_OK, "max pages", completed
        try:
            rows = parse_register_list(html)
            tokens = _tokens(html)
            if not rows or tokens is None or _validation_failure(html):
                raise SessionInvalid(f"page_{target_page}_viewstate")
            _verify_known_window_rows(ledger, rows, start_global)
            _verify_first_unrecorded_page(ledger, rows, start_global)

            positions: list[tuple[int, int] | None] = []
            for i, row in enumerate(rows):
                page_zero, row_index = divmod(start_global + i, REGISTER_PAGE_SIZE)
                page_num = page_zero + 1
                if page_num < target_page or (max_pages is not None and page_num >= first_page + max_pages):
                    positions.append(None)
                    continue
                positions.append((page_num, row_index))
                ledger.ensure_page(
                    page_num,
                    start_headword=str(row["stressed"]) if row_index == 0 else "",
                    end_headword=str(row["stressed"]) if row_index == REGISTER_PAGE_SIZE - 1 else "",
                    row_count=REGISTER_PAGE_SIZE if row_index == REGISTER_PAGE_SIZE - 1 else 0,
                    register_size=_register_size(html),
                )
                ledger.ensure_row(
                    page_num,
                    row_index,
                    select_arg=str(row["select"]),
                    stressed_headword=str(row["stressed"]),
                    normalized_spelling=normalize_ulif_spelling(str(row["unstressed"])),
                )

            _process_walk_rows(client, ledger, cache, rows, tokens, positions)

            completed_here = sorted(
                {
                    page
                    for position in positions
                    if position is not None
                    for page, index in [position]
                    if index == REGISTER_PAGE_SIZE - 1
                }
            )
            has_next = _has_control(html, PAGE_BUTTONS["next"])
            if not has_next and not any(position is not None for position in positions):
                raise ResumeMismatchError(f"page {target_page} absent from terminal window")
            if not has_next and positions:
                final = next((position for position in reversed(positions) if position is not None), None)
                if final and final[0] not in completed_here:
                    last_row = rows[positions.index(final)]
                    recorded = ledger.get_page(final[0])
                    if recorded and recorded["row_count"] and final[1] + 1 < recorded["row_count"]:
                        raise ResumeMismatchError(
                            f"page {final[0]} ended at row {final[1]} before recorded row {recorded['row_count'] - 1}"
                        )
                    ledger.ensure_page(
                        final[0],
                        end_headword=str(last_row["stressed"]),
                        row_count=final[1] + 1,
                        register_size=_register_size(html),
                    )
                    completed_here.append(final[0])

            for page_num in completed_here:
                if page_num < target_page:
                    continue
                page_rows = ledger.page_rows(page_num)
                recorded = ledger.get_page(page_num)
                expected_count = (
                    int(recorded["row_count"]) if recorded and recorded["row_count"] else REGISTER_PAGE_SIZE
                )
                if len(page_rows) != expected_count or any(row["state"] != "completed" for row in page_rows):
                    raise SessionInvalid(f"page_{page_num}_incomplete_rows")
                ledger.mark_page(page_num, "completed")
                completed += 1
                target_page = page_num + 1
                failures = 0
                page_wall = clock() - page_started
                cumulative = float(ledger.meta("cumulative_page_wall_seconds", "0.0") or "0.0")
                timed = int(ledger.meta("cumulative_timed_pages", "0") or "0")
                ledger.set_meta("cumulative_page_wall_seconds", str(cumulative + page_wall))
                ledger.set_meta("cumulative_timed_pages", str(timed + 1))
                if not quiet:
                    counts = ledger.walk_counts()
                    print(
                        _format_walk_progress_line(
                            pages_done=counts["pages_done"],
                            pages_total=counts["pages_total"],
                            entries_stored=counts["entries_stored"],
                            page_req=client.requests_made - page_reqs,
                            total_req=base_requests + client.requests_made,
                            err_count=0,
                            retry_count=0,
                            elapsed_seconds=clock() - started_at,
                            eta_str="?",
                            page_num=page_num,
                        ),
                        file=sys.stderr,
                        flush=True,
                    )
                page_started = clock()
                page_reqs = client.requests_made

            if max_pages is not None and completed >= max_pages:
                return EXIT_OK, "max pages", completed
            if not has_next:
                if rows:
                    _commit_spelling_group(ledger, cache, normalize_ulif_spelling(str(rows[-1]["unstressed"])))
                return EXIT_OK, "finished", completed
            if len(rows) != REGISTER_PAGE_SIZE:
                raise SessionInvalid(f"page_{target_page}_short_nonterminal_window")

            next_fields = _form_fields(
                tokens,
                spelling=str(rows[-1]["unstressed"]),
                extra=_image_click(PAGE_BUTTONS["next"]),
            )
            next_html, request = client.exchange("POST", next_fields)
            _keep_walk(
                ledger,
                cache,
                "",
                f"page:next:{target_page}",
                next_html,
                request,
                current_page=target_page,
            )
            next_rows = parse_register_list(next_html)
            if not next_rows or _tokens(next_html) is None or _validation_failure(next_html):
                raise SessionInvalid(f"page_{target_page}_invalid_next_page")
            if next_html == html:
                raise SessionInvalid(f"page_{target_page}_repeated_window")
            _verify_register_continuity(rows, next_rows, target_page)
            if normalize_ulif_spelling(str(rows[-1]["unstressed"])) != normalize_ulif_spelling(
                str(next_rows[0]["unstressed"])
            ):
                _commit_spelling_group(ledger, cache, normalize_ulif_spelling(str(rows[-1]["unstressed"])))
            html = next_html
            start_global += len(rows)
        except ResumeMismatchError as exc:
            ledger.mark_page(target_page, "error", error="resume_mismatch")
            print(f"stopping: resume_mismatch on page {target_page} ({exc})", file=sys.stderr)
            return EXIT_USAGE, "resume_mismatch", completed
        except SessionInvalid as exc:
            failures += 1
            if failures >= MAX_UNIT_RESEEDS:
                ledger.mark_page(target_page, "retry_scheduled", error=str(exc))
                return EXIT_RETRY_STORM, f"page {target_page} exhausted retries", completed
            while failures < MAX_UNIT_RESEEDS:
                try:
                    html, _, offset = _reseed_to_page(
                        client,
                        ledger,
                        cache,
                        target_page=target_page,
                        start_headword=start_headword,
                        quiet=quiet,
                        marker_prefix="reseed",
                    )
                    start_global = (target_page - 1) * REGISTER_PAGE_SIZE - offset
                    break
                except ResumeMismatchError as mismatch:
                    ledger.mark_page(target_page, "error", error="resume_mismatch")
                    print(f"stopping: resume_mismatch on page {target_page} ({mismatch})", file=sys.stderr)
                    return EXIT_USAGE, "resume_mismatch", completed
                except SessionInvalid as reseed_error:
                    failures += 1
                    if failures >= MAX_UNIT_RESEEDS:
                        ledger.mark_page(target_page, "retry_scheduled", error=str(reseed_error))
                        return EXIT_RETRY_STORM, f"page {target_page} exhausted retries", completed


def run_walk(
    *,
    state_dir: Path,
    db_path: Path,
    delay_seconds: float = MIN_DELAY_SECONDS,
    max_pages: int | None = None,
    max_requests: int | None = None,
    break_stale_lock: bool = False,
    quiet: bool = False,
    start_headword: str = "а",
    resume_cmd: str | None = None,
    transport: Transport | None = None,
    sleep: SleepFn = _default_sleep,
    clock: ClockFn = time.monotonic,
    scanner: Scanner = scan_for_legacy_crawler,
    progress_interval: float | None = None,
) -> int:
    if resume_cmd:
        resolved_resume_cmd = resume_cmd
    else:
        cmd_parts = [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.fetch_ulif_homonyms",
            "walk",
            "--state-dir",
            str(state_dir),
            "--db",
            str(db_path),
            "--delay",
            f"{delay_seconds:g}",
        ]
        if max_pages is not None:
            cmd_parts.extend(["--max-pages", str(max_pages)])
        if max_requests is not None:
            cmd_parts.extend(["--max-requests", str(max_requests)])
        if break_stale_lock:
            cmd_parts.append("--break-stale-lock")
        if quiet:
            cmd_parts.append("--quiet")
        if progress_interval is not None:
            cmd_parts.extend(["--progress-interval", f"{progress_interval:g}"])
        resolved_resume_cmd = shlex.join(cmd_parts)

    try:
        progress_every = resolve_progress_interval(progress_interval)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    if delay_seconds < MIN_DELAY_SECONDS:
        print(f"delay must be >= {MIN_DELAY_SECONDS}", file=sys.stderr)
        _print_walk_stop_summary(
            reason=f"delay must be >= {MIN_DELAY_SECONDS}",
            ledger=None,
            requests_in_process=0,
            elapsed_seconds=0.0,
            resume_cmd=resolved_resume_cmd,
        )
        return EXIT_USAGE

    stop_reason = "finished"
    return_code = EXIT_OK
    start_time = clock()
    base_requests = 0
    process_pages_finished = 0
    process_wall_time = 0.0

    lock: RunnerLock | None = None
    ledger: SpellingLedger | None = None
    cache: sqlite3.Connection | None = None
    client: PoliteClient | None = None

    old_sigterm = None
    if threading.current_thread() is threading.main_thread():

        def _on_sigterm(signum: int, frame: Any) -> None:
            raise InterruptedByOperator("SIGTERM")

        with contextlib.suppress(ValueError, OSError):
            old_sigterm = signal.signal(signal.SIGTERM, _on_sigterm)

    def _emit_walk_progress() -> None:
        if ledger is None:
            return
        counts = ledger.walk_counts()
        process_requests = client.requests_made if client is not None else 0
        requests_made = base_requests + process_requests
        timed = int(ledger.meta("cumulative_timed_pages", "0") or "0")
        wall = float(ledger.meta("cumulative_page_wall_seconds", "0.0") or "0.0")
        remaining = max(0, counts["pages_total"] - counts["pages_done"])
        line = format_periodic_progress(
            kind="pages",
            done=counts["pages_done"],
            total=counts["pages_total"],
            requests_made=requests_made,
            process_requests=process_requests,
            elapsed_seconds=clock() - start_time,
            eta_seconds=_eta_seconds(remaining, timed, wall),
        )
        print(line, file=sys.stderr, flush=True)

    on_heartbeat = OperatorProgress(
        interval=progress_every,
        clock=clock,
        emit=_emit_walk_progress,
    )

    try:
        try:
            _ensure_private_dir(state_dir)
            lock = RunnerLock(state_dir, break_stale=break_stale_lock, scanner=scanner)
            lock.acquire()

            ledger_path = state_dir / "ledger.sqlite"
            if ledger_path.exists():
                probe = SpellingLedger(ledger_path)
                try:
                    existing_mode = _ledger_data_mode(probe)
                    if existing_mode == "run":
                        raise ValueError("targeted run data in --state-dir; walk requires a separate state directory")
                except ValueError as exc:
                    print(f"refusing to start: {exc}", file=sys.stderr)
                    return EXIT_USAGE
                finally:
                    probe.close()
                try:
                    verify_ledger_continuity(ledger_path, warn_on_overlap=True)
                except (ResumeMismatchError, sqlite3.Error) as exc:
                    print(f"stopping: ledger continuity error ({exc})", file=sys.stderr)
                    stop_reason = "ledger continuity error"
                    return EXIT_USAGE

            try:
                cache = prepare_database(db_path)
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                return_code = EXIT_USAGE
                stop_reason = f"database error: {exc}"
            else:
                ledger = SpellingLedger(state_dir / "ledger.sqlite")
                try:
                    existing_mode = _ledger_data_mode(ledger)
                    if existing_mode == "run":
                        raise ValueError("targeted run data in --state-dir; walk requires a separate state directory")
                except ValueError as exc:
                    print(f"refusing to start: {exc}", file=sys.stderr)
                    return EXIT_USAGE
                ledger.set_meta("mode", "walk")
                ledger.set_meta("delay_seconds", str(delay_seconds))
                base_requests = int(ledger.meta("requests_made", "0") or "0")

                def _on_request(req_in_proc: int) -> None:
                    if ledger is not None:
                        with contextlib.suppress(Exception):
                            ledger.set_requests_made(base_requests + req_in_proc)

                client = PoliteClient(
                    transport or _requests_transport(declared_user_agent()),
                    delay_seconds=delay_seconds,
                    sleep=sleep,
                    clock=clock,
                    max_requests=max_requests,
                    heartbeat=on_heartbeat,
                    on_request=_on_request,
                )

                first_unfinished = ledger.first_unfinished_page()
                is_resume = False
                if first_unfinished is not None:
                    p_rec = ledger.get_page(first_unfinished)
                    has_boundaries = bool(
                        p_rec and p_rec["start_headword"] and p_rec["end_headword"] and (p_rec["row_count"] or 0) > 0
                    )
                    if first_unfinished == 1 and not has_boundaries:
                        is_resume = False
                        start_page = 1
                    else:
                        is_resume = True
                        start_page = first_unfinished
                else:
                    completed_count = ledger.conn.execute(
                        "SELECT COUNT(*) FROM register_pages WHERE state = 'completed'"
                    ).fetchone()[0]
                    if completed_count > 0:
                        _print_walk_start_banner(
                            start_page=completed_count,
                            pages_done=completed_count,
                            pages_total=completed_count,
                            to_do_pages=0,
                            delay_seconds=delay_seconds,
                            state_dir=state_dir,
                            db_path=db_path,
                            register_size=ledger.meta("register_size", "") or "unknown",
                        )
                        _print_walk_stop_summary(
                            reason="all pages already completed",
                            ledger=ledger,
                            requests_in_process=0,
                            elapsed_seconds=0.0,
                            resume_cmd=resolved_resume_cmd,
                        )
                        return EXIT_OK
                    start_page = 1

                current_page_html = ""
                resume_offset = 0
                if is_resume:
                    for resume_attempt in range(MAX_UNIT_RESEEDS):
                        try:
                            current_page_html, landed_rows, resume_offset = _reseed_to_page(
                                client,
                                ledger,
                                cache,
                                target_page=start_page,
                                start_headword=start_headword,
                                quiet=quiet,
                                marker_prefix="resume",
                            )
                            break
                        except ResumeMismatchError as exc:
                            ledger.mark_page(start_page, "error", error="resume_mismatch")
                            print(
                                f"stopping: resume_mismatch on page {start_page} ({exc})",
                                file=sys.stderr,
                            )
                            stop_reason = "resume_mismatch"
                            return_code = EXIT_USAGE
                            break
                        except SessionInvalid as exc:
                            if resume_attempt == MAX_UNIT_RESEEDS - 1:
                                ledger.mark_page(start_page, "retry_scheduled", error=str(exc))
                                print(
                                    f"stopping: startup resume for page {start_page} ended retry_scheduled after {MAX_UNIT_RESEEDS} attempts ({exc})",
                                    file=sys.stderr,
                                )
                                stop_reason = f"page {start_page} exhausted retries"
                                return_code = EXIT_RETRY_STORM
                                break
                            continue
                else:
                    for start_attempt in range(MAX_UNIT_RESEEDS):
                        try:
                            seed_html, seed_req = client.exchange("GET", None)
                            _keep_walk(ledger, cache, "", f"seed:start:{start_attempt}", seed_html, seed_req)
                            seed_tokens = _tokens(seed_html)
                            if seed_tokens is None:
                                raise SessionInvalid("seed_missing_viewstate")
                            search_fields = _form_fields(
                                seed_tokens,
                                spelling=start_headword,
                                extra=_image_click(SEARCH_BUTTON),
                            )
                            page_html, page_req = client.exchange("POST", search_fields)
                            _keep_walk(ledger, cache, "", "tsearch:start", page_html, page_req, current_page=1)
                            landed_rows = parse_register_list(page_html)
                            if not landed_rows:
                                raise SessionInvalid("start_missing_register")
                            start_page = 1
                            current_page_html = page_html
                            reg_sz = _register_size(page_html)
                            ledger.ensure_page(
                                1,
                                start_headword=landed_rows[0]["stressed"],
                                end_headword=landed_rows[-1]["stressed"],
                                row_count=len(landed_rows),
                                register_size=reg_sz,
                            )
                            for r in landed_rows:
                                ledger.ensure_row(
                                    1,
                                    int(r["row_index"]),
                                    select_arg=str(r["select"]),
                                    stressed_headword=str(r["stressed"]),
                                    normalized_spelling=normalize_ulif_spelling(str(r["unstressed"])),
                                )
                            break
                        except SessionInvalid as exc:
                            if start_attempt == MAX_UNIT_RESEEDS - 1:
                                ledger.ensure_page(1, start_headword="", end_headword="", row_count=0)
                                ledger.mark_page(1, "retry_scheduled", error=str(exc))
                                print(
                                    f"stopping: startup on page 1 ended retry_scheduled after {MAX_UNIT_RESEEDS} attempts ({exc})",
                                    file=sys.stderr,
                                )
                                stop_reason = "page 1 exhausted retries"
                                return_code = EXIT_RETRY_STORM
                                break
                            continue

                w_counts = ledger.walk_counts()
                pages_done = w_counts["pages_done"]
                pages_total = w_counts["pages_total"]
                to_do_pages = max(0, pages_total - pages_done) if pages_total else 0
                if max_pages is not None:
                    to_do_pages = min(to_do_pages, max_pages)

                _print_walk_start_banner(
                    start_page=start_page,
                    pages_done=pages_done,
                    pages_total=pages_total,
                    to_do_pages=to_do_pages,
                    delay_seconds=delay_seconds,
                    state_dir=state_dir,
                    db_path=db_path,
                    register_size=ledger.meta("register_size", "") or "unknown",
                )

                if return_code == EXIT_OK:
                    current_page = start_page
                    consecutive_retries = 0

                    if resume_offset:
                        return_code, stop_reason, process_pages_finished = _walk_shifted_windows(
                            client,
                            ledger,
                            cache,
                            first_page=start_page,
                            first_html=current_page_html,
                            offset=resume_offset,
                            start_headword=start_headword,
                            max_pages=max_pages,
                            quiet=quiet,
                            base_requests=base_requests,
                            started_at=start_time,
                            clock=clock,
                        )

                    while not resume_offset:
                        if max_pages is not None and process_pages_finished >= max_pages:
                            stop_reason = "max pages"
                            break

                        page_start_clock = clock()
                        page_start_reqs = client.requests_made
                        page_success = False

                        for page_attempt in range(MAX_UNIT_RESEEDS):
                            try:
                                if page_attempt > 0:
                                    current_page_html, rows, reseed_offset = _reseed_to_page(
                                        client,
                                        ledger,
                                        cache,
                                        target_page=current_page,
                                        start_headword=start_headword,
                                        quiet=quiet,
                                        marker_prefix="reseed",
                                    )
                                    if reseed_offset:
                                        return_code, stop_reason, shifted_pages = _walk_shifted_windows(
                                            client,
                                            ledger,
                                            cache,
                                            first_page=current_page,
                                            first_html=current_page_html,
                                            offset=reseed_offset,
                                            start_headword=start_headword,
                                            max_pages=None if max_pages is None else max_pages - process_pages_finished,
                                            quiet=quiet,
                                            base_requests=base_requests,
                                            started_at=start_time,
                                            clock=clock,
                                        )
                                        process_pages_finished += shifted_pages
                                        resume_offset = reseed_offset
                                        break
                                else:
                                    rows = parse_register_list(current_page_html)
                                    if not rows:
                                        raise SessionInvalid(f"page_{current_page}_empty")

                                page_tokens = _tokens(current_page_html)
                                if page_tokens is None or _validation_failure(current_page_html):
                                    raise SessionInvalid(f"page_{current_page}_viewstate")

                                ledger.ensure_page(
                                    current_page,
                                    start_headword=rows[0]["stressed"],
                                    end_headword=rows[-1]["stressed"],
                                    row_count=len(rows),
                                    register_size=_register_size(current_page_html),
                                )
                                for r in rows:
                                    ledger.ensure_row(
                                        current_page,
                                        int(r["row_index"]),
                                        select_arg=str(r["select"]),
                                        stressed_headword=str(r["stressed"]),
                                        normalized_spelling=normalize_ulif_spelling(str(r["unstressed"])),
                                    )

                                _process_walk_rows(
                                    client,
                                    ledger,
                                    cache,
                                    rows,
                                    page_tokens,
                                    [(current_page, int(r["row_index"])) for r in rows],
                                )

                                page_success = True
                                break
                            except ResumeMismatchError as exc:
                                ledger.mark_page(current_page, "error", error="resume_mismatch")
                                stop_reason = "resume_mismatch"
                                return_code = EXIT_USAGE
                                print(
                                    f"stopping: resume_mismatch on page {current_page} ({exc})",
                                    file=sys.stderr,
                                )
                                break
                            except SessionInvalid as exc:
                                consecutive_retries += 1
                                if page_attempt == MAX_UNIT_RESEEDS - 1:
                                    ledger.mark_page(current_page, "retry_scheduled", error=str(exc))
                                    break
                                continue

                        if resume_offset or return_code != EXIT_OK or stop_reason == "resume_mismatch":
                            break

                        if not page_success:
                            stop_reason = f"page {current_page} exhausted retries"
                            return_code = EXIT_RETRY_STORM
                            print(
                                f"stopping: page {current_page} ended retry_scheduled after {MAX_UNIT_RESEEDS} attempts",
                                file=sys.stderr,
                            )
                            break

                        consecutive_retries = 0

                        if not _has_control(current_page_html, PAGE_BUTTONS["next"]):
                            _commit_spelling_group(ledger, cache, normalize_ulif_spelling(str(rows[-1]["unstressed"])))
                            ledger.mark_page(current_page, "completed")
                            process_pages_finished += 1
                            page_wall = clock() - page_start_clock
                            process_wall_time += page_wall

                            cum_wall = float(ledger.meta("cumulative_page_wall_seconds", "0.0") or "0.0") + page_wall
                            cum_pages = int(ledger.meta("cumulative_timed_pages", "0") or "0") + 1
                            ledger.set_meta("cumulative_page_wall_seconds", str(cum_wall))
                            ledger.set_meta("cumulative_timed_pages", str(cum_pages))

                            if not quiet:
                                w_cnt = ledger.walk_counts()
                                p_done = w_cnt["pages_done"]
                                p_total = w_cnt["pages_total"]
                                pg_req = client.requests_made - page_start_reqs
                                tot_req = base_requests + client.requests_made
                                line = _format_walk_progress_line(
                                    pages_done=p_done,
                                    pages_total=p_total,
                                    entries_stored=w_cnt["entries_stored"],
                                    page_req=pg_req,
                                    total_req=tot_req,
                                    err_count=consecutive_retries,
                                    retry_count=0,
                                    elapsed_seconds=clock() - start_time,
                                    eta_str="0:00:00",
                                    page_num=current_page,
                                )
                                print(line, file=sys.stderr, flush=True)
                                on_heartbeat.note_progress()

                            stop_reason = "finished"
                            break

                        next_fields = _form_fields(
                            page_tokens,
                            spelling=str(rows[-1]["unstressed"]),
                            extra=_image_click(PAGE_BUTTONS["next"]),
                        )
                        next_html, next_req = client.exchange("POST", next_fields)
                        _keep_walk(
                            ledger,
                            cache,
                            "",
                            f"page:next:{current_page + 1}",
                            next_html,
                            next_req,
                            current_page=current_page + 1,
                        )
                        next_rows = parse_register_list(next_html)
                        if not next_rows or _tokens(next_html) is None or _validation_failure(next_html):
                            ledger.mark_page(current_page, "retry_scheduled", error="invalid_next_page")
                            print(
                                f"stopping: page transition from page {current_page} returned invalid next page register",
                                file=sys.stderr,
                            )
                            stop_reason = "invalid_next_page"
                            return_code = EXIT_USAGE
                            break

                        ledger.ensure_page(
                            current_page + 1,
                            start_headword=next_rows[0]["stressed"],
                            end_headword=next_rows[-1]["stressed"],
                            row_count=len(next_rows),
                            register_size=_register_size(next_html),
                        )
                        for nr in next_rows:
                            ledger.ensure_row(
                                current_page + 1,
                                int(nr["row_index"]),
                                select_arg=str(nr["select"]),
                                stressed_headword=str(nr["stressed"]),
                                normalized_spelling=normalize_ulif_spelling(str(nr["unstressed"])),
                            )

                        last_norm = normalize_ulif_spelling(str(rows[-1]["unstressed"]))
                        next_norm = normalize_ulif_spelling(str(next_rows[0]["unstressed"]))
                        if last_norm != next_norm:
                            _commit_spelling_group(ledger, cache, last_norm)

                        ledger.mark_page(current_page, "completed")
                        process_pages_finished += 1
                        page_wall = clock() - page_start_clock
                        process_wall_time += page_wall

                        cum_wall = float(ledger.meta("cumulative_page_wall_seconds", "0.0") or "0.0") + page_wall
                        cum_pages = int(ledger.meta("cumulative_timed_pages", "0") or "0") + 1
                        ledger.set_meta("cumulative_page_wall_seconds", str(cum_wall))
                        ledger.set_meta("cumulative_timed_pages", str(cum_pages))

                        if not quiet:
                            w_cnt = ledger.walk_counts()
                            p_done = w_cnt["pages_done"]
                            p_total = w_cnt["pages_total"]
                            pg_req = client.requests_made - page_start_reqs
                            tot_req = base_requests + client.requests_made
                            if process_pages_finished < 5:
                                eta_s = "?"
                            else:
                                rem_p = max(0, p_total - p_done)
                                if rem_p == 0:
                                    eta_s = "0:00:00"
                                else:
                                    mean_w = process_wall_time / process_pages_finished
                                    eta_sec = rem_p * mean_w
                                    eh = int(eta_sec // 3600)
                                    em = int((eta_sec % 3600) // 60)
                                    es = int(eta_sec % 60)
                                    eta_s = f"{eh}:{em:02d}:{es:02d}"

                            line = _format_walk_progress_line(
                                pages_done=p_done,
                                pages_total=p_total,
                                entries_stored=w_cnt["entries_stored"],
                                page_req=pg_req,
                                total_req=tot_req,
                                err_count=consecutive_retries,
                                retry_count=0,
                                elapsed_seconds=clock() - start_time,
                                eta_str=eta_s,
                                page_num=current_page,
                            )
                            print(line, file=sys.stderr, flush=True)
                            on_heartbeat.note_progress()

                        current_page += 1
                        current_page_html = next_html

        except RequestCap:
            stop_reason = "request cap"
        except Forbidden:
            stop_reason = "HTTP 403"
            return_code = EXIT_FORBIDDEN
            print("stopping: HTTP 403 from ULIF", file=sys.stderr)
        except SystemExit as exc:
            stop_reason = str(exc)
            summary_printed = False
            for _ in range(3):
                try:
                    _print_walk_stop_summary(
                        reason=stop_reason,
                        ledger=ledger,
                        requests_in_process=client.requests_made if client else 0,
                        elapsed_seconds=clock() - start_time,
                        resume_cmd=resolved_resume_cmd,
                    )
                    summary_printed = True
                    break
                except (KeyboardInterrupt, InterruptedByOperator):
                    pass
            if not summary_printed:
                with contextlib.suppress(Exception):
                    sys.stderr.write(
                        f"=== ULIF Walk Stop Summary ===\nReason:                 {stop_reason}\nResume command:         {resolved_resume_cmd}\n==============================\n"
                    )
                    sys.stderr.flush()
            raise
        except (KeyboardInterrupt, InterruptedByOperator):
            stop_reason = "interrupted by operator"
            return_code = EXIT_INTERRUPTED
        except Exception as exc:
            stop_reason = str(exc)
            return_code = EXIT_INTERRUPTED
            print(f"interrupted: {exc}", file=sys.stderr)

        if client is not None and ledger is not None:
            written = False
            for _ in range(5):
                try:
                    ledger.set_requests_made(base_requests + client.requests_made)
                    written = True
                    break
                except (KeyboardInterrupt, InterruptedByOperator):
                    stop_reason = "interrupted by operator"
                    return_code = EXIT_INTERRUPTED
                except Exception as exc:
                    print(
                        f"warning: failed to persist final requests_made ({base_requests + client.requests_made}): {exc}",
                        file=sys.stderr,
                    )
                    break
            if not written:
                try:
                    ledger.conn.execute(
                        "INSERT INTO meta (key, value) VALUES ('requests_made', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (str(base_requests + client.requests_made),),
                    )
                    ledger.conn.commit()
                except (KeyboardInterrupt, InterruptedByOperator):
                    stop_reason = "interrupted by operator"
                    return_code = EXIT_INTERRUPTED
                except Exception as exc:
                    if stop_reason == "finished":
                        stop_reason = f"persistence error: {exc}"
                    if return_code == EXIT_OK:
                        return_code = EXIT_INTERRUPTED

        summary_printed = False
        for _ in range(3):
            try:
                _print_walk_stop_summary(
                    reason=stop_reason,
                    ledger=ledger,
                    requests_in_process=client.requests_made if client else 0,
                    elapsed_seconds=clock() - start_time,
                    resume_cmd=resolved_resume_cmd,
                )
                summary_printed = True
                break
            except (KeyboardInterrupt, InterruptedByOperator):
                stop_reason = "interrupted by operator"
                return_code = EXIT_INTERRUPTED

        if not summary_printed:
            with contextlib.suppress(BaseException):
                lines = [
                    "=== ULIF Walk Stop Summary ===",
                    f"Reason:                 {stop_reason}",
                    f"Resume command:         {resolved_resume_cmd}",
                    "==============================",
                ]
                print("\n".join(lines), file=sys.stderr, flush=True)

    finally:
        try:
            if cache is not None:
                with contextlib.suppress(Exception):
                    cache.close()
        except (KeyboardInterrupt, InterruptedByOperator):
            return_code = EXIT_INTERRUPTED
            with contextlib.suppress(Exception):
                if cache is not None:
                    cache.close()

        try:
            if ledger is not None:
                with contextlib.suppress(Exception):
                    ledger.close()
        except (KeyboardInterrupt, InterruptedByOperator):
            return_code = EXIT_INTERRUPTED
            with contextlib.suppress(Exception):
                if ledger is not None:
                    ledger.close()

        if lock is not None:
            for _ in range(5):
                try:
                    lock.release()
                    break
                except (KeyboardInterrupt, InterruptedByOperator):
                    return_code = EXIT_INTERRUPTED
                    if lock.path.exists() and lock._held:
                        with contextlib.suppress(OSError):
                            lock.path.unlink()
                        lock._held = False
                    break

        if old_sigterm is not None:
            with contextlib.suppress(ValueError, OSError):
                signal.signal(signal.SIGTERM, old_sigterm)

    return return_code


def verify_complete(
    *,
    state_dir: Path,
    db_path: Path,
    expected_size: int | None = None,
) -> int:
    """Compare stored entries against printed ULIF register size and itemise differences."""
    ledger_path = state_dir / "ledger.sqlite"
    if not ledger_path.exists():
        print(f"error: ledger not found at {ledger_path}", file=sys.stderr)
        return EXIT_USAGE
    if not db_path.exists():
        print(f"error: database not found at {db_path}", file=sys.stderr)
        return EXIT_USAGE

    ledger = SpellingLedger(ledger_path)
    try:
        cache = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
        try:
            reg_size_str = ledger.meta("register_size")
            if expected_size is not None:
                target_size = expected_size
            elif reg_size_str and reg_size_str.isdigit():
                target_size = int(reg_size_str)
            else:
                print("error: unknown register size in ledger meta; pass --register-size", file=sys.stderr)
                return EXIT_USAGE

            stored_rows_count = ledger.conn.execute(
                "SELECT COUNT(*) FROM register_rows WHERE state = 'completed'"
            ).fetchone()[0]

            diff = target_size - stored_rows_count

            incomplete_pages = list(
                ledger.conn.execute(
                    "SELECT page_num, state, error FROM register_pages WHERE state != 'completed' ORDER BY page_num"
                )
            )
            incomplete_rows = list(
                ledger.conn.execute(
                    """
                    SELECT page_num, row_index, select_arg, stressed_headword, state, error
                    FROM register_rows
                    WHERE state != 'completed'
                    ORDER BY page_num, row_index
                    """
                )
            )

            # Check page continuity and reconcile row page references against page records
            page_records = list(
                ledger.conn.execute("SELECT page_num, state, error FROM register_pages ORDER BY page_num")
            )
            page_continuity_errors: list[str] = []
            if not page_records:
                page_continuity_errors.append("no pages recorded in ledger")
            else:
                if page_records[0]["page_num"] != 1:
                    page_continuity_errors.append(f"pages start at {page_records[0]['page_num']} instead of 1")
                for curr_p, next_p in itertools.pairwise(page_records):
                    if next_p["page_num"] != curr_p["page_num"] + 1:
                        page_continuity_errors.append(
                            f"gap in page sequence between page {curr_p['page_num']} and {next_p['page_num']}"
                        )

            completed_page_set = {int(p["page_num"]) for p in page_records if str(p["state"]) == "completed"}
            row_page_set = {
                int(row[0])
                for row in ledger.conn.execute("SELECT DISTINCT page_num FROM register_rows WHERE state = 'completed'")
            }
            missing_page_records = sorted(row_page_set - completed_page_set)
            if missing_page_records:
                page_continuity_errors.append(
                    f"completed rows reference missing or uncompleted pages: {missing_page_records}"
                )
            pages_without_rows = sorted(completed_page_set - row_page_set)
            if pages_without_rows:
                page_continuity_errors.append(f"completed pages have no completed rows recorded: {pages_without_rows}")

            # Reconcile completed rows with persisted database entries
            table_exists = (
                cache.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ulif_dictua_entries'"
                ).fetchone()
                is not None
            )
            if table_exists:
                entries_count = cache.execute(
                    "SELECT COUNT(*) FROM ulif_dictua_entries WHERE status = 'ok'"
                ).fetchone()[0]
                db_entries = {
                    (str(row[0]), int(row[1]))
                    for row in cache.execute(
                        "SELECT normalized_query, homonym_index FROM ulif_dictua_entries WHERE status = 'ok'"
                    )
                }
            else:
                entries_count = 0
                db_entries = set()

            completed_rows = ledger.conn.execute(
                """
                SELECT page_num, row_index, select_arg, stressed_headword, normalized_spelling, homonym_index
                FROM register_rows
                WHERE state = 'completed'
                ORDER BY page_num, row_index
                """
            ).fetchall()

            missing_db_entries = []
            for r in completed_rows:
                h_idx = r["homonym_index"]
                if h_idx is None or (str(r["normalized_spelling"]), int(h_idx)) not in db_entries:
                    missing_db_entries.append(r)

            print("=== ULIF Verification Report ===", file=sys.stderr)
            print(f"Printed register size: {target_size}", file=sys.stderr)
            print(f"Completed rows:        {stored_rows_count}", file=sys.stderr)
            print(f"Stored entries in DB:  {entries_count}", file=sys.stderr)
            print(f"Difference:            {diff}", file=sys.stderr)

            if page_continuity_errors:
                print(f"Page continuity errors ({len(page_continuity_errors)}):", file=sys.stderr)
                for err in page_continuity_errors:
                    print(f"  {err}", file=sys.stderr)

            if incomplete_pages:
                print(f"Incomplete pages ({len(incomplete_pages)}):", file=sys.stderr)
                for p in incomplete_pages:
                    print(f"  page {p['page_num']}: state={p['state']} error={p['error']}", file=sys.stderr)

            if incomplete_rows:
                print(f"Incomplete rows ({len(incomplete_rows)}):", file=sys.stderr)
                for r in incomplete_rows:
                    print(
                        f"  page {r['page_num']} row {r['row_index']} ({r['select_arg']}): "
                        f"headword={r['stressed_headword']} state={r['state']} error={r['error']}",
                        file=sys.stderr,
                    )

            if missing_db_entries:
                print(f"Missing entries in database ({len(missing_db_entries)}):", file=sys.stderr)
                for m in missing_db_entries[:20]:
                    print(
                        f"  page {m['page_num']} row {m['row_index']} ({m['select_arg']}): "
                        f"headword={m['stressed_headword']} spelling={m['normalized_spelling']} "
                        f"homonym_index={m['homonym_index']}",
                        file=sys.stderr,
                    )
                if len(missing_db_entries) > 20:
                    print(f"  ... and {len(missing_db_entries) - 20} more", file=sys.stderr)

            if (
                diff == 0
                and not incomplete_pages
                and not incomplete_rows
                and not page_continuity_errors
                and not missing_db_entries
                and entries_count >= target_size
            ):
                print("Status: VERIFIED_COMPLETE (stored entries match printed register size)", file=sys.stderr)
                return EXIT_OK
            else:
                print("Status: INCOMPLETE", file=sys.stderr)
                return EXIT_USAGE
        finally:
            cache.close()
    finally:
        ledger.close()


def build_a1_a2_spellings(
    *,
    sources_db: Path,
    vesum_db: Path,
    stored: set[str],
) -> list[str]:
    """PULS A1/A2 lemmas, lemmatised through VESUM, minus spellings already stored."""
    sources = sqlite3.connect(f"file:{sources_db.resolve()}?mode=ro", uri=True)
    vesum = sqlite3.connect(f"file:{vesum_db.resolve()}?mode=ro", uri=True)
    try:
        words = [
            str(row[0])
            for row in sources.execute(
                """
                SELECT DISTINCT word FROM puls_cefr
                WHERE level IN ('A1', 'A2') AND TRIM(word) != ''
                """
            )
        ]
        found: set[str] = set()
        for word in words:
            lemmas = _vesum_lemmas(vesum, word)
            for lemma in lemmas:
                key = normalize_ulif_spelling(lemma)
                if key and key not in stored:
                    found.add(key)
        return sorted(found)
    finally:
        sources.close()
        vesum.close()


def _vesum_lemmas(conn: sqlite3.Connection, word: str) -> list[str]:
    """Lemmas for one PULS item. Multi-word items are kept only when VESUM has the whole string."""
    token = " ".join(word.split())
    if not token:
        return []
    keys = list(dict.fromkeys((token, token.casefold())))
    marks = ",".join("?" for _ in keys)
    rows = conn.execute(
        f"SELECT DISTINCT lemma FROM forms_all WHERE word_form IN ({marks})",
        keys,
    ).fetchall()
    return [str(row[0]) for row in rows if str(row[0]).strip()]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resumable targeted ULIF homonym fetch and offline parser.\nUse to fetch homonym-safe entries and relation tabs from DictUA into SQLite cache.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms run \\
      --spellings-file batch_state/ulif-homonyms/suspects.txt \\
      --state-dir batch_state/ulif-homonyms/state \\
      --db data/sources.db --delay 1.0

  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms status \\
      --state-dir batch_state/ulif-homonyms/state

Outputs:
  Raw response blobs in ulif_dictua_raw_responses (sources.db)
  Parsed homonym entries in ulif_dictua_entries and ulif_dictua_sections
  Progress ledger in <state-dir>/ledger.sqlite

Exit codes:
  0: Success / completed
  1: Usage error or unmigrated database
  2: Retry storm (3 consecutive spellings failed)
  3: HTTP 403 Forbidden
  4: Interrupted by operator (SIGINT / SIGTERM)

Related:
  Runbook: issue #8423
  Master plan: issue #8400
  Spec: issue #8429
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser(
        "run",
        help="Fetch spellings into the raw cache",
        description="Fetch homonym-safe entries from ULIF DictUA into SQLite raw cache.\nUse during targeted runs or whole-index crawls; do not use while another runner holds the lock.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms run \\
      --spellings-file batch_state/ulif-homonyms/suspects.txt \\
      --state-dir batch_state/ulif-homonyms/state \\
      --db data/sources.db --delay 1.0

Outputs:
  Raw HTML responses in ulif_dictua_raw_responses (sources.db)
  Progress and attempt state in <state-dir>/ledger.sqlite

Exit codes:
  0: All spellings finished successfully
  1: Usage error, invalid arguments, or unmigrated database
  2: Retry storm (3 consecutive spellings failed)
  3: HTTP 403 Forbidden from server
  4: Interrupted by operator (SIGINT / SIGTERM)

Related:
  Runbook: issue #8423 (Step 3)
  Master plan: issue #8400 (Step c)
  Spec: issue #8429
""",
    )
    run.add_argument(
        "--spellings-file",
        type=Path,
        required=True,
        help="Path to text file containing spellings, one per line (format: 'слово\\tinfo' or 'слово')",
    )
    run.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="Directory storing runner.lock and ledger.sqlite; use a separate directory from walk",
    )
    run.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Target SQLite database holding ulif_dictua_* tables (e.g. data/sources.db)",
    )
    run.add_argument(
        "--delay",
        type=float,
        default=MIN_DELAY_SECONDS,
        help="Seconds to wait between requests (must be >= 1.0; default: 1.0)",
    )
    run.add_argument(
        "--max-spellings",
        type=int,
        default=None,
        help="Stop after processing this many spellings in this process invocation (default: None, process all)",
    )
    run.add_argument(
        "--max-requests",
        type=int,
        default=None,
        help="Stop after making this many HTTP requests in this process invocation (default: None, unlimited)",
    )
    run.add_argument(
        "--refetch",
        action="store_true",
        help="Refetch spellings even if already marked 'stored' or 'absent_from_ulif' in ledger (default: False)",
    )
    run.add_argument(
        "--break-stale-lock",
        action="store_true",
        help="Break existing runner lock if holding PID is dead (default: False)",
    )
    run.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress per-spelling progress lines (start banner, periodic progress, stop summary always print; default: False)",
    )
    run.add_argument(
        "--progress-interval",
        type=float,
        default=None,
        help=(
            "Seconds between operator progress lines "
            f"(default: {DEFAULT_PROGRESS_INTERVAL_SECONDS:g}, or {PROGRESS_INTERVAL_ENV})"
        ),
    )

    walk = sub.add_parser(
        "walk",
        help="Full register walk across all ULIF entries",
        description="Sequential register walk across all ULIF entries into SQLite cache.\nUse to crawl the entire ULIF index via nextpage; do not use concurrently with another runner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms walk \\
      --state-dir batch_state/ulif-homonyms/state \\
      --db data/sources.db --delay 1.0

  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms walk \\
      --state-dir batch_state/ulif-homonyms/state \\
      --db data/sources.db --max-pages 5 --quiet

  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms walk \\
      --state-dir batch_state/ulif-homonyms/state --verify-ledger

Outputs:
  Raw HTML responses in ulif_dictua_raw_responses (sources.db)
  Parsed homonym entries in ulif_dictua_entries and ulif_dictua_sections (sources.db)
  Walk progress and register pages/rows in <state-dir>/ledger.sqlite

Exit codes:
  0: All pages finished successfully or walk completed
  1: Usage error, invalid arguments, or resume mismatch
  2: Retry storm (3 consecutive pages failed)
  3: HTTP 403 Forbidden from server
  4: Interrupted by operator (SIGINT / SIGTERM)

Related:
  Runbook: issue #8423
  Master plan: issue #8400 (Step e)
  Spec: issue #8429 (Part 2)
""",
    )
    walk.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="Directory storing runner.lock and ledger.sqlite; use a separate directory from targeted run",
    )
    walk.add_argument(
        "--db",
        type=Path,
        help="Target SQLite database holding ulif_dictua_* tables (required unless --verify-ledger; e.g. data/sources.db)",
    )
    walk.add_argument(
        "--verify-ledger",
        action="store_true",
        help="Read and check ledger.sqlite page continuity without making requests or writing files (default: False)",
    )
    walk.add_argument(
        "--delay",
        type=float,
        default=MIN_DELAY_SECONDS,
        help="Seconds to wait between requests (must be >= 1.0; default: 1.0)",
    )
    walk.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Stop after processing this many register pages in this process invocation (default: None, process all)",
    )
    walk.add_argument(
        "--max-requests",
        type=int,
        default=None,
        help="Stop after making this many HTTP requests in this process invocation (default: None, unlimited)",
    )
    walk.add_argument(
        "--break-stale-lock",
        action="store_true",
        help="Break existing runner lock if holding PID is dead (default: False)",
    )
    walk.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress per-page progress lines (start banner, periodic progress, stop summary always print; default: False)",
    )
    walk.add_argument(
        "--progress-interval",
        type=float,
        default=None,
        help=(
            "Seconds between operator progress lines "
            f"(default: {DEFAULT_PROGRESS_INTERVAL_SECONDS:g}, or {PROGRESS_INTERVAL_ENV})"
        ),
    )
    walk.add_argument(
        "--start-headword",
        type=str,
        default="а",
        help="Initial search headword for page 1 on fresh crawl (default: 'а')",
    )

    parse = sub.add_parser(
        "parse",
        help="Parse stored bodies offline",
        description="Parse stored raw ULIF HTML responses into structured entries and sections.\nUse offline after fetch completes or during checkpoint verification; rejects state directories mixing targeted run and walk data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms parse \\
      --state-dir batch_state/ulif-homonyms/state --db data/sources.db

Outputs:
  Populates ulif_dictua_entries and ulif_dictua_sections (sources.db)
  Marks homonym_checked = 1 on stored entries

Exit codes:
  0: Parsing completed successfully
  1: Database or ledger error

Related:
  Runbook: issue #8423 (Step 5)
  Master plan: issue #8400 (Step c)
  Spec: issue #8429
""",
    )
    parse.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="Directory storing ledger.sqlite with stored raw response hashes (e.g. batch_state/ulif-homonyms/state)",
    )
    parse.add_argument(
        "--db",
        type=Path,
        required=True,
        help="SQLite database containing ulif_dictua_raw_responses to parse into entries (e.g. data/sources.db)",
    )

    status = sub.add_parser(
        "status",
        help="Print ledger progress",
        description="Inspect progress and health of a ULIF fetch run.\nUse anytime to monitor runner state, counts, requests, and ETA without interrupting the crawl.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms status \\
      --state-dir batch_state/ulif-homonyms/state

  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms status \\
      --state-dir batch_state/ulif-homonyms/state --watch 10

Outputs:
  Key=value progress report on stdout

Exit codes:
  0: Success
  1: Invalid arguments

Related:
  Runbook: issue #8423
  Master plan: issue #8400
  Spec: issue #8429
""",
    )
    status.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="Directory storing runner.lock and ledger.sqlite (e.g. batch_state/ulif-homonyms/state)",
    )
    status.add_argument(
        "--delay",
        type=float,
        default=MIN_DELAY_SECONDS,
        help="Expected delay in seconds between requests for remaining time calculation (default: 1.0)",
    )
    status.add_argument(
        "--watch",
        type=int,
        default=None,
        help="Reprint status every SECONDS (minimum 5) until interrupted (default: None, run once)",
    )
    status.add_argument(
        "--mode",
        choices=["auto", "walk", "targeted"],
        default="auto",
        help="Status formatting mode: auto (detect from ledger), walk (walk metrics), targeted (targeted metrics; default: auto)",
    )

    verify = sub.add_parser(
        "verify-complete",
        help="Verify stored entries match printed register size",
        description="Verify stored entries in ledger/database match printed ULIF register size.\nUse after completing the register walk to ensure zero missing pages or rows; do not use mid-crawl.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms verify-complete \\
      --state-dir batch_state/ulif-homonyms/state --db data/sources.db

  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms verify-complete \\
      --state-dir batch_state/ulif-homonyms/state --db data/sources.db --register-size 262812

Outputs:
  Detailed verification report on stderr itemising incomplete pages/rows if any

Exit codes:
  0: Verified complete (stored entries match printed register size, 0 incomplete pages/rows)
  1: Incomplete, missing rows/pages, or database/ledger error

Related:
  Runbook: issue #8423
  Master plan: issue #8400 (Step e)
  Spec: issue #8429 (Part 2)
""",
    )
    verify.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="Directory storing ledger.sqlite (e.g. batch_state/ulif-homonyms/state)",
    )
    verify.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Target SQLite database holding ulif_dictua_* tables (e.g. data/sources.db)",
    )
    verify.add_argument(
        "--register-size",
        type=int,
        default=None,
        help="Expected register size to verify against (default: None, reads from ledger metadata)",
    )

    suspects = sub.add_parser(
        "build-suspects",
        help="Write the homonym-suspect spelling list",
        description="Identify spellings in legacy dump that are suspect for homonym collisions.\nUse before starting a targeted homonym crawl to produce suspects.txt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms build-suspects \\
      --dump data/ulif_dump_all.db --vesum data/vesum.db \\
      --out batch_state/ulif-homonyms/suspects.txt

Outputs:
  Suspect spellings written to output text file

Exit codes:
  0: Report written successfully
  1: Input database error or invalid arguments

Related:
  Runbook: issue #8423 (Step 2)
  Master plan: issue #8400 (Step c)
  Spec: issue #8429
""",
    )
    suspects.add_argument(
        "--dump",
        type=Path,
        required=True,
        help="Path to legacy ULIF database (e.g. data/ulif_dump_all.db)",
    )
    suspects.add_argument(
        "--vesum",
        type=Path,
        required=True,
        help="Path to VESUM database (e.g. data/vesum.db)",
    )
    suspects.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for suspect spellings list (e.g. batch_state/ulif-homonyms/suspects.txt)",
    )

    a1 = sub.add_parser(
        "build-a1a2",
        help="Write A1–A2 lemmas minus spellings already stored",
        description="Extract A1–A2 CEFR vocabulary lemmas not yet stored in the ledger.\nUse to generate the secondary targeted crawl list.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  .venv/bin/python -m scripts.lexicon.runner.fetch_ulif_homonyms build-a1a2 \\
      --sources-db data/sources.db --vesum data/vesum.db \\
      --state-dir batch_state/ulif-homonyms/state \\
      --out batch_state/ulif-homonyms/a1a2.txt

Outputs:
  A1-A2 spellings written to output text file

Exit codes:
  0: Spelling list generated successfully
  1: Database or ledger error

Related:
  Runbook: issue #8423 (Step 4)
  Master plan: issue #8400 (Step c)
  Spec: issue #8429
""",
    )
    a1.add_argument(
        "--sources-db",
        type=Path,
        required=True,
        help="Path to sources.db containing puls_cefr table (e.g. data/sources.db)",
    )
    a1.add_argument(
        "--vesum",
        type=Path,
        required=True,
        help="Path to VESUM database (e.g. data/vesum.db)",
    )
    a1.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="Directory storing ledger.sqlite to check already stored spellings",
    )
    a1.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for A1-A2 spellings list (e.g. batch_state/ulif-homonyms/a1a2.txt)",
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        cmd_parts = [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.fetch_ulif_homonyms",
            "run",
            "--spellings-file",
            str(args.spellings_file),
            "--state-dir",
            str(args.state_dir),
            "--db",
            str(args.db),
            "--delay",
            f"{args.delay:g}",
        ]
        if args.max_spellings is not None:
            cmd_parts.extend(["--max-spellings", str(args.max_spellings)])
        if args.max_requests is not None:
            cmd_parts.extend(["--max-requests", str(args.max_requests)])
        if args.refetch:
            cmd_parts.append("--refetch")
        if args.break_stale_lock:
            cmd_parts.append("--break-stale-lock")
        if args.quiet:
            cmd_parts.append("--quiet")
        if args.progress_interval is not None:
            cmd_parts.extend(["--progress-interval", f"{args.progress_interval:g}"])
        resume_cmd = shlex.join(cmd_parts)

        old_sigterm = None
        if threading.current_thread() is threading.main_thread():

            def _on_sigterm(signum: int, frame: Any) -> None:
                raise InterruptedByOperator("SIGTERM")

            with contextlib.suppress(ValueError, OSError):
                old_sigterm = signal.signal(signal.SIGTERM, _on_sigterm)

        try:
            try:
                spellings = _spellings_from_file(args.spellings_file)
            except (KeyboardInterrupt, InterruptedByOperator):
                _print_stop_summary(
                    reason="interrupted by operator",
                    ledger=None,
                    requests_in_process=0,
                    elapsed_seconds=0.0,
                    resume_cmd=resume_cmd,
                )
                return EXIT_INTERRUPTED
            except Exception as exc:
                err_msg = f"failed to read spellings file: {exc}"
                print(err_msg, file=sys.stderr)
                _print_stop_summary(
                    reason=err_msg,
                    ledger=None,
                    requests_in_process=0,
                    elapsed_seconds=0.0,
                    resume_cmd=resume_cmd,
                )
                return EXIT_USAGE
            try:
                code = run_fetch(
                    spellings=spellings,
                    state_dir=args.state_dir,
                    db_path=args.db,
                    delay_seconds=args.delay,
                    max_spellings=args.max_spellings,
                    max_requests=args.max_requests,
                    refetch=args.refetch,
                    break_stale_lock=args.break_stale_lock,
                    quiet=args.quiet,
                    spellings_file=args.spellings_file,
                    resume_cmd=resume_cmd,
                    progress_interval=args.progress_interval,
                )
                if code == EXIT_OK:
                    ledger = SpellingLedger(args.state_dir / "ledger.sqlite")
                    try:
                        print(status_text(ledger, delay_seconds=args.delay, state_dir=args.state_dir))
                    finally:
                        ledger.close()
                return code
            except (KeyboardInterrupt, InterruptedByOperator):
                return EXIT_INTERRUPTED
        finally:
            if old_sigterm is not None:
                with contextlib.suppress(ValueError, OSError):
                    signal.signal(signal.SIGTERM, old_sigterm)
    if args.command == "walk":
        if args.verify_ledger:
            ledger_path = args.state_dir / "ledger.sqlite"
            try:
                checked = verify_ledger_continuity(ledger_path)
            except (ResumeMismatchError, sqlite3.Error) as exc:
                print(f"ledger continuity error: {exc}", file=sys.stderr)
                return EXIT_USAGE
            print(f"ledger continuity OK: {checked} pages checked")
            return EXIT_OK
        if args.db is None:
            parser.error("walk requires --db unless --verify-ledger is set")
        cmd_parts = [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.fetch_ulif_homonyms",
            "walk",
            "--state-dir",
            str(args.state_dir),
            "--db",
            str(args.db),
            "--delay",
            f"{args.delay:g}",
        ]
        if args.max_pages is not None:
            cmd_parts.extend(["--max-pages", str(args.max_pages)])
        if args.max_requests is not None:
            cmd_parts.extend(["--max-requests", str(args.max_requests)])
        if args.break_stale_lock:
            cmd_parts.append("--break-stale-lock")
        if args.quiet:
            cmd_parts.append("--quiet")
        if args.progress_interval is not None:
            cmd_parts.extend(["--progress-interval", f"{args.progress_interval:g}"])
        if args.start_headword != "а":
            cmd_parts.extend(["--start-headword", args.start_headword])
        resume_cmd = shlex.join(cmd_parts)

        old_sigterm = None
        if threading.current_thread() is threading.main_thread():

            def _on_sigterm(signum: int, frame: Any) -> None:
                raise InterruptedByOperator("SIGTERM")

            with contextlib.suppress(ValueError, OSError):
                old_sigterm = signal.signal(signal.SIGTERM, _on_sigterm)

        try:
            code = run_walk(
                state_dir=args.state_dir,
                db_path=args.db,
                delay_seconds=args.delay,
                max_pages=args.max_pages,
                max_requests=args.max_requests,
                break_stale_lock=args.break_stale_lock,
                quiet=args.quiet,
                start_headword=args.start_headword,
                resume_cmd=resume_cmd,
                progress_interval=args.progress_interval,
            )
            if code == EXIT_OK:
                ledger = SpellingLedger(args.state_dir / "ledger.sqlite")
                try:
                    print(status_text(ledger, delay_seconds=args.delay, state_dir=args.state_dir, mode="walk"))
                finally:
                    ledger.close()
            return code
        except (KeyboardInterrupt, InterruptedByOperator):
            return EXIT_INTERRUPTED
        finally:
            if old_sigterm is not None:
                with contextlib.suppress(ValueError, OSError):
                    signal.signal(signal.SIGTERM, old_sigterm)
    if args.command == "parse":
        cache = prepare_database(args.db)
        ledger = SpellingLedger(args.state_dir / "ledger.sqlite")
        try:
            try:
                differing = parse_stored(ledger, cache)
            except ValueError as exc:
                print(f"refusing to parse: {exc}", file=sys.stderr)
                return EXIT_USAGE
        finally:
            cache.close()
            ledger.close()
        print(f"differing_content_hashes={differing}")
        return EXIT_OK
    if args.command == "verify-complete":
        return verify_complete(
            state_dir=args.state_dir,
            db_path=args.db,
            expected_size=args.register_size,
        )
    if args.command == "status":
        watch_interval = args.watch
        if watch_interval is not None and watch_interval < 5:
            print("warning: --watch interval must be at least 5s, using 5s", file=sys.stderr)
            watch_interval = 5

        def _print_status_once() -> None:
            ledger_path = args.state_dir / "ledger.sqlite"
            if not ledger_path.exists():
                lock_path = args.state_dir / LOCK_NAME
                if lock_path.exists():
                    pid, started, _ = _read_lock(lock_path)
                    alive = None if pid is None else _pid_alive(pid)
                    if alive is True:
                        runner_str = f"running pid={pid} since={started}"
                    elif alive is False:
                        runner_str = f"stale_lock pid={pid}"
                    else:
                        runner_str = f"stale_lock pid={pid if pid is not None else 'unknown'}"
                else:
                    runner_str = "not_running"

                if args.mode == "walk":
                    print(
                        "\n".join(
                            [
                                "pages_done=0",
                                "pages_total=0",
                                "entries_stored=0",
                                "spellings=0",
                                "multi_entry_spellings=0",
                                "paradigm_from_entry=0",
                                "paradigm_requested=0",
                                "unknown_control_entries=0",
                                "requests_made=0",
                                "mean_requests_per_entry=0.00",
                                "estimated_time_remaining_seconds=unknown",
                                "register_size=unknown",
                                "register_size_changes=0",
                                "differing_groups=0",
                                "complete=not_started",
                                f"runner={runner_str}",
                                "last_update=none",
                                "seconds_since_last_update=unknown",
                            ]
                        )
                    )
                else:
                    print(
                        "\n".join(
                            [
                                "spellings_total=0",
                                "stored=0",
                                "absent_from_ulif=0",
                                "retry_scheduled=0",
                                "error=0",
                                "entries_stored=0",
                                "requests_made=0",
                                "mean_requests_per_spelling=0.00",
                                "estimated_time_remaining_seconds=0",
                                "register_size=unknown",
                                "complete=not_started",
                                "differing_content_hashes=0",
                                f"runner={runner_str}",
                                "last_update=none",
                                "seconds_since_last_update=unknown",
                            ]
                        )
                    )
            else:
                ledger = SpellingLedger(ledger_path)
                try:
                    print(status_text(ledger, delay_seconds=args.delay, state_dir=args.state_dir, mode=args.mode))
                finally:
                    ledger.close()

        while True:
            _print_status_once()
            if watch_interval is None:
                break
            try:
                time.sleep(watch_interval)
            except KeyboardInterrupt:
                break
        return EXIT_OK
    if args.command == "build-suspects":
        from scripts.lexicon.tools.report_ulif_homonym_suspects import build_report

        build_report(args.dump, args.vesum, args.out)
        return EXIT_OK
    if args.command == "build-a1a2":
        stored: set[str] = set()
        ledger_path = args.state_dir / "ledger.sqlite"
        if ledger_path.exists():
            ledger = SpellingLedger(ledger_path)
            try:
                stored = ledger.stored_spellings()
            finally:
                ledger.close()
        spellings = build_a1_a2_spellings(sources_db=args.sources_db, vesum_db=args.vesum, stored=stored)
        if not args.out.parent.exists():
            _ensure_private_dir(args.out.parent)
        created = not args.out.exists()
        fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("".join(f"{spelling}\n" for spelling in spellings))
        if created:
            _ensure_private_file(args.out)
        print(f"a1a2_spellings={len(spellings)}")
        return EXIT_OK
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
