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
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from scripts.audit import check_research_registry as crr
from scripts.orchestration import issue_stream_audit as isa
from scripts.research import consumption
from scripts.research import registry as reg

logger = logging.getLogger("research.observability")

# Consumer kinds P1 resolves deterministically OFFLINE (file/symbol/decision). An
# ``issue``/``corpus`` consumer needs an injected live resolver the monitor does
# not have — those are reported ``unverified``, never falsely ``dead``.
_OFFLINE_CONSUMER_KINDS = frozenset({"path", "prompt", "rubric", "test", "decision"})

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
def _load_raw_records(root: Path) -> tuple[list[dict[str, Any]] | None, str]:
    """Return (records, status). ``status`` ∈ ok/missing/unreadable/invalid.

    Reads the raw YAML directly so semantic-invalid records stay *visible* — the
    runtime loader would collapse the whole registry to ``None`` on any P1 error.
    """
    path = root / "docs" / "references" / "research-registry.yaml"
    if not path.exists():
        return None, "missing"
    try:
        _raw, data = crr.load_registry(path)
    except (OSError, ValueError, yaml.YAMLError, RecursionError):
        return None, "unreadable"
    records = data.get("records")
    if not isinstance(records, list):
        return None, "invalid"
    return [r for r in records if isinstance(r, dict) and r.get("id")], "ok"


def _consumer_status(record: dict[str, Any], root: Path, decision_ids: set[str]) -> str:
    """Classify an adopted record's typed consumer: alive/dead/unverified/none."""
    consumer = record.get("consumer")
    if not isinstance(consumer, dict) or not consumer.get("kind"):
        return "none"
    kind = consumer["kind"]
    if kind in _OFFLINE_CONSUMER_KINDS:
        try:
            errs = crr.validate_consumer(
                record, project_root=root, decision_ids=decision_ids
            )
        except Exception:  # defensive: a malformed ref must not 500 the monitor
            return "dead"
        return "dead" if errs else "alive"
    if kind in {"issue", "corpus"}:
        return "unverified"
    return "dead"  # unknown kind — cannot resolve


def _lifecycle_and_adoption(root: Path, max_age_s: int) -> dict[str, Any]:
    records, status = _load_raw_records(root)
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

    membership_report = isa.read_membership_index(max_age_s)
    ownership_cache = "fresh" if membership_report is not None else "missing"
    resolver = isa.make_membership_resolver(membership_report) if membership_report else None

    counts: Counter[str] = Counter()
    stale: list[str] = []
    orphaned: list[str] = []
    ownership_unverified: list[str] = []
    deferred: list[str] = []
    superseded: list[str] = []
    dead: list[str] = []
    unverified_consumers: list[str] = []
    adopted = 0
    effective_adopted = 0
    known_ids: set[str] = set()

    for rec in records:
        rid = rec["id"]
        known_ids.add(rid)
        state = rec.get("state")

        # Hash drift ("stale") — only meaningful when the projection resolves.
        drifted = False
        try:
            drifted = rec.get("content_hash") != crr.expected_content_hash(rec, root)
        except crr.ProvenanceError:
            drifted = False  # broken provenance is counted as invalid, not stale
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
            cstatus = _consumer_status(rec, root, decision_ids)
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


def _parse_ts(value: Any, now: datetime) -> datetime | None:
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


def _ingest_line(line: str, now: datetime, start: datetime, acc: _Accumulator) -> None:
    """Fold one JSONL line into ``acc``. Malformed/non-dict lines bump the safe
    counter; only the two research event types with a task+research pair and an
    in-window timestamp contribute. Never logs line content."""
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
        return
    task_id = evt.get("task_id")
    research_id = evt.get("research_id")
    if not isinstance(task_id, str) or not isinstance(research_id, str):
        return
    ts = _parse_ts(evt.get("ts"), now)
    if ts is None or ts < start or ts > now:  # drop out-of-window + future events
        return
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


def _scan_telemetry(
    root: Path, window_days: int, now: datetime, known_ids: set[str]
) -> dict[str, Any]:
    events_dir = root / "batch_state" / "telemetry" / "events"
    start = now - timedelta(days=window_days)
    acc = _Accumulator()

    files_scanned = 0
    unreadable_files = 0
    bytes_scanned = 0
    partial = False
    capped = False

    for stem in _window_dates(now, window_days):
        if capped:
            break
        path = events_dir / f"{stem}.jsonl"
        if not path.exists():
            continue
        files_scanned += 1
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line_bytes = len(line.encode("utf-8"))
                    if bytes_scanned + line_bytes > MAX_SCAN_BYTES:
                        partial = True
                        capped = True
                        break
                    bytes_scanned += line_bytes
                    stripped = line.strip()
                    if stripped:
                        _ingest_line(stripped, now, start, acc)
        except (OSError, UnicodeDecodeError) as exc:
            unreadable_files += 1
            partial = True
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
        files_scanned=files_scanned,
        unreadable_files=unreadable_files,
        bytes_scanned=bytes_scanned,
        partial=partial,
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
        "pending": 0,
    }


def _finalize_consumption(
    *,
    acc: _Accumulator,
    now: datetime,
    known_ids: set[str],
    window_days: int,
    files_scanned: int,
    unreadable_files: int,
    bytes_scanned: int,
    partial: bool,
) -> dict[str, Any]:
    consumed_pairs_set = set(acc.consumed_max)
    all_pairs = set(acc.surfaced_first) | consumed_pairs_set

    # Per-research aggregates. Known ids get their own bucket; every unknown id is
    # folded into a single aggregate — its string is never echoed (privacy).
    per_record: dict[str, dict[str, int]] = {rid: _blank_record_agg() for rid in known_ids}
    unknown = _blank_record_agg()
    unknown["distinct_research_ids"] = 0
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

    status = "partial" if partial else ("empty" if not all_pairs and not files_scanned else "ok")
    return {
        "status": status,
        "window_days": window_days,
        "files_scanned": files_scanned,
        "unreadable_files": unreadable_files,
        "malformed_lines": acc.malformed_lines,
        "bytes_scanned": bytes_scanned,
        "partial": partial,
        "surfaced_events": sum(acc.surfaced_events.values()),
        "consumed_events": sum(acc.consumed_events.values()),
        "surfaced_pairs": len(acc.surfaced_first),
        "consumed_pairs": len(consumed_pairs_set),
        "distinct_pairs": len(all_pairs),
        "surfaced_never_consumed": surfaced_never,
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
                          "superseded": [], "ownership_cache": "missing"},
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
            "status": "error", "window_days": window_days, "files_scanned": 0,
            "unreadable_files": 0, "malformed_lines": 0, "bytes_scanned": 0, "partial": True,
            "surfaced_events": 0, "consumed_events": 0, "surfaced_pairs": 0, "consumed_pairs": 0,
            "distinct_pairs": 0, "surfaced_never_consumed": 0, "pending": 0,
            "per_record": {}, "unknown_research_ids": _blank_record_agg(),
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
