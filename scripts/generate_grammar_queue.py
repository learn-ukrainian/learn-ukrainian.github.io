#!/usr/bin/env python3
"""
Grammar Validation Queue Generator

Extracts sentences from YAML activities and generates a validation queue
for cross-agent grammar checking.

Supported activity types:
- error-correction: Validates both error and corrected sentences
- fill-in: Validates sentences (with answer inserted)
- cloze: Validates passage text
- unjumble: Validates answer sentences
- quiz: Validates questions and options
- translate: Validates Ukrainian sentences
- true-false: Validates statements

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
    """Load activities from YAML file if it exists.

    Checks multiple locations:
    1. {level}/activities/{module}.yaml (new structure)
    2. {level}/activities/{module}.activities.yaml (hybrid)
    3. {level}/{module}.activities.yaml (legacy)
    """
    md_path = Path(md_file_path)

    # New structure: activities/{module}.yaml
    yaml_path = md_path.parent / 'activities' / (md_path.stem + '.yaml')

    # Hybrid: activities/{module}.activities.yaml
    if not yaml_path.exists():
        yaml_path = md_path.parent / 'activities' / (md_path.stem + '.activities.yaml')

    # Fallback to legacy: {module}.activities.yaml
    if not yaml_path.exists():
        yaml_path = md_path.parent / (md_path.stem + '.activities.yaml')

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


def extract_fill_in_items(activities: list[dict]) -> list[dict]:
    """Extract fill-in items for validation."""
    items = []

    for activity in activities:
        act_type = activity.get('type', '').lower()
        if act_type != 'fill-in':
            continue

        title = activity.get('title', 'Untitled')

        for item in activity.get('items', []):
            # Accept both 'sentence' and 'prompt' field names
            sentence = item.get('sentence') or item.get('prompt', '')
            answer = item.get('answer', '')

            if sentence and answer:
                # Create complete sentence by replacing blank marker with answer
                # Handle various blank markers: ___, {blank}, etc.
                complete_sentence = sentence
                for marker in ['___', '{blank}', '____', '_____']:
                    complete_sentence = complete_sentence.replace(marker, answer)

                items.append({
                    'activity': 'fill-in',
                    'title': title,
                    'sentence_template': sentence,
                    'answer': answer,
                    'complete_sentence': complete_sentence,
                    'validate': {
                        'sentence_valid': None,
                        'explanation': None,
                        'confidence': None,
                    }
                })

    return items


def extract_cloze_items(activities: list[dict]) -> list[dict]:
    """Extract cloze passage items for validation."""
    items = []

    for activity in activities:
        act_type = activity.get('type', '').lower()
        if act_type != 'cloze':
            continue

        title = activity.get('title', 'Untitled')
        passage = activity.get('passage', '')
        blanks = activity.get('blanks', [])

        if passage and blanks:
            # Reconstruct complete passage
            complete_passage = passage
            for i, blank in enumerate(blanks):
                answer = blank.get('answer', '')
                # Replace numbered blanks like {1}, {2}, etc.
                complete_passage = complete_passage.replace(f'{{{i+1}}}', answer)
                complete_passage = complete_passage.replace(f'{{blank{i+1}}}', answer)

            items.append({
                'activity': 'cloze',
                'title': title,
                'passage_template': passage,
                'blanks': blanks,
                'complete_passage': complete_passage,
                'validate': {
                    'passage_valid': None,
                    'explanation': None,
                    'confidence': None,
                }
            })

    return items


def extract_unjumble_items(activities: list[dict]) -> list[dict]:
    """Extract unjumble items for validation."""
    items = []

    for activity in activities:
        act_type = activity.get('type', '').lower()
        if act_type != 'unjumble':
            continue

        title = activity.get('title', 'Untitled')

        for item in activity.get('items', []):
            answer = item.get('answer', '')
            jumbled = item.get('jumbled', [])

            if answer:
                items.append({
                    'activity': 'unjumble',
                    'title': title,
                    'jumbled_words': jumbled,
                    'answer': answer,
                    'validate': {
                        'sentence_valid': None,
                        'explanation': None,
                        'confidence': None,
                    }
                })

    return items


def extract_quiz_items(activities: list[dict]) -> list[dict]:
    """Extract quiz items for validation."""
    items = []

    for activity in activities:
        act_type = activity.get('type', '').lower()
        if act_type != 'quiz':
            continue

        title = activity.get('title', 'Untitled')

        for item in activity.get('items', []):
            # Accept both 'question' and 'prompt' field names
            question = item.get('question') or item.get('prompt', '')
            options = item.get('options', [])
            answer = item.get('answer', '')

            if question:
                items.append({
                    'activity': 'quiz',
                    'title': title,
                    'question': question,
                    'options': options,
                    'answer': answer,
                    'validate': {
                        'question_valid': None,
                        'options_valid': None,
                        'explanation': None,
                        'confidence': None,
                    }
                })

    return items


def extract_translate_items(activities: list[dict]) -> list[dict]:
    """Extract translate items for validation."""
    items = []

    for activity in activities:
        act_type = activity.get('type', '').lower()
        if act_type != 'translate':
            continue

        title = activity.get('title', 'Untitled')

        for item in activity.get('items', []):
            # Accept both 'sentence' and 'prompt' field names
            sentence = item.get('sentence') or item.get('prompt', '')
            answer = item.get('answer', '')
            options = item.get('options', [])

            if sentence or answer:
                items.append({
                    'activity': 'translate',
                    'title': title,
                    'source_sentence': sentence,
                    'answer': answer,
                    'options': options,
                    'validate': {
                        'source_valid': None,
                        'answer_valid': None,
                        'explanation': None,
                        'confidence': None,
                    }
                })

    return items


def extract_true_false_items(activities: list[dict]) -> list[dict]:
    """Extract true-false items for validation."""
    items = []

    for activity in activities:
        act_type = activity.get('type', '').lower()
        if act_type != 'true-false':
            continue

        title = activity.get('title', 'Untitled')

        for item in activity.get('items', []):
            statement = item.get('statement', '')
            answer = item.get('answer', '')

            if statement:
                items.append({
                    'activity': 'true-false',
                    'title': title,
                    'statement': statement,
                    'answer': answer,
                    'validate': {
                        'statement_valid': None,
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

    # Extract items from all activity types
    all_items = []
    activity_counts = {}

    extractors = [
        ('error-correction', extract_error_correction_items),
        ('fill-in', extract_fill_in_items),
        ('cloze', extract_cloze_items),
        ('unjumble', extract_unjumble_items),
        ('quiz', extract_quiz_items),
        ('translate', extract_translate_items),
        ('true-false', extract_true_false_items),
    ]

    for activity_type, extractor in extractors:
        items = extractor(activities)
        if items:
            all_items.extend(items)
            activity_counts[activity_type] = len(items)

    if not all_items:
        return None

    # Build scope string from activity types found
    scope = ', '.join(sorted(activity_counts.keys()))

    queue = {
        'module': module_info['module_name'],
        'level': module_info['level'],
        'file': module_info['file_path'],
        'generated': datetime.now().isoformat(),
        'scope': scope,
        'activity_counts': activity_counts,
        'item_count': len(all_items),
        'items': all_items,
    }

    return queue


def write_queue(queue: dict, md_file_path: str) -> str:
    """Write queue to YAML file in queue/ subfolder."""
    md_path = Path(md_file_path)

    # New structure: queue/{module}.yaml
    queue_dir = md_path.parent / 'queue'
    queue_dir.mkdir(exist_ok=True)
    output_path = queue_dir / (md_path.stem + '.yaml')

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
        print(f"  ⏭️  No validatable activities: {Path(md_file_path).name}")
        return False

    output_path = write_queue(queue, md_file_path)
    # Show breakdown by activity type
    counts = queue.get('activity_counts', {})
    breakdown = ', '.join(f"{k}:{v}" for k, v in sorted(counts.items()))
    print(f"  ✅ Generated queue ({queue['item_count']} items: {breakdown}): {Path(output_path).name}")
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

    args = parser.parse_args()

    print("\n🔍 Grammar Queue Generator\n")

    if os.path.isdir(args.path):
        success, skipped = process_directory(args.path)
        print(f"\n📊 Generated {success} queues, skipped {skipped} modules")
    else:
        process_file(args.path)

    print()


if __name__ == '__main__':
    main()
