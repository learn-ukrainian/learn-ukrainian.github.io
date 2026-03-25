import os

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = {
    "Українська офіційна система має три складові частини.": "Українська офіційна система має три частини.",
    "Наприкінці розкажіть, що ви найбільше любите робити у свій вільний час.": "Наприкінці напишіть про ваш вільний час та улюблені справи.",
    "At the end, tell what you like to do most in your free time.": "At the end, write about your free time and favorite activities.",
    "по ба́тькові": "по-ба́тькові",
    "по батькові": "по-батькові",
    "По батькові": "По-батькові",
    "по-батькові (patronymic) is formed from the father's first name": "по-батькові (patronymic) is formed from the father's first name" # Keep English the same
}

for old, new in replacements.items():
    text = text.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done part 2.")
