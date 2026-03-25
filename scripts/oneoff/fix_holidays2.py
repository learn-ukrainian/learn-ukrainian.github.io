import re

with open("curriculum/l2-uk-en/a1/holidays-and-traditions.md", "r") as f:
    lines = f.readlines()

new_lines = []
in_callout = False
for line in lines:
    # Fix callouts missing blockquote prefix
    if re.match(r'^\[!(cultural|note|tip|warning|observe|myth-buster|fact)\]', line):
        in_callout = True
        line = "> " + line
    elif in_callout and line.strip() != "" and not line.startswith("> ") and not line.startswith("#"):
        line = "> " + line
    elif in_callout and (line.strip() == "" or line.startswith("#") or line.startswith("|")):
        in_callout = False
        
    new_lines.append(line)

text = "".join(new_lines)

# Fix remaining pedagogy issues
# 1. 'е, що в' and 'о, що д'
text = text.replace("Ми знаємо, що для цього треба використовувати орудний відмінок.", "Тут треба використовувати орудний відмінок.")
text = text.replace("We know that for this we need to use the Instrumental case.", "Here we need to use the Instrumental case.")

text = text.replace("Тепер ми знаємо, що всесвітньо", "Всесвітньо")
text = text.replace("Now we know that the globally", "The globally")

# 3. 'і коли т'
text = text.replace("Що таке «кутя», з чого її роблять і коли традиційно українці її їдять?", "Що таке «кутя»? Коли традиційно українці її їдять?")

# 4. 'Ви можете використовувати її як...' > 10 words
text = text.replace("Ви можете використовувати її як базову модель для ваших власних текстів.", "Вона є базовою моделлю для ваших текстів.")
text = text.replace("You can use it as a base model for your own texts.", "It is a base model for your texts.")

with open("curriculum/l2-uk-en/a1/holidays-and-traditions.md", "w") as f:
    f.write(text)

print("Pass 2 fixes done.")
