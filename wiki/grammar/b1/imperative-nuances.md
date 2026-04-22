<!-- wiki-meta
slug: imperative-nuances
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
    instruction: "Оберіть правильну відповідь про звуки та літери"
    items:
      - question: "Що ми чуємо і вимовляємо?"
        options: ["звуки", "літери", "слова"]
        correct: 0
      - question: "Що ми бачимо і пишемо?"
        options: ["звуки", "літери", "речення"]
        correct: 1
      - question: "Скільки літер в українській абетці?"
        options: ["26", "30", "33"]
        correct: 2
      - question: "Скільки звуків в українській мові?"
        options: ["33", "38", "42"]
        correct: 1
      - question: "Чи правильно говорити «голосна літера»?"
        options: ["Так", "Ні", "Лише в школі"]
        correct: 1
      - question: "Яка літера не має власного звуку?"
        options: ["Й", "Ь", "Ї"]
        correct: 1

  - id: watch-and-repeat-vowels
    type: watch-and-repeat
    instruction: "Послухайте і повторіть звуки разом з Анною Огойко"
    items:
      - video: "hvB3VpcR3ZE"
        letter: "А"
        word: "акула"
        sound: "[а]"
      - video: "VB1O6PmtYRU"
        letter: "У"
        word: "удав"
        sound: "[у]"
      - video: "KFlsroBW0dk"
        letter: "Е"
        word: "екран"
        sound: "[е]"
      - video: "W-1rCu0indE"
        letter: "И"
        word: "кит"
        sound: "[и]"
      - video: "Z9TH0H4ShGo"
        letter: "І"
        word: "іграшка"
        sound: "[і]"
      - video: "Ez95H4ibuJo"
        letter: "М"
        word: "мама"
        sound: "[м]"
      - video: "vNUfiKHPYaU"
        letter: "Н"
        word: "ніс"
        sound: "[н]"
      - video: "7UsFBgSL91E"
        letter: "С"
        word: "слон"
        sound: "[с]"
      - video: "J7sGEI4-xJo"
        letter: "К"
        word: "кіт"
        sound: "[к]"
      - video: "v6-3Xg52Buk"
        letter: "Л"
        word: "лимон"
        sound: "[л]"
      - video: "fMGsQ5KPQgg"
        letter: "Р"
        word: "риба"
        sound: "[р]"

  - id: letter-grid-alphabet
    type: letter-grid
    instruction: "Вивчіть українську абетку"
    items:
      - letter: "А а"
        word: "акула"
        emoji: "🦈"
        category: "голосний"
      - letter: "Б б"
        word: "білка"
        emoji: "🐿️"
        category: "приголосний"
      - letter: "В в"
        word: "вовк"
        emoji: "🐺"
        category: "приголосний"
      - letter: "Г г"
        word: "гора"
        emoji: "⛰️"
        category: "приголосний"
      - letter: "Ґ ґ"
        word: "ґанок"
        emoji: "🏚️"
        category: "приголосний"
      - letter: "Д д"
        word: "дім"
        emoji: "🏠"
        category: "приголосний"
      - letter: "Е е"
        word: "екран"
        emoji: "📺"
        category: "голосний"
      - letter: "Є є"
        word: "єнот"
        emoji: "🦝"
        category: "голосний"
      - letter: "Ж ж"
        word: "жук"
        emoji: "🪲"
        category: "приголосний"
      - letter: "З з"
        word: "зебра"
        emoji: "🦓"
        category: "приголосний"
      - letter: "И и"
        word: "кит"
        emoji: "🐳"
        category: "голосний"
      - letter: "І і"
        word: "іграшка"
        emoji: "🧸"
        category: "голосний"
      - letter: "Ї ї"
        word: "їжак"
        emoji: "🦔"
        category: "голосний"
      - letter: "Й й"
        word: "йогурт"
        emoji: "🥛"
        category: "приголосний"
      - letter: "К к"
        word: "кіт"
        emoji: "🐈"
        category: "приголосний"
      - letter: "Л л"
        word: "лимон"
        emoji: "🍋"
        category: "приголосний"
      - letter: "М м"
        word: "мама"
        emoji: "👩"
        category: "приголосний"
      - letter: "Н н"
        word: "ніс"
        emoji: "👃"
        category: "приголосний"
      - letter: "О о"
        word: "око"
        emoji: "👁️"
        category: "голосний"
      - letter: "П п"
        word: "півень"
        emoji: "🐓"
        category: "приголосний"
      - letter: "Р р"
        word: "риба"
        emoji: "🐟"
        category: "приголосний"
      - letter: "С с"
        word: "слон"
        emoji: "🐘"
        category: "приголосний"
      - letter: "Т т"
        word: "тигр"
        emoji: "🐅"
        category: "приголосний"
      - letter: "У у"
        word: "удав"
        emoji: "🐍"
        category: "голосний"
      - letter: "Ф ф"
        word: "фламінго"
        emoji: "🦩"
        category: "приголосний"
      - letter: "Х х"
        word: "хліб"
        emoji: "🍞"
        category: "приголосний"
      - letter: "Ц ц"
        word: "цукор"
        emoji: "🧊"
        category: "приголосний"
      - letter: "Ч ч"
        word: "черепаха"
        emoji: "🐢"
        category: "приголосний"
      - letter: "Ш ш"
        word: "шапка"
        emoji: "🧢"
        category: "приголосний"
      - letter: "Щ щ"
        word: "щітка"
        emoji: "🪥"
        category: "приголосний"
      - letter: "Ь ь"
        word: "день"
        emoji: "☁️"
        category: "особливий"
      - letter: "Ю ю"
        word: "юшка"
        emoji: "🥣"
        category: "голосний"
      - letter: "Я я"
        word: "яблуко"
        emoji: "🍎"
        category: "голосний"

  - id: group-sort-vowels-consonants
    type: group-sort
    instruction: "Розподіліть звуки на голосні та приголосні"
    groups:
      - name: "Голосні звуки"
        items: ["[а]", "[о]", "[у]", "[е]", "[и]", "[і]"]
      - name: "Приголосні звуки"
        items: ["[к]", "[м]", "[т]", "[в]", "[н]", "[р]", "[с]", "[х]"]

  - id: match-up-letters-sounds
    type: match-up
    instruction: "З'єднайте літеру зі звуком, який вона позначає"
    items:
      - ["А", "[а]"]
      - ["О", "[о]"]
      - ["У", "[у]"]
      - ["М", "[м]"]
      - ["К", "[к]"]
      - ["Н", "[н]"]

  - id: fill-in-greeting-dialogue
    type: fill-in
    instruction: "Доповніть діалог-привітання"
    items:
      - sentence: "— Привіт! Як {справи}?"
      - sentence: "— {Добре}, дякую. А у тебе?"
      - sentence: "— {Чудово}!"
      - sentence: "— Як тебе {звати}?"
      - sentence: "— Мене звати Марко. А {тебе}?"
      - sentence: "— Рада тебе {бачити}!"

workbook:
  - id: workbook-anagrams
    type: anagram
    instruction: "Складіть слово з літер"
    items:
      - word: "мама"
        scrambled: "аамм"
      - word: "тато"
        scrambled: "атто"
      - word: "око"
        scrambled: "оок"
      - word: "дім"
        scrambled: "ідм"
      - word: "ніс"
        scrambled: "існ"
      - word: "сон"
        scrambled: "онс"

  - id: workbook-count-syllables
    type: count-syllables
    instruction: "Порахуйте склади у словах (пам'ятайте: скільки голосних, стільки й складів)"
    items:
      - word: "мама"
        answer: 2
      - word: "молоко"
        answer: 3
      - word: "добре"
        answer: 2
      - word: "привіт"
        answer: 2
      - word: "чудово"
        answer: 3
      - word: "нормально"
        answer: 3

  - id: workbook-odd-one-out
    type: odd-one-out
    instruction: "Знайдіть зайвий звук у рядку"
    items:
      - sequence: ["а", "о", "у", "м"]
        answer: "м"
      - sequence: ["к", "т", "с", "і"]
        answer: "і"
      - sequence: ["е", "и", "і", "н"]
        answer: "н"
      - sequence: ["р", "в", "х", "а"]
        answer: "а"
      - sequence: ["я", "ю", "є", "п"]
        answer: "п"
      - sequence: ["м", "н", "л", "у"]
        answer: "у"

  - id: workbook-match-greetings
    type: match-up
    instruction: "З'єднайте фразу з логічною відповіддю"
    items:
      - ["Привіт!", "Привіт!"]
      - ["Як справи?", "Добре, дякую."]
      - ["Мене звати Марко.", "Мене звати Софія."]
      - ["Радий тебе бачити!", "Рада тебе бачити!"]
      - ["Добрий день!", "Добрий день!"]
      - ["Як тебе звати?", "Мене звати Марко."]

  - id: workbook-unjumble-alphabet
    type: unjumble
    instruction: "Відновіть правильний алфавітний порядок"
    items:
      - sentence: "А Б В"
        scrambled: "В А Б"
      - sentence: "Г Ґ Д"
        scrambled: "Ґ Д Г"
      - sentence: "Е Є Ж"
        scrambled: "Ж Е Є"
      - sentence: "З И І"
        scrambled: "І З И"
      - sentence: "Ї Й К"
        scrambled: "К Ї Й"
      - sentence: "Л М Н"
        scrambled: "Н Л М"

  - id: workbook-true-false-rules
    type: true-false
    instruction: "Визначте, чи є твердження правильним"
    items:
      - question: "Звуки ми бачимо й пишемо."
        answer: false
      - question: "Букви ми бачимо й пишемо."
        answer: true
      - question: "В українській абетці 33 літери."
        answer: true
      - question: "Голосні звуки вимовляються вільно."
        answer: true
      - question: "Приголосні звуки можна легко співати."
        answer: false
      - question: "Літера Ь має власний звук."
        answer: false
