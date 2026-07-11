"""ADR-011 P4 — deterministic, privacy-safe research-registry observability.

Turns silent registry rot into a visible signal. Powers
``GET /api/knowledge/monitor`` (see ``knowledge_router``), which is **ungated by
the discovery kill switch** — governance must not vanish when serving is disabled.

Two independent signals, both built offline from local files only (no GitHub,
network, ``sources.db``, or embeddings):

* **Lifecycle + adoption** — from the RAW registry and P1 per-record helpers, never
  ``registry.load_runtime_safe()`` (which returns ``None`` on ANY semantic error and
  would hide the very records rot makes invalid). Reports stale (hash-drift),
  orphaned, ownership-unverified, deferred, and superseded id lists; raw state
  counts; adoption rate over non-superseded records; and dead vs unverified adopted
  consumers.
* **Consumption** — from the central telemetry JSONL (``batch_state/telemetry/
  events/YYYY-MM-DD.jsonl``, the same P3 store; no new store). Bounded file/byte
  scan, fail-soft on malformed/unreadable lines, distinct ``(task_id, research_id)``
  pairs (never raw event volume), and surfaced-vs-consumed over a bounded window.

**Privacy contract (never returned):** task ids, run/session/source, role, track,
owned paths, title, summary, source url, prompt, digest body. Only registry ids
(public) and counts leave this module. Unknown research ids get *aggregate* counts
only — their id strings are never echoed.

Determinism: identical (registry, telemetry, cache, ``now``) → identical metrics.
Only ``generated_at``/``generated_ts`` carry wall-clock, by design.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from scripts.audit import atlas_intake_registry
from scripts.audit import check_research_registry as crr
from scripts.orchestration import issue_stream_audit as isa
from scripts.research import consumption
from scripts.research import registry as reg

logger = logging.getLogger("research.observability")

# Consumer kinds P1 resolves deterministically OFFLINE (file/symbol/decision), PLUS
# ``corpus`` — the declared Atlas intake source-family registry is itself a static,
# offline, always-available table (ADR-011 P4/codex-gemini review), so it needs no
# injected live resolver and no cache freshness check, unlike ``issue``.
_OFFLINE_CONSUMER_KINDS = frozenset({"path", "prompt", "rubric", "test", "decision", "corpus"})

# Schema-valid registry id shape (schemas/research_registry.schema.json $defs.slug).
# The monitor is public: a raw record whose ``id`` does not match this shape (or
# is missing/non-string/absurdly long) is never echoed anywhere in the payload —
# it is counted as an anonymous invalid record instead (ADR-011 P4/codex-gemini
# review: secret-like or malformed raw ids must never leak into a public report).
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_RECORD_ID_LEN = 128

# Telemetry scan bounds (ADR-011 P4: "Bound total scanned bytes/files").
MAX_SCAN_BYTES = 64 * 1024 * 1024  # 64 MiB across the whole window
GRACE_SECONDS = 3600  # a surfaced pair younger than this with no consumption is pending

# Adoption ownership freshness: reuse the auditor's default cache max-age.
OWNERSHIP_CACHE_MAX_AGE_S = 3600

WINDOW_MIN_DAYS = 1
WINDOW_MAX_DAYS = 365


# --------------------------------------------------------------------------- #
# Registry lifecycle + adoption (raw records + P1 helpers, never load_runtime)
# --------------------------------------------------------------------------- #
def _valid_record_id(value: object) -> bool:
    """Schema-valid slug shape, bounded length. See ``_SLUG_RE`` above."""
    return (
        isinstance(value, str)
        and 0 < len(value) <= MAX_RECORD_ID_LEN
        and bool(_SLUG_RE.match(value))
    )


def _load_raw_records(root: Path) -> tuple[list[dict[str, Any]] | None, str, int]:
    """Return (records, status, invalid_id_count). ``status`` ∈
    ok/missing/unreadable/invalid.

    Reads the raw YAML directly so semantic-invalid records stay *visible* — the
    runtime loader would collapse the whole registry to ``None`` on any P1 error.
    Structural/per-record id validity is enforced HERE, before any lifecycle or
    adoption classification: a non-dict entry or a record whose ``id`` is
    missing, non-string, oversized, or not a schema-valid slug (secret-like
    strings included) is dropped and folded into ``invalid_id_count`` — its raw
    value is never returned, so it can never be echoed by a public report.
    """
    path = root / "docs" / "references" / "research-registry.yaml"
    if not path.exists():
        return None, "missing", 0
    try:
        _raw, data = crr.load_registry(path)
    except (OSError, ValueError, yaml.YAMLError, RecursionError):
        return None, "unreadable", 0
    records = data.get("records")
    if not isinstance(records, list):
        return None, "invalid", 0
    valid: list[dict[str, Any]] = []
    invalid_count = 0
    for r in records:
        if isinstance(r, dict) and _valid_record_id(r.get("id")):
            valid.append(r)
        else:
            invalid_count += 1
    return valid, "ok", invalid_count


def _consumer_status(
    record: dict[str, Any],
    root: Path,
    decision_ids: set[str],
    issue_resolver: Callable[[str], bool] | None,
) -> str:
    """Classify an adopted record's typed consumer: alive/dead/unverified/none.

    ``path``/``prompt``/``rubric``/``test``/``decision``/``corpus`` all resolve
    OFFLINE and deterministically (the last via the real Atlas intake source-
    family registry — no cache needed). ``issue`` needs a FRESH membership cache
    (``issue_resolver``, distinct from the ownership ``membership_resolver`` —
    record ownership and issue-consumer resolution are validated independently):
    missing/stale cache ⇒ ``unverified`` (never falsely ``dead``); a fresh cache
    proves ``alive`` (open + uniquely owned) or ``dead`` (closed/orphan/ambiguous).
    """
    consumer = record.get("consumer")
    if not isinstance(consumer, dict) or not consumer.get("kind"):
        return "none"
    kind = consumer["kind"]
    if kind in _OFFLINE_CONSUMER_KINDS:
        try:
            errs = crr.validate_consumer(
                record,
                project_root=root,
                decision_ids=decision_ids,
                corpus_resolver=atlas_intake_registry.is_registered_source_family,
            )
        except Exception:  # defensive: a malformed ref must not 500 the monitor
            return "dead"
        return "dead" if errs else "alive"
    if kind == "issue":
        if issue_resolver is None:
            return "unverified"  # no fresh cache — cannot prove OR disprove
        try:
            errs = crr.validate_consumer(
                record, project_root=root, decision_ids=decision_ids,
                issue_resolver=issue_resolver,
            )
        except Exception:
            return "dead"
        return "dead" if errs else "alive"
    return "dead"  # unknown kind — cannot resolve


def _lifecycle_and_adoption(root: Path, max_age_s: int) -> dict[str, Any]:
    records, status, invalid_ids = _load_raw_records(root)
    if records is None:
        return {
            "lifecycle": {
                "status": status,
                "eligible_total": 0,
                "counts": {},
                "stale": [],
                "orphaned": [],
                "ownership_unverified": [],
                "deferred": [],
                "superseded": [],
                "invalid_provenance": [],
                "invalid_ids": 0,
                "ownership_cache": "missing",
            },
            "adoption": {"adopted": 0, "effective_adopted": 0, "eligible_total": 0, "rate": None},
            "dead_consumers": {"dead": [], "unverified": [], "count": 0},
            "known_ids": set(),
        }

    try:
        streams = crr.load_streams(root / "scripts" / "config" / "issue_streams.yaml")
    except (OSError, ValueError, yaml.YAMLError):
        streams = {}
    try:
        decision_ids = crr.load_decision_ids(root / "docs" / "decisions" / "decisions.yaml")
    except (OSError, ValueError, yaml.YAMLError):
        decision_ids = set()

    # Record ownership (proposed) and issue-consumer resolution (adopted) are
    # validated with DISTINCT resolvers built from the same fresh cache — they
    # prove different things and must not be conflated (ADR-011 P4 review).
    membership_report = isa.read_membership_index(max_age_s)
    ownership_cache = "fresh" if membership_report is not None else "missing"
    resolver = isa.make_membership_resolver(membership_report) if membership_report else None
    issue_consumer_resolver = (
        isa.make_issue_resolver(membership_report) if membership_report else None
    )

    counts: Counter[str] = Counter()
    stale: list[str] = []
    orphaned: list[str] = []
    ownership_unverified: list[str] = []
    deferred: list[str] = []
    superseded: list[str] = []
    invalid_provenance: list[str] = []
    dead: list[str] = []
    unverified_consumers: list[str] = []
    adopted = 0
    effective_adopted = 0
    known_ids: set[str] = set()

    for rec in records:
        rid = rec["id"]
        known_ids.add(rid)
        state = rec.get("state")

        # Broken/missing/unsafe provenance is semantic-invalid REGARDLESS of the
        # claimed lifecycle state: it must never be misreported as merely
        # "current" (not stale), must never count toward adopted/effective
        # adoption, and must be visible as invalid — not silently folded into
        # whatever state the record happens to claim (ADR-011 P4 review).
        try:
            provenance_errs = crr.validate_provenance(rec, root)
        except Exception:
            provenance_errs = [f"{rid}: provenance check raised"]
        if provenance_errs:
            counts["invalid"] += 1
            invalid_provenance.append(rid)
            continue

        # Hash drift ("stale") — only meaningful now that provenance is sound.
        drifted = False
        try:
            drifted = rec.get("content_hash") != crr.expected_content_hash(rec, root)
        except Exception:
            drifted = False
        if drifted:
            stale.append(rid)

        if state in {"proposed", "adopted", "deferred", "superseded"}:
            counts[state] += 1
        else:
            counts["invalid"] += 1

        if state == "deferred":
            deferred.append(rid)
        elif state == "superseded":
            superseded.append(rid)
        elif state == "proposed":
            _classify_ownership(rec, streams, resolver, orphaned, ownership_unverified)
        elif state == "adopted":
            adopted += 1
            cstatus = _consumer_status(rec, root, decision_ids, issue_consumer_resolver)
            if cstatus == "unverified":
                unverified_consumers.append(rid)
            elif cstatus in {"dead", "none"}:
                dead.append(rid)
            elif cstatus == "alive" and not drifted:
                effective_adopted += 1

    total = len(records)
    eligible_total = total - counts.get("superseded", 0)
    rate = round(adopted / eligible_total, 4) if eligible_total else None

    return {
        "lifecycle": {
            "status": "ok" if records else "empty",
            "eligible_total": eligible_total,
            "counts": {
                "proposed": counts.get("proposed", 0),
                "adopted": counts.get("adopted", 0),
                "deferred": counts.get("deferred", 0),
                "superseded": counts.get("superseded", 0),
                "invalid": counts.get("invalid", 0),
                "total": total,
            },
            "stale": sorted(stale),
            "orphaned": sorted(orphaned),
            "ownership_unverified": sorted(ownership_unverified),
            "deferred": sorted(deferred),
            "superseded": sorted(superseded),
            "invalid_provenance": sorted(invalid_provenance),
            "invalid_ids": invalid_ids,
            "ownership_cache": ownership_cache,
        },
        "adoption": {
            "adopted": adopted,
            "effective_adopted": effective_adopted,
            "eligible_total": eligible_total,
            "rate": rate,
        },
        "dead_consumers": {
            "dead": sorted(dead),
            "unverified": sorted(unverified_consumers),
            "count": len(dead),
        },
        "known_ids": known_ids,
    }


def _classify_ownership(
    record: dict[str, Any],
    streams: dict[str, list[int]],
    resolver: isa.MembershipResolver | None,
    orphaned: list[str],
    ownership_unverified: list[str],
) -> None:
    """Split a proposed record into orphaned (structurally un-owned) vs
    ownership_unverified (plausible owner not confirmable offline).

    A missing/stale cache never falsely orphans a record that *claims* a valid
    stream epic — it lands in ownership_unverified instead (ADR-011 P4).
    """
    rid = record["id"]
    own = record.get("ownership")
    if not isinstance(own, dict) or "stream" not in own or "issue" not in own:
        orphaned.append(rid)
        return
    try:
        structural_errs = crr.validate_ownership(record, streams, None)
    except Exception:
        orphaned.append(rid)
        return
    if structural_errs:  # stream not a declared epic / duplicate epic
        orphaned.append(rid)
        return
    if resolver is None or not resolver(own["issue"], own["stream"]):
        ownership_unverified.append(rid)


# --------------------------------------------------------------------------- #
# Consumption (bounded telemetry JSONL scan; fail-soft; distinct pairs)
# --------------------------------------------------------------------------- #
def _window_dates(now: datetime, window_days: int) -> list[str]:
    """Deterministic YYYY-MM-DD file stems from ``now`` back ``window_days`` days
    (inclusive). Bounds the file count to ``window_days + 1``."""
    start_date = (now - timedelta(days=window_days)).date()
    days = (now.date() - start_date).days
    return [(start_date + timedelta(days=i)).isoformat() for i in range(days + 1)]


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class _Accumulator:
    """Mutable scan state for one telemetry pass."""

    def __init__(self) -> None:
        self.surfaced_first: dict[tuple[str, str], datetime] = {}
        self.consumed_max: dict[tuple[str, str], datetime] = {}
        self.surfaced_events: Counter[str] = Counter()  # raw events by research_id
        self.consumed_events: Counter[str] = Counter()
        self.malformed_lines = 0


# Contract bounds for P3 event rows (ADR-011 P4 review, item 10): a row that
# claims a P3 event type but violates its field contract is MALFORMED, not
# silently dropped — it must be counted so undercounting a real data-quality
# problem never looks identical to "just noise from another event type".
# Task-id length/shape is validated via consumption._looks_like_task_id below.
MAX_RESEARCH_ID_LEN = 128


def _valid_event_contract(evt: dict[str, Any], event_type: str) -> bool:
    """Structural + field-level validation of one P3 event row, BEFORE it is
    allowed to contribute to any aggregate. Checks: bounded, well-shaped
    ``task_id``/``research_id``; the surface matches the event type (a
    surfaced event must not carry the consumption-reserved ``"record"``
    surface, and a consumed event must carry exactly that); and a consumed
    event's ``status`` is one of the two values the P3 emitter ever writes
    (200/304) — anything else cannot have come from a real consumption call.
    """
    task_id = evt.get("task_id")
    research_id = evt.get("research_id")
    surface = evt.get("surface")
    if not isinstance(task_id, str) or not consumption._looks_like_task_id(task_id):
        return False
    if not isinstance(research_id, str) or not (0 < len(research_id) <= MAX_RESEARCH_ID_LEN):
        return False
    if event_type == consumption.SURFACED_EVENT:
        if not isinstance(surface, str) or not surface or surface == consumption._CONSUMED_SURFACE:
            return False
    else:  # CONSUMED_EVENT
        if surface != consumption._CONSUMED_SURFACE:
            return False
        status = evt.get("status")
        if isinstance(status, bool) or status not in (200, 304):
            return False
    return True


def _ingest_line(line: str, now: datetime, start: datetime, acc: _Accumulator) -> None:
    """Fold one JSONL line into ``acc``. Malformed/non-dict lines, and P3 rows
    that violate the event contract (bad surface/status/ids/timestamp), bump the
    safe malformed counter and never affect any metric. Only a row that is BOTH a
    recognized P3 event type AND contract-valid can contribute — an irrelevant
    (non-P3) event type is not malformed, just filtered. Never logs line content.
    """
    try:
        evt = json.loads(line)
    except ValueError:
        acc.malformed_lines += 1
        return
    if not isinstance(evt, dict):
        acc.malformed_lines += 1
        return
    event_type = evt.get("event_type")
    if event_type not in (consumption.SURFACED_EVENT, consumption.CONSUMED_EVENT):
        return  # not a P3 research event — irrelevant row, not malformed
    if not _valid_event_contract(evt, event_type):
        acc.malformed_lines += 1
        return
    ts = _parse_ts(evt.get("ts"))
    if ts is None:
        acc.malformed_lines += 1  # required timestamp missing/unparsable
        return
    if ts < start or ts > now:  # valid but out-of-window/future — filtered, not malformed
        return
    task_id = evt["task_id"]
    research_id = evt["research_id"]
    pair = (task_id, research_id)
    if event_type == consumption.SURFACED_EVENT:
        acc.surfaced_events[research_id] += 1
        prior = acc.surfaced_first.get(pair)
        if prior is None or ts < prior:
            acc.surfaced_first[pair] = ts
    else:  # research_record_consumed
        acc.consumed_events[research_id] += 1
        prior = acc.consumed_max.get(pair)
        if prior is None or ts > prior:
            acc.consumed_max[pair] = ts


# A single JSONL "line" is bounded so a pathological multi-GB no-newline record
# is never buffered in full (ADR-011 P4 review, item 9). ``str.readline(size)``
# reads AT MOST ``size`` characters even with no newline in sight — that bound,
# not the OS read-buffer size, is what protects memory here.
MAX_LINE_CHARS = 1 * 1024 * 1024  # 1 MiB per JSONL line


class _ByteBudget:
    """Mutable byte counter shared across every file and every physical read in
    one telemetry scan (ADR-011 P4 review, item 2). ``MAX_SCAN_BYTES`` must bound
    TOTAL physical bytes read — including bytes discarded while draining an
    oversized line — not just the bytes of lines that made it into an event.
    Without this, a pathological multi-GB no-newline file stays memory-bounded
    (``str.readline(size)``) but can still be read start-to-finish while
    ``bytes_scanned`` stays near zero, defeating the whole-scan cap."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.consumed = 0

    def take(self, n: int) -> bool:
        """Charge ``n`` freshly-read bytes against the budget. Returns False
        (charging nothing) if this read would exceed the remaining budget — the
        caller must stop reading immediately, without consuming any further
        bytes from the file."""
        if self.consumed + n > self.limit:
            return False
        self.consumed += n
        return True


def _iter_bounded_lines(path: Path, budget: _ByteBudget, max_line_chars: int = MAX_LINE_CHARS):
    """Yield ``(text, oversized, capped)`` per physical line of ``path``, text mode.

    A physical line whose CONTENT (excluding its own trailing newline) exceeds
    ``max_line_chars`` is reported oversized with ``text=None`` — its content is
    never returned or buffered beyond the cap — and the reader drains forward in
    further ``max_line_chars``-bounded reads until it resynchronizes on the next
    newline (or EOF), so a single giant record cannot desynchronize every
    subsequent line in the file. The oversized check compares CONTENT length,
    not ``readline()``'s raw return length: a line whose content is exactly
    ``max_line_chars`` chars long, plus its own trailing newline, fits in one
    ``readline`` call and must never be treated as needing a drain (ADR-011 P4
    review, item 3) — ``readline`` never returns more than ``max_line_chars + 1``
    chars, so that exact case is the only way to hit that length AND end in
    ``"\\n"``.

    Every physical read — including the discarded drain reads for an oversized
    line — is charged against ``budget`` before being kept (item 2). Once the
    shared, scan-wide byte cap is exhausted, the generator yields one final
    ``(None, <oversized-so-far>, True)`` marker and stops: a pathological
    multi-GB no-newline file can never be drained past the remaining budget,
    keeping both memory AND total bytes read bounded.

    Raises ``OSError``/``UnicodeDecodeError`` to the caller exactly as a plain
    ``open().read()`` would (unreadable files stay the caller's concern,
    unchanged from before this helper existed).
    """
    with path.open("r", encoding="utf-8") as handle:
        while True:
            chunk = handle.readline(max_line_chars + 1)
            if chunk == "":
                return  # EOF
            if not budget.take(len(chunk.encode("utf-8"))):
                yield None, False, True
                return
            oversized = len(chunk) == max_line_chars + 1 and not chunk.endswith("\n")
            if not oversized:
                yield (chunk[:-1] if chunk.endswith("\n") else chunk), False, False
                continue
            while True:
                more = handle.readline(max_line_chars + 1)
                if more == "":
                    break
                if not budget.take(len(more.encode("utf-8"))):
                    yield None, True, True
                    return
                if more.endswith("\n"):
                    break
            yield None, True, False


def _scan_telemetry(
    root: Path, window_days: int, now: datetime, known_ids: set[str]
) -> dict[str, Any]:
    events_dir = root / "batch_state" / "telemetry" / "events"
    start = now - timedelta(days=window_days)
    acc = _Accumulator()
    budget = _ByteBudget(MAX_SCAN_BYTES)

    files_in_window = 0
    files_scanned = 0
    files_skipped = 0
    unreadable_files = 0
    oversized_lines = 0
    partial = False
    capped = False
    cap_reason: str | None = None

    # Newest-first (ADR-011 P4 review, item 8): once the byte cap trips, recent
    # activity has already been captured and only older, less-actionable days
    # are the ones dropped — the reverse of scanning oldest-first, where a cap
    # would silently hide today's activity behind ancient history.
    for stem in reversed(_window_dates(now, window_days)):
        path = events_dir / f"{stem}.jsonl"
        if not path.exists():
            continue
        files_in_window += 1
        if capped:
            files_skipped += 1
            continue
        try:
            for text, oversized, hit_cap in _iter_bounded_lines(path, budget, MAX_LINE_CHARS):
                if hit_cap:
                    if oversized:
                        acc.malformed_lines += 1
                        oversized_lines += 1
                    partial = True
                    capped = True
                    cap_reason = cap_reason or "byte_cap"
                    break
                if oversized:
                    acc.malformed_lines += 1
                    oversized_lines += 1
                    partial = True
                    cap_reason = cap_reason or "oversized_line"
                    continue
                stripped = text.strip()
                if stripped:
                    _ingest_line(stripped, now, start, acc)
            files_scanned += 1
        except (OSError, UnicodeDecodeError) as exc:
            unreadable_files += 1
            partial = True
            cap_reason = cap_reason or "unreadable_file"
            logger.warning(
                "research observability: unreadable telemetry file %s (%s)",
                path.name,
                type(exc).__name__,
            )
            continue

    return _finalize_consumption(
        acc=acc,
        now=now,
        known_ids=known_ids,
        window_days=window_days,
        files_in_window=files_in_window,
        files_scanned=files_scanned,
        files_skipped=files_skipped,
        unreadable_files=unreadable_files,
        oversized_lines=oversized_lines,
        bytes_scanned=budget.consumed,
        partial=partial,
        cap_reason=cap_reason,
    )


def _pair_verdict(pair: tuple[str, str], acc: _Accumulator, now: datetime) -> str:
    """consumed / never (surfaced_never_consumed) / pending for a surfaced pair."""
    first = acc.surfaced_first[pair]
    consumed = acc.consumed_max.get(pair)
    if consumed is not None and consumed >= first:
        return "consumed"
    if (now - first).total_seconds() >= GRACE_SECONDS:
        return "never"
    return "pending"


def _blank_record_agg() -> dict[str, int]:
    return {
        "surfaced_events": 0,
        "consumed_events": 0,
        "surfaced_pairs": 0,
        "consumed_pairs": 0,
        "surfaced_never_consumed": 0,
        "surfaced_never_consumed_observed": 0,
        "pending": 0,
    }


def _blank_unknown_agg() -> dict[str, int]:
    """``_blank_record_agg`` plus the unknown-bucket-only ``distinct_research_ids``
    field. Every construction site (finalize + the degraded-fallback payload)
    must use this so the response schema never drops the field on either path."""
    agg = _blank_record_agg()
    agg["distinct_research_ids"] = 0
    return agg


def _finalize_consumption(
    *,
    acc: _Accumulator,
    now: datetime,
    known_ids: set[str],
    window_days: int,
    files_in_window: int,
    files_scanned: int,
    files_skipped: int,
    unreadable_files: int,
    oversized_lines: int,
    bytes_scanned: int,
    partial: bool,
    cap_reason: str | None,
) -> dict[str, Any]:
    consumed_pairs_set = set(acc.consumed_max)
    all_pairs = set(acc.surfaced_first) | consumed_pairs_set

    # Per-research aggregates. Known ids get their own bucket; every unknown id is
    # folded into a single aggregate — its string is never echoed (privacy).
    per_record: dict[str, dict[str, int]] = {rid: _blank_record_agg() for rid in known_ids}
    unknown = _blank_unknown_agg()
    unknown_ids: set[str] = set()

    def _bucket(rid: str) -> dict[str, int]:
        if rid in per_record:
            return per_record[rid]
        unknown_ids.add(rid)
        return unknown

    for rid, count in acc.surfaced_events.items():
        _bucket(rid)["surfaced_events"] += count
    for rid, count in acc.consumed_events.items():
        _bucket(rid)["consumed_events"] += count

    surfaced_never = 0
    pending = 0
    for pair in acc.surfaced_first:
        rid = pair[1]
        bucket = _bucket(rid)
        bucket["surfaced_pairs"] += 1
        verdict = _pair_verdict(pair, acc, now)
        if verdict == "never":
            surfaced_never += 1
            bucket["surfaced_never_consumed"] += 1
            bucket["surfaced_never_consumed_observed"] += 1
        elif verdict == "pending":
            pending += 1
            bucket["pending"] += 1
    for pair in consumed_pairs_set:
        _bucket(pair[1])["consumed_pairs"] += 1

    unknown["distinct_research_ids"] = len(unknown_ids)

    # Drop untouched known buckets so per_record stays a signal, not registry-sized.
    per_record = {
        rid: agg for rid, agg in per_record.items()
        if any(agg[k] for k in agg)
    }

    # ``surfaced_never_consumed`` is the SAME definitive-negative claim at the
    # per-record/unknown-bucket level as it is in the top-level aggregate below —
    # a hidden consuming event for exactly this record could be sitting in the
    # unreadable file, the byte-capped tail, or a discarded oversized line, so
    # asserting a per-record "never" under partial coverage would be just as
    # dishonest as asserting it in aggregate. Null it in every bucket; the
    # observed lower bound stays a number either way (ADR-011 P4 review).
    if partial:
        for agg in per_record.values():
            agg["surfaced_never_consumed"] = None
        unknown["surfaced_never_consumed"] = None

    status = "partial" if partial else ("empty" if not all_pairs and not files_scanned else "ok")
    return {
        "status": status,
        "window_days": window_days,
        "files_in_window": files_in_window,
        "files_scanned": files_scanned,
        "files_skipped": files_skipped,
        "unreadable_files": unreadable_files,
        "oversized_lines": oversized_lines,
        "malformed_lines": acc.malformed_lines,
        "bytes_scanned": bytes_scanned,
        "partial": partial,
        "cap_reason": cap_reason,
        # Positive/raw counts are always LOWER BOUNDS over whatever was actually
        # scanned — safe to report even under partial coverage, since missing
        # data can only under-count them, never manufacture a false positive.
        "surfaced_events": sum(acc.surfaced_events.values()),
        "consumed_events": sum(acc.consumed_events.values()),
        "surfaced_pairs": len(acc.surfaced_first),
        "consumed_pairs": len(consumed_pairs_set),
        "distinct_pairs": len(all_pairs),
        # ``surfaced_never_consumed`` is a DEFINITIVE NEGATIVE claim ("this pair
        # was surfaced and genuinely never consumed") — under partial coverage
        # (byte cap / unreadable file / oversized line) a consuming event could
        # exist outside what was actually scanned, so asserting it would be
        # dishonest. Report null + the lower-bound observed count instead
        # (ADR-011 P4 review, item 8).
        "surfaced_never_consumed": None if partial else surfaced_never,
        "surfaced_never_consumed_observed": surfaced_never,
        "pending": pending,
        "per_record": {rid: per_record[rid] for rid in sorted(per_record)},
        "unknown_research_ids": unknown,
    }


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def build_monitor(
    *,
    window_days: int = 30,
    root: Path | None = None,
    now: datetime | None = None,
    ownership_max_age_s: int = OWNERSHIP_CACHE_MAX_AGE_S,
) -> dict[str, Any]:
    """Build the full deterministic monitor payload. Never raises — every failure
    mode degrades to a safe, bounded section (the endpoint must never 500)."""
    window_days = max(WINDOW_MIN_DAYS, min(WINDOW_MAX_DAYS, int(window_days)))
    root = root if root is not None else reg._live_repo_root()
    now = now if now is not None else datetime.now(UTC)

    try:
        discovery_enabled = reg.is_enabled(root=root)
    except Exception:
        discovery_enabled = False

    try:
        registry_view = _lifecycle_and_adoption(root, ownership_max_age_s)
    except Exception as exc:
        logger.warning("research observability: lifecycle build failed (%s)", type(exc).__name__)
        registry_view = {
            "lifecycle": {"status": "error", "eligible_total": 0, "counts": {}, "stale": [],
                          "orphaned": [], "ownership_unverified": [], "deferred": [],
                          "superseded": [], "invalid_provenance": [], "invalid_ids": 0,
                          "ownership_cache": "missing"},
            "adoption": {"adopted": 0, "effective_adopted": 0, "eligible_total": 0, "rate": None},
            "dead_consumers": {"dead": [], "unverified": [], "count": 0},
            "known_ids": set(),
        }

    known_ids = registry_view.pop("known_ids", set())
    try:
        consumption_view = _scan_telemetry(root, window_days, now, known_ids)
    except Exception as exc:
        logger.warning("research observability: telemetry scan failed (%s)", type(exc).__name__)
        consumption_view = {
            "status": "error", "window_days": window_days,
            "files_in_window": 0, "files_scanned": 0, "files_skipped": 0,
            "unreadable_files": 0, "oversized_lines": 0, "malformed_lines": 0,
            "bytes_scanned": 0, "partial": True, "cap_reason": "error",
            "surfaced_events": 0, "consumed_events": 0, "surfaced_pairs": 0, "consumed_pairs": 0,
            "distinct_pairs": 0, "surfaced_never_consumed": None,
            "surfaced_never_consumed_observed": 0, "pending": 0,
            "per_record": {}, "unknown_research_ids": _blank_unknown_agg(),
        }

    return {
        "generated_at": int(now.timestamp()),
        "generated_ts": now.isoformat(),
        "window_days": window_days,
        "discovery_enabled": discovery_enabled,
        "lifecycle": registry_view["lifecycle"],
        "adoption": registry_view["adoption"],
        "dead_consumers": registry_view["dead_consumers"],
        "consumption": consumption_view,
    }
