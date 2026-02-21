
import sys
import os

path = 'curriculum/l2-uk-en/c1/activities/46-yuriy-nemyrych.yaml'
if not os.path.exists(path):
    print(f"File not found: {path}")
    sys.exit(1)

with open(path, 'r') as f:
    lines = f.readlines()

with open(path, 'w') as f:
    for line in lines:
        # Strict check to only remove property 'id' at indentation level 2 (items) or 0/1?
        # The file shows '  id: c1-46-quiz-1'.
        if line.strip().startswith('id: '):
            continue
        f.write(line)
print("Stripped IDs")
