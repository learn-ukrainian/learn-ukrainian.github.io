"""Auto-sized M cap formula for /goal runs (#1933 item 4).

Picking ``M=30`` up-front was a guess that needed to be bumped to 40,
then 50, then 60 on the 2026-05-14 V7 MDX run. The rule says "don't
inflate counters" but never gave a sizing heuristic, leaving operators
to either over-pick (wasting the abort threshold) or under-pick (the
goal aborts mid-work).

Formula
-------

::

    M = clamp(15, queue_depth * 2 + 5 + async_waits, 200)

Rationale:

* **2 turns per queue item** — one to advance, one to verify. Anything
  tighter loses the verification turn and we re-learn the lesson from
  bug autopsies #M-4 "deterministic over hallucination."
* **+5 buffer** — covers per-run setup, the final GOAL_DONE turn, and
  one or two retry turns when a verification fails the first time.
* **+1 per async wait** — one extra turn budget per expected
  out-of-band signal (CI pass, dispatch land, PR merge). Defaults to
  zero; the operator names a number when they know the goal will
  suspend that many times.
* **floor 15** — under 15 the M counter stops being informative;
  predicate-decrementing work that small should ship without /goal.
* **ceiling 200** — anything more is a planning failure that should
  split into multiple goals, not a single mega-goal.

For long-running async-heavy goals the operator can pass
``dynamic=True`` (or ``--dynamic`` on the CLI). The cap returns a
sentinel ``None`` meaning unbounded — the predicate is the sole
termination condition, not turn count. Use ``GOAL_WAIT`` for the
suspend points.

CLI
---

::

    python -m scripts.goal_driver.size_cap --queue-depth 8 --async-waits 2
    # → 26

    python -m scripts.goal_driver.size_cap --dynamic
    # → infinity
"""

from __future__ import annotations

import argparse
import sys

M_FLOOR = 15
M_CEILING = 200
TURNS_PER_ITEM = 2
BUFFER_TURNS = 5
DYNAMIC_SENTINEL = "infinity"


def compute_m(
    queue_depth: int,
    async_waits: int = 0,
    dynamic: bool = False,
) -> int | None:
    """Return the recommended M cap, or ``None`` for the dynamic-unbounded case.

    Raises ``ValueError`` for negative inputs — both ``queue_depth`` and
    ``async_waits`` must be non-negative integers.
    """
    if queue_depth < 0:
        raise ValueError(f"queue_depth must be non-negative, got {queue_depth}")
    if async_waits < 0:
        raise ValueError(f"async_waits must be non-negative, got {async_waits}")

    if dynamic:
        return None

    raw = queue_depth * TURNS_PER_ITEM + BUFFER_TURNS + async_waits
    return max(M_FLOOR, min(M_CEILING, raw))


def format_m(value: int | None) -> str:
    """Format the result for CLI output."""
    return DYNAMIC_SENTINEL if value is None else str(value)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts.goal_driver.size_cap",
        description="Compute the M cap for a /goal run from queue depth + async waits.",
    )
    parser.add_argument(
        "--queue-depth",
        type=int,
        default=0,
        help="Number of items the goal needs to handle. Required unless --dynamic.",
    )
    parser.add_argument(
        "--async-waits",
        type=int,
        default=0,
        help="Number of expected GOAL_WAIT suspensions during the run. Default: 0.",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Return 'infinity' for goals where predicate is the sole termination signal.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        value = compute_m(
            queue_depth=args.queue_depth,
            async_waits=args.async_waits,
            dynamic=args.dynamic,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(format_m(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
