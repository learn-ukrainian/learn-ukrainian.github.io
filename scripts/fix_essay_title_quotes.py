
import yaml

def fix_essay_title(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    modified = False
    for activity in data:
        if activity.get('title') == 'Есе "Динаміка змін"':
            activity['title'] = 'Есе «Динаміка змін»'
            modified = True
            print("Fixed essay title quotes.")
            
    if modified:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print("YAML updated.")
    else:
        print("Title not found or already fixed.")

fix_essay_title('curriculum/l2-uk-en/c1/activities/17-irregular-verbs-complete.yaml')
