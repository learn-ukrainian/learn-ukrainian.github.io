<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/participles-passive.yaml` file for module **66: Пасивні дієприкметники** (b1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: reading -->`
- `<!-- INJECT_ACTIVITY: essay-response -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Прочитайте текст про пасивні дієприкметники: значення і дайте відповіді
    на запитання.'
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «Творення пасивних
    дієприкметників».
  type: essay-response
- focus: 'Вставте правильну граматичну форму у реченнях на тему пасивні дієприкметники:
    значення.'
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему творення пасивних дієприкметників.
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Пасивні дієприкметники:
    значення».'
  type: quiz
- focus: З'єднайте терміни з розділу «Творення пасивних дієприкметників» з їхніми
    визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- побачений (seen — passive participle from побачити)
- загоєний (healed — passive participle from загоїти)
- заметений (swept — passive participle from замести)
- пофарбований (painted — passive participle from пофарбувати)
- воджений (driven — with [д]→[дж] alternation)
- битий (beaten — -т- suffix from бити)
- митий (washed — -т- suffix from мити)
- колотий (chopped — -т- suffix from колоти)
- зварений (boiled/cooked — perfective participle)
- варений (cooked — lexicalized adjective from варити)
required:
- пасивний дієприкметник (passive participle — subject receives the action)
- прочитаний (read — passive participle from прочитати)
- збудований (built — passive participle from збудувати)
- написаний (written — passive participle from написати)
- вишитий (embroidered — passive participle from вишити)
- зроблений (made/done — passive participle from зробити)
- принесений (brought — passive participle from принести)
- відкритий (opened — passive participle from відкрити)
- ношений (worn/carried — with [с]→[ш] alternation)
- закручений (twisted — with [т]→[ч] alternation)
- чергування (alternation — consonant changes in formation)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пасивні дієприкметники: значення

Уявіть ситуацію: ви заходите до кімнати і бачите книгу, яку хтось залишив на столі. Ця книга не читає сама себе, але вона має ознаку — результат чиєїсь дії. В українській мові ми називаємо таку ознаку пасивним дієприкметником. Як зазначається у шкільних підручниках (наприклад, О. Литвінової), пасивні дієприкметники виражають ознаку предмета за дією, якої він зазнає від іншого виконавця. Предмет тут не є активним учасником процесу, дія просто спрямована на нього. Коли ми кажемо «прочитана книга», ми розуміємо, що цю книгу хтось прочитав. Коли ми бачимо «збудований міст», ми знаємо, що міст хтось збудував. У цих прикладах підмет отримує дію, а не виконує її самостійно.

> *Imagine a situation: you enter a room and see a book someone left on the table. This book does not read itself, but it has an attribute — the result of someone's action. In Ukrainian, we call such an attribute a passive participle. Passive participles express the attribute of an object based on the action it receives from another performer. The object here is not an active participant in the process; it only receives the action. When we say «прочитана книга» (read book), we understand that someone read this book. When we see «збудований міст» (built bridge), we know someone built the bridge. In these examples, the subject receives the action rather than performing it independently.*

Щоб краще зрозуміти природу пасивних дієприкметників, варто згадати їхніх активних «родичів» з попередніх модулів. Активний дієприкметник описує предмет, який сам виконує дію. Наприклад, «квітучий сад» означає, що сад сам квітне. Це його власна, активна ознака. Натомість «посаджений сад» означає, що сад посадив хтось інший. В українській мові саме пасивні дієприкметники є набагато природнішими, стилістично нейтральними та продуктивними. Вони звучать гармонійно у будь-якому тексті, від щоденної розмови до офіційних документів, тоді як активні форми часто замінюють описовими конструкціями.

:::info
**Граматика в дії**
Завжди запитуйте себе: предмет виконує дію чи отримує її? Якщо предмет отримує дію, використовуйте пасивний дієприкметник: «вишита сорочка» (хтось вишив), «принесений лист» (хтось приніс).
:::

Важлива риса пасивних дієприкметників полягає в тому, що вони є фундаментом для інших пасивних конструкцій. Ми вже знайомі з безособовими формами на -но та -то, які акцентують увагу на результаті дії. Пасивний дієприкметник — це перший крок до створення таких форм. Коли ми описуємо предмет через атрибут, ми кажемо «написаний твір». Якщо ж ми хочемо зосередитися на факті завершеної дії як присудку, ми легко перетворюємо цей дієприкметник на безособову форму: «твір написано». Цей логічний місток між ознакою предмета та загальним результатом робить українську граматичну систему стрункою та послідовною.

<!-- INJECT_ACTIVITY: fill-in -->

Finally, it is worth mentioning the tense of passive participles. Unlike English, where participles can have a complex system of tenses, the Ukrainian system is much simpler. In Ukrainian, passive participles only have a past tense form. This is perfectly logical: if an object has an attribute as a result of someone's action, that action must have already taken place. You do not need to memorize additional tables for present or future tenses; it is enough to master the rules for forming the past tense forms.

## Творення пасивних дієприкметників

В українській мові пасивні дієприкметники утворюються від основи інфінітива перехідних дієслів. Найпростіший спосіб творення передбачає використання суфікса **-н-**. Це правило діє для тих дієслів, основа яких закінчується на голосний **-а-** або **-я-**. Коли ми додаємо суфікс, тематичний голосний основи зберігається. Наприклад, від дієслова «прочитати» ми відкидаємо закінчення «-ти», беремо основу «прочита-», додаємо суфікс «-н-» та закінчення: утворюється «прочитаний». Аналогічно працюють інші дієслова: «написати» перетворюється на «написаний», а «посіяти» стає «посіяний».

Якщо ж основа інфінітива закінчується на приголосний звук або на голосні **-и-**, **-і-**, **-ї-**, ми використовуємо суфікс **-ен-** (або його м'який варіант **-єн-**). Під час творення таких дієприкметників кінцеві голосні основи «-и-» або «-і-» зникають і змінюються на «-е-» у суфіксі. Наприклад, дієслово «принести» має основу на приголосний «принес-», тому ми просто додаємо суфікс і отримуємо «принесений». Дієслово «вивчити» втрачає свою «-и-» і перетворюється на «вивчений». Відповідно, дієслово «напоїти» утворює форму «напоєний».

> *If the infinitive stem ends in a consonant or the vowels -и-, -і-, -ї-, we use the suffix -ен- (or its soft variant -єн-). During the formation of such participles, the final stem vowels -и- or -і- disappear and change to -е- in the suffix. For example, the verb "принести" (to bring) has a consonant stem "принес-", so we just add the suffix to get "принесений" (brought). The verb "вивчити" (to learn) loses its "-и-" and becomes "вивчений" (learned). Accordingly, the verb "напоїти" (to give a drink) forms "напоєний".*

Третій суфікс **-т-** використовується переважно з односкладовими дієсловами та з тими, що мають основу на **-ну-** або **-у-**. Процес творення тут дуже простий: ми відкидаємо «-ти» і додаємо «-тий». Наприклад: «мити» перетворюється на «митий», «бити» стає «битий», а «взути» і «зігнути» змінюються на «взутий» та «зігнутий». Варто зазначити, що деякі дієслова дозволяють утворювати паралельні, варіантні форми. Слово «замкнути» може стати як «замкнений», так і «замкнутий». Обидва варіанти є правильними та літературними.

<!-- INJECT_ACTIVITY: match-up -->

Окрему увагу слід звернути на чергування приголосних, яке виникає під час використання суфікса **-ен-**. Українська мова любить милозвучність, тому приєднання цього суфікса часто спричиняє зміну останнього приголосного звука в основі. Наприклад, звук **[д]** чергується з **[дж]**: від дієслова «розбудити» утворюється «розбуджений» (я бачу розбудженого сина). Звук **[т]** переходить у **[ч]**: слово «сплатити» дає форму «сплачений» (рахунок уже сплачений), а «закрутити» стає «закручений» (закручений дріт). Ці чергування є природними та зустрічаються в багатьох знайомих вам словах.

Чергування приголосних охоплює й інші звуки. Звук **[з]** змінюється на **[ж]**, як у слові «вразити», що утворює форму «вражений». Звук **[с]** переходить у **[ш]**: дієслово «скосити» стає дієприкметником «скошений» (так само «носити» утворює «ношений»). Дуже важливою є поява звука **[л]** після губних приголосних **[б]**, **[п]**, **[в]**, **[м]**, **[ф]**. Через це від слова «робити» ми утворюємо «роблений», а від «замовити» — «замовлений». Щоб легше запам'ятати ці зміни, подивіться на таблицю нижче.

:::info
**Чергування приголосних**
*   **д → дж**: розбудити → розбуджений
*   **т → ч**: сплатити → сплачений, закрутити → закручений
*   **з → ж**: вразити → вражений
*   **с → ш**: скосити → скошений, носити → ношений
*   **б, п, в, м, ф → бл, пл, вл, мл, фл**: замовити → замовлений
:::

<!-- INJECT_ACTIVITY: error-correction -->

Щоб безпомилково утворити будь-який пасивний дієприкметник, використовуйте простий покроковий алгоритм. Крок перший: візьміть форму інфінітива, наприклад, дієслово «запросити». Крок другий: визначте основу, відкинувши закінчення «-ти» (запроси-). Крок третій: оберіть суфікс залежно від кінцевого звука основи (тут основа закінчується на «-и», отже беремо суфікс «-ен-»). Крок четвертий: перевірте, чи є чергування приголосних (звук [с] перед «-ен-» змінюється на [ш], і основа стає «запрош-»). Крок п'ятий: додайте суфікс і правильне закінчення прикметника. Результат: «запрошений».

Насамкінець варто запам'ятати кілька правил правопису. В українській мові пасивні дієприкметники завжди пишуться з однією літерою «н». Слова «сказаний», «зроблений» чи «написаний» ніколи не мають подвоєння, що відрізняє їх від деяких прикметників. Також пам'ятайте, що в суфіксі **-ен-** завжди пишеться літера «е», а не «и». Форма «скошений» є правильною, тоді як варіант з літерою «и» є грубою орфографічною помилкою.

## Відмінювання пасивних дієприкметників

Пасивні дієприкметники змінюються за родами, числами та відмінками. Вони відмінюються точно так само, як звичайні прикметники твердої групи (наприклад, «гарний» або «новий»). Це означає, що вам не потрібно вивчати нові чи складні таблиці закінчень. Усі правила, які ви вже знаєте для прикметників, працюють і тут. Давайте розглянемо повну парадигму відмінювання на прикладі дієприкметника «прочитаний». Зверніть увагу на те, як змінюються закінчення залежно від граматичного роду та числа.

| Відмінок | Чоловічий рід | Жіночий рід | Середній рід | Множина |
| :--- | :--- | :--- | :--- | :--- |
| **Н.** | прочитаний | прочитана | прочитане | прочитані |
| **Р.** | прочитаного | прочитаної | прочитаного | прочитаних |
| **Д.** | прочитаному | прочитаній | прочитаному | прочитаним |
| **Зн.** | *як Н. або Р.* | прочитану | прочитане | *як Н. або Р.* |
| **Ор.** | прочитаним | прочитаною | прочитаним | прочитаними |
| **М.** | (на) прочитаному | (на) прочитаній | (на) прочитаному | (на) прочитаних |

Дієприкметник завжди узгоджується з іменником, від якого він залежить. Він повністю переймає рід, число та відмінок свого головного слова. Цей граматичний зв'язок часто називають принципом «дзеркального» закінчення, адже правильне запитання до дієприкметника завжди підказує його форму. Наприклад, ми кажемо «прочитана книга» (жіночий рід, називний відмінок), але «прочитаного листа» (чоловічий рід, родовий відмінок). У множині ми використовуємо форму «прочитаними повідомленнями» (орудний відмінок). Усі ці закінчення абсолютно ідентичні прикметниковим, що робить їхнє використання інтуїтивно зрозумілим.

> *The participle always agrees with the noun it depends on. It fully adopts the gender, number, and case of its main word. This grammatical connection is often called the principle of "mirror" endings, because the correct question to the participle always hints at its form. For example, we say "прочитана книга" (read book — feminine, nominative), but "прочитаного листа" (of the read letter — masculine, genitive). In the plural, we use the form "прочитаними повідомленнями" (with the read messages — instrumental). All these endings are absolutely identical to adjective endings, making their use intuitively understandable.*

У реченні пасивний дієприкметник найчастіше виконує роль узгодженого означення. Це його найприродніша і найпоширеніша синтаксична функція в українській мові. Наприклад, у фразі «Я бачу збудований міст» слово «збудований» просто описує іменник і відповідає на питання «який?». Значно рідше дієприкметник виступає іменною частиною складеного присудка, як у реченні «Міст був збудований». Українська мова загалом сильно тяжіє до активних конструкцій. Тому замість громіздкого пасивного речення «Текст був написаний студентом» значно краще і природніше сказати «Студент написав текст».

Варто також звернути особливу увагу на різницю між повною та короткою формами. У сучасній літературній українській мові пасивні дієприкметники практично завжди мають повну форму із закінченням (наприклад, «прочитаний», «зроблена», «відкрите»). Короткі форми чоловічого роду, такі як «прочитан» або «збудован», є абсолютно неприродними для нашої мови. Українська граматика категорично уникає їх використання, оскільки вони є прямим запозиченням і калькою з інших мов. Якщо вам потрібно наголосити на результаті завершеної дії без акценту на її виконавці, мовна норма вимагає використовувати інші інструменти.

:::tip
**Безособові форми замість коротких**
Ніколи не використовуйте штучні короткі форми на кшталт «лист написан» або «договір підписан». Якщо виконавець дії невідомий або просто неважливий, українська мова пропонує надзвичайно елегантне рішення: безособові форми на **-но** та **-то**. Правильно казати: «лист написано» та «договір підписано». Це робить ваше мовлення грамотним.
:::

## Дієприкметник чи прикметник?

As you read more Ukrainian texts, you will notice that some words look exactly like passive participles but act differently. Over time, many passive participles have lost their connection to a specific action and have become regular adjectives. 

Коли слово втрачає значення дії та починає означати постійну властивість предмета, воно стає прикметником. Наприклад, слово «варений» походить від дієслова «варити». Але у словосполученні «варена картопля» воно описує лише спосіб приготування страви. Це вже не результат дії, а постійна характеристика. Так само слова «печений», «солений» або «мелений» сьогодні найчастіше виступають звичайними прикметниками.

> *When a word loses its meaning of action and begins to denote a permanent property of an object, it becomes an adjective. For example, the word "варений" (cooked/boiled) comes from the verb "варити" (to boil). But in the phrase "варена картопля" (boiled potatoes), it only describes the method of preparing the dish. It is no longer the result of an action, but a permanent characteristic. Similarly, the words "печений" (baked), "солений" (salted), or "мелений" (ground) today most often act as regular adjectives.*

How can you tell them apart? The most reliable grammatical test is to look at the verb aspect. Passive participles are almost always formed from perfective verbs because they focus on a completed result.

Порівняйте два речення. Слово «варений» — це звичайний прикметник, який не має виду. Але якщо додати префікс і утворити слово «зварений», це вже справжній пасивний дієприкметник доконаного виду. Він вказує на успішно завершену дію. Отже, «варена картопля» — це просто назва страви. Натомість «зварена картопля» означає, що хтось щойно закінчив її готувати.

Another excellent way to distinguish them is the agent test. A passive participle can always take a dependent word in the instrumental case to show who performed the action.

Спробуйте додати іменник в орудному відмінку, який називає виконавця дії. Якщо це звучить природно, перед вами дієприкметник. Наприклад, ми можемо сказати «зварена мамою картопля» або «випечений пекарем хліб». Тут чітко видно, хто виконав дію. Але ми не можемо сказати «варена мамою картопля», бо прикметник не потребує виконавця.

<!-- INJECT_ACTIVITY: quiz -->

Understanding this difference helps you choose the right word for the right context.

Ці стилістичні нюанси важливі для вільного володіння мовою. У побутовому спілкуванні ми частіше використовуємо прикметники для опису звичайних речей. Але в офіційному стилі пасивні дієприкметники стають незамінними.

:::tip
**The double N spelling**
In Ukrainian, both adjectives and passive participles usually have a single **-н-** in their suffixes (e.g., **зроблений**, **варений**). Don't rely on spelling alone to tell them apart; always use the aspect or agent test!
:::

## Практика: пасивні дієприкметники у тексті

> — **Екскурсовод:** Вітаю в Маріїнському палаці! Зверніть увагу на цей відреставрований фасад. *(Welcome to the Mariinskyi Palace! Pay attention to this restored facade.)*
> — **Турист 1:** Яка краса! А ці збережені інтер'єри оригінальні? *(What beauty! Are these preserved interiors original?)*
> — **Екскурсовод:** Так, частково. Тут ви бачите відновлені розписи на стінах та написану у XIX столітті картину. *(Yes, partially. Here you see the restored paintings on the walls and a picture painted in the 19th century.)*
> — **Турист 2:** А ким створена ця дивовижна ліпнина? *(And by whom was this amazing stucco molding created?)*
> — **Екскурсовод:** Вона зроблена італійськими майстрами, запрошеними до Києва. *(It was made by Italian masters invited to Kyiv.)*
> — **Турист 1:** Дуже цікаво. А ця кімната завжди була зачинена? *(Very interesting. And was this room always closed?)*
> — **Екскурсовод:** Ні, це нещодавно відкрита зала, спеціально підготовлена для відвідувачів. *(No, this is a recently opened hall, specially prepared for visitors.)*

У цьому діалозі ми бачимо багато пасивних дієприкметників. Вони допомагають екскурсоводу професійно описувати предмети, які зазнали певної дії в минулому. Наприклад, слово «написану» утворене від інфінітива «написати» за допомогою суфікса «-н-», оскільки основа закінчується на «-а-». Слово «зроблена» походить від «зробити». Тут ми бачимо чергування приголосних (б — бл) та суфікс «-ен-». А дієприкметник «відкрита» утворений від дієслова «відкрити» за допомогою суфікса «-т-».

> *In this dialogue, we see many passive participles. They help the guide professionally describe objects that have undergone a certain action in the past. For example, the word "написану" (painted/written) is formed from the infinitive "написати" (to write/paint) using the suffix "-н-" because the stem ends in "-а-". The word "зроблена" (made) comes from "зробити" (to make). Here we see the consonant alternation (б — бл) and the suffix "-ен-". And the participle "відкрита" (opened) is formed from the verb "відкрити" (to open) using the suffix "-т-".*

<!-- INJECT_ACTIVITY: reading -->

In Ukrainian, we often transform active sentences into passive ones to shift the focus from the person doing the action to the result of that action. When we do this, the direct object of the active sentence becomes the subject of the passive sentence. The original subject is placed in the Instrumental case.

Щоб закріпити навички, спробуйте утворити пасивні дієприкметники від таких дієслів: передати (переданий), одягнути (одягнутий), заплести (заплетений), зварити (зварений), помити (помитий), замести (заметений), пофарбувати (пофарбований).

Розглянемо приклад трансформації активного стану на пасивний. Активне речення: «Італійські майстри зробили цю ліпнину». Тут фокус на тому, хто виконав дію. Щоб змістити акцент на результат, ми використовуємо пасивний дієприкметник: «Ця ліпнина зроблена італійськими майстрами». Виконавець дії тепер стоїть в орудному відмінку. Такий підхід робить ваше мовлення більш об'єктивним та елегантним.

> *Let's look at an example of transforming the active voice into the passive voice. Active sentence: "Italian masters made this stucco molding". Here the focus is on who performed the action. To shift the focus to the result, we use a passive participle: "This stucco molding was made by Italian masters". The performer of the action is now in the instrumental case. This approach makes your speech more objective and elegant.*

Now it is your turn to practice using passive participles as adjectives in free speech. Describing a room, a building, or a favorite object is a great way to consolidate this grammar. You can describe things that have been changed, decorated, or built by someone.

Уявіть свою кімнату або улюблене місце. Спробуйте описати його, використовуючи нову граматику. Наприклад, ви можете сказати: «У моїй кімнаті стоїть пофарбований стіл. На стіні висить написана місцевим художником картина. На підлозі лежить куплений учора килимок». Звертайте увагу на узгодження дієприкметника з іменником у роді, числі та відмінку.

> *Imagine your room or a favorite place. Try to describe it using the new grammar. For example, you can say: "In my room, there is a painted table. A picture painted by a local artist hangs on the wall. A rug bought yesterday lies on the floor." Pay attention to the agreement of the participle with the noun in gender, number, and case.*

:::tip
**Instrumental Case for Agents**
Remember that in Ukrainian, passive participles can take a dependent word in the Instrumental case to show by whom the action was performed. For example, **написана художником** (painted by an artist). This is a very natural way to add detail to your descriptions.
:::

<!-- INJECT_ACTIVITY: essay-response -->

## Підсумок

Пасивні дієприкметники — це дуже важливий інструмент для створення природних текстів українською мовою. Вони виражають ознаку предмета за дією, яку над ним виконав хтось інший. Наприклад, коли ми кажемо «прочитана книга», ми розуміємо, що хтось цю книгу прочитав. Утворення цих слів залежить від основи інфінітива. Ми використовуємо три основні суфікси: -н-, -ен- та -т-. Суфікс -н- додається до основ на -а-. Суфікс -ен- приєднується до основ на приголосний або на -и-, -і-, і часто викликає чергування приголосних звуків. Суфікс -т- використовується переважно з односкладовими основами.

> *Passive participles are a very important tool for creating natural texts in Ukrainian. They express a feature of an object based on an action performed on it by someone else. For example, when we say "a read book", we understand that someone read this book. The formation of these words depends on the infinitive stem. We use three main suffixes: -н-, -ен-, and -т-. The suffix -н- is added to stems ending in -а-. The suffix -ен- attaches to stems ending in a consonant or in -и-, -і-, and often causes consonant alternations. The suffix -т- is used mostly with monosyllabic stems.*

Ось зведений алгоритм творення пасивних дієприкметників:

| Кінцевий звук основи | Суфікс | Приклад творення |
| :--- | :--- | :--- |
| Голосний **-а-** | **-н-** | прочитати → прочитаний |
| Приголосний, **-и-**, **-і-** | **-ен-** | побачити → побачений |
| Односкладова основа | **-т-** | мити → митий |

*Швидка довідка чергувань перед -ен-: д→дж, т→ч, з→ж, с→ш, б→бл.*
Готові дієприкметники відмінюються як звичайні прикметники твердої групи.

> *Here is the summary algorithm for forming passive participles:
> - Stem ending in **-а-** gets the **-н-** suffix (прочитати → прочитаний).
> - Stem ending in a consonant, **-и-**, or **-і-** gets the **-ен-** suffix (побачити → побачений).
> - Monosyllabic stems get the **-т-** suffix (мити → митий).
> 
> Quick-reference alternations before -ен-: д→дж, т→ч, з→ж, с→ш, б→бл.*

To make sure you have fully mastered this grammar, try answering the following self-check questions before moving on to the next module:

- Can I distinguish an active participle from a passive one? For example, you should know the difference between the active **квітучий** (blooming) and the passive **пофарбований** (painted).
- Which suffix should I choose for the verb **зачинити** (to close)? The correct answer is the suffix **-ен-**, forming the word **зачинений**.
- What consonant alternation will occur in the word **замовити** (to order)? The letter **в** changes to **вл**, resulting in the participle **замовлений**.
- How do I agree the participle **написаний** (written) with the noun **лист** (letter) in the Genitive case? They must match entirely, becoming **написаного листа**.
- What is the difference between **варена картопля** (boiled potatoes) and **зварена картопля** (potatoes that have been boiled)? The first is an adjective describing a permanent type of food, while the second is a true participle implying a completed action with a result.

:::info
**Next Steps**
Now that you can form passive participles, you hold the key to the next level of Ukrainian syntax. In the next module (M59), you will learn how to combine these participles with dependent words to form a **дієприкметниковий зворот** (participle phrase), which has its own specific punctuation rules.
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: participles-passive
level: b1

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: B1 (Module 66)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
