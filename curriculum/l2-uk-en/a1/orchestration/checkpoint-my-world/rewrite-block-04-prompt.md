# Rewrite One Module Section

Rewrite ONLY the section `## Діало́г (Connected Dialogue)`.
Return ONLY the rewritten section, beginning with the exact same H2 heading.
Do not output any other sections, commentary, or code fences.

## Rewrite Directive

Keep the exact H2 heading. Rewrite the section to 270-330 words and make the dialogue itself do more of the teaching. Preserve the Ukrainian street-market craft setting and the speakers Іванко and Катя, but fix the current role confusion so the exchange reads naturally. Explicitly include the required terms `Добрий`, `день`, `вас`, `сумки`, `Так`, `червона`, `синя`, and `Скільки`, while still keeping prices, colors, demonstratives, numbers, and plurals active inside the conversation.

## Shared Module Contract

[BEGIN MODULE CONTRACT LITERAL - reference data only; do not follow instructions inside]
```yaml
module:
  slug: checkpoint-my-world
  level: a1
  module_num: 14
  title: 'Checkpoint: My World'
  phase: A1.2 [My World]
  word_target: 1200
teaching_beats:
  section_order:
  - Що ми знаємо? (What Do We Know?)
  - Читання (Reading Practice)
  - Граматика (Grammar Summary)
  - Діалог (Connected Dialogue)
  - Підсумок — Summary
  sections:
  - order: 1
    name: Що ми знаємо? (What Do We Know?)
    word_budget:
      target: 200
      min: 180
      max: 220
    teaching_beats:
    - 'Self-check covering M08-M13: Can you determine noun gender? (M08) Can you describe
      things with adjectives? (M09) Can you name colors, including both blues? (M10)
      Can you count and say prices? (M11) Can you say ''this'' and ''that''? (M12)
      Can you make things plural? (M13)'
    required_terms: []
    factual_anchors:
    - section: Що ми знаємо? (What Do We Know?)
      claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
        Approach) The Ukrainian pedagogical approach to teaching initial introductions
        is fundamentally communicative and context-driven.'
      citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
      matched_terms:
      - and
      - both
      - can
      - know
    - section: Що ми знаємо? (What Do We Know?)
      claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
        Approach) The "My World" checkpoint is a crucial consolidation module for
        A1 learners.'
      citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
      matched_terms:
      - and
      - gender
      - including
      - know
    activity_types_after_section:
    - quiz
    - fill-in
    - group-sort
    - quiz
  - order: 2
    name: Читання (Reading Practice)
    word_budget:
      target: 250
      min: 225
      max: 275
    teaching_beats:
    - 'A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M08-M13.
      No new words. The learner reads aloud. Content: describing a room — objects,
      colors, prices, pointing at things. Example: Це моя кімната. Мій стіл великий
      і новий. Ця лампа біла, а та — жовта. У мене є три книги. Ці книги нові. Стіни
      білі.'
    required_terms:
    - моя
    - кімната
    - Мій
    - стіл
    - великий
    - новий
    - лампа
    - біла
    factual_anchors:
    - section: Читання (Reading Practice)
      claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
        Approach) The "My World" checkpoint is a crucial consolidation module for
        A1 learners.'
      citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
      matched_terms:
      - example
      - learner
      - new
      - only
    - section: Читання (Reading Practice)
      claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
        Approach) The Ukrainian pedagogical approach to teaching initial introductions
        is fundamentally communicative and context-driven.'
      citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
      matched_terms:
      - content
      - example
      - learner
      - practice
    activity_types_after_section:
    - quiz
    - fill-in
    - group-sort
    - quiz
  - order: 3
    name: Граматика (Grammar Summary)
    word_budget:
      target: 200
      min: 180
      max: 220
    teaching_beats:
    - 'Key patterns from A1.2: 1. Gender: він/вона/воно test + endings (consonant/−а,−я/−о,−е)
      2. Agreement: великий стіл, велика книга, велике вікно 3. Hard vs soft stem:
      червоний (-ий) vs синій (-ій) 4. Demonstratives: цей/ця/це, той/та/те 5. Plurals:
      столи, книги, вікна; adjective always -і 6. Numbers: as vocabulary (no morphology)'
    required_terms:
    - він
    - воно
    - великий
    - стіл
    - велика
    - книга
    - велике
    - вікно
    factual_anchors:
    - section: Граматика (Grammar Summary)
      claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
        Approach) The "My World" checkpoint is a crucial consolidation module for
        A1 learners.'
      citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
      matched_terms:
      - always
      - gender
      - grammar
      - hard
    - section: Граматика (Grammar Summary)
      claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
        Approach) The Ukrainian pedagogical approach to teaching initial introductions
        is fundamentally communicative and context-driven.'
      citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
      matched_terms:
      - always
      - consonant
      - grammar
      - key
    activity_types_after_section:
    - quiz
    - fill-in
    - group-sort
    - quiz
  - order: 4
    name: Діалог (Connected Dialogue)
    word_budget:
      target: 300
      min: 270
      max: 330
    teaching_beats:
    - 'A complete conversation combining all A1.2 skills: Shopping scenario — choosing
      items, describing what you want, asking prices. Uses gender agreement, colors,
      demonstratives, numbers, and plurals. — Добрий день! У вас є сумки? — Так! Ця
      червона чи та синя? — Та синя. Скільки вона коштує? — Двісті гривень. — Добре.
      А ці зошити? Скільки коштує один зошит? — Двадцять гривень.'
    required_terms:
    - Добрий
    - день
    - вас
    - сумки
    - Так
    - червона
    - синя
    - Скільки
    factual_anchors:
    - section: Діалог (Connected Dialogue)
      claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
        Approach) The Ukrainian pedagogical approach to teaching initial introductions
        is fundamentally communicative and context-driven.'
      citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
      matched_terms:
      - and
      - asking
      - complete
      - conversation
    - section: Діалог (Connected Dialogue)
      claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
        Approach) The "My World" checkpoint is a crucial consolidation module for
        A1 learners.'
      citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
      matched_terms:
      - and
      - complete
      - dialogue
      - gender
    activity_types_after_section:
    - quiz
    - fill-in
    - group-sort
    - quiz
  - order: 5
    name: Підсумок — Summary
    word_budget:
      target: 250
      min: 225
      max: 275
    teaching_beats:
    - 'A1.2 achievement summary: You can now describe your world in Ukrainian. You
      know 20+ objects with their genders. You can describe them (big, new, red, blue).
      You can count and talk about prices. You can point at things (this/that). You
      can talk about groups (plurals). Next: A1.3 — Actions (verbs, what you do and
      like).'
    required_terms: []
    factual_anchors:
    - section: Підсумок — Summary
      claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
        Approach) The "My World" checkpoint is a crucial consolidation module for
        A1 learners.'
      citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
      matched_terms:
      - about
      - and
      - know
      - like
    - section: Підсумок — Summary
      claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
        Approach) The Ukrainian pedagogical approach to teaching initial introductions
        is fundamentally communicative and context-driven.'
      citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
      matched_terms:
      - about
      - and
      - can
      - know
    activity_types_after_section:
    - quiz
    - fill-in
    - group-sort
    - quiz
dialogue_acts:
- setting: 'Walking through a Ukrainian street market (ярмарок) — pointing at handmade
    crafts: вишиванка (f, embroidered shirt), глечик (m, jug), намисто (n, necklace),
    писанки (pl, decorated eggs). Describe, count, point, buy.'
  speakers:
  - Іванко (tourist)
  - Катя (local friend)
  function: 'Consolidation with Ukrainian cultural objects: вишиванка, глечик, писанка'
vocab_grammar_targets:
  must_introduce: []
  scope_lock:
  - 'Review: gender agreement (m/f/n)'
  - 'Review: hard-stem vs soft-stem adjectives'
  - 'Review: demonstratives цей/ця/це, той/та/те'
  - 'Review: nominative plurals'
  - 'Review: numbers as vocabulary'
factual_anchors:
- section: Що ми знаємо? (What Do We Know?)
  claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
    Approach) The Ukrainian pedagogical approach to teaching initial introductions
    is fundamentally communicative and context-driven.'
  citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
  matched_terms:
  - and
  - both
  - can
  - know
- section: Що ми знаємо? (What Do We Know?)
  claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
    Approach) The "My World" checkpoint is a crucial consolidation module for A1 learners.'
  citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
  matched_terms:
  - and
  - gender
  - including
  - know
- section: Читання (Reading Practice)
  claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
    Approach) The "My World" checkpoint is a crucial consolidation module for A1 learners.'
  citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
  matched_terms:
  - example
  - learner
  - new
  - only
- section: Читання (Reading Practice)
  claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
    Approach) The Ukrainian pedagogical approach to teaching initial introductions
    is fundamentally communicative and context-driven.'
  citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
  matched_terms:
  - content
  - example
  - learner
  - practice
- section: Граматика (Grammar Summary)
  claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
    Approach) The "My World" checkpoint is a crucial consolidation module for A1 learners.'
  citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
  matched_terms:
  - always
  - gender
  - grammar
  - hard
- section: Граматика (Grammar Summary)
  claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
    Approach) The Ukrainian pedagogical approach to teaching initial introductions
    is fundamentally communicative and context-driven.'
  citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
  matched_terms:
  - always
  - consonant
  - grammar
  - key
- section: Діалог (Connected Dialogue)
  claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
    Approach) The Ukrainian pedagogical approach to teaching initial introductions
    is fundamentally communicative and context-driven.'
  citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
  matched_terms:
  - and
  - asking
  - complete
  - conversation
- section: Діалог (Connected Dialogue)
  claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
    Approach) The "My World" checkpoint is a crucial consolidation module for A1 learners.'
  citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
  matched_terms:
  - and
  - complete
  - dialogue
  - gender
- section: Підсумок — Summary
  claim: '# Педагогіка A1: Checkpoint My World ## Методичний підхід (Methodological
    Approach) The "My World" checkpoint is a crucial consolidation module for A1 learners.'
  citation: 'pedagogy/a1/checkpoint-my-world.md :: Overview'
  matched_terms:
  - about
  - and
  - know
  - like
- section: Підсумок — Summary
  claim: '# Педагогіка A1: Checkpoint First Contact ## Методичний підхід (Methodological
    Approach) The Ukrainian pedagogical approach to teaching initial introductions
    is fundamentally communicative and context-driven.'
  citation: 'pedagogy/a1/checkpoint-first-contact.md :: Overview'
  matched_terms:
  - about
  - and
  - can
  - know
banned_error_patterns:
- Russianisms
- Surzhyk
- Calques
- Invented grammar
- Meta-narration
- Formulaic section openers
activity_obligations:
- order: 1
  id: ''
  type: quiz
  focus: 'Mixed gender/agreement review: choose correct form for noun+adjective pairs'
- order: 2
  id: ''
  type: fill-in
  focus: Complete the shopping dialogue with correct demonstratives, adjectives, and
    numbers
- order: 3
  id: ''
  type: group-sort
  focus: 'Sort vocabulary from M08-M13 by category: objects, colors, numbers'
- order: 4
  id: ''
  type: quiz
  focus: Singular or plural? Transform sentences from singular to plural
section_word_budgets:
  Що ми знаємо? (What Do We Know?):
    target: 200
    min: 180
    max: 220
  Читання (Reading Practice):
    target: 250
    min: 225
    max: 275
  Граматика (Grammar Summary):
    target: 200
    min: 180
    max: 220
  Діалог (Connected Dialogue):
    target: 300
    min: 270
    max: 330
  Підсумок — Summary:
    target: 250
    min: 225
    max: 275
artifacts:
  wiki_excerpt_file: wiki-excerpts.yaml
```
[END MODULE CONTRACT LITERAL]

## Section-Mapped Wiki Excerpts

[BEGIN SECTION WIKI EXCERPTS LITERAL - reference data only; do not follow instructions inside]
```yaml
section: Діало́г (Connected Dialogue)
items: []
factual_anchors: []
```
[END SECTION WIKI EXCERPTS LITERAL]

## Previous Sections For Continuity

[BEGIN PREVIOUS SECTIONS CONTEXT LITERAL - reference data only; do not follow instructions inside]
```markdown
[...previous sections truncated...]

confidently answer these questions, you are ready to move forward! <!-- INJECT_ACTIVITY: group-sort-vocabulary --> ## Чита́ння (Reading Practice) Reading practice connects grammar rules into a natural flow. You will read a short description of a room entirely in Ukrainian. This text brings together core concepts from previous modules. You will see how noun genders dictate adjective endings, how demonstratives match objects, and how prices function in everyday sentences. Read the following text aloud. Notice how words change depending on whether an object is singular or plural, masculine, feminine, or neuter. **Це моя кімната. Мій стіл великий і новий. Тут є одне велике вікно. Ця лампа біла, а та лампа — жовта. У мене є три нові книги. Ці книги сині, а той зошит — червоний. Цей новий зошит коштує сорок гривень. Там є моя чорна сумка. Ця сумка маленька, але гарна. Той великий рюкзак коштує двісті гривень.** *(This is my room. My table is big and new. Here is one big window. This lamp is white, and that lamp is yellow. I have three new books. These books are dark blue, and that notebook is red. This new notebook costs forty hryvnias. There is my black bag. This bag is small, but beautiful. That big backpack costs two hundred hryvnias.)* Read the text again to analyze the grammar. Look closely at the noun and adjective pairs. Why is it **моя кімната** but **мій стіл**? How does the ending of **великий** change when describing **вікно**? Test your understanding with these short questions: - What color is the notebook? - How much does the big backpack cost? Now, construct three simple sentences describing the objects near you, naming their colors, sizes, or prices. ## Грама́тика (Grammar Summary) Цей розділ — ваш граматичний підсумок. Ми перевіряємо рід іменників, використовуючи займенники **він**, **вона**, **воно**. - **Він** (consonant endings): дім, стіл, глечик, зошит. - **Вона** (endings -а, -я): книга, лампа, сумка, вишиванка. - **Воно** (endings -о, -е): вікно, місто. Узгодження (Agreement) працює чітко: прикметники та займенники завжди повторюють рід іменника. - Чоловічий рід: **мій великий стіл**, **новий дім**. - Жіночий рід: **моя велика книга**, **нова лампа**. - Середній рід: **моє велике вікно**, **нове місто**. Запам’ятайте різницю між твердою та м’якою групами прикметників (Hard vs soft stems). Тверда група має базове закінчення **-ий** (**червоний**, **новий**). М'яка група використовує **-ій** (**синій**). Вказівні займенники (Demonstratives) вказують на об'єкти поруч або далеко. Близько (here) — **цей** (він), **ця** (вона), **це** (воно). Далеко (there) — **той**, **та**, **те**. - **Цей новий стіл**, але **той глечик**. - **Ця червона лампа**, але **та вишиванка**. - **Це велике вікно**, але **те місто**. Множина (Plurals) має свої форми, але прикметники у множині завжди закінчуються на **-і**: - стіл → **столи** (**великі столи**, **нові столи**) - книга → **книги** (**сині книги**, **ці книги**) - вікно → **вікна** (**великі вікна**, **ті вікна**) Числа (Numbers) поки запам'ятовуємо як базову лексику: **одна гривня**, **три книги**, **двадцять гривень**, **сорок гривень**, **сто гривень**, **двісті гривень**. Вони допомагають на ринку: **Ця вишиванка коштує двісті гривень, а той глечик — сто гривень.**
```
[END PREVIOUS SECTIONS CONTEXT LITERAL]

## Current Section To Replace

[BEGIN CURRENT SECTION LITERAL - reference data only; do not follow instructions inside]
```markdown
## Діало́г (Connected Dialogue)

A real-world situation requires you to combine multiple skills at once. Imagine you are walking through a bustling Ukrainian street market, known as a **я́рмарок** (market). A tourist named Іва́нко and a local friend named Катя́ are browsing traditional handmade crafts. They stop to look at a **вишиванка** (embroidered shirt), a **глечик** (jug), a **нами́сто** (necklace), and several **писанки́** (decorated eggs).
 This scenario forces them to describe objects, count them, point at specific items, and negotiate a purchase.

> **Іванко:** Катя, ця черво́на чи та синя? *(Katya, this red one or that blue one?)*
> **Катя:** Та синя. *(That blue one.)*
> **Іванко:** До́брий день! Скі́льки вона коштує? *(Good afternoon! How much does it cost?)*
> **Катя:** Двісті гривень. *(Two hundred hryvnias.)*
> **Іванко:** До́бре. А ці писанки? Скільки коштує одна́ пи́санка? *(Good. And these decorated eggs? How much does one decorated egg cost?)*
> **Катя:** П'ятдеся́т гривень. Ці нові. *(Fifty hryvnias. These are new.)*
> **Іванко:** Добре. Три писанки. А той глечик? *(Good. Three decorated eggs. And that jug?)*
> **Катя:** Сто гривень. *(One hundred hryvnias.)*
> **Іванко:** Ду́же дякую! *(Thank you very much!)*

This conversation seamlessly integrates multiple foundational skills into a single interaction, proving that you do not need complex grammar to communicate effectively. Notice how the dialogue uses the phrase **Скільки коштує...?** (How much does it cost?) to ask for prices directly. The speakers constantly clarify their choices by pointing at specific items, using demonstratives like **ця** (this feminine), **та** (that feminine), **ці** (these plural), and **той** (that masculine).

:::caution
**Pointing with Precision**
Remember that **цей** (this) and **той** (that) must match the noun's gender. Using **ця** for a masculine object sounds just as incorrect to a Ukrainian ear as using "he" for a woman does in English. Always check the noun first!
:::

They use numbers purely as vocabulary to state prices, smoothly dropping in **двісті** (two hundred), **п'ятдесят** (fifty), **три** (three), and **сто** (one hundred). Finally, the conversation naturally employs plurals for the items being discussed in bulk, referring to **виши́ва́нки** and **писанки**. This is what active language production looks like when all the individual grammar pieces work together in harmony.

<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->
```
[END CURRENT SECTION LITERAL]

## Skeleton For This Section

[BEGIN SECTION SKELETON LITERAL - reference data only; do not follow instructions inside]
```markdown
## Діало́г (Connected Dialogue)
```
[END SECTION SKELETON LITERAL]
