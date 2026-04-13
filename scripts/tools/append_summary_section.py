#!/usr/bin/env python3
"""Append a Summary section to built modules that are missing one.

Reads the module content + plan, generates a Summary via Gemini,
appends it before the activity markers. Much cheaper than re-running
the full write pipeline.

Usage:
    .venv/bin/python scripts/tools/append_summary_section.py a2 --dry-run
    .venv/bin/python scripts/tools/append_summary_points.py a2
    .venv/bin/python scripts/tools/append_summary_section.py a2 --slug a2-bridge
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

CURRICULUM = Path("curriculum/l2-uk-en")

PROMPT_TEMPLATE = """You are writing the final Summary section for a Ukrainian language module.

## Module: {title} (Level {level})
## Plan objectives:
{objectives}

## Current module content (last 500 words for context):
{tail_content}

## Plan Summary hints:
{summary_hints}

## Instructions:
Write a "## Підсумок — Summary" section (~{budget} words) that:
1. Reviews the key grammar/vocabulary concepts taught in this module
2. Uses specific Ukrainian examples from the content above
3. Includes 2-3 self-check questions for the learner
4. Matches the teaching style and tone of the rest of the module
5. Uses stress marks on Ukrainian words (like the rest of the module)

Output ONLY the section content starting with the H2 heading. No preamble.
"""


def _find_insertion_point(content: str) -> int:
    """Find where to insert Summary — before activity markers or at end."""
    # Look for first activity marker (INJECT_ACTIVITY or exercise block)
    patterns = [
        r'\n<!-- INJECT[_-]ACTIVITY',
        r'\n## 📝',  # Exercise blocks
        r'\n## Вправи',  # Exercise heading
        r'\n---\s*\n\s*<',  # MDX component separator
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.start()
    return len(content)


def _call_gemini(prompt: str) -> str | None:
    """Call Gemini and return response text."""
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash", "-p", prompt],
            capture_output=True, text=True, timeout=180,
        )
        if result.returncode != 0:
            print(f"    Gemini error: {result.stderr[:200]}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("    Gemini timeout")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def process_module(level: str, slug: str, dry_run: bool = False) -> bool:
    """Append Summary section to a module. Returns True if modified."""
    md_path = CURRICULUM / level / f"{slug}.md"
    plan_path = CURRICULUM / "plans" / level / f"{slug}.yaml"

    if not md_path.exists() or not plan_path.exists():
        return False

    content = md_path.read_text("utf-8")

    # Check if Summary already exists
    if re.search(r'^## .*(?:Summary|Підсумок)', content, re.MULTILINE | re.IGNORECASE):
        return False

    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    if not plan:
        return False

    if dry_run:
        print(f"    Would append Summary to: {slug}")
        return True

    # Build prompt
    objectives = "\n".join(f"- {o}" for o in (plan.get("objectives") or []))

    # Get Summary hints from plan
    summary_hints = ""
    for s in plan.get("content_outline", []):
        if isinstance(s, dict) and ("summary" in s.get("section", "").lower() or "підсумок" in s.get("section", "").lower()):
            points = s.get("points", [])
            summary_hints = "\n".join(f"- {p}" for p in points)
            budget = s.get("words", 200)
            break
    else:
        budget = 200

    # Get last 500 words of content for context
    words = content.split()
    tail = " ".join(words[-500:]) if len(words) > 500 else content

    prompt = PROMPT_TEMPLATE.format(
        title=plan.get("title", slug),
        level=plan.get("level", level.upper()),
        objectives=objectives or "(none)",
        tail_content=tail[-2000:],  # Cap at 2000 chars
        summary_hints=summary_hints or "(generate based on module content)",
        budget=budget,
    )

    response = _call_gemini(prompt)
    if not response:
        print(f"    ❌ Failed: {slug}")
        return False

    # Clean response — ensure it starts with ##
    if not response.startswith("##"):
        # Try to find the heading
        match = re.search(r'^## .*(?:Summary|Підсумок)', response, re.MULTILINE)
        response = response[match.start():] if match else f"## Підсумок — Summary\n\n{response}"

    # Insert before activity markers
    insert_at = _find_insertion_point(content)
    new_content = content[:insert_at] + "\n\n" + response + "\n" + content[insert_at:]

    md_path.write_text(new_content, "utf-8")
    word_count = len(response.split())
    print(f"    ✅ {slug}: +{word_count} words")
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    slug_filter = None
    for i, a in enumerate(sys.argv):
        if a == "--slug" and i + 1 < len(sys.argv):
            slug_filter = set(sys.argv[i + 1].split(","))

    levels = args if args else ["a2"]
    total = 0

    for level in levels:
        level_dir = CURRICULUM / level
        if not level_dir.exists():
            continue
        print(f"\n=== {level.upper()} ===")
        count = 0
        for md_file in sorted(level_dir.glob("*.md")):
            slug = md_file.stem
            if slug_filter and slug not in slug_filter:
                continue
            if process_module(level, slug, dry_run=dry_run):
                count += 1
                if not dry_run:
                    time.sleep(1)
        print(f"  {level.upper()}: {count} modules {'would be ' if dry_run else ''}updated")
        total += count

    print(f"\nTotal: {total} modules {'would be ' if dry_run else ''}updated")


if __name__ == "__main__":
    main()
