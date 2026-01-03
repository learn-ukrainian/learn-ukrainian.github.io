#!/usr/bin/env python3
"""Fix malformed mark-the-words activities in A1/A2/B1.

The md_to_yaml conversion script incorrectly copied markdown annotations
(correct)/(wrong) into YAML. This script strips them.

Usage:
    .venv/bin/python scripts/fix_mark_the_words.py
    .venv/bin/python scripts/fix_mark_the_words.py --dry-run
"""

import re
import sys
from pathlib import Path

import yaml


def fix_activity_file(yaml_path: Path, dry_run: bool = False) -> tuple[bool, int]:
    """Fix mark-the-words activities in a YAML file.
    
    Args:
        yaml_path: Path to the YAML file
        dry_run: If True, only report what would be fixed
        
    Returns:
        Tuple of (was_fixed, count_of_fixes)
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse YAML
    try:
        activities = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"  ⚠️  YAML error in {yaml_path}: {e}")
        return False, 0
    
    if not activities or not isinstance(activities, list):
        return False, 0
    
    fix_count = 0
    
    for activity in activities:
        if not isinstance(activity, dict):
            continue
            
        if activity.get('type') != 'mark-the-words':
            continue
            
        text = activity.get('text', '')
        if not text:
            continue
            
        # Check for malformed patterns
        if '(correct)' not in text and '(wrong)' not in text:
            continue
        
        # Fix: remove (correct) and (wrong) annotations
        # Pattern: *word*(correct) -> *word*
        # Pattern: *word*(wrong) -> *word*  (but wrong words shouldn't be marked)
        fixed_text = re.sub(r'\*([^*]+)\*\(correct\)', r'*\1*', text)
        fixed_text = re.sub(r'\*([^*]+)\*\(wrong\)', r'\1', fixed_text)  # Remove asterisks for wrong
        
        if fixed_text != text:
            fix_count += 1
            if not dry_run:
                activity['text'] = fixed_text
    
    if fix_count > 0 and not dry_run:
        # Write back with proper formatting
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(activities, f, allow_unicode=True, sort_keys=False, 
                     default_flow_style=False, width=1000)
    
    return fix_count > 0, fix_count


def main():
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
    else:
        print("🔧 Fixing mark-the-words activities...\n")
    
    total_files_fixed = 0
    total_activities_fixed = 0
    
    for level in ['a1', 'a2', 'b1']:
        activity_dir = Path(f'curriculum/l2-uk-en/{level}/activities')
        if not activity_dir.exists():
            print(f"  ⚠️  Directory not found: {activity_dir}")
            continue
        
        level_fixes = 0
        for yaml_file in sorted(activity_dir.glob('*.yaml')):
            was_fixed, count = fix_activity_file(yaml_file, dry_run)
            if was_fixed:
                total_files_fixed += 1
                level_fixes += count
                total_activities_fixed += count
                print(f"  {'Would fix' if dry_run else 'Fixed'} {yaml_file.name}: {count} activities")
        
        if level_fixes > 0:
            print(f"  {level.upper()}: {level_fixes} activities\n")
    
    print(f"\n{'Would fix' if dry_run else 'Fixed'}: {total_activities_fixed} activities in {total_files_fixed} files")
    
    if dry_run and total_activities_fixed > 0:
        print("\nRun without --dry-run to apply fixes.")


if __name__ == '__main__':
    main()
