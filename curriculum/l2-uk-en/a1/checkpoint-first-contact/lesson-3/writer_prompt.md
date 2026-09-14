# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: checkpoint-first-contact.
Your current published unit: lesson 3.

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

TOTAL_TARGET: '8'
INLINE_MIN: '3'
INLINE_MAX: '5'
WORKBOOK_MIN: '5'
WORKBOOK_MAX: '8'
ITEMS_MIN: '10'
VOCAB_COUNT_TARGET: '15'
INLINE_ALLOWED_TYPES: match-up, quiz, fill-in, true-false, group-sort
WORKBOOK_ALLOWED_TYPES: fill-in, match-up, group-sort, unjumble, quiz, true-false,
  observe, phrase-table, odd-one-out, anagram
INLINE_PRIORITY_TYPES: match-up, fill-in, quiz
WORKBOOK_PRIORITY_TYPES: fill-in, match-up, group-sort, unjumble, anagram
ACTIVITY_COUNT_TARGET: '8'
ACTIVITY_MIN: '0'
ACTIVITY_MAX: '12'
ALLOWED_ACTIVITY_TYPES: match-up, quiz, fill-in, true-false, group-sort, unjumble,
  observe, phrase-table, odd-one-out, anagram
FORBIDDEN_ACTIVITY_TYPES: image-to-letter, letter-grid, watch-and-repeat, divide-words,
  count-syllables, pick-syllables, classify, cloze, error-correction, mark-the-words,
  translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent,
  etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis,
  dialect-comparison, transcription, highlight-morphemes, grammar-identify, select
REQUIRED_TYPES: ''
PRIORITY_TYPES: match-up, fill-in, quiz


## Learner state before this lesson

(This is the first module — no prior learner knowledge.)
Previously introduced in this module: ["ім'я", "прізвище", "знайомство", "познайомитися", "професія", "походження", "Вітаю", "Дуже приємно", "Мені теж", "Мене звати", "Як тебе звати?", "Звідки ти?", "Я з", "Мені 20 років", "У мене є", "студент", "студентка", "сім'я", "національність", "У тебе є", "вчителька", "інженер", "українка", "канадка", "родина", "мама", "тато", "брат", "сестра", "мій", "моя", "моє", "мої", "його", "її"]

## Deterministic lessons.yaml (read-only)

lessons:
- n: 1
  title: Граматика
  sections:
  - Що ми знаємо?
  - Читання
  - Граматика
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
  title: Діалог
  sections:
  - Діалог
  - Слухай, зошит, підсумок
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
  lesson: 1
- placement: inline
  index: 4
  new_id: act-5
  lesson: 2
- placement: inline
  index: 5
  new_id: act-6
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
  lesson: 3
items_min_exempt:
- id: act-6
  reason: 4-item original activity preserved from baseline
- id: act-w3
  reason: 5-item original activity preserved from baseline
proper_names: []


## Original plan (read-only)

module: a1-007
level: A1
sequence: 7
slug: checkpoint-first-contact
version: 1.2.2
lifecycle: locked
reviewed_at: '2026-04-23T09:43:24Z'
reviewed_by: claude-opus-4-7-xhigh-scale-batch-1
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md,
  following the at-the-cafe (#1412 / PR #1415) template. Wiki-side report: wiki/.reviews/pedagogy/a1/checkpoint-first-contact-review-LOCKED.md
  (5-dim scores 9/9/9/9/9). Plan-side findings addressed: (1) pragmatic register mismatch
  — `setting` reframed from formal conference to peer- to-peer language-meetup so
  that ти-register and family-topic content cohere with the monologue examples; (2)
  integration vocabulary added (професія, національність, знайомство, походження,
  Вітаю, Дуже приємно, Мені теж) to hook wiki Step 6; (3) new fill-in activity drilling
  the wiki "Типові помилки L2" Surzhyk / calque pairs (7 items, A1.1-specific); (4)
  back-reference to locked wiki added to references; (5) author-note warning against
  Surzhyk forms (папа/фамілія/Я є студент/Я маю N років) in Діалог section.'
title: 'Підсумок: Перший контакт'
subtitle: Чи вмієте ви читати, вітатися та розповідати про себе?
focus: review
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
word_target: 1200
objectives:
- Впевнено читати українською кирилицею
- Підтримувати повноцінну розмову під час знайомства (привітання → знайомство → родина)
- Самостійно оцінювати знання звуків, літер, привітань та фраз для знайомства
- Поєднувати всі навички рівня A1.1 у зв'язному мовленні
- Виконувати checkpoint як повторення модулів №1–6 без нової граматики та без нового
  обов'язкового словника
dialogue_situations:
- setting: 'Перший день мовних курсів — двоє студентів знайомляться під час перерви:
    розповідають про себе, родину і майбутню професію (ти-регістр, рівноправний студентський
    контекст).'
  speakers:
  - Богдан (студент із Дніпра, майбутній інженер)
  - Соломія (студентка з Тернополя, майбутня вчителька)
  motivation: 'Закріплення: ім''я, прізвище, походження, професія, родина — повна
    розповідь про себе у ти-регістрі. УВАГА до автора: рівноправний студентський контекст
    обрано навмисно — він природно мотивує і ти-регістр, і розмову про родину (на
    конференції професіоналів родинна лексика не є доречною темою знайомства).'
content_outline:
- section: Що ми знаємо?
  words: 200
  points:
  - 'Самоперевірка за темами модулів №1–6: Чи вмієте ви прочитати будь-яке українське
    слово? (модулі №1–2) Чи розумієте ви функцію м''якого знака (Ь) та апострофа?
    (модуль №3) Чи можете ви правильно ставити наголос? (модуль №4) Чи вмієте ви розповідати
    про себе? (модуль №5) Чи можете ви розповісти про свою родину? (модуль №6)'
- section: Читання
  words: 250
  points:
  - 'Короткий український текст (8-10 речень) з використанням ТІЛЬКИ лексики з модулів
    №1–6. Жодних нових слів. Учень читає вголос. Зміст: Людина розповідає про себе,
    описує родину, згадує професії, каже, звідки вона родом.'
  - 'Оглядовий текст має бути проектно-оригінальним і спиратися лише на вже вивчені
    модулі №1–6: «Я і моя сім''я».'
- section: Граматика
  words: 200
  points:
  - 'Ключові конструкції з A1.1: 1. Це + іменник (ідентифікація) 2. Підмет — Іменник
    (без дієслова "бути"): Я — студент 3. У мене є + іменник (приналежність) 4. Як
    тебе/вас звати? (запитання імені) 5. Мій/моя/моє + іменник (присвійні займенники
    з урахуванням роду) 6. Звідки ти? — Я з... (походження як сталий вираз)'
- section: Діалог
  words: 400
  points:
  - 'Повне знайомство — комплексний діалог, що поєднує ВСЕ з рівня A1.1. Ситуація:
    зустріч із новою людиною у рівноправному студентському контексті (мовні курси,
    студентське орієнтування). Повний цикл: привітання → ім''я → прізвище → походження
    → професія → родина → прощання. Якщо учень розуміє та може відтворити цей діалог,
    рівень A1.1 пройдено.'
  - 'Зв''язний монолог: власна розповідь учня про себе. Привіт! Мене звати [ім''я].
    Моє прізвище [прізвище]. Я з [країна]. Я [національність]. Я — [професія]. Моя
    мама — [професія]. Мій тато — [професія]. У мене є [родина]. Дуже приємно познайомитися!
    Це випускна промова рівня A1.1.'
  - 'УВАГА до автора (типові помилки L2 для A1.1 — див. вікі-статтю, розділ «Типові
    помилки L2»): використовуйте `тато` як початковий нейтральний варіант для активного
    A1-вжитку, але не подавайте `папа` як неукраїнське слово; НЕ використовуйте `фамілія`
    в офіційному значенні прізвища (стандартне слово в анкетах: `прізвище`); НЕ використовуйте
    кальку `Моє ім''я є Іван` (нормативне: `Мене звати Іван`); НЕ використовуйте форсоване
    `Я є студент` (нормативне: `Я студент`); НЕ використовуйте кальку `Я маю 25 років`
    (нормативне: `Мені 25 років`); НЕ використовуйте російські форми для базових вітань
    і прощань, коли вже відпрацьовано `Добрий день` / `До побачення`. Тримайте ти-регістр
    до кінця діалогу — НЕ змішуйте з Ви.'
- section: Підсумок
  words: 150
  points:
  - 'Фінальні запитання для самоперевірки: Скільки літер/звуків в українській мові?
    Привітайтеся формально та неформально. Розкажіть про себе у 5 реченнях. Назвіть
    членів своєї родини, використовуючи присвійні займенники.'
vocabulary_hints:
  author_note: 'Checkpoint vocabulary policy: this module recycles modules №1–6. There
    are no new required words. Recommended labels below are passive review or integration
    supports only and must not become a new production quota.'
  required:
  - All vocabulary from №1–6 is recycled — no new required words
  recommended:
  - ім'я (first name)
  - прізвище (surname — standard; NOT the Surzhyk `фамілія`)
  - знайомство (acquaintance / introduction)
  - професія (profession / occupation)
  - національність (nationality / ethnicity)
  - походження (origin)
  - Вітаю (hello / greeting — neutral; also "congratulations" in other contexts)
  - Дуже приємно (very nice to meet you — greeting closure)
  - Мені теж (me too — reciprocal acknowledgement after Дуже приємно)
  - тато (dad — beginner default; do not teach other attested family forms as nonexistent
    Ukrainian)
activity_hints:
- type: quiz
  focus: 'Комплексне повторення: звуки, літери, привітання, родина'
  items: 12
- type: fill-in
  focus: Доповнити повний монолог-розповідь про себе
  items: 8
- type: match-up
  focus: З'єднати запитання з відповідями (Як звати? → Мене звати...)
  items: 8
- type: fill-in
  focus: Типові помилки A1.1 — оберіть нормативну форму (див. wiki "Типові помилки
    L2")
  items:
  - '{Добрий день|Здрастуйте}! Мене звати Оксана.'
  - '{Мене звати Іван|Моє ім''я є Іван}.'
  - Я {студент|є студент}.
  - '{Мені 25 років|Я маю 25 років}.'
  - Як твоє {прізвище|фамілія}?
  - — Дякую! — Будь ласка. — {До побачення|Пока}!
connects_to:
- a1-008 (Речі мають рід)
prerequisites:
- a1-006 (Моя родина)
grammar:
- 'Повторення: Це + іменник, Підмет — Іменник, У мене є, присвійні займенники'
- Нової граматики немає — лише закріплення
register: розмовний
references:
- title: 'Wiki: pedagogy/a1/checkpoint-first-contact (LOCKED 2026-04-23)'
  notes: Authoritative pedagogical brief — see Крок 6 (чекпойнт-інтеграція A1.1) and
    "Типові помилки L2" (A1.1 self-introduction Surzhyk / calque table). The Діалог
    and Підсумок sections in this plan are hooks into those wiki sections.
changelog:
- version: 1.2.1
  date: '2026-04-23'
  changes:
  - 'Address AC-3 cross-agent (Codex) adversarial-review findings: BLOCKER — removed
    6 Latin-in-Ukrainian-prose tokens flagged as #1392 D1/D7 drift (`peer-to-peer`
    ×3 → `рівноправний студентський контекст`; `student from Dnipro` / `student from
    Ternopil` → `студент із Дніпра` / `студентка з Тернополя`; legacy external-lesson
    shorthand → project-native wording). MEDIUM — disambiguated at-the-cafe template
    provenance (#1412 issue / PR #1415). MEDIUM — LOCKED review now contains explicit
    #1392 D1–D7 systemic-defect scan. NIT — residual non-blockers in LOCKED review
    documents why the 8th wiki Surzhyk row (`Я із Росії`) is intentionally not mirrored
    in the drill activity.'
- version: 1.2.0
  date: '2026-04-23'
  changes:
  - 'Review-and-lock pass (scale batch 1, per docs/best-practices/wiki-plan-review-and-lock.md,
    #1412 at-the-cafe template — landed as PR #1415).'
  - Reframed dialogue_situations[0].setting from formal conference (Ви-register, professional
    first-meeting) to peer-to-peer language-meetup (ти-register, student context)
    — resolves pragmatic mismatch between setting and the ти-register Привіт!-monologue
    in Діалог section, and makes family-topic content situationally coherent.
  - Added integration vocabulary_hints.recommended (знайомство, професія, національність,
    походження, Вітаю, Дуже приємно, Мені теж, тато) to hook locked wiki Step 6.
  - Added new fill-in activity "Типові помилки A1.1" mirroring locked wiki "Типові
    помилки L2" table (7 A1.1-specific Surzhyk / calque pairs).
  - Added author-note in Діалог section listing 6 forbidden Surzhyk / calque forms
    + ти-register consistency warning.
  - Added back-reference to locked wiki in references.
  - Added lifecycle markers (lifecycle / reviewed_at / reviewed_by / review_notes)
    per docs/best-practices/wiki-plan-review-and-lock.md.
- version: 1.2.2
  date: '2026-06-05'
  changes:
  - 'Retrofit plan repair for #2713: made checkpoint vocabulary policy explicit as
    M1-M6 recycling, not a new required-word unit.'
  - 'Softened inherited family-register guidance: `тато` remains the beginner default,
    but `папа` is not framed as nonexistent Ukrainian.'


## Existing module artifacts (read-only)

### module.md

# Підсумок: перший контакт

**Приві́т! Мене́ зва́ти Богдан. Я з Дніпра́.** — Hi! My name is Bohdan.
I am from Dnipro.

This checkpoint is a working rehearsal for the first six modules. Nothing here
needs a new grammar rule. You are checking whether the first-contact pieces can
move together: read Ukrainian script, greet someone, give your name, say where
you are from, name a simple role or profession, and add one family line.

By the end, you can:

- read short Ukrainian words aloud without using Russian as a bridge;
- choose the safe greeting and farewell phrases: **Добрий день**, **Привіт**,
  **До побачення**, and **Бувай**;
- introduce yourself with **Мене звати...**, not a word-for-word English
  sentence;
- say **Я студент / Я студентка** without forcing **є** into the line;
- answer **Звідки ти?** with **Я з...**;
- use **Мені 20 років** for age;
- add family with **У мене є...** and **мій / моя / моє / мої**;
- recognize direct address such as **Привіт, Богдане!** and **Соломіє!** as
  the vocative signal.

The checkpoint keeps a Ukrainian-first frame. Ukrainian letters, stress, and
soft signs are explained as Ukrainian habits. The page never asks you to compare
them to Russian letters or Russian pronunciation. Non-target greetings and
calques appear only as wrong choices inside correction practice.

The roadmap behind this checkpoint has six learner steps: sound and alphabet
control, reading words, special signs, stress, self-introduction, and one
family line. Use that order as a checklist, not as new grammar to memorize.

## Що ми знаємо?

<!-- INJECT_ACTIVITY: act-1 -->

You now have six small toolkits.

| Опора | Що ти вже робиш |
| --- | --- |
| **Звуки́ й лі́тери** | recognize Ukrainian letters, vowels, **ґ**, **ї**, **є**, **и**, **і**, **ь**, and the apostrophe |
| **Чита́ння** | read short words and syllables slowly but confidently |
| **Спеціа́льні зна́ки** | hear that **сім'я́**, **бур'я́н**, and **день** are not spelled decoration |
| **На́голос і мело́дія** | mark the stressed syllable and use a rising yes/no question melody |
| **Хто я?** | say your name, origin, nationality, profession, and age |
| **Моя́ сім'я́** | name close family members and use **У ме́не є...** |

A checkpoint is not a memory trick. It is a task: can you meet one new person
and keep the exchange moving? Use short sentences. Use the phrases exactly. If
you hesitate, return to the sentence frame instead of translating from English.

Keep these blocks as whole blocks:

| Український блок | English support |
| --- | --- |
| **Як тебе́ зва́ти?** | What is your name? |
| **Мене́ зва́ти...** | My name is... |
| **Ду́же приє́мно.** | Nice to meet you. |
| **Мені́ теж.** | Me too. |
| **Зві́дки ти?** | Where are you from? |
| **Я з...** | I am from... |
| **Я студе́нт / студе́нтка.** | I am a student. |
| **Мені́ 20 ро́ків.** | I am 20 years old. |
| **У ме́не є...** | I have... |

Formal address still exists, but this checkpoint uses a peer language-course
setting, so the main dialogue stays in **ти**. Do not mix **ти** and **Ви** in
the same first-contact exchange unless the situation changes.

:::tip
When a line feels hard, reduce it to one phrase: **Мене звати...**, **Я з...**,
**Я студент / студентка**, or **У мене є...**. The checkpoint rewards reliable
phrases, not long translated sentences.
:::

<!-- INJECT_ACTIVITY: act-2 -->

## Читання

Read this text aloud. Use the letter and stress habits from the script modules.
The content is only the A1.1 world: name, place, role, family, and a simple
closing.

```text
Приві́т! Мене́ зва́ти Марко́.
Моє́ прі́звище Ковале́нко.
Я з Ки́єва, але́ за́раз я студе́нт у Льво́ві.
Мені́ 20 ро́ків.
Моя́ профе́сія за́раз — студе́нт.
У ме́не є ма́ма, та́то і сестра́.
Моя́ ма́ма — вчи́телька, а мій та́то — інжене́р.
Мою́ сестру́ зва́ти О́ля.
Ду́же приє́мно познайо́митися!
```

English support after the Ukrainian text:

| Українська | English support |
| --- | --- |
| **Моє́ прі́звище Ковале́нко.** | My surname is Kovalenko. |
| **Я з Ки́єва.** | I am from Kyiv. |
| **Мені́ 20 ро́ків.** | I am 20 years old. |
| **У ме́не є ма́ма, та́то і сестра́.** | I have a mom, dad, and sister. |
| **Ду́же приє́мно познайо́митися!** | Very nice to meet you! |

Now check the reading decisions.

- In **прізвище**, keep **и** and **і** separate.
- In **сім'я**, the apostrophe tells you to keep the **м** and **я** apart.
- In **Київ**, do not flatten **ї**.
- In **вчителька**, read slowly; the word is useful, but the profession table
  is still small.
- In direct address, **Богдан** becomes **Богдане** and **Соломія** becomes
  **Соломіє**. At A1, recognize the signal and copy safe examples. Do not turn
  this checkpoint into a full case table.

Alphabet order is also a learner tool. If you look up **прізвище** in a
dictionary, the first letter is not enough; after **п**, keep comparing the next
letters. That habit matters more than speed.

:::tip
Read the text one line at a time. A checkpoint pass is steady pronunciation and
safe phrases, not a perfect performance at full speed.
:::

<!-- INJECT_ACTIVITY: act-3 -->

## Граматика

The grammar checkpoint has six safe patterns. They are small, but they cover a
real first meeting.

| Опора | Безпечний рядок | Не треба зараз |
| --- | --- | --- |
| **Це + noun** | **Це Богдан. Це моя́ сестра́.** | Do not overbuild the sentence. |
| Identity without **є** | **Я студе́нт. Вона́ лі́карка.** | Do not say **Я є студент** in this A1 sentence. |
| Name | **Мене́ зва́ти Соломі́я.** | Do not build **Моє́ ім'я́ є...** from English. |
| Origin | **Я з Кана́ди. Я зі Льво́ва.** | Use **з / зі** as the learned phrase. |
| Age | **Мені́ 20 ро́ків.** | Do not use the English "have years" shape. |
| Possession | **У ме́не є брат.** | Learn the whole phrase, not a verb for "have." |

For family and identity, the owned word chooses the possessive form:

| Word | My line |
| --- | --- |
| **брат** | **мій брат** |
| **мама** | **моя мама** |
| **місто** | **моє місто** |
| **батьки** | **мої батьки** |

The gender habit is not only a family topic. A word should be stored with its
gender when that helps you later: **студент** is masculine, **студентка** is
feminine, and **прізвище** is neuter. You do not need a full case system today,
but you do need the habit of learning a noun with its form cues.

The safe social vocabulary also stays native Ukrainian. Use **прізвище** for
surname in official-style lines, not colloquial **фамілія**. Use **тато** or
**батько** for father in this course context; keep **папа** as recognition, not
the active A1 default. Use **Добрий день** or **Вітаю** when you need a neutral hello, and
**До побачення** for goodbye.

<!-- INJECT_ACTIVITY: act-4 -->

## Діалог

This is the full first-contact task. Read it once for meaning, then read it
again aloud. The setting is a break on the first day of Ukrainian courses, so
both people use **ти**.

```text
Богда́н: Приві́т! Мене́ зва́ти Богда́н.
Соломі́я: Приві́т, Богда́не! Мене́ зва́ти Соломі́я.
Богда́н: Ду́же приє́мно, Соломі́є.
Соломі́я: Мені́ теж. Зві́дки ти?
Богда́н: Я з Дніпра́. А ти?
Соломі́я: Я з Терно́поля.
Богда́н: Ти студе́нтка?
Соломі́я: Так, я студе́нтка. Моя́ майбу́тня профе́сія — вчи́телька.
Богда́н: Кла́сно. Я студе́нт, майбу́тній інжене́р.
Соломі́я: У те́бе є брати́ чи се́стри?
Богда́н: Так, у ме́не є сестра́. Її́ зва́ти Іри́на.
Соломі́я: У ме́не є брат. Його́ зва́ти Наза́р.
Богда́н: Ду́же приє́мно познайо́митися.
Соломі́я: Мені́ теж. До поба́чення!
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Приві́т, Богда́не!** | Hi, Bohdan! |
| **Ду́же приє́мно, Соломі́є.** | Very nice to meet you, Solomiia. |
| **Я з Дніпра́.** | I am from Dnipro. |
| **У те́бе є брати́ чи се́стри?** | Do you have brothers or sisters? |
| **До поба́чення!** | Goodbye! |

Use this as your graduation speech for A1.1:

```text
Приві́т! Мене́ зва́ти Оле́на.
Моє́ прі́звище Ме́льник.
Я з Кана́ди. Я кана́дка.
Я студе́нтка. Моя́ майбу́тня профе́сія — лі́карка.
Моя́ ма́ма — вчи́телька, а мій та́то — інжене́р.
У ме́не є одна́ сестра́.
Ду́же приє́мно познайо́митися!
```

If you want a shorter answer, keep five sentences: name, origin, role, one
family line, and closing. That is enough for the checkpoint.

:::tip
Your five-sentence answer can stay simple. If it has **Мене звати...**,
**Я з...**, one identity line, one family line, and a polite closing, it is doing
the job.
:::

<!-- INJECT_ACTIVITY: act-5 -->

### Перше знайомство онлайн

A modern first contact may happen in a course chat. The same etiquette applies:
start with a greeting, name yourself, ask one clear question, and close
politely. Do not hide behind emoji-only messages when the task is language
practice.

```text
Лі́на: Приві́т! Мене́ зва́ти Лі́на. Я з Оде́си. А тебе́?
Том: Приві́т, Лі́но! Мене́ зва́ти Том. Я з Кана́ди.
Лі́на: Ду́же приє́мно!
Том: Мені́ теж.
```

English support after the Ukrainian chat:

| Українська | English support |
| --- | --- |
| **А тебе́?** | And you? |
| **Приві́т, Лі́но!** | Hi, Lina! |
| **Мені́ теж.** | Me too. |

This online task also reviews the borrowed-word habit from the wiki brief:
modern Ukrainian can use international words, but your core first-contact
grammar should stay Ukrainian. In a course chat, still say **Мене звати...**,
**Я з...**, and **До побачення**.

<!-- INJECT_ACTIVITY: act-6 -->

## Слу́хай, зошит, підсумок

For lawful listening, use Ukrainian Lessons Podcast Episode 10 as listen-only
review support. Listen for short phrases you already know, repeat them, and
return to this page. Do not copy or transcribe paid material.

For handwriting recognition, ask a teacher, tutor, or classmate to write an
original five-line card with **ім'я́**, **прі́звище**, **Кана́да**,
**сестра́**, and **До поба́чення**. First compare the notebook card with the
printed model; then write your own final card.

## Підсумок

Use this final self-check before you move on.

1. Read the short text aloud without stopping at **ї**, **є**, **и**, **і**,
   **ь**, or the apostrophe.
2. Say how many letters and sounds Ukrainian has: **33 літери, 38 звуків**.
3. Greet a peer informally and a teacher formally.
4. Ask one person **Як тебе звати?**
5. Say your name with **Мене звати...**
6. Say where you are from with **Я з...**
7. Say one role or profession without **є**.
8. Say your age with **Мені ... років**.
9. Add one family sentence with **У мене є...**
10. Choose **мій / моя / моє / мої** for one family word.
11. Close with **Дуже приємно** and **До побачення**.

Your final model can be simple:

```text
До́брий день! Мене́ зва́ти Алекс.
Я з Кана́ди. Я студе́нт.
Мені́ 20 ро́ків.
У ме́не є брат.
Ду́же приє́мно познайо́митися!
```

Use the workbook for extra practice: quick translation, vocabulary mapping,
and digital chat etiquette. Passing the workbook means the A1.1 first-contact
spine is ready for the next module.


### activities.yaml

inline:
  - id: act-1
    type: quiz
    title: Готовність до знайомства
    instruction: Обери безпечний український рядок для ситуації.
    items:
      - prompt: Ти вітаєш ровесника на початку заняття.
        options:
          - text: Привіт!
            correct: true
          - text: До побачення!
            correct: false
          - text: Мені теж.
            correct: false
        explanation: Привіт — неформальне привітання для ровесника.
      - prompt: Ти нейтрально вітаєш викладача або адміністратора.
        options:
          - text: Добрий день!
            correct: true
          - text: Бувай!
            correct: false
          - text: Мене звати!
            correct: false
        explanation: Добрий день — безпечне нейтральне формальне привітання.
      - prompt: Ти називаєш своє ім'я.
        options:
          - text: Мене звати Олена.
            correct: true
          - text: Моє ім'я є Олена.
            correct: false
          - text: Я звати Олена.
            correct: false
        explanation: Мене звати... — головний блок для імені.
      - prompt: Ти кажеш, що ти студент.
        options:
          - text: Я студент.
            correct: true
          - text: Я є студент.
            correct: false
          - text: Мене студент.
            correct: false
        explanation: У такому реченні українська зазвичай не додає є.
      - prompt: Ти кажеш свій вік.
        options:
          - text: Мені 20 років.
            correct: true
          - text: Я маю 20 років.
            correct: false
          - text: Я 20 роки.
            correct: false
        explanation: Вік подаємо блоком Мені ... років.
      - prompt: Скільки літер в українській абетці?
        options:
          - text: '33'
            correct: true
          - text: '38'
            correct: false
          - text: '32'
            correct: false
        explanation: Українська абетка має 33 літери.
      - prompt: Скільки звуків в українській мові?
        options:
          - text: '38'
            correct: true
          - text: '33'
            correct: false
          - text: '10'
            correct: false
        explanation: У базовому підрахунку курсу українська має 38 звуків.
      - prompt: Що робить м'який знак у слові день?
        options:
          - text: Пом'якшує попередній приголосний.
            correct: true
          - text: Позначає окремий голосний звук.
            correct: false
          - text: Замінює апостроф.
            correct: false
        explanation: Ь не має власного звука; він пом'якшує попередній приголосний.
      - prompt: Яке написання з апострофом правильне?
        options:
          - text: сім'я
            correct: true
          - text: сімя
            correct: false
          - text: сімья
            correct: false
        explanation: Вивчений родинний приклад пишемо сім'я.
      - prompt: Де позначено наголос?
        options:
          - text: Приві́т
            correct: true
          - text: Привіт
            correct: false
          - text: Прівіт
            correct: false
        explanation: Позначка над голосною показує наголошений склад.
      - prompt: Ти додаєш одну родинну фразу.
        options:
          - text: У мене є мама і тато.
            correct: true
          - text: Мене є мама і тато.
            correct: false
          - text: Я звати мама і тато.
            correct: false
        explanation: У мене є... — безпечний блок для родини.
      - prompt: Ти ввічливо завершуєш перше знайомство.
        options:
          - text: Дуже приємно. До побачення!
            correct: true
          - text: Дуже прізвище. Привіт!
            correct: false
          - text: Звідки ти? Мені теж!
            correct: false
        explanation: Дуже приємно і До побачення завершують розмову.
  - id: act-2
    type: match-up
    title: Питання і відповіді
    instruction: З'єднай питання з природною відповіддю.
    pairs:
      - left: Як тебе звати?
        right: Мене звати Богдан.
      - left: Звідки ти?
        right: Я з Дніпра.
      - left: Ти студентка?
        right: Так, я студентка.
      - left: У тебе є брат?
        right: Так, у мене є брат.
      - left: Як її звати?
        right: Її звати Ірина.
      - left: Це твоя мама?
        right: Так, це моя мама.
      - left: Скільки тобі років?
        right: Мені 20 років.
      - left: Дуже приємно.
        right: Мені теж.
  - id: act-3
    type: fill-in
    title: Доповни текст
    instruction: Обери пропущене слово або блок у самопрезентації.
    items:
      - sentence: Привіт! ___ звати Марко.
        answer: Мене
        options:
          - Мене
          - Моє
          - Мій
        explanation: Мене звати... — безпечний блок для імені.
      - sentence: Моє ___ Коваленко.
        answer: прізвище
        options:
          - прізвище
          - фамілія
          - професія
        explanation: Прізвище — стандартне українське слово для родового імені.
      - sentence: Я ___ Києва.
        answer: з
        options:
          - з
          - у
          - це
        explanation: Я з... дає походження.
      - sentence: Я ___.
        answer: студент
        options:
          - студент
          - є студент
          - мене студент
        explanation: Речення A1 про ідентичність не потребує є.
      - sentence: ___ 20 років.
        answer: Мені
        options:
          - Мені
          - Я маю
          - Мене
        explanation: Вік подаємо блоком Мені ... років.
      - sentence: У мене ___ сестра.
        answer: є
        options:
          - є
          - звати
          - з
        explanation: У мене є... — блок, щоб сказати, що хтось або щось є в мене.
      - sentence: Це ___ мама.
        answer: моя
        options:
          - моя
          - мій
          - моє
        explanation: Мама — жіночого роду, тому моя.
      - sentence: Дуже ___ познайомитися!
        answer: приємно
        options:
          - приємно
          - прізвище
          - звати
        explanation: Дуже приємно познайомитися завершує знайомство.
  - id: act-4
    type: quiz
    title: Виправ A1.1 пастки
    instruction: Обери нормативну українську форму.
    items:
      - prompt: Представлення імені
        options:
          - text: Мене звати Джон.
            correct: true
          - text: Моє ім'я є Джон.
            correct: false
        explanation: Українська представляє ім'я через Мене звати...
      - prompt: Речення ідентичності
        options:
          - text: Я студент.
            correct: true
          - text: Я є студент.
            correct: false
        explanation: Теперішня ідентичність зазвичай не додає є.
      - prompt: Речення про вік
        options:
          - text: Мені 20 років.
            correct: true
          - text: Я маю 20 років.
            correct: false
        explanation: Вік подаємо блоком Мені ... років.
      - prompt: Пряме звертання
        options:
          - text: Привіт, Максиме!
            correct: true
          - text: Привіт, Максим!
            correct: false
        explanation: Пряме звертання має кличну форму в безпечному прикладі.
      - prompt: Безпечне привітання
        options:
          - text: Добрий день! Мене звати Оксана.
            correct: true
          - text: Здрастуйте! Мене звати Оксана.
            correct: false
        explanation: Добрий день — безпечне стандартне привітання.
      - prompt: Прізвище
        options:
          - text: Моє прізвище Сміт.
            correct: true
          - text: Моя фамілія Сміт.
            correct: false
        explanation: Прізвище — стандартне українське слово.
      - prompt: Прощання
        options:
          - text: До побачення!
            correct: true
          - text: Пока!
            correct: false
        explanation: До побачення — безпечне стандартне прощання.
      - prompt: Звичка до роду іменника
        options:
          - text: Вивчення слова разом із його родом
            correct: true
          - text: Ігнорування роду іменника
            correct: false
        explanation: Запам'ятовуй український іменник разом із підказками роду.
  - id: act-5
    type: fill-in
    title: Пропуски в діалозі
    instruction: Доповни діалог на мовних курсах.
    items:
      - sentence: ___! Мене звати Богдан.
        answer: Привіт
        options:
          - Привіт
          - Прізвище
          - Років
        explanation: Привіт відкриває розмову ровесників.
      - sentence: Привіт, ___! Мене звати Соломія.
        answer: Богдане
        options:
          - Богдане
          - Богдан
          - Богдана
        explanation: Богдане — клична форма прямого звертання.
      - sentence: Дуже приємно, ___.
        answer: Соломіє
        options:
          - Соломіє
          - Соломія
          - Соломію
        explanation: Соломіє — клична форма прямого звертання.
      - sentence: ___ ти? Я з Дніпра.
        answer: Звідки
        options:
          - Звідки
          - Хто
          - Де
        explanation: Звідки ти? питає, звідки людина.
      - sentence: Моя майбутня ___ — вчителька.
        answer: професія
        options:
          - професія
          - прізвище
          - знайомство
        explanation: Професія називає фах або заняття.
      - sentence: У мене є сестра. ___ звати Ірина.
        answer: Її
        options:
          - Її
          - Його
          - Я
        explanation: Її підходить до сестри.
      - sentence: У мене є брат. ___ звати Назар.
        answer: Його
        options:
          - Його
          - Її
          - Вона
        explanation: Його підходить до брата.
      - sentence: Дуже приємно ___!
        answer: познайомитися
        options:
          - познайомитися
          - походження
          - допомогти
        explanation: Дуже приємно познайомитися завершує першу зустріч.
  - id: act-6
    type: quiz
    title: Порядок знайомства
    instruction: Обери наступний рядок у розмові.
    items:
      - prompt: 'Перший рядок: Привіт! Мене звати Богдан.'
        options:
          - text: Привіт, Богдане! Мене звати Соломія.
            correct: true
          - text: До побачення!
            correct: false
          - text: Мені 20 років.
            correct: false
        explanation: Інша людина відповідає привітанням та іменем.
      - prompt: 'Рядок: Дуже приємно, Соломіє.'
        options:
          - text: Мені теж. Звідки ти?
            correct: true
          - text: Моє ім'я є Соломія.
            correct: false
          - text: Моя фамілія Сміт.
            correct: false
        explanation: Мені теж дає взаємну відповідь і рухає розмову далі.
      - prompt: 'Рядок: Я з Дніпра. А ти?'
        options:
          - text: Я з Тернополя.
            correct: true
          - text: Його звати Назар.
            correct: false
          - text: Це мій брат.
            correct: false
        explanation: А ти? повертає питання про походження.
      - prompt: 'Рядок: У мене є брат.'
        options:
          - text: Дуже приємно. До побачення!
            correct: true
          - text: Моє ім'я є брат.
            correct: false
          - text: Я маю брат років.
            correct: false
        explanation: Після родинного рядка пасує ввічливе завершення.
workbook:
  - type: quiz
    title: Швидкий переклад
    instruction: Обери англійське значення кожного українського рядка.
    items:
      - prompt: Мене звати Олена.
        options:
          - text: My name is Olena.
            correct: true
          - text: I am from Olena.
            correct: false
          - text: Olena is my surname.
            correct: false
        explanation: Мене звати... називає ім'я.
      - prompt: Моє прізвище Мельник.
        options:
          - text: My surname is Melnyk.
            correct: true
          - text: My profession is Melnyk.
            correct: false
          - text: My family is Melnyk.
            correct: false
        explanation: Прізвище означає родове ім'я.
      - prompt: Я з Канади.
        options:
          - text: I am from Canada.
            correct: true
          - text: I am in Canada.
            correct: false
          - text: I have Canada.
            correct: false
        explanation: Я з... подає походження.
      - prompt: Я студентка.
        options:
          - text: I am a female student.
            correct: true
          - text: I have a student.
            correct: false
          - text: My name is student.
            correct: false
        explanation: У цьому реченні ідентичність виражена іменником без є.
      - prompt: У мене є сестра.
        options:
          - text: I have a sister.
            correct: true
          - text: You have a sister.
            correct: false
          - text: This is my sister.
            correct: false
        explanation: У мене є... — блок для наявності.
      - prompt: Мені теж.
        options:
          - text: Me too.
            correct: true
          - text: Nice to meet you.
            correct: false
          - text: Goodbye.
            correct: false
        explanation: Мені теж дає взаємну відповідь.
  - type: match-up
    title: Карта лексики
    instruction: З'єднай українське контрольне слово з англійською підказкою.
    pairs:
      - left: ім'я
        right: first name
      - left: прізвище
        right: surname
      - left: знайомство
        right: acquaintance or introduction
      - left: професія
        right: profession
      - left: національність
        right: nationality
      - left: походження
        right: origin
      - left: Дуже приємно
        right: very nice to meet you
      - left: Мені теж
        right: me too
  - type: fill-in
    title: Етикет у чаті
    instruction: Доповни коротку розмову в чаті курсу.
    items:
      - sentence: ___! Мене звати Ліна.
        answer: Привіт
        options:
          - Привіт
          - Пока
          - Прізвище
        explanation: Привіт відкриває неформальний чат.
      - sentence: Я ___ Одеси.
        answer: з
        options:
          - з
          - є
          - моя
        explanation: Я з... подає походження.
      - sentence: Привіт, ___!
        answer: Ліно
        options:
          - Ліно
          - Ліна
          - Ліну
        explanation: Ліно — клична форма прямого звертання.
      - sentence: Дуже ___!
        answer: приємно
        options:
          - приємно
          - професія
          - знайомство
        explanation: Дуже приємно — ввічлива відповідь під час першого знайомства.
      - sentence: Мені ___.
        answer: теж
        options:
          - теж
          - звати
          - професія
        explanation: Мені теж означає взаємну відповідь.


### vocabulary.yaml

# Checkpoint review vocabulary: recycled phrases from M01-M06 plus integration labels.
- lemma: ім'я
  translation: first name
  pos: noun
  usage: Моє ім'я Олена.
- lemma: прізвище
  translation: surname
  pos: noun
  usage: Моє прізвище Мельник.
- lemma: знайомство
  translation: acquaintance / introduction
  pos: noun
  usage: Це перше знайомство.
- lemma: познайомитися
  translation: to meet / get acquainted
  pos: verb
  usage: Дуже приємно познайомитися!
- lemma: професія
  translation: profession
  pos: noun
  usage: Моя професія — вчителька.
- lemma: національність
  translation: nationality
  pos: noun
  usage: Моя національність — канадка.
- lemma: походження
  translation: origin
  pos: noun
  usage: Походження відповідає на питання Звідки ти?
- lemma: Вітаю
  translation: hello / greetings
  pos: interjection
  usage: Вітаю! Мене звати Олена.
- lemma: Дуже приємно
  translation: very nice to meet you
  pos: phrase
  usage: Дуже приємно!
- lemma: Мені теж
  translation: me too
  pos: phrase
  usage: Мені теж.
- lemma: Мене звати
  translation: my name is
  pos: phrase
  usage: Мене звати Богдан.
- lemma: Як тебе звати?
  translation: what is your name? informal
  pos: phrase
  usage: Як тебе звати?
- lemma: Звідки ти?
  translation: where are you from? informal
  pos: phrase
  usage: Звідки ти?
- lemma: Я з
  translation: I am from
  pos: phrase
  usage: Я з Канади.
- lemma: Мені 20 років
  translation: I am 20 years old
  pos: phrase
  usage: Мені 20 років.
- lemma: У мене є
  translation: I have
  pos: phrase
  usage: У мене є сестра.
- lemma: У тебе є
  translation: do you have / you have
  pos: phrase
  usage: У тебе є брат?
- lemma: студент
  translation: male student
  pos: noun
  usage: Я студент.
- lemma: студентка
  translation: female student
  pos: noun
  usage: Я студентка.
- lemma: вчителька
  translation: female teacher
  pos: noun
  usage: Вона вчителька.
- lemma: інженер
  translation: engineer
  pos: noun
  usage: Мій тато — інженер.
- lemma: українка
  translation: Ukrainian woman
  pos: noun
  usage: Олена — українка.
- lemma: канадка
  translation: Canadian woman
  pos: noun
  usage: Олена — канадка.
- lemma: сім'я
  translation: family, close household
  pos: noun
  usage: Це моя сім'я.
- lemma: родина
  translation: family or kin
  pos: noun
  usage: Це моя родина.
- lemma: мама
  translation: mom
  pos: noun
  usage: Це моя мама.
- lemma: тато
  translation: dad
  pos: noun
  usage: Це мій тато.
- lemma: брат
  translation: brother
  pos: noun
  usage: У мене є брат.
- lemma: сестра
  translation: sister
  pos: noun
  usage: У мене є сестра.
- lemma: мій
  translation: my, masculine
  pos: pronoun
  usage: Це мій брат.
- lemma: моя
  translation: my, feminine
  pos: pronoun
  usage: Це моя мама.
- lemma: моє
  translation: my, neuter
  pos: pronoun
  usage: Це моє прізвище.
- lemma: мої
  translation: my, plural
  pos: pronoun
  usage: Це мої батьки.
- lemma: його
  translation: his / him
  pos: pronoun
  usage: Його звати Назар.
- lemma: її
  translation: her
  pos: pronoun
  usage: Її звати Ірина.


### resources.yaml

- title: ULP Season 1, Episode 10 — Review 1-9
  role: podcast
  source_ref: ULP Season 1, Episode 10 — Review 1-9
  url: https://www.ukrainianlessons.com/episode10/
  notes: "Plan reference: connected review speech about myself and my family."


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
