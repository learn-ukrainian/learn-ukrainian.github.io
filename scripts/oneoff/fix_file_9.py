import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

more_replacements = [
    (
        "By clearly differentiating between these three powerful concepts,",
        "Чітка різниця між цими трьома концептами є важливою. (A clear difference between these three concepts is important.)"
    ),
    (
        "If you use it as a question, you have a very polite and safe way to ask for permission.",
        "Використовуйте його як запитання. Це ввічливий спосіб попросити дозвіл. (If you use it as a question, you have a very polite and safe way to ask for permission.)"
    ),
    (
        "This is an excellent, respectful way to interact politely with staff in shops, restaurants, or professional offices.",
        "Це чудовий і ввічливий спосіб говорити з персоналом у магазинах, ресторанах або офісах. (This is an excellent, respectful way to interact politely with staff in shops, restaurants, or professional offices.)"
    ),
    (
        "We choose our second option when the limitation stems entirely from a lack of education, practice, or training.",
        "Ми вибираємо другий варіант, коли обмеження виникає через відсутність освіти, практики або навчання. (We choose our second option when the limitation stems entirely from a lack of education, practice, or training.)"
    )
]

for old, new in more_replacements:
    text = text.replace(old, new)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)

