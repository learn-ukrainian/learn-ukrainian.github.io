"""Chunk-level quality gates for school textbook extraction."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

DEFAULT_SYMBOL_NOISE_THRESHOLD = 0.25
SYMBOL_NOISE_WARNING_DROP_RATIO = 0.30

_UKRAINIAN_CYRILLIC_LETTERS = set(
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
)
_COMMON_PUNCTUATION = set(".,;:!?()-—«»\"'")


@dataclass(frozen=True)
class NoiseGateStats:
    """Per-book symbol-noise gate counters."""

    source_file: str
    chunks_kept: int
    chunks_dropped_noise: int

    @property
    def drop_ratio(self) -> float:
        total = self.chunks_kept + self.chunks_dropped_noise
        if total == 0:
            return 0.0
        return self.chunks_dropped_noise / total

    def manifest_record(self) -> dict[str, object]:
        return {
            "source_file": self.source_file,
            "chunks_kept": self.chunks_kept,
            "chunks_dropped_noise": self.chunks_dropped_noise,
            "drop_ratio": round(self.drop_ratio, 3),
        }


def _is_allowed_symbol_noise_char(ch: str) -> bool:
    return (
        ch in _UKRAINIAN_CYRILLIC_LETTERS
        or "A" <= ch <= "Z"
        or "a" <= ch <= "z"
        or "0" <= ch <= "9"
        or ch.isspace()
        or ch in _COMMON_PUNCTUATION
    )


def symbol_noise_density(text: str) -> float:
    """Return the fraction of characters outside the textbook prose allowlist."""
    if not text:
        return 0.0
    noisy = sum(1 for ch in text if not _is_allowed_symbol_noise_char(ch))
    return noisy / len(text)


def _validate_symbol_noise_threshold(threshold: float) -> float:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("symbol-noise threshold must be between 0.0 and 1.0")
    return threshold


def should_drop_for_symbol_noise(
    text: str,
    *,
    threshold: float = DEFAULT_SYMBOL_NOISE_THRESHOLD,
) -> bool:
    """Return True when a chunk's symbol noise strictly exceeds the threshold."""
    threshold = _validate_symbol_noise_threshold(threshold)
    return symbol_noise_density(text) > threshold


def apply_symbol_noise_gate(
    chunks: Iterable[dict[str, Any]],
    *,
    source_file: str,
    threshold: float = DEFAULT_SYMBOL_NOISE_THRESHOLD,
    warn: Callable[[str], None] | None = print,
) -> tuple[list[dict[str, Any]], NoiseGateStats]:
    """Drop noisy chunks and return kept chunks plus per-book counters."""
    threshold = _validate_symbol_noise_threshold(threshold)
    kept = []
    dropped = 0

    for chunk in chunks:
        if should_drop_for_symbol_noise(str(chunk.get("text", "")), threshold=threshold):
            dropped += 1
        else:
            kept.append(chunk)

    stats = NoiseGateStats(
        source_file=source_file,
        chunks_kept=len(kept),
        chunks_dropped_noise=dropped,
    )
    if warn is not None and stats.drop_ratio > SYMBOL_NOISE_WARNING_DROP_RATIO:
        warn(
            "WARNING: SYMBOL-NOISE gate dropped "
            f"{stats.chunks_dropped_noise}/"
            f"{stats.chunks_kept + stats.chunks_dropped_noise} chunks "
            f"({stats.drop_ratio:.1%}) for {source_file}; "
            "book likely needs layout-aware re-extraction."
        )
    return kept, stats
