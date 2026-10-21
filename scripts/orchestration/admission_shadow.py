"""Bounded, local PSI calibration journal for #10802. Never authorizes admission."""

from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import re
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA = "admission-shadow.v1"
DIRECTORY_ENV = "DISPATCH_PSI_SHADOW_DIR"
MAX_DAY_BYTES = 16 * 1024 * 1024
MAX_ROW_BYTES = 8192
MAX_ATTRIBUTED = 10
SAMPLE_GAP_S = 60
CANDIDATE = {
    "stop_avg10_above": 40,
    "stop_avg60_above": 30,
    "resume_avg10_below": 25,
    "resume_avg60_below": 20,
    "resume_seconds": 60,
}


def label(value: object) -> str:
    """Keep only bounded task identifiers, never arbitrary paths or free text."""
    return value if isinstance(value, str) and re.fullmatch(r"[\w.-]{1,96}", value, re.ASCII) else "unknown"


def read_pressure(proc_root: Path) -> dict[str, Any]:
    """Read fixed-size kernel PSI files; each absent or invalid metric stays unknown.

    Format authority: https://docs.kernel.org/accounting/psi.html . CPU full
    is undefined at system scope and is deliberately not used.
    """
    result: dict[str, Any] = {}
    for resource in ("cpu", "memory", "io"):
        try:
            with (proc_root / "pressure" / resource).open(encoding="ascii") as handle:
                text = handle.read(4097)
            if len(text) > 4096:
                raise ValueError
            rows: dict[str, dict[str, str]] = {}
            for line in text.splitlines():
                parts = line.split()
                if not parts or parts[0] in rows:
                    raise ValueError
                rows[parts[0]] = dict(part.split("=", 1) for part in parts[1:])
        except (OSError, UnicodeError, ValueError):
            rows = {}
        for kind in ("some",) if resource == "cpu" else ("some", "full"):
            key = f"{resource}.{kind}"
            try:
                values = {name: float(rows[kind][name]) for name in ("avg10", "avg60", "avg300")}
                total = int(rows[kind]["total"])
                if total < 0 or any(not math.isfinite(v) or not 0 <= v <= 100 for v in values.values()):
                    raise ValueError
                result[key] = {**values, "unknown": None}
            except (KeyError, ValueError):
                result[key] = {"avg10": None, "avg60": None, "avg300": None, "unknown": "unavailable_or_malformed"}
    return result


def transition(pressure: dict[str, Any], previous: dict[str, Any], now: float) -> dict[str, Any]:
    """Candidate CPU hysteresis; gaps cannot prove a continuous recovery window."""
    cpu = pressure["cpu.some"]
    a, b = cpu["avg10"], cpu["avg60"]
    last = previous.get("timestamp")
    continuous = isinstance(last, (int, float)) and 0 <= now - last <= SAMPLE_GAP_S
    old = previous.get("psi", {}) if continuous else {}
    if a is None or b is None:
        return {"decision": "unknown", "low_since": None, "reason": "cpu_psi_unknown"}
    if a > CANDIDATE["stop_avg10_above"] or b > CANDIDATE["stop_avg60_above"]:
        return {"decision": "refuse", "low_since": None, "reason": "above_candidate_stop"}
    if a < CANDIDATE["resume_avg10_below"] and b < CANDIDATE["resume_avg60_below"]:
        since = old.get("low_since")
        since = since if isinstance(since, (int, float)) and since <= now else now
        if old.get("decision") == "admit" or now - since >= CANDIDATE["resume_seconds"]:
            return {"decision": "admit", "low_since": since, "reason": "below_candidate_resume"}
        return {"decision": old.get("decision", "unknown"), "low_since": since, "reason": "recovery_window_incomplete"}
    return {"decision": old.get("decision", "unknown"), "low_since": None, "reason": "hysteresis_band"}


def _tail(path: Path) -> dict[str, Any]:
    """At most one bounded row, irrespective of journal length."""
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            handle.seek(max(0, handle.tell() - MAX_ROW_BYTES))
            last_line = handle.read(MAX_ROW_BYTES).rstrip(b"\n").rsplit(b"\n", 1)[-1]
        row = json.loads(last_line)
        if not isinstance(row, dict) or row.get("schema") != SCHEMA or row.get("candidate") != CANDIDATE:
            return {}
        psi = row.get("psi")
        if not isinstance(psi, dict) or psi.get("decision") not in {"admit", "refuse", "unknown"}:
            return {}
        return row
    except (OSError, ValueError, IndexError, TypeError):
        return {}


def observe(
    directory: Path, pressure: dict[str, Any], context: dict[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    """Append under a non-waiting lock; failure affects diagnostics only.

    Two date-named files are read at most, without scanning directories. Each
    daily journal is capped. Full, contended or inaccessible journals report
    unknown persistence, never a successful measurement.
    """
    clock = (now or datetime.now(UTC)).astimezone(UTC)
    row = {"schema": SCHEMA, "timestamp": clock.timestamp(), "candidate": CANDIDATE, "pressure": pressure, **context}
    row["psi"] = transition(pressure, {}, clock.timestamp())
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "observer.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            path = directory / f"{clock:%Y-%m-%d}.jsonl"
            previous = _tail(path) or _tail(directory / f"{clock - timedelta(days=1):%Y-%m-%d}.jsonl")
            row["psi"] = transition(pressure, previous, clock.timestamp())
            payload = (json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n").encode()
            if (
                len(payload) > MAX_ROW_BYTES
                or (path.stat().st_size if path.exists() else 0) + len(payload) > MAX_DAY_BYTES
            ):
                row["persistence"] = "unknown: journal_limit"
                return row
            with path.open("ab") as handle:
                handle.write(payload)
        row["persistence"] = "recorded"
    except (OSError, ValueError):
        row["persistence"] = "unknown: journal_unavailable_or_busy"
    return row


def compare_day(directory: Path, day: str) -> dict[str, Any]:
    """Compare a UTC calendar day's sampled decisions, never infer unsampled work."""
    start = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC).timestamp()
    counts: Counter[str] = Counter()
    phases: Counter[str] = Counter()
    enforcement: Counter[str] = Counter()
    unknown_signals: Counter[str] = Counter()
    peaks: dict[str, float] = {}
    first = last = None
    invalid = 0
    with (directory / f"{day}.jsonl").open("rb") as handle:
        if os.fstat(handle.fileno()).st_size > MAX_DAY_BYTES:
            raise ValueError("journal exceeds daily bound")
        for raw in handle:
            try:
                if len(raw) > MAX_ROW_BYTES:
                    raise ValueError
                row = json.loads(raw)
                stamp = row["timestamp"]
                if row["schema"] != SCHEMA or not start <= stamp < start + 86400:
                    raise ValueError
                current, proposed = row["load_decision"], row["psi"]["decision"]
                if current not in {"admit", "refuse", "unknown"} or proposed not in {"admit", "refuse", "unknown"}:
                    raise ValueError
                phase = row["phase"]
                admitted = row["current_admission_decision"]
                if phase not in {"precheck", "evaluate"} or admitted not in {"admit", "refuse", "unknown"}:
                    raise ValueError
                # Validate the whole row before adding any counts.
                signals = row["pressure"]
                if not isinstance(signals, dict):
                    raise ValueError
                for value in signals.values():
                    if not isinstance(value, dict) or "unknown" not in value or "avg60" not in value:
                        raise ValueError
                    if value["unknown"] is None and (
                        not isinstance(value["avg60"], (int, float))
                        or not math.isfinite(value["avg60"])
                        or not 0 <= value["avg60"] <= 100
                    ):
                        raise ValueError
                counts[f"load_{current}__psi_{proposed}"] += 1
                phases[phase] += 1
                enforcement[admitted] += 1
                for signal, value in signals.items():
                    if value["unknown"] is not None:
                        unknown_signals[signal] += 1
                    elif value["avg60"] is not None:
                        peaks[signal] = max(peaks.get(signal, 0), value["avg60"])
                first = stamp if first is None else min(first, stamp)
                last = stamp if last is None else max(last, stamp)
            except (ValueError, KeyError, TypeError):
                invalid += 1
    return {
        "schema": SCHEMA,
        "day": day,
        "denominator": "sampled evaluations, not unique dispatches",
        "samples": sum(counts.values()),
        "comparisons": dict(counts),
        "phases": dict(phases),
        "current_admission_decisions": dict(enforcement),
        "unknown_signals": dict(unknown_signals),
        "peak_avg60_percent": peaks,
        "invalid_rows": invalid,
        "first_timestamp": first,
        "last_timestamp": last,
        "observed_span_seconds": last - first if first is not None else 0,
        "coverage": "sampled_only; unsampled intervals and unattributed load remain unknown",
        "enforcement_changed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare one UTC day of admission PSI shadow samples.\nUse after observation; this cannot authorize PSI enforcement.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.orchestration.admission_shadow --directory <journal-dir> --day 2026-10-20\n"
        "Outputs: JSON comparison on stdout; reads bounded journals only.\nExit codes: 0 report, 1 unavailable or invalid journal.\n"
        "Related: #10802; scripts/orchestration/dispatch_admission.py",
    )
    parser.add_argument(
        "--directory", required=True, type=Path, help="Local shadow journal directory, e.g. <journal-dir>."
    )
    parser.add_argument("--day", required=True, help="UTC calendar day in YYYY-MM-DD format, e.g. 2026-10-20.")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(compare_day(args.directory, args.day), sort_keys=True))
    except (OSError, ValueError):
        print(json.dumps({"error": "comparison_unavailable"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
