#!/usr/bin/env python3
"""
Convert cloze activities from explicit blanks format to inline format.

Explicit format (schema-compliant):
    passage: "Text with {1} and {2} markers"
    blanks:
      - id: 1
        answer: "correct"
        options: ["correct", "wrong1", "wrong2"]

Inline format (de facto standard):
    passage: "Text with {correct|wrong1|wrong2} markers"
"""

import yaml
import re
import sys
from pathlib import Path

def convert_cloze_to_inline(activity):
    """Convert a cloze activity from explicit to inline format."""
    if activity.get('type') != 'cloze':
        return activity
    
    passage = activity.get('passage', '')
    blanks = activity.get('blanks', [])
    
    # If no explicit blanks, already inline format
    if not blanks:
        return activity
    
    # Create mapping of blank IDs to inline format
    blank_map = {}
    for blank in blanks:
        blank_id = blank['id']
        answer = blank['answer']
        options = blank.get('options', [])
        
        # Ensure answer is first in options list
        if answer not in options:
            inline_options = [answer] + options
        else:
            # Move answer to first position
            inline_options = [answer] + [opt for opt in options if opt != answer]
        
        # Create inline format
        blank_map[blank_id] = '{' + '|'.join(inline_options) + '}'
    
    # Replace {1}, {2}, etc. with inline format
    def replace_blank(match):
        blank_id = int(match.group(1))
        return blank_map.get(blank_id, match.group(0))
    
    new_passage = re.sub(r'\{(\d+)\}', replace_blank, passage)
    
    # Return activity with inline format
    result = {k: v for k, v in activity.items() if k != 'blanks'}
    result['passage'] = new_passage
    
    return result

def convert_file(filepath):
    """Convert all cloze activities in a YAML file to inline format."""
    print(f"Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data or 'activities' not in data:
        print(f"  ⚠️  No activities found")
        return False
    
    converted = False
    for i, activity in enumerate(data['activities']):
        if activity.get('type') == 'cloze' and 'blanks' in activity:
            print(f"  Converting cloze activity: {activity.get('title', f'#{i}')}")
            data['activities'][i] = convert_cloze_to_inline(activity)
            converted = True
    
    if converted:
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"  ✅ Converted")
        return True
    else:
        print(f"  ℹ️  No explicit-format cloze activities")
        return False

def main():
    # Find all YAML files with explicit blanks format
    base_path = Path('curriculum/l2-uk-en')
    
    converted_count = 0
    for yaml_file in base_path.glob('*/activities/*.yaml'):
        # Check if file has cloze with explicit blanks
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'type: cloze' in content and re.search(r'^\s+blanks:', content, re.MULTILINE):
                if convert_file(yaml_file):
                    converted_count += 1
    
    print(f"\n✅ Converted {converted_count} files")

if __name__ == '__main__':
    main()
