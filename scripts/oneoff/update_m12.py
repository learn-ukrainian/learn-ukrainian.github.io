import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md', 'r') as f:
    content = f.read()

# 1. Grammar: Dative at A1 (мові)
content = content.replace(
    "Кольори в українській мові — це прикметники.\nColors in the Ukrainian language are adjectives.",
    "Українські кольори — це прикметники.\nUkrainian colors are adjectives."
)

# 2. Grammar: Dative at A1 (вам)
content = content.replace(
    "**Продавець:** Добрий день! Чим я можу вам допомогти?\n**Seller:** Good afternoon! How can I help you?",
    "**Продавець:** Добрий день! Що ви шукаєте?\n**Seller:** Good afternoon! What are you looking for?"
)

# 3. Grammar: Instrumental at A1 (з іменником)
content = content.replace(
    "Вони завжди узгоджуються з іменником.\nThey always agree with the noun.",
    "Колір має рід іменника.\nThe color has the gender of the noun."
)

# 4. Grammar: Participle (улюблений)
content = content.replace(
    "Мій улюблений колір — зелений.\nMy favorite color is green.",
    "Я дуже люблю зелений колір.\nI like the green color very much."
)
content = content.replace(
    "Це моя улюблена біла футболка.\nThis is my favorite white t-shirt.",
    "Я дуже люблю цю білу футболку.\nI like this white t-shirt very much."
)
content = content.replace(
    "Її улюблений колір — червоний.\nHer favorite color is red.",
    "Вона дуже любить червоний колір.\nShe likes the red color very much."
)

# 5. Grammar: Subordinate clause markers
content = content.replace(
    "Слово «одяг» означає всі речі, які ми носимо.\nThe word \"clothing\" means all the things that we wear.",
    "Ми носимо одяг.\nWe wear clothing."
)
content = content.replace(
    "Цікаво, що слово «одяг» має тільки однину.\nInterestingly, the word \"clothing\" only has a singular form.",
    "Слово «одяг» має тільки однину.\nThe word \"clothing\" only has a singular form."
)
content = content.replace(
    "Він одягає теплу шапку, тому що холодно.\nHe is putting on a warm hat because it is cold.",
    "На вулиці холодно. Він одягає теплу шапку.\nIt is cold outside. He is putting on a warm hat."
)
content = content.replace(
    "Але я думаю, що вона трохи велика.\nBut I think that it is a little big.",
    "Але вона трохи велика.\nBut it is a little big."
)
content = content.replace(
    "Ми використовуємо його, коли говоримо про звички.\nWe use it when we talk about habits.",
    "Ми говоримо про звички.\nWe talk about habits."
)
content = content.replace(
    "Ми використовуємо його, коли ми беремо одяг і надягаємо його.\nWe use it when we take clothes and put them on.",
    "Ми беремо одяг і одягаємо його.\nWe take clothes and put them on."
)

# 6. Robotic structure: 'this is...'
content = content.replace(
    "Це мій чорний кіт.\nThis is my black cat.",
    "Ось мій чорний кіт.\nHere is my black cat."
)
content = content.replace(
    "Це синій олівець.\nThis is a dark blue pencil.",
    "Ось синій олівець.\nHere is a dark blue pencil."
)
content = content.replace(
    "Це дуже гарна біла машина.\nThis is a very beautiful white car.",
    "Там стоїть дуже гарна біла машина.\nA very beautiful white car stands there."
)
content = content.replace(
    "Це синя ручка.\nThis is a dark blue pen.",
    "У мене є синя ручка.\nI have a dark blue pen."
)
content = content.replace(
    "Це велике біле вікно.\nThis is a large white window.",
    "Ось велике біле вікно.\nHere is a large white window."
)
content = content.replace(
    "Це глибоке синє море.\nThis is a deep dark blue sea.",
    "Там глибоке синє море.\nThere is a deep dark blue sea."
)
content = content.replace(
    "Це мої чорні коти.\nThese are my black cats.",
    "Ось мої чорні коти.\nHere are my black cats."
)
content = content.replace(
    "Це мій новий теплий світер.\nThis is my new warm sweater.",
    "Ось мій новий теплий світер.\nHere is my new warm sweater."
)
content = content.replace(
    "Це дороге італійське взуття.\nThis is expensive Italian footwear.",
    "Ось дороге італійське взуття.\nHere is expensive Italian footwear."
)

# 7. Inline English in prose
content = content.replace(
    "- Я ношу́ (I wear)\n- Ти но́сиш (You wear - informal)\n- Він / Вона / Воно но́сить (He / She / It wears)\n- Ми но́симо (We wear)\n- Ви но́сите (You wear - plural/formal)\n- Вони но́сять (They wear)",
    "| Українська | English |\n|---|---|\n| Я ношу́ | I wear |\n| Ти но́сиш | You wear |\n| Він / Вона / Воно но́сить | He / She / It wears |\n| Ми но́симо | We wear |\n| Ви но́сите | You wear |\n| Вони но́сять | They wear |"
)
content = content.replace(
    "- Я одяга́ю (I put on)\n- Ти одяга́єш (You put on)\n- Він / Вона / Воно одяга́є (He / She / It puts on)\n- Ми одяга́ємо (We put on)\n- Ви одяга́єте (You put on)\n- Вони одяга́ють (They put on)",
    "| Українська | English |\n|---|---|\n| Я одяга́ю | I put on |\n| Ти одяга́єш | You put on |\n| Він / Вона / Воно одяга́є | He / She / It puts on |\n| Ми одяга́ємо | We put on |\n| Ви одяга́єте | You put on |\n| Вони одяга́ють | They put on |"
)
content = content.replace(
    "Штани лежать на столі (The pants lie on the table).",
    "\nШтани лежать на столі.\nThe pants lie on the table."
)
content = content.replace(
    "In the morning I put on a white shirt. (The action of getting dressed).\nНа роботу я ношу білу сорочку.\nTo work I wear a white shirt. (The habit or dress code).",
    "In the morning I put on a white shirt.\nНа роботу я ношу білу сорочку.\nTo work I wear a white shirt."
)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md', 'w') as f:
    f.write(content)
