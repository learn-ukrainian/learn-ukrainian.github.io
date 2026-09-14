# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: reading-ukrainian.
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
  title: Читаємо слова
  sections:
  - Склади
  - Голосні літери
  - Читаємо слова
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
  title: Друк, зошит, перевірка
  sections:
  - Пастки читання
  - Друк, зошит, перевірка
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
  title: Далі
  sections:
  - Далі
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
  new_id: act-5
  lesson: 3
items_min_exempt:
- id: act-4
  reason: 4-item original activity preserved from baseline
- id: act-w2
  reason: 4-item original activity preserved from baseline
- id: act-w3
  reason: 4-item original activity preserved from baseline
- id: act-w4
  reason: 5-item original activity preserved from baseline
- id: act-w5
  reason: 5-item original activity preserved from baseline
- id: act-5
  reason: 3-item original activity preserved from baseline
proper_names: []


## Original plan (read-only)

module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: 1.3.2
letter_module: true
lifecycle: locked
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-reading-ukrainian
review_notes: Review-and-lock pass for A1 scale batch input. See wiki/.reviews/pedagogy/a1/reading-ukrainian-review-LOCKED.md
  for the wiki-side report (5-dim, all ≥9); see PR body for the plan-side findings
  (pragmatic / Russianism / calque / contradiction / references / cross-pair drift).
  The plan was brought into alignment with the locked wiki by (a) adding a reading-specific
  L2 error-drill activity that mirrors the wiki's new "Типові помилки L2" table, (b)
  adding a `references:` block with a back-reference to the locked wiki, (c) adding
  lifecycle markers per docs/best-practices/wiki-plan-review-and-lock.md. No Russianisms,
  calques, or homoglyphs detected in plan prose; Latin-in-Cyrillic homoglyph scan
  is clean.
title: Читаємо українською
subtitle: Від літер до слів та речень
focus: phonetics
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
word_target: 1200
objectives:
- Вміти читати будь-яке українське слово, розпізнаючи звуки та об'єднуючи їх у склади
- Розуміти правило складоподілу — рахувати голосні, щоб порахувати склади
- Навчитися впевнено читати багатоскладові слова (не по літерах)
- Розуміти, як 10 голосних літер позначають 6 голосних звуків
content_outline:
- section: Склади
  words: 250
  points:
  - 'Большакова, 1 клас, стор. 25: «У слові стільки складів, скільки голосних звуків.»
    Порахуй голосні — дізнаєшся кількість складів. Це правило ніколи не порушується.
    ма-ма (2 голосні = 2 склади), мо-ло-ко (3 голосні = 3 склади), банк (1 голосна
    = 1 склад).'
  - 'Як українські діти вчаться читати — складові ланцюжки: Починаємо з пари приголосний
    + голосний: М → ма, мо, му, ми. Потім навпаки: ам, ом, ум. Далі будуємо слова:
    ма-ма, мо-ло-ко. Це підхід "знизу вгору": звук → склад → слово. (Захарійчук 1
    клас, стор. 46; Большакова 1 клас, стор. 25)'
  - 'Звуковий аналіз слова (Большакова стор. 29): 1) Визначаю голосні звуки 2) Ділю
    слово на склади 3) Ставлю наголос 4) Позначаю приголосні звуки. Тест із підборіддям
    для підрахунку складів (Кравцова 2 клас, стор. 13): покладіть долоню під підборіддя,
    скажіть слово — кожен дотик підборіддя = один склад.'
  - 'Українська система позначення звуків (Захарійчук стор. 15): [●] голосний, [—]
    твердий приголосний, [=] м''який приголосний. Цього вчиться кожна українська дитина
    в 1 класі.'
- section: Голосні літери
  words: 300
  points:
  - 'Повторення з модуля №1: 6 звуків, 10 літер. Тепер розберемо всі 10 окремо. Прості
    голосні (один звук кожна): А [а], О [о], У [у], Е [е], И [и], І [і]. Кожна позначає
    ОДИН стабільний звук — жодних сюрпризів.'
  - 'Йотовані голосні (два звуки або пом''якшення): Я = [йа] на початку слова (яблуко)
    або після голосного (моя). Після приголосного: пом''якшує його + [а] (пісня —
    Н пом''якшений). Ю = [йу] або пом''якшення + [у]. Є = [йе] або пом''якшення +
    [е]. Ї = ЗАВЖДИ [йі] — ніколи не пом''якшує. Лише на початку слова, після голосного
    або після апострофа. Унікальна для української мови.'
  - 'Критичні мінімальні пари: И проти І: кит проти кіт, дим проти дім. Послухайте
    відео Анни з правильною вимовою кожного з них — різниця тонка, але вона змінює
    значення.'
- section: Читання слів
  words: 500
  points:
  - 'Застосовуйте складові ланцюжки до реальних слів. Не читайте по літерах — читайте
    по складах. Використовуйте звуковий аналіз: спочатку знайдіть голосні, поділіть
    на склади, потім об''єднайте. Приклад: книга — знайдіть голосні И, А → кни-га
    → прочитайте.'
  - 'Поступове ускладнення за українською класифікацією: односкладові (1 склад): дім,
    сон, ліс, дуб, хліб. двоскладові (2 склади): ма-ма, та-то, во-да, ру-ка, ха-та,
    ка-ша. трискладові (3 склади): ап-те-ка, мо-ло-ко, лю-ди-на, ву-ли-ця. багатоскладові
    (4+ склади): у-ні-вер-си-тет, біб-лі-о-те-ка, фо-то-гра-фі-я.'
  - 'Назви українських міст як практика читання: Ки-їв, Льві-в, О-де-са, Хар-ків,
    Дні-про, Пол-та-ва. Зверніть увагу на різну кількість складів та їхню структуру.'
  - 'Особливі буквосполучення, на які слід звернути увагу (анонс для модуля №3): Щ
    — це завжди [шч] — що, ще. Ь не має звуку — він пом''якшує: день, сіль, кінь.
    Апостроф розділяє: сім''я, м''ясо, п''ять. Вони будуть детально розібрані у модулі
    №3.'
- section: Підсумок
  words: 150
  points:
  - 'Самоперевірка: Як порахувати склади в українському слові? Назвіть 6 голосних
    звуків. Назвіть 4 йотовані голосні літери. Що робить Ь? Що робить апостроф? Прочитайте
    це слово: бібліотека — скільки в ньому складів?'
vocabulary_hints:
  author_note: На А1 у цьому модулі всі слова (required + recommended) подаються як
    носії фонетичної практики — склади, наголос, йотовані, `ь`, апостроф, ДЖ/ДЗ, Ї,
    Щ. НЕ вводьте відмінкові парадигми, дієвідміну чи ступені порівняння — відмінки
    починаються з модуля №18 (знахідний). Кожне слово тут має одну словоформу, яку
    учень читає вголос і діагностує за таблицею «Типові помилки L2» (див. locked wiki,
    розділ після Словникового мінімуму).
  required:
  - яблуко (apple) — Я at word start = [йа]
  - молоко (milk) — 3 syllables, all simple vowels
  - людина (person) — Л + Ю combination
  - вулиця (street) — Ц sound practice
  - столиця (capital) — Київ — столиця України
  - каша (porridge) — Ш sound practice
  - пісня (song) — softening by Я after consonant
  recommended:
  - університет (university) — long word practice
  - бібліотека (library) — 5 syllables
  - фотографія (photography) — long word with Ф
  - шоколад (chocolate) — Ш + О + К combination
targets:
  new_vocabulary:
  - яблуко
  - молоко
  - людина
  - вулиця
  - столиця
  - каша
  - пісня
  new_grammar: []
  recycle_vocabulary: []
activity_hints:
- type: divide-words
  focus: 'Поділи слова на склади: мо-ло-ко, ап-те-ка, у-ні-вер-си-тет'
  items: 8
- type: count-syllables
  focus: Порахуй склади — скільки голосних, стільки й складів
  items: 8
- type: match-up
  focus: 'З''єднай йотовані голосні з їхніми звуковими компонентами: Я=[й]+[а]'
  items: 6
- type: quiz
  focus: Прочитай слово і вибери його значення
  items: 6
- type: odd-one-out
  focus: Яке слово зайве? — за кількістю складів (односкладове серед двоскладових)
  items: 6
- type: match-up
  focus: Типові помилки L2 при читанні (mirror wiki "Типові помилки L2" table). З'єднайте
    слово з типом помилки, яку воно перевіряє.
  items:
  - день: 'Ігнорування м''якого знака: [ден] замість [ден′]'
  - сім'я: 'Злиття через апостроф: [сіма] замість [сімйа]'
  - дякую: 'Йотована після приголосного: [дйакуйу] замість [д''акуйу]'
  - Україна: '`Ї` → [і]: [Украіна] замість [Украйіна]'
  - борщ: '`Щ` → [ш]: [борш] замість [боршч]'
  - джміль: '`ДЖ` як два звуки: [д]-[жміль] замість [джміль]'
  - молоко: Читання по літерах замість по складах
  - огірок: Сплутування СКЛАДОПОДІЛУ з ПЕРЕНЕСЕННЯМ (складоподіл `о-гі-рок`; перенесення
      `огі-рок`, бо одна літера `о-` не може стояти окремо в рядку)
connects_to:
- a1-003 (Особливі знаки)
prerequisites:
- a1-001 (Звуки, літери та привіт)
grammar:
- 'Правило складоподілу: у слові стільки складів, скільки голосних звуків'
- 'Звуковий аналіз слова: визначити голосні → поділити на склади → наголос → приголосні'
- 'Складові ланцюжки: приголосний + голосний = склад (ма, мо, му)'
- 'Українська система позначення звуків: [●] голосний, [—] твердий приголосний, [=]
  м''який приголосний'
- Співвідношення: 10 голосних літер → 6 голосних звуків
- Йотовані голосні (Я, Ю, Є як два звуки або пом'якшення; Ї завжди [йі])
- 'Класифікація слів: односкладові, двоскладові, трискладові, багатоскладові'
- Ь, апостроф (ознайомлення — детально у модулі №3)
register: розмовний
references:
- title: Большакова, буквар 1 клас, стор. 25
  notes: 'Правило складоподілу: «У слові стільки складів, скільки голосних звуків.»'
- title: Большакова, буквар 1 клас, стор. 29
  notes: Звуковий аналіз слова — як аналізувати звуки у слові.
- title: Захарійчук 1 клас (НУШ 2025), стор. 13-15
  notes: 'Позначення звуків: [•] для голосних, [–] для приголосних, [=] для м''яких.'
- title: Вашуленко, Українська мова 2 клас, стор. 23-27
  notes: Правила переносу, наголос як носій значення (сім'я/сім'я, обід/обід), йотовані
    голосні.
- title: Кравцова, Українська мова 2 клас, стор. 13
  notes: Кінестетичний тест «долоня під підборіддям» для підрахунку складів.
- title: 'Wiki: pedagogy/a1/reading-ukrainian (LOCKED 2026-04-23)'
  notes: Authoritative pedagogical brief — see Кроки 1–7 (sequencing), "Типові помилки
    L2" (reading-specific decoding errors — 8 rows), and Приклад 5 (partner-diagnostic
    drill closing the loop).
- title: 'Wiki: pedagogy/a1/sounds-letters-and-hello (LOCKED 2026-04-23)'
  notes: Sibling wiki for sound-production; this wiki (reading-ukrainian) targets
    the decoding-from-print slice — intentional overlap on Ь/apostrophe/iotated/Щ/ДЖ/ДЗ,
    deliberate distinction in framing (production vs. decoding).
changelog:
- version: 1.3.0
  date: '2026-04-23'
  changes:
  - Review-and-lock pass. Added lifecycle markers (lifecycle/reviewed_at/reviewed_by/review_notes)
    per docs/best-practices/wiki-plan-review-and-lock.md.
  - 'Added new match-up activity: reading-specific L2 error drill (8 items, mirrors
    wiki "Типові помилки L2" table — closes the wiki-plan drift on reading errors).'
  - 'Consolidated `references:` block: added Вашуленко, Кравцова textbook entries
    and back-references to both locked sibling wikis (reading-ukrainian + sounds-letters-and-hello).
    Previous bottom-of-file `references:` had only 3 Большакова/Захарійчук entries.'
  - Removed duplicate `references:` block at end of file (was a pre-existing inconsistency
    — duplicate YAML keys are unsafe and parser-dependent; PyYAML silently takes last-key-wins,
    which meant only the 3-entry tail block was reaching `validate_plans.py`, hiding
    the earlier block). The consolidated single block now carries all 7 entries.
plan_fixes:
- version: 1.3.1
  date: '2026-04-24'
  trigger: Plan check rejected U+0301 combining acute stress marks in 7 place(s).
    Pipeline adds stress marks deterministically AFTER review; plans must be stress-free.
  changes:
  - strip U+0301 from all string values (7 removals)
- version: 1.3.2
  date: '2026-04-25'
  ref: '#1550'
  trigger: Letter-driven module needs explicit exception class for activity-count
    gates and pedagogical-stage reviewer calibration (a1/2 in alphabet/orthography
    exception class with a1/1 and a1/3).
  changes:
  - add letter_module flag (true) — allows higher activity counts for letter-recognition
    coverage; word-count target unchanged


## Existing module artifacts (read-only)

### module.md

# Читаємо українською

**ма — мо — му — ми. ма́ма. молоко́.** — syllables and first words.

Приві́т! In Module 1 you met Ukrainian letters and the word **склад**. Here
you turn that word into a reading tool. Printed Ukrainian comes first; English
support helps you check what your eyes already found.

For one listening pass before you read fast, open the public ULP
[Ukrainian Alphabet guide](https://www.ukrainianlessons.com/ukrainian-alphabet/).
Use it only as listen-and-repeat support: do not download, transcribe, remix,
or reuse the audio. Listen for the vowel sound, point to the letter on this
page, then read the printed word.

Module 1 only previewed **склад**. This module teaches the counting rule:

**one vowel sound = one склад**

In print, count the letters that mark vowel sounds. Then split the word into
syllables and read it without guessing from another alphabet.

By the end, you can:

- count syllables by counting vowel sounds;
- read simple open syllables such as **ма**, **мо**, **му**, **ми**;
- keep the six simple vowel sounds clear;
- explain what **Я, Ю, Є, Ї** do at beginner level;
- read **ма́ма**, **молоко́**, **день**, **я́блуко**, **люди́на**, and
  **ву́лиця**;
- avoid the first reading traps: splitting **дж** and **дз**, ignoring **ь**,
  blurring **о**, and losing **й** in **ї**.

## Склади

**склад** — syllable.

Start every reading attempt with one Ukrainian question:

**Де голосні звуки?** — Where are the vowel sounds?

In Ukrainian, every syllable has a vowel sound. A single vowel can be a whole
syllable, and a consonant by itself cannot make a syllable.

| Слово́ | Letters that mark vowel sounds | Склади́ |
| --- | --- | --- |
| **день** | **е** | 1 |
| **ма́ма** | **а + а** | 2 |
| **молоко́** | **о + о + о** | 3 |
| **ву́лиця** | **у + и + я** | 3 |

Use a simple body check. Put a hand lightly under your chin and say the word
slowly. Each open vowel pulse makes the chin move. That movement is a
beginner check before you write or choose an answer.

Build from syllables instead of naming letters one by one:

| Letter path | Reading path |
| --- | --- |
| М + А | **ма** |
| М + О | **мо** |
| М + У | **му** |
| М + И | **ми** |

Then join syllables:

**ма + ма = ма́ма**

**мо + ло + ко = молоко́**

:::tip
**склад** — syllable. Find the vowel sound first. That is the anchor.
:::

<!-- INJECT_ACTIVITY: act-1 -->

## Голосні лі́тери

**А О У Е И І** — six simple letters for vowel sounds.

The sounds are:

**[а] [о] [у] [е] [и] [і]**

Read them as clean sounds. In **молоко́**, every **о** stays **о**:

**мо-ло-ко́**

Say it slowly as three open beats, but keep the written word whole on the
page.

Now add the four other letters that mark vowel sounds:

**Я Ю Є Ї**

At beginner level, use this two-job rule:

| Лі́тера | At the start of a word or after a vowel/apostrophe | After a consonant |
| --- | --- | --- |
| **Я** | **[йа]** as in **я́блуко** | softens the consonant + **[а]** |
| **Ю** | **[йу]** | softens the consonant + **[у]** |
| **Є** | **[йе]** | softens the consonant + **[е]** |
| **Ї** | always **[йі]** | always **[йі]** |

**Ї** is not a softening letter. It is always two sounds: **[йі]**. In
**Украї́на**, read **ї** as **[йі]**.

Use three safe examples:

| Слово́ | English support | What to read |
| --- | --- | --- |
| **я́блуко** | apple | **я** starts the word: **[йа]** |
| **люди́на** | person | **ю** follows **л** and marks softness + **[у]** |
| **пі́сня** | song | **я** follows **н** and marks softness + **[а]** |

You do not need every phonetic detail yet. Look at the position of
**Я, Ю, Є, Ї**, then read the word slowly.

:::caution
Keep this beginner rule small: **Ї** is always **[йі]**. For **Я, Ю, Є**,
look at the position first, then read slowly.
:::

<!-- INJECT_ACTIVITY: act-2 -->

## Читаємо слова́

**ма́ма. та́то. вода́. ка́ша.**

Use this three-step reading routine:

1. Find the vowel sounds.
2. Split the word into syllables.
3. Read the syllables smoothly, not as separate letter names.

Try the routine with easy words:

| Слово́ | Split | English support |
| --- | --- | --- |
| **ма́ма** | 2 syllables | mother |
| **та́то** | 2 syllables | father |
| **вода́** | 2 syllables | water |
| **ка́ша** | 2 syllables | porridge |
| **ву́лиця** | 3 syllables | street |
| **столи́ця** | 3 syllables | capital |

Longer words use the same routine with more vowel sounds:

| Слово́ | Split | Beginner note |
| --- | --- | --- |
| **університе́т** | 5 syllables | read from left to right |
| **бібліоте́ка** | 5 syllables | **о** is its own vowel pulse |
| **фотогра́фія** | 5 syllables | final **я** gives the last vowel |

Names of Ukrainian cities are also good reading practice:

| Мі́сто | Split | Note |
| --- | --- | --- |
| **Ки́їв** | 2 syllables | **ї** is **[йі]** |
| **Львів** | 1 syllable | one vowel sound |
| **Оде́са** | 3 syllables | initial **О** can stand alone |
| **Дніпро́** | 2 syllables | consonant cluster, still two vowels |
| **Полта́ва** | 3 syllables | steady open syllables |

Three signs or combinations return in Module 3:

| Form | Beginner reading habit |
| --- | --- |
| **Ь** | no sound of its own; softens the previous consonant |
| **апо́строф** | keeps the next **я/ю/є/ї** separate with **й** |
| **ДЖ / ДЗ** | one joined sound, not two broken sounds |

Read **день** with soft **н**, not with an extra vowel after it. Read
**сім'я́** with a clear **й** before **я**. Read **джерело́** with joined
**дж**.

:::tip
If a word feels long, do not speed up. Find the letters for vowel sounds, make
small syllable beats, then smooth them into one word.
:::

<!-- INJECT_ACTIVITY: act-3 -->

## Пастки читання

**молоко́. день. Украї́на. джерело́.**

Use these safety checks:

| Trap | Safer Ukrainian habit |
| --- | --- |
| Reading letter by letter | Read by syllables: three beats in **молоко́** |
| Blurring unstressed **о** | Keep **о** clear every time |
| Reading **дж** as **д + ж** | Join it as one sound |
| Ignoring **ь** | Make the previous consonant soft |
| Reading **ї** as plain **і** | Read **ї** as **[йі]** |
| Treating apostrophe as decoration | Keep the following **й** sound |

Build the habit from words on this page: **день**, **ма́ма**, **молоко́**,
**Украї́на**. Do not use another language's alphabet as the shortcut.

:::note
These are reading habits, not a pronunciation exam. Slow accurate reading is a
win at A1.
:::

<!-- INJECT_ACTIVITY: act-4 -->

## Друк, зошит, перевірка

**Друк:** **ма́ма**, **молоко́**, **день**, **Ки́їв**.

**Зошит:** the same known words written by you, a teacher, or a tutor.

Recognition comes before long handwriting production. Ask a native Ukrainian
teacher or tutor to write one known word in their own hand. Your job is only to
match it to the printed word and read it aloud. Do not copy or trace a
third-party handwriting sample.

| Друк | Notebook recognition prompt |
| --- | --- |
| **ма́ма** | Which printed word matches the handwritten **ма́ма**? |
| **молоко́** | Which printed word matches the handwritten **молоко́**? |
| **день** | Which printed word has the final soft sign? |
| **Ки́їв** | Which printed word has **ї**? |

Use a short partner routine when possible. Student A points to the word.
Student B says only the number of vowel sounds. Then both students read the
word aloud. If you are alone, cover the English support first, count the vowel
sounds, and read before you check meaning.

When a word feels long, slow down:

| Mark | Meaning |
| --- | --- |
| **1** | I can find the vowel sounds. |
| **2** | I can count the syllables. |
| **3** | I can read the word aloud smoothly. |

Before you leave the lesson tab, check that you can do these things:

- explain **склад** as "syllable";
- count the vowel sounds in **молоко́**;
- count three vowel sounds in **ву́лиця**;
- say why **Ї** is always **[йі]**;
- read **я́блуко**, **люди́на**, **пі́сня**, and **день** slowly;
- keep **о** clear in **молоко́** and **столи́ця**;
- say that **дж** and **дз** are joined reading units;
- match a known printed word to a notebook version before copying it.

The workbook repeats easy words and a few longer words on purpose. Repetition
is how the alphabet becomes automatic.

## Далі

Тепер переходь до словника й вправ. You can now look at a printed Ukrainian
word, find the letters that mark vowel sounds, count the syllables, and read
the whole word more calmly.


### activities.yaml

---
inline:
  - id: act-1
    type: count-syllables
    title: Рахуй склади́
    instruction: Рахуй голосні звуки. Кожен голосни́й звук дає один склад.
    maxCount: 5
    items:
      - word: день
        correct: 1
      - word: ма́ма
        correct: 2
      - word: молоко́
        correct: 3
      - word: ву́лиця
        correct: 3
      - word: бібліоте́ка
        correct: 5
      - word: Украї́на
        correct: 4
  - id: act-2
    type: match-up
    title: Роль літер у читанні
    instruction: З'єднай лі́теру з її роллю в читанні.
    pairs:
      - left: А
        right: позначає [а]
      - left: О
        right: позначає [о]
      - left: И
        right: позначає [и]
      - left: І
        right: позначає [і]
      - left: Я на початку слова
        right: '[йа]'
      - left: Ї
        right: завжди [йі]
  - id: act-3
    type: divide-words
    title: Поділи на склади́
    instruction: Поділи кожне друковане слово на склади́.
    items:
      - word: ма́ма
        answer: ма ма
      - word: молоко́
        answer: мо ло ко
      - word: ву́лиця
        answer: ву ли ця
      - word: столи́ця
        answer: сто ли ця
      - word: люди́на
        answer: лю ди на
      - word: бібліоте́ка
        answer: бі блі о те ка
  - id: act-4
    type: error-correction
    title: Пастки читання
    instruction: Обери безпечнішу українську читацьку звичку.
    items:
      - sentence: Не читай молоко́ як малоко.
        error: малоко
        correction: молоко
        options:
          - молоко
          - нечітке о
        explanation: Українське о залишається чистим; читай молоко́ у три відкриті удари.
      - sentence: Не читай дж у слові джерело́ як д плюс ж.
        error: д плюс ж
        correction: один злитий звук
        options:
          - один злитий звук
          - д плюс ж
        explanation: ДЖ читаємо як один злитий звук у словах як джерело́.
      - sentence: Украї́на — не читай ї як просте і.
        error: просте і
        correction: '[йі]'
        options:
          - '[йі]'
          - '[і]'
        explanation: Ї завжди читаємо як [йі].
      - sentence: День — не треба додати голосний після нь.
        error: додати голосний
        correction: пом'якшити н і зупинитися
        options:
          - пом'якшити н і зупинитися
          - додати і після нь
        explanation: Ь не має власного звука; він м'якшить попередній при́голосний.
workbook:
  - type: group-sort
    title: Один, два чи три склади́
    instruction: Розподіли слова за кількістю складів.
    groups:
      - label: Один склад
        items:
          - день
          - Львів
      - label: Два склади́
        items:
          - ма́ма
          - та́то
          - Ки́їв
      - label: Три склади́
        items:
          - молоко́
          - ву́лиця
          - столи́ця
  - type: odd-one-out
    title: Зайве за кількістю складів
    instruction: Обери слово, яке має іншу кількість складів.
    items:
      - words:
          - ма́ма
          - та́то
          - вода́
          - день
        answer: день
        explanation: День має один склад; інші слова мають два.
      - words:
          - молоко́
          - ву́лиця
          - столи́ця
          - Ки́їв
        answer: Ки́їв
        explanation: Ки́їв має два склади; інші слова мають три.
      - words:
          - день
          - Львів
          - ма́ма
          - так
        answer: ма́ма
        explanation: Ма́ма має два склади; інші слова мають один.
      - words:
          - бібліоте́ка
          - університе́т
          - фотогра́фія
          - ка́ша
        answer: ка́ша
        explanation: Ка́ша має два склади; інші слова мають п'ять.
  - type: true-false
    title: Факти про читання
    instruction: Обери правда чи неправда.
    items:
      - statement: Кожен український склад має голосни́й звук.
        correct: true
        explanation: Голосни́й звук — центр складу.
      - statement: Ї іноді м'якшить попередній при́голосний.
        correct: false
        explanation: Ї завжди читаємо як [йі].
      - statement: У молоко́ звук о залишається чистим.
        correct: true
        explanation: Не перетворюй о на нечіткий голосни́й.
      - statement: ДЖ і ДЗ читаємо як злиті одиниці.
        correct: true
        explanation: ДЖ і ДЗ читаємо як злиті одиниці.
  - type: match-up
    title: Друк і зошит
    instruction: З'єднай друковане слово з підказкою в зо́шиті.
    pairs:
      - left: 'друк: ма́ма'
        right: 'зошит: ма́ма'
      - left: 'друк: молоко́'
        right: 'зошит: молоко́'
      - left: 'друк: день'
        right: 'зошит: слово з кінцевим ь'
      - left: 'друк: Ки́їв'
        right: 'зошит: слово з ї'
      - left: 'друк: ву́лиця'
        right: 'зошит: трискладове слово про місто'
  - type: watch-and-repeat
    title: Повтор голосних
    instruction: Подивися огляд абетки ще раз, потім повтори прості голосні.
    items:
      - letter: А
        sound: '[а]'
        word: ма́ма
        video: https://www.youtube.com/watch?v=ksXIXj7CXwc
      - letter: О
        sound: '[о]'
        word: молоко́
        video: https://www.youtube.com/watch?v=ksXIXj7CXwc
      - letter: У
        sound: '[у]'
        word: ву́лиця
        video: https://www.youtube.com/watch?v=ksXIXj7CXwc
      - letter: И
        sound: '[и]'
        word: ми
        video: https://www.youtube.com/watch?v=ksXIXj7CXwc
      - letter: І
        sound: '[і]'
        word: пі́сня
        video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - id: act-5
    type: quiz
    title: Мініпереві́рка читання
    instruction: Обери правильну відповідь.
    items:
      - prompt: Склад — що це?
        options:
          - text: лі́тера
            correct: false
          - text: syllable
            correct: true
          - text: greeting
            correct: false
        explanation: Склад — це частина слова з голосним звуком.
      - prompt: Молоко́ — скільки складів?
        options:
          - text: '2'
            correct: false
          - text: '3'
            correct: true
          - text: '1'
            correct: false
        explanation: Молоко́ має три голосні звуки й три склади́.
      - prompt: Яка літера завжди [йі]?
        options:
          - text: І
            correct: false
          - text: И
            correct: false
          - text: Ї
            correct: true
        explanation: Ї завжди читаємо як [йі].


### vocabulary.yaml

- lemma: склад
  translation: syllable
  pos: noun
  usage: У сло́ві ма́ма два склади́.
- lemma: голосни́й звук
  translation: vowel sound
  pos: noun phrase
  usage: А - голосни́й звук.
- lemma: при́голосний звук
  translation: consonant sound
  pos: noun phrase
  usage: М - при́голосний звук.
- lemma: чита́ти
  translation: to read
  pos: verb
  usage: Я чита́ю сло́во.
- lemma: писа́ти
  translation: to write
  pos: verb
  usage: Я пишу́ лі́теру.
- lemma: ма́ма
  translation: mother
  pos: noun
  usage: Ма́ма.
- lemma: та́то
  translation: father
  pos: noun
  usage: Та́то.
- lemma: молоко́
  translation: milk
  pos: noun
  usage: Молоко́.
- lemma: я́блуко
  translation: apple
  pos: noun
  usage: Я́блуко.
- lemma: люди́на
  translation: person
  pos: noun
  usage: Люди́на.
- lemma: ву́лиця
  translation: street
  pos: noun
  usage: Ву́лиця.
- lemma: столи́ця
  translation: capital
  pos: noun
  usage: Ки́їв - столи́ця Украї́ни.
- lemma: ка́ша
  translation: porridge
  pos: noun
  usage: Ка́ша.
- lemma: пі́сня
  translation: song
  pos: noun
  usage: Пі́сня.
- lemma: день
  translation: day
  pos: noun
  usage: День.
- lemma: о́сінь
  translation: autumn
  pos: noun
  usage: О́сінь.
- lemma: ба́тько
  translation: father
  pos: noun
  usage: Ба́тько.
- lemma: вчи́тель
  translation: teacher
  pos: noun
  usage: Вчи́тель.
- lemma: джерело́
  translation: source / spring
  pos: noun
  usage: Джерело́.
- lemma: дзе́ркало
  translation: mirror
  pos: noun
  usage: Дзе́ркало.
- lemma: абе́тка
  translation: alphabet
  pos: noun
  usage: Украї́нська абе́тка.
- lemma: м'яки́й знак
  translation: soft sign
  pos: noun phrase
  usage: Ь - м'яки́й знак.
- lemma: апо́строф
  translation: apostrophe
  pos: noun
  usage: У сло́ві «сім'я́» є апо́строф.
- lemma: Ки́їв
  translation: Kyiv
  pos: proper noun
  usage: Ки́їв - столи́ця Украї́ни.
- lemma: Украї́на
  translation: Ukraine
  pos: proper noun
  usage: Украї́на.
- lemma: так
  translation: yes / like this
  pos: adverb
  usage: Так.
- lemma: ні
  translation: "no"
  pos: particle
  usage: Ні.


### resources.yaml

- title: Большакова, буквар 1 клас, p. 25
  role: textbook
  source_ref: Большакова, буквар 1 клас, p. 25
  notes: 'Plan reference: syllable rule; every syllable has a vowel sound.'
- title: Большакова, буквар 1 клас, p. 29
  role: textbook
  source_ref: Большакова, буквар 1 клас, p. 29
  notes: 'Plan reference: sound analysis routine for Ukrainian words.'
- title: Захарійчук 1 клас (НУШ 2025), p. 13-15
  role: textbook
  source_ref: Захарійчук 1 клас (НУШ 2025), p. 13-15
  notes: 'Plan reference: symbols for vowel, hard consonant, and soft consonant sounds.'
- title: Вашуленко, Українська мова 2 клас, p. 23-27
  role: textbook
  source_ref: Вашуленко, Українська мова 2 клас, p. 23-27
  notes: 'Plan reference: transfer, stress, and iotated-vowel reading context.'
- title: Кравцова, Українська мова 2 клас, p. 13
  role: textbook
  source_ref: Кравцова, Українська мова 2 клас, p. 13
  notes: 'Plan reference: hand-under-chin syllable counting check.'
- title: Anna Ohoiko — Ukrainian alphabet overview
  role: youtube
  url: https://www.youtube.com/watch?v=ksXIXj7CXwc
  channel: Ukrainian Lessons
  notes: 'Supplemental listening support for the vowel reading pass.'


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
