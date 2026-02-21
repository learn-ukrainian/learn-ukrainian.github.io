#!/usr/bin/env python3
"""
Comprehensive YAML Activity Standardization Script

Fixes 4 categories of issues across ~203 files:
1. Cloze format (88 files)
2. Mark-the-words field names (62 files)
3. Unjumble format (37 files)
4. Activity type names (16 files)
"""

import yaml
import re
import sys
from pathlib import Path
from collections import defaultdict

# Statistics
stats = defaultdict(int)

def fix_cloze_activity(activity):
    """Standardize cloze to inline format."""
    if activity.get('type') != 'cloze':
        return activity, False
    
    passage = activity.get('passage', '')
    blanks = activity.get('blanks', [])
    
    # Already inline format (no explicit blanks)
    if not blanks:
        return activity, False
    
    # Has both - mixed format, remove blanks
    if re.search(r'\{[^}]+\|[^}]+\}', passage):
        result = {k: v for k, v in activity.items() if k != 'blanks'}
        stats['cloze_mixed_fixed'] += 1
        return result, True
    
    # Convert explicit to inline
    blank_map = {}
    for blank in blanks:
        blank_id = blank.get('id')
        if not blank_id:
            continue
        answer = blank['answer']
        options = blank.get('options', [])
        
        # Ensure answer is first
        if answer in options:
            inline_opts = [answer] + [o for o in options if o != answer]
        else:
            inline_opts = [answer] + options
        
        blank_map[blank_id] = '{' + '|'.join(inline_opts) + '}'
    
    # Replace {1}, {2} with inline
    def replace_blank(match):
        return blank_map.get(int(match.group(1)), match.group(0))
    
    new_passage = re.sub(r'\{(\d+)\}', replace_blank, passage)
    
    result = {k: v for k, v in activity.items() if k != 'blanks'}
    result['passage'] = new_passage
    stats['cloze_explicit_to_inline'] += 1
    return result, True

def fix_mark_the_words(activity):
    """Rename text→passage, answers→correct_words."""
    if activity.get('type') != 'mark-the-words':
        return activity, False
    
    changed = False
    result = dict(activity)
    
    if 'text' in result:
        result['passage'] = result.pop('text')
        stats['mark_text_to_passage'] += 1
        changed = True
    
    if 'answers' in result:
        result['correct_words'] = result.pop('answers')
        stats['mark_answers_to_correct_words'] += 1
        changed = True
    
    return result, changed

def fix_unjumble(activity):
    """Rename jumbled→words, convert string to array."""
    if activity.get('type') != 'unjumble':
        return activity, False
    
    items = activity.get('items', [])
    changed = False
    
    for i, item in enumerate(items):
        # Rename jumbled→words
        if 'jumbled' in item:
            item['words'] = item.pop('jumbled')
            stats['unjumble_jumbled_to_words'] += 1
            changed = True
        
        # Convert string to array
        if 'words' in item and isinstance(item['words'], str):
            # Split by / and clean
            words_str = item['words']
            words_array = [w.strip() for w in words_str.split('/')]
            item['words'] = words_array
            stats['unjumble_string_to_array'] += 1
            changed = True
    
    return activity, changed

def fix_activity_type(activity):
    """Standardize activity type names."""
    old_type = activity.get('type')
    
    type_map = {
        'essay': 'essay-response',
        'analysis': 'critical-analysis',
        'comparison': 'comparative-study',
        'short-response': 'essay-response',
        'discussion': 'essay-response',
        'writing': 'essay-response',
        'debate': 'essay-response',
    }
    
    new_type = type_map.get(old_type)
    if new_type:
        activity['type'] = new_type
        stats[f'type_{old_type}_to_{new_type}'] += 1
        return activity, True
    
    return activity, False

def fix_file(filepath):
    """Fix all issues in a YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return False
    
    # Handle both list and dict formats
    if isinstance(data, list):
        activities = data
        is_list_format = True
    elif isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
        is_list_format = False
    else:
        return False
    
    file_changed = False
    
    for i, activity in enumerate(activities):
        activity_changed = False
        
        # Apply all fixes
        activity, changed = fix_cloze_activity(activity)
        activity_changed = activity_changed or changed
        
        activity, changed = fix_mark_the_words(activity)
        activity_changed = activity_changed or changed
        
        activity, changed = fix_unjumble(activity)
        activity_changed = activity_changed or changed
        
        activity, changed = fix_activity_type(activity)
        activity_changed = activity_changed or changed
        
        if activity_changed:
            activities[i] = activity
            file_changed = True
    
    if file_changed:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if is_list_format:
                    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, 
                             default_flow_style=False, width=float('inf'))
                else:
                    yaml.dump(data, f, allow_unicode=True, sort_keys=False, 
                             default_flow_style=False, width=float('inf'))
            stats['files_fixed'] += 1
            return True
        except Exception as e:
            print(f"❌ Error writing {filepath}: {e}")
            return False
    
    return False

def main():
    print("🔧 YAML Activity Standardization")
    print("=" * 60)
    
    base_path = Path('curriculum/l2-uk-en')
    yaml_files = list(base_path.glob('*/activities/*.yaml'))
    
    print(f"Found {len(yaml_files)} YAML files")
    print()
    
    for yaml_file in yaml_files:
        if fix_file(yaml_file):
            print(f"✅ {yaml_file.relative_to(base_path)}")
    
    print()
    print("=" * 60)
    print("📊 STATISTICS")
    print("=" * 60)
    print(f"Files fixed: {stats['files_fixed']}")
    print()
    print("Cloze fixes:")
    print(f"  Explicit→Inline: {stats['cloze_explicit_to_inline']}")
    print(f"  Mixed format: {stats['cloze_mixed_fixed']}")
    print()
    print("Mark-the-words fixes:")
    print(f"  text→passage: {stats['mark_text_to_passage']}")
    print(f"  answers→correct_words: {stats['mark_answers_to_correct_words']}")
    print()
    print("Unjumble fixes:")
    print(f"  jumbled→words: {stats['unjumble_jumbled_to_words']}")
    print(f"  string→array: {stats['unjumble_string_to_array']}")
    print()
    print("Type name fixes:")
    for key, value in stats.items():
        if key.startswith('type_'):
            print(f"  {key}: {value}")
    print()
    print("✅ Standardization complete!")

if __name__ == '__main__':
    main()
