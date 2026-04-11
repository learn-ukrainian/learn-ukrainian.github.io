<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 61: Порядкові числівники і відмінки (B1, B1.5 [Case Nuances & Prepositions])
**Writer:** Gemini
**Word target:** 4000

## Plan (source of truth)

<plan_content>
module: b1-060
level: B1
sequence: 60
slug: cases-with-ordinal-numerals
version: '3.1'
title: "Порядкові числівники і відмінки"
subtitle: "Відмінювання порядкових числівників, дати, час, поверхи"
focus: grammar
pedagogy: PPP
phase: "B1.5 [Case Nuances & Prepositions]"
word_target: 4000
objectives:
  - "Learner can decline ordinal numerals like adjectives (перший-першого-першому)
    and correctly agree them with nouns in gender, number, and case"
  - "Learner can use ordinal numerals in dates: Р.в. for 'on a date' (п'ятнадцятого
    березня), Н.в. for 'today is' (сьогодні п'ятнадцяте березня)"
  - "Learner can use ordinal numerals in clock time expressions: о третій годині,
    за десять хвилин четверта, о пів на п'яту"
  - "Learner can use ordinals in everyday contexts: floors (на третьому поверсі),
    order (перший раз, другий раз), centuries (у двадцять першому столітті)"
  - "Learner can decline compound ordinal numerals where only the last word changes
    (двісті двадцять п'ята — двісті двадцять п'ятої)"
dialogue_situations:
  - setting: 'Buying train tickets at Київський вокзал — specifying dates and platforms:
      Квиток (m, ticket) на п''яте березня. З першого вагона (m, car). Третій перон
      (m, platform). На другому поверсі (m, floor) — каса (f, ticket office).'
    speakers:
      - Пасажир
      - Касир (cashier)
    motivation: 'Ordinal numerals in cases: п''яте березня(acc), першого вагона(gen),
      третій перон(nom)'
content_outline:
  - section: "Відмінювання порядкових числівників"
    words: 800
    points:
      - "From Литвінова Grade 6 p.237: Ordinal numerals decline like adjectives. Твердий
        тип: перший, другий, четвертий, п'ятий, шостий... М'який тип: третій, третя,
        третє, треті. Full paradigm for перший (m/f/n/pl) and третій (m/f/n/pl)."
      - "Agreement: ordinal + noun must agree in gender, number, case. перший урок
        (m. Н.в.), першу книжку (f. Зн.в.), першого вересня (n. Р.в.), перших учнів
        (pl. Р.в.). Practice: decline 'п'ятий клас' through all 7 cases."
      - "Compound ordinals (Заболотний Grade 6 p.179): ONLY the last word declines:
        двадцять третій день → двадцять третього дня → двадцять третьому дню. Practice:
        decline 'сто п'ятнадцята сторінка' through all cases."
      - "Stress patterns: перший (fixed stress), другий (fixed), третій (fixed but
        irregular soft declension), сьомий (fixed), десятий (fixed). All ordinals have
        fixed stress on the same syllable throughout declension, unlike some cardinal
        numerals. This simplifies memorization: once you know the nominative stress,
        it stays."
  - section: "Дати"
    words: 800
    points:
      - "Saying 'today is': Сьогодні + ordinal in Н.в. + month in Р.в.: Сьогодні п'яте
        березня. Сьогодні тридцять перше грудня. Note: the ordinal is NEUTER (число
        = neuter noun implied)."
      - "Saying 'on a date': ordinal in Р.в. + month in Р.в.: п'ятого березня, тридцять
        першого грудня. Він народився п'ятнадцятого вересня тисяча дев'ятсот дев'яностого
        року. Year: тисяча дев'ятсот дев'яностого року (only last word declines)."
      - "Writing dates with digits: 15 березня 2024 року. With ordinal ending: 15-го
        березня, 1-ша сторінка, 5-й клас. But dates in calendar format: 15.03.2024
        (no ending). Hyphen rules: the ordinal suffix attaches with a hyphen after
        digits (5-й, 10-та, 3-тє), but NOT after Roman numerals: ХХІ століття (no
        hyphen)."
      - "Practice: read and write 10 dates in full Ukrainian word form. Include
        historical dates: 24 серпня 1991 року (двадцять четвертого серпня тисяча
        дев'ятсот дев'яносто першого року), birthdays, and future events."
  - section: "Час"
    words: 700
    points:
      - "From Авраменко Grade 11 p.42: Full hours: о першій годині, о другій, о третій,
        о п'ятій. Note: годині is in М.в. (о + М.в.). Half hours: о пів на п'яту (at
        half past four — lit. 'half toward fifth')."
      - "Minutes past: десять хвилин на п'яту (4:10 — 'ten minutes toward fifth').
        Minutes to: за десять хвилин п'ята (4:50 — 'in ten minutes, the fifth'). NOT
        *без десяти п'ять (Russicism from без десяти пять). Correct: за десять хвилин
        п'ята or чотири п'ятдесят."
      - "Formal vs colloquial time: Formal: п'ятнадцять хвилин на четверту (3:15).
        Colloquial: три п'ятнадцять. Both are correct; formal uses ordinals, colloquial
        uses cardinals. In writing, digital format (15:30) doesn't use ordinals."
      - "Practice: express these times in Ukrainian: 3:15, 7:30, 11:45, 1:20, 9:55,
        12:00, 6:05. Give both formal (ordinal) and colloquial (cardinal) versions.
        Then: answer 'Котра година?' for each."
  - section: "Поверхи, номери, порядок"
    words: 600
    points:
      - "Floors: на першому поверсі (М.в.), з другого поверху (Р.в.), на п'ятий поверх
        (Зн.в. — direction). Маршрути: автобус номер сьомий, тролейбус п'ятнадцятий.
        Addresses: будинок третій, квартира п'ята, кабінет двісті десятий."
      - "Order: перший раз, вдруге (adverb — for the second time), утретє, вчетверте.
        В першу чергу (first of all). Centuries: у двадцять першому столітті (М.в.),
        двадцяте століття (Н.в.). По-перше, по-друге, по-третє (firstly, secondly
        — ordinal adverbs for listing)."
      - "Ordinals in document titles and official contexts: стаття перша, пункт третій,
        параграф п'ятий, розділ восьмий. From Авраменко Grade 7 p.63: numeral usage
        in formal/official register."
      - "Practice: describe your building (which floor), give directions (take bus
        number X), discuss historical periods (in the Y century), cite document articles."
  - section: "Порядкові числівники в контексті"
    words: 700
    points:
      - "Reading passage: a schedule/invitation containing multiple dates, times,
        floor numbers, and ordinals. Learners extract information and answer questions
        requiring correct ordinal declension. 'Зустріч відбудеться п'ятнадцятого березня
        о третій годині на четвертому поверсі, у кімнаті двісті двадцять п'ятій.'"
      - "Dialogue: making an appointment — agreeing on date, time, location. 'Коли
        вам зручно? Може, двадцять першого? О котрій годині? О пів на другу? Добре,
        на якому поверсі ваш офіс?'"
      - "Self-check: dates of major Ukrainian historical events: 24 серпня 1991 (День
        Незалежності), 28 червня 1996 (Конституція). Write in full word form with
        correct cases."
  - section: "Підсумок"
    words: 400
    points:
      - "Key patterns: ordinals decline like adjectives; compound ordinals — only
        last word declines; dates in Р.в.; clock time uses ordinals in М.в.; NOT *без
        десяти → за десять хвилин."
      - "Self-check: 1. Decline двадцять п'ятий through all cases. 2. Write today's
        date in full words (both 'today is' and 'on the date'). 3. Express times
        3:15, 7:30, 11:45 in Ukrainian. 4. Say your address with floor and apartment
        number. 5. Name three centuries in М.в. (у ... столітті)."
      - "Preview: кількісні вирази — agreement between quantity words and nouns."
vocabulary_hints:
  required:
    - "порядковий числівник (ordinal numeral — перший, другий, третій)"
    - "дата (date — uses ordinal in Р.в.)"
    - "котра година (what time is it)"
    - "поверх (floor/storey)"
    - "століття (century)"
    - "половина (half — о пів на п'яту)"
    - "хвилина (minute)"
    - "рік (year — року in Р.в.)"
  recommended:
    - "складений числівник (compound numeral — двадцять п'ятий)"
    - "вдруге (for the second time — adverb)"
    - "утретє (for the third time — adverb)"
    - "в першу чергу (first of all)"
    - "двадцять перше століття (twenty-first century)"
activity_hints:
  - type: reading
    focus: "Прочитайте текст про відмінювання порядкових числівників і дайте відповіді на запитання."
  - type: essay-response
    focus: "Напишіть 5 речень, використовуючи нову лексику з розділу «Дати»."
  - type: fill-in
    focus: "Вставте правильну граматичну форму у реченнях на тему відмінювання порядкових числівників."
  - type: error-correction
    focus: "Знайдіть і виправте помилки у реченнях на тему дати."
  - type: quiz
    focus: "Оберіть правильний варіант: лексика та граматика з розділу «Відмінювання порядкових числівників»."
  - type: match-up
    focus: "З'єднайте терміни з розділу «Дати» з їхніми визначеннями."
connects_to:
  - "b1-053 (Кількісні вирази — quantity expressions with cases)"
  - "b1-046 (Родовий відмінок — dates use Р.в.)"
  - "b1-050 (Часові прийменники — time expressions)"
prerequisites:
  - "A2 completion (numbers 1-1000, basic time telling)"
  - "b1-046 (Родовий відмінок деталі — Р.в. for dates)"
grammar:
  - "Відмінювання порядкових числівників як прикметників"
  - "Складені порядкові: тільки останнє слово відмінюється"
  - "Дати: Н.в. (сьогодні п'яте) vs Р.в. (п'ятого березня)"
  - "Час: о третій годині, о пів на п'яту, за десять хвилин четверта"
  - "Помилки: *без десяти → за десять хвилин"
register: науково-навчальний
references:
  - title: "Заболотний Grade 6, p.179"
    notes: "Ordinal numeral declension, compound ordinals, date and time rules."
  - title: "Литвінова Grade 6, p.237"
    notes: "Ordinals decline like adjectives, третій as м'який тип, digit notation."
  - title: "Авраменко Grade 11, p.42"
    notes: "Clock time rules: о пів на, за десять хвилин, avoid *без десяти."
  - title: "Авраменко Grade 11, p.37"
    notes: "Numeral declension overview including ordinals."

</plan_content>

## Generated Content

<generated_module_content>
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

Наприклад, якщо подія відбувається п'ятнадцятого березня, ви напишете «15-го березня». Зверніть увагу на дефіс перед закінченням «-го». Це закінчення підказує нам, що слово стоїть у родовому відмінку. Якщо ви пишете про сторінку книги, це буде «1-ша сторінка» (називний відмінок, жіночий рід). Якщо ви згадуєте клас у школі, ви напишете «5-й клас» (називний відмінок, чоловічий рід). Це правило робить тексти набагато легшими для сприйняття. Завжди використовуйте дефіс перед буквеним закінченням, коли числівник записаний арабськими цифрами і позначає порядок.

Хоча правило дефіса є дуже поширеним, існують важливі винятки, які ви повинні знати. Ці винятки стосуються римських цифр та стандартних календарних форматів. Якщо порядковий числівник записаний римськими цифрами, ми ніколи не додаємо жодних буквених закінчень. Римські цифри часто використовуються для позначення століть, розділів у книгах або імен монархів.

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

Коли хвилинна стрілка знаходиться в першій половині циферблата, ми використовуємо прийменник «на» та знахідний відмінок наступної години. Наприклад, 14:15 ми читаємо як «п'ятнадцять хвилин на третю». Якщо хвилинна стрілка перетнула позначку в тридцять хвилин, ми починаємо відраховувати час, що залишився до наступної години. У цьому випадку ми використовуємо прийменник «за», кількість хвилин у називному відмінку та саму годину в називному відмінку. Час 08:40 буде звучати як «за двадцять хвилин дев'ята», що буквально означає, що через двадцять хвилин настане дев'ята година.

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

Порядкові числівники допомагають нам виражати послідовність дій та новий досвід. Найпростіший спосіб описати таку ситуацію — використати словосолучення «перший раз». Однак, коли ми говоримо про повторювані дії, українська мова пропонує дуже елегантні прислівники, які закінчуються на літеру «-е». Замість того, щоб казати «другий раз», ви можете просто сказати «вдруге». Ця логіка продовжується і далі: «утретє» означає дію в третій раз, а «вчетверте» — в четвертий. Ці слова роблять ваше щоденне мовлення значно більш плавним. Крім того, існує поширена фраза «в першу чергу». Хоча багато українців використовують її щодня, синоніми «насамперед» або «передусім» вважаються більш питомими та літературними. Використовуйте їх, коли хочете підкреслити найважливіше завдання.

> *Ordinal numerals help us express the sequence of actions and new experiences. The simplest way to describe such a situation is to use the phrase «перший раз» (for the first time). However, when we talk about repeated actions, the Ukrainian language offers very elegant adverbs ending in the letter "-е". Instead of saying «другий раз», you can simply say «вдруге» (for the second time). This logic continues further: «утретє» means an action for the third time, and «вчетверте» for the fourth. These words make your daily speech significantly smoother. Additionally, there is a widespread phrase «в першу чергу» (first of all). Although many Ukrainians use it daily, the synonyms «насамперед» or «передусім» are considered more native and literary. Use them when you want to emphasize the most important task.*

When discussing history or art, you will frequently mention centuries. The word for century is «століття», a neuter noun. To state that an event happened in a particular century, use the Locative case with the preposition «у» or «в». For example, "in the twenty-first century" translates to «у двадцять першому столітті». Notice how the compound ordinal «двадцять першому» is in Locative to agree with «столітті». If you are naming the century as the subject, use the Nominative case, as in «двадцяте століття» (the twentieth century). Another important aspect of sequence is listing points in an argument. For this, Ukrainian uses ordinal adverbs formed with the prefix «по-». When structuring your thoughts, use «по-перше» (firstly), «по-друге» (secondly), and «по-третє» (thirdly) to guide your listener through your main points.

:::tip
**Did you know?**
When listing points in an argument (firstly, secondly, thirdly), always use the hyphenated adverbs **по-перше**, **по-друге**, and **по-третє**. In written Ukrainian, these introductory words are always followed by a comma.
:::

Finally, ordinal numerals carry significant weight in formal and official registers, such as legal documents. This style of language is known as «науково-навчальний» or «офіційно-діловий» стиль. When citing laws, contracts, or textbook structures, ordinal numerals are almost exclusively used to ensure absolute clarity. For instance, when referring to a constitution, you will say «стаття перша» (article one) instead of using a cardinal number. The same principle applies to other structural divisions within formal texts. You will regularly encounter phrases like «пункт третій» (point three), «параграф п'ятий» (paragraph five), and «розділ восьмий» (chapter eight). In these contexts, placing the noun before the ordinal numeral adds a distinct tone of authority and formality. Mastering this specific word order is essential if you plan to engage with professional environments or read official announcements.

<!-- INJECT_ACTIVITY: fill-in -->
<!-- INJECT_ACTIVITY: quiz -->

## Порядкові числівники в контексті

To truly master ordinal numerals, you must see them in action within authentic scenarios. In professional environments, formal invitations, schedules, and daily announcements rely heavily on precise dates, times, and locations. Without ordinal numerals, organizing our lives would be incredibly difficult. A single corporate announcement can contain multiple ordinal numerals, each declining differently depending on its specific grammatical role in the sentence. Imagine you have just received an official invitation to an important conference regarding a new software project. This short text demonstrates how ordinal numerals seamlessly integrate with nouns in various cases to convey exact logistical details. Pay close attention to how the endings change to agree with words like "March," "hour," "floor," and "room." Recognizing these patterns in a complete paragraph will help you build your own complex sentences.

Шановні колеги! Офіційна зустріч щодо нашого нового спільного проєкту відбудеться п'ятнадцятого березня. Реєстрація всіх учасників почнеться о другій годині дня біля головного входу. Сама наукова конференція розпочнеться рівно о третій годині. Захід проходитиме в головному офісі нашої компанії, який знаходиться в центрі міста. Головний конференц-зал розташований на четвертому поверсі. Якщо у вас виникнуть будь-які питання, будь ласка, звертайтеся до організаторів у кімнаті двісті двадцять п'ятій. Просимо вас не запізнюватися на відкриття. Це наша перша масштабна подія у двадцять першому столітті. Ми чекаємо на вас із великим нетерпінням!

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
</generated_module_content>

**PIPELINE NOTE — Word count: 5567 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 4000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 974 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Києва — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ конференц — NOT IN VESUM
  ✗ словосолучення — NOT IN VESUM

All 974 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
