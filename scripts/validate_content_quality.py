#!/usr/bin/env python3
"""
Content Quality Validator

Extracts Ukrainian sentences from activities and prepares them for
validation with Ukrainian Grammar Validator (Claude/Gemini).

This checks SEMANTIC correctness (not just format):
- Are quiz answers actually correct?
- Are error-correction errors real errors?
- Are fill-in answers grammatically correct?
- Are translations accurate?

Usage:
    python scripts/validate_content_quality.py curriculum/l2-uk-en/b1/06-aspect-complete-system.md
"""

import sys
import yaml
from pathlib import Path
from typing import Optional

def load_yaml_activities(md_file_path: str) -> list[dict] | None:
    """Load activities from YAML file if it exists.

    Checks two locations (new structure first, then legacy):
    1. {level}/activities/{module}.yaml (new structure)
    2. {level}/{module}.activities.yaml (legacy)
    """
    md_path = Path(md_file_path)

    # New structure: activities/{module}.yaml
    yaml_path = md_path.parent / 'activities' / (md_path.stem + '.yaml')

    # Fallback to legacy: {module}.activities.yaml
    if not yaml_path.exists():
        yaml_path = md_path.parent / (md_path.stem + '.activities.yaml')

    if not yaml_path.exists():
        return None

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Skip comment header
            yaml_content = '\n'.join([line for line in content.split('\n') if not line.startswith('#')])
            data = yaml.safe_load(yaml_content)
            return data if isinstance(data, list) else None
    except Exception as e:
        print(f"Error loading YAML: {e}")
        return None


def extract_validation_items(activities: list[dict], level: str, module_name: str) -> list[dict]:
    """
    Extract items that need validation from activities.

    Returns list of validation requests in format:
    {
        "activity_type": "quiz",
        "activity_title": "...",
        "item_number": 1,
        "sentence": "Ukrainian sentence to validate",
        "context": "What this sentence is teaching/testing",
        "validation_type": "answer_correctness" | "error_detection" | "translation",
        "expected_correct": true/false,
        "explanation": "Why this should be correct/incorrect"
    }
    """
    validation_items = []

    for activity in activities:
        act_type = activity.get('type', '')
        title = activity.get('title', '')
        items = activity.get('items', [])

        # QUIZ: Check if correct answers are actually correct
        if act_type == 'quiz':
            for idx, item in enumerate(items, 1):
                question = item.get('question', '')
                options = item.get('options', [])
                explanation = item.get('explanation', '')

                correct_options = [opt['text'] for opt in options if opt.get('correct')]

                for correct_answer in correct_options:
                    validation_items.append({
                        'activity_type': 'quiz',
                        'activity_title': title,
                        'item_number': idx,
                        'sentence': f"Q: {question}\nA: {correct_answer}",
                        'context': f"Quiz about {title}. This answer is marked as CORRECT.",
                        'validation_type': 'answer_correctness',
                        'expected_correct': True,
                        'explanation': explanation
                    })

        # ERROR-CORRECTION: Check if flagged errors are real errors
        elif act_type == 'error-correction':
            for idx, item in enumerate(items, 1):
                sentence = item.get('sentence', '')
                error_word = item.get('error', '')
                correct_word = item.get('answer', '')
                explanation = item.get('explanation', '')

                validation_items.append({
                    'activity_type': 'error-correction',
                    'activity_title': title,
                    'item_number': idx,
                    'sentence': sentence,
                    'context': f"Error-correction: '{error_word}' flagged as WRONG, should be '{correct_word}'",
                    'validation_type': 'error_detection',
                    'flagged_error': error_word,
                    'suggested_correction': correct_word,
                    'explanation': explanation
                })

        # FILL-IN: Check if answers are grammatically correct
        elif act_type == 'fill-in':
            for idx, item in enumerate(items, 1):
                sentence = item.get('sentence', '')
                answer = item.get('answer', '')

                # Reconstruct full sentence
                full_sentence = sentence.replace('___', answer)

                validation_items.append({
                    'activity_type': 'fill-in',
                    'activity_title': title,
                    'item_number': idx,
                    'sentence': full_sentence,
                    'context': f"Fill-in answer: '{answer}' in context",
                    'validation_type': 'answer_correctness',
                    'answer': answer
                })

        # TRANSLATE: Check if translations are accurate
        elif act_type == 'translate':
            for idx, item in enumerate(items, 1):
                question = item.get('question', '')
                options = item.get('options', [])

                correct_translation = [opt['text'] for opt in options if opt.get('correct')][0] if options else ''

                validation_items.append({
                    'activity_type': 'translate',
                    'activity_title': title,
                    'item_number': idx,
                    'sentence': correct_translation,
                    'context': f"Translation of: '{question}'",
                    'validation_type': 'translation',
                    'source': question,
                    'target': correct_translation
                })

    return validation_items


def generate_validation_report(md_file: str, output_file: Optional[str] = None):
    """Generate validation report for a module."""
    md_path = Path(md_file)

    # Extract level from path
    parts = md_path.parts
    level = 'unknown'
    for part in parts:
        if part.lower() in ('a1', 'a2', 'b1', 'b2', 'c1', 'c2'):
            level = part.upper()
            break

    # Load activities
    activities = load_yaml_activities(md_file)

    if not activities:
        print(f"No YAML activities found for {md_file}")
        return

    # Extract validation items
    validation_items = extract_validation_items(activities, level, md_path.stem)

    # Generate report
    report = []
    report.append(f"# Content Quality Validation Report")
    report.append(f"**Module:** {md_path.name}")
    report.append(f"**Level:** {level}")
    report.append(f"**Activities:** {len(activities)}")
    report.append(f"**Validation Items:** {len(validation_items)}")
    report.append("")
    report.append("---")
    report.append("")

    # Group by activity type
    by_type = {}
    for item in validation_items:
        act_type = item['activity_type']
        if act_type not in by_type:
            by_type[act_type] = []
        by_type[act_type].append(item)

    for act_type, items in by_type.items():
        report.append(f"## {act_type.upper()} Activities ({len(items)} items)")
        report.append("")

        for i, item in enumerate(items[:5], 1):  # Show first 5 of each type
            report.append(f"### Item {i}: {item['activity_title']}")
            report.append("")
            report.append(f"**Sentence:** {item['sentence']}")
            report.append(f"**Context:** {item['context']}")
            report.append(f"**Validation Type:** {item['validation_type']}")

            if 'flagged_error' in item:
                report.append(f"**Flagged Error:** {item['flagged_error']}")
                report.append(f"**Suggested Fix:** {item['suggested_correction']}")

            report.append("")
            report.append("**Validation Request (for Ukrainian Grammar Validator):**")
            report.append("```json")
            report.append("{")
            report.append(f'  "sentence": "{item["sentence"]}",')
            report.append(f'  "level": "{level}",')
            report.append(f'  "context": "{item["context"]}"')
            if 'flagged_error' in item:
                report.append(f'  "flagged_issue": "Is \'{item["flagged_error"]}\' actually wrong?",')
                report.append(f'  "suggested_correction": "{item["suggested_correction"]}"')
            report.append("}")
            report.append("```")
            report.append("")
            report.append("---")
            report.append("")

        if len(items) > 5:
            report.append(f"*...and {len(items) - 5} more items*")
            report.append("")

    report_text = '\n'.join(report)

    if output_file:
        Path(output_file).write_text(report_text, encoding='utf-8')
        print(f"Validation report written to: {output_file}")
    else:
        print(report_text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_content_quality.py <module.md> [output.md]")
        print("Example: python scripts/validate_content_quality.py curriculum/l2-uk-en/b1/06-aspect-complete-system.md")
        sys.exit(1)

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    generate_validation_report(md_file, output_file)
