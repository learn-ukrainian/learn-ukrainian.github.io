{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of lesson 2. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Читаємо слова", "sections": ["Склади", "Голосні літери", "Читаємо слова"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Друк, зошит, перевірка", "sections": ["Пастки читання", "Друк, зошит, перевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Далі", "sections": ["Далі"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 3, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 1}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 1}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 2}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 3}, {"placement": "workbook", "index": 5, "new_id": "act-5", "lesson": 3}], "items_min_exempt": [{"id": "act-4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w2", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w3", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w4", "reason": "5-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "5-item original activity preserved from baseline"}, {"id": "act-5", "reason": "3-item original activity preserved from baseline"}], "proper_names": []}
Independent Astra review after Gemini self-adjust. Fail ungrounded gender/government/examples. VESUM/`sources` is how the Ukrainian is better than a fluent guess; this corpus trains an LLM and tests the tools.

Score ALL five dimensions in ONE JSON object. The lesson artifacts appear ONCE below.
Do not restate them. Do not emit five essays. Do not emit a second JSON object.

Dimensions: pedagogical, naturalness, decolonization, engagement, tone.
Each value must be:
{"score": <0-10 number>, "verdict": "PASS"|"REVISE"|"REJECT", "evidence": "<one short sentence in your words>", "evidence_quotes": ["<8-20 consecutive words copied from the artifacts, single line, no extra spaces>"]}

Upgrade rules: A1 bilingual (UK then EN); no ```text learner examples; last lesson
closes with Підсумок модуля — Module summary; VESUM/sources for gender/government.

Return ONLY one JSON object, nothing before or after:
{"pedagogical": {...}, "naturalness": {...}, "decolonization": {...}, "engagement": {...}, "tone": {...}}

## module.md

# Друк, зошит, перевірка

У першому уроці ви навчилися рахувати склади та читати перші слова: **ма́ма**, **молоко́**, **ву́лиця**. In Lesson 1 you learned to count syllables and read your first words: **ма́ма** (mother), **молоко́** (milk), **ву́лиця** (street).

Тепер ми переходимо до безпечних читацьких звичок і роботи з рукописним текстом — now we turn to safe reading habits and working with handwritten text:
- **Уникати пасток читання** — avoid common reading traps such as splitting **дж** and **дз**, ignoring **ь**, or blurring **о**;
- **Розпізнавати друк і рукопис** — connect printed letters to handwritten forms in a notebook;
- **Перевіряти себе** — apply a step-by-step decoding routine before reading aloud.

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

Let us examine the most common traps that English speakers encounter when reading Ukrainian:

- **Злиті звуки ДЖ та ДЗ** (Fused sounds ДЖ and ДЗ):
  In Ukrainian roots, **дж** and **дз** represent single fused sounds: **[дж]** as in **джерело́** (water spring, source) and **[дз]** as in **дзе́ркало** (mirror). Do not pronounce them as separate letters. Ukrainian textbooks highlight this unified pronunciation: «Буквосполучення дж, дз позначають один злитий звук» (quoted from: Вашуленко, Українська мова 2 клас, p. 23-27).

- **Знак м'якшення Ь** (The soft sign Ь):
  The letter **ь** produces no independent sound; its only role is to indicate that the preceding consonant is soft: «Знак м'якшення не позначає окремого звука, а вказує на м'якість попереднього приголосного» (quoted from: Захарійчук 1 клас (НУШ 2025), p. 13-15). Read **день** (day) with a soft final [нʲ], not an extra vowel. The same softening occurs in **о́сінь** (autumn), **ба́тько** (father), and **вчи́тель** (teacher).

- **Апостроф '** (The apostrophe '):
  The apostrophe indicates a distinct, separate pronunciation where the preceding consonant stays hard, and the following iotated vowel retains its full [й] sound: **сім'я́** (family) is read as a firm [сім] followed by [йа], never merged into [сіма].

- **Чистий звук О** (Clean sound О):
  Ukrainian vowels never reduce to a neutral vowel. Every **о** in **молоко́** (milk) stays a distinct and open **[о]**, whether stressed or unstressed.

- **Літера Ї** (The letter Ї):
  The letter **ї** always marks two sounds: **[йі]**. In **Украї́на** (Ukraine) and **Ки́їв** (Kyiv), pronounce the full **[й]** glide every time.

<!-- INJECT_ACTIVITY: act-traps-match -->

<!-- INJECT_ACTIVITY: act-traps-quiz -->

<!-- INJECT_ACTIVITY: act-traps-tf -->

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

Practice this partner routine with a fellow learner:

> Олена: Подивися на цей запис у зошиті. Що тут написано? (Look at this entry in the notebook. What is written here?)
> Тарас: Тут написано друковане слово «день». (Here is written the printed word "день".)
> Олена: Правильно! А скільки голосних звуків у слові «Київ»? (Correct! And how many vowel sounds in the word "Київ"?)
> Тарас: Два голосні звуки: [и] та [і]. Тому це два склади! (Two vowel sounds: [и] and [і]. Therefore it is two syllables!)
> Олена: Молодець! А як прочитати слово «джерело»? (Well done! And how to read the word "джерело"?)
> Тарас: Буквосполучення «дж» читаємо разом: [джерело]. (The letter combination "дж" is read together: [джерело].)

Support after the dialogue:

| Українська | English support |
| --- | --- |
| **Подивися на цей запис у зошиті. Що тут написано?** | Look at this entry in the notebook. What is written here? |
| **Тут написано друковане слово «день».** | Here is written the printed word "день". |
| **Правильно! А скільки голосних звуків у слові «Київ»?** | Correct! And how many vowel sounds in the word "Київ"? |
| **Два голосні звуки: [и] та [і]. Тому це два склади!** | Two vowel sounds: [и] and [і]. Therefore it is two syllables! |
| **Молодець! А як прочитати слово «джерело»?** | Well done! And how to read the word "джерело"? |
| **Буквосполучення «дж» читаємо разом: [джерело].** | The letter combination "дж" is read together: [джерело]. |

Follow the sound analysis routine established in Ukrainian classrooms: «Звуковий аналіз слова: 1) Визначаю голосні звуки 2) Ділю слово на склади 3) Ставлю наголос 4) Позначаю приголосні звуки» (quoted from: Большакова, буквар 1 клас, p. 29). This four-step sequence guarantees steady progress.

<!-- INJECT_ACTIVITY: act-notebook-match -->

<!-- INJECT_ACTIVITY: act-reading-check -->

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

Ви навчилися впевнено розпізнавати друковані форми, уникати підступних пасток та перевіряти себе перед читанням уголос. You have learned to confidently recognize print forms, avoid tricky reading traps, and check yourself before reading aloud. У наступному уроці ми закріпимо всі правила на цілісних текстах та підіб'ємо підсумок модуля. In the next lesson, we will consolidate all the rules on full texts and summarize the module.


## activities.yaml

inline:
- id: act-traps-match
  type: match-up
  title: Правило для кожної пастки
  instruction: З'єднай слово або знак із правилом безпечного читання.
  pairs:
  - left: джерело́
    right: читай [дж] як один злитий звук
  - left: день
    right: м'який знак пом'якшує приголосний [нʲ]
  - left: сім'я́
    right: 'апостроф розділяє звуки: [сім] і [йа]'
  - left: Украї́на
    right: літера ї завжди дає два звуки [йі]
  - left: молоко́
    right: кожен звук [о] звучить чітко й відкрито
  - left: дзе́ркало
    right: читай [дз] як один злитий звук
- id: act-traps-quiz
  type: quiz
  title: Перевірка читацьких пасток
  instruction: Обери правильне пояснення для поданого слова.
  items:
  - prompt: Як правильно читати буквосполучення «дж» у слові джерело́?
    options:
    - text: Як один злитий звук [дж]
      correct: true
    - text: Як два окремі звуки [д] і [ж]
      correct: false
    explanation: Буквосполучення «дж» у корені позначає один злитий звук.
  - prompt: Яку роль відіграє знак м'якшення у слові день?
    options:
    - text: Пом'якшує попередній звук [н]
      correct: true
    - text: Позначає окремий голосний звук
      correct: false
    explanation: Ь не має власного звука, він пом'якшує попередній приголосний.
  - prompt: Як правильно прочитати слово сім'я́ через апостроф?
    options:
    - text: 'Роздільно: твердий [м] + [йа]'
      correct: true
    - text: 'М''яко разом: [сіма]'
      correct: false
    explanation: 'Апостроф вимагає роздільної вимови: твердий приголосний і йотований
      голосний [йа].'
  - prompt: Чому літеру ї у слові Украї́на не можна читати як просте [і]?
    options:
    - text: Бо ї завжди позначає два звуки [йі]
      correct: true
    - text: Бо ї пом'якшує попередній звук
      correct: false
    explanation: 'Літера Ї в українській мові завжди позначає два звуки: [й] та [і].'
  - prompt: Як звучить ненаголошене «о» в українському слові молоко́?
    options:
    - text: Залишається чистим і виразним звуком [о]
      correct: true
    - text: Перетворюється на нечітке [а]
      correct: false
    explanation: В українській мові ненаголошене «о» ніколи не перетворюється на [а].
  - prompt: Як читаємо буквосполучення «дз» у слові дзе́ркало?
    options:
    - text: Як один злитий звук [дз]
      correct: true
    - text: Як окремі звуки [д] та [з]
      correct: false
    explanation: Буквосполучення «дз» читається як один неподільний злитий звук.
- id: act-traps-tf
  type: true-false
  title: Твердження про пастки читання
  instruction: Визнач, чи є твердження правильним.
  items:
  - statement: У слові «молоко» всі три звуки [о] звучать чітко.
    correct: true
    explanation: В українській мові немає акання.
  - statement: Буквосполучення «дж» у слові «джерело» вимовляємо як два роздільні
      звуки.
    correct: false
    explanation: ДЖ позначає один злитий звук.
  - statement: Літера «ї» в слові «Україна» позначає два звуки [йі].
    correct: true
    explanation: Літера Ї завжди позначає два звуки.
  - statement: М'який знак позначає окремий голосний звук.
    correct: false
    explanation: Ь не має власного звука.
  - statement: Апостроф вимагає твердої вимови приголосного перед я, ю, є, ї.
    correct: true
    explanation: Приголосний перед апострофом залишається твердим.
  - statement: Буквосполучення «дз» у слові «дзеркало» позначає один злитий звук.
    correct: true
    explanation: ДЗ вимовляється як один неподільний звук.
- id: act-notebook-match
  type: match-up
  title: Друк і рукописні форми
  instruction: З'єднай друковане слово з його описом або рукописною ознакою.
  pairs:
  - left: 'друк: день'
    right: 'зошит: слово з кінцевим знаком м''якшення'
  - left: 'друк: Київ'
    right: 'зошит: слово з двома крапками над ї'
  - left: 'друк: джерело'
    right: 'зошит: слово зі злитим буквосполученням дж'
  - left: 'друк: сім''я'
    right: 'зошит: слово з роздільним апострофом'
  - left: 'друк: осінь'
    right: 'зошит: слово з двома м''якими приголосними'
  - left: 'друк: дзеркало'
    right: 'зошит: слово зі злитим буквосполученням дз'
- id: act-reading-check
  type: true-false
  title: Правила самоперевірки читання
  instruction: Визнач, чи є твердження правильним.
  items:
  - statement: Знак м'якшення (ь) ніколи не має власного звука.
    correct: true
    explanation: Ь лише показує м'якість попереднього приголосного.
  - statement: У слові джерело буквосполучення дж вимовляємо як два роздільні звуки.
    correct: false
    explanation: ДЖ у корені слова читаємо як один злитий звук.
  - statement: Апостроф вказує на роздільну вимову твердого приголосного перед я,
      ю, є, ї.
    correct: true
    explanation: Апостроф зберігає твердість приголосного і розділяє його з наступним
      йотованим.
  - statement: Літера ї іноді позначає один звук після м'якого приголосного.
    correct: false
    explanation: Літера Ї завжди позначає два звуки [йі] і ніколи не пом'якшує.
  - statement: В українській мові всі ненаголошені звуки [о] читаються чітко.
    correct: true
    explanation: Українське [о] ніколи не зазнає акання й звучить чітко.
  - statement: Перед читанням слова корисно порахувати голосні звуки.
    correct: true
    explanation: Скільки в слові голосних звуків — стільки й складів.
workbook:
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
- id: act-w3
  type: true-false
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
- id: act-w4
  type: match-up
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
- id: act-wb-group
  type: group-sort
  title: Розподіл слів за фонетичною ознакою
  instruction: Розподіли слова за їхньою ключовою фонетичною ознакою.
  groups:
  - label: Знак м'якшення (ь)
    items:
    - день
    - о́сінь
    - ба́тько
  - label: Злиті звуки (дж, дз)
    items:
    - джерело́
    - дзе́ркало
  - label: Літера ї або апостроф
    items:
    - Ки́їв
    - Украї́на
    - сім'я́
- id: act-wb-quiz
  type: quiz
  title: Читацькі правила на практиці
  instruction: Обери правильну відповідь на запитання про читання слів.
  items:
  - prompt: Скільки звуків позначає літера ї у слові Київ?
    options:
    - text: два звуки [йі]
      correct: true
    - text: один звук [і]
      correct: false
    explanation: 'Літера Ї завжди позначає два звуки: [й] та [і].'
  - prompt: Який приголосний є м'яким у слові батько?
    options:
    - text: звук [тʲ]
      correct: true
    - text: звук [к]
      correct: false
    explanation: 'Знак м''якшення після літери т пом''якшує саме її: [батʲко].'
  - prompt: Як вимовляємо буквосполучення дж у слові джерело?
    options:
    - text: як один неподільний злитий звук
      correct: true
    - text: як два роздільні звуки
      correct: false
    explanation: У кореневих словах буквосполучення «дж» є єдиним звуком.
  - prompt: Що вказує на роздільну вимову в слові сім'я?
    options:
    - text: апостроф
      correct: true
    - text: знак м'якшення
      correct: false
    explanation: Апостроф вказує на роздільну тверду вимову перед йотованим.
  - prompt: Який кінцевий приголосний є м'яким у слові вчитель?
    options:
    - text: звук [лʲ]
      correct: true
    - text: звук [ч]
      correct: false
    explanation: М'який знак у кінці слова вчитель пом'якшує звук [л].
  - prompt: Скільки складів має слово дзеркало?
    options:
    - text: три склади
      correct: true
    - text: чотири склади
      correct: false
    explanation: У слові дзеркало три голосні [е, а, о], отже, три склади.
- id: act-wb-odd
  type: odd-one-out
  title: Зайве слово за звуковою ознакою
  instruction: Обери слово, яке відрізняється від інших за вказаною фонетичною ознакою.
  items:
  - words:
    - день
    - о́сінь
    - вчи́тель
    - ма́ма
    answer: ма́ма
    explanation: Ма́ма не має знака м'якшення, тоді як інші три слова закінчуються
      м'яким знаком.
  - words:
    - джерело́
    - дзе́ркало
    - дзвін
    - молоко́
    answer: молоко́
    explanation: Молоко́ не містить буквосполучень дж чи дз.
  - words:
    - Ки́їв
    - Украї́на
    - ї́жа
    - ба́тько
    answer: ба́тько
    explanation: Ба́тько не має літери ї.
  - words:
    - сім'я́
    - м'я́со
    - п'ять
    - вода́
    answer: вода́
    explanation: Вода́ пишеться без апострофа.
  - words:
    - молоко́
    - столи́ця
    - ка́ша
    - день
    answer: день
    explanation: День — односкладове слово, а інші мають два або три склади.
  - words:
    - ба́тько
    - о́сінь
    - день
    - джерело́
    answer: джерело́
    explanation: Джерело́ не має знака м'якшення.
- id: act-wb-fill
  type: fill-in
  title: Встав правильну літеру або знак
  instruction: Встав пропущену літеру або графічний знак у слово.
  items:
  - sentence: Сьогодні гарний де__ь.
    options:
    - н
    - нь
    answer: нь
    explanation: 'У слові день у кінці пишемо знак м''якшення: день.'
  - sentence: У лісі б'є холодне __ерело.
    options:
    - дж
    - ж
    answer: дж
    explanation: Слово джерело починається зі злитого звука, що позначається буквосполученням
      дж.
  - sentence: Це дружна сім__я.
    options:
    - ''''
    - ь
    answer: ''''
    explanation: У слові сім'я ставимо апостроф для роздільної вимови.
  - sentence: Золота о́сі__ь настала.
    options:
    - н
    - нь
    answer: нь
    explanation: Слово о́сінь закінчується м'яким знаком.
  - sentence: У кімнаті висить велике __еркало.
    options:
    - дз
    - з
    answer: дз
    explanation: Слово дзеркало починається з буквосполучення дз.
  - sentence: Місто Ки__в — столиця України.
    options:
    - ї
    - і
    answer: ї
    explanation: У назві Київ пишемо літеру ї, яка завжди дає два звуки [йі].


## vocabulary.yaml

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
  translation: 'no'
  pos: particle
  usage: Ні.


## resources.yaml

- title: Большакова, буквар 1 клас, p. 29
  role: textbook
  source: Большакова, буквар 1 клас, p. 29
  notes: 'Plan reference: sound analysis routine for Ukrainian words.'
- title: Захарійчук 1 клас (НУШ 2025), p. 13-15
  role: textbook
  source: Захарійчук 1 клас (НУШ 2025), p. 13-15
  notes: 'Plan reference: symbols for vowel, hard consonant, and soft consonant sounds.'
- title: Вашуленко, Українська мова 2 клас, p. 23-27
  role: textbook
  source: Вашуленко, Українська мова 2 клас, p. 23-27
  notes: 'Plan reference: transfer, stress, and iotated-vowel reading context.'
- title: Anna Ohoiko — Ukrainian alphabet overview
  role: youtube
  url: https://www.youtube.com/watch?v=ksXIXj7CXwc
  channel: Ukrainian Lessons
  notes: Supplemental listening support for the vowel reading pass.
