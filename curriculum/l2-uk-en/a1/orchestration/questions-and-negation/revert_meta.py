import yaml
import sys

meta_path = "curriculum/l2-uk-en/a1/meta/questions-and-negation.yaml"
with open(meta_path, "r") as f:
    meta_data = yaml.safe_load(f)

# Revert content_outline to list
if 'content_outline_detailed' in meta_data:
    meta_data['content_outline'] = meta_data['content_outline_detailed']
    # Optionally keep detailed key or remove
    # del meta_data['content_outline_detailed']
    # Keeping it doesn't hurt usually, unless schema forbids extra keys.
    # But let's keep it consistent with Plan format.

with open(meta_path, "w") as f:
    yaml.dump(meta_data, f, allow_unicode=True, default_flow_style=False)

print("Meta file reverted to list format.")
