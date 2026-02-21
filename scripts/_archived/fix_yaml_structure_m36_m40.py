
import yaml
import os

files = [
    'curriculum/l2-uk-en/c1/activities/36-knyahynia-olha.yaml',
    'curriculum/l2-uk-en/c1/activities/37-kniaz-sviatoslav.yaml',
    'curriculum/l2-uk-en/c1/activities/38-volodymyr-velykii.yaml',
    'curriculum/l2-uk-en/c1/activities/39-kniaz-yaroslav-mudryi.yaml',
    'curriculum/l2-uk-en/c1/activities/40-knyazhna-anna-yaroslavna.yaml'
]

def clean_activity(activity):
    # Remove 'id' if present
    if 'id' in activity:
        del activity['id']
    return activity

for file_path in files:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found)")
        continue
        
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Check if nested
    activities = []
    if isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
    elif isinstance(data, list):
        activities = data
    else:
        print(f"Warning: Unknown structure in {file_path}")
        continue
        
    # Clean activities
    cleaned_activities = [clean_activity(a) for a in activities]
    
    # Save as flat list
    with open(file_path, 'w') as f:
        yaml.dump(cleaned_activities, f, allow_unicode=True, sort_keys=False)
    
    print(f"Fixed {file_path}")
