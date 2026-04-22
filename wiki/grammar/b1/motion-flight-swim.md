<!-- wiki-meta
slug: motion-flight-swim
domain: grammar/b1
tracks: [b1, b2]
compiled: 2026-04-07
generated_by_model: gemini-2.5-pro
-->

version: "1.0"
module: sounds-letters-and-hello
level: a1
inline:
  - id: quiz-sounds-vs-letters
    type: quiz
    instruction: "Оберіть правильну відповідь на основі знань про звуки та літери."
    items:
      - question: "Що ми чуємо і вимовляємо?"
        options: ["Звуки", "Літери", "Малюнки"]
        correct: 0
      - question: "Що ми бачимо і пишемо?"
        options: ["Звуки", "Літери", "Слова"]
        correct: 1
      - question: "Скільки літер в українській абетці?"
        options: ["32", "33", "38"]
        correct: 1
      - question: "Скільки звуків в українській мові?"
        options: ["33", "38", "40"]
        correct: 1
      - question: "Чи можна говорити «голосна літера»?"
        options: ["Так", "Ні", "Тільки іноді"]
        correct: 1
      - question: "Яка літера не має власного звука?"
        options: ["А", "Ь (м’який знак)", "М"]
        correct: 1

  - id: watch-and-repeat-vowels
    type: watch-and-repeat
    instruction: "Слухайте та повторюйте звуки разом з Анною Огойко."
    items:
      - youtubeId: "hvB3VpcR3ZE"
        label: "А"
        sound: "[а]"
      - youtubeId: "VB1O6PmtYRU"
        label: "У"
        sound: "[у]"
      - youtubeId: "KFlsroBW0dk"
        label: "Е"
        sound: "[е]"
      - youtubeId: "W-1rCu0indE"
        label: "И"
        sound: "[и]"
      - youtubeId: "Z9TH0H4ShGo"
        label: "І"
        sound: "[і]"
      - youtubeId: "Ez95H4ibuJo"
        label: "М"
        sound: "[м]"
      - youtubeId: "vNUfiKHPYaU"
        label: "Н"
        sound: "[н]"
      - youtubeId: "7UsFBgSL91E"
        label: "С"
        sound: "[с]"
      - youtubeId: "J7sGEI4-xJo"
        label: "К"
        sound: "[к]"
      - youtubeId: "v6-3Xg52Buk"
        label: "Л"
        sound: "[л]"
      - youtubeId: "fMGsQ5KPQgg"
        label: "Р"
        sound: "[р]"

  - id: letter-grid-alphabet
    type: letter-grid
    instruction: "Ознайомтеся з українською абеткою. Голосні виділені червоним."
    items:
      - label: "А а"
        hint: "Абетка 📖"
        category: "vowel"
      - label: "Б б"
        hint: "Барабан 🥁"
        category: "consonant"
      - label: "В в"
        hint: "Вода 💧"
        category: "consonant"
      - label: "Г г"
        hint: "Гора ⛰️"
        category: "consonant"
      - label: "Ґ ґ"
        hint: "Ґудзик 🔘"
        category: "consonant"
      - label: "Д д"
        hint: "Дім 🏠"
        category: "consonant"
      - label: "Е е"
        hint: "Екран 🖥️"
        category: "vowel"
      - label: "Є є"
        hint: "Єнот 🦝"
        category: "vowel"
      - label: "Ж ж"
        hint: "Жук 🪲"
        category: "consonant"
      - label: "З з"
        hint: "Зірка ⭐"
        category: "consonant"
      - label: "И и"
        hint: "Кит 🐋"
        category: "vowel"
      - label: "І і"
        hint: "Іграшка 🧸"
        category: "vowel"
      - label: "Ї ї"
        hint: "Їжак 🦔"
        category: "vowel"
      - label: "Й й"
        hint: "Йогурт 🍦"
        category: "consonant"
      - label: "К к"
        hint: "Кіт 🐈"
        category: "consonant"
      - label: "Л л"
        hint: "Лампа 💡"
        category: "consonant"
      - label: "М м"
        hint: "Мама 👩"
        category: "consonant"
      - label: "Н н"
        hint: "Ніс 👃"
        category: "consonant"
      - label: "О о"
        hint: "Око 👁️"
        category: "vowel"
      - label: "П п"
        hint: "Півень 🐓"
        category: "consonant"
      - label: "Р р"
        hint: "Риба 🐟"
        category: "consonant"
      - label: "С с"
        hint: "Сонце ☀️"
        category: "consonant"
      - label: "Т т"
        hint: "Тато 👨"
        category: "consonant"
      - label: "У у"
        hint: "Учень 🎒"
        category: "vowel"
      - label: "Ф ф"
        hint: "Фарби 🎨"
        category: "consonant"
      - label: "Х х"
        hint: "Хліб 🍞"
        category: "consonant"
      - label: "Ц ц"
        hint: "Цукерка 🍬"
        category: "consonant"
      - label: "Ч ч"
        hint: "Чашка ☕"
        category: "consonant"
      - label: "Ш ш"
        hint: "Шапка 🧢"
        category: "consonant"
      - label: "Щ щ"
        hint: "Щітка 🪥"
        category: "consonant"
      - label: "Ь ь"
        hint: "М'який знак (без звуку)"
        category: "special"
      - label: "Ю ю"
        hint: "Юшка 🍲"
        category: "vowel"
      - label: "Я я"
        hint: "Яблуко 🍎"
        category: "vowel"

  - id: group-sort-vowels-consonants
    type: quiz
    instruction: "Визначте категорію кожного звука."
    items:
      - question: "Звук [а] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 0
      - question: "Звук [к] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 1
      - question: "Звук [о] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 0
      - question: "Звук [м] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 1
      - question: "Звук [у] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 0
      - question: "Звук [т] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 1
      - question: "Звук [і] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 0
      - question: "Звук [р] — це:"
        options: ["Голосний", "Приголосний"]
        correct: 1

  - id: match-up-letters-sounds
    type: match-up
    instruction: "З'єднайте українську літеру зі звуком за схемою «Бачу — Чую»."
    items:
      - left: "А"
        right: "[а]"
      - left: "О"
        right: "[о]"
      - left: "У"
        right: "[у]"
      - left: "М"
        right: "[м]"
      - left: "К"
        right: "[к]"
      - left: "Н"
        right: "[н]"

  - id: fill-in-greeting-dialogue
    type: fill-in
    instruction: "Доповніть речення в діалозі-привітанні."
    items:
      - sentence: "Привіт! Як ____?"
        answer: "справи"
      - sentence: "____, дякую. А у тебе?"
        answer: "Добре"
      - sentence: "У мене все ____!"
        answer: "чудово"
      - sentence: "Привіт! Мене звати ____."
        answer: "Марко"
      - sentence: "Рада тебе ____!"
        answer: "бачити"
      - sentence: "Як ____ звати?"
        answer: "тебе"

workbook:
  - id: workbook-true-false-phonetics
    type: quiz
    instruction: "Визначте, чи є твердження правильним."
    items:
      - question: "Звуки ми бачимо й пишемо."
        options: ["Правда", "Неправда"]
        correct: 1
      - question: "Букви ми бачимо й пишемо."
        options: ["Правда", "Неправда"]
        correct: 0
      - question: "В українській абетці 33 літери."
        options: ["Правда", "Неправда"]
        correct: 0
      - question: "Голосні звуки вимовляються вільно."
        options: ["Правда", "Неправда"]
        correct: 0
      - question: "Приголосні звуки можна легко співати довгий час."
        options: ["Правда", "Неправда"]
        correct: 1
      - question: "Літера Ь (м’який знак) має власний окремий звук."
        options: ["Правда", "Неправда"]
        correct: 1

  - id: workbook-match-greetings
    type: match-up
    instruction: "З'єднайте репліки з логічними відповідями."
    items:
      - left: "Привіт!"
        right: "Привіт!"
      - left: "Як справи?"
        right: "Добре, дякую."
      - left: "Мене звати Марко."
        right: "Мене звати Софія."
      - left: "Радий тебе бачити!"
        right: "Рада тебе бачити!"
      - left: "Добрий день!"
        right: "Добрий день!"
      - left: "Як тебе звати?"
        right: "Мене звати Софія."

  - id: workbook-anagram-vocab
    type: anagram
    instruction: "Складіть слова з поданих літер."
    items:
      - answer: "мама"
        scrambled: "амма"
      - answer: "тато"
        scrambled: "отта"
      - answer: "дім"
        scrambled: "мід"
      - answer: "молоко"
        scrambled: "коломо"
      - answer: "привіт"
        scrambled: "івприт"
      - answer: "добре"
        scrambled: "ердоб"

  - id: workbook-group-sort-words
    type: group-sort
    instruction: "Розподіліть слова за початковим звуком."
    groups:
      - title: "Починається на голосний"
        items: ["око", "учень", "абетка", "іменник"]
      - title: "Починається на приголосний"
        items: ["мама", "тато", "ніс", "сон"]

  - id: workbook-unjumble-dialogue
    type: unjumble
    instruction: "Відновіть правильний порядок слів у реченнях."
    items:
      - answer: "Привіт! Як справи?"
        words: ["справи?", "Як", "Привіт!"]
      - answer: "Мене звати Софія."
        words: ["Софія.", "звати", "Мене"]
      - answer: "Рада тебе бачити."
        words: ["тебе", "бачити.", "Рада"]
      - answer: "У мене все добре."
        words: ["добре.", "все", "У", "мене"]
      - answer: "Як тебе звати?"
        words: ["звати?", "тебе", "Як"]
      - answer: "Добрий день усім!"
        words: ["усім!", "день", "Добрий"]

  - id: workbook-odd-one-out-sounds
    type: quiz
    instruction: "Знайдіть у кожному рядку зайвий звук (той, що не належить до групи)."
    items:
      - question: "[а], [о], [у], [к]"
        options: ["[а]", "[о]", "[у]", "[к]"]
        correct: 3
      - question: "[м], [н], [с], [і]"
        options: ["[м]", "[н]", "[с]", "[і]"]
        correct: 3
      - question: "[е], [и], [і], [т]"
        options: ["[е]", "[и]", "[і]", "[т]"]
        correct: 3
      - question: "[в], [р], [х], [о]"
        options: ["[в]", "[р]", "[х]", "[о]"]
        correct: 3
      - question: "[а], [у], [е], [м]"
        options: ["[а]", "[у]", "[е]", "[м]"]
        correct: 3
      - question: "[к], [т], [с], [а]"
        options: ["[к]", "[т]", "[с]", "[а]"]
        correct: 3
