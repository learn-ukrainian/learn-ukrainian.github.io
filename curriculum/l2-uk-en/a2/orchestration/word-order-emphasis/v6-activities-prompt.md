<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/word-order-emphasis.yaml` file for module **50: Порядок слів і наголос у реченні** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-identify-rheme -->`
- `<!-- INJECT_ACTIVITY: match-question-answer -->`
- `<!-- INJECT_ACTIVITY: group-sort-neutral-marked -->`
- `<!-- INJECT_ACTIVITY: fill-in-reorder-words-to-create-the-correct-emphasis-for-a-given-context -->`
- `<!-- INJECT_ACTIVITY: error-correction-fix-sentences-where-word-order-creates-unintended-emphasis -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify the rheme (new information) in each sentence based on the question
    it answers
  items: 8
  type: quiz
- focus: Match questions with the correctly word-ordered answers (Хто приїхав? → Приїхав
    Тарас, not Тарас приїхав)
  items: 8
  type: match-up
- focus: Reorder words to create the correct emphasis for a given context (the book
    / I / already / read → for emphasis on "the book")
  items: 8
  type: fill-in
- focus: Sort sentences into neutral word order vs. marked/emphatic word order
  items: 8
  type: group-sort
- focus: Fix sentences where word order creates unintended emphasis (e.g., answering
    "What did you buy?" with *Каву купив я instead of Я купив каву)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- виділяти (to highlight, to single out)
- означення (attribute, modifier)
- нейтральний (neutral)
- емфатичний (emphatic)
- акцент (accent, emphasis)
required:
- порядок (order)
- речення (sentence)
- тема (theme, topic (linguistics))
- рема (rheme, new information)
- наголос (stress, emphasis)
- інверсія (inversion)
- контраст (contrast)
- підкреслювати (to emphasize, to underline)
- початок (beginning)
- кінець (end)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ та Діалог 1

В українській мові порядок слів називають **вільним** *(free)*. Але це не означає, що слова стоять хаотично. Порядок слів — це важливий інструмент. В англійській мові граматика диктує, де стоїть підмет, а де присудок. В українській мові ми використовуємо **порядок слів** *(word order)*, щоб передати зміст та емоції. Слово, яке стоїть на початку або в кінці речення, має найбільше значення.

Оленка та Марійка — **сусідки по кімнаті** *(roommates)*. Вони ділять домашні обов'язки. Зверніть увагу, як змінюється порядок слів, коли вони говорять про нову інформацію.

> — **Оленка:** Хто помив посуд? *(Who washed the dishes?)*
> — **Марійка:** Посуд помив Тарас. А підлогу? *(Taras washed the dishes. And the floor?)*
> — **Оленка:** Підлогу ще ніхто не помив. Добре, підлогу помию я. *(No one has washed the floor yet. Okay, I will wash the floor.)*

Оленка запитує про посуд. Для Марійки посуд — це вже відома інформація, тобто **тема** *(theme)*. Тому слово «посуд» стоїть на початку речення. А слово «Тарас» — це нова інформація, або **рема** *(rheme)*. Тому це слово стоїть у кінці речення. Так само працює слово «підлога».

## Тема і рема: що відоме, що нове?

Кожне речення має дві частини. Це те, про що ми говоримо, і що повідомляємо. У лінгвістиці їх називають **тема** *(theme)* і **рема** *(rheme)*. Тема — це відома інформація, яку співрозмовник уже знає. Рема — це нова інформація, або **фокус повідомлення** *(focus of the message)*. Українське речення зазвичай рухається від відомого до нового. Ми починаємо зі знайомих фактів і закінчуємо головною новиною.

This creates an important linguistic principle called "end focus". У нейтральному мовленні найважливіша інформація стоїть у кінці речення. Саме там знаходиться рема. Порівняйте два варіанти. Перший: «Тарас купив книгу». Тут фокус падає на слово «книгу». Співрозмовник знає Тараса, але не знає, що він купив. Другий: «Книгу купив Тарас». Тут рема — це слово «Тарас». Співрозмовник знає про покупку книги, але не знає покупця. The word at the very end of the sentence naturally carries the main communicative weight.

You can easily identify the rheme by asking a simple question. Українська відповідь завжди ставить нову інформацію в кінець. Уявіть питання: «Хто купив книгу?». Слово «книга» вже прозвучало, тому це тема. Нова інформація — це людина. Тому правильна відповідь: «Книгу купив Тарас». Тепер уявіть інше питання: «Що купив Тарас?». Тут відома інформація — це Тарас. Тому відповідь буде іншою: «Тарас купив книгу». Слова змінюють позиції залежно від питання.

Why can Ukrainian do this so effortlessly? Відповідь ховається у відмінках. In English, strict word order tells you exactly who is the subject and who is the object. В українській мові граматичну роль показують **закінчення** *(endings)*. Слово «книгу» має закінчення знахідного відмінка **-у**. Це слово завжди буде додатком. Нам не важливо, де воно стоїть. Саме відмінки дозволяють нам вільно переставляти слова.

There is also a psychological reason for this order. Люди інтуїтивно ставлять нові або довгі поняття в кінець речення. Це допомагає співрозмовнику легше сприймати інформацію. Спочатку людина чує знайомі слова, які готують ґрунт. Потім вона отримує свіжий **акцент** *(accent)*. Такий **порядок слів** *(word order)* робить українське мовлення виразним інструментом.

<!-- INJECT_ACTIVITY: quiz-identify-rheme --> [quiz, Identify the rheme (new information) based on the context/question, 8 items]

## Прямий порядок слів

Українська мова має базовий, або **прямий порядок слів** *(direct word order)*. Це нейтральна схема: **підмет** *(subject)*, **присудок** *(predicate)*, **додаток** *(object)*. Ми використовуємо прямий порядок слів для констатації фактів. Він часто звучить у новинах, наукових текстах або офіційних повідомленнях. Наприклад: «Студент читає текст». «Мама готує вечерю». Тут немає жодних емоцій. Це просто інформація. When you want to state a simple fact without emphasizing any specific part, use this SVO structure. It is the safest choice for beginners.

Де стоїть **означення** *(attribute/adjective)*? У нейтральному реченні прикметник завжди стоїть перед іменником. Ми кажемо: «цікава книга», «велике місто», «холодний вітер». Це звичайна характеристика предмета. Але будьте обережні, коли змінюєте порядок. Якщо ви поставите прикметник після іменника, він стане присудком. Порівняйте: «Це велике місто» *(This is a big city)*. Але: «Місто — велике» *(The city IS big)*. У другому випадку ми робимо акцент на розмірі міста. The position of the adjective completely changes the grammatical structure of the sentence.

Тепер поговоримо про **обставини** *(adverbial modifiers)*. Вони показують, як саме відбувається дія. В українській мові прислівник може стояти перед дієсловом або після нього. Обидва варіанти правильні. Ви можете сказати: «Він добре працює» або «Він працює добре». Є невелика різниця. Коли прислівник стоїть у кінці, він має трохи більше ваги. Це знову правило реми. Moving the adverb to the very end of the sentence naturally makes it the focus of your statement.

Слова, які позначають час або місце, дуже рухливі. Їхня позиція залежить від вашої мети. Часто вони стоять на початку речення. Це створює контекст для всієї ситуації. Наприклад: «Вчора я був удома» *(Yesterday I was at home)*. «У Києві йде дощ» *(It is raining in Kyiv)*. Це нейтральний початок розповіді. Але якщо ви поставите час або місце в кінець, вони стануть ремою. «Я був удома вчора» *(I was at home YESTERDAY)*. Це означає, що ви наголошуєте саме на вчорашньому дні, а не сьогоднішньому.

Є один дуже цікавий і специфічний випадок. Це порядок слів із числівниками. Коли ви називаєте точну кількість, числівник стоїть перед іменником. Наприклад: «До центру п’ять кілометрів» *(It is five kilometers to the center)*. Це точний факт. Але якщо ви поміняєте їх місцями, значення зміниться. «До центру кілометрів п’ять» *(It is ABOUT five kilometers to the center)*. Ця **інверсія** *(inversion)* автоматично робить число приблизним. Ukrainian uses this simple word-swap trick instead of adding extra words like "about" or "approximately".

<!-- INJECT_ACTIVITY: match-question-answer --> [match-up, Match questions with the correctly word-ordered answers, 8 items]

<!-- INJECT_ACTIVITY: group-sort-neutral-marked --> [group-sort, Sort sentences into neutral word order vs. marked/emphatic order, 8 items]

## Діалог 2 та Інверсія для контрасту

> — **Друг 1:** Ти дивився кіно вчора? Цей фільм зняв Сенцов.
> — **Друг 2:** Ні, цей фільм зняв не Сенцов, а Лозниця.
> — **Друг 1:** А, зрозумів. А от «Номери» — це точно Сенцов зняв!

У цьому діалозі друзі обговорюють режисерів. Зверніть увагу на їхні слова. Вони використовують **інверсію** *(inversion)*. Це навмисна зміна порядку слів для **контрасту** *(contrast)*.

In Ukrainian, you can freely move the object to the front of the sentence. Ми називаємо це винесенням додатка на **початок** *(beginning)*. Наприклад, ви можете сказати: «Книгу я вже прочитав». Тут ви протиставляєте цю книгу іншим речам. As for the book, I have already read it (maybe I haven't watched the movie yet). Це дуже популярна конструкція. Ви робите книгу головною темою вашої розмови.

Іноді ми ставимо дієслово на найперше місце в реченні. Це інверсія присудка. Наприклад: «Прочитав я цю книгу!». What does this specific order mean? Putting the verb first shows strong emotion, frustration, or absolute certainty. Це показує ваші сильні емоції або логічну завершеність дії. Ви хочете підкреслити, що дія точно відбулася.

Порядок слів також чудово допомагає швидко виправити помилку співрозмовника. Для цього ми використовуємо конструкцію «не..., а...» *(not..., but...)*. If someone assumes you walked in the park, but you actually walked in the forest, you change the word order to highlight the truth. Ви кажете: «Не в парку ми гуляли, а в лісі». You put the corrected information right at the front for maximum emphasis.

Як ще можна зробити сильний **наголос** *(emphasis)* на одному слові? Ми часто використовуємо просту частку «це» *(this/it)*. Порівняйте два варіанти: «Тарас мені допоміг» та «Це Тарас мені допоміг». The second sentence works exactly like a cleft sentence in English: "It was Taras who helped me." Ви чітко показуєте, хто саме виконав цю важливу дію.

Багато студентів дуже бояться самостійно змінювати порядок слів. Вони думають, що будуть звучати дивно, як майстер Йода з кінофільму «Зоряні війни». Але це міф. Речення «Книгу я бачив» — це абсолютно правильна і красива українська мова. У правильному контексті це звучить стовідсотково природно. Не бійтеся ставити слова у новий порядок у **кінець** *(end)* або на початок речення!

<!-- INJECT_ACTIVITY: fill-in-reorder-words-to-create-the-correct-emphasis-for-a-given-context -->

## Порядок слів у реальному мовленні

Уявіть звичайну розмову. Ми постійно передаємо нову інформацію. Як це працює на практиці? Дуже часто рема одного речення стає темою для наступного. Це наче ланцюжок. This chain structure helps speakers track what is already known and what is new. Подивіться на цей короткий діалог:
> — **Максим:** Де ти був сьогодні?
> — **Андрій:** Я був у парку.

У відповіді Андрія слово «парку» — це нова інформація, тобто рема. Воно стоїть у кінці речення. А тепер Максим запитує далі:
> — **Максим:** А в парку ти що робив?

Тепер «парк» — це вже відома інформація. Це тема. Тому Максим ставить ці слова на початок свого питання. А нова інформація (що саме Андрій там робив) буде в кінці. Ця ланцюжкова структура робить розмову дуже логічною.

Let's do a quick reading practice to see this in action. Read this short text: «На вулиці йшов дощ. Цей дощ не припинявся весь день. Раптом у двері постукали. Увійшов незнайомець». Why did the author choose this specific word order? «На вулиці йшов дощ» uses inversion to set the scene. «Цей дощ» moves to the front in the next sentence because it's now the theme (known info). «У двері постукали» puts the verb last to emphasize the sudden action. And «Увійшов незнайомець» uses verb-first inversion to introduce a brand new character. Analyzing these choices helps you understand the flow of the language!

Коли ми говоримо, ми використовуємо не тільки порядок слів. Ми також використовуємо голос. Це називається **логічний наголос** *(logical stress)*. Ми робимо голос сильнішим на найважливішому слові. Usually, logical stress naturally falls on the rheme at the end of the sentence. But when we use inversion, we combine both tools. Ми змінюємо порядок слів і додаємо інтонацію. Наприклад, ви хочете підкреслити свою довіру до конкретної людини. Ви кажете: «Тобі я вірю». Слово «тобі» стоїть на початку. І ви також виділяєте його голосом. By moving the object to the front and stressing it with your voice, you create a powerful contrast. Цей подвійний **акцент** *(emphasis)* робить ваші емоції дуже зрозумілими. Українці постійно використовують цей прийом у щоденному спілкуванні.

Є ще один дуже важливий **шаблон** *(template)*. Уявіть, що ви розповідаєте історію. Вам потрібно представити нового героя або нову подію. Як ви це зробите? In English, you would use "There is..." or just Subject + Verb ("A teacher entered"). В українській мові ми використовуємо інверсію. Ми ставимо дієслово перед підметом. Ми кажемо: «Увійшов старий вчитель» *(An old teacher entered)*. Чому ми не кажемо «Старий вчитель увійшов»? Тому що поява вчителя — це головна новина. When introducing a brand new subject into the narrative, the subject itself is the rheme, so it goes last. Ви часто почуєте такі фрази: «Прийшла весна» *(Spring came)*, «Почалася злива» *(A downpour started)*, «Настала ніч» *(Night fell)*. Це не просто художній стиль. Це найприродніший спосіб повідомити співрозмовнику про щось нове і раптове. Тепер ви знаєте, як зробити свою розповідь справді українською!

<!-- INJECT_ACTIVITY: error-correction-fix-sentences-where-word-order-creates-unintended-emphasis -->

## Підсумок

Let's review what we have learned today in this module. Порядок слів в українській мові — це дуже потужний інструмент. Це не просто граматична структура. Це спосіб показати ваші емоції, ваші наміри та ваші акценти. Кожен елемент має своє місце, але це місце може змінюватися. When you change the word order, you change the focus of your entire message.

First, you must understand the difference between theme and rheme. Чи розумієте ви різницю між темою та ремою? Тема — це вже відома інформація. Рема — це зовсім нова інформація. Куди зазвичай ставиться нова інформація в нейтральному реченні? In neutral speech, the most important new information always goes to the end. Якщо ви відповідаєте на запитання, ваша головна відповідь має стояти саме в кінці речення.

Second, adjectives and nouns have a strict relationship. Що трапиться, якщо прикметник поставити після іменника? It is no longer just a simple modifier. Він відразу стане присудком. Наприклад, фраза «Холодний вітер» означає просто "a cold wind." Але речення «Вітер холодний» означає "The wind is cold." Це вже повна і самостійна думка.

Third, fronting is your tool for contrast. Для чого виносити додаток на початок речення? We do this to create focus or a strong contrast. Коли ви кажете «Каву я вже пив», ви виділяєте саме слово «кава». You show that you drank the coffee, not the tea or juice.

Finally, word order helps with numbers. Як виразити приблизну кількість за допомогою порядку слів? Якщо ви ставите числівник перед іменником, ви називаєте абсолютно точну кількість. Наприклад, «П'ять кілометрів» — це рівно п'ять. Але якщо ви ставите іменник перед числівником, ви говорите про приблизну кількість. Фраза «Кілометрів п'ять» означає "about five kilometers."

Українська мова дає вам велику свободу у спілкуванні. You do not need to speak with a fixed subject-verb-object structure all the time. Ви можете вільно змінювати порядок слів у щоденній розмові. Це допоможе вашій мові звучати природно, емоційно та по-справжньому українською. Уважно слухайте, як розмовляють українці на вулиці чи у фільмах. Звертайте увагу на те, яке слово стоїть першим, а яке — останнім. Не бійтеся експериментувати з інверсією. Читайте українські тексти та аналізуйте логічний наголос. З часом ви відчуєте справжню красу та гнучкість українського синтаксису!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: word-order-emphasis
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

**Level: A2 (Module 50/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
