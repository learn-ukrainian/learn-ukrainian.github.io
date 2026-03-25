import re
with open("/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md", "r") as f:
    text = f.read()

for m in re.finditer(r".{0,20}\bчолові\b.{0,20}", text, re.IGNORECASE):
    print("чолові:", repr(m.group(0)))

for m in re.finditer(r".{0,20}\bбазові\b.{0,20}", text, re.IGNORECASE):
    print("базові:", repr(m.group(0)))

