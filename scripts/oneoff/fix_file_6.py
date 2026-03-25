import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix complexity
text = text.replace('Ми закінчили велику подорож через важливі концепції можливості, навичок та дозволу.', 'Ми закінчили велику подорож. Ми вивчили можливості, навички та дозволи.')

# 2. Add more translations for immersion (+150 words)
more_replacements = [
    (
        "Explain the fundamental difference in real-world meaning between the sentences «Я можу плавати» and «Я вмію плавати».",
        "Поясніть головну різницю між реченнями «Я можу плавати» та «Я вмію плавати». (Explain the fundamental difference between the sentences «Я можу плавати» and «Я вмію плавати».)"
    ),
    (
        "Is the important word «можна» a verb?",
        "Слово «можна» є дієсловом? (Is the important word «можна» a verb?)"
    ),
    (
        "Does it ever change its endings to match the pronoun «I» or «you»?",
        "Воно змінює свої закінчення для займенників «я» або «ти»? (Does it ever change its endings to match the pronoun «I» or «you»?)"
    ),
    (
        "How do you incredibly politely ask a stranger on a train if it is allowed to sit in the empty chair next to them using an impersonal construction?",
        "Як ви дуже ввічливо запитуєте незнайомця в поїзді, чи можна сісти поруч? (How do you incredibly politely ask a stranger on a train if it is allowed to sit next to them?)"
    ),
    (
        "If you see a large red sign in a hospital that says «Тут не можна курити», what exactly does it mean?",
        "Ви бачите великий червоний знак у лікарні: «Тут не можна курити». Що це означає? (If you see a large red sign in a hospital that says «Тут не можна курити», what exactly does it mean?)"
    ),
    (
        "Which of the ability verbs is entirely regular, predictable, and belongs to the standard -іти conjugation group: могти or вміти?",
        "Яке з цих дієслів є повністю правильним і належить до групи -іти: могти чи вміти? (Which of the ability verbs is entirely regular and belongs to the standard -іти conjugation group: могти or вміти?)"
    ),
    (
        "If you are completely too busy to go to the cinema tonight, which specific verb do you use to say «I cannot go»?",
        "Ви дуже зайняті сьогодні ввечері. Яке дієслово ви використовуєте, щоб сказати «I cannot go»? (If you are completely too busy to go to the cinema tonight, which specific verb do you use to say «I cannot go»?)"
    ),
    (
        "What are you doing tomorrow?",
        "Що ти робиш завтра? (What are you doing tomorrow?)"
    ),
    (
        "This dialogue seamlessly blends the immediate need for physical assistance",
        "Цей діалог показує необхідність фізичної допомоги. (This dialogue seamlessly blends the immediate need for physical assistance)"
    ),
    (
        "This dialogue perfectly demonstrates how to respectfully interact with strict office rules",
        "Цей діалог ідеально показує ввічливу поведінку за суворими правилами. (This dialogue perfectly demonstrates how to respectfully interact with strict office rules)"
    )
]

for old, new in more_replacements:
    text = text.replace(old, new)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)

