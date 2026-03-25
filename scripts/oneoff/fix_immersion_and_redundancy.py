import re

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix redundancy by changing the second dialogue completely.
# Let's replace the formal context dialogue with a restaurant/cafe one.
old_dialogue = """And another scenario in a formal context:

> — **Анна:** Скажіть, будь ласка, де кабінет?
> — **Менеджер:** Ідіть туди. Дивіться, там двері.
> — **Анна:** Дякую.
> — **Менеджер:** Чекайте тут, будь ласка. Не ідіть туди.
> — **Анна:** Добре.
> — **Менеджер:** Візьміть ці документи. Читайте тут.
> — **Анна:** Добре, я читаю.
> — **Менеджер:** Пишіть тут. Не пишіть там.
> — **Анна:** Добре.

| Ukrainian | English |
|-----------|---------|
| Скажіть, будь ласка, де кабінет? | Tell me, please, where is the office? |
| Ідіть туди. Дивіться, там двері. | Go there. Look, there is a door. |
| Дякую. | Thank you. |
| Чекайте тут, будь ласка. Не ідіть туди. | Wait here, please. Do not go there. |
| Добре. | Okay. |
| Візьміть ці документи. Читайте тут. | Take these documents. Read here. |
| Добре, я читаю. | Okay, I am reading. |
| Пишіть тут. Не пишіть там. | Write here. Do not write there. |
| Добре. | Okay. |"""

new_dialogue = """Уявіть ситуацію в кафе (Imagine a situation in a cafe). 

> — **Клієнт:** Дайте, будь ласка, меню.
> — **Офіціант:** Візьміть, будь ласка. Дивіться, тут є кава і чай.
> — **Клієнт:** Покажіть, де кава?
> — **Офіціант:** Ось тут. Читайте.
> — **Клієнт:** Добре. Чекайте, я думаю...
> — **Офіціант:** Не поспішайте. (Don't rush). 

| Українська | English |
|------------|---------|
| Дайте, будь ласка, меню. | Give the menu, please. |
| Візьміть, будь ласка. Дивіться, тут є кава і чай. | Take it, please. Look, here is coffee and tea. |
| Покажіть, де кава? | Show me, where is the coffee? |
| Ось тут. Читайте. | Right here. Read. |
| Добре. Чекайте, я думаю... | Okay. Wait, I am thinking... |
| Не поспішайте. | Do not rush. |"""

content = content.replace(old_dialogue, new_dialogue)

# 2. Translate some English scaffolding to simple Ukrainian.
content = content.replace(
    "Here is a quick classroom exchange using commands:",
    "Ось діалог у класі (Here is a dialogue in the classroom):"
)
content = content.replace(
    "Let's see these commands in action.",
    "Подивіться на ці команди (Look at these commands)."
)
content = content.replace(
    "Let's look at more examples of giving directions in a workspace or study environment:",
    "Ось ще приклади (Here are more examples):"
)
content = content.replace(
    "Here is how you might hear these verbs used in everyday situations or a classroom:",
    "Ось як ми говоримо щодня (Here is how we speak every day):"
)
content = content.replace(
    "Let's look at a short interaction using these verbs:",
    "Читайте короткий діалог (Read the short dialogue):"
)
content = content.replace(
    "Let's look at a brief polite interaction:",
    "Читайте ввічливий діалог (Read the polite dialogue):"
)
content = content.replace(
    "Here are some examples of negative commands.",
    "Ось приклади заборон (Here are examples of prohibitions):"
)
content = content.replace(
    "Let's look at a quick dialogue involving prohibitions.",
    "Читайте діалог про заборони (Read the dialogue about prohibitions):"
)
content = content.replace(
    "Review this final conversation to see commands, polite requests, and prohibitions working together.",
    "Читайте останній діалог (Read the final dialogue)."
)

# 3. Increase immersion by adding a vocabulary practice list in Ukrainian
vocab_list = """
Ось слова для практики (Here are words for practice):
- **Слухай!** (Listen!)
- **Слухайте!** (Listen! - formal)
- **Читай!** (Read!)
- **Читайте!** (Read! - formal)
- **Пиши!** (Write!)
- **Пишіть!** (Write! - formal)
- **Кажи!** (Say!)
- **Кажіть!** (Say! - formal)
- **Роби!** (Do!)
- **Робіть!** (Do! - formal)
- **Чекай!** (Wait!)
- **Чекайте!** (Wait! - formal)
- **Стій!** (Stop/Stand!)
- **Стійте!** (Stop/Stand! - formal)
- **Іди!** (Go!)
- **Ідіть!** (Go! - formal)
"""

content = content.replace(
    "## Вісім обов'язкових дієслів",
    vocab_list + "\n\n## Вісім обов'язкових дієслів"
)

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'w', encoding='utf-8') as f:
    f.write(content)
