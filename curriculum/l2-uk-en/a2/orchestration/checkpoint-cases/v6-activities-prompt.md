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

- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`

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
## Частина 1: Форми множини (Part 1: Plural Forms)

This is our **контрольна точка** (checkpoint). You have reached the final and most important phase of the A2 level. We will do a complete **перевірка** (check, review) of the Ukrainian case system. We have learned all seven cases in both **однина** (singular) and **множина** (plural). The concept of "number" changes how words behave. Mastering plural cases is the final hurdle before moving to more advanced verbs.

First, let's review the Nominative plural — the dictionary form for multiple objects. For masculine and feminine nouns, the standard endings are **-и** or **-і**. Hard stems take **-и**, while soft stems take **-і**. Neuter nouns change their ending from **-о** to **-а**, and from **-е** to **-я**.

*   **Це мій брат. — Це мої брати.** (This is my brother. — These are my brothers.)
*   **Це велика кімната. — Це великі кімнати.** (This is a large room. — These are large rooms.)
*   **Це глибоке озеро. — Це глибокі озера.** (This is a deep lake. — These are deep lakes.)
*   **Це синє море. — Це сині моря.** (This is a blue sea. — These are blue seas.)

Some essential words have irregular plural forms. You must memorize these exceptions because they change their stem or use unpredictable endings. These are very common in daily life.

*   **Одна людина — багато людей.** (One person — many people.)
*   **Моя дитина — мої діти.** (My child — my children.)
*   **Праве око — мої очі.** (Right eye — my eyes.)
*   **Ліве вухо — мої вуха.** (Left ear — my ears.)
*   **Мій друг — мої друзі.** (My friend — my friends.)

The most complex form in Ukrainian is the Genitive plural. It is the "boss" of the case system. While other cases usually have one or two predictable plural endings, the Genitive plural has three completely different patterns: **-ів**, **-ей**, and the "zero ending" (no ending at all).

Most masculine nouns take the ending **-ів** (or **-їв** after a vowel). Some feminine nouns and soft-stem nouns take the ending **-ей**. 

*   **У мене немає братів.** (I do not have brothers.)
*   **У місті багато готелів.** (There are many hotels in the city.)
*   **Я працюю багато ночей.** (I work many nights.)
*   **У мене немає грошей.** (I do not have money.)
*   **У неї немає ідей.** (She has no ideas.)

Many feminine and neuter nouns drop their ending completely in the Genitive plural. This is called the "zero ending". When dropping the ending creates a hard-to-pronounce cluster of consonants, Ukrainian inserts a fleeting vowel (**о** or **е**) to break it up.

*   **Це цікава книга. — У мене багато книг.** (This is an interesting book. — I have many books.)
*   **Це гарне місто. — Я знаю багато міст.** (This is a beautiful city. — I know many cities.)
*   **Це моя сумка. — У мене п'ять сумок.** (This is my bag. — I have five bags.)
*   **Це чисте вікно. — У кімнаті немає вікон.** (This is a clean window. — There are no windows in the room.)
*   **Це моя сестра. — У нього немає сестер.** (This is my sister. — He does not have sisters.)

We use the Genitive plural constantly with quantity expressions. Remember the rule: the number 1 takes the Nominative singular. Numbers 2, 3, and 4 take the Nominative plural (often with a stress shift). Numbers 5 and above, as well as words like **багато** (many) and **скільки** (how many), always take the Genitive plural.

*   **Два брати — п'ять братів.** (Two brothers — five brothers.)
*   **Три книги — десять книг.** (Three books — ten books.)
*   **Чотири вікна — багато вікон.** (Four windows — many windows.)

<!-- INJECT_ACTIVITY: group-sort -->

## Частина 2: Який відмінок? (Part 2: Which Case?)

When speaking Ukrainian, how do you know which **відмінок** (case) to use? The verb is the commander of the sentence. It dictates the case of the noun that follows it. This is called verb government. Let's look at the most important verbs. 

Verbs like **допомагати** (to help) and **дякувати** (to thank) demand the Dative case. Verbs of emotion and perception, like **любити** (to love) and **бачити** (to see), demand the Accusative case. Verbs of engagement, like **займатися** (to be engaged in) and **цікавитися** (to be interested in), require the Instrumental case.

*   **Я завжди допомагаю мамі.** (I always help my mom.)
*   **Учні дякують вчителеві.** (The students thank the teacher.)
*   **Я бачу високий будинок.** (I see a tall building.)
*   **Він любить свою сестру.** (He loves his sister.)
*   **Вона займається спортом.** (She does sports.)
*   **Ми цікавимося історією.** (We are interested in history.)

Prepositions are also strong triggers. Some prepositions only work with one case, while others do double duty. The prepositions **в/у** (in, into) and **на** (on, onto) take the Accusative case for motion (Where to?) and the Locative case for location (Where at?).

*   **Я іду в школу.** (I am going to school. — Motion, Accusative)
*   **Я зараз у школі.** (I am at school now. — Location, Locative)
*   **Він іде на роботу.** (He is going to work. — Motion, Accusative)
*   **Він на роботі.** (He is at work. — Location, Locative)

Other prepositions are strict. **З** means "with" when used with the Instrumental case, but means "from" when used with the Genitive case. **Біля** (near) and **для** (for) always take the Genitive.

*   **Я п'ю каву з молоком.** (I drink coffee with milk. — Instrumental)
*   **Він іде зі школи.** (He is going from school. — Genitive)
*   **Це подарунок для брата.** (This is a gift for my brother. — Genitive)

The Instrumental case is unique because it is often used without any preposition to describe the path of movement or the tool used to perform an action.

*   **Ми їдемо автобусом.** (We are traveling by bus.)
*   **Вони ідуть лісом.** (They are walking through the forest.)
*   **Я пишу синьою ручкою.** (I am writing with a blue pen.)
*   **Він їсть суп ложкою.** (He is eating soup with a spoon.)

Cases are also used in special descriptive constructions. To say when something happens on a day of the week, we use **в/у** + Accusative. For years, we use **в/у** + Locative. To describe what someone is wearing, we use **в/у** + Locative.

*   **У четвер ми йдемо в кіно.** (On Thursday we are going to the cinema.)
*   **Це сталося у 2024 році.** (This happened in the year 2024.)
*   **Я бачу чоловіка у чорному светрі.** (I see a man in a black sweater.)

When you make a **помилка** (error, mistake), how do you find and **виправити** (to correct) it? You need to work backward. First, find the noun. Second, find the word that triggers its case (usually the verb or preposition right before it). Third, check the ending based on the noun's gender and number. If you say "Я допомагаю сестру", find the verb. **Допомагати** requires the Dative case. The noun is feminine. Therefore, it must be **сестрі**.

Finally, remember the rule of animate and inanimate objects in the Accusative plural. For masculine and mixed groups of living beings (animate), the Accusative plural looks exactly like the Genitive plural. For non-living objects (inanimate), the Accusative plural looks exactly like the Nominative plural.

*   **Я бачу нових студентів.** (I see the new students. — Animate, looks like Genitive)
*   **Я бачу нові столи.** (I see the new tables. — Inanimate, looks like Nominative)

<!-- INJECT_ACTIVITY: quiz -->
<!-- INJECT_ACTIVITY: error-correction -->

## Частина 3: Вільне мовлення (Part 3: Free Production)

Let's see how all these cases work together in a real conversation. Two friends are discussing an upcoming wedding. Watch how the cases change naturally depending on what they are talking about.

> **Наречена:** Привіт! Ти вже отримала запрошення для гостей? *(Hi! Did you already receive the invitation for the guests?)*
> **Подруга:** Так, отримала! Я вже купила подарунок нареченій. *(Yes, I received it! I already bought a gift for the bride.)*
> **Наречена:** Дуже дякую! Я так хвилююся. Ти бачила мою нову сукню? *(Thank you so much! I am so nervous. Did you see my new dress?)*
> **Подруга:** Бачила сукню вчора. Вона прекрасна! А хто буде робити фото з молодятами? *(I saw the dress yesterday. It is beautiful! And who will take photos with the newlyweds?)*
> **Наречена:** Мій брат. Він буде фотографом на весіллі. *(My brother. He will be the photographer at the wedding.)*
> **Подруга:** Олено! Все буде ідеально! *(Olena! Everything will be perfect!)*

Let's break down why specific forms were used in this conversation. The word **гостей** is Genitive plural because of the preposition **для**. The phrase **нареченій** is Dative singular because it is the receiver of the gift. The phrase **нову сукню** is Accusative singular because it is the direct object of the verb "to see". The word **молодятами** is Instrumental plural because it follows the preposition **з** (with). The phrase **на весіллі** is Locative singular because it shows location. Finally, **Олено** is the Vocative case, used to address someone directly.

Now it is your turn to use these cases. A great way to practice is to describe your **вихідний день** (day off). When you build a narrative, you naturally use multiple cases. You use the Accusative or Locative to say where you go. You use the Instrumental to say who you spend time with. You use the Accusative for the things you buy, and the Genitive for quantities of things.

Here is a model paragraph describing an ideal day off. Notice how the endings change to fit the grammar.

*   **Прокидаюся о дев'ятій годині.** (I wake up at nine o'clock. — Locative for time)
*   **Я п'ю каву з молоком.** (I drink coffee with milk. — Instrumental)
*   **Потім я гуляю з друзями у великому парку.** (Then I walk with friends in a large park. — Instrumental, then Locative)
*   **Ми йдемо в новий ресторан.** (We go to a new restaurant. — Accusative for motion)
*   **Я купую багато свіжих фруктів.** (I buy a lot of fresh fruits. — Genitive plural for quantity)

:::tip
**Case Compass (Plurals)**
To navigate plural endings, remember the core patterns:
- Nominative Plural: Usually **-и / -і** or **-а / -я**.
- Genitive Plural: Watch out for the zero ending and the fleeting vowels **о / е** (e.g., **вікно → вікон**).
- Dative Plural: Always ends in **-ам / -ям**.
- Instrumental Plural: Always ends in **-ами / -ями**.
- Locative Plural: Always ends in **-ах / -ях**.
:::

You are almost ready for the next phase, A2.6. You have learned to synthesize the entire declension system. You can form plural nouns, choose the correct case based on the verb or preposition, and correct your own mistakes. In the next phase, we will shift our focus to verbs, specifically the concept of Aspect (perfective and imperfective verbs), which will allow you to talk about completed actions and repeated habits.

Thinking in Ukrainian means you no longer translate prepositions word-for-word from English. Instead, you feel the relationship between the words. You know that movement requires the Accusative, while a static location requires the Locative. Using correct cases makes your speech sound natural and elegant to native speakers. It shows that you understand the soul of the language.

<!-- INJECT_ACTIVITY: fill-in -->

## Підсумок

You have completed the **контрольна точка**. Let's do a final **самоперевірка** (self-check). Ask yourself these questions to ensure you are ready to move forward.

- Can I form plural nouns in the Nominative confidently? (e.g., **місто → міста**, **людина → люди**)
- Do I know the three main Genitive Plural endings? (**-ів**, **-ей**, and the zero ending)
- Can I fix a "fleeting vowel" error? (**вікно → вікон**, not *вікн*)
- Do I remember which case follows **дякувати** (Dative) or **цікавитися** (Instrumental)?
- Can I use **в/у** and **на** correctly for both location (Locative) and motion (Accusative)?
- Can I write a short text using at least five different cases naturally?
- Am I ready to stop translating and start feeling the grammar?

If you answered "Yes" to all these questions, you have mastered the foundational case system. You use cases **впевнено** (confidently). Welcome to A2.6!

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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

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
