import os

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = {
    "ваше **по-ба́тькові**": "ваш **патро́нім**",
    "не мати по-батькові": "не мати патроніма",
    "your «по-батькові»": "your «патронім»",
    "**По-батькові:**": "**Патронім:**",
    "Традиція по-батькові": "Традиція патроніма",
    "The **по-батькові**": "The **патронім**",
    "«По-батькові» will": "«Патронім» will"
}

for old, new in replacements.items():
    text = text.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done part 3.")
