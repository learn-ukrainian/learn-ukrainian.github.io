#!/usr/bin/env python3
"""Phase 2: Enrich generic Summary points with module-specific content.

Reads each plan's objectives + content_outline, generates custom Summary
bullet points via Gemini. Only processes plans with generic placeholder points.

Usage:
    # Dry run (show what would be processed)
    .venv/bin/python scripts/tools/enrich_summary_points.py a2 --dry-run

    # Process a single level
    .venv/bin/python scripts/tools/enrich_summary_points.py a2

    # Process specific slugs
    .venv/bin/python scripts/tools/enrich_summary_points.py a2 --slug genitive-intro,aspect-concept

    # All levels
    .venv/bin/python scripts/tools/enrich_summary_points.py a2 b1 b2 c1 c2
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

GENERIC_MARKERS = [
    "Review key concepts from this module",
    "Self-check questions for the learner",
]

PROMPT_TEMPLATE = """You are a curriculum designer for a Ukrainian language course.

Given this plan for module "{title}" (level {level}), generate 2-3 specific Summary bullet points.

## Plan objectives:
{objectives}

## Content outline sections:
{sections}

## Grammar scope:
{grammar}

## Requirements:
1. Name the specific grammar rules or vocabulary patterns to review
2. Include 1-2 concrete self-check questions (e.g., "What is the difference between X and Y?", "How do you say Z in Ukrainian?")
3. Reference specific Ukrainian examples from the content outline
4. Keep total under 200 words

## Gold standard example (from A1 colors module):
"Color agreement follows the same rules as M09: Hard-stem: червоний стіл, червона книга, червоне вікно. Soft-stem: синій стіл, синя книга, синє вікно. Self-check: What color is the Ukrainian flag? (синьо-жовтий) Describe 3 things in your room using colors."

Output ONLY a JSON array of 2-3 strings. No markdown, no explanation.
Example: ["Point 1 with specific grammar...", "Point 2 with self-check questions..."]
"""


def _is_generic(points: list) -> bool:
    """Check if Summary points are generic placeholders."""
    if not points:
        return True
    return any(
        any(marker in str(p) for marker in GENERIC_MARKERS)
        for p in points
    )


def _get_summary_section(plan: dict) -> dict | None:
    """Find the Summary section in content_outline."""
    for s in plan.get("content_outline", []):
        if not isinstance(s, dict):
            continue
        name = s.get("section", "")
        if "Summary" in name or "Підсумок" in name:
            return s
    return None


def _build_prompt(plan: dict) -> str:
    """Build the Gemini prompt for a plan."""
    objectives = "\n".join(f"- {o}" for o in (plan.get("objectives") or []))
    sections = "\n".join(
        f"- {s.get('section', '?')}: {'; '.join(str(p) for p in (s.get('points') or [])[:2])}"
        for s in plan.get("content_outline", [])
        if isinstance(s, dict) and "Summary" not in s.get("section", "")
    )
    grammar = ", ".join(plan.get("grammar_scope", []) or plan.get("grammar", []) or ["(not specified)"])

    return PROMPT_TEMPLATE.format(
        title=plan.get("title", "?"),
        level=plan.get("level", "?"),
        objectives=objectives or "(none)",
        sections=sections or "(none)",
        grammar=grammar,
    )


def _call_gemini(prompt: str) -> list[str] | None:
    """Call Gemini CLI and parse JSON response."""
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash", "-p", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"    Gemini error: {result.stderr[:200]}")
            return None

        # Parse JSON from response (may have markdown fencing)
        text = result.stdout.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = "\n".join(text.split("\n")[:-1])
        text = text.strip()

        points = json.loads(text)
        if isinstance(points, list) and all(isinstance(p, str) for p in points):
            return points
        print(f"    Unexpected format: {type(points)}")
        return None
    except subprocess.TimeoutExpired:
        print("    Gemini timeout")
        return None
    except (json.JSONDecodeError, Exception) as e:
        print(f"    Parse error: {e}")
        return None


def _bump_version(version: str) -> str:
    parts = str(version).split(".")
    if len(parts) <= 2:
        return f"{version}.1"
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def process_plan(plan_path: Path, dry_run: bool = False) -> bool:
    """Process a single plan. Returns True if modified."""
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    if not plan:
        return False

    summary = _get_summary_section(plan)
    if not summary:
        return False

    if not _is_generic(summary.get("points", [])):
        return False  # Already has custom points

    if dry_run:
        print(f"    Would enrich: {plan_path.stem}")
        return True

    prompt = _build_prompt(plan)
    points = _call_gemini(prompt)
    if not points:
        print(f"    ❌ Failed: {plan_path.stem}")
        return False

    summary["points"] = points
    old_v = str(plan.get("version", "3.0"))
    plan["version"] = _bump_version(old_v)

    plan_path.write_text(
        yaml.dump(plan, allow_unicode=True, sort_keys=False, width=120),
        "utf-8",
    )
    print(f"    ✅ {plan_path.stem}: {len(points)} points, v{old_v}→{plan['version']}")
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    slug_filter = None
    for i, a in enumerate(sys.argv):
        if a == "--slug" and i + 1 < len(sys.argv):
            slug_filter = set(sys.argv[i + 1].split(","))

    levels = args if args else ["a2", "b1", "b2", "c1", "c2"]
    total = 0

    for level in levels:
        plans_dir = Path(f"curriculum/l2-uk-en/plans/{level}")
        if not plans_dir.exists():
            continue
        print(f"\n=== {level.upper()} ===")
        count = 0
        for p in sorted(plans_dir.glob("*.yaml")):
            if slug_filter and p.stem not in slug_filter:
                continue
            if process_plan(p, dry_run=dry_run):
                count += 1
                if not dry_run:
                    time.sleep(1)  # Rate limit
        print(f"  {level.upper()}: {count} plans {'would be ' if dry_run else ''}enriched")
        total += count

    print(f"\nTotal: {total} plans {'would be ' if dry_run else ''}enriched")


if __name__ == "__main__":
    main()
