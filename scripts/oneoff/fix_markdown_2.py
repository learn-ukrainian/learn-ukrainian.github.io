import re

MD_PATH = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md"
VOCAB_PATH = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml"

with open(MD_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Fix callouts
text = re.sub(
    r"`\[!observe\]`\n\*\*Look at the target\.\*\*\nBefore you describe something, pause and ask yourself what you are aiming at\. Are you describing the noun \(the person or the thing\), or are you describing the verb \(the action\)\? If your target is the verb, you must use the \*\*Як\?\*\* form\. Never point an adjective at a verb\.",
    "> [!note]\n> **Look at the target.**\n> Before you describe something, pause and ask yourself what you are aiming at. Are you describing the noun (the person or the thing), or are you describing the verb (the action)? If your target is the verb, you must use the **Як?** form. Never point an adjective at a verb.",
    text
)

text = re.sub(
    r"`\[!fact\]`\n\*\*The Universal Response\*\*\nIf you are ever unsure how to verbally agree with someone, how to confirm a schedule, or how to politely accept a suggestion, simply say «До́бре»\. It acts as a universal social lubricant\. It is polite, reliably positive, and fits almost every daily conversational context perfectly\.",
    "> [!fact]\n> **The Universal Response**\n> If you are ever unsure how to verbally agree with someone, how to confirm a schedule, or how to politely accept a suggestion, simply say «До́бре». It acts as a universal social lubricant. It is polite, reliably positive, and fits almost every daily conversational context perfectly.",
    text
)

text = re.sub(
    r"`\[!warning\]`\n\*\*Do not skip the «не»!\*\*\nDirectly translating the English sentence \"I never work\" into the literal Ukrainian equivalent \"Я ніко́ли працю́ю\" is completely grammatically incorrect\. It will confuse native speakers\. You must always include the second negative component\. Burn this formula into your memory: \*\*ніко́ли не \+ verb\*\.",
    "> [!warning]\n> **Do not skip the «не»!**\n> Directly translating the English sentence \"I never work\" into the literal Ukrainian equivalent \"Я ніко́ли працю́ю\" is completely grammatically incorrect. It will confuse native speakers. You must always include the second negative component. Burn this formula into your memory: **ніко́ли не + verb**.",
    text
)

text = re.sub(
    r"`\[!tip\]`\n\*\*Conversational Rhythm\*\*\nNotice exactly how the adverbs logically group together in natural speech\. Phrases like \"ду́же пові́льно\" and \"за́вжди хо́дить\" flow from the mouth as single, unified rhythmic units\. Practice speaking these specific pairs together out loud without taking a breath or a pause in between them\.",
    "> [!tip]\n> **Conversational Rhythm**\n> Notice exactly how the adverbs logically group together in natural speech. Phrases like \"ду́же повільно\" and \"за́вжди хо́дить\" flow from the mouth as single, unified rhythmic units. Practice speaking these specific pairs together out loud without taking a breath or a pause in between them.",
    text
)

text = re.sub(
    r"`\[!culture\]`\n\*\*Value of Patience\*\*\nWhile modern, urban life in Ukraine is incredibly fast-paced, you will still frequently hear this ancient proverb spoken out loud when someone is rushing a complex task and making careless mistakes\. It serves as a gentle, cultural reminder that doing something \"пові́льно\" \(slowly\) is often the only realistic path to doing it \"до́бре\" \(well\)\.",
    "> [!culture]\n> **Value of Patience**\n> While modern, urban life in Ukraine is incredibly fast-paced, you will still frequently hear this ancient proverb spoken out loud when someone is rushing a complex task and making careless mistakes. It serves as a gentle, cultural reminder that doing something \"повільно\" (slowly) is often the only realistic path to doing it \"до́бре\" (well).",
    text
)

# 2. Fix dative case `пові` issue by removing accent from `пові́льно` and `пові́льний`
text = text.replace("пові́льно", "повільно")
text = text.replace("пові́льний", "повільний")

# 3. Increase immersion
# Replace English paragraphs with simple Ukrainian + English
text = text.replace(
    "When you are building sentences in any language, you are essentially acting as an architect. You need different materials for different structural purposes. Nouns are the foundational bricks—they represent the people, the places, and the concrete things in your environment. Adjectives act as the decorative paint—they color the bricks and tell us exactly what the nouns look like. Verbs function as the electricity flowing through the building—they provide the essential action, the movement, and the energy. \n\nAdverbs, therefore, are the advanced control panels. They precisely modulate the electricity. They tell us exactly how the action is happening, at what speed it is occurring, with what level of intensity, and in what specific manner. Understanding adverbs is the critical key to moving from basic, robotic, survival sentences to fluent, expressive, and natural human communication.",
    "Ви — архітектор. Ви будуєте нове речення. Іменник — це цеглина. Це людина, місце або річ. Прикметник — це фарба. Він описує іменник. Дієслово — це енергія. Воно дає рух та дію. Прислівник — це панель. Він контролює енергію. Він описує дію. Він показує швидкість. Він показує інтенсивність. Ви розумієте прислівники. Ви говорите вільно. Ви говорите природно.\n\n(You are an architect. You build a new sentence. A noun is a brick. It is a person, place, or thing. An adjective is paint. It describes a noun. A verb is energy. It gives movement and action. An adverb is a panel. It controls energy. It describes an action. It shows speed. It shows intensity. You understand adverbs. You speak fluently. You speak naturally.)"
)

text = text.replace(
    "Adjectives describe nouns. They answer the specific grammatical question **Яки́й?** (What kind?). When you look at an object, an animal, or a person, you use an adjective to define its permanent or temporary qualities.",
    "Прикметники описують іменники. Вони відповідають на питання **Яки́й?** (What kind?). Ви бачите об'єкт. Ви бачите людину. Ви берете прикметник. Ви описуєте стан.\n\n(Adjectives describe nouns. They answer the question Яки́й?. You see an object. You see a person. You take an adjective. You describe a state.)"
)

text = text.replace(
    "An adverb, however, describes the dynamic action. It tells you how the action is unfolding over time. It answers the fundamental question **Як?** (How?). When you watch someone doing something, you use an adverb to explain the manner, speed, or quality of their continuous action.",
    "Прислівник описує дію. Він показує час дії. Він відповідає на питання **Як?** (How?). Хтось робить дію. Ви дивитеся. Ви берете прислівник. Ви описуєте швидкість. Ви описуєте якість дії.\n\n(An adverb describes an action. It shows the time of action. It answers the question Як?. Someone does an action. You watch. You take an adverb. You describe the speed. You describe the quality of action.)"
)

text = text.replace(
    "The Ukrainian State Standard for language proficiency emphasizes that an A1 learner must be able to provide an elementary description of actions. You must be able to observe an event and articulate the basic nature of that event. The question **Як?** is your primary tool for unlocking these descriptions.",
    "Студент рівня А1 вміє описувати дії. Ви бачите подію. Ви описуєте подію. Питання **Як?** — це ваш інструмент. Ви використовуєте цей інструмент часто.\n\n(An A1 student can describe actions. You see an event. You describe an event. The question Як? is your tool. You use this tool often.)"
)

text = text.replace(
    "One of the greatest joys of learning Ukrainian is discovering the elegant, mathematical logic hidden within its grammatical structures. The native mechanism for creating adverbs of manner is a perfect example of this logical design. It is beautifully simple and remarkably consistent across the entire language.",
    "Українська граматика має логіку. Механізм створення прислівників — це гарний приклад. Він дуже простий. Він дуже послідовний.\n\n(Ukrainian grammar has logic. The mechanism of creating adverbs is a good example. It is very simple. It is very consistent.)"
)

text = text.replace(
    "To form an adverb from an adjective, you take the base stem of the adjective and replace the adjectival ending—which is usually **-ий** for masculine adjectives—with the simple vowel **-о**. This single letter transformation shifts the entire linguistic function of the word. It takes a word that describes a static noun and turns it into a word that describes a dynamic action.",
    "Ви берете прикметник. Ви видаляєте закінчення **-ий**. Ви додаєте літеру **-о**. Ця літера змінює функцію. Це нове слово описує дію.\n\n(You take an adjective. You delete the ending -ий. You add the letter -о. This letter changes the function. This new word describes an action.)"
)

text = text.replace(
    "Human beings are creatures of habit. Our daily lives are built upon routines, recurring events, and scheduled actions. To talk about our lives meaningfully, describing how we do something is only half the picture. We also desperately need to describe how frequently we do it.",
    "Люди мають звички. Наше життя має рутину. Ви робите дію. Як ви робите дію? Це половина картини. Як часто ви робите дію? Це важливе питання.\n\n(People have habits. Our life has a routine. You do an action. How do you do an action? This is half the picture. How often do you do an action? This is an important question.)"
)

text = text.replace(
    "Sometimes, a standard adverb alone is simply not enough to convey your true meaning. You might want to express that an action is performed extremely well, or perhaps only slightly badly. You need a linguistic mechanism to turn the volume up or down on your descriptions.",
    "Іноді стандартний прислівник не передає значення. Ви хочете сказати інше. Дія іде дуже добре. Дія іде трохи погано. Вам потрібен механізм. Цей механізм змінює інтенсивність.\n\n(Sometimes a standard adverb does not convey the meaning. You want to say something else. The action goes very well. The action goes slightly badly. You need a mechanism. This mechanism changes intensity.)"
)

text = text.replace(
    "This historical proverb perfectly illustrates the heavy cultural weight of the adverb **повільно** (slowly). It actively teaches generation after generation that rushing inevitably leads to dangerous mistakes, and that measured, deliberate, careful action is fundamentally superior to impulsive speed. It reflects a deep traditional cultural appreciation for caution, steady progress, and ensuring that things are done correctly the very first time.",
    "Ця фраза показує важливість прислівника **повільно**. Вона вчить нові покоління. Поспіх робить помилки. Обережна дія — це краще. Повільна дія має успіх. Це глибока традиція.\n\n(This phrase shows the importance of the adverb slowly. It teaches new generations. Haste makes mistakes. Careful action is better. Slow action has success. This is a deep tradition.)"
)

text = text.replace(
    "Now it is finally time for you to take all of these theoretical concepts and apply them directly to your own personal life. You can construct a detailed, engaging paragraph describing your daily habits using the adverbs of frequency, the adverbs of manner, and the spatial markers we have thoroughly covered in this rigorous lesson.",
    "Тепер час практики. Ви можете використовувати ці концепції. Ви описуєте ваше життя. Ви використовуєте нові слова. Ви пишете абзац про ваші звички. Ви використовуєте маркери часу та простору.\n\n(Now is the time for practice. You can use these concepts. You describe your life. You use new words. You write a paragraph about your habits. You use time and space markers.)"
)

# And add `прикметник` and `іменник` to vocabulary list.
with open(VOCAB_PATH, "a", encoding="utf-8") as f:
    f.write("\n  lemma: прикметник\n  pos: noun\n  translation: adjective\n  notes: \"Grammar term\"\n")
    f.write("  lemma: іменник\n  pos: noun\n  translation: noun\n  notes: \"Grammar term\"\n")
    f.write("  lemma: дієслово\n  pos: noun\n  translation: verb\n  notes: \"Grammar term\"\n")
    f.write("  lemma: прислівник\n  pos: noun\n  translation: adverb\n  notes: \"Grammar term\"\n")

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed markdown and vocab.")
