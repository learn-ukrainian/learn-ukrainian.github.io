<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/hey-friend.yaml` file for module **42: Hey, Friend!** (a1).

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

- `<!-- INJECT_ACTIVITY: dialogue-flow-practice -->`
- `<!-- INJECT_ACTIVITY: vocative-form-practice -->`
- `<!-- INJECT_ACTIVITY: vocative-choice-quiz -->`
- `<!-- INJECT_ACTIVITY: ending-sorting-activity -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Write vocative: Олена → Олено, Тарас → Тарасе, мама → мамо'
  items:
  - Олена → {Олено}
  - Тарас → {Тарасе}
  - мама → {мамо}
  - Іван → {Іване}
  - сестра → {сестро}
  - Андрій → {Андрію}
  - подруга → {подруго}
  - брат → {брате}
  - Марія → {Маріє}
  - бабуся → {бабусю}
  type: fill-in
- focus: 'Choose correct vocative: (Олена / Олено / Оленю), привіт!'
  items:
  - options:
    - Олено
    - Олена
    - Оленю
    question: ___, привіт!
  - options:
    - Тарасе
    - Тарас
    - Тарасу
    question: Як справи, ___?
  - options:
    - мамо
    - мама
    - маме
    question: Дякую, ___!
  - options:
    - Іване
    - Іван
    - Івану
    question: Ходи сюди, ___!
  - options:
    - синку
    - синок
    - синке
    question: Будь обережний, ___!
  - options:
    - брате
    - брат
    - брату
    question: Що ти робиш, ___?
  - options:
    - пане
    - пан
    - пану
    question: Добрий день, ___!
  - options:
    - Андрію
    - Андрій
    - Андріє
    question: Привіт, ___!
  type: quiz
- focus: 'Sort vocative endings: -о (feminine) vs -е (masculine hard) vs -ю (masculine
    soft)'
  groups:
  - items:
    - Олено
    - мамо
    - сестро
    name: -о (feminine)
  - items:
    - Тарасе
    - Іване
    - брате
    - пане
    name: -е (masculine hard)
  - items:
    - Андрію
    - дідусю
    - вчителю
    name: -ю (masculine soft)
  type: group-sort
- focus: 'Complete dialogue: ___, привіт! Як справи? (name → vocative)'
  items:
  - — {Олено|Олена}, привіт! Як справи?
  - — Добре, дякую, {Тарасе|Тарас}!
  - — {Мамо|Мама}, де мій телефон?
  - — На столі, {синку|синок}.
  - — {Бабусю|Бабуся}, ми йдемо!
  - — Добре, до побачення, {Андрію|Андрій}!
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- синку (son — vocative, from син)
- дочко (daughter — vocative, from дочка)
- козак (Cossack, m)
- вчитель (teacher, m)
- бабуся (grandmother, f)
- дідусь (grandfather, m)
required:
- друг (friend, m)
- подруга (friend, f)
- брат (brother, m)
- сестра (sister, f)
- пан (Mr., m)
- пані (Mrs./Ms., f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Imagine you are at a lively birthday party in Ukraine. The traditional music is playing loudly, people are talking in groups, and you need to get your friend's attention across the crowded room. In English, you would simply shout their name exactly as it is written. In Ukrainian, calling out to someone or addressing them directly requires a specific grammatical shift. You cannot just use their regular, dictionary-form name; you must change its ending to show that you are talking to them, rather than about them. 

Let us look at a typical interaction as guests arrive at the party. The birthday person is greeting friends as they walk through the door. Notice how the names change when they speak directly to each other. Pay special attention to how **Олена** (Olena), **Тарас** (Taras), and **Андрій** (Andriy) are addressed.

> **Іменинник:** **Олено, привіт! Як справи?** *(Olena, hi! How are you?)*
> **Олена:** **Добре, дякую, Тарасе! А в тебе?** *(Good, thanks, Taras! And you?)*
> **Іменинник:** **Теж добре. Олено, ти знаєш мого брата?** *(Also good. Olena, do you know my brother?)*
> **Олена:** **Ні.** *(No.)*
> **Іменинник:** **Андрію, ходи сюди! Це Олена.** *(Andriy, come here! This is Olena.)*
> **Іменинник:** **Олено, це Андрій.** *(Olena, this is Andriy.)*

Later at the same party, the birthday person interacts with different family members in the kitchen. Family words also change their endings when you address them directly. Pay attention to how the words for mom, dad, son, daughter, and grandma transform in conversation when someone is asking a question or giving an instruction.

> **Син:** **Мамо, де мій телефон?** *(Mom, where is my phone?)*
> **Мама:** **На столі, синку.** *(On the table, son.)*
> **Дочка:** **Тату, а де ключі?** *(Dad, and where are the keys?)*
> **Тато:** **У кишені, дочко.** *(In the pocket, daughter.)*
> **Син:** **Бабусю, ми йдемо!** *(Grandma, we are going!)*
> **Бабуся:** **Добре, будьте обережні!** *(Good, be careful!)*
> **Бабуся:** **До побачення, Андрію!** *(Goodbye, Andriy!)*

Did you notice the consistent pattern of direct address in those two dialogues? When the speaker talked about someone, they used the regular name, like saying **Це Олена** (This is Olena) or **Це Андрій** (This is Andriy). But when they spoke directly to them, **Олена** (Olena) became **Олено** (Olena), **Тарас** (Taras) became **Тарасе** (Taras), and **мама** (mom) became **мамо** (mom). This shift is not an optional stylistic choice; it is a fundamental rule of natural Ukrainian communication.

*   **Добрий ранок, пане Іване!** *(Good morning, Mr. Ivan!)*
*   **Добрий вечір, пані Оксано!** *(Good evening, Ms. Oksana!)*
*   **До побачення, вчителю!** *(Goodbye, teacher!)*
*   **На добраніч, синку!** *(Good night, son!)*
*   **Смачного, друзі!** *(Bon appetit, friends!)*

<!-- INJECT_ACTIVITY: dialogue-flow-practice -->

## Кличний відмінок (The Vocative Case)

Ukrainian grammar features seven cases, and one of them is used exclusively for calling, addressing, or getting someone's attention. This is called the **кличний відмінок** (Vocative Case). As you already know, Ukrainian relies on changing word endings to show grammatical relationships within a sentence. While the other six cases indicate who is doing an action or where an object is located, the vocative case serves a purely communicative function. In English you just say the name: "Olena, come here!". In Ukrainian the name CHANGES: **Олено, ходи сюди!** (Olena, come here!). When you address a person, you must alter their name or title to match this specific grammatical role. This is not optional — Ukrainians always use the vocative when addressing someone.

In Ukrainian elementary schools, fourth-grade students learn a simple but effective trick to remember when to use this form. Teachers introduce the vocative case with a Grade 4 helper word and punctuation mark: **Кл. (!)** (Voc. (!)). The exclamation mark acts as a visual reminder that you are "shouting," calling out, or directly addressing someone. This punctuation mark triggers the ending change. Whenever you use a person's name with an exclamation mark or a comma in direct speech, you must apply the vocative ending. This mental trigger ensures that the name correctly reflects the social interaction taking place.

:::note
The vocative case is entirely independent of the other cases. It does not answer any questions (like "who?" or "what?"), because its only job is to get someone's attention.
:::

Understanding the difference between talking about someone and talking to someone is critical for your fluency. The nominative case is the dictionary form, used when someone is the subject of a sentence. Why the vocative matters: **Олена прийшла.** (Olena came.) is in the nominative, because you are talking ABOUT her. However, if you want to address her, you must use the vocative: **Олено, ходи сюди!** (Olena, come here!), because you are talking TO her. Using the nominative to address a person sounds incredibly unnatural to native speakers. It feels as awkward as saying "Hey, him!" instead of "Hey, you!" in English. Let us compare these two states:

**Називний відмінок** (Nominative):
*   **Це мій тато.** *(This is my dad.)*
*   **Тут працює вчитель.** *(A teacher works here.)*
*   **Там стоїть Олена.** *(Olena is standing there.)*
*   **Мій брат читає.** *(My brother is reading.)*

**Кличний відмінок** (Vocative):
*   **Тату, я тебе бачу!** *(Dad, I see you!)*
*   **Вчителю, добрий ранок!** *(Teacher, good morning!)*
*   **Олено, йди туди!** *(Olena, go there!)*
*   **Брате, що ти читаєш?** *(Brother, what are you reading?)*

The vocative case is much more than just a grammatical rule; it is a living marker of Ukrainian linguistic identity. While this grammatical feature has mostly disappeared from standard Russian, surviving only in a few archaic religious terms, it remains vibrant and absolutely necessary in everyday Ukrainian conversation. By using the vocative case correctly, you are not just following a textbook rule. You are actively speaking authentic, decolonized Ukrainian and showing deep respect for the natural structure and historical continuity of the language. When you use the vocative case, native speakers instantly recognize that you are making a genuine effort to understand the rhythm of their language, rather than just translating English words directly into Ukrainian.

## Закінчення кличного (Vocative Endings)

Let us break down the specific rules for forming the vocative case, starting with feminine names and nouns that end in the letter **-а**. This is the most common feminine pattern you will encounter. To create the vocative form, you simply replace the final **-а** with the letter **-о**. 

*   **Олена** → **Олено** (Olena)
*   **мама** → **мамо** (mom)
*   **сестра** → **сестро** (sister)
*   **Оксана** → **Оксано** (Oksana)
*   **подруга** → **подруго** (friend, f)

This rule also applies to informal or diminutive names ending in **-ка**, such as **Наталка** → **Наталко** (Natalka) and **Ірка** → **Ірко** (Irka). Furthermore, longer names ending in **-а** follow this exactly: **Катерина** → **Катерино** (Kateryna), **Тетяна** → **Тетяно** (Tetiana). Note that the polite title **пані** (Mrs. / Ms.) is an exception and does not change its form when used to address someone.

*   **Олено, де мій зошит?** *(Olena, where is my notebook?)*
*   **Мамо, я хочу їсти.** *(Mom, I want to eat.)*
*   **Сестро, ти йдеш у кіно?** *(Sister, are you going to the cinema?)*
*   **Подруго, це твоя книга?** *(Friend, is this your book?)*
*   **Катерино, добрий день!** *(Kateryna, good day!)*

Feminine names that end in **-ія** or the soft letter **-я** follow a slightly different but closely related pattern. If a name ends in **-ія**, the ending shifts to **-іє**. For example, **Марія** (Mariia) becomes **Маріє** (Mariia — vocative, never "Маріо!"). If a feminine word or name ends in a soft **-ся** or is a diminutive form ending in **-я**, the ending changes to **-ю**. 

*   **Марія** → **Маріє** (Mariia)
*   **Юлія** → **Юліє** (Yuliia)
*   **бабуся** → **бабусю** (grandma)
*   **Галя** → **Галю** (Halia)
*   **Наталя** → **Наталю** (Natalia)

Notice how the soft quality of the final consonant is preserved by using the soft vowel **-ю** or **-є**. 

*   **Маріє, як справи?** *(Mariia, how are things?)*
*   **Юліє, ходи сюди!** *(Yuliia, come here!)*
*   **Бабусю, ти дуже добра.** *(Grandma, you are very kind.)*
*   **Наталю, де ти живеш?** *(Natalia, where do you live?)*

:::caution
Do not confuse the feminine ending **-ю** (like in **бабусю**) with the masculine soft ending **-ю** (like in **Андрію**). While they look identical, they come from different spelling patterns.
:::

Now let us look at masculine names and nouns. Most standard masculine words end in a hard consonant. To form the vocative for these words, you do not replace anything; you simply add the letter **-е** directly to the end of the hard consonant. This makes the word slightly longer and easier to call out across a room.

*   **Тарас** → **Тарасе** (Taras)
*   **Іван** → **Іване** (Ivan)
*   **брат** → **брате** (brother)
*   **пан** → **пане** (Mr. / sir)
*   **Богдан** → **Богдане** (Bohdan)

Whenever you use the formal title **пан**, it must also take this ending, as in **Добрий день, пане!** (Good day, sir!).

*   **Тарасе, що ти робиш?** *(Taras, what are you doing?)*
*   **Іване, це твій телефон?** *(Ivan, is this your phone?)*
*   **Брате, йди сюди!** *(Brother, come here!)*
*   **Пане, де тут аптека?** *(Sir, where is the pharmacy here?)*
*   **Богдане, ти студент?** *(Bohdan, are you a student?)*

If a masculine word ends in a soft consonant or the letter **-й**, the added vowel changes to match the softness. Instead of adding **-е**, you must add the letter **-ю** to the end of the word. This maintains the softness of the final sound and creates a smooth, natural flow when speaking.

*   **Андрій** → **Андрію** (Andriy)
*   **Сергій** → **Сергію** (Serhiy)
*   **дідусь** → **дідусю** (grandpa)
*   **вчитель** → **вчителю** (teacher, m)

Replacing the **-й** with **-ю** is one of the most frequent transformations you will make when addressing Ukrainian men.

*   **Андрію, ти маєш брата?** *(Andriy, do you have a brother?)*
*   **Сергію, це твоя машина?** *(Serhiy, is this your car?)*
*   **Дідусю, читай казку!** *(Grandpa, read a fairy tale!)*
*   **Вчителю, я маю питання.** *(Teacher, I have a question.)*

There are a few special cases and consonant alternations that you should memorize because they occur in very common words. The word for dad takes an exceptional **-у** ending: **тато** → **тату** (dad). You must memorize this. The word for son also takes an **-у** ending: **син** → **синку** (son). Additionally, some masculine consonants change their sound entirely to make pronunciation easier. For example, the consonant **г** changes to **ж** in **друг** → **друже** (friend, m), and the consonant **к** changes to **ч** in **козак** → **козаче** (Cossack).

*   **Тату, я йду додому.** *(Dad, I am going home.)*
*   **Синку, будь обережний!** *(Son, be careful!)*
*   **Друже, ти маєш рацію.** *(Friend, you are right.)*
*   **Козаче, куди ти йдеш?** *(Cossack, where are you going?)*

<!-- INJECT_ACTIVITY: vocative-form-practice -->
<!-- INJECT_ACTIVITY: vocative-choice-quiz -->
<!-- INJECT_ACTIVITY: ending-sorting-activity -->

## Підсумок — Summary

Mastering the vocative case is a crucial step in sounding like a natural, fluent Ukrainian speaker. Remember that you must always change the ending of a name or title when you are addressing someone directly. The core patterns are very consistent across the language: feminine words ending in **-а** shift to **-о**, masculine words ending in hard consonants add **-е**, and masculine words ending in soft consonants or **-й** add **-ю**. By applying these simple vowel shifts, you ensure that your greetings, questions, and daily interactions flow smoothly and respect the traditional rules of Ukrainian communication. You will quickly find that these vowel shifts become automatic as your brain learns to associate the act of calling someone with adding these specific soft or hard sounds.

Keep this vocative quick reference guide handy as you practice forming the vocative case. It covers the most frequent patterns you will encounter in everyday conversation.

| Pattern | Nominative → Vocative | Example |
| :--- | :--- | :--- |
| Feminine **-а** | **-а** → **-о** | **Олена** → **Олено**, **мама** → **мамо** |
| Feminine **-ія** | **-ія** → **-іє** | **Марія** → **Маріє** |
| Feminine **-ся** | **-ся** → **-сю** | **бабуся** → **бабусю** |
| Masculine hard | + **-е** | **Тарас** → **Тарасе**, **брат** → **брате** |
| Masculine **-й** / soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю** |
| Special (**г**, **к**) | **г**→**ж**, **к**→**ч** + **-е** | **друг** → **друже** |
| Special (**-у**) | irregular | **тато** → **тату**, **син** → **синку** |

:::tip
Whenever you say **Привіт!** (Hi!), **Добрий день!** (Good day!), or ask **Як справи?** (How are you?), immediately follow it with the vocative form of the person's name or title!
:::

Before moving on to the next module, take a moment to self-check your understanding of these rules. How do you call your family? **мама** (mom) → ? **тато** (dad) → ? **брат** (brother) → ? How do you correctly greet your friend Taras? Most importantly, do you clearly feel the functional difference between the sentence **Марія прийшла** (Mariia came) and the direct command **Маріє, ходи сюди!** (Mariia, come here!)? If you can confidently answer these questions and apply the correct endings, you are ready to continue your Ukrainian journey.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: hey-friend
level: a1

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

**Level: A1.4+ (Module 42/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

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
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
