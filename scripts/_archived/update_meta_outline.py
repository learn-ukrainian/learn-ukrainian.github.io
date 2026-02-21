import yaml
import sys

meta_path = "curriculum/l2-uk-en/a1/meta/around-the-city.yaml"
outline_path = "curriculum/l2-uk-en/a1/orchestration/around-the-city/phase-1-meta_outline.md"

try:
    with open(meta_path, 'r') as f:
        meta = yaml.safe_load(f)

    with open(outline_path, 'r') as f:
        outline_data = yaml.safe_load(f)

    new_outline = {}
    if 'content_outline' in outline_data and isinstance(outline_data['content_outline'], list):
        for item in outline_data['content_outline']:
            new_outline[item['section']] = item['words']
    else:
        print("Error: content_outline not found or not a list in outline file")
        sys.exit(1)

    meta['content_outline'] = new_outline

    with open(meta_path, 'w') as f:
        yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

    print("Successfully updated meta.yaml content_outline")
    print(new_outline)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
