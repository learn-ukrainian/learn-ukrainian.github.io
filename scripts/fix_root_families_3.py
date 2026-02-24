import re

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'r', encoding='utf-8') as f:
    text = f.read()

replacements = [
    ("рухом (movement)", "рухом"),
    ("пішки (on foot)", "пішки"),
    ("підпис (signature)", "підпис"),
    ("письменник (writer)", "письменник"),
    ("недоконаний вид (imperfective)", "недоконаний вид"),
    ("доконаний вид (perfective)", "доконаний вид"),
    ("читати (to read)", "читати"),
    ("прочитати (to read through)", "прочитати"),
    ("читач (reader)", "читач"),
    ("Слухати (to listen)", "Слухати"),
    ("слухач (listener)", "слухач"),
    ("Глядіти (to look)", "Глядіти"),
    ("глядач (viewer, spectator)", "глядач"),
    ("бачити (to see)", "бачити"),
    ("бачення (vision)", "бачення"),
    ("передбачити (to foresee/predict)", "передбачити"),
    ("побачення (romantic date)", "побачення"),
    ("дивитися (to look/watch)", "дивитися"),
    ("В- / У- (in, into)", "В- / У-"),
    ("Ви- (out, outside)", "Ви-"),
    ("При- (arrival, attachment)", "При-"),
    ("Під- (under, from below)", "Під-"),
    ("вхід (entrance —", "вхід ("),
    ("вписати (to type in, to insert text —", "вписати ("),
    ("вихід (exit —", "вихід ("),
    ("виписати (to write out, to prescribe —", "виписати ("),
    ("прихід (arrival —", "прихід ("),
    ("приписати (to assign, to add writing —", "приписати ("),
    ("підхід (approach —", "підхід ("),
]

for old, new in replacements:
    text = text.replace(old, new)

# To further increase immersion, I can translate one small paragraph of English to Ukrainian.
# Let's translate "Creating Your Own Word Networks" -> "Створення власних мереж слів"
# and the text below it.
translation = """
### Створення власних мереж слів
Остання і найефективніша стратегія для вивчення мови — це створення власних мереж слів. Тепер, коли ви розумієте механіку «великої четвірки» коренів, ви можете застосувати цю систему до будь-якого нового кореня, який ви зустрінете. Створіть візуальну карту у своєму зошиті: напишіть новий корінь у центрі та намалюйте лінії, що з'єднують його з усіма префіксами, які ви знаєте (в-, ви-, при-, під-, пере-). Спробуйте передбачити значення кожного нового слова, а потім перевірте словник. Цей активний та аналітичний підхід набагато потужніший, ніж пасивне запам'ятовування довгих списків слів.
"""
text = text.replace("""### Creating Your Own Word Networks
One of the most effective strategies for independent language learning is building your own personal word networks. Now that you understand the mechanics of the "Big Four" roots, you can apply this system to any new root you encounter. Create a visual map in your notebook: write a new core root in the center, and draw branches connecting it to all the prefixes you know (в-, ви-, при-, під-, пере-). Try to predict the meaning of each resulting word, and then check a dictionary to confirm your hypothesis. This active, analytical approach is infinitely more powerful than passively trying to memorize long lists of vocabulary.""", translation)

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'w', encoding='utf-8') as f:
    f.write(text)
