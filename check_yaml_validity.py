
import yaml
import sys
import os

files = [
    "curriculum/l2-uk-en/b2/meta/01-passive-voice-system.yaml",
    "curriculum/l2-uk-en/b2/activities/01-passive-voice-system.yaml",
    "curriculum/l2-uk-en/b2/vocabulary/01-passive-voice-system.yaml",
    "curriculum/l2-uk-en/b2/meta/02-past-passive-participles.yaml",
    "curriculum/l2-uk-en/b2/activities/02-past-passive-participles.yaml",
    "curriculum/l2-uk-en/b2/vocabulary/02-past-passive-participles.yaml",
    "curriculum/l2-uk-en/b2/meta/03-impersonal-passive.yaml",
    "curriculum/l2-uk-en/b2/activities/03-impersonal-passive.yaml",
    "curriculum/l2-uk-en/b2/vocabulary/03-impersonal-passive.yaml",
]

for f in files:
    if not os.path.exists(f):
        print(f"MISSING: {f}")
        continue
    try:
        with open(f, 'r') as stream:
            yaml.safe_load(stream)
            # print(f"VALID: {f}")
    except yaml.YAMLError as exc:
        print(f"INVALID: {f} - {exc}")
