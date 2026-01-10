
import re

path = "curriculum/l2-uk-en/b2/activities/19-register-official-legal.yaml"
with open(path, 'r') as f:
    content = f.read()

# Replace unquoted date
# YAML: - text: 2024-01-01
content = content.replace("text: 2024-01-01", "text: '2024-01-01'")

with open(path, 'w') as f:
    f.write(content)

print("Fixed M19 date.")
