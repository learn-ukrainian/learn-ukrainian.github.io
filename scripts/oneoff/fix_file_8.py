import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix 'розмові'
text = text.replace('У цій розмові вони успішно', 'Цей діалог показує, як вони успішно')

# 2. Add more translations (+30 words)
more_replacements = [
    (
        "Take a quiet moment to reflect deeply on your own life right now.",
        "Подумайте про ваше життя зараз. (Take a quiet moment to reflect deeply on your own life right now.)"
    ),
    (
        "Are you able to list three specific things you know how to do well?",
        "Ви вмієте робити три конкретні речі добре? (Are you able to list three specific things you know how to do well?)"
    ),
    (
        "Try to think of one thing you cannot do today because you are simply too busy?",
        "Що ви не можете зробити сьогодні? Ви дуже зайняті? (Try to think of one thing you cannot do today because you are simply too busy?)"
    ),
    (
        "Try to form these thoughts in your head using the exact grammar structures we learned.",
        "Сформуйте ці думки за допомогою нашої граматики. (Try to form these thoughts in your head using the exact grammar structures we learned.)"
    )
]

for old, new in more_replacements:
    text = text.replace(old, new)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)

