import os

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/writing-skills.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = {
    "Писати поштові листівки дуже приємно.": "Писати ці листівки дуже приємно.",
    "Writing postcards is very pleasant.": "Writing such postcards is very pleasant.",
    "Використовуйте дуже прості базові слова.": "Використовуйте дуже прості слова.",
    "Use very simple basic words.": "Use very simple words.",
    "Але базові слова там завжди однакові.": "Але прості слова там завжди однакові.",
    "But the basic words there are always the same.": "But the simple words there are always the same.",
    "Ви вивчили назви базових полів": "Ви вивчили назви головних полів",
    "Досить часто нам треба написати коротко про себе.": "Досить часто ми пишемо коротко про себе.",
    "Quite often we need to write briefly about ourselves.": "Quite often we write briefly about ourselves.",
    "Також вам треба написати вашу домашню адресу, телефон та електронну пошту.": "Також треба написати домашню адресу, телефон та електронну пошту.",
    "You also need to write your home address, phone, and email.": "Also you need to write a home address, phone, and email.",
    "Вам потрібно дуже швидко зрозуміти, що саме писати в кожному полі.": "Треба дуже швидко зрозуміти кожне поле.",
    "You need to very quickly understand what exactly to write in each field.": "You need to very quickly understand each field.",
    "Вашим друзям буде дуже цікаво це читати.": "Ваші друзі будуть дуже раді це читати.",
    "Your friends will be very interested to read this.": "Your friends will be very glad to read this.",
    "### Ментальне тренування з анкетою": "### Ментальне тренування: анкета",
    "Це офіційний стандарт для всієї країни, який потрібно запам'ятати.": "Це офіційний стандарт для всієї країни. Його потрібно запам'ятати.",
    "This is the official standard for the whole country that you need to remember.": "This is the official standard for the whole country. You need to remember it.",
    "Це та людина, яка отримає ваш лист.": "Ця людина отримає ваш лист.",
    "This is the person who will receive your letter.": "This person will receive your letter.",
    "Це людина, яка фізично пише та надсилає цей лист.": "Ця людина фізично пише та надсилає цей лист.",
    "This is the person who physically writes and sends this letter.": "This person physically writes and sends this letter.",
    "Використовуйте всі ті слова, які ми сьогодні вивчили.": "Використовуйте всі нові слова.",
    "Use all those words that we learned today.": "Use all new words.",
    "Наприклад, ви можете написати, що саме ви зараз бачите.": "Наприклад, ви можете описати ваші враження.",
    "For example, you can write exactly what you see right now.": "For example, you can describe your impressions.",
    "Уявіть, що ці ситуації є абсолютно реальні.": "Ці ситуації є абсолютно реальні.",
    "Imagine that these situations are absolutely real.": "These situations are absolutely real.",
    "Уявіть, що ви зараз відпочиваєте в Одесі.": "Ви зараз відпочиваєте в Одесі.",
    "Imagine that you are currently resting in Odesa.": "You are currently resting in Odesa.",
    "Коли ми пишемо про свій вік, є одне спеціальне правило.": "Ми пишемо про свій вік. Тут є одне спеціальне правило.",
    "When we write about our age, there is one special rule.": "We write about our age. There is one special rule here.",
    "Якщо ми пишемо одразу кільком людям, ми пишемо форму «бувайте».": "Ми пишемо одразу кільком людям. Тоді ми пишемо форму «бувайте».",
    "If we write to several people at once, we write the form «бувайте».": "We write to several people at once. Then we write the form «бувайте».",
    "Щоб ваш короткий текст був дійсно гарним, потрібні правильні фрази.": "Ваш короткий текст буде дійсно гарним. Для цього потрібні правильні фрази.",
    "To make your short text really good, you need the right phrases.": "Your short text will be really good. For this, you need the right phrases.",
    "В офіційних анкетах ми завжди використовуємо прикметники.": "В офіційних анкетах ми завжди використовуємо спеціальні слова.",
    "In official forms, we always use adjectives.": "In official forms, we always use special words.",
    "Де ви напишете прикметник?": "Де ви напишете стать?",
    "Where will you write the adjective?": "Where will you write the gender?",
    "Яке слово ми використовуємо в анкеті для \"male gender\": іменник «чоловік» чи прикметник «чоловіча»?": "Яке слово ми використовуємо в анкеті для \"male gender\": «чоловік» чи «чоловіча»?",
    "Слово «вулиця» ми пишемо як «вул.». Слово «будинок» ми пишемо як «буд.». Слово «квартира» має своє стандартне скорочення «кв.».": "Ми пишемо «вулиця» як «вул.». А «будинок» ми пишемо як «буд.». Також «квартира» має скорочення «кв.».",
    "The word «вулиця» (street) we write as «вул.». The word «будинок» (building) we write as «буд.». The word «квартира» (apartment) has its standard abbreviation «кв.».": "We write «вулиця» (street) as «вул.». And we write «будинок» (building) as «буд.». Also, «квартира» (apartment) has the abbreviation «кв.».",
    "Ви навчилися писати короткий текст про себе, успішно використовуючи правильні граматичні конструкції, особливо давальний відмінок для опису віку.": "Ви навчилися писати короткий текст про себе. Ви успішно використовуєте правильні граматичні конструкції. Давальний відмінок для віку дуже важливий.",
    "You learned to write a short text about yourself, successfully using correct grammatical constructions, especially the Dative case for describing age.": "You learned to write a short text about yourself. You successfully use correct grammatical constructions. The Dative case for age is very important.",
    "**Кому** (To whom) + Давальний відмінок (Dative case)\n* **Від кого** (From whom) + Родовий відмінок (Genitive case)": "Поле «Кому» — давальний відмінок.\n* Поле «Від кого» — родовий відмінок.\n\n**Grammar of the envelope:**\n* The «Кому» field — Dative case.\n* The «Від кого» field — Genitive case."
}

for old, new in replacements.items():
    if old not in text:
        print(f"NOT FOUND: {old}")
    text = text.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done.")
