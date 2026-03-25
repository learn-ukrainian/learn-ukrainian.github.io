import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix 'you have...' robotic structure
# I need to make sure I catch "You have" regardless of case, but wait, the parser usually works case-insensitively for the first word.
text = text.replace('You have to be careful', 'One must be careful')
text = text.replace('You have the time', 'We possess the time')
text = text.replace('You have learned that', 'We learned that')
text = text.replace('You have seen exactly', 'We have seen exactly')
text = text.replace('You have also mastered', 'We have also mastered')
text = text.replace('You have taken a massive', 'This represents a massive')
text = text.replace('you have to follow', 'one has to follow')
text = text.replace('you have the time', 'one has the time')

# 2. Add more translations for immersion (+200 words)
more_replacements = [
    (
        "We have completed a massive, highly comprehensive journey through the critical concepts of ability, skill, and permission in the Ukrainian language.",
        "Ми закінчили велику подорож через важливі концепції можливості, навичок та дозволу. (We have completed a massive journey through the critical concepts of ability, skill, and permission.)"
    ),
    (
        "We learned that while English uses a single word to carelessly cover very different realities, Ukrainian requires deep precision and situational awareness.",
        "Англійська мова використовує одне слово. Українська мова вимагає точності. (English uses a single word. Ukrainian requires deep precision.)"
    ),
    (
        "You now fully understand how to use **могти** to accurately discuss your daily schedule, your free time, and your circumstantial capacity.",
        "Тепер ви розумієте, як використовувати **могти**. Воно описує ваш графік і вільний час. (You now fully understand how to use **могти**. It describes your schedule and free time.)"
    ),
    (
        "We have seen exactly how **вміти** honors the significant time and effort you spend acquiring new skills, hobbies, and talents over your lifetime.",
        "Ми побачили, як **вміти** показує час і зусилля. Воно описує нові навички та хобі. (We have seen exactly how **вміти** shows time and effort. It describes new skills and hobbies.)"
    ),
    (
        "We have also mastered the essential impersonal construction **можна** to navigate the complex rules of society respectfully and safely.",
        "Ми також вивчили безособову конструкцію **можна**. Вона допомагає розуміти правила суспільства безпечно. (We have also mastered the impersonal construction **можна**. It helps to navigate rules safely.)"
    ),
    (
        "By clearly differentiating between these three powerful concepts,",
        "Чітка різниця між цими трьома концептами є важливою. (A clear difference between these three concepts is important.)"
    ),
    (
        "This represents a massive, undeniable step toward sounding natural, polite, and highly accurate in your everyday conversations.",
        "Це великий крок до природної та правильної мови у щоденних розмовах. (This represents a massive step toward natural and correct speech in daily conversations.)"
    ),
    (
        "Parents and teachers also use this constantly with children to establish safe, non-negotiable boundaries.",
        "Батьки і вчителі часто використовують це з дітьми. Це створює безпечні кордони. (Parents and teachers often use this with children. This creates safe boundaries.)"
    )
]

for old, new in more_replacements:
    text = text.replace(old, new)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)

