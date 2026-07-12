#!/usr/bin/env python3
"""Measure dossier-led module size policy signals without enforcing gates.

This command is deliberately advisory. It reports how a plan's current
``word_target`` relates to the available research/evidence packet so #4801 can
be calibrated before any prompt, config, or audit gate starts changing behavior.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
RESEARCH_ROOT = PROJECT_ROOT / "docs" / "research"

SEMINAR_TRACKS = {
    "bio",
    "folk",
    "hist",
    "history",
    "istorio",
    "lit",
    "lit-crimea",
    "lit-doc",
    "lit-drama",
    "lit-fantastika",
    "lit-hist-fic",
    "lit-humor",
    "lit-war",
    "lit-youth",
    "oes",
    "ruth",
}
CORE_RESEARCH_TRACKS = {"c1", "c2"}

MODULE_SIZE_BANDS: dict[str, tuple[int, int | None]] = {
    "sparse": (3800, 5000),
    "normal": (5000, 6500),
    "dense": (6500, 8000),
    "exceptional": (8000, None),
}

_URL_RE = re.compile(r"https?://[^\s)>\"]+")
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_WORD_RE = re.compile(r"\S+")
_CHUNK_ID_RE = re.compile(
    r"\b(?:[0-9a-f]{8}_c\d{4}|[a-z0-9-]+_s\d{4}|wikipedia:[^\s`]+:chunk_\d+)\b",
    re.IGNORECASE,
)
_SOURCE_SIGNAL_RE = re.compile(
    r"(?:"
    r"verify_quote|search_literary|search_sources|search_grinchenko|search_heritage|"
    r"Джерельна опора|Джерельний статус|Основні опори|Raw evidence|Raw verify|"
    r"Named recording|edition-like references|Source-disagreement|"
    r"Українська літературна енциклопедія|Енциклопедія українознавства|"
    r"Енциклопедія Сучасної України|Історія української культури|"
    r"Грушевськ|Крип'якевич|Заболотн|Авраменк|Антонович|Колесс|Грінченк"
    r")",
    re.IGNORECASE,
)
_PRIMARY_MARKERS_RE = re.compile(
    r"\b(?:primary|quote|verbatim|архів|архівн|першоджерел|цитат|вериф|корпус|"
    r"виданн|запис|рукопис)\w*",
    re.IGNORECASE,
)
_CONTESTED_MARKERS_RE = re.compile(
    r"\b(?:contested|debate|disagree|myth|decolon|дискус|супереч|міф|"
    r"деколон|колон|радянськ|імпер)\w*",
    re.IGNORECASE,
)
_VARIANT_MARKERS_RE = re.compile(
    r"\b(?:variant|ritual|performance|region|варіант|обряд|ритуал|"
    r"виконав|побутув|регіон|локаль)\w*",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DensityMetrics:
    words: int
    headings: int
    source_refs: int
    primary_markers: int
    contested_markers: int
    variant_markers: int


@dataclass(frozen=True)
class SizePolicyRecord:
    track: str
    slug: str
    basis: str
    plan_path: str
    dossier_path: str | None
    module_path: str | None
    plan_floor: int | None
    plan_outline_words: int | None
    actual_words: int | None
    density_band: str
    band_min: int | None
    band_max: int | None
    effective_min: int | None
    advisory_ceiling: int | None
    status: str
    notes: list[str]
    metrics: DensityMetrics | None


@dataclass(frozen=True)
class SizePolicyOverride:
    """A human-reviewed per-plan replacement for generic density-band limits."""

    floor_words: int
    recommended_min: int
    recommended_max: int
    ceiling_words: int
    basis: str
    saturation_evidence: str


def display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def word_count(path: Path) -> int:
    return len(_WORD_RE.findall(path.read_text(encoding="utf-8")))


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _sum_outline_words(items: Any) -> int | None:
    if not isinstance(items, list):
        return None
    total = 0
    seen = False
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get("words")
        if isinstance(value, int):
            total += value
            seen = True
        elif isinstance(value, str) and value.isdigit():
            total += int(value)
            seen = True
    return total if seen else None


def _source_ref_count(text: str) -> int:
    refs: set[str] = set()
    refs.update(match.group(0) for match in _URL_RE.finditer(text))
    refs.update(match.group(1) for match in _MD_LINK_RE.finditer(text))
    refs.update(match.group(0) for match in _CHUNK_ID_RE.finditer(text))
    for line_number, line in enumerate(text.splitlines(), 1):
        if _SOURCE_SIGNAL_RE.search(line):
            refs.add(f"source-line:{line_number}")
    return len(refs)


def dossier_metrics(path: Path) -> DensityMetrics:
    text = path.read_text(encoding="utf-8")
    return DensityMetrics(
        words=len(_WORD_RE.findall(text)),
        headings=len(_HEADING_RE.findall(text)),
        source_refs=_source_ref_count(text),
        primary_markers=len(_PRIMARY_MARKERS_RE.findall(text)),
        contested_markers=len(_CONTESTED_MARKERS_RE.findall(text)),
        variant_markers=len(_VARIANT_MARKERS_RE.findall(text)),
    )


def _track_profile(track: str) -> str:
    normalized = track.lower()
    if normalized == "folk":
        return "folk"
    if normalized == "bio":
        return "bio"
    if normalized in CORE_RESEARCH_TRACKS:
        return "core"
    return "seminar"


def classify_dossier(track: str, metrics: DensityMetrics) -> str:
    """Return an advisory source-density band normalized by track.

    The thresholds intentionally treat FOLK as dossier-heavy because its
    existing quality contract says thin dossiers usually mean insufficient
    corpus work, not a genuinely sparse topic.
    """
    profile = _track_profile(track)
    evidence_markers = (
        metrics.primary_markers + metrics.contested_markers + metrics.variant_markers
    )

    if profile == "folk":
        if metrics.words < 2500 or metrics.source_refs < 4 or evidence_markers < 6:
            return "sparse"
        if metrics.words >= 5500 and metrics.source_refs >= 8 and evidence_markers >= 14:
            return "dense"
        return "normal"

    if profile == "bio":
        if metrics.words < 1200 or metrics.source_refs < 2:
            return "sparse"
        if metrics.words >= 2600 and metrics.source_refs >= 8 and evidence_markers >= 8:
            return "dense"
        return "normal"

    if metrics.words < 2200 or metrics.source_refs < 3:
        return "sparse"
    if metrics.words >= 5200 and metrics.source_refs >= 8 and evidence_markers >= 10:
        return "dense"
    return "normal"


def classify_core_evidence(plan: dict[str, Any]) -> str:
    """Classify C1-C2 modules by plan/evidence pressure, not dossier size."""
    target = _as_int(plan.get("word_target"))
    outline_words = _sum_outline_words(plan.get("content_outline"))
    refs = plan.get("references")
    ref_count = len(refs) if isinstance(refs, list) else 0
    primary_sources = 0
    for section in plan.get("content_outline") or []:
        if isinstance(section, dict) and isinstance(section.get("primary_sources"), list):
            primary_sources += len(section["primary_sources"])

    if target and target >= 5000 and (ref_count >= 3 or primary_sources >= 2):
        return "core_research_extended"
    if outline_words and outline_words > 4500:
        return "core_research_extended"
    return "core_pedagogy_standard"


def band_limits(band: str) -> tuple[int | None, int | None]:
    if band == "core_research_extended":
        return 4500, 6500
    if band == "core_pedagogy_standard":
        return 3500, 5000
    low, high = MODULE_SIZE_BANDS[band]
    return low, high


def _as_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _is_positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_size_policy_override(plan: Mapping[str, Any]) -> list[str]:
    """Return deterministic schema errors for an explicit plan size override.

    An absent ``size_policy`` is intentionally valid: generic dossier/evidence
    bands remain the policy for legacy plans.  A present policy must be fully
    reviewed and self-contained before it can replace those bands.
    """
    if "size_policy" not in plan:
        return []

    policy = plan["size_policy"]
    if not isinstance(policy, Mapping):
        return ["size_policy must be a mapping."]

    errors: list[str] = []
    floor = policy.get("floor_words")
    recommended_range = policy.get("recommended_range")
    ceiling = policy.get("ceiling_words")

    if not _is_positive_integer(floor):
        errors.append("size_policy.floor_words must be a positive integer.")

    recommended_min: int | None = None
    recommended_max: int | None = None
    if (
        not isinstance(recommended_range, list)
        or len(recommended_range) != 2
        or not all(_is_positive_integer(value) for value in recommended_range)
    ):
        errors.append(
            "size_policy.recommended_range must be a two-item list of positive integers."
        )
    else:
        recommended_min, recommended_max = recommended_range
        if recommended_min > recommended_max:
            errors.append("size_policy.recommended_range must not be inverted.")
        if _is_positive_integer(floor) and recommended_min < floor:
            errors.append(
                "size_policy.recommended_range[0] must be at least size_policy.floor_words."
            )

    if not _is_positive_integer(ceiling):
        errors.append("size_policy.ceiling_words must be a positive integer.")
    else:
        if _is_positive_integer(floor) and ceiling < floor:
            errors.append(
                "size_policy.ceiling_words must be at least size_policy.floor_words."
            )
        if recommended_max is not None and ceiling < recommended_max:
            errors.append(
                "size_policy.ceiling_words must be at least size_policy.recommended_range[1]."
            )

    word_target = _as_int(plan.get("word_target"))
    if not _is_positive_integer(word_target):
        errors.append("size_policy requires word_target to be a positive integer.")
    elif _is_positive_integer(floor) and floor != word_target:
        errors.append(
            "size_policy.floor_words "
            f"({floor}) must equal word_target ({word_target})."
        )

    for field in ("basis", "saturation_evidence"):
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"size_policy.{field} must be a nonempty string.")

    if policy.get("exceptional_justification") != "required_above_ceiling":
        errors.append(
            "size_policy.exceptional_justification must be required_above_ceiling."
        )

    return errors


def explicit_size_policy_override(
    plan: Mapping[str, Any],
) -> tuple[SizePolicyOverride | None, list[str]]:
    """Return a parsed override or the actionable errors that reject it."""
    errors = validate_size_policy_override(plan)
    if errors or "size_policy" not in plan:
        return None, errors

    policy = plan["size_policy"]
    assert isinstance(policy, Mapping)
    recommended_range = policy["recommended_range"]
    assert isinstance(recommended_range, list)
    return (
        SizePolicyOverride(
            floor_words=policy["floor_words"],
            recommended_min=recommended_range[0],
            recommended_max=recommended_range[1],
            ceiling_words=policy["ceiling_words"],
            basis=policy["basis"].strip(),
            saturation_evidence=policy["saturation_evidence"].strip(),
        ),
        [],
    )


def build_explicit_size_policy_record(
    *,
    track: str,
    slug: str,
    plan_path: str,
    dossier_path: str | None,
    module_path: str | None,
    plan_floor: int | None,
    plan_outline_words: int | None,
    actual_words: int | None,
    metrics: DensityMetrics | None,
    override: SizePolicyOverride,
) -> SizePolicyRecord:
    """Build the effective record for a valid, reviewed plan override."""
    notes = [
        "A reviewed explicit plan size policy override replaces generic density-band limits.",
        f"Review basis: {override.basis}",
        f"Saturation evidence: {override.saturation_evidence}",
        (
            "Above the explicit advisory ceiling, exceptional justification is "
            "required."
        ),
    ]
    status = "explicit_override"
    if actual_words is not None:
        if actual_words < override.floor_words:
            status = "below_plan_floor"
            notes.append("Built module is below the current plan floor.")
        elif actual_words > override.ceiling_words:
            status = "exceptional_justification_required"
            notes.append(
                "Built module exceeds the explicit advisory ceiling and requires "
                "exceptional justification."
            )

    return SizePolicyRecord(
        track=track,
        slug=slug,
        basis="explicit_plan_size_policy",
        plan_path=plan_path,
        dossier_path=dossier_path,
        module_path=module_path,
        plan_floor=plan_floor,
        plan_outline_words=plan_outline_words,
        actual_words=actual_words,
        density_band="reviewed_plan_override",
        band_min=override.recommended_min,
        band_max=override.recommended_max,
        effective_min=override.floor_words,
        advisory_ceiling=override.ceiling_words,
        status=status,
        notes=notes,
        metrics=metrics,
    )


def _plan_paths_for_track(track: str) -> list[Path]:
    plans_dir = CURRICULUM_ROOT / "plans" / track
    if not plans_dir.exists():
        return []
    return sorted(path for path in plans_dir.glob("*.yaml") if not path.name.endswith(".bak.yaml"))


def _module_path(track: str, slug: str) -> Path:
    return CURRICULUM_ROOT / track / slug / "module.md"


def _dossier_from_plan(plan: dict[str, Any]) -> Path | None:
    references = plan.get("references")
    if not isinstance(references, list):
        return None
    for reference in references:
        if not isinstance(reference, dict):
            continue
        path_value = reference.get("path")
        if reference.get("type") != "dossier" or not isinstance(path_value, str):
            continue
        path = Path(path_value)
        candidate = path if path.is_absolute() else PROJECT_ROOT / path
        if candidate.exists():
            return candidate
    return None


def _dossier_path(track: str, slug: str, plan: dict[str, Any]) -> Path | None:
    from_plan = _dossier_from_plan(plan)
    if from_plan is not None:
        return from_plan

    candidates = [
        RESEARCH_ROOT / track / f"{slug}.md",
        CURRICULUM_ROOT / track / "research" / f"{slug}-research.md",
        CURRICULUM_ROOT / track / "research" / f"{slug}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _status_and_notes(
    *,
    track: str,
    plan_floor: int | None,
    actual_words: int | None,
    band: str,
    band_max: int | None,
    advisory_ceiling: int | None,
    dossier_path: Path | None,
) -> tuple[str, list[str]]:
    notes: list[str] = []
    status = "advisory_ok"

    if plan_floor is None:
        return "missing_plan_word_target", ["Plan has no numeric word_target."]

    if track.lower() in SEMINAR_TRACKS and dossier_path is None:
        return "missing_dossier", ["Seminar module has no discoverable research dossier."]

    if band == "sparse":
        notes.append(
            "Sparse classification is not permission to underbuild; require source-saturation evidence before lowering a plan."
        )
    if band.startswith("core_"):
        notes.append(
            "Core C1-C2 uses a pedagogy/evidence-packet basis; do not apply seminar dossier ceilings mechanically."
        )

    if band_max is not None and plan_floor > band_max:
        status = "plan_review_needed"
        notes.append(
            "Plan floor exceeds the dossier/evidence advisory ceiling; review the plan before asking writers to expand."
        )

    if actual_words is not None:
        if actual_words < plan_floor:
            if status == "plan_review_needed":
                notes.append(
                    "Built module is below the current plan floor, but the plan floor already exceeds the advisory ceiling; review the plan before expanding."
                )
            else:
                status = "below_plan_floor"
                notes.append("Built module is below the current plan floor.")
        elif advisory_ceiling is not None and actual_words > advisory_ceiling:
            if status != "plan_review_needed":
                status = "over_advisory_ceiling"
            notes.append(
                "Built module exceeds the advisory ceiling; expansion should be justified by sourced pedagogy."
            )
        if actual_words >= MODULE_SIZE_BANDS["exceptional"][0]:
            if status != "plan_review_needed":
                status = "exceptional_justification_required"
            notes.append("Modules at 8000+ words require explicit justification.")

    return status, notes


def build_record(track: str, plan_path: Path) -> SizePolicyRecord:
    plan = read_yaml(plan_path)
    slug = str(plan.get("slug") or plan_path.stem)
    plan_floor = _as_int(plan.get("word_target"))
    plan_outline_words = _sum_outline_words(plan.get("content_outline"))
    module_path = _module_path(track, slug)
    actual_words = word_count(module_path) if module_path.exists() else None
    dossier_path = _dossier_path(track, slug, plan)

    metrics = dossier_metrics(dossier_path) if dossier_path else None
    override, override_errors = explicit_size_policy_override(plan)
    displayed_plan_path = display_path(plan_path) or str(plan_path)
    displayed_dossier_path = display_path(dossier_path)
    displayed_module_path = display_path(module_path) if module_path.exists() else None
    if override is not None:
        return build_explicit_size_policy_record(
            track=track,
            slug=slug,
            plan_path=displayed_plan_path,
            dossier_path=displayed_dossier_path,
            module_path=displayed_module_path,
            plan_floor=plan_floor,
            plan_outline_words=plan_outline_words,
            actual_words=actual_words,
            metrics=metrics,
            override=override,
        )

    if metrics is not None:
        basis = "research_dossier"
        band = classify_dossier(track, metrics)
    elif track.lower() in CORE_RESEARCH_TRACKS:
        basis = "core_evidence_packet"
        band = classify_core_evidence(plan)
    else:
        basis = "missing_research_dossier"
        band = "sparse"

    band_min, band_max = band_limits(band)
    effective_min = plan_floor
    advisory_ceiling = None
    if plan_floor is not None:
        advisory_ceiling = max(plan_floor, band_max) if band_max is not None else None

    status, notes = _status_and_notes(
        track=track,
        plan_floor=plan_floor,
        actual_words=actual_words,
        band=band,
        band_max=band_max,
        advisory_ceiling=advisory_ceiling,
        dossier_path=dossier_path,
    )
    if override_errors:
        status = "invalid_size_policy"
        notes.extend(
            [
                "Explicit size_policy is invalid and cannot replace generic density-band limits.",
                *override_errors,
            ]
        )

    return SizePolicyRecord(
        track=track,
        slug=slug,
        basis=basis,
        plan_path=displayed_plan_path,
        dossier_path=displayed_dossier_path,
        module_path=displayed_module_path,
        plan_floor=plan_floor,
        plan_outline_words=plan_outline_words,
        actual_words=actual_words,
        density_band=band,
        band_min=band_min,
        band_max=band_max,
        effective_min=effective_min,
        advisory_ceiling=advisory_ceiling,
        status=status,
        notes=notes,
        metrics=metrics,
    )


def select_plan_paths(
    tracks: list[str],
    slugs: set[str] | None,
    built_only: bool,
) -> list[tuple[str, Path]]:
    selected: list[tuple[str, Path]] = []
    for track in tracks:
        for plan_path in _plan_paths_for_track(track):
            plan = read_yaml(plan_path)
            slug = str(plan.get("slug") or plan_path.stem)
            if slugs is not None and slug not in slugs:
                continue
            if built_only and not _module_path(track, slug).exists():
                continue
            selected.append((track, plan_path))
    return selected


def _parse_slug_filter(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    slugs: set[str] = set()
    for value in values:
        slugs.update(part.strip() for part in value.split(",") if part.strip())
    return slugs or None


def _record_to_dict(record: SizePolicyRecord) -> dict[str, Any]:
    data = asdict(record)
    if record.metrics is not None:
        data["metrics"] = asdict(record.metrics)
    return data


def build_records(
    *,
    tracks: list[str],
    slugs: set[str] | None = None,
    built_only: bool = False,
) -> list[SizePolicyRecord]:
    """Build advisory size-policy records for selected module plans."""
    normalized_tracks = [track.lower() for track in tracks]
    return [
        build_record(track, plan_path)
        for track, plan_path in select_plan_paths(normalized_tracks, slugs, built_only)
    ]


def build_report(
    *,
    tracks: list[str],
    slugs: set[str] | None = None,
    built_only: bool = False,
) -> list[dict[str, Any]]:
    """Return a stable JSON-serializable advisory report."""
    records = build_records(tracks=tracks, slugs=slugs, built_only=built_only)
    return [_record_to_dict(record) for record in records]


def print_summary(records: list[SizePolicyRecord]) -> None:
    if not records:
        print("No module plans selected.")
        return

    headers = [
        "track",
        "slug",
        "basis",
        "band",
        "plan",
        "actual",
        "ceiling",
        "dossier",
        "refs",
        "status",
    ]
    rows: list[list[str]] = []
    for record in records:
        rows.append(
            [
                record.track,
                record.slug,
                record.basis,
                record.density_band,
                str(record.plan_floor if record.plan_floor is not None else "-"),
                str(record.actual_words if record.actual_words is not None else "-"),
                str(
                    record.advisory_ceiling
                    if record.advisory_ceiling is not None
                    else "-"
                ),
                str(record.metrics.words if record.metrics else "-"),
                str(record.metrics.source_refs if record.metrics else "-"),
                record.status,
            ]
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print()
    print(
        "Advisory only: this command reports policy pressure and returns 0; it does not change build gates."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report dossier/evidence-led module size policy signals.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tracks",
        nargs="+",
        default=["bio", "folk"],
        help="Track directories under curriculum/l2-uk-en/plans/ to inspect.",
    )
    parser.add_argument(
        "--slugs",
        nargs="*",
        help="Optional slug filter; accepts repeated values or comma-separated lists.",
    )
    parser.add_argument(
        "--built-only",
        action="store_true",
        help="Only report plans with an existing curriculum/l2-uk-en/{track}/{slug}/module.md.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    slugs = _parse_slug_filter(args.slugs)
    records = build_records(tracks=args.tracks, slugs=slugs, built_only=args.built_only)

    if args.format == "json":
        report = [_record_to_dict(record) for record in records]
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_summary(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
