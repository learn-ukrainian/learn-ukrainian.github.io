#!/usr/bin/env python3
"""Validate plan file ordering and metadata against curriculum.yaml.

Checks every plan file for a given track (or all tracks) against the
curriculum manifest. Reports mismatches in:
  - module: field (should be {level}-{seq:03d})
  - level: field
  - sequence: field
  - slug: field (should match filename)
  - connects_to / prerequisites references (b1-XX should point to correct seq)
  - orphaned plan files (no curriculum.yaml entry)
  - missing plan files (curriculum.yaml entry but no file)

Usage:
    .venv/bin/python scripts/validate_plan_ordering.py          # all tracks
    .venv/bin/python scripts/validate_plan_ordering.py b1       # single track
    .venv/bin/python scripts/validate_plan_ordering.py --fix    # auto-fix all fixable issues
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURRICULUM_PATH = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
PLANS_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"


def load_curriculum() -> dict[str, list[str]]:
    """Load curriculum.yaml and return {level: [slug, ...]} mapping."""
    with open(CURRICULUM_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result: dict[str, list[str]] = {}
    for level_key, level_data in data.get("levels", {}).items():
        modules = level_data.get("modules", [])
        result[level_key] = [m for m in modules if isinstance(m, str)]
    return result


def expected_module_id(level: str, seq: int) -> str:
    """Generate expected module field value."""
    return f"{level}-{seq:03d}"


def find_plan_dir(level: str) -> Path | None:
    """Find the plan directory for a level."""
    d = PLANS_DIR / level
    if d.is_dir():
        return d
    return None


def _level_variants(level_key: str) -> set[str]:
    """Generate acceptable level field values for a curriculum.yaml key.

    e.g., "b1" -> {"B1"}, "lit-essay" -> {"LIT-ESSAY", "LIT.ESSAY", "LIT"},
    "c1-pro" -> {"C1-PRO", "C1"}
    """
    upper = level_key.upper()
    variants = {upper, upper.replace("-", ".")}
    # Also accept the base level (e.g., "LIT" for "lit-essay")
    base = upper.split("-")[0].split(".")[0]
    variants.add(base)
    # Handle sub-tracks: lit-youth -> LIT-YOUTH, LIT.YOUTH, LIT.JUVENILE, LIT
    # Add common alternate naming
    alt_names = {
        "LIT-YOUTH": {"LIT.JUVENILE", "LIT.YOUTH", "LIT-YOUTH"},
        "LIT-ESSAY": {"LIT.ESSAY", "LIT-ESSAY"},
        "LIT-HIST-FIC": {"LIT.HIST.FIC", "LIT-HIST-FIC"},
        "LIT-FANTASTIKA": {"LIT.FANTASTIKA", "LIT-FANTASTIKA"},
        "LIT-WAR": {"LIT.WAR", "LIT-WAR"},
        "LIT-HUMOR": {"LIT.HUMOR", "LIT-HUMOR"},
        "LIT-DOC": {"LIT.DOC", "LIT-DOC"},
        "LIT-DRAMA": {"LIT.DRAMA", "LIT-DRAMA"},
        "LIT-CRIMEA": {"LIT.CRIMEA", "LIT-CRIMEA"},
    }
    if upper in alt_names:
        variants.update(alt_names[upper])
    return variants


def _slug_similarity(slug: str, description: str) -> float:
    """Score how well a slug matches a parenthetical description (0-1)."""
    # Normalize: remove apostrophes, punctuation, lowercase
    def _normalize(text: str) -> set[str]:
        text = text.replace("'", "").replace("ʼ", "").replace("\u02BC", "")
        words = set(re.sub(r"[^\w\s]", " ", text).lower().split())
        trivial = {"the", "a", "an", "and", "or", "of", "in", "to", "for", "is", "at",
                   "та", "і", "й", "у", "в", "з", "із", "на", "для", "до"}
        return words - trivial

    slug_words = _normalize(slug.replace("-", " "))
    desc_words = _normalize(description)
    if not slug_words or not desc_words:
        return 0.0
    # If slug and description use different scripts (Latin vs Cyrillic),
    # word overlap is impossible — skip comparison (assume correct).
    slug_has_cyrillic = any("\u0400" <= c <= "\u04ff" for c in slug)
    desc_has_cyrillic = any("\u0400" <= c <= "\u04ff" for c in description)
    if slug_has_cyrillic != desc_has_cyrillic:
        return 1.0  # Cross-script — can't compare, assume correct
    overlap = slug_words & desc_words
    return len(overlap) / min(len(slug_words), len(desc_words))


def _resolve_ref_by_description(
    raw_entry: str, level: str,
    slug_to_seq: dict[str, int],
) -> tuple[int, str] | None:
    """Try to resolve the intended slug from a ref's parenthetical description.

    Returns (correct_seq, matched_slug) or None if no match.
    """
    paren_match = re.search(r"\((.+?)\)", raw_entry)
    if not paren_match:
        return None

    desc = paren_match.group(1)
    best_score = 0.0
    best_slug = None

    for slug, seq in slug_to_seq.items():
        score = _slug_similarity(slug, desc)
        if score > best_score:
            best_score = score
            best_slug = slug

    if best_slug and best_score >= 0.3:
        return slug_to_seq[best_slug], best_slug

    return None


def _fix_ref_in_file(plan_file: Path, old_ref: str, new_ref: str,
                     old_entry: str, new_entry: str) -> bool:
    """Fix a single reference in a plan file. Returns True if changed."""
    content = plan_file.read_text(encoding="utf-8")
    if old_entry in content:
        new_content = content.replace(old_entry, new_entry, 1)
        if new_content != content:
            plan_file.write_text(new_content, encoding="utf-8")
            return True
    return False


def validate_track(level: str, slugs: list[str], fix: bool = False) -> tuple[list[str], int]:
    """Validate all plan files for a track. Returns (issues, fix_count)."""
    errors: list[str] = []
    warnings: list[str] = []
    fix_count = 0
    plan_dir = find_plan_dir(level)

    if not plan_dir:
        errors.append(f"[{level}] Plan directory not found: {PLANS_DIR / level}")
        return errors, 0

    # Build slug -> sequence mapping (1-indexed)
    slug_to_seq: dict[str, int] = {}
    for i, slug in enumerate(slugs, 1):
        slug_to_seq[slug] = i

    # Build seq -> slug reverse mapping
    seq_to_slug: dict[int, str] = {v: k for k, v in slug_to_seq.items()}

    # Track which slugs have plan files
    found_slugs: set[str] = set()

    # Check every plan file
    for plan_file in sorted(plan_dir.glob("*.yaml")):
        file_slug = plan_file.stem
        found_slugs.add(file_slug)

        try:
            with open(plan_file, encoding="utf-8") as f:
                plan = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"[{level}] YAML parse error in {plan_file.name}: {e}")
            continue

        if not isinstance(plan, dict):
            errors.append(f"[{level}] {plan_file.name}: not a dict (got {type(plan).__name__})")
            continue

        # Check if slug is in curriculum
        if file_slug not in slug_to_seq:
            warnings.append(f"[{level}] ORPHAN: {plan_file.name} has no curriculum.yaml entry")
            continue

        expected_seq = slug_to_seq[file_slug]
        expected_mod = expected_module_id(level, expected_seq)
        # Level field can use various conventions:
        # curriculum key "b1" -> plan "B1", "lit-essay" -> "LIT.ESSAY" or "LIT-ESSAY"
        expected_level_variants = _level_variants(level)

        # Check slug field
        plan_slug = plan.get("slug", "")
        if plan_slug and plan_slug != file_slug:
            errors.append(
                f"[{level}] {plan_file.name}: slug={plan_slug!r}, expected={file_slug!r}"
            )

        # Check sequence field
        plan_seq = plan.get("sequence")
        if plan_seq is not None and int(plan_seq) != expected_seq:
            errors.append(
                f"[{level}] {plan_file.name}: sequence={plan_seq}, expected={expected_seq}"
            )
            if fix:
                _fix_field(plan_file, "sequence", plan_seq, expected_seq)
                fix_count += 1

        # Check module field
        plan_mod = plan.get("module", "")
        if plan_mod and str(plan_mod) != expected_mod:
            errors.append(
                f"[{level}] {plan_file.name}: module={plan_mod!r}, expected={expected_mod!r}"
            )
            if fix:
                _fix_field(plan_file, "module", plan_mod, expected_mod)
                fix_count += 1

        # Check level field
        plan_level = plan.get("level", "")
        if plan_level and plan_level not in expected_level_variants:
            errors.append(
                f"[{level}] {plan_file.name}: level={plan_level!r}, "
                f"expected one of {expected_level_variants}"
            )

        # Check connects_to and prerequisites references
        for field_name in ("connects_to", "prerequisites"):
            field_val = plan.get(field_name)
            if not field_val:
                continue
            ref_pattern = re.compile(rf"\b{re.escape(level)}-(\d+)\b")
            for raw_entry in field_val:
                entry_str = str(raw_entry)
                match = ref_pattern.search(entry_str)
                if not match:
                    continue

                ref_seq = int(match.group(1))
                ref_str = f"{level}-{match.group(1)}"
                is_bad = False

                # Check: ref points to nonexistent seq
                if ref_seq not in seq_to_slug:
                    errors.append(
                        f"[{level}] {plan_file.name}: {field_name} ref {ref_str} "
                        f"-> seq {ref_seq} doesn't exist (max={len(slugs)})"
                    )
                    is_bad = True

                # Check: prerequisite points forward
                if field_name == "prerequisites" and ref_seq in seq_to_slug and ref_seq >= expected_seq:
                    errors.append(
                        f"[{level}] {plan_file.name}: {field_name} ref {ref_str} "
                        f"(seq {ref_seq}) >= module seq ({expected_seq}) — can't come after"
                    )
                    is_bad = True

                # Check: description doesn't match actual slug at that seq
                paren_match = re.search(r"\((.+?)\)", entry_str)
                if paren_match and ref_seq in seq_to_slug:
                    actual_slug = seq_to_slug[ref_seq]
                    desc = paren_match.group(1)
                    score = _slug_similarity(actual_slug, desc)
                    if score < 0.3:
                        warnings.append(
                            f"[{level}] {plan_file.name}: {field_name} {ref_str} "
                            f"desc '{desc}' doesn't match slug '{actual_slug}'"
                        )
                        # Fix: update description to match actual slug
                        if fix and not is_bad:
                            slug_desc = actual_slug.replace("-", " ").title()
                            new_entry = entry_str.replace(
                                f"({desc})", f"({slug_desc})"
                            )
                            if new_entry != entry_str and _fix_ref_in_file(
                                plan_file, ref_str, ref_str, entry_str, new_entry
                            ):
                                fix_count += 1
                            else:
                                is_bad = True
                        else:
                            is_bad = True

                # Try to fix by resolving description to correct slug
                if is_bad and fix and paren_match:
                    resolved = _resolve_ref_by_description(entry_str, level, slug_to_seq)
                    if resolved:
                        correct_seq, matched_slug = resolved
                        # For prerequisites, verify it doesn't point forward
                        if field_name == "prerequisites" and correct_seq >= expected_seq:
                            # Can't fix — the description itself points forward.
                            # Remove the entry entirely.
                            if _remove_entry_from_file(plan_file, entry_str):
                                fix_count += 1
                                print(f"  REMOVED: {plan_file.name} {field_name}: "
                                      f"'{entry_str}' (forward ref, can't fix)")
                        else:
                            new_ref = f"{level}-{correct_seq:02d}"
                            new_entry = re.sub(
                                rf"\b{re.escape(level)}-\d+",
                                new_ref, entry_str, count=1
                            )
                            if new_entry != entry_str and _fix_ref_in_file(
                                plan_file, ref_str, new_ref, entry_str, new_entry
                            ):
                                fix_count += 1
                                print(f"  FIXED: {plan_file.name} {field_name}: "
                                      f"'{entry_str}' -> '{new_entry}'")
                    elif is_bad and fix:
                        # No description match — remove if forward prereq
                        if field_name == "prerequisites" and ref_seq >= expected_seq:
                            if _remove_entry_from_file(plan_file, entry_str):
                                fix_count += 1
                                print(f"  REMOVED: {plan_file.name} {field_name}: "
                                      f"'{entry_str}' (forward ref, no description match)")

    # Check for missing plan files
    for slug, seq in slug_to_seq.items():
        if slug not in found_slugs:
            errors.append(
                f"[{level}] MISSING: {slug}.yaml (seq {seq}) has no plan file"
            )

    return errors + warnings, fix_count


def _fix_field(plan_file: Path, field: str, old_val, new_val) -> None:
    """Fix a single field in a plan YAML file using text replacement."""
    content = plan_file.read_text(encoding="utf-8")

    if field == "sequence":
        pattern = rf"^(sequence:\s*){re.escape(str(old_val))}$"
        replacement = rf"\g<1>{new_val}"
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
    elif field == "module":
        pattern = rf"^(module:\s*){re.escape(str(old_val))}$"
        replacement = rf"\g<1>{new_val}"
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
    else:
        return

    if new_content != content:
        plan_file.write_text(new_content, encoding="utf-8")
        print(f"  FIXED: {plan_file.name} {field}: {old_val} -> {new_val}")


def _remove_entry_from_file(plan_file: Path, entry: str) -> bool:
    """Remove a specific list entry from a YAML file."""
    content = plan_file.read_text(encoding="utf-8")
    # Try to remove the line containing this entry (with leading "- ")
    # Handle both quoted and unquoted YAML list entries
    for pattern in [
        f"- '{re.escape(entry)}'\n",
        f"- \"{re.escape(entry)}\"\n",
        f"- {re.escape(entry)}\n",
    ]:
        if pattern in content:
            new_content = content.replace(pattern, "", 1)
            if new_content != content:
                plan_file.write_text(new_content, encoding="utf-8")
                return True
    return False


def main():
    fix = "--fix" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    curriculum = load_curriculum()

    if args:
        tracks = args
    else:
        tracks = list(curriculum.keys())

    total_errors = 0
    total_warnings = 0
    total_fixes = 0

    for track in tracks:
        if track not in curriculum:
            print(f"Track '{track}' not found in curriculum.yaml")
            print(f"Available: {', '.join(sorted(curriculum.keys()))}")
            continue

        slugs = curriculum[track]
        print(f"\n{'=' * 60}")
        print(f"Track: {track} ({len(slugs)} modules)")
        print(f"{'=' * 60}")

        issues, fixes = validate_track(track, slugs, fix=fix)

        errors = [i for i in issues if "ORPHAN" not in i and "doesn't match" not in i]
        warnings = [i for i in issues if "ORPHAN" in i or "doesn't match" in i]

        if not issues:
            print(f"  ✅ All {len(slugs)} modules verified — no issues found")
        else:
            for issue in errors:
                print(f"  ❌ {issue}")
            for issue in warnings:
                print(f"  ⚠️  {issue}")

            print(f"\n  Summary: {len(errors)} errors, {len(warnings)} warnings"
                  + (f", {fixes} fixes applied" if fixes else ""))

        total_errors += len(errors)
        total_warnings += len(warnings)
        total_fixes += fixes

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total_errors} errors, {total_warnings} warnings across {len(tracks)} tracks")
    if total_fixes:
        print(f"       {total_fixes} fixes applied")
    if total_errors > 0 and not fix:
        print("Run with --fix to auto-fix mismatches")
    print(f"{'=' * 60}")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
