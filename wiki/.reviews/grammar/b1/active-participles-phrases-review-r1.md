✅ Message sent to Gemini (ID: 28352) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28352...
📨 Message #28352
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-b1-active-participles-phrases-r1
   Time: 2026-04-06T09:47:11.338238+00:00

============================================================

You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: b1, Slug: active-participles-phrases, Round: 1

## Review Rubric (score EACH dimension 1-10, then average)

1. **Factual accuracy** — every claim must have evidence from sources. Vague or unsourced claims → deduct points.
2. **Ukrainian language quality** — check for Russianisms (кон→кін), surzhyk (шо→що), calques (приймати душ→брати душ). Even ONE Russianism = max 7/10.
3. **Decolonization** — is Ukrainian presented on its own terms? Any 'like Russian but...' framing = max 6/10.
4. **Completeness** — does it cover ALL aspects a module writer needs? Missing sections or shallow treatment → deduct.
5. **Actionable guidance** — can a writer actually USE this? Generic advice like 'teach it well' = max 5/10. Must have specific examples, sequences, exercises.

## Rules
- Score each dimension separately, then give weighted average.
- Be honest. If the article is excellent, say so. 10/10 IS possible.
- 9/10 = excellent with minor issues. 8/10 = good. 7/10 = needs work.
- Output a <fixes> block with specific changes. If the article is clean, output <fixes></fixes> (empty).
- Do NOT invent problems. Fabricated issues waste rebuild cycles.

## Fix syntax

Two formats are available:

**1. Replace existing text** (for corrections, rewording):
Use a SHORT anchor (1-2 sentences max) for the old: text. Do NOT paste massive paragraphs — they break exact matching.
```
old: short exact text to find
new: replacement text
```

**2. Insert new content** (for missing sections, added examples):
Use INSERT AFTER with a short anchor from the article, then the new text to add.
```
INSERT AFTER: short anchor text that exists in the article
NEW TEXT: the new content to insert after the anchor
```

Separate multiple fixes with `---`.

## Output format

Dimension scores:
1. Factual: X/10 — [evidence]
2. Language: X/10 — [evidence]
3. Decolonization: X/10 — [evidence]
4. Completeness: X/10 — [evidence]
5. Actionable: X/10 — [evidence]

**Overall: X/10**

<fixes>
old: exact text to find in the article
new: replacement text
---
INSERT AFTER: anchor text in article
NEW TEXT: content to add after the anchor
</fixes>

## Article to review

# Граматика B1: Активні дієприкметники та їхній стиль

<!-- wiki-meta
slug: active-participles-style
domain: grammar/b1
tracks: [b1, b2]
sources: [7-klas-ukrmova-zabolotnyi-2024_s0092, 10-klas-ukrmova-karaman-2018_s0333, 7-klas-ukrmova-litvinova-2024_s0094, 7-klas-ukrmova-zabolotnyi-2024_s0095, 11-klas-ukrajinska-mova-glazova-2019_s0071, 11-klas-ukrmova-zabolotnyi-2019_s0075, 7-klas-ukrmova-avramenko-2024_s0106, 11-klas-ukrajinska-mova-glazova-2019_s0072, 7-klas-ukrmova-litvinova-2024_s0096, 11-klas-ukrajinska-mova-avramenko-2019_s0075, 7-klas-ukrmova-zabolotnyi-2024_s0096, 11-klas-ukrajinska-mova-avramenko-2019_s0077, 9-klas-ukrajinska-mova-avramenko-2017_s0141, 7-klas-ukrmova-zabolotnyi-2024_s0093, 11-klas-ukrmova-zabolotnyi-2019_s0076, 10-klas-ukrmova-karaman-2018_s0337, 7-klas-ukrmova-litvinova-2024_s0103, 7-klas-ukrmova-zabolotnyi-2024_s0094, 11-klas-ukrajinska-mova-glazova-2019_s0070]
compiled: 2026-04-06
-->

## Як це пояснюють у школі (How Schools Teach This)

В українській шкільній програмі тема дієприкметників, зокрема розрізнення активних та пасивних, системно вводиться у 7 класі. Підручники послідовно визначають дієприкметник як особливу форму дієслова, що виражає ознаку предмета за дією (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`, `10-klas-ukrmova-karaman-2018_s0333`).

Ключовим для пояснення є семантичний критерій:
- **Активні дієприкметники** виражають ознаку предмета, який **сам виконує дію** (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0092`, `7-klas-ukrmova-litvinova-2024_s0094`, `11-klas-ukrajinska-mova-glazova-2019_s0071`). Типові приклади, що наводяться для ілюстрації: *пожовкле листя* (листя само пожовкло), *сяючі зорі* (зорі сяють самі), *палаючий вогонь* (вогонь сам палає).
- **Пасивні дієприкметники** виражають ознаку предмета, який **зазнає дії з боку іншого виконавця** (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0092`, `7-klas-ukrmova-litvinova-2024_s0094`). Приклади: *написаний (учнем) твір*, *зірване (вітром) листя*.

Цей фундаментальний поділ на "діяча" та "об'єкт дії" є відправною точкою для подальшого вивчення їх творення, відмінювання та, що найважливіше для рівня B1+, стилістично правильного вживання. Вже у 7 класі учнів попереджають про обмеженість уживання активних дієприкметників теперішнього часу (Джерело: `7-klas-ukrmova-avramenko-2024_s0106`, `7-klas-ukrmova-litvinova-2024_s0096`).

## Повна парадигма (Full Paradigm)

Активні дієприкметники мають форми теперішнього та минулого часу. Вони змінюються за родами, числами та відмінками, як прикметники твердої групи (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`).

### Активні дієприкметники минулого часу

Це найпоширеніша та стилістично нейтральна група активних дієприкметників.

| Правило творення | Приклад |
| :--- | :--- |
| Основа інфінітива **доконаного** виду неперехідного дієслова + суфікс **-л-** | `посивіти → посиві**л**ий` (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`)<br>`потемніти → потемні**л**ий` (Джерело: `11-klas-ukrmova-zabolotnyi-2019_s0075`)<br>`змарніти → змарні**л**ий` (Джерело: `11-klas-ukrmova-zabolotnyi-2019_s0075`) |
| Якщо основа інфінітива закінчується на суфікс **-ну-**, він випадає. | `засохнути → засохлий` (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0095`)<br>`змерзнути → змерзлий` (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0095`)<br>`притихнути → притихлий` (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`) |

### Активні дієприкметники теперішнього часу

Ці форми мають **дуже обмежене** та стилістично марковане вживання в сучасній українській мові.

| Правило творення | Приклад |
| :--- | :--- |
| Основа дієслова **теперішнього** часу **недоконаного** виду І дієвідміни + суфікс **-уч- (-юч-)** | `знають → зна**юч**ий` (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`)<br>`працюють → прац**ююч**ий` (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`)<br>`в'януть → в'ян**уч**ий` (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0095`) |
| Основа дієслова **теперішнього** часу **недоконаного** виду ІІ дієвідміни + суфікс **-ач- (-яч-)** | `лежать → леж**ач**ий` (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`)<br>`стоять → сто**яч**ий` (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0071`)<br>`тремтять → тремт**яч**ий` (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0095`) |

## Частотність і пріоритети (Frequency & Priorities)

Для учня рівня B1/B2 пріоритезація є критично важливою:

1.  **Найвищий пріоритет: Активні дієприкметники минулого часу на `-лий`**. Це продуктивна, стилістично нейтральна і широко вживана форма. Володіння нею є обов'язковим. Приклади як *пожовклий, опалий, зів'ялий, розквітлий* є невід'ємною частиною природного мовлення.

2.  **Середній пріоритет: Розпізнавання та правильна інтерпретація дієприкметників на `-учий/-ячий`, що стали прикметниками**. Учень має знати, що слова на кшталт *лежачий (камінь), квітучий (сад), співучий (народ), палюче (сонце)* позначають **постійну ознаку**, а не дію в процесі (Джерело: `7-klas-ukrmova-litvinova-2024_s0096`, `11-klas-ukrajinska-mova-avramenko-2019_s0077`).

3.  **Низький пріоритет: Самостійне утворення активних дієприкметників теперішнього часу на `-учий/-ячий`**. Це не є продуктивною моделлю для сучасного мовлення. Підручники наголошують, що такі форми "не властиві" (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0072`), їх "вживаємо рідко" (Джерело: `7-klas-ukrmova-avramenko-2024_s0106`), і вони "переважно не відповідають нормам сучасної української мови" (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0096`). Їхнє вживання здебільшого обмежується науковими термінами (*блукаючий нерв*) та художнім стилем (*синіючі далі*) (Джерело: `11-klas-ukrajinska-mova-avramenko-2019_s0075`).

**Основний пріоритет для учня – не творити нові форми на `-учий/-ячий`, а натомість опанувати природні українські відповідники.**

## Типові помилки L2 (Common L2 Errors)

Для англомовних учнів, звиклих до продуктивності суфікса "-ing", спокуса калькувати цю модель є основною причиною помилок. Головне завдання — засвоїти, що українська мова використовує інші, синтаксичніші, засоби.

| ❌ Помилково (Unnatural Ukrainian) | ✅ Правильно (Natural Ukrainian) | Чому |
| :--- | :--- | :--- |
| *людина, **читаюча** книгу* | *людина, **що (яка) читає** книгу* | Для опису дії, що відбувається в цей момент, перевага надається підрядним реченням зі сполучником *що* або *який*. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0096`, `11-klas-ukrajinska-mova-glazova-2019_s0072`) |
| ***діючий** закон* | ***чинний** закон* | Для багатьох поширених понять існують сталі прикметники або синоніми, які витіснили активні дієприкметники. (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0072`, `7-klas-ukrmova-avramenko-2024_s0106`) |
| ***оточуючі** люди* | ***довколишні** люди* / *оточення* | Замість дієприкметника часто використовується інший прикметник або іменник. (Джерело: `11-klas-ukrajinska-mova-avramenko-2019_s0077`, `11-klas-ukrajinska-mova-glazova-2019_s0072`) |
| ***знеболюючий** засіб* | ***знеболювальний** засіб* | Для позначення призначення предмета часто вживаються прикметники із суфіксом **-альн-**. (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0072`, `7-klas-ukrmova-zabolotnyi-2024_s0096`) |
| ***сидячі** місця* | *місця **для сидіння*** | Часто замість дієприкметника використовується конструкція "іменник + прийменник + іменник". (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0072`, `7-klas-ukrmova-zabolotnyi-2024_s0096`) |
| *чоловік, **зробивший** роботу* | *чоловік, **який зробив** роботу* / *той, **що зробив*** | В українській мові **не утворюються** активні дієприкметники минулого часу за допомогою суфіксів **-ш-**, **-вш-**. Це грубе порушення норми. (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0072`, `7-klas-ukrmova-litvinova-2024_s0096`) |
| ***навчавшийся** у школі* | *той, хто **навчався** в школі* | В українській мові **не утворюються** дієприкметники від дієслів на **-ся**. (Джерело: `7-klas-ukrmova-litvinova-2024_s0096`) |

## Деколонізаційні застереження (Decolonization Notes)

**Це ключовий розділ для розуміння стилістики активних дієприкметників.** Обережне ставлення до форм на `-учий/-ячий` та повна заборона форм на `-вший/-ший` є важливим елементом мовної стійкості та утвердження самобутності української мови.

1.  **Відмінність від російської мови:** На відміну від російської, де активні дієприкметники теперішнього часу (*читающий, делающий*) та минулого (*читавший, делавший*) є надзвичайно продуктивними і стилістично нейтральними, в українській мові їхня роль значно вужча. Намагання калькувати російські конструкції призводить до появи неприродних для української мови висловів.

2.  **Стилістична норма як маркер:** Вживання конструкцій на кшталт *ідуча дівчина* замість *дівчина, що йде* або *бувший уряд* замість *колишній уряд* (Джерело: `11-klas-ukrajinska-mova-avramenko-2019_s0075`) сприймається як ознака суржику або недостатнього володіння літературною нормою. Боротьба за чистоту мови, про яку писав Б. Антоненко-Давидович, включає уникнення таких русизмів (Джерело: `10-klas-ukrmova-karaman-2018_s0115`, `ext-article-0`).

3.  **Українська граматика — не "варіант російської"**: Важливо пояснити учням, що обмежене вживання активних дієприкметників теперішнього часу — це не "недолік" чи "виняток", а системна риса українського синтаксису, який віддає перевагу підрядним реченням для вираження відповідних значень. Українська норма є самодостатньою.

4.  **Форми на `-ший/-вший` — червона лінія**: Це найпомітніший маркер російського впливу. Підручники категоричні: слів *сказавший, привівша* в українській мові не існує, це грубе порушення норми (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0072`, `11-klas-ukrmova-zabolotnyi-2019_s0075`). Правильним відповідником є конструкція з *той, що/який* + дієслово минулого часу.

## Природні приклади (Natural Examples)

**Група 1: Активні дієприкметники минулого часу на `-лий` (поширена і природна модель)**

1.  Чути шелест **опалого** вночі листя. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0093`)
2.  Після повеней відновлюються **висохлі** в спеку ставки. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0093`)
3.  У саду пишається ще не **розквітлий** бузок. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0093`)
4.  **Посивілий** з літами в бою, я над квітами щастя стою. (Джерело: `10-klas-ukrmova-karaman-2018_s0337`)
5.  **Усохлий** дуб, насупившись рогато, червоний обрій настромив на ріг. (Джерело: `11-klas-ukrmova-zabolotnyi-2019_s0076`)
6.  ...вітер змітає останні **пожовклі** листки. (Джерело: `11-klas-ukrmova-zabolotnyi-2019_s0076`)

**Група 2: Активні дієприкметники теперішнього часу на `-учий/-ячий` (вживаються рідко, переважно в художньому/науковому стилях або як постійна ознака)**

7.  Вірю в Слово. Велике, **палаюче**, наче сонце! (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0070`)
8.  Скільки ласки й привабливих мрій у цій милій **чаруючій** мові! (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0070`)
9.  Моя люба зоря ронить в серце мені, наче сльози, проміння **тремтяче**. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0096`)
10. Здалеку долітають **завмираючі** гуки музики. (Джерело: `7-klas-ukrmova-avramenko-2024_s0106`)
11. Під **лежачий** камінь вода не тече. (Джерело: `7-klas-ukrmova-avramenko-2024_s0106`)
12. І сходить сонце, **скупане** в росі, і спіє день... (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0092`) — *Примітка: це пасивний дієприкметник, але наведений для контрасту з активними.*

## Рекомендації для вправ (Activity Concepts)

-   **Phase 1: Ідентифікація та розрізнення.** Вправи на розрізнення активних і пасивних дієприкметників за значенням. "Назвіть, у якому реченні листя саме пожовкло, а в якому його пофарбували?". Завдання типу "випишіть спочатку речення з активними дієприкметниками, а потім – з пасивними" (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0094`).
-   **Phase 2: Засвоєння форм на `-лий`**. Вправи на утворення дієприкметників минулого часу від дієслів доконаного виду (*постаріти -> постарілий*). Завдання "доповніть речення, утворивши дієприкметник від дієслова в дужках". (Джерело: `10-klas-ukrmova-karaman-2018_s0337`).
-   **Phase 3: Опанування стилістичної заміни.** Це ключовий етап для B1+. Вправи на трансформацію неприродних речень у природні. "Перепишіть, замінюючи виділені дієприкметники правильними відповідниками". Завдання "замініть підрядну частину дієприкметниковим зворотом, де це можливо, або опишіть, чому це неможливо" (Джерело: `11-klas-ukrmova-zabolotnyi-2019_s0076`). Набір вправ "Знайди помилку" з класичними помилками (*діючий закон, слідуюча зупинка*).

## Зв'язки з іншими темами

-   **Пасивні дієприкметники:** Тема вивчається нерозривно з пасивними дієприкметниками для контрасту.
-   **Прикметники:** Дієприкметники мають граматичні ознаки прикметників (рід, число, відмінок) і часто виконують ту ж синтаксичну роль означення. Важливо розрізняти дієприкметник (ознака за дією) від чистого прикметника (постійна ознака) (Джерело: `10-klas-ukrmova-karaman-2018_s0340`).
-   **Підрядні означальні речення:** Конструкції з *що/який* є основним синтаксичним еквівалентом для активних дієприкметників теперішнього часу.
-   **Дієприкметниковий зворот:** Дієприкметники є ядром дієприкметникових зворотів, вивчення яких є важливою темою синтаксису та пунктуації.

## Пов'язані статті

-   `grammar/b1/passive-participles`
-   `grammar/a2/adjectives-declension`
-   `syntax/b1/relative-clauses-that-define`
-   `syntax/b1/participial-phrases-punctuation`


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=16792 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum w...
1. **Factual accuracy**: 10/10 — The brief correctly defines active participles, accurately details the formation rules (past tense from perfective intransitive verbs with `-л-`; present tense with `-уч-/-юч-`, `-ач-/-яч-`), and correctly identifies common L2 errors and their natural Ukrainian equivalents.
2. **Ukrainian language quality**: 9/10 — The language is highly professional and natural, with one minor exception. The comparative adjective form "синтаксичніші" in "інші, синтаксичніші, засоби" is stylistically awkward and non-standard (as "синтаксичний" is a relative adjective that typically does not form degrees of comparison). It should be rephrased.
3. **Decolonization**: 10/10 — Outstanding. The brief explicitly tackles the most pervasive Russian interference (the overuse of present active participles and the non-existent `-вший/-ший` suffixes). It frames the Ukrainian preference for relative clauses as a "systemic feature" and "self-sufficient norm," rather than a deficiency compared to Russian.
4. **Completeness**: 10/10 — The brief covers all necessary aspects: grammatical paradigms, strict priority levels for B1/B2 learners (which is crucial to prevent them from wasting time on unproductive forms), common L2 pitfalls, decolonization context, and authentic textbook examples.
5. **Actionable guidance**: 10/10 — The recommendations for activities are structured logically into phases (Identification -> Mastering `-лий` -> Stylistic replacement). The "Find the Error" suggestions directly target the most frequent L2 mistakes.

**Overall: 9.8/10**

<fixes>
old: Головне завдання — засвоїти, що українська мова використовує інші, синтаксичніші, засоби.
new: Головне завдання — засвоїти, що українська мова використовує інші, переважно синтаксичні, засоби.
</fixes>


────────────────────────────────────────
✅ Gemini finished (1796 chars)
✅ Message sent to Claude (ID: 28354)
✓ Message 28354 acknowledged
   Auto-acknowledged reply #28354 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-b1-active-participles-phrases-r1' — skipping GH posting (review saved to orchestration/)
✓ Message 28352 acknowledged
