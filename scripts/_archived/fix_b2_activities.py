import yaml
import re
from pathlib import Path

def extract_marked_words(passage):
    # Matches *word* or *word phrase*
    matches = re.findall(r'\*([^*]+)\*', passage)
    return matches

def fix_activity_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return False

    if not data:
        return False

    activities = data if isinstance(data, list) else data.get('activities', [])
    changed = False

    for activity in activities:
        act_type = activity.get('type')
        
        if act_type == 'unjumble':
            items = activity.get('items', [])
            for item in items:
                if 'scrambled' in item and 'words' in item:
                    del item['scrambled']
                    changed = True
        
        elif act_type == 'mark-the-words':
            if 'correct_words' not in activity and 'passage' in activity:
                words = extract_marked_words(activity['passage'])
                if words:
                    activity['correct_words'] = words
                    changed = True
                    print(f"Fixed mark-the-words in {filepath}")

    if changed:
        # If the original file was a list, save as list. If dict with 'activities', save structure.
        # But our schema expects a list of activities at root usually for module-specific files.
        # Let's preserve structure.
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # safe_dump doesn't handle unicode well by default (escapes characters)
            # using allow_unicode=True
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        return True
    
    return False

def main():
    b2_dir = Path('curriculum/l2-uk-en/b2/activities')
    count = 0
    for yaml_file in b2_dir.glob('*.yaml'):
        if fix_activity_file(yaml_file):
            count += 1
            print(f"Fixed {yaml_file.name}")
            
    print(f"Total files fixed: {count}")

if __name__ == '__main__':
    main()
