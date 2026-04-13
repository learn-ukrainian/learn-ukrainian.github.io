<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-adjectives-pronouns.yaml` file for module **13: Мого друга, цієї книги** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-genitive-adjectives -->`
- `<!-- INJECT_ACTIVITY: quiz-possessive-pronouns -->`
- `<!-- INJECT_ACTIVITY: match-up-nom-to-gen -->`
- `<!-- INJECT_ACTIVITY: fill-in-demonstratives-full-phrases -->`
- `<!-- INJECT_ACTIVITY: error-correction-genitive-agreement -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the adjective and noun into the correct Genitive form
  items: 8
  type: fill-in
- focus: Choose the correct possessive pronoun form (мого vs. моєї etc.)
  items: 8
  type: quiz
- focus: Match Nominative noun phrases to their Genitive equivalents
  items: 8
  type: match-up
- focus: Build complete Genitive phrases with demonstrative + adjective + noun
  items: 8
  type: fill-in
- focus: Find and fix adjective-noun agreement errors in Genitive phrases (e.g., *нової
    друга → нового друга, *цієї будинку → цього будинку)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- молодий (young)
- старший (older, elder)
- дівчина (girl, young woman)
- олівець (pencil)
required:
- прикметник (adjective)
- займенник (pronoun)
- присвійний (possessive)
- вказівний (demonstrative)
- узгодження (agreement (grammatical))
- дозвіл (permission)
- підручник (textbook)
- документ (document)
- вчителька (female teacher)
- важливий (important)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Який? Якого? Прикметники в родовому (~770 words)

> — **Власник:** Добрий день! Я шукаю речі мого старшого брата. *(Good afternoon! I am looking for my older brother's things.)*
> — **Працівник:** Добрий день. Що саме ви шукаєте? *(Good afternoon. What exactly are you looking for?)*
> — **Власник:** Тут немає нашого великого чемодану? *(Is our large suitcase not here?)*
> — **Працівник:** Ні, великого чемодану немає. А ви не бачили цієї червоної парасольки? Вона ваша? *(No, the large suitcase is not here. And have you seen this red umbrella? Is it yours?)*
> — **Власник:** Ні, це не моя парасолька. Мій брат загубив ще свій підручник. *(No, this is not my umbrella. My brother also lost his textbook.)*
> — **Працівник:** Якого підручника у вас немає? *(Which textbook do you not have?)*
> — **Власник:** У нас немає нового підручника з історії. *(We do not have the new history textbook.)*

When you lose something or need to describe exactly what is missing, describing the object in detail is crucial. You cannot just say you lost a suitcase; you need to explain that it is a large suitcase or a new textbook. This means we must learn how to change adjectives to match the nouns they describe when we use the Genitive case. This skill allows you to be precise and specific in everyday situations.

Узгодження — це дуже важливе правило української мови. Коли іменник змінює свою форму, прикметник також обов'язково повинен змінитися. Вони завжди працюють разом як одна команда.

> *Agreement is a very important rule in the Ukrainian language. When a noun changes its form, the adjective must also absolutely change. They always work together as one team.*

In Ukrainian, an adjective (**прикметник**) always copies the gender, number, and case of the noun it modifies. This grammatical harmony is called agreement (**узгодження**). When a noun changes to the Genitive case—for example, after the word «немає», after expressions of quantity, or after specific prepositions—the adjective describing that noun must also change to reflect the Genitive case. Instead of asking «який?» (which one?), the Genitive form answers the questions «якого?» for masculine and neuter nouns, and «якої?» for feminine nouns. This is a very **важливий** (important) concept for speaking clearly.

Для чоловічого та середнього роду ми використовуємо закінчення -ого або -ього. Тверда група має закінчення -ого, а м'яка група має закінчення -ього. Ви часто будете чути ці слова.

> *For masculine and neuter genders, we use the endings -ого or -ього. The hard group has the ending -ого, and the soft group has the ending -ього. You will often hear these words.*

For masculine and neuter adjectives, the hard stem ending is `-ого`. For example, the word «новий» (new) becomes «нов**ого**», and «великий» (large) becomes «велик**ого**». If you are talking about a missing textbook (**підручник**), you use the Genitive and say «тут немає нового підручника». If you are describing a missing **документ** (document), you say «тут немає важливого документа». If the adjective belongs to the soft group, the ending softens to `-ього`. The word «синій» (dark blue) changes to «син**ього**», as in «без синього олівця».

:::info
**Decolonization Check: The Sound of `-ого`**
In Ukrainian, the `-ого` ending is always pronounced exactly as it is written: with a distinct «г» sound in the middle. It is never pronounced with a «v» sound like in Russian. Say «нового» with a clear, breathy «г» (like the 'h' in 'hello') to sound authentically Ukrainian!
:::

Жіночий рід у родовому відмінку завжди має інші закінчення. Прикметники твердої групи закінчуються на -ої. Прикметники м'якої групи закінчуються на -ьої.

> *The feminine gender in the Genitive case always has different endings. Adjectives of the hard group end in -ої. Adjectives of the soft group end in -ьої.*

Feminine Genitive adjectives are completely distinct from their masculine and neuter counterparts. For hard stem feminine adjectives, the ending is `-ої`. For example, «нова» changes to «нов**ої**», and «стара» changes to «стар**ої**». For soft stem adjectives, the ending is `-ьої`. The word «синя» becomes «син**ьої**». Notice how these endings clearly signal that we are dealing with a feminine noun. Learning to quickly distinguish between masculine and feminine Genitive endings is a major milestone in your Ukrainian journey.

Коли ми використовуємо прийменники з родовим відмінком, уся фраза працює як єдине ціле. Прикметник і іменник завжди змінюються разом. Це робить мову дуже мелодійною.

> *When we use prepositions with the Genitive case, the whole phrase works as a single unit. The adjective and the noun always change together. This makes the language very melodic.*

Let's look at how both the adjective and the noun change together as a unit when following prepositions that require the Genitive case. Common prepositions like «без» (without), «біля» (near), «від» (from), and «для» (for) always trigger the Genitive. This is where agreement really shines in everyday conversations.

**Він прийшов на урок без нового підручника.** — *He came to the lesson without a new textbook.*
**Ми зустрілися біля старої церкви в центрі міста.** — *We met near the old church in the city center.*
**У мене немає синього олівця для малювання.** — *I do not have a dark blue pencil for drawing.*

Великі речі часто губляться, а маленькі речі важко знайти. Ми описуємо старі та нові предмети щодня, коли говоримо про наше життя.

> *Large things often get lost, and small things are hard to find. We describe old and new objects every day when we talk about our lives.*

Here is a quick reference for common descriptive opposites in the Genitive case. You will use these constantly, so practice changing these forms when you describe missing objects, locations, or people:

- «великий» → «великого» (masculine/neuter), «великої» (feminine)
- «маленький» → «маленького» (masculine/neuter), «маленької» (feminine)
- «старий» → «старого» (masculine/neuter), «старої» (feminine)
- «молодий» → «молодого» (masculine/neuter), «молодої» (feminine)

<!-- INJECT_ACTIVITY: fill-in-genitive-adjectives -->

## Мого, твого, нашого: присвійні займенники (~715 words)

Now that you understand how the Ukrainian **прикметник** (adjective) changes, let's look at words like "my", "your", and "our". We call this type of word a **присвійний** (possessive) **займенник** (pronoun). It tells us who owns an object. You cannot simply memorize one word for "my" and use it everywhere. 

Instead, this pronoun requires strict **узгодження** (agreement (grammatical)) with the noun it describes. It must adapt to match the gender and case of the object being possessed. This is a core feature of the Ukrainian language.

Коли ми говоримо про наші речі, ми використовуємо присвійний займенник. Він завжди має той самий рід, число та відмінок, що й іменник. Ми не можемо змінити лише одне слово у фразі, коли будуємо речення.

> *When we talk about our things, we use a possessive pronoun. It always has the same gender, number, and case as the noun. We cannot change only one word in the phrase when we build a sentence.*

In English, words like "my" or "your" never change, regardless of the preposition you use. You say "without my brother" or "for my sister". In Ukrainian, you cannot simply say "without my" followed by a Genitive noun. Both the pronoun and the noun must be in the Genitive case. The whole phrase transforms together, creating a rhythmic and highly structured sentence.

For masculine and neuter nouns, the Genitive forms of possessive pronouns share the same `-ого` ending sound that you learned for adjectives. The pronoun «мій» (my) becomes «мого», and «твій» (your, informal) becomes «твого». You will need these forms when asking for a **дозвіл** (permission) or looking for an object.

Я йду на концерт без мого старшого брата. Ми не можемо почати цей проєкт без твого дозволу. У мене зараз немає мого синього олівця.

> *I am going to the concert without my older brother. We cannot start this project without your permission. I do not have my dark blue pencil right now.*

Notice how «мого» perfectly matches the adjectives and nouns that follow it. If you are addressing someone formally, or talking about something that belongs to "us", you use forms that look exactly like hard group adjectives. The pronoun «наш» (our) becomes «нашого», and «ваш» (your, formal/plural) becomes «вашого».

Діти зараз грають у футбол біля нашого нового будинку. Я все ще чекаю відповіді від вашого директора. Чому тут немає нашого великого чемодану?

> *The children are playing football near our new house right now. I am still waiting for an answer from your director. Why is our large suitcase not here?*

Feminine possessive pronouns in the Genitive case take endings that sound like `-еї` or `-ої`. The pronoun «моя» (my) changes to «моєї», and «твоя» (your, informal) changes to «твоєї». 

Я купив красиві квіти для моєї молодої дівчини. Він досі не знає адреси твоєї нової роботи. Ми живемо недалеко від моєї улюбленої кав'ярні.

> *I bought beautiful flowers for my young girlfriend. He still does not know the address of your new job. We live not far from my favorite coffee shop.*

When using "our" or "your" (formal/plural) with feminine nouns, the pronouns follow the standard hard group adjective pattern. The pronoun «наша» (our) becomes «нашої», and «ваша» (your, formal/plural) becomes «вашої». We often use these forms when talking about people like our **вчителька** (female teacher).

Вчора учні купили нову книгу для нашої вчительки. Я зовсім не бачу вашої машини біля школи. Ми вийшли з нашої квартири дуже рано вранці.

> *Yesterday the students bought a new book for our female teacher. I do not see your car near the school at all. We left our apartment very early in the morning.*

The third-person possessive pronouns — "his", "her", and "their" — behave quite differently from the others. The words «його» (his) and «її» (her) are completely unchanging when they indicate possession. They look exactly the same in the Nominative and Genitive cases, unlike a **вказівний** (demonstrative) pronoun which always changes. You only change the noun and any adjectives that follow them. We often use these when looking for a **підручник** (textbook).

Це його новий підручник, але зараз у мене немає його підручника. Це її велика сумка, а ключі лежать біля її сумки.

> *This is his new textbook, but right now I do not have his textbook. This is her large bag, and the keys are lying near her bag.*

However, "their" is a completely different story. The Ukrainian word for "their" is «їхній». This is a full adjective-like pronoun that belongs to the soft group, and it must decline along with the noun. For masculine and neuter nouns, it becomes «їхнього». For feminine nouns, it becomes «їхньої».

:::info
**Decolonization Check: "Their" is «їхній»**
A very common mistake (and a direct Russianism) is using the unchanging personal pronoun «їх» (them) to mean "their", as in ❌ «їх проблеми» (their problems) or ❌ «без їх друга». In standard Ukrainian, "their" is always the declining pronoun **їхній**. You must say ✅ «їхні проблеми» and, in the Genitive, ✅ «без їхнього друга». Never use «їх» for possession!
:::

Ми довго стояли біля їхнього старого будинку. Я справді не знаю номера телефону їхньої старшої сестри. Вони приїхали на свято без їхнього маленького сина.

> *We stood near their old house for a long time. I really do not know the phone number of their older sister. They arrived at the holiday without their little son.*

Let's consolidate these possessive forms with the spatial and logical prepositions you learned in previous modules. Remember that prepositions like «з» (from/out of), «без» (without), «для» (for), and «до» (to/towards) always require the Genitive case. A **важливий** (important) **документ** (document) or piece of information often follows these prepositions.

Моя найкраща подруга приїхала з мого рідного міста. Я ніяк не можу зробити це без твоєї допомоги. Це дуже важливий документ для нашого нового вчителя.

> *My best friend arrived from my hometown. I cannot do this without your help at all. This is a very important document for our new teacher.*

Notice how the preposition anchors the entire phrase. Every word that follows it — the pronoun, the adjective, and the noun — falls into the Genitive case in perfect grammatical harmony. This agreement is the core rhythm of the Ukrainian language. It might take some time to get used to changing two or three words instead of just one, but soon it will feel completely natural.

Сьогодні ми йдемо до вашої нової лікарні. Вона щойно повернулася з їхньої великої дачі. Цей дорогий подарунок лежить біля мого робочого стола.

> *Today we are going to your new hospital. She just returned from their large summer house. This expensive gift is lying near my work desk.*

<!-- INJECT_ACTIVITY: quiz-possessive-pronouns -->
<!-- INJECT_ACTIVITY: match-up-nom-to-gen -->

## Цього, того: вказівні займенники та повні фрази (~715 words)

You already know how to point at things using the Nominative case forms like «цей» (this) and «той» (that). When we talk about absence, quantity, or location, every single **займенник** (pronoun) must adapt to the Genitive case. A **вказівний** (demonstrative) pronoun specifically points out which exact item is missing from a group, or where something is located relative to a specific object. Just like adjectives, these pointing words change their endings to perfectly match the gender and case of the noun they describe. This creates a clear logical link.

Ми часто використовуємо вказівні займенники, коли шукаємо дуже конкретну річ у кімнаті. Я не бачу цього стола на нашому плані. Вона зараз стоїть біля того великого вікна.

> *We often use demonstrative pronouns when we are looking for a very specific thing in a room. I do not see this table on our plan. She is currently standing near that large window.*

For masculine and neuter nouns, the demonstrative pronouns take the specific ending «-ого». The word «цей» (this) softens and changes to «цього», while «той» (that) simply becomes «того». You will use these forms constantly in everyday conversation, especially with spatial prepositions like «біля» (near) or temporal prepositions like «після» (after). Remember that the pointing pronoun always comes directly before the noun or adjective it modifies. If you are searching your bag for a specific **підручник** (textbook) or handing over an official **документ** (document), you must use these exact Genitive forms to be understood clearly.

Студенти довго чекають біля цього старого будинку. Після того довгого дня ми просто хотіли швидко спати. Я вчора отримав важливого листа від цього нового вчителя. У мене сьогодні немає цього підручника, але є копія того документа.

> *The students are waiting near this old building for a long time. After that long day, we just wanted to sleep quickly. Yesterday I received an important letter from this new teacher. I do not have this textbook today, but I have a copy of that document.*

When pointing to feminine nouns, the ending shifts to «-єї». The pronoun «ця» (this) becomes «цієї», and «та» (that) becomes «тієї». There is also a slightly shorter, highly conversational form for "that": «тої». Both «тієї» and «тої» are absolutely correct and widely used in modern spoken Ukrainian. You will hear these feminine forms frequently when talking about people, like a **вчителька** (female teacher), or when asking for official **дозвіл** (permission) to enter a specific place or do a specific action.

Вони вчора купили гарні квіти для цієї молодої дівчини. Новий продуктовий магазин відкрили прямо навпроти тієї великої школи. Студенти ніколи не можуть піти додому без дозволу тієї вчительки. Ми ще не читали тої дуже цікавої книги.

> *Yesterday they bought beautiful flowers for this young girl. A new grocery store was opened right opposite that large school. The students can never go home without the permission of that female teacher. We have not yet read that very interesting book.*

:::info
**Grammatical Harmony**
Notice how the «-ої» ending of a feminine Genitive adjective rhymes perfectly with the «-ої» sound in «тої». This matching sound pattern across the whole phrase is a hallmark of Ukrainian sentence structure.
:::

Now you have all the grammatical puzzle pieces needed to build rich, descriptive phrases. The natural Ukrainian word order always places the demonstrative pronoun first, followed by any **присвійний** (possessive) pronoun or descriptive **прикметник** (adjective), and finally the noun itself. Every single modifier before the noun must take the appropriate Genitive case ending. This creates a beautiful rhythm where multiple words in a row share similar sounds. When you are describing something highly **важливий** (important), adding these stacked layers gives you much more precision and fluency.

Ми вчора зустрілися біля цього нового міського ринку. Я нарешті купив ідеальний подарунок для моєї старшої сестри. Вони ніяк не можуть почати працювати без того важливого документа.

> *We met yesterday near this new city market. I finally bought the perfect gift for my older sister. They cannot start working at all without that important document.*

This complete matching of endings across multiple words is called **узгодження** (agreement (grammatical)). It might seem slightly intimidating to change three or four words at once, but you can always build these complex phrases step by step in your head. Start with the core noun in the Genitive: «друга» (of a friend). Add an adjective: «нового друга» (of a new friend). Then add your demonstrative or possessive pronoun: «цього нового друга» (of this new friend). Finally, anchor the entire structure with a preposition: «для цього нового друга» (for this new friend).

Я зовсім не знаю номера телефону. Я зовсім не знаю номера телефону брата. Я зовсім не знаю номера телефону мого старшого брата. Я зовсім не знаю номера телефону цього старшого брата.

> *I do not know the phone number at all. I do not know the brother's phone number at all. I do not know my older brother's phone number at all. I do not know the phone number of this older brother at all.*

<!-- INJECT_ACTIVITY: fill-in-demonstratives-full-phrases -->
<!-- INJECT_ACTIVITY: error-correction-genitive-agreement -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-adjectives-pronouns
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

**Level: A2 (Module 13/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
