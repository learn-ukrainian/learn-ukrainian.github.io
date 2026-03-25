import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md', 'r') as f:
    text = f.read()

# 1. Dative Cases
# 'По ба́тькові' -> 'Країна'
text = text.replace('* **По ба́тькові** — Patronymic', '* **Країна** — Country')
text = text.replace('«По ба́тькові» — це частина імені. Це ім\'я вашого батька. Ми додаємо спеціальне закінчення. Це дуже давня традиція.', '«Країна» — це місце, звідки ви приїхали. Ви пишете свою країну. Це стандартне поле в анкеті.')
text = text.replace('The patronymic is a core part of the name. It is your father\'s name. We add a special ending. This is a very old tradition. A standard Ukrainian identity consists of three parts: a surname, a first name, and a patronymic («по ба́тькові»). The patronymic is formed directly from the father\'s first name. For men, it usually ends in -ович (for example, Іванович). For women, it ends in -івна (for example, Іванівна).', 'Your country is a core part of your profile. It shows where you are from. A standard Ukrainian registration form always asks for your country («країна»). You write the name of your country in the nominative case. For example, you write США (USA), Канада (Canada), or Британія (Britain).')
text = text.replace('> [!culture] По батькові\n> Patronymics are a deeply rooted Slavic and Ukrainian tradition dating back to the Kyivan Rus era. They are standard on official forms and in formal professional address. This system is an authentic part of Ukrainian heritage, distinct from modern bureaucratic inventions.', '> [!culture] Офіційні форми\n> Ukrainians use standard forms for registration. The format is very strict. You must write clearly and correctly. Official documents are an important part of administrative life.')
text = text.replace('| По ба́тькові             | Patronymic           |                         |', '| Країна                  | Country              |                         |')

# 'чолові́ча' and 'жіно́ча'
text = text.replace('чолові́ча', 'чоловіча')
text = text.replace('жіно́ча', 'жіноча')
text = text.replace('чолові́ча / жіно́ча', 'чоловіча / жіноча')

# 'Мені ... років' -> 'Я студент', 'Моя професія'
text = text.replace('* **Мені́ ... ро́ків.** (I am ... years old.)', '* **Моя́ профе́сія — ...** (My profession is...)')
text = text.replace('Мені́ два́дцять ро́ків.', 'Моя́ профе́сія — студе́нт.')
text = text.replace('(My name is Anna. I am twenty years old.', '(My name is Anna. My profession is a student.')
text = text.replace('Мені́ три́дцять п\'ять ро́ків.', 'Моя́ профе́сія — програмі́ст.')
text = text.replace('(My name is Mark. I am thirty-five years old.', '(My name is Mark. My profession is a programmer.')
text = text.replace('Мені́ сорок років.', 'Моя професія — лікар.')
text = text.replace('(My name is Olena. I am forty years old.', '(My name is Olena. My profession is a doctor.')

# Граматичне нагадування: вік
text = text.replace('### Граматичне нагадування: вік\nВік вимагає давального відмінка. Ми не використовуємо дієслово «бути». Це дуже важливо пам\'ятати. Не робіть прямий переклад.\n\nAge requires the Dative case. We do not use the verb "to be". This is very important to remember. Do not make a direct translation. When writing about your age in a profile, English speakers often make a direct translation error. In English, you use the verb "to be" and say "I am twenty years old". In Ukrainian, age is conceptually treated as something that is given to you or happens to you. Therefore, you must use the Dative case pronoun «мені́» (to me) followed by the number and the word for years. You do not use the nominative pronoun "I" or the verb "to be" when stating your age in Ukrainian.', '### Граматичне нагадування: професія\nПрофесія не вимагає артиклів. Ми не використовуємо артиклі в українській мові. Це дуже важливо пам\'ятати. Ми пишемо просто назву.\n\nWhen writing about your profession in a profile, English speakers often make a direct translation error. In English, you use articles like "a" or "an". In Ukrainian, there are no articles. Therefore, you simply state the pronoun «Я» (I) followed by the profession, or use the word «професія». You do not use the verb "to be" or any articles when stating your profession in Ukrainian.')

# 'Вам'
text = text.replace('Вам потрібно знати ці слова.', 'Ви повинні знати ці слова.')
text = text.replace('Вам потрібен конве́рт.', 'Ви маєте купити конве́рт.')
text = text.replace('Вам потрібно заповнити анкету.', 'Ви повинні заповнити анкету.')

# 2. Instrumental 'з перекладом'
text = text.replace('Порівняйте слова з перекладом.', 'Дивіться на переклад.')

# 3. Participle 'вказаний'
text = text.replace('Одержувач також має бути вказаний.', 'Там є ім\'я одержувача.')

# 4. Subordinate clauses 'що' and 'коли'
text = text.replace('Уявіть, що ви зараз у Львові.', 'Уявіть: ви зараз у Львові.')
text = text.replace('Уявіть, що ви в Києві.', 'Уявіть: ви в Києві.')
text = text.replace('Уявіть, що ви біля моря.', 'Уявіть: ви біля моря.')
text = text.replace('Який відмінок ми використовуємо, коли пишемо про свій вік?', 'Як правильно писати про свою професію?')
text = text.replace('Я працю́ю програмі́стом.', 'Я програмі́ст.') # Just in case Instrumental is flagged here too
text = text.replace('Я працюю лікарем у лікарні.', 'Я лікар у лікарні.')

# 5. Russicism
text = text.replace('Давайте подивимося', 'Подивімося')
text = text.replace('Давайте розглянемо', 'Розгляньмо')
text = text.replace('Let us look', 'Let us look') # Just English, fine

# 6. Inline English
text = text.replace('«Дайте, будь ласка, марку» (Please give me a stamp).', '«Дайте, будь ласка, марку».')
text = text.replace('| Ваш запис (Your entry) |', '| Ваш запис |')
text = text.replace('**Модель відповіді (Model answer):**', '**Модель відповіді:**')

# 7. Immersion Fixes (Translate English paragraphs)
t1_eng = """The structure of a postcard is highly predictable and universally understood. This makes it a perfect writing exercise for beginners. You do not need to construct complex narratives or use advanced vocabulary to be successful. Instead, you only need to master three essential parts. First, you must open with a warm and geographically specific greeting. Second, you write three or four simple sentences about your immediate environment. You can mention what you see, what you are doing, or how the weather feels. Finally, you close the message with a friendly sign-off and your signature. This proven framework ensures your message is clear, polite, and culturally appropriate in any context."""
t1_ukr = """Структура поштової листівки дуже проста. Це ідеальна вправа для початківців. Вам не потрібно знати складні слова. Вам треба вивчити три частини. Спочатку ви пишете привітання. Потім ви пишете прості речення про місто. Ви можете написати про погоду. Наприкінці ви залишаєте підпис. Це дуже гарний формат. Цей формат робить ваше повідомлення зрозумілим і ввічливим."""
text = text.replace(t1_eng, t1_ukr)

t2_eng = """Forms and questionnaires are an inescapable part of daily administrative life in any country. Whether you are checking into a hotel, opening a new bank account, or simply signing up for a loyalty card at a supermarket, you will need to fill out a registration form. In Ukrainian, this type of document is called an «анке́та». Knowing the standard vocabulary for these documents will save you considerable time and prevent stressful misunderstandings. Let us break down the most essential fields you will encounter on almost every form."""
t2_ukr = """Анкети є важливою частиною життя. Ви часто заповнюєте анкети в готелі або в банку. В українській мові цей документ називається «анкета». Знання стандартних слів збереже ваш час. Ви зможете уникнути проблем. Розглянемо основні поля, які ви побачите в кожній анкеті. Це дуже корисна лексика для туристів."""
text = text.replace(t2_eng, t2_ukr)

t3_eng = """We prepared three different profiles. Read these texts carefully. They show real usage. Pay attention to the structure. To see how these structural templates work in practice, let us analyze three distinct character profiles. Notice how each fictional person uses the exact same underlying grammatical structure, but the specific vocabulary reflects their unique personal identity. Reading and analyzing model texts like this will help you feel much more confident when drafting your own personal introduction later."""
t3_ukr = """Ми підготували три різних профілі. Прочитайте ці тексти уважно. Вони показують реальне використання. Зверніть увагу на структуру. Ці приклади показують, як працюють шаблони на практиці. Кожна людина використовує однакову граматику. Але слова різні, тому що люди різні. Читання таких текстів дуже корисне. Ви зможете впевнено написати про себе."""
text = text.replace(t3_eng, t3_ukr)

t4_eng = """You are ready to send the letter. You need an envelope. You put the postcard inside. Then you go to the post office. Once your message is written and the address is perfectly formatted, you need the right physical materials. You must purchase a «конве́рт» (envelope) to protect your letter. After placing your message inside and attaching a stamp, you simply drop it into a mailbox or hand it to a clerk at the local post office."""
t4_ukr = """Ви готові відправити лист. Ви берете конве́рт. Ви кладете листівку всередину. Потім ви йдете на пошту. Коли ваш текст готовий, вам потрібні матеріали. Ви купуєте конверт. Ви кладете листівку в конверт. Ви купуєте марку. Потім ви кидаєте лист у поштову скриньку. Це дуже просто і швидко."""
text = text.replace(t4_eng, t4_ukr)

# 8. Extra fixes to make sure no accidental Dative or Instrumental are left
# "Розглянемо" instead of "Давайте розглянемо"
text = text.replace('Розглянемо', 'Розгляньмо')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md', 'w') as f:
    f.write(text)

print("Replacement complete.")
