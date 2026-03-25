import yaml
import re

with open("curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml", "r") as f:
    data = yaml.safe_load(f)

for act in data:
    if act.get("type") == "match-up" and act.get("title") == "Match the Phrases":
        act["pairs"].extend([
            {"left": "кіт і собака", "right": "cat and dog"},
            {"left": "мій брат", "right": "my brother"}
        ])

with open("curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml", "w", encoding="utf-8") as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
