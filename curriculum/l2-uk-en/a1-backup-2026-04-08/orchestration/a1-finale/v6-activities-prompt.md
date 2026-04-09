<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a1-finale.yaml` file for module **55: A1 Finale** (a1).

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

- `<!-- INJECT_ACTIVITY: order-day-events -->`
- `<!-- INJECT_ACTIVITY: fill-in-tenses -->`
- `<!-- INJECT_ACTIVITY: match-situation-phrase -->`
- `<!-- INJECT_ACTIVITY: quiz-a1-review -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the events of the day in chronological order.
  items:
  - Зранку я прокинувся в готелі.
  - Потім я снідав у кафе.
  - Після сніданку я їхав на метро в центр.
  - Я гуляв по місту і купив сувеніри.
  - Вдень я обідав з новою подругою Оленою.
  - Ввечері ми ходили в кіно.
  - Потім ми вечеряли в ресторані.
  - Вночі я повернувся в готель і відпочивав.
  type: order
- focus: Complete the sentences narrating the day using past, present, and future
    tenses.
  items:
  - '{Зранку|Завтра|Ввечері} я снідав у кафе.'
  - Зараз я {гуляю|гуляв|буду гуляти} по Хрещатику, тут дуже гарно!
  - Учора я {купив|купую|буду купувати} квиток на поїзд.
  - Завтра я {буду подорожувати|подорожував|подорожую} по Україні.
  - Ввечері ми {ходили|ходимо|будемо ходити} в кіно.
  - Зараз Олена {замовляє|замовляла|замовить} борщ і салат.
  - Учора була гарна погода, і ми {гуляли|гуляємо|будемо гуляти} в парку.
  - Я вже {готовий|початок|сувенір} до рівня А2! Вітаю!
  type: fill-in
- focus: Match the situation to the correct A1 survival phrase.
  items:
  - Ordering coffee == Будь ласка, каву з молоком.
  - Asking for directions == Вибачте, як дістатися до метро?
  - Buying a souvenir == Скільки коштує ця вишиванка?
  - Meeting someone new == Привіт! Звідки ти?
  - Emergency == Допоможіть! Викличте швидку!
  - At the pharmacy == Дайте, будь ласка, таблетки від головного болю.
  - Saying goodbye == Дякую! До побачення!
  type: match-up
- focus: Review of key A1 grammar and survival vocabulary.
  items:
  - options:
    - Скільки коштує квиток?
    - Де тут квиток?
    - Дайте один квиток.
    question: How do you ask about the price of a ticket?
  - options:
    - Ходімо в кафе!
    - Я був у кафе.
    - Де кафе?
    question: You are inviting a friend to a cafe. What do you say?
  - options:
    - У мене болить голова.
    - У мене температура.
    - Я хворий.
    question: How do you say 'My head hurts'?
  - options:
    - Я на вулиці Хрещатик.
    - Мене звати Адам.
    - Я з Канади.
    question: Someone asks 'Де ви?'. How do you answer?
  - options:
    - Future
    - Past
    - Present
    question: What tense is 'Завтра я буду читати книгу'?
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- круасан (croissant, m)
- карта (map, f)
- лінія (line, f)
- фільм (film, m)
- познайомитися (to get acquainted)
- подорожувати (to travel)
- Лавра (Lavra — Kyiv monastery)
- готель (hotel, m)
required:
- готовий (ready, adj m)
- вітаю (congratulations — chunk)
- початок (beginning, m)
- сувенір (souvenir, m)
- квиток (ticket, m)
- зустріти (to meet)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Ранок (Morning)

Сьомий ранку. Ти **прокинувся** (woke up, masc.) — або **прокинулася** (woke up, fem.) — у **готелі** (hotel) в Києві. Ти **відчинив/відчинила** (opened) вікно. **Надворі** (outside) тепло і сонячно — близько двадцять градусів. **Доброго ранку!** Час **снідати** (to have breakfast). Ти одягаєшся і йдеш у кафе на першому поверсі.

Notice the past tense forms: **прокинувся** for masculine, **прокинулася** for feminine. This is how Ukrainian marks gender in the past tense — a pattern you learned in M48. Throughout this module, you'll see both forms separated by a slash. Pick the one that fits you.

> **Ти:** Доброго ранку! *(Good morning!)*
> **Офіціант:** Доброго ранку! Що бажаєте? *(Good morning! What would you like?)*
> **Ти:** Будь ласка, каву з молоком і **круасан** (croissant). *(A coffee with milk and a croissant, please.)*
> **Офіціант:** Звичайно. Щось іще? *(Of course. Anything else?)*
> **Ти:** Дякую, це все. **Скільки коштує?** *(Thanks, that's all. How much does it cost?)*
> **Офіціант:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Ти:** Ось, будь ласка. *(Here you go.)*
> **Офіціант:** Дякую! **Смачного!** *(Thanks! Enjoy your meal!)*

Everything here is review: greetings from M01, café ordering from M28, food from M36, numbers from M10, and **будь ласка** — the polite formula from M43. The phrase **смачного** literally means "of tasty" — it's the standard Ukrainian way to say "bon appétit."

Після сніданку ти **виходиш** (go out) із готелю. **Тобі потрібна** (you need) зелена **лінія** (line) метро — станція Хрещатик. Ти **купуєш** (buy) один **квиток** (ticket). Transport vocabulary from M34, colors from M22 — all coming together now.

> **Ти:** Вибачте, де тут метро? *(Excuse me, where is the metro here?)*
> **Перехожий:** Ідіть прямо, потім **ліворуч** (to the left). *(Go straight, then left.)*
> **Ти:** Дякую! *(Thanks!)*
> **Перехожий:** Будь ласка, гарного дня! *(You're welcome, have a good day!)*

Directions from M31, polite phrases from M43 — short and natural.

**Зранку** (in the morning) ти **снідав/снідала** (had breakfast) у кафе, потім **їхав/їхала** (rode) на метро. Усе добре! Ти вже в центрі Києва. **Хрещатик** — головна вулиця міста. Тут гарні магазини, кафе і парки. Notice how the narration switches between tenses: **зранку ти снідав** (past — what already happened) and **ти вже в центрі** (present — where you are now). Ukrainian does this naturally when recapping events.

<!-- INJECT_ACTIVITY: order-day-events -->

## День (Daytime)

Ти **гуляєш** (stroll) по Хрещатику. Яка гарна вулиця! Ти **бачиш** (see) великий магазин — і заходиш. На стінах — **вишиванки** (embroidered shirts). Вишиванка — це і традиція, і сучасна мода. Елементи вишивки сьогодні носять не тільки в Україні. Гарний **сувенір** (souvenir)!

> **Ти:** Скільки коштує **ця** (this) вишиванка? *(How much does this vyshyvanka cost?)*
> **Продавець:** Тисяча двісті гривень. *(One thousand two hundred hryvnias.)*
> **Ти:** О, дорого! А **ця**? *(Oh, expensive! And this one?)*
> **Продавець:** Ця — вісімсот. *(This one is eight hundred.)*
> **Ти:** Добре, я **беру** (I'll take it)! *(Alright, I'll take it!)*
> **Продавець:** Будь ласка. Чудовий вибір! *(Here you go. Wonderful choice!)*

The demonstrative pronoun **ця** (this, feminine) points to a specific item — review from M12. The seller says **чудовий вибір** (wonderful choice) — a phrase you'll hear in real Ukrainian shops. Notice the register: this is casual, friendly **розмовний** (colloquial) Ukrainian.

Ти виходиш із магазину з пакетом. На годиннику — **дванадцята** (twelve o'clock). Час **обідати** (to have lunch)! Time-telling from M26 helps you plan the day naturally.

You walk into a café nearby — and someone is waving at you.

> **Олена:** Привіт! Звідки ти? *(Hi! Where are you from?)*
> **Ти:** Я з Канади. А ти? *(I'm from Canada. And you?)*
> **Олена:** Я з Харкова. Мене звати Олена. *(I'm from Kharkiv. My name is Olena.)*
> **Ти:** Дуже приємно! *(Very nice to meet you!)*
> **Олена:** **Ходімо** (let's go) обідати! *(Let's have lunch!)*
> **Ти:** Із задоволенням! *(With pleasure!)*
> **Олена:** Що **замовляєш** (are you ordering)? *(What are you ordering?)*
> **Ти:** Борщ і вареники. Тут дуже смачно! *(Borshch and varenyky. It's very tasty here!)*
> **Олена:** Я теж борщ! *(I'll have borshch too!)*
> **Ти:** Смачно! *(Delicious!)*
> **Олена:** Ти добре говориш українською! *(You speak Ukrainian well!)*
> **Ти:** Дякую! Я вивчаю вже три місяці. *(Thanks! I've been learning for three months.)*

This dialogue packs in: introductions (M06), the imperative **ходімо** (M43), food ordering (M36), and a genuine compliment. The verb **замовляти** (to order food) is the correct Ukrainian word — never use the Russian-influenced *заказати* for ordering at a restaurant.

**Вдень** (during the day) ти **познайомився/познайомилася** (got acquainted) з Оленою і **пообідав/пообідала** (had lunch) у кафе. Гарний день! The verb **познайомитися** (to get acquainted) is a preview of A2 vocabulary — you'll use it a lot at the next level.

<!-- INJECT_ACTIVITY: fill-in-tenses -->

## Вечір (Evening)

After lunch, you and Olena walk through the city together. Evening is approaching — time to make plans.

> **Олена:** Що **будемо робити** (will we do) ввечері? *(What are we going to do this evening?)*
> **Ти:** Ходімо в кіно! Є гарний український **фільм** (film). *(Let's go to the cinema! There's a good Ukrainian film.)*
> **Олена:** О котрій? *(At what time?)*
> **Ти:** О сьомій. *(At seven.)*
> **Олена:** Чудово! Де **зустрінемося** (will we meet)? *(Great! Where shall we meet?)*
> **Ти:** Біля **кінотеатру** (cinema) о шостій п'ятдесят. *(Near the cinema at six fifty.)*

The future tense **будемо робити** (we will do) — the analytical form you learned in M50. And **ходімо** appears again — this imperative for suggestions is one of the most useful words in spoken Ukrainian.

Ви сидите в кінотеатрі. **Фільм** починається. Ти не все розумієш, але багато слів вже знайомі: **родина** (family), **місто** (city), **Україна**. Це приємно! After sixty-four modules, Ukrainian on screen is no longer just noise — you catch real words, real phrases. Ukrainian cinema is vibrant and growing. Remember this feeling.

> **Олена:** Ну, як фільм? *(So, how was the film?)*
> **Ти:** Дуже цікаво! *(Very interesting!)*
> **Олена:** (сміється) Ходімо в ресторан! *((laughs) Let's go to a restaurant!)*
> **Ти:** Добре! Де тут ресторан? *(Sure! Where's a restaurant here?)*
> **Олена:** Он там, за рогом. *(Over there, around the corner.)*
> **Ти:** Ідемо! *(Let's go!)*

Short, punchy, completely natural — this is how two friends talk after a movie. **За рогом** (around the corner) — a useful location phrase from M31.

**Ввечері** (in the evening) в готелі ти думаєш про свій день. **Сьогодні був чудовий день!** Зранку я снідав/снідала у кафе і їхав/їхала на метро. Потім я гуляв/гуляла по Хрещатику і купив/купила **сувенір**. Вдень я познайомився/познайомилася з Оленою і пообідав/пообідала. Ввечері ми ходили в кіно і ресторан. **Завтра я буду їздити по Києву.** Я хочу побачити **Лавру** (Lavra — the famous Kyiv monastery)!

This paragraph is the grammatical heart of the module. Three tenses appear naturally: **past** (зранку я снідав, я гуляв, ми ходили), **present** (я думаю, я хочу), and **future** (завтра я буду їздити). Masculine and feminine pairs throughout — pick your set. You are already combining all three tenses the way native speakers do: telling what happened, feeling something now, planning for tomorrow.

:::tip
**Зверни увагу** (pay attention): in that reflection paragraph, three tenses work together. **Минулий час** (past): я снідав, я гуляв. **Теперішній час** (present): я думаю, я хочу. **Майбутній час** (future): я буду їздити. You're already using all three naturally. Це А1!
:::

<!-- INJECT_ACTIVITY: match-situation-phrase -->

## Підсумок: ти готовий/готова! (You're Ready!)

Fifty-five modules. Hundreds of words. And today — a whole day in Kyiv, entirely in Ukrainian. Here is everything you can now do:

- **Привітатися й познайомитися** (greet and introduce yourself) — «Привіт! Мене звати Адам. Я з Канади.» (A1.1)
- **Описати людину, сім'ю, речі** (describe people, family, things) — «Моя мама висока і добра. У мене є сестра.» (A1.2)
- **Розповісти про дії та звички** (talk about actions and habits) — «Я люблю читати. Щодня я ходжу в парк.» (A1.3)
- **Говорити про час і погоду** (talk about time and weather) — «Сьогодні вівторок, дванадцята година. Надворі холодно.» (A1.4)
- **Орієнтуватися в місті** (navigate a city) — «Їдьте на метро, станція Хрещатик.» (A1.5)
- **Замовляти їжу, робити покупки** (order food, shop) — «Будь ласка, борщ і каву. Скільки коштує?» (A1.6)
- **Звертатися ввічливо** (address people politely) — «Вибачте, допоможіть, будь ласка.» (A1.7)
- **Розповідати про минуле, робити плани** (talk about the past, make plans) — «Учора я був у кіно. Завтра буду вдома. Допоможіть! Викличте швидку!» (A1.8)

At **A2**, you'll discover **відмінки** (cases — how words change form depending on their role in a sentence), **вид дієслова** (verb aspect — perfective and imperfective), the **синтетичний майбутній час** (synthetic future: **прочитаю**, **скажу** instead of **буду читати**), and more complex sentences. The grammar deepens — but the foundation is solid. **Святкуй!** (Celebrate!) Ти вивчив/вивчила А1. **Вітаю!** (Congratulations!) Ти вже можеш жити в українському місті. Це тільки **початок** (beginning)!

**Перевір себе** (check yourself): can you describe your day in a Ukrainian city in ten or more sentences? Use past, present, and future tense. Start like this: «Сьогодні вранці я прокинувся/прокинулася…» If you can — ти **готовий/готова** (ready) до А2. **Вперед!** (Forward!)

<!-- INJECT_ACTIVITY: quiz-a1-review -->

Дякуємо, що ти вивчаєш українську. Ця мова — жива, красива і важлива. Вона звучить у піснях, у книжках, на вулицях Києва, Львова, Харкова. Тепер вона трохи твоя теж. **До зустрічі на А2!** (See you at A2!)

Хрещатик, метро, борщ, вишиванка, **Лавра** — за цей модуль ти **провів/провела** (spent) цілий день у Києві. Ці слова більше не просто слова — це твій досвід. Україна — це не тільки мова. Це культура, люди, міста. Ти тільки починаєш **відкривати** (to discover) для себе цю країну. А попереду — ще так багато цікавого.

## Підсумок

**Що ти зробив/зробила у цьому модулі:**

- Провів/провела цілий день у Києві — від ранку до вечора
- Використав/використала всі три часи: минулий, теперішній, майбутній
- Замовляв/замовляла їжу, робив/робила покупки, орієнтувався/орієнтувалася в місті
- Познайомився/познайомилася з новою людиною і провів/провела вечір разом

**Перевірка:** Read the evening reflection paragraph again. Can you identify which verbs are past, which are present, and which are future? Can you retell your own version — your day, your city, your plans? If yes, you have completed A1. **Ти готовий/готова до А2. Вітаю!**

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a1-finale
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
```

---

## Activity Type Reference

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 55/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: general-vocabulary
- **match-up** — Слово → переклад: Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Fill in the missing word from context
- **anagram** — Склади слово: Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Choose correct translation from options


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
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
