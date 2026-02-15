import yaml
import os

placeholders_path = "curriculum/l2-uk-en/b2/orchestration/passive-voice-system/placeholders.yaml"

with open(placeholders_path, 'r') as f:
    data = yaml.safe_load(f)

# Update stats
data['AUDIT_STATUS'] = "✅ AUDIT PASSED"
data['AUDIT_WORD_COUNT'] = "6245"
data['ACTIVITY_COUNT'] = "10"
data['ENGAGEMENT_COUNT'] = "13"
data['IMMERSION_PERCENT'] = "99.2%"
data['IMMERSION_TARGET'] = "90-100%"
data['VOCAB_COUNT'] = "31"
data['WORD_PERCENT'] = "156%"
data['PREV_MODULE'] = "B1 Completion"

with open(placeholders_path, 'w') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
