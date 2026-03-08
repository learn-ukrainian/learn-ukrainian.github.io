"""
YAML Activity Schema Auto-Fix Orchestration.

Orchestrates auto-fix pipeline for activity YAML files: raw text fixes,
schema validation, type-specific fixes, and file I/O.
Separated from yaml_schema_validation.py for maintainability.
"""

import json
import re
from pathlib import Path

import yaml

from .yaml_item_fixers import (
    TYPE_FIXERS,
    fix_cloze_blank_lines,
    fix_invalid_top_level_properties,
    fix_missing_instruction,
    fix_quiz_select_items,
    fix_select_property_renames,
)
from .yaml_schema_validation import (
    get_activity_schema,
    get_schemas_dir,
    load_base_schema,
    safe_load_with_duplicate_check,
)


def fix_activity_violations(activity: dict, base_schema: dict) -> tuple[bool, list[str]]:
    """Automatically fix common YAML schema violations in an activity.

    Returns (was_modified, list_of_fixes_applied).
    """
    activity_type = activity.get('type', 'unknown')
    type_schema = get_activity_schema(activity_type, base_schema)
    if not type_schema:
        return False, []

    allowed_properties = type_schema.get('properties', {}).keys()
    all_fixes = []

    all_fixes.extend(fix_invalid_top_level_properties(activity, activity_type, allowed_properties))

    # Type-specific fixes via dispatch table
    fixer = TYPE_FIXERS.get(activity_type)
    if fixer:
        all_fixes.extend(fixer(activity))
    elif activity_type in ('quiz', 'select'):
        all_fixes.extend(fix_quiz_select_items(activity, activity_type))

    if activity_type == 'select':
        all_fixes.extend(fix_select_property_renames(activity))

    all_fixes.extend(fix_missing_instruction(activity, activity_type))

    if activity_type == 'cloze':
        all_fixes.extend(fix_cloze_blank_lines(activity))

    return bool(all_fixes), all_fixes


def _fix_first_entry_indent(content: str) -> tuple[str, list[str]]:
    """Fix first-entry indent bug where first item has extra leading spaces."""
    lines = content.split('\n')
    if lines and re.match(r'^  - \S', lines[0]):
        has_root_entries = any(re.match(r'^- \S', l) for l in lines[1:])
        if has_root_entries:
            lines[0] = lines[0][2:]
            return '\n'.join(lines), ["Fixed first-entry indent bug (removed leading spaces)"]
    return content, []


def _convert_quotes_to_guillemets(text: str) -> str:
    """Convert ASCII double quotes to guillemets in alternating pairs."""
    result = []
    quote_open = False
    for char in text:
        if char == '"':
            result.append('\u00bb' if quote_open else '\u00ab')
            quote_open = not quote_open
        else:
            result.append(char)
    return ''.join(result)


def _fix_asterisk_quoting(content: str) -> tuple[str, list[str]]:
    """Convert double-quoted text fields containing asterisks to single quotes."""
    fixes = []
    fixed_lines = []

    for line in content.split('\n'):
        match = re.match(r'^(\s*text:\s*)"(.+)"(\s*)$', line)
        if match and '*' in match.group(2):
            prefix, text_content, suffix = match.group(1), match.group(2), match.group(3)
            text_content = text_content.replace('\\"', '"')
            text_content = _convert_quotes_to_guillemets(text_content)
            text_content = text_content.replace("'", "''")
            fixes.append("Converted double-quoted text with asterisks to single quotes")
            fixed_lines.append(f"{prefix}'{text_content}'{suffix}")
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines), fixes


def fix_raw_yaml_text(content: str) -> tuple[str, list[str]]:
    """Fix YAML issues at the raw text level (before parsing).

    Returns (fixed_content, list_of_fixes).
    """
    all_fixes = []
    content, fixes = _fix_first_entry_indent(content)
    all_fixes.extend(fixes)
    content, fixes = _fix_asterisk_quoting(content)
    all_fixes.extend(fixes)
    return content, all_fixes


def _get_forbidden_types(level_code: str, module_focus: str | None) -> tuple[set, str]:
    """Get forbidden activity types for a level/focus combination."""
    from ..config import LEVEL_CONFIG
    config_key = f"{level_code}-{module_focus}" if module_focus else level_code
    config = LEVEL_CONFIG.get(config_key, LEVEL_CONFIG.get(level_code, {}))
    return config.get('forbidden_types', set()), config_key


def _filter_activities(activities: list, forbidden_types: set, config_key: str) -> tuple[list, int, list[str]]:
    """Filter out forbidden activities, returning kept list, count removed, and messages."""
    kept = []
    removed = 0
    messages = []
    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            kept.append(activity)
            continue
        act_type = activity.get('type', '').lower()
        if act_type in forbidden_types:
            title = activity.get('title', f'Activity {i+1}')
            removed += 1
            messages.append(f"  \U0001f5d1\ufe0f  Removed [{act_type}] '{title[:40]}...' (forbidden in {config_key})")
        else:
            kept.append(activity)
    return kept, removed, messages


def _parse_yaml_activities(raw_content: str) -> tuple[list | None, list[str]]:
    """Parse YAML content and extract activities list."""
    try:
        data, duplicate_errors = safe_load_with_duplicate_check(raw_content)
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]

    warnings = [f"\u26a0\ufe0f CANNOT AUTO-FIX: {err}" for err in (duplicate_errors or [])]

    if not data:
        return None, warnings

    if isinstance(data, dict) and 'activities' in data:
        return data['activities'], warnings
    elif isinstance(data, list):
        return data, warnings
    return None, [*warnings, "Invalid YAML structure"]


def remove_forbidden_activities(yaml_path: Path, level_code: str, module_focus: str | None = None, dry_run: bool = False) -> tuple[int, list[str]]:
    """Remove forbidden activity types from a YAML activity file.

    Returns (num_removed, list_of_messages).
    """
    if not yaml_path.exists():
        return 0, []

    forbidden_types, config_key = _get_forbidden_types(level_code, module_focus)
    if not forbidden_types:
        return 0, ["No forbidden types defined for this level/track"]

    with open(yaml_path, encoding='utf-8') as f:
        raw_content = f.read()

    activities, parse_msgs = _parse_yaml_activities(raw_content)
    if activities is None:
        return 0, parse_msgs

    activities_to_keep, removed_count, all_messages = _filter_activities(
        activities, forbidden_types, config_key)

    if removed_count > 0:
        if not dry_run:
            try:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(activities_to_keep, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)
                all_messages.insert(0, f"\u2705 Removed {removed_count} forbidden activities from {yaml_path.name}")
            except Exception as e:
                all_messages.insert(0, f"\u274c Error saving: {e}")
                return 0, all_messages
        else:
            all_messages.insert(0, f"\U0001f50d DRY RUN: Would remove {removed_count} forbidden activities from {yaml_path.name}")

    return removed_count, all_messages


def _detect_track_schema(yaml_path: Path) -> dict | None:
    """Detect and load track-specific schema from the file path."""
    track_levels = ('a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit',
                    'hist', 'bio', 'istorio', 'oes', 'ruth',
                    'b2-pro', 'c1-pro')
    for parent in yaml_path.parents:
        if parent.name in track_levels:
            track_path = get_schemas_dir() / f"activities-{parent.name}.schema.json"
            if track_path.exists():
                with open(track_path, encoding='utf-8') as f:
                    return json.load(f)
            break
    return None


def _apply_raw_text_fixes(yaml_path: Path, dry_run: bool) -> tuple[str, list[str], int]:
    """Apply raw text fixes and return the fixed content."""
    with open(yaml_path, encoding='utf-8') as f:
        raw_content = f.read()

    fixed_content, raw_fixes = fix_raw_yaml_text(raw_content)
    total = 0
    if raw_fixes:
        total = len(raw_fixes)
        if not dry_run:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
        raw_content = fixed_content

    return raw_content, raw_fixes, total


def _extract_activities_list(data, all_fixes: list[str]) -> tuple[list | None, int]:
    """Extract the activities list from parsed YAML data."""
    if isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
        stripped_keys = [k for k in data if k != 'activities']
        if stripped_keys:
            all_fixes.append(f"\u2713 Stripped metadata keys from YAML: {', '.join(stripped_keys)}")
        all_fixes.append("\u2713 Unwrapped `activities:` dictionary to bare list (required format)")
        return activities, 1
    elif isinstance(data, list):
        return data, 0
    return None, 0


def _fix_all_activities(activities: list, fix_schema: dict, all_fixes: list[str]) -> int:
    """Apply schema fixes to each activity in the list."""
    total = 0
    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            continue
        modified, fixes = fix_activity_violations(activity, fix_schema)
        if modified:
            total += len(fixes)
            activity_title = activity.get('title', f'Activity {i+1}')[:40]
            all_fixes.append(f"[{i+1}] {activity_title}:")
            for fix in fixes:
                all_fixes.append(f"    \u2713 {fix}")
    return total


def _save_fixed_yaml(yaml_path: Path, activities: list, total_fixes: int,
                     all_fixes: list[str], dry_run: bool) -> tuple[int, list[str]]:
    """Save fixed activities to YAML file."""
    if total_fixes > 0 and not dry_run:
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(activities, f, allow_unicode=True,
                         default_flow_style=False, sort_keys=False)
            all_fixes.insert(0, f"\u2705 Saved {total_fixes} fixes to {yaml_path.name}")
        except Exception as e:
            all_fixes.insert(0, f"\u274c Error saving fixes: {e}")
            return 0, all_fixes
    elif total_fixes > 0 and dry_run:
        all_fixes.insert(0, f"\U0001f50d DRY RUN: Would apply {total_fixes} fixes to {yaml_path.name}")

    return total_fixes, all_fixes


def fix_yaml_file(yaml_path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Auto-fix schema violations in a YAML activity file.

    Returns (num_fixes_applied, list_of_fix_messages).
    """
    if not yaml_path.exists():
        return 0, []

    try:
        base_schema = load_base_schema()
    except FileNotFoundError as e:
        return 0, [f"Schema not found: {e}"]

    fix_schema = _detect_track_schema(yaml_path) or base_schema

    # Phase 1: Raw text fixes
    raw_content, raw_fixes, total_fixes = _apply_raw_text_fixes(yaml_path, dry_run)
    all_fixes = list(raw_fixes)

    # Phase 2: Parse YAML
    try:
        data, duplicate_errors = safe_load_with_duplicate_check(raw_content)
        if duplicate_errors:
            all_fixes.extend([f"\u26a0\ufe0f CANNOT AUTO-FIX: {err}" for err in duplicate_errors])
    except yaml.YAMLError as e:
        return total_fixes, [*all_fixes, f"YAML parse error (cannot auto-fix): {e}"]

    if not data:
        return 0, []

    # Phase 3: Extract activities list
    activities, unwrap_fixes = _extract_activities_list(data, all_fixes)
    if activities is None:
        return 0, ["Invalid YAML structure"]
    total_fixes += unwrap_fixes

    # Phase 4: Fix each activity
    total_fixes += _fix_all_activities(activities, fix_schema, all_fixes)

    # Phase 5: Save
    return _save_fixed_yaml(yaml_path, activities, total_fixes, all_fixes, dry_run)
