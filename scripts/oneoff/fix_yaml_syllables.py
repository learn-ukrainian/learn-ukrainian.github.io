filepath = "curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml"
with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

zwsp = "\u200B"
targets = ["МА", "СУ", "ЛУ", "МУ", "НА", "СА"]

# We want to replace these targets when they appear as isolated uppercase strings
# like "МА + МА", "СУ + МА", etc.
for t in targets:
    # We replace "t + " with "t[0]zwspt[1] + "
    text = text.replace(f'{t} + ', f'{t[0]}{zwsp}{t[1]} + ')
    # And " + t" with " + t[0]zwspt[1]"
    text = text.replace(f' + {t}', f' + {t[0]}{zwsp}{t[1]}')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed yaml syllables!")
