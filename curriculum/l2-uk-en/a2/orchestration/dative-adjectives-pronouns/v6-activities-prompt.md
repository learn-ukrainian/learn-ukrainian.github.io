<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-adjectives-pronouns.yaml` file for module **19: Моєму другові, нашій вчительці** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-sort-dative-adjective-forms-by-gender-masculine-feminine-plural -->`
- `<!-- INJECT_ACTIVITY: quiz-possessive-forms -->`
- `<!-- INJECT_ACTIVITY: match-up-nominative-dative -->`
- `<!-- INJECT_ACTIVITY: fill-in-dative-phrases -->`
- `<!-- INJECT_ACTIVITY: error-correction-agreement -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete dative noun phrases with the correct adjective/pronoun ending (мо___
    друг___)
  items: 8
  type: fill-in
- focus: Choose the correct dative form of the possessive pronoun (моєму vs. моїй
    vs. моїм)
  items: 8
  type: quiz
- focus: Match nominative noun phrases to their dative equivalents (мій друг → моєму
    другові)
  items: 8
  type: match-up
- focus: Sort dative adjective forms by gender (masculine -ому, feminine -ій, plural
    -им)
  items: 8
  type: group-sort
- focus: Find and fix adjective-pronoun agreement errors in dative phrases (e.g.,
    *моїй другові → моєму другові, *нашому вчительці → нашій вчительці)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- вказівний (demonstrative)
- узгодження (agreement (grammar))
- іменникова група (noun phrase)
- їхньому (to their (masc./neut. dat.))
required:
- моєму (to my (masc./neut. dat.))
- моїй (to my (fem. dat.))
- твоєму (to your (masc./neut. dat.))
- нашій (to our (fem. dat.))
- цьому (to this (masc./neut. dat.))
- тому (to that (masc./neut. dat.))
- новому (to the new (masc./neut. dat.))
- старшому (to the older (masc./neut. dat.))
- прикметник (adjective)
- присвійний (possessive)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Прикметники у давальному відмінку (~660 words)

When you give a gift to a friend, the form of the word for "friend" changes to the Dative case. But what if you want to specify exactly which friend you mean? Giving a thoughtful gift to a new friend is quite different from giving one to an old friend. In Ukrainian grammar, every **прикметник** (adjective) must perfectly agree with the noun it describes. This fundamental concept is called **узгодження** (agreement). If the core noun is in the Dative case because it is the recipient of an action, the attached adjective must also be in the Dative case. It must match the noun's gender, number, and case perfectly to form a cohesive grammatical unit. This creates a beautiful harmony in the sentence.

Уявіть, що ви обираєте подарунок на свято. Ви купуєте цікаву книгу новому другу. Або ви купуєте квитки в театр старому другу. Прикметник і іменник працюють разом як одна граматична команда.

> *Imagine that you are choosing a gift for a holiday. You buy an interesting book for a new friend. Or you buy theater tickets for an old friend. The adjective and the noun work together as one grammatical team.*

For masculine and neuter nouns, the Dative adjective ending is very consistent and easy to spot. Most adjectives belong to the hard group, meaning their stem ends in a hard consonant. These adjectives take the strong, resonant ending "-ому". For example, "новий" becomes **новому** (to the new (masc./neut. dat.)), and "старший" becomes **старшому** (to the older (masc./neut. dat.)). If an adjective belongs to the soft group, it takes the softer, but very similar ending "-ьому". For example, "синій" becomes "синьому", and "останній" becomes "останньому". Notice a beautiful phonetic feature of the Ukrainian language here: it unifies the "-ому" sound across both hard and soft groups. This makes the language melodic and highly predictable compared to other Slavic languages, which often have diverging sounds.

Я часто допомагаю старшому братові ремонтувати його нову машину. Цей яскравий колір дуже пасує синьому костюму. Ми завжди щиро радіємо кожному теплому дню весни.

> *I often help my older brother repair his new car. This bright color really suits the blue suit. We always sincerely rejoice at every warm spring day.*

Feminine adjectives in the Dative case are even easier to learn and remember. Both hard and soft stems take the exact same elegant ending: "-ій". So, the hard-stem adjective "нова" simply becomes "новій", "стара" becomes "старій", and the soft-stem adjective "синя" becomes "синій". There is also a special, very friendly rule for adjectives whose stems end in the harsh consonants "г", "к", or "х", such as "довга" or "тиха". Unlike feminine nouns, which often soften and change their consonant in the Dative case, adjectives stubbornly keep their original consonant. You simply add "-ій" to get "довгій" and "тихій".

Я зараз телефоную новій колезі по роботі. Він уважно пише довге повідомлення старій знайомій. Ми повільно йдемо по дуже довгій вулиці міста.

> *I am currently calling a new colleague from work. He is carefully writing a long message to an old female acquaintance. We are walking slowly along a very long city street.*

:::note
**Quick tip** — Remember that the noun might change its consonant in the Dative case, but the adjective before it will not. You will say "дорогій подрузі", never "дорозі подрузі".
:::

When dealing with plural nouns in the Dative case, the adjective ending becomes completely uniform across all genders. This is a huge relief for language learners! Every plural adjective, regardless of whether it describes a group of masculine, feminine, or neuter nouns, takes the exact same ending: "-им". This means that "нові" simply changes to "новим", "старі" becomes "старим", "гарні" becomes "гарним", and "сині" becomes "синім". You do not have to worry about the gender of the noun at all when you are speaking in the plural. This simplicity allows you to focus purely on the meaning of your sentence.

Ми часто купуємо солодкі подарунки маленьким дітям на свята. Вона з великою радістю розповідає цю смішну історію новим сусідам. Я завжди намагаюся допомагати моїм старим друзям.

> *We often buy sweet gifts for little children for the holidays. She tells this funny story to new neighbors with great joy. I always try to help my old friends.*

Let's look at a comprehensive chart comparing the Nominative, Genitive, and Dative adjective endings. Recognizing these vertical patterns will make it much easier to choose the correct ending in fluid conversation. Notice how the Dative forms build an entirely different sound profile compared to the Genitive forms you learned previously. The Genitive often features an "-ого" or "-ої" sound, while the Dative introduces the characteristic "-ому" and "-ій" sounds.

:::info
**Adjective Endings Comparison (Hard Stem)**
| Відмінок (Case) | Чоловічий (Masc.) / Середній (Neut.) | Жіночий (Fem.) | Множина (Plural) |
| :--- | :--- | :--- | :--- |
| Називний (Nom.) | новий / нове | нова | нові |
| Родовий (Gen.) | нового | нової | нових |
| Давальний (Dat.) | **новому** | **новій** | **новим** |
:::

Ця таблиця показує логіку української мови. Кожен відмінок має свій унікальний звук. Ви швидко запам'ятаєте ці нові закінчення.

> *This table shows the logic of the Ukrainian language. Each case has its unique sound. You will quickly remember these new endings.*

Now let's see these familiar A1 and A2 adjectives in action through simple, everyday situations. Read these short sentences aloud and pay close attention to how the adjective and the noun harmonize perfectly in the Dative case. The more you hear these pairs spoken together, the more natural they will feel when you need to use them in your own speech. Practice makes perfect, especially with agreement.

Я зараз телефоную новому другу. Я з радістю допомагаю новій подрузі. Вчитель дає дуже складне завдання розумним студентам.

> *I am currently calling a new friend. I gladly help a new female friend. The teacher gives a very difficult task to smart students.*

<!-- INJECT_ACTIVITY: group-sort-sort-dative-adjective-forms-by-gender-masculine-feminine-plural -->

## Присвійні та вказівні займенники у давальному відмінку (~600 words)

In Ukrainian, a **присвійний** (possessive) pronoun or a demonstrative pronoun usually acts just like a **прикметник** (adjective) when it comes to case endings. When you want to say that you are giving a gift "to my friend" or explaining a difficult concept "to this teacher", the pronoun must agree perfectly with the noun in the Dative case. These pronouns answer the questions «чиєму?» or «чиїй?» (to whose?) and «якому?» or «якій?» (to which?). If you have already mastered the standard adjective endings from the previous section, learning how to decline these pronouns will feel very familiar and logical.

Let's start with the pronouns that mean "my", "your" (informal), and "one's own": «мій», «твій», and «свій». For masculine and neuter nouns, these pronouns take the ending «-єму», giving us words like **моєму** (to my (masc./neut. dat.)) and **твоєму** (to your (masc./neut. dat.)). When addressing an older male sibling, you might use an adjective like **старшому** (to the older (masc./neut. dat.)) before the noun. For feminine nouns, they take the ending «-їй», such as **моїй** (to my (fem. dat.)). Because the stems of these pronouns end in a vowel, they require a softer, more melodic transition into the case ending compared to regular hard adjectives.

Я завжди довіряю моєму старшому братові, бо він дуже розумний. Батько купив новий телефон моїй сестрі на день народження. Твоєму другові потрібна наша допомога зараз. Кожна людина бажає щастя своєму синові.

> *I always trust my older brother because he is very smart. Father bought a new phone for my sister for her birthday. Your friend needs our help right now. Every person wishes happiness to their own son.*

:::note
**Quick tip** — Notice how the ending «-єму» has an «є» instead of an «о». This happens because the stem of these pronouns ends in a vowel sound, which naturally softens the following letter in Ukrainian pronunciation.
:::

The pronouns «наш» (our) and «ваш» (your formal or plural) behave exactly like standard hard-stem adjectives, similar to **новому** (to the new (masc./neut. dat.)). They take the familiar ending «-ому» for masculine and neuter nouns, and «-ій» for feminine nouns, giving us forms like **нашій** (to our (fem. dat.)). The pronoun «їхній» (their), however, acts like a soft-stem adjective. It takes the ending «-ьому» for masculine and neuter, and «-ій» for feminine.

Ми дуже вдячні нашій вчительці за цікаві уроки. Директор передав важливі документи вашому новому колезі. Вони часто допомагають їхньому сусідові з ремонтом квартири. Ми хочемо зробити приємний сюрприз їхній мамі.

> *We are very grateful to our teacher for the interesting lessons. The director passed the important documents to your new colleague. They often help their neighbor with apartment renovations. We want to make a pleasant surprise for their mom.*

There is one crucial rule you must remember about the possessive pronouns «його» (his/its) and «її» (her). When they are used to indicate possession, they never change their form, regardless of the case. A very common mistake for English-speaking learners is trying to add Dative endings to these words. If you want to give a gift to "his friend" (його друг), it simply becomes «його другові». You must never say "йогому" or "їїй" — those forms do not exist in the Ukrainian language.

Я детально пояснюю це нове правило його другові. Вона телефонує її сестрі кожного вечора після роботи.

> *I am explaining this new rule in detail to his friend. She calls her sister every evening after work.*

Now let's look at the demonstrative pronouns «цей» (this) and «той» (that), which are essential for pointing things out. The pronoun «цей» becomes **цьому** (to this (masc./neut. dat.)) for masculine and neuter nouns, and «цій» for feminine nouns. The pronoun «той» changes to **тому** (to that (masc./neut. dat.)) and «тій». In the plural, for all genders, they become «цим» and «тим». These words are extremely common when you need to specify exactly which person or object is receiving the action of your verb.

Поясни це складне завдання тому хлопцеві в синій куртці. Цьому старому будинку потрібен великий ремонт. Я хочу подарувати ці красиві квіти цій дівчині. Що ти скажеш тим людям на вулиці?

> *Explain this difficult task to that boy in the blue jacket. This old building needs major repairs. I want to give these beautiful flowers to this girl. What will you say to those people on the street?*

:::info
**Grammar box** — The forms «цьому» and «тому» are incredibly common in everyday Ukrainian speech. You will hear them constantly when people point things out or clarify exactly who they are talking to.
:::

To summarize, possessive and demonstrative pronouns are the grammatical glue that holds your Dative noun phrases together. By accurately matching the pronoun's ending to the noun it describes, you ensure that your sentence is clear and sounds perfectly natural to a native speaker's ear. Let's practice these new patterns to build your confidence.

<!-- INJECT_ACTIVITY: quiz-possessive-forms -->
<!-- INJECT_ACTIVITY: match-up-nominative-dative -->

## Повні іменникові групи у давальному відмінку (~550 words)

When you want to be specific, you will often combine a possessive pronoun, an adjective, and a noun into a single phrase. This is called an іменникова група (noun phrase). The most important rule here is total agreement. The Ukrainian word for adjective is **прикметник** (adjective), and the word for possessive is **присвійний** (possessive). When building a full noun phrase, the possessive pronoun, the adjective, and the noun must all match perfectly in gender, number, and case. In our situation, that means they all need to be in the Dative case. The word order remains exactly the same as in the Nominative case: possessive first, then adjective, then the core noun.

Let's see this total agreement in action. Imagine a teacher handing back graded essays to her class.

> — **Вчитель:** Моєму найкращому студентові — десятка! Нашій новій студентці — дев'ятка. А цьому хлопцю треба більше працювати. *(To my best student — a ten! To our new student — a nine. And this boy needs to work more.)*
> — **Студенти:** Дякуємо нашій добрій вчительці! *(We thank our kind teacher!)*

Let's analyze the phrases from the dialogue to see how the mechanics work. In the phrase «моєму найкращому студентові», the core noun is masculine. Therefore, the pronoun takes the masculine form, which is **моєму** (to my (masc./neut. dat.)), and the adjective takes the «-ому» ending. For the feminine phrase «нашій новій студентці», everything shifts to the feminine endings. The pronoun becomes **нашій** (to our (fem. dat.)), the adjective takes «-ій», and the noun ends in «-і». Finally, «цьому хлопцю» shows how a demonstrative pronoun like **цьому** (to this (masc./neut. dat.)) perfectly matches the masculine Dative noun.

These full phrases are incredibly useful in everyday situations. For example, you will use them when giving presents, such as giving a gift to a female relative using **моїй** (to my (fem. dat.)) or to a male friend using **твоєму** (to your (masc./neut. dat.)). You also need them when writing messages to family members or colleagues.

When explaining things to someone specific, you must carefully match the endings. This applies whether you are talking to a colleague using **тому** (to that (masc./neut. dat.)), a new person using **новому** (to the new (masc./neut. dat.)), or an older sibling using **старшому** (to the older (masc./neut. dat.)).

Я хочу подарувати цю книгу моєму дорогому другові. Ми завтра напишемо повідомлення нашій старій бабусі. Мені потрібно пояснити це завдання тому новому студентові. Я завжди допомагаю моїй молодшій сестрі та твоєму старшому братові.

> *I want to give this book to my dear friend. We will write a message to our old grandmother tomorrow. I need to explain this task to that new student. I always help my younger sister and your older brother.*

When building these longer phrases, a common mistake for English-speaking learners is mixing genders. You must never combine a masculine pronoun with a feminine noun, or vice versa. Phrases like «моїй другові» or «нашому вчительці» are incorrect and will sound very confusing to a native speaker. Always establish the gender of the core noun first, and then make sure your pronoun and adjective endings perfectly align with it.

:::info
**Grammar box** — Think of the noun as the "boss" of the phrase. The noun dictates the gender, and all the descriptive words (pronouns and adjectives) must put on the correct "uniform" (endings) to match the boss in the Dative case.
:::

<!-- INJECT_ACTIVITY: fill-in-dative-phrases -->
<!-- INJECT_ACTIVITY: error-correction-agreement -->

## Порівняння відмінків (~390 words)

Comparing cases is an essential step if you want to truly master the Ukrainian language and speak with confidence. As you learn more cases, the different endings can naturally start to blur together. Learners very often confuse the endings of the Nominative, Genitive, and Dative cases. This happens particularly often for feminine nouns and their modifiers. By placing these forms side-by-side, we can easily reveal the distinct patterns and avoid common conversational mistakes. Whenever you see a **прикметник** (adjective) or a **присвійний** (possessive) pronoun, its ending acts as a signal, telling you exactly what role the core noun plays in the sentence.

Let's start by comparing the masculine and neuter forms in context.

Ось називний відмінок: це мій новий друг. А це родовий відмінок: у мене немає мого нового друга. Тепер подивіться на давальний відмінок: я завжди допомагаю моєму новому другові. Ти даєш цікаву книгу твоєму старшому братові. Ми пояснюємо це складне завдання цьому новому студентові або тому хлопцю.

> *Here is the Nominative case: this is my new friend. And this is the Genitive case: I don't have my new friend. Now look at the Dative case: I always help my new friend. You give an interesting book to your older brother. We explain this difficult task to this new student or to that boy.*

Notice the clear and consistent difference in the endings. The Genitive case strictly uses **-ого** for both adjectives and pronouns. However, the Dative case relies on the **-ому** ending, as seen in words like **новому** (to the new (masc./neut. dat.)) and **цьому** (to this (masc./neut. dat.)). Sometimes you will also see the word **тому** (to that (masc./neut. dat.)) used to point out a specific person.

For soft stems and certain pronouns, the ending becomes **-єму**. This is why we say **моєму** (to my (masc./neut. dat.)) and **твоєму** (to your (masc./neut. dat.)). If you want to describe someone's age relative to yours, you might give a gift to an older sibling using the word **старшому** (to the older (masc./neut. dat.)). It is absolutely crucial to remember that Ukrainian endings are unified; both hard and soft masculine adjectives comfortably take the **-ому** ending in the Dative case.

Now, let's carefully examine the feminine forms, where the distinction between Genitive and Dative is extremely important for clear communication.

Ось називний відмінок: це моя нова подруга. А це родовий відмінок: це гарний подарунок для моєї нової подруги. Тепер подивіться на давальний відмінок: я з радістю дарую квіти моїй новій подрузі. Ми зараз телефонуємо нашій дорогій мамі.

> *Here is the Nominative case: this is my new friend. And this is the Genitive case: this is a beautiful gift for my new friend. Now look at the Dative case: I joyfully give flowers to my new friend. We are calling our dear mother right now.*

In the feminine paradigm, we must sharply contrast the Genitive **-ої** ending with the Dative **-ій** ending. When you encounter forms like **моїй** (to my (fem. dat.)) or **нашій** (to our (fem. dat.)), you know immediately that you are dealing with the Dative case. The ending tells you exactly who is receiving the action.

Remember that prepositions and verbs dictate the required case. A preposition like «для» (for) always triggers the Genitive case, so you would say «для їхньої мами» (for their mother). Conversely, a verb like «допомагати» (to help) always triggers the Dative case without a preposition, so you must say «допомагаю їхній мамі» (I help their mother).

:::info
**Grammar box** — Always look at the main verb or the preposition first! They act as traffic controllers, telling your adjectives and pronouns exactly which case endings they need to wear.
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-adjectives-pronouns
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

**Level: A2 (Module 19/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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
