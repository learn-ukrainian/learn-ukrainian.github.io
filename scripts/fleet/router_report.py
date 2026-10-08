"""Bounded-hour private export over existing immutable Fleet events (#10154).

No event store, migrations, mutable-state joins, provider calls or writes.
``read_hour`` issues an in-process receipt bound to the complete read; a JSON
copy is an audit record, never authority for ``aggregate_hour``. Private
watchers use ``export_hour`` (or the CLI's explicit private visibility).
"""

from __future__ import annotations

import argparse
import hmac
import json
import secrets
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.fleet.router_policy import (
    RouterPolicyError,
    digest,
    fingerprint,
    hour_bounds,
    public_decision,
    read_private_bytes,
    strict_json,
    timestamp,
    utc_time,
)

_READER_SEAL = object()
_READER_KEY = secrets.token_bytes(32)
_SOURCES = ("routing_reservation_decisions", "authority_job_events")
_METRICS = ("selected", "admitted", "executed_done", "delivered", "merged")


@dataclass(frozen=True)
class HourReaderReceipt:
    """Reader-issued evidence; callers cannot replace it with a bool/dict."""

    start: str
    end: str
    source_sha256: str
    events_sha256: str
    pages: int
    observed_at: str
    exhausted: bool
    code: str
    _seal: object = field(repr=False, compare=False, default=None)
    _attestation: str | None = field(repr=False, compare=False, default=None)

    def private_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "model-router-hour-reader.v1",
            "start": self.start, "end": self.end,
            "source_sha256": self.source_sha256, "events_sha256": self.events_sha256,
            "sources": list(_SOURCES), "pages": self.pages, "observed_at": self.observed_at,
            "exhausted": self.exhausted, "code": self.code,
            "coverage": "full_snapshot" if self.exhausted and self.code == "COMPLETE" else "unknown",
        }


@dataclass(frozen=True)
class HourReadResult:
    events: tuple[dict[str, Any], ...]
    receipt: HourReaderReceipt


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _normalize_event(row: sqlite3.Row, source: str) -> dict[str, Any]:
    """Use immutable evidence only, retaining its full private payload."""
    routing = source == _SOURCES[0]
    metadata = strict_json(row["evidence_json" if routing else "metadata_json"])
    if not isinstance(metadata, dict) or timestamp(row["created_at"]) is None:
        raise RouterPolicyError("READER_CORRUPT")
    raw_id = row["decision_id" if routing else "event_id"]
    subject = row["reservation_id" if routing else "job_id"]
    if not isinstance(raw_id, str) or not raw_id or not isinstance(subject, str) or not subject:
        raise RouterPolicyError("READER_CORRUPT")
    task_id = metadata.get("task_id", f"{source}:{subject}")
    nonce = metadata.get("run_nonce", subject if routing else str(row["fence_token"]))
    if not isinstance(task_id, str) or not task_id or not isinstance(nonce, str) or not nonce:
        raise RouterPolicyError("READER_CORRUPT")
    terminal = metadata.get("terminal_evidence")
    proof_data = terminal if isinstance(terminal, dict) else metadata
    event_type, state = row["event_type"], row["state"]
    if not isinstance(event_type, str) or not isinstance(state, str):
        raise RouterPolicyError("READER_CORRUPT")
    return {
        "event_id": f"{source}:{row['decision_id' if routing else 'event_id']}",
        "task_id": task_id, "run_nonce": nonce, "event_type": event_type,
        "state": state, "created_at": row["created_at"],
        # Routing settlement uses exactly the same current_iso for both the
        # terminal row and immutable event. Job events use a separate clock;
        # absent immutable finished_at is UNKNOWN, never the later job state.
        "finished_at": (row["created_at"] if routing and event_type == "settled"
                        else metadata.get("finished_at") if not routing and event_type == "finished" else None),
        "behavior_proof_receipt": proof_data.get("behavior_proof_record", proof_data.get("behavior_proof_receipt")),
        "forge_receipt": proof_data.get("forge_receipt"),
        "metadata": metadata,
    }


def read_hour(*, root: Path | None = None, start: Any, end: Any,
              page_size: int = 500, max_pages: int | None = None) -> HourReadResult:
    """Exhaust all pages in one authoritative read-only snapshot.

    Scan both complete event histories because metric timestamps may differ
    from event creation (e.g. a merge observation arrives in a later hour).
    A cap is permitted only as an explicitly incomplete, UNKNOWN read. No
    missing database/table is interpreted as an empty hour.
    """
    from scripts.control_plane.storage import StoreId, assert_component_supported
    from scripts.control_plane.storage import connect as cp_connect
    from scripts.fleet_comms.paths import default_plane_root

    first, last = hour_bounds(start, end)
    if type(page_size) is not int or not 1 <= page_size <= 10_000 or (
        max_pages is not None and (type(max_pages) is not int or max_pages < 1)
    ):
        raise RouterPolicyError("EXPORT_INVALID")
    events: list[dict[str, Any]] = []
    pages = 0
    code, exhausted = "COMPLETE", False
    connection = None
    observed = _utc_now()
    try:
        if last > observed:
            raise RouterPolicyError("READER_PARTIAL")
        path = (Path(root) if root is not None else default_plane_root()) / "comms.sqlite3"
        if not path.is_file() or any(part.is_symlink() for part in (path, *path.parents)):
            raise RouterPolicyError("READER_UNAVAILABLE")
        assert_component_supported(StoreId.FLEET_COMMS, "routing_reservations")
        connection = cp_connect(StoreId.FLEET_COMMS, path=path, read_only=True)
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")
        # Snapshot begins with this table read, then remains stable across pages.
        tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not set(_SOURCES) <= tables:
            raise RouterPolicyError("READER_UNAVAILABLE")
        for source in _SOURCES:
            cursor_id = "decision_id" if source == _SOURCES[0] else "event_id"
            previous = None
            while True:
                if max_pages is not None and pages >= max_pages:
                    raise RouterPolicyError("READER_PARTIAL")
                rows = connection.execute(
                    f"SELECT * FROM {source} WHERE (? IS NULL OR {cursor_id} > ?) ORDER BY {cursor_id} LIMIT ?",
                    (previous, previous, page_size),
                ).fetchall()
                pages += 1
                events.extend(_normalize_event(row, source) for row in rows)
                if len(rows) < page_size:
                    break
                previous = rows[-1][cursor_id]
        exhausted = True
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, RuntimeError) as exc:
        code = exc.code if isinstance(exc, RouterPolicyError) and exc.code.startswith("READER_") else "READER_CORRUPT"
    finally:
        if connection is not None:
            connection.close()
    try:
        events_sha = digest(events)
    except (TypeError, ValueError, RecursionError):
        # An invalid adapter/source cannot mint a complete receipt. Raw source
        # stays intact in Fleet; a failed export has no serializable event set.
        events, code, exhausted = [], "READER_CORRUPT", False
        events_sha = digest(events)
    receipt = HourReaderReceipt(
        timestamp(first), timestamp(last), digest({"sources": _SOURCES, "events_sha256": events_sha}),
        events_sha, pages, timestamp(observed), exhausted, code, _READER_SEAL,
    )
    receipt = replace(receipt, _attestation=_attest(receipt))
    return HourReadResult(tuple(events), receipt)


def _attest(receipt: HourReaderReceipt) -> str:
    return hmac.digest(_READER_KEY, digest(receipt.private_dict()).encode(), "sha256").hex()


def _proof_file(reference: Any) -> dict[str, Any]:
    if not isinstance(reference, dict) or not isinstance(reference.get("receipt_path"), str):
        raise RouterPolicyError("PROOF_MISSING")
    raw = read_private_bytes(reference["receipt_path"])
    import hashlib

    if reference.get("receipt_sha256") != "sha256:" + hashlib.sha256(raw).hexdigest():
        raise RouterPolicyError("PROOF_INVALID")
    value = strict_json(raw)
    if not isinstance(value, dict):
        raise RouterPolicyError("PROOF_INVALID")
    return value


def _delivery_proof(record: Any) -> tuple[str, str]:
    """Canonical lifecycle evidence timing + verified behavior receipt.

    Fleet metadata carries the existing lifecycle ``behavior_proof`` evidence
    record as ``behavior_proof_record``. Its recorded_at supplies the proof
    time; code-review-receipt.v1 itself has no timestamp. A bare reference,
    copied status or caller-provided delivery time cannot establish a count.
    """
    from scripts.orchestration.task_lifecycle import _behavior_proof_reference_error
    from scripts.orchestration.task_lifecycle import digest as lifecycle_digest

    if not isinstance(record, dict) or record.get("type") != "behavior_proof":
        raise RouterPolicyError("PROOF_MISSING")
    material = {key: value for key, value in record.items() if key != "id"}
    if record.get("id") != lifecycle_digest(material):
        raise RouterPolicyError("PROOF_INVALID")
    details = record.get("details")
    reference = details.get("behavior_proof_receipt") if isinstance(details, dict) else None
    _proof_file(reference)
    subject = record.get("subject")
    if not isinstance(subject, dict) or subject.get("commit") != reference.get("target_sha"):
        raise RouterPolicyError("PROOF_INVALID")
    if _behavior_proof_reference_error(record, head_sha=reference.get("target_sha")) is not None:
        raise RouterPolicyError("PROOF_INVALID")
    at = timestamp(record.get("recorded_at"))
    if at is None:
        raise RouterPolicyError("PROOF_INVALID")
    return at, reference["receipt_sha256"]


def _merge_proof(reference: Any) -> tuple[str, tuple[str, int, str]]:
    """Read a hashed canonical task-closeout forge observation, never a flag."""
    if not isinstance(reference, dict) or set(reference) != {"receipt_path", "receipt_sha256"}:
        raise RouterPolicyError("PROOF_INVALID")
    proof = _proof_file(reference)
    github = proof.get("github")
    if (proof.get("schema_version") != "task-closeout-observation.v1" or not isinstance(github, dict)
        or "error" not in github or github["error"] is not None):
        raise RouterPolicyError("PROOF_INVALID")
    pr = github.get("pr")
    if not isinstance(pr, dict) or pr.get("state") != "MERGED" or fingerprint(pr.get("merge_sha"), sha=True) is None:
        raise RouterPolicyError("PROOF_INVALID")
    at = timestamp(pr.get("merged_at"))
    observed = timestamp(proof.get("observed_at"))
    if observed is None or (at is not None and utc_time(observed) < utc_time(at)):
        raise RouterPolicyError("PROOF_INVALID")
    repo, number = github.get("repository"), pr.get("number")
    if at is None or not isinstance(repo, str) or not repo or type(number) is not int or number < 1:
        raise RouterPolicyError("PROOF_INVALID")
    return at, (repo, number, pr["merge_sha"])


def aggregate_read_hour(events: Iterable[Mapping[str, Any]], *, start: Any, end: Any,
                        receipt: Any) -> dict[str, Any]:
    first, last = hour_bounds(start, end)
    material = list(events)
    code = "COMPLETE"
    try:
        if (not isinstance(receipt, HourReaderReceipt) or receipt._seal is not _READER_SEAL
            or not isinstance(receipt._attestation, str) or not hmac.compare_digest(receipt._attestation, _attest(receipt))
            or receipt.start != timestamp(first) or receipt.end != timestamp(last) or receipt.events_sha256 != digest(material)):
            code = "READER_MISMATCH"
        elif not receipt.exhausted or receipt.code != "COMPLETE":
            code = receipt.code
    except (TypeError, ValueError, RecursionError):
        code = "READER_CORRUPT"
    counts: dict[str, set[Any]] = {metric: set() for metric in _METRICS}
    tasks: set[str] = set()
    hour_events: set[str] = set()
    seen: dict[str, str] = {}
    faults: dict[str, set[str]] = {metric: set() for metric in _METRICS}
    for event in material if code == "COMPLETE" else []:
        try:
            if not isinstance(event, Mapping):
                raise RouterPolicyError("READER_CORRUPT")
            event_id, task_id, nonce = (event[key] for key in ("event_id", "task_id", "run_nonce"))
            if not all(isinstance(value, str) and value for value in (event_id, task_id, nonce)):
                raise RouterPolicyError("READER_CORRUPT")
            event_digest = digest(event)
            if event_id in seen:
                if seen[event_id] != event_digest:
                    raise RouterPolicyError("READER_CORRUPT")
                continue
            seen[event_id] = event_digest
            created = utc_time(event["created_at"])
            if first <= created < last:
                hour_events.add(event_id)
                tasks.add(task_id)
            event_type, state = event["event_type"], event["state"]
            key = (task_id, nonce)
            for metric, types in (("selected", {"reserved", "selected"}), ("admitted", {"reserved", "admitted"})):
                if event_type in types and first <= created < last:
                    counts[metric].add(key)
            if event_type in {"settled", "finished"} and state in {"complete", "done"}:
                finished = None
                try:
                    finished = utc_time(event.get("finished_at"))
                    if first <= finished < last:
                        counts["executed_done"].add(key)
                        tasks.add(task_id)
                except RouterPolicyError:
                    faults["executed_done"].add("PROOF_MISSING")
                    faults["delivered"].add("PROOF_MISSING")
                    faults["merged"].add("PROOF_MISSING")
                # Completion never supplies delivery/merge. Missing canonical
                # references leave those metrics UNKNOWN, not a false zero.
                if finished is not None and first <= finished < last and not event.get("behavior_proof_receipt"):
                    faults["delivered"].add("PROOF_MISSING")
                if finished is not None and first <= finished < last and not event.get("forge_receipt"):
                    faults["merged"].add("PROOF_MISSING")
            for metric, reference_key, verifier in (
                ("delivered", "behavior_proof_receipt", _delivery_proof),
                ("merged", "forge_receipt", _merge_proof),
            ):
                reference = event.get(reference_key)
                if reference is not None or event_type == metric:
                    try:
                        at, proof_key = verifier(reference)
                        if first <= utc_time(at) < last:
                            counts[metric].add(key if metric == "delivered" else proof_key)
                            tasks.add(task_id)
                    except (RouterPolicyError, KeyError, TypeError, ValueError, OSError):
                        faults[metric].add("PROOF_INVALID" if reference is not None else "PROOF_MISSING")
        except (RouterPolicyError, KeyError, TypeError, ValueError, RecursionError):
            code = "READER_CORRUPT"
            break
    metrics = {
        name: {"status": "COMPLETE" if code == "COMPLETE" and not faults[name] else "UNKNOWN",
               "count": len(counts[name]) if code == "COMPLETE" and not faults[name] else None,
               "codes": sorted(faults[name] if code == "COMPLETE" else {code})}
        for name in _METRICS
    }
    report_complete = code == "COMPLETE" and all(item["status"] == "COMPLETE" for item in metrics.values())
    return {
        "schema_version": "model-router-hour.v1", "start": timestamp(first), "end": timestamp(last),
        "status": "COMPLETE" if report_complete else "UNKNOWN",
        "code": code if code != "COMPLETE" or report_complete else sorted(set().union(*faults.values()))[0],
        "denominator": {"events": len(hour_events) if code == "COMPLETE" else None,
                        "unique_tasks": len(tasks) if code == "COMPLETE" else None,
                        "identity_basis": "immutable_task_id_or_source_subject"},
        "metrics": metrics,
        "reader": receipt.private_dict() if isinstance(receipt, HourReaderReceipt) and receipt._seal is _READER_SEAL else None,
    }


def export_hour(*, root: Path | None = None, start: Any, end: Any,
                page_size: int = 500, max_pages: int | None = None, include_events: bool = False) -> dict[str, Any]:
    """Private watcher API. Raw private events are explicitly opt-in."""
    from scripts.fleet.router_policy import aggregate_hour

    read = read_hour(root=root, start=start, end=end, page_size=page_size, max_pages=max_pages)
    report = aggregate_hour(read.events, start=start, end=end, complete=read.receipt)
    if include_events:
        report["private_events"] = list(read.events)
    return report


class _SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise RouterPolicyError("EXPORT_INVALID")


def main(argv: list[str] | None = None) -> int:
    parser = _SafeParser(
        description="Export one UTC hour from existing Fleet durable events, read-only.\n"
                    "Use for private reporting; public mode emits only a closed status receipt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.fleet.router_report --start 2035-01-01T00:00:00Z --end 2035-01-01T01:00:00Z\n"
               "  .venv/bin/python -m scripts.fleet.router_report --start 2035-01-01T00:00:00Z --end 2035-01-01T01:00:00Z --visibility private\n"
               "Outputs: JSON on stdout; no files, database updates or provider calls.\n"
               "Exit codes: 0 complete; 2 UNKNOWN or invalid input.\nRelated: #10154; router_policy.aggregate_hour; Fleet Comms authority.",
    )
    parser.add_argument("--start", required=True, help="Inclusive UTC hour start, e.g. 2035-01-01T00:00:00Z.")
    parser.add_argument("--end", required=True, help="Exclusive UTC hour end, e.g. 2035-01-01T01:00:00Z.")
    parser.add_argument("--root", type=Path, help="Existing Fleet plane directory; default: configured authority root.")
    parser.add_argument("--page-size", type=int, default=500, help="Rows per page, 1..10000; default: 500.")
    parser.add_argument("--max-pages", type=int, help="Optional safety cap; default: exhaust all pages. Capped reads are UNKNOWN.")
    parser.add_argument("--visibility", choices=("public", "private"), default="public", help="Output boundary; default: public. Private includes hourly counts/reader receipt.")
    parser.add_argument("--include-events", action="store_true", help="Include full private events; requires --visibility private; default: off.")
    try:
        args = parser.parse_args(argv)
        if args.include_events and args.visibility != "private":
            raise RouterPolicyError("EXPORT_INVALID")
        report = export_hour(root=args.root, start=args.start, end=args.end,
                             page_size=args.page_size, max_pages=args.max_pages, include_events=args.include_events)
        complete = report["status"] == "COMPLETE"
        output = report if args.visibility == "private" else public_decision({
            "status": "complete" if complete else "unknown", "code": "HOUR_COMPLETE" if complete else report["code"],
            "snapshot_sha256": (report.get("reader") or {}).get("source_sha256"),
        })
    except (RouterPolicyError, OSError, ValueError, TypeError) as exc:
        complete = False
        output = public_decision({"status": "unknown", "code": exc.code if isinstance(exc, RouterPolicyError) else "EXPORT_INVALID"})
    print(json.dumps(output, sort_keys=True, allow_nan=False))
    return 0 if complete else 2


if __name__ == "__main__":
    # -m must use the same receipt class/seal as router_policy imports.
    from scripts.fleet.router_report import main as package_main

    raise SystemExit(package_main())
