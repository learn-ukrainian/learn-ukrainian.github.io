"""Generate Site landing pages for all tracks from curriculum.yaml.

Reads curriculum.yaml + plan files + status files to produce
accurate landing pages with correct slugs, titles, and build statuses.

Usage:
    .venv/bin/python scripts/generate_landing_pages.py [--track a1]
    .venv/bin/python scripts/generate_landing_pages.py --all
    .venv/bin/python scripts/generate_landing_pages.py --track b2 --check
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, OrderedDict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SITE_DOCS = PROJECT_ROOT / "site" / "src" / "content" / "docs"

# Track display config
TRACK_CONFIG = {
    "a1": {
        "title": "A1 — Beginner · Перші кроки",
        "uk_title": "Перші кроки · First Steps",
        "uk_sub": "Ukrainian for absolute beginners",
        "word_target": 1200,
    },
    "a2": {
        "title": "A2 — Pre-Intermediate Course",
        "uk_title": "Перші кроки далі",
        "uk_sub": "Pre-Intermediate Ukrainian course",
        "word_target": 2000,
    },
    "b1": {
        "title": "B1 — Intermediate",
        "uk_title": "Крок вперед",
        "uk_sub": "Intermediate Ukrainian course",
        "word_target": 4000,
    },
    "b2": {
        "title": "B2 — Upper Intermediate",
        "uk_title": "Впевнено · Confident Ukrainian",
        "uk_sub": "Upper-intermediate Ukrainian course",
        "landing_description": (
            "Released upper-intermediate Ukrainian course — {module_count} modules in curriculum order"
        ),
        "landing_subtitle": (
            "Released upper-intermediate Ukrainian course — {active_count} learner pages available"
        ),
        "progress_title": "B2 Release Status",
        "progress_description": "{active_count} available · deterministic checks clear · {planned_count} planned",
        "word_target": 4000,
    },
    "c1": {"title": "C1 — Advanced", "uk_title": "Вільно", "uk_sub": "Advanced Ukrainian course", "word_target": 4000},
    "c2": {
        "title": "C2 — Mastery",
        "uk_title": "Досконало",
        "uk_sub": "Mastery-level Ukrainian course",
        "word_target": 5000,
    },
    "hist": {
        "title": "HIST - Історія України",
        "uk_title": "HIST - Історія України",
        "uk_sub": "History Track",
        "word_target": 4000,
    },
    "bio": {
        "title": "BIO - Біографії",
        "uk_title": "BIO - Біографії",
        "uk_sub": "Biography Track",
        "word_target": 4000,
    },
    "lit": {
        "title": "LIT - Українська література",
        "uk_title": "LIT - Українська література",
        "uk_sub": "Literature Track",
        "word_target": 4000,
    },
    "istorio": {
        "title": "ISTORIO - Історіографія",
        "uk_title": "ISTORIO - Історіографія",
        "uk_sub": "Historiography Track",
        "word_target": 4000,
    },
    "oes": {
        "title": "OES - Old East Slavic",
        "uk_title": "OES - Давньоруські тексти",
        "uk_sub": "Old East Slavic Text Track",
        "word_target": 4000,
    },
    "ruth": {
        "title": "RUTH - Ruthenian",
        "uk_title": "RUTH - Руська канцелярська мова",
        "uk_sub": "Ruthenian Text Track",
        "word_target": 4000,
    },
    "folk": {
        "title": "FOLK",
        "uk_title": "FOLK · Фольклор та усна традиція",
        "uk_sub": "Фольклор та усна традиція",
        "word_target": 5000,
    },
    "lit-essay": {
        "title": "LIT-ESSAY - Есеїстика",
        "uk_title": "LIT-ESSAY - Есеїстика",
        "uk_sub": "Essay Track",
        "word_target": 4000,
    },
    "lit-hist-fic": {
        "title": "LIT-HIST-FIC - Історична проза",
        "uk_title": "LIT-HIST-FIC - Історична проза",
        "uk_sub": "Historical Fiction Track",
        "word_target": 4000,
    },
    "lit-fantastika": {
        "title": "LIT-FANTASTIKA - Фантастика",
        "uk_title": "LIT-FANTASTIKA - Фантастика",
        "uk_sub": "Speculative Literature Track",
        "word_target": 4000,
    },
    "lit-war": {
        "title": "LIT-WAR - Література війни",
        "uk_title": "LIT-WAR - Література війни",
        "uk_sub": "War Literature Track",
        "word_target": 4000,
    },
    "lit-humor": {
        "title": "LIT-HUMOR - Гумор і сатира",
        "uk_title": "LIT-HUMOR - Гумор і сатира",
        "uk_sub": "Humor and Satire Track",
        "word_target": 4000,
    },
    "lit-youth": {
        "title": "LIT-YOUTH - Дитяча та юнацька література",
        "uk_title": "LIT-YOUTH - Дитяча та юнацька література",
        "uk_sub": "Youth Literature Track",
        "word_target": 4000,
    },
    "lit-drama": {
        "title": "LIT-DRAMA - Драма і театр",
        "uk_title": "LIT-DRAMA - Драма і театр",
        "uk_sub": "Drama Track",
        "word_target": 4000,
    },
}


def truncate_card_subtitle(text: str, limit: int = 96) -> str:
    """Trim generated card subtitles without cutting through a word."""
    if len(text) <= limit:
        return text

    shortened = text[:limit].rstrip()
    if " " in shortened:
        shortened = shortened.rsplit(" ", 1)[0]
    return shortened


def ua_plural(count: int, one: str, few: str, many: str) -> str:
    """Return the Ukrainian form for 1, 2-4, and 5+/teens counts."""
    count_10 = count % 10
    count_100 = count % 100
    if count_10 == 1 and count_100 != 11:
        return one
    if count_10 in {2, 3, 4} and count_100 not in {12, 13, 14}:
        return few
    return many


def get_module_status(level: str, slug: str) -> str:
    """Check if module is deployed and, when available, passing audit."""
    status_path = CURRICULUM_ROOT / level / "status" / f"{slug}.json"
    content_paths = [
        CURRICULUM_ROOT / level / f"{slug}.md",
        CURRICULUM_ROOT / level / slug / "module.md",
        SITE_DOCS / level / f"{slug}.mdx",
    ]

    if not any(path.exists() for path in content_paths):
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


def format_track_template(
    template: str,
    *,
    level: str,
    module_count: int,
    active_count: int,
    done_count: int,
    planned_count: int,
) -> str:
    """Format optional track display overrides from generated landing counts."""
    return template.format(
        level=level.upper(),
        module_count=module_count,
        active_count=active_count,
        done_count=done_count,
        planned_count=planned_count,
    )


def validate_module_groups(level: str, modules: list[str], groups: list[dict]) -> list[dict]:
    """Validate manifest group anchors and return ordered group ranges."""
    if not groups:
        raise ValueError(f"{level}: missing groups metadata")

    module_counts = Counter(modules)
    duplicate_modules = sorted(slug for slug, count in module_counts.items() if count > 1)
    if duplicate_modules:
        raise ValueError(f"{level}: duplicate module slugs in modules list: {', '.join(duplicate_modules)}")

    module_index = {slug: i for i, slug in enumerate(modules)}
    covered: dict[str, str] = {}
    labels: set[str] = set()
    anchor_uses: dict[str, list[str]] = {}
    validated: list[dict] = []
    previous_end = -1

    for idx, group in enumerate(groups, 1):
        label = str(group.get("label", "")).strip()
        start = group.get("start")
        end = group.get("end")

        if not label or not start or not end:
            raise ValueError(f"{level}: group #{idx} must define label, start, and end")
        if label in labels:
            raise ValueError(f"{level}: duplicate group label {label!r}")
        labels.add(label)

        for field, slug in (("start", start), ("end", end)):
            if slug not in module_index:
                raise ValueError(f"{level}: group {label!r} has missing {field} anchor {slug!r}")
            anchor_uses.setdefault(slug, []).append(f"{label}.{field}")

        start_index = module_index[start]
        end_index = module_index[end]
        if start_index > end_index:
            raise ValueError(f"{level}: group {label!r} start anchor comes after end anchor")
        if start_index <= previous_end:
            raise ValueError(f"{level}: group {label!r} overlaps or is out of order")
        previous_end = end_index

        for slug in modules[start_index : end_index + 1]:
            if slug in covered:
                raise ValueError(f"{level}: module {slug!r} appears in both {covered[slug]!r} and {label!r}")
            covered[slug] = label

        validated.append(
            {
                "label": label,
                "start_index": start_index,
                "end_index": end_index,
            }
        )

    duplicate_anchors = {
        slug: uses
        for slug, uses in anchor_uses.items()
        if len(uses) > 1 and not (len(uses) == 2 and uses[0].rsplit(".", 1)[0] == uses[1].rsplit(".", 1)[0])
    }
    if duplicate_anchors:
        details = "; ".join(f"{slug}: {', '.join(uses)}" for slug, uses in sorted(duplicate_anchors.items()))
        raise ValueError(f"{level}: duplicated group anchors: {details}")

    ungrouped = [slug for slug in modules if slug not in covered]
    if ungrouped:
        raise ValueError(f"{level}: modules left ungrouped: {', '.join(ungrouped)}")

    return validated


def generate_landing_page(level: str, curriculum: dict) -> str:
    """Generate landing page MDX for a track."""
    level_data = curriculum.get("levels", {}).get(level, {})
    modules = level_data.get("modules", [])
    groups = level_data.get("groups", [])

    if not modules:
        print(f"  ⚠️  No modules found for {level}")
        return ""

    validated_groups = validate_module_groups(level, modules, groups)

    config = TRACK_CONFIG.get(
        level,
        {
            "title": f"{level.upper()}",
            "uk_title": level.upper(),
            "uk_sub": f"{level.upper()} Track",
            "word_target": 4000,
        },
    )

    module_to_group = {}
    for group in validated_groups:
        label = group["label"]
        for slug in modules[group["start_index"] : group["end_index"] + 1]:
            module_to_group[slug] = label

    phase_items: OrderedDict[str, list[str]] = OrderedDict()
    done_count = 0
    active_count = 0

    for i, slug in enumerate(modules, 1):
        plan = get_plan_data(level, slug)
        title = plan.get("title", slug.replace("-", " ").title())
        subtitle = plan.get("subtitle", "")
        unit_name = module_to_group[slug]

        if unit_name not in phase_items:
            phase_items[unit_name] = []

        status = get_module_status(level, slug)
        if status == "done":
            done_count += 1
        elif status == "active":
            active_count += 1

        card_subtitle = title if level == "folk" else subtitle
        sub_escaped = escape_js_string(truncate_card_subtitle(card_subtitle))
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

    planned_count = len(modules) - done_count - active_count
    track_subtitle = config.get("uk_sub", "")
    if level == "folk":
        if active_count:
            available_label = ua_plural(active_count, "доступна тема", "доступні теми", "доступних тем")
            total_label = ua_plural(len(modules), "теми", "тем", "тем")
            subtitle = f"{track_subtitle} · {active_count} {available_label} із {len(modules)} {total_label}"
        else:
            module_label = ua_plural(len(modules), "тема", "теми", "тем")
            subtitle = f"{track_subtitle} · {len(modules)} {module_label} у курсі"
        progress_title = "Стан побудови FOLK"
        progress_description = (
            f"Доступно: {active_count} · Перевірено: {done_count} · Заплановано: {planned_count}"
        )
        module_label = ua_plural(len(modules), "тема", "теми", "тем")
        description = f"{track_subtitle} — {len(modules)} {module_label} у порядку курсу"
    else:
        if active_count:
            page_label = "page" if active_count == 1 else "pages"
            subtitle = (
                f"{track_subtitle} — {active_count} learner {page_label} available · {len(modules)} modules"
            )
        else:
            subtitle = f"{track_subtitle} — {len(modules)} modules"
        progress_title = f"{level.upper()} Build Status"
        progress_description = f"{active_count} available · {done_count} reviewed · {planned_count} planned"
        description = f"{track_subtitle} — {len(modules)} modules in curriculum order"

    format_kwargs = {
        "level": level,
        "module_count": len(modules),
        "active_count": active_count,
        "done_count": done_count,
        "planned_count": planned_count,
    }
    if config.get("landing_description"):
        description = format_track_template(config["landing_description"], **format_kwargs)
    if config.get("landing_subtitle"):
        subtitle = format_track_template(config["landing_subtitle"], **format_kwargs)
    if config.get("progress_title"):
        progress_title = format_track_template(config["progress_title"], **format_kwargs)
    if config.get("progress_description"):
        progress_description = format_track_template(config["progress_description"], **format_kwargs)

    mdx = f"""---
title: "{config["title"]}"
description: "{escape_js_string(description)}"
template: splash
---

import LevelLanding from '@site/src/components/LevelLanding';

<LevelLanding
  client:load
  level="{level.upper()}"
  title="{config["uk_title"]}"
  subtitle="{escape_js_string(subtitle)}"
  progressTitle="{escape_js_string(progress_title)}"
  progressDescription="{escape_js_string(progress_description)}"
  moduleCount={{{len(modules)}}}
  wordTarget={{{config["word_target"]}}}
  color="var(--lu-id-{level})"
  modules={{[
{modules_js}
  ]}}
/>
"""
    return mdx


def main():
    parser = argparse.ArgumentParser(description="Generate Site landing pages")
    parser.add_argument("--track", help="Generate for specific track (e.g., a1)")
    parser.add_argument("--all", action="store_true", help="Generate for all tracks")
    parser.add_argument("--check", action="store_true", help="Fail if generated landing pages differ from disk")
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

    stale_paths: list[Path] = []
    for level in tracks:
        if level not in levels:
            print(f"⚠️  Track {level} not in curriculum.yaml, skipping")
            continue

        print(f"Generating {level.upper()} landing page...")
        mdx = generate_landing_page(level, curriculum)
        if not mdx:
            continue

        out_dir = SITE_DOCS / level
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.mdx"
        if args.check:
            if not out_path.exists() or out_path.read_text("utf-8") != mdx:
                stale_paths.append(out_path)
                print(f"  STALE {out_path}")
            else:
                print(f"  OK {out_path}")
            continue

        out_path.write_text(mdx, "utf-8")
        print(f"  ✅ {out_path}")

    if stale_paths:
        print("\nLanding page drift detected. Regenerate with:")
        for path in stale_paths:
            level = path.parent.name
            print(f"  .venv/bin/python scripts/generate_landing_pages.py --track {level}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
