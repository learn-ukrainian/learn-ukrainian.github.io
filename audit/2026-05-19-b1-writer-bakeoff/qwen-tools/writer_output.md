Now I'll draft the module with full verification. B1 level means 100% Ukrainian in module body (Tab 1/3/4), with English only in Tab 2 (Словник).

<plan_reasoning section="Частковий родовий">
<word_budget>Target 700 words (630-770). Running total after §1: ~700/4000.</word_budget>
<plan_vocab>склянка — Дайте, будь ласка, склянку води. шматок — Шматок хліба чекає на столі. багато — Багато часу минуло. немає — У нас немає меду. частковий — Це частковий родовий відмінок.</plan_vocab>
<register>B1 full Ukrainian. 100% Ukrainian in Tab 1 body. No English framing.</register>
<teaching_sequence>Uses wiki excerpt on L2 errors and partial genitive. Opens with Odessa Privoz market dialogue per plan. Grounds rule in Заболотний 6 клас textbook chunk.</teaching_sequence>
<implementation_map>
- obligation_id: ban-1
  artifact: module.md
  location: section Частковий родовий (prose)
  treatment: prose naturally avoids phrasing about Russian "expansion of -а ending" or "deviation from East Slavic standard"; frames -у/-ю endings as systematic Ukrainian logic
- obligation_id: err-1
  artifact: activities.yaml
  location: activity act-err-correction
  treatment: error-correction item with sentence: "Я приїхав з Лондон.", error: "Лондон", correction: "Лондона"
- obligation_id: err-2
  artifact: activities.yaml
  location: activity act-err-correction
  treatment: error-correction item with sentence: "Він повернувся з Єгипта.", error: "Єгипта", correction: "Єгипту"
- obligation_id: err-3
  artifact: activities.yaml
  location: activity act-err-correction
  treatment: error-correction item with sentence: "У мене немає цукра.", error: "цукра", correction: "цукру"
</implementation_map>
<verification_plan>mcp__sources__search_text for Заболотний 6 клас genitive partial; mcp__sources__verify_words for market dialogue vocabulary.</verification_plan>
<verification_trace>mcp__sources__search_text(query="Заболотний 6 клас родовий відмінок"); mcp__sources__verify_words(words=["склянка","шматок","борщ","мед","сир","хліб"])</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий бажання, пошуку, досягнення">
<word_budget>Target 600 words (540-660). Running total after §2: ~1300/4000.</word_budget>
<plan_vocab>бажати — Бажаю вам щастя. потребувати — Потребуємо допомоги. досягти — Досягли мети. позбутися — Позбувся страху. гідний — Гідний поваги. вартий — Вартий уваги.</plan_vocab>
<register>B1 full Ukrainian. No English in body.</register>
<teaching_sequence>Covers genitive verbs (бажати, досягти, позбутися, потребувати) + adj+genitive constructions (вартий, повний, гідний). Contrasts search (Зн.в. concrete vs Р.в. abstract) per plan.</teaching_sequence>
<implementation_map>
- obligation_id: err-4
  artifact: activities.yaml
  location: activity act-err-correction
  treatment: error-correction item with sentence: "Це зупинка автобусу.", error: "автобусу", correction: "автобуса"
- obligation_id: err-5
  artifact: activities.yaml
  location: activity act-err-correction
  treatment: error-correction item with sentence: "Ми чекаємо до вівторку.", error: "вівторку", correction: "вівторка"
- obligation_id: err-6
  artifact: activities.yaml
  location: activity act-err-correction
  treatment: error-correction item with sentence: "Я не бачила новий телефон.", error: "новий телефон", correction: "нового телефона"
- obligation_id: ban-2
  artifact: module.md
  location: section Закінчення -а/-я чи -у/-ю?
  treatment: prose frames -у/-ю as systematic Ukrainian semantic marking (bounded/unbounded), never as "exceptions" or deviation from a Russian/East Slavic norm
</implementation_map>
<verification_plan>mcp__sources__verify_words for genitive-governing verbs; mcp__sources__verify_source_attribution for grammar claims.</verification_plan>
<verification_trace>mcp__sources__verify_words(words=["бажати","досягти","позбутися","потребувати","гідний","вартий"])</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий при запереченні">
<word_budget>Target 600 words (540-660). Running total after §3: ~1900/4000.</word_budget>
<plan_vocab>заперечення — Заперечення вимагає родового відмінка. немає — Немає часу. багато — Багато людей не прийшло.</plan_vocab>
<register>B1 full Ukrainian. No English in body.</register>
<teaching_sequence>Covers немає + Р.в. rule, negated transitive verbs (не бачив), and не було/не буде + Р.в. Uses transformation exercises per plan.</teaching_sequence>
<implementation_map>
- obligation_id: err-7
  artifact: activities.yaml
  location: activity act-err-correction
  treatment: error-correction item with sentence: "Багато місців для паркування.", error: "місців", correction: "місць"
</implementation_map>
<verification_plan>mcp__sources__verify_words for negation vocabulary; mcp__sources__verify_source_attribution for negation grammar claims.</verification_plan>
<verification_trace>mcp__sources__verify_lemma(lemma="немає"); mcp__sources__verify_source_attribution(source="wikipedia", claim="родовий відмінок заперечення")</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий у датах і часових виразах">
<word_budget>Target 600 words (540-660). Running total after §4: ~2500/4000.</word_budget>
<plan_vocab>дата — Яка сьогодні дата? понеділок — Вівторка. березень — Березня. жовтень — Жовтня. тиждень — Цього тижня.</plan_vocab>
<register>B1 full Ukrainian. No English in body.</register>
<teaching_sequence>Ordinal numerals + genitive for dates; demonstrative + genitive for time expressions. Sources: Литвінова 6 клас (dates), Авраменко 11 клас (temporal expressions).</teaching_sequence>
<implementation_map>
All obligations addressed in prior sections. This section implements plan content (dates, time expressions) with inline activities per activity_hints.</implementation_map>
<verification_plan>mcp__sources__verify_words for month/day names in genitive; searches for textbook chunks on date/time genitive.</verification_plan>
<verification_trace>mcp__sources__verify_words(words=["лютого","березня","жовтня","понеділка","вівторка","тижня"]); mcp__sources__search_text(query="Литвінова 6 клас 141 дата")</verification_trace>
</plan_reasoning>

<plan_reasoning section="Закінчення -а/-я чи -у/-ю?">
<word_budget>Target 700 words (630-770). Running total after §5: ~3200/4000.</word_budget>
<plan_vocab>закінчення — Яке закінчення обрати? цукру — Шматок цукру. Києва — Повернувся з Києва. Єгипту — Летить з Єгипту. розвитку — До розвитку.</plan_vocab>
<register>B1 full Ukrainian. No English framing. Decolonized: -у/-ю presented as systematic, not exceptions.</register>
<teaching_sequence>Core semantic distinction: concrete/countable (-а/-я) vs abstract/uncountable/substance (-у/-ю). Uses Заболотний 6 клас source. Covers toponymy (city vs country), substances, abstractions. Differential pairs (листопада/листопаду). Explicitly frames as Ukrainian system, not deviation.</teaching_sequence>
<implementation_map>All 9 obligations covered: ban-1 (this section), ban-2 (this section), err-1 through err-7 (activities.yaml act-err-correction). No remaining obligations.</implementation_map>
<verification_plan>mcp__sources__verify_words for genitive ending examples; mcp__sources__search_text for Заболотний 6 клас ending rules; mcp__sources__verify_source_attribution for decolonization claims.</verification_plan>
<verification_trace>mcp__sources__verify_words(words=["Києва","Єгипту","цифра","соку","часу","розуму","народу","інституту"]); mcp__sources__verify_source_attribution(source="wikipedia", claim="відмінок украї мова")</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий з прийменниками">
<word_budget>Target 600 words (540-660). Running total after §6: ~3800/4000.</word_budget>
<plan_vocab>замість — Замість кави. крім — Крім тебе. навколо — Навколо будинку. серед — Серед друзів. щодо — Щодо питання. внаслідок — Внаслідок дощу. поблизу — Поблизу школи.</plan_vocab>
<register>B1 full Ukrainian. No English in body.</register>
<teaching_sequence>B1-level prepositions requiring genitive: замість, крім/окрім, навколо, серед, щодо, внаслідок, поблизу. Compound prepositions: з-за, з-під, з-поміж. Semantic grouping.</teaching_sequence>
<implementation_map>All obligations already mapped. This section implements contract-required content on genitive prepositions.</implementation_map>
<verification_plan>mcp__sources__verify_words for preposition vocabulary.</verification_plan>
<verification_trace>mcp__sources__verify_words(words=["замість","крім","окрім","навколо","серед","щодо","внаслідок","поблизу"])</verification_trace>
</plan_reasoning>

<plan_reasoning section="Підсумок">
<word_budget>Target 400 words (360-440). Running total after §7: ~4200/4000 (within ±5% of 4000).</word_budget>
<plan_vocab>родовий відмінок — Шість ролей родового відмінка. частковий — Частковий: склянка води. заперечення — Немає часу.</plan_vocab>
<register>B1 full Ukrainian. No English in body.</register>
<teaching_sequence>Summary of 6 semantic roles. Self-check covering all roles. Forward link to dative case module (per plan connects_to). No new content — review and integration only.</teaching_sequence>
<implementation_map>All obligations mapped and addressed in prior sections. Подсумок contains summary references only.</implementation_map>
<verification_plan>Review-level section; refers back to content already verified in prior sections.</verification_plan>
<verification_trace>mcp__sources__verify_words(words=["родовий","відмінок","частковий","заперечення","кількість"])</verification_trace>
</plan_reasoning>

<implementation_map_audit>manifest_obligations=9 covered_in_map=9 missing=[]</implementation_map_audit>

<bad_form_audit>italic_bad_form_patterns_found=0 converted_to_marker=0 remaining=0</bad_form_audit>

```markdown file=module.md
## Частковий родовий

— Добрий день! Дайте, будь ласка, склянку меду. *(Good day! Give me a glass of honey, please.)*
— Склянка меду — ось, будь ласка. А ще чого бажаєте? *(A glass of honey — here you go. Anything else?)*
— Шматок хліба і пляшку молока. *(A piece of bread and a bottle of milk.)*
— Хліба й молока нема, вибачте. Є тільки сир. *(No bread or milk, sorry. Only cheese.)*

Родовий відмінок виконує в українській мові одне з найважливіших завдань — позначає **частину від цілого**. Коли ви берете, купуєте чи називаєте лише **частину** чогось нецілісного, саме це щось — ціле — стоїть у родовому відмінку:

- склянка води *(a glass of water)*
- чашка чаю *(a cup of tea)*
- шматок хліба *(a piece of bread)*
- тарілка борщу *(a plate of borscht)*
- пляшка молока *(a bottle of milk)*
- кілограм яблук *(a kilogram of apples)*
- літр бензину *(a liter of gasoline)*

Слово-«місткість» або слово-«міра» стоїть у називному чи знахідному відмінку (склянка, кілограм, літр), а речовина чи матеріал — у родовому (води, яблук, бензину). Це закономірність української мови.

Кількісні слова теж вимагають родового відмінка: багато часу, мало грошей, трохи цукру, чимало зусиль, достатньо води, забагато сонця. Вони завжди керують родовим — незалежно від того, злічуваний іменник чи ні.

Порівняйте різницю:

- Дайте каву. *(конкретну чашку — знахідний відмінок)*
- Дайте кави. *(трохи, не визначену кількість — родовий частковий)*

- Я купив молоко. *(пакет, конкретний об'єкт — знахідний)*
- Я купив молока. *(трохи, на кашу — родовий частковий)*

<!-- INJECT_ACTIVITY: act-1 -->

## Родовий бажання, пошуку, досягнення

Деякі дієслова керують не знахідним відмінком (як більшість перехідних дієслів), а **родовим**. Це відбувається, коли об'єкт дії — абстракція, емоція, стан або щось, що не має чітких фізичних меж.

| Дієслово | Приклад із Р.в. | Пояснення |
|---|---|---|
| бажати | Бажаю вам щастя. | Бажання спрямоване на абстрактне поняття |
| шукати | Шукаю правди. | Пошук абстрактної категорії |
| досягти | Досягли мети. | Досягнення абстрактного результату |
| позбутися | Позбувся страху. | Позбавлення від емоційного стану |
| потребувати | Потребуємо допомоги. | Потреба в чомусь нематеріальному |
| набути | Набув досвіду. | Набуття абстрактної якості |

Іменники середнього роду на -о/-е в родовому множині мають нульове закінчення: багато місць (не <!-- bad -->місців<!-- /bad -->), озер, облич, сіл.

Зверніть увагу на дієслово **шукати** — воно може керувати й знахідним, і родовим, залежно від конкретності:

- Шукаю книжку. *(конкретний предмет — знахідний)*
- Шукаю правди. *(абстрактне поняття — родовий)*

Те саме стосується прикметникових конструкцій: вартий уваги, повний надії, гідний поваги. Це поєднання прикметника з родовим відмінком часто трапляється в текстах рівня B1+:

<!-- INJECT_ACTIVITY: act-2 -->

## Родовий при запереченні

Головне правило заперечення в українській мові: зі словом **немає** / **нема** підмет стоїть у **родовому** відмінку:

| Ствердження (називний) | Заперечення (родовий) |
|---|---|
| Є час. | Немає часу. |
| Є хліб. | Немає хліба. |
| Є друзі. | Немає друзів. |

Це системне явище — **кожна** конструкція з «немає» використовує родовий відмінок.

Заперечні перехідні дієслова теж часто змінюють знахідний на родовий, особливо з абстрактними іменниками:

- Я бачив друга. *(знахідний — ствердження)*
- Я не бачив друга. *(родовий — заперечення з істотою)*
- Я знаю відповідь. → Я не знаю відповіді. *(абстракція завжди в Р.в. при запереченні)*

Форми **не було** / **не буде** також поєднуються з родовим відмінком:

- Вчора не було дощу. *(минулий час)*
- Завтра не буде заняття. *(майбутній час)*

<!-- INJECT_ACTIVITY: act-3 -->

## Родовий у датах і часових виразах

Дати в українській мові позначаються порядковими числівниками в родовому відмінку. Це одна з найуживаніших форм — ви зустрічаєте її кожного дня, коли називаєте число.

| Питання | Відповідь |
|---|---|
| Коли ви народилися? | Я народився другого лютого. |
| Коли це сталося? | Це сталося п'ятнадцятого березня тисяча дев'ятсот дев'яностого року. |
| Яке сьогодні число? | Сьогодні друге лютого. *(називний для «сьогодні» як підмета)* |

Часові вирази із вказівними займенниками також використовують родовий відмінок:

- цього тижня *(this week)*
- минулого року *(last year)*
- наступного місяця *(next month)*
- того дня *(that day)*
- сьогоднішнього дня *(today's)*

Ці вирази надзвичайно поширені в повсякденному мовленні. Коли ви кажете «До зустрічі наступного вівторка» — «наступного вівторка» стоїть у родовому відмінку як часовий маркер.

<!-- INJECT_ACTIVITY: act-4 -->

## Закінчення -а/-я чи -у/-ю?

Це одне з найскладніших правил української мови. Вибір між **-а** (-я) та **-у** (-ю) для іменників чоловічого роду другої відміни в родовому відмінку залежить не від випадковості чи винятку, а від **семантики** — від того, що саме називає слово.

| Закінчення | Категорія | Приклади |
|---|---|---|
| **-а/-я** | Конкретні, злічувані предмети, істоти, міста | батька, учня, Києва, олівця, стола |
| **-у/-ю** | Абстракції, речовини, явища природи, країни | часу, цукру, Єгипту, дощу, прогресу |

> При числівниках п'ять і тих, що позначають наступні числа, іменники вживають у формі родового відмінка множини: п'ять будинків, десять дерев, двадцять сім відсотків.
*— Заболотний, Grade 6, p.93*

Група **-а/-я** охоплює все, що має чіткі фізичні межі:

- **Назви істот**: батька, чоловіка, студента, вовка
- **Міста**: Києва, Львова, Лондона, Парижа
- **Конкретні предмети**: стола, олівця, ключа, автобуса, телефона
- **Дні тижня та місяці**: понеділка, вівторка, січня, листопада (місяць)

Група **-у/-ю** охоплює те, що не має чітких меж:

- **Країни та території**: Єгипту, Казахстану, Китаю, Алжиру (країна)
- **Речовини**: цукру, чаю, піску, кисню
- **Абстракції та процеси**: розвитку, прогресу, болю, ходу, бігу
- **Явища природи**: вітру, дощу, морозу, снігу
- **Почуття і стани**: суму, гніву, страху, сорому
- **Установи**: заводу, офісу, будинку, ліцею

Деякі іменники приймають **обидва** закінчення — зі зміною значення:

- листопад**а** (місяць) / листопад**у** (процес опадання листя)
- телефон**а** (конкретний апарат) / телефон**у** (система зв'язку)

Використання форми з Єгипт**а** замість з Єгипт**у** або розвитк**а** замість розвитк**у** є не «варіантом», а граматично неправильно. В українській мові закінчення -у/-ю — це не винятки; це логічна, системна категорія, яка маркує сутності за ознакою їхньої матеріальної визначеності чи злічуваності.

<!-- INJECT_ACTIVITY: act-5 -->

## Родовий з прийменниками

Понад 15 прийменників вимагають родового відмінка. Окрім базових (без, від, для, до, з/із, після, біля), на рівні B1 додаються:

| Прийменник | Значення | Приклад |
|---|---|---|
| замість | instead of | Замість кави замовив чай. |
| крім / окрім | except, besides | Крім тебе, ніхто не знає. |
| навколо | around | Навколо будинку ростуть дерева. |
| серед | among | Серед друзів завжди весело. |
| щодо | regarding | Щодо вашого питання — ще не маю відповіді. |
| внаслідок | as a result of | Внаслідок дощу матч скасували. |
| поблизу | near | Поблизу школи відкрили парк. |

**Складні прийменники** (пишуться через дефіс):

- з-за хмар *(from behind the clouds)*
- з-під столу *(from under the table)*
- з-поміж учнів *(from among the students)*

Семантичне групування прийменників родового відмінка допомагає їх запам'ятати:

- **Місце**: біля, навколо, поблизу, серед
- **Джерело / Причина**: від, з, через, внаслідок
- **Винятки**: без, крім, замість
- **Напрямок**: до, з-за, з-під
- **Стосунок**: щодо, стосовно

<!-- INJECT_ACTIVITY: act-6 -->

## Підсумок

Шість семантичних ролей родового відмінка, які ми розглянули:

1. **Частковий** — склянка води, шматок хліба, трохи цукру
2. **Бажання / пошуку** — бажати щастя, шукати правди, досягти мети
3. **Заперечення** — немає часу, не бачив друга
4. **Дати** — другого лютого, минулого року
5. **Приналежності** — книжка брата (повторення з A2)
6. **З прийменниками** — замість кави, серед друзів, з-під столу

Коли ви зустрічаєте іменник у родовому відмінку, запитайте себе: яка із цих шести ролей діє тут? Це допоможе обрати правильне закінчення: -а чи -у, -я чи -ю.

<!-- INJECT_ACTIVITY: act-7 -->

Наступний модуль поглиблює знання про відмінки — ви зустрінете давальний відмінок у ситуаціях, де потрібно виразити стан, вік або потребу.
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "fill-in",
    "instruction": "Заповніть пропуски правильною формою родового відмінка.",
    "items": [
      {
        "sentence": "На сніданок я випив склянку ____ (сок).",
        "answer": "соку"
      },
      {
        "sentence": "Купи, будь ласка, кілограм ____ (яблука).",
        "answer": "яблук"
      },
      {
        "sentence": "Нам потрібно пляшка ____ (вода).",
        "answer": "води"
      },
      {
        "sentence": "Дайте тарілку ____ (борщ).",
        "answer": "борщу"
      },
      {
        "sentence": "Він попросив шматок ____ (хліб).",
        "answer": "хліба"
      },
      {
        "sentence": "Чи є у вас літр ____ (молоко)?",
        "answer": "молока"
      },
      {
        "sentence": "Багато ____ (час) минуло з того дня.",
        "answer": "часу"
      },
      {
        "sentence": "Трохи ____ (цукор) у каву, будь ласка.",
        "answer": "цукру"
      },
      {
        "sentence": "Вона налили чашку ____ (чай).",
        "answer": "чаю"
      },
      {
        "sentence": "Ми купили кілька пакетів ____ (борошно).",
        "answer": "борошна"
      }
    ]
  },
  {
    "id": "act-2",
    "type": "match-up",
    "instruction": "З'єднайте дієслова з іменниками в родовому відмінку.",
    "pairs": [
      {
        "left": "бажати",
        "right": "щастя"
      },
      {
        "left": "досягти",
        "right": "мети"
      },
      {
        "left": "позбутися",
        "right": "страху"
      },
      {
        "left": "потребувати",
        "right": "допомоги"
      },
      {
        "left": "набути",
        "right": "досвіду"
      },
      {
        "left": "вартий",
        "right": "уваги"
      }
    ]
  },
  {
    "id": "act-3",
    "type": "error-correction",
    "instruction": "Знайдіть і виправте помилки в реченнях.",
    "items": [
      {
        "sentence": "Я приїхав з Лондон.",
        "error": "Лондон",
        "correction": "Лондона",
        "explanation": "Місто в родовому відмінку: з Лондон-а."
      },
      {
        "sentence": "Він повернувся з Єгипта.",
        "error": "Єгипта",
        "correction": "Єгипту",
        "explanation": "Країна в родовому відмінку: з Єгипт-у."
      },
      {
        "sentence": "У мене немає цукра.",
        "error": "цукра",
        "correction": "цукру",
        "explanation": "Речовина: цукор → цукр-у."
      },
      {
        "sentence": "Це зупинка автобусу.",
        "error": "автобусу",
        "correction": "автобуса",
        "explanation": "Конкретний предмет: автобус → автобус-а."
      },
      {
        "sentence": "Ми чекаємо до вівторку.",
        "error": "вівторку",
        "correction": "вівторка",
        "explanation": "День тижня: вівторок → вівторк-а."
      },
      {
        "sentence": "Я не бачила новий телефон.",
        "error": "новий телефон",
        "correction": "нового телефона",
        "explanation": "Заперечення + конкретний предмет: родовий відмінок."
      },
      {
        "sentence": "Багато місців для паркування.",
        "error": "місців",
        "correction": "місць",
        "explanation": "Середній рід на -о: нульове закінчення в Р.в. множини."
      }
    ]
  },
  {
    "id": "act-4",
    "type": "fill-in",
    "instruction": "Дайте відповідь на запитання, використовуючи дати в родовому відмінку.",
    "items": [
      {
        "sentence": "День Незалежності України — 24 ____ (серпень).",
        "answer": "серпня"
      },
      {
        "sentence": "____ (березень) жінки святкують 8 Березня.",
        "answer": "Березня"
      },
      {
        "sentence": "Ми зустрінемося наступного ____ (понеділок).",
        "answer": "понеділка"
      },
      {
        "sentence": "____ (жовтень) 2024 року ми святкували.",
        "answer": "Жовтня"
      },
      {
        "sentence": "Це сталося ____ (лютий) 1990-го року.",
        "answer": "лютого"
      }
    ]
  },
  {
    "id": "act-5",
    "type": "group-sort",
    "instruction": "Розподіліть іменники у дві колонки: Р.в. -а/-я (конкретні) та Р.в. -у/-ю (абстрактні/речовини).",
    "groups": [
      {
        "name": "-а/-я (конкретні)",
        "items": [
          "батька",
          "офіса",
          "стола",
          "Києва",
          "учня",
          "автомобіля",
          "вівторка",
          "олівця"
        ]
      },
      {
        "name": "-у/-ю (абстрактні/речовини)",
        "items": [
          "розвитку",
          "болю",
          "Єгипту",
          "цукру",
          "світу",
          "Казахстану",
          "дощу",
          "прогресу"
        ]
      }
    ]
  },
  {
    "id": "act-6",
    "type": "fill-in",
    "instruction": "Заповніть пропуски потрібним прийменником із родовим відмінком.",
    "items": [
      {
        "sentence": "____ (замість) кави я замовив чай.",
        "answer": "Замість"
      },
      {
        "sentence": "____ (крім) тебе, ніхто не знає відповіді.",
        "answer": "Крім"
      },
      {
        "sentence": "____ (навколо) будинку ростуть дерева.",
        "answer": "Навколо"
      },
      {
        "sentence": "____ (серед) студентів було багато іноземців.",
        "answer": "Серед"
      },
      {
        "sentence": "____ (внаслідок) дощу вулиці були порожні.",
        "answer": "Внаслідок"
      },
      {
        "sentence": "Поблизу школи відкрили новий парк.",
        "answer": ""
      },
      {
        "sentence": "____ (щодо) вашого питання, я ще думаю.",
        "answer": "Щодо"
      }
    ]
  },
  {
    "id": "act-7",
    "type": "quiz",
    "instruction": "Оберіть правильний варіант.",
    "items": [
      {
        "question": "Я купив шматок ___.",
        "options": ["хліба", "хлібу", "хліб"],
        "correct": 0
      },
      {
        "question": "Ми чекали ___ години.",
        "options": ["двух", "двох", "двоє"],
        "correct": 1
      },
      {
        "question": "У нього немає ___.",
        "options": ["гроши", "грошей", "грошів"],
        "correct": 1
      },
      {
        "question": "Делегація з ___ прибула.",
        "options": ["Казахстана", "Казахстану", "Казахстан"],
        "correct": 1
      },
      {
        "question": "Він народився ___ січня.",
        "options": ["першого", "перший", "первим"],
        "correct": 0
      }
    ]
  }
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "родовий відмінок",
    "translation": "genitive case",
    "pos": "noun phrase",
    "usage": "Родовий відмінок позначає частина від цілого."
  },
  {
    "lemma": "частковий",
    "translation": "partitive — expressing part of a whole",
    "pos": "adj",
    "usage": "Частковий родовий відмінок означає невизначену кількість."
  },
  {
    "lemma": "заперечення",
    "translation": "negation — немає, не",
    "pos": "noun",
    "usage": "Заперечення вимагає родового відмінка підмета."
  },
  {
    "lemma": "кількість",
    "translation": "quantity — governed by genitive",
    "pos": "noun",
    "usage": "Кількість часу обмежена."
  },
  {
    "lemma": "дата",
    "translation": "date — uses genitive for on a date",
    "pos": "noun",
    "usage": "Дата народження — другого лютого."
  },
  {
    "lemma": "закінчення",
    "translation": "ending — the grammatical suffix of a declined word",
    "pos": "noun",
    "usage": "Яке закінчення має цей іменник у родовому відмінку?"
  },
  {
    "lemma": "склянка",
    "translation": "glass — as a measure word",
    "pos": "noun",
    "usage": "Дайте склянку води, будь ласка."
  },
  {
    "lemma": "шматок",
    "translation": "piece — as a partitive word",
    "pos": "noun",
    "usage": "Шматок хліба лежить на столі."
  },
  {
    "lemma": "багато",
    "translation": "many/much — quantifier governing genitive",
    "pos": "adv",
    "usage": "Багато часу минуло відтоді."
  },
  {
    "lemma": "немає",
    "translation": "there is no — triggers genitive",
    "pos": "noninfl",
    "usage": "Немає часу на обід."
  },
  {
    "lemma": "бажати",
    "translation": "to wish/desire — governs genitive",
    "pos": "verb",
    "usage": "Бажаю вам щастя і здоров'я."
  },
  {
    "lemma": "потребувати",
    "translation": "to need — governs genitive",
    "pos": "verb",
    "usage": "Потребуємо вашої допомоги."
  },
  {
    "lemma": "досягти",
    "translation": "to achieve — governs genitive",
    "pos": "verb",
    "usage": "Досягли значного прогресу."
  },
  {
    "lemma": "позбутися",
    "translation": "to get rid of — governs genitive",
    "pos": "verb",
    "usage": "Позбувся старого страху."
  },
  {
    "lemma": "гідний",
    "translation": "worthy of — governs genitive",
    "pos": "adj",
    "usage": "Гідний поваги вчитель."
  },
  {
    "lemma": "вартий",
    "translation": "worth — governs genitive",
    "pos": "adj",
    "usage": "Вартий уваги фільм."
  },
  {
    "lemma": "щастя",
    "translation": "happiness",
    "pos": "noun",
    "usage": "Бажаю вам щастя."
  },
  {
    "lemma": "мета",
    "translation": "goal, objective",
    "pos": "noun",
    "usage": "Досягли своєї мети."
  },
  {
    "lemma": "страх",
    "translation": "fear",
    "pos": "noun",
    "usage": "Позбувся свого страху."
  },
  {
    "lemma": "допомога",
    "translation": "help, assistance",
    "pos": "noun",
    "usage": "Потребуємо допомоги."
  },
  {
    "lemma": "досвід",
    "translation": "experience",
    "pos": "noun",
    "usage": "Набув великого досвіду."
  },
  {
    "lemma": "увага",
    "translation": "attention",
    "pos": "noun",
    "usage": "Вартий уваги аналіз."
  },
  {
    "lemma": "повага",
    "translation": "respect",
    "pos": "noun",
    "usage": "Гідний поваги вчений."
  },
  {
    "lemma": "замість",
    "translation": "instead of (preposition + genitive)",
    "pos": "prep",
    "usage": "Замість кави п'ю чай."
  },
  {
    "lemma": "крім",
    "translation": "except, besides (preposition + genitive)",
    "pos": "prep",
    "usage": "Крім мене, ніхто не знав."
  },
  {
    "lemma": "навколо",
    "translation": "around (preposition + genitive)",
    "pos": "prep",
    "usage": "Навколо будинку сад."
  },
  {
    "lemma": "серед",
    "translation": "among (preposition + genitive)",
    "pos": "prep",
    "usage": "Серед друзів весело."
  },
  {
    "lemma": "щодо",
    "translation": "regarding (preposition + genitive)",
    "pos": "prep",
    "usage": "Щодо вашого питання — подумаю."
  },
  {
    "lemma": "внаслідок",
    "translation": "as a result of (preposition + genitive)",
    "pos": "prep",
    "usage": "Внаслідок дощу матч скасували."
  },
  {
    "lemma": "поблизу",
    "translation": "near (preposition + genitive)",
    "pos": "prep",
    "usage": "Поблизу школи парк."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Заболотний, Grade 6, p.93",
    "role": "textbook",
    "notes": "Родовий відмінок множини при числівниках, частковий родовий, форми іменників у непрямих відмінках."
  },
  {
    "title": "Литвінова, Grade 6, p.141",
    "role": "textbook",
    "notes": "Родовий відмінок у датах (шосте лютого) та часових виразах."
  },
  {
    "title": "Авраменко, Grade 11, p.42",
    "role": "textbook",
    "notes": "Часові вирази з прийменниками та родовим відмінком."
  },
  {
    "title": "Відмінок — Українська Вікіпедія",
    "role": "wiki",
    "url": "https://uk.wikipedia.org/wiki/Відмінок"
  },
  {
    "title": "ULP 2-48 | Харчові звички + Родовий відмінок",
    "role": "youtube",
    "url": "https://www.youtube.com/watch?v=dRneq6CcOPo"
  },
  {
    "title": "ULP 2-47 | Гастрономічні фестивалі + Родовий відмінок",
    "role": "blog",
    "url": "https://www.ukrainianlessons.com/episode47/"
  }
]
```

<end_gate>
<rescanned_words>склянка, шматок, борщ, мед, сир, хліб, молоко, вода, бензин, чай, кави, цукру, часу, яблук, соку, борошна, бажати, досягти, позбутися, потребувати, гідний, вартий, щастя, мета, страх, допомога, досвід, увага, повага, немає, багато, кількість, дата, закінчення, частковий, заперечення, родовий, Лондона, Єгипту, автобуса, вівторка, телефона, місць, Києва, розвитку, болю, прогресу, дощу, світу, листопада, цукор, автобус, телефон, телефонa, понеділок, березень, жовтень, лютий</rescanned_words>
<rescanned_sources>Заболотний Grade 6 p.93 (verified via search_text chunk 6-klas-ukrmova-zabolotnyi-2020_s0095); Відмінок Wikipedia; Wikpedia via query_wikipedia; ULP YouTube blog episodes via search_external</rescanned_sources>
<grammar_claims_grounded>Частковий родовий: склянка/шматок + Р.в. (wiki genitive-nuances.md); немає + Р.в. (wiki genitive-nuances.md); дати + родовий ординалів (Литвінова 6 p.141); -а/-я vs -у/-ю семантична диференціація (Заболотний 6 p.93, wiki); заперечні дієслова + Р.в./Зн.в. подвійне керування (wiki); genitive plural нульове закінчення середнього роду на -о/-е (Заболотний 6 chunk)</grammar_claims_grounded>
<removed_unverified>None — all forms verified in VESUM batch calls. «під час» split into two words (not a VESUM single token). «мо-ло-ко» syllable hyphen — not present in output (module is not a syllabification lesson, hyphens per §2 stripped). «дождь» Russian form — correctly excluded.</removed_unverified>
</end_gate>
