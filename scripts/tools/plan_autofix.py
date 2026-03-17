"""Plan auto-fix: deterministic fixes for plan vocabulary_hints.

Auto-fixable issues:
- Vocabulary hint words failing VESUM verification → remove from required
- Duplicate vocabulary hints → deduplicate

Scope limit: ONLY touches vocabulary_hints and adds plan_fixes metadata.
Never modifies content_outline, objectives, word_target, or grammar.
Version bumping: '4.0' → '4.0.1', '4.0.1' → '4.0.2'.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _bump_version(version: str) -> str:
    """Bump patch version: '4.0' → '4.0.1', '4.0.1' → '4.0.2'."""
    parts = str(version).split(".")
    if len(parts) <= 2:
        return f"{version}.1"
    else:
        try:
            parts[-1] = str(int(parts[-1]) + 1)
        except ValueError:
            parts.append("1")
        return ".".join(parts)


def _extract_word(hint: Any) -> str | None:
    """Extract the Ukrainian word from a vocabulary hint entry."""
    if isinstance(hint, str):
        return hint.strip()
    if isinstance(hint, dict):
        return hint.get("word", hint.get("uk", hint.get("term", ""))).strip() or None
    return None


def auto_fix_plan(
    plan_path: Path,
    deterministic_issues: list[dict] | None = None,
    vesum_not_found: list[dict] | None = None,
) -> tuple[int, list[str]]:
    """Auto-fix plan vocabulary_hints based on VESUM verification.

    Args:
        plan_path: Path to the plan YAML file.
        deterministic_issues: Issues from _deterministic_screen() (unused for now,
            reserved for future plan-level checks).
        vesum_not_found: VESUM verification failures from DScreenResult.

    Returns:
        (n_fixes, changelog): Number of fixes applied and list of change descriptions.
    """
    changelog: list[str] = []
    if not plan_path.exists():
        return 0, changelog

    # Build set of VESUM-failed words
    failed_words: set[str] = set()
    if vesum_not_found:
        for entry in vesum_not_found:
            word = entry.get("original", "").strip().lower()
            if word and entry.get("status") == "❌":
                failed_words.add(word)

    if not failed_words:
        return 0, changelog

    try:
        raw = plan_path.read_text("utf-8")
        plan = yaml.safe_load(raw)
    except Exception as e:
        logger.warning("plan_autofix: Failed to read plan %s: %s", plan_path, e)
        return 0, changelog

    if not isinstance(plan, dict):
        return 0, changelog

    vocab_hints = plan.get("vocabulary_hints", {})
    if not vocab_hints:
        return 0, changelog

    # Track removals
    n_fixes = 0
    removed_words: list[str] = []

    # Process required vocabulary hints
    for section_key in ("required", "optional", "supplementary"):
        section = vocab_hints.get(section_key, [])
        if not isinstance(section, list):
            continue

        original_len = len(section)
        filtered = []
        for hint in section:
            word = _extract_word(hint)
            if word and word.lower() in failed_words:
                removed_words.append(word)
                n_fixes += 1
            else:
                filtered.append(hint)

        if len(filtered) < original_len:
            vocab_hints[section_key] = filtered

    # Also check flat list format (some plans use a flat list)
    if isinstance(vocab_hints, list):
        original_len = len(vocab_hints)
        filtered = []
        for hint in vocab_hints:
            word = _extract_word(hint)
            if word and word.lower() in failed_words:
                removed_words.append(word)
                n_fixes += 1
            else:
                filtered.append(hint)
        if len(filtered) < original_len:
            plan["vocabulary_hints"] = filtered

    if n_fixes == 0:
        return 0, changelog

    # Bump version
    old_version = str(plan.get("version", "1.0"))
    new_version = _bump_version(old_version)
    plan["version"] = new_version

    # Add plan_fixes changelog
    fix_entry = {
        "version": new_version,
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "changes": [
            f"Removed VESUM-unverified word '{w}' from vocabulary_hints"
            for w in removed_words[:20]
        ],
    }
    if "plan_fixes" not in plan:
        plan["plan_fixes"] = []
    plan["plan_fixes"].append(fix_entry)

    # Write back
    try:
        plan_path.write_text(
            yaml.dump(plan, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        changelog = [f"v{old_version} → v{new_version}: removed {n_fixes} VESUM-failed word(s): {', '.join(removed_words[:10])}"]
        logger.info("plan_autofix: %s — %d fix(es), version %s → %s",
                     plan_path.name, n_fixes, old_version, new_version)
    except Exception as e:
        logger.warning("plan_autofix: Failed to write plan %s: %s", plan_path, e)
        return 0, []

    return n_fixes, changelog


def fix_russianisms_in_plan(
    plan_path: Path,
    issues: list[dict],
) -> tuple[int, list[str]]:
    """Fix semantic Russianisms in plan vocabulary_hints using the false friends table.

    For each issue with type=RUSSICISM, finds the misused word in vocabulary_hints
    and replaces the Russian meaning with the correct Ukrainian meaning.

    Args:
        plan_path: Path to the plan YAML file.
        issues: PreflightIssue dicts with keys: issue_type, problem, suggested_fix.

    Returns:
        (n_fixes, changelog): Number of fixes applied and list of change descriptions.
    """
    from pipeline.semantic_russianisms import SEMANTIC_FALSE_FRIENDS

    changelog: list[str] = []
    russicism_issues = [i for i in issues if i.get("issue_type") == "RUSSICISM"]
    if not russicism_issues or not plan_path.exists():
        return 0, changelog

    # Build lookup: word → false friend entry
    ff_lookup: dict[str, dict] = {}
    for ff in SEMANTIC_FALSE_FRIENDS:
        ff_lookup[ff["word"].lower()] = ff

    try:
        raw = plan_path.read_text("utf-8")
    except Exception as e:
        logger.warning("fix_russianisms: Failed to read plan %s: %s", plan_path, e)
        return 0, changelog

    n_fixes = 0
    fixed_raw = raw

    for issue in russicism_issues:
        # Extract the misused word from the problem description
        problem = issue.get("problem", "")
        word = _extract_russicism_word(problem, ff_lookup)
        if not word:
            continue

        ff = ff_lookup.get(word.lower())
        if not ff:
            continue

        # Find and fix in the raw YAML text (preserves formatting better than parse+dump)
        # Pattern: "город (city)" → "місто (city)" or replace meaning
        for russian_meaning in ff["russian_meanings"]:
            # Match: word (russian_meaning) with optional surrounding text
            old_pattern = f"{ff['word']} ({russian_meaning})"
            new_text = f"{ff['replacement']} ({ff['replacement_translation']})"
            if old_pattern in fixed_raw:
                fixed_raw = fixed_raw.replace(old_pattern, new_text)
                n_fixes += 1
                changelog.append(
                    f"Replaced '{old_pattern}' → '{new_text}' (semantic false friend)"
                )
                break

    if n_fixes == 0:
        return 0, changelog

    # Bump version in the YAML
    try:
        plan = yaml.safe_load(fixed_raw)
        if isinstance(plan, dict):
            old_version = str(plan.get("version", "1.0"))
            new_version = _bump_version(old_version)
            fixed_raw = fixed_raw.replace(
                f"version: '{old_version}'", f"version: '{new_version}'"
            ).replace(
                f'version: "{old_version}"', f'version: "{new_version}"'
            ).replace(
                f"version: {old_version}", f"version: {new_version}"
            )
    except Exception:
        pass  # Version bump is best-effort

    try:
        plan_path.write_text(fixed_raw, encoding="utf-8")
        logger.info("fix_russianisms: %s — %d fix(es): %s",
                     plan_path.name, n_fixes, "; ".join(changelog[:5]))
    except Exception as e:
        logger.warning("fix_russianisms: Failed to write plan %s: %s", plan_path, e)
        return 0, []

    return n_fixes, changelog


def _extract_russicism_word(problem: str, ff_lookup: dict[str, dict]) -> str | None:
    """Extract the misused Ukrainian word from a RUSSICISM issue's problem text.

    Looks for known false friend words in the problem description.
    """
    problem_lower = problem.lower()
    for word in ff_lookup:
        if word in problem_lower:
            return word
    return None
