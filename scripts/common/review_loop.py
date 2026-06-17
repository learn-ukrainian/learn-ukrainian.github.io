"""Shared helpers for bounded dimensional review loops."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


def _entry_value(entry: Any, key: str, default: Any = None) -> Any:
    if isinstance(entry, Mapping):
        return entry.get(key, default)
    return getattr(entry, key, default)


def aggregate_min(dim_results: Mapping[str, Any]) -> tuple[float, str | None]:
    """Return ``(min_score, min_dim)`` across one review round.

    Entries may be dataclass-like objects with ``score`` / ``verdict``
    attributes or plain mappings with those keys. A reviewer ``ERROR`` counts
    as score ``0.0`` so failed review calls cannot mask as a passing round.
    """
    if not dim_results:
        return 0.0, None
    min_score = float("inf")
    min_dim: str | None = None
    for dim, entry in dim_results.items():
        verdict = str(_entry_value(entry, "verdict", "") or "").upper()
        raw_score = 0.0 if verdict == "ERROR" else _entry_value(entry, "score", 0.0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0
        if score < min_score:
            min_score = score
            min_dim = dim
    if min_score == float("inf"):
        return 0.0, None
    return min_score, min_dim


def min_score_regressed(
    prev: Mapping[str, Any],
    curr: Mapping[str, Any],
    *,
    tolerance: float = 0.0,
) -> bool:
    """True iff the aggregate MIN score dropped beyond tolerance."""
    prev_min, _ = aggregate_min(prev)
    curr_min, _ = aggregate_min(curr)
    return (prev_min - curr_min) > float(tolerance)


def best_round_index(
    rounds: Sequence[Any],
    dim_results_for_round: Callable[[Any], Mapping[str, Any]],
) -> int:
    """Pick the earliest round with the highest aggregate MIN score."""
    if not rounds:
        raise ValueError("best_round_index requires at least one round")
    return max(
        range(len(rounds)),
        key=lambda i: (aggregate_min(dim_results_for_round(rounds[i]))[0], -i),
    )
