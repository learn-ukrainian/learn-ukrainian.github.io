#!/usr/bin/env python3
"""
Generate activity quality validation queue files.

This script:
1. Reads activity YAML files
2. Runs deterministic quality checks from activity_quality.py
3. Generates queue YAML files with:
   - Pre-populated deterministic check results
   - Empty fields for manual semantic validation

Usage:
    python scripts/audit/generate_activity_quality_queue.py l2-uk-en b1 52
    python scripts/audit/generate_activity_quality_queue.py l2-uk-en b2 75
"""

import argparse
import sys
from pathlib import Path
import yaml
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.audit.checks.activity_quality import (
    validate_activity_quality_deterministic,
    analyze_sentence_variety,
    estimate_vocabulary_difficulty,
    analyze_distractor_quality,
    check_natural_ukrainian_markers,
    estimate_cognitive_load
)


def extract_activity_text(activity: Dict, item: Dict = None) -> str:
    """
    Extract all Ukrainian text from an activity item for analysis.

    Args:
        activity: Activity dict with type and items
        item: Optional specific item to extract from

    Returns:
        Combined text string for analysis
    """
    text_parts = []

    # Use specific item if provided, otherwise use first item
    if item is None and activity.get('items'):
        item = activity['items'][0]

    if not item:
        return ""

    activity_type = activity.get('type', '')

    # Extract based on activity type
    if activity_type in ['quiz', 'translate', 'select']:
        if 'question' in item:
            text_parts.append(item['question'])
        if 'sentence' in item:
            text_parts.append(item['sentence'])
        if 'prompt' in item:
            text_parts.append(item['prompt'])

    elif activity_type == 'fill-in':
        if 'sentence' in item:
            text_parts.append(item['sentence'])
        if 'prompt' in item:
            text_parts.append(item['prompt'])

    elif activity_type == 'error-correction':
        if 'sentence' in item:
            text_parts.append(item['sentence'])
        if 'error' in item:
            text_parts.append(item['error'])
        if 'answer' in item:
            text_parts.append(item['answer'])

    elif activity_type == 'cloze':
        if 'text' in item:
            text_parts.append(item['text'])
        if 'passage' in item:
            text_parts.append(item['passage'])

    elif activity_type == 'unjumble':
        if 'words' in item:
            text_parts.append(' '.join(item['words']))
        if 'answer' in item:
            text_parts.append(item['answer'])

    elif activity_type == 'true-false':
        if 'statement' in item:
            text_parts.append(item['statement'])

    elif activity_type == 'match-up':
        # For match-up, combine all pairs
        if 'pairs' in activity:
            for pair in activity['pairs']:
                if 'left' in pair:
                    text_parts.append(pair['left'])
                if 'right' in pair:
                    text_parts.append(pair['right'])

    return ' '.join(text_parts).strip()


def extract_options(activity: Dict, item: Dict = None) -> tuple[List[str], str]:
    """
    Extract options and correct answer from activity item.

    Returns:
        (options_list, correct_answer)
    """
    if item is None and activity.get('items'):
        item = activity['items'][0]

    if not item:
        return [], None

    activity_type = activity.get('type', '')
    options = []
    correct_answer = None

    if activity_type in ['quiz', 'select', 'translate']:
        if 'options' in item:
            for opt in item['options']:
                opt_text = opt.get('text', '')
                options.append(opt_text)
                if opt.get('correct'):
                    correct_answer = opt_text

    elif activity_type == 'fill-in':
        if 'options' in item:
            options = item['options']
        if 'answer' in item:
            correct_answer = item['answer']

    elif activity_type == 'error-correction':
        if 'options' in item:
            options = item['options']
        if 'answer' in item:
            correct_answer = item['answer']

    return options, correct_answer


def run_deterministic_checks(
    activity: Dict,
    level_code: str,
    module_num: int
) -> Dict[str, Any]:
    """
    Run all deterministic quality checks on an activity.

    Returns:
        Dict with deterministic check results
    """
    activity_type = activity.get('type', '')
    activity_title = activity.get('title', 'Untitled')

    # Extract text from all items
    all_text = []
    all_items_checks = []

    for idx, item in enumerate(activity.get('items', [])):
        item_text = extract_activity_text(activity, item)
        if item_text:
            all_text.append(item_text)

            # Run checks per item
            options, correct_answer = extract_options(activity, item)

            item_checks = validate_activity_quality_deterministic(
                text=item_text,
                activity_type=activity_type,
                level_code=level_code,
                options=options if options else None,
                correct_answer=correct_answer
            )

            all_items_checks.append({
                'item_index': idx,
                'text_preview': item_text[:100] + '...' if len(item_text) > 100 else item_text,
                'checks': item_checks
            })

    # Aggregate results
    combined_text = ' '.join(all_text)

    # Overall variety check (across all items)
    all_sentences = []
    for text in all_text:
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 5]
        all_sentences.extend(sentences)

    variety_result = analyze_sentence_variety(all_sentences) if len(all_sentences) > 2 else None

    # Aggregate difficulty
    vocab_difficulty = estimate_vocabulary_difficulty(combined_text, level_code)

    # Aggregate cognitive load
    cognitive_load = estimate_cognitive_load(combined_text, activity_type, level_code)

    # Aggregate naturalness issues
    naturalness_result = check_natural_ukrainian_markers(combined_text)

    # Aggregate distractor quality (average across items with options)
    distractor_qualities = []
    for item_check in all_items_checks:
        if item_check['checks'].get('distractor_analysis'):
            quality = item_check['checks']['distractor_analysis'].get('quality')
            if quality:
                distractor_qualities.append(quality)

    avg_distractor_quality = sum(distractor_qualities) / len(distractor_qualities) if distractor_qualities else None

    return {
        'activity_id': f"{activity_type}-{activity_title.lower().replace(' ', '-')[:30]}",
        'activity_type': activity_type,
        'activity_title': activity_title,
        'item_count': len(activity.get('items', [])),
        'deterministic_checks': {
            'variety_score': variety_result['score'] if variety_result else None,
            'variety_issues': variety_result['issues'] if variety_result else [],
            'vocabulary_difficulty': vocab_difficulty,
            'cognitive_load': cognitive_load,
            'naturalness_issues': naturalness_result['issues'],
            'naturalness_suggestions': naturalness_result['suggestions'],
            'distractor_quality_avg': avg_distractor_quality,
            'per_item_checks': all_items_checks
        },
        # Manual validation fields (empty)
        'naturalness': None,  # 1-5 scale
        'difficulty': None,  # too_easy | appropriate | too_hard
        'engagement': None,  # 1-5 scale
        'distractor_score': None,  # 1-5 scale
        'variety_score': None,  # 1-5 scale (manual assessment)
        'issues': [],
        'suggestions': []
    }


def generate_queue_file(
    content_root: Path,
    level: str,
    module_num: int
) -> None:
    """
    Generate quality validation queue file for a module.

    Args:
        content_root: Root content directory (curriculum/l2-uk-en)
        level: Level code (a1, a2, b1, b2, c1, c2)
        module_num: Module number (1-200)
    """
    level_dir = content_root / level

    # Find activity YAML file
    activity_files = list((level_dir / 'activities').glob(f'{module_num:02d}-*.yaml'))
    if not activity_files:
        # Try without zero-padding
        activity_files = list((level_dir / 'activities').glob(f'{module_num}-*.yaml'))

    if not activity_files:
        print(f"⚠️  No activity file found for {level.upper()} module {module_num}")
        return

    activity_file = activity_files[0]
    module_slug = activity_file.stem

    print(f"📄 Processing: {activity_file.name}")

    # Load activities
    with open(activity_file, 'r', encoding='utf-8') as f:
        activities = yaml.safe_load(f)

    if not activities:
        print(f"⚠️  No activities found in {activity_file}")
        return

    # Run deterministic checks on each activity
    queue_data = {
        'module': module_slug,
        'level': level.upper(),
        'module_number': module_num,
        'activity_file': str(activity_file.relative_to(content_root)),
        'activities': []
    }

    for activity in activities:
        checks = run_deterministic_checks(activity, level.upper(), module_num)
        queue_data['activities'].append(checks)

    # Write queue file
    queue_dir = level_dir / 'queue'
    queue_dir.mkdir(exist_ok=True)
    queue_file = queue_dir / f'{module_slug}-quality.yaml'

    with open(queue_file, 'w', encoding='utf-8') as f:
        yaml.dump(queue_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ Generated: {queue_file.relative_to(content_root)}")
    print(f"   Activities: {len(activities)}")

    # Print summary of deterministic checks
    variety_issues = sum(len(a['deterministic_checks']['variety_issues']) for a in queue_data['activities'])
    naturalness_issues = sum(len(a['deterministic_checks']['naturalness_issues']) for a in queue_data['activities'])

    if variety_issues > 0:
        print(f"   ⚠️  Variety issues: {variety_issues}")
    if naturalness_issues > 0:
        print(f"   ⚠️  Naturalness issues: {naturalness_issues}")

    difficulty_inappropriate = sum(
        1 for a in queue_data['activities']
        if a['deterministic_checks']['vocabulary_difficulty'] != 'appropriate'
    )
    if difficulty_inappropriate > 0:
        print(f"   ⚠️  Difficulty mismatches: {difficulty_inappropriate}/{len(activities)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate activity quality validation queue files'
    )
    parser.add_argument('content', help='Content identifier (e.g., l2-uk-en)')
    parser.add_argument('level', help='Level (a1, a2, b1, b2, c1, c2)')
    parser.add_argument('module', type=int, nargs='?', help='Module number (optional, generates all if omitted)')

    args = parser.parse_args()

    # Resolve paths
    repo_root = Path(__file__).parent.parent.parent
    content_root = repo_root / 'curriculum' / args.content

    if not content_root.exists():
        print(f"❌ Content directory not found: {content_root}")
        sys.exit(1)

    level = args.level.lower()
    level_dir = content_root / level

    if not level_dir.exists():
        print(f"❌ Level directory not found: {level_dir}")
        sys.exit(1)

    print(f"🔍 Generating quality queues for {args.content}/{level}")
    print()

    if args.module:
        # Single module
        generate_queue_file(content_root, level, args.module)
    else:
        # All modules in level
        activity_files = sorted((level_dir / 'activities').glob('*.yaml'))

        if not activity_files:
            print(f"⚠️  No activity files found in {level_dir / 'activities'}")
            return

        print(f"Found {len(activity_files)} activity files\n")

        for activity_file in activity_files:
            # Extract module number from filename
            import re
            match = re.match(r'(\d+)-', activity_file.stem)
            if match:
                module_num = int(match.group(1))
                generate_queue_file(content_root, level, module_num)
                print()


if __name__ == '__main__':
    main()
