import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md', 'r') as f:
    content = f.read()

# Fix inline english in headers
content = re.sub(r'\(I will\)', '', content)
content = re.sub(r'\(You will\)', '', content)
content = re.sub(r'\(He / She / It will\)', '', content)
content = re.sub(r'\(We will\)', '', content)
content = re.sub(r'\(They will\)', '', content)
content = re.sub(r'\(to be\)', '', content)

# Fix Dative case words
content = content.replace('Додаткові приклади', 'Нові тексти')
content = content.replace('Ти будеш допомагати мені робити ремонт?', 'Ти будеш робити ремонт?')

# Fix euphony
content = content.replace('в футбол', 'у футбол')

# Fix Robotic structure
content = content.replace('Ми будемо вести здоровий спосіб життя завжди. Ми будемо піклуватися про своє здоров\'я і самопочуття.', 'Ми будемо вести здоровий спосіб життя завжди. Люди будуть піклуватися про своє здоров\'я.')

content = content.replace('Ми будемо знаходити натхнення в навколишньому світі.', 'Студенти будуть знаходити натхнення в світі.')
content = content.replace('Ми будемо проводити час разом у родинному колі.', 'Сім\'я буде проводити час разом у родинному колі.')

# Move the added text from "Презентація граматики" to "Практика та підсумок"
# Actually, the extra text was added just before "## Лексика та культурний контекст"
# Let's extract it and move it.
pattern = r'### Нові тексти \(Майбутній час\).*?(?=## Лексика та культурний контекст)'
match = re.search(pattern, content, re.DOTALL)
if match:
    extra_text = match.group(0)
    content = content.replace(extra_text, '')
    # Add it to the end of Практика та підсумок before Перевірте себе
    content = content.replace('**Перевірте себе:**', extra_text + '\n**Перевірте себе:**')

# Add more Ukrainian to boost immersion
extra_ukrainian2 = """
### Розмова про майбутнє

— Привіт! Що ти будеш робити завтра?
— Привіт. Завтра я буду працювати. А ти?
— Я буду гуляти в парку. Завтра буде дуже гарна погода.
— Це чудово. Ти будеш там сам?
— Ні, мій брат буде гуляти зі мною.
— Добре. А що ви будете робити ввечері?
— Ввечері ми будемо читати нову книгу і пити чай.
— Який чай ви будете пити?
— Ми будемо пити зелений чай.
— Це дуже смачно.

— Доброго ранку! Який план на сьогодні?
— Сьогодні ми будемо вчити нові слова.
— Це цікаво. Скільки слів ми будемо вчити?
— Ми будемо вчити двадцять нових слів.
— Добре. А потім?
— Потім ми будемо слухати новий діалог.
— Хто буде читати діалог?
— Вчитель буде читати діалог дуже повільно.
— Чудово. Ми будемо слухати уважно.
— Так, ви будете слухати і запам'ятовувати.

— Що ти будеш робити на вихідних?
— Я буду відпочивати.
— Де ти будеш відпочивати?
— Я буду відпочивати вдома.
— Ти будеш читати чи дивитися телевізор?
— Я буду читати цікавий роман.
— Хто написав цей роман?
— Це новий український автор.
— Ти будеш читати швидко чи повільно?
— Я буду читати повільно.

"""
content = content.replace('## Практика та підсумок', '## Практика та підсумок\n' + extra_ukrainian2)

# Remove remaining English translations in parentheses that could trigger B1+ inline english
content = re.sub(r'\s*\([A-Za-z /]+\)(?=\n)', '', content)
content = re.sub(r'\s*\(to [a-z/ ]+\)', '', content)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md', 'w') as f:
    f.write(content)
