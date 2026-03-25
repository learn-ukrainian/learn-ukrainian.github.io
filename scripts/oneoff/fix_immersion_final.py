with open('curriculum/l2-uk-en/a1/my-world-objects.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix Dative
text = text.replace('Нам потрібно тренувати наш мозок.', 'Ми повинні тренувати наш мозок.')

# Boost immersion in Special Plural
special_old = """As you build your vocabulary of household objects, you will encounter a few words that do not follow the standard singular-plural rules. One of the most common and important examples is the word for door: **двері**.

In English, "door" is typically singular, and "doors" is plural. In Ukrainian, the noun **двері** is inherently and exclusively plural. There is no singular form for a door in the Ukrainian language. Whether you are talking about a single entrance to your bedroom or a set of grand double doors at a theater entrance, you will always use the plural form.

Because **двері** is always plural, any demonstrative pronoun attached to it must also be in its plural form. You can never use the singular **ця** or **та** with it.

*   To say "this door" (near you), you must use the plural "these":
    *   «Ці двері» — This door / These doors
*   To say "that door" (far from you), you must use the plural "those":
    *   «Ті двері» — That door / Those doors

This logic applies to all adjectives and verbs associated with the door as well. You will often hear the phrase «вхідні двері» (the front door / entrance door). Remembering that **двері** is plural will save you from one of the most common grammatical missteps learners make when navigating a Ukrainian home."""

special_new = """Коли ви вивчаєте нові слова, ви побачите спеціальні слова. As you build your vocabulary of household objects, you will encounter a few words that do not follow the standard singular-plural rules. Одне з таких слів — це двері. One of the most common and important examples is the word for door: **двері**.

В англійській мові "door" — це однина. In English, "door" is typically singular, and "doors" is plural. В українській мові слово "двері" завжди має форму множини. In Ukrainian, the noun **двері** is inherently and exclusively plural. В українській мові немає форми однини для цього слова. There is no singular form for a door in the Ukrainian language. Ви завжди будете використовувати множину. Whether you are talking about a single entrance to your bedroom or a set of grand double doors at a theater entrance, you will always use the plural form.

Тому що слово "двері" — це множина, вказівний займенник також має бути у формі множини. Because **двері** is always plural, any demonstrative pronoun attached to it must also be in its plural form. Ви ніколи не можете використовувати слова "ця" або "та" з цим словом. You can never use the singular **ця** or **та** with it.

*   Щоб сказати "this door", ми використовуємо слово "ці":
    To say "this door" (near you), you must use the plural "these":
    *   «Ці двері» — This door / These doors
*   Щоб сказати "that door", ми використовуємо слово "ті":
    To say "that door" (far from you), you must use the plural "those":
    *   «Ті двері» — That door / Those doors

Ця логіка також працює для всіх прикметників. This logic applies to all adjectives and verbs associated with the door as well. Ви часто будете чути фразу «вхідні двері» — the front door. You will often hear the phrase «вхідні двері» — the front door / entrance door. Пам'ятайте, що двері — це завжди множина! Remembering that **двері** is plural will save you from one of the most common grammatical missteps learners make."""

text = text.replace(special_old, special_new)

# Boost immersion in Interior Designer Task
task_old = """Now it is time for you to step into a completely new role. You are no longer just a language learner sitting at a desk; you are a busy interior designer carefully mapping out a space for a demanding client. Look around the room you are currently sitting in. We are going to put your new vocabulary and grammar to the absolute test in a real-world, physical scenario."""

task_new = """Тепер час для вашого нового завдання. Now it is time for you to step into a completely new role. Ви — дизайнер інтер'єру. You are no longer just a language learner sitting at a desk; you are a busy interior designer carefully mapping out a space for a demanding client. Подивіться на вашу кімнату. Look around the room you are currently sitting in. Ми будемо тестувати ваші нові слова. We are going to put your new vocabulary and grammar to the absolute test in a real-world, physical scenario."""

text = text.replace(task_old, task_new)

with open('curriculum/l2-uk-en/a1/my-world-objects.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("More immersion added.")
