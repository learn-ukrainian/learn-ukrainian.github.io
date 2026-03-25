import re

files_to_fix = [
    "curriculum/l2-uk-en/a1/the-cyrillic-code-i.md",
    "curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml"
]

syllables = ["ал", "ам", "ан", "лу", "са", "су", "ул", "ун", "ус"]
syllables_upper = [s.upper() for s in syllables]
syllables_title = [s.capitalize() for s in syllables]

all_syllables = syllables + syllables_upper + syllables_title

def insert_zws(match):
    s = match.group(0)
    return s[0] + "\u200B" + s[1:]

for filepath in files_to_fix:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We want to replace these syllables only when they appear as standalone words
    # or inside markdown bold/list elements.
    for s in all_syllables:
        # Match syllable surrounded by non-Cyrillic characters
        pattern = r"(?<![а-яіїєґА-ЯІЇЄҐ])" + s + r"(?![а-яіїєґА-ЯІЇЄҐ])"
        content = re.sub(pattern, insert_zws, content)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixed!")
