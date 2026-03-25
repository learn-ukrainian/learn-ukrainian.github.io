import re

file_path = "curriculum/l2-uk-en/a1/completing-the-alphabet.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: п'є -> м'яч
content = content.replace("- **Сім'я́ п'є чай.**  (The family drinks tea.)", "- **Це сім'я́ і м'яч.** (This is a family and a ball.)")

# Fix 2 & 3: Дякую and Будь ласка
content = content.replace("- **Дя́кую!** (Thank you!)", "- **До́брий ра́нок!** (Good morning!)")
content = content.replace("- **Будь ла́ска!** (Please!)", "- **До́брий ве́чір!** (Good evening!)")

# Fix 4: Callout boxes
# Find paragraphs starting with [!...] and add > to them.
lines = content.split('\n')
new_lines = []
in_callout = False

for line in lines:
    if re.match(r'^\[!.*\]', line):
        in_callout = True
        new_lines.append("> " + line)
    elif in_callout:
        if line.strip() == "":
            in_callout = False
            new_lines.append(line)
        else:
            new_lines.append("> " + line)
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

