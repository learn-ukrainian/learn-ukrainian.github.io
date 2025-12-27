#!/usr/bin/env python3
"""
Grammar Validation Queue Generator

Extracts sentences from YAML activities and generates a validation queue
for cross-agent grammar checking.

Phase 1: Error-correction activities only
Phase 2: Expand to fill-in, cloze, unjumble (future)

Usage:
    python scripts/generate_grammar_queue.py curriculum/l2-uk-en/b1/17-motion-coming-going.md
    python scripts/generate_grammar_queue.py curriculum/l2-uk-en/b1/  # All modules in directory
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml


def load_yaml_activities(md_file_path: str) -> list[dict] | None:
    """Load activities from YAML file if it exists."""
    yaml_path = Path(md_file_path).with_suffix('.activities.yaml')
    if not yaml_path.exists():
        return None

    with open(yaml_path, 'r', encoding='utf-8') as f:
        raw_data = yaml.safe_load(f)

    if raw_data is None:
        return None

    # Support both formats: direct list or wrapped in 'activities' key
    if isinstance(raw_data, dict) and 'activities' in raw_data:
        return raw_data['activities']

    if isinstance(raw_data, list):
        return raw_data

    return None


def extract_error_correction_items(activities: list[dict]) -> list[dict]:
    """Extract error-correction items for validation."""
    items = []

    for activity in activities:
        act_type = activity.get('type', '').lower()
        if act_type != 'error-correction':
            continue

        title = activity.get('title', 'Untitled')

        for item in activity.get('items', []):
            sentence = item.get('sentence', '')
            error = item.get('error', '')
            answer = item.get('answer', '')
            options = item.get('options', [])
            explanation = item.get('explanation', '')

            if sentence and error and answer:
                # Create sentence with error replaced by answer
                sentence_corrected = sentence.replace(error, answer)

                items.append({
                    'activity': 'error-correction',
                    'title': title,
                    'sentence_with_error': sentence,
                    'error': error,
                    'answer': answer,
                    'sentence_corrected': sentence_corrected,
                    'options': options,
                    'original_explanation': explanation,
                    'validate': {
                        'error_is_real_mistake': None,
                        'corrected_sentence_valid': None,
                        'explanation': None,
                        'confidence': None,
                    }
                })

    return items


def extract_module_info(md_file_path: str) -> dict:
    """Extract module info from file path."""
    path = Path(md_file_path)

    # Get level from parent directory
    level = path.parent.name.upper()

    # Get module name from filename (without extension)
    module_name = path.stem

    # Try to extract module number
    parts = module_name.split('-')
    try:
        module_num = int(parts[0])
    except (ValueError, IndexError):
        module_num = 0

    return {
        'level': level,
        'module_name': module_name,
        'module_num': module_num,
        'file_path': str(path),
    }


def generate_queue(md_file_path: str) -> dict | None:
    """Generate grammar validation queue for a module."""
    activities = load_yaml_activities(md_file_path)

    if not activities:
        return None

    module_info = extract_module_info(md_file_path)

    # Phase 1: Error-correction only
    error_correction_items = extract_error_correction_items(activities)

    if not error_correction_items:
        return None

    queue = {
        'module': module_info['module_name'],
        'level': module_info['level'],
        'file': module_info['file_path'],
        'generated': datetime.now().isoformat(),
        'phase': 1,
        'scope': 'error-correction',
        'item_count': len(error_correction_items),
        'items': error_correction_items,
    }

    return queue


def write_queue(queue: dict, md_file_path: str) -> str:
    """Write queue to YAML file."""
    output_path = Path(md_file_path).with_suffix('.grammar-queue.yaml')

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(queue, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return str(output_path)


def process_file(md_file_path: str) -> bool:
    """Process a single module file."""
    if not os.path.exists(md_file_path):
        print(f"  ❌ File not found: {md_file_path}")
        return False

    queue = generate_queue(md_file_path)

    if not queue:
        print(f"  ⏭️  No error-correction activities: {Path(md_file_path).name}")
        return False

    output_path = write_queue(queue, md_file_path)
    print(f"  ✅ Generated queue ({queue['item_count']} items): {Path(output_path).name}")
    return True


def process_directory(dir_path: str) -> tuple[int, int]:
    """Process all modules in a directory."""
    success = 0
    skipped = 0

    for md_file in sorted(Path(dir_path).glob('*.md')):
        # Skip audit/review files
        if 'audit' in str(md_file) or 'review' in str(md_file):
            continue

        if process_file(str(md_file)):
            success += 1
        else:
            skipped += 1

    return success, skipped


def main():
    parser = argparse.ArgumentParser(
        description='Generate grammar validation queue from YAML activities'
    )
    parser.add_argument(
        'path',
        help='Module file (.md) or directory containing modules'
    )
    parser.add_argument(
        '--phase',
        type=int,
        default=1,
        choices=[1, 2],
        help='Extraction phase: 1=error-correction only, 2=all activities (future)'
    )

    args = parser.parse_args()

    print(f"\n🔍 Grammar Queue Generator (Phase {args.phase})\n")

    if os.path.isdir(args.path):
        success, skipped = process_directory(args.path)
        print(f"\n📊 Generated {success} queues, skipped {skipped} modules")
    else:
        process_file(args.path)

    print()


if __name__ == '__main__':
    main()
