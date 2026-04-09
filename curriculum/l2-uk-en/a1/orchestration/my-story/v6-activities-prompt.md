<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-story.yaml` file for module **52: My Story** (a1).

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

- `<!-- INJECT_ACTIVITY: matching-tense-category -->`
- `<!-- INJECT_ACTIVITY: fill-in-signal-words -->`
- `<!-- INJECT_ACTIVITY: ordering-life-events -->`
- `<!-- INJECT_ACTIVITY: fill-in-biography-combined -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the life events in logical chronological order
  items:
  - Я народився в Торонто.
  - У дитинстві я жив з батьками.
  - Потім я вчився в університеті.
  - Зараз я живу в Києві і працюю програмістом.
  - Далі я буду подорожувати.
  type: ordering
- focus: Use signal words to determine the correct tense
  items:
  - Раніше я {жив|живу|буду жити} в Канаді.
  - Зараз я {працюю|працював|буду працювати} в університеті.
  - Далі я {буду вивчати|вивчав|вивчаю} українську мову.
  - У дитинстві вона {любила|любить|буде любити} читати.
  - Сьогодні ми {живемо|жили|будемо жити} в Україні.
  type: fill-in
- focus: Match the life event verb to the correct tense category
  pairs:
  - народився: Минулий час (Past)
  - переїхала: Минулий час (Past)
  - живу: Теперішній час (Present)
  - працюю: Теперішній час (Present)
  - буду подорожувати: Майбутній час (Future)
  - будемо вчитися: Майбутній час (Future)
  type: matching
- focus: Complete a biography combining all three tenses
  items:
  - Я {народилася|народився|народилися} у Львові.
  - Там я {вчилася|вчився|вчилися} в школі.
  - Зараз я {працюю|працювала|буду працювати} вчителькою.
  - Наступного року я {буду подорожувати|подорожувала|подорожую}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- подорожувати (to travel)
- закінчити (to finish/graduate)
- дитинство (childhood, n)
- університет (university, m)
- програміст (programmer, m)
- успіх (success, m)
- мрія (dream, f)
- батьки (parents, pl)
required:
- народитися (to be born)
- жити (to live)
- вчитися (to study)
- переїхати (to move)
- зараз (now)
- раніше (before/earlier)
- далі (further/next)
- розповідати (to tell/narrate)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Learning a language is about connecting with people. You already know how to state simple facts about yourself: your name, your country, and your profession. Now, it is time to move from simple facts to a cohesive narrative. A life story spans across time. You need to talk about where you were born, what you do now, and what you plan for the future. By combining the past, present, and future tenses, you can share your unique journey. 

When getting to know someone deeply, you will ask about their past and their plans. Read this interview between two friends.

> **Олег:** **Розкажи про себе!** *(Tell about yourself!)*
> **Марко:** **Я народився в Канаді, у Торонто.** *(I was born in Canada, in Toronto.)*
> **Олег:** **А зараз ти живеш тут?** *(And now do you live here?)*
> **Марко:** **Так, зараз я живу в Києві.** *(Yes, now I live in Kyiv.)*
> **Олег:** **Чому ти переїхав?** *(Why did you move?)*
> **Марко:** **Я хотів вивчати українську.** *(I wanted to study Ukrainian.)* **Мої бабуся і дідусь з України.** *(My grandmother and grandfather are from Ukraine.)*
> **Олег:** **А що ти будеш робити далі?** *(And what will you do next?)*
> **Марко:** **Я буду працювати тут і вчити мову.** *(I will work here and study the language.)*
> **Олег:** **Чудово! Успіхів тобі!** *(Wonderful! Success to you!)*

Notice how Marko moves smoothly through time. He starts in the past with **народився** (was born). Then, he uses the present tense **живу** (I live) to describe his current situation. Finally, he shifts to the future tense with **буду працювати** (I will work). In just a few sentences, he paints a complete picture of his life using three different grammatical timeframes.

Now, let us read Anna's story. She talks about her education and her career path.

> **Максим:** **Анно, розкажи свою історію.** *(Anna, tell your story.)*
> **Анна:** **Я народилася у Львові.** *(I was born in Lviv.)* **Там я вчилася в школі.** *(There I studied in school.)*
> **Максим:** **А університет?** *(And university?)*
> **Анна:** **Потім я переїхала в Київ і закінчила університет.** *(Then I moved to Kyiv and finished university.)*
> **Максим:** **Ким ти працюєш?** *(What do you work as?)*
> **Анна:** **Зараз я працюю вчителькою і живу в центрі міста.** *(Now I work as a teacher and live in the city center.)*
> **Максим:** **А що далі?** *(And what next?)*
> **Анна:** **Я буду подорожувати!** *(I will travel!)* **Я хочу побачити Японію.** *(I want to see Japan.)*
> **Максим:** **І ти будеш вчити японську?** *(And you will study Japanese?)*
> **Анна:** **Може! Але спочатку — українська для тебе!** *(Maybe! But first — Ukrainian for you!)*

Anna explains her sequence of life events clearly: Birth, School, University, Job, and Future Dream. Because Anna is a woman, she uses feminine past tense endings: **народилася** (was born), **вчилася** (studied), and **переїхала** (moved). Each stage of her life requires a specific grammatical form to show exactly when it happened.

## Три часи разом (Three Tenses Together)

To tell your biography, you need a "Time Line" that combines three main structures. First, the Past Tense (**Минулий час**). This uses gendered endings: **-в** for masculine, and **-ла** for feminine. Second, the Present Tense (**Теперішній час**). This uses person endings, like **-ю** or **-єш**. Third, the Compound Future Tense (**Майбутній час**). This uses the auxiliary verb **буду** plus an infinitive. Together, they organize your story.

Let us look at a grandparent telling their life story to their grandchildren. This perfectly demonstrates the Past Tense.

> **Дідусь:** **Я народився в селі.** *(I was born in a village.)*
> **Онук:** **Там була школа?** *(Was there a school there?)*
> **Дідусь:** **Так, я ходив у школу.** *(Yes, I went to school.)*

The verb **народитися** means "to be born". It is almost always used in the past tense. A man says **я народився**, and a woman says **я народилася**. Other key verbs are **жити** (to live) and **вчитися** (to study).
*   **Він жив у селі.** (He lived in a village.)
*   **Вона жила у місті.** (She lived in a city.)
*   **Я вчився в університеті.** (I studied at the university. — masculine)

Next, you ground your story in the present. Use the adverb **зараз** (now) to show you are talking about today. The Present Tense uses endings that match the person speaking.
*   **Зараз я живу в місті.** (Now I live in a city.)
*   **Зараз я працюю в лікарні.** (Now I work in a hospital.)
*   **Я вивчаю українську мову.** (I study the Ukrainian language.)

These actions are happening right now in your timeline. 

Finally, you look forward. The Future Tense describes your plans and dreams. Use the words **потім** (then) and **далі** (further) to signal a shift into the future. Form the future by taking **буду** (I will) and adding an infinitive verb.
*   **Потім я буду жити в Одесі.** (Then I will live in Odesa.)
*   **Далі ми будемо подорожувати.** (Further we will travel.)
*   **Я буду відпочивати на дачі.** (I will rest at the dacha.)

Signal words are crucial. They tell the listener which tense is coming before you even say the verb. Here is a table of the most important signal words for your life story:

| Signal Word | Meaning | Tense Trigger |
| :--- | :--- | :--- |
| **раніше** | before / earlier | Past |
| **у дитинстві** | in childhood | Past |
| **коли я був маленьким** | when I was little (masc) | Past |
| **зараз** | now | Present |
| **сьогодні** | today | Present |
| **цього року** | this year | Present |
| **потім** | then | Future |
| **далі** | further / next | Future |
| **наступного року** | next year | Future |

If you start a sentence with **раніше**, your listener automatically expects a past tense verb.

<!-- INJECT_ACTIVITY: matching-tense-category -->

<!-- INJECT_ACTIVITY: fill-in-signal-words -->

## Моя історія (My Story)

Now, read a complete model story. This is Taras's life. Notice how he connects simple sentences into a full biography.

*   **Я народився в Одесі у тисяча дев'ятсот дев'яносто п'ятому році.** (I was born in Odesa in nineteen ninety-five.)
*   **Я жив там з батьками і сестрою.** (I lived there with parents and sister.)
*   **Я ходив у школу і любив математику.** (I went to school and loved math.)
*   **Потім я переїхав у Київ і вчився в університеті.** (Then I moved to Kyiv and studied in the university.)
*   **Зараз я живу в Києві.** (Now I live in Kyiv.)
*   **Я працюю програмістом.** (I work as a programmer.)
*   **Я люблю свою роботу.** (I love my work.)
*   **У вільний час я граю у футбол і читаю книжки.** (In free time I play football and read books.)
*   **Далі я буду подорожувати.** (Next I will travel.)
*   **Я буду вивчати англійську.** (I will study English.)
*   **І я буду жити в Києві — це моє місто!** (And I will live in Kyiv — this is my city!)

Taras's story uses a clear structure taught in Ukrainian schools. It has three parts. First is the **Зачин** (Introduction) — he states his birth and childhood. Second is the **Основна частина** (Main Part) — he describes his current life, job, and hobbies. Third is the **Кінцівка** (Conclusion) — he shares his future plans and his feelings about his city.

A key verb for storytelling is **переїхати** (to move). It acts as a bridge between locations and times in your life. Another important verb is **закінчити** (to finish / to graduate). When you talk about the future, you can mention a **мрія** (dream). Using **переїхати** physically changes the setting of your narrative from your past home to your present home.

Now it is your turn to tell your story. You will write a short biography of 8 to 10 sentences. Follow these steps. Start with the past. Use these sentence starters:
*   **Я народився в...** (I was born in...) or **Я народилася в...** (for women).
*   **Я жив у...** (I lived in...) or **Я жила у...**
*   **Я вчився в...** (I studied in...) or **Я вчилася в...**
*   **Я працював...** (I worked...) or **Я працювала...**

Then, move to the present.
*   **Зараз я живу в...** (Now I live in...)
*   **Я працюю...** (I work...)
*   **Я вивчаю українську...** (I study Ukrainian...)

Finally, finish with the future.
*   **Далі я буду...** (Next I will...)
*   **Я хочу...** (I want...)

Use at least three past verbs, three present verbs, and three future constructions.

<!-- INJECT_ACTIVITY: ordering-life-events -->

<!-- INJECT_ACTIVITY: fill-in-biography-combined -->

## Summary

You can now tell a complete life story. The three-tense system is your timeline. Here is a final recap:

| Tense | Form | Example |
| :--- | :--- | :--- |
| **Минулий** (Past) | **-в** (m), **-ла** (f), **-ли** (pl) | **Я народився.** (I was born.) / **Я жила.** (I lived.) |
| **Теперішній** (Present) | **-ю**, **-єш**, **-є** (person endings) | **Я живу.** (I live.) / **Ти працюєш.** (You work.) |
| **Майбутній** (Future) | **буду**, **будеш**, **буде** + infinitive | **Я буду працювати.** (I will work.) |

Let us check your core vocabulary for this module. You need these eight words to narrate your journey:
*   **народитися** (to be born): **Я народився в Америці.** (I was born in America.)
*   **жити** (to live): **Ми живемо в місті.** (We live in the city.)
*   **вчитися** (to study): **Вона вчиться в школі.** (She studies at school.)
*   **переїхати** (to move): **Я хочу переїхати в Україну.** (I want to move to Ukraine.)
*   **зараз** (now): **Зараз він працює.** (Now he is working.)
*   **раніше** (before / earlier): **Раніше я жив там.** (Before I lived there.)
*   **далі** (further / next): **Що ти будеш робити далі?** (What will you do next?)
*   **розповідати** (to tell / narrate): **Я люблю розповідати історії.** (I love to tell stories.)

Before you finish this module, use this self-check checklist:
*   Can you state where you were born using the correct gender agreement (**народився** or **народилася**)?
*   Can you use the word **зараз** to describe your current job or study?
*   Can you list two things you will do next year using **буду**?
*   Do you know the difference between **раніше** (before) and **потім** (then)?
*   Have you written your own 8-10 sentence narrative using all three tenses?

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-story
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

**Level: A1.4+ (Module 52/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
