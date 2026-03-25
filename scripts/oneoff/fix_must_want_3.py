import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/must-and-want.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Robotic structure
content = content.replace("Correct: Мені треба йти.", "Say: Мені треба йти.")
content = content.replace("Correct: Мені потрібен лікар.", "Remember: Мені потрібен лікар.")
content = content.replace("Correct: Вона повинна спати.", "Note: Вона повинна спати.")
content = content.replace("Correct: Мені треба працювати.", "Finally: Мені треба працювати.")

# 2. Dative false positive
content = content.replace("Це базові навички", "Це прості навички")

# 3. Find the subordinate clause marker ", яке с"
for line in content.split('\n'):
    if "яке " in line:
        print("FOUND:", line)

