import os

filepath = 'curriculum/l2-uk-en/bio/yevhen-chykalenko.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    "а не лише селянських оповідань": "а не тільки селянських оповідань"
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Remaining 'не просто': {content.count('не просто')}")
print(f"Remaining 'не лише': {content.count('не лише')}")
