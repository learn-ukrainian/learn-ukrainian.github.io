import sys
from pathlib import Path
from scripts.audit.checks.content_gaming import extract_words_from_activities

md_path = Path("curriculum/l2-uk-en/a1/checkpoint-sentences.md")
activity_words = extract_words_from_activities(md_path)
print("куди in activity_words:", "куди" in activity_words)
