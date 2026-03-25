import re

file_path = "curriculum/l2-uk-en/a1/shopping-and-market.md"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Dative & Complex sentences
text = text.replace("Вміння запитати ціну та купити базові речі дає вам свободу і впевненість.", "Вміння запитати ціну та купити прості речі дає свободу.")
text = text.replace("Базові засоби гігієни", "Основні засоби гігієни")
text = text.replace("базові засоби гігієни", "основні засоби гігієни")
text = text.replace("в українській мові чоловічого роду", "це чоловічий рід")

text = text.replace("Іноді нам потрібно запитати", "Іноді ми хочемо запитати")
text = text.replace("Нам також потрібні речі", "Ми також купуємо речі")
text = text.replace("Нам потрібно вказати", "Ми називаємо")
text = text.replace("вам потрібно знайти", "ви шукаєте")
text = text.replace("Тоді вам потрібно запитати", "Тоді ви запитуєте")
text = text.replace("Вам потрібно пам'ятати", "Пам'ятайте")
text = text.replace("вам потрібна автоматична реакція", "потрібна автоматична реакція")

text = text.replace("перед походом у великий супермаркет", "")

text = text.replace("Ми також маємо форму множини, яка звучить як «коштують».", "Ми також маємо форму множини. Вона звучить як «коштують».")
text = text.replace("думають, що слово «шампунь»", "думають: слово «шампунь»")

text = text.replace("Коли ми використовуємо одиниці вимірювання, ми завжди змінюємо форму наступного слова.", "Ми використовуємо одиниці вимірювання. Тоді ми змінюємо форму наступного слова.")

text = text.replace("Коли ви шукаєте ці товари, вам потрібно знайти правильний магазин.", "Ви шукаєте ці товари. Ви шукаєте правильний магазин.")

text = text.replace("Давайте подивимося на різні приклади, щоб ви зрозуміли логіку.", "Подивімося на різні приклади. Так ви зрозумієте логіку.")

text = text.replace("щоб показати приналежність", "Це показує приналежність")
text = text.replace("Ми використовуємо родовий відмінок, щоб показати приналежність.", "Ми використовуємо родовий відмінок. Це показує приналежність.")

text = text.replace("Щоб швидко говорити, вам потрібна автоматична реакція.", "Ви хочете швидко говорити. Тоді потрібна автоматична реакція.")

# 2. Complexity (>10 words)
text = text.replace("Ви також знаєте як правильно поєднувати числа зі словом «гривня» та основними одиницями вимірювання (кілограм, літр, пляшка).", "Ви знаєте, як правильно поєднувати числа і слово «гривня». Ви знаєте одиниці вимірювання.")
text = text.replace("Нарешті ви вивчили базові засоби гігієни, такі як мило, шампунь і рушник.", "Нарешті ви вивчили основні засоби гігієни. Це мило, шампунь і рушник.")

text = text.replace("Коли ви шукаєте ці товари, ви шукаєте правильний магазин.", "Ви шукаєте ці товари. Ви шукаєте магазин.")

# 3. Robotic structure 'It is a...'
text = text.replace("It is a masculine noun.", "This word is masculine.")
text = text.replace("It is also a masculine noun.", "This word is masculine too.")
text = text.replace("It is a feminine noun.", "This word is feminine.")
text = text.replace("It is a neuter noun.", "This word is neuter.")
text = text.replace("It is your ultimate survival phrase", "This phrase is your ultimate survival tool")

# 4. Russicisms 'давайте ...'
text = text.replace("Давайте подивимося", "Подивімося")
text = text.replace("давайте подивимося", "подивімося")
text = text.replace("Давайте уявимо", "Уявімо")
text = text.replace("Давайте прочитаємо", "Прочитаймо")

# 5. Immersion (Fixing some English bloat to boost % from 34.9% to ~37%)
text = text.replace("""When you enter a store or a market, you need a reliable way to ask for the price. The most universal question you can ask is «Скільки це коштує?». The word «скільки» means "how much" or "how many". The word «це» means "this". Therefore, the complete phrase literally translates to "How much does this cost?". You do not need to conjugate the verb for yourself or the vendor. The subject of the sentence is the item you are buying. Because an item is an "it", we rely on the third-person singular form «коштує». If you are asking about multiple items at once, you would use the plural form «коштують». However, using the singular form «коштує» with the word «це» is perfectly fine for almost every situation. This phrase is your ultimate survival tool when shopping.""", 
"""When you enter a store or a market, ask: «Скільки це коштує?». The word «скільки» means "how much". The word «це» means "this". The complete phrase translates to "How much does this cost?". The subject of the sentence is the item. Because an item is an "it", we rely on the third-person singular form «коштує». If you are asking about multiple items, use the plural form «коштують». Using the singular form «коштує» with the word «це» works for almost every situation.""")

text = text.replace("""In a previous lesson about numbers, we learned that nouns change their endings depending on the number that comes before them. The word for our currency follows this exact same pattern. Let us review how it works so you can understand price tags and spoken amounts perfectly.""",
"""In a previous lesson, we learned that nouns change endings after numbers. The word for our currency follows this exact pattern. Let us review how it works.""")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
