#!/usr/bin/env python3
"""
Build landing pages for all curriculum levels.

Shows ALL planned modules (existing + planned) based on level-status.yaml.
Status indicators:
  ✅ Ready - MDX file exists in starlight/src/content/docs/{level}/
  🚧 In Progress - Meta file exists but no MDX
  📋 Planned - No files yet (up to planned count)
"""

import json
import sys
from pathlib import Path

import yaml

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from manifest_utils import get_modules_for_level

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
DOCS_DIR = PROJECT_ROOT / "starlight" / "src" / "content" / "docs"
LEVEL_STATUS_FILE = PROJECT_ROOT / "docs" / "l2-uk-en" / "level-status.yaml"

# Core levels and specialized tracks
CORE_LEVELS = ["a1", "a2", "b1", "b2", "c1", "c2"]
SPECIALIZED_TRACKS = ["hist", "bio", "istorio", "b2-pro", "c1-pro", "lit", "oes", "ruth"]

# Ukrainian level names
LEVEL_NAMES_UK = {
    "a1": "A1 - Початковий",
    "a2": "A2 - Елементарний",
    "b1": "B1 - Середній",
    "b2": "B2 - Вищий середній",
    "c1": "C1 - Просунутий",
    "c2": "C2 - Досконалий",
    "hist": "HIST - Історія України",
    "bio": "BIO - Біографії українців",
    "istorio": "ISTORIO - Історіографія",
    "b2-pro": "B2-PRO - Професійна українська",
    "c1-pro": "C1-PRO - Фахова українська",
    "lit": "LIT - Українська література",
    "oes": "OES - Давньоруська мова",
    "ruth": "RUTH - Руська мова XIV-XVIII",
}

# English level names for intro
LEVEL_NAMES_EN = {
    "a1": "Beginner",
    "a2": "Elementary",
    "b1": "Intermediate",
    "b2": "Upper-Intermediate",
    "c1": "Advanced",
    "c2": "Mastery",
    "hist": "History Track",
    "bio": "Biography Track",
    "istorio": "Historiography Track",
    "b2-pro": "Professional Track",
    "c1-pro": "Professional Mastery",
    "lit": "Literature Track",
    "oes": "Old East Slavic Track",
    "ruth": "Ruthenian Track",
}


def load_level_status():
    """Load level status configuration."""
    with open(LEVEL_STATUS_FILE, encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_module_files(level):
    """Get existing module files for a level (core levels with slug-based files)."""
    meta_dir = CURRICULUM_DIR / level / "meta"
    mdx_dir = DOCS_DIR / level
    review_dir = CURRICULUM_DIR / level / "review"
    audit_dir = CURRICULUM_DIR / level / "audit"

    meta_files = {}
    mdx_files = {}
    review_files = {}
    audit_files = {}

    # Use manifest for module lookup
    modules = get_modules_for_level(level)
    for mod in modules:
        meta_file = meta_dir / f"{mod.slug}.yaml"
        if meta_file.exists():
            meta_files[mod.local_num] = meta_file

        mdx_file = mdx_dir / f"{mod.slug}.mdx"
        if mdx_file.exists():
            mdx_files[mod.local_num] = mdx_file

        review_file = review_dir / f"{mod.slug}-review.md"
        if review_file.exists():
            review_files[mod.local_num] = review_file

        audit_file = audit_dir / f"{mod.slug}-audit.md"
        if audit_file.exists():
            audit_files[mod.local_num] = audit_file

    return meta_files, mdx_files, review_files, audit_files


def get_track_module_files(level):
    """Get existing module files for a track (slug-based files).

    Uses manifest to get module list and checks for slug-based MDX files.
    """
    mdx_dir = DOCS_DIR / level
    review_dir = CURRICULUM_DIR / level / "review"
    audit_dir = CURRICULUM_DIR / level / "audit"
    modules = get_modules_for_level(level)

    mdx_files = {}  # {local_num: mdx_path}
    review_files = {}
    audit_files = {}
    meta_data = {}  # {local_num: (title, subtitle)}

    for mod in modules:
        # Check if MDX exists (slug-based naming)
        mdx_path = mdx_dir / f"{mod.slug}.mdx"
        if mdx_path.exists():
            mdx_files[mod.local_num] = mdx_path

        review_file = review_dir / f"{mod.slug}-review.md"
        if review_file.exists():
            review_files[mod.local_num] = review_file

        audit_file = audit_dir / f"{mod.slug}-audit.md"
        if audit_file.exists():
            audit_files[mod.local_num] = audit_file

        # Store meta data from manifest
        meta_data[mod.local_num] = (mod.title.replace("<!-- Title -->", ""), '')

    return meta_data, mdx_files, review_files, audit_files


def get_module_title(meta_file):
    """Extract title from meta YAML file."""
    try:
        with open(meta_file, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('title', 'Untitled'), data.get('subtitle', '')
    except Exception:
        return 'Untitled', ''


def build_level_landing(level, config, is_track=False):
    """Build landing page for a single level using LevelLanding component."""
    planned = config.get('planned', 0)

    if is_track:
        meta_files, mdx_files, review_files, audit_files = get_track_module_files(level)
    else:
        meta_files, mdx_files, review_files, audit_files = get_module_files(level)

    # Build module list from manifest
    modules = get_modules_for_level(level)
    module_items = []
    ready_count = 0

    for mod in modules:
        num = mod.local_num
        title = (mod.title or '').replace('<!-- Title -->', '').strip() or f'Module {num:02d}'
        is_checkpoint = any(x in mod.slug.lower() for x in ['checkpoint', 'review', 'exam', 'finale'])

        if num in mdx_files:
            if num in review_files:
                status = 'ready'
                ready_count += 1
            elif num in audit_files:
                status = 'qa'
                ready_count += 1
            else:
                status = 'ready'
                ready_count += 1
        elif num in meta_files:
            status = 'wip'
        else:
            status = 'planned'

        # Escape quotes in title for JSON
        safe_title = title.replace('"', '\\"')
        module_items.append(
            f'  {{ num: {num}, title: "{safe_title}", slug: "{mod.slug}", '
            f'status: "{status}"{", isCheckpoint: true" if is_checkpoint else ""} }}'
        )

    modules_js = ',\n'.join(module_items)

    # English subtitle from config
    en_name = LEVEL_NAMES_EN.get(level, '')
    subtitle = f'{en_name} — {planned} modules' if en_name else f'{planned} modules'

    # Use the short description from config, not the long markdown introduction
    description = config.get('description', '').strip()

    content = f"""---
title: {LEVEL_NAMES_UK[level]}
sidebar:
  order: 1
---

import LevelLanding from '@site/src/components/LevelLanding';

<LevelLanding
  client:load
  level="{level}"
  levelName="{LEVEL_NAMES_UK[level]}"
  subtitle="{subtitle}"
  introduction="{description}"
  totalPlanned={{{planned}}}
  modules={{[
{modules_js}
  ]}}
/>
"""

    return content, ready_count, planned


def build_intro_page(level_status):
    content = """---
title: "Learn Ukrainian"
description: "A free, open-source Ukrainian language course from A1 to C2"
template: splash
---

import Home from '@site/src/components/Home';

<Home client:load />
"""
    return content


# Sidebar positions for _category.json
LEVEL_POSITIONS = {
    "a1": 2, "a2": 3, "b1": 4, "b2": 5, "c1": 6, "c2": 7,
    "hist": 8, "bio": 9, "istorio": 10,
    "b2-pro": 11, "c1-pro": 12,
    "lit": 13, "oes": 14, "ruth": 15,
}

# Descriptions for _category.json (with module count placeholder {n})
CATEGORY_DESCRIPTIONS = {
    "a1": "Learn the Cyrillic alphabet, basic grammar, and everyday vocabulary. {n} modules from first letters to first conversations.",
    "a2": "All 7 cases, verbal aspect, and practical scenarios. {n} modules for elementary proficiency.",
    "b1": "Achieve aspect mastery, learn motion verbs, and develop complex sentence fluency. {n} modules for independent users.",
    "b2": "Master passive voice, participles, and stylistic variation. {n} modules for advanced communication.",
    "c1": "Stylistics, folk culture, literature, and advanced language. {n} modules for proficient users.",
    "c2": "Stylistic perfection and professional specialization. {n} modules for complete mastery.",
    "hist": "Ukrainian history from Trypillia to modern independence. {n} modules at B2 level.",
    "bio": "Notable Ukrainians through history — poets, scientists, warriors, artists. {n} biographical modules.",
    "istorio": "Primary sources, historiography, and analytical history. {n} modules at academic level.",
    "b2-pro": "Business communication and professional domains. {n} modules for the workplace.",
    "c1-pro": "Executive, academic, and specialized professional Ukrainian. {n} modules.",
    "lit": "Ukrainian literature from Kotliarevsky to contemporary authors. {n} modules.",
    "oes": "Old East Slavic historical linguistics and primary sources X-XIII century. {n} modules.",
    "ruth": "Ruthenian / Middle Ukrainian language and documents XIV-XVIII century. {n} modules.",
}

# _category.json labels
CATEGORY_LABELS = {
    "a1": "A1 - Beginner", "a2": "A2 - Elementary",
    "b1": "B1 - Intermediate", "b2": "B2 - Upper-Intermediate",
    "c1": "C1 - Advanced", "c2": "C2 - Mastery",
    "hist": "HIST - Історія України",
    "bio": "BIO - Біографії українців",
    "istorio": "ISTORIO - Історіографія",
    "b2-pro": "B2-PRO - Професійна українська",
    "c1-pro": "C1-PRO - Фахова українська",
    "lit": "LIT - Literature",
    "oes": "OES - Old East Slavic",
    "ruth": "RUTH - Ruthenian",
}


def update_category_json(level, planned):
    """Update or create _category.json for a level with correct module count."""
    cat_path = DOCS_DIR / level / "_category.json"
    cat_path.parent.mkdir(parents=True, exist_ok=True)

    position = LEVEL_POSITIONS.get(level, 99)
    label = CATEGORY_LABELS.get(level, level.upper())
    desc_template = CATEGORY_DESCRIPTIONS.get(level, f"{level.upper()} track. {{n}} modules.")
    description = desc_template.format(n=planned)

    # Use generated-index for core levels, doc link for specialized tracks without index
    if level in CORE_LEVELS:
        link_type = "generated-index"
        title = f"{label} Modules"
        data = {
            "label": label,
            "position": position,
            "link": {
                "type": link_type,
                "title": title,
                "description": description,
                "slug": f"/{level}",
            }
        }
    else:
        # Specialized tracks use doc link to their index.mdx
        data = {
            "label": label,
            "position": position,
            "link": {
                "type": "doc",
                "id": f"{level}/index",
            }
        }

    with open(cat_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

    return cat_path


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

        # cat_path = update_category_json(level, planned)
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

        # cat_path = update_category_json(level, planned)
        print(f"  {level.upper()}: {ready}/{planned} modules ({output_path})")

    # Build intro page
    intro_content = build_intro_page(level_status)
    intro_path = DOCS_DIR / "index.mdx"
    with open(intro_path, 'w', encoding='utf-8') as f:
        f.write(intro_content)
    print(f"  Intro page: {intro_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
