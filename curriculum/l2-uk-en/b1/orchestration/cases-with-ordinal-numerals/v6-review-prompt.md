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

Ordinal numerals are an essential part of the Ukrainian language, allowing you to express the order or sequence of items, people, and events. Whenever you need to answer the question about which one in a sequence you are referring to, you will use these specific numbers. They are fundamentally different from cardinal numerals, which only express the total quantity.

В українській мові порядкові числівники завжди відповідають на питання «котрий?», «котра?», «котре?» або «котрі?». Вони вказують на порядок предметів при лічбі і є дуже важливими для правильного спілкування. Головне правило, яке вам потрібно запам'ятати, полягає в тому, що всі порядкові числівники поводяться абсолютно так само, як звичайні прикметники.

> *In the Ukrainian language, ordinal numerals always answer the questions "which one?" (masculine, feminine, neuter, or plural). They indicate the order of items when counting and are very important for correct communication. The main rule you need to remember is that all ordinal numerals behave exactly like regular adjectives.*

If you already know how to decline an adjective to match a noun in gender, number, and case, you already know how to decline an ordinal numeral. This architectural similarity makes them highly predictable and logical to use in everyday speech.

The vast majority of Ukrainian ordinal numerals belong to the hard group of declension. This means they take the exact same endings as hard-stem adjectives like «зелений» або «новий». When you look at words like «перший», «другий», «четвертий», «п'ятий», and «шостий», you can immediately recognize the characteristic hard endings. To demonstrate this pattern clearly, we will use the numeral «п'ятий» as our primary model.

Порядковий числівник «п'ятий» має закінчення «-ий» для чоловічого роду, «-а» для жіночого, «-е» для середнього та «-і» для множини. Під час відмінювання ці закінчення змінюються за правилами твердої групи прикметників.

| Відмінок | Чоловічий рід | Жіночий рід | Середній рід | Множина |
| :--- | :--- | :--- | :--- | :--- |
| **Н.в.** (хто? що?) | п'ятий | п'ята | п'яте | п'яті |
| **Р.в.** (кого? чого?) | п'ятого | п'ятої | п'ятого | п'ятих |
| **Д.в.** (кому? чому?) | п'ятому | п'ятій | п'ятому | п'ятим |
| **Зн.в.** (кого? що?) | п'ятий / п'ятого | п'яту | п'яте | п'яті / п'ятих |
| **Ор.в.** (ким? чим?) | п'ятим | п'ятою | п'ятим | п'ятими |
| **М.в.** (на кому? на чому?) | на п'ятому / п'ятім | на п'ятій | на п'ятому / п'ятім | на п'ятих |

Notice how the masculine and neuter forms share identical endings in the genitive, dative, instrumental, and locative cases. The accusative case for masculine and plural forms depends on animacy, just as it does for regular nouns and adjectives. If the noun is animate, you use the genitive form; if it is inanimate, you use the nominative form. The locative case offers a stylistic variant for masculine and neuter forms, allowing you to choose between «на п'ятому» and the slightly more traditional «на п'ятім».

While the hard group covers almost everything, there is one major exception that you must memorize. The ordinal numeral «третій» belongs to the soft group of declension. This specific numeral declines exactly like a soft-stem adjective such as «синій» або «ранній». Because the stem ends in a soft consonant sound, the grammatical endings reflect this softness by using letters like «я», «є», «ю», and the soft sign «ь».

Виняток становить лише числівник «третій», який має м'яку основу і відмінюється за м'якою групою. У жіночому роді він має закінчення «-я», а в середньому — закінчення «-є».

| Відмінок | Чоловічий рід | Жіночий рід | Середній рід | Множина |
| :--- | :--- | :--- | :--- | :--- |
| **Н.в.** (хто? що?) | третій | третя | третє | треті |
| **Р.в.** (кого? чого?) | третього | третьої | третього | третіх |
| **Д.в.** (кому? чому?) | третьому | третій | третьому | третім |
| **Зн.в.** (кого? що?) | третій / третього | третю | третє | треті / третіх |
| **Ор.в.** (ким? чим?) | третім | третьою | третім | третіми |
| **М.в.** (на кому? на чому?) | на третьому / третім | на третій | на третьому / третім | на третіх |

This soft declension paradigm is entirely consistent within itself. Pay special attention to the spelling in the genitive, dative, and locative cases for masculine and neuter forms, where the soft sign «ь» appears before the vowel «о» to preserve the soft pronunciation of the root consonant. The instrumental case «третім» and locative case «на третім» feature the letter «і» instead of the hard «и».

Because ordinal numerals function as adjectives grammatically, the rules of agreement are strict and mandatory. The ordinal numeral and the noun it modifies must always agree in gender, number, and case. You cannot decline the noun without simultaneously declining the numeral attached to it. This creates a synchronized pairing where both words reflect the same grammatical state.

Узгодження числівника з іменником є обов'язковою умовою правильної граматики. Якщо іменник стоїть у знахідному відмінку жіночого роду, то і числівник повинен мати таку саму форму. Це правило працює для всіх відмінків і родів без винятків.

For instance, if you are talking about the "first lesson" in the nominative case, you say «перший урок» because the noun is masculine singular. If you are reading the "first book" and need the accusative case, you change both words to feminine accusative, resulting in «першу книжку». When referring to the "first of September" in the genitive case, the neuter phrase becomes «першого вересня». Finally, if you are discussing the "first students" in the plural genitive case, you must say «перших учнів».

To see this synchronized noun-adjective agreement in action, let us walk through a complete practice declension of the phrase «п'ятий клас». This phrase is masculine and inanimate, which will influence our accusative case form.

*   **Н.в.:** п'ятий клас
*   **Р.в.:** п'ятого класу
*   **Д.в.:** п'ятому класу
*   **Зн.в.:** п'ятий клас
*   **Ор.в.:** п'ятим класом
*   **М.в.:** у п'ятому класі

Кожен відмінок демонструє ідеальну гармонію між прикметниковим закінченням числівника та відповідним закінченням іменника.

As you progress in Ukrainian, you will naturally encounter larger numbers, leading to compound ordinal numerals. These are numerals consisting of two or more words, such as twenty-third or one hundred fifteenth. The grammatical rule for compound ordinal numerals is remarkably simple and elegant: ONLY the absolute last word in the sequence declines. All preceding words remain frozen in their standard nominative cardinal form.

У складених порядкових числівниках відмінюється виключно останнє слово. Всі інші частини цього числа залишаються незмінними, незалежно від того, який відмінок вимагає контекст речення.

Consider the nominative phrase «двадцять третій день». The first word is a cardinal numeral, and the second is our soft-group ordinal. If we want to express "of the twenty-third day" in the genitive case, we only change the final word, producing «двадцять третього дня». The word «двадцять» does not change at all.

Let us decline the feminine phrase «сто п'ятнадцята сторінка» to reinforce this critical concept.

*   **Н.в.:** сто п'ятнадцята сторінка
*   **Р.в.:** сто п'ятнадцятої сторінки
*   **Д.в.:** сто п'ятнадцятій сторінці
*   **Зн.в.:** сто п'ятнадцяту сторінку
*   **Ор.в.:** сто п'ятнадцятою сторінкою
*   **М.в.:** на сто п'ятнадцятій сторінці

:::info
**Compound declension rule**
Always remember that compound ordinal numerals freeze all words except the very last one. You will never say «двадцятого третього дня» — the correct form is always «двадцять третього дня».
:::

Finally, let us discuss the pronunciation aspect of these words. Ukrainian ordinal numerals feature fixed stress patterns. Unlike some cardinal numerals or complex nouns that shift their stress from the stem to the ending depending on the case, ordinal numerals are wonderfully stable.

Наголос у порядкових числівниках ніколи не переходить на інший склад під час відмінювання. Якщо ви вивчили правильну вимову початкової форми, ви не зробите помилки в інших відмінках.

Words like «перший», «другий», «третій», «сьомий», and «десятий» keep the stress on the exact same syllable throughout their entire declension paradigms. This linguistic feature significantly simplifies memorization for language learners. Once you know the nominative stress placement, you can confidently decline the numeral through all seven cases without ever worrying about shifting vowel emphasis.

<!-- INJECT_ACTIVITY: fill-in-declension -->
<!-- INJECT_ACTIVITY: quiz-declension -->

## Дати

One of the most common and practical uses of ordinal numerals is expressing the current date. When you want to state what today's date is in Ukrainian, you must use the Nominative case for the ordinal numeral and the Genitive case for the month. This construction literally translates to "today is the Nth of the Xth month". A crucial detail here is that the ordinal numeral is always in the neuter gender. You might wonder why a neuter ending like «п'яте» or «перше» is used. This happens because the neuter noun «число» (date or number) is grammatically implied, even though it is almost never spoken in natural conversation. The month that follows simply answers the question "of which month?", which naturally requires the Genitive case. For instance, to say "Today is the fifth of March," you say «Сьогодні п'яте березня». If it is the end of the year, you say «Сьогодні тридцять перше грудня».

Кожного дня ми використовуємо порядкові числівники, щоб сказати поточну дату. Коли ми відповідаємо на питання «яке сьогодні число?», ми завжди ставимо числівник у називний відмінок середнього роду. Назва місяця при цьому обов'язково має форму родового відмінка. Ми кажемо «сьогодні перше січня» або «сьогодні двадцять четверте серпня». Слово «число» ми просто пропускаємо, але воно керує закінченням числівника.

Now that you know how to state today's date, we must look at how to describe an event happening *on* a specific date. In English, we use the preposition "on" for this purpose. In Ukrainian, however, you do not use a preposition for dates. Instead, the entire phrase shifts into the Genitive case to answer the question «коли?» (when). This is a very strict rule in Ukrainian grammar. You must take the neuter Nominative form, like «п'яте», and change it to the neuter Genitive form, which is «п'ятого». The month remains in the Genitive case. Therefore, the phrase "on the fifth of March" translates to «п'ятого березня».

Ця граматична конструкція є надзвичайно важливою для розповідей про минуле або планування майбутнього. Якщо ви хочете сказати, коли саме відбулася певна подія, ви не використовуєте жодних прийменників. Ви просто ставите порядковий числівник у форму родового відмінка. Наприклад, речення "He was born on the fifteenth of September" перекладається як «Він народився п'ятнадцятого вересня». У цьому реченні і числівник «п'ятнадцятого», і місяць «вересня» стоять у родовому відмінку.

:::info
**Date cases summary**
To say "today is...", use the Nominative case for the numeral: «Сьогодні десяте жовтня». To say "on a specific date...", use the Genitive case for the numeral: «Концерт буде десятого жовтня». The month is always Genitive.
:::

When discussing historical events or biographies, dates often include the year. Expressing the year in Ukrainian requires another application of the Genitive case and a firm understanding of compound ordinal numerals. The word for year is «рік», and to say "of the year", you use its Genitive form «року». The numeral representing the year is always an ordinal numeral. Here, you must apply the compound ordinal numeral rule discussed in the previous section. In any compound ordinal numeral, only the very last word declines. All preceding numbers remain in their frozen, Nominative cardinal form.

Розгляньмо цей принцип на конкретному прикладі. Якщо вам потрібно сказати "in the year nineteen ninety", ви перекладаєте це як «тисяча дев'ятсот дев'яностого року». Зверніть увагу, що слова «тисяча» та «дев'ятсот» не змінюються взагалі. Вони залишаються кількісними числівниками у називному відмінку. Відмінюється лише останнє слово «дев'яностого», яке приймає форму родового відмінка, узгоджуючись зі словом «року». Цей принцип працює для всіх складних дат, від давньої історії до нашого часу.

> *Let us examine this principle using a specific example. If you need to say "in the year nineteen ninety", you translate it as «тисяча дев'ятсот дев'яностого року». Notice that the words «тисяча» and «дев'ятсот» do not change at all. They remain cardinal numerals in the Nominative case. Only the last word «дев'яностого» declines, taking the form of the Genitive case to agree with the word «року». This principle works for all complex dates, from ancient history to our time.*

In written Ukrainian, dates and ordinal numerals are frequently represented using digits rather than being spelled out entirely in words. When you write an ordinal numeral using Arabic numerals, you must attach a specific suffix to indicate its grammatical case, gender, and number. This suffix is connected to the digit with a hyphen. The rule for determining the correct suffix is straightforward: you take the last one or two letters of the spelled-out ordinal numeral. You never write the entire word after the digit, just the grammatical ending.

Правильне написання цих закінчень допомагає читачеві миттєво зрозуміти відмінок числа. Наприклад, якщо ви пишете дату «п'ятнадцятого березня» цифрами, ви повинні додати закінчення родового відмінка. Оскільки слово «п'ятнадцятого» закінчується на літери «го», ви пишете «15-го березня». Так само працює узгодження з іменниками жіночого та чоловічого роду в різних відмінках. Якщо ви згадуєте «першу сторінку» у називному відмінку, ви пишете «1-ша сторінка». Якщо ви говорите про «п'ятий клас», ви пишете «5-й клас».

While the hyphen rule is widely applied, there are two major exceptions you must memorize to write flawless Ukrainian. The first exception concerns Roman numerals, which are traditionally used in Ukrainian typography to denote centuries, millennia, or the names of monarchs. When you write an ordinal numeral using Roman numerals, you must never attach a hyphen or a grammatical suffix. The Roman numeral itself inherently functions as an ordinal. Therefore, when writing about the twenty-first century, you simply write «ХХІ століття». Adding a suffix, such as «ХХІ-го», is a strict orthographic error.

Другий важливий виняток стосується стандартного календарного формату запису дат. У діловому листуванні або в коротких нотатках дати часто записують лише цифрами, розділеними крапками. У такому цифровому форматі закінчення порядкових числівників ніколи не використовуються. Наприклад, якщо ви хочете записати п'ятнадцяте березня дві тисячі двадцять четвертого року, ви пишете просто «15.03.2024». Ви не додаєте жодних літер чи дефісів до цих цифр. Читач автоматично прочитає цю послідовність цифр словами у правильних відмінках, спираючись на контекст речення.

To consolidate these complex rules, let us walk through the process of translating a complete historical date into full Ukrainian words. Consider the date of Ukrainian Independence: "24 серпня 1991 року". We know this date answers the question "when?", which means the entire phrase must be in the Genitive case. We start with the day. The number twenty-four is a compound numeral, so only the word "four" becomes an ordinal in the Genitive case. Thus, "twenty-fourth" becomes «двадцять четвертого». The month "August" is already in the Genitive case as «серпня». Next, we tackle the year: one thousand nine hundred ninety-first. Again, only the absolute final word declines. "One thousand" is «тисяча», "nine hundred" is «дев'ятсот», and "ninety" is «дев'яносто». The final word "first" becomes the Genitive ordinal «першого».

Тепер ми можемо об'єднати всі ці частини в єдину, граматично досконалу фразу. Повна і правильна вимова цієї історичної дати звучить так: «двадцять четвертого серпня тисяча дев'ятсот дев'яносто першого року». Це здається складним на перший погляд, але структура є абсолютно логічною. Кожне слово виконує свою конкретну функцію. Використовуйте цей покроковий метод для перекладу дат народження, історичних подій або майбутніх зустрічей, і ви завжди говоритимете правильно.

<!-- INJECT_ACTIVITY: match-up-dates -->
<!-- INJECT_ACTIVITY: error-correction-dates -->
<!-- INJECT_ACTIVITY: essay-response-dates -->

## Час

In Ukrainian, when you want to ask "At what time?" you say «О котрій годині?». To answer this question for full hours, you must use the preposition «о» (or «об» before a vowel sound) followed by an ordinal numeral in the Locative case (Місцевий відмінок). The word for hour, «година», also takes the Locative case, becoming «годині». Because you are specifying a point in a sequence, you use ordinals like "first" or "second" rather than cardinal numbers. This means that to say "at one o'clock", you literally say "at the first hour".

Українською мовою ми завжди використовуємо порядкові числівники для позначення точного часу. Якщо подія відбувається рівно о першій годині, ми кажемо «о першій годині». Коли зустріч запланована на одинадцяту, ми говоримо «об одинадцятій годині» або просто «об одинадцятій». Прийменник «об» використовується перед голосними звуками для милозвучності.

> *In Ukrainian, we always use ordinal numerals to indicate exact time. If an event happens exactly at one o'clock, we say "at the first hour". When a meeting is scheduled for eleven, we say "at the eleventh hour" or simply "at the eleventh". The preposition "об" is used before vowel sounds for euphony.*

Expressing half hours in Ukrainian requires a completely different logical structure compared to English. You use the phrase «о пів на» followed by the ordinal numeral of the *upcoming* hour in the Accusative case (Знахідний відмінок). The word «пів» is an indeclinable noun meaning "half", and «на» is a preposition indicating direction. Therefore, the phrase «о пів на п'яту» literally translates to "at half toward the fifth". This logic reflects the progression of time moving towards the next full hour.

Коли хвилинна стрілка показує рівно половину години, ми дивимося на наступну годину. Наприклад, час чотири тридцять ми називаємо «о пів на п'яту». Якщо зараз дев'ята тридцять, ми скажемо, що це «о пів на десяту». Ви повинні пам'ятати, що числівник після прийменника «на» завжди стоїть у формі знахідного відмінка жіночого роду.

> *When the minute hand shows exactly half an hour, we look at the next hour. For example, we call the time four thirty "at half toward the fifth". If it is currently nine thirty, we will say that it is "at half toward the tenth". You must remember that the numeral after the preposition "на" is always in the form of the accusative case of the feminine gender.*

To express minutes past the hour, Ukrainian uses the preposition «на» just like with half hours. You state the number of minutes that have passed as a cardinal numeral, followed by «на» and the next hour as an ordinal numeral in the Accusative case. For example, 4:10 is expressed as «десять хвилин на п'яту» (ten minutes toward the fifth). Conversely, to express minutes to the hour, you use the preposition «за». You state the word «за», then the number of remaining minutes, followed by the upcoming hour in the Nominative case. Therefore, 4:50 becomes «за десять хвилин п'ята» (in ten minutes, the fifth). If you want to use the word for "quarter", which is «чверть», the same prepositions apply. A quarter past four is «чверть на п'яту», and a quarter to five is «за чверть п'ята».

:::info
**Grammar box**
When saying minutes past the hour, use «на» + Accusative (Знахідний відмінок). When saying minutes to the hour, use «за» + Nominative (Називний відмінок). The word «хвилина» (minute) is often omitted in casual speech.
:::

A crucial decolonization rule applies to telling time in Ukrainian. You must explicitly avoid the common, yet entirely incorrect, Russicism «*без десяти п'ять». This literal translation of a Russian time structure does not exist in standard Ukrainian grammar. The Ukrainian language has its own distinct and natural constructions for indicating approaching time, primarily using the preposition «за». Using «*без десяти» immediately identifies a speaker as using Surzhyk. To express 4:50 correctly, you have only two valid options. You can use the traditional prepositional structure «за десять хвилин п'ята», or you can simply read the digital time as «чотири п'ятдесят». Both of these native options maintain the purity of the language and ensure that your speech sounds natural to a native ear.

While the traditional structures with ordinal numerals are considered the standard formal register, everyday Ukrainian also embraces a simpler colloquial approach. In informal settings, you can simply read the numbers as they appear on a digital clock, using cardinal numerals for both hours and minutes. This means that while 3:15 is formally expressed as «п'ятнадцять хвилин на четверту» or «чверть на четверту», you will frequently hear people say «три п'ятнадцять». Both registers are completely acceptable and widely understood depending on the social context. The digital reading is particularly common in transportation schedules, business meetings, and situations requiring maximum brevity. Conversely, the traditional ordinal structures are preferred in literature, formal broadcasting, and elegant everyday speech.

Let us practice translating specific times into both formal and colloquial Ukrainian formats. We will examine 3:15, 7:30, 11:45, 12:00, and 6:05. For 3:15, the formal version is «чверть на четверту» or «п'ятнадцять хвилин на четверту», while the colloquial is «три п'ятнадцять». For 7:30, the formal structure dictates «о пів на восьму», and the digital reading is «сім тридцять». To say 11:45, you formally use «за чверть дванадцята» or «за п'ятнадцять хвилин дванадцята», whereas colloquially it is «одинадцять сорок п'ять». Exactly 12:00 is simply «дванадцята година» formally, or «дванадцять нуль нуль» informally. Finally, 6:05 is formally «п'ять хвилин на сьому» and colloquially «шість нуль п'ять». By mastering both the traditional ordinal structures and the modern cardinal readings, you can confidently navigate any conversational setting or official schedule.

<!-- INJECT_ACTIVITY: quiz -->
<!-- INJECT_ACTIVITY: fill-in -->

## Поверхи, номери, порядок

When navigating buildings and describing movement between levels, ordinal numerals are essential. In Ukrainian, the case of the ordinal numeral and the noun **поверх** (floor) changes depending on whether you are describing a static location, an origin, or a destination. To say that something is located on a specific floor, you use the preposition **на** with the Locative case.

**на першому поверсі** — *on the first floor*
**на третьому поверсі** — *on the third floor*

If you are describing movement originating from a floor, use the preposition **з** with the Genitive case.

**з другого поверху** — *from the second floor*

Conversely, when indicating movement toward a specific floor, you must use **на** with the Accusative case. Therefore, if you are taking an elevator up, you go **на п'ятий поверх** (to the fifth floor). Notice how the ordinal numeral always perfectly matches the case, gender, and number of the noun it modifies.

Мій офіс знаходиться на дев'ятому поверсі великого бізнес-центру. Кожного ранку я піднімаюся на дев'ятий поверх ліфтом, а ввечері спускаюся з дев'ятого поверху сходами. Мої колеги працюють на сьомому поверсі, тому я часто ходжу до них у гості.

> *My office is located on the ninth floor of a large business center. Every morning I go up to the ninth floor by elevator, and in the evening I go down from the ninth floor by the stairs. My colleagues work on the seventh floor, so I often go to visit them.*

Beyond building levels, ordinal numerals frequently appear in transportation routes and physical addresses. When specifying a public transport route, it is common to use the word **номер** followed by an ordinal numeral in the Nominative case.

**автобус номер сьомий** — *bus number seven*
**тролейбус п'ятнадцятий** — *trolleybus fifteen*

This structure treats the route number as a descriptive quality of the vehicle. Similarly, when giving an address or locating a specific room, ordinal numerals identify the exact sequential position of the house, apartment, or office.

**будинок третій** — *house three*
**квартира п'ята** — *apartment five*

In large institutions, such as universities or corporate headquarters, rooms are often designated with compound numerals. If you need to find a specific office, you might be directed to **кабінет двісті десятий** (office two hundred ten). Remember the crucial rule for these compound ordinals: only the final word changes its form during declension, while the preceding numbers remain securely in their Nominative state.

Expressing the frequency or sequence of events requires a mix of ordinal numerals and specific numerical adverbs. When you want to say that something is happening for the first time, you use the standard ordinal adjective and noun combination, such as **перший раз** (the first time). However, for subsequent occurrences, Ukrainian employs specialized adverbs ending in **-е** or **-є**.

**вдруге** — *for the second time*
**утретє** — *for the third time*
**вчетверте** — *for the fourth time*

These adverbs elegantly compress the meaning into a single word and are heavily favored in natural speech. Additionally, when prioritizing tasks or thoughts, you can use a very common idiom. The phrase **в першу чергу** (first of all) literally translates to "in the first queue" and is a staple of both conversational and professional Ukrainian.

Я приїхав до Києва в першу чергу для того, щоб зустрітися з друзями. Це вже мій другий візит, але я відчуваю, ніби я тут перший раз. Сподіваюся, що коли я приїду сюди втретє, я зможу говорити українською ще краще.

> *I came to Kyiv primarily to meet with friends. This is already my second visit, but I feel as if I am here for the first time. I hope that when I come here for the third time, I will be able to speak Ukrainian even better.*

Historical periods and centuries are always expressed using ordinal numerals in Ukrainian, reflecting the chronological sequence of human history. The word for century is **століття**, which is a neuter noun. When stating that a historical event occurred within a specific century, you must use the preposition **у** or **в** followed by the Locative case.

**у двадцять першому столітті** — *in the twenty-first century*

If you are simply naming the century as the subject of a sentence, you use the Nominative case, such as **двадцяте століття** (the twentieth century). Beyond dates, when you are structuring a logical argument or presenting a list of reasons, ordinal adverbs are your best tools for organizing the information. To list your points sequentially, use **по-перше** (firstly), **по-друге** (secondly), and **по-третє** (thirdly). These adverbs are indispensable for creating a clear flow in your analytical speech.

:::info
**Grammar box**
Remember that ordinal adverbs like **по-перше** and **по-друге** are always written with a hyphen. They are typically used as introductory words at the beginning of a sentence and must be separated from the rest of the clause by commas.
:::

Finally, ordinal numerals are a cornerstone of the formal and official registers, known in Ukrainian as the **науково-навчальний** (scientific-educational) and **офіційно-діловий** (official-business) styles. In legal documents, contracts, and academic papers, the structure of the text is meticulously numbered. Unlike casual speech where numbers might precede the noun, formal citations often place the ordinal numeral after the noun for emphasis and clarity.

**стаття перша** — *article one*
**пункт третій** — *point three*
**параграф п'ятий** — *paragraph five*
**розділ восьмий** — *chapter eight*

This inverted word order sounds highly authoritative and is the standard convention for citing specific sections of any formal text.

Згідно з правилами університету, кожен студент повинен уважно прочитати розділ восьмий навчального посібника. У цьому розділі параграф п'ятий детально пояснює процедуру складання іспитів. Якщо виникають питання, стаття перша статуту містить усі необхідні відповіді.

> *According to the university rules, every student must carefully read chapter eight of the study guide. In this chapter, paragraph five explains the examination procedure in detail. If questions arise, article one of the statute contains all the necessary answers.*

<!-- INJECT_ACTIVITY: match-up-match-ordinals-with-their-appropriate-usage-contexts -->
<!-- INJECT_ACTIVITY: error-correction-correct-the-declension-of-ordinal-numbers-in-sentences -->

## Порядкові числівники в контексті

To truly master ordinal numerals, you must see them working together in a natural environment. In everyday professional life in Ukraine, you will constantly encounter texts that are packed with dates, times, and locations. Imagine you have just received a formal email or a printed invitation to an important business meeting at a corporate office in Kyiv. This type of text is a perfect example of the **офіційно-діловий** (official-business) style. Such messages require precision, meaning that every single number—from the day of the month to the exact room number—must be expressed using the correct case. Let us read this short invitation and observe how the ordinal numerals adapt to their specific grammatical roles within the sentence.

Шановні колеги! Офіційна зустріч щодо нового проєкту відбудеться п'ятнадцятого березня о третій годині дня. Захід проходитиме в головному офісі нашої компанії. Зверніть увагу, що конференц-зал розташований на четвертому поверсі, у кімнаті двісті двадцять п'ятій. Будь ласка, не запізнюйтеся, оскільки презентація розпочнеться рівно о пів на четверту. Для реєстрації вам потрібно підійти до адміністратора, який знаходиться на першому поверсі біля головного входу. Якщо у вас виникнуть питання, ви можете зателефонувати до нашого секретаря. Чекаємо на вас і сподіваємося на плідну співпрацю!

> *Dear colleagues! The official meeting regarding the new project will take place on the fifteenth of March at three o'clock in the afternoon. The event will be held in the main office of our company. Please note that the conference hall is located on the fourth floor, in room two hundred and twenty-five. Please do not be late, as the presentation will start exactly at half past three. For registration, you need to approach the receptionist, who is located on the first floor near the main entrance. If you have any questions, you can call our secretary. We look forward to seeing you and hope for fruitful cooperation!*

Let us break down the grammar in this invitation to understand why each ordinal numeral took its specific form. The text begins with the date: **п'ятнадцятого березня** (on the fifteenth of March). Because it answers the question of when a specific event occurs on the calendar, the ordinal numeral must be in the Genitive case. Next, we see the time: **о третій годині** (at three o'clock). To indicate the exact hour an event begins, Ukrainian uses the preposition **о** followed by the Locative case. The location of the hall is described as being **на четвертому поверсі** (on the fourth floor). The preposition **на** indicating a static location requires the Locative case, and the ordinal numeral perfectly agrees with the masculine noun. Finally, the specific room is **у кімнаті двісті двадцять п'ятій** (in room two hundred and twenty-five). Here, the noun is in the Locative case after the preposition **у**. Notice that in the compound numeral, the words **двісті** and **двадцять** remain in the Nominative form, and only the last word, **п'ятій**, declines to match the feminine Locative case.

:::info
**Grammar box**
When reading long compound numerals in a text, do not let them intimidate you. Remember the golden rule: no matter how many words make up the number, only the very last word changes its case ending to agree with the noun.
:::

Now let us shift from formal written text to everyday spoken communication. One of the most common situations where you will need to actively produce ordinal numerals is when navigating the transportation system. Imagine you are at **Київський вокзал** (Kyiv Railway Station), preparing for a trip across the country. You approach the ticket window to speak with a **касир** (cashier) about buying a train ticket. In this fast-paced exchange, you must specify the exact date of your departure, confirm the platform number, and ask about the train car. Navigating a large railway station also requires asking for directions, which often involves floor numbers. Pay close attention to the cases used in this practical conversation.

> — **Пасажир:** Добрий день! Мені потрібен квиток на п'яте березня до Львова. *(Good day! I need a ticket for the fifth of March to Lviv.)*
> — **Касир:** Добрий день. Є квитки на ранковий потяг. Відправлення о восьмій годині. *(Good day. There are tickets for the morning train. Departure is at eight o'clock.)*
> — **Пасажир:** Чудово. А звідки посадка? З якого вагона починається нумерація? *(Great. And where is the boarding? From which car does the numbering start?)*
> — **Касир:** Нумерація починається з першого вагона. Ваш потяг прибуває на третій перон. *(The numbering starts from the first car. Your train arrives at the third platform.)*
> — **Пасажир:** Дякую. А де я можу роздрукувати електронний квиток? *(Thank you. And where can I print an electronic ticket?)*
> — **Касир:** На другому поверсі — каса для електронних квитків. *(On the second floor is the ticket office for electronic tickets.)*
> — **Пасажир:** Зрозумів. На п'яте березня, третій перон. Дякую за допомогу! *(Understood. For the fifth of March, the third platform. Thank you for your help!)*

In this dialogue, the grammatical roles of the ordinal numerals change rapidly depending on the context. The passenger asks for a ticket **на п'яте березня** (for the fifth of March). Because the preposition **на** here indicates a target date for the ticket, the ordinal numeral takes the Accusative case, which matches the form of the implied neuter noun. When discussing the numbering of the train cars, the cashier says **з першого вагона** (from the first car). The preposition **з** denotes origin or starting point and always dictates the Genitive case. When the cashier states that the train arrives at **третій перон** (the third platform), the phrase functions as the destination of motion; since it is an inanimate masculine noun, its Accusative form is identical to the Nominative form. Finally, to explain where the ticket office is located, the cashier uses **на другому поверсі** (on the second floor), applying the Locative case to express a static position.

<!-- INJECT_ACTIVITY: reading -->

## Підсумок

In this module, we have explored how ordinal numerals function within the Ukrainian case system. The fundamental rule to remember is that ordinal numerals decline exactly like adjectives, agreeing with the noun they modify in gender, number, and case. Most follow the hard group pattern, while «третій» is the notable exception that follows the soft group. When dealing with compound ordinal numerals, the rule simplifies significantly: only the very last word changes its form, while all preceding words remain strictly in the Nominative case. We also examined how these numerals are applied in daily life. For expressing dates, you must use the Genitive case for both the ordinal numeral and the month when answering the question «коли?» (when). However, when stating the current date with «сьогодні», the Nominative case is required. When telling time, the Locative case is necessary to specify the exact hour an event occurs, such as «о третій годині». Finally, always remember to use the preposition «за» or «до» for approaching hours, such as «за десять хвилин п'ята», and strictly avoid the incorrect construction «*без десяти».

:::tip
**Did you know?** — The stress on most ordinal numerals is fixed and does not shift when the word changes cases. Once you learn the stress pattern for the Nominative form of words like «перший» or «сьомий», you can be confident it remains exactly the same throughout the entire declension paradigm.
:::

Тепер настав час перевірити ваші знання на практиці. Виконайте ці п'ять завдань самостійно, щоб закріпити матеріал цього розділу. По-перше, провідміняйте складений числівник «двадцять п'ятий» за всіма сімома відмінками чоловічого роду. По-друге, напишіть сьогоднішню дату словами у двох різних форматах: як відповідь на запитання «яке сьогодні число?», а потім як відповідь на запитання «коли відбулася подія?». По-третє, напишіть час 3:15, 7:30 та 11:45 українською мовою, використовуючи офіційний стиль з порядковими числівниками. По-четверте, скажіть свою адресу, обов'язково вказавши правильний поверх у місцевому відмінку та номер квартири. Нарешті, назвіть три різні століття, використовуючи місцевий відмінок з прийменником «у» (наприклад, «у двадцятому столітті»).

> *Now it is time to test your knowledge in practice. Complete these five tasks independently to consolidate the material of this section. First, decline the compound numeral "twenty-fifth" through all seven cases of the masculine gender. Second, write today's date in words in two different formats: as an answer to the question "what is today's date?", and then as an answer to the question "when did the event occur?". Third, write the times 3:15, 7:30, and 11:45 in Ukrainian, using the formal style with ordinal numerals. Fourth, state your address, being sure to indicate the correct floor in the Locative case and the apartment number. Finally, name three different centuries, using the Locative case with the preposition "in" (for example, "in the twentieth century").*

Looking ahead to our next topic, we will continue our deep dive into the world of numbers by exploring quantitative expressions and their interaction with the case system. While ordinal numerals elegantly align with adjective rules, cardinal numerals—the numbers used for counting quantities like "one", "two", or "five"—have their own unique and sometimes surprising demands on the nouns that follow them. You will learn the crucial difference between how the numbers "two", "three", and "four" dictate the Nominative plural, while numbers "five" and above require the Genitive plural. Understanding these foundational rules for quantitative expressions will allow you to confidently count objects, discuss amounts, and build complex sentences without hesitation.
</generated_module_content>

**PIPELINE NOTE — Word count: 5780 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 676 words | Not found: 3 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Києва — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ конференц — NOT IN VESUM

All 676 other words are confirmed to exist in VESUM.

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
