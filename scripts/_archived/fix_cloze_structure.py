
import yaml
import re

def fix_cloze(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    modified = False
    for activity in data:
        if activity['type'] == 'cloze':
            if 'items' in activity and 'passage' not in activity:
                # Fix structure
                items = activity.get('items', [])
                if items and 'passage' in items[0]:
                    passage = items[0]['passage']
                    activity['passage'] = passage
                    del activity['items']
                    
                    # Generate blanks
                    blanks = []
                    # Regex to find {a|b|c}
                    matches = list(re.finditer(r'\{([^}]+)\}', passage))
                    for i, match in enumerate(matches):
                        content = match.group(1)
                        parts = content.split('|')
                        answer = parts[0]
                        options = parts # All parts are options
                        
                        blanks.append({
                            'id': i,
                            'answer': answer,
                            'options': options
                        })
                    
                    activity['blanks'] = blanks
                    modified = True
                    print(f"Fixed cloze structure. Generated {len(blanks)} blanks.")
            
    if modified:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print("Saved changes.")
    else:
        print("No cloze fixes needed.")

fix_cloze('curriculum/l2-uk-en/c1/activities/17-irregular-verbs-complete.yaml')
