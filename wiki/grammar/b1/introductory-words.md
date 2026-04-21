<!-- wiki-meta
slug: introductory-words-homogeneous-parts
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
    instruction: "Оберіть правильну відповідь на запитання про звуки та літери."
    items:
      - question: "Що ми чуємо і вимовляємо?"
        options: ["Звуки", "Літери", "Цифри"]
        correct: 0
      - question: "Що ми бачимо і пишемо?"
        options: ["Сни", "Літери", "Звуки"]
        correct: 1
      - question: "Скільки літер в українській абетці?"
        options: ["26", "38", "33"]
        correct: 2
      - question: "Скільки звуків в українській мові?"
        options: ["33", "38", "42"]
        correct: 1
      - question: "Чи правильно говорити «голосна літера»?"
        options: ["Так", "Ні", "Іноді"]
        correct: 1
      - question: "Що є «живою плоттю» мови?"
        options: ["Літера", "Слово", "Звук"]
        correct: 2

  - id: watch-and-repeat-vowels
    type: watch-and-repeat
    instruction: "Дивіться відео, слухайте та повторюйте звуки за Анною Огойко."
    items:
      - label: "А [а]"
        youtube_id: "hvB3VpcR3ZE"
        description: "Голосний звук [а], як у слові Абетка."
      - label: "У [у]"
        youtube_id: "VB1O6PmtYRU"
        description: "Голосний звук [у], як у слові Уля."
      - label: "Е [е]"
        youtube_id: "KFlsroBW0dk"
        description: "Голосний звук [е], як у слові Екран."
      - label: "И [и]"
        youtube_id: "W-1rCu0indE"
        description: "Голосний звук [и], як у слові Киця."
      - label: "І [і]"
        youtube_id: "Z9TH0H4ShGo"
        description: "Голосний звук [і], як у слові Іній."
      - label: "М [м]"
        youtube_id: "Ez95H4ibuJo"
        description: "Приголосний звук [м], як у слові Мама."
      - label: "Н [н]"
        youtube_id: "vNUfiKHPYaU"
        description: "Приголосний звук [н], як у слові Ніс."
      - label: "С [с]"
        youtube_id: "7UsFBgSL91E"
        description: "Приголосний звук [с], як у слові Сон."
      - label: "К [к]"
        youtube_id: "J7sGEI4-xJo"
        description: "Приголосний звук [к], як у слові Кіт."
      - label: "Л [л]"
        youtube_id: "v6-3Xg52Buk"
        description: "Приголосний звук [л], як у слові Ліс."
      - label: "Р [р]"
        youtube_id: "fMGsQ5KPQgg"
        description: "Приголосний звук [р], як у слові Риба."

  - id: letter-grid-alphabet
    type: letter-grid
    instruction: "Ознайомтеся з усіма літерами української абетки."
    items:
      - label: "А а"
        example: "Абетка"
        emoji: "📖"
        category: "голосна"
      - label: "Б б"
        example: "Бджола"
        emoji: "🐝"
        category: "приголосна"
      - label: "В в"
        example: "Вода"
        emoji: "💧"
        category: "приголосна"
      - label: "Г г"
        example: "Голос"
        emoji: "🗣️"
        category: "приголосна"
      - label: "Ґ ґ"
        example: "Ґудзик"
        emoji: "🔘"
        category: "приголосна"
      - label: "Д д"
        example: "Дім"
        emoji: "🏠"
        category: "приголосна"
      - label: "Е е"
        example: "Екран"
        emoji: "📺"
        category: "голосна"
      - label: "Є є"
        example: "Єнот"
        emoji: "🦝"
        category: "голосна (йотована)"
      - label: "Ж ж"
        example: "Життя"
        emoji: "🌱"
      - label: "З з"
        example: "Зебра"
        emoji: "🦓"
      - label: "И и"
        example: "Кит"
        emoji: "🐋"
        category: "голосна"
      - label: "І і"
        example: "Індик"
        emoji: "🦃"
        category: "голосна"
      - label: "Ї ї"
        example: "Їжак"
        emoji: "🦔"
        category: "голосна (йотована)"
      - label: "Й й"
        example: "Йогурт"
        emoji: "🍦"
      - label: "К к"
        example: "Кіт"
        emoji: "🐈"
      - label: "Л л"
        example: "Літак"
        emoji: "✈️"
      - label: "М м"
        example: "Мама"
        emoji: "👩"
      - label: "Н н"
        example: "Ніс"
        emoji: "👃"
      - label: "О о"
        example: "Око"
        emoji: "👁️"
        category: "голосна"
      - label: "П п"
        example: "Прапор"
        emoji: "🇺🇦"
      - label: "Р р"
        example: "Робот"
        emoji: "🤖"
      - label: "С с"
        example: "Сонце"
        emoji: "☀️"
      - label: "Т т"
        example: "Тато"
        emoji: "👨"
      - label: "У у"
        example: "Учень"
        emoji: "🧑‍🎓"
        category: "голосна"
      - label: "Ф ф"
        example: "Фарби"
        emoji: "🎨"
      - label: "Х х"
        example: "Хліб"
        emoji: "🍞"
      - label: "Ц ц"
        example: "Цукерка"
        emoji: "🍬"
      - label: "Ч ч"
        example: "Чай"
        emoji: "🍵"
      - label: "Ш ш"
        example: "Шапка"
        emoji: "🧢"
      - label: "Щ щ"
        example: "Щітка"
        emoji: "🪥"
      - label: "Ь ь"
        example: "М'якість"
        emoji: "☁️"
        category: "особлива"
      - label: "Ю ю"
        example: "Юшка"
        emoji: "🥣"
        category: "голосна (йотована)"
      - label: "Я я"
        example: "Яблуко"
        emoji: "🍎"
        category: "голосна (йотована)"

  - id: group-sort-vowels-consonants
    type: group-sort
    instruction: "Розподіліть подані звуки на голосні та приголосні."
    items:
      - item: "[а]"
        group: "Голосні"
      - item: "[о]"
        group: "Голосні"
      - item: "[у]"
        group: "Голосні"
      - item: "[е]"
        group: "Голосні"
      - item: "[и]"
        group: "Голосні"
      - item: "[і]"
        group: "Голосні"
      - item: "[к]"
        group: "Приголосні"
      - item: "[м]"
        group: "Приголосні"
      - item: "[т]"
        group: "Приголосні"
      - item: "[в]"
        group: "Приголосні"
      - item: "[н]"
        group: "Приголосні"
      - item: "[р]"
        group: "Приголосні"
      - item: "[с]"
        group: "Приголосні"
      - item: "[х]"
        group: "Приголосні"

  - id: match-up-letters-sounds
    type: match-up
    instruction: "З'єднайте українську літеру зі звуком, який вона позначає (за принципом «Бачу — Чую»)."
    items:
      - prompt: "А"
        answer: "[а]"
      - prompt: "О"
        answer: "[о]"
      - prompt: "У"
        answer: "[у]"
      - prompt: "М"
        answer: "[м]"
      - prompt: "К"
        answer: "[к]"
      - prompt: "Н"
        answer: "[н]"

  - id: fill-in-greeting-dialogue
    type: fill-in
    instruction: "Доповніть діалог-привітання, вставивши пропущені слова."
    items:
      - sentence: "— {Привіт}! Як справи?"
        answer: "Привіт"
      - sentence: "— Добре, дякую. А як у {тебе} справи?"
        answer: "тебе"
      - sentence: "— У мене все {нормально}."
        answer: "нормально"
      - sentence: "— {Чудово}! Радий тебе бачити."
        answer: "Чудово"
      - sentence: "— Як тебе {звати}?"
        answer: "звати"
      - sentence: "— Мене звати {Марко}."
        answer: "Марко"

workbook:
  - id: workbook-true-false-phonetics
    type: true-false
    instruction: "Визначте, чи є твердження правильним (Правда) чи неправильним (Неправда)."
    items:
      - statement: "Звуки ми бачимо й пишемо."
        answer: false
      - statement: "Букви ми бачимо й пишемо."
        answer: true
      - statement: "В українській абетці 33 літери."
        answer: true
      - statement: "Голосні звуки вимовляються вільно, без перешкод."
        answer: true
      - statement: "Приголосні звуки можна легко співати довгий час."
        answer: false
      - statement: "Літера Ь (м’який знак) має власний окремий звук."
        answer: false

  - id: workbook-match-greetings
    type: match-up
    instruction: "З'єднайте репліки з логічними відповідями."
    items:
      - prompt: "Привіт!"
        answer: "Привіт!"
      - prompt: "Як справи?"
        answer: "Добре, дякую."
      - prompt: "Мене звати Марко."
        answer: "Мене звати Софія."
      - prompt: "Радий тебе бачити!"
        answer: "Рада тебе бачити!"
      - prompt: "Добрий день!"
        answer: "Добрий день!"
      - prompt: "Як тебе звати?"
        answer: "Мене звати Марко."

  - id: workbook-anagram-vocab
    type: anagram
    instruction: "Складіть слова з поданих літер."
    items:
      - word: "мама"
        scrambled: "амма"
      - word: "тато"
        scrambled: "отта"
      - word: "дім"
        scrambled: "мід"
      - word: "молоко"
        scrambled: "колом о"
      - word: "привіт"
        scrambled: "івприт"
      - word: "добре"
        scrambled: "ердоб"

  - id: workbook-group-sort-words
    type: group-sort
    instruction: "Розподіліть слова за початковим звуком (голосний чи приголосний)."
    items:
      - item: "око"
        group: "Починається на голосний"
      - item: "учень"
        group: "Починається на голосний"
      - item: "абетка"
        group: "Починається на голосний"
      - item: "іменник"
        group: "Починається на голосний"
      - item: "мама"
        group: "Починається на приголосний"
      - item: "тато"
        group: "Починається на приголосний"
      - item: "ніс"
        group: "Починається на приголосний"
      - item: "сон"
        group: "Починається на приголосний"

  - id: workbook-unjumble-dialogue
    type: unjumble
    instruction: "Відновіть правильний порядок слів у реченнях."
    items:
      - sentence: "Привіт! Як справи?"
        scrambled: ["Як", "справи?", "Привіт!"]
      - sentence: "Мене звати Софія."
        scrambled: ["Софія.", "звати", "Мене"]
      - sentence: "Рада тебе бачити."
        scrambled: ["тебе", "Рада", "бачити."]
      - sentence: "У мене все добре."
        scrambled: ["все", "У", "мене", "добре."]
      - sentence: "Як тебе звати?"
        scrambled: ["звати?", "тебе", "Як"]
      - sentence: "Добрий день усім!"
        scrambled: ["усім!", "день", "Добрий"]

  - id: workbook-odd-one-out-sounds
    type: odd-one-out
    instruction: "Знайдіть у кожному рядку зайвий звук (той, що не належить до групи)."
    items:
      - options: ["[а]", "[о]", "[у]", "[к]"]
        correct: 3
      - options: ["[м]", "[н]", "[с]", "[і]"]
        correct: 3
      - options: ["[е]", "[и]", "[і]", "[т]"]
        correct: 3
      - options: ["[в]", "[р]", "[х]", "[о]"]
        correct: 3
      - options: ["[а]", "[у]", "[е]", "[м]"]
        correct: 3
      - options: ["[к]", "[т]", "[с]", "[а]"]
        correct: 3
