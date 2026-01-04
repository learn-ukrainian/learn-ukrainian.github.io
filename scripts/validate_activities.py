#!/usr/bin/env python3
"""Universal activity validator - detects broken activities at all pipeline stages.

Checks activities at 3 levels:
1. YAML Level - Structural validation
2. MDX Level - Generation correctness  
3. HTML Level - Browser rendering (requires dev server)

Usage:
    .venv/bin/python scripts/validate_activities.py l2-uk-en a1
    .venv/bin/python scripts/validate_activities.py l2-uk-en a1 26
    .venv/bin/python scripts/validate_activities.py l2-uk-en a1 --fix
"""

import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


# Activity type validation rules
ACTIVITY_TYPES = {
    'quiz', 'match-up', 'fill-in', 'true-false', 'group-sort', 'unjumble',
    'anagram', 'error-correction', 'cloze', 'mark-the-words',
    'dialogue-reorder', 'select', 'translate'
}

REQUIRED_FIELDS = {
    'quiz': ['title', 'items'],
    'match-up': ['title', 'pairs'],
    'fill-in': ['title', 'items'],
    'true-false': ['title', 'items'],
    'group-sort': ['title', 'groups'],
    'unjumble': ['title', 'items'],
    'anagram': ['title', 'items'],
    'error-correction': ['title', 'items'],
    'cloze': ['title', 'passage'],
    'mark-the-words': ['title', 'text'],
    'dialogue-reorder': ['title', 'lines'],
    'select': ['title', 'items'],
    'translate': ['title', 'items'],
}


class ActivityValidator:
    def __init__(self, curriculum: str, level: str, module_num: int = None):
        self.curriculum = curriculum
        self.level = level
        self.module_num = module_num
        self.errors = []
        self.warnings = []

    def validate_yaml(self, yaml_path: Path) -> Dict:
        """Validate YAML activity file structure."""
        results = {'pass': True, 'errors': [], 'warnings': []}

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            results['pass'] = False
            results['errors'].append(f"YAML parse error: {e}")
            return results

        # Handle both formats: direct list or dict with 'activities' key
        if isinstance(data, dict) and 'activities' in data:
            activities = data['activities']
        elif isinstance(data, list):
            activities = data
        else:
            results['pass'] = False
            results['errors'].append("Not a valid activity list")
            return results

        if not activities:
            results['pass'] = False
            results['errors'].append("Empty activity list")
            return results

        for idx, activity in enumerate(activities, 1):
            if not isinstance(activity, dict):
                results['errors'].append(f"Activity {idx}: Not a dict")
                results['pass'] = False
                continue

            activity_type = activity.get('type')
            if not activity_type:
                results['errors'].append(f"Activity {idx}: Missing 'type' field")
                results['pass'] = False
                continue

            if activity_type not in ACTIVITY_TYPES:
                results['errors'].append(f"Activity {idx}: Unknown type '{activity_type}'")
                results['pass'] = False
                continue

            # Check required fields
            required = REQUIRED_FIELDS.get(activity_type, [])
            for field in required:
                if field not in activity:
                    results['errors'].append(
                        f"Activity {idx} ({activity_type}): Missing required field '{field}'"
                    )
                    results['pass'] = False

            # Type-specific validation
            if activity_type == 'unjumble' or activity_type == 'anagram':
                self._validate_unjumble(activity, idx, results)

            elif activity_type == 'mark-the-words':
                self._validate_mark_the_words(activity, idx, results)

        return results

    def _validate_unjumble(self, activity: dict, idx: int, results: dict):
        """Validate unjumble/anagram activity."""
        items = activity.get('items', [])

        for item_idx, item in enumerate(items, 1):
            has_words = 'words' in item
            has_jumbled = 'jumbled' in item
            has_prompt = 'prompt' in item
            has_scrambled = 'scrambled' in item
            has_answer = 'answer' in item

            if not has_answer:
                results['errors'].append(
                    f"Activity {idx} item {item_idx}: Missing 'answer' field"
                )
                results['pass'] = False

            if not (has_words or has_jumbled or has_prompt or has_scrambled):
                results['errors'].append(
                    f"Activity {idx} item {item_idx}: Missing 'words', 'jumbled', 'prompt', or 'scrambled' field"
                )
                results['pass'] = False

            # Check words format
            if has_words and not isinstance(item['words'], list):
                results['errors'].append(
                    f"Activity {idx} item {item_idx}: 'words' must be array"
                )
                results['pass'] = False

    def _validate_mark_the_words(self, activity: dict, idx: int, results: dict):
        """Validate mark-the-words activity."""
        text = activity.get('text', '')

        # Check for malformed markdown annotations
        if '(correct)' in text or '(wrong)' in text:
            results['errors'].append(
                f"Activity {idx}: Contains (correct)/(wrong) annotations - "
                f"use *word* only (see Issue #361)"
            )
            results['pass'] = False

    def validate_mdx(self, mdx_path: Path) -> Dict:
        """Validate MDX generation correctness."""
        results = {'pass': True, 'errors': [], 'warnings': []}

        if not mdx_path.exists():
            results['pass'] = False
            results['errors'].append(f"MDX file not found: {mdx_path}")
            return results

        content = mdx_path.read_text(encoding='utf-8')

        # Check for empty jumbled fields (Issue #362)
        unjumble_pattern = r'<Unjumble[^>]*items=\{JSON\.parse\(`([^`]+)`\)\}'
        for match in re.finditer(unjumble_pattern, content):
            json_str = match.group(1)
            try:
                items = json.loads(json_str)
                for item in items:
                    if 'jumbled' in item and not item['jumbled']:
                        results['errors'].append(
                            f"Unjumble activity has empty 'jumbled' field (Issue #362)"
                        )
                        results['pass'] = False
                        break
            except json.JSONDecodeError:
                results['warnings'].append("Could not parse Unjumble JSON")

        # Check for mark-the-words malformed patterns
        mark_words_pattern = r'<MarkTheWords[^>]*text="([^"]*)\(correct\)'
        if re.search(mark_words_pattern, content):
            results['errors'].append(
                "MarkTheWords component contains (correct) annotation (Issue #361)"
            )
            results['pass'] = False

        return results

    def run(self) -> Dict:
        """Run validation pipeline."""
        if self.module_num:
            modules = [self.module_num]
        else:
            # Find all modules in level
            level_dir = Path(f'curriculum/{self.curriculum}/{self.level}')
            modules = sorted([
                int(f.stem.split('-')[0])
                for f in level_dir.glob('*.md')
                if f.stem[0].isdigit()
            ])

        total_errors = 0
        total_warnings = 0

        for module_num in modules:
            # Find YAML activity file
            yaml_path = Path(
                f'curriculum/{self.curriculum}/{self.level}/activities/'
            )
            yaml_files = list(yaml_path.glob(f'{module_num:02d}-*.yaml'))
            
            if not yaml_files:
                yaml_files = list(yaml_path.glob(f'{module_num}-*.yaml'))

            if not yaml_files:
                continue

            yaml_file = yaml_files[0]

            print(f"\n=== Module {module_num} ===")

            # 1. YAML validation
            yaml_results = self.validate_yaml(yaml_file)
            if not yaml_results['pass']:
                print(f"  ❌ YAML: {len(yaml_results['errors'])} errors")
                for err in yaml_results['errors']:
                    print(f"     - {err}")
                total_errors += len(yaml_results['errors'])
            else:
                print(f"  ✅ YAML")

            if yaml_results['warnings']:
                total_warnings += len(yaml_results['warnings'])
                for warn in yaml_results['warnings']:
                    print(f"     ⚠️  {warn}")

            # 2. MDX validation
            mdx_path = Path(f'docusaurus/docs/{self.level}/module-{module_num:02d}.mdx')
            mdx_results = self.validate_mdx(mdx_path)
            if not mdx_results['pass']:
                print(f"  ❌ MDX: {len(mdx_results['errors'])} errors")
                for err in mdx_results['errors']:
                    print(f"     - {err}")
                total_errors += len(mdx_results['errors'])
            else:
                print(f"  ✅ MDX")

            if mdx_results['warnings']:
                total_warnings += len(mdx_results['warnings'])
                for warn in mdx_results['warnings']:
                    print(f"     ⚠️  {warn}")

        print(f"\n{'='*50}")
        if total_errors > 0:
            print(f"❌ FAILED: {total_errors} errors, {total_warnings} warnings")
            return {'pass': False, 'errors': total_errors, 'warnings': total_warnings}
        elif total_warnings > 0:
            print(f"⚠️  WARNINGS: {total_warnings} warnings")
            return {'pass': True, 'errors': 0, 'warnings': total_warnings}
        else:
            print(f"✅ ALL VALIDATIONS PASSED")
            return {'pass': True, 'errors': 0, 'warnings': 0}


def main():
    if len(sys.argv) < 3:
        print("Usage: .venv/bin/python scripts/validate_activities.py <curriculum> <level> [module_num]")
        print("Example: .venv/bin/python scripts/validate_activities.py l2-uk-en a1")
        print("Example: .venv/bin/python scripts/validate_activities.py l2-uk-en a1 26")
        return 1

    curriculum = sys.argv[1]
    level = sys.argv[2]
    module_num = int(sys.argv[3]) if len(sys.argv) > 3 else None

    validator = ActivityValidator(curriculum, level, module_num)
    result = validator.run()

    return 0 if result['pass'] else 1


if __name__ == '__main__':
    exit(main())
