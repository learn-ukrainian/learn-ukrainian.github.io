#!/usr/bin/env python3
"""Extract plan files from c1-bio track meta.yaml files.

One-time migration script for M2 of Epic #465.
"""
import re
import yaml
from pathlib import Path


def extract_ukrainian_word(hint: str) -> str:
    """Extract Ukrainian word from 'слово (translation)' format."""
    if not hint:
        return hint
    # Pattern: "word (translation)" -> "word"
    match = re.match(r'^([^(]+)', hint)
    if match:
        return match.group(1).strip()
    return hint.strip()


def convert_meta_to_plan(meta: dict, slug: str) -> dict:
    """Convert meta.yaml format to module-plan.schema.json format."""
    # Map content_outline: points -> subsections
    content_outline = []
    for section in meta.get('content_outline', []):
        outline_section = {
            'section': section.get('section', ''),
            'words': section.get('words', 0),
        }
        if 'points' in section:
            outline_section['subsections'] = section['points']
        if 'key_concepts' in section:
            outline_section['key_concepts'] = section['key_concepts']
        content_outline.append(outline_section)

    # Extract vocabulary (strip translations)
    vocab_hints = meta.get('vocabulary_hints', {})
    vocabulary = {
        'required': [extract_ukrainian_word(w) for w in vocab_hints.get('required', [])],
        'recommended': [extract_ukrainian_word(w) for w in vocab_hints.get('recommended', [])],
        'forbidden': [],
    }

    # Extract activity types and counts
    activity_hints = meta.get('activity_hints', [])
    types_required = []
    for hint in activity_hints:
        if 'type' in hint:
            types_required.append(hint['type'])

    activities = {
        'types_required': types_required if types_required else ['reading', 'quiz', 'match-up', 'essay-response', 'fill-in', 'group-sort'],
        'min_items_per_type': 8,
        'total_min_items': 40,
        'no_mirroring': True,
    }

    # Map sources
    sources = {'primary': [], 'secondary': []}
    for src in meta.get('sources', []):
        source_entry = {
            'url': src.get('url', ''),
            'title': src.get('name', ''),
        }
        if 'notes' in src:
            source_entry['notes'] = src['notes']

        src_type = src.get('type', 'primary')
        if src_type == 'primary':
            sources['primary'].append(source_entry)
        else:
            sources['secondary'].append(source_entry)

    # Build plan
    plan = {
        'module': slug,
        'level': 'c1-bio',
        'sequence': 0,  # Will be set based on id if available
        'version': meta.get('version', '1.0'),
        'title': meta.get('title', ''),
    }

    # Extract sequence from id if available (c1-bio-20 -> 20)
    if 'id' in meta:
        match = re.search(r'(\d+)$', str(meta['id']))
        if match:
            plan['sequence'] = int(match.group(1))

    plan['focus'] = 'biography'
    plan['pedagogy'] = 'seminar'

    if 'objectives' in meta:
        plan['objectives'] = meta['objectives']
    else:
        # Generate default objectives from title
        title = meta.get('title', slug)
        plan['objectives'] = [
            f"Зрозуміти життєвий шлях та досягнення особи",
            f"Проаналізувати історичний контекст епохи",
            f"Оцінити внесок у українську культуру та історію",
        ]

    if sources['primary'] or sources['secondary']:
        plan['sources'] = sources

    plan['content_outline'] = content_outline
    plan['word_target'] = meta.get('word_target', 4000)
    plan['word_tolerance'] = 0.05
    plan['vocabulary'] = vocabulary
    plan['activities'] = activities

    # Connections
    connects_to = {}
    if 'prerequisites' in meta:
        prereqs = meta['prerequisites']
        if prereqs and isinstance(prereqs, list) and len(prereqs) > 0:
            connects_to['previous'] = str(prereqs[0])

    if 'connects_to' in meta:
        related = meta['connects_to']
        if related:
            connects_to['related'] = [str(r) for r in related] if isinstance(related, list) else [str(related)]

    if connects_to:
        plan['connects_to'] = connects_to

    # Constraints
    plan['constraints'] = {
        'min_engagement_boxes': 2,
        'min_examples': 10,
        'immersion_target': 1.0,
        'naturalness_threshold': 8,
        'min_primary_sources': 2,
    }

    return plan


def main():
    base_path = Path(__file__).parent.parent / 'curriculum' / 'l2-uk-en'
    meta_dir = base_path / 'c1-bio' / 'meta'
    plans_dir = base_path / 'plans' / 'c1-bio'

    # Ensure plans directory exists
    plans_dir.mkdir(parents=True, exist_ok=True)

    # Process each meta file
    processed = 0
    skipped = 0

    for meta_file in sorted(meta_dir.glob('*.yaml')):
        slug = meta_file.stem

        # Skip checkpoint files
        if 'checkpoint' in slug:
            print(f"Skipping {meta_file.name}: checkpoint file")
            skipped += 1
            continue

        # Read meta file
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = yaml.safe_load(f)

        # Check if meta has content_outline (indicates it's well-developed)
        if not meta.get('content_outline'):
            print(f"Skipping {meta_file.name}: no content_outline (skeleton)")
            skipped += 1
            continue

        # Convert to plan format
        plan = convert_meta_to_plan(meta, slug)

        # Write plan file
        plan_file = plans_dir / meta_file.name
        with open(plan_file, 'w', encoding='utf-8') as f:
            yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

        print(f"Created {plan_file.name}")
        processed += 1

    print(f"\nDone: {processed} plans created, {skipped} skipped")


if __name__ == '__main__':
    main()
