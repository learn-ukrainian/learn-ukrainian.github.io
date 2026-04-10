"""Activity validator — detect structural and pedagogical problems in activity YAML.

Structural checks (per-item):
- fill-in: answer in options, no parenthetical hints, blank present
- quiz: correct index in range, no duplicate options
- error-correction: error word in sentence, correction differs from error
- unjumble: commas in tiles, positional anchors (delegated to exercise_verify)
- match-up: no duplicate pairs
- true-false: correct field is boolean

Section-level checks (requires level context):
- Inline count within INLINE_MIN..INLINE_MAX
- Workbook count within WORKBOOK_MIN..WORKBOOK_MAX
- No INLINE_ONLY type appears in workbook section
- No WORKBOOK_ONLY type appears in inline section
- Per-section type only uses allowed types from config

Usage:
    from build.activity_validator import validate_activities
    issues = validate_activities(
        "curriculum/l2-uk-en/a1/activities/where-to.yaml",
        level="a1", module_num=1,
    )
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# Ensure scripts/ on sys.path so we can import pipeline.config_tables
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


@dataclass
class ActivityIssue:
    """A problem found in an activity."""

    slug: str
    section: str  # "inline" or "workbook"
    activity_type: str
    item_index: int  # -1 for activity-level issues
    severity: str  # "error" (broken) or "warning" (pedagogical)
    message: str

    def __str__(self) -> str:
        loc = f"[{self.section}] {self.activity_type}"
        if self.item_index >= 0:
            loc += f" item {self.item_index}"
        icon = "❌" if self.severity == "error" else "⚠️"
        return f"{icon} {self.slug} {loc}: {self.message}"


def _infer_level_from_path(path: Path) -> tuple[str, int] | None:
    """Best-effort level + module_num inference from file path."""
    # curriculum/l2-uk-en/{level}/activities/{slug}.yaml
    try:
        parts = path.parts
        if "activities" in parts:
            level = parts[parts.index("activities") - 1]
            slug = path.stem
            try:
                from batch_gemini_config import num_for_slug
                return level, num_for_slug(level, slug)
            except Exception:
                return level, 1
    except Exception:
        pass
    return None


def validate_activities(
    path: str | Path,
    level: str | None = None,
    module_num: int | None = None,
) -> list[ActivityIssue]:
    """Validate a single activities YAML file. Returns list of issues.

    If level + module_num are provided (or can be inferred from path),
    section-level checks are applied (count, inline/workbook type placement,
    per-section allowlists).
    """
    path = Path(path)
    slug = path.stem
    activities = yaml.safe_load(path.read_text("utf-8"))
    if not activities:
        return []

    issues: list[ActivityIssue] = []

    # Infer level/module_num from path if not provided
    if level is None or module_num is None:
        inferred = _infer_level_from_path(path)
        if inferred:
            level = level or inferred[0]
            module_num = module_num or inferred[1]

    # Structural per-item checks
    for section in ("inline", "workbook"):
        for act in activities.get(section, []) or []:
            if not isinstance(act, dict):
                continue
            atype = act.get("type", "")
            items = act.get("items", []) or []

            if atype == "fill-in":
                issues.extend(_check_fill_in(slug, section, items))
            elif atype == "quiz":
                issues.extend(_check_quiz(slug, section, items))
            elif atype == "error-correction":
                issues.extend(_check_error_correction(slug, section, items))
            elif atype == "match-up":
                pairs = act.get("pairs", []) or []
                issues.extend(_check_match_up(slug, section, pairs))
            elif atype == "true-false":
                issues.extend(_check_true_false(slug, section, items))

    # Section-level checks (need level context)
    if level and module_num:
        issues.extend(_check_section_placement(slug, activities))
        issues.extend(_check_section_counts_and_types(slug, activities, level, module_num))

    return issues


def _check_section_placement(slug: str, activities: dict) -> list[ActivityIssue]:
    """Enforce INLINE_ONLY vs WORKBOOK_ONLY type placement rules.

    Independent of per-level config — these are semantic rules
    (essay-response never belongs inline, image-to-letter never in workbook).
    """
    try:
        from pipeline.config_tables import INLINE_ONLY_TYPES, WORKBOOK_ONLY_TYPES
    except ImportError:
        return []  # Can't validate without config

    issues: list[ActivityIssue] = []

    # Inline section: reject WORKBOOK_ONLY types
    for act in activities.get("inline", []) or []:
        if not isinstance(act, dict):
            continue
        atype = act.get("type", "")
        if atype in WORKBOOK_ONLY_TYPES:
            issues.append(ActivityIssue(
                slug, "inline", atype, -1, "error",
                f"type '{atype}' is WORKBOOK-ONLY — move to workbook section",
            ))

    # Workbook section: reject INLINE_ONLY types
    for act in activities.get("workbook", []) or []:
        if not isinstance(act, dict):
            continue
        atype = act.get("type", "")
        if atype in INLINE_ONLY_TYPES:
            issues.append(ActivityIssue(
                slug, "workbook", atype, -1, "error",
                f"type '{atype}' is INLINE-ONLY — move to inline section",
            ))

    return issues


def _check_section_counts_and_types(
    slug: str, activities: dict, level: str, module_num: int,
) -> list[ActivityIssue]:
    """Enforce per-level inline/workbook count minimums and type allowlists."""
    try:
        from pipeline.config_tables import get_activity_config
    except ImportError:
        return []

    try:
        config = get_activity_config(level, module_num)
    except Exception:
        return []

    issues: list[ActivityIssue] = []

    inline_count = len(activities.get("inline", []) or [])
    workbook_count = len(activities.get("workbook", []) or [])

    # Count checks
    try:
        inline_min = int(config.get("INLINE_MIN", "0"))
        inline_max = int(config.get("INLINE_MAX", "99"))
        workbook_min = int(config.get("WORKBOOK_MIN", "0"))
        workbook_max = int(config.get("WORKBOOK_MAX", "99"))
    except (TypeError, ValueError):
        inline_min = inline_max = workbook_min = workbook_max = 0

    if inline_min and inline_count < inline_min:
        issues.append(ActivityIssue(
            slug, "inline", "-", -1, "error",
            f"inline count {inline_count} below minimum {inline_min} for {level}",
        ))
    if inline_max and inline_count > inline_max:
        issues.append(ActivityIssue(
            slug, "inline", "-", -1, "warning",
            f"inline count {inline_count} exceeds maximum {inline_max} for {level} — prose may be fragmented",
        ))
    if workbook_min and workbook_count < workbook_min:
        issues.append(ActivityIssue(
            slug, "workbook", "-", -1, "error",
            f"workbook count {workbook_count} below minimum {workbook_min} for {level}",
        ))
    if workbook_max and workbook_count > workbook_max:
        issues.append(ActivityIssue(
            slug, "workbook", "-", -1, "warning",
            f"workbook count {workbook_count} exceeds maximum {workbook_max} for {level}",
        ))

    # Per-section type allowlists
    inline_allowed_str = config.get("INLINE_ALLOWED_TYPES", "")
    workbook_allowed_str = config.get("WORKBOOK_ALLOWED_TYPES", "")
    inline_allowed = {t.strip() for t in inline_allowed_str.split(",") if t.strip()}
    workbook_allowed = {t.strip() for t in workbook_allowed_str.split(",") if t.strip()}

    for act in activities.get("inline", []) or []:
        if not isinstance(act, dict):
            continue
        atype = act.get("type", "")
        if inline_allowed and atype and atype not in inline_allowed:
            issues.append(ActivityIssue(
                slug, "inline", atype, -1, "error",
                f"type '{atype}' not in {level} inline allowlist "
                f"(allowed: {', '.join(sorted(inline_allowed))})",
            ))

    for act in activities.get("workbook", []) or []:
        if not isinstance(act, dict):
            continue
        atype = act.get("type", "")
        if workbook_allowed and atype and atype not in workbook_allowed:
            issues.append(ActivityIssue(
                slug, "workbook", atype, -1, "error",
                f"type '{atype}' not in {level} workbook allowlist "
                f"(allowed: {', '.join(sorted(workbook_allowed))})",
            ))

    return issues


def validate_all(level: str) -> list[ActivityIssue]:
    """Validate all activity files for a level. Returns all issues."""
    act_dir = CURRICULUM_DIR / level / "activities"
    if not act_dir.exists():
        return []

    all_issues: list[ActivityIssue] = []
    for fname in sorted(os.listdir(act_dir)):
        if not fname.endswith(".yaml"):
            continue
        all_issues.extend(validate_activities(act_dir / fname))

    return all_issues


def format_report(issues: list[ActivityIssue]) -> str:
    """Format issues as a readable report."""
    if not issues:
        return "✅ All activities valid"

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    lines = [f"Found {len(issues)} issues ({len(errors)} errors, {len(warnings)} warnings):"]
    if errors:
        lines.append("\nErrors (broken — must fix):")
        for i in errors:
            lines.append(f"  {i}")
    if warnings:
        lines.append("\nWarnings (pedagogical — should fix):")
        for i in warnings:
            lines.append(f"  {i}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Per-type validators
# ---------------------------------------------------------------------------


def _check_fill_in(
    slug: str, section: str, items: list,
) -> list[ActivityIssue]:
    issues: list[ActivityIssue] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        sent = str(item.get("sentence", ""))
        answer = str(item.get("answer", ""))
        opts = item.get("options", []) or []

        # Blank must exist (____  for word-level, single _ for letter-level)
        if "_" not in sent:
            issues.append(ActivityIssue(
                slug, section, "fill-in", i, "error",
                f"no blank in sentence: \"{sent[:60]}\"",
            ))

        # Answer must be in options (if options present)
        if opts and answer not in opts:
            issues.append(ActivityIssue(
                slug, section, "fill-in", i, "error",
                f"answer \"{answer}\" not in options {opts}",
            ))

        # No hints in parentheses — learner should produce from context, not copy
        hint_match = re.search(r"\([^)]+\)", sent)
        if hint_match:
            issues.append(ActivityIssue(
                slug, section, "fill-in", i, "error",
                f"hint in parentheses: \"{sent[:60]}\" — remove hint, context should be enough",
            ))

    return issues


def _check_quiz(
    slug: str, section: str, items: list,
) -> list[ActivityIssue]:
    issues: list[ActivityIssue] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        opts = item.get("options", []) or []
        correct = item.get("correct")

        # Correct index must be valid
        if isinstance(correct, int) and (correct < 0 or correct >= len(opts)):
            issues.append(ActivityIssue(
                slug, section, "quiz", i, "error",
                f"correct={correct} out of range (0-{len(opts) - 1})",
            ))

        # Duplicate options
        if len(opts) != len(set(opts)):
            dupes = [o for o in opts if opts.count(o) > 1]
            issues.append(ActivityIssue(
                slug, section, "quiz", i, "error",
                f"duplicate options: {set(dupes)}",
            ))

    return issues


def _check_error_correction(
    slug: str, section: str, items: list,
) -> list[ActivityIssue]:
    issues: list[ActivityIssue] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        sent = str(item.get("sentence", ""))
        error = str(item.get("error", ""))
        correction = str(item.get("correction", "") or item.get("answer", ""))

        # Error word must be in sentence
        if error and error not in sent:
            issues.append(ActivityIssue(
                slug, section, "error-correction", i, "error",
                f"error \"{error}\" not found in sentence \"{sent[:60]}\"",
            ))

        # Correction must differ from error
        if error and correction and error == correction:
            issues.append(ActivityIssue(
                slug, section, "error-correction", i, "error",
                f"correction = error \"{error}\" — nothing to fix",
            ))

    return issues


def _check_match_up(
    slug: str, section: str, pairs: list,
) -> list[ActivityIssue]:
    issues: list[ActivityIssue] = []
    seen_left: set[str] = set()
    seen_right: set[str] = set()

    for i, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            continue
        left = str(pair.get("left", ""))
        right = str(pair.get("right", ""))

        if left in seen_left:
            issues.append(ActivityIssue(
                slug, section, "match-up", i, "error",
                f"duplicate left: \"{left}\"",
            ))
        if right in seen_right:
            issues.append(ActivityIssue(
                slug, section, "match-up", i, "error",
                f"duplicate right: \"{right}\"",
            ))
        seen_left.add(left)
        seen_right.add(right)

    return issues


def _check_true_false(
    slug: str, section: str, items: list,
) -> list[ActivityIssue]:
    issues: list[ActivityIssue] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        correct = item.get("correct", item.get("isTrue"))
        if correct is None:
            issues.append(ActivityIssue(
                slug, section, "true-false", i, "error",
                "missing 'correct' field",
            ))
        elif not isinstance(correct, bool):
            issues.append(ActivityIssue(
                slug, section, "true-false", i, "error",
                f"'correct' should be boolean, got {type(correct).__name__}: {correct}",
            ))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python scripts/build/activity_validator.py <level> [slug]")
        print("  level: a1, a2, b1, ...")
        print("  slug: optional — validate single module")
        sys.exit(1)

    level = sys.argv[1]

    if len(sys.argv) >= 3:
        slug = sys.argv[2]
        path = CURRICULUM_DIR / level / "activities" / f"{slug}.yaml"
        if not path.exists():
            print(f"Not found: {path}")
            sys.exit(1)
        issues = validate_activities(path)
    else:
        issues = validate_all(level)

    print(format_report(issues))
    sys.exit(1 if any(i.severity == "error" for i in issues) else 0)
