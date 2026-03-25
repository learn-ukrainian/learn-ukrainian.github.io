with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/must-and-want.md', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("Correct: Мені треба йти.", "Say: Мені треба йти.")
content = content.replace("Correct: Мені потрібен лікар.", "Remember: Мені потрібен лікар.")
content = content.replace("Correct: Вона повинна спати.", "Note: Вона повинна спати.")
content = content.replace("Correct: Мені треба працювати.", "Finally: Мені треба працювати.")
content = content.replace("Це базові навички", "Це прості навички")
content = content.replace("Подумайте, яке слово підходить найкраще.", "Оберіть найкраще слово.")

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/must-and-want.md', 'w', encoding='utf-8') as f:
    f.write(content)
