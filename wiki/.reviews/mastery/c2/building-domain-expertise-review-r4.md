✅ Message sent to Gemini (ID: 28319) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28319...
📨 Message #28319
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-c2-building-domain-expertise-r4
   Time: 2026-04-06T08:58:07.328888+00:00

============================================================

You are a HARSH adversarial reviewer of a academic brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: c2, Slug: building-domain-expertise, Round: 4

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

# Майстерність C2: Побудова галузевої експертизи

<!-- wiki-meta
slug: building-domain-expertise
domain: mastery/c2
tracks: [c2]
sources: [11-klas-ukrajinska-mova-voron-2019_s0369, 10-klas-ukrmova-glazova-2018_s0062, 10-klas-ukrmova-glazova-2018_s0089, 11-klas-ukrmova-zabolotnyi-2019_s0314, 11-klas-ukrmova-zabolotnyi-2019_s0321, 4-klas-ukrmova-zaharijchuk_s0152, 5-klas-ukrmova-zabolotnyi-2023_s0225, 8-klas-ukrlit-zabolotnyi-2025_s0017, 10-klas-ukrajinska-mova-zabolotnij-2018_s0232, 10-klas-ukrmova-karaman-2018_s0001, 10-klas-ukrmova-zabolotnyi-2018_s0232, 2-klas-ukrmova-bolshakova-2019-2_s0022, 4-klas-ukrmova-zaharijchuk_s0100, 4-klas-ukrmova-zaharijchuk_s0104, 4-klas-ukrmova-zaharijchuk_s0122, 4-klas-ukrmova-zaharijchuk_s0173, 5-klas-ukrlit-avramenko-2022_s0090, 5-klas-ukrlit-avramenko-2022_s0298, 5-klas-ukrmova-avramenko-2022_s0074, 5-klas-ukrmova-golub-2022_s0131, 5-klas-ukrmova-litvinova-2022_s0011, 5-klas-ukrmova-litvinova-2022_s0012, 5-klas-ukrmova-zabolotnyi-2023_s0057, 6-klas-ukrlit-avramenko-2023_s0110, 6-klas-ukrmova-avramenko-2023_s0127, 6-klas-ukrmova-avramenko-2023_s0166, 6-klas-ukrmova-avramenko-2023_s0191, 6-klas-ukrmova-avramenko-2023_s0206, 6-klas-ukrmova-litvinova-2023_s0047, 6-klas-ukrmova-litvinova-2023_s0135, 6-klas-ukrmova-zabolotnyi-2020_s0230, 6-klas-ukrmova-zabolotnyi-2020_s0234, 6-klas-ukrmova-zabolotnyi-2020_s0239, 6-klas-ukrmova-zabolotnyi-2020_s0242, 6-klas-ukrmova-zabolotnyi-2020_s0245, 7-klas-ukrlit-avramenko-2024_s0344, 7-klas-ukrlit-zabolotnyi-2024_s0089, 7-klas-ukrlit-zabolotnyi-2024_s0219, 7-klas-ukrmova-avramenko-2024_s0015, 7-klas-ukrmova-avramenko-2024_s0043, 7-klas-ukrmova-avramenko-2024_s0091, 7-klas-ukrmova-avramenko-2024_s0102, 7-klas-ukrmova-avramenko-2024_s0103, 7-клас-ukrmova-avramenko-2024_s0132, 7-клас-ukrmova-avramenko-2024_s0181]
compiled: 2026-04-06
-->

## Академічний контекст (Academic Context)
На рівні C2 володіння мовою виходить за межі загальної компетенції та переходить у площину **галузевої експертизи**. В українській академічній традиції це означає свідоме опанування **функціональних різновидів** літературної мови, зокрема наукового, офіційно-ділового та публіцистичного стилів. Центральним поняттям є **"мова професійного спілкування"**, яка визначається як "функціональний різновид української літературної мови, яким послуговуються представники певної галузі виробництва, професі

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

# Майстерність C2: Побудова галузевої експертизи

<!-- wiki-meta
slug: building-domain-expertise
domain: mastery/c2
tracks: [c2]
sources: [11-klas-ukrajinska-mova-voron-2019_s0369, 10-klas-ukrmova-glazova-2018_s0062, 10-klas-ukrmova-glazova-2018_s0089, 11-klas-ukrmova-zabolotnyi-2019_s0314, 11-klas-ukrmova-zabolotnyi-2019_s0321, 4-klas-ukrmova-zaharijchuk_s0152, 5-klas-ukrmova-zabolotnyi-2023_s0225, 8-klas-ukrlit-zabolotnyi-2025_s0017, 10-klas-ukrajinska-mova-zabolotnij-2018_s0232, 10-klas-ukrmova-karaman-2018_s0001, 10-klas-ukrmova-zabolotnyi-2018_s0232, 2-klas-ukrmova-bolshakova-2019-2_s0022, 4-klas-ukrmova-zaharijchuk_s0100, 4-klas-ukrmova-zaharijchuk_s0104, 4-klas-ukrmova-zaharijchuk_s0122, 4-klas-ukrmova-zaharijchuk_s0173, 5-klas-ukrlit-avramenko-2022_s0090, 5-klas-ukrlit-avramenko-2022_s0298, 5-klas-ukrmova-avramenko-2022_s0074, 5-klas-ukrmova-golub-2022_s0131, 5-klas-ukrmova-litvinova-2022_s0011, 5-klas-ukrmova-litvinova-2022_s0012, 5-klas-ukrmova-zabolotnyi-2023_s0057, 6-klas-ukrlit-avramenko-2023_s0110, 6-klas-ukrmova-avramenko-2023_s0127, 6-klas-ukrmova-avramenko-2023_s0166, 6-klas-ukrmova-avramenko-2023_s0191, 6-klas-ukrmova-avramenko-2023_s0206, 6-klas-ukrmova-litvinova-2023_s0047, 6-klas-ukrmova-litvinova-2023_s0135, 6-klas-ukrmova-zabolotnyi-2020_s0230, 6-klas-ukrmova-zabolotnyi-2020_s0234, 6-klas-ukrmova-zabolotnyi-2020_s0239, 6-klas-ukrmova-zabolotnyi-2020_s0242, 6-klas-ukrmova-zabolotnyi-2020_s0245, 7-klas-ukrlit-avramenko-2024_s0344, 7-klas-ukrlit-zabolotnyi-2024_s0089, 7-klas-ukrlit-zabolotnyi-2024_s0219, 7-klas-ukrmova-avramenko-2024_s0015, 7-klas-ukrmova-avramenko-2024_s0043, 7-klas-ukrmova-avramenko-2024_s0091, 7-klas-ukrmova-avramenko-2024_s0102, 7-klas-ukrmova-avramenko-2024_s0103, 7-клас-ukrmova-avramenko-2024_s0132, 7-клас-ukrmova-avramenko-2024_s0181]
compiled: 2026-04-06
-->

## Академічний контекст (Academic Context)
На рівні C2 володіння мовою виходить за межі загальної компетенції та переходить у площину **галузевої експертизи**. В українській академічній традиції це означає свідоме опанування **функціональних різновидів** літературної мови, зокрема наукового, офіційно-ділового та публіцистичного стилів. Центральним поняттям є **"мова професійного спілкування"**, яка визначається як "функціональний різновид української літературної мови, яким послуговуються представники певної галузі виробництва, професії, роду діяльності" (Джерело: `11-klas-ukrajinska-mova-voron-2019_s0369`).

Метою є не просто знання, а досягнення "лінгвістичної ерудиції, мовного чуття, стилістичної вправності" (Джерело: `10-klas-ukrmova-karaman-2018_s0001`). Цей рівень майстерності передбачає здатність не лише споживати, а й створювати складні, структуровані, аргументовані тексти в обраній галузі, що є предметом вивчення на старших курсах філологічних факультетів українських університетів у межах дисциплін "Стилістика української мови", "Практична риторика", "Теорія і практика перекладу".

## Основний зміст (Main Content)
Побудова галузевої експертизи ґрунтується на кількох ключових компетенціях, які дозволяють створювати тексти, що відповідають високим академічним та професійним стандартам.

### 1. Структурна організація фахових текстів
Основою будь-якого фахового тексту є його чітка та логічна структура. Українська шкільна та академічна традиція виділяє три базові типи мовлення, комбінація яких утворює складніші жанри (Джерело: `5-klas-ukrmova-zabolotnyi-2023_s0225`, `6-klas-ukrmova-zabolotnyi-2020_s0230`).

| Тип мовлення | Загальне питання | Структурні компоненти | Джерело |
| :--- | :--- | :--- | :--- |
| **Розповідь** | Що сталося? | Початок дії → Розвиток дії → Кінець дії | `5-klas-ukrmova-zabolotnyi-2023_s0225` |
| **Опис** | Який? | Назва об'єкта → Головні ознаки → Власне враження | `5-klas-ukrmova-zabolotnyi-2023_s0225` |
| **Роздум** | Чому? | **Теза** (основне твердження) → **Докази** (аргументи) → **Висновок** | `5-klas-ukrmova-zabolotnyi-2023_s0225` |

Для створення складних текстів (наукових статей, аналітичних звітів) ключовим є вміння розробляти **складний план**, де мікротеми об'єднуються в пункти, що деталізуються підпунктами (Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0239`, `7-klas-ukrmova-avramenko-2024_s0043`). Це дозволяє систематизувати матеріал та узагальнити основні положення перед написанням тексту (Джерело: `11-klas-ukrmova-zabolotnyi-2019_s0314`).

### 2. Майстерність аргументації (Роздум)
Центральним елементом експертного мовлення є **роздум** — висловлення, де доводиться правильність чи неправильність твердження за допомогою аргументів (Джерело: `5-klas-ukrmova-zabolotnyi-2023_s0225`). Його структура є канонічною:

1.  **Теза**: формулювання основної думки.
    *   *Мовні засоби*: `Я думаю, що…`, `На мою думку…`, `Я впевнений, що…`, `Як на мене, то…` (Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0242`).
2.  **Докази (Аргументи)**: обґрунтування тези.
    *   *Мовні засоби*: `Насамперед…`, `Це пояснюється тим, що…`, `Доказом може бути…`, `По-перше…`, `По-друге…`, `Крім того…` (Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0242`).
3.  **Висновок**: підсумок міркувань.
    *   *Мовні засоби*: `Отже…`, `Ось чому…`, `Можна зробити висновок…`, `Ми переконалися в тому, що…` (Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0242`).

❌ **Помилково**: *Треба займатися спортом, бо це добре. Тому займайтеся спортом.*
✅ **Правильно**:
*   **Теза**: *Я вважаю, що всі повинні знаходити час для фізкультури.*
*   **Доказ**: *Насамперед фізичні вправи допомагають зміцнювати здоров’я, підтримувати гарну фізичну форму, загартовувати силу волі. Навіть проста ранкова гімнастика... заряджає енергією на весь день.*
*   **Висновок**: *Отже, можна зробити висновок, що заняття фізкультурою є невід’ємною частиною здорового способу життя.* (на основі Джерела: `6-klas-ukrmova-zabolotnyi-2020_s0242`)

### 3. Риторична компетенція та культура дискурсу
Галузева експертиза проявляється не лише в письмових текстах, а й в усному фаховому спілкуванні. **Майстерність промови** полягає у "високій культурі, аргументованості й переконливості, художній вираженості, стилістичній точності" (Джерело: `10-klas-ukrmova-glazova-2018_s0062`).

Важливою складовою є вміння вести конструктивну суперечку. Розрізняють такі її різновиди:
*   **Дискусія**: публічна суперечка з метою спільного пошуку істини та порівняння різних точок зору (Джерело: `10-klas-ukrajinska-mova-zabolotnij-2018_s0232`).
*   **Полеміка**: суперечка, де є конфронтація та протиставлення поглядів.
*   **Диспут (дебати)**: наукова або публічна суперечка заздалегідь визначеною темою.

Ключовим принципом є **толерантність** — повага до чужої думки, навіть при повній незгоді з нею (Джерело: `10-klas-ukrmova-zabolotnyi-2018_s0232`). Ефективне слухання, що включає аналіз, оцінювання та виявлення неточностей у мовленні опонента, є не менш важливим, ніж власне висловлювання (Джерело: `10-klas-ukrmova-glazova-2018_s0089`).

### 4. Інтерпретація та представлення даних
Сучасна експертиза неможлива без уміння працювати з нелінійними джерелами інформації, зокрема з графічними даними. Це включає здатність аналізувати діаграми, графіки, таблиці та представляти отримані дані у вигляді зв'язного, аргументованого тексту. При цьому в основній частині висловлення необхідно подавати конкретні факти: кількісні показники, співвідношення та порівняння (Джерело: `7-klas-ukrmova-avramenko-2024_s0102`, `7-klas-ukrmova-avramenko-2024_s0103`). Наприклад, аналізуючи діаграму про вплив чинників на здоров'я, експерт має не просто перелічити їх, а інтерпретувати, наприклад: "Як свідчать дані, спосіб життя людини є визначальним чинником, що на 50% впливає на її здоров'я, що значно переважає вплив екології та системи охорони здоров'я разом узятих" (на основі Джерела: `7-klas-ukrmova-avramenko-2024_s0103`).

## Типові помилки L2 (Common L2 Errors)
На рівні C2 помилки стають більш тонкими, часто стосуючись стилістики, реєстру та синтаксису, а не базової граматики.

| ❌ Помилково (часто під впливом англійської/російської) | ✅ Правильно (відповідає нормам українського наукового стилю) | Пояснення |
| :--- | :--- | :--- |
| *Проблема **розглядається** в цьому розділі.* | *У цьому розділі **розглянуто** проблему.* АБО *Автор **розглядає** проблему в цьому розділі.* | Українському науковому та офіційно-діловому стилям властиві безособові конструкції на **-но, -то**, які є більш ідіоматичними, ніж пасивні дієслова на -ся, часто вживані під впливом російської мови. |
| *Я **рахую**, що ця гіпотеза є вірною.* | *Я **вважаю**, що ця гіпотеза є слушною (правильною).* | Лексична помилка. `Рахувати` — про числа. `Вважати` — висловлювати думку. `Вірний` — той, хто не зраджує; про гіпотезу — `слушна`, `правильна`. |
| *Головна ціль цієї роботи — **проаналізувати** дані. **Аналіз** показав...* | *Метою цієї роботи є **аналіз** даних. Результати **аналізу** показали...* | Калькування англійської інфінітивної конструкції "The goal is to analyze...". В українському науковому стилі перевага надається іменниковим конструкціям ("метою є аналіз"). |
| *Згідно статті, результати є значними.* | ***Згідно зі статтею**, результати є значними.* АБО ***Відповідно до статті**, результати є значними.* | Прийменник `згідно` вимагає форми орудного відмінка з прийменником `з` (`зі`), а `відповідно до` — родового відмінка. |
| *По-перше, економічна ситуація. По-друге, політичні чинники.* | ***По-перше**, слід врахувати економічну ситуацію. **По-друге**, важливу роль відіграють політичні чинники.* | Надмірна номіналізація та телеграфний стиль. Науковий виклад вимагає повноцінних речень, а не лише номінативних конструкцій, що вводяться вставними словами. |

## Деколонізаційні застереження (Decolonization Notes)
Питання стилістики та синтаксису є ключовими на полі деколонізації української мови, оскільки саме тут вплив русифікації був найглибшим.

1.  **Безособові конструкції на `-но`, `-то`**: Це одна з найяскравіших рис українського синтаксису, що відрізняє його від російського. Активне використання конструкцій типу `досліджено`, `проаналізовано`, `встановлено` замість російських кальок з пасивними дієсловами на `-ся` (`исследуется`, `анализируется`) є маркером високої мовної культури та свідомого дотримання національних норм. Хоча українська мова має безособові форми, вона уникає зворотних дієслів у пасивному значенні (типу "досліджується", "виконується"), віддаючи перевагу або активним конструкціям із чітким суб'єктом ("автор досліджує"), або питомим безособовим формам на -но, -то ("досліджено").

2.  **Активні та пасивні дієприкметники**: Українська мова, на відміну від російської, уникає активних дієприкметників теперішнього часу на `-учий`, `-ачий` (`працюючий`, `бажаючий`). Їхнє вживання в науковому стилі є грубою помилкою.
    *   ❌ `діючий закон` → ✅ `чинний закон`
    *   ❌ `керуючий комітетом` → ✅ `керівник комітету`
    *   ❌ `виступаючий доповідач` → ✅ `доповідач`

3.  **Термінологія**: Слід надавати перевагу автентичній українській термінології або усталеним інтернаціоналізмам, уникаючи прямих запозичень з російської, які не встигли адаптуватися.
    *   ❌ `співставляти` → ✅ `зіставляти`, `порівнювати`
    *   ❌ `учбовий процес` → ✅ `навчальний процес`
    *   ❌ `заключати договір` → ✅ `укладати договір`

4.  **Стилістична традиція**: Український науковий стиль історично тяжіє до більшої ясності та прямоти, на відміну від подекуди ускладненого, "канцелярського" стилю, що сформувався в російській та радянській наукових школах. Орієнтиром має бути мова українських науковців початку XX століття та сучасні фахові видання, що дотримуються високих стандартів мовної редактури.

## Наукові дискусії (Scholarly Debates)
Хоча шкільні підручники репрезентують кодифіковану норму, у сучасному академічному дискурсі тривають жваві дебати щодо меж пуризму у фаховій мові. Зокрема, обговорюється доцільність транслітерації англомовної термінології (в ІТ, бізнесі, медицині) на противагу творенню питомих українських відповідників. Також дискусійним залишається питання абсолютної заборони на використання пасивних конструкцій на *-ся* в текстах точних наук, де автори часто вважають їх зручнішими за форми на *-но, -то*.

## Рекомендації для розробників модулів (Actionable Guidance for Writers)
Для ефективного формування галузевої експертизи на рівні C2 розробникам модулів слід впроваджувати такі підходи:

1. **

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18319 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a academic brief for the Ukrainian language curriculum ...
Dimension scores:
1. Factual: 10/10 — The article accurately cites Ukrainian academic traditions and 5th-11th grade textbooks regarding text types (розповідь, опис, роздум), argumentation structure (теза, докази, висновок), and discourse forms (дискусія, полеміка, диспут).
2. Language: 6/10 — Found several Russian calques and improper word choices that violate C2 standards: "компетенція" instead of "компетентність" (when referring to skill/ability), "точок зору" instead of "поглядів" (calque of "точка зрения"), "при повній незгоді" instead of "за повної незгоди", "невід’ємною" instead of "невіддільною" (calque of "неотъемлемый"), "представлення" instead of "подання" (calque of "представление"). 
3. Decolonization: 9/10 — The specific section on decolonization is strong and accurately pinpoints syntactic differences (avoiding passive *-ся*, avoiding active participles on *-учий/ачий*), though the author's own use of calques in previous sections slightly betrays the premise.
4. Completeness: 4/10 — The file is literally truncated at the very end (`1. **`), cutting off the entire Actionable Guidance section.
5. Actionable: 2/10 — Due to the truncation, there is zero actionable guidance for curriculum writers currently present in the text. 

**Overall: 6/10**

<fixes>
old: Побудова галузевої експертизи ґрунтується на кількох ключових компетенціях
new: Побудова галузевої експертизи ґрунтується на кількох ключових компетентностях
---
old: `Я впевнений, що…`, `Як на мене, то…`
new: `Я переконаний, що…`, `Як на мене, то…`
---
old: є невід’ємною частиною здорового способу життя.
new: є невіддільною частиною здорового способу життя.
---
old: ### 3. Риторична компетенція та культура дискурсу
new: ### 3. Риторична компетентність та культура дискурсу
---
old: порівняння різних точок зору
new: порівняння різних поглядів
---
old: суперечка заздалегідь визначеною темою.
new: суперечка із заздалегідь визначеної теми.
---
old: навіть при повній незгоді з нею
new: навіть за повної незгоди з нею
---
old: ### 4. Інтерпретація та представлення даних
new: ### 4. Інтерпретація та подання даних
---
old: аналізувати діаграми, графіки, таблиці та представляти отримані дані
new: аналізувати діаграми, графіки, таблиці та подавати отримані дані
---
old: тексту. При цьому в основній частині
new: тексту. Водночас в основній частині
---
old: 1. **
new: 1. **Аналіз автентичних фахових текстів**: Розпочинайте модулі з препарування реальних наукових статей, юридичних документів чи аналітичних звітів. Звертайте увагу студентів на композицію тексту та специфічні мовні маркери.
2. **Скафолдинг складної аргументації**: Надавайте здобувачам чіткі фрейми (шаблони) для побудови роздуму — від формулювання тези до добору аргументів і синтезу висновків, використовуючи питомі українські конектори (`насамперед`, `відповідно до`, `з огляду на`).
3. **Інтеграція роботи з даними**: Обов'язково включайте завдання на інтерпретацію нелінійної інформації (інфографіка, статистичні таблиці). Студенти повинні вміти вербалізувати кількісні показники та робити на їхній основі аналітичні висновки українською мовою.
4. **Моделювання дискусійних панелей**: Створюйте комунікативні ситуації (дебати, круглі столи, захист проєктів), що вимагають обстоювання власної позиції, критичного слухання опонентів та дотримання норм академічної етики й толерантності.
</fixes>


────────────────────────────────────────
✅ Gemini finished (3360 chars)
✅ Message sent to Claude (ID: 28322)
✓ Message 28322 acknowledged
   Auto-acknowledged reply #28322 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-c2-building-domain-expertise-r4' — skipping GH posting (review saved to orchestration/)
✓ Message 28319 acknowledged
