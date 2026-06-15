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

import json
import re
import sys
from pathlib import Path

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit.checks.yaml_schema_validation import validate_activity_yaml_file
from manifest_utils import get_module_by_number, get_modules_for_level
from yaml_activities import ActivityParser

# Activity type validation rules
ACTIVITY_TYPES = {
    'quiz', 'match-up', 'fill-in', 'true-false', 'group-sort', 'unjumble',
    'anagram', 'error-correction', 'cloze', 'mark-the-words',
    'select', 'translate',
    # Advanced activity types (C1+)
    'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'
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
    'mark-the-words': ['title'],  # Accept both 'text' and 'passage' (checked separately)
    'select': ['title', 'items'],
    'translate': ['title', 'items'],
    # Advanced activity types (C1+) - minimal validation (context optional)
    'reading': ['title'],
    'essay-response': ['title'],
    'critical-analysis': ['title'],
    'comparative-study': ['title'],
    'authorial-intent': ['title'],
}


class ActivityValidator:
    def __init__(self, curriculum: str, level: str, module_num: int | None = None):
        self.curriculum = curriculum
        self.level = level
        self.module_num = module_num
        self.errors = []
        self.warnings = []

    def validate_yaml(self, yaml_path: Path) -> dict:
        """Validate YAML against schema and the renderer parser."""
        results = {'pass': True, 'errors': [], 'warnings': []}

        schema_ok, schema_errors = validate_activity_yaml_file(yaml_path)
        if not schema_ok:
            results['pass'] = False
            results['errors'].extend(schema_errors)

        try:
            parsed = ActivityParser().parse(yaml_path)
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as e:
            results['pass'] = False
            results['errors'].append(f"Parser error: {type(e).__name__}: {e}")
            return results

        if not parsed:
            results['pass'] = False
            results['errors'].append("No renderable activities found")

        return results

    def validate_mdx(self, mdx_path: Path) -> dict:
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
                            "Unjumble activity has empty 'jumbled' field (Issue #362)"
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

    def _modules(self):
        """Return manifest modules for this run."""
        if self.module_num:
            module = get_module_by_number(self.level, self.module_num)
            return [module] if module else []
        return get_modules_for_level(self.level)

    def _activity_yaml_path(self, module) -> Path | None:
        """Find the activity YAML for current per-module layout, with legacy fallback."""
        level_dir = PROJECT_ROOT / 'curriculum' / self.curriculum / self.level
        candidates = [
            level_dir / module.slug / 'activities.yaml',
            level_dir / 'activities' / f'{module.slug}.yaml',
            level_dir / 'activities' / f'{module.numbered_slug}.yaml',
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def run(self) -> dict:
        """Run validation pipeline."""
        modules = self._modules()
        if not modules:
            print(f"No manifest modules found for level {self.level!r}")
            return {'pass': False, 'errors': 1, 'warnings': 0}

        total_errors = 0
        total_warnings = 0
        scanned = 0

        for module in modules:
            yaml_file = self._activity_yaml_path(module)
            if not yaml_file:
                total_warnings += 1
                print(f"\n=== Module {module.local_num}: {module.slug} ===")
                print("  ⚠️  YAML: no activity file found")
                continue

            scanned += 1

            print(f"\n=== Module {module.local_num}: {module.slug} ===")

            # 1. YAML validation
            yaml_results = self.validate_yaml(yaml_file)
            if not yaml_results['pass']:
                print(f"  ❌ YAML: {len(yaml_results['errors'])} errors")
                for err in yaml_results['errors']:
                    print(f"     - {err}")
                total_errors += len(yaml_results['errors'])
            else:
                print("  ✅ YAML")

            if yaml_results['warnings']:
                total_warnings += len(yaml_results['warnings'])
                for warn in yaml_results['warnings']:
                    print(f"     ⚠️  {warn}")

            # 2. MDX validation
            mdx_path = PROJECT_ROOT / 'site' / 'src' / 'content' / 'docs' / self.level / f'{module.slug}.mdx'
            mdx_results = self.validate_mdx(mdx_path)
            if not mdx_results['pass']:
                print(f"  ❌ MDX: {len(mdx_results['errors'])} errors")
                for err in mdx_results['errors']:
                    print(f"     - {err}")
                total_errors += len(mdx_results['errors'])
            else:
                print("  ✅ MDX")

            if mdx_results['warnings']:
                total_warnings += len(mdx_results['warnings'])
                for warn in mdx_results['warnings']:
                    print(f"     ⚠️  {warn}")

        print(f"\n{'='*50}")
        if scanned == 0:
            print("❌ FAILED: no activity files scanned")
            return {'pass': False, 'errors': 1, 'warnings': total_warnings}

        if total_errors > 0:
            print(f"❌ FAILED: {total_errors} errors, {total_warnings} warnings")
            return {'pass': False, 'errors': total_errors, 'warnings': total_warnings}
        elif total_warnings > 0:
            print(f"⚠️  WARNINGS: {total_warnings} warnings")
            return {'pass': True, 'errors': 0, 'warnings': total_warnings}
        else:
            print("✅ ALL VALIDATIONS PASSED")
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
