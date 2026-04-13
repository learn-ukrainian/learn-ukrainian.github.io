<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-foundations.yaml` file for module **8: Контрольна точка: Основи А2** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 3 | 5 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 7 | 10 | extended practice |
| Items per activity | 10 | — | each activity must have at least 10 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 3 inline activities AND at least 7 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, quiz, true-false, mark-the-words, observe, phrase-table
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 3–5 quick checks after key teaching points. Workbook = 7–10 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-mixed-grammar -->`
- `<!-- INJECT_ACTIVITY: fill-in-transformation -->`
- `<!-- INJECT_ACTIVITY: error-correction-mixed -->`
- `<!-- INJECT_ACTIVITY: fill-in-production -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed Grammar Quiz
  items: 8
  type: quiz
- focus: Sentence Transformation Drill
  items: 8
  type: fill-in
- focus: Short written responses using genitive and aspect
  items: 6
  type: fill-in
- focus: Find and fix mixed grammar errors — wrong aspect choice, wrong genitive endings,
    agreement mistakes
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- правильний (correct)
- варіант (option, variant)
- обрати (to choose)
- написати (to write)
required:
- вправа (exercise)
- перевірка (check, test)
- контрольна точка (checkpoint)
- завдання (task)
- текст (text)
- речення (sentence)
- відповідь (answer)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Вправи на розпізнавання (Part 1: Recognition Exercises)

**Кожна мова потребує часу на повторення. Сьогодні ми будемо перевіряти ваші знання.** (Every language requires time for review. Today we will be checking your knowledge.)

Learning a language requires stopping to review what you know. A **контрольна точка** (checkpoint) is precisely that moment in your journey. This module serves as a comprehensive **перевірка** (check) of the foundational grammar topics covered so far at the A2 level. You will deeply review how to navigate verb aspect, known as the **вид дієслова**, and how to master the Genitive case, or the **родовий відмінок**. Both of these grammatical systems are fundamental to speaking clearly and being understood by native speakers. Without them, you cannot accurately describe what happened yesterday, what will happen tomorrow, or what you currently do not have. Mastering these forms moves you away from speaking in broken phrases and allows you to build complete, logical sentences.

**Граматика завжди працює в реальному житті. Давайте подивимося на розмову двох студентів.** (Grammar always works in real life. Let's look at a conversation between two students.)

Before jumping into grammar rules, read a natural conversation. Two students are studying together before their Ukrainian class. One is struggling with numbers and cases, while the other helps him navigate the rules.

> **Олена:** Привіт, Марку! Що ти читаєш? Це новий **текст** (text) до уроку?
> **Марко:** Привіт, Олено! Ні, я просто повторюю граматику. Я маю тест завтра.
> **Олена:** Це добре. Тобі потрібна допомога?
> **Марко:** Так, дуже потрібна! Скільки у тебе братів? Треба казати «два брати» чи «двох братів»? Ох, я завжди плутаю ці складні закінчення.
> **Олена:** Дивись, правило просте. Треба казати «два брати», але «п'ять братів». Це дуже важливо пам'ятати, коли ти купуєш щось у магазині або рахуєш людей.
> **Марко:** Зрозумів. А сестер? Як сказати правильно про сестер?
> **Олена:** У мене немає сестри. Але у мого друга є три сестри і п'ять братів.
> **Марко:** Ого, це велика родина! Добре, я зрозумів логіку. Дякую за допомогу!
> **Олена:** Нема за що. Успіхів на тесті!

*(Vocabulary: плутаю — I confuse; рахуєш — you count; родина — family; успіхів — good luck)*

Notice how Марко struggles with the plural endings, but Олена quickly provides the right forms based on the numbers used. This is a common situation for language learners trying to memorize the rules for numbers.

Recognizing verb aspect is your first major step in this review. The imperfective aspect, or **недоконаний вид** (imperfective aspect), focuses entirely on the process of an action or its regular repetition. The perfective aspect, or **доконаний вид** (perfective aspect), signals a completed result or a one-time action that is successfully finished. These two verb forms together make up an aspectual pair, which linguists call a **видова пара** (aspectual pair). The upcoming **вправа** (exercise) will thoroughly test your ability to recognize these pairs in context.

* Читаємо українською (Reading in Ukrainian):
* **Я читаю цікаву книгу щодня.** (I read an interesting book every day. — *Process/Repetition*)
* **Я прочитав цю книгу вчора.** (I read this book yesterday. — *Result/Completion*)
* **Вона довго писала довгого листа.** (She was writing a long letter for a long time. — *Process*)
* **Вона швидко написала листа і пішла.** (She quickly wrote the letter and left. — *Result/Completion*)
* **Ми вчимо нові слова кожного ранку.** (We learn new words every morning. — *Process/Repetition*)
* **Сьогодні ми нарешті вивчили всі слова.** (Today we finally learned all the words. — *Result/Completion*)
* **Брат часто готував вечерю.** (Brother often cooked dinner. — *Process/Repetition*)
* **Брат приготував дуже смачну вечерю.** (Brother cooked a very tasty dinner. — *Result/Completion*)

The second major grammar topic for this review is the Genitive case. The most common trigger for this case is absence or negation, specifically using the word **немає** (there is no). Following absence, expressing possession is another major trigger, answering the specific question «whose?». Finally, basic prepositions like **з** (from), **без** (without), and **для** (for) strictly require the Genitive case. For this **завдання** (task), you must recognize these grammatical forms embedded in a connected text and inside an individual **речення** (sentence).

* Читаємо українською (Reading in Ukrainian):
* **У мене зараз немає вільного часу.** (I do not have free time right now. — *Absence*)
* **Він прийшов на урок без свого телефона.** (He arrived to the lesson without his phone. — *Preposition*)
* **Це нова машина мого старшого брата.** (This is my older brother's new car. — *Possession*)
* **Цей великий подарунок тільки для тебе.** (This big gift is only for you. — *Preposition*)
* **На столі немає гарячої кави.** (There is no hot coffee on the table. — *Absence*)
* **Я живу недалеко від центру міста.** (I live not far from the city center. — *Preposition*)
* **Ми п'ємо чай без цукру і молока.** (We drink tea without sugar and milk. — *Preposition*)
* **Сьогодні немає гарної погоди.** (There is no good weather today. — *Absence*)

<!-- INJECT_ACTIVITY: quiz-mixed-grammar -->

## Частина 2: Вправи на вибір (Part 2: Choice Exercises)

**Вибір дієслова — це завжди вибір контексту.** (Choosing a verb is always a choice of context.)

Choosing the right verb aspect depends entirely on the specific context of your sentence. Words like «завжди» (always) or «довго» (for a long time) point directly to a continuous process, requiring the imperfective aspect. Conversely, words like «нарешті» (finally) or a specific, limited timeframe for a result require the perfective aspect. When completing tests or writing emails, you must identify what is **правильний** (correct) and what is incorrect. You need to **обрати** (choose) the best **варіант** (option) based entirely on these time markers.

:::tip
Always look for time words in a sentence. If a sentence has «кожного дня» (every day), the verb will almost certainly be imperfective. If it has «за одну годину» (in one hour) or «вже» (already), it will be perfective because it shows a clear, completed result.
:::

* Читаємо українською (Reading in Ukrainian):
* **Вчора я читав нову книгу три години.** (Yesterday I read the new book for three hours. — *Process: три години*)
* **Я успішно прочитав книгу за один вечір.** (I successfully read the book in one evening. — *Result: за один вечір*)
* **Ми часто купували свіже молоко тут.** (We often bought fresh milk here. — *Habit: часто*)
* **Сьогодні вранці ми купили яблучний сік.** (This morning we bought apple juice. — *Result: сьогодні вранці (one time)*)
* **Він завжди довго робив домашнє завдання.** (He always did his homework for a long time. — *Habit: завжди*)
* **Він швидко зробив завдання за п'ять хвилин.** (He quickly did the task in five minutes. — *Result: за п'ять хвилин*)
* **Вона завжди купувала каву вранці.** (She always bought coffee in the morning. — *Habit: завжди*)
* **Раптом вона купила зелений чай.** (Suddenly she bought green tea. — *Result: раптом*)

**Українські числівники завжди працюють разом з відмінками. Це дуже важливе правило.** (Ukrainian numbers always work together with cases. This is a very important rule.)

The Genitive case intersects heavily and predictably with numbers. Numbers 5 and above always require the Genitive plural, or **родовий відмінок множини** (Genitive plural). The numbers 2, 3, and 4 act completely differently, requiring the Nominative plural instead. This specific split in the number system is an ancient grammatical feature that you will use every single day when shopping or counting objects.

* Читаємо українською (Reading in Ukrainian):
* **У нашому класі стоїть два великі столи.** (There are two large tables in our classroom. — *Nominative plural*)
* **У цьому кабінеті є шість старих столів.** (There are six old tables in this office. — *Genitive plural*)
* **Я вчора купив три цікаві книги.** (I bought three interesting books yesterday. — *Nominative plural*)
* **Мій сусід має десять товстих книжок.** (My neighbor has ten thick books. — *Genitive plural*)
* **Там на вулиці стоїть п'ять нових студентів.** (Five new students are standing there on the street. — *Genitive plural*)
* **У мене є чотири гарні яблука.** (I have four beautiful apples. — *Nominative plural*)
* **Він з'їв сім солодких яблук.** (He ate seven sweet apples. — *Genitive plural*)
* **Ми побачили вісім великих машин.** (We saw eight large cars. — *Genitive plural*)

Forming the Genitive plural correctly requires learning a few specific patterns. For feminine and neuter nouns, you generally drop the final vowel to create a zero ending, sometimes inserting an «o» or «e» to make the word pronounceable. Masculine nouns that end in a consonant usually take the «-ів» ending. There are also important exceptions like the «-ей» ending for words such as «стаття» (article) or «ніч» (night).

* Читаємо українською (Reading in Ukrainian):
* **Одна гарна сестра → п'ять гарних сестер** (One beautiful sister → five beautiful sisters)
* **Одна цікава думка → дуже багато думок** (One interesting thought → very many thoughts)
* **Один старший брат → п'ять старших братів** (One older brother → five older brothers)
* **Один дерев'яний стіл → десять дерев'яних столів** (One wooden table → ten wooden tables)
* **Одна темна ніч → сім темних ночей** (One dark night → seven dark nights)
* **Одна нова стаття → шість нових статей** (One new article → six new articles)
* **Одне велике вікно → дев'ять великих вікон** (One large window → nine large windows)
* **Один розумний студент → багато розумних студентів** (One smart student → many smart students)

You are now fully ready for the choice and transformation exercises. In the upcoming section, you will complete a challenging sentence transformation drill where you insert the correct grammatical form into the blank space. Pay close attention to the **дієвідміна** (conjugation) of the verbs you use, and ensure that every single **особове закінчення** (personal ending) matches the sentence's subject perfectly.

<!-- INJECT_ACTIVITY: fill-in-transformation -->

## Частина 3: Практичне застосування (Part 3: Production Exercises)

**Тепер час говорити і писати самостійно. Ми будемо поєднувати всі правила в одному тексті.** (Now it is time to speak and write independently. We will combine all the rules in one text.)

Shifting from choosing answers on a screen to actually producing them in real speech is your ultimate goal. You will frequently need to combine verb aspect and the Genitive case in the exact same sentence. For instance, using a perfective verb in a negative sentence very often requires a Genitive object to clearly show that a specific item was not obtained or found.

* Читаємо українською (Reading in Ukrainian):
* **Я пішов у магазин, але не купив молока.** (I went to the store, but did not buy milk. — *Perfective verb + Genitive object*)
* **Вона шукала довго, але не знайшла ключів.** (She searched for a long time, but did not find the keys. — *Perfective verb + Genitive plural object*)
* **Ми були там, але не побачили наших друзів.** (We were there, but did not see our friends. — *Perfective verb + Genitive plural object*)
* **Він купив газету, але не прочитав цікавої статті.** (He bought the newspaper, but did not read the interesting article. — *Perfective verb + Genitive object*)
* **Я хотів працювати, але не мав вільного часу.** (I wanted to work, but did not have free time. — *Imperfective verb + Genitive object*)
* **Вони дивилися фільм, але не побачили фіналу.** (They watched the movie, but did not see the finale. — *Perfective verb + Genitive object*)

Before writing your own original text, you must systematically analyze common errors made by learners. The verb «потребувати» (to need) rigidly demands the Genitive case, so translating "I need help" directly is a severe mistake. Another classic error is ignoring the required case after negation, or matching numbers incorrectly like «п'ять книга». Use the "Світлофор" (Traffic light) strategy to stop completely and check your mental translations.

:::caution
Do not use the word «приймати» for taking a shower or participating in an event. You must use the verb «брати». A very common mistake is saying «приймати участь»; the correct and natural Ukrainian phrase is always **брати участь**.
:::

* Читаємо українською (Reading in Ukrainian):
* ❌ *Я дуже сильно потребую допомогу.* → ✅ **Я дуже сильно потребую допомоги.** (I very much need help.)
* ❌ *На жаль, у мене немає сестра.* → ✅ **На жаль, у мене немає сестри.** (Unfortunately, I don't have a sister.)
* ❌ *Я вчора купив п'ять книга.* → ✅ **Я вчора купив п'ять книжок.** (I bought five books yesterday.)
* ❌ *Зараз вона приймає душ.* → ✅ **Зараз вона бере душ.** (She is taking a shower now.)
* ❌ *Сьогодні ми приймаємо участь.* → ✅ **Сьогодні ми беремо участь.** (Today we are participating.)
* ❌ *Я не маю новий телефон.* → ✅ **Я не маю нового телефона.** (I do not have a new phone.)

You are now acting as the teacher for a moment. In the following error correction **вправа** (exercise), you must read each provided **відповідь** (answer) carefully and find the hidden mixed grammar errors. Your specific job is to identify the wrong aspect choice, spot incorrect genitive endings, and fix any verb or noun agreement mistakes. Finding errors in other people's writing builds the exact mental muscle you need to catch errors in your own speaking. Look closely at every single noun immediately following a number or a preposition, as that is where mistakes usually hide.

<!-- INJECT_ACTIVITY: error-correction-mixed -->

Open-ended questions simulate real, unpredictable conversations. You will need to answer personal questions which immediately require you to use genitive plural numbers and perfective verbs correctly. You must **написати** (write) your own authentic answers to these questions. Take your time to think deeply about the correct cases and verb forms before you write anything down.

> **Марко:** Привіт, Олено! Ми дуже давно не бачилися. Як твої справи?
> **Олена:** Привіт! Все чудово. Я зараз багато працюю.
> **Марко:** Скільки у тебе братів і сестер зараз? Вони живуть тут?
> **Олена:** У мене є два старші брати і немає сестер. Вони живуть у Києві. А у тебе велика родина?
> **Марко:** У мене одна маленька сестра. Зрозуміло. А що ти зробила вчора ввечері? Ти відпочивала?
> **Олена:** Ні, я не відпочивала. Я нарешті прочитала нову цікаву книгу і написала довгий текст для університету. Я працювала чотири години.
> **Марко:** О, це дуже багато роботи! Я вчора просто дивився телевізор.
> **Олена:** Тобі пощастило! Але сьогодні ти мусиш вчитися.

*(Vocabulary: давно не бачилися — haven't seen each other for a long time; відпочивала — rested; пощастило — got lucky; мусиш — must)*

The final writing prompt tests your ability to plan ahead and organize your thoughts. You will write a short paragraph about your plans for the weekend using both aspects naturally. Combine imperfective verbs for ongoing, continuous processes and perfective verbs for specific, completed goals. Mixing these aspects gives your writing much more depth, realistic pacing, and precision.

:::note
**Практика читання** (Reading practice):
Вчора я був у великому супермаркеті. Я дуже хотів купити молоко для кави, але там зовсім не було молока. Я довго шукав, але не знайшов його. Тому я купив п'ять червоних яблук, шість солодких бананів і десять свіжих яєць. Я завжди купую свіжі фрукти на ринку, але сьогодні пішов у магазин. Потім я швидко пішов додому і прочитав свіжі новини в інтернеті. Це був звичайний і дуже спокійний день.

*(Vocabulary: зовсім — absolutely; свіжі яйця — fresh eggs; ринок — market; спокійний — calm)*
:::

<!-- INJECT_ACTIVITY: fill-in-production -->

## Підсумок — Summary

The A2 level builds the essential core of your everyday speaking ability. You have thoroughly reviewed the fundamental distinction between the imperfective and perfective verb aspects, learning exactly when to focus on the ongoing process and when to highlight the final result. You have also actively practiced the Genitive case, especially its critical role with negation, expressing possession, and pairing with numbers. Mastering the Genitive plural after the number five is a major linguistic milestone for any Ukrainian learner. This checkpoint confirms your solid understanding of these interconnected systems. As you progress further, these rules will become automatic reflexes rather than mathematical puzzles you have to solve. You are building a strong, reliable foundation for fluent, natural communication in all your future conversations.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-foundations
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 3–5 inline / 7–10 workbook,
# 10+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 10 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 10 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 10 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 10 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 10 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 10 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 10 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 10 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**Level: A2 (Module 8/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 10 activities.** Inline: 3–5. Workbook: 7–10. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 10 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 10.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 3** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 7** workbook activities.
- [ ] **Total ≥ 10.**
- [ ] **Every** activity has **at least 10** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 3 and 5. I did NOT create more injection markers than 5.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
