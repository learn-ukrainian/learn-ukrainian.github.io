import yaml
import os

placeholders_path = "curriculum/l2-uk-en/b2/orchestration/passive-voice-system/placeholders.yaml"
tier_guidance_path = "claude_extensions/commands/review-tiers/tier-2-core.md"

with open(tier_guidance_path, 'r') as f:
    tier_content = f.read()

with open(placeholders_path, 'r') as f:
    data = yaml.safe_load(f)

data['TIER_GUIDANCE'] = tier_content

with open(placeholders_path, 'w') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
