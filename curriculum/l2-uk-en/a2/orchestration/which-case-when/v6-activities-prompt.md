<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/which-case-when.yaml` file for module **36: Компас відмінків** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-sort-prepositions-by-which-case-s-they-govern-acc-gen-instr-loc -->`
- `<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->`
- `<!-- INJECT_ACTIVITY: quiz-case-verb-prep -->`
- `<!-- INJECT_ACTIVITY: true-false-case-pairs -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Given a sentence with a blank, choose the correct case form based on the
    governing verb or preposition
  items: 8
  type: quiz
- focus: Sort prepositions by which case(s) they govern (Acc., Gen., Instr., Loc.)
  items: 8
  type: group-sort
- focus: Complete sentences with the correct noun form — mixed cases triggered by
    different prepositions and verbs, including time expressions (у четвер), characteristics
    (у червоному светрі), and path (по кімнаті)
  items: 8
  type: fill-in
- focus: Judge whether the case used in a sentence is correct or incorrect, including
    tricky pairs like на роботу (Acc.) vs. на роботі (Loc.)
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- алгоритм (algorithm)
- контекст (context)
- керувати (to manage, drive)
- майбутнє (future)
required:
- відмінок (grammatical case)
- прийменник (preposition)
- дієслово (verb)
- напрямок (direction)
- місце (place, location)
- час (time)
- характеристика (characteristic, description)
- думати (to think)
- боятися (to be afraid)
- користуватися (to use)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Дієслово вирішує: Який відмінок після дієслова? (~600 words)

Сьогодні ми граємо в граматичних детективів. Ми читаємо українську газету і шукаємо кожен **відмінок** (grammatical case).

> — **Вчитель:** Читаємо перший текст. «Президент зустрівся з прем'єром. Для журналістів підготували зал». Де тут називний відмінок? *(Let's read the first text. "The president met with the prime minister. They prepared a hall for the journalists". Where is the nominative case here?)*
> — **Студенти:** Слово «президент». Це суб'єкт, він робить дію. *(The word "president". It is the subject, he is doing the action.)*
> — **Вчитель:** Правильно. А чому ми кажемо «з прем'єром»? *(Correct. And why do we say "with the prime minister"?)*
> — **Студенти:** Тому що тут є **прийменник** (preposition) «з». Це орудний відмінок. *(Because there is the preposition "with" here. It is the instrumental case.)*
> — **Вчитель:** Чудово! А слово «журналістів»? *(Great! And the word "journalists"?)*
> — **Студенти:** Це родовий відмінок після прийменника «для». *(It is the genitive case after the preposition "for".)*
> — **Вчитель:** А слово «зал»? *(And the word "hall"?)*
> — **Студенти:** Це знахідний відмінок. Це об'єкт дії «підготували». *(It is the accusative case. It is the object of the action "prepared".)*

When an action passes directly onto an object, the Ukrainian language uses the Accusative case. Most transitive verbs require this case, and mastering them is your first big step in sentence building.

Коли ви хочете щось купити, знайти або прочитати, вам потрібен знахідний відмінок. Такі слова як «бачити», «знати», «любити», «читати», «купити» та «шукати» завжди вимагають об'єкта. Я читаю книгу. Ми шукаємо ключі. Вона знає цього хлопця. Кожне **дієслово** (verb) тут напряму впливає на об'єкт.

> *When you want to buy, find, or read something, you need the accusative case. Words like "to see", "to know", "to love", "to read", "to buy", and "to look for" always require an object. I am reading a book. We are looking for the keys. She knows this guy. Every verb here directly affects the object.*

Some actions are directed *towards* a recipient rather than done *to* an object. In Ukrainian, you do these actions *to* or *for* someone, which means you must use the Dative case.

Ми даємо допомогу або пораду комусь. Тому слова «допомагати», «телефонувати», «дякувати», «радити» та «заважати» вимагають давального відмінка. Я допомагаю сестрі. Ми щиро дякуємо вчителям. Він телефонує батькам. Це дуже важливе правило.

> *We give help or advice to someone. Therefore, words like "to help", "to call", "to thank", "to advise", and "to bother" require the dative case. I help my sister. We sincerely thank the teachers. He calls his parents. This is a very important rule.*

:::info
**Grammar box**
Always remember: you thank *to* someone (`дякувати комусь`), help *to* someone (`допомагати комусь`), and bother *to* someone (`заважати комусь`). Using the Accusative here is a very common mistake!
:::

Another specific group of verbs describes what tool you use, what you manage, or what you are interested in. These concepts are expressed using the Instrumental case, completely without prepositions.

Якщо ви хочете чимось **користуватися** (to use), вам потрібен орудний відмінок. Він користується новим комп'ютером. Вона цікавиться історією. Мій друг займається спортом. Директор керує великою компанією. Іменник показує інструмент дії або сферу вашого інтересу.

> *If you want to use something, you need the instrumental case. He uses a new computer. She is interested in history. My friend does sports. The director manages a large company. The noun shows the tool of the action or the area of your interest.*

Verbs expressing fear, need, or a lack of something strictly require the Genitive case.

Найпопулярніше слово для цього відмінка — «немає». У мене немає часу. Але ми також маємо дієслова. Якщо ви хочете чогось **боятися** (to be afraid) або потребувати, використовуйте родовий відмінок. Вона боїться темряви. Проєкт потребує інвестицій.

> *The most popular word for this case is "there is no". I have no time. But we also have verbs. If you want to be afraid of something or require something, use the genitive case. She is afraid of the dark. The project requires investments.*

Finally, some verbs require a specific preposition, which dictates the case. A classic example is when you **думати** (to think) about something. The preposition «про» always takes the Accusative.

Коли ви мрієте або думаєте про щось, ви використовуєте прийменник «про» і знахідний відмінок. Я часто думаю про майбутнє. Вони мріють про подорож. Ми думаємо про новий план.

> *When you dream or think about something, you use the preposition "про" and the accusative case. I often think about the future. They dream about a trip. We are thinking about a new plan.*

## Прийменник вирішує: Один прийменник — різні відмінки (~600 words)

In Ukrainian, a **прийменник** (preposition) usually dictates which grammatical case must follow it. Many prepositions are strictly tied to just one specific case and never change their behavior. However, the most interesting and common prepositions in the language are dual-use. They can govern two completely different cases depending on their core meaning in the sentence. The most frequent distinction these prepositions make is between a dynamic **напрямок** (direction) of a movement and a static **місце** (place, location) where an action happens. Understanding this logical difference is the absolute key to mastering Ukrainian prepositions and avoiding basic errors.

Прийменник «на» дуже часто вказує на напрямок або місце, і це змінює відмінок. Якщо ви активно рухаєтесь кудись, це напрямок, і вам обов'язково потрібен знахідний відмінок. Наприклад, я щоранку йду на роботу. Поклади цю нову книгу на стіл, будь ласка. Але якщо ви вже там знаходитесь і дія статична, це місце. Тоді потрібен місцевий відмінок. Я зараз на роботі і не можу говорити. Книга вже довго лежить на столі.

> *The preposition "на" very often indicates direction or location, and this changes the case. If you are actively moving somewhere, it is a direction, and you absolutely need the accusative case. For example, I go to work every morning. Put this new book on the table, please. But if you are already located there and the action is static, it is a place. Then you need the locative case. I am at work now and cannot talk. The book has been lying on the table for a long time.*

The preposition "у" or "в" works exactly the same way, creating a clear division between movement and static presence. When it shows the destination of a movement, you use the Accusative case.

**Я йду в магазин.** — *I am going to the store.*

This means you are currently walking towards the building. But when it describes a static location where someone or something already is, you must use the Locative case.

**Я в магазині.** — *I am in the store.*

This means you are already inside the store shopping. This logical split between moving somewhere and being somewhere is very consistent across the language. Soon, we will also see how these prepositions are used to talk about **час** (time).

:::info
**Grammar box**
Always ask yourself the core question of the sentence. If the question is «Куди?» (Where to?), use the Accusative case for your destination. If the question is «Де?» (Where?), use the Locative case for your current location. This single trick solves most preposition dilemmas.
:::

Прийменник «по» в українській мові найчастіше працює з місцевим відмінком. Він показує рух по якійсь поверхні або довгий шлях. Маленькі діти дуже люблять швидко бігати по кімнаті. Ми часто ходимо по вулиці ввечері, коли маємо вільний час. Наші друзі хочуть подорожувати по Україні наступного року. Цей прийменник чудово показує широкий простір, де відбувається дія.

Another fascinating dual-use preposition is "з" or "із". When it means "from" or "out of" a specific place, it governs the Genitive case. Both of these examples describe the origin point of a movement:

**вийти з дому** — *to go out of the house*
**приїхати з Києва** — *to arrive from Kyiv*

However, when it means "together with" a person or an object, it strictly requires the Instrumental case. The intended meaning completely shifts the grammatical rules you apply:

**піти з другом** — *to go with a friend*
**кава з молоком** — *coffee with milk*

Прийменник «за» також має дві зовсім різні граматичні ролі. Якщо ви даєте щось в обмін або щиро дякуєте, ви використовуєте знахідний відмінок. Я хочу подякувати за допомогу. Ми завжди платимо за квитки онлайн. Але якщо щось знаходиться фізично позаду, ви використовуєте орудний відмінок. Вони зараз сидять за столом. Собака дуже швидко біжить за автобусом.

> *The preposition "за" also has two completely different grammatical roles. If you give something in exchange or sincerely say thank you, you use the accusative case. I want to say thank you for the help. We always pay for the tickets online. But if something is physically located behind, you use the instrumental case. They are sitting at the table now. The dog is running very fast after the bus.*

<!-- INJECT_ACTIVITY: group-sort-sort-prepositions-by-which-case-s-they-govern-acc-gen-instr-loc -->

## Особливі випадки: Час, характеристика, шлях (~550 words)

When we talk about **час** (time), the choice of case depends on the specific period we are describing. For days of the week and specific blocks of time, Ukrainian uses the Accusative case.

Для днів тижня ми використовуємо прийменник «у» або «в» та знахідний відмінок. Наприклад, ми часто кажемо «у четвер», «у середу» або «у п'ятницю». Іноді ми можемо сказати про час навіть без прийменника. Якщо ви хочете сказати про свої плани, ви можете сказати: «Цю неділю я відпочиваю». Але для фраз зі словами «наступний» або «минулий» ми завжди обираємо родовий відмінок. Наприклад, ми кажемо «наступного тижня» або «минулого року».

> *For days of the week, we use the preposition "у" or "в" and the accusative case. For example, we often say "on Thursday", "on Wednesday" or "on Friday". Sometimes we can talk about time even without a preposition. If you want to talk about your plans, you can say: "This Sunday I am resting". But for phrases with the words "next" or "last", we always choose the genitive case. For example, we say "next week" or "last year".*

:::note
**Quick tip** — Use the Accusative case for days of the week (`у понеділок`), but remember to switch to the Genitive case for phrases with "next" or "last" (`наступного вівторка`, `минулого тижня`).
:::

The Locative case has a very special and descriptive function. We use it to describe a physical **характеристика** (characteristic, description), especially what someone is wearing. The pattern is simply the noun plus "у" or "в" followed by the Locative case.

Коли ми описуємо людей на вулиці, ми звертаємо увагу на їхній одяг. Для цього ми використовуємо місцевий відмінок. Наприклад, ви можете побачити, як іде хлопець у червоному светрі. Біля нього стоїть дівчина в окулярах. А поруч розмовляє по телефону жінка у білому пальті. Це дуже зручний спосіб описати зовнішність людини без складних речень.

> *When we describe people on the street, we pay attention to their clothes. For this, we use the locative case. For example, you might see a guy in a red sweater walking. A girl in glasses is standing next to him. And nearby, a woman in a white coat is talking on the phone. This is a very convenient way to describe a person's appearance without complex sentences.*

We also return to the Locative case when talking about years and broader contexts of time, such as life stages or centuries.

Для великих періодів часу українська мова теж вимагає місцевого відмінка. Ми завжди використовуємо його, коли називаємо конкретний рік. Наприклад, багато важливих подій відбулося у 2014 році. Ми живемо у двадцять першому столітті. Також ми вживаємо цю форму для періодів життя. Часто можна почути фрази «у дитинстві» або «в юності».

> *For large periods of time, the Ukrainian language also requires the locative case. We always use it when we name a specific year. For example, many important events happened in 2014. We live in the twenty-first century. We also use this form for life periods. You can often hear the phrases "in childhood" or "in youth".*

Finally, let's look at how to describe movement across a **місце** (place, location) or a specific path. The preposition "по" paired with the Locative case is your best tool for this.

Прийменник «по» показує рух по поверхні або в межах певної території. Він чудово описує хаотичний рух або довгий шлях. Маленькі діти люблять швидко бігати по кімнаті. У вихідні ми можемо довго гуляти по парку з собакою. А туристи часто люблять їздити по місту на автобусі. У цих реченнях дія не має кінцевої точки, це просто рух у просторі.

> *The preposition "по" shows movement across a surface or within a certain territory. It perfectly describes chaotic movement or a long path. Small children like to run fast around the room. On weekends, we can walk around the park with the dog for a long time. And tourists often like to ride around the city on a bus. In these sentences, the action does not have an end point, it is just movement in space.*

<!-- INJECT_ACTIVITY: fill-in-mixed-cases --> [fill-in, Complete sentences with the correct noun form — mixed cases triggered by different prepositions and verbs, including time expressions (у четвер), characteristics (у червоному светрі), and path (по кімнаті), 8 items]

## Алгоритм вибору відмінка (~450 words)

When you speak Ukrainian, choosing the correct **відмінок** (grammatical case) can feel overwhelming. To make it easier, we use a simple three-step algorithm. The first step is to look for a **прийменник** (preposition). If there is one, it usually dictates the case immediately. If there is no preposition, move to step two: check the **дієслово** (verb). Many verbs require a specific case for their object. Finally, step three: if you are still unsure, ask the case question, such as «кого?», «що?», «кому?», or «ким?».

Цей простий алгоритм допомагає швидко знайти правильну форму слова. Спочатку ми завжди шукаємо прийменник у реченні. Якщо його немає, ми дивимося на головне дієслово. Дієслово часто керує іменником і вимагає конкретного відмінка. Якщо це не допомагає, ми ставимо питання до слова.

> *This simple algorithm helps to quickly find the correct word form. First, we always look for a preposition in the sentence. If there isn't one, we look at the main verb. The verb often governs the noun and requires a specific case. If that doesn't help, we ask a question to the word.*

Let's walk through this decision tree using a real sentence: "The student reads a book on the table." First, who is doing the action? The subject is always in the Nominative case. Then, we apply our algorithm to the rest of the sentence. We must determine if the preposition indicates a **місце** (place, location) or a **напрямок** (direction).

Студент читає книгу на столі. Хто виконує дію? Студент. Це називний відмінок. Далі ми бачимо дієслово «читати». Воно вимагає знахідного відмінка для об'єкта, тому ми кажемо «книгу». Потім іде прийменник «на». Він вказує на локацію, а не на рух. Тому ми використовуємо місцевий відмінок і кажемо «на столі».

> *The student reads a book on the table. Who performs the action? The student. This is the nominative case. Next, we see the verb "to read". It requires the accusative case for the object, so we say "a book". Then comes the preposition "on". It indicates a location, not a movement. Therefore, we use the locative case and say "on the table".*

There are a few common pitfalls that learners often encounter. The biggest confusion is usually with the preposition "на" and expressions of **час** (time). Remember that we also use the Locative case when describing a physical **характеристика** (characteristic, description) of a person. Another trap involves specific verbs. For example, the verb **думати** (to think) takes "про" plus the Accusative case, not the Locative.

Студенти часто плутають напрямок і статику. Вони також забувають правильні відмінки після конкретних дієслів. Багато людей помилково використовують родовий відмінок після дієслова «допомагати». Але це дієслово завжди вимагає давального відмінка. Також ми ніколи не кажемо «думати в чомусь», ми кажемо «думати про щось».

> *Students often confuse direction and static location. They also forget the correct cases after specific verbs. Many people mistakenly use the genitive case after the verb "to help". But this verb always requires the dative case. Also, we never say "to think in something", we say "to think about something".*

Do not let the case system intimidate you. It is normal **боятися** (to be afraid) of making mistakes at first. But by systematically applying this algorithm, you can confidently **користуватися** (to use) the correct forms. Always check your prepositions and verbs first, and memorize the specific cases they trigger.

:::tip
**Quick tip** — When learning a new verb, always memorize the preposition and case it requires as a single block. For example, learn "думати про + Acc." instead of just "думати".
:::

Спочатку ця система здається дуже складною. Але регулярна практика робить дива. З часом ви будете автоматично вибирати правильний відмінок. Ви просто запам'ятаєте, як слова працюють разом у контексті. Ваша українська мова стане природною та впевненою.

> *At first, this system seems very difficult. But regular practice does miracles. Over time, you will automatically choose the correct case. You will simply remember how words work together in context. Your Ukrainian language will become natural and confident.*

<!-- INJECT_ACTIVITY: quiz-case-verb-prep -->
<!-- INJECT_ACTIVITY: true-false-case-pairs -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: which-case-when
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

**Level: A2 (Module 36/60) — ELEMENTARY**

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
