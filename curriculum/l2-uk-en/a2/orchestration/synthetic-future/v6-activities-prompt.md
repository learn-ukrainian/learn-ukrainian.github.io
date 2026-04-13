<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/synthetic-future.yaml` file for module **41: Я напишу!** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-sort-verb-forms-into-two-groups-synthetic-future-perfective-and-analytical-future-imperfective -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-synthetic-perfective-future-forms-based-on-context -->`
- `<!-- INJECT_ACTIVITY: unjumble-future-sentences -->`
- `<!-- INJECT_ACTIVITY: fill-in-future-aspect -->`
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete sentences with the correct future form (synthetic perfective or
    analytical imperfective) based on context
  items: 8
  type: fill-in
- focus: Identify whether a future sentence uses synthetic or analytical future and
    explain the aspect choice
  items: 8
  type: quiz
- focus: Sort verb forms into two groups — synthetic future (perfective) and analytical
    future (imperfective)
  items: 8
  type: group-sort
- focus: Reorder words to form correct future tense sentences using both synthetic
    (напишу) and analytical (буду писати) forms
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- приїхати (to arrive — pf.)
- обіцяти (to promise)
- планувати (to plan)
- прибирати / прибрати (to clean up — impf./pf.)
required:
- майбутній час (future tense)
- простий (simple, synthetic)
- складений (compound, analytical)
- сказати / скажу (to say/tell — pf. future)
- написати / напишу (to write — pf. future)
- зробити / зроблю (to do — pf. future)
- буду (I will — auxiliary)
- прочитати (to read through — pf.)
- подзвонити (to call — pf.)
- купити (to buy — pf.)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Два майбутніх часи (~450 words)

Новий рік — це завжди особливий час для нових планів, великих мрій і важливих обіцянок. Група друзів зустрічається, щоб весело відсвяткувати це свято разом. Вони сидять за великим столом, їдять смачні традиційні страви і довго говорять про майбутнє. Кожен має свої цікаві цілі на наступний рік. Вони жваво обговорюють, що саме хочуть змінити у своєму житті. Хтось планує багато подорожувати, хтось хоче знайти нову престижну роботу або швидко вивчити іноземну мову. Усі друзі дуже радісні, енергійні та повні світлих надій.

> *New Year is always a special time for new plans, big dreams, and important promises. A group of friends meets to merrily celebrate this holiday together. They sit at a large table, eat delicious traditional dishes, and talk for a long time about the future. Everyone has their own interesting goals for the next year. They actively discuss exactly what they want to change in their lives. Someone plans to travel a lot, someone wants to find a new prestigious job or quickly learn a foreign language. All the friends are very joyful, energetic, and full of bright hopes.*

> — **Олена:** У новому році я обов'язково напишу книгу! *(In the new year, I will definitely write a book!)*
> — **Марко:** А я вивчу іспанську мову. *(And I will learn Spanish.)*
> — **Софія:** Мій брат прочитає п'ятдесят книг за рік! *(My brother will read fifty books in a year!)*
> — **Максим:** А моя сестра нарешті складе важливий іспит. *(And my sister will finally pass an important exam.)*

:::note
**Quick tip:** When talking about academic tests, Ukrainian uses the phrase **складати / скласти іспит** (to take / pass an exam). Never use the Russian calque "здавати іспит".
:::

When we listen to these friends, we notice something fascinating about how they express their goals. In English, there is one primary way to talk about the future, usually by simply adding the word "will" before the main verb. However, Ukrainian grammar has two distinct ways to form the **майбутній час** (future tense). The choice between these two forms has absolutely nothing to do with formality or style. Instead, it is entirely about the aspect of the verb.

The first type is the **простий** (simple, synthetic) future tense. It is formed using perfective verbs. Because perfective verbs describe completed actions, they do not have a true present tense. Instead, when you conjugate them, they automatically point to the future. For example, the pair **сказати / скажу** (to say/tell — pf. future) shows this shift. Similarly, **написати / напишу** (to write — pf. future) guarantees a finished text.

You will use this synthetic future for single, completed actions. For instance, the pair **зробити / зроблю** (to do — pf. future) indicates a successfully completed task. If you plan to reach the end of a novel, you will use **прочитати** (to read through — pf.). If you need to acquire a new item, you choose **купити** (to buy — pf.). These forms ensure that the action will produce a final, tangible result.

When you need to contact someone quickly by phone, you will select **подзвонити** (to call — pf.). On the other hand, the second type of future is the **складений** (compound, analytical) future tense. We use this analytical form exclusively with imperfective verbs to describe ongoing or repeated actions. To build it, you only need to conjugate the auxiliary verb **буду** (I will — auxiliary) and add an imperfective infinitive.

<!-- INJECT_ACTIVITY: group-sort-sort-verb-forms-into-two-groups-synthetic-future-perfective-and-analytical-future-imperfective -->

## Простий майбутній час (~550 words)

The **простий** (simple, synthetic) **майбутній час** (future tense) is formed exclusively using perfective verbs. Because perfective verbs describe an action that is fully completed, they cannot physically happen "right now" in the present moment. An action is either ongoing, or it is completely finished. Therefore, perfective verbs do not have a true present tense. When you conjugate a perfective verb using the standard present-tense endings you already know, the meaning automatically shifts to the future. It points to a completed action that will happen later.

Ми використовуємо цей час, коли говоримо про конкретний результат у майбутньому. Ви вже чудово знаєте, як відмінювати дієслова в теперішньому часі. Тепер ви просто берете доконане дієслово і додаєте ті самі закінчення.

> *We use this tense when we talk about a concrete result in the future. You already know perfectly well how to conjugate verbs in the present tense. Now you simply take a perfective verb and add the exact same endings.*

Let's look at the first conjugation. You simply take the stem of the perfective verb and apply the standard endings. There are no new endings to memorize here. For example, the perfective verb **прочитати** (to read through — pf.) uses these simple forms. You say: я прочитаю, ти прочитаєш, він прочитає. For multiple people: ми прочитаємо, ви прочитаєте, вони прочитають. This pattern is very reliable.

Ще один важливий приклад — це дієслово «поїхати». Воно має такі самі знайомі закінчення. Ви кажете: я поїду, ти поїдеш, він поїде. У множині це: ми поїдемо, ви поїдете, вони поїдуть. Ця форма описує поїздку, яка точно відбудеться.

:::info
**Grammar box** — Do not confuse the English "will" with the Ukrainian forms here. The Ukrainian synthetic future does not use an extra helper word. The future meaning is built directly into the perfective verb itself.
:::

Now let's examine the second conjugation perfective verbs. The rules here are also identical to the present tense, including the consonant mutations in the first person singular. For instance, the perfective verb "побачити" (to see) changes the consonant "т" to "ч": я побачу, ти побачиш, він побачить, ми побачимо, ви побачите, вони побачать. Another common example is the verb **зробити / зроблю** (to do — pf. future).

З цим дієсловом ми бачимо типове додавання літери «л» після губного приголосного «б». Подивіться на ці форми. В однині ми кажемо: я зроблю, ти зробиш, він зробить. У множині: ми зробимо, ви зробите, вони зроблять. Ви вже добре знаєте це правило з дієслова «робити».

> *With this verb, we see the typical addition of the letter "л" after the labial consonant "б". Look at these forms. In the singular we say: я зроблю, ти зробиш, він зробить. In the plural: ми зробимо, ви зробите, вони зроблять. You already know this rule well from the verb "робити".*

You will use the **простий** future tense exclusively for a single, completed action in the future that will produce a clear result. It focuses entirely on the successful achievement of a goal, not on the process or duration. You want to emphasize that the task will be done. For example, consider the verb **написати / напишу** (to write — pf. future).

Коли я кажу, що я напишу листа, це означає чудовий результат. Лист точно буде готовий. Я почну і повністю закінчу цю дію. Якщо мій брат прочитає книгу, він дочитає її до кінця.

In daily life, Ukrainians constantly use specific perfective verbs to make firm plans and promises. These verbs are absolutely essential for everyday communication and building relationships. You will often hear verbs like **подзвонити** (to call — pf.), **купити** (to buy — pf.), or **сказати / скажу** (to say/tell — pf. future) when people arrange meetings, share news, or go shopping.

Я обов'язково подзвоню тобі завтра вранці. Ми точно купимо свіжий хліб і молоко. Я швидко приїду на вокзал. Я скажу йому всю правду про цю ситуацію.

> *I will definitely call you tomorrow morning. We will exactly buy fresh bread and milk. I will quickly arrive at the train station. I will tell him the whole truth about this situation.*

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-synthetic-perfective-future-forms-based-on-context -->

## Складений майбутній час (~550 words)

Now let's look at the second way to talk about the future in Ukrainian. When we want to describe an action that is ongoing, continuous, or repeated, we must use imperfective verbs. However, imperfective verbs cannot express the future tense on their own because their conjugated forms describe the present. They need a helper word to point to the future. To form the **складений** (compound, analytical) future tense, we combine the conjugated future tense of the helper verb "бути" with the imperfective infinitive of the main verb. This structure might feel familiar because it is similar to how English uses "will be" plus an "-ing" verb. It specifically emphasizes the process, the duration, or the routine of the action.

Допоміжне дієслово «бути» має свої спеціальні форми для майбутнього часу. Їх потрібно добре запам'ятати. Ось як ми його відмінюємо в однині. Я **буду**, ти будеш, він або вона буде. У множині форми такі: ми будемо, ви будете, вони будуть. Це єдине слово в конструкції, яке змінюється. Головне дієслово завжди залишається в інфінітиві і ніколи не втрачає своє закінчення.

> *The auxiliary verb "бути" has its own special forms for the future tense. You need to remember them well. Here is how we conjugate it in the singular. I will be, you will be, he or she will be. In the plural, the forms are: we will be, you will be, they will be. This is the only word in the construction that changes. The main verb always remains in the infinitive and never loses its ending.*

:::info
**Grammar box** — The helper verb does all the grammatical work in the compound future tense. It shows exactly who is doing the action. The second verb just tells you what the action is, so it must stay in its basic dictionary form (usually ending in -ти).
:::

Давайте подивимося на прості і життєві приклади. Увечері я буду читати цікаву статтю про історію. Завтра ми будемо працювати в офісі. Наступного року вони будуть вивчати українську мову в університеті. Ми будемо чекати на вас біля театру.

> *Let's look at simple and real-life examples. In the evening I will be reading an interesting article about history. Tomorrow we will be working in the office. Next year they will be studying the Ukrainian language at the university. We will be waiting for you near the theater.*

You will use this compound future tense for ongoing, repeated, or general actions in the future where the duration or process is important. The focus is entirely on the fact that the action will be happening, not on the completion or the final result of the task. If you want to say what you will be doing for a whole day, or what your general routine will be next month, you must use this specific form. It sets the scene and describes the background activity.

Завтра я буду працювати весь день, тому я буду дуже зайнятий. Влітку вони будуть подорожувати по Європі автомобілем. Кожного ранку вона буде пити каву на балконі.

> *Tomorrow I will be working all day, so I will be very busy. In summer they will be traveling around Europe by car. Every morning she will be drinking coffee on the balcony.*

Let's draw a direct, clear contrast between the two future formations using the exact same root verb. If you use **написати / напишу** (to write — pf. future), you are using the **простий** (simple, synthetic) perfective future. It means "I will write the letter" — the task will be successfully completed and the letter will be ready. But if you say "Я буду писати листа", you are using the analytical imperfective future. This means "I will be writing the letter," focusing purely on the continuous process. You might spend hours on it, and you might not actually finish it by the end of the day. The choice of aspect completely changes the meaning of your future plans.

Ви можете легко поєднувати ці форми у звичайній розмові. Вранці я буду прибирати квартиру, а потім я приготую смачний обід. Я буду довго читати книгу, а ввечері напишу короткий лист.

<!-- INJECT_ACTIVITY: unjumble-future-sentences --> [unjumble, Reorder words to form correct future tense sentences using both synthetic (напишу) and analytical (буду писати) forms, 6 items]

## Як обрати вид для майбутнього (~450 words)

When you need to speak about the **майбутній час** (future tense), your choice depends entirely on how you view the action. Here is a practical decision guide. Ask yourself a simple question: will the action be completed with a final result? If the answer is yes, you must choose the **простий** (simple, synthetic) perfective future. This form is perfect for single events where the outcome is guaranteed. However, ask yourself another question: will the action be ongoing, repeated, or is the duration itself the main point? If the answer is yes, you must choose the **складений** (compound, analytical) imperfective future. Understanding this difference is the key to speaking naturally and accurately.

Щоб краще зрозуміти різницю, розгляньмо кілька життєвих ситуацій. Якщо дія разова і має результат, ми вибираємо доконаний вид. Наприклад: «Я подзвоню тобі ввечері». Це означає один конкретний дзвінок. Але для постійної дії ми скажемо інакше: «Я буду дзвонити тобі щодня». Порівняйте також результат і процес під час читання. Речення «Він прочитає статтю» означає кінцевий результат. Речення «Він буде читати статтю» просто описує довгий процес. Він витратить на це час.

> *To better understand the difference, let's consider a few real-life situations. If the action is one-time and has a result, we choose the perfective aspect. For example: "I will call you in the evening." This means one specific call. But for a constant action, we will say differently: "I will be calling you every day." Compare also the result and process during reading. The sentence "He will read the article" means a final result. The sentence "He will be reading the article" simply describes a long process. He will spend time on it.*

For the analytical future, you simply use the helper verb **буду** (I will — auxiliary) with an imperfective infinitive. To guarantee a result, you must know perfective verbs like **прочитати** (to read through — pf.) and **подзвонити** (to call — pf.). You will frequently mix these aspects in daily conversations when making plans, promises, or predictions. A classic question you will hear is «Що ти будеш робити завтра?». This focuses on your general process. The reply often mixes aspects: «Я прибиратиму квартиру, а потім приготую вечерю». Note that «прибиратиму» is just a stylish, one-word variant of «буду прибирати».

If you need to promise an email, use **написати** / **напишу** (to write — pf. future). When you take responsibility for a task, say **зробити** / **зроблю** (to do — pf. future). If you promise to get groceries, use **купити** (to buy — pf.). Choosing the correct future tense form is ultimately about expressing *how* you view the action unfolding.

:::info
**Grammar box** — Master these choices! When you share information and guarantee you will do it, use **сказати** / **скажу** (to say/tell — pf. future). This gives you incredible expressive power in Ukrainian, letting you highlight nuance that you simply cannot express easily in English.
:::

<!-- INJECT_ACTIVITY: fill-in-future-aspect -->
<!-- INJECT_ACTIVITY: quiz-aspect-choice -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: synthetic-future
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

**Level: A2 (Module 41/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
