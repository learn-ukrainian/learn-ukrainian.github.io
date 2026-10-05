#!/usr/bin/env python3
"""
Build landing pages for all curriculum levels.

Shows ALL planned modules (existing + planned) based on level-status.yaml.
Status indicators:
  ✅ Ready - MDX file exists in site/src/content/docs/{level}/
  🚧 In Progress - Meta file exists but no MDX
  📋 Planned - No files yet (up to planned count)
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
import manifest_utils
from manifest_utils import get_modules_for_level

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
DOCS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "docs"
LEVEL_STATUS_FILE = PROJECT_ROOT / "docs" / "l2-uk-en" / "level-status.yaml"

# Core levels and specialized tracks
CORE_LEVELS = ["a1", "a2", "b1", "b2", "c1", "c2"]
SPECIALIZED_TRACKS = ["hist", "bio", "istorio", "lit", "oes", "ruth"]

# Levels whose landing (and module pages) scripts/build/build_arc_landing.py
# generates from the accepted arc (#8397). Keep in step with
# ARC_LANDING_LEVELS in that module and in scripts/generate_landing_pages.py.
ARC_LANDING_LEVELS = frozenset({"a1"})

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
    "lit": 11, "oes": 12, "ruth": 13,
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


def generated_pages(level_status):
    """Derive each managed page with the same renderers used for regeneration."""
    pages = {}
    for levels, is_track in ((CORE_LEVELS, False), (SPECIALIZED_TRACKS, True)):
        for level in levels:
            if not is_track and level in ARC_LANDING_LEVELS:
                continue
            config = level_status.get(level, {})
            if not config:
                continue
            pages[DOCS_DIR / level / "index.mdx"] = build_level_landing(
                level, config, is_track=is_track
            )
    pages[DOCS_DIR / "index.mdx"] = (build_intro_page(level_status), 0, 0)
    return pages


class LandingInputError(ValueError):
    """Privacy-safe diagnostic for an incompatible required producer input."""


def validate_check_inputs(level_status):
    """Refuse incomplete/incompatible producer inputs before comparing outputs."""
    if not isinstance(level_status, dict) or not level_status:
        raise LandingInputError("docs/l2-uk-en/level-status.yaml must contain a non-empty mapping")
    # Recompute titles and membership on every check, including in-process callers.
    manifest_utils.clear_manifest_cache()
    manifest = manifest_utils.load_manifest()
    if not isinstance(manifest, dict) or not isinstance(manifest.get("levels"), dict):
        raise LandingInputError("curriculum/l2-uk-en/curriculum.yaml must contain a levels mapping")
    for level in (*CORE_LEVELS, *SPECIALIZED_TRACKS):
        if level in ARC_LANDING_LEVELS:
            continue
        output = f"site/src/content/docs/{level}/index.mdx"
        config = level_status.get(level)
        if config is None:
            continue
        if not isinstance(config, dict):
            raise LandingInputError(f"{output}: level-status.yaml: {level} must be a mapping")
        if not config:
            continue
        planned = config.get("planned", 0)
        if type(planned) is not int or planned < 0:
            raise LandingInputError(f"{output}: level-status.yaml: {level}.planned must be a non-negative integer")
        if not isinstance(config.get("description", ""), str):
            raise LandingInputError(f"{output}: level-status.yaml: {level}.description must be a string")
        entry = manifest["levels"].get(level)
        if not isinstance(entry, dict) or not isinstance(entry.get("modules"), list):
            raise LandingInputError(f"{output}: curriculum.yaml: {level} must declare a modules list")
        if any(not isinstance(slug, str) or not slug for slug in entry["modules"]):
            raise LandingInputError(f"{output}: curriculum.yaml: {level} module slugs must be non-empty strings")


def check_pages(pages):
    """Compare exact bytes and refuse obsolete known non-arc output paths."""
    problems = []
    for path, (content, _, _) in pages.items():
        relative = path.relative_to(PROJECT_ROOT)
        try:
            actual = path.read_bytes()
        except FileNotFoundError:
            problems.append(f"missing: {relative}")
        except OSError:
            problems.append(f"unreadable: {relative}")
        else:
            if actual != content.encode("utf-8"):
                problems.append(f"stale: {relative}")
    # These names bound this producer's ownership even if a configuration or
    # configured level/track is removed. Do not scan arc or unrelated pages.
    for level in LEVEL_NAMES_UK.keys() - ARC_LANDING_LEVELS:
        path = DOCS_DIR / level / "index.mdx"
        if path not in pages and path.exists():
            problems.append(
                f"obsolete: {path.relative_to(PROJECT_ROOT)} "
                "(no longer configured; restore its source/config or remove the obsolete managed page)"
            )
    return sorted(problems)


def main(argv=()):
    parser = argparse.ArgumentParser(
        description=(
            "Build non-arc curriculum landing pages and the root intro.\n"
            "Use --check to verify freshness without writing; arc pages use build_arc_landing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Usage examples:
  .venv/bin/python -m scripts.build.build_landing_pages --check
  .venv/bin/python scripts/build_landing_pages.py --check
  .venv/bin/python -m scripts.build.build_landing_pages

Outputs: Without --check, writes configured non-arc level/track index.mdx
  pages and the root index.mdx under site/src/content/docs, creating level
  directories as needed. --check and --help write nothing.
Exit codes: 0 = generated successfully or all expected pages are current;
  1 = stale/missing/obsolete output or invalid/unavailable producer input;
  2 = invalid command-line arguments.
Related: scripts/build/build_arc_landing.py; scripts/generate_curriculum_stats.py;
  docs/l2-uk-en/level-status.yaml; #9721.
""",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="compare producer-derived bytes without writing (default: regenerate; example: --check)",
    )
    args = parser.parse_args(argv)
    if not args.check:
        print("Building landing pages...")
    try:
        level_status = load_level_status()
        if args.check:
            validate_check_inputs(level_status)
        pages = generated_pages(level_status)
    except LandingInputError as exc:
        print(
            f"Cannot derive site/src/content/docs landing pages: {exc}; "
            "restore valid producer inputs before regenerating with "
            ".venv/bin/python -m scripts.build.build_landing_pages.",
            file=sys.stderr,
        )
        return 1
    except (OSError, yaml.YAMLError, ValueError, TypeError, AttributeError, KeyError) as exc:
        # Loader exceptions can contain private absolute paths or source text.
        print(
            f"Cannot derive site/src/content/docs landing pages ({type(exc).__name__}); "
            "verify docs/l2-uk-en/level-status.yaml, curriculum/l2-uk-en/curriculum.yaml "
            "and producer-consumed meta/plan inputs before regenerating.",
            file=sys.stderr,
        )
        return 1

    if args.check:
        problems = check_pages(pages)
        if problems:
            for problem in problems:
                print(problem, file=sys.stderr)
            print(
                "Restore valid producer inputs/configuration, then regenerate with "
                ".venv/bin/python -m scripts.build.build_landing_pages; "
                "resolve obsolete pages explicitly and rerun --check.",
                file=sys.stderr,
            )
            return 1
        print(f"{len(pages)} non-arc landing/intro pages are current")
        return 0

    for levels, is_track in ((CORE_LEVELS, False), (SPECIALIZED_TRACKS, True)):
        for level in levels:
            if not is_track and level in ARC_LANDING_LEVELS:
                print(f"  Skipping {level} - landing generated by scripts/build/build_arc_landing.py")
            elif not level_status.get(level, {}):
                print(f"  Skipping {level} - no config")
            else:
                output_path = DOCS_DIR / level / "index.mdx"
                content, ready, planned = pages[output_path]
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  {level.upper()}: {ready}/{planned} modules ({output_path})")

    intro_path = DOCS_DIR / "index.mdx"
    with open(intro_path, 'w', encoding='utf-8') as f:
        f.write(pages[intro_path][0])
    print(f"  Intro page: {intro_path}")
    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
