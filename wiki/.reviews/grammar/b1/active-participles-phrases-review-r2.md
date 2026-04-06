✅ Message sent to Gemini (ID: 28297) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28297...
📨 Message #28297
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-b1-active-participles-phrases-r2
   Time: 2026-04-06T08:00:01.384933+00:00

============================================================

You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: b1, Slug: active-participles-phrases, Round: 2

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
slug: b1-active-participles-style
domain: grammar/b1
tracks: [b1, b2]
sources: [11-klas-ukrajinska-mova-avramenko-2019_s0295, 7-klas-ukrmova-litvinova-2024_s0009, 11-klas-ukrajinska-mova-glazova-2019_s0010, 7-klas-ukrmova-litvinova-2024_s0103, 6-klas-ukrmova-golub-2023_s0262, 7-klas-ukrmova-zabolotnyi-2024_s0092, 10-klas-ukrmova-karaman-2018_s0333, 10-klas-ukrmova-karaman-2018_s0337, 11-klas-ukrajinska-mova-glazova-2019_s0072, 5-klas-ukrmova-uhor-2022-1_s0092, 7-klas-ukrmova-avramenko-2024_s0106, 7-klas-ukrmova-litvinova-2024_s0094, 7-klas-ukrmova-litvinova-2024_s0096, 7-klas-ukrmova-litvinova-2024_s0209, 7-klas-ukrmova-zabolotnyi-2024_s0093, 7-klas-ukrmova-zabolotnyi-2024_s0094, 7-klas-ukrmova-zabolotnyi-2024_s0095, 7-klas-ukrmova-zabolotnyi-2024_s0096, 7-klas-ukrmova-zabolotnyi-2024_s0101, 9-klas-ukrajinska-mova-avramenko-2017_s0108, 9-klas-ukrajinska-mova-avramenko-2017_s0141, 10-klas-ukrajinska-mova-avramenko-2018_s0018, 10-klas-ukrmova-karaman-2018_s0115, 10-klas-ukrmova-karaman-2018_s0282, 10-klas-ukrmova-karaman-2018_s0340, 11-klas-ukrajinska-mova-avramenko-2019_s0062, 11-klas-ukrajinska-mova-avramenko-2019_s0075, 11-klas-ukrajinska-mova-avramenko-2019_s0077, 11-klas-ukrajinska-mova-avramenko-2019_s0082, 11-klas-ukrajinska-mova-avramenko-2019_s0246, 11-klas-ukrajinska-mova-avramenko-2019_s0295, 11-klas-ukrajinska-mova-glazova-2019_s0070, 11-klas-ukrajinska-mova-glazova-2019_s0071, 11-klas-ukrajinska-mova-glazova-2019_s0128, 11-klas-ukrajinska-mova-glazova-2019_s0325, 11-klas-ukrajinska-mova-voron-2019_s0039, 11-klas-ukrajinska-mova-voron-2019_s0416, 11-klas-ukrmova-zabolotnyi-2019_s0075, 11-klas-ukrmova-zabolotnyi-2019_s0076, 11-klas-ukrmova-zabolotnyi-2019_s0267, 11-klas-ukrmova-zabolotnyi-2019_s0271, 11-klas-ukrmova-zabolotnyi-2019_s0295, 11-klas-ukrmova-zabolotnyi-2019_s0301, 5-klas-ukrmova-litvinova-2022_s0194, 5-klas-ukrmova-litvinova-2022_s0209]
compiled: 2026-04-06
-->

## Як це пояснюють у школі (How Schools Teach This)

Українські шкільні підручники (зокрема, Заболотного, Авраменко, Глазової для 7-11 класів) вводять дієприкметники як особливу форму дієслова, що поєднує ознаки дієслова та прикметника. Ключовим для розуміння є поділ на **активні** та **пасивні** дієприкметники, який зазвичай ілюструється простою схемою:

*   **Активні дієп

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

```markdown
# Граматика B1: Активні дієприкметники та їхній стиль

<!-- wiki-meta
slug: b1-active-participles-style
domain: grammar/b1
tracks: [b1, b2]
sources: [11-klas-ukrajinska-mova-avramenko-2019_s0295, 7-klas-ukrmova-litvinova-2024_s0009, 11-klas-ukrajinska-mova-glazova-2019_s0010, 7-klas-ukrmova-litvinova-2024_s0103, 6-klas-ukrmova-golub-2023_s0262, 7-klas-ukrmova-zabolotnyi-2024_s0092, 10-klas-ukrmova-karaman-2018_s0333, 10-klas-ukrmova-karaman-2018_s0337, 11-klas-ukrajinska-mova-glazova-2019_s0072, 5-klas-ukrmova-uhor-2022-1_s0092, 7-klas-ukrmova-avramenko-2024_s0106, 7-klas-ukrmova-litvinova-2024_s0094, 7-klas-ukrmova-litvinova-2024_s0096, 7-klas-ukrmova-litvinova-2024_s0209, 7-klas-ukrmova-zabolotnyi-2024_s0093, 7-klas-ukrmova-zabolotnyi-2024_s0094, 7-klas-ukrmova-zabolotnyi-2024_s0095, 7-klas-ukrmova-zabolotnyi-2024_s0096, 7-klas-ukrmova-zabolotnyi-2024_s0101, 9-klas-ukrajinska-mova-avramenko-2017_s0108, 9-klas-ukrajinska-mova-avramenko-2017_s0141, 10-klas-ukrajinska-mova-avramenko-2018_s0018, 10-klas-ukrmova-karaman-2018_s0115, 10-klas-ukrmova-karaman-2018_s0282, 10-klas-ukrmova-karaman-2018_s0340, 11-klas-ukrajinska-mova-avramenko-2019_s0062, 11-klas-ukrajinska-mova-avramenko-2019_s0075, 11-klas-ukrajinska-mova-avramenko-2019_s0077, 11-klas-ukrajinska-mova-avramenko-2019_s0082, 11-klas-ukrajinska-mova-avramenko-2019_s0246, 11-klas-ukrajinska-mova-avramenko-2019_s0295, 11-klas-ukrajinska-mova-glazova-2019_s0070, 11-klas-ukrajinska-mova-glazova-2019_s0071, 11-klas-ukrajinska-mova-glazova-2019_s0128, 11-klas-ukrajinska-mova-glazova-2019_s0325, 11-klas-ukrajinska-mova-voron-2019_s0039, 11-klas-ukrajinska-mova-voron-2019_s0416, 11-klas-ukrmova-zabolotnyi-2019_s0075, 11-klas-ukrmova-zabolotnyi-2019_s0076, 11-klas-ukrmova-zabolotnyi-2019_s0267, 11-klas-ukrmova-zabolotnyi-2019_s0271, 11-klas-ukrmova-zabolotnyi-2019_s0295, 11-klas-ukrmova-zabolotnyi-2019_s0301, 5-klas-ukrmova-litvinova-2022_s0194, 5-klas-ukrmova-litvinova-2022_s0209]
compiled: 2026-04-06
-->

## Як це пояснюють у школі (How Schools Teach This)

Українські шкільні підручники (зокрема, Заболотного, Авраменко, Глазової для 7-11 класів) вводять дієприкметники як особливу форму дієслова, що поєднує ознаки дієслова та прикметника. Ключовим для розуміння є поділ на **активні** та **пасивні** дієприкметники, який зазвичай ілюструється простою схемою:

*   **Активні дієприкметники**: Ознака за дією, яку предмет виконує **сам**. (Джерело: Заболотний 7, chunk `s0092`).
    *   *Приклад:* `пожовтіле листя` (листя *само* пожовтіло), `сяючі зорі` (зорі *самі* сяють).
*   **Пасивні дієприкметники**: Ознака за дією, яку **хтось** виконує над предметом.
    *   *Приклад:* `написаний твір` (його *хтось* написав), `розбитий ящик` (його *хтось* розбив).

Вивчення активних дієприкметників починається в 7 класі, але набагато глибше й з погляду стилістичної норми розглядається в 10-11 класах. Основний акцент робиться на тому, що активні дієприкметники теперішнього часу є **невластивими** і **маловживаними** в сучасній українській мові. Усі підручники приділяють значну увагу правилам заміни таких форм.

## Повна парадигма (Full Paradigm)

Активні дієприкметники поділяються на дві групи за часом.

### 1. Активні дієприкметники минулого часу

Це продуктивна і стилістично нейтральна група в українській мові.

*   **Творення**: Від основи інфінітива **доконаного** виду за допомогою суфікса **-л-**.
    *   `посивіти` -> `посиві**л**ий`
    *   `потемніти` -> `потемні**л**ий`
    *   `розквітнути` -> `розквіт**л**ий`
*   **Особливість**: Якщо основа дієслова закінчується на суфікс **-ну-**, він випадає.
    *   `змерз**ну**ти` -> `змерз**л**ий` (не *змерзнулий*)
    *   `засох**ну**ти` -> `засох**л**ий` (не *засохнулий*)

### 2. Активні дієприкметники теперішнього часу

Ця група є **непродуктивною** і стилістично обмеженою. Їх вживання здебільшого вважається ознакою наукового, книжного стилю або калькуванням з російської мови.

*   **Творення**: Від основи дієслова теперішнього часу **недоконаного** виду за допомогою суфіксів:
    *   **-уч- (-юч-)** для дієслів I дієвідміни:
        *   `знають` -> `зна**юч**ий`
        *   `працюють` -> `прац**ююч**ий`
        *   `квітнуть` -> `квітн**уч**ий`
    *   **-ач- (-яч-)** для дієслів II дієвідміни:
        *   `лежать` -> `леж**ач**ий`
        *   `стоять` -> `сто**яч**ий`
        *   `тремтять` -> `тремт**яч**ий`

## Частотність і пріоритети (Frequency & Priorities)

Для рівня B1/B2 пріоритети чіткі:

1.  **Майстерне володіння активними дієприкметниками минулого часу на `-лий`**. Вони поширені, природні й необхідні для вираження послідовності дій (`опале листя`, `прибулий потяг`).

2.  **Засвоєння і автоматичне використання АЛЬТЕРНАТИВ дієприкметникам теперішнього часу**. Навчитись уникати форм на `-учий/-ачий` є важливішим, ніж навчитись їх утворювати. Найпоширеніші заміни (Джерела: Глазова 11, `s0072`; Авраменко 7, `s0106`; Заболотний 7, `s0096`):
    *   **Підрядна частина речення (конструкція "той, що..."):** Це найуніверсальніший і найправильніший спосіб.
        *   *НЕПРАВИЛЬНО:* `студент, читаючий книгу` -> *ПРАВИЛЬНО:* `студент, **що читає книгу**`
        *   *НЕПРАВИЛЬНО:* `протікаюча бочка` -> *ПРАВИЛЬНО:* `бочка, **що протікає**`
    *   **Іменник:**
        *   *НЕПРАВИЛЬНО:* `завідуючий відділом` -> *ПРАВИЛЬНО:* `**завідувач** відділу`
        *   *НЕПРАВИЛЬНО:* `початкуючий художник` -> *ПРАВИЛЬНО:* `художник-**початківець**`
    *   **Прикметник (часто з суфіксом `-альн-`):**
        *   *НЕПРАВИЛЬНО:* `знеболюючий засіб` -> *ПРАВИЛЬНО:* `знеболю**вальн**ий засіб`
        *   *НЕПРАВИЛЬНО:* `миючі засоби` -> *ПРАВИЛЬНО:* `**мийні** засоби`
    *   **Синонім:**
        *   *НЕПРАВИЛЬНО:* `хвилююча зустріч` -> *ПРАВИЛЬНО:* `**зворушлива** зустріч`
        *   *НЕПРАВИЛЬНО:* `діючий закон` -> *ПРАВИЛЬНО:* `**чинний** закон`
    *   **Інші конструкції:**
        *   *НЕПРАВИЛЬНО:* `сидячі місця` -> *ПРАВИЛЬНО:* `місця **для сидіння**`

## Типові помилки L2 (Common L2 Errors)

1.  **Надмірне вживання форм на `-учий/-ячий`**: Найпоширеніша помилка, що виникає через прямий переклад англійських "-ing" форм (a *reading* student) або під впливом російської мови. Для учнів B1/B2 це головна "погана звичка", якої треба позбутися.

2.  **Творення дієприкметників за російським зразком (суфікси `-ш-`, `-вш-`)**: Це грубе порушення норми. Форми як `попрацювавший`, `сказавший`, `прийшовший` є абсолютно неприпустимими в українській мові.
    *   *НЕПРАВИЛЬНО:* `постарівший чоловік` -> *ПРАВИЛЬНО:* `постарі**л**ий чоловік`
    *   *НЕПРАВИЛЬНО:* `людина, сказавша правду` -> *ПРАВИЛЬНО:* `людина, **що сказала** правду`

3.  **Творення дієприкметників від дієслів на `-ся`**: В українській мові такі форми не утворюються.
    *   *НЕПРАВИЛЬНО:* `хлопчик, що вмиваючийся` -> *ПРАВИЛЬНО:* `хлопчик, **що вмивається**`

## Деколонізаційні застереження (Decolonization Notes)

Тема активних дієприкметників є одним з ключових полів боротьби за чистоту української мови та її звільнення від російського впливу.

*   **Пряма калька**: Активні дієприкметники теперішнього часу на `-учий (-ючий), -ачий (-ячий)` фонетично і функціонально схожі на російські `-ущий (-ющий), -ащий (-ящий)`. У російській мові вони є нормальною, продуктивною частиною граматики. В українській мові вони історично мали обмежене вживання, але їх використання значно поширилося в радянський період через мовний контакт і пряме калькування.

*   **Стилістичний маркер**: У сучасному українському мовленні уникнення невиправданого вживання цих форм є ознакою високої мовної культури. Прагнення замінити `існуюча проблема` на `проблема, що існує` або `наявна проблема` — це свідомий вибір на користь питомо української синтаксичної моделі.

*   **Педагогічний імператив**: Навчаючи української, важливо пояснювати, що українська граматика — це самостійна система. Не можна пояснювати ці форми як "схожі на російські, але з обмеженнями". Треба наголошувати, що український синтаксис віддає перевагу підрядним реченням (`що робить`), а не дієприкметниковим зворотам там, де російська мова зробила б навпаки. Це і є навчання "мислити українською".

## Природні приклади (Natural Examples)

**Активні минулого часу (на `-лий`) - Пріоритет для вивчення**

1.  Чути шелест **опалого** вночі листя. (Джерело: Заболотний 7, `s0093`)
2.  Аж до самого небосхилу розляглося **засипане** снігом поле. (це пасивний, але структура речення добра) -> (Краще) Аж до самого небосхилу розляглось **потемніле** від хмар поле.
3.  І сходить сонце, **скупане** в росі... (це пасивний) -> (Краще) З-за гори виглянуло сонце, **позолотиле** верхівки дерев.
4.  Усохлий дуб, насупившись рогато, червоний обрій настромив на ріг. (Джерело: Глазова 11, `s0076`)
5.  Повсюди гілки, **зламані** під час буревію. (це пасивний) -> (Краще) На землі лежали **почорнілі** від дощу гілки.
6.  Раз добром **нагріте** серце вік не прохолоне. (це пасивний) -> (Краще) Його **посивіле** волосся розвівав вітер.
7.  Через усю кімнату простягнувся **пожовклий** сонячний промінь.
8.  На столі лежав **застиглий** шматок воску.
9.  Ми побачили **змерзлого** горобця, що сидів на гілці.
10. Я люблю дивитися на **потемніле** перед грозою небо.

**Стилістично виправдане або "застигле" вживання активних теперішнього часу**

1.  Під **лежачий** камінь вода не тече. (прислів'я, дієприкметник перейшов у прикметник)
2.  Здалеку долітають **завмираючі** гуки музики. (художній стиль)
3.  Вірю в Слово. Велике, **палаюче**, наче сонце! (поетичний, високий стиль)
4.  Скільки ласки й привабливих мрій у цій милій **чаруючій** мові! (художній стиль)
5.  Це був **зворушливий** (не *хвилюючий*) момент прощання.

## Зв'язки з іншими темами

*   **Passive Participles**: Активні та пасивні дієприкметники завжди вивчаються в парі для контрасту.
*   **Adjectives**: Активні дієприкметники відмінюються точно так само, як прикметники твердої групи, і виконують у реченні ту ж синтаксичну роль (означення).
*   **Complex Sentences (Складнопідрядні речення)**: Уміння будувати речення з підрядною означальною частиною (`..., що ...`) є необхідною передумовою для правильної заміни небажаних активних дієприкметників.
*   **Verbal Aspect (Вид дієслова)**: Творення дієприкметників чітко прив'язане до виду: минулого часу — переважно від доконаного, теперішнього — від недоконаного.

## Пов'язані статті

*   `grammar/b1/passive-participles-formation`
*   `grammar/a2/adjective-declension`
*   `syntax/b1/relative-clauses-що-який`
*   `verbs/b1/perfective-imperfective-aspect-review`
```


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=17211 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are rewriting specific sections of a grammar brief for the Ukrainian language curriculum wi...
Dimension scores:
1. Factual: 5/10 — The guide misses the absolute most critical rule about past active participles: they can **only** be formed from intransitive verbs (неперехідні дієслова). It then violently violates this missing rule in the "Natural Examples" section by inventing the non-existent word "позолотиле" (formed from the transitive verb *позолотити*). 
2. Language: 6/10 — The "Natural Examples" section is weirdly formatted with internal monologue and self-corrections ("це пасивний... -> Краще") that compare apples to oranges, alongside the hallucinated surzhyk/error form "позолотиле".
3. Decolonization: 9/10 — Excellent breakdown of the Soviet legacy of active present participles. Framing Ukrainian syntax on its own terms (favoring relative clauses) rather than "Russian with exceptions" is exactly right.
4. Completeness: 7/10 — The explanation of the forms and stylistic replacements is quite thorough, but completely omitting the transitive/intransitive distinction leaves a massive gap for anyone trying to actually generate these words.
5. Actionable: 6/10 — The replacement strategies are great, but the "Natural Examples" list for the recommended `-лий` participles is full of confusing meta-commentary and errors. A module writer cannot simply copy and use these as models.

**Overall: 6.6/10**

<fi

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18319 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum w...
```markdown
# Граматика B1: Активні дієприкметники та їхній стиль

<!-- wiki-meta
slug: b1-active-participles-style
domain: grammar/b1
tracks: [b1, b2]
sources: [11-klas-ukrajinska-mova-avramenko-2019_s0295, 7-klas-ukrmova-litvinova-2024_s0009, 11-klas-ukrajinska-mova-glazova-2019_s0010, 7-klas-ukrmova-litvinova-2024_s0103, 6-klas-ukrmova-golub-2023_s0262, 7-klas-ukrmova-zabolotnyi-2024_s0092, 10-klas-ukrmova-karaman-2018_s0333, 10-klas-ukrmova-karaman-2018_s0337, 11-klas-ukrajinska-mova-glazova-2019_s0072, 5-klas-ukrmova-uhor-2022-1_s0092, 7-klas-ukrmova-avramenko-2024_s0106, 7-klas-ukrmova-litvinova-2024_s0094, 7-klas-ukrmova-litvinova-2024_s0096, 7-klas-ukrmova-litvinova-2024_s0209, 7-klas-ukrmova-zabolotnyi-2024_s0093, 7-klas-ukrmova-zabolotnyi-2024_s0094, 7-klas-ukrmova-zabolotnyi-2024_s0095, 7-klas-ukrmova-zabolotnyi-2024_s0096, 7-klas-ukrmova-zabolotnyi-2024_s0101, 9-klas-ukrajinska-mova-avramenko-2017_s0108, 9-klas-ukrajinska-mova-avramenko-2017_s0141, 10-klas-ukrajinska-mova-avramenko-2018_s0018, 10-klas-ukrmova-karaman-2018_s0115, 10-klas-ukrmova-karaman-2018_s0282, 10-klas-ukrmova-karaman-2018_s0340, 11-klas-ukrajinska-mova-avramenko-2019_s0062, 11-klas-ukrajinska-mova-avramenko-2019_s0075, 11-klas-ukrajinska-mova-avramenko-2019_s0077, 11-klas-ukrajinska-mova-avramenko-2019_s0082, 11-klas-ukrajinska-mova-avramenko-2019_s0246, 11-klas-ukrajinska-mova-avramenko-2019_s0295, 11-klas-ukrajinska-mova-glazova-2019_s0070, 11-klas-ukrajinska-mova-glazova-2019_s0071, 11-klas-ukrajinska-mova-glazova-2019_s0128, 11-klas-ukrajinska-mova-glazova-2019_s0325, 11-klas-ukrajinska-mova-voron-2019_s0039, 11-klas-ukrajinska-mova-voron-2019_s0416, 11-klas-ukrmova-zabolotnyi-2019_s0075, 11-klas-ukrmova-zabolotnyi-2019_s0076, 11-klas-ukrmova-zabolotnyi-2019_s0267, 11-klas-ukrmova-zabolotnyi-2019_s0271, 11-klas-ukrmova-zabolotnyi-2019_s0295, 11-klas-ukrmova-zabolotnyi-2019_s0301, 5-klas-ukrmova-litvinova-2022_s0194, 5-klas-ukrmova-litvinova-2022_s0209]
compiled: 2026-04-06
-->

## Як це пояснюють у школі (How Schools Teach This)

Українські шкільні підручники (зокрема, Заболотного, Авраменко, Глазової для 7-11 класів) вводять дієприкметники як особливу форму дієслова, що поєднує ознаки дієслова та прикметника. Ключовим для розуміння є поділ на **активні** та **пасивні** дієприкметники, який зазвичай ілюструється простою схемою:

*   **Активні дієприкметники**: Ознака за дією, яку предмет виконує **сам**. (Джерело: Заболотний 7, chunk `s0092`).
    *   *Приклад:* `пожовтіле листя` (листя *само* пожовтіло), `сяючі зорі` (зорі *самі* сяють).
*   **Пасивні дієприкметники**: Ознака за дією, яку **хтось** виконує над предметом.
    *   *Приклад:* `написаний твір` (його *хтось* написав), `розбитий ящик` (його *хтось* розбив).

Вивчення активних дієприкметників починається в 7 класі, але набагато глибше й з погляду стилістичної норми розглядається в 10-11 класах. Основний акцент робиться на тому, що активні дієприкметники теперішнього часу є **невластивими** і **маловживаними** в сучасній українській мові. Усі підручники приділяють значну увагу правилам заміни таких форм.

## Повна парадигма (Full Paradigm)

Активні дієприкметники поділяються на дві групи за часом.

### 1. Активні дієприкметники минулого часу

Це продуктивна і стилістично нейтральна група в українській мові.

*   **Творення**: Від основи інфінітива **неперехідних** дієслів (intransitive verbs) **доконаного** виду за допомогою суфікса **-л-**.
    *   `посивіти` -> `посиві**л**ий`
    *   `потемніти` -> `потемні**л**ий`
    *   `розквітнути` -> `розквіт**л**ий`
*   **Особливість**: Якщо основа дієслова закінчується на суфікс **-ну-**, він випадає.
    *   `змерз**ну**ти` -> `змерз**л**ий` (не *змерзнулий*)
    *   `засох**ну**ти` -> `засох**л**ий` (не *засохнулий*)

### 2. Активні дієприкметники теперішнього часу

Ця група є **непродуктивною** і стилістично обмеженою. Їх вживання здебільшого вважається ознакою наукового, книжного стилю або калькуванням з російської мови.

*   **Творення**: Від основи дієслова теперішнього часу **недоконаного** виду за допомогою суфіксів:
    *   **-уч- (-юч-)** для дієслів I дієвідміни:
        *   `знають` -> `зна**юч**ий`
        *   `працюють` -> `прац**ююч**ий`
        *   `квітнуть` -> `квітн**уч**ий`
    *   **-ач- (-яч-)** для дієслів II дієвідміни:
        *   `лежать` -> `леж**ач**ий`
        *   `стоять` -> `сто**яч**ий`
        *   `тремтять` -> `тремт**яч**ий`

## Частотність і пріоритети (Frequency & Priorities)

Для рівня B1/B2 пріоритети чіткі:

1.  **Майстерне володіння активними дієприкметниками минулого часу на `-лий`**. Вони поширені, природні й необхідні для вираження послідовності дій (`опале листя`, `прибулий потяг`).

2.  **Засвоєння і автоматичне використання АЛЬТЕРНАТИВ дієприкметникам теперішнього часу**. Навчитись уникати форм на `-учий/-ачий` є важливішим, ніж навчитись їх утворювати. Найпоширеніші заміни (Джерела: Глазова 11, `s0072`; Авраменко 7, `s0106`; Заболотний 7, `s0096`):
    *   **Підрядна частина речення (конструкція "той, що..."):** Це найуніверсальніший і найправильніший спосіб.
        *   *НЕПРАВИЛЬНО:* `студент, читаючий книгу` -> *ПРАВИЛЬНО:* `студент, **що читає книгу**`
        *   *НЕПРАВИЛЬНО:* `протікаюча бочка` -> *ПРАВИЛЬНО:* `бочка, **що протікає**`
    *   **Іменник:**
        *   *НЕПРАВИЛЬНО:* `завідуючий відділом` -> *ПРАВИЛЬНО:* `**завідувач** відділу`
        *   *НЕПРАВИЛЬНО:* `початкуючий художник` -> *ПРАВИЛЬНО:* `художник-**початківець**`
    *   **Прикметник (часто з суфіксом `-альн-`):**
        *   *НЕПРАВИЛЬНО:* `знеболюючий засіб` -> *ПРАВИЛЬНО:* `знеболю**вальн**ий засіб`
        *   *НЕПРАВИЛЬНО:* `миючі засоби` -> *ПРАВИЛЬНО:* `**мийні** засоби`
    *   **Синонім:**
        *   *НЕПРАВИЛЬНО:* `хвилююча зустріч` -> *ПРАВИЛЬНО:* `**зворушлива** зустріч`
        *   *НЕПРАВИЛЬНО:* `діючий закон` -> *ПРАВИЛЬНО:* `**чинний** закон`
    *   **Інші конструкції:**
        *   *НЕПРАВИЛЬНО:* `сидячі місця` -> *ПРАВИЛЬНО:* `місця **для сидіння**`

## Типові помилки L2 (Common L2 Errors)

1.  **Надмірне вживання форм на `-учий/-ячий`**: Найпоширеніша помилка, що виникає через прямий переклад англійських "-ing" форм (a *reading* student) або під впливом російської мови. Для учнів B1/B2 це головна "погана звичка", якої треба позбутися.

2.  **Творення дієприкметників за російським зразком (суфікси `-ш-`, `-вш-`)**: Це грубе порушення норми. Форми як `попрацювавший`, `сказавший`, `прийшовший` є абсолютно неприпустимими в українській мові.
    *   *НЕПРАВИЛЬНО:* `постарівший чоловік` -> *ПРАВИЛЬНО:* `постарі**л**ий чоловік`
    *   *НЕПРАВИЛЬНО:* `людина, сказавша правду` -> *ПРАВИЛЬНО:* `людина, **що сказала** правду`

3.  **Творення дієприкметників від дієслів на `-ся`**: В українській мові такі форми не утворюються.
    *   *НЕПРАВИЛЬНО:* `хлопчик, що вмиваючийся` -> *ПРАВИЛЬНО:* `хлопчик, **що вмивається**`

## Деколонізаційні застереження (Decolonization Notes)

Тема активних дієприкметників є одним з ключових полів боротьби за чистоту української мови та її звільнення від російського впливу.

*   **Пряма калька**: Активні дієприкметники теперішнього часу на `-учий (-ючий), -ачий (-ячий)` фонетично і функціонально схожі на російські `-ущий (-ющий), -ащий (-ящий)`. У російській мові вони є нормальною, продуктивною частиною граматики. В українській мові вони історично мали обмежене вживання, але їх використання значно поширилося в радянський період через мовний контакт і пряме калькування.

*   **Стилістичний маркер**: У сучасному українському мовленні уникнення невиправданого вживання цих форм є ознакою високої мовної культури. Прагнення замінити `існуюча проблема` на `проблема, що існує` або `наявна проблема` — це свідомий вибір на користь питомо української синтаксичної моделі.

*   **Педагогічний імператив**: Навчаючи української, важливо пояснювати, що українська граматика — це самостійна система. Не можна пояснювати ці форми як "схожі на російські, але з обмеженнями". Треба наголошувати, що український синтаксис віддає перевагу підрядним реченням (`що робить`), а не дієприкметниковим зворотам там, де російська мова зробила б навпаки. Це і є навчання "мислити українською".

## Природні приклади (Natural Examples)

**Активні минулого часу (на `-лий`) - Пріоритет для вивчення**

1.  Чути шелест **опалого** вночі листя. (Джерело: Заболотний 7, `s0093`)
2.  Аж до самого небосхилу розляглось **потемніле** від хмар поле.
3.  З-за хмар виглянуло **помарніле** осіннє сонце.
4.  **Усохлий** дуб, насупившись рогато, червоний обрій настромив на ріг. (Джерело: Глазова 11, `s0076`)
5.  На землі лежали **почорнілі** від дощу гілки.
6.  Його **посивіле** волосся розвівав вітер.
7.  Через усю кімнату простягнувся **пожовклий** сонячний промінь.
8.  На столі лежав **застиглий** шматок воску.
9.  Ми побачили **змерзлого** горобця, що сидів на гілці.
10. Я люблю дивитися на **потемніле** перед грозою небо.

**Стилістично виправдане або "застигле" вживання активних теперішнього часу**

1.  Під **лежачий** камінь вода не тече. (прислів'я, дієприкметник перейшов у прикметник)
2.  Здалеку долітають **завмираючі** гуки музики. (художній стиль)
3.  Вірю в Слово. Велике, **палаюче**, наче сонце! (поетичний, високий стиль)
4.  Скільки ласки й привабливих мрій у цій милій **чаруючій** мові! (художній стиль)
5.  Це був **зворушливий** (не *хвилюючий*) момент прощання.

## Зв'язки з іншими темами

*   **Passive Participles**: Активні та пасивні дієприкметники завжди вивчаються в парі для контрасту.
*   **Adjectives**: Активні дієприкметники відмінюються точно так само, як прикметники твердої групи, і виконують у реченні ту ж синтаксичну роль (означення).
*   **Complex Sentences (Складнопідрядні речення)**: Уміння будувати речення з підрядною означальною частиною (`..., що ...`) є необхідною передумовою для правильної заміни небажаних активних дієприкметників.
*   **Verbal Aspect (Вид дієслова)**: Творення дієприкметників чітко прив'язане до виду: минулого часу — переважно від доконаного, теперішнього — від недоконаного.

## Пов'язані статті

*   `grammar/b1/passive-participles-formation`
*   `grammar/a2/adjective-declension`
*   `syntax/b1/relative-clauses-що-який`
*   `verbs/b1/perfective-imperfective-aspect-review`
```


────────────────────────────────────────
✅ Gemini finished (10227 chars)
✅ Message sent to Claude (ID: 28298)
✓ Message 28298 acknowledged
   Auto-acknowledged reply #28298 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-b1-active-participles-phrases-r2' — skipping GH posting (review saved to orchestration/)
✓ Message 28297 acknowledged
