import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('You ask for medicine for a cough. You ask for medicine for pain. You ask for medicine for a fever.', 'You ask for medicine for a cough. Then you request medicine for pain. Or you get medicine for a fever.')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied fix_module4")
