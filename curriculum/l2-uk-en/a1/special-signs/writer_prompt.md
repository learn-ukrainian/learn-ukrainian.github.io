# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: special-signs.
Your current published unit: dry-run preview of all lesson briefs.

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

### Find-and-Fix (`error-correction`) — HARD (upgrade gate)

Step 1 is “spot the bad token”. Step 2 must be a **real spelling choice**, not a
tautology. After the learner marks the error, chips that are only
`[correction, same-error]` fail the lesson gates (and teach nothing).

For **every** `error-correction` item that has a non-empty `error:`:

1. `sentence:` is a **natural Ukrainian carrier** (dialogue/scene). At **A1**,
   for **new** Find-and-Fix items add a short English scaffold after an em dash
   `—` (or a parenthetical gloss). For items preserved from the original module,
   do **not** rewrite `sentence:` (structural preservation); put EN in
   `explanation:` instead if needed. Forbidden: English meta stems
   (“Find the word…”, “Identify which…”, “In Ukrainian, the word for…”).
2. Canonical fields only: `sentence`, `error`, `correction`, `options`,
   optional `explanation` (same contract as fresh write).
3. `options:` has **≥3 distinct** forms, **includes `correction`**, and includes
   **≥1 distractor that is not the spotted `error` token**.
4. **Render-faithful chips:** after MDX derivation, at least one option string
   must equal the rendered `correctForm` **exactly** (React uses
   `selectedFix === correctForm`). Do not put English glosses on chips
   (`день (day)` vs bare `день`); keep glosses in `sentence` / `explanation`.
5. Distractors come **only** from the inventory below (wiki L2 / bad-form pairs /
   cumulative learner-state contrasts). Never invent Russianisms or fabricate
   wrong forms. If inventory is thin, reuse attested pairs from the original
   module’s other EC items / quiz contrasts — still never ship `[corr, err]` alone.
6. You **may grow** original `options` lists (preservation is ⊆). You **must**
   grow empty or binary tautological originals to satisfy (3)–(5).

Empty `options` (UI reveal-only) is a hard fail.

### Fill-in (`fill-in`) — HARD (upgrade gate, #8214)

Every fill-in **item** must include a non-empty `explanation:` that teaches why
the answer is correct (apostrophe rule, soft sign, letter, etc.). Micro-blanks
like `бур___ян` / answer `'` without feedback are a hard fail — same contract as
quiz/translate explanations. Structural blank + `answer∈options` checks still
apply.

### Activity chrome language

Learner-facing `instruction:` / bilingual titles may keep `UA — EN` shape; the
site chrome locale toggle picks the facing language at runtime. Do not bake
English-only instructions for Ukrainian chrome. Content stems stay as above.

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


## Distractor inventory (read-only — use for EC / MCQ wrong forms)

### Wiki `/home/ops/learn-ukrainian/.worktrees/builds/a1-special-signs-20260918-081833/wiki/pedagogy/a1/special-signs.md`

## Типові помилки L2 (англомовні учні)

Англомовні учні неминуче стикаються зі специфічними, системними труднощами під час вивчення українських особливих знаків. Це пов'язано насамперед з тим, що англійська мова не має жодних прямих графічних аналогів цим фонетичним явищам [S9]. В англійській мові апостроф виконує граматичну функцію (приналежність або скорочення), а м'якого знака не існує взагалі. Автор-письменник модулів А1 повинен завчасно передбачити ці типові помилки та органічно інтегрувати в уроки запобіжні вправи та пояснення.

| ❌ Типова помилка L2 | ✅ Правильна українська форма | Чому виникає ця помилка та як її ефективно виправити методично |
| --- | --- | --- |
| Вимова слова «день» як [ден] (з грубим, твердим англійським «н») | Вимова «день» із м'яким, делікатним кінцевим [н'] | В англійській мові просто немає фонематичного протиставлення твердих і м'яких приголосних наприкінці слова [<!-- VERIFY: Фонетична інтерференція -->]. Тому учні цілком природно ігнорують м'який знак, вважаючи його «німим». Рішення: педагогічно порівнювати англійське слово «new» (де артикулюється [н'] перед голосним) із кінцевим українським [н'], змушуючи учня затримати язик у цій верхній позиції [S9]. |
| Читання слова «сім'я» як «сімя» (зі злитим, м'яким [м']) | Читання «сім'я» з чітким, виразним звуком [й]: [сімйа] | Англомовні учні часто ігнорують апостроф, візуально сприймаючи його як пунктуаційну помилку, знак наголосу або декоративний елемент [<!-- VERIFY: Візуальне сприйняття графіки -->]. В результаті вони незаконно пом'якшують губний приголосний. Рішення: наполегливо нагадувати через візуальні метафори, що апостроф діє як бетонна «стіна» між звуками, яка стоїть на сторожі звуку [й] [S9]. |
| Вимова м'якого знака як окремого, повноцінного звуку [і] чи [й] у слові «батько» (виходить: батіко, батйко) | Злита вимова «батько» як [бат'ко] | Початківці наївно намагаються чесно озвучити кожну літеру алфавіту [S8]. Оскільки «ь» не має власного звуку, вони в паніці замінюють його найближчим знайомим аналогом. Рішення: постійно та терпляче наголошувати, що «ь» — це лише мовчазна інструкція, дорожній знак для попередньої літери, а не самостійний звук, який має право голосу [S9]. |
| Штучна пауза (різке гортанне зімкнення) на місці апострофа: [п'ят'] виголошується як [п — ят'] | Плавний, але роздільний перехід від твердого приголосного до [й]: [пйат'] | Англомовні мовці підсвідомо сприймають апостроф як прямий сигнал для різкої зупинки потоку повітря (glottal stop), подібно до того, як це відбувається в діалектній вимови слова «bottle» [<!-- VERIFY: Гортанне зімкнення в L2 -->]. Рішення: чітко пояснювати, що український апостроф вимагає збереження безперервного потоку дихання і виголошення звуку [й], а не повної фонетичної зупинки [S9]. |
| Написання апострофа замість м'якого знака у міжнародних словах типу «мільйон» (помилково: міл'йон) | Нормативне написання «мільйон» | Учні логічно плутають функцію розділення й пом'якшення в словах іншомовного походження. Однак українські підручники строго зазначають, що перед буквосполученням «йо» завжди пишеться м'який знак, і ніколи не апостроф (батальйон, бульйон, мільйон, каньйон) [S6]. Рішення: для початкового рівня А1 давати такі слова виключно як цілісні словникові одиниці, не перевантажуючи учня надмірною теорією [S1]. |

Ці помилки не є ознакою неуважності учня; вони є природним наслідком перенесення фонетичної бази рідної мови на українську. Розуміння цих механізмів дозволяє автору-письменнику створювати емпатичний і дієвий навчальний контент.

### Archived module contrasts

- distractor: Є апо́строф. — There is an apostrophe.
- distractor: Ї завжди [йі]. — Ї is always [йі].
- distractor: Р зникає. — Р disappears.
- distractor: Додає звук [і]. — It adds the sound [і].
- distractor: Мовчить. — It is silent.
- distractor: Це м'яки́й знак. — It is the soft sign.
- ❌ сімя → ✅ сім'я́
- ❌ ден → ✅ день
- ❌ св'ято → ✅ свя́то
- ❌ льожка → ✅ ло́жка
- ❌ пять → ✅ п'ять
- ❌ бурян → ✅ бур'я́н
- distractor: сімя
- distractor: ден
- distractor: св'ято

## Learner state before this lesson

(This is the first module — no prior learner knowledge.)
Previously introduced in this module: []

## Deterministic lessons.yaml (read-only)

lessons:
- n: 1
  title: 'М''яки́й знак (Ь) та африка́ти: Лі́тери Ь, Ц, Ч · Soft Sign (Ь) and Affricates:
    Letters Ь, Ц, Ч'
  sections:
  - М'який знак
  - Африкати Ц та Ч
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
  title: 'Йото́вані лі́тери та напівголосни́й: Лі́тери Й, Я, Ю, Є · Iotated Vowels
    and Semivowel: Letters Й, Я, Ю, Є'
  sections:
  - Йотовані голосні
  - Буква Й та етикетні формули
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
  title: 'За́вжди два зву́ки: Лі́тери Ї, Щ та лі́тера Ф · Always Two Sounds: Letters
    Ї, Щ and Letter Ф'
  sections:
  - 'Завжди два звуки: Ї та Щ'
  - Буква Ф та повний спектр вітань
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
  title: 'Апо́строф і три ключові́ контра́сти: буря́к, бур''я́н, свя́то · The Apostrophe
    and Three Key Contrasts: буря́к, бур''я́н, свя́то'
  sections:
  - Апостроф
  - Контраст і пастки
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
- n: 5
  title: Пра́вила перено́су слів та си́нтез особли́вих зна́ків · Word Hyphenation
    Rules and Special Signs Synthesis
  sections:
  - Перенос і письмо
  - Далі
  - Підсумок модуля
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
  unverified_stress:
  - Мар'я́но
  unverified_lemmas: []
closes_module: 5
provenance:
- placement: inline
  index: 0
  new_id: act-1
  lesson: 4
- placement: inline
  index: 1
  new_id: act-2
  lesson: 1
- placement: inline
  index: 2
  new_id: act-3
  lesson: 4
- placement: inline
  index: 3
  new_id: act-4
  lesson: 4
- placement: inline
  index: 4
  new_id: act-5
  lesson: 5
- placement: workbook
  index: 0
  new_id: act-w1
  lesson: 4
- placement: workbook
  index: 1
  new_id: act-w2
  lesson: 4
- placement: workbook
  index: 2
  new_id: act-w3
  lesson: 4
- placement: workbook
  index: 3
  new_id: act-w4
  lesson: 4
- placement: workbook
  index: 4
  new_id: act-w5
  lesson: 5
- placement: workbook
  index: 5
  new_id: act-w6
  lesson: 5
- placement: workbook
  index: 6
  new_id: act-w7
  lesson: 5
items_min_exempt:
- id: act-1
  reason: 3-item original activity preserved from baseline
- id: act-2
  reason: 5-item original activity preserved from baseline
- id: act-3
  reason: 4-item original activity preserved from baseline
- id: act-4
  reason: 4-item original activity preserved from baseline
- id: act-5
  reason: 4-item original activity preserved from baseline
- id: act-w2
  reason: 4-item original activity preserved from baseline
- id: act-w4
  reason: 4-item original activity preserved from baseline
- id: act-w5
  reason: 5-item original activity preserved from baseline
- id: act-w6
  reason: 3-item original activity preserved from baseline
- id: act-w7
  reason: 3-item original activity preserved from baseline
proper_names:
- Київ
- Україна
- Мар'яна
- Софія
- Марко
- Вашуленко
- Захарійчук
- Большакова
- Пристинська
- Авраменко
- Оксана
- Тарас
- Анна
- Огойко
- Мар'я́но


## Original plan (read-only)

module: a1-003
level: A1
sequence: 3
slug: special-signs
version: 1.4.2
letter_module: true
lifecycle: locked
reviewed_at: '2026-04-23T09:32:45Z'
reviewed_by: codex-scale-special-signs
review_notes: 'Review-and-lock pass per the #1412 rubric template (docs/best-practices/wiki-plan-review-and-lock.md).
  Plan-side findings: the prior plan drifted outside the slug by teaching voiced/voiceless
  pairs, Г/Ґ, Р, and И inside `special-signs`, while the paired wiki is specifically
  about `ь` + apostrophe. Fixed by re-scoping the plan to special signs only, adding
  hooks for the locked wiki''s key contrasts (`буряк` / `бур''ян` / `свято` / `цвях`),
  adding a transfer block (`Мар''-яна`, `дере-в''яний`), mirroring the wiki''s `Типові
  помилки L2` table in activity_hints, and adding lifecycle markers plus a wiki back-reference.
  Scan clean for Russianisms, calques, homoglyphs, and word-count contradictions.'
title: Особливі знаки
subtitle: Ь, апостроф і три ключові контрасти - день, сім'я, буряк/бур'ян
focus: phonetics
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
word_target: 1200
objectives:
- Розуміти, як `я`, `ю`, `є`, `ї` працюють як передумова для м'якого знака й апострофа
- Читати й писати базові слова з м'яким знаком (`день`, `кінь`, `сіль`, `вчитель`)
- Читати й писати базові слова з апострофом (`сім'я`, `м'ясо`, `п'ять`, `комп'ютер`)
- Розрізняти три сценарії - м'якість без апострофа (`буряк`), апостроф (`бур'ян`)
  і зону без апострофа після збігу приголосних (`свято`, `цвях`)
- Користуватися готовими моделями переносу (`Мар'-яна`, `дере-в'яний`, `бур'-ян`,
  `паль-ці`)
- Впізнавати й виправляти типові L2-помилки - пропуск апострофа, механічне вставляння
  апострофа, пропуск `ь`, механічне `льожка`
content_outline:
- section: Йотовані голосні як передумова
  words: 250
  points:
  - 'Почати з короткого повторення: `я`, `ю`, `є` після приголосного без апострофа
    зазвичай пом''якшують його, а після апострофа читаються роздільно. `Ї` завжди
    дає `[йі]`. Без цього контрасту `ь` та апостроф зависають у повітрі як дві окремі
    "дивні букви".'
  - 'Показати найраніший набір слів-моделей: `буряк`, `люди`, `свято` проти `м''ята`,
    `сім''я`, `п''ять`. На цьому етапі не вчимо нове велике правило - лише ставимо
    слуховий маяк: "тут звук м''якшає", "тут чути `[й]`".'
- section: М'який знак
  words: 250
  points:
  - 'М''який знак не має власного звука. Він лише змінює попередній приголосний. Основні
    A1-слова: `день`, `кінь`, `сіль`, `вчитель`, `маленький`, `сьогодні`.'
  - 'Для контрасту дати 2-3 короткі пари: `стан` - `стань`, `лан` - `лань`, `рис`
    - `рись`. Саме такі пари показують, що `ь` не "читається", але без нього слово
    звучить і виглядає інакше.'
  - 'Авторова примітка: коротка шкільна мнемоніка `Де ти з''їси ці лини?` корисна
    лише як опора для ядра вправ; у повному орфографічному наборі для `ь` автор пам''ятає
    `д, т, з, с, ц, л, н, р, дз`, але не перевантажує цим учня на першому проході.'
- section: Апостроф
  words: 250
  points:
  - 'Базова A1-модель: апостроф після `б`, `п`, `в`, `м`, `ф`, `р` перед `я`, `ю`,
    `є`, `ї`. Перші слова: `сім''я`, `м''ясо`, `п''ять`, `дев''ять`, `ім''я`, `комп''ютер`.'
  - 'Найважливіше пояснення - апостроф не робить попередній звук м''яким, а навпаки
    не дає його пом''якшити: `м''я` = твердий `м` + `[йа]`. Саме це треба почути вголос
    і повторити кілька разів.'
  - Префіксний апостроф (`під'їзд`, `з'їзд`) згадуємо лише як пізнішу тему; не робимо
    з нього продуктивне правило цього модуля.
- section: Контраст і типові помилки L2
  words: 250
  points:
  - 'Центральний контраст модуля: `буряк` проти `бур''ян`. У першому слові `р` м''який
    і немає апострофа; у другому - апостроф утримує `р` твердим і після нього чути
    `[йа]`.'
  - 'Окремо дати "зону без апострофа": `свято`, `цвях`, `морквяний`. Тут апостроф
    не пишеться, хоча учень може чекати його механічно. Це готові приклади, а не правило
    для виведення з нуля.'
  - 'Усі activity_hints цього блоку повинні дзеркалити wiki "Типові помилки L2": пропуск
    апострофа у слові `сім''я`, механічний апостроф (`св''ято`), пропуск `ь` (`ден`),
    механічне `льожка`.'
- section: Перенос і підсумок
  words: 200
  points:
  - 'Закріпити, що `ь` та апостроф тримаються попередньої літери при переносі: `Мар''-яна`,
    `дере-в''яний`, `бур''-ян`, `паль-ці`. Додати правило: одну букву не залишаємо
    окремо і не переносимо саму.'
  - 'Самоперевірка: учень має вміти пояснити різницю між `день`, `сім''я`, `буряк`,
    `бур''ян`, `свято`; вставити знак у 4-5 словах; правильно поділити для переносу
    2-3 приклади.'
vocabulary_hints:
  author_note: 'У цьому модулі слова подаються як орфографічні та фонетичні чанки,
    а не як матеріал для відмінювання чи словотвору. НЕ робіть продуктивним префіксне
    правило апострофа, НЕ перетворюйте `буряк/бур''ян/свято` на повний урок з фонології,
    НЕ виводьте нові "аналогії" поза списком нижче без перевірки у VESUM. Мета модуля
    - стабілізувати три контрасти: `день`, `сім''я`, `буряк/бур''ян`.'
  required:
  - день (day) - soft sign after Н
  - кінь (horse) - soft sign after Н
  - сіль (salt) - soft sign after Л
  - вчитель (teacher) - soft sign in a common noun
  - сім'я (family) - apostrophe after М
  - м'ясо (meat) - apostrophe after М
  - п'ять (five) - apostrophe after П
  - комп'ютер (computer) - apostrophe in a common loanword
  - буряк (beetroot) - no apostrophe, soft Р before Я
  - бур'ян (weed) - apostrophe after Р
  - свято (holiday) - no apostrophe after consonant cluster
  - цвях (nail) - no apostrophe after consonant cluster
  recommended:
  - дев'ять (nine) - apostrophe after В
  - ім'я (name) - apostrophe after М
  - здоров'я (health) - apostrophe after В
  - маленький (small) - soft sign in a high-frequency adjective
  - сьогодні (today) - soft sign in a frequent adverb
  - Мар'яна (given name) - transfer model `Мар'-яна`
  - дерев'яний (wooden) - transfer model `дере-в'яний`
  - ложка (spoon) - counterexample against mechanical `льожка`
targets:
  new_vocabulary:
  - день
  - кінь
  - сіль
  - вчитель
  - сім'я
  - м'ясо
  - п'ять
  - комп'ютер
  - буряк
  - бур'ян
  - свято
  - цвях
  new_grammar: []
  recycle_vocabulary: []
activity_hints:
- type: fill-in
  focus: 'Додай `ь` або апостроф: сім_я, ден_, п_ять, комп_ютер, бур_ян, мален_кий'
  items: 6
- type: group-sort
  focus: 'Розподіли слова на три колонки: є `ь` / є апостроф / немає знака'
  items: 12
- type: match-up
  focus: 'З''єднай слово з поясненням контрасту: `буряк` = м''якість без апострофа,
    `бур''ян` = апостроф, `свято` = збіг приголосних без апострофа, `цвях` = збіг
    приголосних без апострофа'
  items: 4
- type: error-correction
  focus: 'Типові помилки L2 - виправте написання з пропущеним знаком: сім_я, п_ять,
    свято з апострофом, ден_, льожка'
  items: 6
- type: divide-words
  focus: 'Поділи слова для переносу: Мар''-яна, дере-в''яний, бур''-ян, паль-ці'
  items: 4
connects_to:
- a1-004 (Наголос та мелодика)
prerequisites:
- a1-001 (Звуки, літери та привіт)
- a1-002 (Читаємо українською)
grammar:
- 'Йотовані літери як передумова: `я`, `ю`, `є` після приголосного без апострофа зазвичай
  пом''якшують його; після апострофа читаються роздільно'
- '`Ї` завжди позначає `[йі]`; м''який знак перед нею не ставиться'
- М'який знак (`ь`) не має звука й пом'якшує попередній приголосний
- 'Для автора: повний набір приголосних для `ь` - `д, т, з, с, ц, л, н, р, дз`; для
  учня на A1 достатньо високочастотних моделей `день`, `кінь`, `сіль`, `вчитель`'
- 'Базова A1-модель апострофа: після `б`, `п`, `в`, `м`, `ф`, `р` перед `я`, `ю`,
  `є`, `ї`'
- 'Контраст `буряк` / `бур''ян` / `свято` як три окремі сценарії: м''якість без апострофа
  / апостроф / збіг приголосних без апострофа'
- 'Перенос: `ь` та апостроф не відриваються від попередньої літери; одну букву не
  залишаємо окремо'
register: розмовний
references:
- title: Захарійчук, 1 клас (НУШ 2025), стор. 97
  notes: 'Базове правило апострофа: після б, п, в, м, ф, р перед я, ю, є, ї.'
- title: Авраменко, 5 клас, стор. 75
  notes: М'який знак як показник м'якості приголосного; шкільне узагальнення про набір
    приголосних.
- title: Большакова, 2 клас, стор. 58-59
  notes: 'Апостроф і перенос слів: моделі `Мар''-яна`, `дере-в''яний`, `бур''-ян`.'
- title: 'Wiki: pedagogy/a1/special-signs (LOCKED 2026-04-23)'
  notes: Authoritative pedagogical brief - see the contrast block (`буряк` / `бур'ян`
    / `свято` / `цвях`), the writer note after "Словниковий мінімум", and the wiki
    "Типові помилки L2" table.
changelog:
- version: 1.4.0
  date: '2026-04-23'
  changes:
  - Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md. Added
    lifecycle markers (lifecycle/reviewed_at/reviewed_by/review_notes).
  - 'Re-scoped the plan to the actual slug: removed voiced/voiceless, Г/Ґ, Р, and
    И coverage that belonged to sibling phonetics modules; this plan now teaches only
    `ь` + apostrophe.'
  - 'Added explicit wiki-plan hooks for the locked wiki''s key contrasts: `буряк`
    / `бур''ян` / `свято` / `цвях`.'
  - Added a dedicated transfer block (`Мар'-яна`, `дере-в'яний`, `бур'-ян`, `паль-ці`)
    and a matching `divide-words` activity.
  - Added an `error-correction` activity that mirrors the wiki "Типові помилки L2"
    table and a wiki back-reference in references[].
- version: 1.4.1
  date: '2026-04-25'
  ref: '#1550'
  trigger: Letter-driven module needs explicit exception class for activity-count
    gates and pedagogical-stage reviewer calibration (a1/3 in alphabet/orthography
    exception class with a1/1 and a1/2).
  changes:
  - add letter_module flag (true) — allows higher activity counts for letter-recognition
    coverage; word-count target unchanged


## Existing module artifacts (read-only)

### module.md

# Особливі знаки

**день. сім'я́. буря́к. бур'я́н.** — four words, two signs, three
beginner contrasts.

The signs are small on the page, but they are not decorative. They tell your
mouth how to read the nearby letters.

Listen once before you write. A native Ukrainian teacher or tutor can say
**день**, **сім'я́**, **буря́к**, **бур'я́н**, and **свя́то**; you point to
the sign you hear on the page. If you are working alone, record your own voice
and compare it with the routine below.

Teacher Oksana's routine for this module is short: find the sign, say what it
does, then read the word once.

Keep the goal simple. You are not learning every spelling rule today. You are
learning these beginner contrasts:

- **день** — **ь** has no sound, but it softens the consonant before it;
- **сім'я́** — apostrophe keeps the previous consonant hard and lets you hear
  **[й]** before **я**;
- **буря́к / бур'я́н / свя́то / цвях** — sometimes **я** softens, sometimes
  apostrophe separates, and sometimes two consonants before **я** mean there is
  no apostrophe.

By the end, you can:

- recognize **ь** and apostrophe in common A1 words;
- read **день**, **кінь**, **сіль**, and **вчи́тель** without adding an extra
  vowel;
- read **сім'я́**, **м'я́со**, **п'ять**, and **комп'ю́тер** with **й** after
  the apostrophe;
- sort words into **м'яки́й знак**, **апо́строф**, and **без зна́ка**;
- choose the safer form when a visual habit creates a mistake.

## Йотовані голосні

**Я Ю Є Ї** — the four special vowel letters.

Earlier lessons introduced basic vowel letters. Here you only need the quick review
that makes **ь** and apostrophe readable.

At beginner level, use this rule:

| Position | Beginner reading habit |
| --- | --- |
| **я, ю, є** after a consonant with no apostrophe | the consonant becomes soft, then you read the vowel |
| **я, ю, є, ї** after an apostrophe | keep the previous consonant hard, then read **[й] + vowel** |
| **ї** anywhere | always **[йі]** |

Compare two words:

| Слово́ | Reading effect |
| --- | --- |
| **буря́к** | no apostrophe; **р** softens before **я** |
| **бур'я́н** | apostrophe; **р** stays hard, then you hear **[йа]** |

The apostrophe is a Ukrainian reading instruction: do not soften the previous
consonant; keep the next **й** sound.

Use one listening question before spelling. Say or hear the word slowly: do I
hear a separate **й** before **я, ю, є, ї**? If yes, apostrophe may be part of
the prepared spelling. If no, the vowel letter may simply soften the previous
consonant.

<!-- INJECT_ACTIVITY: act-1 -->

## М'яки́й знак

**Ь ь** — **м'яки́й знак**.

It has no sound of its own. It changes the consonant before it.

| Слово́ | English support | What to notice |
| --- | --- | --- |
| **день** | day | final **нь** is soft |
| **кінь** | horse | final **нь** is soft |
| **сіль** | salt | final **ль** is soft |
| **вчи́тель** | teacher | final **ль** is soft |

Do not read **ь** as **і**, **й**, or a tiny extra vowel. In **день**, stop on
soft **н**. In **сіль**, stop on soft **л**.

Short contrast pairs show the job. Treat them as sound examples, not new
vocabulary to memorize today:

| Without soft sign | With soft sign | Reading idea |
| --- | --- | --- |
| **стан** | **стань** | listen only for hard **н** vs soft **нь** |
| **лан** | **лань** | listen only for hard **н** vs soft **нь** |
| **рис** | **рись** | listen only for hard **с** vs soft **сь** |

These pairs are reading tools. You do not need to use all of them in
conversation today.

:::tip
**ь** points backward. It is a silent instruction for the consonant before it.
:::

<!-- INJECT_ACTIVITY: act-2 -->

## Апостроф

**'** — **апо́строф**.

Read it as a separation sign. It does not make a big pause. It keeps the
previous consonant hard and lets the next **я, ю, є, ї** start with **[й]**.

The first A1 model is:

**б, п, в, м, ф, р + апостроф + я, ю, є, ї**

Start with these words:

| Слово́ | English support | What to hear |
| --- | --- | --- |
| **сім'я́** | family | **м** stays hard, then **[йа]** |
| **м'я́со** | meat | **м** stays hard, then **[йа]** |
| **п'ять** | five | **п** stays hard, then **[йа]** |
| **де́в'ять** | nine | **в** stays hard, then **[йа]** |
| **ім'я́** | name | **м** stays hard, then **[йа]** |
| **комп'ю́тер** | computer | **п** stays hard, then **[йу]** |

Read **п'ять** smoothly, with a clear **й** sound. The airflow continues; the
spelling tells you to separate the consonant from the iotated vowel.

For now, do not build a large system from loanwords. **Комп'ю́тер** is useful
because learners know the object, but the lesson target is the apostrophe
itself.

<!-- INJECT_ACTIVITY: act-3 -->

## Контраст і пастки

**буря́к / бур'я́н / свя́то / цвях** — the central contrast.

| Scenario | Example | Beginner explanation |
| --- | --- | --- |
| softness with no apostrophe | **буря́к** | **р** softens before **я** |
| apostrophe | **бур'я́н** | **р** stays hard, then **[йа]** |
| two consonants before **я** with no apostrophe | **свя́то**, **цвях** | no apostrophe in these prepared words |

Mechanical spelling fails here. You cannot put apostrophe before every **я**.
You also cannot ignore apostrophe when it is written.

Use these safe decisions:

| If you see... | Do this |
| --- | --- |
| **день**, **кінь**, **сіль** | read the final consonant softly; add no extra vowel |
| **сім'я́**, **м'я́со**, **п'ять** | keep the consonant hard and read the following **й** |
| **буря́к** | no apostrophe; read soft **р** before **я** |
| **бур'я́н** | apostrophe; read hard **р** plus **[йа]** |
| **свя́то**, **цвях** | remember them as no-apostrophe words |

Common learner traps:

| Trap | Safer habit |
| --- | --- |
| dropping the apostrophe in the family word | write **сім'я́** |
| putting apostrophe into **свя́то** | keep **свя́то** with no apostrophe |
| writing **ден** for **день** | keep **ь** after **н** |
| inventing a soft-sign version of **ло́жка** | do not invent a soft sign or soft **л** |
| treating apostrophe as a hard stop | keep airflow and pronounce **й** |

Stay inside Ukrainian for this lesson. The apostrophe and soft sign already
have Ukrainian jobs, so you do not need another alphabet or another sign to
explain them.

<!-- INJECT_ACTIVITY: act-4 -->

## Перенос і письмо

You will sometimes see words split across a line in printed Ukrainian. At this
level, use only prepared models:

| Whole word | Safe line-break model |
| --- | --- |
| **Мар'я́на** | `Мар'-яна` |
| **дерев'я́ний** | `дере-в'яний` |
| **бур'я́н** | `бур'-ян` |
| **па́льці** | `паль-ці` |

The simple idea: **ь** and apostrophe stay with the letter before them. Also,
do not leave one single letter alone on a line.

Reading before writing: first recognize the printed word, then copy the sign in
a notebook cue.

Use original text on this page, your own notebook, or live handwriting from a
teacher/tutor.

| Printed word | Notebook cue |
| --- | --- |
| **день** | find the soft sign at the end |
| **сім'я́** | find the apostrophe before **я** |
| **п'ять** | find both apostrophe and soft sign |
| **свя́то** | confirm there is no apostrophe |

Ask a native Ukrainian teacher or tutor to listen to a short read-aloud:
**день, сім'я́, буря́к, бур'я́н, свя́то**. The feedback target is small:
soft ending, clear **й**, no invented pause.

Before you leave the lesson tab, check that you can do these things:

- say that **ь** has no sound of its own;
- read **день**, **кінь**, **сіль**, and **вчи́тель** without adding **і**;
- say that apostrophe keeps the previous consonant hard;
- read **сім'я́**, **м'я́со**, **п'ять**, and **комп'ю́тер** with **й** after
  the apostrophe;
- explain **буря́к** and **бур'я́н** with the support table;
- remember that **свя́то** and **цвях** have no apostrophe;
- choose the correct sign in short prepared words;
- identify missing-apostrophe, missing-soft-sign, and invented-soft-sign
  errors.

Use the signs as reading instructions, not decorations. Before moving on,
choose one word from each contrast and do a final sign check: name the sign,
state its effect, then read the word.

<!-- INJECT_ACTIVITY: act-5 -->

## Далі

**Далі** means next. Go to Vocabulary and Activities; those drills reuse the
same six contrast words: **день**, **сім'я́**, **буря́к**, **бур'я́н**,
**свя́то**, **цвях**.


### activities.yaml

---
inline:
  - id: act-1
    type: quiz
    title: М'яко чи розді́льно — Soft or separate
    instruction: Обери пояснення для читання. — Choose the explanation for reading.
    items:
      - prompt: Буря́к — що відбувається перед літерою я? — Буря́к — what happens before the letter я?
        options:
          - text: Р пом'якшується перед я. — Р softens before я.
            correct: true
          - text: Є апо́строф. — There is an apostrophe.
            correct: false
          - text: Ї завжди [йі]. — Ї is always [йі].
            correct: false
        explanation: У слові буря́к немає апо́строфа; р пом'якшується перед я. — In the word буря́к there is no apostrophe; р softens before я.
      - prompt: Бур'я́н — що робить апо́строф? — Бур'я́н — what does the apostrophe do?
        options:
          - text: Р зникає. — Р disappears.
            correct: false
          - text: Р залишається твердим, потім чути [йа]. — Р remains hard, then [йа] is heard.
            correct: true
          - text: Додає звук [і]. — It adds the sound [і].
            correct: false
        explanation: Апо́строф відділяє р від я. — The apostrophe separates р from я.
      - prompt: Ї — що завжди правильно? — Ї — what is always true?
        options:
          - text: Мовчить. — It is silent.
            correct: false
          - text: Це м'яки́й знак. — It is the soft sign.
            correct: false
          - text: Завжди [йі]. — Always [йі].
            correct: true
        explanation: Ї завжди позначає [йі]. — Ї always represents [йі].
  - id: act-2
    type: match-up
    title: Що робить ь
    instruction: З'єднай кожне слово з підказкою про м'яки́й знак.
    pairs:
      - left: день
        right: soft [n'] in «день»
      - left: кінь
        right: soft [n'] in «кінь»
      - left: сіль
        right: soft [l'] in «сіль»
      - left: вчи́тель
        right: soft [l'] in «вчи́тель»
      - left: ь (soft sign)
        right: has no sound of its own
  - id: act-3
    type: fill-in
    title: Додай знак — Add a sign
    instruction: Обери ь, апо́строф або без знака. — Choose ь, an apostrophe, or no sign.
    items:
      - sentence: сім___я
        answer: "'"
        options:
          - "'"
          - ь
          - без знака — no sign
      - sentence: ден___
        answer: ь
        options:
          - ь
          - "'"
          - без знака — no sign
      - sentence: п___ять
        answer: "'"
        options:
          - "'"
          - ь
          - без знака — no sign
      - sentence: У слові свя́то правильний вибір — ___ . — In the word "свя́то", the correct choice is […].
        answer: без знака — no sign
        options:
          - без знака — no sign
          - "'"
          - ь
  - id: act-4
    type: error-correction
    title: Виправ пастки — Correct the traps
    instruction: Обери правильну українську форму. — Choose the correct Ukrainian form.
    items:
      - sentence: Моя́ дру́жна сімя живе́ у Ки́єві.
        error: сімя
        correction: сім'я́
        options:
          - сім'я́
          - сімя
        explanation: У слові сім'я́ потрібен апо́строф. — In the word сім'я́ an apostrophe is needed.
      - sentence: Сього́дні га́рний і те́плий ден.
        error: ден
        correction: день
        options:
          - день
          - ден
        explanation: День потребує м'якого знака. — День requires a soft sign.
      - sentence: Сього́дні у мі́сті вели́ке св'ято.
        error: св'ято
        correction: свя́то
        options:
          - свя́то
          - св'ято
        explanation: У слові свя́то немає апо́строфа. — In the word свя́то there is no apostrophe.
      - sentence: На столі́ лежи́ть вели́ка льожка.
        error: льожка
        correction: ло́жка
        options:
          - ло́жка
          - льожка
        explanation: Ло́жка не має м'якого знака після л. — Ло́жка has no soft sign after л.
  - id: act-5
    type: divide-words
    title: Практика переносу слів
    instruction: Обери підготовлену модель переносу.
    items:
      - word: Мар'я́на
        answer: Мар'-яна
      - word: дерев'я́ний
        answer: дере-в'яний
      - word: бур'я́н
        answer: бур'-ян
      - word: па́льці
        answer: паль-ці
workbook:
  - type: group-sort
    title: Сортуй за знаком — Sort by sign
    instruction: Розподіли кожне слово в правильну групу. — Sort each word into the correct group.
    groups:
      - label: Є ь — Has ь
        items:
          - день
          - кінь
          - сіль
          - вчи́тель
          - мале́нький
      - label: Є апо́строф — Has apostrophe
        items:
          - сім'я́
          - м'я́со
          - п'ять
          - комп'ю́тер
          - бур'я́н
      - label: Немає знака — No sign
        items:
          - буря́к
          - свя́то
          - цвях
          - ло́жка
  - type: match-up
    title: Поясни контраст — Explain the contrast
    instruction: З'єднай слово з поясненням. — Match each word with its explanation.
    pairs:
      - left: буря́к
        right: 'м''я́кість без апо́строфа: р + я — softness without apostrophe: р + я'
      - left: бур'я́н
        right: 'апо́строф: р тверди́й, по́тім [йа] — apostrophe: hard р, then [йа]'
      - left: свя́то
        right: 'збіг св + я без апо́строфа — cluster св + я without apostrophe'
      - left: цвях
        right: 'збіг цв + я без апо́строфа — cluster цв + я without apostrophe'
  - type: error-correction
    title: Виправ усі пастки — Fix all traps
    instruction: Обери правильну українську форму. — Choose the correct Ukrainian form.
    items:
      - sentence: Це на́ша дру́жна сімя.
        error: сімя
        correction: сім'я́
        options:
          - сім'я́
          - сімя
        explanation: У слові сім'я́ потрібен апо́строф. — In the word сім'я́ an apostrophe is needed.
      - sentence: У руці́ рі́вно пять па́льців.
        error: пять
        correction: п'ять
        options:
          - п'ять
          - пять
        explanation: У слові п'ять потрібен апо́строф. — In the word п'ять an apostrophe is needed.
      - sentence: На по́лі росте́ зеле́ний бурян.
        error: бурян
        correction: бур'я́н
        options:
          - бур'я́н
          - бурян
        explanation: У слові бур'я́н потрібен апо́строф після р. — In the word бур'я́н an apostrophe is needed after р.
      - sentence: Сього́дні ду́же те́плий ден.
        error: ден
        correction: день
        options:
          - день
          - ден
        explanation: День потребує м'якого знака. — День requires a soft sign.
      - sentence: Сього́дні у на́с весе́ле св'ято.
        error: св'ято
        correction: свя́то
        options:
          - свя́то
          - св'ято
        explanation: У слові свя́то немає апо́строфа. — In the word свя́то there is no apostrophe.
      - sentence: У су́пі лежи́ть вели́ка льожка.
        error: льожка
        correction: ло́жка
        options:
          - ло́жка
          - льожка
        explanation: Ло́жка не має м'якого знака після л. — Ло́жка has no soft sign after л.
  - type: true-false
    title: Факти про знаки — Facts about signs
    instruction: 'Обери: правда чи неправда. — Choose: true or false.'
    items:
      - statement: Ь не має власного звука. — Ь has no sound of its own.
        correct: true
        explanation: Він пом'якшує попередній при́голосний. — It softens the preceding consonant.
      - statement: Апо́строф тримає попередній при́голосний твердим. — The apostrophe keeps the preceding consonant hard.
        correct: true
        explanation: Він відділяє при́голосний від йотованої голосної. — It separates the consonant from the iotated vowel.
      - statement: Ї іноді мовчить. — Ї is sometimes silent.
        correct: false
        explanation: Ї завжди читаємо як [йі]. — We always read ї as [йі].
      - statement: Свя́то має апо́строф. — Свя́то has an apostrophe.
        correct: false
        explanation: Свя́то — модельне слово без апо́строфа. — Свя́то is a model word without an apostrophe.
  - type: fill-in
    title: Додай знак у нових словах
    instruction: Обери ь, апо́строф або без знака.
    items:
      - sentence: бур___ян
        answer: "'"
        options:
          - "'"
          - ь
          - без знака — no sign
      - sentence: комп___ютер
        answer: "'"
        options:
          - "'"
          - ь
          - без знака — no sign
      - sentence: ім___я
        answer: "'"
        options:
          - "'"
          - ь
          - без знака — no sign
      - sentence: У слові мален_кий потрібен ___ . — In the word "мален_кий", […] is needed.
        answer: ь
        options:
          - ь
          - "'"
          - без знака — no sign
      - sentence: У слові цвях правильний вибір — ___ . — In the word "цвях", the correct choice is […].
        answer: без знака — no sign
        options:
          - без знака — no sign
          - "'"
          - ь
  - type: quiz
    title: Правильна форма
    instruction: Обери правильно написане слово.
    items:
      - prompt: Сім'я́ — яка́ фо́рма пра́вильна? — Сім'я́ — which form is correct?
        options:
          - text: сім'я́
            correct: true
          - text: сімя
            correct: false
        explanation: Сім'я́ потребує апо́строфа.
      - prompt: День — яка́ фо́рма пра́вильна? — День — which form is correct?
        options:
          - text: ден
            correct: false
          - text: день
            correct: true
        explanation: День потребує м'якого знака.
      - prompt: Сло́во без апо́строфа? — Which word is without an apostrophe?
        options:
          - text: св'ято
            correct: false
          - text: свя́то
            correct: true
        explanation: У слові свя́то немає апо́строфа.
  - type: odd-one-out
    title: Зайве за знаком
    instruction: Обери слово, яке не має такого самого знака, як інші.
    items:
      - words:
          - сім'я́
          - м'я́со
          - п'ять
          - буря́к
        answer: буря́к
        explanation: Буря́к без апо́строфа; інші слова мають апо́строф.
      - words:
          - день
          - кінь
          - сіль
          - свя́то
        answer: свя́то
        explanation: Свя́то без ь; інші слова мають м'який знак.
      - words:
          - буря́к
          - свя́то
          - цвях
          - бур'я́н
        answer: бур'я́н
        explanation: Бур'я́н має апо́строф; інші слова тут без знака.


### vocabulary.yaml

- lemma: м'яки́й знак
  translation: soft sign
  pos: noun phrase
  usage: Ь - м'яки́й знак.
- lemma: апо́строф
  translation: apostrophe
  pos: noun
  usage: У сло́ві «сім'я́» є апо́строф.
- lemma: знак
  translation: sign
  pos: noun
  usage: Це знак.
- lemma: м'яки́й
  translation: soft
  pos: adjective
  usage: Це м'яки́й звук.
- lemma: тверди́й
  translation: hard
  pos: adjective
  usage: Це тверди́й звук.
- lemma: йото́ваний
  translation: iotated
  pos: adjective
  usage: Я - йото́вана лі́тера.
- lemma: розді́льно
  translation: separately
  pos: adverb
  usage: Чита́й розді́льно.
- lemma: зли́то
  translation: together / smoothly
  pos: adverb
  usage: Чита́й зли́то.
- lemma: день
  translation: day
  pos: noun
  usage: День.
- lemma: кінь
  translation: horse
  pos: noun
  usage: Кінь.
- lemma: сіль
  translation: salt
  pos: noun
  usage: Сіль.
- lemma: вчи́тель
  translation: teacher
  pos: noun
  usage: Вчи́тель.
- lemma: сім'я́
  translation: family
  pos: noun
  usage: Сім'я́.
- lemma: м'я́со
  translation: meat
  pos: noun
  usage: М'я́со.
- lemma: п'ять
  translation: five
  pos: numeral
  usage: П'ять.
- lemma: де́в'ять
  translation: nine
  pos: numeral
  usage: Де́в'ять.
- lemma: ім'я́
  translation: name
  pos: noun
  usage: Ім'я́.
- lemma: здоро́в'я
  translation: health
  pos: noun
  usage: Здоро́в'я.
- lemma: комп'ю́тер
  translation: computer
  pos: noun
  usage: Комп'ю́тер.
- lemma: буря́к
  translation: beetroot
  pos: noun
  usage: Буря́к.
- lemma: бур'я́н
  translation: weed
  pos: noun
  usage: Бур'я́н.
- lemma: свя́то
  translation: holiday
  pos: noun
  usage: Свя́то.
- lemma: цвях
  translation: nail
  pos: noun
  usage: Цвях.
- lemma: мале́нький
  translation: small
  pos: adjective
  usage: Мале́нький знак.
- lemma: сього́дні
  translation: today
  pos: adverb
  usage: Сього́дні свя́то.
- lemma: ло́жка
  translation: spoon
  pos: noun
  usage: Ло́жка.
- lemma: Мар'я́на
  translation: Mariana
  pos: proper noun
  usage: Мар'я́на.
- lemma: дерев'я́ний
  translation: wooden
  pos: adjective
  usage: Дерев'я́ний стіл.
- lemma: па́льці
  translation: fingers
  pos: noun
  usage: Па́льці.


### resources.yaml

- title: Захарійчук, 1 клас (НУШ 2025), p. 97
  role: textbook
  source_ref: Захарійчук, 1 клас (НУШ 2025), p. 97
  notes: 'Plan reference: basic apostrophe rule before я, ю, є, ї.'
- title: Большакова, 2 клас, p. 58-59
  role: textbook
  source_ref: Большакова, 2 клас, p. 58-59
  notes: 'Apostrophe as hard consonant + [йа], and transfer models Мар''-яна / Дере-в''яний.'
- title: Вашуленко, 3 клас, p. 90
  role: textbook
  source_ref: Вашуленко, 3 клас, p. 90
  notes: 'Line-break rule: apostrophe is not separated from the previous letter.'


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
