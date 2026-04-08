<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-cases.yaml` file for module **39: Контрольна точка: Відмінки та множина** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: nominative-plural-forms -->`
- `<!-- INJECT_ACTIVITY: genitive-plural-challenge -->`
- `<!-- INJECT_ACTIVITY: quantity-genitive-pl -->`
- `<!-- INJECT_ACTIVITY: case-trigger-quiz -->`
- `<!-- INJECT_ACTIVITY: group-sort-noun-cases -->`
- `<!-- INJECT_ACTIVITY: mixed-error-hunt -->`
- `<!-- INJECT_ACTIVITY: writing-ideal-day -->`
- `<!-- INJECT_ACTIVITY: dialogue-gap-fill -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed case drill — complete sentences requiring all 7 cases, singular and
    plural
  items: 8
  type: fill-in
- focus: Error correction — identify and fix case errors in sentences
  items: 8
  type: quiz
- focus: Sort noun forms by case (Nom., Gen., Dat., Acc., Instr., Loc., Voc.)
  items: 8
  type: group-sort
- focus: Find and fix mixed case errors in sentences — wrong endings after prepositions,
    animate/inanimate confusion, Gen.Pl. mistakes
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- самоперевірка (self-check)
- впевнено (confidently)
- вихідний день (day off)
required:
- перевірка (check, review)
- контрольна точка (checkpoint)
- завдання (task, exercise)
- помилка (error, mistake)
- виправити (to correct)
- відмінок (grammatical case)
- множина (plural)
- однина (singular)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ: Весільний квест та компас відмінків

Ласкаво просимо до фінального випробування рівня A2! Ця **контрольна точка** (checkpoint) — час перевірити, як добре ви орієнтуєтеся у світі відмінків та множини. Це ваша головна **перевірка** (review). Ви вже знаєте, як іменники змінюють свої закінчення залежно від їхньої ролі в реченні. Ваш **компас відмінків** (case compass) з модуля 31 залишається головним інструментом навігації. Ми синтезуємо все, що ви знаєте про такі категорії, як **однина** (singular) та **множина** (plural). 

> **Наречена:** **Олено!** Ти маєш хвилину? *(Olena! Do you have a minute?)*
> **Подруга:** Привіт! Так, звичайно. Що сталося? *(Hi! Yes, of course. What happened?)*
> **Наречена:** Я планую весілля. Це такий стрес! Я пишу **запрошення для гостей**. *(I am planning a wedding. It is such stress! I am writing invitations for the guests.)*
> **Подруга:** О, це чудово! Я вже маю **подарунок нареченій**. *(Oh, that is wonderful! I already have a gift for the bride.)*
> **Наречена:** Дякую! Я так хочу, щоб усе було ідеально. Коли я **бачу наречену** в кіно, вона завжди спокійна. *(Thank you! I want everything to be perfect so much. When I see a bride in a movie, she is always calm.)*
> **Подруга:** Ти теж будеш спокійною. Уяви: красивий ресторан, музика, ти танцюєш **з молодятами**... Ой, тобто зі своїм чоловіком! *(You will be calm too. Imagine: a beautiful restaurant, music, you are dancing with the newlyweds... Oh, I mean with your husband!)*
> **Наречена:** Так, **на весіллі** всі будуть танцювати. *(Yes, at the wedding everyone will dance.)*

This dialogue naturally uses all seven Ukrainian cases. We see the Vocative (**Олено**), Nominative (**весілля**), Genitive (**для гостей**), Dative (**нареченій**), Accusative (**наречену**), Instrumental (**з молодятами**), and Locative (**на весіллі**). Every noun adapts to its specific environment.

## Частина 1: Форми множини (Part 1: Plural Forms)

First, consider the Nominative plural — the dictionary form for multiple items. The ending depends on the noun's gender and whether its stem ends in a hard or soft consonant. For the hard group, masculine and feminine nouns take **-и**: **столи** (tables), **книжки** (books). Soft group nouns take **-і** or **-ї**: **дні** (days), **землі** (lands). Neuter nouns change completely, taking **-а** or **-я**: **вікна** (windows), **моря** (seas). Remember the "high priority trio" of irregular plurals: **друг** (friend) becomes **друзі**, **людина** (person) becomes **люди**, and **дитина** (child) becomes **діти**.
- Тут живуть мої **друзі**. (My friends live here.)
- Це нові **столи** та **книжки**. (These are new tables and books.)
- У кімнаті великі **вікна**. (There are big windows in the room.)
- Мої **батьки** дуже добрі. (My parents are very kind.)

The Genitive plural is the "wall" that many learners hit. It is the hardest form, but also the most common. For feminine and neuter nouns, the ending simply disappears — this is the zero ending. **Книга** (book) becomes **книг**, and **місто** (city) becomes **міст**. Most masculine nouns take the **-ів** ending: **студент** (student) becomes **студентів**. Sometimes, dropping the ending creates a difficult consonant cluster. To fix this, Ukrainian inserts a "fleeting vowel" (**вставний голосний**). **Земля** (land) becomes **земель**, **вікно** (window) becomes **вікон**, and **дошка** (board) becomes **дощок**.
- У мене немає **книг**. (I do not have books.)
- У групі багато **студентів**. (There are many students in the group.)
- Я бачу п'ять **вікон**. (I see five windows.)
- На столі немає **тарілок**. (There are no plates on the table.)

Some nouns have a fixed number. They are either Pluralia Tantum (plural only) or Singularia Tantum (singular only). Everyday items that consist of two parts are often plural-only: **гроші** (money), **окуляри** (glasses), **штани** (pants), **двері** (doors). Geographical names like **Карпати** (Carpathians) are also plural-only. Remember that verbs and adjectives must agree with them in the plural: "Гроші **були** на столі" (The money was on the table — literally "they were"). Some nouns are collective singulars, like **молодь** (youth) or **людство** (humanity).
- Мої нові **штани** дуже зручні. (My new pants are very comfortable.)
- **Гроші** лежать у сумці. (The money lies in the bag.)
- Сучасна **молодь** любить технології. (Modern youth loves technology.)
- Вона відчиняє великі **двері**. (She opens the big doors.)

A few nouns use special suffixal plurals. Baby animals and some abstract concepts belong to the fourth declension and add **-ат-** / **-ят-** or **-ен-** in the plural. **Курча** (chick) becomes **курчата**, **кошеня** (kitten) becomes **кошенята**, and **ім'я** (name) becomes **імена**. Ukrainian also preserves remnants of the ancient dual number. "Double body parts" take the unique **-има** ending in the Instrumental case: **очима** (with eyes), **плечима** (with shoulders), **вушима** (with ears).
- У дворі граються **кошенята**. (Kittens are playing in the yard.)
- Я бачу це своїми **очима**. (I see this with my own eyes.)
- Які ваші **імена**? (What are your names?)

The good news is that the Dative, Instrumental, and Locative plural endings are highly consistent across all genders. They are much easier to memorize than the Genitive plural. Dative takes **-ам** / **-ям**, Instrumental takes **-ами** / **-ями**, and Locative takes **-ах** / **-ях**.
- Я даю їжу **кошенятам**. (I give food to the kittens.)
- Ми гуляємо з **друзями**. (We are walking with friends.)
- Книги лежать на **столах**. (The books lie on the tables.)

<!-- INJECT_ACTIVITY: nominative-plural-forms -->
<!-- INJECT_ACTIVITY: genitive-plural-challenge -->
<!-- INJECT_ACTIVITY: quantity-genitive-pl -->

## Частина 2: Який відмінок? (Part 2: Which Case?)

Choosing the right **відмінок** (case) depends heavily on verb government. Every verb demands a specific case from its object. The verb **допомагати** (to help) requires the Dative case: "Я допомагаю **мамі**" (I help my mom). The verb **бачити** (to see) requires the Accusative case: "Я бачу **маму**" (I see my mom). **Користуватися** (to use) triggers the Instrumental case: "Я користуюся **телефоном**" (I use a phone). Always remember the contrast between a direct object (Accusative) and absence or quantity (Genitive). "Я маю **плани**" (I have plans - Accusative direct object). But negated: "Я не маю **планів**" (I do not have plans - Genitive of negation).
- Ми часто дякуємо **батькам**. (We often thank our parents.)
- Вони бачать високі **дерева**. (They see tall trees.)
- Він користується новим **ноутбуком**. (He uses a new laptop.)
- Вона дарує квіти **вчителю**. (She gives flowers to the teacher.)

Prepositions are your next major navigation tool. Double-case prepositions change their meaning based on the case. **У** or **в** with the Locative case means static location: "Я живу в **місті**" (I live in the city). With the Accusative case, it means direction: "Я їду в **місто**" (I am going into the city). The preposition **на** works the exact same way. The preposition **з** means origin when used with the Genitive: "Я з **України**" (I am from Ukraine). But it means company when used with the Instrumental: "Я йду з **братом**" (I am walking with my brother). The preposition **по** is used for movement along a surface or a schedule in the Locative: "йти по **вулицях**" (to walk along the streets), "по **суботах**" (on Saturdays).
- Книги лежать на **полиці**. (The books lie on the shelf.)
- Ми кладемо книги на **полицю**. (We are putting the books onto the shelf.)
- Вона п'є каву з **молоком**. (She drinks coffee with milk.)
- Вони гуляють по **парку**. (They walk through the park.)

Special constructions also trigger specific cases. Time expressions often use the Accusative or Locative. Days of the week take the Accusative: **у четвер** (on Thursday). Hours of the day take the Locative: **о п'ятій годині** (at five o'clock). When describing appearance or characteristics, use the Locative or Instrumental: **хлопець у светрі** (the boy in the sweater), **дівчина з карими очима** (the girl with brown eyes). For path and means of transport, use the Instrumental without a preposition: **летіти літаком** (to fly by plane), **йти лісом** (to walk through the forest).
- Ми зустрінемося **у п'ятницю**. (We will meet on Friday.)
- Це **чоловік у капелюсі**. (This is the man in the hat.)
- Вони подорожують **поїздом**. (They travel by train.)

Error analysis is a crucial skill. You must distinguish between similar endings. For inanimate nouns, the Nominative and Accusative plural look identical: "Дерев'яні **столи** стоять тут" (Wooden tables stand here - Nominative subject). "Я бачу дерев'яні **столи**" (I see wooden tables - Accusative object). For animate nouns, the Accusative plural looks exactly like the Genitive plural: "Я бачу **друзів**" (I see friends). Watch out for direct translations that use the wrong case. In Ukrainian, **чекати** (to wait) takes the Genitive or Accusative, never the Dative. **Дякувати** (to thank) takes the Dative, never the Accusative.
- Я бачу нові **будинки**. (I see new buildings.)
- Вона любить своїх **котів**. (She loves her cats.)
- Ми чекаємо **автобуса**. (We are waiting for the bus.)

Read this short text about a trip to identify cases in context:
"Минулого року ми їздили в **Карпати** (Accusative - direction). У **Карпатах** (Locative - location) дуже красиво. Ми гуляли зеленими **лісами** (Instrumental - path) і пили воду з гірських **річок** (Genitive - origin). Наші **друзі** (Nominative - subject) робили багато **фотографій** (Genitive - quantity). Ми розповідали **людям** (Dative - recipient) про нашу подорож."
Notice how "у Карпатах" shows location, while "в Карпати" shows direction. Every noun form has a specific trigger.

<!-- INJECT_ACTIVITY: case-trigger-quiz -->
<!-- INJECT_ACTIVITY: group-sort-noun-cases -->
<!-- INJECT_ACTIVITY: mixed-error-hunt -->

## Частина 3: Вільне мовлення (Part 3: Free Production)

Guided writing requires strategy. Ваше **завдання** (task) — "Опишіть свій ідеальний **вихідний день**" (Describe your ideal day off). Building a coherent narrative requires using the full case spectrum. Start with your destination using the Accusative: "У суботу я їду в **центр**" (On Saturday I go to the center). Mention your company using the Instrumental: "Я гуляю з **друзями**" (I walk with friends). Describe your activities using the Accusative or Instrumental: "Я бачу красиві **будівлі**" (I see beautiful buildings), "Я малюю **олівцем**" (I draw with a pencil). Finally, mention what you eat using the Genitive for quantities or Accusative for specific items: "Я купую багато **яблук**" (I buy many apples), "Я їм смачну **піцу**" (I eat a tasty pizza).
- Мій ідеальний **вихідний день** починається пізно. (My ideal day off starts late.)
- У неділю я читаю **книгу**. (On Sunday I read a book.)
- Ми йдемо в **парк**. (We go to the park.)

Dialogue completion requires strict logical agreement. When answering a question, you must provide a natural short answer that respects the case of the question word. The question "Кого?" (Whom? - Accusative/Genitive animate) requires an Accusative or Genitive response. "Кому?" (To whom? - Dative) requires a Dative response.
> **Максим:** З ким ти розмовляв? *(With whom were you talking?)*
> **Анна:** З **батьками**. *(With parents.)*
> **Максим:** Про що ви говорили? *(About what were you talking?)*
> **Анна:** Про **плани** на вихідні. *(About plans for the weekend.)*
> **Максим:** Кому ви будете дзвонити завтра? *(To whom will you call tomorrow?)*
> **Анна:** Нашим **родичам**. *(To our relatives.)*

A critical focus is the living Vocative case (**Кличний відмінок**). It is not an archaic relic; it is a vital part of modern Ukrainian communication. Whenever you address someone directly, you must use it. For singular names and nouns, use endings like -о, -е, or -ю: **Мамо** (Mom!), **Оксано** (Oksana!), **пане** (sir!). For plural, the Vocative usually matches the Nominative: **Друзі!** (Friends!), **Колеги!** (Colleagues!). Using the Vocative is a sign of cultured, natural Ukrainian speech.
- **Брате**, допоможи мені, будь ласка. (Brother, help me, please.)
- Добрий день, **пане** Іване! (Good day, Mr. Ivan!)
- Шановні **колеги**, почнемо нашу зустріч. (Respected colleagues, let's begin our meeting.)
- **Сергію**, де ти був? (Serhiy, where were you?)

A letter to a friend synthesizes everything. This models how to connect thoughts across sentences while maintaining case agreement and logical flow.
"Привіт, **Олено**! Як твої **справи**? Я зараз у **Львові**. Це чудове **місто** з красивими **вулицями**. Учора я гуляла з **друзями** по **центру**. Ми бачили багато старих **будівель** і пили каву в затишному **кафе**. Я купила **сувеніри** для **батьків**. Завтра ми їдемо в **гори**. Я чекаю твого **листа**!"
Notice how every noun seamlessly connects to its verb or preposition. This is the goal of your free production practice.

<!-- INJECT_ACTIVITY: writing-ideal-day -->
<!-- INJECT_ACTIVITY: dialogue-gap-fill -->

## Підсумок

You have reached the end of the A2 case checkpoint. Take a moment for **самоперевірка** (self-check) to ensure you can use these forms **впевнено** (confidently). Ask yourself these questions:
- Чи можу я **впевнено** утворити Родовий відмінок множини (**книг**, **столів**)? (Can I confidently form the Genitive plural?)
- Чи пам'ятаю я нерегулярні форми (**люди**, **діти**, **друзі**)? (Do I remember the irregular forms?)
- Чи знаю я, які відмінки вимагають прийменники "на", "в", "з", "по"? (Do I know which cases the prepositions require?)
- Чи використовую я Кличний відмінок під час звертання? (Do I use the Vocative case during direct address?)

Якщо ви бачите **помилку** (error), ви знаєте, як її **виправити** (to correct). You have now mastered the skeleton of the Ukrainian language. The case system is the foundation. You are ready to move to A2.6 to add the flesh of adjectives and verbs of motion to this strong structure!
```

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-cases
level: a2

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 39/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
