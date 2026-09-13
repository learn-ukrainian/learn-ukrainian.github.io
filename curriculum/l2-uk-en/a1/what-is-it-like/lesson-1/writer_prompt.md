# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: what-is-it-like.
Your current published unit: lesson 1.

Upgrade the supplied built module into the deterministic lesson map below.
Do not write a plan, retrieve a wiki packet, or author a replacement from scratch.
The original plan and artifacts are input evidence, never files you may change.
Return artifacts for the current lesson only using the existing V7 output contract.

## Lesson contract

Each lesson is a 60-minute block: warm-up and retrieval, Ukrainian-first presentation,
dialogue and breakdown, guided practice, independent practice, recap and next step.
Preserve every original paragraph in its mapped section and lesson verbatim, exactly
once across the split (only whitespace and deterministic stress annotation may differ).
The introduction belongs to lesson 1. Keep original section headings and activity IDs.
Expand with useful transitions, explanations and breakdown tables; never pad or repeat
paragraphs to meet the floor. Each lesson must meet its word_target (minimum 550);
the whole module must reach at least 2000 prose tokens. The final lesson closes the module.

Follow docs/best-practices/ulp-presentation-pattern.md and the v4 lesson contract.
Use a direct, friendly teaching voice with NO named narrator and NO self-introduction.
Named people occur only inside dialogues. Do not adopt any reference author's persona
or lesson structure. A quotation must be visibly marked, attributed, and have a matching
entry in resources.yaml (Ресурси). Preserve source provenance.
Ukrainian comes first, with English scaffolding appropriate to the supplied learner state.
Added Ukrainian passages of three or more sentences require side-by-side English support.
Write dialogues as > blockquotes, never as code fences; put the English breakdown after.
Verify language claims with sources/VESUM tools; never guess Ukrainian forms or stress.
Stress annotation runs deterministically AFTER review; do not invent stressed spellings.

## Activities and vocabulary

Keep every original activity's type, items, answer flags and groups structurally intact.
Use provenance to find its assigned lesson. Inline IDs stay unchanged; id-less workbook
originals use act-w1, act-w2, etc. Add distinct activities with globally unique IDs.
Each lesson needs >=10 activities: 4–6 inline and 6–9 workbook; >=6 items each unless
the deterministic map declares an original-item exemption. Do not create exemptions.
Use <!-- INJECT_ACTIVITY: id --> for each inline activity, once, in its relevant section.
Use only the base A1 placement/type matrix below. Preserve every option of odd-one-out.

Allocate each original vocabulary entry once, at its first teaching use. Keep the union
equal to the original vocabulary, with >=12 complete entries per lesson. Learner knowledge
is cumulative: prior-module vocabulary plus entries introduced in previous lessons.
Every entry needs lemma, translation, pos, usage. Every lesson needs nonempty resources
with title plus url, chunk_id or source. The landing page aggregates these artifacts.

TOTAL_TARGET: '10'
INLINE_MIN: '4'
INLINE_MAX: '6'
WORKBOOK_MIN: '6'
WORKBOOK_MAX: '9'
ITEMS_MIN: '6'
VOCAB_COUNT_TARGET: '20'
INLINE_ALLOWED_TYPES: image-to-letter, letter-grid, watch-and-repeat, divide-words,
  count-syllables, pick-syllables, unjumble, order, odd-one-out, observe, phrase-table,
  match-up, group-sort, quiz, true-false, fill-in
WORKBOOK_ALLOWED_TYPES: divide-words, count-syllables, pick-syllables, anagram, unjumble,
  order, odd-one-out, observe, phrase-table, match-up, group-sort, quiz, true-false,
  fill-in, error-correction, translate
INLINE_PRIORITY_TYPES: image-to-letter, match-up, fill-in, quiz, watch-and-repeat
WORKBOOK_PRIORITY_TYPES: fill-in, match-up, group-sort, anagram, unjumble
ACTIVITY_COUNT_TARGET: '10'
ACTIVITY_MIN: '0'
ACTIVITY_MAX: '15'
ALLOWED_ACTIVITY_TYPES: image-to-letter, letter-grid, watch-and-repeat, divide-words,
  count-syllables, pick-syllables, anagram, unjumble, order, odd-one-out, observe,
  phrase-table, match-up, group-sort, quiz, true-false, fill-in, error-correction,
  translate
FORBIDDEN_ACTIVITY_TYPES: classify, mark-the-words, cloze, grammar-identify, highlight-morphemes,
  essay-response, reading, critical-analysis, translation-critique, comparative-study,
  source-evaluation, authorial-intent, debate, etymology-trace, paleography-analysis,
  dialect-comparison, transcription, select
REQUIRED_TYPES: ''
PRIORITY_TYPES: fill-in, match-up, quiz, image-to-letter, watch-and-repeat


## Learner state before this lesson

(This is the first module — no prior learner knowledge.)
Previously introduced in this module: []

## Deterministic lessons.yaml (read-only)

lessons:
- n: 1
  title: Який? Яка? Яке?
  sections:
  - Діалоги
  - Який? Яка? Яке?
  minutes: 60
  word_target: 550
  activities:
    total: 10
    inline:
    - 4
    - 6
    workbook:
    - 6
    - 9
  unverified_stress: []
  unverified_lemmas: []
- n: 2
  title: Прикметники
  sections:
  - Прикметники
  minutes: 60
  word_target: 550
  activities:
    total: 10
    inline:
    - 4
    - 6
    workbook:
    - 6
    - 9
  unverified_stress: []
  unverified_lemmas: []
- n: 3
  title: Підсумок
  sections:
  - Підсумок
  minutes: 60
  word_target: 550
  activities:
    total: 10
    inline:
    - 4
    - 6
    workbook:
    - 6
    - 9
  unverified_stress: []
  unverified_lemmas: []
closes_module: 3
provenance:
- placement: inline
  index: 0
  new_id: act-1
  lesson: 1
- placement: inline
  index: 1
  new_id: act-2
  lesson: 1
- placement: inline
  index: 2
  new_id: act-3
  lesson: 1
- placement: inline
  index: 3
  new_id: act-4
  lesson: 2
- placement: workbook
  index: 0
  new_id: act-w1
  lesson: 1
- placement: workbook
  index: 1
  new_id: act-w2
  lesson: 1
- placement: workbook
  index: 2
  new_id: act-w3
  lesson: 2
- placement: workbook
  index: 3
  new_id: act-w4
  lesson: 2
- placement: workbook
  index: 4
  new_id: act-w5
  lesson: 3
- placement: workbook
  index: 5
  new_id: act-w6
  lesson: 3
items_min_exempt: []
proper_names: []


## Original plan (read-only)

module: a1-009
level: A1
sequence: 9
slug: what-is-it-like
version: 1.3.0
lifecycle: locked
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-what-is-it-like
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md
  template (worked example: at-the-cafe / PR #1412). See PR body for the wiki-side
  gap closure (lifecycle metadata, Типові помилки L2 table, writer-scope tightening)
  and the plan-side findings (no Russianisms in prose, no calques in vocab_hints,
  no plan-internal contradictions; the one drift gap — no plan-side hook for the wiki''s
  adjective Surzhyk table — was closed by adding a fill-in activity mirroring the
  table 1:1). Lifecycle marker convention per the rubric doc.'
title: Який він?
subtitle: Великий стіл, нова книга — опис предметів
focus: grammar
pedagogy: PPP
phase: A1.2 [Мій світ]
word_target: 1200
objectives:
- Навчитися узгоджувати прикметники з іменниками в роді (лише в називному відмінку)
- Вміти ставити запитання за допомогою слів який/яка/яке
- Описувати предмети та кімнати, використовуючи поширені пари прикметників
- Будувати описові речення, поєднуючи іменники з попереднього модуля «Речі мають рід»
  з прикметниками з цього модуля
- Впізнавати типові адʼєктивні суржикові пари (вкусний → смачний, жолтий → жовтий,
  черний → чорний, красний → червоний, плохий → поганий, вірний → правильний, любий
  → будь-який, умний → розумний, ленивий → лінивий)
dialogue_situations:
- setting: 'На книжковому ярмарку вихідного дня — розглядаємо книги, карти та плакати.
    Описуємо предмети: новий атлас (m), цікава книга (f), старе фото (n), великий
    плакат (m), маленька листівка (f). НЕ сумки чи меблі.'
  speakers:
  - Тарас
  - Софія
  motivation: Запитання Який/яка/яке? зі словами книга(f), атлас(m), фото(n), плакат(m),
    листівка(f)
content_outline:
- section: Діалоги
  words: 300
  points:
  - 'Діалог 1 — Опис кімнати (Вашуленко 3 клас, с.131 «Моя кімната»): — Яка твоя кімната?
    — Моя кімната велика і світла. — А стіл? — Стіл новий. А ліжко — старе. Узгодження
    прикметників засвоюється через природний опис предметів.'
  - 'Діалог 2 — Розглядання вітрин: — Яка гарна сумка! — Так, але вона дорога. — А
    телефон? Який він? — Він великий і дешевий.'
- section: Який? Яка? Яке?
  words: 300
  points:
  - 'Запитання до прикметників змінюється за родами — за тією ж схемою, що й мій/моя/моє:
    Який стіл? (m) → Великий стіл. Яка книга? (f) → Нова книга. Яке вікно? (n) → Чисте
    вікно.'
  - 'Пономарова 3 клас, с.98: Прикметник має той самий рід, що й іменник. Чоловічий
    рід: -ий (великий, новий, чистий). Жіночий рід: -а (велика, нова, чиста). Середній
    рід: -е (велике, нове, чисте). Прикметники м''якої групи (-ій/-я/-є, як-от «синій»)
    вивчатимуться в наступному модулі «Кольори». Ця закономірність повторюватиметься
    в кожному відмінку, тому її важливо добре засвоїти вже зараз.'
- section: Прикметники
  words: 300
  points:
  - 'Вивчаються парами (антоніми — так легше запам''ятати): великий ↔ маленький, новий
    ↔ старий, гарний ↔ поганий, чистий ↔ брудний, дорогий ↔ дешевий, світлий ↔ темний.'
  - 'Побудова описів із предметами з попереднього модуля («Речі мають рід»): У мене
    є великий стіл. Моя кімната маленька, але гарна. Вікно велике і чисте. Стілець
    старий, а ліжко — нове. Зверніть увагу: «а» використовується для протиставлення,
    «і» — для поєднання рівнозначних ознак.'
- section: Підсумок
  words: 300
  points:
  - 'Самоперевірка: Яке закінчення має прикметник чоловічого роду? (-ий/-ій). Жіночого?
    (-а/-я). Середнього? (-е/-є). Опишіть свою кімнату трьома реченнями, використовуючи
    прикметники.'
vocabulary_hints:
  required:
  - який, яка, яке (what kind? — m/f/n)
  - великий (big)
  - маленький (small)
  - новий (new)
  - старий (old)
  - гарний (nice, beautiful)
  - чистий (clean)
  - дорогий (expensive)
  - дешевий (cheap)
  recommended:
  - поганий (bad)
  - брудний (dirty)
  - світлий (light, bright)
  - темний (dark)
  - а (and/but — contrast)
  - але (but)
activity_hints:
- type: fill-in
  focus: 'Додайте правильне закінчення прикметника: нов__ книга, велик__ стіл, чист__
    вікно'
  items: 10
- type: match-up
  focus: 'З''єднайте прикметники-антоніми: великий ↔ маленький'
  items: 6
- type: quiz
  focus: Який/яка/яке? Оберіть правильне питальне слово.
  items: 6
- type: fill-in
  focus: Опишіть кімнату, використовуючи подані іменники та прикметники
  items: 6
- type: fill-in
  focus: Типові адʼєктивні суржикові пари — оберіть нормативну форму (1:1 mirror of
    wiki "Типові помилки L2", усі 9 пар)
  items:
  - Цей суп дуже {смачний|вкусний}.
  - У мене є {жовтий|жолтий} олівець.
  - У сусідки {чорний|черний} кіт.
  - Прапор {червоний|красний}, а не білий.
  - Це {поганий|плохий} фільм.
  - Це {правильна|вірна} відповідь на запитання.
  - Дай мені, будь ласка, {будь-який|любий} олівець.
  - Сергій — {розумний|умний} хлопчик.
  - Тарас — {лінивий|ленивий} учень.
connects_to:
- a1-010 (Кольори)
prerequisites:
- a1-008 (Речі мають рід)
grammar:
- Узгодження прикметника з іменником у називному відмінку (закінчення -ий/-а/-е)
- Питальні слова який/яка/яке/які
- Пари прикметників-антонімів як стратегія розширення словникового запасу
- Сполучник «а» (протиставлення) та «і» (поєднання)
register: розмовний
references:
- title: Пономарова Grade 3, p.98
  notes: 'Правило: Прикметник має такий рід, як іменник, з яким він зв''язаний.'
- title: Вашуленко Grade 3, p.128-131
  notes: Вправи на узгодження прикметників, завдання на опис кімнати.
- title: 'Wiki: pedagogy/a1/what-is-it-like (LOCKED 2026-04-23)'
  notes: Authoritative pedagogical brief — see Step 5 "Межа A1" callout (oblique-case
    scope), the writer-note pinning the three permitted A1 adj formats, and the "Типові
    помилки L2" table (9 verified adjective-specific Surzhyk / calque / paronym pairs).
changelog:
- version: 1.3.0
  date: '2026-04-23'
  changes:
  - 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md (worked
    example: at-the-cafe / PR #1412).'
  - Added Surzhyk-drill fill-in activity mirroring the wiki "Типові помилки L2" table
    1:1 (all 9 wiki pairs as quiz items — closes the wiki-plan drift gap completely).
  - Added new objective for recognising adjective-specific Surzhyk pairs (mirrors
    at-the-cafe pattern of pairing decolonization vocabulary with an explicit objective).
  - Added wiki back-reference to references[] (LOCKED 2026-04-23).
  - Added lifecycle markers (lifecycle / reviewed_at / reviewed_by / review_notes)
    per the rubric convention.


## Existing module artifacts (read-only)

### module.md

# Який він?

In the last module, you learned that every Ukrainian noun has a gender signal:
**стіл** is **він**, **книга** is **вона**, and **вікно** is **воно**. Now you
can use that signal to describe things. The small rule is this: the noun chooses
the adjective ending.

By the end, you can:

- ask **який? / яка? / яке? / які?** with the right kind of noun;
- use hard-ending adjective phrases in the nominative case:
  **великий стіл**, **нова книга**, **чисте вікно**, **гарні речі**;
- describe a room or a book-fair table with short A1 sentences;
- join two qualities with **і**, or contrast them with **а** and **але**;
- repair common adjective traps such as **смачний**, **жовтий**,
  **правильний**, and **розумний**.

Keep the scope small. Today is not a full adjective-declension lesson. You are
training the first visible pattern: noun gender plus adjective ending.

## Діалоги

<!-- INJECT_ACTIVITY: act-1 -->

Start with the question word. English has one easy phrase, "what kind of."
Ukrainian asks it four ways because the noun still matters.

| Ask | Use with | Answer phrase |
| --- | --- | --- |
| **Який?** | **стіл**, **атлас**, **плакат** | **новий стіл** |
| **Яка?** | **книга**, **листівка**, **кімната** | **нова книга** |
| **Яке?** | **фото**, **вікно**, **ліжко** | **нове фото** |
| **Які?** | plural things | **нові книги** |

Read the question and the answer as a pair:

- **Який стіл?** — **Великий стіл.**
- **Яка книга?** — **Цікава книга.**
- **Яке фото?** — **Старе фото.**
- **Які речі?** — **Нові речі.**

At a weekend book fair, Sofia and Taras are looking at a small table:

```text
Софія: Дивись, це нова книга.
Тарас: Яка вона?
Софія: Вона цікава і гарна.
Тарас: А атлас? Який він?
Софія: Він старий, але корисний.
Тарас: А фото? Яке воно?
Софія: Воно маленьке.
```

Support after the Ukrainian lines:

| Українська | English support |
| --- | --- |
| **Софія: Дивись, це нова книга.** | Sofia: Look, this is a new book. |
| **Тарас: Яка вона?** | Taras: What is it like? |
| **Софія: Вона цікава і гарна.** | Sofia: It is interesting and nice. |
| **Тарас: А атлас? Який він?** | Taras: And the atlas? What is it like? |
| **Софія: Він старий, але корисний.** | Sofia: It is old, but useful. |
| **Тарас: А фото? Яке воно?** | Taras: And the photo? What is it like? |
| **Софія: Воно маленьке.** | Sofia: It is small. |

Notice the short answers. You do not need **є** here. Say **Книга цікава**,
not a word-for-word English sentence with "is."

<!-- INJECT_ACTIVITY: act-2 -->

## Який? Яка? Яке?

Use the same gender habit from **мій / моя / моє**. If the noun is masculine,
the adjective usually ends in **-ий**. If the noun is feminine, use **-а**. If
the noun is neuter, use **-е**. For plural A1 phrases, use **-і**.

| Noun signal | Question | Adjective ending | Example |
| --- | --- | --- | --- |
| **він / мій** | **який?** | **-ий** | **великий стіл** |
| **вона / моя** | **яка?** | **-а** | **велика кімната** |
| **воно / моє** | **яке?** | **-е** | **велике вікно** |
| plural | **які?** | **-і** | **великі книги** |

This is the **Називний відмінок**, the naming form. You are describing the noun
as it stands on its own: **стіл новий**, **книга нова**, **вікно нове**.

Colors and soft-looking adjectives come next. If you see **синій** or
**синє** today, treat it as a preview word, not a new pattern to practice. The
productive pattern here is still **-ий / -а / -е / -і**.

For **прикметники в множині**, the first A1 pattern is friendly: masculine,
feminine, and neuter nouns all use **-і** in the plural. Ask **які?** and say
**нові столи**, **нові книги**, **нові фото**. Later you will meet more plural
details; today, just recognize **які?** plus **-і**.

<!-- INJECT_ACTIVITY: act-3 -->

:::tip
When you hesitate, do not start with the English adjective. Start with the
Ukrainian noun: **стіл -> він -> який? -> новий стіл**. The noun gives you
the ending.
:::

## Прикметники

Learn adjectives in pairs. Opposites make the memory hook stronger.

| Pair | Use it for |
| --- | --- |
| **великий / маленький** | size |
| **новий / старий** | age of a thing |
| **гарний / поганий** | general quality |
| **чистий / брудний** | clean or dirty |
| **дорогий / дешевий** | price |
| **світлий / темний** | light or dark |

The three useful A1 formats are:

| Format | Example | Meaning |
| --- | --- | --- |
| question and answer | **Який стіл? — Новий стіл.** | What kind of table? A new table. |
| adjective before noun | **нова книга** | a new book |
| adjective after noun | **Книга нова.** | The book is new. |

For plural, keep one friendly A1 rule: the same ending **-і** works for
masculine, feminine, and neuter nouns. Say **нові столи**, **нові книги**,
**нові фото**. You do not choose gender in plural.

Later lessons will change adjective endings when a noun is an object. Today,
keep the safe nominative phrases: **цікава книга**, **цікавий атлас**,
**цікаве фото**.

Use **і** for two qualities that simply go together:

- **Кімната велика і світла.**
- **Вікно велике і чисте.**
- **Книга нова і цікава.**

Use **а** when you contrast two things:

- **Стіл новий, а стілець старий.**
- **Книга дорога, а листівка дешева.**
- **Вікно чисте, а дзеркало брудне.**

Use **але** when the second idea limits the first:

- **Атлас старий, але корисний.**
- **Кімната маленька, але гарна.**
- **Плакат великий, але дешевий.**

<!-- INJECT_ACTIVITY: act-4 -->

Here is the room pattern:

```text
Марія: Це моя кімната.
Оленка: Яка вона?
Марія: Вона маленька, але світла.
Оленка: А стіл?
Марія: Стіл новий і чистий.
Оленка: А ліжко?
Марія: Ліжко старе, але зручне.
```

Support after the Ukrainian lines:

| Українська | English support |
| --- | --- |
| **Марія: Це моя кімната.** | Mariia: This is my room. |
| **Оленка: Яка вона?** | Olenka: What is it like? |
| **Марія: Вона маленька, але світла.** | Mariia: It is small, but bright. |
| **Оленка: А стіл?** | Olenka: And the table? |
| **Марія: Стіл новий і чистий.** | Mariia: The table is new and clean. |
| **Оленка: А ліжко?** | Olenka: And the bed? |
| **Марія: Ліжко старе, але зручне.** | Mariia: The bed is old, but comfortable. |

Cover the English and answer aloud:

- **Яка кімната?** — **Маленька, але світла.**
- **Який стіл?** — **Новий і чистий.**
- **Яке ліжко?** — **Старе, але зручне.**

### Пильнуй пастки

Adjectives are a common interference zone. Keep Ukrainian on its own terms.
Do not explain endings through another language, and do not trust look-alike
words. Use the clean Ukrainian pair.

| Avoid | Use |
| --- | --- |
| <!-- bad -->вкусний<!-- /bad --> суп | **смачний суп** |
| <!-- bad -->жолтий<!-- /bad --> олівець | **жовтий олівець** |
| <!-- bad -->черний<!-- /bad --> кіт | **чорний кіт** |
| <!-- bad -->красний<!-- /bad --> прапор | **червоний прапор** |
| <!-- bad -->плохий<!-- /bad --> фільм | **поганий фільм** |
| <!-- bad -->вірна<!-- /bad --> відповідь | **правильна відповідь** |
| <!-- bad -->любий<!-- /bad --> олівець | **будь-який олівець** |
| <!-- bad -->умний<!-- /bad --> хлопчик | **розумний хлопчик** |
| <!-- bad -->ленивий<!-- /bad --> учень | **лінивий учень** |

One more sentence-frame trap: present-tense Ukrainian often has no visible
"to be." Use **Він добрий студент**, not **Він є добрий студент**. Use
**Книга нова**, not an English-shaped sentence.

## Підсумок

Оглядово: **якісні: великий, смачний** name qualities, while
**відносні: український, вчорашній** connect a noun to a place, language, or
time. You do not need the theory yet. You only need safe phrases:

- **Добрий день.**
- **смачна кава**
- **українська мова**
- **рідні люди**
- **популярний музикант**
- **активна жінка**
- **талановитий композитор**

Now make your own three-line room description. Keep it short:

```text
Це моя кімната.
Вона маленька, але гарна.
У мене є новий стіл і стара лампа.
```

Support after the Ukrainian lines:

| Українська | English support |
| --- | --- |
| **Це моя кімната.** | This is my room. |
| **Вона маленька, але гарна.** | It is small, but nice. |
| **У мене є новий стіл і стара лампа.** | I have a new table and an old lamp. |

Then change one noun and one adjective:

- **стіл** -> **телефон**: **новий телефон**
- **книга** -> **листівка**: **гарна листівка**
- **вікно** -> **фото**: **старе фото**

A good final check is to cover the ending and ask two questions. First, what
gender is the noun? Second, is the noun one thing or many things? If the noun is
**стіл**, your answer is **який?** and **-ий**. If it is **книга**, your
answer is **яка?** and **-а**. If it is **фото**, your answer is **яке?** and
**-е**. If it is **книги**, your answer is **які?** and **-і**. This small
routine is more useful than memorizing a large table before you can use the
phrases.

Workbook practice will make the pattern automatic: choose the right question
word, finish the adjective ending, match opposites, describe a room, and repair
the adjective traps.


### activities.yaml

---
inline:
  - id: act-1
    type: quiz
    title: Яке питальне слово?
    instruction: Choose the question word that fits the noun.
    items:
      - prompt: стіл
        options:
          - text: Який?
            correct: true
          - text: Яка?
            correct: false
          - text: Яке?
            correct: false
        explanation: Стіл is masculine, so ask Який?
      - prompt: книга
        options:
          - text: Яка?
            correct: true
          - text: Який?
            correct: false
          - text: Яке?
            correct: false
        explanation: Книга is feminine, so ask Яка?
      - prompt: фото
        options:
          - text: Яке?
            correct: true
          - text: Яка?
            correct: false
          - text: Який?
            correct: false
        explanation: Фото is neuter in this lesson, so ask Яке?
      - prompt: кімната
        options:
          - text: Яка?
            correct: true
          - text: Який?
            correct: false
          - text: Які?
            correct: false
        explanation: Кімната is feminine.
      - prompt: книги
        options:
          - text: Які?
            correct: true
          - text: Яке?
            correct: false
          - text: Який?
            correct: false
        explanation: Книги is plural, so ask Які?
      - prompt: вікно
        options:
          - text: Яке?
            correct: true
          - text: Який?
            correct: false
          - text: Яка?
            correct: false
        explanation: Вікно is neuter.
  - id: act-2
    type: fill-in
    title: Заверши прикметник
    instruction: Choose the adjective ending that matches the noun.
    items:
      - sentence: велик__ стіл
        answer: ий
        options:
          - ий
          - а
          - е
        explanation: Стіл is masculine, so use великий.
      - sentence: нов__ книга
        answer: а
        options:
          - а
          - ий
          - е
        explanation: Книга is feminine, so use нова.
      - sentence: чист__ вікно
        answer: е
        options:
          - е
          - ий
          - а
        explanation: Вікно is neuter, so use чисте.
      - sentence: стар__ фото
        answer: е
        options:
          - е
          - а
          - ий
        explanation: Фото is neuter in this lesson.
      - sentence: дорог__ телефон
        answer: ий
        options:
          - ий
          - а
          - е
        explanation: Телефон is masculine.
      - sentence: дешев__ листівка
        answer: а
        options:
          - а
          - е
          - ий
        explanation: Листівка is feminine.
      - sentence: гарн__ кімната
        answer: а
        options:
          - а
          - ий
          - е
        explanation: Кімната is feminine.
      - sentence: брудн__ дзеркало
        answer: е
        options:
          - е
          - а
          - ий
        explanation: Дзеркало is neuter.
      - sentence: світл__ плакат
        answer: ий
        options:
          - ий
          - е
          - а
        explanation: Плакат is masculine.
      - sentence: нов__ книги
        answer: і
        options:
          - і
          - а
          - е
        explanation: Plural A1 phrases use нові.
  - id: act-3
    type: group-sort
    title: Сортуй фрази
    instruction: Sort each adjective-noun phrase by the question it answers.
    groups:
      - label: Який?
        items:
          - великий стіл
          - новий телефон
          - старий атлас
          - дорогий плакат
      - label: Яка?
        items:
          - нова книга
          - гарна листівка
          - чиста кімната
          - дешева ручка
      - label: Яке?
        items:
          - старе фото
          - чисте вікно
          - велике ліжко
          - брудне дзеркало
      - label: Які?
        items:
          - нові книги
          - гарні речі
          - старі фото
          - дешеві листівки
  - id: act-4
    type: match-up
    title: Поєднай протилежності
    instruction: Match each adjective with its opposite.
    pairs:
      - left: великий
        right: маленький
      - left: новий
        right: старий
      - left: гарний
        right: поганий
      - left: чистий
        right: брудний
      - left: дорогий
        right: дешевий
      - left: світлий
        right: темний
workbook:
  - type: quiz
    title: Модель речення
    instruction: Choose the natural A1 sentence.
    items:
      - prompt: The book is new.
        options:
          - text: Книга нова.
            correct: true
          - text: Книга є нова.
            correct: false
          - text: Книга новий.
            correct: false
        explanation: Ukrainian usually leaves out є in this present-tense frame.
      - prompt: The table is clean.
        options:
          - text: Стіл чистий.
            correct: true
          - text: Стіл чиста.
            correct: false
          - text: Стіл є чистий.
            correct: false
        explanation: Стіл is masculine, and the no-є frame is natural.
      - prompt: The window is big.
        options:
          - text: Вікно велике.
            correct: true
          - text: Вікно великий.
            correct: false
          - text: Вікно велика.
            correct: false
        explanation: Вікно is neuter.
      - prompt: A nice postcard
        options:
          - text: гарна листівка
            correct: true
          - text: гарний листівка
            correct: false
          - text: гарне листівка
            correct: false
        explanation: Листівка is feminine.
      - prompt: A useful atlas
        options:
          - text: корисний атлас
            correct: true
          - text: корисна атлас
            correct: false
          - text: корисне атлас
            correct: false
        explanation: Атлас is masculine.
      - prompt: Interesting things
        options:
          - text: цікаві речі
            correct: true
          - text: цікава речі
            correct: false
          - text: цікаве речі
            correct: false
        explanation: Plural phrases use цікаві.
  - type: fill-in
    title: Опиши кімнату
    instruction: Complete the short room lines.
    items:
      - sentence: Моя кімната ___ і світла.
        answer: маленька
        options:
          - маленька
          - маленький
          - маленьке
        explanation: Кімната is feminine.
      - sentence: Стіл ___ і чистий.
        answer: новий
        options:
          - новий
          - нова
          - нове
        explanation: Стіл is masculine.
      - sentence: Ліжко старе, ___ зручне.
        answer: але
        options:
          - але
          - який
          - яка
        explanation: Але adds a contrast.
      - sentence: Вікно ___ і чисте.
        answer: велике
        options:
          - велике
          - великий
          - велика
        explanation: Вікно is neuter.
      - sentence: Книга дорога, ___ листівка дешева.
        answer: а
        options:
          - а
          - і
          - яке
        explanation: А contrasts two things.
      - sentence: У мене є ___ стіл і стара лампа.
        answer: новий
        options:
          - новий
          - нова
          - нове
        explanation: Стіл is masculine.
  - type: error-correction
    title: Виправ узгодження прикметників
    instruction: Fix the adjective or sentence frame.
    items:
      - sentence: Він є добрий студент.
        error: Він є добрий студент.
        answer: Він добрий студент.
        options:
          - Він добрий студент.
          - Він добра студент.
          - Він є добра студент.
        explanation: In this present-tense frame, Ukrainian normally omits є.
      - sentence: Це гарна хлопець.
        error: Це гарна хлопець.
        answer: Це гарний хлопець.
        options:
          - Це гарний хлопець.
          - Це гарне хлопець.
          - Це гарна хлопець.
        explanation: Хлопець is masculine.
      - sentence: Який твоє ім'я?
        error: Який твоє ім'я?
        answer: "Яке твоє ім'я? (або: Як тебе звати?)"
        options:
          - "Яке твоє ім'я? (або: Як тебе звати?)"
          - Яка твоє ім'я?
          - Який твоє ім'я?
        explanation: Ім'я is neuter; in real introductions, use Як тебе звати?
      - sentence: Це цікавий книга.
        error: Це цікавий книга.
        answer: Це цікава книга.
        options:
          - Це цікава книга.
          - Це цікавий книга.
          - Це цікаве книга.
        explanation: Книга is feminine, so use цікава.
      - sentence: Моя кава смачний.
        error: Моя кава смачний.
        answer: Моя кава смачна.
        options:
          - Моя кава смачна.
          - Моя кава смачний.
          - Моя кава смачне.
        explanation: Кава is feminine, so use смачна.
      - sentence: Це мій новий ручка.
        error: Це мій новий ручка.
        answer: Це моя нова ручка.
        options:
          - Це моя нова ручка.
          - Це мій новий ручка.
          - Це моє нове ручка.
        explanation: Ручка is feminine, so use моя and нова.
  - type: fill-in
    title: Виправ прикметникові пастки
    instruction: Choose the standard Ukrainian adjective.
    items:
      - sentence: Цей суп дуже ___.
        answer: смачний
        options:
          - смачний
          - вкусний
        explanation: Use смачний for tasty.
      - sentence: У мене є ___ олівець.
        answer: жовтий
        options:
          - жовтий
          - жолтий
        explanation: Use жовтий.
      - sentence: У сусідки ___ кіт.
        answer: чорний
        options:
          - чорний
          - черний
        explanation: Use чорний.
      - sentence: Прапор ___, а не білий.
        answer: червоний
        options:
          - червоний
          - красний
        explanation: Use червоний for red in ordinary modern Ukrainian.
      - sentence: Це ___ фільм.
        answer: поганий
        options:
          - поганий
          - плохий
        explanation: Use поганий.
      - sentence: Це ___ відповідь на запитання.
        answer: правильна
        options:
          - правильна
          - вірна
        explanation: Use правильна відповідь for a correct answer.
      - sentence: Дай мені, будь ласка, ___ олівець.
        answer: будь-який
        options:
          - будь-який
          - любий
        explanation: Use the standard Ukrainian form for any.
      - sentence: Сергій — ___ хлопчик.
        answer: розумний
        options:
          - розумний
          - умний
        explanation: Use розумний.
      - sentence: Тарас — ___ учень.
        answer: лінивий
        options:
          - лінивий
          - ленивий
        explanation: Use лінивий.
  - type: translate
    title: Обери український рядок
    instruction: Choose the Ukrainian sentence that matches the English cue.
    items:
      - source: My room is small but nice.
        options:
          - text: Моя кімната маленька, але гарна.
            correct: true
          - text: Мій кімната маленький, але гарний.
            correct: false
          - text: Моє кімната маленьке, але гарне.
            correct: false
        explanation: Кімната is feminine.
      - source: The table is new and clean.
        options:
          - text: Стіл новий і чистий.
            correct: true
          - text: Стіл нова і чиста.
            correct: false
          - text: Стіл нове і чисте.
            correct: false
        explanation: Стіл is masculine.
      - source: The photo is old.
        options:
          - text: Фото старе.
            correct: true
          - text: Фото стара.
            correct: false
          - text: Фото старий.
            correct: false
        explanation: Фото is neuter in this lesson.
      - source: A cheap postcard
        options:
          - text: дешева листівка
            correct: true
          - text: дешевий листівка
            correct: false
          - text: дешеве листівка
            correct: false
        explanation: Листівка is feminine.
      - source: Good afternoon.
        options:
          - text: Добрий день.
            correct: true
          - text: Добра день.
            correct: false
          - text: Добре день.
            correct: false
        explanation: День is masculine, so the greeting is Добрий день.
      - source: The books are interesting.
        options:
          - text: Книги цікаві.
            correct: true
          - text: Книги цікава.
            correct: false
          - text: Книги цікаве.
            correct: false
        explanation: Plural phrases use цікаві.
  - type: true-false
    title: Швидка перевірка
    instruction: Decide if the statement is right.
    items:
      - statement: Стіл новий.
        answer: true
        explanation: Стіл is masculine, so новий is correct.
      - statement: Книга нове.
        answer: false
        explanation: Книга is feminine; say Книга нова.
      - statement: Вікно чисте.
        answer: true
        explanation: Вікно is neuter.
      - statement: Який кімната?
        answer: false
        explanation: Кімната is feminine; ask Яка кімната?
      - statement: Кімната маленька, але гарна.
        answer: true
        explanation: Both adjectives agree with кімната.
      - statement: 'В українській можна описати річ без є: Книга цікава.'
        answer: true
        explanation: This no-є present-tense frame is normal.


### vocabulary.yaml

- lemma: який
  translation: what kind, masculine
  pos: pronoun
  usage: Який стіл?
- lemma: яка
  translation: what kind, feminine
  pos: pronoun
  usage: Яка книга?
- lemma: яке
  translation: what kind, neuter
  pos: pronoun
  usage: Яке фото?
- lemma: які
  translation: what kind, plural
  pos: pronoun
  usage: Які речі?
- lemma: великий
  translation: big, masculine
  pos: adj
  usage: Це великий стіл.
- lemma: велика
  translation: big, feminine
  pos: adj
  usage: Це велика кімната.
- lemma: велике
  translation: big, neuter
  pos: adj
  usage: Це велике вікно.
- lemma: маленький
  translation: small, masculine
  pos: adj
  usage: Це маленький плакат.
- lemma: новий
  translation: new, masculine
  pos: adj
  usage: Стіл новий.
- lemma: нова
  translation: new, feminine
  pos: adj
  usage: Книга нова.
- lemma: нове
  translation: new, neuter
  pos: adj
  usage: Фото нове.
- lemma: старий
  translation: old, masculine
  pos: adj
  usage: Атлас старий.
- lemma: стара
  translation: old, feminine
  pos: adj
  usage: Лампа стара.
- lemma: старе
  translation: old, neuter
  pos: adj
  usage: Ліжко старе.
- lemma: гарний
  translation: nice, beautiful, masculine
  pos: adj
  usage: Плакат гарний.
- lemma: гарна
  translation: nice, beautiful, feminine
  pos: adj
  usage: Листівка гарна.
- lemma: гарне
  translation: nice, beautiful, neuter
  pos: adj
  usage: Вікно гарне.
- lemma: поганий
  translation: bad, masculine
  pos: adj
  usage: Це поганий фільм.
- lemma: чистий
  translation: clean, masculine
  pos: adj
  usage: Стіл чистий.
- lemma: чиста
  translation: clean, feminine
  pos: adj
  usage: Кімната чиста.
- lemma: чисте
  translation: clean, neuter
  pos: adj
  usage: Вікно чисте.
- lemma: брудний
  translation: dirty, masculine
  pos: adj
  usage: Дзеркало брудне.
- lemma: дорогий
  translation: expensive, masculine
  pos: adj
  usage: Телефон дорогий.
- lemma: дешевий
  translation: cheap, masculine
  pos: adj
  usage: Плакат дешевий.
- lemma: світлий
  translation: light, bright, masculine
  pos: adj
  usage: Клас світлий.
- lemma: темний
  translation: dark, masculine
  pos: adj
  usage: Коридор темний.
- lemma: цікавий
  translation: interesting, masculine
  pos: adj
  usage: Це цікавий атлас.
- lemma: цікава
  translation: interesting, feminine
  pos: adj
  usage: Це цікава книга.
- lemma: цікаве
  translation: interesting, neuter
  pos: adj
  usage: Це цікаве фото.
- lemma: смачний
  translation: tasty, masculine
  pos: adj
  usage: Це смачний суп.
- lemma: правильний
  translation: correct, masculine
  pos: adj
  usage: Це правильний приклад.
- lemma: розумний
  translation: smart, masculine
  pos: adj
  usage: Сергій розумний.
- lemma: лінивий
  translation: lazy, masculine
  pos: adj
  usage: Учень лінивий.
- lemma: а
  translation: and / but for contrast
  pos: conj
  usage: Стіл новий, а стілець старий.
- lemma: але
  translation: but
  pos: conj
  usage: Кімната маленька, але гарна.
- lemma: і
  translation: and
  pos: conj
  usage: Книга нова і цікава.
- lemma: атлас
  translation: atlas
  pos: noun
  usage: Атлас старий.
- lemma: листівка
  translation: postcard
  pos: noun
  usage: Листівка дешева.
- lemma: плакат
  translation: poster
  pos: noun
  usage: Плакат великий.


### resources.yaml

- title: "Типові прикметники — Common Ukrainian Adjectives"
  role: article
  source_ref: "Типові прикметники — Common Ukrainian Adjectives (Useful Table and Audio)"
  url: https://www.ukrainianlessons.com/vocabulary-adjectives/
  notes: "Learner-safe adjective list with audio; use it for extra repetition of common descriptive words."
- title: "Прикметники і прислівники — Adjectives and Adverbs in Ukrainian"
  role: article
  source_ref: "Прикметники і прислівники — Adjectives and Adverbs in Ukrainian (with Illustrations and Audio)"
  url: https://www.ukrainianlessons.com/adjectives-and-adverbs/
  notes: "Ukrainian Lessons overview of adjective agreement and adverb contrast."
- title: "Introduction to Ukrainian ADJECTIVES — прикметники"
  role: video
  source_ref: "Introduction to Ukrainian ADJECTIVES - прикметники [Ukrainian Grammar Guide]"
  url: https://www.ukrainianlessons.com/video-adjectives/
  notes: "Anna Ohoiko video page for a visual introduction to Ukrainian adjectives."
- title: "Adjectives & Adverbs Chart"
  role: article
  source_ref: "Adjectives & Adverbs Chart"
  url: https://www.ukrainianlessons.com/adjectives-adverbs-chart/
  notes: "Reference chart for learners who want a compact follow-up after the lesson."
- title: "Dobra Forma: Adjectives (Gender and Number in Nominative)"
  role: article
  source_ref: "16.1 Adjectives (Gender and Number in Nominative) – Добра форма"
  url: https://opentext.ku.edu/dobraforma/chapter/16-1/
  notes: "Open textbook exercises for nominative adjective agreement."


## Response format

Return exactly four named fenced blocks, with no other commentary:
```markdown file=module.md
(the current lesson's complete preserved-and-expanded prose)
```
```json file=activities.yaml
{"inline": [], "workbook": []}
```
```json file=vocabulary.yaml
[]
```
```json file=resources.yaml
[]
```
The arrays above describe the syntax; empty artifacts fail the gates. Structured artifacts
must be strict JSON inside the fences; V7 writes them as YAML. Do not return lessons.yaml.
