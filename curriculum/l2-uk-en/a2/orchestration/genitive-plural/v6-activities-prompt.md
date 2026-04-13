<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-plural.yaml` file for module **14: Багато книг, мало студентів** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-masculine -->`
- `<!-- INJECT_ACTIVITY: quiz-genitive-endings -->`
- `<!-- INJECT_ACTIVITY: group-sort-endings -->`
- `<!-- INJECT_ACTIVITY: fill-in-all-genders -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the Genitive plural of given nouns (all three genders)
  items: 8
  type: fill-in
- focus: Choose the correct Genitive plural ending (-ів, -ей, zero, or -їв)
  items: 8
  type: quiz
- focus: Match Nominative singular nouns to their Genitive plural forms
  items: 8
  type: match-up
- focus: Sort Genitive plural forms by ending type (-ів/-їв vs. zero vs. -ей)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- чоловічий рід (masculine gender)
- жіночий рід (feminine gender)
- середній рід (neuter gender)
- виняток (exception)
- вставний голосний (inserted vowel)
required:
- множина (plural)
- нульове закінчення (zero ending)
- кілька (a few, several)
- багато (a lot, many)
- мало (a little, few)
- скільки (how many)
- людина (person) / люди (people)
- стаття (article)
- завдання (task, assignment)
- питання (question)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чоловічий рід: -ів та нульове закінчення (~720 words)

Welcome to the most complex form of the Ukrainian noun: the Genitive plural. We use this case constantly when we talk about quantities. Numbers from five and above require the Genitive plural. We also use this form after the question word **скільки** (how many) and words denoting quantity, such as **багато** (a lot, many), **мало** (a little, few), and **кілька** (a few, several).

Сьогодні ми вивчаємо родовий відмінок. Це **множина** іменників. Коли ми рахуємо **людей** або предмети, нам потрібна ця форма. Якщо ви маєте п'ять або десять предметів, ви змінюєте слово. Ми також використовуємо цю форму після слова **скільки**. Коли предметів **багато**, **мало** або є лише **кілька**, ми змінюємо закінчення.

> *Today we are studying the Genitive case. This is the **plural** of nouns. When we count **people** or objects, we need this form. If you have five or ten items, you change the word. We also use this form after the word **how many**. When there are **a lot**, **a little**, or just **a few** objects, we change the ending.*

The dominant pattern for masculine nouns in the Genitive plural is the **-ів** ending. Most hard-stem masculine nouns simply add this ending to the base form. If a word ends in a hard consonant, you will almost always use this pattern. Let us look at some everyday words.

У нас є один стіл, але в кімнаті стоїть п'ять столів. Мій сусід має три брати, а я маю п'ять братів. Наш університет приймає багато студентів. На цій вулиці побудували кілька нових будинків. Там є дуже багато підручників для школи.

> *We have one desk, but there are five desks in the room. My neighbor has three brothers, and I have five brothers. Our university accepts many students. They built several new houses on this street. There are very many textbooks for school there.*

Words like `стіл` (desk) become `столів`, and `студент` (student) becomes `студентів`. This is the most reliable rule for masculine nouns.

:::note
**Quick tip** — Notice how the vowel **і** in the root of `стіл` changes back to **о** in the Genitive plural form `столів`. This is a common vowel alternation in Ukrainian.
:::

You might expect soft-stem masculine nouns to have a different ending, but they predominantly take the **-ів** ending as well. When a masculine noun ends in a soft sign, you drop the soft sign and add the ending. This highly productive ending distinguishes Ukrainian from other Slavic languages.

У школі працює багато хороших учителів. Мій син купив десять олівців для малювання. Скільки вчителів працює у вашій школі? У мене залишилося мало олівців. Ми поважаємо наших учителів.

> *Many good teachers work in the school. My son bought ten pencils for drawing. How many teachers work in your school? I have few pencils left. We respect our teachers.*

The word `учитель` (teacher) transforms into `учителів`, and `олівець` (pencil) becomes `олівців`. The soft sign disappears because the **-і-** naturally softens the preceding consonant.

There is a spelling variant of this ending: **-їв**. True **-їв** appears only after stems that end in a vowel or an apostrophe. Despite this spelling variation, remember that most soft masculine nouns take **-ів**, not **-їв**.

У центрі міста є багато гарних подвір'їв. Цей рік приніс нам кілька відкриттів. Ми пам'ятаємо імена наших героїв. На зупинці стояло п'ять нових трамваїв. Після дощу на вулиці немає трамваїв.

> *There are many beautiful courtyards in the city center. This year brought us several discoveries. We remember the names of our heroes. Five new trams stood at the stop. After the rain, there are no trams on the street.*

The noun `герой` (hero) becomes `героїв`, and `трамвай` (tram) becomes `трамваїв`. Some neuter nouns follow this pattern too, such as `подвір'я` (courtyard) becoming `подвір'їв`, and `відкриття` (discovery) becoming `відкриттів`. The letter **ї** represents the sound after vowels and apostrophes.

Watch out for fleeting vowels. Many masculine nouns have an **о** or **е** in their final syllable. When we add the **-ів** ending, these vowels often drop out of the word completely.

Один тиждень має сім днів. У класі вчиться багато розумних хлопців. Скільки днів ви будете у Києві? На стадіоні ми бачили кілька молодих хлопців.

> *One week has seven days. Many smart boys study in the class. How many days will you be in Kyiv? At the stadium, we saw a few young boys.*

The word `день` (day) loses its **е** and becomes `днів`. The word `хлопець` (boy) also loses its **е** and becomes `хлопців`. Practice recognizing these stem changes.

Finally, there is a rare **нульове закінчення** (zero ending) for a specific group of masculine nouns. Nouns denoting people that end in **-ин** or **-їн** lose this suffix in the plural. When forming the Genitive plural, they take a zero ending.

На площі зібралося багато громадян. У цьому селі живе кілька працьовитих селян. На конференцію приїхало п'ять болгар. У кімнаті сиділо десять чоловік.

> *Many citizens gathered on the square. A few hardworking villagers live in this village. Five Bulgarians came to the conference. Ten men sat in the room.*

Thus, `громадянин` (citizen) becomes `громадян`, `селянин` (villager) becomes `селян`, and `болгарин` (Bulgarian) becomes `болгар`. The word `чоловік` (man) has parallel forms: `п'ять чоловік` or `п'ять чоловіків`. Most masculine nouns, however, take the **-ів** ending.

Тепер ви знаєте основні правила для чоловічого роду. Перевірте свої знання та зробіть наступну вправу дуже уважно.

<!-- INJECT_ACTIVITY: match-up-masculine --> [match-up, Match Nominative singular nouns to their Genitive plural forms, 8 items]

## Жіночий рід: нульове закінчення (~770 words)

Feminine nouns have special rules for the Genitive plural. Listen to this conversation between a seller and his assistant counting inventory.

> — **Продавець:** Скільки пляшок води залишилося на полиці? *(How many bottles of water are left on the shelf?)*
> — **Помічник:** П'ять. А ще там є багато соку. *(Five. And there is also a lot of juice there.)*
> — **Продавець:** Добре. А скільки банок меду у нас є? *(Good. And how many jars of honey do we have?)*
> — **Помічник:** Тільки три. Нам треба замовити ще. *(Only three. We need to order more.)*
> — **Продавець:** Згоден. А булок? Скільки свіжих булок? *(Agreed. And buns? How many fresh buns?)*
> — **Помічник:** Немає булок! Усі продали вранці. *(No buns! We sold all of them in the morning.)*
> — **Продавець:** Зрозуміло. Тоді запиши: вода, мед і багато булок. *(Understood. Then write it down: water, honey, and a lot of buns.)*

In the dialogue, counting feminine nouns like "пляшка" (bottle) or "банка" (jar) with numbers from five upwards requires the Genitive **множина** (plural). The primary pattern is the **нульове закінчення** (zero ending). You drop the final **-а** from hard-stem nouns, leaving no ending. For example, "книга" (book) becomes "книг", and "жінка" (woman) becomes "жінок".

У нашому місті є багато нових бібліотек і цікавих книг. Після роботи я зустрів кілька знайомих жінок біля метро. У мене є дві сестри, і сьогодні я чекаю в гості своїх сестер. Ми купили десять великих пляшок чистої води для свята. На столі у кухні стояло п'ять банок домашнього меду. У пекарні ми взяли кілька свіжих булок.

> *In our city, there are many new libraries and interesting books. After work, I met a few familiar women near the subway. I have two sisters, and today I am expecting my sisters as guests. We bought ten large bottles of clean water for the holiday. Five jars of homemade honey stood on the table in the kitchen. In the bakery, we took a few fresh buns.*

When dropping the final **-а** leaves a difficult consonant cluster, Ukrainian inserts a vowel to make pronunciation fluid. We insert **о** after hard consonants, and **е** after soft consonants or hissing sounds. This is very useful when asking **скільки** (how many) items are left. Dropping **-а** from "студентка" (female student) leaves "студентк", so we insert **о** to get "студенток". Similarly, "зупинка" (bus stop) becomes "зупинок".

:::info
**Вставний голосний** (Inserted vowel)
Whenever dropping a final vowel creates an awkward consonant sequence (like *-тк*, *-нк*, *-мк*), Ukrainian adds **о** або **е** to break it up.
:::

> — **Анна:** Скільки автобусних зупинок до центру міста?
> — **Максим:** Здається, п'ять зупинок. А чому ти питаєш?
> — **Анна:** Там є великий магазин сумок. Я хочу купити подарунок для мами.
> — **Максим:** Так, там дійсно багато магазинів. І продають дуже багато красивих сумок.
> — **Анна:** Чудово! Сподіваюся, там сьогодні мало людей.
> — **Максим:** Сьогодні середа, тому людей буде небагато.
> — **Анна:** А які сумки там є?
> — **Максим:** Там є багато червоних, чорних і білих сумок.
> — **Анна:** Супер. Мені треба дві сумки.

В університеті навчається багато розумних студенток із різних країн. На цій довгій вулиці є п'ять автобусних зупинок. У новому магазині продають кілька стильних шкіряних сумок. Ми бачили багато красивих українок на святковому концерті. На столі лежить кілька нових кольорових ручок для малювання.

> *Many smart female students from different countries study at the university. There are five bus stops on this long street. The new store sells several stylish leather bags. We saw many beautiful Ukrainian women at the festive concert. There are a few new colored pens for drawing lying on the table.*

Soft-stem feminine nouns typically end in **-я**. They take a zero ending but leave a soft sign (**ь**) to preserve softness. You will often use these forms when describing **кілька** (a few, several) objects. Dropping **-я** from "пісня" (song) requires an inserted **е** and a soft sign, making "пісень". For nouns ending in **-ія**, the **-я** drops and the **і** changes to **й**. Thus, "станція" (station) becomes "станцій".

Наш місцевий хор знає дуже багато старих народних пісень. У бабусиному саду росте кілька великих вишень і яблунь. У цьому промисловому місті є п'ять залізничних станцій. Сьогодні студенти уважно слухали дві лекції з історії. Завтра у студентів немає лекцій, тому вони відпочивають. На столі стоїть кілька нових фотографій. Скільки цікавих історій ти знаєш?

> *Our local choir knows a lot of old folk songs. A few large cherry and apple trees grow in grandmother's garden. There are five railway stations in this industrial city. Today the students listened carefully to two history lectures. Tomorrow the students have no lectures, so they are resting. A few new photographs stand on the table. How many interesting stories do you know?*

Feminine nouns ending in a hissing consonant (**ж**, **ч**, **ш**, **щ**) take a pure zero ending without inserted vowels or soft signs. Just remove the final **-а**. You will use this pattern when you see **багато** (a lot, many) objects. The word "площа" (square) becomes "площ", and "задача" (task) becomes "задач".

У центрі нашої столиці є кілька дуже красивих площ. На уроці математики ми разом вирішили десять складних задач. Під час літньої подорожі ми бачили багато старих кам'яних веж. У цьому густому лісі дуже мало лісових хащ. Біля нашої річки є багато високих круч. Увечері на вулицях міста завжди багато великих калюж після дощу. У цій старій книзі є багато цікавих задач.

A small group of first-declension soft-stem nouns takes the **-ей** ending instead of a zero ending. The noun **стаття** (article) changes to "статей", and "сім'я" (family) becomes "сімей". Another key word is **людина** (person). While the plural is **люди** (people), its Genitive plural is "людей".

> — **Студент:** Вибачте, Олено Іванівно, у мене є кілька питань про наше нове завдання.
> — **Викладач:** Звичайно, Максиме. Слухаю вас. Скільки статей вам треба прочитати до п'ятниці?
> — **Студент:** Ви сказали прочитати п'ять статей. Але в бібліотеці дуже мало вільних комп'ютерів. Там постійно працює багато студенток і студентів.
> — **Викладач:** Так, зараз кінець семестру. Там зазвичай багато людей. Але ви можете читати ці тексти вдома.
> — **Студент:** Я розумію. А скільки сторінок у кожній статті?
> — **Викладач:** Близько десяти сторінок. Це небагато.
> — **Студент:** Добре. А на іспиті буде багато складних задач?
> — **Викладач:** Ні, на іспиті буде тільки п'ять задач і кілька відкритих питань.
> — **Студент:** Дякую! Тепер я маю менше питань. Піду читати.
> — **Викладач:** Бажаю успіху. У вас є ще п'ять днів.
> — **Студент:** Так, часу ще багато. До побачення!
> — **Викладач:** До зустрічі на лекції!

Finally, you will frequently combine these forms with quantity words like **мало** (a little, few). Soon, you will also learn that neuter nouns use zero endings too, such as **завдання** (task, assignment) becoming "завдань", and **питання** (question) becoming "питань".

Відомий журналіст написав п'ять нових статей про сучасну економіку. У нашому великому будинку живе кілька молодих сімей. У старому темному підвалі ми несподівано побачили багато маленьких мишей. Скільки цікавих людей прийшло на цей вечірній концерт? Учора на головній площі було дуже мало людей через сильний дощ. Учитель дав нам нове завдання, і тепер ми маємо багато складних питань.

> *The famous journalist wrote five new articles about the modern economy. Several young families live in our large building. In the old dark basement, we unexpectedly saw many small mice. How many interesting people came to this evening concert? Yesterday there were very few people on the main square because of the heavy rain. The teacher gave us a new task, and now we have many difficult questions.*

<!-- INJECT_ACTIVITY: quiz-genitive-endings --> [quiz, Choose the correct Genitive plural ending (-ів, -ей, zero, or -їв), 8 items]

## Середній рід та узагальнення (~700 words)

Neuter nouns with hard stems ending in **-о** behave very much like feminine nouns. When forming the **множина** (plural), you simply drop the final vowel. This leaves them with a **нульове закінчення** (zero ending). Just as with feminine words, dropping the vowel sometimes creates a cluster of consonants that is hard to pronounce, so an extra vowel is inserted. For example, «вікно» becomes «вікон» and «місто» becomes «міст». If the stem has an «о» before the ending, it often changes to «і», so «слово» becomes «слів».

У цьому старому будинку немає нових вікон. Микола знає багато українських слів. У Європі є дуже багато красивих міст. На столі лежить кілька яблук. Після свята у нас залишилося мало смачних тістечок.

> *There are no new windows in this old building. Mykola knows many Ukrainian words. There are very many beautiful cities in Europe. There are a few apples lying on the table. After the holiday, we have few tasty cakes left.*

:::info
**Grammar box**
When a neuter noun drops its **-о**, watch out for vowel insertion. The word «вікно» naturally turns into «вікон» to avoid the awkward «вікн» sound at the end.
:::

Soft neuter nouns ending in **-е** are full of surprises. Instead of taking a zero ending, they borrow the masculine pattern and take the **-ів** ending. For instance, «море» becomes «морів», and «поле» becomes «полів». However, neuter nouns ending in **-ння** take a zero ending plus a soft sign, and they drop their double consonant. Therefore, **завдання** (task, assignment) becomes «завдань», and **питання** (question) becomes «питань».

Студенти мають багато складних завдань. У мене є кілька важливих питань до викладача. Географи досліджують екологію південних морів. В Україні є багато широких полів. Учитель дав нам декілька нових завдань на завтра.

> *Students have many difficult tasks. I have a few important questions for the teacher. Geographers study the ecology of southern seas. There are many wide fields in Ukraine. The teacher gave us several new tasks for tomorrow.*

Neuter nouns ending in **-тя** and words for young animals belong to a special declension group. They undergo unique stem changes when they form the plural. The word **ім'я** (name) changes its stem entirely to become «імен». Words for baby animals keep their special plural suffixes. For example, «теля» becomes «телят», and «кошеня» becomes «кошенят».

На фермі мого дідуся є п'ять маленьких телят. Я не пам'ятаю імен цих нових студентів. У нашому дворі грається багато смішних кошенят. Фермер годує десять голодних телят.

> *There are five small calves on my grandfather's farm. I do not remember the names of these new students. Many funny kittens are playing in our yard. The farmer is feeding ten hungry calves.*

To understand the big picture, let us review the main patterns for all genders. Most masculine nouns take the **-ів** ending, though a few exceptions take a zero ending. Most feminine nouns take a zero ending, often with an inserted vowel or a soft sign. A few feminine exceptions take **-ей**, so **стаття** (article) becomes «статей». Most neuter nouns also take a zero ending, but those ending in **-е** take **-ів**. Additionally, a small closed group of masculine and neuter nouns takes a true **-ей** ending, so «кінь» becomes «коней», and «око» becomes «очей».

| Рід | Основне закінчення | Приклади | Винятки |
| :--- | :--- | :--- | :--- |
| Чоловічий | **-ів** | студентів, столів, братів | громадян (нульове), гостей (**-ей**) |
| Жіночий | **нульове закінчення** | книг, жінок, сестер, пісень | статей (**-ей**), сімей (**-ей**) |
| Середній | **нульове закінчення** | міст, слів, завдань, питань | морів (**-ів**), очей (**-ей**) |

Now we can confidently use quantity words with nouns of all genders. Whenever you use words like **багато** (a lot, many), **кілька** (a few, several), or **мало** (a little, few), you must use the Genitive plural. These expressions are incredibly common in everyday conversations.

The same rule applies when you ask **скільки** (how many). It also applies to the word **людина** (person). Remember that its plural is **люди** (people), which becomes «людей» in the Genitive plural. You will use this specific form almost every day.

> — **Оксана:** Скільки людей живе у твоєму місті? *(How many people live in your city?)*
> — **Марко:** У нас живе близько ста тисяч людей. *(About a hundred thousand people live in our city.)*
> — **Оксана:** Це досить багато. А скільки шкіл і лікарень є у місті? *(That is quite a lot. And how many schools and hospitals are in the city?)*
> — **Марко:** Є десять шкіл і три лікарні. *(There are ten schools and three hospitals.)*
> — **Оксана:** Я бачу, що тут також є кілька нових площ. *(I see that there are also a few new squares here.)*
> — **Марко:** Так, але старих будівель дуже мало. *(Yes, but there are very few old buildings.)*

:::tip
**Did you know?**
The word «люди» is highly irregular. After numbers 5 and higher, or after quantity words, you must always use the form «людей» (багато людей, скільки людей).
:::

The Genitive plural has the most variation of any case in Ukrainian. While it seems like a lot to remember, the key is to learn the main patterns first. Start by mastering **-ів** for masculine nouns and a zero ending for feminine and neuter nouns. Memorize common exceptions individually. With practice, you will start to intuitively hear which ending sounds right.

<!-- INJECT_ACTIVITY: group-sort-endings -->
<!-- INJECT_ACTIVITY: fill-in-all-genders -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-plural
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

**Level: A2 (Module 14/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень


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
