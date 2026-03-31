<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-concept.yaml` file for module **2: Зроблено чи в процесі? Вступ до виду дієслів** (a2).

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

(No injection markers found in prose. All activities will go to workbook.)

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Aspect Sorting: Process vs. Result'
  items: 8
  type: quiz
- focus: Identify the Aspect in Sentences
  items: 8
  type: fill-in
- focus: Choose the Correct Aspect (Context-based)
  items: 8
  type: match-up
- focus: Find and fix wrong aspect choice in sentences (e.g., *Він щодня зробив вправи
    → робив, *Вона довго написала листа → писала)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- завершений (completed, finished)
- тривалий (ongoing, lasting)
- одноразовий (single, one-time)
- концепція (concept)
required:
- вид дієслова (verb aspect)
- недоконаний вид (imperfective aspect)
- доконаний вид (perfective aspect)
- процес (process)
- результат (result)
- дія (action)
- повторення (repetition)
- робити / зробити (to do)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що таке вид дієслова?

Two friends are watching a football match on TV. The striker rushes toward the goal — «Він біжить!» Then the ball hits the net — «Він забив гол!» Same player, two moments. But notice: Ukrainian used two completely different verbs. «Біжить» captures the running *as it happens* — you can almost see the legs moving. «Забив» captures a done deal — the goal exists, the scoreboard changed. This difference is not about *when* something happened. It is about *how* the action unfolds. Ukrainian has a name for this hidden layer: **вид дієслова** (verb aspect).

Every Ukrainian verb carries aspect. There are exactly two kinds: **недоконаний вид** (imperfective aspect), abbreviated **НВ**, and **доконаний вид** (perfective aspect), abbreviated **ДВ**. Aspect is not tense. Tense tells you *when* — yesterday, now, tomorrow. Aspect tells you *how* — is the action a process that is unfolding, or is it a completed result that already exists? Here is your first pair: **писати** (to write, НВ) and **написати** (to write and finish, ДВ). Same action, different perspective.

Think of it like watching a movie. Imperfective is the film playing — the camera rolls, scenes unfold, you are inside the story. Perfective is the screen that reads «Кінець» (The End) — the story is over, the result is final. Here is another way to see it, straight from the kitchen. «Варити борщ» (НВ) — the pot is on the stove, steam is rising, someone is stirring. «Зварити борщ» (ДВ) — the stove is off, the borsch is ready, grab a bowl.

How can you tell which aspect you need? Ask yourself what question the verb answers:

- **НВ** answers: What was happening? How long did it last? How often did it repeat?
- **ДВ** answers: What got done? What is the result?

Here are four common pairs. Notice that the ДВ verb usually adds a **prefix** to the НВ verb — this is the most frequent pattern in Ukrainian:

| НВ (process) | ДВ (result) |
|---|---|
| **читати** (to read) | **прочитати** (to finish reading) |
| **робити** (to do) | **зробити** (to get done) |
| **писати** (to write) | **написати** (to finish writing) |
| **вчити** (to study) | **вивчити** (to master) |

Now let's return to that football match. Listen to Андрій and Олена commenting on the game:

> **Андрій:** Він біжить так швидко!
>
> **Олена:** Він передав м'яч!
>
> **Андрій:** Вони грають добре сьогодні.
>
> **Олена:** О, вона забила гол!
>
> **Андрій:** Суперники атакують.
>
> **Олена:** Нарешті! Ми виграли матч!

Did you feel the difference? Some lines describe action unfolding right now — the camera is rolling. Other lines announce a result — something just happened and the outcome is clear. Let's label each one:

- «Він біжить так швидко!» — **НВ**. The running is in progress. We are watching it happen.
- «Він передав м'яч!» — **ДВ**. The pass is complete. The ball is already with another player.
- «Вони грають добре сьогодні.» — **НВ**. The match is still going. The playing continues.
- «О, вона забила гол!» — **ДВ**. The ball crossed the line. A single completed moment.
- «Суперники атакують.» — **НВ**. The attack is unfolding right now.
- «Нарешті! Ми виграли матч!» — **ДВ**. The final whistle blew. The victory is a fact.

The pattern is simple: if the action is still happening — НВ. If the result already exists — ДВ.

<!-- INJECT_ACTIVITY: quiz, Aspect Sorting: Process vs. Result -->


## Недоконаний вид: Процес і повторення

Now that you can tell НВ from ДВ at a glance, it is time to practise recognising imperfective verbs in real situations. There are three contexts where Ukrainian requires НВ — think of them as three doors that all lead to the same verb form:

1. **Action in progress** at a specific moment — «Я читав, коли ти подзвонив.»
2. **Repeated or habitual action** — «Я читав цю книгу три рази.» / «Діти читають книги щодня.»
3. **General fact or permanent state** — «Вона добре співає.»

Whenever the situation fits one of these three doors, reach for an imperfective verb. Let's walk through each one.

### Door 1: Action in progress

Imagine a scene: someone is doing something, and then another event interrupts. The background action — the one already happening — is always НВ. The interruption that breaks into the scene is usually ДВ. Think of it as a film playing on screen: the imperfective verb is the movie rolling, and the perfective verb is someone pressing pause.

> «Я читав, коли телефон задзвонив.»

«Читав» (was reading) — НВ, the background. «Задзвонив» (rang) — ДВ, the interruption.

> «Вони грали у футбол, коли пішов дощ.»

«Грали» (were playing) — НВ, the scene. «Пішов» (started, came down) — ДВ, the interruption.

> «Мама варила вечерю, коли я повернувся додому.»

«Варила» (was cooking) — НВ, still in progress. «Повернувся» (came back) — ДВ, single completed action.

Notice the pattern: in every sentence, the НВ verb sets the stage, and the ДВ verb breaks into it. The movie was playing — then someone pressed pause.

### Door 2: Repeated and habitual actions

When an action happens more than once — a daily routine, a weekly habit, a pattern — Ukrainian uses НВ. There is a set of signal adverbs that point straight to imperfective. Learn them, and choosing the right aspect becomes much easier:

- **завжди** (always)
- **часто** (often)
- **зазвичай** (usually)
- **щодня** (every day)
- **іноді** (sometimes)
- **ніколи** (never)

When you see one of these words in a sentence, НВ is almost always the correct choice. The action is a pattern, not a single unique event.

> «Він завжди читає перед сном.»

He always reads — a habit, not one particular evening.

> «Вона часто дзвонила бабусі.»

She often called grandma — many times, a repeated pattern.

> «Ми щодня робили вправи.»

We did exercises every day — a routine, over and over.

The rule is simple: if the action repeats, use НВ.

### Door 3: General facts and permanent states

Some actions are not processes and not habits — they are simply true all the time. A permanent characteristic, a general ability, a fact about the world. These also take НВ, and this is the easiest context of the three: nothing is being completed, nothing is changing, so there is no room for ДВ.

> «Кіт спить вдень.»

A cat sleeps during the day — that is what cats do.

> «Вона добре малює.»

She draws well — a skill she has, not one drawing she finished.

> «Вони не їдять м'яса.»

They don't eat meat — a permanent fact about their life.

No surprise, no completion, no single moment — just a general truth. НВ every time.

### НВ in the present tense

Imperfective verbs are the only verbs in Ukrainian that have a true present tense — action happening right now. Here is «читати» (to read) conjugated in the present:

| | Singular | Plural |
|---|---|---|
| 1st person | читаю | читаємо |
| 2nd person | читаєш | читаєте |
| 3rd person | читає | читають |

This is important: ДВ has no present tense at all. When you conjugate a perfective verb the same way, the form looks like present tense — but it means future. «Прочитаю» does not mean "I am finishing reading" — it means "I will finish reading." We will explore this in the next section. For now, remember: only НВ can describe what is happening at this very moment.

### Діалог: Соломія дзвонить Василю

> **Соломія:** Привіт, Василю! Що ти зараз робиш?
>
> **Василь:** Читаю нову книгу. А ти?
>
> **Соломія:** Готую обід. А що ти зазвичай робиш щонеділі?
>
> **Василь:** Зазвичай ходжу на ринок і готую обід.
>
> **Соломія:** Ти часто готуєш?
>
> **Василь:** Так, завжди готую сам.

Every verb in this dialogue is НВ. Let's label each one:

- «Що ти зараз **робиш**?» — action in progress (Door 1). She asks what he is doing right now.
- «**Читаю** нову книгу.» — action in progress (Door 1). He is reading at this moment.
- «**Готую** обід.» — action in progress (Door 1). She is cooking right now.
- «Зазвичай **ходжу** на ринок і **готую** обід.» — habitual action (Door 2). Signal word: «зазвичай».
- «Ти часто **готуєш**?» — habitual action (Door 2). Signal word: «часто».
- «Завжди **готую** сам.» — habitual action (Door 2). Signal word: «завжди».

Notice how the same verb «готую» appears in two different contexts — present action and habitual action — and both times it is НВ. The aspect stays the same because both doors lead to imperfective.

<!-- INJECT_ACTIVITY: fill-in, Identify the Aspect in Sentences, 8 items -->


## Доконаний вид: Результат!

Now we turn to the other side of Ukrainian aspect. If НВ is about the process — watching the action unfold — then **доконаний вид** (ДВ, perfective aspect) is about the finish line. ДВ tells us that an action happened once, it is complete, and a result exists right now. The question to ask yourself is simple: *"Is the action done? Does a result exist?"* If the answer is yes — ДВ. Compare these two sentences:

> «Я читав книгу.»

> «Я прочитав книгу.»

The first sentence (НВ) tells us about a process — I was reading a book. Maybe I finished it, maybe I didn't. The sentence does not care about the ending. The second sentence (ДВ) tells us about a result — I read the book and it is finished. I now know what is in that book. The difference between «читав» and «прочитав» is not *when* the action happened — both are past tense. The difference is *whether the completion matters*.

### ДВ in past tense — your safe starting zone

Past tense is the most natural place to use ДВ. One event happened, it is done, the result exists. Here is «написати» (to write — perfective) conjugated in the past:

| | Masculine | Feminine | Neuter | Plural |
|---|---|---|---|---|
| Past | написав | написала | написало | написали |

Notice there is no first/second/third person distinction in the past — only gender and number. Four sentences with ДВ in the past:

> «Вона написала листа другові.» She wrote a letter to her friend — the letter is finished.

> «Він зробив домашнє завдання.» He did his homework — it is complete.

> «Ми прочитали цю книгу за тиждень.» We read this book in a week — the whole book, start to finish.

> «Вчора я вивчив десять нових слів.» Yesterday I learned ten new words — all ten, done.

Every sentence describes a single event with a clear result. That is what makes past tense the safest context for ДВ at your level — one event, it happened, it is done.

### ДВ has no true present tense

This is a critical detail that surprises many learners. If you take the perfective verb «прочитати» and conjugate it like a present-tense verb, you get «прочитаю». But «прочитаю» does not mean "I am finishing reading right now." It means "I will read it and finish." The form looks like present tense, but the meaning is future. This is a peculiarity of Ukrainian aspect: the perfective "present" form always points forward to a future result. Compare:

> «Я читаю зараз.» I am reading right now — НВ, true present, action in progress.

> «Я прочитаю цю статтю за годину.» I will read this article in an hour — ДВ, future meaning, result expected.

For this module, stay in past tense with ДВ. That is where the system is simplest and clearest.

### Signal words for ДВ

Just as НВ has its signal words — «завжди», «часто», «щодня» — ДВ has its own markers. These words point to single, completed events:

- **вчора** (yesterday) — a single event, not a habit
- **раптом** (suddenly) — something happened in one instant
- **нарешті** (finally) — a long wait, then completion
- **одразу** (at once) — immediate result
- **за годину / за тиждень** (in an hour / in a week) — time it took to complete

Notice the contrast with НВ signal words. «Щодня» (every day) points to repetition — НВ. «Раптом» (suddenly) points to a single moment — ДВ. The signal word tells you which aspect fits:

> «Раптом він упав.» Suddenly he fell — one instant, one event.

> «Нарешті вона зрозуміла задачу.» She finally understood the problem — the result arrived.

> «Він одразу відповів на питання.» He answered the question at once — immediate, complete.

> «Ми прочитали книгу за три дні.» We read the book in three days — start to finish, done.

### Діалог: Після матчу

The football match is over. Андрій and Олена discuss what happened:

> **Андрій:** Хто забив перший гол?

> **Олена:** Олексієнко забив на двадцять третій хвилині.

> **Андрій:** А потім?

> **Олена:** Потім суперники швидко відповіли — Мельник одразу зрівняв рахунок.

> **Андрій:** Хто виграв?

> **Олена:** Наша команда нарешті перемогла! Вони зробили це!

Every verb in this dialogue is ДВ. The match is over, and each verb describes a single completed event with a clear result:

- «**забив**» — scored (one goal, one moment)
- «**відповіли**» — answered back (one counter-attack, complete)
- «**зрівняв**» — equalized (the score changed — result)
- «**перемогла**» — won (the match ended in victory — result)
- «**зробили**» — did it (achievement, complete)

Compare this to the НВ dialogue in the previous section, where Соломія and Василь talked about what they were doing and what they usually do. Here, everything has already happened. The results are in.

### Common mistakes with ДВ

Learners often reach for ДВ when НВ is needed — or the reverse. Here are natural traps to watch for:

**Trap 1: Daily habit with ДВ.** «Він щодня зробив вправи» — ❌. The signal word «щодня» means every day, a repeated action. That is НВ territory: «Він щодня робив вправи.»

**Trap 2: Long duration with ДВ.** «Вона довго написала листа» — ❌. The word «довго» (for a long time) emphasizes the process, not the result. НВ: «Вона довго писала листа.»

**Trap 3: Completion implied but НВ used.** «Я читав усю книгу минулого тижня» — this is ambiguous. НВ «читав» focuses on the process, but «усю книгу» (the whole book) implies you finished it. If the result matters — and it usually does when you say "the whole book" — use ДВ: «Я прочитав усю книгу минулого тижня.»

These are not failures — they are the natural growing pains of learning aspect. The key question always works: *Is the completion and result what I want to communicate?* If yes — ДВ. If no — НВ.

<!-- INJECT_ACTIVITY: match-up, Choose the Correct Aspect (Context-based), 8 items -->


## Порівняння пар: Бачимо різницю (Comparing Pairs: Seeing the Difference)

Now put the two aspects side by side. Each pair below uses the same verb root — one НВ, one ДВ — in the past tense. Read both sentences and feel the difference:

| НВ (процес) | ДВ (результат) |
|---|---|
| «Він писав лист.» — He was writing a letter. Maybe he finished, maybe not. The process is what matters. | «Він написав лист.» — He wrote the letter. It is done. The letter exists. |
| «Вона читала книгу.» — She was reading a book. We see the action unfolding. | «Вона прочитала книгу.» — She read the book. Cover to cover, finished. |
| «Діти робили домашнє завдання.» — The kids were doing homework. They were in the middle of it. | «Діти зробили домашнє завдання.» — The kids did their homework. It is complete. |
| «Він вчив нові слова.» — He was studying new words. The learning process was happening. | «Він вивчив нові слова.» — He learned the new words. He knows them now. |

In every pair, the НВ sentence leaves the action open — we do not know if it ended. The ДВ sentence closes it — the result is here.

Picture two timelines. The НВ timeline is a long arrow stretching across time with no endpoint — the action fills that space, like a river flowing. You see the movement, but there is no stop sign. The ДВ timeline looks different: a single dot on the time axis with a star (★) at the end — the moment of completion. The action hits its target and stops there. «Він писав» is the river. «Він написав» is the arrow that reached the target.

This is the heart of aspect. НВ shows you the action from inside — you are standing in the middle of the river, watching it flow around you. ДВ shows you the action from outside — you see the finished product, the result sitting on the table.

### Швидка перевірка (Quick Self-Check)

Before moving on, test yourself with these four questions. No grade — just anchors for your thinking:

**1.** Яке питання задати, щоб вибрати НВ?

*"Is this a process or a habit?"* — if yes, НВ.

**2.** Яке питання задати для ДВ?

*"Is the action completed? Does a result exist?"* — if yes, ДВ.

**3.** Яке слово-підказка вказує на НВ?

«Завжди», «часто», «щодня» — repetition and routine.

**4.** А на ДВ?

«Нарешті», «раптом», «вчора» (for a single event) — completion and result.

Come back to these four questions any time you are unsure which aspect to use. They work every time.

<!-- INJECT_ACTIVITY: error-correction, Find and fix wrong aspect choice, 6 items -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-concept
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

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 2/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present
- **fill-in** — Відмінюй дієслово: Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Find incorrectly conjugated verb and fix it

### Pattern: grammar-verb-aspect
- **group-sort** — Доконаний чи недоконаний?: Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Identify aspect of a given verb


**Use these patterns.** If the pattern library recommends `divide-words` for a syllable module, generate a `divide-words` exercise. If it recommends `group-sort` for gender, generate a `group-sort`. The patterns encode how Ukrainian teachers actually test these concepts.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Every activity MUST have at least 6 items.** Quiz = 6+ questions. Fill-in = 6+ sentences. Match-up = 6+ pairs. True-false = 6+ statements. Group-sort = 6+ items per group minimum. Anagram = 6+ words.
- If you can't think of 6 items, add more examples from the module's vocabulary and content. NEVER submit an activity with fewer than 6 items.
- **3-5 options per quiz/fill-in question** — enough to prevent guessing, not so many to overwhelm.

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
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp__rag__verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp__rag__verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp__rag__verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp__rag__query_pravopys` or `mcp__rag__search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
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
