"""Private routing policy and closed public projections (#10154).

This module grants no execution or spending authority. ``load_policy`` returns
the complete validated private document (including inactive campaigns); only
``public_decision`` is suitable for public receipts. Hour reports are private.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import unicodedata
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_VERSION = "model-router-policy.v1"
RECEIPT_VERSION = "model-router-receipt.v1"
MAX_POLICY_BYTES = 1_048_576
_SCHEMA = Path(__file__).resolve().parents[2] / "schemas/model-router-policy.schema.json"
_DIGEST = re.compile(r"(?:sha256:)?[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_RULE = re.compile(r"[A-Z][A-Z0-9_]{0,79}\Z")
PUBLIC_CODES = frozenset({
    "UNKNOWN", "SELECTED", "REFUSED", "POLICY_INVALID", "POLICY_UNAVAILABLE",
    "POLICY_UNSAFE", "FACTS_UNKNOWN", "CAPACITY_UNKNOWN", "CAPACITY_EXHAUSTED",
    "READER_UNAVAILABLE", "READER_CORRUPT", "READER_PARTIAL", "READER_MISMATCH",
    "PROOF_MISSING", "PROOF_INVALID", "HOUR_INVALID", "HOUR_COMPLETE", "EXPORT_INVALID",
    "provider_unavailable", "transport_error", "timeout", "rate_limited",
    "result_invalid", "cancelled", "ttl_expired_orphan", "admission_refused",
})
STATUSES = frozenset({
    "selected", "refused", "unknown", "UNKNOWN", "reserved", "running", "complete",
    "failed", "expired", "cancelled", "queued", "dead_lettered", "done",
})
EVENT_TYPES = frozenset({
    "reserved", "started", "settled", "expired", "authorized_substitution",
    "superseded_active_attempt", "circuit_recorded", "circuit_healed",
    "legacy_authorization_envelope_reconstructed", "enqueued", "claimed", "finished",
    "selected", "admitted", "delivered", "merged", "complete", "failed", "cancelled",
})


class RouterPolicyError(ValueError):
    """A bounded code, with no input, content, path or chained exception."""

    def __init__(self, code: str) -> None:
        self.code = code if code in PUBLIC_CODES else "UNKNOWN"
        super().__init__(self.code)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def utc_time(value: Any) -> datetime:
    """Parse explicit UTC only; offsets, naive times and booleans confer no time."""
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
            raise ValueError
        return parsed.astimezone(UTC)
    except (AttributeError, TypeError, ValueError, OverflowError):
        raise RouterPolicyError("HOUR_INVALID") from None


def timestamp(value: Any) -> str | None:
    try:
        return utc_time(value).isoformat().replace("+00:00", "Z")
    except RouterPolicyError:
        return None


def hour_bounds(start: Any, end: Any) -> tuple[datetime, datetime]:
    first, last = utc_time(start), utc_time(end)
    if first.minute or first.second or first.microsecond or last - first != timedelta(hours=1):
        raise RouterPolicyError("HOUR_INVALID")
    return first, last


def read_private_bytes(path: str | Path, *, limit: int = MAX_POLICY_BYTES) -> bytes:
    """Open every component without following links, then read a bounded regular file.

    Directory descriptors avoid check/open races. Nonblocking open prevents
    FIFOs/devices from hanging before the regular-file check. No ``resolve``
    normalizes away a symlink or an unsafe parent traversal.
    """
    directory_fd = file_fd = None
    try:
        raw = os.fspath(path)
        if not isinstance(raw, str) or not raw or any(
            unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} for ch in raw
        ) or ".." in raw.split("/"):
            raise RouterPolicyError("POLICY_UNSAFE")
        parts = Path(raw).parts
        if not parts or parts == ("/",):
            raise RouterPolicyError("POLICY_UNSAFE")
        directory_fd = os.open("/" if Path(raw).is_absolute() else ".", os.O_RDONLY | os.O_DIRECTORY)
        relative = parts[1:] if Path(raw).is_absolute() else parts
        for part in relative[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(relative[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        info = os.fstat(file_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise RouterPolicyError("POLICY_UNSAFE")
        chunks = bytearray()
        while len(chunks) <= limit:
            block = os.read(file_fd, min(65536, limit + 1 - len(chunks)))
            if not block:
                return bytes(chunks)
            chunks.extend(block)
        raise RouterPolicyError("POLICY_UNSAFE")
    except (OSError, TypeError, ValueError) as exc:
        code = exc.code if isinstance(exc, RouterPolicyError) else "POLICY_UNAVAILABLE"
        # Raise outside the handler below so formatted tracebacks cannot include
        # the private OS exception through implicit context.
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)
    raise RouterPolicyError(code)


def strict_json(raw: bytes | str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise ValueError

    def finite_float(raw: str) -> float:
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError
        return value

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant, parse_float=finite_float)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        pass
    raise RouterPolicyError("POLICY_INVALID")


def load_policy(path: str | Path, *, now: Any) -> dict[str, Any]:
    """Return a closed, nonsecret private policy or a content-free typed refusal.

    Campaign time applicability is ``starts_at <= now < expires_at``; the
    selector consumes the original timestamps. Manual spend defaults off and
    is retained solely for legitimate private reporting, never for ranking.
    """
    document = strict_json(read_private_bytes(path))
    try:
        clock = utc_time(now)
        schema = json.loads(_SCHEMA.read_bytes())
        if not Draft202012Validator(schema).is_valid(document):
            raise ValueError
        document.setdefault("manual_spend_authorization", {"enabled": False})
        ids: set[str] = set()
        for campaign in document["campaigns"]:
            if campaign["id"] in ids or utc_time(campaign["starts_at"]) >= utc_time(campaign["expires_at"]):
                raise ValueError
            ids.add(campaign["id"])
            if any(public_identity(model) is None for model in campaign.get("models", [])) or any(
                public_identity(lane, "route") is None for lane in campaign.get("lanes", [])
            ):
                raise ValueError
        for window in document.get("window_metadata", []):
            if (utc_time(window["resets_at"]) - utc_time(window["starts_at"])).total_seconds() != window["duration_seconds"]:
                raise ValueError
        # Validate clock even for a document with no campaigns.
        del clock
        return document
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        pass
    raise RouterPolicyError("POLICY_INVALID")


@lru_cache(maxsize=4)
def _public_identity_sets(signature: tuple[int, int]) -> dict[str, set[str]]:
    from scripts.review.model_catalog import load_model_catalog, model_aliases

    catalog = load_model_catalog()
    routes = set(catalog.get("orchestrator_seats", {})) | set(catalog.get("review_candidates", {}))
    for seat in catalog.get("seats", {}).values():
        for route in seat.get("routes", {}).values():
            routes.update(route.get(key) for key in ("harness", "transport", "candidate", "lane", "route", "legacy_name"))
    routes.update({"codex", "claude", "grok", "agy", "cursor", "opencode", "kimi", "glm",
                   "native_codex", "native_claude", "native_grok", "native_kimi", "claude-code"})
    return {"model": set(model_aliases(catalog)) | set(catalog["models"]),
            "family": {item["family"] for item in catalog["models"].values()}, "route": routes}


def public_identity(value: Any, kind: str = "model") -> str | None:
    """Exact installed catalog identities only; regex-shaped secrets are not IDs."""
    from scripts.review.model_catalog import CATALOG_PATH, ModelCatalogError

    if not isinstance(value, str):
        return None
    try:
        info = CATALOG_PATH.stat()
        allowed = _public_identity_sets((info.st_mtime_ns, info.st_size))
        return value if value in allowed.get(kind, set()) else None
    except (ModelCatalogError, OSError, ValueError, TypeError, KeyError):
        return None


def public_code(value: Any) -> str | None:
    return value if isinstance(value, str) and value in PUBLIC_CODES else None


def fingerprint(value: Any, *, sha: bool = False) -> str | None:
    return value if isinstance(value, str) and (_SHA if sha else _DIGEST).fullmatch(value) else None


def public_decision(decision: Any) -> dict[str, Any]:
    """A closed projection, never a shallow copy or recursive raw trace filter."""
    data = decision if isinstance(decision, Mapping) else {}
    result: dict[str, Any] = {
        "schema_version": RECEIPT_VERSION,
        "status": data.get("status") if isinstance(data.get("status"), str) and data["status"] in STATUSES else "unknown",
        "code": public_code(data.get("code")) or "UNKNOWN",
        "rule_ids": [],
    }
    # Rule IDs must be explicitly registered by executable source. Unknown
    # strings, including syntactically plausible private strings, stay out.
    registered = PUBLIC_CODES
    rules = data.get("rule_ids")
    if isinstance(rules, (list, tuple)):
        result["rule_ids"] = sorted({rule for rule in rules if isinstance(rule, str) and _RULE.fullmatch(rule) and rule in registered})
    for key in ("model", "family", "lane", "harness", "transport"):
        value = public_identity(data.get(key), "family" if key == "family" else "model" if key == "model" else "route")
        if value is not None:
            result[key] = value
    for key in ("target_sha", "prompt_sha256", "catalog_sha256", "policy_sha256", "snapshot_sha256", "task_sha256"):
        value = fingerprint(data.get(key), sha=key == "target_sha")
        if value is not None:
            result[key] = value
    for key in ("observed_at", "expires_at"):
        value = timestamp(data.get(key))
        if value is not None:
            result[key] = value
    if data.get("effort") in ("low", "medium", "high", "xhigh", "max"):
        result["effort"] = data["effort"]
    return result


def opaque_id(value: Any) -> str | None:
    """Hash arbitrary authority/replay keys; never reflect their private strings."""
    if not isinstance(value, str) or not value:
        return None
    return value if re.fullmatch(r"[0-9a-f]{64}", value) else hashlib.sha256(value.encode()).hexdigest()


def finite_number(value: Any) -> int | float | None:
    return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def public_routing_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Close the legacy ledger/Runtime shape, keeping safe aliases and unknowns."""
    result: dict[str, Any] = {}
    for key, value in record.items():
        if key in {"requested", "resolved", "retry", "replay", "lifecycle", "latest_event"}:
            result[key] = public_routing_record(value) if isinstance(value, Mapping) else {}
        elif key == "event_history":
            result[key] = [public_routing_record(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []
        elif key in {"decision_id", "reservation_id", "source_authority_id", "authority_key", "idempotency_key", "initiator"}:
            result[key] = opaque_id(value)
        elif key in {"model", "resolved_model", "author_model", "requested_reviewer", "requested_route"}:
            result[key] = public_identity(value)
        elif key in {"family", "resolved_family", "author_family"}:
            result[key] = public_identity(value, "family")
        elif key in {"route", "candidate", "resolved_route", "resolved_candidate", "fallback_from"}:
            result[key] = public_identity(value, "route")
        elif key in {"event_type", "decision_event"}:
            result[key] = value if isinstance(value, str) and value in EVENT_TYPES else "unknown"
        elif key in {"state", "status", "decision_state", "current_state", "reservation_state", "terminal_status"}:
            result[key] = value if isinstance(value, str) and value in STATUSES else "unknown"
        elif key in {"created_at", "timestamp", "expires_at", "started_at", "settled_at"}:
            result[key] = timestamp(value)
        elif key in {"failure_classification", "selection_reason", "reason", "code"}:
            result[key] = public_code(value)
        elif key in {"risk", "requested_risk"}:
            result[key] = value if value in ("low", "medium", "high", "critical") else None
        elif key in {"role", "requested_role", "profile", "requested_profile"}:
            result[key] = value if value in ("review", "formal-review", "implementation", "recon", "code", "infra", "advisor", "security", "consult", "strict") else None
        elif key in {"route_mode"}:
            result[key] = value if value in ("auto", "explicit") else None
        elif key in {"automatic", "exceptional_pin", "completed", "zombie_expired"}:
            result[key] = value if isinstance(value, bool) else None
        elif key in {"attempt", "retry_attempt", "event_count", "duration_s", "estimated_input_bytes", "actual_bytes", "actual_tokens",
                     "actual_input_bytes", "actual_output_bytes", "actual_input_tokens", "actual_output_tokens", "actual_work_bytes"}:
            result[key] = finite_number(value)
        elif key in {"quota", "quota_snapshot", "trace", "selection_trace", "selection_reasoning", "quota_source", "quota_freshness",
                     "quota_freshness_state", "quota_fresh_at", "quota_headroom", "quota_headroom_band", "credential_bucket",
                     "quota_bucket", "policy_version", "evidence", "capacity_evidence", "retry_chain", "failover_chain",
                     "replay_status", "cache_status"}:
            result[key] = None
    return result


def aggregate_hour(events: Iterable[Mapping[str, Any]], *, start: Any, end: Any, complete: Any) -> dict[str, Any]:
    """Aggregate private immutable events using a reader-issued completeness receipt.

    The reader validates canonical outcome references; booleans or caller
    mappings cannot establish coverage. A report never promotes done to delivery.
    """
    from scripts.fleet.router_report import aggregate_read_hour

    return aggregate_read_hour(events, start=start, end=end, receipt=complete)
