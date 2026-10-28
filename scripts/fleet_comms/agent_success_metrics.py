"""Read-only dispatch-v2 cohort metrics. No prompts, transcripts or result bodies escape."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any

from learn_ukrainian_v4_runtime.model_families import canonical_cursor_model

from scripts.fleet_comms.efficiency_metrics import _parse_timestamp, _read_task_record, _task_record_paths
from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, model_aliases
from scripts.review.record_cf_verdict import RecordError, normalize_verdict
from scripts.review.verdict_parser import _commonmark_lines, _without_code_fences

STATUSES = (
    "done",
    "no_deliverable",
    "failed",
    "timeout",
    "rate_limited",
    "cancelled",
    "crashed",
    "needs_finalize",
    "running",
    "spawning",
    "unknown",
)
TERMINAL = frozenset(STATUSES[:7])
REASONS = (
    "outside_owned_paths",
    "owned_paths_verification_failed",
    "worktree_dirty_or_unknown",
    "no_commits_or_unknown",
    "work_not_pushed_or_unknown",
    "unknown",
)
ERROR_CLASSES = (
    "permission_denied",
    "stream",
    "auto_denied",
    "rate_limited",
    "timeout",
    "cancelled",
    "crashed",
    "no_deliverable",
    "output_schema_invalid",
    "review_missing_verdict_line",
    "review_ambiguous_verdict",
    "review_gate_error",
    "unknown",
)
VERDICTS = {
    "APPROVE": "APPROVED",
    "APPROVED": "APPROVED",
    "REQUEST_CHANGES": "CHANGES_REQUESTED",
    "CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "BLOCKED": "BLOCKED",
}
SEVERITIES = ("P0", "P1", "P2", "P3", "critical", "high", "medium", "low", "unknown")
TOKEN_ALIASES = {
    "input_tokens": ("input_tokens", "inputTokens"),
    "output_tokens": ("output_tokens", "outputTokens"),
    "total_tokens": ("total_tokens",),
    "cache_read_tokens": (
        "cached_input_tokens",
        "cache_read_input_tokens",
        "cache_read_tokens",
        "cacheReadTokens",
        "cached_tokens",
    ),
    "cache_write_tokens": ("cache_write_input_tokens", "cache_creation_input_tokens", "cacheWriteTokens"),
    "reasoning_tokens": ("reasoning_output_tokens", "thinking_tokens", "reasoning_tokens"),
}
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
# Only explicit finding headers count. Quoted/code examples and prose mentions do not.
_FINDING = re.compile(r"^ {0,3}(?:#{1,6} |[-*] )?[*_]*\[(P[0-3])\](?:[*_\s:.-]|$)")
_FINDING_ID = re.compile(
    r"^ {0,3}(?:#{1,6} +|[-*+] +|\d+[.)] +)?[*_]*(F\d+)\b[*_]*"
    r"[\s:.(\[—–-]*(?:severity[:\s]+)?(P[0-3])\b",
    re.IGNORECASE,
)


def _label(value: object) -> str:
    if isinstance(value, str) and _ID.fullmatch(value) and ".." not in value:
        return value
    return "unknown"


def _number(value: object) -> float | int | None:
    return value if type(value) in (float, int) and 0 <= value <= 1e100 and math.isfinite(value) else None


def _first_number(mapping: dict, names: tuple[str, ...]) -> float | int | None:
    return next((n for key in names if (n := _number(mapping.get(key))) is not None), None)


def _metric(values: list, total: int, *, operation=sum) -> dict:
    return {
        "value": operation(values) if values else "unknown",
        "observed": len(values),
        "unknown": total - len(values),
    }


def _rate(done: int, total: int) -> dict:
    return {"numerator": done, "denominator": total, "percent": round(100 * done / total, 2) if total else "unknown"}


def _failure(record: dict, status: str) -> str:
    text = "\n".join(v for k in ("last_error", "error", "failure_code") if isinstance(v := record.get(k), str)).lower()
    code = text.split(":", 1)[0]
    if code in ERROR_CLASSES:
        return code
    for label, pattern in (
        ("auto_denied", r"auto[_ -]denied"),
        ("permission_denied", r"permission[_ -]denied|eacces"),
        ("stream", r"stream(?:[_ -](?:error|closed|failed|disconnected)|error)"),
        ("rate_limited", r"rate[_ -]limit"),
    ):
        if re.search("^(?:" + pattern + r")(?:$|[\s:_ -])", text, re.MULTILINE):
            return label
    return status if status in ERROR_CLASSES else "unknown"


def _result_text(path: Path, record: dict) -> str | None:
    """Read only an adjacent final-result sidecar, never a record-supplied arbitrary path."""
    declared = record.get("result_file")
    name = Path(declared).name if isinstance(declared, str) else path.stem + ".result"
    if not name.endswith(".result"):
        return None
    result = path.with_name(name)
    try:
        fd = os.open(result, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > 4 * 1024 * 1024:
                return None
            with os.fdopen(fd, "rb", closefd=False) as stream:
                raw = stream.read(4 * 1024 * 1024 + 1)
        finally:
            os.close(fd)
        if len(raw) > 4 * 1024 * 1024:
            return None
        expected = record.get("result_sha256")
        if not expected or hashlib.sha256(raw).hexdigest() != expected:
            return None
        return raw.decode("utf-8")
    except (OSError, ValueError):
        return None


def _review(path: Path, record: dict) -> dict | None:
    if not any(record.get(k) for k in ("review_profile", "review_author_model", "require_review_verdict")):
        return None
    verdict, findings = "unknown", None
    if record.get("status") == "done":
        recorded = VERDICTS.get(str(record.get("review_verdict")), "unknown")
        text = _result_text(path, record)
        if text is not None:
            try:
                verdict = normalize_verdict(text)
            except RecordError:
                verdict = "unknown"
            if recorded != "unknown" and recorded != verdict:
                verdict = "unknown"
            try:
                payload = json.loads(text)
            except (ValueError, RecursionError):
                payload = None
            if isinstance(payload, dict) and isinstance(payload.get("findings"), list) and verdict != "unknown":
                findings = payload["findings"]
            elif verdict != "unknown":
                identified, anonymous = {}, []
                for line in _commonmark_lines(_without_code_fences(text, keep_unclosed=False)):
                    match = _FINDING_ID.match(line)
                    if match:
                        identity, priority = match[1].upper(), match[2].upper()
                        earlier = identified.get(identity, priority)
                        identified[identity] = priority if earlier == priority else "unknown"
                    elif match := _FINDING.match(line):
                        anonymous.append(match[1])
                priorities = [*identified.values(), *anonymous]
                if priorities:
                    findings = [{"priority": priority} for priority in priorities]
        else:
            verdict = recorded
        if verdict != "unknown" and findings is None and isinstance(record.get("findings"), list):
            findings = record["findings"]
    severities = Counter()
    confirmations = []
    if findings is not None:
        for finding in findings:
            finding = finding if isinstance(finding, dict) else {}
            priority = finding.get("priority", finding.get("severity"))
            severities[priority if isinstance(priority, str) and priority in SEVERITIES else "unknown"] += 1
            if type(finding.get("confirmed")) is bool:
                confirmations.append(int(finding["confirmed"]))
    return {
        "verdict": verdict,
        "findings": findings,
        "severities": severities,
        "confirmations": confirmations,
        "round": _number(record.get("review_round")) if verdict == "APPROVED" else None,
    }


def _usage(record: dict, model: str) -> dict:
    usage = record.get("usage")
    if not isinstance(usage, dict):
        return {}
    if record.get("agent") == "muse":
        rows = usage.get("models")
        if not isinstance(rows, list):
            return {}
        rows = [r for r in rows if isinstance(r, dict) and r.get("model") == model]
        result = {}
        for key, aliases in TOKEN_ALIASES.items():
            values = [_first_number(row, aliases) for row in rows]
            if values and all(v is not None for v in values):
                result[key] = sum(values)
        return result
    result = {key: n for key, aliases in TOKEN_ALIASES.items() if (n := _first_number(usage, aliases)) is not None}
    details = usage.get("output_tokens_details")
    if (
        "reasoning_tokens" not in result
        and isinstance(details, dict)
        and (n := _number(details.get("thinking_tokens"))) is not None
    ):
        result["reasoning_tokens"] = n
    return result


def _summary(rows: list[dict]) -> dict:
    statuses = Counter(r["status"] for r in rows)
    reasons = Counter()
    errors = Counter()
    roles = Counter()
    for row in rows:
        record, status = row["record"], row["status"]
        roles["review" if row["review"] else "authoring" if record.get("mode") == "workspace-write" else "other"] += 1
        if status == "no_deliverable":
            raw = record.get("no_deliverable_reason")
            reason = raw.split(":", 1)[0] if isinstance(raw, str) else None
            reasons[reason if reason in REASONS else "unknown"] += 1
        if status in TERMINAL - {"done"}:
            errors[_failure(record, status)] += 1
    terminal = sum(statuses[s] for s in TERMINAL)
    durations = []
    for row in rows:
        record = row["record"]
        if row["status"] not in TERMINAL:
            continue
        duration = _number(record.get("duration_s"))
        if duration is None:
            start, end = _parse_timestamp(record.get("started_at")), _parse_timestamp(record.get("finished_at"))
            duration = _number((end - start).total_seconds()) if start and end else None
        if duration is not None:
            durations.append(duration)
    reviews = [r["review"] for r in rows if r["review"] is not None]
    verdicts = Counter(r["verdict"] for r in reviews)
    findings = [r for r in reviews if r["findings"] is not None]
    severity = sum((r["severities"] for r in findings), Counter())
    confirmed = [v for r in findings for v in r["confirmations"]]
    finding_count = sum(len(r["findings"]) for r in findings)
    approvals = [r for r in reviews if r["verdict"] == "APPROVED"]
    rounds = [r["round"] for r in approvals if type(r["round"]) is int and r["round"] > 0]
    result = {
        "tasks": len(rows),
        "roles": dict(roles),
        "model_sources": dict(Counter(r["model_source"] for r in rows)),
        "status": {s: statuses[s] for s in STATUSES},
        "success": _rate(statuses["done"], len(rows)),
        "terminal_success": _rate(statuses["done"], terminal),
        "no_deliverable_reasons": {s: reasons[s] for s in REASONS},
        "failure_classes": {s: errors[s] for s in ERROR_CLASSES},
        "median_wall_seconds": _metric(durations, terminal, operation=median),
        "reviews": {
            "tasks": len(reviews),
            "verdicts": {v: verdicts[v] for v in ("APPROVED", "CHANGES_REQUESTED", "BLOCKED", "unknown")},
            "changes_requested": verdicts["CHANGES_REQUESTED"],
            "rounds_to_approval": _metric(rounds, len(approvals), operation=median),
            "findings": _metric([len(r["findings"]) for r in findings], len(reviews)),
            "finding_severities": {s: severity[s] for s in SEVERITIES} if findings else "unknown",
            "confirmed_findings": _metric(confirmed, finding_count),
            "confirmation_rate": _rate(sum(confirmed), len(confirmed)),
            "unobserved_finding_reviews": len(reviews) - len(findings),
        },
        "tokens": {k: _metric([r["usage"][k] for r in rows if k in r["usage"]], len(rows)) for k in TOKEN_ALIASES},
    }
    for key in ("pr_opened", "pr_merged", "merge_group_ci_failures", "cost_usd"):
        records = [r["record"] for r in rows]
        values = []
        prs = set()
        for record in records:
            value = record.get(key)
            if key.startswith("pr_"):
                if record.get("mode") != "workspace-write" or type(value) is not bool:
                    continue
                if value:
                    number = record.get("pr", record.get("pr_number"))
                    if type(number) is not int or number <= 0:
                        continue
                    repository = record.get("repository", record.get("repository_id", record.get("repo")))
                    if not isinstance(repository, str) or not repository:
                        continue
                    prs.add((repository, number))
                values.append(int(value))
            elif key == "cost_usd":
                usage = record.get("usage")
                cost = _first_number(record, ("cost_usd", "total_cost_usd"))
                if cost is None and isinstance(usage, dict):
                    cost = _first_number(usage, ("cost_usd", "total_cost_usd"))
                if cost is not None:
                    values.append(cost)
            elif key == "merge_group_ci_failures" and type(value) is int and value >= 0:
                values.append(value)
        result[key] = _metric(values, len(records))
        if key.startswith("pr_") and values:
            result[key]["value"] = len(prs)
    return result


def collect_agent_success(
    *, tasks_dir: Path, since: datetime | None = None, until: datetime | None = None
) -> dict[str, Any]:
    """Count unique v2 runs started in [since, until), with hot records winning duplicate nonces."""
    until = (until or datetime.now(UTC)).astimezone(UTC)
    since = (since or until - timedelta(days=3)).astimezone(UTC)
    if since >= until:
        raise ValueError("since must precede until")
    coverage = Counter()
    rows, seen = [], set()
    available = True
    try:
        catalog = load_model_catalog()
        aliases = {alias.casefold(): owner for alias, owner in model_aliases(catalog).items()}
        for owner, model in catalog["models"].items():
            for alias in (*model.get("routing_wire_ids", {}).values(), *model.get("runtime_model_ids", [])):
                key = alias.casefold()
                aliases[key] = owner if aliases.get(key, owner) == owner else "unknown"
    except ModelCatalogError:
        available, aliases = False, {}
        coverage["model_catalog_unavailable"] += 1
    for directory, source in ((tasks_dir, "hot"), (tasks_dir / "archive", "archive")):
        try:
            paths = _task_record_paths(directory, optional=source == "archive")
        except OSError:
            available = False
            coverage["unreadable_directories"] += 1
            continue
        for path in paths:
            coverage[source + "_records"] += 1
            record, error = _read_task_record(path)
            if error or not isinstance(record, dict):
                coverage["invalid_records"] += 1
                continue
            if type(record.get("schema_version")) is not int or record["schema_version"] != 2:
                coverage["excluded_legacy"] += 1
                continue
            if (
                record.get("dry_run") is True
                or record.get("status") == "dry_run"
                or record.get("launch_mode") == "dry_run"
            ):
                coverage["excluded_dry_run"] += 1
                continue
            identity = record.get("task_id"), record.get("run_nonce")
            if not all(isinstance(v, str) and v for v in identity):
                coverage["invalid_records"] += 1
                continue
            if identity in seen:
                coverage["duplicate_runs"] += 1
                continue
            seen.add(identity)
            start = _parse_timestamp(record.get("started_at"))
            if start is None:
                coverage["undated_records"] += 1
                continue
            if not since <= start < until:
                coverage["outside_window"] += 1
                continue
            requested = _label(record.get("model"))
            # Runtime identity wins when recorded as known; display aliases use the shared normalizer.
            resolved = record.get("resolved_model")
            if record.get("agent") == "cursor" and isinstance(resolved, str):
                resolved = canonical_cursor_model(resolved) or resolved
            observed = _label(resolved) if record.get("resolved_model_known") is True else "unknown"
            model = observed if observed != "unknown" else requested
            model = _label(aliases.get(model.casefold(), model)) if available else "unknown"
            selector = requested.lower()
            if observed == "unknown" and selector in {"auto", "default", "unknown"}:
                model = "unknown"
            status = record.get("status")
            rows.append(
                {
                    "record": record,
                    "agent": _label(record.get("agent")),
                    "model": model,
                    "status": status if isinstance(status, str) and status in STATUSES else "unknown",
                    "model_source": "resolved"
                    if observed != "unknown"
                    else "requested"
                    if model != "unknown"
                    else "unknown",
                    "review": _review(path, record),
                    "usage": _usage(record, requested),
                }
            )
    return {
        "schema_version": "agent-success.v1",
        "content_included": False,
        "source": "dispatch_v2",
        "available": available,
        "complete": available and not any(coverage[k] for k in ("invalid_records", "undated_records")),
        "window": {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "cohort": "started_at",
            "bounds": "[since,until)",
        },
        "coverage": {
            k: coverage[k]
            for k in (
                "hot_records",
                "archive_records",
                "excluded_legacy",
                "excluded_dry_run",
                "invalid_records",
                "undated_records",
                "outside_window",
                "duplicate_runs",
                "unreadable_directories",
                "model_catalog_unavailable",
            )
        },
        "tasks": len(rows),
        "by_agent": {
            key: _summary([r for r in rows if r["agent"] == key]) for key in sorted({r["agent"] for r in rows})
        },
        "by_model": {
            key: _summary([r for r in rows if r["model"] == key]) for key in sorted({r["model"] for r in rows})
        },
    }
