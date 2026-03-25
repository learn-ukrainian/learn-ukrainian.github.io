import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Find all occurrences of bolded Ukrainian followed by parenthetical English
# We only want to remove it if it looks like a translation (contains English letters)
# And we probably want to remove translations in quotes too: "**Цей сті́л** (This table)"

def replace_translation(match):
    ukr_text = match.group(1)
    translation = match.group(2)
    # If the parenthesis contains mostly English or looks like translation, remove it
    if re.search(r'[a-zA-Z]', translation):
        return ukr_text
    return match.group(0)

text = re.sub(r'(\*\*[А-Яа-яієїґ\'́\s.,?!A-Za-z-]+\*\*)(?:\s*)\((.*?)\)', replace_translation, text)

# Also handle cases like: "**«В гостя́х до́бре, а вдо́ма кра́ще»** (Being a guest is good...)"
text = re.sub(r'(\*\*«[А-Яа-яієїґ\'́\s.,?!]+»\*\*)(?:\s*)\((.*?)\)', replace_translation, text)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md', 'w', encoding='utf-8') as f:
    f.write(text)

