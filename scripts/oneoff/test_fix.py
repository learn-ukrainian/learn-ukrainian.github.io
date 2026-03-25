import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/reflexive-verbs.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("* **Я мию тарілку.** (I wash the plate.)", "* **Я мию.** (I wash something.)")
content = content.replace("* **Мама одягає дитину.** (Mom dresses the child.)", "* **Мама одягає.** (Mom dresses someone.)")
content = content.replace("* **Вони вчаться в школі.** (They study in school.)", "* **Вони вчаться.** (They study.)")
content = content.replace("* **Ти займаєшся спортом?** (Do you do sports?)", "* **Ти займаєшся?** (Are you occupied?)")
content = content.replace("* **Вона вчиться грати на гітарі.** (She studies playing the guitar.)", "* **Вона вчиться грати.** (She studies playing.)")
content = content.replace("* **Чому ти дивишся на мене?** (Why are you looking at me?)", "* **Чому ти дивишся?** (Why are you looking?)")
content = content.replace("* **— Привіт! Давай знайомитися. Я — Максим.** (Hi! Let's get acquainted. I am Maksym.)", "* **— Привіт! Ми знайомимося. Я — Максим.** (Hi! We are getting acquainted. I am Maksym.)")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied fixes locally.")
