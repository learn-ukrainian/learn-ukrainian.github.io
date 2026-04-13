<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-concept.yaml` file for module **2: Зроблено чи в процесі? Вступ до виду дієслів** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-aspect-sorting -->`
- `<!-- INJECT_ACTIVITY: fill-in-identify-the-aspect-in-sentences -->`
- `<!-- INJECT_ACTIVITY: match-up-choose-the-correct-aspect-context-based -->`
- `<!-- INJECT_ACTIVITY: error-correction-fix-aspect -->`

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
## Що таке вид дієслова? (What is Verb Aspect?) (~550 words)

Imagine you are sitting on the comfortable couch with a good friend, watching an intensely competitive football match on television. The players are moving fast across the green field, the crowd is cheering loudly, and the sports commentary is flying rapidly. In such an exciting and dynamic situation, you might hear a conversation that sounds exactly like this:

> **Максим:** Дивись, він швидко біжить до воріт! *(Look, he is running fast to the goal!)*
> **Андрій:** Удар... і він забив красивий гол! *(A strike... and he scored a beautiful goal!)*
> **Максим:** Вони грають дуже добре сьогодні. *(They are playing very well today.)*
> **Андрій:** Так, вона класно передала м'яч. *(Yes, she passed the ball nicely.)*

In this short exchange, we can easily spot the core vocabulary of a sports match: the **гра** (game), the **гол** (goal), and the **м'яч** (ball). But if you look much closer at the verbs the friends are using, you will notice a hidden dimension of the Ukrainian language. This crucial grammatical dimension is formally called **вид дієслова** (verb aspect). It is a concept that changes everything about how you will build sentences from this point forward.

Aspect is not about *when* an action happens in the timeline of the universe, which is the specific job of grammatical tense. Instead, aspect describes exactly *how* the action unfolds in time. Let us compare the verbs from our football dialogue to see this clearly. When Maksym excitedly says «біжить» (is running), he is describing an action that is currently ongoing and active. You can picture the player's legs moving right now. However, when Andriy shouts «забив» (scored), he is not describing a continuous process at all. He is announcing an instantaneous, completed event that just occurred.

To truly understand and master Ukrainian verbs, you must formally meet the two fundamental types of aspect. The first type is the **недоконаний вид** (imperfective aspect). We use this aspect to describe an ongoing **процес** (process), a regular **повторення** (repetition) of an action, or simply to state a general, continuous fact. The second type is the **доконаний вид** (perfective aspect). This aspect is strictly reserved for a single, successfully completed **дія** (action) that has a clear, visible, and undeniable **результат** (result).

:::info
**Grammar box**
Most Ukrainian verbs exist in permanent pairs. You will learn one verb for the continuous process, and a slightly different "twin" verb for the completed result. Learning them together as a matching set is the absolute key to natural fluency.
:::

Кожне українське дієслово має своє спеціальне запитання. Якщо дія постійно триває, ми запитуємо «що робити?». Якщо ця дія має чіткий результат, ми запитуємо «що зробити?».

> *Every Ukrainian verb has its own special question. If the action is constantly ongoing, we ask "what to do?". If this action has a clear result, we ask "what to have done?".*

Let us look closer at those two essential questions that Ukrainian school children learn. The question for the imperfective aspect focuses purely on the activity itself. It does not care about the destination or the final outcome. The question for the perfective aspect adds a tiny prefix to the question word, which acts as a signal of completion. It demands to know what has been accomplished, achieved, or finalized.

A highly helpful way to remember this grammatical distinction is the classic movie analogy. Using the imperfective aspect is exactly like watching a film frame by frame. You are observing the action as it happens continuously, like watching someone **робити** (to do) their difficult homework. You do not know if they will ever finish it. Using the perfective aspect, on the other hand, is like finally seeing the "The End" screen at the conclusion of the film. The action is entirely finished, the story is over, and you can see the final product, meaning someone managed to successfully **зробити** (to do / to have done) their homework.

Вид дієслова — це важлива концепція, яку ви повинні добре відчути. Уявіть будь-який процес як довгу пряму лінію, а фінальний результат — як яскраву крапку в кінці цієї довгої лінії.

> *Verb aspect is an important concept that you must feel well. Imagine any process as a long straight line, and the final result as a bright dot at the end of this long line.*

There is one very important, unbreakable rule about the present tense in Ukrainian grammar. Actions that are happening right now, at this exact, fleeting moment, are always imperfective. They are active processes unfolding directly before your eyes. You logically cannot be in the middle of an instantaneous completion in the present moment. Therefore, perfective verbs simply do not have a true present tense form at all. If an action is happening now, it is a process, and it must be imperfective.

Зараз ми дивимося цікавий матч і вболіваємо за нашу улюблену команду. Цей процес відбувається прямо зараз, тому ми використовуємо тільки недоконаний вид.

> *Right now we are watching an interesting match and cheering for our favorite team. This process is happening right now, so we use only the imperfective aspect.*

<!-- INJECT_ACTIVITY: quiz-aspect-sorting --> [quiz, Aspect Sorting: Process vs. Result, 8 items]

## Недоконаний вид: Процес і повторення (Imperfective: Process & Repetition) (~660 words)

Let us take a deep dive into the first essential category, which is the **недоконаний вид** (imperfective aspect). Unlike the **доконаний вид** (perfective aspect) that focuses on sudden completion, the primary and most common function of the imperfective form is to describe a continuous **процес** (process). 

When you use these verbs, you are inviting the listener to step inside the timeline of the event and witness an ongoing **дія** (action). You are emphasizing the effort, the duration, or the simple reality that the activity was happening at a specific moment, regardless of whether it ever reached a conclusion. The focus is entirely on the journey, not the destination.

Я читав цікаву книгу, коли ти несподівано подзвонив. Учора весь вечір я прибирав у своїй кімнаті, але там досі брудно. Моя сестра готувала смачну вечерю, поки ми дивилися телевізор.

> *I was reading an interesting book when you unexpectedly called. Yesterday evening I was cleaning my room the whole time, but it is still dirty there. My sister was cooking a delicious dinner while we were watching television.*

The second core function of the imperfective aspect is to express regular, habitual, or frequent **повторення** (repetition). Whenever an action happens more than once, or is part of an established routine, it automatically becomes an imperfective concept. Even if each individual event was successfully completed on its own, the overarching pattern of doing it multiple times requires the imperfective form. You are not highlighting a single finished outcome, but rather a recurring cycle or a habit that defines a lifestyle.

Я читав цю популярну книгу три рази, тому що вона мені дуже подобається. Наші сусіди завжди купують свіжі овочі на місцевому ярмарку. Кожного ранку мій брат п'є чорну каву і слухає новини.

> *I read this popular book three times because I like it very much. Our neighbors always buy fresh vegetables at the local market. Every morning my brother drinks black coffee and listens to the news.*

The third distinct use of the imperfective aspect is stating a general fact. Sometimes, you only want to confirm whether an action took place at all, or state a universal truth, without focusing on any specific **результат** (result). You do not care if someone managed to successfully **зробити** (to do) a task completely. In these situations, the imperfective verb acts as a simple naming device for the activity. You are asking about the sheer existence of the event in history, or making a broad statement about how things generally operate in the world, completely ignoring the concept of completion.

Маленькі діти часто читають яскраві книги перед сном. Ти бачив новий український фільм у кінотеатрі? Ми вчора говорили про важливі проблеми нашої школи.

> *Small children often read bright books before bed. Did you see the new Ukrainian movie at the cinema? We were talking about the important problems of our school yesterday.*

Because the imperfective aspect is so strongly tied to habits and duration, it frequently pairs with specific signal words. These adverbs act as giant neon signs pointing directly to the imperfective form. When you see the following words, you almost always need to use an imperfective verb:

- **завжди** (always)
- **часто** (often)
- **зазвичай** (usually)
- **довго** (for a long time)
- **щодня** (every day)

These words inherently describe extended periods or recurring events. This fundamentally contradicts the idea of a single, sudden completion, making the imperfective aspect the only logical choice.

:::info
**Grammar box**
Signal words are your best friends when choosing the **вид дієслова** (verb aspect). If a sentence contains a word that implies routine or extended time, you can confidently select the imperfective form without overthinking it.
:::

Мій найкращий друг завжди допомагає мені робити складні завдання. Він щодня читає свіжі новини в інтернеті. Ми довго гуляли в парку, бо погода була чудова.

> *My best friend always helps me do difficult tasks. He reads fresh news on the internet every day. We walked in the park for a long time because the weather was wonderful.*

It is crucial to understand that aspect is completely separate from tense. The aspect simply describes the internal nature of the action, while the tense tells you when it happened on the calendar. You can have an imperfective process happening right now, or you can have an imperfective process that used to happen in the past. The core identity of the action remains exactly the same; only the time frame changes. This proves that focusing on the journey is a perspective you can apply across different periods of time.

Зараз я уважно читаю цікаву статтю про історію. Учора я також довго читав цей журнал у бібліотеці. Завтра я буду читати нові матеріали для нашого проєкту.

> *Right now I am carefully reading an interesting article about history. Yesterday I also read this magazine in the library for a long time. Tomorrow I will be reading new materials for our project.*

<!-- INJECT_ACTIVITY: fill-in-identify-the-aspect-in-sentences -->

## Доконаний вид: Результат! (Perfective: The Result!) (~660 words)

Now it is time to explore the other side of the coin: the **доконаний вид** (perfective aspect). While the **недоконаний вид** (imperfective aspect) focuses on an ongoing **процес** (process), the perfective aspect cares exclusively about the destination. Its absolute core meaning is a single, successfully completed action that has a clear boundary or a final outcome. This aspect acts like a snapshot of a finished event, capturing the exact moment when an activity reaches its goal.

When you use this aspect, you are declaring that an event was brought to its logical conclusion. The duration of the event no longer matters, and the effort spent getting there is irrelevant; the only important detail is that the final **результат** (result) was successfully achieved. Ukrainian mothers often explain this fundamental difference to their children when discussing household chores, highlighting how effort does not always equal completion.

Мати часто каже сину: «Прибирати й прибрати — різні дії!» Ти довго прибирав, але так і не прибрав свою кімнату.

> *A mother often tells her son: "To clean and to have cleaned are different actions!" You were cleaning for a long time, but you still have not cleaned your room.*

To truly understand the perfective aspect, we must contrast it directly with the imperfective forms we just learned. The difference between emphasizing a process and emphasizing a result completely changes the underlying meaning of a sentence. Let us look at how the verbs **робити** (to do) and **зробити** (to do) behave, or how reading works in both aspects. If you want to announce that you successfully finished a novel and are ready to discuss the ending, you must use the perfective form.

Учора я читав нову українську книгу весь вечір. Сьогодні вранці я нарешті прочитав цю книгу до кінця. Тепер я можу дати її тобі.

> *Yesterday I was reading a new Ukrainian book all evening. This morning I finally read this book to the end. Now I can give it to you.*

When you say you were reading, you only confirm the **дія** (action) itself was happening at some point. Maybe you finished the book, or maybe you abandoned it after three pages because it was boring. However, when you say you have read it, you guarantee that the text is finished, the story is complete, and the knowledge is firmly in your head.

Because the perfective aspect fundamentally describes a completed achievement, there is a crucial grammatical rule you must memorize. Perfective verbs have no true present tense. Think about it logically: you cannot be currently in the middle of completing a single, instantaneous result right now. An action is either ongoing as a process, or it is already completely done. Therefore, when you see a perfective verb that looks like it is conjugated in the present tense, it actually carries a future meaning.

:::info
**Grammar box**
Perfective verbs cannot happen "right now" because a result is instantaneous. Their "present" forms automatically point to the future. For example, the imperfective verb for writing in the present tense simply means "I am writing". But the perfective form automatically transforms the meaning into "I will write" or "I will finish writing".
:::

Я напишу цей важливий лист завтра вранці. Мій брат купить свіжі овочі на ярмарку. Ми зробимо це складне завдання разом.

> *I will write this important letter tomorrow morning. My brother will buy fresh vegetables at the market. We will do this difficult task together.*

For now, we will not worry about mastering the future tense. In this module, we will focus exclusively on using perfective verbs in the past tense. These forms are essential for marking finished events, historical facts, and personal achievements in your past. When you want to report that someone successfully did something, wrote something, or scored a point in a game, you will always reach for the past perfective form.

Мій улюблений футболіст забив красивий гол. Моя сестра написала чудову статтю для журналу. Студент зробив усі домашні вправи.

> *My favorite football player scored a beautiful goal. My sister wrote a wonderful article for the magazine. The student did all the homework exercises.*

These sentences do not describe what people were busy doing, nor do they imply any kind of **повторення** (repetition) over time. They strictly and cleanly report what these people successfully accomplished.

Just like the imperfective forms, perfective verbs have their own set of highly reliable signal words. These adverbs highlight suddenness, completion, or the successful achievement of a goal. When you see words like suddenly, finally, or already, you almost certainly need a perfective verb to complete the thought. However, you must be extremely careful with the tricky word for yesterday. This word simply sets the historical time frame, meaning it works perfectly with both aspects depending on your focus!

Раптом почався сильний дощ, але ми вже прийшли додому. Вчора я довго читав журнал, а мій друг вчора прочитав цілу книгу.

> *Suddenly a heavy rain started, but we had already arrived home. Yesterday I read a magazine for a long time, and my friend read a whole book yesterday.*

Notice how yesterday can frame both a long, ongoing activity and a sudden, completed achievement. Your choice of the **вид дієслова** (verb aspect) depends entirely on whether you want to emphasize the long time spent on the task or the final, successful outcome.

<!-- INJECT_ACTIVITY: match-up-choose-the-correct-aspect-context-based -->

## Порівняння пар: Бачимо різницю (Comparing Pairs: Seeing the Difference) (~330 words)

In Ukrainian, almost every verb has a partner. Together, they form an aspect pair to describe every possible situation, like **робити / зробити** (to do). Usually, the base word represents the **недоконаний вид** (imperfective aspect). To create its partner, the **доконаний вид** (perfective aspect), we most often simply add a short prefix to the beginning of the word.

Найчастіше ми утворюємо доконаний вид за допомогою префікса. Наприклад, ми беремо слово «писати» і додаємо префікс «на-». Тепер ми маємо пару: «писати» і «написати». Так само працюють слова «читати» і «прочитати».

> *Most often we form the perfective aspect using a prefix. For example, we take the word "писати" and add the prefix "на-". Now we have a pair: "писати" and "написати". The words "читати" and "прочитати" work the same way.*

This prefix does not change the core meaning, but it adds the crucial idea of completion and a final **результат** (result). Let us put these pairs side by side to see how the **вид дієслова** (verb aspect) completely changes the story. When you use the imperfective form, you invite the listener to watch a **процес** (process) unfold in real-time. 

Порівняймо два речення. «Він писав лист» означає, що дія тривала у минулому. Можливо, він ще пише цей лист зараз. Але «він написав лист» означає, що лист уже готовий. Інший приклад: «вона купувала продукти» проти «вона купила продукти».

> *Let's compare two sentences. "Він писав лист" means that the action was ongoing in the past. Perhaps he is still writing this letter now. But "він написав лист" means that the letter is already ready. Another example: "вона купувала продукти" versus "вона купила продукти".*

To master this concept, try visualizing the **дія** (action) on a timeline. Imagine the imperfective aspect as a long, continuous line (`------`) showing a lasting activity, or as a series of dots (`...`) representing the **повторення** (repetition) of a habit. In contrast, picture the perfective aspect as a single, solid dot (`•`) or an arrow hitting a brick wall (`--->|`). The activity hits that wall, stops completely, and leaves a permanent mark.

:::note
**Quick tip**
When you learn a new verb, always try to memorize its aspect pair right away. Knowing both forms is the key to speaking naturally and accurately describing your daily life.
:::

<!-- INJECT_ACTIVITY: error-correction-fix-aspect --> [error-correction, Find and fix wrong aspect choice in sentences, 6 items]
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-concept
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

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
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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

**Level: A2 (Module 2/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
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

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
