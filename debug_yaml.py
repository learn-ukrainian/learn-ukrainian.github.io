import yaml
import sys
from pathlib import Path

path = Path("curriculum/l2-uk-en/c1/activities/03-research-verbs.yaml")

try:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    print(f"Successfully loaded {path}")
    print(f"Items count: {len(data.get('items', []))}")
    for item in data.get('items', []):
        print(f" - Found item: {item.get('id')}")

except Exception as e:
    print(f"FAILED to load: {e}")
    sys.exit(1)
