import os

with open('curriculum/l2-uk-en/a1/weather-and-nature.md', 'r') as f:
    text = f.read()

replacements = {
    "Привіт! Я ваш гід. Я живу в Карпатах. Це великі **го́ри** (mountains) в Україні.": "Карпати — це великі **го́ри** (mountains) в Україні.",
    "Hello! I am your guide. I live in the Carpathians. These are large mountains in Ukraine.": "The Carpathian Mountains are large mountains in Ukraine.",
    "Сьогодні ми вивчаємо нові слова. Ми вчимо назви пір року. Ми говоримо про температуру. Ми вивчаємо нову граматику.": "Цей урок дає нові слова. Він пояснює назви пір року. Він дає слова про температуру. Він показує нову граматику.",
    "Today we are learning new words. We are learning the names of the seasons. We are talking about temperature. We are learning new grammar.": "This lesson introduces new words. It covers the names of the seasons. It presents words about temperature. It explains new grammar.",
    "В українській мові ми використовуємо": "Українська мова використовує",
    "In the Ukrainian language, we use": "The Ukrainian language uses",
    "Нам не потрібен підмет.": "Підмет не потрібен.",
    "We do not need a subject.": "A subject is not needed.",
    "Мені прохолодно.": "Стає прохолодно.",
    "I feel cool.": "It becomes cool.",
    "Сонце дає нам тепло.": "Сонце дає тепло.",
    "The sun gives us warmth.": "The sun gives warmth.",
    "Прогноз допомагає нам жити.": "Прогноз дуже допомагає.",
    "The forecast helps us to live.": "The forecast helps a lot.",
    "Люди погоджуються з вами.": "Люди погоджуються.",
    "People agree with you.": "People agree.",
    "Наша культура пов'язана з ними.": "Наша культура шанує сезони.",
    "Our culture is connected to them.": "Our culture honors the seasons.",
    "Ми знаємо, що робити.": "Ми маємо план.",
    "We know what to do.": "We have a plan."
}

for old, new in replacements.items():
    text = text.replace(old, new)

with open('curriculum/l2-uk-en/a1/weather-and-nature.md', 'w') as f:
    f.write(text)

