"""Upgrade vague A1 activity_hints to exact exercise templates using Gemini.

Reads plan YAML files, identifies vague activity_hints (no Ukrainian text,
no exercise markers like ↔/→/___/{}), sends them to Gemini with the full
plan context, and writes back upgraded hints with version bump + backup.

Usage:
    .venv/bin/python scripts/tools/upgrade_activity_hints.py a1 sounds-letters-and-hello
    .venv/bin/python scripts/tools/upgrade_activity_hints.py a1 --all
    .venv/bin/python scripts/tools/upgrade_activity_hints.py a1 --all --dry-run
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

# Add scripts/ to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tools.plan_autofix import _bump_version

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_DIR = REPO_ROOT / "curriculum" / "l2-uk-en" / "plans"

# Markers that indicate a hint is already specific (has real Ukrainian content)
_SPECIFICITY_MARKERS = re.compile(r"[↔→{}«»]|___|\|")

# Cyrillic character range for detecting Ukrainian text in hints
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]{2,}")

# Minimum number of Cyrillic words to consider a hint "specific"
_MIN_CYRILLIC_WORDS = 2

GEMINI_CLI = shutil.which("gemini") or "gemini"

# Snapshot environment (same as bridge uses)
import os

_PARENT_ENV = os.environ.copy()
_PARENT_ENV["GEMINI_SESSION"] = "1"


def is_hint_vague(hint: dict) -> bool:
    """Determine if an activity_hint is vague (lacks concrete Ukrainian content).

    A hint is vague if its 'focus' field:
    - Has no exercise markers (↔, →, ___, {}, |)
    - Has fewer than 2 Cyrillic words
    - Has no 'pairs' or 'items' with Ukrainian content

    Returns True if the hint needs upgrading.
    """
    focus = hint.get("focus", "")
    if not isinstance(focus, str):
        focus = str(focus)

    # Check focus for specificity markers
    if _SPECIFICITY_MARKERS.search(focus):
        return False

    # Count Cyrillic words in focus
    cyrillic_words = _CYRILLIC_RE.findall(focus)
    if len(cyrillic_words) >= _MIN_CYRILLIC_WORDS:
        return False

    # Check if 'pairs' or 'items' contain Ukrainian content
    for key in ("pairs", "items"):
        items = hint.get(key)
        if isinstance(items, list):
            items_text = " ".join(str(i) for i in items)
            if _SPECIFICITY_MARKERS.search(items_text):
                return False
            cyrillic_in_items = _CYRILLIC_RE.findall(items_text)
            if len(cyrillic_in_items) >= _MIN_CYRILLIC_WORDS:
                return False

    return True


def count_vague_hints(plan: dict) -> tuple[int, int]:
    """Count (vague, total) activity_hints in a plan."""
    hints = plan.get("activity_hints", [])
    if not isinstance(hints, list):
        return 0, 0
    vague = sum(1 for h in hints if isinstance(h, dict) and is_hint_vague(h))
    return vague, len(hints)


def build_gemini_prompt(plan: dict, plan_text: str) -> str:
    """Build the prompt for Gemini to upgrade vague activity_hints."""
    # Identify which hints are vague
    hints = plan.get("activity_hints", [])
    vague_indices = [
        i for i, h in enumerate(hints) if isinstance(h, dict) and is_hint_vague(h)
    ]

    vague_hints_yaml = yaml.dump(
        [hints[i] for i in vague_indices],
        allow_unicode=True,
        default_flow_style=False,
    )

    return f"""\
You are upgrading activity_hints in a Ukrainian language curriculum plan from vague descriptions to exact exercise templates.

## Full Plan
```yaml
{plan_text}
```

## Vague Hints to Upgrade (indices: {vague_indices})
```yaml
{vague_hints_yaml}
```

## Task
Generate specific exercise templates for EACH vague hint above. Rules:

1. Use ONLY vocabulary from this plan's vocabulary_hints (required + recommended)
2. Include actual Ukrainian sentences, word pairs, or fill-in patterns
3. Stay within this module's grammar scope — do NOT use grammar not yet taught
4. Use textbook exercise patterns: "Оберіть правильний варіант...", "Складіть речення..."
5. Keep the same 'type' and 'items' count (or increase if needed for good coverage)
6. For quiz: include actual questions with answer options separated by |
7. For match-up: include actual pairs with ↔
8. For fill-in: include sentences with {{blanks}} and options in parentheses separated by |
9. For group-sort: include actual items to sort into named groups

## Output Format
Return ONLY a YAML array (no ```yaml fences, no commentary) with the upgraded hints.
Each hint must have: type, focus, items (count or list).
The array must have exactly {len(vague_indices)} elements, one per vague hint, in the same order.

Example output format:
- type: quiz
  focus: "Люблю or подобається? Я ___ читати. (люблю | подобається) | Мені ___ ця книга. (люблю | подобається)"
  items: 8
- type: match-up
  focus: "Match greeting to response"
  pairs:
  - "Привіт! ↔ Привіт!"
  - "Як справи? ↔ Добре, дякую."
"""


def call_gemini(prompt: str, model: str = "gemini-3.1-pro-preview",
                timeout: int = 120) -> str | None:
    """Call Gemini CLI with a prompt and return stdout."""
    try:
        result = subprocess.run(
            [GEMINI_CLI, "-m", model, "-y"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT),
            env=_PARENT_ENV,
        )
        if result.returncode != 0:
            logger.error("Gemini CLI failed (exit %d): %s", result.returncode, result.stderr[:500])
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.error("Gemini CLI timed out after %ds", timeout)
        return None
    except FileNotFoundError:
        logger.error("Gemini CLI not found at: %s", GEMINI_CLI)
        return None


def parse_gemini_response(response: str) -> list[dict] | None:
    """Parse Gemini's YAML response into a list of activity_hints."""
    # Strip markdown fences if present
    cleaned = response.strip()
    if cleaned.startswith("```"):
        # Remove first line (```yaml or ```)
        lines = cleaned.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == "```":
                end = i
                break
        cleaned = "\n".join(lines[start:end])

    try:
        parsed = yaml.safe_load(cleaned)
    except yaml.YAMLError as e:
        logger.error("Failed to parse Gemini YAML response: %s", e)
        return None

    if not isinstance(parsed, list):
        logger.error("Gemini response is not a YAML list: %s", type(parsed))
        return None

    # Validate each hint has required fields
    for i, hint in enumerate(parsed):
        if not isinstance(hint, dict):
            logger.error("Hint %d is not a dict: %s", i, type(hint))
            return None
        if "type" not in hint or "focus" not in hint:
            logger.error("Hint %d missing 'type' or 'focus': %s", i, hint)
            return None

    return parsed


def upgrade_plan(
    plan_path: Path,
    *,
    dry_run: bool = False,
    model: str = "gemini-3.1-pro-preview",
) -> tuple[int, list[str]]:
    """Upgrade vague activity_hints in a plan file.

    Returns (n_upgraded, changelog).
    """
    changelog: list[str] = []

    if not plan_path.exists():
        logger.warning("Plan not found: %s", plan_path)
        return 0, changelog

    raw = plan_path.read_text("utf-8")
    plan = yaml.safe_load(raw)
    if not isinstance(plan, dict):
        return 0, changelog

    hints = plan.get("activity_hints", [])
    if not isinstance(hints, list):
        return 0, changelog

    vague_indices = [
        i for i, h in enumerate(hints) if isinstance(h, dict) and is_hint_vague(h)
    ]
    if not vague_indices:
        logger.info("No vague hints in %s — skipping", plan_path.name)
        return 0, changelog

    slug = plan_path.stem
    print(f"  {slug}: {len(vague_indices)}/{len(hints)} vague hints")

    if dry_run:
        for idx in vague_indices:
            h = hints[idx]
            print(f"    [{idx}] {h.get('type', '?')}: {h.get('focus', '?')[:80]}")
        return len(vague_indices), [f"[dry-run] {len(vague_indices)} vague hints in {slug}"]

    # Build prompt and call Gemini
    prompt = build_gemini_prompt(plan, raw)
    print(f"  Calling Gemini ({model})...")
    response = call_gemini(prompt, model=model)
    if not response:
        logger.error("No response from Gemini for %s", slug)
        return 0, changelog

    # Parse response
    upgraded = parse_gemini_response(response)
    if not upgraded:
        logger.error("Failed to parse Gemini response for %s", slug)
        return 0, changelog

    if len(upgraded) != len(vague_indices):
        logger.error(
            "Gemini returned %d hints but expected %d for %s",
            len(upgraded), len(vague_indices), slug,
        )
        return 0, changelog

    # Replace vague hints with upgraded ones
    for i, idx in enumerate(vague_indices):
        hints[idx] = upgraded[i]

    plan["activity_hints"] = hints

    # Bump version
    old_version = str(plan.get("version", "1.0"))
    new_version = _bump_version(old_version)
    plan["version"] = new_version

    # Add plan_fixes entry
    fix_entry = {
        "version": new_version,
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "changes": [
            f"Upgraded {len(vague_indices)} vague activity_hints to exact exercise templates (Gemini)"
        ],
    }
    if "plan_fixes" not in plan:
        plan["plan_fixes"] = []
    plan["plan_fixes"].append(fix_entry)

    # Backup and write
    backup_path = plan_path.with_suffix(".yaml.bak")
    shutil.copy2(plan_path, backup_path)
    print(f"  Backup: {backup_path.name}")

    plan_path.write_text(
        yaml.dump(plan, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    changelog.append(
        f"v{old_version} → v{new_version}: upgraded {len(vague_indices)} activity_hints in {slug}"
    )
    print(f"  Done: {changelog[0]}")
    return len(vague_indices), changelog


def get_all_plan_paths(level: str) -> list[Path]:
    """Get all plan YAML paths for a level, sorted by name."""
    level_dir = PLANS_DIR / level
    if not level_dir.is_dir():
        logger.error("Plans directory not found: %s", level_dir)
        return []
    return sorted(level_dir.glob("*.yaml"))


def main():
    parser = argparse.ArgumentParser(
        description="Upgrade vague activity_hints to exact exercise templates using Gemini"
    )
    parser.add_argument("level", help="Level (e.g., a1)")
    parser.add_argument("slug", nargs="?", help="Module slug (or --all for all plans)")
    parser.add_argument("--all", action="store_true", help="Process all plans with vague hints")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without modifying")
    parser.add_argument("--model", default="gemini-3.1-pro-preview", help="Gemini model to use")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.all:
        paths = get_all_plan_paths(args.level)
        if not paths:
            print(f"No plans found for level {args.level}")
            sys.exit(1)
    elif args.slug:
        plan_path = PLANS_DIR / args.level / f"{args.slug}.yaml"
        if not plan_path.exists():
            print(f"Plan not found: {plan_path}")
            sys.exit(1)
        paths = [plan_path]
    else:
        parser.error("Provide a slug or use --all")
        return  # unreachable but makes type checker happy

    total_upgraded = 0
    total_changelog: list[str] = []

    action = "Scanning" if args.dry_run else "Upgrading"
    print(f"\n{action} {len(paths)} plan(s) in {args.level}...\n")

    for path in paths:
        n, changes = upgrade_plan(path, dry_run=args.dry_run, model=args.model)
        total_upgraded += n
        total_changelog.extend(changes)

    print(f"\n{'=' * 50}")
    if args.dry_run:
        print(f"Dry run: {total_upgraded} vague hints found across {len(paths)} plan(s)")
    else:
        print(f"Upgraded {total_upgraded} hints across {len(total_changelog)} plan(s)")
    for entry in total_changelog:
        print(f"  {entry}")


if __name__ == "__main__":
    main()
