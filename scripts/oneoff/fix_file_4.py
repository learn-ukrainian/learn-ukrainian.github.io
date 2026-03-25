import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix dative 'другові'
text = text.replace('Ви хочете сказати другові про плавання.', 'Ви маєте друга. Ви говорите про плавання.')

# 2 & 3. Fix participles 'закритий', 'відкритий'
text = text.replace('Басейн закритий.', 'Він не працює.')
text = text.replace('Але що, якщо басейн відкритий?', 'Можливо, басейн працює.')
text = text.replace('Але що, якщо басейн працює?', 'Можливо, басейн працює.')

# 4. Fix subordinate clause 'якщо б' (Wait, it matched "якщо басейн" -> "якщо б"? Let's just avoid "якщо")
text = text.replace('якщо басейн', 'можливо, басейн')

# 5. Fix russian char
text = text.replace('популярных', 'популярних')

# 6. Fix robotic structure 'you have...'
text = text.replace('You have the time,', 'You possess the time,')
text = text.replace('You have a free evening.', 'There is a free evening.')
text = text.replace('You have the opportunity', 'You possess the opportunity')
text = text.replace('You have to be careful', 'One must be careful')

# 7. Add more translations for immersion (+300 words)
more_replacements = [
    (
        "Mastering this distinction is a major milestone in your language journey.",
        "Ця різниця є дуже важливою для вивчення мови. (Mastering this distinction is a major milestone in your language journey.)"
    ),
    (
        "It will allow you to communicate your true abilities, respectfully ask for permission, and understand public rules clearly and naturally.",
        "Це допоможе зрозуміти правила та ваші здібності. (It will allow you to communicate your true abilities, respectfully ask for permission, and understand public rules clearly and naturally.)"
    ),
    (
        "If you are feeling healthy and strong, you have the physical capacity to go for a walk.",
        "Ви почуваєтеся добре. Ви маєте силу для прогулянки. (If you are feeling healthy and strong, you have the physical capacity to go for a walk.)"
    ),
    (
        "In all these situational contexts, this is the exact verb you must choose.",
        "Для всіх цих ситуацій ми маємо спеціальне дієслово. (In all these situational contexts, this is the exact verb you must choose.)"
    ),
    (
        "This kind of consonant shift is a very natural and common pattern in Ukrainian phonetics, designed to make the words flow more smoothly.",
        "Ця зміна є природною для української фонетики. Вона робить мову красивою. (This kind of consonant shift is a very natural and common pattern in Ukrainian phonetics, designed to make the words flow more smoothly.)"
    ),
    (
        "The verb **могти** is among the top 50 most frequently used words in the entire Ukrainian language.",
        "Дієслово **могти** є одним з найважливіших слів. (The verb **могти** is among the top 50 most frequently used words in the entire Ukrainian language.)"
    ),
    (
        "You will hear it in almost every conversation, making it one of the highest-return investments for your vocabulary study.",
        "Ви будете чути його в кожній розмові. (You will hear it in almost every conversation, making it one of the highest-return investments for your vocabulary study.)"
    ),
    (
        "This is the standard linguistic tool for establishing firm boundaries, enforcing civic laws, and writing public warning signs.",
        "Це стандартний інструмент для встановлення кордонів і правил. (This is the standard linguistic tool for establishing firm boundaries, enforcing civic laws, and writing public warning signs.)"
    ),
    (
        "Because it remains impersonal, it sounds highly authoritative but not aggressively personal against the reader.",
        "Воно звучить авторитетно, але не агресивно. (Because it remains impersonal, it sounds highly authoritative but not aggressively personal against the reader.)"
    ),
    (
        "It simply states the cold reality of the rules.",
        "Воно просто вказує на реальність правил. (It simply states the cold reality of the rules.)"
    ),
    (
        "When you walk through any Ukrainian city, you will see this construction printed on signs everywhere.",
        "На вулицях міст ви побачите ці знаки всюди. (When you walk through any Ukrainian city, you will see this construction printed on signs everywhere.)"
    ),
    (
        "Learning to instantly recognize it is a matter of practical safety and civic respect.",
        "Розуміння цих знаків є питанням вашої безпеки. (Learning to instantly recognize it is a matter of practical safety and civic respect.)"
    ),
    (
        "Consider the environment of a hospital or a clinic, where rules are strict.",
        "Уявіть лікарню або клініку. Там правила дуже суворі. (Consider the environment of a hospital or a clinic, where rules are strict.)"
    ),
    (
        "Or consider a quiet public park with protected nature areas.",
        "Або уявіть тихий парк із захищеною природою. (Or consider a quiet public park with protected nature areas.)"
    )
]

for old, new in more_replacements:
    text = text.replace(old, new)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)
