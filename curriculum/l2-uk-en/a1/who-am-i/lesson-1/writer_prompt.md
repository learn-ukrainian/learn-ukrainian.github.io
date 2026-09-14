# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: who-am-i.
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
the whole module must reach at least 2000 prose tokens. The final lesson closes the module. On that lesson, end with a bilingual heading
`### Підсумок модуля — Module summary` and 4–7 bilingual bullets of what the
learner can now do (module 9 shape). Do **not** title it `Завершення модуля` /
`Module completion`, and do **not** put that close in a support table.

Follow docs/best-practices/ulp-presentation-pattern.md and the v4 lesson contract.
Use a direct, friendly teaching voice with NO named narrator and NO self-introduction.
Named people occur only inside dialogues. Do not adopt any reference author's persona
or lesson structure. A quotation must be visibly marked, attributed, and have a matching
entry in resources.yaml (Ресурси). Preserve source provenance.
Ukrainian comes first, with English scaffolding appropriate to the supplied learner state
and to **this module's original A1 mix** (do not clone module 9's adjectives lesson;
clone only its close/summary *shape*). Added Ukrainian passages of three or more
sentences require side-by-side English support. Write dialogues as > blockquotes,
never as code fences; put the English breakdown after.

**Why you must call `sources` / VESUM — not as a ritual, as the reason this page is better Ukrainian.**
A fluent model still mixes Russian calques, wrong gender, wrong government, and invented
example sentences. VESUM is the dictionary of record for lemma, gender, aspect, and
rections. Looking it up is what makes the line teachable. This run is also a **test of
the sources tools**: we will check your tool trace. If you never call them, we cannot
tell they work, and this corpus is the dataset for a Ukrainian LLM — guessed forms
become the next model's errors. If a lookup misses, mark `<!-- VERIFY: … -->` and do
not invent. Stress marks still come from the pipeline annotator after review; do not
invent stressed spellings.

A1 landing overview (lesson 1 only): if the original module opening (text before the first `##`) has no "By the end, you can" after tables/tips/code fences are ignored, also return:

```markdown file=landing-overview.md
```

Shape = module 9, not a clone: (1) 1–2 short English-carrier paragraphs with bold Ukrainian targets, (2) "By the end, you can:" 4–7 communicative bullets, (3) one "keep the scope small" sentence. Vary the hook. No `:::tip`, no markdown tables, no `Привіт!` narrator. If the cleaned original already has "By the end, you can", do **not** write this file.

A2+ upgrade: full Ukrainian immersion. Do not write English-carrier landings or landing-overview.md.

## Activities and vocabulary

Keep every original activity's type, items, answer flags and groups structurally intact.
Use provenance to find its assigned lesson. Inline IDs stay unchanged; id-less workbook
originals use act-w1, act-w2, etc. Add distinct activities with globally unique IDs.
A lesson with no activities is a defect (boring theory). After a 2–5 lesson split the
originals will not fill every lesson — **generate new unique activities** until this
lesson has 4–6 inline and 6–9 workbook (≥10 total). Closing/summary lessons still need
practice, not recap-only. >=6 items each unless the deterministic map declares an
original-item exemption. Do not create exemptions.
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
  title: Мене звати...
  sections:
  - Діалоги
  - Мене звати...
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
  title: Я — студент
  sections:
  - Це...
  - Особові займeнники
  - Я — студент
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
  title: Слухай і записуй
  sections:
  - Звідки?
  - Слухай і записуй
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
- n: 4
  title: Самоперевірка
  sections:
  - Самоперевірка
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
closes_module: 4
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
  lesson: 2
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
  lesson: 2
- placement: workbook
  index: 2
  new_id: act-w3
  lesson: 2
- placement: workbook
  index: 3
  new_id: act-w4
  lesson: 3
- placement: workbook
  index: 4
  new_id: act-w5
  lesson: 4
- placement: workbook
  index: 5
  new_id: act-w6
  lesson: 4
items_min_exempt:
- id: act-1
  reason: 4-item original activity preserved from baseline
- id: act-2
  reason: 5-item original activity preserved from baseline
- id: act-3
  reason: 5-item original activity preserved from baseline
- id: act-4
  reason: 4-item original activity preserved from baseline
proper_names: []


## Original plan (read-only)

module: a1-005
level: A1
sequence: 5
slug: who-am-i
version: 1.2.1
lifecycle: locked
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-who-am-i
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md
  (rubric template from PR #1412, at-the-cafe). See PR body for the full plan-side
  findings (pragmatic / Russianism / calque / contradiction / references / wiki-alignment)
  and wiki/.reviews/pedagogy/a1/who-am-i-review-LOCKED.md for the wiki-side report.
  Plan brought into alignment with the locked wiki: echo-question pattern (А тебе?
  / А вас?) reinforced without `А у тебе?` (#1392 Defect 2 avoidance); Dialogue 3
  split into an explicit two-speaker exchange; Surzhyk drill added as fill-in activity
  (mirrors wiki "Типові помилки L2" table); feminitives called out as primary form
  for female speakers; wiki back-reference added.'
title: Хто я?
subtitle: Мене звати... — ваша перша справжня розмова
focus: vocabulary
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
word_target: 1200
objectives:
- Вміти представити себе, назвавши своє ім'я, національність і професію
- Використовувати конструкцію з часткою «це» для ідентифікації предметів і людей
- Вміти ставити запитання «Як тебе/вас звати?» та відповідати на нього формально і
  неформально
- Розуміти структуру українського речення без дієслова-зв'язки «бути» (Я — студент)
- Переадресовувати питання співрозмовникові еховим патерном `А тебе?` / `А вас?` (БЕЗ
  форми `А у тебе?`, яка викликає граматику родового відмінка з прийменником)
- 'Вибирати безпечні A1-формули для знайомства та родини: «тато» як початковий нейтральний
  варіант для активного вжитку; «дружина», «лікар/лікарка», «вибачте», «дякую/спасибі»,
  «теж/також» як нормативні відповіді на типові суржикові або російські форми без
  твердження, що кожна інша засвідчена родинна форма є неукраїнською.'
dialogue_situations:
- setting: Кімната відпочинку в хостелі — два туристи з рюкзаками вперше зустрічаються
  speakers:
  - Марко
  - Олена
  motivation: Мене звати, Звідки ти? — контекст реального першого знайомства
- setting: Орієнтаційний день в університеті — студенти представляються групі
  speakers:
  - Тарас
  - Софія
  motivation: Формальний та неформальний регістри, назви професій із конструкцією
    Я — студент
content_outline:
- section: Діалоги
  words: 350
  points:
  - 'Діалог 1 — У хостелі (неформальний): — Привіт! Як тебе звати? — Мене звати Марко.
    А тебе? — Мене звати Олена. Звідки ти? — Я з Канади. А ти? — Я з України. — Дуже
    приємно!'
  - 'Діалог 2 — На конференції (формальний): — Добрий день! Як вас звати? — Мене звати
    Петро. Дуже приємно! — Мені також! Ви з України? — Так, я з Києва.'
  - 'Діалог 3 — Представлення когось іншого (обов''язково ДВА СПІВРОЗМОВНИКИ, не монолог).
    — Це Андрій. Він зі Львова. — Дуже приємно. А це хто? — А це Оксана. Вона з Одеси.
    Вона — лікарка. Завдання автора: чергувати репліки між двома мовцями; питання
    `А це хто?` переводить фокус на другу особу. УВАГА: для жінки обов''язково використовуйте
    фемінітив (`лікарка`, не `лікар`).'
- section: Мене звати...
  words: 250
  points:
  - 'Конструкція «Мене звати...» є безособовою. В українській мові для представлення
    себе дієслово-зв''язка «є» не потрібне. Питання: Як тебе звати? (неформально)
    / Як вас звати? (формально). Про інших: Як його звати? / Як її звати?.'
  - 'Приємно познайомитись: Дуже приємно! або Приємно познайомитись! Ця фраза звучить
    ПІСЛЯ обміну іменами.'
  - 'Еховий патерн «відлуння» (обов''язковий у Діалозі 1 і 2): після того, як А назвала
    ім''я, Б відповідає `А тебе?` (неформально) або `А вас?` (формально). НЕ використовувати
    форму `А у тебе?` — вона тягне за собою родовий відмінок з прийменником `у`, який
    на А1 ще не вивчається (див. wiki «Крок 1»; уникнення патерну #1392 Defect 2).'
- section: Це...
  words: 200
  points:
  - 'Займенник «це» використовується для вказівки на щось або когось. Дієслово-зв''язка
    «є» тут також не потрібне. Це кава. Це Київ. Це Андрій. Питання: Що це? Хто це?
    Питальні слова завжди стоять НА ПОЧАТКУ речення: Хто це? (не *Це хто?).'
- section: Особові займенники
  words: 100
  points:
  - 'Базові особові займенники: я, ти (неформально), він, вона, ми, ви (формально/множина),
    вони. Зверніть увагу: «ви» використовується як для ввічливого звертання до однієї
    особи, так і для звертання до кількох осіб (на письмі при ввічливому звертанні
    часто пишеться з великої літери — Ви). Ці займенники знадобляться для побудови
    будь-якого речення.'
- section: Я — студент
  words: 150
  points:
  - 'У теперішньому часі дієслово-зв''язка «є» пропускається. Підмет — Іменник: Я
    — студент. Він — лікар. Вона — вчителька. Тире (—) позначає місце, де в інших
    мовах стояло б дієслово «бути».'
  - 'Національності (називний відмінок, без дієслова): українець / українка, американець
    / американка, канадієць / канадка. Професії: студент/студентка, вчитель/вчителька,
    лікар/лікарка, програміст/програмістка, інженер/інженерка, авторка. УВАГА до автора:
    для жінки ПОДАВАТИ ФЕМІНІТИВ як основну форму (`Оксана — лікарка`, не `Оксана
    — лікар`). Російська мова фемінітивів системно не має; українська — має. Усі перелічені
    жіночі форми перевірено у VESUM. Див. wiki «Крок 6» + «Деколонізаційні застереження»
    пункт 5.'
- section: Звідки?
  words: 200
  points:
  - 'Звідки ти? / Звідки ви? Я з України. Я з Канади. Я зі Штатів. Я з Німеччини.
    Зверніть увагу: у конструкції «з/зі + країна» використовуються форми родового
    відмінка (України, Канади), але ми подаємо їх як ЗАВЧЕНІ ФРАЗИ, оскільки граматика
    родового відмінка вивчається на рівні А2. На цьому етапі НЕ вводьте питання «Де
    ви живете?» — використання місцевого відмінка та дієвідмінювання вивчатимуться
    пізніше (дієслова в М16, місцевий відмінок у М29).'
- section: Підсумок
  words: 100
  points:
  - 'Мікроперевірка без нового граматичного аналізу: привітайтеся, назвіть ім''я,
    запитайте ім''я співрозмовника, скажіть звідки ви, назвіть професію або роль і
    поверніть питання через `А тебе?` / `А вас?`. Завершіть коротким `Дуже приємно`.'
vocabulary_hints:
  required:
  - я (I)
  - ти (you, informal)
  - він (he)
  - вона (she)
  - ви (you, formal/plural)
  - мене звати (my name is)
  - як тебе звати? (what's your name, informal)
  - як вас звати? (what's your name, formal)
  - це (this is / these are)
  - дуже приємно (pleased to meet you)
  - студент, студентка (student m/f)
  - вчитель, вчителька (teacher m/f)
  - лікар, лікарка (doctor m/f)
  - українець, українка (Ukrainian m/f)
  - Україна (Ukraine)
  recommended:
  - ми (we)
  - вони (they)
  - програміст, програмістка (programmer m/f)
  - інженер, інженерка (engineer m/f)
  - авторка (author — feminitive)
  - звідки (where from)
  - друг, подруга (friend m/f)
  - його (his — doesn't change)
  - її (her — doesn't change)
  - Канада (Canada)
  - Німеччина (Germany)
  - тато (dad — beginner default; do not teach other attested family forms as nonexistent
    Ukrainian)
  - дружина (wife — native form, NOT `жена`)
  - дякую / спасибі (thank you — native forms, NOT `спасібо`)
  - вибачте / пробачте (excuse me — native forms, NOT `ізвиніть`)
  - теж / також (also — native forms, NOT `тоже`)
  - А тебе? / А вас? (echo-reciprocal — chunk, NOT `А у тебе?`)
activity_hints:
- type: fill-in
  focus: 'Доповніть розповідь про себе: Мене звати..., Я з..., Я —...'
  items: 6
- type: quiz
  focus: Формально чи неформально? Оберіть правильний варіант представлення.
  items: 6
- type: match-up
  focus: З'єднайте назви професій у чоловічому та жіночому роді
  items: 8
- type: fill-in
  focus: Доповніть діалог правильними фразами
  items: 6
- type: fill-in
  focus: 'Типові суржикові пари теми «знайомство» — оберіть безпечну нормативну форму
    для A1. Не включайте `папа/тато` як пару помилка/виправлення: `тато` є початковим
    нейтральним варіантом, але `папа` не слід подавати як неукраїнське слово.'
  items:
  - Це моя {жена|дружина} Марія.
  - '{Ізвиніть|Вибачте}, як вас звати?'
  - '{Спасібо|Дякую}, дуже приємно!'
  - Мені {тоже|теж} приємно.
  - Оксана — {інженер|інженерка}.
  - Це мій {врач|лікар}.
connects_to:
- a1-006 (Моя родина)
prerequisites:
- a1-004 (Наголос та мелодика)
grammar:
- 'Особові займенники: я, ти, він, вона, ми, ви, вони (лише називний відмінок)'
- Конструкція «Мене звати» (безособова)
- Вказівна частка «це» + іменник
- Нульова зв'язка (Я — студент, пропуск дієслова «є»)
- Лексика на позначення національностей та професій (називний відмінок) із системним
  вибором фемінітива для жінки (лікарка, вчителька, інженерка, програмістка)
- Конструкція «Звідки?» + назва країни як стала фраза (БЕЗ пояснення граматики родового
  відмінка)
- 'Еховий патерн-«відлуння» для переадресації питання: `А тебе?` (неформально) / `А
  вас?` (формально) — як неподільний чанк, БЕЗ форми `А у тебе?`'
- Нормативний вибір у контрасті до типового суржику/русизму теми «знайомство» (дружина
  vs жена; лікар/лікарка vs врач; вибачте/пробачте vs ізвиніть; дякую/спасибі vs спасібо;
  теж/також vs тоже; фемінітив vs чоловічий генерик для жінки) і регістрово безпечний
  початковий вибір «тато» без маркування інших засвідчених родинних форм як неукраїнських.
register: розмовний
references:
- title: 'Wiki: pedagogy/a1/who-am-i (LOCKED 2026-04-23)'
  notes: 'Authoritative pedagogical brief — see Крок 1 (echo pattern `А тебе?` + `А
    у тебе?` avoidance), Крок 6 (feminitives), Декол. point #5 (feminitives as decolonization),
    та розділ "Типові помилки L2" (7 introductions-specific Surzhyk pairs).'
changelog:
- version: 1.2.0
  date: '2026-04-23'
  changes:
  - 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md (rubric
    from PR #1412, at-the-cafe template).'
  - Added lifecycle markers (lifecycle/reviewed_at/reviewed_by/review_notes).
  - 'Aligned with locked wiki: echo-question pattern (А тебе? / А вас?) made explicit
    in "Мене звати..." section; `А у тебе?` explicitly forbidden (#1392 Defect 2 avoidance).'
  - Split Діалог 3 from single-speaker monologue to explicit two-speaker exchange
    (addresses module-build r1 finding on mono-speaker dialogue).
  - 'Added feminitive directive to "Я — студент" section (Оксана — лікарка, NOT лікар)
    + called out as decolonization per wiki Крок 6 + Декол. #5.'
  - 'Added Surzhyk drill as new fill-in activity (7 items: папа/тато, жена/дружина,
    ізвиніть/вибачте, спасібо/дякую, тоже/теж, інженер/інженерка, врач/лікар) — mirrors
    wiki "Типові помилки L2" table.'
  - Extended `recommended` vocabulary with native-form counterparts (тато, дружина,
    дякую/спасибі, вибачте/пробачте, теж/також, А тебе?/А вас?, авторка, подруга).
  - 'Added wiki back-reference in references: section.'
- version: 1.2.1
  date: '2026-06-05'
  changes:
  - 'Retrofit plan repair for #2713: gave the summary section a real word budget and
    self-check function.'
  - 'Softened family-register guidance: `тато` remains the beginner default, but `папа`
    is not framed as nonexistent Ukrainian.'


## Existing module artifacts (read-only)

### module.md

# Хто я?

**Приві́т! Мене́ зва́ти Марко́. А тебе́?** — Hi! My name is Marko.
And yours?

This lesson stays short and spoken. First you hear a Ukrainian line, then you
use a small amount of English support to check the meaning. Treat the first
phrases as whole expressions:

| Українська опора | English support |
| --- | --- |
| **Мене́ зва́ти...** | My name is... |
| **Як тебе́ зва́ти?** | What is your name? informal |
| **Як вас зва́ти?** | What is your name? formal |
| **Ду́же приє́мно!** | Nice to meet you! |
| **Зві́дки ти?** | Where are you from? |

You do not need to explain every form yet. A first conversation can be built
from safe pieces.

By the end, you can:

- ask **Як тебе́ зва́ти?** with a peer and **Як вас зва́ти?** with a new adult;
- answer **Мене́ зва́ти...**;
- return the question with **А тебе́?** or **А вас?**;
- point to a person or thing with **це**;
- use **я**, **ти**, **він**, **вона**, and **ви** in simple identity lines;
- say **Я — студе́нт** or **Я — студе́нтка** without adding a present-tense
  "am" word;
- say where you are from with memorized phrases such as **Я з Украї́ни** and
  **Я з Кана́ди**;
- choose Ukrainian identity words, including **лі́карка**, **вчи́телька**, and
  **інжене́рка**.

## Діало́ги

Read each Ukrainian dialogue first. Do not translate line by line while you
read. The support table comes after the dialogue.

```text
Марко́: Приві́т! Як тебе́ зва́ти?
Оле́на: Мене́ зва́ти Оле́на. А тебе́?
Марко́: Мене́ зва́ти Марко́. Ду́же приє́мно!
Оле́на: Ду́же приє́мно! Зві́дки ти?
Марко́: Я з Кана́ди. А ти?
Оле́на: Я з Украї́ни.
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Приві́т!** | Hi! |
| **Як тебе́ зва́ти?** | What is your name? informal |
| **А тебе́?** | And yours? informal |
| **Я з Кана́ди.** | I am from Canada. |
| **Я з Украї́ни.** | I am from Ukraine. |

Use **Приві́т** with peers. Use **А тебе́?** only after the name question is
already active. It is an echo pattern: short, polite, and easy.

Now read a formal first meeting:

```text
Петро́: До́брий день! Як вас зва́ти?
Софі́я: Мене́ зва́ти Софі́я. А вас?
Петро́: Мене́ зва́ти Петро́. Ду́же приє́мно!
Софі́я: Мені́ також. Ви з Украї́ни?
Петро́: Так, я з Ки́єва.
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **До́брий день!** | Good afternoon! |
| **Як вас зва́ти?** | What is your name? formal |
| **А вас?** | And yours? formal |
| **Мені́ також.** | Me too. |
| **Так, я з Ки́єва.** | Yes, I am from Kyiv. |

The formal version changes two pieces. **тебе́** becomes **вас**. **ти**
becomes **ви**. English has one everyday word, "you"; Ukrainian asks you to
choose relationship and politeness.

The third dialogue introduces another person:

```text
Тара́с: Це Андрі́й. Він зі Льво́ва.
Ната́лка: Ду́же приє́мно. А хто це?
Тара́с: Це Окса́на. Вона́ з Оде́си. Вона́ — лі́карка.
Ната́лка: Ду́же приє́мно!
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це Андрі́й.** | This is Andrii. |
| **Він зі Льво́ва.** | He is from Lviv. |
| **А хто це?** | And who is this? |
| **Вона́ — лі́карка.** | She is a doctor. |

For a woman, use the feminine profession form when Ukrainian has the normal
form: **лі́карка**, **вчи́телька**, **інжене́рка**, **програмі́стка**,
**студе́нтка**. These are standard Ukrainian identity words.

<!-- INJECT_ACTIVITY: act-1 -->

## Мене́ зва́ти...

**Мене́ зва́ти...** is one phrase. You do not need the grammar of **мене́** or
**зва́ти** yet. You need the social move: ask, answer, echo.

| Українська | English support |
| --- | --- |
| **Мене́ зва́ти Марко́.** | My name is Marko. |
| **Мене́ зва́ти Оле́на.** | My name is Olena. |
| **Мене́ зва́ти [ім'я́].** | My name is [name]. |
| **Як тебе́ зва́ти?** | What is your name? informal |
| **Як вас зва́ти?** | What is your name? formal |
| **До поба́чення!** | Goodbye! |

Name exchange order:

1. **Приві́т!** or **До́брий день!**
2. **Як тебе́ зва́ти?** or **Як вас зва́ти?**
3. **Мене́ зва́ти...**
4. **А тебе́?** or **А вас?**
5. **Ду́же приє́мно!**

:::tip
For this module, **А тебе́?** and **А вас?** are return buttons. Use them only
after the same question is already active in the conversation.
:::

Avoid the English-shaped line "My name is..." as a Ukrainian sentence. The
natural first-introduction model is **Мене́ зва́ти...**.

<!-- INJECT_ACTIVITY: act-2 -->

## Це...

**Це** is the fast pointing word. It can introduce a thing, a city, or a
person:

| Українська | English support |
| --- | --- |
| **Це ка́ва.** | This is coffee. |
| **Це Ки́їв.** | This is Kyiv. |
| **Це Андрі́й.** | This is Andrii. |
| **Це Окса́на.** | This is Oksana. |

Use **Що це?** for a thing: **Що це? Це ка́ва.** Use **Хто це?** for a
person: **Хто це? Це Окса́на.**

Keep the question word first. Ukrainian beginner questions are easier when the
question word opens the question: **Хто це?**, **Що це?**, **Зві́дки ти?**

Use **це** instead of an English-style "it" when you identify a person in a
photo, on the phone, or in a group:

| Українська | English support |
| --- | --- |
| **Це мій та́то.** | This is my dad. |
| **Це моя́ ма́ма.** | This is my mom. |
| **Це моя́ подру́га.** | This is my female friend. |

For people, **він** and **вона́** are also possible after you know who the
person is: **Це Андрі́й. Він зі Льво́ва.** **Це Окса́на. Вона́ — лі́карка.**

<!-- INJECT_ACTIVITY: act-3 -->

## Особо́ві займéнники

Learn only the naming case now:

| Українська | English support |
| --- | --- |
| **я** | I, the speaker |
| **ми** | we |
| **ти** | you, one familiar person |
| **ви** | you formal, or you plural |
| **він** | he |
| **вона́** | she |
| **вони́** | they |

The important beginner contrast is **ти / ви**. Use **ти** **для дру́зів,
діте́й** (for friends and children) and close classmates when the relationship
is informal. Use **ви** **для викладачі́в, ста́рших люде́й** (for teachers and
older people), one unknown adult, a host, or several people.

Mini-patterns:

| Неформально | Формально |
| --- | --- |
| **Як тебе́ зва́ти?** | **Як вас зва́ти?** |
| **А тебе́?** | **А вас?** |
| **Зві́дки ти?** | **Зві́дки ви?** |

When you write polite **Ви** to one person, Ukrainian often uses a capital
letter. In this course page, lower-case **ви** is enough for practice, but
recognize **Ви** when you see it.

<!-- INJECT_ACTIVITY: act-4 -->

## Я — студе́нт

Ukrainian present-time identity lines do not need a word for English "am" or
"is":

| Українська | English support |
| --- | --- |
| **Я — студе́нт.** | I am a male student. |
| **Я — студе́нтка.** | I am a female student. |
| **Він — лі́кар.** | He is a doctor. |
| **Вона́ — лі́карка.** | She is a doctor. |

The same identity pattern works for nationality:

| Чоловіча форма | Жіноча форма |
| --- | --- |
| **Я — украї́нець.** | **Я — украї́нка.** |
| **Я — канаді́єць.** | **Я — кана́дка.** |
| **Я — америка́нець.** | **Я — америка́нка.** |

The dash is a reading helper. It marks the place where English expects "am" or
"is." In ordinary writing, you may see the same pattern without a dash:
**Я студе́нт.**

Use profession pairs as pairs:

| Чоловіча форма | Жіноча форма |
| --- | --- |
| **студе́нт** | **студе́нтка** |
| **вчи́тель** | **вчи́телька** |
| **лі́кар** | **лі́карка** |
| **програмі́ст** | **програмі́стка** |
| **інжене́р** | **інжене́рка** |
| **украї́нець** | **украї́нка** |
| **канаді́єць** | **кана́дка** |
| **америка́нець** | **америка́нка** |

The feminine form is the primary form for a woman. **Окса́на — лі́карка.**
**Софі́я — студе́нтка.** **Ната́лка — інжене́рка.**

## Зві́дки?

**Зві́дки?** means "from where?" Use the country phrases as memorized expressions:

| Питання | Відповідь |
| --- | --- |
| **Зві́дки ти?** | **Я з Украї́ни.** |
| **Зві́дки ви?** | **Я з Кана́ди.** |
| **Ви з Украї́ни?** | **Так, я з Ки́єва.** |

Add a few prepared places:

| Українська | English support |
| --- | --- |
| **Я з Украї́ни.** | I am from Ukraine. |
| **Я з Кана́ди.** | I am from Canada. |
| **Я зі Шта́тів.** | I am from the States. |
| **Я з Німе́ччини.** | I am from Germany. |
| **Я з Ки́єва.** | I am from Kyiv. |
| **Я зі Льво́ва.** | I am from Lviv. |
| **Я з Оде́си.** | I am from Odesa. |

The forms after **з / зі** are memorized here. Do not open the full grammar of
"from" yet. Your speaking goal is a natural first-contact answer.

Build a three-line self-introduction:

```text
До́брий день. Мене́ зва́ти Софі́я.
Я з Украї́ни.
Я — студе́нтка.
```

Or informal:

```text
Приві́т! Мене́ зва́ти Марко́.
Я з Кана́ди.
Я — програмі́ст.
```

Native Ukrainian choices matter even in tiny introductions. Use **та́то** for
dad, **дружи́на** for wife, **ви́бачте** or **проба́чте** for excuse me,
**дя́кую** or **спаси́бі** for thank you, and **теж** or **та́кож** for also.

## Слу́хай і записуй

The Resources tab has three optional Ukrainian Lessons Podcast links: Episode
3 for introductions, Episode 4 for **Зві́дки?**, and Episode 8 for
professions. Listen for one short phrase, repeat it once, and come back here.

For handwriting recognition, ask a teacher, tutor, or classmate to write these
original labels in a notebook: **ім'я́** (name), **прі́звище** (surname),
**Ки́їв**, **студе́нтка**, **лі́карка**. First compare the notebook label with
the printed word; then write your own line.

## Самопереві́рка

Cover the English support and read the Ukrainian aloud:

| Українська | English support |
| --- | --- |
| **Як тебе́ зва́ти?** | What is your name? informal |
| **Мене́ зва́ти...** | My name is... |
| **А тебе́?** | And yours? informal |
| **А вас?** | And yours? formal |
| **Це Окса́на.** | This is Oksana. |
| **Хто це?** | Who is this? |
| **Я — студе́нтка.** | I am a female student. |
| **Вона́ — лі́карка.** | She is a doctor. |
| **Зві́дки ти?** | Where are you from? informal |
| **Я з Кана́ди.** | I am from Canada. |

Use the workbook for extra practice: profession pairs, dialogue fill-ins,
safer Ukrainian sentence choices, native-form choices, and vocabulary
recognition.

You can now greet someone, ask and answer a name question, say where you are
from, name a simple role, and return the question with **А тебе́?** or
**А вас?**. Next, Module 6 uses these people words for family.


### activities.yaml

inline:
  - id: act-1
    type: quiz
    title: Ти чи ви?
    instruction: Обери фразу для ситуації.
    items:
      - prompt: Ти знайомишся з однокурсником свого віку.
        options:
          - text: Як тебе звати?
            correct: true
          - text: Як вас звати?
            correct: false
        explanation: З одним знайомим або рівним співрозмовником уживай тебе.
      - prompt: Ти знайомишся з незнайомим дорослим на орієнтації.
        options:
          - text: Як вас звати?
            correct: true
          - text: Як тебе звати?
            correct: false
        explanation: З незнайомим дорослим або у формальній ситуації уживай вас.
      - prompt: Однокурсник питає твоє ім'я. Ти відповідаєш і повертаєш питання.
        options:
          - text: Мене звати Олена. А тебе?
            correct: true
          - text: Мене звати Олена. А вас?
            correct: false
        explanation: Рівна ситуація залишається неформальною.
      - prompt: Викладач питає твоє ім'я. Ти відповідаєш і повертаєш питання.
        options:
          - text: Мене звати Петро. А вас?
            correct: true
          - text: Мене звати Петро. А тебе?
            correct: false
        explanation: З викладачем ситуація залишається формальною.
  - id: act-2
    type: fill-in
    title: Склади ім'я
    instruction: Обери пропущене слово або фразу.
    items:
      - sentence: ___ звати Марко.
        answer: Мене
        options:
          - Мене
          - Ти
          - Це
        explanation: Мене звати... — цілий блок для представлення імені.
      - sentence: Як ___ звати?
        answer: тебе
        options:
          - тебе
          - я
          - він
        explanation: Як тебе звати? — неформальне питання.
      - sentence: Як ___ звати?
        answer: вас
        options:
          - вас
          - вона
          - ми
        explanation: Як вас звати? — формальне або множинне питання.
      - sentence: Дуже ___!
        answer: приємно
        options:
          - приємно
          - студент
          - звідки
        explanation: Дуже приємно звучить після обміну іменами.
      - sentence: Мене звати Олена. А ___?
        answer: тебе
        options:
          - тебе
          - Київ
          - це
        explanation: А тебе? неформально повертає питання.
  - id: act-3
    type: match-up
    title: Це / хто / що
    instruction: З'єднай український рядок із його роботою.
    pairs:
      - left: Це Андрій.
        right: представити людину
      - left: Це Оксана.
        right: представити іншу людину
      - left: Хто це?
        right: запитати про людину
      - left: Що це?
        right: запитати про річ
      - left: Це кава.
        right: назвати річ
  - id: act-4
    type: quiz
    title: Обери займенник
    instruction: Обери займенник для української ситуації.
    items:
      - prompt: Мовець говорить про себе.
        options:
          - text: я
            correct: true
          - text: ти
            correct: false
          - text: вони
            correct: false
        explanation: Я — це мовець.
      - prompt: Один друг або близький однокурсник.
        options:
          - text: ти
            correct: true
          - text: ви
            correct: false
          - text: він
            correct: false
        explanation: Ти — один неформальний співрозмовник.
      - prompt: Один незнайомий дорослий або формальна ситуація.
        options:
          - text: ви
            correct: true
          - text: ти
            correct: false
          - text: вона
            correct: false
        explanation: Ви — формально до однієї людини, а також множина.
      - prompt: Жінка або дівчина вже відома в розмові.
        options:
          - text: вона
            correct: true
          - text: він
            correct: false
          - text: я
            correct: false
        explanation: Вона вказує на жінку або дівчину.
workbook:
  - type: error-correction
    title: Обери українське речення
    anchor_id: fix-common-l2-traps
    instruction: Обери безпечніший український рядок про ідентичність.
    items:
      - sentence: Я є студент.
        error: Я є студент.
        correction: Я студент.
        options:
          - Я студент.
          - Я є студент.
        explanation: У теперішній ідентичності кажи Я студент або Я — студент.
      - sentence: Моє ім'я є Джон.
        error: Моє ім'я є Джон.
        correction: Мене звати Джон.
        options:
          - Мене звати Джон.
          - Моє ім'я є Джон.
        explanation: Мене звати... — частотна модель першого представлення.
      - sentence: Мене звати Марко. А у тебе?
        error: А у тебе?
        correction: А тебе?
        options:
          - А тебе?
          - А у тебе?
        explanation: На A1 уживай короткий відлунний блок А тебе?; форму з у вивчатимемо пізніше.
      - sentence: Оксана каже, "Я (жінка) лікар."
        error: Я (жінка) лікар.
        correction: Я лікарка.
        options:
          - Я лікарка.
          - Я (жінка) лікар.
        explanation: Лікарка — стандартна жіноча форма для жінки, яка працює лікарем.
      - sentence: Воно мій тато.
        error: Воно
        correction: Це мій тато.
        options:
          - Це мій тато.
          - Воно мій тато.
        explanation: Для першого називання людини вживай це; він можливе після цього.
      - sentence: Привіт, пане професоре!
        error: Привіт
        correction: Добрий день, пане професоре!
        options:
          - Добрий день, пане професоре!
          - Привіт, пане професоре!
        explanation: З професором або незнайомим дорослим уживай Добрий день.
  - type: match-up
    title: Пари професій
    instruction: З'єднай чоловічу і жіночу форму професії.
    pairs:
      - left: студент
        right: студентка
      - left: вчитель
        right: вчителька
      - left: лікар
        right: лікарка
      - left: програміст
        right: програмістка
      - left: інженер
        right: інженерка
      - left: українець
        right: українка
      - left: канадієць
        right: канадка
      - left: американець
        right: американка
  - type: group-sort
    title: Неформально чи формально
    instruction: Розклади фрази за ситуацією.
    groups:
      - label: Неформально
        items:
          - Як тебе звати?
          - А тебе?
          - Звідки ти?
      - label: Формально
        items:
          - Як вас звати?
          - А вас?
          - Звідки ви?
  - type: fill-in
    title: Доповни діалог
    instruction: Обери фразу, яка завершує рядок першого знайомства.
    items:
      - sentence: Привіт! Як ___ звати?
        answer: тебе
        options:
          - тебе
          - вас
          - це
        explanation: Привіт показує неформальну ситуацію з ровесником.
      - sentence: Мене ___ Олена.
        answer: звати
        options:
          - звати
          - це
          - з
        explanation: Мене звати... — блок для імені.
      - sentence: Мене звати Марко. ___ тебе?
        answer: А
        options:
          - А
          - Хто
          - Що
        explanation: А тебе? повертає питання.
      - sentence: Добрий день! Як ___ звати?
        answer: вас
        options:
          - вас
          - тебе
          - я
        explanation: Добрий день пасує до формальної версії тут.
      - sentence: Дуже ___!
        answer: приємно
        options:
          - приємно
          - Київ
          - студентка
        explanation: Дуже приємно звучить після обміну іменами.
      - sentence: ___ ти? Я з Канади.
        answer: Звідки
        options:
          - Звідки
          - Хто
          - Що
        explanation: Звідки питає, звідки людина.
  - type: fill-in
    title: Обери українську норму
    instruction: Заповни речення українським вибором.
    items:
      - sentence: Це моя ___ Марія.
        answer: дружина
        options:
          - дружина
          - жена
        explanation: Дружина — природний український вибір для жінки в шлюбі.
      - sentence: ___, як вас звати?
        answer: Вибачте
        options:
          - Вибачте
          - Ізвиніть
        explanation: Вибачте і пробачте — безпечні українські вибори.
      - sentence: ___, дуже приємно!
        answer: Дякую
        options:
          - Дякую
          - Спасібо
        explanation: Дякую і спасибі — безпечні українські вибори.
      - sentence: Мені ___ приємно.
        answer: теж
        options:
          - теж
          - тоже
        explanation: Теж і також — безпечні українські вибори.
      - sentence: Оксана — ___.
        answer: інженерка
        options:
          - інженерка
          - інженер
        explanation: Для жінки вживай фемінітив, коли українська форма існує.
      - sentence: Це мій ___.
        answer: лікар
        options:
          - лікар
          - врач
        explanation: Лікар — українська форма; врач — російське слово.
  - type: translate
    title: Лексика знайомства
    instruction: Обери англійське значення.
    items:
      - source: Мене звати...
        options:
          - text: My name is...
            correct: true
          - text: Where are you from?
            correct: false
          - text: This is...
            correct: false
        explanation: Мене звати... — блок для імені.
      - source: Як тебе звати?
        options:
          - text: What is your name? informal
            correct: true
          - text: Who is this?
            correct: false
          - text: I am from Ukraine.
            correct: false
        explanation: Тебе позначає неформальну версію.
      - source: Як вас звати?
        options:
          - text: What is your name? formal
            correct: true
          - text: And yours? informal
            correct: false
          - text: This is Kyiv.
            correct: false
        explanation: Вас позначає формальну версію.
      - source: Дуже приємно!
        options:
          - text: Pleased to meet you!
            correct: true
          - text: Goodbye!
            correct: false
          - text: Where from?
            correct: false
        explanation: Дуже приємно ввічливо завершує представлення.
      - source: Звідки ти?
        options:
          - text: Where are you from? informal
            correct: true
          - text: What is this?
            correct: false
          - text: I am a student.
            correct: false
        explanation: Звідки питає про походження.
      - source: Я — студентка.
        options:
          - text: I am a female student.
            correct: true
          - text: She is a doctor.
            correct: false
          - text: My name is...
            correct: false
        explanation: Студентка — жіноча форма.


### vocabulary.yaml

- lemma: я
  translation: I
  pos: pronoun
  usage: Я з України.
- lemma: ти
  translation: you, informal singular
  pos: pronoun
  usage: Звідки ти?
- lemma: він
  translation: he
  pos: pronoun
  usage: Він зі Львова.
- lemma: вона
  translation: she
  pos: pronoun
  usage: Вона — лікарка.
- lemma: ми
  translation: we
  pos: pronoun
  usage: Ми студенти.
- lemma: ви
  translation: you, formal or plural
  pos: pronoun
  usage: Як вас звати?
- lemma: вони
  translation: they
  pos: pronoun
  usage: Вони з України.
- lemma: мене звати
  translation: my name is
  pos: phrase
  usage: Мене звати Олена.
- lemma: прізвище
  translation: surname
  pos: noun
  usage: "Прізвище: Шевченко."
- lemma: як тебе звати?
  translation: what is your name? informal
  pos: phrase
  usage: Як тебе звати?
- lemma: як вас звати?
  translation: what is your name? formal
  pos: phrase
  usage: Як вас звати?
- lemma: а тебе?
  translation: and yours? informal
  pos: phrase
  usage: А тебе?
- lemma: а вас?
  translation: and yours? formal
  pos: phrase
  usage: А вас?
- lemma: дуже приємно
  translation: pleased to meet you
  pos: phrase
  usage: Дуже приємно!
- lemma: це
  translation: this is / this
  pos: pronoun
  usage: Це Оксана.
- lemma: хто
  translation: who
  pos: pronoun
  usage: Хто це?
- lemma: що
  translation: what
  pos: pronoun
  usage: Що це?
- lemma: звідки
  translation: where from
  pos: adverb
  usage: Звідки ти?
- lemma: з
  translation: from
  pos: preposition
  usage: Я з Канади.
- lemma: зі
  translation: from
  pos: preposition
  usage: Він зі Львова.
- lemma: Україна
  translation: Ukraine
  pos: proper noun
  usage: Я з України.
- lemma: Канада
  translation: Canada
  pos: proper noun
  usage: Я з Канади.
- lemma: Німеччина
  translation: Germany
  pos: proper noun
  usage: Я з Німеччини.
- lemma: Штати
  translation: the States
  pos: proper noun plural
  usage: Я зі Штатів.
- lemma: Київ
  translation: Kyiv
  pos: proper noun
  usage: Я з Києва.
- lemma: Львів
  translation: Lviv
  pos: proper noun
  usage: Він зі Львова.
- lemma: Одеса
  translation: Odesa
  pos: proper noun
  usage: Вона з Одеси.
- lemma: українець
  translation: Ukrainian man
  pos: noun
  usage: Андрій — українець.
- lemma: українка
  translation: Ukrainian woman
  pos: noun
  usage: Олена — українка.
- lemma: канадієць
  translation: Canadian man
  pos: noun
  usage: Марко — канадієць.
- lemma: канадка
  translation: Canadian woman
  pos: noun
  usage: Олена — канадка.
- lemma: американець
  translation: American man
  pos: noun
  usage: Андрій — американець.
- lemma: американка
  translation: American woman
  pos: noun
  usage: Софія — американка.
- lemma: студент
  translation: male student
  pos: noun
  usage: Я — студент.
- lemma: студентка
  translation: female student
  pos: noun
  usage: Я — студентка.
- lemma: вчитель
  translation: male teacher
  pos: noun
  usage: Він — вчитель.
- lemma: вчителька
  translation: female teacher
  pos: noun
  usage: Вона — вчителька.
- lemma: лікар
  translation: male doctor
  pos: noun
  usage: Він — лікар.
- lemma: лікарка
  translation: female doctor
  pos: noun
  usage: Вона — лікарка.
- lemma: програміст
  translation: male programmer
  pos: noun
  usage: Марко — програміст.
- lemma: програмістка
  translation: female programmer
  pos: noun
  usage: Олена — програмістка.
- lemma: інженер
  translation: male engineer
  pos: noun
  usage: Андрій — інженер.
- lemma: інженерка
  translation: female engineer
  pos: noun
  usage: Оксана — інженерка.
- lemma: тато
  translation: dad
  pos: noun
  usage: Це мій тато.
- lemma: мама
  translation: mom
  pos: noun
  usage: Це моя мама.
- lemma: дружина
  translation: wife
  pos: noun
  usage: Це моя дружина.
- lemma: подруга
  translation: female friend
  pos: noun
  usage: Це моя подруга.
- lemma: вибачте
  translation: excuse me
  pos: interjection
  usage: Вибачте, як вас звати?
- lemma: пробачте
  translation: excuse me / forgive me
  pos: interjection
  usage: Пробачте.
- lemma: дякую
  translation: thank you
  pos: interjection
  usage: Дякую!
- lemma: спасибі
  translation: thank you
  pos: interjection
  usage: Спасибі!
- lemma: теж
  translation: also / too
  pos: adverb
  usage: Мені теж приємно.
- lemma: також
  translation: also
  pos: adverb
  usage: Мені також приємно.
- lemma: добрий день
  translation: good afternoon / hello
  pos: phrase
  usage: Добрий день!
- lemma: привіт
  translation: hi
  pos: interjection
  usage: Привіт!


### resources.yaml

- title: ULP Season 1, Episode 3 — How to Introduce Yourself
  role: podcast
  source_ref: ULP Season 1, Episode 3 — How to Introduce Yourself
  url: https://www.ukrainianlessons.com/episode3/
  notes: "Plan reference: Мене звати, nationalities, and Дуже приємно."
- title: ULP Season 1, Episode 4 — Where You Live and Where From
  role: podcast
  source_ref: ULP Season 1, Episode 4 — Where You Live and Where From
  url: https://www.ukrainianlessons.com/episode4/
  notes: "Plan reference: Звідки ви? and from-place phrases."
- title: ULP Season 1, Episode 8 — Jobs and Professions
  role: podcast
  source_ref: ULP Season 1, Episode 8 — Jobs and Professions
  url: https://www.ukrainianlessons.com/episode8/
  notes: "Plan reference: profession vocabulary with masculine and feminine forms."


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
