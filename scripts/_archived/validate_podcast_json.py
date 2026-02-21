#!/usr/bin/env python3
import json
import sys
import os

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("❌ Error: 'jsonschema' library not found. Please install it using: pip install jsonschema")
    sys.exit(1)

# Define paths relative to project root
SCHEMA_PATH = 'docs/resources/podcasts/podcast_schema.json'
DATA_PATH = 'docs/resources/podcasts/podcast_prototype.json'

def load_schema():
    if not os.path.exists(SCHEMA_PATH):
        print(f"❌ Error: Schema file not found at {SCHEMA_PATH}")
        sys.exit(1)
    with open(SCHEMA_PATH) as f:
        return json.load(f)

def load_podcast_data():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Data file not found at {DATA_PATH}")
        sys.exit(1)
    with open(DATA_PATH) as f:
        return json.load(f)

def check_duplicate_ids(data):
    ids = [episode['id'] for episode in data]
    duplicates = [id for id in ids if ids.count(id) > 1]
    if duplicates:
        print(f"❌ Duplicate IDs found: {set(duplicates)}")
        return False
    return True

def main():
    print(f"🔍 Validating {DATA_PATH} against {SCHEMA_PATH}...")
    schema = load_schema()
    data = load_podcast_data()

    try:
        validate(instance=data, schema=schema)
        print("✅ JSON structure is valid")
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        print(f"  Path: {list(e.path)}")
        sys.exit(1)

    if not check_duplicate_ids(data):
        sys.exit(1)

    print(f"✅ All {len(data)} episodes validated successfully")

if __name__ == '__main__':
    main()
