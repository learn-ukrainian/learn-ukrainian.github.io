# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: things-have-gender.
Your current published unit: lesson 2.

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
Previously introduced in this module: ["рід", "іме́нник", "хто це?", "що це?", "він", "вона́", "воно́", "мій", "моя́", "моє́", "стіл", "кни́га", "вікно́", "мі́сто", "та́то", "ба́тько", "соба́ка", "Мико́ла"]

## Deterministic lessons.yaml (read-only)

lessons:
- n: 1
  title: Він, вона, воно
  sections:
  - Діалоги
  - Він, вона, воно
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
  title: Предмети навколо
  sections:
  - Предмети навколо
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
  - Імена, пастки й самоперевірка
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
  new_id: act-5
  lesson: 1
- placement: inline
  index: 4
  new_id: act-4
  lesson: 2
- placement: inline
  index: 5
  new_id: act-9
  lesson: 3
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
  lesson: 3
items_min_exempt:
- id: act-9
  reason: 4-item original activity preserved from baseline
- id: act-w5
  reason: 5-item original activity preserved from baseline
proper_names: []


## Original plan (read-only)

module: a1-008
level: A1
sequence: 8
slug: things-have-gender
version: 1.2.0
lifecycle: locked
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-things-have-gender
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md
  (rubric template from PR #1412 `at-the-cafe` + PR #1436 `who-am-i`). See PR body
  for the full plan-side findings (pragmatic / Russianism / calque / contradiction
  / references / wiki-alignment) and wiki/.reviews/pedagogy/a1/things-have-gender-review-LOCKED.md
  for the wiki-side report. Plan brought into alignment with the locked wiki: (1)
  gender-flip objective added (`біль` ч.р. / `степ` ч.р. as demo pairs); (2) feminitive
  pairs (`вчителька`, `лікарка`) added as recommended vocab to mirror wiki Декол.
  #4; (3) gender-flip drill added as new quiz activity_hint mirroring wiki "Типові
  помилки L2" table + Exercise 5; (4) chunk-guidance writer-note in content_outline
  (`мій стіл / моя ручка / моє вікно / велике яблуко / синє море` as indivisible chunks);
  (5) wiki back-reference added.'
title: Речі мають рід
subtitle: він, вона, воно — кожен іменник має рід
focus: grammar
pedagogy: PPP
phase: A1.2 [Мій світ]
word_target: 1200
objectives:
- Визначати рід іменників за допомогою тесту він/вона/воно
- Розпізнавати рід за закінченнями слів (приголосний = ч, -а/-я = ж, -о/-е = с)
- Називати понад 20 поширених предметів із правильним родом
- Використовувати конструкцію "У мене є" з предметами (розширення теми родини з модуля
  модуль №6)
- Застосовувати український тест `він/вона/воно` до будь-якого іменника — зокрема
  там, де інтуїція з іншої мови могла б дати неправильну відповідь (діагностична міні-вправа
  з 5 пунктів; детальна таблиця у wiki «Типові помилки L2»)
- Використовувати фемінітив як основну форму професії для жінки (`вчителька`, `лікарка`)
dialogue_situations:
- setting: 'Вдома або під час відеодзвінка з демонстрацією кімнати. Учні вказують
    на повсякденні предмети та вживають із ними слова він/вона/воно: стіл, книга,
    вікно, лампа, ліжко, телефон, а також кілька знайомих домашніх улюбленців чи речей,
    як-от кіт та дзеркало.'
  speakers:
  - Марія
  - Оленка
  motivation: Займенники він/вона/воно з іменниками, що позначають кімнату та предмети
    побуту, такі як стіл, книга, вікно, лампа, ліжко, телефон, а також кілька знайомих
    живих істот, наприклад, кіт
content_outline:
- section: Діалоги
  words: 300
  points:
  - 'Діалог 1 — Відеодзвінок із демонстрацією кімнати: — Привіт! Дивись, це моя кімната.
    — Класно! У тебе є стіл? — Так, у мене є стіл і ліжко. Рід виникає природно через
    словосполучення мій стіл, моя кімната, моє ліжко.'
  - Діалог 2 — Що у твоїй сумці? — Що у тебе є? — У мене є книга, телефон і фото.
    — А у мене є ручка і зошит.
- section: Він, вона, воно
  words: 300
  points:
  - 'Пономарова, 3 клас, с. 86: Українські іменники мають рід. Тест: чи можете ви
    замінити іменник на він, вона або воно? Чоловічий рід: стіл — він. Можна додати:
    мій стіл. Жіночий рід: книга — вона. Можна додати: моя книга. Середній рід: вікно
    — воно. Можна додати: моє вікно.'
  - 'Вашуленко, 3 клас, с. 112 — закінчення за родами: Чоловічий: зазвичай закінчується
    на приголосний — стіл, телефон, зошит. Жіночий: зазвичай закінчується на -а або
    -я — книга, лампа, кімната, ручка. Середній: зазвичай закінчується на -о або -е
    — вікно, ліжко, крісло, місто. Це охоплює ~90% іменників. Винятки (наприклад,
    слова на -ь) вивчатимуться пізніше.'
- section: Предмети навколо
  words: 300
  points:
  - 'Лексика кімнати, згрупована за родами: Чоловічий: стіл, стілець, телефон, комп''ютер,
    зошит, ключ. Жіночий: книга, лампа, сумка, ручка, кімната, стіна. Середній: вікно,
    ліжко, крісло, дзеркало, фото.'
  - 'Поширення конструкції "У мене є" з модуля модуль №6 (родина) на предмети: У мене
    є стіл. У мене є книга. У мене є вікно. Та сама модель, нова лексика.'
- section: Підсумок
  words: 300
  points:
  - 'Визначення роду в 3 кроки: 1. Скажіть він/вона/воно з іменником — що підходить?
    2. Перевірте закінчення — приголосний? -а/-я? -о/-е? 3. Використовуйте правильний
    присвійний займенник — мій/моя/моє. Самоперевірка: Якого роду слово "стіл"? Якого
    роду слово "книга"? А як щодо "вікно"? Скажіть українською, що у вас є стілець.'
  - 'УВАГА до автора: (а) на A1 подавати `мій стіл / моя ручка / моє вікно / велике
    яблуко / синє море` як неподільні чанки — НЕ пояснювати повну парадигму відмінювання
    прикметників, тверду/м''яку групу, узгодження у множині чи відмінювання присвійних
    займенників. (б) Діагностична gender-flip міні-вправа (activity_hints[4], 5 пунктів)
    — короткий фінальний дрил на 5 хвилин, що дзеркалить п''ять рядків wiki «Типові
    помилки L2». НЕ робити з неї окрему повноцінну лексичну тему: слова `біль`, `степ`,
    `розпис`, `літопис`, `путь` — діагностичні опори, не module vocab. (в) Для професій
    (`вчителька`, `лікарка`) використовувати фемінітив як основну форму, коли мова
    про жінку, — не «Вона — лікар».'
vocabulary_hints:
  required:
  - стіл (table, m)
  - книга (book, f)
  - вікно (window, n)
  - кімната (room, f)
  - ліжко (bed, n)
  - стілець (chair, m)
  - лампа (lamp, f)
  - телефон (phone, m)
  - комп'ютер (computer, m)
  - він, вона, воно (he, she, it — gender test words)
  recommended:
  - зошит (notebook, m)
  - ручка (pen, f)
  - сумка (bag, f)
  - крісло (armchair, n)
  - дзеркало (mirror, n)
  - ключ (key, m)
  - фото (photo, n)
  - стіна (wall, f)
  - вчителька / учителька (teacher, f — feminitive, VESUM-verified; mirror of вчитель
    / учитель m)
  - лікарка (doctor, f — feminitive, VESUM-verified; mirror of лікар m)
activity_hints:
- type: group-sort
  focus: Розподіліть предмети за родами (чоловічий/жіночий/середній)
  items: 12
- type: quiz
  focus: Він, вона чи воно? Виберіть для кожного іменника.
  items: 8
- type: fill-in
  focus: мій/моя/моє ___ (доберіть присвійний займенник до іменника)
  items: 8
- type: quiz
  focus: Який рід? Подивіться на закінчення.
  items: 6
- type: quiz
  focus: Gender-flip diagnostic — оберіть український займенник (він / вона / воно).
    Дзеркалить п'ять рядків wiki "Типові помилки L2" + Приклад 5 один-до-одного (AC-3
    drift check). Усі правильні відповіді перевірено в VESUM.
  items:
  - question: Який у мене сильний ___ у плечі! (БІЛЬ)
    options:
    - він
    - вона
    - воно
    answer: він
  - question: Український ___ широкий і вітряний. (СТЕП)
    options:
    - він
    - вона
    - воно
    answer: він
  - question: Цей ___ на стіні — робота українського художника. (РОЗПИС)
    options:
    - він
    - вона
    - воно
    answer: він
  - question: Давній ___ «Повість временних літ» розповідає про Київську Русь. (ЛІТОПИС)
    options:
    - він
    - вона
    - воно
    answer: він
  - question: 'Книжне / урочисте: «У далеку ___» — форма ж.р. (ПУТЬ, зворотний напрям)'
    options:
    - він
    - вона
    - воно
    answer: вона
connects_to:
- a1-009 (Яке воно?)
prerequisites:
- a1-007 (Рубіж — Перший контакт)
grammar:
- 'Рід іменників: чоловічий (він, мій), жіночий (вона, моя), середній (воно, моє)'
- 'Визначення роду за закінченням: приголосний=ч, -а/-я=ж, -о/-е=с'
- Конструкція "У мене є", розширена на предмети (з теми родини у модулі №6)
- 'Діагностичний принцип: український рід визначає VESUM-парадигма + тест він/вона/воно.
  П''ять показових пар (`біль`, `степ`, `розпис`, `літопис`, `путь`) у wiki «Типові
  помилки L2» + quiz №5 в activity_hints.'
- 'Фемінітиви як основна форма назви професії для жінки: вчителька, лікарка (НЕ «Вона
  — вчитель»)'
register: розмовний
references:
- title: Пономарова Grade 3, p.86
  notes: 'Тест на рід: він/мій, вона/моя, воно/моє.'
- title: Вашуленко Grade 3, p.112
  notes: 'Таблиця закінчень за родами: приголосний, -а/-я, -о/-е.'
- title: ULP Season 1, Episode 6 — Gender naturally through family
  url: https://www.ukrainianlessons.com/episode6/
  notes: Рід природно випливає з уже вивчених присвійних займенників.
- title: 'Wiki: pedagogy/a1/things-have-gender (LOCKED 2026-04-23)'
  notes: Authoritative pedagogical brief — see the four-step sequence (Крок 1-4),
    the animate-masculine exceptions block (`тато`, `дядько`, `Микола`), the Словниковий
    мінімум table (VESUM-cited), the "Типові помилки L2" gender-flip table (9 rows,
    every pair evidenced by VESUM presence of the Ukrainian form + VESUM absence of
    the Russian counterpart), the feminitive decolonization point (#4), and Приклад
    5 (gender-flip drill). The writer-note block pinning `мій стіл` / `моя ручка`
    / `моє вікно` / `велике яблуко` / `синє море` as indivisible chunks is load-bearing
    — do NOT teach adjective declension, hard/soft group, or plural agreement at this
    level.
changelog:
- version: 1.2.0
  date: '2026-04-23'
  changes:
  - 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md (rubric
    template: at-the-cafe #1412, who-am-i #1436).'
  - Added lifecycle markers (lifecycle / reviewed_at / reviewed_by / review_notes).
  - 'Added two objectives: (a) diagnostic принцип «український тест він/вона/воно
    + VESUM-парадигма» (5-item mini-drill); (b) feminitive as primary form for female
    professions.'
  - 'Added feminitive pairs `вчителька / учителька`, `лікарка` to recommended vocabulary_hints
    — mirrors locked wiki Декол. #4. Gender-flip demo words (`біль`, `степ`, `розпис`,
    `літопис`, `путь`) are intentionally NOT in vocabulary_hints — they live only
    in activity_hints[4] quiz items as diagnostic props (writer-note in Підсумок makes
    this explicit).'
  - 'Added two grammar items: (a) diagnostic principle + five demo pairs; (b) feminitive
    as primary form. Each mapped to new objectives.'
  - Added fifth activity_hint (gender-flip quiz, 5 enumerated items one-to-one with
    wiki Типові помилки L2 five rows) — satisfies rubric AC-3 drift check.
  - 'Added writer-note in section Підсумок: five indivisible chunks (`мій стіл` etc.);
    gender-flip treated as short diagnostic mini-drill mirroring wiki; feminitive-first
    rule for female professions.'
  - Added wiki back-reference to references list.
  - 'Post-Codex-adversarial-review tightening: (a) wiki Типові помилки L2 table shrunk
    9 → 5 rows (addresses Goroh нестандартне-form nuance for `ярмарка` and rubric
    AC-3 compliance); (b) objective 5 rephrased from "не переносити рід з російської"
    → positive-framing "застосовувати український тест … зокрема там, де інтуїція
    з іншої мови могла б дати неправильну відповідь" (reduces D3 rubric-cap risk);
    (c) grammar item 4 similarly rephrased; (d) `кір` removed from wiki Exercise 5
    (off-scope A1) — replaced with `розпис`; (e) `ярмарок` dropped from both wiki
    table and plan/wiki exercises; (f) Anglicism `Мірор` → `Дзеркалить` fixed.'


## Existing module artifacts (read-only)

### module.md

# Речі мають рід

English has "he," "she," and "it." Ukrainian also has **він**, **вона**,
and **воно**, but Ukrainian uses them for every noun, including things in your
room. A table is **він**. A book is **вона**. A window is **воно**.

By the end, you can:

- ask whether a word is a person or a thing with **Хто це?** and **Що це?**;
- test common nouns with **він / вона / воно**;
- use the easy ending signals: consonant = usually masculine, **-а / -я** =
  usually feminine, **-о / -е** = usually neuter;
- say simple room and bag lines with **У мене є...**;
- choose **мій / моя / моє** as a whole phrase with a noun;
- use **вчителька** and **лікарка** when the person is a woman;
- repair the most common A1 gender traps without comparing Ukrainian to any
  other language.

Keep the goal small. You are not learning a full adjective or case system.
You are learning to store a noun with its gender cue.

:::tip
Treat gender as part of the noun card. Do not ask, "Who owns it?" Ask, "What
phrase travels with this noun: **мій**, **моя**, or **моє**?"
:::

<!--
Крок 1. Концепція «Хто?» і «Що?» та базові займенники. Спочатку вводиться концепція іменника як слова, що називає предмет. Учні вчаться розрізняти питання «Хто?» (істоти: людина, тварина) і «Що?» (неістоти: предмети, явища) [S5]. На цьому ж етапі вводяться особові займенники «він», «вона», «воно». Завдання автора-письменника — створити достатню кількість вправ, де учні просто тренуються ставити правильне питання до зображення чи слова [S5].
Крок 2. Рід істот (біологічна стать дорівнює граматичному роду). Наступний крок — пояснити рід на прикладі людей. Тут англомовному учневі найлегше, адже граматичний рід збігається з біологічною статтю. Використовуються слова-маркери «мій/він» для чоловіків (тато, брат, син, співак) та «моя/вона» для жінок (мати, сестра, дочка, співачка) [S2]. Важливо показати, як утворюються парні назви істот, наприклад: малюк — маля, соліст — солістка [S2]. На цьому етапі учні вчаться конструкціям на кшталт «Це мій брат Назар. Він архітектор» або «Це моя сестра Оксана. Вона студентка» [S8]. Обов'язково вказується правильна форма: тато, а не російський відповідник [S8].
Крок 3. Перенесення категорії роду на неістоти. Це критичний момент. Потрібно прямо заявити: «В українській мові стіл — це він, книга — це вона, а вікно — це воно». Для цього використовуємо слова з максимально прозорими фонетичними закінченнями [S9]. Чоловічий рід: приголосний звук (олівець, будинок, колектив, ячмінь) [S3]. Жіночий рід: закінчення -а, -я (земля, країна, мати) [S5]. Середній рід: закінчення -о, -е (сонце) [S5]. Учні тренуються замінювати слова на «він», «вона», «воно» [S1].
Крок 4. Засвоєння маркерів-закінчень як системи. Після того як концепція засвоєна, подаються таблиці типових закінчень. Учні дізнаються, що іменники, до яких можна додати слова «мій, він» (наприклад: тато, батько, ранок, січень), є іменниками чоловічого роду [S2]. Іменники зі словами «моя, вона» (мати, бабуся, річка, зима) — жіночого роду [S2]. А слова «моє, воно» (маля, серце, життя, літо) — середнього [S2]. На цьому етапі вводяться вправи на категоризацію слів за колонками (Ч.р., Ж.р., С.р.) [S1].
Крок 5. Винятки та слова спільного роду. Лише коли базова система закріпилася, можна переходити до ускладнень. Слід пояснити, що деякі чоловічі імена (Микола, Ілля, Михайло, Павло, Петро, Данило) закінчуються на -а/-я/-о, але залишаються чоловічого роду, оскільки позначають чоловіків [S8]. Також вводяться такі слова як батько, тато, дядько, що мають нетипове для чоловічого роду закінчення -о [S8]. Додається інформація про те, що слово собака в українській мові належить до чоловічого роду (на відміну від російської) [S8]. Згодом, на рівні А2-В1, можна вводити поняття іменників спільного роду (базікало, вереда) [S4].
Мій книга, мій ручка -> Моя книга, моя ручка. Де стіл? — Воно там. -> Де стіл? — Він там. Це моя тато. / Вона Микола. -> Це мій тато. / Він Микола. Моя собака дуже гарна. -> Мій собака дуже гарний. Я є студент. / Моє ім'я є Джон. -> Я студент. / Мене звати Джон.
Не пояснювати рід чи відмінювання українських слів через порівняння з російською. Собака в українській мові належить до чоловічого роду: він, мій собака. Уникати слова папа замість нормативного тато або батько. Не наводити англомовні фонетичні аналогії, які спотворюють українські звуки. Використовувати Добрий день і До побачення.
-->

## Діалоги

<!-- INJECT_ACTIVITY: act-1 -->

### Питальні слова

Start with the noun question.

| Question | Use it for | Examples |
| --- | --- | --- |
| **Хто це?** | a person or animal | **тато**, **сестра**, **кіт** |
| **Що це?** | a thing or place | **стіл**, **книга**, **вікно** |

In family words, gender often feels familiar:

| Ukrainian | Gender test | My phrase |
| --- | --- | --- |
| **тато** | **він** | **мій тато** |
| **брат** | **він** | **мій брат** |
| **сестра** | **вона** | **моя сестра** |
| **мама** | **вона** | **моя мама** |

But things also have gender:

| Ukrainian | English | Gender test | My phrase |
| --- | --- | --- | --- |
| **стіл** | table | **він** | **мій стіл** |
| **книга** | book | **вона** | **моя книга** |
| **вікно** | window | **воно** | **моє вікно** |

<!-- INJECT_ACTIVITY: act-2 -->

Do not ask whether the speaker is a man or a woman. Ask what gender the
Ukrainian noun has. **Мій стіл** is the same if the owner is Olena, Marko, or
you.

## Він, вона, воно

<!--
По-друге, необхідно пильнувати за лексичним наповненням. Наприклад, слово «собака» в українській мові належить винятково до чоловічого роду (він, мій собака) [S8]. Вживання його в жіночому роді є поширеним русизмом і наслідком мовної інтерференції, якого автори матеріалів повинні суворо уникати [S8]. Так само слід уникати використання слова «папа» замість нормативного тато або батько [S8].
-->

The fastest A1 habit is the **він / вона / воно** test. Endings help you guess
when the word is new.

| Signal | Usually | Examples |
| --- | --- | --- |
| consonant ending | **він**, **мій** | **стіл**, **телефон**, **зошит**, **ключ** |
| **-а / -я** | **вона**, **моя** | **книга**, **лампа**, **кімната**, **ручка** |
| **-о / -е** | **воно**, **моє** | **вікно**, **ліжко**, **дзеркало**, **море** |

At A1, this covers the clear everyday words you need. Some nouns are not clear
from the ending. You have already seen one important pattern: **тато** and
**батько** are masculine because they name a male person. Later you will learn
more exceptions. Today you only need a safe beginner reaction: if a word does
not fit the easy pattern, learn it as a phrase.

<!-- INJECT_ACTIVITY: act-5 -->

:::tip
The ending rule is a first guess, not a debate. If this lesson gives you a safe
phrase such as **мій тато** or **мій собака**, store the whole phrase.
:::

One high-value exception is **собака**. In Ukrainian, use **він** and
**мій собака**. For father, keep the course words **тато** and **батько**.
Do not replace them with **папа** in these A1 lines.

Keep these phrases whole:

| Phrase | Meaning |
| --- | --- |
| **мій стіл** | my table |
| **моя ручка** | my pen |
| **моє вікно** | my window |
| **велике яблуко** | a big apple |
| **синє море** | a blue sea |

Those last two phrases preview the next module. Do not turn them into a full
adjective table yet.

<!-- INJECT_ACTIVITY: act-3 -->

## Предмети навколо

Use **У мене є...** from the family module with objects. Read the Ukrainian
dialogue first. Use the support table after the dialogue to check meaning.

```text
Марія: Привіт! Дивись, це моя кімната.
Оленка: Класно! У тебе є стіл?
Марія: Так, у мене є стіл і ліжко.
Оленка: А це твоя лампа?
Марія: Так. Це моя лампа. Вона тут.
Оленка: А вікно?
Марія: Ось воно. Моє вікно велике.
```

Support after the dialogue:

| Українська | English support |
| --- | --- |
| **Привіт!** | Hi! |
| **Дивись, це моя кімната.** | Look, this is my room. |
| **У тебе є стіл?** | Do you have a table? |
| **У мене є стіл і ліжко.** | I have a table and a bed. |
| **А це твоя лампа?** | And is this your lamp? |
| **Вона тут.** | It is here. The word **лампа** chooses **вона**. |
| **Ось воно.** | Here it is. The word **вікно** chooses **воно**. |
| **Моє вікно велике.** | My window is big. |

Read the object lines again and notice the pronoun:

- **Де стіл? Він тут.**
- **Де книга? Вона тут.**
- **Де вікно? Воно тут.**

English uses "it" for all three. Ukrainian does not. Let the Ukrainian noun
choose the pronoun.

Now move to a bag:

```text
Оленка: Що у тебе є?
Марія: У мене є книга, телефон і фото.
Оленка: А у мене є ручка і зошит.
```

Support after the dialogue:

| Українська | English support |
| --- | --- |
| **Що у тебе є?** | What do you have? |
| **У мене є книга, телефон і фото.** | I have a book, a phone, and a photo. |
| **А у мене є ручка і зошит.** | And I have a pen and a notebook. |

**Фото** is a useful beginner word. Store it as **воно**: **моє фото**.

<!-- INJECT_ACTIVITY: act-4 -->

### Мій, моя, моє

The possessive word follows the noun.

| Noun | Gender | Say |
| --- | --- | --- |
| **стіл** | masculine | **мій стіл** |
| **телефон** | masculine | **мій телефон** |
| **книга** | feminine | **моя книга** |
| **ручка** | feminine | **моя ручка** |
| **вікно** | neuter | **моє вікно** |
| **ліжко** | neuter | **моє ліжко** |

This is the same habit from family:

- **мій брат**, **мій тато**, **мій стіл**
- **моя сестра**, **моя мама**, **моя книга**
- **моє місто**, **моє прізвище**, **моє вікно**

If you want to say "my room," use **моя кімната**. If you want to say "my
chair," use **мій стілець**. If you want to say "my bed," use **моє ліжко**.

:::tip
The owner does not decide the form. The noun decides it. Learn the phrase as a
pair: **стіл -> мій стіл**, **книга -> моя книга**, **вікно -> моє вікно**.
:::

## Підсумок

For people, choose the form that fits the person.

| Masculine | Feminine |
| --- | --- |
| **студент** | **студентка** |
| **вчитель / учитель** | **вчителька / учителька** |
| **лікар** | **лікарка** |
| **актор** | **акторка** |
| **співак** | **співачка** |

Use the feminine profession as the normal form for a woman:

```text
Вона студентка.
Вона вчителька.
Вона лікарка.
```

| Українська | English support |
| --- | --- |
| **Вона студентка.** | She is a student. |
| **Вона вчителька.** | She is a teacher. |
| **Вона лікарка.** | She is a doctor. |

For a man:

```text
Він студент.
Він вчитель.
Він лікар.
```

| Українська | English support |
| --- | --- |
| **Він студент.** | He is a student. |
| **Він вчитель.** | He is a teacher. |
| **Він лікар.** | He is a doctor. |

Keep the earlier identity rule: **Я студент. Я студентка.** Do not force
**є** into that A1 sentence.

<!-- INJECT_ACTIVITY: act-9 -->

## Імена, пастки й самоперевірка

Some male names end in **-а**, **-я**, or **-о**: **Микола**, **Ілля**,
**Павло**. They are still **він** because they name men. Family words such as
**тато**, **батько**, and **дядько** are also masculine.

### Пильнуй пастки

Most errors come from using English habits too directly or from trusting the
ending when the word is an exception.

| Trap | Say this |
| --- | --- |
| **мій книга** | **моя книга** |
| **мій ручка** | **моя ручка** |
| **Де стіл? Воно там.** | **Де стіл? Він там.** |
| **Це моя тато.** | **Це мій тато.** |
| **Вона Микола.** | **Він Микола.** |
| **Моя собака гарна.** | **Мій собака гарний.** |
| **Я є студент.** | **Я студент.** |
| **Моє ім'я є Джон.** | **Мене звати Джон.** |

For **собака**, just memorize the course phrase **мій собака**. You do not need
a long exception list today.

The gender-flip mini-check uses five words that are not your active vocabulary:
**біль**, **степ**, **розпис**, **літопис**, and **путь**. They are diagnostic
props. The point is simple: trust the Ukrainian gender test, not an instinct
from another language.

### Самоперевірка

Cover the English support and say the Ukrainian aloud:

| Українська | English support |
| --- | --- |
| **Це моя кімната.** | This is my room. |
| **У мене є стіл.** | I have a table. |
| **У мене є книга.** | I have a book. |
| **У мене є вікно.** | I have a window. |
| **мій стіл** | my table |
| **моя ручка** | my pen |
| **моє ліжко** | my bed |
| **Де стіл? Він тут.** | Where is the table? It is here. |
| **Де книга? Вона тут.** | Where is the book? It is here. |
| **Де вікно? Воно тут.** | Where is the window? It is here. |

Then make three tiny room lines. Read the Ukrainian first, then check the
support.

```text
Це моя кімната.
У мене є стіл, книга і вікно.
Мій стіл тут, моя книга тут, моє вікно там.
```

| Українська | English support |
| --- | --- |
| **Це моя кімната.** | This is my room. |
| **У мене є стіл, книга і вікно.** | I have a table, a book, and a window. |
| **Мій стіл тут, моя книга тут, моє вікно там.** | My table is here, my book is here, my window is there. |

Workbook practice will make the pattern automatic: sort nouns by gender, choose
**він / вона / воно**, complete **мій / моя / моє**, use **У мене є...**, and
repair the gender traps.


### activities.yaml

---
inline:
  - id: act-1
    type: quiz
    title: Хто чи що?
    instruction: Choose the question or pronoun that fits the noun.
    items:
      - prompt: тато
        options:
          - text: Хто це?
            correct: true
          - text: Що це?
            correct: false
          - text: Воно?
            correct: false
        explanation: Тато is a person word, so ask Хто це?
      - prompt: стіл
        options:
          - text: Що це?
            correct: true
          - text: Хто це?
            correct: false
          - text: Вона?
            correct: false
        explanation: Стіл is a thing word, so ask Що це?
      - prompt: сестра
        options:
          - text: вона
            correct: true
          - text: він
            correct: false
          - text: воно
            correct: false
        explanation: Сестра is feminine.
      - prompt: брат
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Брат is masculine.
      - prompt: книга
        options:
          - text: вона
            correct: true
          - text: він
            correct: false
          - text: воно
            correct: false
        explanation: Книга is feminine.
      - prompt: вікно
        options:
          - text: воно
            correct: true
          - text: вона
            correct: false
          - text: він
            correct: false
        explanation: Вікно is neuter.
  - id: act-2
    type: group-sort
    title: Сортуй предмети за родом
    instruction: Sort each noun by its safest A1 gender phrase.
    groups:
      - label: він / мій
        items:
          - стіл
          - стілець
          - телефон
          - комп'ютер
      - label: вона / моя
        items:
          - книга
          - кімната
          - лампа
          - ручка
      - label: воно / моє
        items:
          - вікно
          - ліжко
          - крісло
          - дзеркало
  - id: act-3
    type: quiz
    title: Він, вона чи воно?
    instruction: Choose the Ukrainian gender-test word.
    items:
      - prompt: стіл
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Стіл ends in a consonant and is masculine.
      - prompt: книга
        options:
          - text: вона
            correct: true
          - text: він
            correct: false
          - text: воно
            correct: false
        explanation: Книга is feminine.
      - prompt: вікно
        options:
          - text: воно
            correct: true
          - text: він
            correct: false
          - text: вона
            correct: false
        explanation: Вікно is neuter.
      - prompt: телефон
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Телефон is masculine.
      - prompt: лампа
        options:
          - text: вона
            correct: true
          - text: воно
            correct: false
          - text: він
            correct: false
        explanation: Лампа is feminine.
      - prompt: ліжко
        options:
          - text: воно
            correct: true
          - text: вона
            correct: false
          - text: він
            correct: false
        explanation: Ліжко is neuter.
      - prompt: тато
        options:
          - text: він
            correct: true
          - text: воно
            correct: false
          - text: вона
            correct: false
        explanation: Тато is masculine because it names a male person.
      - prompt: Микола
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Микола is a masculine name.
  - id: act-5
    type: quiz
    title: Закінчення підказує рід
    instruction: Choose the usual gender signal from the noun ending.
    items:
      - prompt: стіл закінчується на приголосний.
        options:
          - text: він / мій
            correct: true
          - text: вона / моя
            correct: false
          - text: воно / моє
            correct: false
        explanation: A clear consonant ending is usually masculine.
      - prompt: телефон закінчується на приголосний.
        options:
          - text: він / мій
            correct: true
          - text: вона / моя
            correct: false
          - text: воно / моє
            correct: false
        explanation: Телефон is masculine in this A1 pattern.
      - prompt: книга закінчується на -а.
        options:
          - text: вона / моя
            correct: true
          - text: він / мій
            correct: false
          - text: воно / моє
            correct: false
        explanation: A clear -а ending is usually feminine.
      - prompt: кімната закінчується на -а.
        options:
          - text: вона / моя
            correct: true
          - text: він / мій
            correct: false
          - text: воно / моє
            correct: false
        explanation: Кімната is feminine in this A1 pattern.
      - prompt: вікно закінчується на -о.
        options:
          - text: воно / моє
            correct: true
          - text: він / мій
            correct: false
          - text: вона / моя
            correct: false
        explanation: A clear -о ending is usually neuter.
      - prompt: ліжко закінчується на -о.
        options:
          - text: воно / моє
            correct: true
          - text: вона / моя
            correct: false
          - text: він / мій
            correct: false
        explanation: Ліжко is neuter in this A1 pattern.
  - id: act-4
    type: fill-in
    title: Мій предмет
    instruction: Choose мій, моя, or моє.
    items:
      - sentence: Це ___ стіл.
        answer: мій
        options:
          - мій
          - моя
          - моє
        explanation: Стіл is masculine.
      - sentence: Це ___ книга.
        answer: моя
        options:
          - моя
          - мій
          - моє
        explanation: Книга is feminine.
      - sentence: Це ___ вікно.
        answer: моє
        options:
          - моє
          - мій
          - моя
        explanation: Вікно is neuter.
      - sentence: Це ___ кімната.
        answer: моя
        options:
          - моя
          - мій
          - моє
        explanation: Кімната is feminine.
      - sentence: Це ___ ліжко.
        answer: моє
        options:
          - моє
          - моя
          - мій
        explanation: Ліжко is neuter.
      - sentence: Це ___ телефон.
        answer: мій
        options:
          - мій
          - моя
          - моє
        explanation: Телефон is masculine.
      - sentence: Це ___ ручка.
        answer: моя
        options:
          - моя
          - мій
          - моє
        explanation: Ручка is feminine.
      - sentence: Це ___ фото.
        answer: моє
        options:
          - моє
          - моя
          - мій
        explanation: Фото is neuter in this lesson.
  - id: act-9
    type: quiz
    title: Форми професій
    instruction: Choose the natural profession form.
    items:
      - prompt: She is a teacher.
        options:
          - text: Вона вчителька.
            correct: true
          - text: Вона вчитель.
            correct: false
          - text: Воно вчителька.
            correct: false
        explanation: Use the feminine profession form for a woman.
      - prompt: She is a doctor.
        options:
          - text: Вона лікарка.
            correct: true
          - text: Вона лікар.
            correct: false
          - text: Він лікарка.
            correct: false
        explanation: Лікарка is the feminine form.
      - prompt: He is a student.
        options:
          - text: Він студент.
            correct: true
          - text: Він студентка.
            correct: false
          - text: Вона студент.
            correct: false
        explanation: Студент is the masculine form.
      - prompt: She is an actor.
        options:
          - text: Вона акторка.
            correct: true
          - text: Вона актор.
            correct: false
          - text: Воно акторка.
            correct: false
        explanation: Акторка is the feminine profession form.
workbook:
  - type: group-sort
    title: Сортуй за родом
    instruction: Sort each noun by its A1 gender signal.
    groups:
      - label: він / мій
        items:
          - стіл
          - телефон
          - зошит
          - ключ
          - тато
      - label: вона / моя
        items:
          - книга
          - лампа
          - кімната
          - ручка
          - сестра
      - label: воно / моє
        items:
          - вікно
          - ліжко
          - крісло
          - дзеркало
          - фото
  - type: match-up
    title: Слова для кімнати й сумки
    instruction: Match each Ukrainian noun with its English cue.
    pairs:
      - left: стіл
        right: table
      - left: книга
        right: book
      - left: вікно
        right: window
      - left: кімната
        right: room
      - left: ліжко
        right: bed
      - left: телефон
        right: phone
      - left: ручка
        right: pen
      - left: зошит
        right: notebook
  - type: fill-in
    title: У мене є предмети
    instruction: Complete the object sentence.
    items:
      - sentence: ___ мене є стіл.
        answer: У
        options:
          - У
          - Це
          - Хто
        explanation: У мене є... is the I-have phrase.
      - sentence: У мене ___ книга.
        answer: є
        options:
          - є
          - звати
          - моя
        explanation: У мене є... stays as one phrase.
      - sentence: У ___ є телефон?
        answer: тебе
        options:
          - тебе
          - мене
          - мій
        explanation: У тебе є...? asks one familiar person.
      - sentence: У мене є ___.
        answer: вікно
        options:
          - вікно
          - він
          - моя
        explanation: Вікно is an object noun after У мене є.
      - sentence: Де стіл? ___ тут.
        answer: Він
        options:
          - Він
          - Вона
          - Воно
        explanation: Стіл is masculine, so use він.
      - sentence: Де книга? ___ тут.
        answer: Вона
        options:
          - Вона
          - Він
          - Воно
        explanation: Книга is feminine, so use вона.
      - sentence: Де вікно? ___ там.
        answer: Воно
        options:
          - Воно
          - Вона
          - Він
        explanation: Вікно is neuter, so use воно.
  - type: error-correction
    title: Виправ пастки роду
    instruction: Choose the safer Ukrainian sentence.
    items:
      - sentence: Мій книга, мій ручка (якщо говорить чоловік).
        error: Мій книга, мій ручка (якщо говорить чоловік).
        correction: Моя книга, моя ручка.
        options:
          - Моя книга, моя ручка.
          - Мій книга, мій ручка.
        explanation: The possessive follows the nouns книга and ручка, not the speaker.
      - sentence: Мій книга тут.
        error: Мій книга тут.
        correction: Моя книга тут.
        options:
          - Моя книга тут.
          - Мій книга тут.
        explanation: Книга is feminine, so use моя.
      - sentence: Мій ручка там.
        error: Мій ручка там.
        correction: Моя ручка там.
        options:
          - Моя ручка там.
          - Мій ручка там.
        explanation: Ручка is feminine, so use моя.
      - sentence: Де стіл? — Воно там. (Where is the table? — It is there.)
        error: Де стіл? — Воно там. (Where is the table? — It is there.)
        correction: Де стіл? — Він там.
        options:
          - Де стіл? — Він там.
          - Де стіл? — Воно там.
        explanation: Стіл is masculine, so the pronoun is він.
      - sentence: Це моя тато.
        error: Це моя тато.
        correction: Це мій тато.
        options:
          - Це мій тато.
          - Це моя тато.
        explanation: Тато is masculine.
      - sentence: Вона Микола.
        error: Вона Микола.
        correction: Він Микола.
        options:
          - Він Микола.
          - Вона Микола.
        explanation: Микола is a masculine name.
      - sentence: Моя собака дуже гарна.
        error: Моя собака дуже гарна.
        correction: Мій собака дуже гарний.
        options:
          - Мій собака дуже гарний.
          - Моя собака дуже гарна.
        explanation: Собака is masculine in Ukrainian; memorize мій собака.
      - sentence: Я є студент.
        error: Я є студент.
        correction: Я студент.
        options:
          - Я студент.
          - Я є студент.
        explanation: Present identity normally omits є.
      - sentence: Моє ім'я є Джон.
        error: Моє ім'я є Джон.
        correction: Мене звати Джон.
        options:
          - Мене звати Джон.
          - Моє ім'я є Джон.
        explanation: Мене звати... is the safe name phrase.
  - type: quiz
    title: Перевірка роду
    instruction: Choose the Ukrainian gender-test word. These are diagnostic props, not new active vocabulary.
    items:
      - prompt: Який у мене сильний біль у плечі!
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Біль is masculine in Ukrainian.
      - prompt: Український степ широкий і вітряний.
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Степ is masculine in Ukrainian.
      - prompt: Цей розпис на стіні — робота українського художника.
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Розпис is masculine in Ukrainian.
      - prompt: Давній літопис розповідає про Київську Русь.
        options:
          - text: він
            correct: true
          - text: вона
            correct: false
          - text: воно
            correct: false
        explanation: Літопис is masculine in Ukrainian.
      - prompt: 'Книжне / урочисте: у далеку путь.'
        options:
          - text: вона
            correct: true
          - text: він
            correct: false
          - text: воно
            correct: false
        explanation: Путь is feminine in this diagnostic expression.


### vocabulary.yaml

- lemma: рід
  translation: grammatical gender
  pos: noun
  usage: Українські іменники мають рід.
- lemma: іменник
  translation: noun
  pos: noun
  usage: Стіл — це іменник.
- lemma: хто це?
  translation: who is this?
  pos: phrase
  usage: Хто це? Це тато.
- lemma: що це?
  translation: what is this?
  pos: phrase
  usage: Що це? Це стіл.
- lemma: він
  translation: he / masculine gender-test word
  pos: pronoun
  usage: Стіл — він.
- lemma: вона
  translation: she / feminine gender-test word
  pos: pronoun
  usage: Книга — вона.
- lemma: воно
  translation: it / neuter gender-test word
  pos: pronoun
  usage: Вікно — воно.
- lemma: мій
  translation: my, masculine
  pos: pronoun
  usage: Це мій стіл.
- lemma: моя
  translation: my, feminine
  pos: pronoun
  usage: Це моя книга.
- lemma: моє
  translation: my, neuter
  pos: pronoun
  usage: Це моє вікно.
- lemma: у мене є
  translation: I have
  pos: phrase
  usage: У мене є стіл.
- lemma: у тебе є
  translation: do you have / you have
  pos: phrase
  usage: У тебе є стіл?
- lemma: стіл
  translation: table
  pos: noun
  usage: У мене є стіл.
- lemma: книга
  translation: book
  pos: noun
  usage: Це моя книга.
- lemma: вікно
  translation: window
  pos: noun
  usage: Моє вікно велике.
- lemma: кімната
  translation: room
  pos: noun
  usage: Це моя кімната.
- lemma: ліжко
  translation: bed
  pos: noun
  usage: Це моє ліжко.
- lemma: стілець
  translation: chair
  pos: noun
  usage: Це мій стілець.
- lemma: лампа
  translation: lamp
  pos: noun
  usage: Це моя лампа.
- lemma: телефон
  translation: phone
  pos: noun
  usage: Це мій телефон.
- lemma: комп'ютер
  translation: computer
  pos: noun
  usage: Це мій комп'ютер.
- lemma: зошит
  translation: notebook
  pos: noun
  usage: Це мій зошит.
- lemma: ручка
  translation: pen
  pos: noun
  usage: Це моя ручка.
- lemma: сумка
  translation: bag
  pos: noun
  usage: Це моя сумка.
- lemma: крісло
  translation: armchair
  pos: noun
  usage: Це моє крісло.
- lemma: дзеркало
  translation: mirror
  pos: noun
  usage: Це моє дзеркало.
- lemma: ключ
  translation: key
  pos: noun
  usage: Це мій ключ.
- lemma: фото
  translation: photo
  pos: noun
  usage: Це моє фото.
- lemma: стіна
  translation: wall
  pos: noun
  usage: Це моя стіна.
- lemma: місто
  translation: city
  pos: noun
  usage: Моє місто велике.
- lemma: тато
  translation: dad
  pos: noun
  usage: Це мій тато.
- lemma: батько
  translation: father
  pos: noun
  usage: Це мій батько.
- lemma: дядько
  translation: uncle
  pos: noun
  usage: Це мій дядько.
- lemma: собака
  translation: dog
  pos: noun
  usage: Це мій собака.
- lemma: студент
  translation: male student
  pos: noun
  usage: Він студент.
- lemma: студентка
  translation: female student
  pos: noun
  usage: Вона студентка.
- lemma: вчитель
  translation: male teacher
  pos: noun
  usage: Він вчитель.
- lemma: вчителька
  translation: female teacher
  pos: noun
  usage: Вона вчителька.
- lemma: учителька
  translation: female teacher
  pos: noun
  usage: Вона учителька.
- lemma: лікар
  translation: male doctor
  pos: noun
  usage: Він лікар.
- lemma: лікарка
  translation: female doctor
  pos: noun
  usage: Вона лікарка.
- lemma: актор
  translation: male actor
  pos: noun
  usage: Він актор.
- lemma: акторка
  translation: female actor
  pos: noun
  usage: Вона акторка.
- lemma: співак
  translation: male singer
  pos: noun
  usage: Він співак.
- lemma: співачка
  translation: female singer
  pos: noun
  usage: Вона співачка.
- lemma: Микола
  translation: Mykola
  pos: proper noun
  usage: Він Микола.
- lemma: Ілля
  translation: Illia
  pos: proper noun
  usage: Він Ілля.
- lemma: Павло
  translation: Pavlo
  pos: proper noun
  usage: Він Павло.


### resources.yaml

- title: ULP Season 1, Episode 6 — Gender naturally through family
  role: podcast
  source_ref: ULP Season 1, Episode 6 — Gender naturally through family
  url: https://www.ukrainianlessons.com/episode6/
  notes: "Plan reference: gender appears through family and simple possessive phrases."
- title: Noun Genders in Ukrainian
  role: article
  source_ref: Noun Genders in Ukrainian
  url: https://www.ukrainianlessons.com/noun-genders-in-ukrainian/
  notes: "External resource: infographic with noun-gender rules and examples."
- title: How to know noun gender in Ukrainian language? Рід іменника
  role: video
  source_ref: "How to know noun gender in Ukrainian language? Рід іменника [Ukrainian Grammar Guide]"
  url: https://www.ukrainianlessons.com/video-noun-gender/
  notes: "External resource: Anna Ohoiko grammar guide video page."
- title: Gender of Ukrainian Nouns
  role: youtube
  source_ref: Gender of Ukrainian Nouns
  url: https://www.youtube.com/watch?v=Vl5MAW3AYoU
  notes: "External resource: additional noun-gender overview video."
- title: "Dobra Forma: Gender of Nouns"
  role: article
  source_ref: "Dobra Forma: Gender of Nouns"
  url: https://opentext.ku.edu/dobraforma/chapter/1-1/
  notes: "Plan/wiki source: gender of nouns reference."
- title: "Dobra Forma: Gender of Nouns (Masculine and Feminine)"
  role: article
  source_ref: "Dobra Forma: Gender of Nouns (Masculine and Feminine)"
  url: https://opentext.ku.edu/dobraforma/chapter/1-2/
  notes: "External resource: masculine and feminine noun forms."


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
