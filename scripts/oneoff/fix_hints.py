import re
filepath = "curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = [line for line in lines if "hint:" not in line or "symbol_hint:" in line]

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Hints removed!")
