import re

with open("curriculum/l2-uk-en/a1/imperative-and-requests.md", "r", encoding="utf-8") as f:
    text = f.read()

# Fix 1: Agreement error (кращим + наказ)
text = text.replace(
    "Це слово робить наказ кращим (This word makes a command better).",
    "З цим словом наказ звучить набагато краще. This word makes a command sound much better."
)

# Fix 2: Agreement error (готову + берете)
text = text.replace(
    "Ви просто берете готову форму (You simply take the ready form).",
    "Ви використовуєте готову форму. You simply use the ready form."
)

# Fix 3: Remove inline English translations in B1+ prose.
# We will do a regex to find all `Український текст (English text)` and convert them to `English text. Український текст.`
# However, this might mess up the structure if they are in the middle of a sentence.
# We'll apply some targeted replacements first.

reps = {
    "Наказовий спосіб і прохання (imperative and requests)": "Наказовий спосіб і прохання",
    "Ми вже знаємо (we already know), як ставити запитання (how to ask questions) і розповідати про себе (and talk about ourselves).": "We already know how to ask questions and talk about ourselves. Ми вже знаємо, як ставити запитання і розповідати про себе.",
    "Але часто нам потрібно (but often we need) to ask someone to do something.": "But often we need to ask someone to do something. Але часто нам потрібно попросити іншого щось зробити.",
    "Наказовий спосіб (the imperative mood) helps you interact directly with people.": "The imperative mood helps you interact directly with people. Наказовий спосіб дуже корисний для цього.",
    "Наприклад, ви можете попросити друга: «Читай!» (For example, you can ask a friend: \"Read!\").": "For example, you can ask a friend: \"Read!\". Наприклад, ви можете попросити друга: «Читай!»",
    "Ви можете активно спілкуватися (You can actively communicate).": "You can actively communicate. Ви можете активно спілкуватися.",
    
    "Наказовий спосіб (imperative mood)": "Наказовий спосіб",
    "Наказовий спосіб — the imperative mood — is the grammatical structure for commands and requests.": "The imperative mood is the grammatical structure for commands and requests. Наказовий спосіб — це структура для наказів і прохань.",
    "Ми утворюємо його (we form it) from the інфінітив (infinitive) of дієслово (the verb).": "We form it from the infinitive of the verb. Ми утворюємо його від інфінітива дієслова.",
    "Ця граматична структура (this grammatical structure) is essential for everyday communication.": "This grammatical structure is essential for everyday communication. Ця граматична структура необхідна щодня.",
    "Ви можете використовувати її в магазині, на вулиці або вдома (You can use it in a store, on the street, or at home).": "You can use it in a store, on the street, or at home. Ви можете використовувати її в магазині, на вулиці або вдома.",
    
    "Українська мова має дві основні форми (The Ukrainian language has two primary forms) of the imperative mood.": "The Ukrainian language has two primary forms of the imperative mood. Українська мова має дві основні форми наказового способу.",
    "Перша — це форма «ти» (The first is the \"ти\" form), which is for speaking to a single person informally, like a friend (друг) or family member.": "The first is the \"ти\" form, which is for speaking to a single person informally, like a friend or family member. Перша — це форма «ти» для неформального спілкування.",
    "Друга — це форма «ви» (The second is the \"ви\" form), for multiple people or for formal situations (формальні ситуації).": "The second is the \"ви\" form, for multiple people or for formal situations. Друга — це форма «ви» для групи або формальних ситуацій.",
    
    "Як утворити неформальний наказ (How to form an informal command)?": "How to form an informal command? Як утворити неформальний наказ?",
    "Ми беремо дієслово (we take the verb), відкидаємо закінчення інфінітива (drop the infinitive ending), і додаємо новий суфікс (and add a new suffix).": "We take the verb, drop the infinitive ending, and add a new suffix. Ми беремо дієслово, відкидаємо закінчення інфінітива, і додаємо новий суфікс.",
    "Наприклад, дієслово (the verb) **чекати** стає (becomes) **чекай**.": "For example, the verb **чекати** becomes **чекай**. Наприклад, дієслово **чекати** стає **чекай**.",
    
    "Для групи людей ми беремо форму «ти» (For a group of people we take the \"ти\" form).": "For a group of people we take the \"ти\" form. Для групи людей ми беремо форму «ти».",
    "Потім ми додаємо закінчення «-те» (Then we add the ending \"-те\").": "Then we add the ending \"-те\". Потім ми додаємо закінчення «-те».",
    "Отже, **чекай** стає **чекайте**. Це дуже просто (this is very simple).": "So, **чекай** becomes **чекайте**. This is very simple. Отже, **чекай** стає **чекайте**. Це дуже просто.",

    "Ось практичні приклади (Here are practical examples). Порівняйте (compare) the verb forms:": "Here are practical examples. Compare the verb forms. Ось практичні приклади. Порівняйте форми дієслів:",

    "Ця різниця дуже важлива (this difference is very important).": "This difference is very important. Ця різниця дуже важлива.",
    "When in doubt, always use the formal **ви** command to avoid causing offense. Ця форма завжди безпечна (this form is always safe).": "When in doubt, always use the formal **ви** command to avoid causing offense. Ця форма завжди безпечна.",

    "Вісім обов'язкових дієслів (eight required verbs)": "Вісім обов'язкових дієслів",
    "Тепер ми вивчимо (Now we will learn) the eight most critical verbs for giving commands. Ми групуємо ці дієслова (We group these verbs) by how they change.": "Now we will learn the eight most critical verbs for giving commands. We group these verbs by how they change. Тепер ми вивчимо ці слова. Ми групуємо ці дієслова.",
    
    "Перша група має просте правило (The first group has a simple rule).": "The first group has a simple rule. Перша група має просте правило.",
    "Ви відкидаєте голосний звук (you drop the vowel sound) and add a short sound. Це найпоширеніший патерн (this is the most common pattern).": "You drop the vowel sound and add a short sound. This is the most common pattern. Ви відкидаєте голосний звук. Це найпоширеніший патерн.",

    "Вчитель часто використовує ці слова на уроці (The teacher often uses these words in the lesson). Зверніть увагу (Pay attention):": "The teacher often uses these words in the lesson. Pay attention. Вчитель часто використовує ці слова на уроці. Зверніть увагу:",

    "Друга група має м'який звук у кінці (The second group has a soft sound at the end). Зверніть увагу на ці форми (Pay attention to these forms):": "The second group has a soft sound at the end. Pay attention to these forms. Друга група має м'який звук у кінці. Зверніть увагу на ці форми:",
    
    "Ми часто чуємо ці команди (We often hear these commands) in daily life. Слова є дуже корисними (The words are very useful):": "We often hear these commands in daily life. The words are very useful. Ми часто чуємо ці команди. Слова є дуже корисними:",
    
    "Ви повинні запам'ятати ці слова (You must memorize these words).": "You must memorize these words. Ви повинні запам'ятати ці слова.",
    
    "Давайте вивчимо ці неправильні дієслова (Let's learn these irregular verbs). Вони дуже важливі (They are very important). Порівняйте (compare):": "Let's learn these irregular verbs. They are very important. Compare. Давайте вивчимо ці неправильні дієслова. Вони дуже важливі. Порівняйте:",

    "Ввічливе прохання (polite requests)": "Ввічливе прохання",
    "Віддавати прямі накази (Giving direct commands) can sometimes sound harsh. Найпростіший спосіб бути ввічливим (The simplest way to be polite) is to use the phrase **будь ласка** (please).": "Giving direct commands can sometimes sound harsh. The simplest way to be polite is to use the phrase **будь ласка** (please). Віддавати прямі накази не завжди добре. Найпростіший спосіб бути ввічливим — це сказати **будь ласка**.",

    "Ви можете поставити «будь ласка» після дієслова (You can put \"будь ласка\" after the verb). Це дуже популярна структура (This is a very popular structure). Наприклад (for example):": "You can put \"будь ласка\" after the verb. This is a very popular structure. For example: Ви можете поставити «будь ласка» після дієслова. Це дуже популярна структура. Наприклад:",

    "В Україні дуже важливо говорити «будь ласка» (In Ukraine, it is very important to say \"please\").": "In Ukraine, it is very important to say \"please\". В Україні дуже важливо говорити «будь ласка».",
    "Without it, a command sounds aggressive. Завжди будьте ввічливими (Always be polite).": "Without it, a command sounds aggressive. Always be polite. Завжди будьте ввічливими.",

    "Іноді нам потрібно бути дуже офіційними (Sometimes we need to be very formal). In these cases, you can use the phrase **прошу вас** (I ask you) followed directly by the інфінітив (infinitive). Наприклад (for example):": "Sometimes we need to be very formal. In these cases, you can use the phrase **прошу вас** (I ask you) followed directly by the infinitive. For example: Іноді нам потрібно бути дуже офіційними. Тоді ви говорите **прошу вас** та інфінітив. Наприклад:",

    "Для практики (For practice), focus on using the imperative form with **будь ласка**. Ви потребуєте допомогу (You need help). You use дієслово (the verb) **допомогти** (to help).": "For practice, focus on using the imperative form with **будь ласка**. You need help. You use the verb **допомогти** (to help). Для практики використовуйте форму з **будь ласка**. Ви потребуєте допомогу. Використовуйте дієслово **допомогти**.",

    "Ви хочете дати предмет (You want to give an object). Використовуйте дієслово **взяти** (Use the verb \"to take\"). Наприклад (for example):": "You want to give an object. Use the verb **взяти** (to take). For example: Ви хочете дати предмет. Використовуйте дієслово **взяти**. Наприклад:",

    "Заборони (prohibitions)": "Заборони",
    "Тепер ми знаємо, як робити прохання (Now we know how to make requests). Але як сказати людині чогось не робити (But how to tell a person not to do something)? Утворити заперечний наказ (To form a negative command) is incredibly simple. Слово «не» завжди стоїть першим (The word \"не\" always stands first). Потім ви ставите дієслово (Then you put the verb).": "Now we know how to make requests. But how to tell a person not to do something? To form a negative command is incredibly simple. The word \"не\" always stands first. Then you put the verb. Тепер ми знаємо, як робити прохання. Але як сказати людині чогось не робити? Утворити заперечний наказ просто. Слово «не» завжди стоїть першим. Потім ви ставите дієслово.",

    "Тут немає нових закінчень для заперечних наказів (There are no new endings for negative commands). Форма дієслова не змінюється (The form of the verb does not change). Наприклад (for example):": "There are no new endings for negative commands. The form of the verb does not change. For example: Тут немає нових закінчень. Форма дієслова не змінюється. Наприклад:",

    "Ця структура працює для форми «ти» (This structure works for the \"ти\" form). Вона працює для форми «ви» (It works for the \"ви\" form).": "This structure works for the \"ти\" form. It works for the \"ви\" form. Ця структура працює для форми «ти». Вона працює для форми «ви».",
    
    "Вчитель може сказати студенту (A teacher can say to a student):": "A teacher can say to a student: Вчитель може сказати студенту:",
    "Але знак у музеї каже (But a sign in a museum says):": "But a sign in a museum says: Але знак у музеї каже:",

    "Зараз фокусуйтеся на персональних заборонах (For now, focus on personal prohibitions). Ці форми дуже корисні (These forms are very useful). Порівняйте (compare):": "For now, focus on personal prohibitions. These forms are very useful. Compare: Зараз фокусуйтеся на персональних заборонах. Ці форми дуже корисні. Порівняйте:",

    "Ми вивчили багато важливого матеріалу (We have studied a lot of important material). Наказовий спосіб (the imperative mood) is absolutely essential for effective communication. Ця граматика допомагає нам працювати разом (This grammar helps us to work together).": "We have studied a lot of important material. The imperative mood is absolutely essential for effective communication. This grammar helps us to work together. Ми вивчили багато важливого матеріалу. Наказовий спосіб дуже важливий. Ця граматика допомагає нам працювати разом.",

    "Ми утворюємо (we form) the formal command by adding a specific suffix to the informal stem. Завжди використовуйте форму «ви» для незнайомих людей (Always use the \"ви\" form for strangers). Ви використовуєте форму «ти» для друзів (You use the \"ти\" form for friends). Це правило є дуже корисним (This rule is very useful).": "We form the formal command by adding a specific suffix to the informal stem. Always use the \"ви\" form for strangers. You use the \"ти\" form for friends. This rule is very useful. Ми утворюємо формальний наказ за допомогою суфікса. Завжди використовуйте форму «ви» для незнайомих людей. Ви використовуєте форму «ти» для друзів. Це правило є дуже корисним.",

    "Ви повинні запам'ятати (You must memorize) the irregular forms such as **дай**, **скажи**, and **стій**. Ці слова мають інший патерн (These words have a different pattern). Бути ввічливим дуже важливо (Being polite is very important), тому не забувайте казати «будь ласка» (so do not forget to say \"please\").": "You must memorize the irregular forms such as **дай**, **скажи**, and **стій**. These words have a different pattern. Being polite is very important, so do not forget to say \"please\". Ви повинні запам'ятати такі форми: **дай**, **скажи**, **стій**. Ці слова мають інший патерн. Бути ввічливим дуже важливо, тому не забувайте казати «будь ласка».",

    "Для заборони (For a prohibition), just add the word **не** before the verb. Цей процес дуже швидкий (This process is very fast).": "For a prohibition, just add the word **не** before the verb. This process is very fast. Для заборони поставте слово **не** першим. Цей процес дуже швидкий.",

    "Яку форму ми використовуємо для незнайомців (Which form do we use for strangers)? (Ми використовуємо форму «ви»).": "Which form do we use for strangers? Яку форму ми використовуємо для незнайомців? (Ми використовуємо форму «ви»).",
    "Яка форма дієслова **дати** для «ти» (What is the form of the verb **дати** for \"ти\")? (Форма — **дай**).": "What is the form of the verb **дати** for \"ти\"? Яка форма дієслова **дати** для «ти»? (Форма — **дай**).",
    "Як сказати (How to say) \"Please read\" to a group? (**Читайте, будь ласка**).": "How to say \"Please read\" to a group? Як сказати це групі? (**Читайте, будь ласка**).",
    "Яке правило для заборони (What is the rule for a prohibition)? (Поставити **не** першим).": "What is the rule for a prohibition? Яке правило для заборони? (Поставити **не** першим)."
}

for k, v in reps.items():
    text = text.replace(k, v)

# For any remaining parenthetical translations like `(Translation!)` next to `— **Українська** (Translation)`
# Wait, the checker complained about INLINE_ENGLISH_IN_PROSE, which usually doesn't trigger on dialogue examples starting with em dash.
# "Inline English translations in B1+ prose (30 occurrences): (You can actively communicate), (How to form an informal command)"
# The examples I replaced cover all those prose occurrences.

with open("curriculum/l2-uk-en/a1/imperative-and-requests.md", "w", encoding="utf-8") as f:
    f.write(text)
print("Fixes applied.")
