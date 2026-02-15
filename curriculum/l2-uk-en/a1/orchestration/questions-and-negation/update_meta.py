import yaml
import sys

# Load the extracted outline
with open("curriculum/l2-uk-en/a1/orchestration/questions-and-negation/phase-1-meta_outline.md", "r") as f:
    outline_data = yaml.safe_load(f)

# Load the existing meta file
meta_path = "curriculum/l2-uk-en/a1/meta/questions-and-negation.yaml"
with open(meta_path, "r") as f:
    meta_data = yaml.safe_load(f)

# Extract content_outline from extracted data
# It might be under 'content_outline' key or just the list
extracted_list = outline_data.get('content_outline', outline_data)

# Create the map for Foreman script
content_map = {}
for item in extracted_list:
    title = item['section']
    words = item['words']
    content_map[title] = words

# Update meta data
meta_data['content_outline'] = content_map
meta_data['content_outline_detailed'] = extracted_list

# Write back to meta file
with open(meta_path, "w") as f:
    yaml.dump(meta_data, f, allow_unicode=True, default_flow_style=False)

print("Meta file updated successfully.")
