
import yaml
import sys
from pathlib import Path

def clean_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # If root is dict with 'activities', extract it
    if isinstance(data, dict) and 'activities' in data:
        data = data['activities']
        
    # Remove 'id' from all activities
    if isinstance(data, list):
        for activity in data:
            if 'id' in activity:
                del activity['id']
                
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=1000)
    print(f"Cleaned {file_path}")

clean_yaml('curriculum/l2-uk-en/c1/activities/42-roksolana.yaml')
