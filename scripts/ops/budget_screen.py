"""Read-only funding screen using the same inputs as dispatch shadow selection."""

from __future__ import annotations

import argparse
import shlex
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.dispatcher import pool_selector as selector


def shadow_history(now: datetime, pool_sources: dict[str, str], records: list[dict]) -> tuple[Counter, dict]:
    counts = Counter()
    samples = {}
    for record in records:
        shadow = record.get("pool_shadow") or {}
        observed = selector.timestamp(shadow.get("observed_at"))
        if (observed and now - timedelta(hours=24) <= observed <= now
                and shadow.get("decision") in {"Selected", "ResetRequired"}):
            counts[shadow.get("pool")] += 1
        if observed is None or observed > now:
            continue
        for key, raw in shadow.get("meters", {}).items():
            if key not in pool_sources or shadow.get("pool_sources", {}).get(key) != pool_sources[key]:
                continue
            meter = selector.Meter(selector.timestamp(raw.get("observed_at")),
                tuple(selector.Window(w["name"], w["left"], selector.timestamp(w.get("ends_at")), w["unit"])
                      for w in raw["windows"]), raw["status"])
            if meter.observed_at:
                samples.setdefault(key, {})[meter.observed_at] = meter
    return counts, samples


def burn_pace(current: selector.Meter, previous: selector.Meter | None) -> str:
    if (previous is None or current.status != "ok" or previous.status != "ok"
            or current.observed_at is None or previous.observed_at is None):
        return "unknown"
    seconds = (current.observed_at - previous.observed_at).total_seconds()
    if seconds <= 0:
        return "unknown"
    old = {w.name: w for w in previous.windows}
    if set(old) != {w.name for w in current.windows}:
        return "unknown"
    rates = []
    for window in current.windows:
        before = old.get(window.name)
        if (before is None or before.ends_at != window.ends_at or before.unit != window.unit
                or window.ends_at is None or window.left is None or before.left is None
                or window.left > before.left):
            return "unknown"
        unit = "pp/h" if window.unit == "%" else f"{window.unit}/h"
        rates.append(f"{window.name}:{(before.left - window.left) * 3600 / seconds:.2f} {unit}")
    return ", ".join(rates) or "unknown"


def needed_pace(pool: selector.Pool | None, meter: selector.Meter, now: datetime) -> str:
    if pool is None or pool.kind != "api":
        return "unknown"
    deadline = selector.timestamp(pool.expires_at)
    approximate = False
    if deadline is None and isinstance(pool.expires_at, str) and len(pool.expires_at) == 10:
        try:
            deadline = datetime.fromisoformat(pool.expires_at).replace(tzinfo=UTC)
            approximate = True  # date-only grants do not establish an execution deadline
        except ValueError:
            pass
    if deadline is None:
        deadline = min((w.ends_at for w in meter.windows if w.ends_at), default=None)
    if deadline is None or deadline <= now:
        return "unknown"
    days = (deadline - now).total_seconds() / 86400
    balance = next((w for w in meter.windows if w.name == "balance" and w.left is not None), None)
    detail = f"{days:.1f}d left"
    if balance and meter.status in {"ok", "unconfirmed"}:
        detail += f"; {balance.left / days:.2f} {balance.unit}/day"
    if approximate or meter.status == "unconfirmed":
        detail += " (approx/unconfirmed)"
    return detail


def screen(policy_path: Path | None = None, *, redact: bool = False) -> str:
    now = datetime.now(UTC)
    rows = []
    try:
        policy = selector.read_policy(policy_path)
    except (OSError, ValueError, KeyError, TypeError):
        policy = None
        rows.append(["policy", "NOT CHECKED", "unknown", "unknown", "unknown", "unknown", "unknown",
                     'jq -e . "${XDG_CONFIG_HOME:-$HOME/.config}/learn-ukrainian/budget_pools.json"'])
    try:
        sources = selector.budget_sources(selector.read_budget(), now)
    except Exception:
        sources = {}
    from scripts.dispatcher.store import list_tasks

    records = list_tasks(include_archive=True)
    counts, history = shadow_history(now, {p.key: p.source for p in policy.pools} if policy else {}, records)
    meters = selector.apply_exhaustion(selector.pool_meters(policy, sources),
                                        policy, records, now) if policy else {}
    entries = [(p.key, p.source, p) for p in policy.pools] if policy else []
    mapped = {source for _, source, _ in entries}
    entries.extend((source, source, None) for source in sources if source not in mapped)
    for label, source, pool in sorted(entries, key=lambda entry: entry[0]):
        meter = meters.get(pool.key) if pool else sources.get(source)
        meter = meter or selector.Meter(None, ())
        if redact:
            label = f"pool-{len(rows) + 1}"
        left = ", ".join(f"{w.name}:{w.left:g}{w.unit}" for w in meter.windows if w.left is not None)
        if redact and left:
            left = "[redacted]"
        if meter.status == "unconfirmed":
            left = f"NOT CHECKED (unconfirmed: {left or 'unknown'})"
        elif meter.status != "ok":
            left = "NOT CHECKED"
        if meter.status == "pool_exhausted":
            left = "POOL EXHAUSTED"
        if (pool and (pool.held or pool.kind == "held")) or source.endswith(":held"):
            left = "HELD " + left
        max_age = policy.max_age_s if policy else 720
        if meter.observed_at and not 0 <= (now - meter.observed_at).total_seconds() < max_age:
            left = "STALE " + left
        deadline = ", ".join(f"{w.name}:{w.ends_at.isoformat()}" for w in meter.windows if w.ends_at) or "unknown"
        if deadline == "unknown" and pool and pool.expires_at:
            deadline = f"{pool.expires_at} (unconfirmed time)"
        age = f"{(now - meter.observed_at).total_seconds():.0f}s" if meter.observed_at else "unknown"
        samples = history.get(pool.key, {}) if pool else {}
        earlier = [t for t in samples if meter.observed_at and t < meter.observed_at]
        previous = samples[max(earlier)] if earlier else None
        pace = burn_pace(meter, previous)
        provider = source.split(":", 1)[0]
        check = ""
        if not left or any(status in left for status in ("NOT CHECKED", "STALE", "POOL EXHAUSTED")):
            check = (pool.check_command if pool else "") or (
                f"codexbar usage --provider {shlex.quote(provider)} --format json --no-color")
            if provider == "private" and not (pool and pool.check_command):
                check = ('jq -e ".pools[] | select(.operator_reading_confirmed == true)" '
                         '"${XDG_CONFIG_HOME:-$HOME/.config}/learn-ukrainian/budget_pools.json"')
            if redact and pool and pool.check_command:
                check = "[private check command]"
        needed = needed_pace(pool, meter, now)
        if redact and ";" in needed:
            needed = needed.split(";", 1)[0] + "; [redacted]"
        rows.append([label, left or "NOT CHECKED", deadline, age, pace, needed,
                     str(counts[pool.key]) if pool else "unmapped", check])
    if not sources:
        rows.append(["meters", "NOT CHECKED", "unknown", "unknown", "unknown", "unknown", "unknown",
                     'curl --fail "$MONITOR_URL/api/state/routing-budget"'])
    headings = ["pool", "left", "reset or expiry", "observation age", "burn pace", "days left / needed pace",
                "shadow choices 24h", "check command"]
    widths = [max(len(row[i]) for row in [headings, *rows]) for i in range(len(headings))]
    return "\n".join(" | ".join(value.ljust(width) for value, width in zip(row, widths, strict=True)).rstrip()
                     for row in [headings, *rows])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Print one funding table from existing cached meters and shadow task records.\n"
                    "Use for budget inspection; this command never refreshes meters or changes dispatch.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/ops/budget_screen.py\n"
               "  .venv/bin/python scripts/ops/budget_screen.py --redact\n"
               "Outputs: one table on stdout; no files, provider calls or state changes.\n"
               "Exit codes: 0 table printed, 2 invalid arguments. Missing inputs appear as NOT CHECKED.\n"
               "Related: scripts/dispatcher/pool_selector.py describes the private policy schema.",
    )
    parser.add_argument("--config", type=Path, default=None,
                        help="Private policy JSON, e.g. ./private-policy.json (default: host budget_pools.json)")
    parser.add_argument("--redact", action="store_true", help="Hide pool labels and balances (default: off)")
    args = parser.parse_args(argv)
    print(screen(args.config, redact=args.redact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
