import re

with open('curriculum/l2-uk-en/a1/yesterday-past-tense.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the combining acute accent (U+0301)
text = text.replace('\u0301', '')

with open('curriculum/l2-uk-en/a1/yesterday-past-tense.md', 'w', encoding='utf-8') as f:
    f.write(text)
