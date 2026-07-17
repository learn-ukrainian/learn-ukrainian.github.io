"""VPS/network host durable write-through cache (#5230 PR3).

Independent of the local run ledger (spec §6): exclusive OS lock, request-level
fenced claims reusing PR2 CAS/generation machinery, and atomic raw cache rows
(metadata + compressed body in one SQLite transaction).

Network workers that open this cache must never construct or open ``sources.db``.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import sqlite3
import time
import uuid
import zlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import (
    ADAPTER_VERSION,
    NETWORK_CACHE_SCHEMA_VERSION,
    REQUEST_POLICY_VERSION,
    ErrorCode,
    canonical_json,
)
from scripts.lexicon.runner.sources_guard import (
    SourcesDbForbiddenError,
    assert_not_sources_db,
    guard_network_worker,
)

# Active-computation lease for in-flight fetches (transport itself holds no lease).
DEFAULT_REQUEST_LEASE_TTL_SECONDS = 300
DEFAULT_MAX_FETCH_ATTEMPTS = 5


class RequestClaimState(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    DONE = "done"
    RETRY_SCHEDULED = "retry_scheduled"
    FAILED_TERMINAL = "failed_terminal"


class CacheCasStatus(StrEnum):
    OK = "ok"
    STALE_COMMIT_REJECTED = "stale_commit_rejected"
    DUPLICATE_RUNNER_REFUSED = "duplicate_runner_refused"
    NOT_FOUND = "not_found"
    INVALID_STATE = "invalid_state"
    CACHE_HIT = "cache_hit"
    ATTEMPT_CAP_EXHAUSTED = "attempt_cap_exhausted"
    HOST_COOLDOWN = "host_cooldown"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_cache (
    request_key TEXT PRIMARY KEY,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    request_body_hash TEXT NOT NULL,
    headers_json TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    request_policy_version TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_headers_json TEXT NOT NULL,
    body_sha256 TEXT NOT NULL,
    body_zlib BLOB NOT NULL,
    freshness_policy TEXT NOT NULL DEFAULT '',
    fetched_at REAL NOT NULL,
    meta_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS request_claims (
    request_key TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    lease_generation INTEGER NOT NULL DEFAULT 0,
    owner TEXT,
    leased_until REAL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS parsed_cache (
    parsed_key TEXT PRIMARY KEY,
    request_key TEXT NOT NULL,
    body_sha256 TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    normalizer_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    parsed_sha256 TEXT NOT NULL,
    parsed_zlib BLOB NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY (request_key) REFERENCES raw_cache(request_key)
);

CREATE INDEX IF NOT EXISTS idx_parsed_request ON parsed_cache(request_key);

CREATE TABLE IF NOT EXISTS host_cooldowns (
    host TEXT PRIMARY KEY,
    next_allowed_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fetch_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    request_key TEXT,
    created_at REAL NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}'
);
"""


@dataclass(frozen=True, slots=True)
class CacheCasResult:
    status: CacheCasStatus
    detail: str = ""
    lease_generation: int | None = None
    request_key: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is CacheCasStatus.OK


@dataclass(frozen=True, slots=True)
class RequestClaimResult:
    status: CacheCasStatus
    request_key: str
    lease_generation: int | None = None
    attempt_count: int | None = None
    detail: str = ""
    cached_body: bytes | None = None
    body_sha256: str | None = None
    status_code: int | None = None

    @property
    def ok(self) -> bool:
        return self.status in {CacheCasStatus.OK, CacheCasStatus.CACHE_HIT}

    @property
    def is_cache_hit(self) -> bool:
        return self.status is CacheCasStatus.CACHE_HIT


@dataclass(frozen=True, slots=True)
class RawCacheEntry:
    request_key: str
    method: str
    url: str
    request_body_hash: str
    headers_json: str
    adapter_version: str
    request_policy_version: str
    status_code: int
    response_headers_json: str
    body_sha256: str
    body: bytes
    freshness_policy: str
    fetched_at: float
    meta_json: str


class DuplicateCacheRunnerError(RuntimeError):
    """Second process tried to open the same network cache for writing."""


def compute_request_key(
    *,
    method: str,
    url: str,
    request_body: bytes | str | None = None,
    response_affecting_headers: dict[str, str] | None = None,
    adapter_version: str = ADAPTER_VERSION,
    request_policy_version: str = REQUEST_POLICY_VERSION,
) -> str:
    """Canonical raw request key (spec §5)."""
    if request_body is None:
        body_repr = ""
    elif isinstance(request_body, bytes):
        body_repr = hashlib.sha256(request_body).hexdigest()
    else:
        body_repr = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
    payload = {
        "adapter_version": adapter_version,
        "method": method.upper(),
        "request_body": body_repr,
        "request_policy_version": request_policy_version,
        "response_affecting_headers": {
            str(k).lower(): str(v)
            for k, v in sorted((response_affecting_headers or {}).items(), key=lambda kv: kv[0].lower())
        },
        "url": url,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def compute_parsed_key(
    *,
    request_key: str,
    body_sha256: str,
    parser_version: str,
    normalizer_version: str,
    schema_version: str,
) -> str:
    payload = {
        "body_sha256": body_sha256,
        "normalizer_version": normalizer_version,
        "parser_version": parser_version,
        "request_key": request_key,
        "schema_version": schema_version,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class NetworkCache:
    """Single-writer durable network cache (VPS-side, independent of local ledger)."""

    def __init__(
        self,
        path: Path,
        *,
        max_attempts: int = DEFAULT_MAX_FETCH_ATTEMPTS,
        lease_ttl_seconds: float = DEFAULT_REQUEST_LEASE_TTL_SECONDS,
        owner_id: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_attempts = int(max_attempts)
        self.lease_ttl_seconds = float(lease_ttl_seconds)
        self.owner_id = owner_id or f"net-{uuid.uuid4().hex[:12]}"
        self._conn: sqlite3.Connection | None = None
        self._lock_fh: Any | None = None
        self._locked = False
        # Crash-injection points (tests only).
        self.crash_after_claim = False
        self.crash_mid_cache_write = False
        self.crash_after_cache_write = False
        self.fetch_count = 0  # instrumentation: real network/fetch attempts

    def open(self, *, create: bool = True) -> None:
        if self._conn is not None:
            return
        # Hard guard: never point the cache path at sources.db.
        assert_not_sources_db(self.path)
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_fh = open(lock_path, "a+", encoding="utf-8")  # noqa: SIM115
        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            lock_fh.close()
            raise DuplicateCacheRunnerError(
                f"duplicate runner refused: network cache lock held on {lock_path}"
            ) from exc
        self._lock_fh = lock_fh
        self._locked = True
        lock_fh.seek(0)
        lock_fh.truncate()
        lock_fh.write(f"{self.owner_id}\n{time.time():.6f}\n")
        lock_fh.flush()

        self._conn = sqlite3.connect(self.path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = FULL")
        self._conn.executescript(SCHEMA_SQL)
        self._conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("schema_version", NETWORK_CACHE_SCHEMA_VERSION),
        )

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        if self._lock_fh is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(self._lock_fh.fileno(), fcntl.LOCK_UN)
            self._lock_fh.close()
            self._lock_fh = None
        self._locked = False

    def __enter__(self) -> NetworkCache:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _require(self) -> sqlite3.Connection:
        if self._conn is None or not self._locked:
            raise RuntimeError("network cache not open under exclusive writer lock")
        return self._conn

    def _now(self, now: float | None = None) -> float:
        return time.time() if now is None else float(now)

    def _event(self, event: str, request_key: str | None = None, **payload: Any) -> None:
        conn = self._require()
        conn.execute(
            "INSERT INTO fetch_events(event, request_key, created_at, payload_json) "
            "VALUES (?, ?, ?, ?)",
            (event, request_key, self._now(), canonical_json(payload)),
        )

    def set_host_cooldown(self, host: str, next_allowed_at: float) -> None:
        conn = self._require()
        conn.execute(
            "INSERT INTO host_cooldowns(host, next_allowed_at) VALUES (?, ?) "
            "ON CONFLICT(host) DO UPDATE SET next_allowed_at = excluded.next_allowed_at",
            (host, float(next_allowed_at)),
        )

    def host_cooldown_active(self, host: str, *, now: float | None = None) -> float | None:
        """Return next_allowed_at if host is still cooling down, else None."""
        conn = self._require()
        ts = self._now(now)
        row = conn.execute(
            "SELECT next_allowed_at FROM host_cooldowns WHERE host = ?",
            (host,),
        ).fetchone()
        if row is None:
            return None
        until = float(row["next_allowed_at"])
        return until if until > ts else None

    def get_raw(self, request_key: str) -> RawCacheEntry | None:
        conn = self._require()
        row = conn.execute(
            "SELECT * FROM raw_cache WHERE request_key = ?",
            (request_key,),
        ).fetchone()
        if row is None:
            return None
        body = zlib.decompress(bytes(row["body_zlib"]))
        return RawCacheEntry(
            request_key=str(row["request_key"]),
            method=str(row["method"]),
            url=str(row["url"]),
            request_body_hash=str(row["request_body_hash"]),
            headers_json=str(row["headers_json"]),
            adapter_version=str(row["adapter_version"]),
            request_policy_version=str(row["request_policy_version"]),
            status_code=int(row["status_code"]),
            response_headers_json=str(row["response_headers_json"]),
            body_sha256=str(row["body_sha256"]),
            body=body,
            freshness_policy=str(row["freshness_policy"] or ""),
            fetched_at=float(row["fetched_at"]),
            meta_json=str(row["meta_json"] or "{}"),
        )

    def ensure_claim_row(self, request_key: str, *, now: float | None = None) -> None:
        conn = self._require()
        ts = self._now(now)
        conn.execute(
            "INSERT OR IGNORE INTO request_claims("
            "request_key, state, lease_generation, owner, leased_until, "
            "attempt_count, updated_at"
            ") VALUES (?, ?, 0, NULL, NULL, 0, ?)",
            (request_key, RequestClaimState.PENDING.value, ts),
        )

    def claim_request(
        self,
        request_key: str,
        owner: str,
        *,
        now: float | None = None,
        host: str | None = None,
    ) -> RequestClaimResult:
        """Fenced claim. Cache hits return CACHE_HIT without incrementing fetch_count."""
        conn = self._require()
        ts = self._now(now)
        if host is not None:
            cool = self.host_cooldown_active(host, now=ts)
            if cool is not None:
                return RequestClaimResult(
                    status=CacheCasStatus.HOST_COOLDOWN,
                    request_key=request_key,
                    detail=f"host cooldown until {cool}",
                )

        # Cache hit: no fetch, no lease needed for reparse-from-cache path.
        cached = self.get_raw(request_key)
        if cached is not None:
            self.ensure_claim_row(request_key, now=ts)
            self._event("cache_hit", request_key, body_sha256=cached.body_sha256)
            return RequestClaimResult(
                status=CacheCasStatus.CACHE_HIT,
                request_key=request_key,
                cached_body=cached.body,
                body_sha256=cached.body_sha256,
                status_code=cached.status_code,
                detail="raw cache hit; parse without fetch",
            )

        self.ensure_claim_row(request_key, now=ts)
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                "SELECT * FROM request_claims WHERE request_key = ?",
                (request_key,),
            ).fetchone()
            assert row is not None
            state = str(row["state"])
            if state in {
                RequestClaimState.DONE.value,
                RequestClaimState.FAILED_TERMINAL.value,
            }:
                # Race: another writer may have committed raw since we checked.
                again = conn.execute(
                    "SELECT body_sha256, body_zlib, status_code FROM raw_cache "
                    "WHERE request_key = ?",
                    (request_key,),
                ).fetchone()
                if again is not None:
                    conn.execute("COMMIT")
                    body = zlib.decompress(bytes(again["body_zlib"]))
                    return RequestClaimResult(
                        status=CacheCasStatus.CACHE_HIT,
                        request_key=request_key,
                        cached_body=body,
                        body_sha256=str(again["body_sha256"]),
                        status_code=int(again["status_code"]),
                    )
                conn.execute("ROLLBACK")
                return RequestClaimResult(
                    status=CacheCasStatus.INVALID_STATE,
                    request_key=request_key,
                    detail=f"not claimable in state={state}",
                )
            if state == RequestClaimState.LEASED.value and float(row["leased_until"] or 0) >= ts:
                conn.execute("ROLLBACK")
                return RequestClaimResult(
                    status=CacheCasStatus.INVALID_STATE,
                    request_key=request_key,
                    detail="request already leased",
                )
            attempt_count = int(row["attempt_count"])
            if attempt_count >= self.max_attempts:
                conn.execute(
                    "UPDATE request_claims SET state = ?, error_code = ?, updated_at = ? "
                    "WHERE request_key = ?",
                    (
                        RequestClaimState.FAILED_TERMINAL.value,
                        "attempt_cap_exhausted",
                        ts,
                        request_key,
                    ),
                )
                conn.execute("COMMIT")
                return RequestClaimResult(
                    status=CacheCasStatus.ATTEMPT_CAP_EXHAUSTED,
                    request_key=request_key,
                    attempt_count=attempt_count,
                    detail="total automatic fetch attempts exhausted",
                )

            new_gen = int(row["lease_generation"]) + 1
            new_attempts = attempt_count + 1
            leased_until = ts + self.lease_ttl_seconds
            cur = conn.execute(
                "UPDATE request_claims SET state = ?, lease_generation = ?, owner = ?, "
                "leased_until = ?, attempt_count = ?, updated_at = ? "
                "WHERE request_key = ? AND lease_generation = ? AND state IN (?, ?, ?)",
                (
                    RequestClaimState.LEASED.value,
                    new_gen,
                    owner,
                    leased_until,
                    new_attempts,
                    ts,
                    request_key,
                    int(row["lease_generation"]),
                    RequestClaimState.PENDING.value,
                    RequestClaimState.RETRY_SCHEDULED.value,
                    RequestClaimState.LEASED.value,
                ),
            )
            if cur.rowcount != 1:
                conn.execute("ROLLBACK")
                return RequestClaimResult(
                    status=CacheCasStatus.STALE_COMMIT_REJECTED,
                    request_key=request_key,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                )
            self._event(
                "request_claimed",
                request_key,
                lease_generation=new_gen,
                owner=owner,
                attempt_count=new_attempts,
            )
            if self.crash_after_claim:
                raise RuntimeError("injected crash: after_claim")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        return RequestClaimResult(
            status=CacheCasStatus.OK,
            request_key=request_key,
            lease_generation=new_gen,
            attempt_count=new_attempts,
        )

    def commit_raw(
        self,
        request_key: str,
        owner: str,
        lease_generation: int,
        *,
        method: str,
        url: str,
        request_body: bytes | str | None = None,
        response_affecting_headers: dict[str, str] | None = None,
        adapter_version: str = ADAPTER_VERSION,
        request_policy_version: str = REQUEST_POLICY_VERSION,
        status_code: int,
        response_headers: dict[str, str] | None = None,
        body: bytes,
        freshness_policy: str = "",
        meta: dict[str, Any] | None = None,
        now: float | None = None,
    ) -> CacheCasResult:
        """Atomic raw cache write (metadata + compressed body) under CAS claim."""
        conn = self._require()
        ts = self._now(now)
        if isinstance(request_body, str):
            body_bytes_req = request_body.encode("utf-8")
        elif request_body is None:
            body_bytes_req = b""
        else:
            body_bytes_req = request_body
        req_body_hash = hashlib.sha256(body_bytes_req).hexdigest()
        body_sha = hashlib.sha256(body).hexdigest()
        body_z = zlib.compress(body, level=9)

        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                "SELECT * FROM request_claims WHERE request_key = ?",
                (request_key,),
            ).fetchone()
            if row is None:
                conn.execute("ROLLBACK")
                return CacheCasResult(status=CacheCasStatus.NOT_FOUND, detail="claim missing")
            if (
                str(row["owner"]) != owner
                or int(row["lease_generation"]) != int(lease_generation)
                or str(row["state"]) != RequestClaimState.LEASED.value
            ):
                conn.execute("ROLLBACK")
                self._event(
                    ErrorCode.STALE_COMMIT_REJECTED.value,
                    request_key,
                    op="commit_raw",
                    lease_generation=lease_generation,
                    owner=owner,
                )
                return CacheCasResult(
                    status=CacheCasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                    lease_generation=lease_generation,
                    request_key=request_key,
                )

            # Idempotent: identical raw body already present.
            existing = conn.execute(
                "SELECT body_sha256 FROM raw_cache WHERE request_key = ?",
                (request_key,),
            ).fetchone()
            if existing is not None and str(existing["body_sha256"]) == body_sha:
                conn.execute(
                    "UPDATE request_claims SET state = ?, owner = NULL, leased_until = NULL, "
                    "updated_at = ? WHERE request_key = ? AND lease_generation = ?",
                    (RequestClaimState.DONE.value, ts, request_key, int(lease_generation)),
                )
                conn.execute("COMMIT")
                return CacheCasResult(
                    status=CacheCasStatus.OK,
                    lease_generation=lease_generation,
                    request_key=request_key,
                    detail="raw already cached",
                )
            if existing is not None:
                conn.execute("ROLLBACK")
                return CacheCasResult(
                    status=CacheCasStatus.INVALID_STATE,
                    detail="raw cache hash conflict",
                    request_key=request_key,
                )

            if self.crash_mid_cache_write:
                raise RuntimeError("injected crash: mid_cache_write")

            conn.execute(
                "INSERT INTO raw_cache("
                "request_key, method, url, request_body_hash, headers_json, "
                "adapter_version, request_policy_version, status_code, "
                "response_headers_json, body_sha256, body_zlib, freshness_policy, "
                "fetched_at, meta_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    request_key,
                    method.upper(),
                    url,
                    req_body_hash,
                    canonical_json(
                        {
                            str(k).lower(): str(v)
                            for k, v in (response_affecting_headers or {}).items()
                        }
                    ),
                    adapter_version,
                    request_policy_version,
                    int(status_code),
                    canonical_json(
                        {str(k).lower(): str(v) for k, v in (response_headers or {}).items()}
                    ),
                    body_sha,
                    body_z,
                    freshness_policy,
                    ts,
                    canonical_json(meta or {}),
                ),
            )
            conn.execute(
                "UPDATE request_claims SET state = ?, owner = NULL, leased_until = NULL, "
                "updated_at = ? WHERE request_key = ? AND lease_generation = ?",
                (RequestClaimState.DONE.value, ts, request_key, int(lease_generation)),
            )
            self._event(
                "raw_cache_committed",
                request_key,
                body_sha256=body_sha,
                status_code=status_code,
                lease_generation=lease_generation,
            )
            if self.crash_after_cache_write:
                raise RuntimeError("injected crash: after_cache_write")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        return CacheCasResult(
            status=CacheCasStatus.OK,
            lease_generation=lease_generation,
            request_key=request_key,
        )

    def commit_retry_scheduled(
        self,
        request_key: str,
        owner: str,
        lease_generation: int,
        *,
        host: str | None = None,
        next_allowed_at: float | None = None,
        error_code: str = "http_429",
        now: float | None = None,
    ) -> CacheCasResult:
        """Release claim to retry_scheduled; optionally advance host-wide cooldown."""
        conn = self._require()
        ts = self._now(now)
        conn.execute("BEGIN IMMEDIATE")
        try:
            cur = conn.execute(
                "UPDATE request_claims SET state = ?, owner = NULL, leased_until = NULL, "
                "error_code = ?, updated_at = ? "
                "WHERE request_key = ? AND owner = ? AND lease_generation = ? AND state = ?",
                (
                    RequestClaimState.RETRY_SCHEDULED.value,
                    error_code,
                    ts,
                    request_key,
                    owner,
                    int(lease_generation),
                    RequestClaimState.LEASED.value,
                ),
            )
            if cur.rowcount != 1:
                conn.execute("ROLLBACK")
                return CacheCasResult(
                    status=CacheCasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                    lease_generation=lease_generation,
                    request_key=request_key,
                )
            if host is not None and next_allowed_at is not None:
                conn.execute(
                    "INSERT INTO host_cooldowns(host, next_allowed_at) VALUES (?, ?) "
                    "ON CONFLICT(host) DO UPDATE SET "
                    "next_allowed_at = excluded.next_allowed_at",
                    (host, float(next_allowed_at)),
                )
            self._event(
                "retry_scheduled",
                request_key,
                error_code=error_code,
                host=host,
                next_allowed_at=next_allowed_at,
                lease_generation=lease_generation,
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return CacheCasResult(
            status=CacheCasStatus.OK,
            lease_generation=lease_generation,
            request_key=request_key,
        )

    def put_parsed(
        self,
        *,
        request_key: str,
        body_sha256: str,
        parser_version: str,
        normalizer_version: str,
        schema_version: str,
        parsed_payload: bytes | str,
        now: float | None = None,
    ) -> str:
        """Store parsed artifact keyed by raw body + parser/normalizer/schema versions."""
        conn = self._require()
        ts = self._now(now)
        parsed_bytes = (
            parsed_payload.encode("utf-8") if isinstance(parsed_payload, str) else parsed_payload
        )
        parsed_sha = hashlib.sha256(parsed_bytes).hexdigest()
        parsed_key = compute_parsed_key(
            request_key=request_key,
            body_sha256=body_sha256,
            parser_version=parser_version,
            normalizer_version=normalizer_version,
            schema_version=schema_version,
        )
        conn.execute(
            "INSERT OR REPLACE INTO parsed_cache("
            "parsed_key, request_key, body_sha256, parser_version, normalizer_version, "
            "schema_version, parsed_sha256, parsed_zlib, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                parsed_key,
                request_key,
                body_sha256,
                parser_version,
                normalizer_version,
                schema_version,
                parsed_sha,
                zlib.compress(parsed_bytes, level=9),
                ts,
            ),
        )
        return parsed_key

    def get_parsed(self, parsed_key: str) -> bytes | None:
        conn = self._require()
        row = conn.execute(
            "SELECT parsed_zlib FROM parsed_cache WHERE parsed_key = ?",
            (parsed_key,),
        ).fetchone()
        if row is None:
            return None
        return zlib.decompress(bytes(row["parsed_zlib"]))

    def record_fetch_attempt(self) -> None:
        """Instrumentation: count a real network/fetch side-effect."""
        self.fetch_count += 1

    def list_events(self, event: str | None = None) -> list[dict[str, Any]]:
        conn = self._require()
        if event is None:
            rows = conn.execute(
                "SELECT * FROM fetch_events ORDER BY event_id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM fetch_events WHERE event = ? ORDER BY event_id",
                (event,),
            ).fetchall()
        return [dict(r) for r in rows]


def open_network_cache(path: Path, **kwargs: Any) -> NetworkCache:
    """Open a network cache under the network-worker sources.db guard."""
    with guard_network_worker():
        # Refuse accidental sources.db path and any open attempt.
        if path.name == "sources.db" or path.resolve().name == "sources.db":
            raise SourcesDbForbiddenError(
                f"network workers cannot open sources.db (refused path={path})"
            )
        cache = NetworkCache(path, **kwargs)
        cache.open()
        return cache
