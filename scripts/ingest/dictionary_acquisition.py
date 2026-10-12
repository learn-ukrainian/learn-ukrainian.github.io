"""Isolated, resumable staging jobs for explicitly bounded dictionary targets (#10003).

No live-store import. SQLite owns progress; JSON status is a replaceable projection.
The local transport preserves HTTP distinctions erased by the legacy fetch helpers.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.repo_root import project_interpreter
from scripts.lexicon.enrich_manifest import (
    _SLOVNYK_CACHE_SCHEMA_VERSION,
    _SLOVNYK_USER_AGENT,
    _parse_slovnyk_entry,
    _slovnyk_cache_path,
    _slovnyk_lookup_word,
    _valid_slovnyk_positive,
)
from scripts.wiki.slovnyk_me import SLOVNYK_ME_DICTS, resolve_dict_slug
from scripts.wiki.sum20_official import (
    DEFAULT_USER_AGENT,
    PARSER_VERSION,
    SUM20_SOURCE_ID,
    Sum20ParseError,
    official_url_for_wordid,
    parse_sum20_article,
)

SCHEMA = "dictionary-acquisition.v1"
SUCCESS = {"positive", "not_found", "reused"}
EXIT = {
    "complete": 0,
    "invalid": 2,
    "blocked": 3,
    "parse_error": 4,
    "exhausted": 5,
    "conflict": 6,
    "transient": 75,
    "running": 75,
}


class JobError(ValueError):
    """A path-free admission refusal suitable for logs."""


def packed(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    """Replace only after fsync; caller holds the corresponding persistent lock."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(packed(value) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextlib.contextmanager
def lock(path: Path, *, blocking: bool = False) -> Iterator[None]:
    """Never unlink lock files: flock admission is released by the OS on crash."""
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError as exc:
            raise JobError("conflicting_writer") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def dictionary_name(value: str) -> str:
    name = resolve_dict_slug(value)
    if name != SUM20_SOURCE_ID and name not in SLOVNYK_ME_DICTS:
        raise JobError("invalid_dictionary")
    return name


def make_spec(args: argparse.Namespace) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    """Bind raw input bytes, ordered unique targets, parser and request configuration."""
    name = dictionary_name(args.dictionary)
    if not all(math.isfinite(x) and x > 0 for x in (args.delay, args.timeout, args.backoff)):
        raise JobError("invalid_timing")
    if args.delay < 2 or not 1 <= args.max_attempts <= 10 or not 0 <= args.max_restarts <= 10:
        raise JobError("invalid_budget")
    spec = {
        "schema": SCHEMA,
        "dictionary": name,
        "delay": args.delay,
        "timeout": args.timeout,
        "backoff": args.backoff,
        "max_attempts": args.max_attempts,
        "max_restarts": args.max_restarts,
        "seed_identity": digest(str(args.seed_cache.resolve()).encode()) if args.seed_cache else None,
    }
    if name == SUM20_SOURCE_ID:
        if args.manifest or args.seed_cache or args.start_wordid is None or args.end_wordid is None:
            raise JobError("official_requires_explicit_range")
        if not 1 <= args.start_wordid <= args.end_wordid:
            raise JobError("invalid_range")
        targets = [(str(i), str(i)) for i in range(args.start_wordid, args.end_wordid + 1)]
        spec.update(start_wordid=args.start_wordid, end_wordid=args.end_wordid, parser_version=PARSER_VERSION)
        parser_path = Path(parse_sum20_article.__code__.co_filename)
    else:
        if not args.manifest or args.start_wordid is not None or args.end_wordid is not None:
            raise JobError("slovnyk_requires_manifest")
        raw = args.manifest.read_bytes()
        manifest = json.loads(raw)
        if not isinstance(manifest, dict) or not isinstance(manifest.get("entries"), list):
            raise JobError("invalid_manifest")
        targets = []
        seen = set()
        for entry in manifest["entries"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("lemma"), str) or not entry["lemma"].strip():
                raise JobError("invalid_manifest_lemma")
            lemma = entry["lemma"]
            if lemma not in seen:
                lookup = _slovnyk_lookup_word(lemma)
                if not lookup:
                    raise JobError("empty_lookup")
                targets.append((lemma, lookup))
                seen.add(lemma)
        if not targets:
            raise JobError("empty_manifest")
        spec.update(manifest_sha256=digest(raw), cache_schema=_SLOVNYK_CACHE_SCHEMA_VERSION)
        parser_path = Path(_parse_slovnyk_entry.__code__.co_filename)
    spec["parser_sha256"] = digest(parser_path.read_bytes())
    spec["transport_sha256"] = digest(Path(__file__).read_bytes())
    spec["targets_sha256"] = digest(packed(targets).encode())
    spec["denominator"] = len(targets)
    return spec, targets


def valid_slovnyk(row: Any, dictionary: str, lookup: str) -> bool:
    """Validate a positive retained article and its direct dictionary locator."""
    return _valid_slovnyk_positive(row, dictionary, lookup)


def seed_row(directory: Path | None, lemma: str, lookup: str, dictionary: str) -> dict[str, Any] | None:
    """Read only current positive snapshots; nulls never attest an HTTP miss."""
    if directory is None:
        return None
    try:
        raw = (directory / _slovnyk_cache_path(lemma).name).read_bytes()
        cache = json.loads(raw)
        if (
            not isinstance(cache, dict)
            or cache.get("schema_version") != _SLOVNYK_CACHE_SCHEMA_VERSION
            or cache.get("lookup_word") != lookup
            or cache.get("lemma") != lemma
            or not isinstance(cache.get("lookups"), dict)
        ):
            return None
        row = cache["lookups"].get(dictionary)
        if not valid_slovnyk(row, dictionary, lookup):
            return None
        timestamp = cache.get("fetched_at")
        if not isinstance(timestamp, str) or datetime.fromisoformat(timestamp).tzinfo is None:
            return None
        return {
            "article": row,
            "fetched_at": timestamp,
            "cache_sha256": digest(raw),
            "source_url": row["source_url"],
            "provenance": "legacy_positive",
            "http_status": None,
        }
    except (OSError, ValueError, TypeError):
        return None


def connect(directory: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(directory / "staging.sqlite3", timeout=1)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def initialize(
    conn: sqlite3.Connection, spec: dict[str, Any], targets: list[tuple[str, str]], seed: Path | None, now: float
) -> None:
    """One durable creation transaction, or refuse a changed input before requests."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS job (
            singleton INTEGER PRIMARY KEY CHECK(singleton=1), spec TEXT NOT NULL,
            fingerprint TEXT NOT NULL, state TEXT NOT NULL, reason TEXT NOT NULL,
            started REAL NOT NULL, restarts INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS results (
            position INTEGER PRIMARY KEY, target TEXT NOT NULL UNIQUE, lookup TEXT NOT NULL,
            status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
            next_attempt_at REAL NOT NULL DEFAULT 0, http_status INTEGER,
            reason TEXT NOT NULL DEFAULT '', payload TEXT);
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY, position INTEGER, time REAL NOT NULL,
            kind TEXT NOT NULL, http_status INTEGER);
    """)
    row = conn.execute("SELECT * FROM job").fetchone()
    fingerprint = digest(packed(spec).encode())
    if row is not None:
        if row["fingerprint"] != fingerprint or row["spec"] != packed(spec):
            raise JobError("frozen_input_mismatch")
        stored = [(r["target"], r["lookup"]) for r in conn.execute("SELECT * FROM results ORDER BY position")]
        if stored != targets:
            raise JobError("durable_targets_mismatch")
        return
    with conn:
        conn.execute(
            "INSERT INTO job(singleton,spec,fingerprint,state,reason,started) VALUES(1,?,?, 'running','',?)",
            (packed(spec), fingerprint, now),
        )
        for index, (target, lookup) in enumerate(targets):
            reused = seed_row(seed, target, lookup, spec["dictionary"])
            conn.execute(
                "INSERT INTO results(position,target,lookup,status,payload) VALUES(?,?,?,?,?)",
                (index, target, lookup, "reused" if reused else "pending", packed(reused) if reused else None),
            )


def no_progress_launches(conn: sqlite3.Connection) -> int:
    """Count durable launch reservations since the last resolved target or explicit resume."""
    return conn.execute(
        "SELECT COUNT(*) FROM events WHERE kind='supervisor_launch' AND id > "
        "COALESCE((SELECT MAX(id) FROM events WHERE kind IN ('positive','not_found','operator_resume')),0)"
    ).fetchone()[0]


def project_status(conn: sqlite3.Connection, directory: Path, now: float) -> dict[str, Any]:
    """Reconcile counts/checkpoint from durable result rows, never from old JSON."""
    job = conn.execute("SELECT * FROM job").fetchone()
    spec = json.loads(job["spec"])
    rows = conn.execute("SELECT * FROM results ORDER BY position").fetchall()
    counts = dict.fromkeys(("positive", "miss", "pending", "error", "reused"), 0)
    checkpoint = 0
    requests_count = 0
    for row in rows:
        key = {"not_found": "miss"}.get(row["status"], row["status"])
        counts[key if key in counts else "error"] += 1
        requests_count += row["attempts"]
        if row["position"] == checkpoint and row["status"] in SUCCESS:
            checkpoint += 1
    next_row = rows[checkpoint] if checkpoint < len(rows) else None
    elapsed = max(0, now - job["started"])
    resolved_network = counts["positive"] + counts["miss"]
    eta = None
    if resolved_network >= 2 and elapsed > 0 and job["state"] in {"running", "transient", "complete"}:
        eta = elapsed / resolved_network * (len(rows) - checkpoint)
    value = {
        "schema": SCHEMA,
        "dictionary": spec["dictionary"],
        "input_fingerprint": job["fingerprint"],
        "target_fingerprint": spec["targets_sha256"],
        "denominator": spec["denominator"],
        "coverage_scope": "bounded_wordid_range" if spec["dictionary"] == SUM20_SOURCE_ID else "frozen_manifest",
        "counts": counts,
        "checkpoint": checkpoint,
        "state": job["state"],
        "terminal_reason": job["reason"],
        "elapsed_seconds": elapsed,
        "eta_seconds": eta,
        "request_attempts": conn.execute("SELECT COUNT(*) FROM events WHERE kind='attempt'").fetchone()[0],
        "current_attempt_budget_used": requests_count,
        "attempt_accounting": "reserved_before_http_including_interrupted",
        "retry": {
            "attempts": next_row["attempts"] if next_row else 0,
            "max_attempts": spec["max_attempts"],
            "next_attempt_at": next_row["next_attempt_at"] if next_row else None,
            "supervisor_launches": job["restarts"],
            "supervisor_restarts": max(0, job["restarts"] - 1),
            "no_progress_launches": no_progress_launches(conn),
            "max_no_progress_launches": spec["max_restarts"] + 1,
            "max_restarts": spec["max_restarts"],
        },
        "updated_at": datetime.fromtimestamp(now, UTC).isoformat(),
    }
    if spec["dictionary"] == SUM20_SOURCE_ID:
        value["range"] = [spec["start_wordid"], spec["end_wordid"]]
        value["next_wordid"] = int(next_row["target"]) if next_row else None
    atomic_json(directory / "status.json", value)
    return value


def report(conn: sqlite3.Connection, directory: Path, now: float) -> dict[str, Any]:
    value = project_status(conn, directory, now)
    # Only closed codes and counters: no exception text, input paths, targets or response bodies.
    with (directory / "job.log").open("a", encoding="utf-8") as log:
        log.write(
            packed(
                {
                    k: value[k]
                    for k in (
                        "updated_at",
                        "state",
                        "terminal_reason",
                        "checkpoint",
                        "counts",
                        "retry",
                        "request_attempts",
                        "current_attempt_budget_used",
                    )
                }
            )
            + "\n"
        )
    return value


def stop(conn: sqlite3.Connection, state: str, reason: str) -> int:
    with conn:
        conn.execute("UPDATE job SET state=?, reason=?", (state, reason))
    return EXIT[state]


def refusal(root: Path, state: str, reason: str) -> int:
    """Journal path-free admission failures without touching another writer's job."""
    value = {"schema": SCHEMA, "state": state, "terminal_reason": reason, "updated_at": datetime.now(UTC).isoformat()}
    # A bad/unwritable destination cannot carry a receipt; stdout still reports it.
    try:
        root.mkdir(parents=True, exist_ok=True)
        with lock(root / "admission.lock", blocking=True):
            atomic_json(root / "refusal.json", value)
            with (root / "refusals.log").open("a", encoding="utf-8") as handle:
                handle.write(packed(value) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
    except (OSError, JobError):
        value["evidence_error"] = "refusal_storage_unavailable"
    print(packed(value))
    return EXIT[state]


def retry_after(headers: Any, now: float) -> float:
    """Honor delta seconds and HTTP dates without trusting or logging the header."""
    value = headers.get("Retry-After", "")
    try:
        seconds = float(value)
        return max(0, seconds) if math.isfinite(seconds) else 0
    except (ValueError, TypeError):
        try:
            return max(0, parsedate_to_datetime(value).timestamp() - now)
        except (ValueError, TypeError, OverflowError):
            return 0


def fetch_once(session: Any, spec: dict[str, Any], row: sqlite3.Row, now: float) -> tuple[str, int | None, Any, float]:
    """Exactly one GET, no redirects, retries, or challenge bypasses; existing parsers."""
    official = spec["dictionary"] == SUM20_SOURCE_ID
    url = (
        official_url_for_wordid(int(row["target"]))
        if official
        else f"https://slovnyk.me/dict/{spec['dictionary']}/{quote(row['lookup'], safe='')}"
    )
    try:
        response = session.get(
            url,
            timeout=spec["timeout"],
            allow_redirects=False,
            headers={
                "User-Agent": DEFAULT_USER_AGENT if official else _SLOVNYK_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
            **({"params": {"page": 0}} if official else {}),
        )
    except requests.RequestException:
        return "transient_error", None, None, 0
    code = response.status_code
    if code in {401, 403}:
        return "blocked", code, None, 0
    if code == 404:
        return "not_found", code, None, 0
    if code in {408, 425, 429} or 500 <= code <= 599:
        return "transient_error", code, None, retry_after(response.headers, now)
    if code != 200:
        return "blocked", code, None, 0
    try:
        if official:
            article = parse_sum20_article(response.text, int(row["target"]))
            payload = {
                "article": asdict(article),
                "parser_version": PARSER_VERSION,
                "content_sha256": article.content_sha256,
            }
        else:
            article = _parse_slovnyk_entry(
                response.text, lemma=row["target"], lookup_word=row["lookup"], slug=spec["dictionary"], url=url
            )
            if not valid_slovnyk(article, spec["dictionary"], row["lookup"]):
                return "parse_error", code, None, 0
            payload = {"article": article, "content_sha256": digest(article["text"].encode())}
    except (Sum20ParseError, ValueError, TypeError, RecursionError):
        return "parse_error", code, None, 0
    payload.update(
        source_url=url,
        fetched_at=datetime.fromtimestamp(now, UTC).isoformat(),
        http_status=code,
        provenance="observed_http",
    )
    return "positive", code, payload, 0


def acquire(
    conn: sqlite3.Connection,
    directory: Path,
    root: Path,
    *,
    session: Any,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
) -> int:
    """Run until resolved, terminal stop, or one transient result (exit 75)."""
    job = conn.execute("SELECT * FROM job").fetchone()
    if job["state"] not in {"running", "transient"}:
        report(conn, directory, clock())
        return EXIT[job["state"]]
    spec = json.loads(job["spec"])
    host = "sum20ua" if spec["dictionary"] == SUM20_SOURCE_ID else "slovnyk"
    while True:
        row = conn.execute(
            "SELECT * FROM results WHERE status NOT IN ('positive','not_found','reused') ORDER BY position LIMIT 1"
        ).fetchone()
        if row is None:
            code = stop(conn, "complete", "target_resolved")
            report(conn, directory, clock())
            return code
        if row["attempts"] >= spec["max_attempts"]:
            with conn:
                conn.execute(
                    "UPDATE results SET status='exhausted',reason='attempt_budget' WHERE position=?", (row["position"],)
                )
            code = stop(conn, "exhausted", "attempt_budget")
            report(conn, directory, clock())
            return code
        report(conn, directory, clock())
        with lock(root / f"{host}.lock", blocking=True):
            throttle = root / f"{host}.json"
            gate = json.loads(throttle.read_text()) if throttle.exists() else {"next_request_at": 0}
            deadline = max(gate["next_request_at"], row["next_attempt_at"])
            sleep(max(0, deadline - clock()))
            now = clock()
            # Reserve before GET, including a worst-case request timeout. A killed GET cannot
            # leave the next process sending a request immediately into the same host.
            atomic_json(throttle, {"next_request_at": now + spec["timeout"] + spec["delay"]})
            with conn:
                conn.execute("UPDATE job SET state='running',reason=''")
                conn.execute(
                    "UPDATE results SET status='transient_error',attempts=attempts+1,reason='request_in_flight',next_attempt_at=? WHERE position=?",
                    (now + spec["timeout"] + spec["backoff"] * 2 ** row["attempts"], row["position"]),
                )
                conn.execute("INSERT INTO events(position,time,kind) VALUES(?,?,'attempt')", (row["position"], now))
            report(conn, directory, now)
            status, http, payload, retry = fetch_once(session, spec, row, now)
            finished = clock()
            delay = max(spec["delay"], spec["backoff"] * 2 ** row["attempts"], retry)
            state = {"blocked": "blocked", "parse_error": "parse_error", "transient_error": "transient"}.get(
                status, "running"
            )
            reason = {
                "blocked": "access_or_http_stop",
                "parse_error": "unusable_article",
                "transient_error": "retryable_request",
            }.get(status, "")
            if status == "transient_error" and row["attempts"] + 1 >= spec["max_attempts"]:
                status, state, reason = "exhausted", "exhausted", "attempt_budget"
            with conn:
                conn.execute(
                    "UPDATE results SET status=?,http_status=?,payload=?,reason=?,next_attempt_at=? WHERE position=?",
                    (
                        status,
                        http,
                        packed(payload) if payload else None,
                        reason,
                        finished + delay if status in {"transient_error", "exhausted"} else 0,
                        row["position"],
                    ),
                )
                conn.execute("UPDATE job SET state=?,reason=?", (state, reason))
                conn.execute(
                    "INSERT INTO events(position,time,kind,http_status) VALUES(?,?,?,?)",
                    (row["position"], finished, status, http),
                )
            # Hold the host lock until outcome is durable, then permit the next host slot.
            atomic_json(throttle, {"next_request_at": finished + max(spec["delay"], retry)})
        report(conn, directory, clock())
        if state != "running":
            return EXIT[state]


def manual_resume(conn: sqlite3.Connection, now: float) -> None:
    """Explicit operator action; never forwarded by the unattended supervisor."""
    with conn:
        conn.execute(
            "UPDATE results SET status='pending',attempts=0,next_attempt_at=0,reason='',http_status=NULL,payload=NULL WHERE status NOT IN ('positive','not_found','reused')"
        )
        conn.execute("UPDATE job SET state='running',reason=''")
        conn.execute("INSERT INTO events(time,kind) VALUES(?,'operator_resume')", (now,))


def supervise(
    args: argparse.Namespace,
    *,
    launch: Callable[..., Any] = subprocess.run,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
) -> int:
    """Bounded child supervisor; both retry and crash budgets survive its own restart."""
    spec, targets = make_spec(args)
    root = args.root.resolve()
    directory = root / spec["dictionary"]
    directory.mkdir(parents=True, exist_ok=True)
    with lock(directory / "supervisor.lock"):
        while True:
            with lock(directory / "writer.lock"), contextlib.closing(connect(directory)) as conn:
                initialize(conn, spec, targets, args.seed_cache, clock())
                job = conn.execute("SELECT * FROM job").fetchone()
                report(conn, directory, clock())
                if job["state"] not in {"running", "transient"}:
                    return EXIT[job["state"]]
                if no_progress_launches(conn) >= spec["max_restarts"] + 1:
                    code = stop(conn, "exhausted", "supervisor_budget")
                    report(conn, directory, clock())
                    return code
                # Count launches before spawn: unexpected child/supervisor crashes cannot reset it.
                with conn:
                    conn.execute("UPDATE job SET restarts=restarts+1")
                    conn.execute("INSERT INTO events(time,kind) VALUES(?,'supervisor_launch')", (clock(),))
                report(conn, directory, clock())
            command = [
                str(project_interpreter()),
                "-m",
                "scripts.ingest.dictionary_acquisition",
                "run",
                "--root",
                str(root),
                "--dictionary",
                spec["dictionary"],
                "--delay",
                str(args.delay),
                "--timeout",
                str(args.timeout),
                "--backoff",
                str(args.backoff),
                "--max-attempts",
                str(args.max_attempts),
                "--max-restarts",
                str(args.max_restarts),
            ]
            if args.manifest:
                command += ["--manifest", str(args.manifest)]
            if args.seed_cache:
                command += ["--seed-cache", str(args.seed_cache)]
            if args.start_wordid is not None:
                command += ["--start-wordid", str(args.start_wordid), "--end-wordid", str(args.end_wordid)]
            result = launch(command, check=False)
            if result.returncode in {0, 2, 3, 4, 5, 6}:
                return result.returncode
            # A terminal durable state is checked above before another launch, even if a
            # killed child never delivered its terminal exit code. Never busy-loop.
            sleep(max(2, args.backoff))


class AcquisitionParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        """Reject malformed CLI input without reflecting paths or secret arguments."""
        self.print_usage(sys.stderr)
        self.exit(2, packed({"state": "invalid", "terminal_reason": "invalid_arguments"}) + "\n")


def parser() -> argparse.ArgumentParser:
    result = AcquisitionParser(
        description="Acquire one explicitly selected dictionary into isolated resumable staging.\n"
        "Use for frozen manifests or finite wordid ranges; never imports or publishes live data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ingest.dictionary_acquisition run --root batch_state/acquisition --dictionary vts --manifest manifest.json
  .venv/bin/python -m scripts.ingest.dictionary_acquisition supervise --root batch_state/acquisition --dictionary sum20_official --start-wordid 5 --end-wordid 12
  .venv/bin/python -m scripts.ingest.dictionary_acquisition status --root batch_state/acquisition --dictionary vts
Outputs: <root>/<dictionary>/{staging.sqlite3,status.json,job.log}; persistent locks and host throttle files.
Exit codes: 0 complete/status/resume; 2 invalid/mismatch; 3 blocked HTTP; 4 parse error; 5 exhausted;
            6 conflicting writer/supervisor; 75 transient (run only). No terminal state resumes implicitly.
Related: docs/runbooks/dictionary-acquisition.md; #10003 / #6321; build_slovnyk_mirror (foreground shared-cache tool).
""",
    )
    result.add_argument(
        "action",
        choices=("run", "supervise", "status", "resume"),
        help="run once, supervise bounded restarts, reconcile status, or explicitly reset stopped work",
    )
    result.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Shared local staging/throttle root, e.g. batch_state/acquisition (required)",
    )
    result.add_argument(
        "--dictionary", required=True, help="Exactly one catalogue slug (e.g. vts, newsum) or sum20_official; required"
    )
    result.add_argument(
        "--manifest", type=Path, help="Slovnyk JSON with entries[].lemma, e.g. manifest.json; default none"
    )
    result.add_argument("--start-wordid", type=int, help="Official inclusive first wordid, e.g. 5; default none")
    result.add_argument(
        "--end-wordid", type=int, help="Official inclusive last wordid, e.g. 12; default none; finite range only"
    )
    result.add_argument(
        "--seed-cache",
        type=Path,
        help="Read-only schema-current legacy cache directory; validated positives only; default none",
    )
    result.add_argument(
        "--delay",
        type=float,
        default=4,
        help="Minimum shared host spacing after every request, including retries; default 4 seconds, minimum 2",
    )
    result.add_argument("--timeout", type=float, default=30, help="HTTP timeout seconds; default 30, e.g. 60")
    result.add_argument(
        "--backoff",
        type=float,
        default=4,
        help="Base exponential transient backoff seconds; default 4, e.g. 10; Retry-After honored",
    )
    result.add_argument(
        "--max-attempts",
        type=int,
        default=4,
        help="Durable attempts per target, including interrupted requests; default 4, range 1..10",
    )
    result.add_argument(
        "--max-restarts",
        type=int,
        default=3,
        help="Durable restart cap without resolved-target progress; default 3 (four launches), range 0..10",
    )
    return result


def main(
    argv: list[str] | None = None,
    *,
    session_factory: Callable[..., Any] = requests.Session,
    clock: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
    launch: Callable[..., Any] = subprocess.run,
) -> int:
    args = parser().parse_args(argv)
    try:
        name = dictionary_name(args.dictionary)
        if args.action == "supervise":
            return supervise(args, launch=launch, sleep=sleep, clock=clock)
        root = args.root.resolve()
        directory = root / name
        if args.action == "status" and not (directory / "staging.sqlite3").is_file():
            raise JobError("job_not_found")
        if args.action == "resume" and not (directory / "staging.sqlite3").is_file():
            raise JobError("job_not_found")
        spec, targets = make_spec(args) if args.action != "status" else (None, None)
        directory.mkdir(parents=True, exist_ok=True)
        resume_guard = lock(directory / "supervisor.lock") if args.action == "resume" else contextlib.nullcontext()
        with resume_guard, lock(directory / "writer.lock"), contextlib.closing(connect(directory)) as conn:
            if spec is not None:
                initialize(conn, spec, targets, args.seed_cache, clock())
            if args.action == "status":
                print(packed(report(conn, directory, clock())))
                return 0
            if args.action == "resume":
                manual_resume(conn, clock())
                print(packed(report(conn, directory, clock())))
                return 0
            with session_factory() as session:
                # No environment proxy or implicit netrc credentials on this public transport.
                session.trust_env = False
                return acquire(conn, directory, root, session=session, clock=clock, sleep=sleep)
    except JobError as exc:
        return refusal(args.root, "conflict" if str(exc) == "conflicting_writer" else "invalid", str(exc))
    except (OSError, ValueError, TypeError, sqlite3.Error):
        # Deliberately omit exception strings: paths, requests and payloads may be private.
        return refusal(args.root, "invalid", "input_or_storage_error")


if __name__ == "__main__":
    raise SystemExit(main())
