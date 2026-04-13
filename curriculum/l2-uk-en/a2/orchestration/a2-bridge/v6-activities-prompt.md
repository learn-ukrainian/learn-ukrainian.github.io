<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a2-bridge.yaml` file for module **1: Ласкаво просимо до рівня А2** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-case-identification -->`
- `<!-- INJECT_ACTIVITY: fill-in-phonological-alternations -->`
- `<!-- INJECT_ACTIVITY: match-up-euphony-choice -->`
- `<!-- INJECT_ACTIVITY: error-correction-euphony -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Case Identification Drill
  items: 8
  type: quiz
- focus: Phonological Alternation Pairs
  items: 8
  type: fill-in
- focus: Euphony Choice Exercise
  items: 8
  type: match-up
- focus: Euphony Error Correction
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- милозвучність (euphony, melodiousness)
- огляд (review, overview)
- система (system)
- правило (rule)
required:
- відмінок (case)
- називний (nominative)
- знахідний (accusative)
- місцевий (locative)
- кличний (vocative)
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- наголос (stress (accent))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пригадуємо відмінки (~660 words)

Welcome back! Let us imagine your first day at a language school in Kyiv as you start the A2 level. You walk into the classroom, meet your teacher, and immediately start using all the grammatical cases you learned in the A1 level to introduce yourself.

> — **Викладач:** Добрий день! Ласкаво просимо до рівня А2. *(Good afternoon! Welcome to the A2 level.)*
> — **Новий студент:** Привіт, Оксано! Дякую. Я — новий студент. *(Hi, Oksana! Thank you. I am a new student.)*
> — **Викладач:** Дуже приємно. Що ви робите тут? *(Nice to meet you. What are you doing here?)*
> — **Новий студент:** Я вивчаю українську мову. Я живу в Києві. *(I am studying the Ukrainian language. I live in Kyiv.)*
> — **Викладач:** Чудово! Ви вже добре говорите. *(Wonderful! You already speak well.)*

In this short exchange, the student successfully used the Nominative case for the subject («студент»), the Accusative case for the direct object («українську мову»), the Locative case for the location («в Києві»), and the Vocative case to address the teacher («Оксано»).

Welcome to the A2 level! In this phase of your learning journey, we are going to organize and expand everything you know about Ukrainian grammar. The cornerstone of this entire system is the concept of a **відмінок** (case). In Ukrainian, nouns change their endings based on their specific grammatical role in the sentence. This process is known as declension. Instead of relying purely on a strict word order like we do in English, Ukrainian uses these changing endings to show exactly who is doing the action, what is receiving the action, or where the action takes place. By mastering how to change these endings, you unlock the ability to construct flexible, natural, and complex sentences. It allows you to speak with true precision.

Let us start our review with the two most foundational cases. The **називний** (nominative) case is the basic dictionary form of a word. It answers the questions "who?" or "what?" (Хто? Що?) and always acts as the main subject or the "doer" of the sentence. Whenever you look up a word in a dictionary or learn a new noun from a vocabulary list, you are always learning it in the Nominative case. In contrast, the **кличний** (vocative) case stands apart because it does not answer any specific question and never acts as a subject or an object. Instead, it has one specific and vital purpose: addressing someone directly.

Кличний відмінок є душею українського спілкування. Коли ми звертаємося до людини, ми обов'язково змінюємо закінчення її імені. Ми кажемо «друже», «мамо» або «Оксано».

> *The Vocative case is the soul of Ukrainian communication. When we address a person, we obligatorily change the ending of their name. We say "friend", "mom", or "Oksana".*

:::tip
**Did you know?**
The Vocative case is a living, essential feature of the Ukrainian language. Unlike in Russian, where the vocative has largely disappeared from modern speech, failing to use the Vocative in Ukrainian when addressing someone sounds incredibly unnatural and immediately marks you as a foreigner. It is a beautiful marker of the language's unique identity.
:::

Next, we review the cases that handle objects and locations. The **знахідний** (accusative) case identifies the direct object of an action. It answers the questions "whom?" or "what?" (Кого? Що?). If you read a fascinating book, drink cold water, or see an old friend, those nouns must take the Accusative form because the action of the verb is happening directly to them. On the other hand, the **місцевий** (locative) case is used exclusively to indicate a physical or abstract location, answering the questions "where?", "on whom?", or "on what?" (Де? На кому? На чому?).

Місцевий відмінок є особливим, тому що він ніколи не вживається самостійно. Цей відмінок завжди вимагає прийменника, такого як «у», «в» або «на». Без прийменника він не має сенсу.

> *The Locative case is special because it is never used independently. This case always requires a preposition, such as "in", "in", or "on". Without a preposition, it makes no sense.*

To truly think in Ukrainian, you need to see the whole picture. The Ukrainian language features a complete system of exactly seven cases. While you already know four of them from your previous studies, seeing them all arranged together helps you understand how the language functions as a beautiful, interconnected web. The seven cases are: Nominative (Називний), Genitive (Родовий), Dative (Давальний), Accusative (Знахідний), Instrumental (Орудний), Locative (Місцевий), and Vocative (Кличний).

:::info
**Grammar box**
Ukrainian students learn a fun mnemonic phrase in school to remember the exact order of the seven cases. The first letter of each word matches the first letter of a case:
**Н**ашого **Р**омчика **Д**ивує **З**ебра — **О**ця **М**аленька **К**расуня.
*(Our Romchyk is surprised by the zebra — this little beauty.)*
:::

As you progress through the A2 level, you will conquer the remaining three cases, unlocking exciting new layers of expression. You will learn the Genitive case to talk about absence, possession, and quantities. You will master the Dative case to express who receives an action or who is experiencing a certain feeling. Finally, you will explore the Instrumental case to describe the tools you use to perform an action or the people you spend your time with. These new grammatical tools will bridge the gap between making simple, isolated statements and engaging in fluent, detailed conversations about your daily life.

<!-- INJECT_ACTIVITY: quiz-case-identification -->

## Магія української фонології (~770 words)

Welcome to the magic of Ukrainian sounds. As you continue your journey, you will notice that words often change slightly when they take on new grammatical roles. These changes in word stems during declension are not random exceptions designed to frustrate learners. Instead, they follow deep historical, predictable patterns that make the language flow smoothly. To master these patterns, we need to introduce the concept of **чергування** (alternation). This process involves swapping one sound for another. We will look at the predictable swapping of a **голосний** (vowel) as well as the transformation of a **приголосний** (consonant). Understanding these rules will make vocabulary acquisition much more intuitive.

Українська мова має дуже логічну систему звуків. Коли ми змінюємо форму слова, ми часто змінюємо один звук на інший. Це робить нашу мову мелодійною та зручною для швидкого мовлення.

> *The Ukrainian language has a very logical sound system. When we change the form of a word, we often change one sound to another. This makes our language melodic and convenient for fast speech.*

Let us start with the most famous vowel shift in the language: the alternation of «о» or «е» with «і». This happens because of the "closed syllable" rule. A closed syllable is one that ends in a consonant. Historically, when a syllable became closed, the vowels «о» and «е» transformed into the narrower sound «і». However, when you add an ending to the word, the syllable opens up again, and the original «о» or «е» returns. This explains why dictionaries show one vowel, but sentences demand another.

Мій брат купив новий стіл. Цього великого стола раніше тут не було. Я дуже люблю Київ. Ми поїхали з Києва до Львова.

> *My brother bought a new table. This big table was not here before. I love Kyiv very much. We went from Kyiv to Lviv.*

As you can see, the base form «стіл» has a closed syllable, so it uses «і». But when the **відмінок** (case) changes to Genitive, it becomes «стола». The syllable is now open (сто-ла), so the «о» comes back. The exact same magic happens with the capital of Ukraine: «Київ» uses «і», but «з Києва» reveals the hidden «е».

Now we move to consonant alternations, specifically the first palatalization. This is a crucial rule for feminine nouns ending in «-а» or «-я». When these nouns are put into the Dative or **місцевий** (locative) cases, the ending changes to «-і». But Ukrainian phonetics strongly dislikes pronouncing the hard consonants «г», «к», or «х» right before the soft vowel «і». Therefore, these consonants soften and mutate: «г» becomes «з», «к» becomes «ц», and «х» becomes «с».

Моя права нога дуже болить. У мене є маленька рана на нозі. Мама тримає дитину за руку. У її руці є нова іграшка. На вікні сидить велика муха. Я бачу бруд на цій мусі.

> *My right leg hurts a lot. I have a small wound on my leg. The mother holds the child by the hand. There is a new toy in her hand. A big fly is sitting on the window. I see dirt on this fly.*

:::note
**Quick tip**
A very common mistake among learners is saying «подругі» (to a female friend) instead of the correct «подрузі». Always remember that the «г» must change to a «з» before the «і» ending in these cases!
:::

Another fascinating aspect of Ukrainian pronunciation is consonant assimilation. First, you should know that the letter combinations «дж» and «дз» function as single sounds, known as affricates. They are not two separate consonants smashed together, but rather one unified, buzzing sound. You will hear this in words like «джерело» (spring) or «бджола» (bee). Furthermore, Ukrainian features voicing assimilation before voiced consonants. This means that a voiceless consonant will borrow the "voice" of the consonant immediately following it.

У лісі є чисте джерело. Там літає велика бджола. Наша боротьба за свободу триває. Ми довго чекали нашого друга біля вокзалу.

> *There is a clean spring in the forest. A big bee is flying there. Our struggle for freedom continues. We waited a long time for our friend near the station.*

In the word «боротьба» (struggle), the voiceless «т» stands before the voiced «б». Because of this, the «т» is pronounced as a voiced «д», making the word sound like [бород'ба]. You can also observe this in «просьба» (request), which sounds like [проз'ба]. Similarly, «вокзал» (train station) is pronounced [воґзал] because the voiceless «к» assimilates to the voiced «з» that follows it.

Let us talk about the soul of a word: its **наголос** (stress (accent)). In Ukrainian, stress is not fixed to a specific syllable like it is in some other languages. It is free and mobile, which means it plays a crucial role in conveying correct meaning. Sometimes, the only difference between two completely different words is which syllable receives the emphasis. These words are called homographs. Misplacing the stress can completely change what you are trying to say.

Ми дивимося на старовинний замок. Мій новий замок на дверях зламався. Я ніколи не їм м'яса. Мені зараз ніколи відпочивати.

> *We are looking at an ancient castle. My new lock on the door broke. I never eat meat. I have no time to rest right now.*

If you stress the first syllable in «замок», it means "castle". If you stress the second syllable, it means "lock". Similarly, «ніколи» means "never", but «ніколи» means "no time". Mastering stress patterns is just as important as learning the letters themselves.

Finally, you will discover that stress often shifts within the exact same word depending on its grammatical role. This mobile stress in noun paradigms is a key feature of the Ukrainian rhythm. The stress shifts between the word stem and the case ending across different forms. Recognizing these shifts will help you predict the pronunciation of new nouns and speak with a natural, authentic cadence.

Холодна вода тече з крана. Я хочу пити чисту воду. Моя права рука відпочиває. Мої дві руки дуже втомилися після роботи.

> *Cold water flows from the tap. I want to drink clean water. My right hand is resting. My two hands are very tired after work.*

Notice how the stress in «вода» in the **називний** (nominative) case falls on the ending, but when it becomes the direct object «воду» in the **знахідний** (accusative) case, the stress jumps back to the stem. The word «рука» stresses the ending, but «руки» stresses the stem. You will even see changes like this in the **кличний** (vocative) case. Embracing this shifting melody will bring your Ukrainian to a whole new level.

<!-- INJECT_ACTIVITY: fill-in-phonological-alternations -->

## Милозвучність мови: евфонія (~440 words)

Have you ever noticed how smooth and melodic Ukrainian sounds when spoken naturally? This rhythmic flow is called euphony, or **милозвучність** (euphony). The Ukrainian language actively avoids awkward clusters of vowels or consonants. It relies on a system of specific phonetic laws, known as **чергування** (alternation), to ensure that words connect seamlessly in speech. This euphonic alternation is not just an optional stylistic choice; it is a strict grammatical rule that every speaker follows. For example, Ukrainian naturally breaks up groups of three consonants to keep the melody alive. This is a fundamental law of the language, which stands in stark contrast to Russian, where heavy, unbroken consonant clusters are entirely normal and expected.

The most common euphonic alternation you will encounter involves the prepositions and prefixes «у» and «в». To maintain the melodic rhythm of your speech, you must choose between them based entirely on the surrounding sounds. If you are placing the preposition between two consonants, or if you are at the very beginning of a sentence before a **приголосний** (consonant), you must use «у». This inserts a necessary vowel break and makes the phrase much easier to pronounce. Conversely, if you are placing the preposition between two vowels, or immediately after a **голосний** (vowel) and before a consonant, you should use «в» to avoid vowel collision.

Він був у школі. У місті є новий парк. Вона пішла в аптеку. Ми живемо в Україні.

> *He was at school. There is a new park in the city. She went to the pharmacy. We live in Ukraine.*

You will apply this exact same melodic logic to the conjunctions «і» and «й», which both mean "and". When you connect words or ideas, the language demands a smooth, uninterrupted transition. You should use «і» when you are connecting two words that end and begin with consonants, or when you are starting a new phrase right after a pause in speech. On the other hand, you must use «й» when the word immediately before it ends in a vowel. This is especially important if the next word also starts with a vowel, preventing an awkward pause.

Мій брат і сестра читають книгу. Батько і мати працюють разом. Оксана й Андрій гуляють. Вона любить кіно й театр.

> *My brother and sister are reading a book. Father and mother are working together. Oksana and Andriy are walking. She loves the cinema and theater.*

Finally, the preposition meaning "with" or "from" changes its form to match its phonetic environment. The basic, default form is «з», which you will use before most single consonants or before vowels. However, if the following word starts with a difficult consonant cluster—especially those beginning with sibilant sounds like «с», «ш», or «з»—you must use «зі». This adds a crucial vowel break. Furthermore, you can use the form «із» between specific, heavy groups of consonants to perfectly maintain the rhythmic balance of the whole sentence.

Я часто гуляю з собакою. Цей студент працює зі мною. Моя донька повертається зі школи. Ми отримали лист із Києва.

> *I often walk with the dog. This student works with me. My daughter is returning from school. We received a letter from Kyiv.*

:::info
**Grammar box** — The choice between «у/в», «і/й», and «з/зі/із» depends almost entirely on whether the surrounding letters are a **голосний** (vowel) or a **приголосний** (consonant). Vowels and consonants take turns to keep the music of the sentence flowing smoothly.
:::

<!-- INJECT_ACTIVITY: match-up-euphony-choice -->
<!-- INJECT_ACTIVITY: error-correction-euphony -->

## Що нас чекає на рівні А2? (~330 words)

Welcome to the A2 level, where your Ukrainian journey shifts from making simple statements to expressing complex ideas and building true narrative ability. In our previous lessons, you established a solid core by learning how to identify the subject using the **називний** (nominative) case and the direct object using the **знахідний** (accusative) case. 

You also learned to describe locations using the **місцевий** (locative) case and how to politely address people with the **кличний** (vocative) case. Now, you will build on this essential framework to achieve true functional fluency. You will soon be able to tell detailed stories, clearly explain your reasoning, and participate comfortably in natural conversations.

The comprehensive roadmap for A2 contains several exciting grammatical milestones that will transform how you speak. First, we will complete our map of the noun **відмінок** (case) system by mastering the Genitive, Dative, and Instrumental cases. Next, you will discover the most significant milestone of Ukrainian verbs: verbal aspect, which elegantly distinguishes between ongoing processes and completed results.

As we learn new verb conjugation patterns and dynamic verbs of motion, you will notice frequent stem changes. This often involves predictable **чергування** (alternation) to make the word flow better. You will learn how a specific **голосний** (vowel) or **приголосний** (consonant) shifts depending on its environment. 

We will also pay close attention to correct **наголос** (stress (accent)), because shifting the emphasis can sometimes change a word's entire meaning. While the framework of rules might initially seem challenging to remember, mastering this foundation is incredibly rewarding and unlocks true fluency.

:::tip
**Did you know?** — The concept of verbal aspect is often considered the heart of Slavic languages. Mastering the difference between a process and a result will completely change how you express time in Ukrainian!
:::

Українська система іноді може здаватися дуже складною. Але кожне нове правило робить вашу мову більш красивою. Не бійтеся помилятися, коли ви активно говорите з людьми. Щоденна практика допомагає нам краще розуміти українську мову.

> *The Ukrainian system can sometimes seem very complex. But every new rule makes your language more beautiful. Do not be afraid to make mistakes when you actively speak with people. Daily practice helps us understand the Ukrainian language better.*

Every new ending you apply correctly brings you one step closer to thinking directly in Ukrainian. Embrace your inevitable mistakes as a vital, helpful part of the learning journey. Commit to active, joyful practice every day, and your progress will be remarkable.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a2-bridge
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

**Level: A2 (Module 1/60) — ELEMENTARY**

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
