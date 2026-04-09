"""Generate Starlight landing pages for all tracks from curriculum.yaml.

Reads curriculum.yaml + plan files + status files to produce
accurate landing pages with correct slugs, titles, and build statuses.

Usage:
    .venv/bin/python scripts/generate_landing_pages.py [--track a1]
    .venv/bin/python scripts/generate_landing_pages.py --all
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
STARLIGHT_DOCS = PROJECT_ROOT / "starlight" / "src" / "content" / "docs"

# Track display config
TRACK_CONFIG = {
    "a1": {"title": "A1 — Beginner", "uk_title": "Перші кроки", "uk_sub": "First Steps", "color": "#2E7D32", "word_target": 1200},
    "a2": {"title": "A2 — Elementary", "uk_title": "Мій світ", "uk_sub": "My World", "color": "#1565C0", "word_target": 2000},
    "b1": {"title": "B1 — Intermediate", "uk_title": "Крок вперед", "uk_sub": "A Step Forward", "color": "#6A1B9A", "word_target": 4000},
    "b2": {"title": "B2 — Upper Intermediate", "uk_title": "Впевнено", "uk_sub": "With Confidence", "color": "#BF360C", "word_target": 4000},
    "c1": {"title": "C1 — Advanced", "uk_title": "Вільно", "uk_sub": "Freely", "color": "#37474F", "word_target": 4000},
    "c2": {"title": "C2 — Mastery", "uk_title": "Досконало", "uk_sub": "Mastery", "color": "#212121", "word_target": 5000},
}


def get_module_status(level: str, slug: str) -> str:
    """Check if module is built and passing audit."""
    status_path = CURRICULUM_ROOT / level / "status" / f"{slug}.json"
    content_path = CURRICULUM_ROOT / level / f"{slug}.md"

    if not content_path.exists():
        return "locked"

    if status_path.exists():
        try:
            data = json.loads(status_path.read_text("utf-8"))
            overall = data.get("overall", {}).get("status", "")
            if overall == "pass":
                return "done"
        except (json.JSONDecodeError, KeyError):
            pass

    return "active"  # Content exists but not passing


def get_plan_data(level: str, slug: str) -> dict:
    """Read plan file for title and subtitle."""
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if plan_path.exists():
        try:
            return yaml.safe_load(plan_path.read_text("utf-8")) or {}
        except yaml.YAMLError:
            pass
    return {}


def escape_js_string(s: str | int | float) -> str:
    """Escape string for JavaScript object literal."""
    s = str(s) if not isinstance(s, str) else s
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def generate_landing_page(level: str) -> str:
    """Generate landing page MDX for a track."""
    curriculum = yaml.safe_load((CURRICULUM_ROOT / "curriculum.yaml").read_text("utf-8"))
    level_data = curriculum.get("levels", {}).get(level, {})
    modules = level_data.get("modules", [])

    if not modules:
        print(f"  ⚠️  No modules found for {level}")
        return ""

    config = TRACK_CONFIG.get(level, {
        "title": f"{level.upper()}",
        "uk_title": level.upper(),
        "uk_sub": "",
        "color": "#546E7A",
        "word_target": 4000,
    })

    # Group modules by phase — consolidate (same phase may appear at multiple positions)
    from collections import OrderedDict
    phase_items: OrderedDict[str, list[str]] = OrderedDict()
    done_count = 0

    for i, slug in enumerate(modules, 1):
        plan = get_plan_data(level, slug)
        title = plan.get("title", slug.replace("-", " ").title())
        subtitle = plan.get("subtitle", "")
        phase = plan.get("phase", "")

        unit_name = phase if phase else f"{level.upper()} Modules"

        if unit_name not in phase_items:
            phase_items[unit_name] = []

        status = get_module_status(level, slug)
        if status == "done":
            done_count += 1

        sub_escaped = escape_js_string(subtitle[:80])
        title_escaped = escape_js_string(title)

        phase_items[unit_name].append(
            f'        {{ num: {i}, slug: "{slug}", title: "{title_escaped}", '
            f'sub: "{sub_escaped}", status: "{status}" }}'
        )

    units = list(phase_items.items())

    # Build the modules JS array
    modules_js_lines = []
    for unit_name, items in units:
        unit_escaped = escape_js_string(unit_name)
        modules_js_lines.append("    {")
        modules_js_lines.append(f'      unit: "{unit_escaped}",')
        modules_js_lines.append("      items: [")
        modules_js_lines.append(",\n".join(items) + ",")
        modules_js_lines.append("      ]")
        modules_js_lines.append("    },")

    modules_js = "\n".join(modules_js_lines)

    description = f"{config.get('uk_sub', '')} — {len(modules)} modules"

    mdx = f"""---
title: "{config['title']}"
description: "{escape_js_string(description)}"
template: splash
---

import LevelLanding from '@site/src/components/LevelLanding';

<LevelLanding
  client:load
  level="{level.upper()}"
  title="{config['uk_title']}"
  subtitle="{config.get('uk_sub', '')} — {done_count}/{len(modules)} modules complete"
  moduleCount={{{len(modules)}}}
  wordTarget={{{config['word_target']}}}
  color="{config['color']}"
  modules={{[
{modules_js}
  ]}}
/>
"""
    return mdx


def main():
    parser = argparse.ArgumentParser(description="Generate Starlight landing pages")
    parser.add_argument("--track", help="Generate for specific track (e.g., a1)")
    parser.add_argument("--all", action="store_true", help="Generate for all tracks")
    args = parser.parse_args()

    curriculum = yaml.safe_load((CURRICULUM_ROOT / "curriculum.yaml").read_text("utf-8"))
    levels = curriculum.get("levels", {})

    tracks = []
    if args.track:
        tracks = [args.track]
    elif args.all:
        tracks = [k for k in levels if levels[k].get("modules")]
    else:
        tracks = [k for k in levels if levels[k].get("modules")]

    for level in tracks:
        if level not in levels:
            print(f"⚠️  Track {level} not in curriculum.yaml, skipping")
            continue

        print(f"Generating {level.upper()} landing page...")
        mdx = generate_landing_page(level)
        if not mdx:
            continue

        out_dir = STARLIGHT_DOCS / level
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.mdx"
        out_path.write_text(mdx, "utf-8")
        print(f"  ✅ {out_path}")


if __name__ == "__main__":
    main()
