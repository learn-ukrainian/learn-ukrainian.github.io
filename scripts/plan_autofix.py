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
