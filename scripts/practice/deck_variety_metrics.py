#!/usr/bin/env python3
"""Deck variety metrics for the practice gate (#5376 check 5).

Build-time (non-playwright) guard that turns "the deck feels samey" into
numbers. Reads the hydrated practice deck shards (``practice-index.<LEVEL>.json``)
and reports, per level:

- exercise-type mix: distinct modes offered, mean modes per item, and the
  share of items that offer only a single exercise type;
- pool size per type: items offering each mode (a focused session draws from
  exactly this pool);
- per-session repetition rate: for a focused session of size S over a mode
  pool P, ``max(0, S - P) / S`` — the share of the session that MUST be
  repeats when the pool cannot fill it;
- simulated mixed-session type diversity: seeded deterministic sessions of
  size S drawn without replacement, one random offered mode per card.

Thresholds (warn vs fail) are constants below; the gate exits 1 on any FAIL.
Zero-pool modes are reported but not penalized: modes with no authored
content are honestly disabled in the UI (e.g. cloze before #3797), which is a
product state, not a variety regression.

No network, stdlib only.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INDEX_RE = re.compile(r"^practice-index\.(?P<level>[A-C][12])\.json$")
DEFAULT_PRACTICE_DIR = ROOT / "site" / "public" / "lexicon"

# Fixed seed: simulations are deterministic so CI results are reproducible.
SIM_SEED = 20260717
SIM_SESSIONS = 200

# --- Thresholds (tune deliberately; each has a justification) ---------------
# A level with fewer than 3 distinct exercise types is a "samey" deck by
# definition — one or two activity shapes repeated.
FAIL_MIN_DISTINCT_MODES = 3
# If most items can only be practiced one way, mixed sessions cannot vary.
FAIL_MAX_SINGLE_MODE_SHARE = 0.50
# A mode pool of exactly 1 means every focused session is the same card.
# (Pool 0 = mode honestly disabled; reported, not penalized.)
FAIL_MIN_NONZERO_MODE_POOL = 2
# Simulated mixed sessions should routinely show at least 3 distinct types.
FAIL_MIN_SESSION_TYPE_DIVERSITY = 3.0
# Warn when a non-empty mode pool cannot fill one focused session without
# repeats, and when mixed-session diversity dips below 5 types.
WARN_MIN_MODE_POOL_VS_SESSION = True
WARN_MIN_SESSION_TYPE_DIVERSITY = 5.0


def load_index(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data.get("items"), list):
        raise ValueError(f"{path.name}: missing items list")
    return data


def simulate_mixed_diversity(items: list[dict[str, Any]], session_size: int) -> float:
    """Mean distinct exercise types across seeded mixed sessions."""
    pool = [item for item in items if item.get("modes")]
    if not pool:
        return 0.0
    rng = random.Random(SIM_SEED)
    draws = min(session_size, len(pool))
    total = 0
    for _ in range(SIM_SESSIONS):
        session_items = rng.sample(pool, draws)
        types = {rng.choice(item["modes"]) for item in session_items}
        total += len(types)
    return total / SIM_SESSIONS


def evaluate_level(level: str, items: list[dict[str, Any]], session_size: int) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []

    if not items:
        return {
            "level": level,
            "items": 0,
            "failures": [f"{level}: deck has 0 items"],
            "warnings": [],
        }

    mode_pools: Counter[str] = Counter()
    single_mode = 0
    modes_per_item: list[int] = []
    for item in items:
        modes = list(item.get("modes") or [])
        modes_per_item.append(len(modes))
        if len(modes) == 1:
            single_mode += 1
        for mode in set(modes):
            mode_pools[mode] += 1

    distinct_modes = len(mode_pools)
    single_mode_share = single_mode / len(items)
    mean_modes = sum(modes_per_item) / len(modes_per_item)
    diversity = simulate_mixed_diversity(items, session_size)

    if distinct_modes < FAIL_MIN_DISTINCT_MODES:
        failures.append(
            f"{level}: only {distinct_modes} distinct exercise types "
            f"(fail floor {FAIL_MIN_DISTINCT_MODES})"
        )
    if single_mode_share > FAIL_MAX_SINGLE_MODE_SHARE:
        failures.append(
            f"{level}: {single_mode_share:.0%} of items offer exactly one exercise type "
            f"(fail ceiling {FAIL_MAX_SINGLE_MODE_SHARE:.0%})"
        )
    if diversity < FAIL_MIN_SESSION_TYPE_DIVERSITY:
        failures.append(
            f"{level}: simulated {session_size}-card mixed sessions average "
            f"{diversity:.2f} distinct types (fail floor {FAIL_MIN_SESSION_TYPE_DIVERSITY})"
        )
    elif diversity < WARN_MIN_SESSION_TYPE_DIVERSITY:
        warnings.append(
            f"{level}: simulated {session_size}-card mixed sessions average "
            f"{diversity:.2f} distinct types (warn floor {WARN_MIN_SESSION_TYPE_DIVERSITY})"
        )

    repetition: dict[str, float] = {}
    for mode, pool_size in sorted(mode_pools.items()):
        repetition[mode] = round(max(0, session_size - pool_size) / session_size, 3)
        if pool_size < FAIL_MIN_NONZERO_MODE_POOL:
            failures.append(
                f"{level}: mode '{mode}' pool is {pool_size} — every focused session "
                f"is the same card (fail floor {FAIL_MIN_NONZERO_MODE_POOL})"
            )
        elif WARN_MIN_MODE_POOL_VS_SESSION and pool_size < session_size:
            warnings.append(
                f"{level}: mode '{mode}' pool {pool_size} < session size {session_size} — "
                f"a focused session is {repetition[mode]:.0%} repeats"
            )

    return {
        "level": level,
        "items": len(items),
        "distinctModes": distinct_modes,
        "meanModesPerItem": round(mean_modes, 2),
        "singleModeShare": round(single_mode_share, 3),
        "modePools": dict(sorted(mode_pools.items())),
        "focusedSessionRepetition": repetition,
        "mixedSessionTypeDiversity": round(diversity, 2),
        "failures": failures,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--practice-dir",
        type=Path,
        default=DEFAULT_PRACTICE_DIR,
        help="Directory holding practice-index.<LEVEL>.json shards (default: %(default)s)",
    )
    parser.add_argument("--session-size", type=int, default=10, help="Session size S (default: 10)")
    parser.add_argument("--json", type=Path, default=None, help="Optional JSON report output path")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote warnings to failures",
    )
    args = parser.parse_args(argv)

    index_files = sorted(
        p for p in args.practice_dir.glob("practice-index.*.json") if INDEX_RE.match(p.name)
    )
    if not index_files:
        print(f"FAIL: no practice-index.<LEVEL>.json shards in {args.practice_dir}")
        return 1

    reports = []
    for path in index_files:
        data = load_index(path)
        level = str(data.get("level") or INDEX_RE.match(path.name).group("level"))  # type: ignore[union-attr]
        reports.append(evaluate_level(level, data["items"], args.session_size))

    total_failures = 0
    total_warnings = 0
    for report in reports:
        failures = report["failures"]
        warnings = report["warnings"]
        if args.strict:
            failures = failures + warnings
            warnings = []
        total_failures += len(failures)
        total_warnings += len(warnings)
        status = "FAIL" if failures else ("WARN" if warnings else "OK")
        print(f"[{status}] {report['level']}: items={report.get('items')} "
              f"distinctModes={report.get('distinctModes')} "
              f"meanModesPerItem={report.get('meanModesPerItem')} "
              f"singleModeShare={report.get('singleModeShare')} "
              f"mixedSessionTypeDiversity={report.get('mixedSessionTypeDiversity')}")
        for mode, pool in (report.get("modePools") or {}).items():
            rep = report["focusedSessionRepetition"][mode]
            print(f"       pool {mode}: {pool} (focused-session repetition {rep:.0%})")
        for warning in warnings:
            print(f"       warn: {warning}")
        for failure in failures:
            print(f"       FAIL: {failure}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps({"sessionSize": args.session_size, "levels": reports}, indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

    print(
        f"deck variety: {len(reports)} levels, {total_failures} failures, {total_warnings} warnings"
    )
    return 1 if total_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
