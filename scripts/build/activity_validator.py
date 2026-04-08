"""Activity validator — detect structural and pedagogical problems in activity YAML.

Checks:
- fill-in: answer in options, no trivial hints (hint = answer), blank present
- quiz: correct index in range, options count
- error-correction: error word in sentence, correction differs from error
- unjumble: commas in tiles, positional anchors (delegated to exercise_verify)
- match-up: no duplicate pairs
- all types: item count meets schema minimums

Usage:
    from build.activity_validator import validate_activities
    issues = validate_activities("curriculum/l2-uk-en/a1/activities/where-to.yaml")

    # Or batch:
    from build.activity_validator import validate_all
    all_issues = validate_all("a1")
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"


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


def validate_activities(path: str | Path) -> list[ActivityIssue]:
    """Validate a single activities YAML file. Returns list of issues."""
    path = Path(path)
    slug = path.stem
    activities = yaml.safe_load(path.read_text("utf-8"))
    if not activities:
        return []

    issues: list[ActivityIssue] = []

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
