<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-dates-numbers.yaml` file for module **6: Скільки? Котра година? Яке число?** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-what-s-the-date-drill -->`
- `<!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->`
- `<!-- INJECT_ACTIVITY: match-up-accusative-genitive-negation -->`
- `<!-- INJECT_ACTIVITY: match-up-qa-quantities-dates -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: What's the Date? (Drill)
  items: 8
  type: quiz
- focus: Counting Objects (1, 2-4, 5+ Rule)
  items: 8
  type: fill-in
- focus: Accusative to Genitive Negation
  items: 8
  type: match-up
- focus: Q&A about quantities and dates
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- числівник (numeral)
- додаток (object (grammatical))
- правило (rule)
required:
- число (дата) (date)
- місяць (month)
- січень (січня) (January)
- лютий (лютого) (February)
- березень (березня) (March)
- квітень (квітня) (April)
- травень (травня) (May)
- червень (червня) (June)
- липень (липня) (July)
- серпень (серпня) (August)
- вересень (вересня) (September)
- жовтень (жовтня) (October)
- листопад (листопада) (November)
- грудень (грудня) (December)
- заперечення (negation)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Яке сьогодні число? Родовий з датами (What's the Date? Genitive with Dates) (~550 words)

Dates and numbers are essential for everyday tasks, such as making reservations, scheduling meetings, or planning vacations. Let's see how we discuss dates and quantities in a realistic setting. Imagine a common situation at a hotel reception. A guest arrives and wants to book a room for a few nights during the busy spring season. Pay attention to how the receptionist asks about specific dates and how the guest responds.

Уявіть ситуацію на рецепції готелю. Гість хоче забронювати кімнату на кілька днів.

> *Imagine a situation at a hotel reception. A guest wants to book a room for a few days.*

> — **Адміністратор:** Добрий день! З якого числа ви хочете забронювати номер? *(Good afternoon! From what date do you want to book a room?)*
> — **Гість:** Добрий день. З п'ятого березня. *(Good afternoon. From March 5th.)*
> — **Адміністратор:** До якого числа ви плануєте залишитися? *(Until what date do you plan to stay?)*
> — **Гість:** До десятого березня. *(Until March 10th.)*
> — **Адміністратор:** Скільки номерів вам потрібно? *(How many rooms do you need?)*
> — **Гість:** Нам потрібно два номери. *(We need two rooms.)*
> — **Адміністратор:** Скільки гостей буде проживати? *(How many guests will be staying?)*
> — **Гість:** П'ять гостей. *(Five guests.)*

To ask about the current **число** (date), we use the simple question «Яке сьогодні число?» (What is today's date?). When you answer this question, the grammar is split into two distinct parts. First, the day is expressed as an ordinal numeral in the neuter gender, such as the Ukrainian words for first, second, or third. This happens because the numeral must grammatically agree with the hidden neuter noun «число». Second, the **місяць** (month) is added. The month always takes the Genitive singular form to indicate a day of that specific month.

Сьогодні перше січня. Завтра буде друге лютого. Післязавтра — третє березня. Моє улюблене число — двадцять п'яте грудня.

> *Today is January 1st. Tomorrow will be February 2nd. The day after tomorrow is March 3rd. My favorite date is December 25th.*

All twelve months in Ukrainian are masculine nouns, and learning their Genitive forms is absolutely essential for daily conversation. Most of them end in a soft consonant, so they naturally take the standard **-я** ending in the Genitive case. Here is the complete calendar breakdown:

| Називний відмінок (Nominative) | Родовий відмінок (Genitive) |
| :--- | :--- |
| **січень** (January) | **січня** |
| **лютий** (February) | **лютого** |
| **березень** (March) | **березня** |
| **квітень** (April) | **квітня** |
| **травень** (May) | **травня** |
| **червень** (June) | **червня** |
| **липень** (July) | **липня** |
| **серпень** (August) | **серпня** |
| **вересень** (September) | **вересня** |
| **жовтень** (October) | **жовтня** |
| **листопад** (November) | **листопада** |
| **грудень** (December) | **грудня** |

There are only two exceptions among the months. The word **листопад** has a hard ending, so it takes the **-а** ending, making its Genitive form **листопада**. Finally, the word **лютий** is entirely unique because it declines like an adjective, taking the adjectival ending to become **лютого**.

:::note
**Quick tip** — Ukrainian month names reflect nature and the changing seasons. For example, «листопад» literally means "falling leaves," «квітень» comes from the word for "flower," and «лютий» describes the "fierce" cold of winter.
:::

When you want to say exactly when an event happens, you must answer the questions «Коли?» (When?) or «Якого числа?» (On what date?). This is fundamentally different from just stating today's date. In this situation, the grammar changes to show that an action occurs *on* a specific day. The day becomes an ordinal numeral in the masculine Genitive case, taking endings like **-ого**. The month remains in the Genitive case just like before. The complete structure is always an ordinal numeral in the masculine Genitive plus the month in the Genitive.

Ми зустрічаємося першого січня.
Концерт відбудеться п'ятого квітня.
Свято буде двадцять четвертого серпня.
Я починаю нову роботу сьомого вересня.

> *We are meeting on January 1st.*
> *The concert will take place on April 5th.*
> *The holiday will be on August 24th.*
> *I am starting a new job on September 7th.*

Let's look at how we talk about important historical dates, cultural events, and personal birthdays in Ukrainian. The Genitive case is always used for both the day and the month when discussing when a specific event took place or will take place. Historical texts, news broadcasts, and everyday conversations rely heavily on this grammatical structure.

Тарас Шевченко народився дев'ятого березня.
Прийнято Акт проголошення незалежності України двадцять четвертого серпня.
Моя старша сестра народилася п'ятого жовтня, а мій брат — другого листопада.
Новий рік починається першого січня, а Різдво ми святкуємо двадцять п'ятого грудня.

> *Taras Shevchenko was born on March 9th.*
> *The Act of Declaration of Independence of Ukraine was adopted on August 24th.*
> *My older sister was born on October 5th, and my brother on November 2nd.*
> *The New Year begins on January 1st, and we celebrate Christmas on December 25th.*

### Читаємо українською (Reading Practice)

Сьогодні десяте жовтня. Моя подруга Олена планує велику вечірку. Її день народження буде п'ятнадцятого жовтня. Вона запросила двадцять гостей. Я купила квиток на швидкісний поїзд до Києва. Мій поїзд відправляється чотирнадцятого жовтня о дев'ятій годині ранку. Я буду там вчасно.

> *Today is October 10th. My friend Olena is planning a big party. Her birthday will be on October 15th. She invited twenty guests. I bought a ticket for the high-speed train to Kyiv. My train departs on October 14th at nine o'clock in the morning. I will be there on time.*

<!-- INJECT_ACTIVITY: quiz-what-s-the-date-drill -->

## Рахуємо предмети: правило '1, 2-4, 5+' (Counting Items: The '1, 2-4, 5+' Rule) (~900 words)

Counting objects in Ukrainian is completely different from English. In English, the rule is simple: one item uses the singular noun, and any number greater than one uses the plural. One table, two tables, five tables. Ukrainian grammar, however, approaches counting with much more precision. Instead of a singular-plural binary, Ukrainian uses a specific framework we can call the "1, 2-4, 5+" rule. This rule dictates that the grammatical case and number of the noun change entirely depending on the final digit of the number you are using. To speak correctly, you must always look at the last number in the sequence. It is this final digit that strictly determines the grammatical ending of the following noun.

Let us start with the simplest category: the number one, along with any compound numbers ending in one, like twenty-one or fifty-one. The only exception is the number eleven, which follows different rules. Whenever you use a number ending in one, the following noun must be in the Nominative Singular case. This is exactly how you find the word in a dictionary. However, the numeral "один" itself must change to agree with the gender of the noun. You must choose "один" for masculine, "одна" for feminine, and "одне" for neuter nouns.

Я маю один великий стіл у новій кімнаті. Вона купила двадцять один квиток на вечірній концерт. На полиці лежить одна дуже цікава книга. У цьому будинку є тільки одне маленьке вікно. Сорок один студент успішно написав складний тест.

> *I have one large table in the new room. She bought twenty-one tickets to the evening concert. One very interesting book is lying on the shelf. In this house there is only one small window. Forty-one students successfully wrote the difficult test.*

Now we move to the second category, which covers the numbers two, three, and four. This rule also applies to compound numbers ending in these digits, such as twenty-two or thirty-four. The primary exceptions are the teen numbers: twelve, thirteen, and fourteen. Whenever your quantity ends in a two, three, or four, the following noun must take the Nominative Plural form. Furthermore, you must pay close attention to the number two. While "три" and "чотири" stay the same for all genders, the number two has distinct forms. You must use "два" for masculine and neuter nouns, but you absolutely must use "дві" for feminine nouns. This distinction is very important.

У кав'ярні стоять два круглі столи і три м'які крісла. Ми чекали чотири довгі **місяці** на цю зустріч. Я уважно прочитала дві нові книги за вихідні. Вона має три дуже розумні старші сестри. У цій кімнаті є два великі вікна і чотири двері.

> *In the cafe stand two round tables and three soft armchairs. We waited four long months for this meeting. I carefully read two new books over the weekend. She has three very smart older sisters. In this room there are two large windows and four doors.*

The final and largest category encompasses the numbers from five to twenty, and all numbers ending in five through nine, and zero. Crucially, this includes indefinite quantities like "багато" (many) and the question word "скільки" (how many). Whenever you use these numbers, the following noun must be put into the Genitive Plural case. This requirement might seem strange, but it makes sense historically. In ancient times, numbers from five upwards were considered nouns themselves, meaning "a group of five." Therefore, they naturally required the following noun to be in the genitive case to show possession, translating to "a group of five of tables." This structure has survived into modern Ukrainian.

:::info
**Grammar box** — The Genitive Plural can be a particularly tricky form to master because it often involves completely dropping the final vowel of a feminine or neuter word, leaving what we call a zero ending, or adding **-ів** for most masculine words.
:::

Сьогодні в нашому офісі працюють п'ять нових менеджерів. Вони купили на ринку десять свіжих яблук і шість бананів. Скільки дійсно цікавих книг ти маєш удома? На цій вулиці стоїть двадцять великих автомобілів. Ми бачили багато красивих міст під час подорожі.

> *Today five new managers are working in our office. They bought ten fresh apples and six bananas at the market. How many truly interesting books do you have at home? Twenty large cars are parked on this street. We saw many beautiful cities during the trip.*

You must carefully pay attention to feminine nouns when applying these counting rules, as their forms can cause confusion. For many feminine words ending in **-а**, the Nominative Plural and the Genitive Singular look identical, typically ending in **-и**. For example, the word "сестра" becomes "сестри" in both cases. However, when you count five or more, you must use the Genitive Plural. For most feminine nouns, this means utilizing a zero ending, where the final **-а** disappears entirely. Sometimes, an inserted vowel like **-е-** або **-о-** appears between the final consonants to make pronunciation easier. You must deliberately contrast these forms.

Мої дві веселі сестри зараз живуть у Києві. Його п'ять дорослих сестер живуть у центрі Львова. На столі лежать три старі історичні книги. У нашій бібліотеці є тисяча нових книг.

> *My two cheerful sisters currently live in Kyiv. His five adult sisters live in the center of Lviv. Three old historical books are lying on the table. In our library there are a thousand new books.*

Finally, let us look at some natural, everyday examples of counting in a conversational context to solidify these fundamental rules. Notice how the ending of the noun changes based strictly on the precise quantity mentioned.

> — **Олена:** Скільки нових учнів навчається у твоєму класі? *(How many new students study in your class?)*
> — **Марко:** У нашому класі зараз навчається двадцять п'ять учнів, але працюють тільки два вчителі. *(Twenty-five students currently study in our class, but only two teachers work.)*
> — **Олена:** Оборона старого українського аеропорту безперервно тривала двісті сорок два дні. *(The defense of the old Ukrainian airport lasted continuously for two hundred and forty-two days.)*
> — **Марко:** Ми швидко купили чотири квитки на поїзд. *(We quickly bought four train tickets.)*

<!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->

## Заперечення з прямим додатком (Negation with a Direct Object) (~750 words)

When you learn a new verb, you often practice it with a direct object in the Accusative case. For example, you might say you are reading a book or buying a ticket. However, the Ukrainian language has a specific and beautiful rule for **заперечення** (negation). When you negate a transitive verb — a verb that normally takes a direct object in the Accusative case — the object often shifts into the Genitive case. Look at how the transformation works in practice.

Я зараз читаю цікаву книгу. Мій брат також читає нову книгу в кімнаті. Але наша сестра не читає книги сьогодні. Я добре розумію це правило. Мій друг зовсім не розуміє цього правила.

> *I am currently reading an interesting book. My brother is also reading a new book in the room. But our sister is not reading a book today. I understand this rule well. My friend does not understand this rule at all.*

You might wonder about the nuance and motivation behind this grammatical shift. Using the Genitive case adds a sense of emphasis and totality to the negation. It completely removes the object from the context of the action. There is a subtle difference in meaning between the two cases. Using the Accusative form in negation might imply that you did not read that specific book, but perhaps you read a different one. In contrast, using the Genitive case implies that you did not read any book at all.

Студент не зробив домашнього завдання на сьогодні. Я не бачив цього нового фільму вчора. Ми не купували квитків на вечірній поїзд. Вони не знайшли правильної відповіді на питання.

> *The student did not do the homework for today. I did not see this new movie yesterday. We did not buy tickets for the evening train. They did not find the correct answer to the question.*

:::info
**Grammar box** — Think of the Accusative case as pointing at a specific, existing target. When you switch to the Genitive in a negated sentence, you erase that target entirely. You are essentially saying, "Of this category of things, I interacted with none."
:::

Let us look at clear examples across different noun genders to demonstrate this shift. For masculine inanimate nouns, the ending typically changes to **-а** or **-у**. For feminine nouns, the ending changes to **-и** or **-і**. For neuter nouns, it changes to **-а** or **-я**.

Він має квиток на вечірній концерт. Він не має квитка на концерт. Мій друг купив нову машину. Мій друг не купив нової машини. Я добре бачу велике вікно. Я зовсім не бачу великого вікна.

> *He has a ticket to the evening concert. He does not have a ticket to the concert. My friend bought a new car. My friend did not buy a new car. I see the large window well. I do not see the large window at all.*

We must also clarify the modern conversational reality of this grammatical rule. In everyday spoken Ukrainian, it is entirely possible and common to hear the Accusative case used in simple negation. A friend on the street might say they are not drinking coffee using the Accusative form without anyone correcting them. Languages constantly evolve, and spoken language often simplifies complex rules. However, the Genitive case remains the grammatically standard, traditional, and highly frequent choice. It is expected in professional writing, formal speech, and literature. Mastering this shift elevates your Ukrainian, demonstrates a deep respect for the language's historical structure, and makes you sound remarkably natural to native speakers.

Я не п'ю каву вранці, бо я дуже поспішаю. Але мій дідусь ніколи не п'є кави. Наш гість не їсть м'яса взагалі. Ти не слухаєш сучасну музику зараз. Вона не слухає сучасної музики.

> *I do not drink coffee in the morning because I am in a great hurry. But my grandfather never drinks coffee. Our guest does not eat meat at all. You are not listening to modern music right now. She does not listen to modern music.*

We can summarize this core concept by connecting it to the absolute negation word немає (there is no). This powerful word ALWAYS requires the Genitive case, regardless of the noun's gender, animacy, or the specific context of the situation. There are no exceptions to this rule. This absolute requirement reinforces the central idea that the Genitive is the true case of absence in the Ukrainian language. Once you master this connection, applying the Genitive in other negated sentences will feel much more intuitive.

У мене немає вільного часу на ці довгі розмови. В магазині біля мого дому немає свіжого хліба. На цій старій вулиці зовсім немає дерев. У них немає жодної проблеми з цим завданням.

> *I have no free time for these long conversations. There is no fresh bread in the store near my house. There are absolutely no trees on this old street. They have no problem at all with this task.*

### Читаємо українською (Reading Practice)

To fully master this module's vocabulary, let us observe how negation and time phrases interact throughout the year. We frequently use these structures when discussing a specific **число** (date) or **місяць** (month).

Узимку ми маємо три місяці. Це **грудень**, **січень** та **лютий**. Кожен місяць має свій характер. Сьогодні двадцять п'яте грудня. Ми не маємо вільного часу взимку через свята.

> *In winter we have three months. These are **December**, **January**, and **February**. Each month has its character. Today is the twenty-fifth of December. We do not have free time in winter because of the holidays.*

Весна приносить тепло і нове життя. Починається **березень**, потім приходить **квітень**, а за ним — **травень**. Я не бачу снігу навесні. Ми завжди чекаємо на ці світлі дні.

> *Spring brings warmth and new life. **March** begins, then **April** comes, and after it — **May**. I do not see snow in spring. We always wait for these bright days.*

Літо — це час для довгого відпочинку. Наш улюблений час — це **червень**, **липень** і спекотний **серпень**. У цей час студенти не читають складних книг. Вони просто відпочивають.

> *Summer is a time for a long rest. Our favorite time is **June**, **July**, and hot **August**. During this time students do not read complex books. They simply rest.*

Осінь часто буває прохолодною. **Вересень** ще дарує тепле сонце, але **жовтень** та **листопад** приносять сильні дощі. Ми не плануємо довгих подорожей на осінь. 

> *Autumn is often cool. **September** still gives warm sun, but **October** and **November** bring strong rains. We do not plan long trips for autumn.*

:::tip
**Did you know?** — The names of the Ukrainian months are deeply connected to nature and traditional agricultural cycles. For example, листопад literally translates to "falling leaves," and серпень comes from the word for a sickle, referring to the historic harvest season.
:::

<!-- INJECT_ACTIVITY: match-up-accusative-genitive-negation -->
<!-- INJECT_ACTIVITY: match-up-qa-quantities-dates -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-dates-numbers
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**Level: A2 (Module 6/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
