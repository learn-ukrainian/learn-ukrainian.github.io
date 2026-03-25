import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix subordinate clause 'щоб сказати'
text = text.replace('Яке дієслово ви використовуєте, щоб сказати «I cannot go»?', 'Яке дієслово означає «I cannot go»?')

# 2. Add more translations (+60 words)
more_replacements = [
    (
        "In this short exchange, they successfully navigated a scheduling possibility,",
        "У цій розмові вони успішно вирішили питання розкладу. (In this short exchange, they successfully navigated a scheduling possibility,)"
    ),
    (
        "checked a permanent skill to see if an activity was viable,",
        "вони перевірили постійні навички для діяльності, (checked a permanent skill to see if an activity was viable,)"
    ),
    (
        "and finally proposed a new circumstantial plan.",
        "і запропонували новий ситуативний план. (and finally proposed a new circumstantial plan.)"
    ),
    (
        "Now, let us move to a professional office environment.",
        "Тепер ми переходимо до професійного офісу. (Now, let us move to a professional office environment.)"
    ),
    (
        "In any workplace, one has to follow corporate rules",
        "На роботі ми повинні дотримуватися корпоративних правил (In any workplace, one has to follow corporate rules)"
    ),
    (
        "and politely request help based on other people's availability.",
        "і ввічливо просити про допомогу. (and politely request help based on other people's availability.)"
    ),
    (
        "Observe the careful use of impersonal permission and circumstantial ability.",
        "Зверніть увагу на використання безособового дозволу. (Observe the careful use of impersonal permission and circumstantial ability.)"
    )
]

for old, new in more_replacements:
    text = text.replace(old, new)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)

