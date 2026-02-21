
import yaml
import os

file_path = 'curriculum/l2-uk-en/c1/activities/37-kniaz-sviatoslav.yaml'

with open(file_path, 'r') as f:
    data = yaml.safe_load(f)

if isinstance(data, list):
    # Filter out select activity with title 'Наслідки правління'
    new_data = [a for a in data if not (a.get('type') == 'select' and a.get('title') == 'Наслідки правління')]
    
    if len(new_data) < len(data):
        with open(file_path, 'w') as f:
            yaml.dump(new_data, f, allow_unicode=True, sort_keys=False)
        print(f"Removed problematic select activity from {file_path}")
    else:
        print("Select activity not found")
