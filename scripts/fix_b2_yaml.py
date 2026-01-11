import yaml
import sys
import os

def fix_activity(activity):
    a_type = activity.get('type')
    
    # Remove top-level 'id' if present
    if 'id' in activity:
        del activity['id']

    # Fix fill-in: remove blank_index from items
    if a_type == 'fill-in':
        if 'items' in activity:
            for item in activity['items']:
                if 'blank_index' in item:
                    del item['blank_index']

    # Fix true-false: remove context
    if a_type == 'true-false':
        if 'context' in activity:
            del activity['context'] # We handled content move in previous manual edit, so just delete

    # Fix quiz and translate: move explanation from options to item
    if a_type in ['quiz', 'translate', 'select']:
        if 'items' in activity:
            for item in activity['items']:
                if 'options' in item and isinstance(item['options'], list):
                    found_expl = None
                    for opt in item['options']:
                        if isinstance(opt, dict) and 'explanation' in opt:
                            found_expl = opt.pop('explanation')
                    
                    if found_expl and 'explanation' not in item:
                        item['explanation'] = found_expl

    return activity

def main():
    target_file = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/activities/99-austrian-galicia.yaml'
    
    with open(target_file, 'r') as f:
        data = yaml.safe_load(f)

    if 'activities' in data:
        new_activities = []
        for act in data['activities']:
            new_activities.append(fix_activity(act))
        data['activities'] = new_activities

    with open(target_file, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"Fixed {target_file}")

if __name__ == "__main__":
    main()
