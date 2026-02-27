import re

file_path = "curriculum/l2-uk-en/b2/synonyms-abstract.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove all Latin transliteration in parentheses
content = re.sub(r' \([a-zA-Z\s/-]+\)', '', content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
