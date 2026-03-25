import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Ми вибираємо другий варіант, коли обмеження виникає через відсутність освіти, практики або навчання.', 'Ми вибираємо другий варіант. Проблема виникає через відсутність освіти чи практики.')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)
