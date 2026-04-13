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
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: match-up-match-ordinals-with-their-appropriate-usage-contexts -->`
- `<!-- INJECT_ACTIVITY: error-correction-correct-the-declension-of-ordinal-numbers-in-sentences -->`
- `<!-- INJECT_ACTIVITY: reading -->`

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

Ordinal numerals are an essential part of the Ukrainian language, allowing you to express the order or sequence of items, people, and events. Whenever you need to answer the question about which one in a sequence you are referring to, you will use these specific numbers. They are fundamentally different from cardinal numerals, which only express the total quantity.

В українській мові порядкові числівники завжди відповідають на питання «котрий?», «котра?», «котре?» або «котрі?». Вони вказують на порядок предметів при лічбі і є дуже важливими для правильного спілкування. Головне правило, яке вам потрібно запам'ятати, полягає в тому, що всі порядкові числівники поводяться абсолютно так само, як звичайні прикметники.

> *In the Ukrainian language, ordinal numerals always answer the questions "which one?" (masculine, feminine, neuter, or plural). They indicate the order of items when counting and are very important for correct communication. As outlined in Литвінова Grade 6 (p. 237), the main rule you need to remember is that all ordinal numerals behave exactly like regular adjectives.*

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

As you progress in Ukrainian, you will naturally encounter larger numbers, leading to compound ordinal numerals. These are numerals consisting of two or more words, such as twenty-third or one hundred fifteenth. According to Заболотний Grade 6 (p. 179), the grammatical rule for compound ordinal numerals is remarkably simple and elegant: ONLY the absolute last word in the sequence declines. All preceding words remain frozen in their standard nominative cardinal form.

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

In Ukrainian, when you want to ask "At what time?" you say «О котрій годині?». As explained in Авраменко Grade 11 (p. 42), to answer this question for full hours, you must use the preposition «о» (or «об» before a vowel sound) followed by an ordinal numeral in the Locative case (Місцевий відмінок). The word for hour, «година», also takes the Locative case, becoming «годині». Because you are specifying a point in a sequence, you use ordinals like "first" or "second" rather than cardinal numbers. This means that to say "at one o'clock", you literally say "at the first hour".

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

Finally, as highlighted in Авраменко Grade 7 (p. 63) regarding numeral usage in the formal register, ordinal numerals are a cornerstone of the **науково-навчальний** (scientific-educational) and **офіційно-діловий** (official-business) styles. In legal documents, contracts, and academic papers, the structure of the text is meticulously numbered. Unlike casual speech where numbers might precede the noun, formal citations often place the ordinal numeral after the noun for emphasis and clarity.

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

This same flexibility applies to making professional appointments:

> — **Клієнт:** Коли вам зручно? Може, двадцять першого? *(When is it convenient for you? Maybe on the twenty-first?)*
> — **Менеджер:** О котрій годині? О пів на другу? *(At what time? At half past one?)*
> — **Клієнт:** Добре, на якому поверсі ваш офіс? *(Good, on which floor is your office?)*

For a quick self-check on historical dates, remember that Independence Day is 24 серпня 1991. Now try writing Constitution Day: 28 червня 1996 (Конституція). It is written as «двадцять восьмого червня тисяча дев'ятсот дев'яносто шостого року».

<!-- INJECT_ACTIVITY: reading -->

## Підсумок

In this module, we have explored how ordinal numerals function within the Ukrainian case system. The fundamental rule to remember is that ordinal numerals decline exactly like adjectives, agreeing with the noun they modify in gender, number, and case. Most follow the hard group pattern, while «третій» is the notable exception that follows the soft group. When dealing with compound ordinal numerals, the rule simplifies significantly: only the very last word changes its form, while all preceding words remain strictly in the Nominative case. We also examined how these numerals are applied in daily life. For expressing dates, you must use the Genitive case for both the ordinal numeral and the month when answering the question «коли?» (when). However, when stating the current date with «сьогодні», the Nominative case is required. When telling time, the Locative case is necessary to specify the exact hour an event occurs, such as «о третій годині». Finally, always remember to use the preposition «за» or «до» for approaching hours, such as «за десять хвилин п'ята», and strictly avoid the incorrect construction «*без десяти».

:::tip
**Did you know?** — The stress on most ordinal numerals is fixed and does not shift when the word changes cases. Once you learn the stress pattern for the Nominative form of words like «перший» or «сьомий», you can be confident it remains exactly the same throughout the entire declension paradigm.
:::

Тепер настав час перевірити ваші знання на практиці. Виконайте ці п'ять завдань самостійно, щоб закріпити матеріал цього розділу. По-перше, провідміняйте складений числівник «двадцять п'ятий» за всіма сімома відмінками чоловічого роду. По-друге, напишіть сьогоднішню дату словами у двох різних форматах: як відповідь на запитання «яке сьогодні число?», а потім як відповідь на запитання «коли відбулася подія?». По-третє, напишіть час 3:15, 7:30 та 11:45 українською мовою, використовуючи офіційний стиль з порядковими числівниками. По-четверте, скажіть свою адресу, обов'язково вказавши правильний поверх у місцевому відмінку та номер квартири. Нарешті, назвіть три різні століття, використовуючи місцевий відмінок з прийменником «у» (наприклад, «у двадцятому столітті»).

> *Now it is time to test your knowledge in practice. Complete these five tasks independently to consolidate the material of this section. First, decline the compound numeral "twenty-fifth" through all seven cases of the masculine gender. Second, write today's date in words in two different formats: as an answer to the question "what is today's date?", and then as an answer to the question "when did the event occur?". Third, write the times 3:15, 7:30, and 11:45 in Ukrainian, using the formal style with ordinal numerals. Fourth, state your address, being sure to indicate the correct floor in the Locative case and the apartment number. Finally, name three different centuries, using the Locative case with the preposition "in" (for example, "in the twentieth century").*

Looking ahead to our next topic, we will continue our deep dive into the world of numbers by exploring quantitative expressions and their interaction with the case system. While ordinal numerals elegantly align with adjective rules, cardinal numerals—the numbers used for counting quantities like "one", "two", or "five"—have their own unique and sometimes surprising demands on the nouns that follow them. You will learn the crucial difference between how the numbers "two", "three", and "four" dictate the Nominative plural, while numbers "five" and above require the Genitive plural. Understanding these foundational rules for quantitative expressions will allow you to confidently count objects, discuss amounts, and build complex sentences without hesitation.
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
