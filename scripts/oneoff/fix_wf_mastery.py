import re

with open("curriculum/l2-uk-en/a2/wf-mastery.md", "r", encoding="utf-8") as f:
    content = f.read()

# Transliteration
content = content.replace("Фабрика суфіксів: Діячі (Agents)", "Фабрика суфіксів: Діячі")
content = content.replace("Фабрика суфіксів: Процеси (Processes)", "Фабрика суфіксів: Процеси")

# Euphony
content = content.replace("вам зробити каву з собою", "вам зробити каву із собою")

# Participle
content = content.replace("завершений аналог", "фінальний результат")

# Complex sentences
content = content.replace(
    "Письменники та поети часто створюють нові слова (неологізми), просто поєднуючи існуючі корені та префікси новими способами.",
    "Письменники та поети часто створюють нові слова (неологізми). Вони просто поєднують існуючі корені та префікси новими способами."
)
content = content.replace(
    "Коли ви починаєте розпізнавати ці структурні патерни замість запам'ятовування окремих слів, ви відкриваєте для себе мову.",
    "Ви починаєте розпізнавати ці структурні патерни замість запам'ятовування окремих слів. Так ви відкриваєте для себе мову."
)
content = content.replace(
    "Державний стандарт української мови робить акцент на розумінні видових пар саме через цю призму використання префіксів.",
    "Державний стандарт української мови робить акцент на розумінні видових пар. Це відбувається саме через призму використання префіксів."
)
content = content.replace(
    "Багато студентів, які говорять англійською, намагаються запозичити англійський префікс \"re-\", коли хочуть сказати, що роблять щось знову.",
    "Багато студентів говорять англійською. Вони намагаються запозичити англійський префікс \"re-\", коли хочуть робити щось знову."
)
content = content.replace(
    "Він додається до кореня, щоб вказати на людину, яка виконує специфічну дію або має певну роль.",
    "Він додається до кореня. Це вказує на людину, яка виконує дію або має певну роль."
)
content = content.replace(
    "Коли вам потрібно говорити про дію як про абстрактну концепцію (віддієслівний іменник), ви використовуєте суфікс **-ння**.",
    "Іноді вам потрібно говорити про дію як про абстрактну концепцію (віддієслівний іменник — verbal noun). Тоді ви використовуєте суфікс **-ння**."
)
content = content.replace(
    "Дорослі люди постійно використовують їх у повсякденному житті, літературі та навіть у професійному середовищі, щоб пом'якшити прохання або висловити товариськість.",
    "Дорослі люди постійно використовують їх у житті, літературі та на роботі. Це пом'якшує прохання або висловлює товариськість."
)
content = content.replace(
    "Бюрократія, рутина та щоденні графіки майже повністю побудовані на коренях **-ход-** (рух), **-пис-** (писати) та **-роб-** (працювати).",
    "Бюрократія, рутина та щоденні графіки використовують ці елементи. Вони майже повністю побудовані на коренях **-ход-**, **-пис-** та **-роб-**."
)
content = content.replace(
    "Це поєднання створює природну та вільну розмову, яка звучить так само, як говорять носії української мови на вулицях Києва, Львова чи Одеси.",
    "Це поєднання створює природну та вільну розмову. Вона звучить так само, як говорять носії мови на вулицях Києва."
)

# Metalanguage missing translations (іменник)
content = content.replace("статичний іменник", "статичний іменник (noun)")
content = content.replace("іменника на позначення", "іменника (noun) на позначення")
content = content.replace("простого іменника", "простого іменника (noun)")

# Lower immersion by adding English translations and expanding short sections
content = content.replace(
    "Щоб стати успішним архітектором слів, ви повинні спочатку освоїти базові будівельні блоки. Давайте подивимося на п'ять дуже продуктивних префіксів. Вони можуть повністю змінити напрямок або стан завершення дієслова.",
    "Щоб стати успішним архітектором слів, ви повинні спочатку освоїти базові будівельні блоки. Давайте подивимося на п'ять дуже продуктивних префіксів. Вони можуть повністю змінити напрямок або стан завершення дієслова.\n\nTo become a successful word architect, you must first master the basic building blocks. Let's look at five highly productive prefixes. They can completely change the direction or the state of completion of a verb. Understanding these will give you the power to manipulate actions precisely."
)

content = content.replace(
    "Цей префікс вказує на початок дії, обмеження в часі (робити щось недовго) або просте завершення. Це один із найпопулярніших блоків, які ви будете використовувати.",
    "Цей префікс вказує на початок дії, обмеження в часі (робити щось недовго) або просте завершення. Це один із найпопулярніших блоків, які ви будете використовувати. The prefix **по-** is extremely versatile. It can indicate the start of an action, a time limit (doing something for a short while), or a simple completion. It's one of the most popular blocks you will use."
)

content = content.replace(
    "Цей префікс є головним індикатором завершення або об'єднання. Він перетворює тривалий процес на фінальний, остаточний результат. Дія стає повністю готовою.",
    "Цей префікс є головним індикатором завершення або об'єднання. Він перетворює тривалий процес на фінальний, остаточний результат. Дія стає повністю готовою. This prefix is the main indicator of completion or joining together. It turns a lengthy process into a final, definitive result. The action becomes fully complete."
)

content = content.replace(
    "Коли вам потрібно показати рух назовні або вилучення чогось, обирайте цей префікс. Він працює як англійське слово \"out\".",
    "Коли вам потрібно показати рух назовні або вилучення чогось, обирайте цей префікс. Він працює як англійське слово \"out\". When you need to show outward movement or the extraction of something, choose this prefix. It functions very much like the English word \"out\" or the prefix \"ex-\"."
)

content = content.replace(
    "Цей префікс означає перетин межі, повторення дії або переміщення чогось з одного стану або місця в інше. Це український еквівалент англійських \"re-\" або \"trans-\".",
    "Цей префікс означає перетин межі, повторення дії або переміщення чогось з одного стану або місця в інше. Це український еквівалент англійських \"re-\" або \"trans-\". This prefix signifies crossing a boundary, repeating an action, or moving something from one state or place to another. It is the Ukrainian equivalent of the English prefixes \"re-\" or \"trans-\"."
)

content = content.replace(
    "Цей префікс часто вказує на рух за межу або заглиблення у стан. Він також означає початок дії, яка стає фіксованою.",
    "Цей префікс часто вказує на рух за межу або заглиблення у стан. Він також означає початок дії, яка стає фіксованою. This prefix often indicates movement beyond a boundary or going deep into a state. It also means the beginning of an action that becomes fixed or permanent."
)

content = content.replace(
    "Головне рівняння для побудови слів в українській мові є дуже простим: \n**Prefix + Root + Suffix/Ending = New Word**\n\nКожне складне слово має первісну базу та похідні форми. Давайте подивимося, як додавання різних блоків до одного кореня змінює його семантичне значення. Ми використовуємо концепцію \"математики слів\", щоб чітко візуалізувати цей процес.",
    "Головне рівняння для побудови слів в українській мові є дуже простим: \n**Prefix + Root + Suffix/Ending = New Word**\n\nIn this section, we will look at how adding different blocks to a single root changes its semantic meaning completely. We use the concept of \"word math\" to clearly visualize this process. Every complex word has an original base and derivative forms. Understanding this helps you see that you don't need to memorize entirely new words for related concepts.\n\nКожне складне слово має первісну базу та похідні форми. Давайте подивимося, як додавання різних блоків до одного кореня змінює його семантичне значення. Ми використовуємо концепцію \"математики слів\", щоб чітко візуалізувати цей процес."
)

content = content.replace(
    "Корінь **-ход-** несе базову ідею руху або ходіння. Це один із найбільш універсальних коренів в українській мові. Додаючи різні префікси, ми рухаємося через простір і концепції.",
    "Корінь **-ход-** несе базову ідею руху або ходіння. Це один із найбільш універсальних коренів в українській мові. Додаючи різні префікси, ми рухаємося через простір і концепції.\n\nThe root **-ход-** carries the basic idea of motion, specifically walking or going. It is one of the most universal roots in the Ukrainian language. By attaching different prefixes, we navigate through space and concepts, indicating direction such as entering, exiting, or crossing over."
)

content = content.replace(
    "Державний стандарт української мови робить акцент на розумінні видових пар. Це відбувається саме через призму використання префіксів. В англійській ви використовуєте часи групи Perfect (\"I have done\") для завершення. В українській мові ми синтезуємо нове слово. Найпопулярніший спосіб створити дієслово доконаного виду (результат) з недоконаного (процес) — додати префікс.",
    "Державний стандарт української мови робить акцент на розумінні видових пар. Це відбувається саме через призму використання префіксів. В англійській ви використовуєте часи групи Perfect (\"I have done\") для завершення. В українській мові ми синтезуємо нове слово. Найпопулярніший спосіб створити дієслово доконаного виду (результат) з недоконаного (процес) — додати префікс.\n\nThis is a critical concept in Ukrainian grammar: the aspectual pairs. English uses Perfect tenses (like \"I have done\") to show completion, but Ukrainian relies on morphology. We synthesize a new word. The most common way to create a perfective verb (showing result) from an imperfective one (showing process) is by adding a prefix. This system makes the language very precise. We immediately understand whether a person is just enjoying the process or focusing on the final result."
)

# Expand conclusion
old_conclusion = """## Підсумок: Матриця майстерності

Ми пройшли великий шлях у нашій майстерні. Від розуміння базових префіксів до складання 19-літерних гігантів та налаштування емоційної температури слів. Ви побачили, що українська мова — це не хаотичний набір випадкових термінів, а струнка, логічна архітектура. 

Ваша мета тепер — не просто запам'ятовувати, а **аналізувати** та **синтезувати**. Коли ви бачите нове слово, шукайте корінь. Звертайте увагу на префікси, які вказують на напрямок чи завершення (по-, з-, ви-, пере-, за-). Використовуйте суфікси (-ник, -ння, -ус-), щоб змінювати ролі слів або додавати їм емоцій.

Українське словотворення є свідченням незалежної еволюції мови та її внутрішньої креативності. Воно дає змогу мовцям будувати точні, нюансовані значення з простих блоків. Це демонструє глибоку лінгвістичну інженерію, яка є абсолютно самостійною. Тепер ви озброєні "матрицею майстерності", щоб активно розкодовувати мову."""

new_conclusion = """## Підсумок: Матриця майстерності

Ми пройшли великий шлях у нашій майстерні. Від розуміння базових префіксів до складання 19-літерних гігантів та налаштування емоційної температури слів. Ви побачили, що українська мова — це не хаотичний набір випадкових термінів, а струнка, логічна архітектура. 

You have learned that Ukrainian word formation is a highly logical and predictable system. Instead of viewing vocabulary as a massive list of unrelated words, you now possess the analytical tools to break down complex terms into their basic components. By mastering a core set of roots (like **-ход-**, **-пис-**, **-роб-**) and a handful of productive prefixes (such as **по-**, **з-**, **ви-**, **пере-**, **за-**), you can exponentially increase your vocabulary. This morphological approach—synthesizing new meanings by attaching specific blocks—is fundamental to Ukrainian grammar. It not only allows you to deduce the meaning of unfamiliar words you encounter in texts or conversations but also empowers you to construct your own words accurately. 

Furthermore, you explored how suffixes do more than just change a word's grammatical category. The agent suffix **-ник** turns actions into the people who perform them, while the process suffix **-ння** transforms dynamic verbs into static nouns describing the action itself. We also looked at the unique emotional engineering of the Ukrainian language. Diminutive suffixes like **-ус-** or **-ик-** are not just for children; they are powerful sociolinguistic tools used daily by adults to adjust emotional distance, express warmth, soften requests, and show empathy.

Ваша мета тепер — не просто запам'ятовувати, а **аналізувати** та **синтезувати**. Коли ви бачите нове слово, шукайте корінь. Звертайте увагу на префікси, які вказують на напрямок чи завершення (по-, з-, ви-, пере-, за-). Використовуйте суфікси (-ник, -ння, -ус-), щоб змінювати ролі слів або додавати їм емоцій.

Українське словотворення є свідченням незалежної еволюції мови та її внутрішньої креативності. Воно дає змогу мовцям будувати точні, нюансовані значення з простих блоків. Це демонструє глибоку лінгвістичну інженерію, яка є абсолютно самостійною. Тепер ви озброєні "матрицею майстерності", щоб активно розкодовувати мову. The matrix of mastery is in your hands. Use it whenever you read, listen, or speak, and watch how the language opens up to you in a completely new, structured way."""

content = content.replace(old_conclusion, new_conclusion)

with open("curriculum/l2-uk-en/a2/wf-mastery.md", "w", encoding="utf-8") as f:
    f.write(content)
