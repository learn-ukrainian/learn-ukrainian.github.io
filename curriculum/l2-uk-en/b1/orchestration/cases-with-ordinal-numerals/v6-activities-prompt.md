<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/cases-with-ordinal-numerals.yaml` file for module **61: Порядкові числівники і відмінки** (b1).

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

- `<!-- INJECT_ACTIVITY: fill-in-declension -->`
- `<!-- INJECT_ACTIVITY: quiz-declension -->`
- `<!-- INJECT_ACTIVITY: match-up-dates -->`
- `<!-- INJECT_ACTIVITY: error-correction-dates -->`
- `<!-- INJECT_ACTIVITY: essay-response-dates -->`
- `<!-- INJECT_ACTIVITY: quiz-time -->`
- `<!-- INJECT_ACTIVITY: fill-in-time -->`
- `<!-- INJECT_ACTIVITY: fill-in-order -->`
- `<!-- INJECT_ACTIVITY: quiz-order -->`
- `<!-- INJECT_ACTIVITY: reading-ordinals -->`
- `<!-- INJECT_ACTIVITY: quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Прочитайте текст про відмінювання порядкових числівників і дайте відповіді
    на запитання.
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «Дати».
  type: essay-response
- focus: Вставте правильну граматичну форму у реченнях на тему відмінювання порядкових
    числівників.
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему дати.
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Відмінювання
    порядкових числівників».'
  type: quiz
- focus: З'єднайте терміни з розділу «Дати» з їхніми визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- складений числівник (compound numeral — двадцять п'ятий)
- вдруге (for the second time — adverb)
- утретє (for the third time — adverb)
- в першу чергу (first of all)
- двадцять перше століття (twenty-first century)
required:
- порядковий числівник (ordinal numeral — перший, другий, третій)
- дата (date — uses ordinal in Р.в.)
- котра година (what time is it)
- поверх (floor/storey)
- століття (century)
- половина (half — о пів на п'яту)
- хвилина (minute)
- рік (year — року in Р.в.)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Відмінювання порядкових числівників

When you need to express the order of items, dates, or time, you use ordinal numerals. In Ukrainian, these are called порядкові числівники. They answer the questions «котрий?» (which one in order, masculine), «котра?» (feminine), «котре?» (neuter), or «котрі?» (plural). The most important foundational rule to remember is that ordinal numerals behave exactly like adjectives. They share the same endings and follow the same declension patterns, meaning if you know how to decline a standard adjective, you already know how to decline an ordinal numeral.

Порядкові числівники завжди вказують на порядок предметів при лічбі. Вони повністю втрачають граматичні властивості кількісних числівників і поводяться в реченні як звичайні прикметники. Це означає, що вони мають категорію роду, числа та відмінка, які завжди залежать від іменника.

> *Ordinal numerals always indicate the order of objects when counting. They completely lose the grammatical properties of cardinal numerals and behave in a sentence like regular adjectives. This means they have the category of gender, number, and case, which always depend on the noun.*

Більшість порядкових числівників належить до твердої групи відмінювання. Вони відмінюються точно так само, як тверді прикметники, наприклад, «новий» або «зелений». Розгляньмо числівник «п'ятий» як нашу основну модель. Цей зразок застосовується майже до всіх порядкових числівників, включаючи «перший», «другий», «четвертий» та «шостий».

| Відмінок | Чоловічий рід | Жіночий рід | Середній рід | Множина |
| :--- | :--- | :--- | :--- | :--- |
| **Н.в.** | п'ятий | п'ята | п'яте | п'яті |
| **Р.в.** | п'ятого | п'ятої | п'ятого | п'ятих |
| **Д.в.** | п'ятому | п'ятій | п'ятому | п'ятим |
| **Зн.в.** | п'ятий / п'ятого | п'яту | п'яте | п'яті / п'ятих |
| **Ор.в.** | п'ятим | п'ятою | п'ятим | п'ятими |
| **М.в.** | (на) п'ятому / п'ятім | (на) п'ятій | (на) п'ятому / п'ятім | (на) п'ятих |
| **Кл.в.** | п'ятий | п'ята | п'яте | п'яті |

Notice that in the Accusative case for the masculine singular and the plural forms, the ending depends on whether the noun being described is animate or inanimate. If the noun is an inanimate object, the Accusative form matches the Nominative. If the noun is animate, representing a person or an animal, the Accusative form matches the Genitive. For the feminine and neuter forms, this animacy distinction does not apply. Also, observe the alternate endings in the Locative case for masculine and neuter forms; both «п'ятому» and «п'ятім» are grammatically correct and widely used in modern Ukrainian.

While almost all ordinal numerals belong to the hard declension group, there is one critical exception that you must memorize: the numeral «третій» (third). This numeral, along with compound numbers ending in it like «двадцять третій», declines according to the soft group of adjectives, similar to the word «синій». This means you will see a soft sign or the soft vowel letters taking the place of the hard vowels in the endings.

| Відмінок | Чоловічий рід | Жіночий рід | Середній рід | Множина |
| :--- | :--- | :--- | :--- | :--- |
| **Н.в.** | третій | третя | третє | треті |
| **Р.в.** | третього | третьої | третього | третіх |
| **Д.в.** | третьому | третій | третьому | третім |
| **Зн.в.** | третій / третього | третю | третє | треті / третіх |
| **Ор.в.** | третім | третьою | третім | третіми |
| **М.в.** | (на) третьому / третім | (на) третій | (на) третьому / третім | (на) третіх |
| **Кл.в.** | третій | третя | третє | треті |

When writing forms like «третього» or «третьому», pay close attention to the spelling. The soft sign is required before the vowel «о» to maintain the soft sound of the consonant. In the feminine Accusative case, the ending is «-ю» instead of «-у», and the neuter Nominative ends in «-є» rather than «-е». Mastering this single exception is essential because the third position is incredibly common in dates, addresses, and daily scheduling.

Оскільки порядкові числівники функціонують як прикметники, вони повинні суворо узгоджуватися з іменником. Це узгодження відбувається одразу за трьома граматичними категоріями: родом, числом та відмінком. Ви не можете просто поставити порядковий числівник у називному відмінку поруч з іменником в іншому відмінку. Щоразу, коли іменник змінює свою форму відповідно до граматичного контексту речення, порядковий числівник також змінюється, щоб збігатися з ним.

Let us look at some clear examples of this synchronized agreement. If you are talking about the first lesson, which is masculine and in the Nominative case, you say «перший урок». If you are reading the first book, the feminine noun takes the Accusative case, so the numeral must also become Accusative: «першу книжку». When referring to the first of September, a neuter concept representing a date, you use the Genitive case: «першого вересня». Finally, if you are discussing the first students in a plural Genitive context, both words adapt accordingly to become «перших учнів».

:::info
**Grammar box**
Always identify the gender, number, and case of the core noun first. Once you know these three properties, apply the exact same properties to the ordinal numeral modifying it.
:::

To demonstrate how this noun-adjective agreement works in action, let us walk through a practice declension of the phrase «п'ятий клас» (fifth grade) across all seven cases. The noun «клас» is a masculine, inanimate object belonging to the hard declension group. Watch how the endings of both words change in harmony. Because the noun is inanimate, the Accusative case remains identical to the Nominative case for the entire phrase.

*   **Н.в.** (хто? що?): п'ятий клас
*   **Р.в.** (кого? чого?): п'ятого класу
*   **Д.в.** (кому? чому?): п'ятому класу
*   **Зн.в.** (кого? що?): п'ятий клас
*   **Ор.в.** (ким? чим?): п'ятим класом
*   **М.в.** (на кому? на чому?): у п'ятому класі
*   **Кл.в.** (кличний): п'ятий класе

As you progress to higher numbers, you will frequently encounter compound ordinal numerals, which are known as складені числівники. These are numerals made up of two or more words, such as twenty-fifth or one hundred fifteenth. The critical rule for compound ordinal numerals in Ukrainian is that ONLY the very last word declines. All the preceding words in the number remain frozen in their Nominative case forms.

У складених порядкових числівниках змінюється лише останнє слово. Це суттєва відмінність від кількісних числівників, де кожна частина складного числа може змінювати свою форму. Порівняйте називний відмінок «двадцять третій день» із родовим відмінком «двадцять третього дня». Слово «двадцять» зовсім не змінюється.

Let us walk through declining the feminine phrase «сто п'ятнадцята сторінка» (the one hundred fifteenth page) through all the cases. This rule significantly simplifies the use of large dates and complex numbers, as you only need to worry about conjugating the final adjective-like word.

*   **Н.в.** (хто? що?): сто п'ятнадцята сторінка
*   **Р.в.** (кого? чого?): сто п'ятнадцятої сторінки
*   **Д.в.** (кому? чому?): сто п'ятнадцятій сторінці
*   **Зн.в.** (кого? що?): сто п'ятнадцяту сторінку
*   **Ор.в.** (ким? чим?): сто п'ятнадцятою сторінкою
*   **М.в.** (на кому? на чому?): на сто п'ятнадцятій сторінці
*   **Кл.в.** (кличний): сто п'ятнадцята сторінко

One of the most comforting aspects of learning ordinal numerals in Ukrainian is their predictable stress pattern. When you learn a cardinal number, the stress sometimes shifts to a different syllable depending on the case you are using. However, for ordinal numerals, the stress remains completely fixed on the exact same syllable throughout all grammatical cases.

If the stress falls on the first syllable in the Nominative case, as in «перший», it stays there for all other forms like «першого» or «першому». The same fixed stress rule applies to «другий», «третій», «сьомий», and «десятий». This fixed stress simplifies memorization greatly. Once you learn the correct pronunciation for the dictionary form of an ordinal numeral, you can confidently apply that same stress pattern across the entire declension paradigm without any second-guessing.

<!-- INJECT_ACTIVITY: fill-in-declension -->
<!-- INJECT_ACTIVITY: quiz-declension -->

## Дати

Коли ми хочемо сказати, яке сьогодні число, ми використовуємо порядковий числівник у називному відмінку. Зверніть увагу, що числівник завжди стоїть у формі середнього роду. Це відбувається тому, що слово «число» мається на увазі, навіть якщо ми його не вимовляємо. Назва місяця завжди стоїть у родовому відмінку однини, адже це число певного місяця.

> *When we want to say what date it is today, we use an ordinal numeral in the Nominative case. Note that the numeral always takes the neuter form. This happens because the word "число" (date/number) is implied, even if we don't say it. The name of the month is always in the Genitive singular, because it is the date of a specific month.*

Наприклад, якщо ви подивитеся на календар, ви можете сказати: «Сьогодні п'яте березня». Або, якщо наближається Новий рік, ви скажете: «Сьогодні тридцять перше грудня». Слово «сьогодні» починає речення, далі йде числівник середнього роду в називному відмінку, а потім місяць у родовому. Це найпростіший спосіб відповісти на запитання «Яке сьогодні число?». Уявіть, що ви читаєте новини. Журналіст часто починає ефір саме так: «Доброго ранку, сьогодні десяте жовтня».

Ситуація змінюється, коли ми хочемо сказати, що якась подія відбулася або відбудеться в певний день. Якщо ви відповідаєте на запитання «коли?», вам потрібно поставити сам порядковий числівник у родовий відмінок. Назва місяця, як і в попередньому випадку, також залишається в родовому відмінку. Ця конструкція є дуже поширеною, коли ви плануєте зустрічі, купуєте квитки або розповідаєте про своє життя.

Розглянемо різницю. Якщо ви кажете «Сьогодні п'яте березня», це констатація факту. Але якщо ви плануєте поїздку, ви скажете: «Я їду до Києва п'ятого березня». Інший приклад: «Він народився п'ятнадцятого вересня». У цих реченнях порядковий числівник відповідає на запитання «коли?», тому він приймає форму родового відмінка середнього роду. Ви часто почуєте цю форму в новинах або під час офіційних розмов. Наприклад: «Конференція почнеться двадцятого лютого». Отже, запам'ятайте просте правило: якщо є дія, яка відбувається в певний день, числівник вимагає родового відмінка.

Щоб назвати повну дату, вам потрібно додати рік. У повних датах слово «рік» завжди стоїть у родовому відмінку — «року». Сам числівник, який позначає рік, є складеним порядковим числівником. Як ви вже знаєте, головне правило для таких числівників полягає в тому, що відмінюється лише останнє слово. Всі попередні слова залишаються незмінними.

Давайте подивимося, як це працює на практиці. Якщо ви хочете сказати, що подія відбулася в тисяча дев'ятсот дев'яностому році, дата звучатиме так: «тисяча дев'ятсот дев'яностого року». Слова «тисяча», «дев'ятсот» залишаються в початковій формі. Змінюється лише останнє слово «дев'яностого», приймаючи форму родового відмінка. Уявімо повну дату: «Вона народилася першого січня дві тисячі п'ятого року». Тут ми маємо день, місяць і рік — усі елементи стоять у родовому відмінку, щоб відповісти на запитання «коли?».

:::info
**Grammar box**
When stating a full date answering the question "when?", every component is in the Genitive case: the day (ordinal), the month (noun), and the year (ordinal + noun). Remember that in the compound numeral for the year, only the last word declines.
:::

На письмі ми часто використовуємо цифри замість того, щоб писати довгі числівники словами. Проте українська мова має чіткі правила щодо того, як правильно додавати закінчення до цифр. Якщо ви пишете порядковий числівник цифрою, вам потрібно додати буквене нарощення через дефіс. Це допомагає читачеві зрозуміти, у якому відмінку, роді та числі стоїть слово.

Наприклад, якщо подія відбувається п'ятнадцятого числа, ви напишете «15-го числа». Зверніть увагу на дефіс перед закінченням «-го». Це закінчення підказує нам, що слово стоїть у родовому відмінку. Якщо ви пишете про сторінку книги, це буде «1-ша сторінка» (називний відмінок, жіночий рід). Якщо ви згадуєте клас у школі, ви напишете «5-й клас» (називний відмінок, чоловічий рід). Це правило робить тексти набагато легшими для сприйняття. Завжди використовуйте дефіс перед буквеним закінченням, коли числівник записаний арабськими цифрами і позначає порядок.

Хоча правило дефіса є дуже поширеним, існують важливі винятки, які ви повинні знати. Ці винятки стосуються римських цифр та стандартних календарних форматів. Якщо порядковий числівник записаний римськими цифрами, ми ніколи не додаємо жодних буквених закінчень. Римські цифри часто використовуються для позначення століть, розділів у книгах або імен монархів. Також буквене нарощення ніколи не додається до дат, якщо після цифри вказано назву місяця або слово «рік» (наприклад, «15 березня», «2024 року»).

Наприклад, ви часто побачите напис «ХХІ століття». Ви не можете написати «ХХІ-е століття», це вважається серйозною помилкою. Ви повинні читати це як «двадцять перше століття», але на письмі залишаються лише римські цифри. Інший важливий виняток — це стандартний формат дати, де день, місяць і рік розділені крапками. Якщо ви бачите дату у форматі «15.03.2024», ви не додаєте жодних закінчень чи слів. Ви просто читаєте це як звичайну дату, підставляючи правильні відмінки самостійно під час читання вголос.

:::note
**Quick tip**
Never attach ordinal suffixes (like "-го" or "-й") to Roman numerals. It is always "ХХ століття", never "ХХ-те століття". The same applies to dates written with dots: "15.03.2024" stands alone without any hyphenated endings.
:::

Тепер давайте потренуємося застосовувати всі ці правила разом, читаючи повні історичні дати. Це завдання вимагає уважності, адже вам потрібно узгодити день, місяць і рік. Почнемо з найважливішої дати для України. Як би ви прочитали «24 серпня 1991 року»?

Спочатку беремо день. Запитання «коли?», тому нам потрібен родовий відмінок: «двадцять четвертого». Місяць залишається в родовому відмінку: «серпня». Далі йде рік: «тисяча дев'ятсот дев'яносто першого». І закінчуємо словом «року». Разом виходить: «двадцять четвертого серпня тисяча дев'ятсот дев'яносто першого року». Спробуйте подумки прочитати дату вашого народження. Спочатку переведіть число в родовий відмінок, потім додайте місяць. Після цього прочитайте рік, пам'ятаючи, що змінюється лише останнє слово. Ця практика допоможе вам почуватися впевнено під час спілкування в офіційних установах або в розмовах з друзями про минулі події.

Ви також можете зустріти дати без точного дня, лише з місяцем і роком. У такому випадку місяць стоїть у місцевому відмінку з прийменником «у» або «в», а рік залишається в родовому. Наприклад: «У серпні тисяча дев'ятсот дев'яносто першого року». Але для точних повних дат завжди використовуйте повністю родовий відмінок без прийменників.

<!-- INJECT_ACTIVITY: match-up-dates -->
<!-- INJECT_ACTIVITY: error-correction-dates -->
<!-- INJECT_ACTIVITY: essay-response-dates -->

## Час

Telling time in Ukrainian requires a solid understanding of ordinal numerals, as hours are almost always expressed as an order in a sequence. When someone asks «Котра година?» (What time is it?), they are literally asking "Which hour is it?". The answer uses the Nominative case of the ordinal numeral, such as «Зараз п'ята година» (It is the fifth hour). However, when you need to state *at what time* an event happens, answering the question «О котрій годині?» (At what time?), the grammar shifts. You must use the preposition «о» (or «об» before vowels) followed by the ordinal numeral in the Locative case. For feminine ordinal numerals, this means using the «-ій» ending.

Якщо подія відбувається рівно о певній годині, ми завжди використовуємо прийменник «о» або «об» та місцевий відмінок. Слово «година» є іменником жіночого роду, тому порядковий числівник також приймає форму жіночого роду. Наприклад, ми кажемо «о першій годині», «о другій годині» або «о десятій годині». Якщо числівник починається з голосного звуку, для милозвучності ми використовуємо прийменник «об», як у виразі «об одинадцятій годині». Зверніть увагу, що слово «година» часто можна опустити в розмові, і фраза «зустрінемось о сьомій» буде абсолютно зрозумілою та природною.

> *If an event happens exactly at a certain hour, we always use the preposition "о" or "об" and the Locative case. The word "hour" is a feminine noun, so the ordinal numeral also takes the feminine form. For example, we say "at the first hour", "at the second hour", or "at the tenth hour". If the numeral starts with a vowel sound, for euphony we use the preposition "об", as in the expression "at the eleventh hour". Note that the word "hour" can often be omitted in conversation, and the phrase "let's meet at the seventh" will be perfectly understandable and natural.*

Expressing half-hours in Ukrainian uses a unique and highly structured approach that might seem counterintuitive at first. Instead of looking back at the hour that has passed, Ukrainian looks forward to the approaching hour. The construction uses the phrase «о пів на» (literally "at half toward") followed by the ordinal numeral of the *next* hour in the Accusative case. The Accusative ending for feminine ordinal numerals is «-ю». For example, 4:30 is expressed as «о пів на п'яту». You are essentially saying that time has advanced halfway toward the fifth hour.

Конструкція з «о пів на» є дуже поширеною в повсякденному спілкуванні і вимагає уважності. Ви повинні завжди думати про наступну годину, яка ще не настала. Якщо зараз 8:30, українською мовою це звучить як «о пів на дев'яту». Використання знахідного відмінка після прийменника «на» вказує на напрямок руху часу. Ця логіка кардинально відрізняється від багатьох інших мов, де час зазвичай прив'язується до поточної години. Спочатку це може здатися незвичним, але регулярна практика швидко перетворить цю конструкцію на автоматичну навичку.

When expressing minutes past or to the hour, the logic of looking forward or backward dictates the prepositions used. For minutes *past* the hour (the first 30 minutes), Ukrainian uses the preposition «на» + Accusative case of the next hour, similar to the half-hour rule. For example, 4:10 is «десять хвилин на п'яту» (ten minutes toward the fifth). When expressing minutes *to* the hour (the last 30 minutes), the perspective flips. You state the minutes remaining, followed by the preposition «за» + Nominative case of the approaching hour. Thus, 4:50 becomes «за десять хвилин п'ята» (in ten minutes, the fifth).

Коли хвилинна стрілка перебуває в першій половині циферблата, ми використовуємо прийменник «на» та знахідний відмінок наступної години. Наприклад, 14:15 ми читаємо як «п'ятнадцять хвилин на третю». Якщо хвилинна стрілка перетнула позначку в тридцять хвилин, ми починаємо відраховувати час, що залишився до наступної години. У цьому випадку ми використовуємо прийменник «за», кількість хвилин у називному відмінку та саму годину в називному відмінку. Час 08:40 буде звучати як «за двадцять хвилин дев'ята», що буквально означає, що через двадцять хвилин настане дев'ята година.

:::info
**Grammar box**
A common error among learners and even some native speakers is using the preposition «без» (without) + Genitive case to express minutes to the hour, such as saying *«без десяти п'ять» for 4:50. This is a direct calque (literal translation) from Russian and is considered a severe grammatical error in standard Ukrainian. The only correct traditional forms are «за десять хвилин п'ята» or «десять хвилин до п'ятої». If these constructions feel too complex in the moment, you can always rely on the simple digital reading, saying «чотири п'ятдесят».
:::

Уникання кальок є важливим кроком до чистої та правильної української мови. Конструкція з прийменником «без» для позначення часу є яскравим прикладом російського впливу, якого слід свідомо позбуватися. Коли ви хочете сказати 11:45, ніколи не кажіть «без п'ятнадцяти дванадцять». Правильними та природними варіантами є «за п'ятнадцять хвилин дванадцята» або «за чверть дванадцята». Слово «чверть» означає п'ятнадцять хвилин і часто використовується для зручності. Якщо ви сумніваєтесь у правильності відмінків, завжди краще назвати час цифрами, ніж використовувати неправильну граматичну конструкцію з іншої мови.

> *Avoiding calques is an important step toward clean and correct Ukrainian. The construction with the preposition "без" for telling time is a clear example of Russian influence that should be consciously eliminated. When you want to say 11:45, never say "без п'ятнадцяти дванадцять". The correct and natural options are "за п'ятнадцять хвилин дванадцята" or "за чверть дванадцята". The word "чверть" means fifteen minutes and is often used for convenience. If you are unsure about the correct cases, it is always better to name the time using digits rather than using an incorrect grammatical construction from another language.*

In modern Ukrainian, there is a clear distinction between the formal traditional way of telling time and the colloquial digital method. Formal time expressions rely heavily on ordinal numerals and the prepositions «на», «за», or «до» (e.g., «п'ятнадцять хвилин на четверту» for 3:15). This style is standard in literature, broadcasting, and polite conversation. However, the colloquial approach simply reads the numbers as they appear on a digital clock, using cardinal numerals. Saying «три п'ятнадцять» (three fifteen) or «п'ятнадцята тридцять» (fifteen thirty) is perfectly acceptable in everyday situations, train stations, or business meetings where clarity and brevity are prioritized.

Обидва способи називати час є правильними, але вони мають різний стилістичний відтінок. Традиційний формат з порядковими числівниками робить ваше мовлення більш вишуканим і демонструє глибоке розуміння граматики. Цифровий формат є більш прагматичним і часто використовується в офіційних розкладах транспорту або коли потрібно уникнути будь-яких непорозумінь. Вибір між цими двома стилями залежить від контексту спілкування та ваших особистих уподобань. Головне — бути послідовним і не змішувати обидві системи в одному реченні.

Let's walk through a practice exercise to solidify these rules. We will take five specific times and express them in both the formal (ordinal) and colloquial (cardinal) variants. This mental drill will help bridge the gap between understanding the grammar and producing it fluently.

Розглянемо час 03:15. Формальний варіант вимагає прийменника «на»: «п'ятнадцять хвилин на четверту» (або «чверть на четверту»). Розмовний варіант дуже простий: «третя п'ятнадцять». Для 07:30 традиційною формою є «о пів на восьму», тоді як цифровий еквівалент — «сьома тридцять». Час 11:45 формально звучить як «за п'ятнадцять хвилин дванадцята» (або «за чверть дванадцята»), а розмовно — «одинадцята сорок п'ять». Рівно 12:00 найкраще виражається як «дванадцята година» або просто «дванадцята». Нарешті, 06:05 перетворюється на «п'ять хвилин на сьому» в традиційній системі та на «шоста нуль п'ять» у повсякденній розмові. Регулярно перекладайте час на своєму годиннику українською, щоб швидко звикнути до цих конструкцій.

<!-- INJECT_ACTIVITY: quiz-time -->
<!-- INJECT_ACTIVITY: fill-in-time -->

## Поверхи, номери, порядок

When navigating a building, you will rely heavily on ordinal numerals to identify floors. The word for floor is «поверх», a masculine noun. Just like with any other location, the grammatical case depends entirely on whether you describe a static position or movement. To say someone is located on a specific floor, use the Locative case with the preposition «на». For instance, «на першому поверсі» means "on the first floor", and «на дев'ятому поверсі» means "on the ninth floor". However, when talking about movement, the rules change to reflect your trajectory. To express the origin of movement, like coming down from a floor, use the Genitive case with the preposition «з». An example is «з другого поверху» (from the second floor). Conversely, to indicate the destination of your movement, such as going up, you must use the Accusative case with the preposition «на». Thus, you would say «ми йдемо на п'ятий поверх» (we are going to the fifth floor). Understanding these patterns ensures accurate directions.

:::info
**Grammar box**
When navigating spaces, remember the preposition pairings: **на + Місцевий** (Locative) for static location («на першому поверсі»), **з + Родовий** (Genitive) for origin («з третього поверху»), and **на + Знахідний** (Accusative) for destination («на п'ятий поверх»).
:::

Ordinal numerals are also crucial for transport routes and precise addresses. When waiting at an intersection for public transport, you will refer to routes using ordinals. You might say you are waiting for «автобус номер сьомий» (bus number seven) or «тролейбус п'ятнадцятий» (trolleybus fifteen). It is very common in spoken Ukrainian to drop the word for "number" entirely, resulting in phrases like «сьомий автобус» (the seventh bus). Beyond public transport, these numerals are naturally used for pinpointing specific locations. When reading an address, you will refer to «будинок третій» (building three). Once inside, you will look for the specific door, which could be «квартира п'ята» (apartment five) for residential spaces, or «кабінет двісті десятий» (office two hundred ten) in commercial settings. Remember that the numeral must agree with the noun in gender. Since «будинок» and «кабінет» are masculine, their accompanying ordinals are masculine, while the feminine «квартира» requires a feminine ordinal.

Порядкові числівники допомагають нам виражати послідовність дій та новий досвід. Найпростіший спосіб описати таку ситуацію — використати словосполучення «перший раз». Однак, коли ми говоримо про повторювані дії, українська мова пропонує дуже елегантні прислівники, які закінчуються на літеру «-е». Замість того, щоб казати «другий раз», ви можете просто сказати «вдруге». Ця логіка продовжується і далі: «утретє» означає дію в третій раз, а «вчетверте» — в четвертий. Ці слова роблять ваше щоденне мовлення значно більш плавним. Крім того, існує поширена фраза «в першу чергу». Хоча багато українців використовують її щодня, синоніми «насамперед» або «передусім» вважаються більш питомими та літературними. Використовуйте їх, коли хочете підкреслити найважливіше завдання.

> *Ordinal numerals help us express the sequence of actions and new experiences. The simplest way to describe such a situation is to use the phrase «перший раз» (for the first time). However, when we talk about repeated actions, the Ukrainian language offers very elegant adverbs ending in the letter "-е". Instead of saying «другий раз», you can simply say «вдруге» (for the second time). This logic continues further: «утретє» means an action for the third time, and «вчетверте» for the fourth. These words make your daily speech significantly smoother. Additionally, there is a widespread phrase «в першу чергу» (first of all). Although many Ukrainians use it daily, the synonyms «насамперед» or «передусім» are considered more native and literary. Use them when you want to emphasize the most important task.*

When discussing history or art, you will frequently mention centuries. The word for century is «століття», a neuter noun. To state that an event happened in a particular century, use the Locative case with the preposition «у» or «в». For example, "in the twenty-first century" translates to «у двадцять першому столітті». Notice how the compound ordinal «двадцять першому» is in Locative to agree with «столітті». If you are naming the century as the subject, use the Nominative case, as in «двадцяте століття» (the twentieth century). Another important aspect of sequence is listing points in an argument. For this, Ukrainian uses ordinal adverbs formed with the prefix «по-». When structuring your thoughts, use «по-перше» (firstly), «по-друге» (secondly), and «по-третє» (thirdly) to guide your listener through your main points.

:::tip
**Did you know?**
When listing points in an argument (firstly, secondly, thirdly), always use the hyphenated adverbs **по-перше**, **по-друге**, and **по-третє**. In written Ukrainian, these introductory words are always followed by a comma.
:::

Finally, ordinal numerals carry significant weight in formal and official registers, such as legal documents. This style of language is known as «науково-навчальний» or «офіційно-діловий» стиль. When citing laws, contracts, or textbook structures, ordinal numerals are almost exclusively used to ensure absolute clarity. For instance, when referring to a constitution, you will say «стаття перша» (article one) instead of using a cardinal number. The same principle applies to other structural divisions within formal texts. You will regularly encounter phrases like «пункт третій» (point three), «параграф п'ятий» (paragraph five), and «розділ восьмий» (chapter eight). In these contexts, placing the noun before the ordinal numeral adds a distinct tone of authority and formality. Mastering this specific word order is essential if you plan to engage with professional environments or read official announcements.

<!-- INJECT_ACTIVITY: fill-in-order -->
<!-- INJECT_ACTIVITY: quiz-order -->

## Порядкові числівники в контексті

To truly master ordinal numerals, you must see them in action within authentic scenarios. In professional environments, formal invitations, schedules, and daily announcements rely heavily on precise dates, times, and locations. Without ordinal numerals, organizing our lives would be incredibly difficult. A single corporate announcement can contain multiple ordinal numerals, each declining differently depending on its specific grammatical role in the sentence. Imagine you have just received an official invitation to an important conference regarding a new software project. This short text demonstrates how ordinal numerals seamlessly integrate with nouns in various cases to convey exact logistical details. Pay close attention to how the endings change to agree with words like "March," "hour," "floor," and "room." Recognizing these patterns in a complete paragraph will help you build your own complex sentences.

Шановні колеги! Офіційна зустріч щодо нашого нового спільного проєкту відбудеться п'ятнадцятого березня. Реєстрація всіх учасників почнеться о другій годині дня біля головного входу. Сама наукова конференція розпочнеться рівно о третій годині. Захід проходитиме в головному офісі нашої компанії, який розташований у центрі міста. Головний конференц-зал розташований на четвертому поверсі. Якщо у вас виникнуть будь-які питання, будь ласка, звертайтеся до організаторів у кімнаті двісті двадцять п'ятій. Просимо вас не запізнюватися на відкриття. Це наша перша масштабна подія у двадцять першому столітті. Ми чекаємо на вас із великим нетерпінням!

> *Dear colleagues! The official meeting regarding our new joint project will take place on the fifteenth of March. Registration of all participants will begin at two o'clock in the afternoon near the main entrance. The scientific conference itself will start exactly at three o'clock. The event will be held in the main office of our company, which is located in the city center. The main conference hall is located on the fourth floor. If you have any questions, please contact the organizers in room two hundred and twenty-five. We ask you not to be late for the opening. This is our first large-scale event in the twenty-first century. We look forward to seeing you with great anticipation!*

Let us thoroughly analyze the grammar utilized in this formal invitation. The phrase «п'ятнадцятого березня» uses the Genitive case because it directly answers the question "on what date did something happen?". In Ukrainian, both the ordinal numeral and the month must be in the Genitive case to form this time expression. When indicating the exact clock time of the conference, the text uses «о третій годині» in the Locative case, directly following the preposition «о». The word for floor is a masculine noun, so saying "on the fourth floor" becomes «на четвертому поверсі». This again uses the Locative case to indicate a static physical location within a building. Finally, the compound numeral in the phrase «у кімнаті двісті двадцять п'ятій» requires a special rule: only the very last word declines. Because the noun «кімнаті» is a feminine word in the Locative case, the ordinal numeral becomes «п'ятій», while the cardinal number "two hundred twenty" remains completely unchanged in its base Nominative form.

:::info
**Grammar box**
When stating that an event happened "on a date", both the ordinal numeral and the month must be in the Genitive case (e.g., **п'ятнадцятого березня**). However, when expressing that you need something "for a specific date" (like booking a ticket), you must use the preposition **на** followed by the Accusative case (e.g., **на п'яте березня**).
:::

Another extremely common situation where ordinal numerals are absolutely vital is purchasing travel tickets and navigating transportation hubs. Whether you are standing at a busy bus terminal, an airport check-in counter, or a train station, you will constantly need to specify exact dates, platforms, and seat numbers. Let us look at a typical everyday conversation at the central railway station, Київський вокзал. A passenger is trying to buy a train ticket to Lviv for a specific upcoming day. This short dialogue perfectly highlights how grammatical cases shift quickly as the conversation context changes from target dates to points of origin and physical locations within the large station complex.

> — **Пасажир:** Добрий день! Мені потрібен квиток до Львова на п'яте березня. *(Good day! I need a ticket to Lviv for the fifth of March.)*
> — **Касир:** Добрий день. На жаль, на ранковий експрес квитків уже немає. Але є вільні місця на вечірній потяг. *(Good day. Unfortunately, there are no tickets left for the morning express. But there are available seats on the evening train.)*
> — **Пасажир:** Чудово, мені це підходить. А з якого вагона починається нумерація? *(Great, that suits me. And from which car does the numbering start?)*
> — **Касир:** З першого вагона, з голови потяга. Ваш третій перон, колія номер п'ять. *(From the first car, from the head of the train. Your platform is the third platform, track number five.)*
> — **Пасажир:** Зрозумів. А де я можу роздрукувати мій електронний квиток? *(Understood. And where can I print my electronic ticket?)*
> — **Касир:** На другому поверсі — спеціальна каса для електронних квитків. *(On the second floor is a special ticket office for electronic tickets.)*
> — **Пасажир:** Дуже дякую за допомогу! *(Thank you very much for the help!)*

In this exchange, the passenger actively asks for a ticket «на п'яте березня». Here, the preposition «на» indicates a specific target date or a deadline for a reservation. This construction always requires the Accusative case. Since the word «п'яте» acts as a neuter numeral (implying the neuter noun «число»), its Accusative form conveniently matches its Nominative form. When the cashier explains the layout and numbering of the train cars, she says «з першого вагона». The preposition «з» (meaning "from" or "out of") always demands the Genitive case to show the definitive point of origin. The phrase «третій перон» serves simply as the grammatical subject of that particular sentence, so it remains comfortably in the default Nominative case. Lastly, when explaining exactly where the passenger can print the physical ticket, the cashier uses the phrase «на другому поверсі». Just like in our previous reading passage about the conference, indicating a static location inside a building requires the Locative case. By breaking down these real-world examples, you can clearly see how ordinal numerals adapt to their surroundings.

<!-- INJECT_ACTIVITY: reading-ordinals -->

## Підсумок

The rules governing ordinal numerals in Ukrainian might seem numerous at first glance, but they follow highly predictable patterns. The most fundamental principle to remember is that ordinal numerals decline exactly like adjectives. This means they must always agree with their accompanying noun in gender, number, and case. When you encounter a compound ordinal numeral, remember that only the last word changes its form, while all preceding words remain frozen in the Nominative case. In practical usage, specific contexts demand specific cases. Dates always require the Genitive case to indicate when an event occurred. Conversely, expressing clock time requires the Locative case.

**сьомого березня** — *on the seventh of March*
**о третій годині** — *at three o'clock*

Finally, when talking about minutes approaching the next hour, always use the proper preposition to indicate time remaining. You must completely avoid unnatural constructions borrowed from Russian.

**за десять хвилин сьома** — *ten minutes to seven (never "без десяти")*

Українська граматика вимагає точності у використанні числівників. Якщо ви запам'ятаєте базові правила відмінювання та керування відмінками, ви зможете впевнено говорити про час, дати та розклади.

> *Ukrainian grammar requires precision in the use of numerals. If you remember the basic rules of declension and case governance, you will be able to speak confidently about time, dates, and schedules.*

:::info
**Перевірте себе**
Now that we have covered the theory, it is time to put your knowledge into practice. Complete the following tasks to ensure you have mastered the material. You can write your answers down or say them aloud.
:::

Тепер час для невеликої самоперевірки. Спробуйте виконати ці п'ять практичних завдань, щоб остаточно закріпити вивчений матеріал.

Перше завдання стосується граматики. Відміняйте складений числівник «двадцять п'ятий» за всіма відмінками. Зверніть особливу увагу на те, яке саме слово змінює своє закінчення під час відмінювання.

Друге завдання пов'язане з календарем. Напишіть сьогоднішню дату словами двома різними способами. Спочатку напишіть, яке сьогодні число, використовуючи правильний відмінок. Потім уявіть, що певна подія відбулася саме сьогодні, і напишіть цю дату.

Третє завдання перевірить ваше вміння називати час. Напишіть час 3:15, 7:30 та 11:45 українською мовою. Спробуйте використати як офіційний, так і розмовний стилі для кожного варіанта, пам'ятаючи про прийменники.

Четверте та п'яте завдання мають практичне значення. Скажіть свою адресу, обов'язково вказавши поверх і номер квартири у відповідному відмінку. Після цього назвіть три різні історичні століття у місцевому відмінку, використовуючи правильну форму порядкових числівників.

In the next module, we will explore a closely related and equally important topic: quantitative expressions. While this module focused on ordinal numbers indicating sequence and order, the next one will delve into cardinal numbers. We will learn exactly how numbers like two, five, or forty interact with nouns in different cases. You will discover the unique rules of agreement between numbers and nouns, such as why the number two requires the Nominative plural, while the number five demands the Genitive plural. Understanding these quantitative rules will allow you to count objects, describe quantities, and express measurements with absolute grammatical accuracy.

<!-- INJECT_ACTIVITY: quiz -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: cases-with-ordinal-numerals
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

**Level: B1 (Module 61)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
