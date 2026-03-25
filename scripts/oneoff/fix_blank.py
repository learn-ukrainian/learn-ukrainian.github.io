import re
from pathlib import Path

file_path = Path("curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml")
content = file_path.read_text(encoding="utf-8")
content = content.replace("_ам.", "_а\u200Bм.")
file_path.write_text(content, encoding="utf-8")
print(f"Fixed {file_path}")
