#!/usr/bin/env python3
"""Extract module plans from b2-hist meta.yaml files."""

import yaml
from pathlib import Path
import re


def extract_sequence_from_id(meta_id: str) -> int:
    """Extract sequence number from module ID like 'b2-hist-41'."""
    match = re.search(r'b2-hist-(\d+)', meta_id)
    if match:
        return int(match.group(1))
    return 0


def convert_meta_to_plan(meta: dict, sequence: int) -> dict:
    """Convert meta.yaml format to module-plan.schema.json format."""
    slug = meta.get('slug', meta.get('module', ''))

    # Convert content_outline points to subsections
    content_outline = []
    for section in meta.get('content_outline', []):
        outline_section = {
            'section': section.get('section', ''),
            'words': section.get('words', 0),
        }
        if 'points' in section:
            outline_section['subsections'] = section['points']
        content_outline.append(outline_section)

    # Convert vocabulary_hints - strip English translations
    vocabulary = []
    for word in meta.get('vocabulary_hints', {}).get('required', []):
        # Take only the Ukrainian word (before parenthetical translation)
        uk_word = word.split('(')[0].strip()
        vocabulary.append(uk_word)
    for word in meta.get('vocabulary_hints', {}).get('recommended', []):
        uk_word = word.split('(')[0].strip()
        vocabulary.append(uk_word)

    # Convert activity_hints
    activities = []
    for hint in meta.get('activity_hints', []):
        activity = {'type': hint.get('type', '')}
        if 'focus' in hint:
            activity['focus'] = hint['focus']
        if 'items' in hint:
            activity['items'] = hint['items']
        activities.append(activity)

    plan = {
        'module': slug,
        'level': 'b2-hist',
        'sequence': sequence,
        'version': '1.0',
        'title': meta.get('title', ''),
        'focus': meta.get('focus', 'history'),
        'pedagogy': meta.get('pedagogy', 'seminar'),
        'objectives': meta.get('objectives', []),
        'content_outline': content_outline,
        'word_target': meta.get('word_target', 4000),
    }

    if vocabulary:
        plan['vocabulary'] = vocabulary
    if activities:
        plan['activities'] = activities
    if 'sources' in meta:
        plan['sources'] = meta['sources']

    return plan


def main():
    meta_dir = Path('curriculum/l2-uk-en/b2-hist/meta')
    output_dir = Path('curriculum/l2-uk-en/plans/b2-hist')
    output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0

    for meta_file in sorted(meta_dir.glob('*.yaml')):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f)

            if not meta:
                print(f"  Skipping empty file: {meta_file.name}")
                skipped += 1
                continue

            # Skip if no content_outline (skeleton file)
            if not meta.get('content_outline'):
                print(f"  Skipping skeleton: {meta_file.name}")
                skipped += 1
                continue

            # Extract sequence from module ID
            sequence = extract_sequence_from_id(meta.get('id', meta.get('module', '')))
            if sequence == 0:
                # Try to extract from filename
                match = re.search(r'(\d+)', meta_file.stem)
                if match:
                    sequence = int(match.group(1))

            plan = convert_meta_to_plan(meta, sequence)

            # Write plan file
            slug = meta.get('slug', meta_file.stem)
            output_file = output_dir / f"{slug}.yaml"
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            processed += 1

        except Exception as e:
            print(f"  Error processing {meta_file.name}: {e}")
            skipped += 1

    print(f"\nExtracted {processed} plans, skipped {skipped}")


if __name__ == '__main__':
    main()
