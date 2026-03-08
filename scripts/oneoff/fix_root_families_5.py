import re

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix transliteration issue (agent)
text = text.replace(" (agent)", "")

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'w', encoding='utf-8') as f:
    f.write(text)
