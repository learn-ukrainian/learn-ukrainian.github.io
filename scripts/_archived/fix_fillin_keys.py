
import yaml

def fix_fillin(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    modified = False
    for activity in data:
        if activity.get('type') == 'fill-in':
            items = activity.get('items', [])
            for item in items:
                if 'question' in item:
                    item['sentence'] = item.pop('question')
                    modified = True
    
    if modified:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print("Fixed fill-in keys.")
    else:
        print("No changes.")

fix_fillin('curriculum/l2-uk-en/c1/activities/17-irregular-verbs-complete.yaml')
