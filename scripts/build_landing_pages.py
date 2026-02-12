#!/usr/bin/env python3
"""
Build landing pages for all curriculum levels.

Shows ALL planned modules (existing + planned) based on level-status.yaml.
Status indicators:
  ✅ Ready - MDX file exists in docusaurus/docs/{level}/
  🚧 In Progress - Meta file exists but no MDX
  📋 Planned - No files yet (up to planned count)
"""

import os
import sys
import yaml
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from manifest_utils import get_modules_for_level

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
DOCS_DIR = PROJECT_ROOT / "docusaurus" / "docs"
LEVEL_STATUS_FILE = PROJECT_ROOT / "docs" / "l2-uk-en" / "level-status.yaml"

# Core levels and specialized tracks
CORE_LEVELS = ["a1", "a2", "b1", "b2", "c1", "c2"]
SPECIALIZED_TRACKS = ["b2-hist", "c1-bio", "c1-hist", "b2-pro", "c1-pro", "lit"]

# Ukrainian level names
LEVEL_NAMES_UK = {
    "a1": "A1 - Початковий",
    "a2": "A2 - Елементарний",
    "b1": "B1 - Середній",
    "b2": "B2 - Вищий середній",
    "c1": "C1 - Просунутий",
    "c2": "C2 - Досконалий",
    "b2-hist": "B2-HIST - Історія України",
    "c1-bio": "C1-BIO - Біографії українців",
    "c1-hist": "C1-HIST - Історіографія",
    "b2-pro": "B2-PRO - Професійна українська",
    "c1-pro": "C1-PRO - Фахова українська",
    "lit": "LIT - Українська література",
}

# English level names for intro
LEVEL_NAMES_EN = {
    "a1": "Beginner",
    "a2": "Elementary",
    "b1": "Intermediate",
    "b2": "Upper-Intermediate",
    "c1": "Advanced",
    "c2": "Mastery",
    "b2-hist": "History Track",
    "c1-bio": "Biography Track",
    "c1-hist": "Historiography Track",
    "b2-pro": "Professional Track",
    "c1-pro": "Professional Mastery",
    "lit": "Literature Track",
}


def load_level_status():
    """Load level status configuration."""
    with open(LEVEL_STATUS_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_module_files(level):
    """Get existing module files for a level (core levels with slug-based files)."""
    meta_dir = CURRICULUM_DIR / level / "meta"
    mdx_dir = DOCS_DIR / level

    meta_files = {}
    mdx_files = {}

    # Use manifest for module lookup
    modules = get_modules_for_level(level)
    for mod in modules:
        meta_file = meta_dir / f"{mod.slug}.yaml"
        if meta_file.exists():
            meta_files[mod.local_num] = meta_file

        mdx_file = mdx_dir / f"{mod.slug}.mdx"
        if mdx_file.exists():
            mdx_files[mod.local_num] = mdx_file

    return meta_files, mdx_files


def get_track_module_files(level):
    """Get existing module files for a track (slug-based files).

    Uses manifest to get module list and checks for slug-based MDX files.
    """
    mdx_dir = DOCS_DIR / level
    modules = get_modules_for_level(level)

    mdx_files = {}  # {local_num: mdx_path}
    meta_data = {}  # {local_num: (title, subtitle)}

    for mod in modules:
        # Check if MDX exists (slug-based naming)
        mdx_path = mdx_dir / f"{mod.slug}.mdx"
        if mdx_path.exists():
            mdx_files[mod.local_num] = mdx_path

        # Store meta data from manifest
        meta_data[mod.local_num] = (mod.title, '')

    return meta_data, mdx_files


def get_module_title(meta_file):
    """Extract title from meta YAML file."""
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('title', 'Untitled'), data.get('subtitle', '')
    except Exception:
        return 'Untitled', ''


def build_level_landing(level, config, is_track=False):
    """Build landing page for a single level."""
    planned = config.get('planned', 0)
    description = config.get('description', '')
    introduction = config.get('introduction', '').strip()

    if is_track:
        meta_files, mdx_files = get_track_module_files(level)
    else:
        meta_files, mdx_files = get_module_files(level)

    # Count stats
    ready_count = len(mdx_files)
    in_progress_count = len([n for n in meta_files if n not in mdx_files])

    # Determine status emoji for header
    if ready_count == planned:
        status_emoji = "✅"
        status_text = "Завершено"
    elif ready_count > 0:
        status_emoji = "🔍"
        status_text = f"На перевірці — {ready_count}/{planned} модулів"
    else:
        status_emoji = "📋"
        status_text = "Заплановано"

    # Build module table rows
    rows = []

    # Build module rows from manifest
    modules = get_modules_for_level(level)
    for mod in modules:
        num = mod.local_num
        if num in mdx_files:
            status = "✅"
            link = f"[{mod.title}](./{mod.slug})"
        elif num in meta_files:
            status = "🚧"
            link = f"{mod.title}"
        else:
            status = "📋"
            link = f"Модуль {num:02d}"
        rows.append(f"| {num} | {link} | {status} |")

    # Build introduction section
    intro_section = ""
    if introduction:
        intro_section = f"\n{introduction}\n"

    # Build content
    content = f"""---
sidebar_position: 1
title: {LEVEL_NAMES_UK[level]}
---

# {status_emoji} {LEVEL_NAMES_UK[level]}

**{status_text}**
{intro_section}
---

## Модулі

| # | Модуль | Статус |
|---|--------|--------|
{chr(10).join(rows)}

---

## Прогрес

- **Готові модулі:** {ready_count}
- **Заплановані модулі:** {planned}
- **Завершення:** {round(ready_count / planned * 100) if planned > 0 else 0}%
"""

    return content, ready_count, planned


def build_intro_page(level_status):
    """Build the main intro.mdx page."""

    # Calculate totals
    core_rows = []
    track_rows = []
    total_lessons = 0
    total_planned = 0

    for level in CORE_LEVELS:
        config = level_status.get(level, {})
        planned = config.get('planned', 0)
        description = config.get('description', '')
        meta_files, mdx_files = get_module_files(level)
        ready = len(mdx_files)

        total_lessons += ready
        total_planned += planned

        # Determine status
        status_override = config.get('status', 'auto')
        if status_override == 'complete':
            status = "✅ Complete"
        elif ready == planned:
            status = "🔍 In QA"
        elif ready > 0:
            status = "🚧 In Progress"
        else:
            status = "📋 Planned"

        core_rows.append(f"| **{level.upper()}** | {description} | {planned} | {status} |")

    for level in SPECIALIZED_TRACKS:
        config = level_status.get(level, {})
        if not config:
            continue
        planned = config.get('planned', 0)
        description = config.get('description', '')
        meta_files, mdx_files = get_track_module_files(level)
        ready = len(mdx_files)

        total_lessons += ready
        total_planned += planned

        # Determine status
        if ready == planned and planned > 0:
            status = "✅ Complete"
        elif ready > 0:
            status = "🚧 In Progress"
        else:
            status = "📋 Planned"

        track_rows.append(f"| **{level.upper()}** | {description} | {planned} | {status} |")

    content = f"""---
sidebar_position: 1
slug: /
---

# Learn Ukrainian

**Мова – душа народу • Language is the soul of a nation**

A free, open-source Ukrainian language course from A1 to C2, based on the **Ukrainian State Standard 2024**.

---

## Find a Teacher First

> **Учитель – це професія від Бога, усі решта професій – від учителя.**
>
> *A teacher is a profession from God; all other professions come from the teacher.*

**No app, website, or course can replace a qualified native teacher.** This curriculum is designed to supplement — not replace — human instruction. Before diving into self-study:

1. **Find a native Ukrainian teacher** — Online platforms like [Preply](https://preply.com) (Ukrainian company) or local Ukrainian communities
2. **Join a class** — Many Ukrainian cultural centers offer group lessons
3. **Practice with native speakers** — Language exchange, conversation partners, Ukrainian friends

A good teacher will correct your pronunciation, explain cultural nuances, and adapt to your learning style in ways no app ever can.

---

## What is Learn Ukrainian?

A complete **{total_planned}-lesson pathway** for learning Ukrainian as a second language. From your first Cyrillic letter to native-level literary analysis, every lesson is designed with pedagogical rigor and cultural authenticity.

### Why Learn Ukrainian?

- **45 million speakers** worldwide
- **Rich literary tradition** — Shevchenko, Franko, Lesya Ukrainka
- **Unique grammar** — 7 cases, verbal aspect, motion verb system
- **Growing global interest** — solidarity with Ukraine

### Our Approach

- **Theory-First Learning** — Understand the "why" behind grammar patterns, not just memorization
- **Cultural Immersion** — Authentic materials, folklore, literature, music, and historical context
- **Interactive Practice** — Every lesson includes 8-16 activities: quizzes, fill-ins, matching, translation
- **Progressive Immersion** — Gradually increase Ukrainian exposure from 25% (A1) to 98% (C2)
- **100% Free** — No ads, no subscriptions, no paywalls

---

## Core Curriculum

| Level | Description | Lessons | Status |
|-------|-------------|---------|--------|
{chr(10).join(core_rows)}

---

## Specialized Tracks

Optional tracks for deeper exploration of specific topics.

| Track | Description | Lessons | Status |
|-------|-------------|---------|--------|
{chr(10).join(track_rows)}

---

## Get Started

Use the sidebar to navigate to your level.

**New to Ukrainian?** Start with [**A1 Beginner**](/docs/a1/) to learn the Cyrillic alphabet and build your foundation.

**Already know some Ukrainian?** Jump to the level that matches your current ability.

---

## Acknowledgments

This curriculum was inspired by and built upon the work of dedicated Ukrainian language educators:

- **[Ukrainian Lessons Podcast](https://ukrainianlessons.com/)** — Anna Ohoiko's excellent podcast and courses for learners at all levels
- **[Dombra Forma](https://www.dombraforma.com/)** — Quality Ukrainian language instruction and cultural content

We encourage all learners to support these creators and the broader community of Ukrainian language teachers.

---

## Standards & Quality

- **CEFR-aligned** — Common European Framework of Reference for Languages
- **Ukrainian State Standard 2024** — Official language proficiency requirements
- **Automated quality audits** — Every lesson checked for vocabulary, grammar, and activity counts
- **Looking for native reviewers** — Help us improve linguistic accuracy!

---

**Слава Україні!**
"""

    return content


def main():
    print("Building landing pages...")

    level_status = load_level_status()

    # Build core level landing pages
    for level in CORE_LEVELS:
        config = level_status.get(level, {})
        if not config:
            print(f"  Skipping {level} - no config")
            continue

        content, ready, planned = build_level_landing(level, config)
        output_path = DOCS_DIR / level / "index.mdx"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  {level.upper()}: {ready}/{planned} modules ({output_path})")

    # Build specialized track landing pages
    for level in SPECIALIZED_TRACKS:
        config = level_status.get(level, {})
        if not config:
            print(f"  Skipping {level} - no config")
            continue

        content, ready, planned = build_level_landing(level, config, is_track=True)
        output_path = DOCS_DIR / level / "index.mdx"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  {level.upper()}: {ready}/{planned} modules ({output_path})")

    # Build intro page
    intro_content = build_intro_page(level_status)
    intro_path = DOCS_DIR / "intro.mdx"
    with open(intro_path, 'w', encoding='utf-8') as f:
        f.write(intro_content)
    print(f"  Intro page: {intro_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
