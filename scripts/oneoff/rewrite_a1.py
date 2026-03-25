import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-market.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix Dative case
text = text.replace('чудові фотографії', 'гарні фото')
text = text.replace('В українській мові слово змінює', 'Українські слова змінюють')
text = text.replace('Мені потрібен', 'Я хочу купити')
text = text.replace('дають вам', 'дають покупцю')
text = text.replace('повертає вам частину', 'дає решту')
text = text.replace('Для такого приємного покупця — зроблю знижку!', 'Я зроблю знижку!')

# 2. Fix Instrumental case
text = text.replace('з продавцем про товар', 'про товар')
text = text.replace('з продавцем', 'з продавцем') # Wait, I will just do:
text = text.replace('говорити з продавцем', 'говорити')
text = text.replace('числівники з вагою', 'числівники та вага')
text = text.replace('говорити з ним про товар', 'говорити про товар')
text = text.replace('Перед вами лежать', 'Там лежать')
text = text.replace('Тренуйтеся перед дзеркалом', 'Тренуйтеся вдома')

# 3. Fix subordinate clauses
text = text.replace('Вони кажуть, що їхні фрукти найкращі', 'Вони кажуть: наші фрукти найкращі')
text = text.replace('Продавець знає, що продукт хороший', 'Продавець знає свій продукт')
text = text.replace('Покупець знає, що він купує якісну їжу', 'Покупець бачить якісну їжу')
text = text.replace('Щоб дізнатися ціну, треба запитати', 'Ми хочемо дізнатися ціну. Ми запитуємо')

# 4. Long sentence
text = text.replace('Тепер ви готові йти на справжній базар і купувати найсмачніші продукти самостійно.', 'Тепер ви готові йти на базар. Ви можете купувати продукти.')

# 5. Russicism "здача" -> "решта"
text = text.replace('здача', 'решта')
text = text.replace('здачі', 'решти')
text = text.replace('здачу', 'решту')
text = text.replace('зда́ча [ˈzdatʃa]', 'ре́шта [ˈrɛʃta]')

# 6. Inline English
text = re.sub(r' \([a-zA-Z /]+\)', '', text)  # remove inline (english)
# But wait, we want to keep English in some places, so let's do targeted removal
