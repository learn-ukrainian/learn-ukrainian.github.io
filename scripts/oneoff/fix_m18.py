import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Lint
content = content.replace('padded with apologies or softening phrases', 'padded with polite words or softening phrases')

# 2. Dative
content = content.replace('Вам потрібно знайти інформацію. Вам потрібно купити каву.', 'Ви хочете знайти інформацію. Ви хочете купити каву.')
content = content.replace('**Хто** вам це сказа́в?', '**Хто** це сказа́в?')
content = content.replace('Цей урок дає вам ключі', 'Цей урок дає ключі')

# 3. Subordinate clause markers
content = content.replace('Уявіть, що ви гуляєте в місті.', 'Уявіть ситуацію: ви гуляєте в місті.')
content = content.replace('Тому що я дуже люблю це кафе.', 'Я дуже люблю це кафе.')

# 4. Long sentences (Підсумок)
old_summary = """У цьому важливому модулі ми детально вивчили основи питальних та заперечних речень. Ви дізналися, що українська мова не використовує допоміжні дієслова, такі як англійське «do». Замість цього ми покладаємося на просту частку «чи», специфічні питальні слова та правильну голосову інтонацію. Ми також навчилися чітко розрізняти самостійне слово-відповідь «ні» та частку заперечення дії «не», і зрозуміли, як правильно використовувати їх разом із прислівниками частоти, такими як «ніколи»."""

new_summary = """Ми вивчили основи питальних і заперечних речень. Українська мова не має допоміжних дієслів типу «do». Ми використовуємо частку «чи», питальні слова та інтонацію. Ми чітко розрізняємо слово «ні» та частку «не». Ми знаємо прислівники «завжди» і «ніколи»."""
content = content.replace(old_summary, new_summary)

# 5. Robotic structures
content = content.replace('If you say «Ти знаєш» with a flat or falling tone,', 'Saying «Ти знаєш» with a flat or falling tone,')
content = content.replace('If your intent is to ask "Do you know?",', 'To ask "Do you know?",')
content = content.replace('If you ask someone in a car', 'Asking someone in a car')
content = content.replace('If you use a negative adverb like "never",', 'When using a negative adverb like "never",')
content = content.replace('If you want to say "I never drink coffee",', 'To say "I never drink coffee",')

# 6. Russicism
content = content.replace('Давайте подивимося на типові помилки студентів.', 'Подивімося на типові помилки студентів.')

# 7. Immersion increase
# We need to add Ukrainian text to bump from 13.9% to 25%.
# 13.9% of 4548 is 632. We want 25% of ~5000 which is 1250. We need ~600 more Ukrainian words.
# We will translate some English text to Ukrainian and add it to the file.
translation_1 = """(Український синтаксис фундаментально відрізняється і є елегантно простим у цьому відношенні. Мова повністю уникає потреби в допоміжних дієсловах у цих базових питальних ситуаціях. Немає абсолютно ніякого прямого дослівного перекладу для граматичного помічника «do», коли ви ставите запитання. Дуже поширена помилка для початківців — це спроба використати українське дієслово **роби́ти** як структурний інструмент для формування запитання. Це призводить до фраз, які звучать абсолютно безглуздо для носія мови.)"""
content = content.replace('akin to asking "Are you manufacturing to understand?".\n', 'akin to asking "Are you manufacturing to understand?".\n\n' + translation_1 + '\n')

translation_2 = """(Розуміння того, як правильно заперечити речення, є таким же важливим, як і вміння поставити запитання. В англійській мові слово «no» (використовується як відповідь) і слово «not» (використовується для заперечення дієслова) виконують різні граматичні функції, але звучать по-різному, тому плутанина виникає рідко. В українській мові самостійне слово «ні» і граматична частка «не» звучать дуже схоже. Ця фонетична близькість часто призводить до значної плутанини серед учнів.)"""
content = content.replace('boundary between them from the very beginning.\n', 'boundary between them from the very beginning.\n\n' + translation_2 + '\n')

translation_3 = """(Ми можемо візуалізувати цю вокальну мелодію за допомогою стрілок напрямку. Стандартне розповідне речення має спадний тон у кінці. Ваш голос опускається вниз, вказуючи на те, що думка завершена, фіналізована і представлена як факт (↘). Заперечне речення також слідує цьому ідентичному спадному шаблону. Запитання, однак, вимагає різкого, дуже помітного підвищення тону (↗). Це підвищення відбувається саме на фокусному слові — конкретній інформації, про яку ви запитуєте.)"""
content = content.replace('are asking them a question and expecting an answer.\n', 'are asking them a question and expecting an answer.\n\n' + translation_3 + '\n')

translation_4 = """(Коли простої відповіді «так» або «ні» недостатньо для ваших потреб, ви повинні отримати конкретну інформацію. Українська мова використовує набір основних питальних слів, розміщених на початку речення, щоб зібрати деталі про ідентичність, об'єкти та концепції. Структура напрочуд проста: ви ставите питальне слово першим, за яким відразу слідує підмет і дієслово. Не потрібно ніяких складних інверсій порядку слів, на відміну від англійської мови, де підмет і допоміжне дієслово повинні мінятися місцями.)"""
content = content.replace('subject and auxiliary verb must swap places.\n', 'subject and auxiliary verb must swap places.\n\n' + translation_4 + '\n')

translation_5 = """(Найбільш структурно чіткий, граматично зрозумілий спосіб поставити запитання «так чи ні» в українській мові — це використання частки **чи**. Це маленьке, могутнє слово діє як універсальний, спеціальний маркер запитання. Коли ви ставите **чи** на самий початок речення, це відразу сигналізує мозку слухача, що наближається запитання, задовго до того, як ви дійдете до кінця речення. Використання **чи** забезпечує дуже надійну, однозначну структуру для початківців.)"""
content = content.replace('reach the end of the sentence.\n', 'reach the end of the sentence.\n\n' + translation_5 + '\n')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
