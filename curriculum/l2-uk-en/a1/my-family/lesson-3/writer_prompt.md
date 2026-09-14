# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: a1. Module: my-family.
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
Previously introduced in this module: ["сім'я", "родина", "мама", "мати", "тато", "батько", "брат", "сестра", "син", "дочка", "донька", "бабуся", "дідусь", "батьки", "у мене є", "у тебе є", "у вас є", "один", "одна", "два", "дві", "тільки", "мій", "моя", "моє", "мої", "твій"]

## Deterministic lessons.yaml (read-only)

lessons:
- n: 1
  title: Сім'я
  sections:
  - Діалоги
  - Сім'я
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
  title: Мій / моя
  sections:
  - У мене є
  - Мій / моя
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
  title: Слухай, фото, зошит
  sections:
  - Слухай, фото, зошит
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
- id: act-w4
  reason: 4-item original activity preserved from baseline
- id: act-w5
  reason: 5-item original activity preserved from baseline
- id: act-w6
  reason: 5-item original activity preserved from baseline
proper_names: []


## Original plan (read-only)

module: a1-006
level: A1
sequence: 6
slug: my-family
version: 1.4.0
lifecycle: locked
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-scale-my-family
review_notes: 'Review-and-lock pass for A1 ship-readiness (overnight scale batch 1,
  per docs/best-practices/wiki-plan-review-and-lock.md). Pragmatic / Russianism /
  calque / contradiction / references checks all clean — no findings in plan prose
  (homoglyph scan NONE; no "приймати X" / "Давайте + 1pl" / "на винос" patterns).
  The plan was brought into alignment with the locked wiki: Крок 6 patronymic recognition
  hook added to "Сім''я" section (fenced as recognition-only, NOT an added `dialogue_situation`
  — both dialogues remain peer/photo-sharing); `ім''я`, `прізвище`, `по батькові`,
  `родичі` added to recommended vocab; family-Surzhyk fill-in activity added (7 pairs:
  жена/дружина, муж/чоловік, бабушка/бабуся, родственники/родичі, ребьонок/дитина,
  младший/молодший, женатий/одружений — NO папа/тато pair because VESUM lists `папа`
  without restrictive tags); wiki back-reference added to references. Cross-agent
  adversarial review (Codex) caught `папа` overreach in first draft; fixed before
  lock. See PR body for full audit and wiki/.reviews/pedagogy/a1/my-family-review-LOCKED.md.'
title: Моя сім'я
subtitle: У мене є брат — показуємо фотографії
focus: vocabulary
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
word_target: 1200
objectives:
- Вміти називати близьких членів родини українською мовою
- Навчитися використовувати конструкцію «У мене є» для вираження власності (як сталий
  вираз)
- Вміти вживати присвійні займенники мій/моя/моє лише в називному відмінку
- Навчитися представляти членів родини, використовуючи конструкцію «Це» + присвійні
  займенники
dialogue_situations:
- setting: 'Відеодзвінок: показуємо фотографії на телефоні новому другу'
  speakers:
  - Оля
  - Марк
  motivation: У мене є + члени родини, присвійні займенники мій/моя з фотографіями
- setting: Показуємо сімейні фото новому українському другу в школі — розповідаємо,
    хто є хто, розпитуємо про сім'ї одне одного
  speakers:
  - Даша
  - Андрій
  motivation: Лексика про сім'ю, запитання «У тебе є брати? Це мій/моя...» у природному
    підлітковому контексті
content_outline:
- section: Діалоги
  words: 400
  points:
  - 'Діалог 1 — Показуємо фото з телефону (Anna Епізод 6-7): — У тебе є брати чи сестри?
    — Так, у мене є два брати і одна сестра. — Ого! У мене тільки один брат. Як його
    звати? — Коля.'
  - 'Діалог 2 — Сім''я на фотографії (Anna Епізод 7): — Це моя сім''я на фотографії.
    — Класно! Хто це? — Це моя мама Марина. Це мій тато Євген. Це моя сестра Катя
    і мої брати — Іван і Денис. — А це твоя бабуся? — Так, її звати Тетяна.'
  - 'Діалог 3 — Зв''язне мовлення (Anna Епізод 10, повторення шаблону): Привіт! Мене
    звати... Моя мама — вчителька. Мій тато — інженер. У мене є один брат. Поєднання
    всіх навичок з A1.1.'
- section: Сім'я
  words: 200
  points:
  - 'Anna Епізод 6: Два слова для позначення сім''ї: «сім''я» та «родина» (обидва
    вживаються). Основні: мама/мати, тато/батько, брат, сестра, син, дочка/донька.
    Додаткові: бабуся/баба, дідусь/дід, тітка, дядько. Зверніть увагу: в українській
    немає одного слова для «grandparents» — завжди кажемо «бабуся і дідусь».'
  - 'Ім''я + по батькові — ТІЛЬКИ для впізнавання (не для продукції на А1, не окреме
    `dialogue_situation`): українська модель повного імені — `ім''я + по батькові
    + прізвище` (наприклад, `Марія Василівна Коваленко`). Суфікси: чоловічі `-ович`/`-йович`
    (`Іван → Іванович`), жіночі `-івна`/`-ївна` (`Петро → Петрівна`). УВАГА до автора:
    українська жіноча форма — `-івна`/`-ївна`, НЕ російська `-овна`. Подати ОДИН короткий
    ілюстративний приклад у секції (напр. у самому тексті «Сім''я» або «Підсумок»):
    `— Добрий день, Маріє Василівно!` з позначкою «recognition-only; формальний регістр».
    Дві головні `dialogue_situations[]` залишаються peer/photo-sharing з `ти` — формальний
    регістр з `по батькові` не вводиться як окремий діалог і не тренується продуктивно.
    Продукція власних форм по батькові відкладається на А2; А1 = впізнавання + розуміння,
    що це сигнал формальності.'
- section: У мене є
  words: 250
  points:
  - 'Шаблон з Anna Епізод 6: В українській мові не кажуть "I have" за допомогою дієслова
    мати. Натомість використовують конструкцію: У мене є брат. Для рівня А1 вивчаємо
    лише: у мене є, у тебе є, у вас є (ввічлива форма). Інші форми (у нього, у неї,
    у нас, у них) вимагають використання займенників у родовому відмінку, що є граматикою
    рівня А2 — вводимо їх поступово через діалоги як сталі фрази, а не як парадигму.'
  - 'Запитання з висхідною інтонацією: У тебе є сестра? ↗ Заперечення: Відкладаємо
    вивчення "У мене немає" до рівня А2 (коли вивчатимемо родовий відмінок). На рівні
    А1 учні відповідають: Ні. / Ні, у мене тільки один брат. Це дозволяє уникнути
    педагогічної пастки використання "немає" + називний відмінок (*немає брат).'
  - 'Ознайомлення з числівниками (Anna Епізод 6): один/одна змінюється за родами:
    один брат, одна сестра. два/дві: два брати, дві сестри.'
- section: Мій, моя, моє
  words: 200
  points:
  - 'Anna Епізод 7: Присвійні займенники узгоджуються в роді з іменником, якого стосуються.
    мій брат (m), моя сестра (f), моє місто (n), мої батьки (pl). твій/твоя/твоє/твої
    (your, informal). його (не змінюється), її (не змінюється). Зауваження згідно
    з Державним стандартом: повна парадигма (наш, ваш, їхній) — це рівень А2. На рівні
    А1 вивчаємо мій/твій/його/її лише в називному відмінку.'
- section: Підсумок
  words: 150
  points:
  - 'Самоперевірка: Назвіть 5 членів родини. Скажіть "У мене є сестра". Яка різниця
    між «мій» та «моя»? Розкажіть про свою сім''ю у 4-5 реченнях.'
vocabulary_hints:
  required:
  - сім'я (family) — apostrophe word
  - мама (mother)
  - тато (father)
  - брат (brother)
  - сестра (sister)
  - бабуся (grandmother)
  - дідусь (grandfather)
  - мій, моя, моє, мої (my — m/f/n/pl)
  - твій, твоя, твоє (your — m/f/n, informal)
  - у мене є (I have)
  - у тебе є (you have, informal)
  recommended:
  - батьки (parents)
  - дядько (uncle)
  - тітка (aunt)
  - дочка (daughter)
  - син (son)
  - дружина (wife)
  - чоловік (man / husband)
  - родичі (relatives, kin — countable plural)
  - його (his — doesn't change)
  - її (her — doesn't change)
  - один, одна (one — m/f)
  - два, дві (two — m/f)
  - чи (or — in questions)
  - тільки (only)
  - ім'я (given name — recognition only at A1, `Мене звати + ім'я`)
  - прізвище (surname — recognition only)
  - по батькові (patronymic — recognition only, paired with formal `Ви`)
activity_hints:
- type: quiz
  focus: '«У тебе є...?» — дайте відповідь Так/Ні. Використовуйте ЛИШЕ сталий вираз
    «у тебе є». Приклади питань: "У тебе є брат?", "У тебе є сестра?", "У тебе є бабуся?".
    Варіанти відповідей: "Так, у мене є брат." / "Ні." / "Так, у мене є два брати."
    НЕ використовуйте імена в родовому відмінку (ніякого "У Оксани є").'
  items: 6
- type: fill-in
  focus: 'Оберіть правильний присвійний займенник. ТОЧНИЙ шаблон: "Це {___} мама."
    → моя | "Де {___} тато?" → твій | "Ось {___} батьки." → мої. Усе в називному відмінку.
    Варіанти: мій/моя/моє/мої або твій/твоя/твоє/твої.'
  items: 8
- type: match-up
  focus: 'З''єднайте англійські слова про сім''ю з українськими відповідниками. Пари:
    parents↔батьки, uncle↔дядько, aunt↔тітка, grandfather↔дідусь, grandmother↔бабуся,
    brother↔брат, sister↔сестра, mother and father↔мама і тато.'
  items: 8
- type: fill-in
  focus: 'Заповніть пропуски в діалозі про знайомство з сім''єю. Шаблон: "— Привіт!
    Це {твій} брат?" / "— Так, це мій брат. Ось мій {тато}." Варіанти для пропусків:
    члени родини або присвійні займенники. ЖОДНИХ форм родового відмінка.'
  items: 4
- type: fill-in
  focus: 'Типові родинні суржикові пари — оберіть нормативну форму (див. wiki "Типові
    помилки L2"). Мета: нейтралізувати поширені запозичення з рос. (`жена`, `муж`,
    `бабушка`, `родственники`, `ребьонок`, `младший`, `женатий`) перед тим, як вони
    закріпляться як «норма». УВАГА: пара `папа/тато` свідомо відсутня — `папа` зафіксоване
    у VESUM без обмежень і є регістрово-стильовою преференцією, а не словниковою помилкою
    (автор модулює `тато`, але не маркує `папа` як «неправильно»).'
  items:
  - Моя {дружина|жена} — вчителька.
  - Мій {чоловік|муж} працює в лікарні.
  - Це моя {бабуся|бабушка}. Їй сімдесят років.
  - У нас велика родина — близько десяти {родичів|родственників}.
  - Моя племінниця ще маленька {дитина|ребьонок}.
  - Мій {молодший|младший} брат навчається в школі.
  - Мій старший брат уже {одружений|женатий}. У нього двоє дітей.
connects_to:
- a1-007 (Рубіжний контроль — Перший контакт)
prerequisites:
- a1-005 (Хто я?)
grammar:
- У мене є / у тебе є / у вас є (завчені фрази для вираження власності)
- Присвійні займенники мій/моя/моє/мої, твій/твоя/твоє — фокус на називному відмінку
- 'Форми родового відмінка з''являються ЛИШЕ як завчені сталі вирази: у мене, у тебе,
  у вас. Форми у нього, у неї можуть траплятися в діалогах для ознайомлення, але НЕ
  відпрацьовуються — повна парадигма родового відмінка вивчається на рівні А2.'
- 'Узгодження в роді (присвійний займенник + іменник): мій брат, моя сестра'
- Числівники один/одна, два/дві з членами родини
- 'Опис родинних зв''язків: використовуйте конструкцію Це + називний відмінок (Це
  мій брат), а НЕ конструкції з родовим відмінком (уникайте: мама мого тата). Описуйте
  стосунки через прості речення: Мій тато. Його мама — моя бабуся.'
- 'Заперечення: Ні + проста відповідь (У мене немає — перенесено на рівень А2)'
register: розмовний
references:
- title: ULP Season 1, Episode 6 — Family + I Have
  url: https://www.ukrainianlessons.com/episode6/
  notes: Конструкція «у мене є» з лексикою про сім'ю. Рід числівників один/одна.
- title: ULP Season 1, Episode 7 — Possessive Pronouns
  url: https://www.ukrainianlessons.com/episode7/
  notes: Парадигма мій/моя/моє. Конструкція «Це моя мама».
- title: ULP Season 1, Episode 10 — Review
  url: https://www.ukrainianlessons.com/episode10/
  notes: 'Зв''язна розповідь про себе: Я і моя сім''я.'
- title: 'Wiki: pedagogy/a1/my-family (LOCKED 2026-04-23)'
  notes: 'Authoritative pedagogical brief — see Крок 6 (patronymic recognition + `-івна/-ївна`
    vs `-овна`) and "Типові помилки L2" (family-specific Surzhyk table: 8 pairs).'
changelog:
- version: 1.4.0
  date: '2026-04-23'
  changes:
  - Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md (scale
    batch 1, alongside food-and-drink / colors / sounds-letters-and-hello). Added
    lifecycle markers (lifecycle/reviewed_at/reviewed_by/review_notes).
  - Added patronymic recognition hook in "Сім'я" section (ім'я + по батькові + Ви
    as formal-register signal; `-івна`/`-ївна` explicitly flagged as distinct from
    Russian `-овна`) to align with locked wiki Крок 6.
  - Added ім'я / прізвище / по батькові / родичі to recommended vocabulary (recognition-only
    at A1).
  - 'Added family-Surzhyk fill-in activity mirroring the wiki "Типові помилки L2"
    table (7 pairs: жена/дружина, муж/чоловік, бабушка/бабуся, родственники/родичі,
    ребьонок/дитина, младший/молодший, женатий/одружений). NOTE: папа/тато pair dropped
    after AC-3 cross-agent adversarial review — VESUM lists `папа` without restrictive
    tags, so framing it as a dictionary-backed error would be overreach.'
  - 'Added wiki back-reference to references: section.'


## Existing module artifacts (read-only)

### module.md

# Моя сім'я

**Це моя́ сім'я́. У ме́не є брат.** — This is my family. I have a brother.

Family is the first topic where you introduce other people, not only yourself.
Keep the Ukrainian small and photo-based. Point to a person, say who it is,
and add one simple line with **У ме́не є...** or **Це мій / моя́...**.

By the end, you can:

- name close family members: **мама**, **тато**, **брат**, **сестра**,
  **бабуся**, **дідусь**;
- ask **У тебе є брат?** and answer with **Так, у мене є...** or **Ні.**;
- use **один брат**, **одна сестра**, **два брати**, and **дві сестри**;
- choose **мій**, **моя**, **моє**, or **мої** by the family word, not by
  the owner;
- recognize **його** and **її** in lines such as **Його звати...** and
  **Її звати...**;
- say **сім'я** for your close family and recognize **родина** as the wider
  family or kin circle;
- recognize a formal patronymic greeting without producing patronymics yet.

## Діало́ги

Read the Ukrainian first as a photo exchange. You do not need the whole grammar
of possession. Treat **У ме́не є** and **У те́бе є** as whole phrases.

```text
О́ля: Приві́т, Ма́рку! Це фо́то моє́ї сім'ї́.
Марк: Кла́сно! У те́бе є брати́ чи се́стри?
О́ля: Так, у ме́не є два брати́ і одна́ сестра́.
Марк: Ого́! У ме́не ті́льки оди́н брат.
О́ля: Як його́ зва́ти?
Марк: Його́ зва́ти Ко́ля.
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це фо́то моє́ї сім'ї́.** | This is a photo of my family. |
| **У те́бе є брати́ чи се́стри?** | Do you have brothers or sisters? |
| **У ме́не є два брати́ і одна́ сестра́.** | I have two brothers and one sister. |
| **Як його́ зва́ти?** | What is his name? |

Now use **це** to identify people in a family photo.

```text
Да́ша: Це моя́ сім'я́ на фотогра́фії.
Андрі́й: Хто це?
Да́ша: Це моя́ ма́ма Мари́на. Це мій та́то Євге́н.
Андрі́й: А це твоя́ сестра́?
Да́ша: Так. Це моя́ сестра́ Ка́тя і мої́ брати́, Іва́н і Дени́с.
Андрі́й: А це твоя́ бабу́ся?
Да́ша: Так, її́ зва́ти Тетя́на.
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це моя́ сім'я́.** | This is my family. |
| **Хто це?** | Who is this? |
| **Це моя́ ма́ма.** | This is my mom. |
| **Це мій та́то.** | This is my dad. |
| **її́ зва́ти Тетя́на.** | Her name is Tetiana. |

A short connected answer can reuse M5 and add family:

```text
Приві́т! Мене́ зва́ти Софі́я.
Моя́ ма́ма — вчи́телька.
Мій та́то — інжене́р.
У ме́не є оди́н брат.
```

Notice the question word from earlier modules: **хто?** asks about a person.
For this lesson, use it in **Хто це?** and keep the answers short.

The old name phrase still works inside family talk: **Мене звати [ім'я]**. Use
it as one memorized block before you add family information.

<!-- INJECT_ACTIVITY: act-1 -->

## Сім'я́

Use family words with a photo or a simple drawing. The first task is not a
family tree; it is recognizing and saying the common people words.

| Ukrainian | English |
| --- | --- |
| **сім'я** | family, usually the close household |
| **родина** | family or kin, often wider than the household |
| **мама / мати** | mom / mother |
| **тато / батько** | dad / father |
| **брат** | brother |
| **сестра** | sister |
| **син** | son |
| **дочка / донька** | daughter |
| **бабуся** | grandmother |
| **дідусь** | grandfather |
| **батьки** | parents |
| **родичі** | relatives |

Ukrainian does not use one normal beginner word for "grandparents." Say
**бабуся і дідусь**.

The gender habit starts here. Say **він / мій** with masculine family words:
**тато**, **брат**, **син**, **дідусь**. Say **вона / моя** with feminine
family words: **мама**, **мати**, **сестра**, **дочка**, **донька**,
**бабуся**.

| Pointing line | English |
| --- | --- |
| **Це мій брат. Він студент.** | This is my brother. He is a student. |
| **Це моя сестра. Вона студентка.** | This is my sister. She is a student. |
| **Це мій син.** | This is my son. |
| **Це моя дочка.** | This is my daughter. |

Ukrainian also has a formal full-name pattern: given name, patronymic, and
surname: **Марія Василівна Коваленко**. At A1, only recognize the signal.
You might hear **Добрий день, Маріє Василівно!** in a formal setting. This is
recognition-only; do not try to build your own patronymic forms yet.

Use **ім'я** for given name, **прізвище** for surname, and **по батькові** for
patronymic. Patronymics are a Ukrainian naming tradition and not something to
erase or treat as outside Ukrainian culture. Production waits until a later
level.

<!-- INJECT_ACTIVITY: act-2 -->

## У ме́не є

English says "I have a brother." Ukrainian normally uses a different shape:
**У ме́не є брат.** Learn it as one piece.

| Ukrainian phrase | English use |
| --- | --- |
| **У мене є брат.** | I have a brother. |
| **У мене є сестра.** | I have a sister. |
| **У тебе є брат?** | Do you have a brother? informal |
| **У тебе є сестра?** | Do you have a sister? informal |
| **У вас є діти?** | Do you have children? formal or plural |
| **Так, у мене є брат.** | Yes, I have a brother. |
| **Ні.** | No. |
| **Ні, у мене тільки один брат.** | No, I only have one brother. |

Do not build the English sentence word by word with a verb for "have." Your
safe phrase is **У мене є...**. The other forms, such as "he has" and
"she has," need more grammar, so they stay as recognition only inside
dialogues.

Use the easy number agreement phrases:

| Masculine | Feminine |
| --- | --- |
| **один брат** | **одна сестра** |
| **два брати** | **дві сестри** |
| **один син** | **одна дочка** |

For a negative answer, keep it simple: **Ні.** or **Ні, у мене тільки один
брат.** The full "I do not have..." pattern waits until later because it
requires more case grammar.

<!-- INJECT_ACTIVITY: act-3 -->

## Мій / моя́

The Ukrainian possessive pronoun for "my" changes to match the person or thing
you own. It does not match the gender of the owner.

| Owned word | My | Your, informal |
| --- | --- | --- |
| **брат** | **мій брат** | **твій брат** |
| **мама** | **моя мама** | **твоя мама** |
| **місто** | **моє місто** | **твоє місто** |
| **батьки** | **мої батьки** | **твої батьки** |

The key contrast is **Це мій брат** but **Це моя сестра**. The owner can be a
man or a woman; the form still follows **брат** or **сестра**.

:::tip
When you hesitate, point to the owned word. **Брат** asks for **мій**.
**Мама** asks for **моя**. The speaker's gender does not decide the form.
:::

**Його** and **її** are easier. They do not change here:

| Ukrainian | English |
| --- | --- |
| **Це мій брат. Його звати Коля.** | This is my brother. His name is Kolia. |
| **Це моя сестра. Її звати Катя.** | This is my sister. Her name is Katia. |
| **Це її мама.** | This is her mom. |
| **Це його тато.** | This is his dad. |

You may also hear the older classroom-style verb form **Це мій брат. Його
звуть...**. Treat **Його звуть...** and **Його звати...** as recognition
patterns for "his name is..." while you keep your own production simple.

Leave the other possessive forms for later. This module's photo tool is the
small set you can already use: **мій**, **моя**, **моє**, **мої**, **твій**,
**твоя**, **твоє**, **твої**.

Use **чи** for a choice or a yes/no photo question:

| Українська | English support |
| --- | --- |
| **У тебе є брати чи сестри?** | Do you have brothers or sisters? |
| **Чи це твоя бабуся?** | Is this your grandmother? |

<!-- INJECT_ACTIVITY: act-4 -->

## Слу́хай, фо́то, зошит

The Resources tab has optional Ukrainian Lessons Podcast pages for this topic:
Episode 6 for **сім'я́ / У ме́не є...**, Episode 7 for **мій / моя́**, and
Episode 10 for connected review speech. Choose one short phrase, listen once,
repeat once, and come back to the page.

For handwriting recognition, ask a teacher, tutor, or classmate to write these
original labels beside a simple family sketch: **ма́ма**, **та́то**,
**брат**, **сестра́**, **сім'я́**, **бабу́ся**. First compare the notebook
label with the printed word; then write your own line.

## Самопереві́рка

Cover the English support and read the Ukrainian aloud:

| Українська | English support |
| --- | --- |
| **Це моя́ сім'я́.** | This is my family. |
| **Це моя́ ма́ма.** | This is my mom. |
| **Це мій та́то.** | This is my dad. |
| **У те́бе є брат?** | Do you have a brother? |
| **Так, у ме́не є оди́н брат.** | Yes, I have one brother. |
| **Ні.** | No. |
| **У ме́не є дві сестри́.** | I have two sisters. |
| **Це мій брат. Його́ зва́ти Ко́ля.** | This is my brother. His name is Kolia. |
| **Це моя́ сестра́. Її́ зва́ти Ка́тя.** | This is my sister. Her name is Katia. |
| **Чи це твоя́ бабу́ся?** | Is this your grandmother? |

You can now make a four-sentence family introduction:

```text
Мене́ зва́ти Марко́.
Це моя́ сім'я́.
Моя́ ма́ма — вчи́телька.
У ме́не є одна́ сестра́.
```

Use native Ukrainian family words in the workbook: **дружи́на** for wife,
**чолові́к** for husband or man by context, **бабу́ся** for grandmother,
**ро́дичі** for relatives, **дити́на** for child, **моло́дший** for younger,
and **одру́жений** for married. Register note: for everyday family talk, choose
**чолові́к**. **Муж** is an older or elevated Ukrainian word in some contexts,
not the first photo-sharing word for "husband."

In the workbook, build a small family-photo script step by step: choose safe
sentences, pick the everyday Ukrainian family word, sort one/two phrases, notice
the formal name signal, and then complete a short photo dialogue.


### activities.yaml

inline:
  - id: act-1
    type: quiz
    title: Питання до фото
    instruction: Обери український рядок для фото-розмови.
    items:
      - prompt: Ти питаєш одного ровесника про брата.
        options:
          - text: У тебе є брат?
            correct: true
          - text: У мене є брат?
            correct: false
          - text: Це брат?
            correct: false
        explanation: У тебе є...? питає одну знайому людину.
      - prompt: Ти відповідаєш так і кажеш, що маєш одну сестру.
        options:
          - text: Так, у мене є одна сестра.
            correct: true
          - text: Так, у тебе є одна сестра.
            correct: false
          - text: Так, це одна сестра.
            correct: false
        explanation: У мене є... відповідає за себе.
      - prompt: Ти відповідаєш ні короткою A1-фразою.
        options:
          - text: Ні.
            correct: true
          - text: У мене немає брат.
            correct: false
          - text: Ні є брат.
            correct: false
        explanation: На A1 тримай заперечну відповідь простою.
      - prompt: Ти питаєш, як його звати.
        options:
          - text: Як його звати?
            correct: true
          - text: Як її звати?
            correct: false
          - text: Що його звати?
            correct: false
        explanation: Його підходить до брата, тата, сина або дідуся.
      - prompt: Ти показуєш маму на фото.
        options:
          - text: Це моя мама.
            correct: true
          - text: Це мій мама.
            correct: false
          - text: Це моє мама.
            correct: false
        explanation: Мама — жіночого роду, тому моя.
      - prompt: Ти показуєш батьків.
        options:
          - text: Це мої батьки.
            correct: true
          - text: Це мій батьки.
            correct: false
          - text: Це моя батьки.
            correct: false
        explanation: Батьки — множина, тому мої.
  - id: act-2
    type: match-up
    title: Слова родини
    instruction: З'єднай українське слово з українською підказкою.
    pairs:
      - left: мама
        right: мати
      - left: тато
        right: батько
      - left: брат
        right: син для моїх батьків
      - left: сестра
        right: дочка для моїх батьків
      - left: бабуся
        right: мама мами або тата
      - left: дідусь
        right: тато мами або тата
      - left: батьки
        right: мама і тато
      - left: родичі
        right: люди з родини
  - id: act-3
    type: fill-in
    title: Склади У мене є
    instruction: Обери слово або фразу для родинного речення.
    items:
      - sentence: ___ мене є брат.
        answer: У
        options:
          - У
          - Це
          - Хто
        explanation: У мене є... — цілий блок, щоб сказати, що хтось або щось є в мене.
      - sentence: У ___ є сестра.
        answer: мене
        options:
          - мене
          - мій
          - це
        explanation: У мене є... відповідає за себе.
      - sentence: У ___ є брат?
        answer: тебе
        options:
          - тебе
          - мене
          - він
        explanation: У тебе є...? питає одну знайому людину.
      - sentence: У ___ є діти?
        answer: вас
        options:
          - вас
          - твій
          - вона
        explanation: У вас є...? — формально або множина.
      - sentence: У мене є ___ брат.
        answer: один
        options:
          - один
          - одна
          - дві
        explanation: Брат — чоловічого роду, тому один.
      - sentence: У мене є ___ сестра.
        answer: одна
        options:
          - одна
          - один
          - два
        explanation: Сестра — жіночого роду, тому одна.
      - sentence: У мене є ___ брати.
        answer: два
        options:
          - два
          - дві
          - одна
        explanation: Брати вживаємо з два.
      - sentence: У мене є ___ сестри.
        answer: дві
        options:
          - дві
          - два
          - один
        explanation: Зі словом сестри тут уживаємо дві.
  - id: act-4
    type: fill-in
    title: Мій чи моя?
    instruction: Обери присвійний займенник до родинного слова.
    items:
      - sentence: Це ___ брат.
        answer: мій
        options:
          - мій
          - моя
          - моє
          - мої
        explanation: Брат — чоловічого роду.
      - sentence: Це ___ мама.
        answer: моя
        options:
          - моя
          - мій
          - моє
          - мої
        explanation: Мама — жіночого роду.
      - sentence: Це ___ місто.
        answer: моє
        options:
          - моє
          - мій
          - моя
          - мої
        explanation: Місто — середнього роду.
      - sentence: Це ___ батьки.
        answer: мої
        options:
          - мої
          - мій
          - моя
          - моє
        explanation: Батьки — множина.
      - sentence: Це ___ тато?
        answer: твій
        options:
          - твій
          - твоя
          - твоє
          - твої
        explanation: Тато — чоловічого роду, хоча слово закінчується на -о.
      - sentence: Це ___ сестра?
        answer: твоя
        options:
          - твоя
          - твій
          - твоє
          - твої
        explanation: Сестра — жіночого роду.
      - sentence: Це ___ прізвище?
        answer: твоє
        options:
          - твоє
          - твій
          - твоя
          - твої
        explanation: Прізвище — середнього роду.
      - sentence: Це ___ родичі?
        answer: твої
        options:
          - твої
          - твій
          - твоя
          - твоє
        explanation: Родичі — множина.
workbook:
  - type: error-correction
    title: Обери українське родинне речення
    instruction: Обери безпечніший український рядок.
    items:
      - sentence: Моє ім'я є Джон.
        error: Моє ім'я є Джон.
        correction: Мене звати Джон.
        options:
          - Мене звати Джон.
          - Моє ім'я є Джон.
        explanation: Мене звати... — природна модель першого представлення.
      - sentence: Я маю брата.
        error: Я маю брата.
        correction: У мене є брат.
        options:
          - У мене є брат.
          - Я маю брата.
        explanation: Для родини на A1 вживай безпечний блок У мене є...
      - sentence: Це мій мама.
        error: Це мій мама.
        correction: Це моя мама.
        options:
          - Це моя мама.
          - Це мій мама.
        explanation: Мама — жіночого роду, тому вживай моя.
      - sentence: Це є мій брат.
        error: Це є мій брат.
        correction: Це мій брат.
        options:
          - Це мій брат.
          - Це є мій брат.
        explanation: У простому фото-реченні є не потрібне.
      - sentence: Батьки (у значенні батька)
        error: Батьки (у значенні батька)
        correction: Тато / батько
        options:
          - Тато / батько
          - Батьки
        explanation: Батьки означає маму й тата або кількох батьків, а не одного тата.
      - sentence: У мене немає брат.
        error: У мене немає брат.
        correction: Ні.
        options:
          - Ні.
          - У мене немає брат.
        explanation: На A1 відповідай коротко; повний блок із немає буде пізніше.
  - type: fill-in
    title: Обери українську родинну норму
    instruction: Обери українське слово для звичайної родинної розмови.
    items:
      - sentence: Моя ___ — вчителька.
        answer: дружина
        options:
          - дружина
          - жена
        explanation: Для wife вживай дружина; жена — російська форма.
      - sentence: Мій ___ працює в лікарні.
        answer: чоловік
        options:
          - чоловік
          - муж
        explanation: У звичайній родинній розмові вживай чоловік; муж — старше або піднесене слово.
      - sentence: Це моя ___ Тетяна.
        answer: бабуся
        options:
          - бабуся
          - бабушка
        explanation: Бабуся — українське слово для grandmother.
      - sentence: У нас велика родина — близько десяти ___.
        answer: родичів
        options:
          - родичів
          - родственників
        explanation: Родичі — українське слово для relatives; у цьому реченні форма родичів уже дана як готовий блок.
      - sentence: Це ще маленька ___.
        answer: дитина
        options:
          - дитина
          - ребьонок
        explanation: Дитина — українське слово для child.
      - sentence: Це мій ___ брат.
        answer: молодший
        options:
          - молодший
          - младший
        explanation: Молодший означає менший за віком.
      - sentence: Мій старший брат уже ___.
        answer: одружений
        options:
          - одружений
          - женатий
        explanation: Для married у цьому родинному реченні вживай одружений.
  - type: group-sort
    title: Один / одна / два / дві
    instruction: Розподіли родинні фрази за числівником.
    groups:
      - label: один
        items:
          - один брат
          - один син
          - один дідусь
      - label: одна
        items:
          - одна сестра
          - одна дочка
          - одна бабуся
      - label: два
        items:
          - два брати
          - два сини
      - label: дві
        items:
          - дві сестри
          - дві дочки
  - type: match-up
    title: Повне ім'я як сигнал
    instruction: З'єднай частину формального імені з підказкою. Це тільки впізнавання.
    pairs:
      - left: ім'я
        right: Марія
      - left: прізвище
        right: Коваленко
      - left: по батькові
        right: Василівна
      - left: Добрий день, Маріє Василівно!
        right: формальне звертання
  - type: fill-in
    title: Доповни фотодіалог
    instruction: Обери пропущене слово з родинної розмови.
    items:
      - sentence: Це ___ сім'я на фотографії.
        answer: моя
        options:
          - моя
          - мій
          - моє
        explanation: Сім'я — жіночого роду.
      - sentence: ___ це? Це мій тато.
        answer: Хто
        options:
          - Хто
          - Що
          - Де
        explanation: Для людини вживай хто.
      - sentence: Це моя сестра. ___ звати Катя.
        answer: Її
        options:
          - Її
          - Його
          - Вони
        explanation: Її підходить до сестри.
      - sentence: Це мій брат. ___ звати Коля.
        answer: Його
        options:
          - Його
          - Її
          - Вона
        explanation: Його підходить до брата.
      - sentence: А це ___ бабуся?
        answer: твоя
        options:
          - твоя
          - твій
          - твоє
        explanation: Бабуся — жіночого роду.
  - type: translate
    title: Швидка перевірка родинної лексики
    instruction: Обери англійське значення.
    items:
      - source: сім'я
        options:
          - text: family, close household
            correct: true
          - text: surname
            correct: false
          - text: profession
            correct: false
        explanation: Сім'я — слово для близької родини.
      - source: родина
        options:
          - text: family or kin
            correct: true
          - text: only one parent
            correct: false
          - text: first name
            correct: false
        explanation: Родина часто звучить ширше, ніж сім'я.
      - source: У мене є брат.
        options:
          - text: I have a brother.
            correct: true
          - text: You have a brother.
            correct: false
          - text: This is my brother.
            correct: false
        explanation: У мене є... — блок, щоб сказати, що щось або хтось є в мене.
      - source: Це моя сестра.
        options:
          - text: This is my sister.
            correct: true
          - text: This is my brother.
            correct: false
          - text: This is her sister.
            correct: false
        explanation: Моя узгоджується зі словом сестра.
      - source: Це мій тато.
        options:
          - text: This is my dad.
            correct: true
          - text: This is my mom.
            correct: false
          - text: Do you have a brother?
            correct: false
        explanation: Мій узгоджується зі словом тато.


### vocabulary.yaml

- lemma: сім'я
  translation: family, close household
  pos: noun
  usage: Це моя сім'я.
- lemma: родина
  translation: family or kin
  pos: noun
  usage: У мене велика родина.
- lemma: мама
  translation: mom
  pos: noun
  usage: Це моя мама.
- lemma: мати
  translation: mother
  pos: noun
  usage: Це моя мати.
- lemma: тато
  translation: dad
  pos: noun
  usage: Це мій тато.
- lemma: батько
  translation: father
  pos: noun
  usage: Це мій батько.
- lemma: брат
  translation: brother
  pos: noun
  usage: У мене є брат.
- lemma: сестра
  translation: sister
  pos: noun
  usage: У мене є сестра.
- lemma: син
  translation: son
  pos: noun
  usage: Це мій син.
- lemma: дочка
  translation: daughter
  pos: noun
  usage: Це моя дочка.
- lemma: донька
  translation: daughter
  pos: noun
  usage: Це моя донька.
- lemma: бабуся
  translation: grandmother
  pos: noun
  usage: Це моя бабуся.
- lemma: дідусь
  translation: grandfather
  pos: noun
  usage: Це мій дідусь.
- lemma: батьки
  translation: parents
  pos: noun plural
  usage: Це мої батьки.
- lemma: місто
  translation: city
  pos: noun
  usage: Це моє місто.
- lemma: родичі
  translation: relatives
  pos: noun plural
  usage: Це мої родичі.
- lemma: дядько
  translation: uncle
  pos: noun
  usage: Це мій дядько.
- lemma: тітка
  translation: aunt
  pos: noun
  usage: Це моя тітка.
- lemma: дружина
  translation: wife
  pos: noun
  usage: Моя дружина — вчителька.
- lemma: чоловік
  translation: man / husband
  pos: noun
  usage: Мій чоловік працює в лікарні.
- lemma: дитина
  translation: child
  pos: noun
  usage: Це маленька дитина.
- lemma: молодший
  translation: younger
  pos: adjective
  usage: Це мій молодший брат.
- lemma: старший
  translation: older
  pos: adjective
  usage: Це мій старший брат.
- lemma: одружений
  translation: married
  pos: adjective
  usage: Мій брат одружений.
- lemma: мій
  translation: my, masculine
  pos: pronoun
  usage: Це мій брат.
- lemma: моя
  translation: my, feminine
  pos: pronoun
  usage: Це моя сестра.
- lemma: моє
  translation: my, neuter
  pos: pronoun
  usage: Це моє місто.
- lemma: мої
  translation: my, plural
  pos: pronoun
  usage: Це мої батьки.
- lemma: твій
  translation: your, masculine informal
  pos: pronoun
  usage: Це твій брат?
- lemma: твоя
  translation: your, feminine informal
  pos: pronoun
  usage: Це твоя мама?
- lemma: твоє
  translation: your, neuter informal
  pos: pronoun
  usage: Це твоє прізвище?
- lemma: твої
  translation: your, plural informal
  pos: pronoun
  usage: Це твої родичі?
- lemma: його
  translation: his / him, fixed possessive here
  pos: pronoun
  usage: Його звати Коля.
- lemma: її
  translation: her, fixed possessive here
  pos: pronoun
  usage: Її звати Катя.
- lemma: у мене є
  translation: I have
  pos: phrase
  usage: У мене є брат.
- lemma: у тебе є
  translation: you have, informal
  pos: phrase
  usage: У тебе є сестра?
- lemma: у вас є
  translation: you have, formal or plural
  pos: phrase
  usage: У вас є діти?
- lemma: один
  translation: one, masculine
  pos: numeral
  usage: один брат
- lemma: одна
  translation: one, feminine
  pos: numeral
  usage: одна сестра
- lemma: два
  translation: two, masculine/neuter
  pos: numeral
  usage: два брати
- lemma: дві
  translation: two, feminine
  pos: numeral
  usage: дві сестри
- lemma: чи
  translation: or / whether in questions
  pos: conjunction
  usage: У тебе є брати чи сестри?
- lemma: тільки
  translation: only
  pos: adverb
  usage: У мене тільки один брат.
- lemma: ім'я
  translation: given name
  pos: noun
  usage: Моє ім'я Марко.
- lemma: прізвище
  translation: surname
  pos: noun
  usage: Моє прізвище Коваленко.
- lemma: по батькові
  translation: patronymic
  pos: phrase
  usage: Василівно — це по батькові.
- lemma: хто
  translation: who
  pos: pronoun
  usage: Хто це?
- lemma: звати
  translation: to call / be named
  pos: verb
  usage: Його звати Коля.
- lemma: працювати
  translation: to work
  pos: verb
  usage: Вона працює в школі.
- lemma: вчителька
  translation: female teacher
  pos: noun
  usage: Моя мама — вчителька.
- lemma: інженер
  translation: engineer
  pos: noun
  usage: Мій тато — інженер.


### resources.yaml

- title: ULP Season 1, Episode 6 — Family + I Have
  role: podcast
  source_ref: ULP Season 1, Episode 6 — Family + I Have
  url: https://www.ukrainianlessons.com/episode6/
  notes: "Plan reference: family words, the phrase У мене є, and one/two gender agreement."
- title: ULP Season 1, Episode 7 — Possessive Pronouns
  role: podcast
  source_ref: ULP Season 1, Episode 7 — Possessive Pronouns
  url: https://www.ukrainianlessons.com/episode7/
  notes: "Plan reference: мій/моя/моє/мої and Це моя мама."
- title: ULP Season 1, Episode 10 — Review
  role: podcast
  source_ref: ULP Season 1, Episode 10 — Review
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
