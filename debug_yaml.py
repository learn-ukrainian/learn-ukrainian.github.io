import yaml
import sys

try:
    with open('curriculum/l2-uk-en/c1/activities/139-high-formal-register.yaml', 'r') as f:
        yaml.safe_load(f)
    print("YAML is valid")
except yaml.YAMLError as exc:
    print(exc)
