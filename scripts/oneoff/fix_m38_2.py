import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-daily-routine.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Давайте подивимося', 'Подивімося')
text = text.replace('давайте подивимося', 'подивімося')
text = text.replace('слухачеві', 'людям')
text = text.replace('нам ', 'ми ')
text = text.replace('нам потрібен', 'потрібен')
text = text.replace('очікуваний ', ' ')
text = text.replace('довгоочікуваний', 'хороший')

# find "які д"
text = re.sub(r', які д.*?\.', '.', text)
# "тому що м" -> "тому що можу..."
text = text.replace('тому що можу', 'Я можу')
text = text.replace('бо поспішаю', 'Я поспішаю')
text = text.replace('щоб бути', 'Ми хочемо бути')
text = text.replace('Щоб правильно', 'Для того щоб правильно') # wait, "щоб" is still bad. "Для правильного точного часу події потрібен прийменник."

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-daily-routine.md', 'w', encoding='utf-8') as f:
    f.write(text)
