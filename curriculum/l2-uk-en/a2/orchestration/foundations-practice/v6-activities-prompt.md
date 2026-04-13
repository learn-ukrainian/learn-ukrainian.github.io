<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/foundations-practice.yaml` file for module **7: Перші кроки в А2** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-role-play-planning-a-party-aspect-in-future-tense -->`
- `<!-- INJECT_ACTIVITY: fill-in-shopping-groceries -->`
- `<!-- INJECT_ACTIVITY: match-up-story-aspect -->`
- `<!-- INJECT_ACTIVITY: match-up-narrative-questions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Role-play: Planning a Party (aspect in future tense)'
  items: 8
  type: quiz
- focus: 'Role-play: Shopping for Groceries'
  items: 8
  type: fill-in
- focus: 'Story Completion: Choose the Right Aspect'
  items: 8
  type: match-up
- focus: Answering questions about a short narrative
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- сценарій (scenario)
- діалог (dialogue)
- обговорювати (to discuss)
- замовляти / замовити (to order)
required:
- планувати / запланувати (to plan)
- купувати / купити (to buy)
- готувати / приготувати (to cook, prepare)
- ринок (market)
- коштувати (to cost)
- кілограм (kilogram)
- вечірка (party)
- день (day)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Сценарій 1: Плануємо вечірку (Scenario 1: Planning a Party) (~650 words)

Two friends, Oksana and Taras, are organizing a housewarming party. To make sure everything goes smoothly, they sit down to discuss their future plans and allocate tasks. They need to figure out what is missing for the celebration and who will be responsible for each part of the preparation for that special **день** (day). Let's listen to how they manage their checklist.

> — **Оксана:** Тарасе, давай **планувати** нашу **вечірку**. *(Taras, let's plan our party.)*
> — **Тарас:** Давай. Буде десять гостей. Це буде чудовий день. Хто і що робить? *(Let's do it. There will be ten guests. It will be a wonderful day. Who is doing what?)*
> — **Оксана:** Я буду **готувати** салат. А що ти будеш робити? *(I will make a salad. And what will you do?)*
> — **Тарас:** Ми будемо **купувати** напої та серветки разом. *(We will buy drinks and napkins together.)*
> — **Оксана:** Згодна. А як щодо десерту? *(Agreed. And what about dessert?)*
> — **Тарас:** Ми вже **купили** два торти вчора, пам'ятаєш? *(We already bought two cakes yesterday, remember?)*
> — **Оксана:** Точно! Але у нас немає музики! *(Exactly! But we have no music!)*
> — **Тарас:** Я зроблю плейлист. Що ще? *(I will make a playlist. What else?)*
> — **Оксана:** Треба купити багато фруктів. Ти підеш на **ринок**? *(We need to buy a lot of fruit. Will you go to the market?)*
> — **Тарас:** Добре. А ти вже **приготувала** салат? *(Good. And have you already prepared the salad?)*
> — **Оксана:** Так, я вже приготувала салат вранці. *(Yes, I already prepared the salad in the morning.)*
> — **Тарас:** Чудово, тоді ми майже готові. *(Great, then we are almost ready.)*

When discussing future plans and ongoing processes, you will use the imperfective aspect. To form the compound future tense in Ukrainian, combine the conjugated future form of the verb **бути** (to be) with the imperfective infinitive of your main verb. This emphasizes the process of doing something rather than the final result.

Ми будемо купувати напої. Оксана каже: «Я буду готувати салат». Вони будуть планувати вечірку весь вечір. Ця форма показує, що дія триватиме певний час.

> *We will be buying drinks. Oksana says: "I will be making a salad". They will be planning the party all evening. This form shows that the action will last for a certain time.*

:::info
**Grammar box**
Remember that the compound future tense can ONLY be formed with imperfective verbs. You will never use **бути** with a perfective verb.
:::

This compound future tense often translates similarly to the English future continuous ("will be doing"), focusing on the activity itself. Whenever you are outlining tasks that take time to complete, such as shopping or cooking, the imperfective aspect is your best choice.

As you plan an event, you will inevitably discover what is missing and how much you need to buy. In Ukrainian, expressing the absence of something always requires the Genitive case. The word **немає** (there is no / do not have) acts as a trigger that forces the following noun into the Genitive form.

Оксана помітила проблему і сказала: «У нас немає музики!». Музика — це називний відмінок, але після слова «немає» ми завжди використовуємо родовий відмінок. 

> *Oksana noticed a problem and said: "We have no music!". Music is the Nominative case, but after the word "немає" we always use the Genitive case.*

:::tip
**Did you know?**
The word **немає** is actually a contraction of **не має** (does not have). Over time, it became a single word used specifically to indicate absence, acting as an impersonal state rather than an active verb.
:::

Beyond absence, the Genitive case is also essential when talking about specific quantities or volumes. Whenever you use words like **багато** (a lot), **мало** (a little), or specific numbers (five and up), the item being counted must take the Genitive plural form.

Також для вечірки треба купити багато фруктів. Слово «фруктів» стоїть у родовому відмінку множини. Вони чекають десять гостей, тому їм потрібно багато їжі.

> *Also, for the party they need to buy a lot of fruit. The word "фруктів" is in the Genitive plural. They are expecting ten guests, so they need a lot of food.*

Once a task on your party checklist is finished, you shift from discussing the process to confirming the result. To state that an action is successfully completed, you must use the perfective aspect. In the past tense, perfective verbs often function similarly to the English present perfect ("have done"), emphasizing the result relevant to the present moment.

Оксана каже: «Я вже приготувала салат». Це означає, що салат готовий і стоїть на столі. Тарас радіє, бо вони вже купили два торти для свята. Вони мають хороший результат.

> *Oksana says: "I already prepared the salad". This means that the salad is ready and sitting on the table. Taras is happy because they already bought two cakes for the holiday. They have a good result.*

Notice the contrast between the ongoing process and the final achievement. While **купувати** (to be buying) describes the activity of shopping, **купити** (to have bought) confirms that the items are securely in your possession. Always use perfective verbs when the outcome is what matters most.

<!-- INJECT_ACTIVITY: quiz-role-play-planning-a-party-aspect-in-future-tense -->

## Сценарій 2: На ринку (Scenario 2: At the Market) (~650 words)

When you step out of the supermarket and into a traditional Ukrainian farmers **ринок** (market), the conversational rules change entirely. This dynamic environment requires you to negotiate with sellers, request specific amounts of produce, and ask about prices. A bustling market in a city like Kyiv is the absolute best place to practice your numbers, ask how much things **коштувати** (to cost), and test your mastery of the Genitive case in real time.

> — **Продавець:** Добрий день! Що ви бажаєте купити сьогодні? *(Good day! What do you want to buy today?)*
> — **Покупець:** Добрий день! Дайте мені, будь ласка, один **кілограм** яблук, дві дині і п'ять лимонів. *(Good day! Give me, please, one kilogram of apples, two melons, and five lemons.)*
> — **Продавець:** Вибачте, у мене немає лимонів. *(Sorry, I do not have lemons.)*
> — **Покупець:** Шкода. А скільки коштує кілограм меду? *(That is a pity. And how much does a kilogram of honey cost?)*
> — **Продавець:** Триста гривень. Дуже смачний! *(Three hundred hryvnias. Very tasty!)*
> — **Покупець:** Добре, я візьму банку. Ще мені потрібен сир. Я не бачу помідорів, у вас є? *(Good, I will take a jar. I also need cheese. I do not see tomatoes, do you have any?)*
> — **Продавець:** Ні, помідорів сьогодні вже немає. Беріть свіжі ягоди! *(No, there are no tomatoes today anymore. Take fresh berries!)*
> — **Покупець:** Дякую, давайте ягоди і сир. *(Thank you, let's do the berries and cheese.)*

The most common task at a market is asking for specific quantities of food. In Ukrainian, the number you use directly governs the grammatical case of the noun that follows it. The rules change depending on whether you are asking for one item, two to four items, or five and more items.

Один кілограм вимагає називного відмінка для слова «кілограм», але наступне слово завжди стоїть у родовому відмінку. Наш покупець чітко каже: «один кілограм яблук». Якщо ви купуєте дві, три або чотири речі, іменник отримує форму називного відмінка множини. Вона ввічливо просить: «дві дині». Після цифри п'ять і більше ми завжди використовуємо родовий відмінок множини. Покупець хоче купити «п'ять лимонів».

> *One kilogram requires the Nominative case for the word "кілограм", but the following word always stands in the Genitive case. Our buyer clearly says: "one kilogram of apples". If you buy two, three, or four things, the noun takes the form of the Nominative plural. She politely asks: "two melons". After the number five and more, we always use the Genitive plural. The buyer wants to buy "five lemons".*

:::info
**Grammar box**
Always remember the 1, 2-4, 5+ counting rule. Use Nominative singular for 1, Nominative plural for 2-4, and Genitive plural for 5 and above. When you ask "Скільки коштує кілограм меду?" (How much does a kilogram of honey cost?), "меду" is in the Genitive singular because it follows a measure of quantity.
:::

Another frequent situation at a local market is discovering that a vendor is completely sold out of what you need. In English, you might say "I don't see the tomatoes," keeping the direct object exactly the same as in a positive sentence. In Ukrainian, when a verb is negated with the particle «не», its direct object very often shifts into the Genitive case. This feature is known as the Genitive of negation.

Продавець на ринку сумно каже: «Вибачте, у мене немає лимонів». Слово «лимонів» стоїть у родовому відмінку тільки через слово «немає». Покупець шукає свіжі овочі і каже: «Я не бачу помідорів». Дієслово «бачити» вимагає звичайного знахідного відмінка, але заперечення «не бачу» змінює форму на родовий відмінок.

> *The vendor at the market sadly says: "Sorry, I do not have lemons". The word "лимонів" is in the Genitive case only because of the word "немає". The buyer looks for fresh vegetables and says: "I do not see tomatoes". The verb "бачити" requires the regular Accusative case, but the negation "не бачу" changes the form to the Genitive case.*

A defining characteristic of spoken Ukrainian, especially in hospitable settings like a neighborhood market, is the extensive use of diminutive suffixes. Vendors use these special forms not because they are talking to small children, but to sound friendly, polite, and welcoming to their customers. This creates a deep sense of **милозвучність** (euphony or sweet-sounding language) that is central to traditional Ukrainian culture.

Ви часто почуєте на ринку такі приємні слова: солодкі мандаринки, свіжий борщик, зелена цибулька або гострий часничок. Продавці щиро пропонують вам свої найкращі продукти. Це робить їхню щоденну мову дуже живою та емоційною. Важливо також завжди пам'ятати про правильні слова для згоди. Ніколи не кажіть «да», а завжди кажіть «так».

> *You will often hear such pleasant words at the market: sweet little mandarins, fresh little borsch, green little onions, or spicy little garlic. The vendors sincerely offer you their best products. This makes their daily speech very lively and emotional. It is also important to always remember the correct words for agreement. Never say "да" (a Russian calque), but always say "так" (yes).*

:::tip
**Did you know?**
Diminutives are the DNA of the Ukrainian language. Forms like мандаринки or цибулька are not just "baby talk"; they are a fully realized emotional register that adults use daily to express warmth and care.
:::

<!-- INJECT_ACTIVITY: fill-in-shopping-groceries -->

## Сценарій 3: Як пройшов твій день? (Scenario 3: How Was Your Day?) (~900 words)

In our final scenario, two friends are catching up on how their **день** (day) went after spending time apart. This everyday situation perfectly highlights the core narrative difference between describing an ongoing process and reporting a completed result. When you tell a story, you absolutely need both grammatical aspects to make your timeline clear. 

Let us see how they discuss their recent activities and future intentions.

> — **Оксана:** Привіт, Тарасе! Як пройшов твій день? *(Hi, Taras! How was your day?)*
> — **Тарас:** Привіт, Оксано! Дуже активно. Зранку я їздив на центральний ринок. *(Hi, Oksana! Very actively. In the morning I went to the central market.)*
> — **Оксана:** О, ти хотів купити свіжі овочі та фрукти? *(Oh, you wanted to buy fresh vegetables and fruits?)*
> — **Тарас:** Так. Я запитав продавця, скільки коштує один кілограм помідорів, і вирішив взяти три кілограми. *(Yes. I asked the vendor how much one kilogram of tomatoes costs, and decided to take three kilograms.)*
> — **Оксана:** Це добре. А я вчора довго обговорювала наш план на вихідні з друзями. *(That is good. And yesterday I discussed our plan for the weekend with friends for a long time.)*
> — **Тарас:** Ви вже почали готувати якісь цікаві страви? Це буде дуже крута вечірка! *(Have you already started cooking some interesting dishes? It will be a very cool party!)*
> — **Оксана:** Ні, спочатку ми будемо купувати необхідні продукти, а потім я зможу приготувати салати. *(No, first we will be buying necessary groceries, and then I will be able to prepare salads.)*
> — **Тарас:** Я теж хочу допомогти і планую замовити смачну піцу для нас усіх. *(I also want to help and plan to order a delicious pizza for all of us.)*
> — **Оксана:** Чудова ідея! Якраз вчора я змогла знайти гарний італійський ресторан неподалік. *(Great idea! Just yesterday I managed to find a nice Italian restaurant nearby.)*

This conversation highlights how we use specific vocabulary to organize our time. For instance, you must learn the verb pair **планувати / запланувати** (to plan) when organizing a social event. This is especially true when you want to host a fun **вечірка** (party) with your friends.

The friends also discussed their errands and food preparations. When we visit a traditional **ринок** (market), we frequently ask the vendors how much fresh items **коштувати** (to cost). We usually buy produce by the **кілограм** (kilogram), which requires careful attention to the numbers we use.

Finally, household chores require their own dedicated set of action words. The fundamental verbs **купувати / купити** (to buy) are used when we acquire our groceries. Once we have everything we need, we rely on the verbs **готувати / приготувати** (to cook, prepare) to make our meals.

When you want to describe an ongoing action or set the scene in the past, you must use the imperfective aspect. This form focuses entirely on the duration, the process, or the repetition of an action, without indicating whether it ever reached a conclusion. Think of the imperfective aspect as painting the atmospheric background of your story before the main events actually happen.

Вчора ввечері йшов сильний дощ, а я довго читав цікаву книгу. Моя сестра тихо слухала музику, поки ми чекали на наших гостей. Ми нікуди не поспішали і просто відпочивали у вітальні.

> *Yesterday evening heavy rain was falling, and I was reading an interesting book for a long time. My sister was quietly listening to music while we were waiting for our guests. We were not rushing anywhere and were simply resting in the living room.*

The verbs in this scene show multiple actions that were happening simultaneously over a period of time. There is no clear end point, only the continuous, unbroken flow of the process.

In sharp contrast, when you want to report a clear sequence of completed events, you must use the perfective aspect. Perfective verbs move a narrative forward by presenting actions as a chain of specific, finalized results. They answer the crucial question of what was actually accomplished or achieved at a specific moment in time.

Спочатку я смачно поснідав, потім пішов на роботу, а ввечері подивився новий документальний фільм. Я купив квитки заздалегідь, тому ми дуже швидко зайшли в темний зал.

> *First I had a tasty breakfast, then I went to work, and in the evening I watched a new documentary movie. I bought the tickets in advance, so we very quickly entered the dark hall.*

Each of these actions is a closed, completed chapter in the story. One action finishes completely and provides a result before the next chronological action begins. This creates a very clear timeline of consecutive events.

One of the most common and powerful narrative structures in the Ukrainian language combines both aspects within a single sentence. You typically use an imperfective verb to describe a continuous background action, and then use a perfective verb to introduce a sudden, completed event that interrupts it. This is exactly how we express the English concept of "was doing something when something else suddenly happened."

Я уважно писав довгого листа, коли ти несподівано подзвонив. Ми спокійно йшли додому через парк, коли раптом почалася сильна осіння злива.

> *I was carefully writing a long letter when you unexpectedly called. We were calmly walking home through the park when suddenly a heavy autumn downpour started.*

The imperfective background action creates the setting and the mood, while the perfective verb delivers the new, completed piece of information that changes the situation.

A very helpful way to understand which verbal aspect to choose is to look closely at the question being asked by your conversation partner. The question "Що ти робив?" (What were you doing?) specifically asks about the process, the effort, or the time spent, and it strictly requires an imperfective answer. However, the question "Що ти зробив?" (What did you get done?) focuses entirely on the final result and requires a perfective answer.

:::info
**Grammar box**
English speakers frequently make the mistake of using the imperfective past tense for absolutely every past action. This happens because the English simple past (like "I read the book") covers both the process and the result. In Ukrainian, if you actually finished reading the book, you must use the perfective "прочитав". Saying "я читав книгу" simply implies you spent time reading it, but perhaps you abandoned it halfway through.
:::

Mastering this fundamental distinction takes deliberate practice, but it completely changes how natural you sound in spoken Ukrainian. When you correctly pair the continuous process with the definitive result, your personal stories become vivid, accurate, and highly engaging. Pay close attention to the context of your daily conversations, listen carefully to native speakers, and soon choosing the right aspect will feel entirely instinctive.

### Читаємо українською (Reading Practice)

Вчора був дуже довгий і цікавий день. Зранку я уважно читав новий журнал про сучасне мистецтво. Я читав його дві години, але так і не прочитав до кінця. Потім мій друг несподівано написав мені коротке повідомлення. Він запропонував піти в затишне кафе на центральній площі. Ми зустрілися там, замовили смачну каву і довго розмовляли про наші майбутні плани. Коли ми нарешті випили каву, ми вирішили погуляти вечірнім містом. Це був чудовий відпочинок після важкого робочого тижня.

> *Yesterday was a very long and interesting day. In the morning I was carefully reading a new magazine about modern art. I was reading it for two hours, but still did not read it to the end. Then my friend unexpectedly wrote me a short message. He suggested going to a cozy cafe on the central square. We met there, ordered delicious coffee and talked for a long time about our future plans. When we finally drank the coffee, we decided to walk around the evening city. It was a wonderful rest after a hard work week.*

<!-- INJECT_ACTIVITY: match-up-story-aspect -->
<!-- INJECT_ACTIVITY: match-up-narrative-questions -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: foundations-practice
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

**Level: A2 (Module 7/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

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
