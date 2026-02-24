import re

file_path = "curriculum/l2-uk-en/b1/diminutives-master-class.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove all Latin in parentheses.
# e.g.  (white), (good/beautiful), (Pen / door handle), etc.
content = re.sub(r'\s*\([a-zA-Z\s/,\-]+\)', '', content)

# Fix the long sentence
old_sentence = "Щоб по-справжньому і вільно володіти мовою на впевненому рівні В1 та вище, ви маєте обов'язково вміти миттєво зчитувати ці приховані прагматичні значення, розуміти глибинний культурний код нації та розпізнавати тонку іронію."
new_sentence = "Щоб вільно володіти мовою на впевненому рівні В1 та вище, ви маєте миттєво зчитувати ці приховані прагматичні значення. Також обов'язково потрібно розуміти глибинний культурний код нації та розпізнавати тонку іронію."
content = content.replace(old_sentence, new_sentence)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
