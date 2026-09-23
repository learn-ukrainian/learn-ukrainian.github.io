"""Lesson immersion payload computation (#8414, #8431 r3 §6/§7).

Reads compute_lesson_immersion_band and returns the structured immersion payload:
- advisory Ukrainian share (min %, max %)
- structural minimums / targets
- permitted languages per field role:
  narration, dialogue_line, activity_instruction, activity_item, gloss, quote, resource_line
- source and not_checked tracking

Permitted languages are loaded strictly from the data table (immersion_table.yaml)
which cites writer contract #8431 r3 §6/§7 per row. Where the contract gives no row,
computation fails closed with 'unsupported_immersion_band'.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.learner_state.immersion import (
    ImmersionError,
    LessonBand,
    compute_lesson_immersion_band,
)

FIELD_ROLES: tuple[str, ...] = (
    "narration",
    "dialogue_line",
    "activity_instruction",
    "activity_item",
    "gloss",
    "quote",
    "resource_line",
)

IMMERSION_TABLE_PATH = Path(__file__).parent / "immersion_table.yaml"


def load_immersion_table(table_path: Path | None = None) -> dict[str, Any]:
    """Load the permitted languages table citing writer contract #8431 r3 §6/§7."""
    path = table_path or IMMERSION_TABLE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Immersion table file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Immersion table at {path} must be a dictionary keyed by band.")
    return data


_CACHED_IMMERSION_TABLE: dict[str, Any] | None = None


def get_immersion_table() -> dict[str, Any]:
    global _CACHED_IMMERSION_TABLE
    if _CACHED_IMMERSION_TABLE is None:
        _CACHED_IMMERSION_TABLE = load_immersion_table()
    return _CACHED_IMMERSION_TABLE


@dataclass(frozen=True)
class ImmersionPayload:
    """Deterministic immersion payload for a lesson position (#8431 §7)."""

    band_key: str
    advisory_uk_share: tuple[int, int]
    structural_targets: dict[str, int]
    permitted_languages: dict[str, tuple[str, ...]]
    source: str
    not_checked: list[str]
    waiver: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Machine-readable dictionary representation."""
        result: dict[str, Any] = {
            "band_key": self.band_key,
            "advisory_uk_share": list(self.advisory_uk_share),
            "structural_targets": dict(self.structural_targets),
            "permitted_languages": {k: list(v) for k, v in self.permitted_languages.items()},
            "source": self.source,
            "not_checked": list(self.not_checked),
        }
        if self.waiver:
            result["waiver"] = self.waiver
        return result


def _permitted_languages_for_band(
    band_key: str,
    *,
    table: dict[str, Any] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Look up permitted languages per field role in the contract-sourced immersion table.

    Fails closed if the band key has no row in the contract table (#8431 §6/§7).
    """
    tbl = table if table is not None else get_immersion_table()
    if band_key not in tbl:
        raise ImmersionError(
            "unsupported_immersion_band",
            f"immersion band {band_key!r} has no row in contract immersion table",
        )

    row = tbl[band_key]
    roles = row.get("roles", {})
    return {role: tuple(roles.get(role, ())) for role in FIELD_ROLES}


def compute_immersion_payload(
    track: str,
    arc_position: int,
    lesson_n: int,
    cumulative_core_count: int | None = None,
    *,
    waiver: str | None = None,
    arc_loader: Any = None,
    arc_path: Path | None = None,
    doc_path: Path | None = None,
    lesson_band: LessonBand | None = None,
    immersion_table: dict[str, Any] | None = None,
) -> ImmersionPayload:
    """Compute the lesson immersion payload (#8431 §7).

    One function consumes compute_lesson_immersion_band and returns the payload:
    - permitted languages per field role (sourced from immersion_table.yaml)
    - structural targets (dialogue lines, example sentences, vocab entries)
    - advisory Ukrainian share
    """
    if lesson_band is None:
        lesson_band = compute_lesson_immersion_band(
            track=track,
            arc_position=arc_position,
            lesson_n=lesson_n,
            cumulative_core_count=cumulative_core_count,
            waiver=waiver,
            arc_loader=arc_loader,
            arc_path=arc_path,
            doc_path=doc_path,
        )

    permitted = _permitted_languages_for_band(
        band_key=lesson_band.band_key,
        table=immersion_table,
    )

    return ImmersionPayload(
        band_key=lesson_band.band_key,
        advisory_uk_share=lesson_band.advisory_uk_share,
        structural_targets=dict(lesson_band.module_structural),
        permitted_languages=permitted,
        source=lesson_band.source,
        not_checked=list(lesson_band.not_checked),
        waiver=lesson_band.waiver,
    )
