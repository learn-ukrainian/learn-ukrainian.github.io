#!/usr/bin/env python3
"""Fix invalid activity types in plan YAML files.

Maps hallucinated activity types to valid schema types.
"""

import re
import sys
from pathlib import Path

VALID_TYPES = {
    'match-up', 'fill-in', 'quiz', 'true-false', 'group-sort',
    'unjumble', 'error-correction', 'anagram', 'select', 'translate',
    'cloze', 'mark-the-words', 'reading', 'essay-response',
    'critical-analysis', 'comparative-study', 'authorial-intent'
}

# Explicit mappings for common invalid types
EXPLICIT_MAPPING = {
    # Direct renames
    'matching': 'match-up',
    'translation': 'translate',
    'multiple-choice': 'quiz',
    
    # Reading variants
    'reading-comprehension': 'reading',
    'reading-test': 'reading',
    
    # Quiz variants
    'quiz-test': 'quiz',
    'diagnostic': 'quiz',
    'recognition': 'quiz',
    'prediction': 'quiz',
    'prophecy-test': 'quiz',
    'skill-assessment': 'quiz',
    
    # Cloze variants
    'cloze-test': 'cloze',
    'cloze-analysis': 'cloze',
    'role-play': 'cloze',
    'dialogue': 'cloze',
    'production': 'cloze',
    'formation': 'cloze',
    'calculation': 'cloze',
    'context-matching': 'cloze',
    'note-taking': 'cloze',
    'integration': 'cloze',
    'task': 'cloze',
    
    # Unjumble/sentence variants  
    'sentence-combining': 'unjumble',
    'sentence-building': 'unjumble',
    'unjumble-construction': 'unjumble',
    
    # Error correction variants
    'text-editing': 'error-correction',
    
    # Fill-in variants
    'word-building': 'fill-in',
    'agreement': 'fill-in',
    
    # Match-up variants
    'vocabulary-drill': 'match-up',
    'collocation': 'match-up',
    
    # Group-sort variants
    'organization': 'group-sort',
    
    # Not supported (audio/speaking)
    'speaking': 'quiz',
    'discussion': 'quiz',
    'listening': 'quiz',
    'oral-presentation': 'quiz',
    
    # Other
    'self-assessment': 'quiz',
    'transformation': 'cloze',
    'writing': 'cloze',
    'sequencing': 'unjumble',
    'timeline': 'unjumble',
}

# Pattern-based mappings for C1-HIST analytical types
PATTERN_MAPPING = {
    r'.*-analysis$': 'critical-analysis',
    r'.*-study$': 'comparative-study',
    r'.*-comparison$': 'comparative-study',
    r'.*-mapping$': 'critical-analysis',
    r'.*-assessment$': 'critical-analysis',
    r'.*-evaluation$': 'critical-analysis',
    r'.*-reflection$': 'essay-response',
    r'.*-connection$': 'critical-analysis',
    r'.*-recognition$': 'critical-analysis',
    r'.*-tracking$': 'critical-analysis',
    r'.*-reconstruction$': 'critical-analysis',
    r'.*-documentation$': 'critical-analysis',
    r'.*-deconstruction$': 'critical-analysis',
    r'.*-mechanics$': 'critical-analysis',
    r'.*-scenarios$': 'essay-response',
    r'.*-questions$': 'essay-response',
    r'.*-debate$': 'essay-response',
    r'.*-politics$': 'critical-analysis',
    r'.*-table$': 'match-up',
    r'.*-source$': 'reading',
    r'.*-stories$': 'reading',
    r'.*-learned$': 'essay-response',
}


def get_replacement(invalid_type: str) -> str | None:
    """Get the valid type to replace an invalid type."""
    if invalid_type in VALID_TYPES:
        return None  # Already valid
    
    # Check explicit mapping first
    if invalid_type in EXPLICIT_MAPPING:
        return EXPLICIT_MAPPING[invalid_type]
    
    # Check pattern mapping
    for pattern, replacement in PATTERN_MAPPING.items():
        if re.match(pattern, invalid_type):
            return replacement
    
    # Default fallback for unknown types
    return 'critical-analysis'


def fix_file(filepath: Path, dry_run: bool = True) -> list[str]:
    """Fix invalid activity types in a single file."""
    changes = []
    content = filepath.read_text()
    new_content = content

    # Find all "- type: X" patterns
    for match in re.finditer(r'- type: ([a-z0-9-]+)', content):
        old_type = match.group(1)
        new_type = get_replacement(old_type)
        
        if new_type:
            old_pattern = f'- type: {old_type}'
            new_pattern = f'- type: {new_type}'
            
            if old_pattern in new_content:
                count = new_content.count(old_pattern)
                new_content = new_content.replace(old_pattern, new_pattern)
                changes.append(f"  {old_type} → {new_type} ({count}x)")

    # Deduplicate changes (same replacement might be found multiple times)
    changes = list(dict.fromkeys(changes))
    
    if changes and not dry_run:
        filepath.write_text(new_content)

    return changes


def main():
    dry_run = '--fix' not in sys.argv
    plans_dir = Path('curriculum/l2-uk-en/plans')

    if not plans_dir.exists():
        print(f"Error: {plans_dir} not found")
        sys.exit(1)

    print(f"{'DRY RUN - ' if dry_run else ''}Scanning {plans_dir}...")
    if dry_run:
        print("Add --fix to apply changes\n")
    else:
        print()

    total_files = 0
    total_changes = 0

    for yaml_file in sorted(plans_dir.rglob('*.yaml')):
        changes = fix_file(yaml_file, dry_run)
        if changes:
            total_files += 1
            total_changes += len(changes)
            print(f"{yaml_file.relative_to(plans_dir)}:")
            for change in changes:
                print(change)
            print()

    print(f"\n{'Would fix' if dry_run else 'Fixed'}: {total_changes} type(s) in {total_files} file(s)")

    if dry_run and total_files > 0:
        print("\nRun with --fix to apply changes")


if __name__ == '__main__':
    main()
