import sys
from pathlib import Path
from scripts.audit.checks.content_gaming import extract_words_from_activities, extract_ukrainian_words

md_path = Path("curriculum/l2-uk-en/a1/checkpoint-sentences.md")
content = md_path.read_text(encoding="utf-8")
content_words = extract_ukrainian_words(content)
activity_words = extract_words_from_activities(md_path)
all_used = content_words | activity_words

print("куди in all_used:", "куди" in all_used)
print("хто in all_used:", "хто" in all_used)
print("де in all_used:", "де" in all_used)
