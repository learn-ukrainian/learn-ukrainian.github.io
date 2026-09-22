"""Lesson immersion band and structural minimums computation (issue #8414).

Computes the lesson immersion band for a given track, position, lesson number,
and cumulative vocabulary count.
- A1: derives band from cumulative_vocabulary using config.compute_immersion_band (source: ulp_vocab).
  Fails closed when USE_ULP_IMMERSION_DERIVATION is False (ulp_derivation_disabled).
  Requires cumulative_core_count (fails with cumulative_core_count_missing if None).
- A2, B1, B2: reads ArcPosition.band_key from load_arc (source: arc_table) and looks up
  via config._find_immersion_band_by_key. A level whose arc has no band_key fails with
  arc_band_table_missing, never falling back to module numbers.
- module_structural carries min_uk_dialogue_lines, min_uk_example_sentences, min_vocab_entries unchanged.
- not_checked always contains lesson_structural_minimums_not_calibrated.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from scripts import config
from scripts.curriculum.arc.loader import ArcPosition, load_arc

from . import codes

REPO_ROOT = Path(__file__).resolve().parents[3]


class ImmersionError(Exception):
    """Failure outcome in immersion band computation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class LessonBand:
    """Immersion band and structural targets for a lesson position."""

    band_key: str
    advisory_uk_share: tuple[int, int]
    module_structural: dict[str, int]
    source: Literal["ulp_vocab", "arc_table"]
    not_checked: list[str]
    waiver: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Machine-readable dictionary representation."""
        result: dict[str, Any] = {
            "band_key": self.band_key,
            "advisory_uk_share": list(self.advisory_uk_share),
            "module_structural": self.module_structural,
            "source": self.source,
            "not_checked": self.not_checked,
        }
        if self.waiver:
            result["waiver"] = self.waiver
        return result

    def render_text(self) -> str:
        """Human-readable text output."""
        lines = [
            f"Immersion band: {self.band_key}",
            f"Advisory Ukrainian share: {self.advisory_uk_share[0]}-{self.advisory_uk_share[1]}%",
            "Module structural minimums (uncalibrated per-lesson):",
            f"  min_uk_dialogue_lines: {self.module_structural['min_uk_dialogue_lines']}",
            f"  min_uk_example_sentences: {self.module_structural['min_uk_example_sentences']}",
            f"  min_vocab_entries: {self.module_structural['min_vocab_entries']}",
            f"Source: {self.source}",
        ]
        if self.waiver:
            lines.append(f"Waiver: {self.waiver}")
        if self.not_checked:
            lines.append(f"Not checked: {', '.join(self.not_checked)}")
        return "\n".join(lines)


def compute_lesson_immersion_band(
    track: str,
    arc_position: int,
    lesson_n: int,
    cumulative_core_count: int | None = None,
    *,
    waiver: str | None = None,
    arc_loader: Callable[[str], list[ArcPosition]] | None = None,
    arc_path: Path | None = None,
    doc_path: Path | None = None,
) -> LessonBand:
    """Compute the lesson immersion band and structural minimums.

    For A1, uses config.compute_immersion_band with the seven ULP knees.
    For A2, B1, B2, reads ArcPosition.band_key from load_arc and looks up via
    config._find_immersion_band_by_key. An unknown band_key or missing band_key
    fails with arc_band_table_missing, never falling back to top band or module numbers.
    """
    track_key = track.lower().split("-")[0] if "-" in track else track.lower()

    if track_key == "a1":
        if not config.USE_ULP_IMMERSION_DERIVATION:
            raise ImmersionError(
                codes.ULP_DERIVATION_DISABLED,
                "USE_ULP_IMMERSION_DERIVATION is False; refusing to derive A1 immersion band without derivation",
            )
        if cumulative_core_count is None:
            raise ImmersionError(
                codes.CUMULATIVE_CORE_COUNT_MISSING,
                "cumulative_core_count is required for A1 immersion band computation",
            )
        band = config.compute_immersion_band(
            "a1",
            arc_position,
            {"cumulative_vocabulary": cumulative_core_count},
        )
        band_key = str(band["key"])
        source: Literal["ulp_vocab", "arc_table"] = "ulp_vocab"
    else:
        # Load arc
        if arc_loader is not None:
            positions = arc_loader(track)
        else:
            try:
                positions = load_arc(track, arc_path=arc_path, doc_path=doc_path)
            except Exception as err:
                raise ImmersionError(
                    codes.ARC_BAND_TABLE_MISSING,
                    f"failed loading arc for track {track!r}: {err}",
                ) from err

        pos_record = next((p for p in positions if p.position == arc_position), None)
        if pos_record is None:
            raise ImmersionError(
                codes.POSITION_NOT_FOUND,
                f"position {arc_position} not found in arc for {track}",
            )
        if not pos_record.band_key:
            raise ImmersionError(
                codes.ARC_BAND_TABLE_MISSING,
                f"arc position {arc_position} in {track} has no band_key; never falling back to module numbers",
            )
        band_key = pos_record.band_key

        family = config._immersion_track_key(track)
        family_bands = config.IMMERSION_POLICIES.get(family, ())
        default_bands = config.IMMERSION_POLICIES.get("default", ())
        known_keys = {b["key"] for b in family_bands} | {b["key"] for b in default_bands}
        if band_key not in known_keys:
            raise ImmersionError(
                codes.ARC_BAND_TABLE_MISSING,
                f"unknown band_key {band_key!r} for track {track!r} not found in immersion policies; "
                "refusing to fall through to top band",
            )

        band = config._find_immersion_band_by_key(track, band_key)
        if band.get("key") != band_key:
            raise ImmersionError(
                codes.ARC_BAND_TABLE_MISSING,
                f"unknown band_key {band_key!r} for track {track!r} not found in immersion policies; "
                "refusing to fall through to top band",
            )
        source = "arc_table"

    advisory_uk_share = (int(band["advisory_pct_min"]), int(band["advisory_pct_max"]))
    module_structural = {
        "min_uk_dialogue_lines": int(band["min_uk_dialogue_lines"]),
        "min_uk_example_sentences": int(band["min_uk_example_sentences"]),
        "min_vocab_entries": int(band["min_vocab_entries"]),
    }

    return LessonBand(
        band_key=band_key,
        advisory_uk_share=advisory_uk_share,
        module_structural=module_structural,
        source=source,
        not_checked=[codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED],
        waiver=waiver,
    )
