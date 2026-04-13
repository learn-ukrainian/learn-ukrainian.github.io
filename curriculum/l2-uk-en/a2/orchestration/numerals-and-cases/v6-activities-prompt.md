<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/numerals-and-cases.yaml` file for module **55: Числа у відмінках** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-ordinals -->`
- `<!-- INJECT_ACTIVITY: fill-in-decline-in-context -->`
- `<!-- INJECT_ACTIVITY: quiz-noun-agreement -->`
- `<!-- INJECT_ACTIVITY: sort-numeral-cases -->`
- `<!-- INJECT_ACTIVITY: match-up-expressions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Decline ordinal numerals in context (dates, addresses)
  items: 8
  type: fill-in
- focus: Choose the correct noun form after a numeral (Nom.Pl. vs Gen.Pl.)
  items: 8
  type: quiz
- focus: Sort numerals by which noun case they require (Nom.Sg., Nom.Pl., Gen.Pl.)
  items: 8
  type: group-sort
- focus: Match numeral expressions to their correct Ukrainian form
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- обидва (both, m.)
- обидві (both, f.)
- десяток (a ten, a dozen)
- пів (half)
required:
- числівник (numeral)
- порядковий (ordinal)
- кількісний (cardinal)
- перший (first)
- третій (third)
- один (one)
- скільки (how many)
- кілограм (kilogram)
- коштувати (to cost)
- вік (age)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Порядкові числівники: -ий та -ій (Ordinal Numerals: -ий and -ій) (~600 words)

> — **Вчитель:** Увага, починаємо шкільні спортивні змагання! *(Attention, we are starting the school sports competitions!)*
> — **Учень:** Хто грає у футбол сьогодні? *(Who is playing football today?)*
> — **Вчитель:** Перша команда — десять учнів. Другий забіг о десятій годині. *(The first team is ten students. The second race is at ten o'clock.)*
> — **Учень:** У нас проблема. Одного м'яча не вистачає! *(We have a problem. One ball is missing!)*
> — **Вчитель:** Не проблема, я принесу ще один. А де нагороди? *(Not a problem, I'll bring another one. And where are the awards?)*
> — **Учень:** Ось тут. У нас є п'ять медалей для переможців. *(Right here. We have five medals for the winners.)*

В українській мові кожне число має дві форми. Ми маємо **кількісний** (cardinal) **числівник** (numeral), який відповідає на питання «**скільки**?» (how many?). Наприклад, це слова один, два або п'ять. Ми використовуємо їх, коли просто рахуємо предмети.

> *In the Ukrainian language, every number has two forms. We have a cardinal numeral, which answers the question "how many?". For example, these are the words one, two, or five. We use them when we simply count objects.*

Також ми маємо **порядковий** (ordinal) числівник. Цей числівник працює як звичайний прикметник і вказує на місце предмета при лічбі. Наприклад, ми говоримо «**перший** (first) день» для чоловічого роду та «перша команда» для жіночого роду. У множині всі роди мають однакове закінчення «-і»: «перші переможці». Ви вже добре знаєте ці правила з теми про прикметники.

Більшість порядкових числівників мають тверде закінчення **-ий**. Вони відмінюються так само, як прикметники твердої групи. Візьмемо для прикладу слово «п'ятий». У називному відмінку чоловічого роду це «п'ятий». Коли ми змінюємо відмінок, змінюється лише закінчення. У родовому відмінку ми кажемо «п'ятого», а у давальному — «п'ятому». В орудному відмінку форма буде «п'ятим», а в місцевому — «на п'ятому». Для жіночого роду початкова форма — це «п'ята». В орудному відмінку ми використовуємо форму «п'ятою».

Але є **один** (one) дуже важливий виняток. Це слово **третій** (third). Цей числівник має м'яке закінчення **-ій**. Він відмінюється як прикметник м'якої групи, тому в його формах часто з'являється м'який знак. У чоловічому роді родовий відмінок буде «третього», давальний — «третьому», а орудний — «третім». Слово «перший» має основу на шиплячий приголосний, але його закінчення здебільшого залишаються твердими («першого», «першому»).

:::info
**Grammar box**
Remember that **третій** (third) is the only truly soft ordinal numeral. All others, like **другий** (second), **четвертий** (fourth), and **п'ятий** (fifth), are hard. The numeral **перший** (first) has a stem ending in a hissing consonant, so it takes standard hard endings in most cases.
:::

Порядкові числівники дуже часто використовуються для позначення дат. Коли ми говоримо про конкретний день, ми відповідаємо на питання «коли?». Тоді ми завжди використовуємо порядковий числівник у родовому відмінку. Наприклад, ми скажемо «двадцять першого березня» або «другого квітня». У складених числівниках змінюється лише останнє слово. Погляньмо на велике число «сто сорок п'ятий». Ми скажемо: «Я щойно вийшов зі сто сорок п'ятого кабінету».

> *Ordinal numerals are very often used to indicate dates. When we talk about a specific day, we answer the question "when?". Then we always use the ordinal numeral in the genitive case. For example, we will say "the twenty-first of March" or "the second of April". In compound numerals, only the last word changes. Let's look at the large number "one hundred and forty-fifth". We will say: "I just came out of the one hundred forty-fifth office."*

<!-- INJECT_ACTIVITY: fill-in-ordinals -->

## Один/одна/одне у відмінках (One in All Cases) (~450 words)

Слово **один** (one) — це особливий **кількісний** (cardinal) **числівник** (numeral). Він працює зовсім не так, як інші числа в українській мові. Цей числівник дуже схожий на звичайний прикметник. Він має свої форми для всіх трьох родів. Наприклад, ми обов'язково кажемо «один брат» або «один стіл» для чоловічого роду. Для жіночого роду ми використовуємо форму «одна», наприклад, «одна сестра» або «одна книга». Для середнього роду правильна форма — це «одне». Наприклад, ми кажемо «одне вікно» чи «одне місто».

> *The word "один" (one) is a special cardinal numeral. It works completely differently from other numbers in the Ukrainian language. This numeral is very similar to a regular adjective. It has its own forms for all three genders. For example, we must say "один брат" or "один стіл" for the masculine gender. For the feminine gender, we use the form "одна", for example, "одна сестра" or "одна книга". For the neuter gender, the correct form is "одне". For example, we say "одне вікно" or "одне місто".*

Також це слово має унікальну форму множини — «одні». Ми використовуємо форму множини для слів, які не мають форми однини. Наприклад, ми говоримо «одні двері» (one door), «одні окуляри» (one pair of glasses) або «одні ножиці» (one pair of scissors). Він завжди узгоджується з іменником, з яким стоїть поруч.

Числівник «один» відмінюється за всіма сімома відмінками, як прикметник твердої групи. Це означає, що його закінчення будуть вам дуже знайомі. У чоловічому та середньому роді форми в непрямих відмінках повністю однакові. У родовому відмінку ми використовуємо форму «одного». Наприклад, ми можемо сказати: «На футбольному полі зараз немає одного м'яча». У давальному відмінку це буде «одному», а в орудному — «одним». У місцевому відмінку ми часто кажемо: «Ми стоїмо на одному місці». Жіночий рід має свої власні закінчення, які теж нагадують прикметники. У родовому відмінку ми найчастіше кажемо «однієї» або використовуємо коротку форму «одної». У давальному та місцевому відмінках форма буде «одній». В орудному відмінку ми використовуємо красиву форму «однією» або її короткий варіант «одною». Наприклад, ми можемо сказати: «Я вчора гуляв у парку з однією сестрою». У множині всі форми абсолютно схожі на прикметники. Форма родового відмінка — «одних», давального — «одним», а орудного — «одними».

:::info
**Grammar box**
The numeral **один** (one) declines exactly like a hard-stem adjective. It must agree with its noun in gender, number, and case. Note the alternative forms for the feminine gender: you can use either *однієї* or *одної* in the Genitive case, and *однією* or *одною* in the Instrumental case. Both variants are correct and widely used in modern Ukrainian.
:::

Цікаво, що слово «один» має також багато інших значень у щоденному спілкуванні. Ми використовуємо його не тільки тоді, коли рахуємо предмети чи людей. Дуже часто це слово означає «якийсь» або «певний». Наприклад, коли ми починаємо розповідати нову історію або казку, ми часто кажемо таке: «Один чоловік сказав мені правду про це місто». Тут ми не рахуємо чоловіків, а просто говоримо про конкретну людину. Ми просто не знаємо її ім'я або не хочемо його називати. Крім того, слово «один» дуже часто означає «сам». Якщо ви сьогодні вдома без друзів чи родини, ви можете просто сказати: «Я сьогодні один» або «Я сьогодні одна». Ще одне надзвичайно корисне значення — це «той самий». Якщо ви живете там, де і ваш друг, ви радісно кажете: «О, ми ж з одного міста!». Або якщо ви маєте однакову кількість років, ви кажете: «Ми одного **віку** (age)».

Подивіться на цей короткий діалог. Він показує, як ми використовуємо це слово в різних значеннях кожного дня:

> — **Анна:** Привіт! Ти сьогодні працюєш один? *(Hi! Are you working alone today?)*
> — **Марко:** Так, мій колега захворів. А ти знаєш, ми з ним з одного міста! *(Yes, my colleague got sick. And you know, we are from the same city!)*
> — **Анна:** Серйозно? А вчора одна жінка сказала, що він з Києва. *(Seriously? But yesterday a certain woman said he is from Kyiv.)*
> — **Марко:** Ні, ми з одного маленького села біля Львова. *(No, we are from the same small village near Lviv.)*

<!-- INJECT_ACTIVITY: fill-in-decline-in-context -->

## Скільки чого? Числівник + іменник (How Many? Numeral + Noun Agreement) (~650 words)

Ви вже знаєте багато українських чисел, але сьогодні ми навчимося правильно поєднувати їх з іменниками. Це одна з найважливіших тем, бо правила тут суттєво відрізняються від англійської мови. В англійській мові ми просто додаємо закінчення до іменника, якщо предметів більше ніж один. В українській мові ми маємо складніший граматичний цикл. Кожен **кількісний числівник** (cardinal numeral) вимагає своєї форми іменника. Перше правило стосується числа один. Коли ми кажемо **один** (one), одна або одне, ми завжди використовуємо називний відмінок однини.

> *You already know many Ukrainian numbers, but today we will learn how to correctly combine them with nouns. This is one of the most important topics because the rules here differ significantly from English. In English, we simply add an ending to the noun if there are more than one item. In Ukrainian, we have a more complex grammatical cycle. Each cardinal numeral requires its own noun form. The first rule concerns the number one. When we say one (masculine, feminine, or neuter), we always use the Nominative singular.*

Другий крок нашого циклу — це числа два, три та чотири. Після цих числівників ми завжди ставимо іменник у називний відмінок множини. Це дуже важливо запам’ятати, бо саме тут студенти часто роблять помилки. Також не забувайте про рід для числа два. Ми використовуємо форму **два** для чоловічого та середнього роду, а форму **дві** для жіночого роду. Це правило діє і для слова «обидва». Ми кажемо «**обидва** (both, m.) студенти», але «**обидві** (both, f.) дівчини». Українська мова дуже логічна в цьому питанні, тому завжди дивіться на рід іменника.

> *The second step of our cycle is the numbers two, three, and four. After these numerals, we always put the noun in the Nominative plural. This is very important to remember because students often make mistakes exactly here. Also, do not forget about the gender for the number two. We use the form "dva" for masculine and neuter, and the form "dvi" for feminine. This rule also applies to the word "both." We say "both students" (masculine) but "both girls" (feminine). The Ukrainian language is very logical in this matter, so always look at the gender of the noun.*

Будьте дуже обережними та уникайте кальок з інших мов у цій групі. Деякі люди помилково використовують родовий відмінок однини після чисел два, три чи чотири, кажуть «чотири брата» замість «чотири брати». Це типова помилка через вплив російської мови. В українській мові ми використовуємо виключно називний відмінок множини для цієї групи чисел. Ви завжди можете перевірити себе: якщо ви можете сказати «ці брати» (множина), то ця форма підходить і для чисел 2, 3, 4.

:::info
**Grammar box**
The agreement rule for **2, 3, 4** is a unique feature of Ukrainian. Remember:
- **1** + Nominative Singular (*один студент*)
- **2, 3, 4** + Nominative Plural (*два студенти*)
- **5-20** + Genitive Plural (*п'ять студентів*)
Never use the Genitive Singular (e.g., *студента*) after 2, 3, or 4 in Ukrainian!
:::

Третій крок циклу починається з числа п’ять і триває до двадцяти. Сюди також входять усі числа, які закінчуються на нуль, наприклад, тридцять чи п’ятдесят. У цій ситуації нам потрібен родовий відмінок множини. Це означає, що ми кажемо «п’ять днів», «десять друзів» або «двадцять вікон». Якщо ви купуєте щось у магазині, ви будете постійно використовувати ці форми. Наприклад, ви просите продавця дати вам «сім яблук» або «дев’ять бананів». Це правило діє для всіх числівників, які позначають велику групу предметів.

Коли ви рахуєте більше двадцяти, граматика залежить від останнього слова у складеному числі. Якщо ви кажете «двадцять один», ви знову повертаєтеся до першого кроку і використовуєте однину. Якщо «двадцять три» — використовуєте називний множини. Це правило повторюється нескінченно для будь-яких великих чисел. Але є один важливий виняток. Це числа одинадцять, дванадцять, тринадцять і чотирнадцять. Хоча вони закінчуються на один, два, три та чотири, вони завжди вимагають родового відмінка множини. Ми кажемо «одинадцять днів», а не «одинадцять день».

> *When you count beyond twenty, the grammar depends on the last word in the compound number. If you say "twenty-one," you return to the first step and use the singular again. If it is "twenty-three," you use the Nominative plural. This rule repeats endlessly for any large numbers. However, there is one important exception. These are the numbers eleven, twelve, thirteen, and fourteen. Although they end in one, two, three, and four, they always require the Genitive plural. We say "eleven days" and not "eleven day."*

Останній важливий момент стосується слів, які показують неозначену кількість. Це слова «багато», «мало», «кілька» та питання **скільки** (how many). Після них ми завжди використовуємо родовий відмінок множини, як після числівника п’ять. Це надзвичайно зручно для розмови про ціни або **вік** (age). Ми часто питаємо друзів: «**Скільки** років вашому братові?». Також ці знання допоможуть вам на ринку. Коли ви хочете дізнатися, **скільки коштує** (how much costs) один **кілограм** (kilogram) картоплі, ви використовуєте ці граматичні конструкції для природного спілкування.

:::tip
**Did you know?**
The numerals 11-14 behave like 5-20 because historically the word "ten" (*десять*) was the dominant part of the phrase. Even though we see "one" in *одинадцять*, the grammar still treats it as part of the "teen" group, requiring the Genitive Plural.
:::

### Читаємо українською: На ринку

Сьогодні я йду на великий ринок у центрі міста. Мені потрібно купити багато продуктів для великої вечері. Спочатку я купую один кілограм цукру та одну пачку солі. Потім я бачу дуже гарні овочі. Я беру два огірки, три помідори та чотири солодкі перці. Продавець каже, що ці овочі сьогодні дуже свіжі. Далі я йду до фруктів. Там я купую шість великих яблук і десять жовтих бананів. На ринку зараз багато людей, тому я витрачаю сорок п’ять хвилин на покупки. Тепер у моїй сумці є двадцять один предмет. Я задоволений, бо все коштує досить недорого.

<!-- INJECT_ACTIVITY: quiz-noun-agreement -->
<!-- INJECT_ACTIVITY: sort-numeral-cases -->

## Числа навколо нас (Numbers Around Us) (~500 words)

> — **Покупець:** Добрий день! Скільки коштують ці яблука? *(Good day! How much do these apples cost?)*
> — **Продавець:** Добрий день! Вони коштують тридцять п'ять гривень за кілограм. *(Good day! They cost thirty-five hryvnias per kilogram.)*
> — **Покупець:** Дайте, будь ласка, два кілограми. І ще один кілограм груш. Скільки коштують груші? *(Give me two kilograms, please. And also one kilogram of pears. How much do the pears cost?)*
> — **Продавець:** Груші коштують сорок дві гривні. Разом це сто дванадцять гривень. *(Pears cost forty-two hryvnias. Together that is one hundred twelve hryvnias.)*
> — **Покупець:** Ось сто двадцять гривень. *(Here is one hundred twenty hryvnias.)*
> — **Продавець:** Ваша решта — вісім гривень. Дякую за покупку! *(Your change is eight hryvnias. Thank you for your purchase!)*

Коли ви на ринку в Україні, ви часто запитуєте: «**Скільки** (how many) це коштує?». Ви хочете знати, скільки буде **коштувати** (to cost) продукт за **кілограм** (kilogram). Наша валюта змінюється після числівників за загальними правилами. Якщо ціна закінчується на один, ми кажемо «одна гривня» (називний відмінок однини). Після чисел два, три та чотири ми говоримо «дві гривні» (називний відмінок множини). Для чисел від п'яти до дев'яти потрібен родовий відмінок множини. Це правило також діє для нуля і чисел від одинадцяти до чотирнадцяти. Тому ми просимо «п'ять гривень» або «сто гривень».

> *When you are at the market in Ukraine, you often ask: "How much does this cost?". You want to know how much a product will cost per kilogram. Our currency changes after numerals according to general rules. If the price ends in one, we say "one hryvnia" (Nominative singular). After the numbers two, three, and four we say "two hryvnias" (Nominative plural). For numbers from five to nine, the Genitive plural is needed. This rule also applies to zero and numbers from eleven to fourteen. Therefore we ask for "five hryvnias" or "one hundred hryvnias".*

:::info
**Grammar box**
To express **вік** (age), use the person in the Dative case followed by the numeral and the correct form of the word for "year": **рік** (1), **роки** (2-4), or **років** (5-20). For example: *Йому двадцять один рік* (He is 21), *Їй сорок два роки* (She is 42), *Їм п'ятдесят років* (They are 50).
:::

### Читаємо українською: Числа в історії та географії

Україна — це велика країна, і числа допомагають нам краще її зрозуміти. Найважливіше державне свято — День Незалежності. Ми святкуємо його двадцять четвертого серпня. Тут ми використовуємо **порядковий** (ordinal) **числівник** (numeral) для дати. Відомий український поет Тарас Шевченко прожив сорок сім років. Наш **перший** (first) президент Леонід Кравчук обійняв посаду у тисяча дев'ятсот дев'яносто першому році. Інший видатний письменник, Іван Франко, знав чотирнадцять мов.

Коли ми подорожуємо, числа показують нам відстань. Відстань від Києва до Львова становить п'ятсот сорок кілометрів. Поїзд їде туди приблизно п'ять або шість годин. Іноді ви можете витратити на дорогу **один** (one) цілий день. Від Києва до Харкова — чотириста вісімдесят кілометрів. Сьогодні столиця України має понад три мільйони жителів. Знати числа дуже корисно, коли ви шукаєте правильну адресу або купуєте квиток.

Числа також дуже важливі для орієнтації в місті. Українська адреса має специфічний формат. Спочатку ви називаєте вулицю, потім номер будинку. А **третій** (third) елемент — це номер квартири. Наприклад, ви кажете: «вулиця Хрещатик, будинок двадцять два, квартира п'ять». Якщо хтось запитує, де ви живете, ви використовуєте прийменники «на» та «у». Ви відповідаєте: «Я живу на вулиці Хрещатик, у будинку двадцять два, у квартирі п'ять». Зверніть увагу, що слова «вулиця», «будинок» і «квартира» змінюють закінчення. Але самі **кількісні** (cardinal) числівники залишаються у звичайній початковій формі.

> *Numbers are also very important for navigating the city. A Ukrainian address has a specific format. First you name the street, then the building number. And the third element is the apartment number. For example, you say: "22 Khreshchatyk Street, apartment 5". If someone asks where you live, you use the prepositions "on" and "in". You answer: "I live on Khreshchatyk Street, in building twenty-two, in apartment five". Notice that the words "street", "building", and "apartment" change their endings. But the cardinal numerals themselves remain in their regular initial form.*

<!-- INJECT_ACTIVITY: match-up-expressions -->

## Підсумок (~150 words)

Ми завершили цей модуль і тепер розуміємо, як працює **числівник** (numeral) в українській мові. Ви знаєте, що кожен **порядковий** (ordinal) числівник відмінюється як прикметник. Більшість із них має тверде закінчення «-ий», але слово **третій** (third) має м'яке закінчення «-ій».

> *We have finished this module and now understand how a numeral works in the Ukrainian language. You know that every ordinal numeral declines like an adjective. Most of them have the hard ending "-ий", but the word "third" has the soft ending "-ій".*

Слово **перший** (first) також є важливим порядковим словом. З іншого боку, звичайний **кількісний** (cardinal) числівник показує кількість предметів. Ми побачили, що слово **один** (one) змінюється за родами та відмінками як типовий прикметник.

Часто ми запитуємо, **скільки** (how many) товарів ми купуємо і що вони будуть **коштувати** (to cost). Також використовуйте правильні відмінки, коли ви купуєте один **кілограм** (kilogram) яблук.

Знати числа необхідно, коли ви описуєте **вік** (age) людини. Ось коротке правило для узгодження чисел з іменниками:

*   1 — Називний відмінок однини (один студент, одна книга).
*   2, 3, 4 — Називний відмінок множини (два студенти, три книги).
*   5–20 — Родовий відмінок множини (п'ять студентів, десять книг).

:::tip
**Quick tip** — Memorize the 1, 2-4, 5-20 cycle as a rhythmic chant. This single rule will solve most of your counting problems in everyday conversations!
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: numerals-and-cases
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

**Level: A2 (Module 55/60) — ELEMENTARY**

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
