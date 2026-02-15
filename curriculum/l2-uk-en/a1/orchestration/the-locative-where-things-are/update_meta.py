import yaml
import sys

meta_path = "curriculum/l2-uk-en/a1/meta/the-locative-where-things-are.yaml"
outline_path = "curriculum/l2-uk-en/a1/orchestration/the-locative-where-things-are/phase-1-meta_outline.md"

try:
    with open(outline_path, 'r') as f:
        # Load all documents if there are multiple, or just the first one
        # The file might contain YAML frontmatter or just YAML.
        # safe_load handles standard YAML.
        outline_data = yaml.safe_load(f)
except Exception as e:
    print(f"Error reading outline: {e}")
    sys.exit(1)

new_outline = {}
# Check if content_outline exists and is a list
if outline_data and 'content_outline' in outline_data and isinstance(outline_data['content_outline'], list):
    for item in outline_data['content_outline']:
        if 'section' in item and 'words' in item:
            new_outline[item['section']] = item['words']
        else:
             print(f"Skipping invalid item: {item}")
elif outline_data and isinstance(outline_data, list):
    # Maybe the file is just the list itself?
    for item in outline_data:
         if 'section' in item and 'words' in item:
            new_outline[item['section']] = item['words']
else:
    print(f"Error: Invalid outline format. Data: {outline_data}")
    sys.exit(1)

try:
    with open(meta_path, 'r') as f:
        meta_data = yaml.safe_load(f)
except Exception as e:
    print(f"Error reading meta: {e}")
    sys.exit(1)

meta_data['content_outline'] = new_outline

try:
    with open(meta_path, 'w') as f:
        yaml.dump(meta_data, f, allow_unicode=True, sort_keys=False)
    print("Updated meta.yaml")
except Exception as e:
    print(f"Error writing meta: {e}")
    sys.exit(1)
