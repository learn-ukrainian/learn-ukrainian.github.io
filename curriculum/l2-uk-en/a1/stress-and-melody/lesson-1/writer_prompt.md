# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: stress-and-melody.
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
  title: Мелодика
  sections:
  - Наголос
  - Мелодика
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
  title: Друк, зошит, голос
  sections:
  - Читаємо вголос
  - Друк, зошит, голос
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
  title: Перевірка
  sections:
  - Перевірка
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
items_min_exempt:
- id: act-1
  reason: 4-item original activity preserved from baseline
- id: act-2
  reason: 4-item original activity preserved from baseline
- id: act-3
  reason: 3-item original activity preserved from baseline
- id: act-4
  reason: 5-item original activity preserved from baseline
- id: act-w4
  reason: 4-item original activity preserved from baseline
- id: act-w5
  reason: 4-item original activity preserved from baseline
- id: act-w6
  reason: 4-item original activity preserved from baseline
proper_names: []


## Original plan (read-only)

module: a1-004
level: A1
sequence: 4
slug: stress-and-melody
version: 1.2.3
letter_module: true
lifecycle: locked
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-stress-and-melody
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md.
  Wiki locked to 9/10 on all 5 dimensions (wiki/.reviews/pedagogy/a1/stress-and-melody-review-LOCKED.md).
  Plan findings: (1) internal contradiction between grammar item 3 "питальна ↗" and
  grammar item 4 "питальні слова не потребують висхідної інтонації" — tightened item
  3 to "питання без питального слова (так/ні) ↗"; (2) Читаємо вголос dialogue marked
  `Як справи? ↗` which contradicts the plan''s own WH-question rule — normalised to
  `↘` with an author-note about the conversational-register exception; (3) typo `з
  модуля модуль №1` → `з модуля №1`; (4) added stress-transfer-error fill-in activity
  mirroring the new wiki "Типові помилки L2 (наголос)" table; (5) added `мука / борошно`
  writer-note to disambiguate the homograph pair''s pedagogical role vs. the modern
  standard term for "flour"; (6) wiki back-reference added to references. See PR body
  for full findings + fixes.'
title: Наголос і мелодика
subtitle: Наголос змінює значення, інтонація змінює намір
focus: phonetics
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
word_target: 1200
objectives:
- Розуміти, що український наголос є вільним і може змінювати значення слова
- Правильно ставити наголос у поширених словах рівня A1
- Використовувати висхідну інтонацію для загальних питань (так/ні) і низхідну для
  тверджень
- Читати вголос із природним українським ритмом
content_outline:
- section: Наголос
  words: 350
  points:
  - 'Заболотний, 5 клас, с. 73: Українська мова має 38 звуків, і наголос визначає,
    який склад вимовляється голосніше та довше. Наголос є ВІЛЬНИМ — він може падати
    на будь-який склад і РУХОМИМ — може переміщуватися між формами одного слова. Це
    відрізняє його від французької (завжди на останньому) чи чеської (завжди на першому).'
  - 'Наголос змінює значення — реальні пари слів, які зустрінуться учням: замок (castle)
    / замок (lock), атлас (atlas) / атлас (satin), орган (organ of the body) / орган
    (musical instrument), сім''я (family) / сім''я (seed). Неправильний наголос =
    неправильне слово. Ось чому позначки наголосу є важливими. (Примітка до автора:
    пара `мука / мука` — не подавати як "torment/flour"; модерна словникова норма
    для "flour" — `борошно`.)'
  - На письмі позначки наголосу (') ставляться в підручниках і словниках, але НЕ у
    звичайних українських текстах. Учням завжди слід перевіряти наголос на goroh.pp.ua,
    якщо є сумніви.
  - 'Поширені моделі для початківців: Перший склад: мама, тато, ранок, кава, книга.
    Останній склад: вода, зима, рука, метро, кафе. Короткого шляху немає — потрібно
    вивчати наголос для кожного слова окремо.'
- section: Інтонація
  words: 300
  points:
  - 'Українська мова використовує інтонацію (мелодику) для розрізнення типів речень.
    Ті самі слова, різна мелодика, різне значення. Твердження: Це кава. ↘ Питання:
    Це кава? ↗ Оклик: Як гарно! ↘↘'
  - 'Питальні слова (хто, що, де, коли) утворюють питання БЕЗ висхідної інтонації:
    Що це? ↘ Де метро? ↘ Але загальні питання (так/ні) завжди мають висхідну інтонацію:
    Це метро? ↗'
  - 'В українській мові речення класифікують за метою висловлювання: розповідні, питальні,
    спонукальні. Будь-яке з них може бути також окличним — це окремий вимір. Для A1
    зосередимося на трьох моделях пунктуації: . для тверджень, ? для питань, ! для
    окликів або наказів.'
- section: Читаємо вголос
  words: 300
  points:
  - 'Читання багатоскладових слів із правильним наголосом: у-кра-їн-ська, фо-то-гра-фі-я,
    ві-дпо-чи-нок. Метод: розділити на склади → знайти наголошений склад → прочитати
    у природному темпі.'
  - 'Практика читання наголошених слів — читати вголос із правильним наголосом: Ки-їв,
    мо-ло-ко, ран-ок, ка-ва, во-да, зи-ма, у-кра-їн-ська. Знайдіть наголошений склад,
    а потім прочитайте все слово в природному темпі.'
  - 'Практика діалогів з використанням вітань з модуля №1: — Привіт! ↘ — Привіт! Як
    справи? ↘ — Добре! А у тебе? ↗ — Добре! ↘ Застосовуйте інтонаційні моделі до вже
    вивчених привітань. УВАГА до автора: `Як справи?` містить питальне слово `як`,
    тому за правилом має спадну інтонацію. У живому розмовному мовленні ця фраза часто
    звучить з висхідною (фатична функція), але для A1 подаємо нормативний спадний
    контур, щоб учень закріпив правило WH-питань.'
- section: Підсумок
  words: 250
  points:
  - 'Самоперевірка: Що таке наголос? Чи може він змінювати значення слова? Наведіть
    приклад. Яку інтонацію ви використовуєте для загальних питань (так/ні)? Для тверджень?
    Прочитайте це вголос: Це аптека? Так, це аптека. Як гарно!'
vocabulary_hints:
  required:
  - наголос (stress/accent)
  - замок (castle — stress on first syllable)
  - замок (lock — stress on last syllable)
  - кава (coffee)
  - вода (water)
  - столиця (capital)
  recommended:
  - атлас (atlas — stress on first syllable; pairs with атлас for meaning-distinguishing
    drill)
  - атлас (satin — stress on last syllable; pairs with атлас)
  - орган (organ of the body — stress on first syllable; pairs with орган)
  - орган (musical instrument — stress on last syllable; pairs with орган)
  - ранок (morning)
  - метро (metro)
  - фотографія (photograph)
  - одинадцять (eleven — stress on `-на-`; classic L2 stress-transfer target)
  - чотирнадцять (fourteen — stress on `-на-`; classic L2 stress-transfer target)
targets:
  new_vocabulary:
  - наголос
  - замок
  - кава
  - вода
  - столиця
  - атлас
  - орган
  - ранок
  - метро
  - фотографія
  - одинадцять
  - чотирнадцять
  new_grammar: []
  recycle_vocabulary: []
activity_hints:
- type: quiz
  focus: Де наголос? Виберіть правильний склад.
  items: 8
- type: match-up
  focus: 'З''єднайте пари слів за наголосом: замок ↔ замок'
  items: 4
- type: quiz
  focus: Твердження, питання чи оклик? Виберіть на основі пунктуації.
  items: 6
- type: fill-in
  focus: 'Поставте правильний розділовий знак: Це кава_ Де метро_ Як гарно_'
  items: 6
- type: fill-in
  focus: 'Типові L2-помилки наголосу — оберіть нормативну форму (див. wiki "Типові
    помилки L2 (наголос)"). Формат: `слово {нормативний_наголос|помилковий_наголос}`.'
  items:
  - Це моя {новий|новий} комп''ютер. (adjective ending-stress, R-L1 transfer)
  - Мій дідусь {старий|старий}. (adjective ending-stress, R-L1 transfer)
  - У мене в руці {одинадцять|одиннадцять} гривень. (numeral — stress on `-на-`)
  - Я вивчив {чотирнадцять|чотирнадцять} нових слів. (numeral — stress on `-на-`)
  - У мене болять {гóлови|голови}. (plural — mobile stress, plural is stem-stressed)
  - Мене звати {Марія|Марія}. (feminine -ія name — stress on `-і-`)
connects_to:
- a1-005 (Хто я?)
prerequisites:
- a1-003 (Спеціальні знаки)
grammar:
- Вільний наголос
- Пари слів, значення яких залежить від наголосу
- 'Три інтонаційні моделі: розповідна ↘, питання без питального слова (так/ні) ↗,
  оклична ↘↘'
- Питальні речення з питальним словом (хто/що/де/коли/як) мають спадну інтонацію,
  як і розповідні
register: розмовний
references:
- title: Заболотний Grade 5, p.73
  notes: 38 звуків, наголос. Наголос як вільний і рухомий.
- title: Авраменко Grade 5, p.19
  notes: Інтонація речень — розповідні, питальні, окличні.
- title: ULP Season 1, Episode 5 — Pronunciation Trainer
  url: https://www.ukrainianlessons.com/episode5/
  notes: Практика наголосу з числівниками.
- title: 'Wiki: pedagogy/a1/stress-and-melody (LOCKED 2026-04-23)'
  notes: Authoritative pedagogical brief — see Крок 5 (чотири базові інтонаційні контури
    з прикладовими реченнями) and "Типові помилки L2 (наголос)" (R-L1 + англ. stress-transfer
    drill).
changelog:
- version: 1.2.0
  date: '2026-04-23'
  changes:
  - Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md. Added
    lifecycle markers (lifecycle / reviewed_at / reviewed_by / review_notes) per the
    convention.
  - 'Fixed internal contradiction in grammar[]: tightened "Три інтонаційні моделі:
    розповідна ↘, питальна ↗, оклична ↘↘" → "…питання без питального слова (так/ні)
    ↗…" (matches the WH-question falling-intonation rule stated elsewhere in the plan
    and in the locked wiki).'
  - 'Fixed intonation inconsistency in Читаємо вголос: `Як справи? ↗` → `Як справи?
    ↘` (applies the plan''s own WH-question rule). Added author-note explaining the
    conversational-register exception so the writer does not silently invert back
    to the "natural" rising contour.'
  - 'Fixed typo: "з модуля модуль №1" → "з модуля №1".'
  - Added stress-transfer-error fill-in activity (6 items) mirroring the new wiki
    "Типові помилки L2 (наголос)" table — covers numerals, adjective ending-stress,
    mobile plural, homograph pairs.
  - Annotated meaning-distinguishing stress pairs directly in vocabulary_hints (замок
    / замок, атлас / атлас, орган / орган — all with stress marks and English glosses).
    Dropped the disputed `мука / мука` flour/torment pair from vocabulary_hints; a
    note in content_outline[0].points[1] flags that the modern standard term for flour
    is `борошно` so the writer does not silently teach a dialectal form.
  - Added одинадцять / чотирнадцять to recommended vocabulary as canonical L2 stress-transfer
    targets.
  - 'Added wiki back-reference to references: (LOCKED 2026-04-23).'
plan_fixes:
- version: 1.2.1
  date: '2026-04-24'
  trigger: Plan check rejected U+0301 combining acute stress marks in 43 place(s).
    Pipeline adds stress marks deterministically AFTER review; plans must be stress-free.
  changes:
  - strip U+0301 from all string values (43 removals)


## Existing module artifacts (read-only)

### module.md

# Наголос і мелодика

**ка́ва. вода́. Це ка́ва? Де метро́?** — stress and sentence melody.

Teacher Oksana starts with a tiny routine: listen, mark, repeat. If you have a
teacher or tutor, let them read one word first. If you are working alone, read
the stress mark first and then say the word slowly.

Today you are not memorizing every stress pattern in Ukrainian. You are
learning why stress matters, how to read words with stress marks, and how to
use three beginner sentence melodies.

By the end, you can:

- explain **на́голос** — word stress;
- read **ка́ва**, **вода́**, **ра́нок**, and **метро́** with the marked syllable
  stronger and a little longer;
- keep Ukrainian vowels clear outside stress;
- recognize pairs where stress changes meaning, such as **за́мок** and
  **замо́к**;
- use falling melody for statements, rising melody for yes/no questions, and
  falling melody for questions with **хто**, **що**, **де**, **коли**, or
  **як**;
- read a short greeting dialogue with Ukrainian rhythm.

:::tip
If you want extra listening support, open [ULP Season 1, Episode 5 —
Pronunciation Trainer](https://www.ukrainianlessons.com/episode5/) from the
Resources tab and copy only short model words.
:::

## Наголос

**ка́ва. вода́. молоко́.** Listen first, then read the marks.

**На́голос** is the syllable you say with more force and a little more length.
In learning materials, this course marks it with an accent: **ка́ва**,
**вода́**, **молоко́**. In ordinary Ukrainian texts, the mark is usually
absent, so you learn stress as part of each new word.

Use this quick pass before the table:

1. Point to the stress mark.
2. Say only the stronger syllable.
3. Say the whole word once.

Ukrainian stress is free. It can fall near the beginning, middle, or end of a
word.

| Model | Read it slowly |
| --- | --- |
| first syllable | **ма́ма**, **та́то**, **ра́нок**, **ка́ва**, **кни́га** |
| final syllable | **вода́**, **зима́**, **рука́**, **метро́**, **кафе́** |
| middle syllable | **столи́ця**, **люди́на**, **одина́дцять** |

There is no useful shortcut for A1 learners. That is normal. Treat stress as
part of the word, just like spelling. When you add a word to your notebook,
add its stress too: **ка́ва**, not just кава.

A second habit matters just as much: do not blur unstressed vowels. In
**молоко́**, the first two **о** sounds stay **о**. They are lighter than the
stressed final **о**, but they stay clear. Read slowly first:
**мо-ло-ко́**. Keep every vowel clear, then speed up.

Some Ukrainian words move stress when the form changes. For now, only notice
the idea. **голова́** can become **го́лови** in plural. That is a future
grammar habit, but you can already hear that Ukrainian stress can move.

Stress can also change meaning:

| Pair | English support |
| --- | --- |
| **за́мок** | castle |
| **замо́к** | lock |
| **а́тлас** | atlas |
| **атла́с** | satin |
| **о́рган** | body organ |
| **орга́н** | musical instrument |
| **сі́м'я** | seed |
| **сім'я́** | family |

Do not guess these from spelling alone. Use the stress mark when it is given,
and check a dictionary such as goroh.pp.ua when you are unsure.

:::tip
You already saw **за́мок** and **замо́к**, and you already know **сім'я́**
from Module 3. Here they are reminders, not a new memory load: the mark is
small, but it can carry meaning.
:::

<!-- INJECT_ACTIVITY: act-1 -->

<!-- INJECT_ACTIVITY: act-3 -->

## Мелодика

**Це ка́ва. Це ка́ва? Як га́рно!** — same words can carry different melody.

**Мелодика** is the movement of the voice across a whole sentence. For A1, use
three safe models:

| Sentence type | Model | Voice |
| --- | --- | --- |
| statement | **Це ка́ва.** | falling **↘** |
| yes/no question | **Це ка́ва?** | rising **↗** |
| exclamation | **Як га́рно!** | stronger falling **↘↘** |

The punctuation helps you choose the melody, but your voice must still do the
work.

Now add the most important beginner exception. A question with a question word
usually falls, not rises:

| Question word | Example | Melody |
| --- | --- | --- |
| **що** | **Що це?** | falling **↘** |
| **де** | **Де метро́?** | falling **↘** |
| **як** | **Як спра́ви?** | falling **↘** |
| **хто** | **Хто це?** | falling **↘** |

But a yes/no question rises:

| Yes/no question | Melody |
| --- | --- |
| **Це метро́?** | rising **↗** |
| **Це вода́?** | rising **↗** |
| **А у те́бе?** | rising **↗** |

<!-- INJECT_ACTIVITY: act-4 -->

Logical stress means the important word inside the sentence. Keep this simple
today. In **Це ка́ва?**, the important word is **ка́ва** because you are
checking the object. In **А у те́бе?**, the important part is **те́бе** because
you are turning the question back to the other person.

Keep the explanation Ukrainian-centered. Listen to the Ukrainian words, notice
the stress, and copy the contour.

:::tip
Do not worry if your melody feels slow at first. Slow and clear is the right
A1 target.
:::

<!-- INJECT_ACTIVITY: act-2 -->

## Читаємо вголос

**украї́нська. фотогра́фія. відпочи́нок.**

Use this three-step routine for longer words:

1. Split the word into syllables.
2. Find the stressed syllable.
3. Read the whole word in a natural tempo.

Practice:

| Whole word | Stressed part to notice |
| --- | --- |
| **украї́нська** | the **ї́н** part is strongest |
| **фотогра́фія** | the **гра́** part is strongest |
| **відпочи́нок** | the **чи́** part is strongest |
| **одина́дцять** | the **на́** part is strongest |
| **чотирна́дцять** | the **на́** part is strongest |

For the number words below, put stress on **на́**:
**одина́дцять**, **чотирна́дцять**. When you write these in your notebook,
write the full word with the stress mark, then underline only the strong part.

:::tip
For this module, a stress mark is a training wheel. It is not usually printed
in ordinary Ukrainian texts, but it helps your eyes remember the sound until
the word becomes familiar.
:::

Read the Ukrainian dialogue first:

```text
О́ля: Приві́т! ↘
Тара́с: Приві́т! Як спра́ви? ↘
О́ля: До́бре! А у те́бе? ↗
Тара́с: До́бре! ↘
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Приві́т!** | Hi! |
| **Як спра́ви?** | How are things? |
| **До́бре!** | Good! |
| **А у те́бе?** | And you? |

Notice two details. **Як спра́ви?** has the question word **як**, so the
beginner model is falling. **А у те́бе?** is a yes/no-style return question, so
it rises.

Now read a second tiny exchange:

```text
О́ля: Це ка́ва. ↘
Тара́с: Це ка́ва? ↗
О́ля: Так, це ка́ва. ↘
Тара́с: Де вода́? ↘
О́ля: Ось вода́. ↘
Тара́с: Як га́рно! ↘↘
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це ка́ва.** | This is coffee. |
| **Це ка́ва?** | Is this coffee? |
| **Так, це ка́ва.** | Yes, this is coffee. |
| **Де вода́?** | Where is the water? |
| **Ось вода́.** | Here is water. |
| **Як га́рно!** | How nice! |

Common traps now become workbook habits:

| Trap | Safer Ukrainian habit |
| --- | --- |
| blurring unstressed vowels in **молоко́** | keep **мо-ло-ко́** clear |
| reading **нови́й** or **стари́й** with early stress | stress the final part |
| keeping stress fixed in **голова́ / го́лови** | notice that stress can move |
| always emphasizing a pronoun | put logical stress on the meaningful word |
| reading **Марі́я** with first-syllable stress | stress the **рі́** part |
| reading **одина́дцять** or **чотирна́дцять** with early stress | stress **на́** |

You do not need to produce all of these words fluently today. You need to
recognize the safer habit and avoid building the wrong one.

<!-- INJECT_ACTIVITY: act-5 -->

## Друк, зошит, голос

**Друк:** **ка́ва**, **вода́**, **молоко́**, **метро́**.

**Зошит:** the same known words written by you, a teacher, or a tutor with the
stress mark preserved.

Recognition comes before fast writing. Match the notebook word to the printed
word, then read it aloud with the stress and melody.

| Друк | Notebook recognition prompt |
| --- | --- |
| **ка́ва** | Which notebook word has stress on the first syllable? |
| **вода́** | Which notebook word has stress on the final syllable? |
| **молоко́** | Which notebook word keeps all three **о** sounds clear? |
| **метро́** | Which notebook word ends with the stressed vowel? |

## Перевірка

Before you leave the lesson tab, check four things aloud:

- What is **на́голос**?
- Can stress change meaning? Say **за́мок** and **замо́к**.
- Which melody do you use for **Це апте́ка?**
- Which melody do you use for **Де метро́?**

Final reading:

```text
О́ля: Це апте́ка? ↗
Тара́с: Так, це апте́ка. ↘
О́ля: Як га́рно! ↘↘
```

Ask a native Ukrainian teacher or tutor to listen to one read-aloud from this
module. The feedback target is narrow: stress, clear vowels, and the direction
of the sentence melody.

You can now read a marked Ukrainian word, keep vowels clear, and choose the
first safe melody for a statement or question. Next, Module 5 uses this sound
control when you introduce yourself.

The workbook adds extra practice with the same skills: stress sorting,
stress-transfer repair, quick facts, and word recognition.


### activities.yaml

inline:
  - id: act-1
    type: quiz
    title: Де на́голос
    instruction: Обери склад із позначеним на́голосом.
    items:
      - prompt: 'Читай: ка́ва. Де на́голос?'
        options:
          - text: перший склад
            correct: true
          - text: останній склад
            correct: false
          - text: немає наголосу
            correct: false
        explanation: У слові ка́ва на́голос на ка́.
      - prompt: 'Читай: вода́. Де на́голос?'
        options:
          - text: останній склад
            correct: true
          - text: перший склад
            correct: false
          - text: усі склади однакові
            correct: false
        explanation: У слові вода́ на́голос на да́.
      - prompt: 'Читай: столи́ця. Де на́голос?'
        options:
          - text: середній склад
            correct: true
          - text: перший склад
            correct: false
          - text: останній склад
            correct: false
        explanation: У слові столи́ця на́голос на ли́.
      - prompt: 'Молоко́: що робимо з ненаголошеними голосними?'
        options:
          - text: тримаємо кожен голосни́й чистим
            correct: true
          - text: пропускаємо перший голосни́й
            correct: false
          - text: читаємо кожне о як а
            correct: false
        explanation: Українські ненаголошені голосні залишаються чистими.
  - id: act-2
    type: quiz
    title: Вибір мелодики
    instruction: Обери першу модель мелодики речення.
    items:
      - prompt: Це ка́ва.
        options:
          - text: спадна ↘
            correct: true
          - text: висхідна ↗
            correct: false
        explanation: Твердження має спадну мелодику.
      - prompt: Це ка́ва?
        options:
          - text: висхідна ↗
            correct: true
          - text: спадна ↘
            correct: false
        explanation: Так/ні питання має висхідну мелодику.
      - prompt: Де метро́?
        options:
          - text: спадна ↘
            correct: true
          - text: висхідна ↗
            correct: false
        explanation: Питання з де на A1 має спадну мелодику.
      - prompt: Як га́рно!
        options:
          - text: сильніша спадна ↘↘
            correct: true
          - text: висхідна ↗
            correct: false
        explanation: Оклик має сильнішу спадну мелодику.
  - id: act-3
    type: quiz
    title: Швидкий контраст
    instruction: Обери коротку англійську підказку.
    items:
      - prompt: за́мок
        options:
          - text: castle
            correct: true
          - text: lock
            correct: false
        explanation: За́мок із наголосом на першому складі — castle.
      - prompt: замо́к
        options:
          - text: lock
            correct: true
          - text: castle
            correct: false
        explanation: Замо́к із наголосом на останньому складі — lock.
      - prompt: сім'я́
        options:
          - text: family
            correct: true
          - text: seed
            correct: false
        explanation: Сім'я́ з фінальним наголосом — family.
  - id: act-4
    type: fill-in
    title: Пунктуація і мелодика
    instruction: Обери розділовий знак, який відповідає реченню.
    items:
      - sentence: Це ка́ва_
        answer: .
        options:
          - .
          - '?'
          - '!'
        explanation: Твердження має крапку й спадну мелодику.
      - sentence: Це метро́_
        answer: '?'
        options:
          - '?'
          - .
          - '!'
        explanation: Так/ні питання має знак питання й висхідну мелодику.
      - sentence: Де апте́ка_
        answer: '?'
        options:
          - '?'
          - .
          - '!'
        explanation: Де робить це питанням, але мелодика спадна.
      - sentence: Як га́рно_
        answer: '!'
        options:
          - '!'
          - '?'
          - .
        explanation: Це оклик.
      - sentence: Так, це вода́_
        answer: .
        options:
          - .
          - '?'
          - '!'
        explanation: Це твердження.
  - id: act-5
    type: fill-in
    title: Типові пастки наголосу
    instruction: Обери нормативну форму з позначеним наголосом.
    items:
      - sentence: "Це мій ___ комп'ютер."
        answer: нови́й
        options:
          - нови́й
          - но́вий
        explanation: У слові нови́й наголос наприкінці.
      - sentence: "Мій дідусь ___."
        answer: стари́й
        options:
          - стари́й
          - ста́рий
        explanation: У слові стари́й наголос наприкінці.
      - sentence: "У мене ___ гривень."
        answer: одина́дцять
        options:
          - одина́дцять
          - о́динадцять
        explanation: Одина́дцять має наголос на -на́-.
      - sentence: "Я знаю ___ нових слів."
        answer: чотирна́дцять
        options:
          - чотирна́дцять
          - чоти́рнадцять
        explanation: Чотирна́дцять теж має наголос на -на́-.
      - sentence: "Множина слова голова́: ___."
        answer: го́лови
        options:
          - го́лови
          - голови́
        explanation: У цій словниковій парі наголос рухається.
      - sentence: "Мене звати ___."
        answer: Марі́я
        options:
          - Марі́я
          - Ма́рія
        explanation: У цьому імені наголос на рі́.
workbook:
  - type: fill-in
    title: Типові помилки наголосу
    instruction: Обери нормативну форму з позначеним наголосом.
    items:
      - sentence: "новий: ___"
        answer: нови́й
        options:
          - нови́й
          - но́вий
        explanation: У слові нови́й наголос на останній частині.
      - sentence: "старий: ___"
        answer: стари́й
        options:
          - стари́й
          - ста́рий
        explanation: У слові стари́й наголос на останній частині.
      - sentence: "одинадцять: ___"
        answer: одина́дцять
        options:
          - одина́дцять
          - о́динадцять
        explanation: Одина́дцять має наголос на -на́-.
      - sentence: "чотирнадцять: ___"
        answer: чотирна́дцять
        options:
          - чотирна́дцять
          - чоти́рнадцять
        explanation: Чотирна́дцять теж має наголос на -на́-.
      - sentence: "множина слова голова́: ___"
        answer: го́лови
        options:
          - го́лови
          - голови́
        explanation: "У цій парі наголос рухається: голова́, але го́лови."
      - sentence: "ім'я: ___"
        answer: Марі́я
        options:
          - Марі́я
          - Ма́рія
        explanation: У цьому імені наголос на рі́.
  - type: match-up
    title: На́голос змінює значення
    instruction: З'єднай наголошене слово з короткою англійською підказкою.
    pairs:
      - left: за́мок
        right: castle
      - left: замо́к
        right: lock
      - left: а́тлас
        right: atlas
      - left: атла́с
        right: satin
      - left: о́рган
        right: body organ
      - left: орга́н
        right: musical instrument
      - left: сі́м'я
        right: seed
      - left: сім'я́
        right: family
  - type: group-sort
    title: Сортуй за наголосом
    instruction: Розподіли кожне слово за позначеним наголошеним складом.
    groups:
      - label: Перший склад
        items:
          - ма́ма
          - та́то
          - ра́нок
          - ка́ва
      - label: Середній склад
        items:
          - столи́ця
          - люди́на
          - одина́дцять
          - чотирна́дцять
      - label: Останній склад
        items:
          - вода́
          - зима́
          - рука́
          - метро́
  - type: match-up
    title: Друк і зошит
    instruction: З'єднай друковане слово з підказкою в зо́шиті.
    pairs:
      - left: 'друк: ка́ва'
        right: 'зошит: на́голос на першому складі'
      - left: 'друк: вода́'
        right: 'зошит: на́голос на останньому складі'
      - left: 'друк: молоко́'
        right: 'зошит: три чисті звуки о'
      - left: 'друк: метро́'
        right: 'зошит: останній наголошений голосни́й'
  - type: true-false
    title: Факти про наголос і мелодику
    instruction: Обери правда чи неправда.
    items:
      - statement: Український на́голос може бути на різних складах.
        correct: true
        explanation: На́голос вільний, тому вчи його разом із кожним словом.
      - statement: Звичайні українські тексти завжди мають позначки наголосу.
        correct: false
        explanation: Позначки наголосу є в навчальних матеріалах і словниках, а не в більшості звичайних текстів.
      - statement: Так/ні питання Це вода́? має висхідну мелодику на A1.
        correct: true
        explanation: Так/ні питання має висхідну мелодику.
      - statement: Питання з де завжди потребує висхідної мелодики на A1.
        correct: false
        explanation: Питання з питальним словом як де має спадну мелодику.
  - type: translate
    title: Слова з наголосом
    instruction: Спочатку прочитай українське слово, потім обери англійську підказку.
    items:
      - source: на́голос
        options:
          - text: stress / accent
            correct: true
          - text: lock
            correct: false
          - text: water
            correct: false
        explanation: На́голос — stress / accent.
      - source: ка́ва
        options:
          - text: coffee
            correct: true
          - text: capital
            correct: false
          - text: morning
            correct: false
        explanation: Ка́ва — coffee.
      - source: вода́
        options:
          - text: water
            correct: true
          - text: photograph
            correct: false
          - text: atlas
            correct: false
        explanation: Вода́ — water.
      - source: столи́ця
        options:
          - text: capital
            correct: true
          - text: metro
            correct: false
          - text: family
            correct: false
        explanation: Столи́ця — capital.


### vocabulary.yaml

- lemma: наголос
  translation: stress / accent
  pos: noun
  usage: Наголос у слові ка́ва.
- lemma: мелодика
  translation: melody / intonation
  pos: noun
  usage: Мелодика речення.
- lemma: склад
  translation: syllable
  pos: noun
  usage: Один склад.
- lemma: наголошений
  translation: stressed
  pos: adjective
  usage: Наголошений склад.
- lemma: ненаголошений
  translation: unstressed
  pos: adjective
  usage: Ненаголошений склад.
- lemma: голосний
  translation: vowel
  pos: adjective / noun
  usage: Голосний звук.
- lemma: слово
  translation: word
  pos: noun
  usage: Слово ка́ва.
- lemma: речення
  translation: sentence
  pos: noun
  usage: Речення має мелодику.
- lemma: питання
  translation: question
  pos: noun
  usage: Це питання.
- lemma: хто
  translation: who
  pos: pronoun
  usage: Хто це?
- lemma: що
  translation: what
  pos: pronoun
  usage: Що це?
- lemma: де
  translation: where
  pos: adverb
  usage: Де метро́?
- lemma: коли
  translation: when
  pos: adverb
  usage: Коли?
- lemma: як
  translation: how
  pos: adverb
  usage: Як спра́ви?
- lemma: кава
  translation: coffee
  pos: noun
  usage: Ка́ва.
- lemma: вода
  translation: water
  pos: noun
  usage: Вода́.
- lemma: столиця
  translation: capital
  pos: noun
  usage: Це столи́ця.
- lemma: замок
  translation: castle / lock
  pos: noun
  usage: За́мок і замо́к.
- lemma: атлас
  translation: atlas / satin
  pos: noun
  usage: А́тлас і атла́с.
- lemma: орган
  translation: organ
  pos: noun
  usage: О́рган і орга́н.
- lemma: сім'я
  translation: seed / family by stress
  pos: noun
  usage: Сі́м'я і сім'я́.
- lemma: ранок
  translation: morning
  pos: noun
  usage: Ра́нок.
- lemma: метро
  translation: metro
  pos: noun
  usage: Метро́.
- lemma: фотографія
  translation: photograph
  pos: noun
  usage: Фотогра́фія.
- lemma: одинадцять
  translation: eleven
  pos: numeral
  usage: Одина́дцять.
- lemma: чотирнадцять
  translation: fourteen
  pos: numeral
  usage: Чотирна́дцять.
- lemma: мама
  translation: mother
  pos: noun
  usage: Ма́ма.
- lemma: тато
  translation: father
  pos: noun
  usage: Та́то.
- lemma: книга
  translation: book
  pos: noun
  usage: Кни́га.
- lemma: зима
  translation: winter
  pos: noun
  usage: Зима́.
- lemma: рука
  translation: hand / arm
  pos: noun
  usage: Рука́.
- lemma: кафе
  translation: cafe
  pos: noun
  usage: Кафе́.
- lemma: молоко
  translation: milk
  pos: noun
  usage: Молоко́.
- lemma: голова
  translation: head
  pos: noun
  usage: Голова́.
- lemma: голови
  translation: heads
  pos: noun plural
  usage: Го́лови.
- lemma: людина
  translation: person
  pos: noun
  usage: Люди́на.
- lemma: українська
  translation: Ukrainian
  pos: adjective
  usage: Украї́нська мова.
- lemma: відпочинок
  translation: rest / vacation
  pos: noun
  usage: Відпочи́нок.
- lemma: новий
  translation: new
  pos: adjective
  usage: Нови́й.
- lemma: старий
  translation: old
  pos: adjective
  usage: Стари́й.
- lemma: аптека
  translation: pharmacy
  pos: noun
  usage: Апте́ка.
- lemma: гарно
  translation: nicely / beautiful
  pos: adverb
  usage: Як га́рно!
- lemma: Марія
  translation: Maria
  pos: proper noun
  usage: Марі́я.


### resources.yaml

- title: Заболотний Grade 5, p.73
  role: textbook
  source_ref: Заболотний Grade 5, p.73
  notes: 'Plan reference: 38 sounds and stress as the louder/longer syllable; stress is free and mobile.'
- title: Авраменко Grade 5, p.19
  role: textbook
  source_ref: Авраменко Grade 5, p.19
  notes: 'Plan reference: sentence intonation categories and punctuation patterns.'
- title: ULP Season 1, Episode 5 - Pronunciation Trainer
  role: podcast
  source_ref: ULP Season 1, Episode 5 — Pronunciation Trainer
  url: https://www.ukrainianlessons.com/episode5/
  notes: 'Plan reference: beginner stress practice with numerals.'


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
