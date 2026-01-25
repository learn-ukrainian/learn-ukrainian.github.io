#!/usr/bin/env python3
"""
Fix invalid activity types in meta/*.yaml files.

Mappings:
- transform → fill-in (verb form transformation)
- conjugation → fill-in (verb conjugation)
- dialogue → REMOVE (content type, not activity)
- roleplay → REMOVE (content type, not activity)
- self-assessment → REMOVE (content type, not activity)
- flashcards → match-up (memorization alternative)
"""

import sys
from pathlib import Path
import yaml

# Mapping of invalid types to valid replacements (None = remove entirely)
TYPE_MAPPINGS = {
    'transform': 'fill-in',
    'conjugation': 'fill-in',
    'dialogue': None,  # Remove - content type, not activity
    'roleplay': None,  # Remove - content type, not activity
    'role-play': None,  # Remove - content type, not activity
    'self-assessment': None,  # Remove - content type, not activity
    'flashcards': 'match-up',
    'rewrite': 'error-correction',  # Transform sentences = error correction
    'compare': 'group-sort',  # Comparison = sorting/categorizing
    'identify': 'mark-the-words',  # Identify = mark in text
    'diagram': None,  # Remove - not an activity type
    'writing': 'essay-response',  # Writing = essay
    'discussion': None,  # Remove - content type, not activity
    'edit': 'error-correction',  # Editing text = correcting/improving
    'vocabulary': 'match-up',  # Vocabulary matching = match-up
    'source-evaluation': 'critical-analysis',  # Evaluating sources = critical analysis
    # C1-HIST specialized types → map to standard types
    'practical': 'reading',  # Practical exercises = reading with application
    'vocabulary-building': 'match-up',  # Vocabulary building = match-up
    'close-reading': 'reading',  # Close reading = reading
    'creative': 'essay-response',  # Creative writing = essay response
    'research': 'reading',  # Research = reading with analysis
    'map-exercise': None,  # Remove - not a text-based activity
    'timeline': None,  # Remove - not a text-based activity
    'ideology-analysis': 'critical-analysis',  # Ideology analysis = critical analysis
    'document-analysis': 'critical-analysis',  # Document analysis = critical analysis
    'rhetoric-analysis': 'critical-analysis',  # Rhetoric analysis = critical analysis
    'legal-analysis': 'critical-analysis',  # Legal analysis = critical analysis
    'bibliography': None,  # Remove - not an activity type
    # Additional C1-HIST specialized types
    'debate': None,  # Remove - discussion format, not activity
    'synthesis': 'essay-response',  # Synthesis = essay response
    'portfolio': None,  # Remove - process, not activity
    'peer-review': None,  # Remove - process, not activity
    'counterfactual': 'essay-response',  # Counterfactual = essay response
    'consequence-analysis': 'critical-analysis',
    'methodology-critique': 'critical-analysis',
    'ethical-reflection': 'essay-response',
    'evidence-building': 'critical-analysis',
    'biography-study': 'reading',
    'biographical-study': 'reading',
    'legacy-tracing': 'critical-analysis',
    'mechanism-mapping': 'critical-analysis',
    'mapping': None,  # Remove - visual, not text
    'context-mapping': 'critical-analysis',
    'paradox-analysis': 'critical-analysis',
    'memory-study': 'critical-analysis',
    'contemporary-parallel': 'comparative-study',
    'stakeholder-analysis': 'critical-analysis',
    'perspective-comparison': 'comparative-study',
    'long-term-impact': 'critical-analysis',
    'camp-life-analysis': 'critical-analysis',
    'ideological-comparison': 'comparative-study',
    'institutional-analysis': 'critical-analysis',
    'institutional-comparison': 'comparative-study',
    'social-analysis': 'critical-analysis',
    'layered-history': 'critical-analysis',
    'tatar-history': 'reading',
    'deportation-study': 'critical-analysis',
    'cycle-mapping': 'critical-analysis',
    'pattern-application': 'critical-analysis',
    'negotiation-analysis': 'critical-analysis',
    '2014-test': 'quiz',  # Test = quiz
}

VALID_ACTIVITY_TYPES = [
    "match-up", "fill-in", "quiz", "true-false", "group-sort", "unjumble",
    "error-correction", "anagram", "select", "translate", "cloze",
    "mark-the-words", "reading", "essay-response", "critical-analysis",
    "comparative-study", "authorial-intent"
]


def fix_meta_file(meta_path: Path, dry_run: bool = True) -> tuple[int, list[str]]:
    """
    Fix invalid activity types in a meta YAML file.

    Returns (num_fixes, list of change messages)
    """
    changes = []

    with open(meta_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return 0, [f"  ❌ YAML parse error: {e}"]

    if not data or 'activity_hints' not in data:
        return 0, []

    activity_hints = data.get('activity_hints', [])
    if not activity_hints:
        return 0, []

    new_hints = []
    num_fixes = 0

    for hint in activity_hints:
        if not isinstance(hint, dict):
            new_hints.append(hint)
            continue

        activity_type = hint.get('type')

        if activity_type in TYPE_MAPPINGS:
            replacement = TYPE_MAPPINGS[activity_type]
            if replacement is None:
                # Remove this entry
                changes.append(f"  🗑️  REMOVED: {activity_type} (content type, not activity)")
                num_fixes += 1
            else:
                # Replace with valid type
                hint['type'] = replacement
                changes.append(f"  🔄 REPLACED: {activity_type} → {replacement}")
                new_hints.append(hint)
                num_fixes += 1
        elif activity_type not in VALID_ACTIVITY_TYPES:
            # Unknown invalid type - flag but keep
            changes.append(f"  ⚠️  UNKNOWN: {activity_type} (not in mappings, keeping)")
            new_hints.append(hint)
        else:
            # Valid type - keep as is
            new_hints.append(hint)

    if num_fixes == 0:
        return 0, []

    # Update the data
    data['activity_hints'] = new_hints

    if not dry_run:
        # Write back with preserved formatting (using ruamel.yaml would be better, but this works)
        with open(meta_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return num_fixes, changes


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix invalid activity types in meta/*.yaml files')
    parser.add_argument('path', nargs='?', default='curriculum/l2-uk-en', help='Path to search for meta files')
    parser.add_argument('--level', help='Filter by level (e.g., b1, b2)')
    parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry-run)')
    args = parser.parse_args()

    base_path = Path(args.path)

    # Find all meta directories
    if args.level:
        meta_dirs = [base_path / args.level / 'meta']
    else:
        meta_dirs = list(base_path.glob('*/meta'))

    total_fixes = 0
    files_changed = 0

    for meta_dir in sorted(meta_dirs):
        if not meta_dir.exists():
            continue

        level = meta_dir.parent.name

        for meta_file in sorted(meta_dir.glob('*.yaml')):
            num_fixes, changes = fix_meta_file(meta_file, dry_run=not args.apply)

            if num_fixes > 0:
                print(f"\n📄 {level}/{meta_file.name}")
                for change in changes:
                    print(change)
                total_fixes += num_fixes
                files_changed += 1

    print(f"\n{'='*50}")
    if args.apply:
        print(f"✅ APPLIED: {total_fixes} fixes in {files_changed} files")
    else:
        print(f"🔍 DRY RUN: {total_fixes} fixes would be made in {files_changed} files")
        print("   Run with --apply to apply changes")


if __name__ == '__main__':
    main()
