import re
from pathlib import Path

file_path = Path("curriculum/l2-uk-en/b2/activities/word-formation-place-object-names.yaml")
lines = file_path.read_text().splitlines()
new_lines = []

for line in lines:
    m = re.match(r"^(\s*(?:-\s+|[a-zA-Z_]+:\s+))\'(.*?)\'$", line)
    if m:
        prefix = m.group(1)
        content = m.group(2)
        if "'" in content:
            content = content.replace('"', '\\"')
            line = prefix + '"' + content + '"'
    new_lines.append(line)

file_path.write_text('\n'.join(new_lines) + '\n')
