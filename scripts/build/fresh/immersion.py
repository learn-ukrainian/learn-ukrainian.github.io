"""Lesson immersion payload computation (#8414, #8431 §7).

Reads compute_lesson_immersion_band and returns the structured immersion payload:
- advisory Ukrainian share (min %, max %)
- structural minimums / targets
- permitted languages per field role:
  narration, dialogue_line, activity_instruction, activity_item, gloss, quote, resource_line
- source and not_checked tracking

Both the writer's prompt and E3's gate consume this single function.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.curriculum.learner_state.immersion import LessonBand, compute_lesson_immersion_band

FIELD_ROLES: tuple[str, ...] = (
    "narration",
    "dialogue_line",
    "activity_instruction",
    "activity_item",
    "gloss",
    "quote",
    "resource_line",
)


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
    level: str,
    band_key: str,
    arc_position: int,
) -> dict[str, tuple[str, ...]]:
    """Determine permitted languages per field role based on level, band, and position."""
    lvl = level.lower().split("-")[0] if "-" in level else level.lower()

    # Quote and dialogue lines are always Ukrainian only; gloss is English.
    base: dict[str, tuple[str, ...]] = {
        "dialogue_line": ("uk",),
        "quote": ("uk",),
        "gloss": ("en",),
        "resource_line": ("en", "uk"),
    }

    if lvl in ("b1", "b2") or band_key.startswith(("b1", "b2")):
        # B1+ onward is full immersion
        base["narration"] = ("uk",)
        base["activity_instruction"] = ("uk",)
        base["activity_item"] = ("uk",)
    elif lvl == "a2" or band_key.startswith("a2"):
        if band_key == "a2-bridge":
            base["narration"] = ("uk", "en")
            base["activity_instruction"] = ("uk", "en")
            base["activity_item"] = ("uk",)
        else:
            base["narration"] = ("uk",)
            base["activity_instruction"] = ("uk",)
            base["activity_item"] = ("uk",)
    else:
        # A1 band: English scaffolding early, Ukrainian-primary later
        if arc_position >= 41 or band_key in ("a1-m35-54", "a1-m55+"):
            base["narration"] = ("en", "uk")
            base["activity_instruction"] = ("en", "uk")
            base["activity_item"] = ("uk", "en")
        else:
            base["narration"] = ("en",)
            base["activity_instruction"] = ("en",)
            base["activity_item"] = ("uk", "en")

    return {role: base[role] for role in FIELD_ROLES}


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
) -> ImmersionPayload:
    """Compute the lesson immersion payload (#8431 §7).

    One function consumes compute_lesson_immersion_band and returns the payload:
    - permitted languages per field role
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
        level=track,
        band_key=lesson_band.band_key,
        arc_position=arc_position,
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
