import yaml
import sys

meta_path = "curriculum/l2-uk-en/b2/meta/passive-voice-system.yaml"
new_outline_path = "curriculum/l2-uk-en/b2/orchestration/passive-voice-system/phase-1-meta_outline.md"

# Load original meta
with open(meta_path, 'r') as f:
    meta = yaml.safe_load(f)

# Load new outline
with open(new_outline_path, 'r') as f:
    outline_data = yaml.safe_load(f)

# Check if outline_data has 'content_outline' key
if 'content_outline' in outline_data:
    meta['content_outline'] = outline_data['content_outline']
else:
    # Maybe the file IS the list?
    if isinstance(outline_data, list):
        meta['content_outline'] = outline_data
    else:
        print("Error: Could not find content_outline in new data")
        sys.exit(1)

# Write back
with open(meta_path, 'w') as f:
    yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

print(f"Updated {meta_path}")
