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
import hashlib
import json
import os
import sqlite3
import sys
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
                raise SystemExit(
                    f"refusing to start: runner lock held by live pid {pid} since {started} ({self.path})"
                )
            print(
                f"stale lock: pid {pid} is not alive (started {started}) at {self.path}",
                file=sys.stderr,
            )
            if not self.break_stale:
                raise SystemExit("refusing to start: stale lock; pass --break-stale-lock")
            self.path.unlink()
        payload = f"{os.getpid()}\n{_now_iso()}\n"
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError as exc:
            raise SystemExit(f"refusing to start: lock appeared at {self.path}") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        self._held = True

    def release(self) -> None:
        if not self._held or not self.path.exists():
            return
        pid, _started, _raw = _read_lock(self.path)
        if pid == os.getpid():
            self.path.unlink()
        self._held = False


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
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
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
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        self.conn.commit()
        self._ensure_duplicate_content_column()

    def _ensure_duplicate_content_column(self) -> None:
        columns = {str(row[1]) for row in self.conn.execute("PRAGMA table_info(spellings)")}
        if "duplicate_content" not in columns:
            self.conn.execute(
                "ALTER TABLE spellings ADD COLUMN duplicate_content INTEGER NOT NULL DEFAULT 0"
            )
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

    def add_requests(self, count: int) -> None:
        current = int(self.meta("requests_made", "0") or "0")
        self.set_meta("requests_made", str(current + count))

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

    def tab_responses(self, spelling: str, homonym_index: int) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT * FROM responses
                WHERE spelling = ? AND role = 'tab' AND homonym_index = ?
                ORDER BY id
                """,
                (spelling, homonym_index),
            )
        )

    def stored_spellings(self) -> set[str]:
        rows = self.conn.execute("SELECT spelling FROM spellings WHERE state = 'stored'")
        return {str(row["spelling"]) for row in rows}


def status_text(ledger: SpellingLedger, *, delay_seconds: float) -> str:
    counts = ledger.counts()
    requests_made = int(ledger.meta("requests_made", "0") or "0")
    finished = counts["stored"] + counts["absent_from_ulif"] + counts["retry_scheduled"] + counts["error"]
    mean = (requests_made / finished) if finished else 0.0
    remaining = counts["pending"] + counts["retry_scheduled"] + counts["error"]
    if remaining == 0:
        eta: str | float = 0
    elif finished == 0:
        eta = "unknown"
    else:
        eta = round(remaining * mean * delay_seconds, 1)
    register = ledger.meta("register_size", "") or "unknown"
    complete = counts["pending"] == 0 and counts["retry_scheduled"] == 0 and counts["error"] == 0
    differing = ledger.meta("differing_content_hashes", "0")
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
        f"complete={'yes' if complete else 'no'}",
        f"differing_content_hashes={differing}",
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
    ) -> None:
        if delay_seconds < MIN_DELAY_SECONDS:
            raise ValueError(f"delay must be >= {MIN_DELAY_SECONDS}, got {delay_seconds}")
        self.transport = transport
        self.delay_seconds = delay_seconds
        self.sleep = sleep
        self.clock = clock
        self.max_requests = max_requests
        self.requests_made = 0
        self._last_at = 0.0

    def exchange(self, method: str, fields: dict[str, str] | None) -> tuple[str, bytes]:
        """Return ``(body, redacted_request)``. Raises on 403, exhaustion, or a dead session."""
        import requests

        redacted = _redact_payload(fields, method=method)
        last_code = "http_error"
        for attempt in range(1, MAX_HTTP_ATTEMPTS + 1):
            self._wait_turn()
            if self.max_requests is not None and self.requests_made >= self.max_requests:
                raise RequestCap(str(self.max_requests))
            try:
                result = self.transport(method, fields)
            except requests.RequestException:
                self.requests_made += 1
                self._last_at = self.clock()
                last_code = "transport_error"
                if attempt == MAX_HTTP_ATTEMPTS:
                    raise RequestExhausted(last_code) from None
                self.sleep(_retry_after_seconds({}, attempt))
                continue
            self.requests_made += 1
            self._last_at = self.clock()
            code = result.status_code
            if code == 403:
                raise Forbidden("http_403")
            if code == 500 or (code == 200 and _validation_failure(result.text)):
                raise SessionInvalid(f"http_{code}" if code != 200 else "event_validation")
            if code == 429 or code >= 500:
                last_code = f"http_{code}"
                if attempt == MAX_HTTP_ATTEMPTS:
                    raise RequestExhausted(last_code)
                self.sleep(_retry_after_seconds(result.headers, attempt))
                continue
            if code != 200:
                last_code = f"http_{code}"
                if attempt == MAX_HTTP_ATTEMPTS:
                    raise RequestExhausted(last_code)
                self.sleep(_retry_after_seconds(result.headers, attempt))
                continue
            return result.text, redacted
        raise RequestExhausted(last_code)

    def _wait_turn(self) -> None:
        if not self._last_at:
            return
        elapsed = self.clock() - self._last_at
        if elapsed < self.delay_seconds:
            self.sleep(self.delay_seconds - elapsed)


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
        ordered = _dedupe_register_rows(
            [*before, *({**row, "page_delta": 0} for row in matches), *after]
        )
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
            self.ledger.set_meta("register_size", str(size))


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


def parse_stored(ledger: SpellingLedger, cache: sqlite3.Connection) -> int:
    """Parse stored bodies offline and write homonym rows. Returns differing-hash count."""
    from scripts.wiki.sources_db import store_ulif_dictua_entry

    differing = 0
    spellings = [
        str(row["spelling"])
        for row in ledger.conn.execute("SELECT spelling FROM spellings WHERE state = 'stored' ORDER BY spelling")
    ]
    for spelling in spellings:
        parsed_rows: list[dict[str, Any]] = []
        section_sets: list[dict[str, object]] = []
        raw_sets: list[dict[str, str]] = []
        for entry in ledger.entry_responses(spelling):
            html = _load_body(cache, str(entry["response_sha256"]))
            parsed = parse_ulif_entry(
                html,
                homonym_index=int(entry["homonym_index"]),
                register_position=str(entry["register_position"]),
            )
            sections: dict[str, object] = {}
            raw: dict[str, str] = {}
            for tab in ledger.tab_responses(spelling, int(entry["homonym_index"])):
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
                error=(
                    "printed_number_mismatch "
                    f"register={list(register)} printed={list(printed)}"
                ),
            )
            continue
        differing += _write_group(cache, spelling, parsed_rows, section_sets, raw_sets, store_ulif_dictua_entry)
        ledger.set_duplicate_content(spelling, _duplicate_content(parsed_rows))
    ledger.set_meta("differing_content_hashes", str(differing))
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
    unchanged = (
        len(parsed_rows) == 1
        and len(existing) == 1
        and str(existing[0][1] or "") == str(parsed_rows[0]["content_sha256"])
        and str(existing[0][1] or "") != ""
    )
    if unchanged:
        cache.execute(
            """
            UPDATE ulif_dictua_entries
            SET homonym_checked = 1
            WHERE normalized_query = ? AND homonym_index = ?
            """,
            (normalized, int(existing[0][0])),
        )
        cache.commit()
        return 0
    if len(parsed_rows) == 1 and len(existing) == 1:
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

    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = _ulif_dictua_conn(db_path, create=True)
    assert conn is not None
    return conn


def _spellings_from_file(path: Path) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.split("\t", 1)[0].strip()
        if not text or text.startswith("#"):
            continue
        key = normalize_ulif_spelling(text)
        if key in seen:
            continue
        seen.add(key)
        found.append(key)
    return found


def _requests_transport(user_agent: str) -> Transport:
    import requests

    session = requests.Session()
    session.headers["User-Agent"] = user_agent

    def send(method: str, data: dict[str, str] | None) -> HttpResult:
        response = session.request(method, ULIF_URL, data=data, timeout=REQUEST_TIMEOUT_SECONDS)
        return HttpResult(response.status_code, response.text, dict(response.headers))

    return send


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
    transport: Transport | None = None,
    sleep: SleepFn = _default_sleep,
    clock: ClockFn = time.monotonic,
    scanner: Scanner = scan_for_legacy_crawler,
) -> int:
    if delay_seconds < MIN_DELAY_SECONDS:
        print(f"delay must be >= {MIN_DELAY_SECONDS}", file=sys.stderr)
        return EXIT_USAGE
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = RunnerLock(state_dir, break_stale=break_stale_lock, scanner=scanner)
    lock.acquire()
    ledger: SpellingLedger | None = None
    cache: sqlite3.Connection | None = None
    client: PoliteClient | None = None
    try:
        try:
            cache = prepare_database(db_path)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_USAGE
        ledger = SpellingLedger(state_dir / "ledger.sqlite")
        ledger.set_meta("delay_seconds", str(delay_seconds))
        for spelling in spellings:
            ledger.ensure(spelling)
        client = PoliteClient(
            transport or _requests_transport(declared_user_agent()),
            delay_seconds=delay_seconds,
            sleep=sleep,
            clock=clock,
            max_requests=max_requests,
        )
        fetcher = HomonymFetcher(client, ledger, cache)
        consecutive_retries = 0
        processed = 0
        for spelling in spellings:
            state = ledger.state_of(spelling)
            if state in COMPLETE_STATES and not refetch:
                continue
            if max_spellings is not None and processed >= max_spellings:
                break
            try:
                outcome = fetcher.fetch(spelling)
            except RequestCap:
                break
            except Forbidden:
                ledger.mark(spelling, "error", error="http_403")
                print("stopping: HTTP 403 from ULIF", file=sys.stderr)
                return EXIT_FORBIDDEN
            except RequestExhausted as exc:
                ledger.mark(spelling, "retry_scheduled", error=exc.code)
                consecutive_retries += 1
                processed += 1
                if consecutive_retries >= CONSECUTIVE_RETRY_STOP:
                    print(
                        "stopping: three consecutive spellings ended retry_scheduled",
                        file=sys.stderr,
                    )
                    return EXIT_RETRY_STORM
                continue
            except SessionInvalid as exc:
                ledger.mark(spelling, "retry_scheduled", error=str(exc))
                consecutive_retries += 1
                processed += 1
                if consecutive_retries >= CONSECUTIVE_RETRY_STOP:
                    print(
                        "stopping: three consecutive spellings ended retry_scheduled",
                        file=sys.stderr,
                    )
                    return EXIT_RETRY_STORM
                continue
            except Exception as exc:
                print(f"interrupted on {spelling}: {exc}", file=sys.stderr)
                return EXIT_INTERRUPTED
            ledger.mark(
                spelling,
                outcome.state,
                entry_count=outcome.entry_count,
                straddled=outcome.straddled,
            )
            if outcome.state in COMPLETE_STATES:
                consecutive_retries = 0
            processed += 1
        return EXIT_OK
    finally:
        if ledger is not None and client is not None:
            ledger.add_requests(client.requests_made)
        if cache is not None:
            cache.close()
        if ledger is not None:
            ledger.close()
        lock.release()


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


def _positive_delay(value: str) -> float:
    delay = float(value)
    if delay < MIN_DELAY_SECONDS:
        raise argparse.ArgumentTypeError(f"delay must be >= {MIN_DELAY_SECONDS} seconds")
    return delay


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Fetch spellings into the raw cache")
    run.add_argument("--spellings-file", type=Path, required=True)
    run.add_argument("--state-dir", type=Path, required=True)
    run.add_argument("--db", type=Path, required=True)
    run.add_argument("--delay", type=_positive_delay, default=MIN_DELAY_SECONDS)
    run.add_argument("--max-spellings", type=int, default=None)
    run.add_argument("--max-requests", type=int, default=None)
    run.add_argument("--refetch", action="store_true")
    run.add_argument("--break-stale-lock", action="store_true")

    parse = sub.add_parser("parse", help="Parse stored bodies offline")
    parse.add_argument("--state-dir", type=Path, required=True)
    parse.add_argument("--db", type=Path, required=True)

    status = sub.add_parser("status", help="Print ledger progress")
    status.add_argument("--state-dir", type=Path, required=True)
    status.add_argument("--delay", type=_positive_delay, default=MIN_DELAY_SECONDS)

    suspects = sub.add_parser("build-suspects", help="Write the homonym-suspect spelling list")
    suspects.add_argument("--dump", type=Path, required=True)
    suspects.add_argument("--vesum", type=Path, required=True)
    suspects.add_argument("--out", type=Path, required=True)

    a1 = sub.add_parser("build-a1a2", help="Write A1–A2 lemmas minus spellings already stored")
    a1.add_argument("--sources-db", type=Path, required=True)
    a1.add_argument("--vesum", type=Path, required=True)
    a1.add_argument("--state-dir", type=Path, required=True)
    a1.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "run":
        spellings = _spellings_from_file(args.spellings_file)
        code = run_fetch(
            spellings=spellings,
            state_dir=args.state_dir,
            db_path=args.db,
            delay_seconds=args.delay,
            max_spellings=args.max_spellings,
            max_requests=args.max_requests,
            refetch=args.refetch,
            break_stale_lock=args.break_stale_lock,
        )
        ledger = SpellingLedger(args.state_dir / "ledger.sqlite")
        try:
            print(status_text(ledger, delay_seconds=args.delay))
        finally:
            ledger.close()
        return code
    if args.command == "parse":
        cache = prepare_database(args.db)
        ledger = SpellingLedger(args.state_dir / "ledger.sqlite")
        try:
            differing = parse_stored(ledger, cache)
        finally:
            cache.close()
            ledger.close()
        print(f"differing_content_hashes={differing}")
        return EXIT_OK
    if args.command == "status":
        ledger_path = args.state_dir / "ledger.sqlite"
        if not ledger_path.exists():
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
                        "complete=yes",
                        "differing_content_hashes=0",
                    ]
                )
            )
            return EXIT_OK
        ledger = SpellingLedger(ledger_path)
        try:
            print(status_text(ledger, delay_seconds=args.delay))
        finally:
            ledger.close()
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
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("".join(f"{spelling}\n" for spelling in spellings), encoding="utf-8")
        print(f"a1a2_spellings={len(spellings)}")
        return EXIT_OK
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
