import re

file_path = "curriculum/l2-uk-en/a1/describing-things-adjectives.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Fix specific parens
replacements = [
    ("Подивіться на кімнату (Look at the room).", "Подивіться на кімнату. — Look at the room."),
    ("Ми вже знаємо слова. Тепер ми описуємо світ! (We already know the words. Now we describe the world!)", "Ми вже знаємо слова. Тепер ми описуємо світ! — We already know the words. Now we describe the world!"),
    ('Most adjectives in Ukrainian belong to the "тверда група" (hard group).', 'Most adjectives in Ukrainian belong to the "тверда група" — hard group.'),
    ("У словнику прикметник завжди має чоловічий рід (In the dictionary, an adjective always has a masculine gender).", "У словнику прикметник завжди має чоловічий рід. — In the dictionary, an adjective always has a masculine gender."),
    ("Де ми ставимо прикметник? (Where do we put the adjective?)", "Де ми ставимо прикметник? — Where do we put the adjective?"),
    ("Зазвичай він стоїть перед іменником (Usually it stands before the noun).", "Зазвичай він стоїть перший: нова машина, новий дім. — Usually it stands first: nova mashyna, novyi dim."),
    ("Додамо ще кілька слів (Let's add a few more words).", "Додамо ще кілька слів. — Let's add a few more words."),
    ("Ці слова описують розмір і якість (These words describe size and quality).", "Ці слова описують розмір і якість. — These words describe size and quality."),
    ('Now let us look at the "м\'яка група" (soft group).', 'Now let us look at the "м\'яка група" — soft group.'),
    ("Ці прикметники дуже важливі (These adjectives are very important).", "Ці прикметники дуже важливі. — These adjectives are very important."),
    ("Золоте правило множини (The golden rule of plurals): усі прикметники у множині закінчуються на -і (all plural adjectives end in -і).", "Золоте правило множини — the golden rule of plurals: усі прикметники у множині закінчуються на -і. — All plural adjectives end in -і."),
    ("Давайте практикувати! (Let's practice!) Ми починаємо з української культури. (We start with Ukrainian culture.)", "Давайте практикувати! — Let's practice! Ми починаємо з української культури. — We start with Ukrainian culture."),
    ("Ви чули про Мавку? (Have you heard of Mavka?)", "Ви чули про Мавку? — Have you heard of Mavka?"),
    ("Це містичний дух лісу (She is a mystical spirit of the forest),", "Це містичний дух лісу — She is a mystical spirit of the forest,"),
    ("Як ми можемо описати Мавку? (How can we describe Mavka?)", "Як ми можемо описати Мавку? — How can we describe Mavka?"),
    ("Ми можемо описувати місця та речі в місті (We can describe places and things in the city):", "Ми можемо описувати місця та речі в місті. — We can describe places and things in the city:"),
    ("І, звичайно, прикметники важливі для їжі (And, of course, adjectives are important for food):", "І, звичайно, прикметники важливі для їжі. — And, of course, adjectives are important for food:"),
    ("Повторімо (Let's review). Прикметники завжди відповідають роду та числу іменника (Adjectives always match the gender and number of the noun). Ми питаємо (We ask):", "Повторімо. — Let's review. Прикметники завжди відповідають роду та числу іменника. — Adjectives always match the gender and number of the noun. Ми питаємо. — We ask:"),
    ("— Добрий день! Це новий дім? (Good afternoon! Is this a new house?)", "— Добрий день! Це новий дім? — Good afternoon! Is this a new house?"),
    ("— Добрий день! Так, це новий дім. (Good afternoon! Yes, this is a new house.)", "— Добрий день! Так, це новий дім. — Good afternoon! Yes, this is a new house."),
    ("— Він великий? (Is it big?)", "— Він великий? — Is it big?"),
    ("— Так, він дуже великий. І вікно нове. (Yes, it is very big. And the window is new.)", "— Так, він дуже великий. І вікно нове. — Yes, it is very big. And the window is new."),
    ("— Це цікаво. Дякую! (That is interesting. Thank you!)", "— Це цікаво. Дякую! — That is interesting. Thank you!")
]

for old, new in replacements:
    text = text.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
