<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **11: How Many?** (A1, A1.2 [My World]).

**Word target: 1200 words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
module: a1-011
level: A1
sequence: 11
slug: how-many
version: '1.2'
title: How Many?
subtitle: Один, два, три — numbers through prices, ages, and phones
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Count from 1 to 100 in Ukrainian
- Say prices using гривня and round numbers up to 1000
- Give age using Мені ... років (as memorized chunk — NO case grammar)
- Read and say Ukrainian phone numbers
dialogue_situations:
- setting: 'At a bakery — ordering bread, pastries, and cakes for a family gathering.
    Count: один хліб (m, bread), одна булочка (f, bun), одне тістечко (n, pastry). Prices in гривні.
    Ask: Скільки коштує торт? А три булочки?'
  speakers:
  - Покупець
  - Пекар (baker)
  motivation: Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)
- setting: Counting items in a school backpack before class — ручка (f, pen), олівець
    (m, pencil), зошит (m, notebook), підручник (m, textbook).
  speakers:
  - Учень (student)
  - Мама
  motivation: 'Numbers with school supplies: один олівець, дві ручки, п''ять зошитів'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At a market stall: — Скільки коштує сумка? — Двісті гривень.
    — А маленька? — Сто п''ятдесят. — Добре, дякую!
    Numbers emerge through real shopping context. Uses only vocabulary from M08-M10
    (gender, adjectives, colors). Demonstratives (ця/та) come in M12.'
  - 'Dialogue 2 — Meeting someone new (extending M05): — Скільки тобі років? — Мені
    двадцять п''ять. А тобі? — Мені тридцять два. А твоя сестра? — Їй вісімнадцять.
    Age formula as chunk: Мені/тобі/їй + number + років/роки/рік.'
- section: Числа 1-20 (Numbers 1-20)
  words: 300
  points:
  - '1-10: один, два, три, чотири, п''ять, шість, сім, вісім, дев''ять, десять. Pronunciation
    focus: п''ять (apostrophe!), сім (not ''сем''), дев''ять (apostrophe!). Practice:
    counting objects from M08 — один стіл, два стільці, три книги. Note: the noun
    changes after numbers, but we learn the PATTERNS as chunks, not the grammar rule.'
  - '11-20: одинадцять, дванадцять, тринадцять, чотирнадцять, п''ятнадцять, шістнадцять,
    сімнадцять, вісімнадцять, дев''ятнадцять, двадцять. Pattern: base + -надцять (like
    English ''-teen''). Watch the stress: одинáдцять, дванáдцять — stress always falls
    on the syllable ''на'' in -надцять.'
- section: Десятки і сотні (Tens and Hundreds)
  words: 300
  points:
  - 'Tens: двадцять, тридцять, сорок (!), п''ятдесят, шістдесят, сімдесят, вісімдесят,
    дев''яносто (!), сто. Two irregulars: сорок (40 — not ''чотиридесят'') and дев''яносто
    (90 — not ''дев''ятдесят''). Combined: двадцять один, тридцять п''ять, сорок сім
    — just add the unit.'
  - 'Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400),
    п''ятсот (500), тисяча (1000). Гривня: одна гривня, дві гривні, п''ять гривень.
    These noun changes are memorized patterns — grammar comes in A2. ULP Ep9: Anna
    teaches numbers through real prices.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three practical uses of numbers: 1. Prices: Скільки коштує? — Двісті гривень.
    Сто п''ятдесят гривень. 2. Age: Скільки тобі років? — Мені двадцять три (роки).
    3. Phone: Мій номер — нуль дев''яносто сім, три два один, сорок п''ять, шістдесят
    сім. Self-check: Say your age in Ukrainian. Say a price (250 hryvnias). Read a
    phone number.'
vocabulary_hints:
  required:
  - один, два, три, чотири, п'ять (1-5)
  - шість, сім, вісім, дев'ять, десять (6-10)
  - двадцять, тридцять, сорок (20, 30, 40)
  - сто, тисяча (100, 1000)
  - скільки (how many/how much)
  - коштує (costs — from коштувати)
  - гривня (hryvnia — Ukrainian currency)
  - рік, роки, років (year/years — age chunks)
  recommended:
  - п'ятдесят, шістдесят, сімдесят (50, 60, 70)
  - вісімдесят, дев'яносто (80, 90)
  - двісті, триста, п'ятсот (200, 300, 500)
  - копійка (kopek)
  - номер (number — phone/room)
  - нуль (zero)
activity_hints:
- type: fill-in
  focus: 'Write the number in words: 15 → п''ятнадцять, 47 → сорок сім'
  items: 10
- type: quiz
  focus: Скільки коштує? Match price tags to spoken prices.
  items: 8
- type: quiz
  focus: Скільки років? Match ages to descriptions.
  items: 6
- type: fill-in
  focus: Complete the phone number dictation
  items: 4
connects_to:
- a1-012 (This and That)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- Cardinal numbers 1-1000 (vocabulary, not morphology)
- Скільки коштує? question pattern
- 'Age chunk: Мені + number + років/роки/рік (memorized, not analyzed)'
- 'Irregular tens: сорок (40), дев''яносто (90)'
register: розмовний
references:
- title: ULP Season 1, Episode 5
  url: https://www.ukrainianlessons.com/episode5/
  notes: Numbers 1-10 pronunciation.
- title: ULP Season 1, Episode 9
  url: https://www.ukrainianlessons.com/episode9/
  notes: Numbers 11-100 and prices.
- title: Авраменко Grade 6, p.152
  notes: Числівники кількісні vs порядкові — basic classification.

</plan_content>

---

## Wiki Teaching Brief

Skim this for the key concepts, paradigms, and examples you must cover. Reference specific examples from the article that you plan to use in each paragraph.

<knowledge_packet>
# Knowledge Packet: How Many?
**Module:** how-many | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/how-many.md

# Педагогіка A1: How Many



## Методичний підхід (Methodological Approach)

Навчання кількісних числівників на рівні A1 має бути зосереджено на негайному практичному застосуванні. Українські підручники для початкових класів демонструють підхід, що базується на поступовому ускладненні: від простого рахунку до вирішення елементарних математичних прикладів і практичних завдань, як-от відповіді на питання "Скільки тобі років?".

Основний принцип — зв'язок числівника з конкретним іменником. На відміну від англійської, де числівник є статичним, в українській мові він "живе" і впливає на форму іменника, з яким він пов'язаний. Тому вправи повинні з першого дня вводити числівники у словосполученнях, а не ізольовано (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`).

Педагогічний підхід для L2-учнів має імітувати цей природний процес:
1.  **Візуальна асоціація:** Починати з рахунку предметів на малюнках (Джерело: `ext-article-4`).
2.  **Аудіо-повторення:** Багаторазове прослуховування та повторення числівників для закріплення вимови та наголосу (Джерело: `ext-article-5`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`).
3.  **Контекстуалізація:** Введення числівників через діалоги та практичні ситуації: вік, час, номер телефону, ціна (Джерело: `ext-other_blogs-10`, `5-klas-ukrmova-uhor-2022-1_s0037`).
4.  **Ігрові елементи:** Використання простих математичних прикладів (`два плюс два дорівнює чотири`) як вправи на повторення (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0092`, `5-klas-ukrmova-uhor-2022-1_s0037`).
5.  **Чітке правило:** Явно і багаторазово пояснювати правило "1, 2-4, 5+" для узгодження іменників, оскільки це є найбільшою трудністю для англомовних учнів (Джерело: `ext-article-1`).

Кінцева мета на рівні A1 — не знання всіх відмінкових форм, а впевнене використання числівників у називному відмінку для базового рахунку та в сталих виразах (вік, час).

## Послідовність введення (Introduction Sequence)

Порядок введення числівників має бути логічним і відповідати зростанню складності як самих чисел, так і граматичних правил, що їх супроводжують.

1.  **Step 1: Numbers 0-10.** Це основа. Вводяться числівники `нуль`, `один`, `два`, `три`, `чотири`, `п'ять`, `шість`, `сім`, `вісім`, `дев'ять`, `десять`. На цьому етапі основна увага приділяється правильній вимові та наголосу (Джерело: `5-klas-ukrmova-uhor-2022-1_s0036`).

2.  **Step 2: Gender Agreement for 1 and 2.** Відразу після введення базових числівників необхідно пояснити родові форми:
    *   `один` (чоловічий рід, напр., *один стіл*)
    *   `одна` (жіночий рід, напр., *одна книга*)
    *   `одне` (середній рід, напр., *одне вікно*)
    *   `два` (чоловічий/середній рід, напр., *два столи, два вікна*)
    *   `дві` (жіночий рід, напр., *дві книги*)
    Це фундаментальне правило, яке відрізняє українську від англійської, і його потрібно закріпити до переходу до складніших тем (Джерело: `10-klas-ukrmova-karaman-2018_s0299`, `6-klas-ukrmova-zabolotnyi-2020_s0164`).

3.  **Step 3: The "1, 2-4, 5+" Noun Agreement Rule.** Це найважливіше граматичне правило при вивченні числівників для L2-учнів.
    *   **1 + Іменник у Н.в. однини:** `один рік` (Джерело: `5-klas-ukrmova-uhor-2022-1_s0037`).
    *   **2, 3, 4 + Іменник у Н.в. множини:** `два роки`, `три студенти`, `чотири гривні` (Джерело: `5-klas-ukrmova-uhor-2022-1_s0037`, `6-klas-ukrmova-litvinova-2023_s0248`). Важливо наголосити, що для англомовних учнів це виглядає як "чотири студенти" (Nom.Pl), хоча історично це форма двоїни.
    *   **5+ (до 20) + Іменник у Р.в. множини:** `п'ять років`, `десять студентів`, `двадцять гривень` (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`). Це вимагає знання закінчень родового відмінка множини.

4.  **Step 4: Numbers 11-20 and Tens.** Після засвоєння базових правил вводяться числівники на `-надцять` та круглі десятки (`двадцять`, `тридцять`...).
    *   `одинадцять` - `дев'ятнадцять` (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`).
    *   `двадцять`, `тридцять`, `сорок`, `п'ятдесят` і т.д. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0036`). Пояснити, що ці числівники також керують іменником у родовому відмінку множини.

5.  **Step 5: Practical Application - "How much/many?" and Age.** Вводиться питальне слово `Скільки?` та структура для відповіді про вік.
    *   `Скільки тобі років?`
    *   `Мені ... років/рік/роки.`
    Це знайомить учнів із давальним відмінком займенників (`мені`, `тобі`) у фіксованому, високочастотному контексті (Джерело: `ext-other_blogs-10`).

## Типові помилки L2 (Common L2 Errors)

Англомовні учні часто роблять передбачувані помилки, що виникають через інтерференцію з рідною мовою.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `два книга` | `дві книги` | Учні ігнорують рід іменника та не використовують жіночу форму `дві`. Також забувають про форму множини іменника. (Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0164`) |
| `п'ять студент` | `п'ять студентів` | Найпоширеніша помилка. Після числівників 5 і більше іменник повинен стояти в родовому відмінку множини, а не в однині чи називному множини. (Джерело: `ext-article-1`, `6-klas-ukrmova-litvinova-2023_s0248`) |
| `п'ят**ь**надцять` | `п'ятнадцять` | Перенесення м'якого знака з `п'ять` у середину складного числівника. Правило: `ь` не пишеться в середині числівників `-надцять` та `-десят`. (Джерело: `6-klas-ukrmova-golub-2023_s0160`, `6-klas-ukrmova-zabolotnyi-2020_s0170`) |
| `одинадц**я**ть` (наголос на я) | `один**а́**дцять` | Неправильний наголос. У числівниках на `-а́дцять` наголос падає на склад `-на́-`. (Джерело: `6-klas-ukrmova-betsa-2023_s0005`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`) |
| `Я маю двадцять років.` | `Мені двадцять років.` | Прямий переклад англійської конструкції "I have X years". В українській мові для позначення віку використовується давальний відмінок (`Мені`, `Тобі`, `Йому`). (Джерело: `ext-other_blogs-10`) |
| `чотир**ь**ма` | `чотирма` | Хибне додавання `ь` в орудний відмінок числівника `чотири` за аналогією до `трьох`, `п'ятьох`. Форма `чотирма` є винятком і пишеться без `ь`. (Джерело: `6-klas-ukrmova-avramenko-2023_s0176`) |

## Деколонізаційні застереження (Decolonization Notes)

**Це обов'язковий розділ.** Навчання української мови має відбуватися на її власних умовах, без опори на російську як "посередника" чи "базову" мову.

1.  **Жодних порівнянь з російською.** Заборонено пояснювати українські числівники через їхню схожість або відмінність від російських. Наприклад, ніколи не казати: "Українське *дев'яносто* — це як російське *девяносто*, але пишеться інакше". Учень має будувати нову лінгвістичну систему з нуля.

2.  **Фонетика з чистого аркуша.** Вимова українських числівників має базуватися на фонетичних правилах української мови. Не можна використовувати російські звуки як аналоги (напр., пояснювати український звук [и] через російський [ы]).

3.  **Історична самодостатність.** Підкреслюйте, що українські числівники, як і вся лексика, є частиною самостійної східнослов'янської мовної традиції. Такі слова, як `сорок` чи `дев'яносто`, мають власну історію в давньоруській мові і не є запозиченнями (Джерело: `ext-other_blogs-67`). Це не "спільні" з російською слова, а слова спільного спадку, який кожна мова розвинула по-своєму.

4.  **Уникати "суржикізмів" у прикладах.** Приклади речень та діалогів повинні бути природними для сучасної української мови. Не можна використовувати кальки з російської, навіть якщо вони поширені в побутовому мовленні. Наприклад, конструкції типу `Я рахую, що...` (калька з "Я считаю, что...") слід замінювати на `Я вважаю, що...` або `На мою думку...`.

Навчання числівників — це чудова нагода показати системну відмінність та самобутність української мови на базовому рівні.

## Словниковий мінімум (Vocabulary Boundaries)

На рівні А1 лексика для рахунку має бути простою, високочастотною та конкретною.

| Частина мови | Слово | Рівень | Приклад |
| :--- | :--- | :--- | :--- |
| **Іменники** | | | |
| | рік, роки, років | ★★★ | один рік, п'ять років |
| | гривня, гривні, гривень | ★★★ | дві гривні, десять гривень |
| | стіл, столи, столів | ★★★ | один стіл, три столи |
| | книга, книги, книг | ★★★ | одна книга, сім книг |
| | вікно, вікна, вікон | ★★★ | одне вікно, чотири вікна |
| | студент(ка) | ★★ | два студенти |
| | день, дні, днів | ★★ | три дні |
| | брат, сестра | ★★ | два брати, одна сестра |
| | кілометр | ★ | сорок кілометрів |
| | будинок | ★ | десять будинків |
| **Дієслова** | | | |
| | бути (є) | ★★★ | У мене є одна сестра. |
| | мати | ★★★ | Я маю двадцять гривень. |
| | коштувати | ★★ | Скільки це коштує? |
| | дорівнювати | ★ | два плюс два дорівнює чотири |
| **Прислівники/Питальні слова** | | | |
| | скільки | ★★★ | Скільки тобі років? |
| | плюс, мінус | ★ | п'ять плюс п'ять |

## Приклади з підручників (Textbook Examples)

Ці приклади демонструють формати вправ, які є ефективними та відповідають українській педагогічній традиції.

**1. Вправа: Математичні приклади (для відпрацювання вимови та форм)**
Прочитайте приклади. Запишіть (на вибір) два речення. Підкресліть числівники.
*   `Чотири плюс вісім дорівнює дванадцять.`
*   `Сто мінус сімдесят дорівнює тридцять.`
*   `П’ятдесят три плюс сімнадцять дорівнює сімдесят.`
(Джерело: `2-klas-ukrmova-kravcova-2019-1_s0092`)

**2. Вправа: Відповіді на питання (контекстуалізація)**
Запиши повні відповіді на запитання.
*   `Скільки дівчаток у вашому класі?`
*   `Скільки хлопчиків?`
*   `Скільки загалом дітей у вашому класі?`
(Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`)

**3. Вправа: Узгодження з іменником (ключове правило 1, 2-4, 5+)**
Прочитайте вголос словосполучення, правильно узгоджуючи числівник з іменником.
*   `будинок № 25 (двадцять п'ять)`
*   `будинок № 1 (один)`
*   `будинок № 4 (чотири)`
*   `квартира № 14 (чотирнадцять)`
*   `квартира № 2 (дві)`
(Адаптовано з Джерела: `5-klas-ukrmova-uhor-2022-1_s0037`)

**4. Вправа: Заміна цифр словами (письмове закріплення)**
Спишіть речення, замінюючи цифри словами. Зверніть увагу на правильність уживання іменників.
*   `Текст був на 294 сторінках.`
*   `Зустріч із 45 студентами відбулась у вівторок.`
*   `У школі навчається понад 1000 учнів і учениць.`
(Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0177`)

## Пов'язані статті (Related Articles)

*   `pedagogy/a1/what-is-this`
*   `grammar/a1/noun-genders`
*   `grammar/a1/nominative-case`
*   `grammar/a2/genitive-case`
*   `pedagogy/a1/telling-time`

---

### Вікі: pedagogy/a1/many-things.md

# Педагогіка A1: Many Things



## Методичний підхід (Methodological Approach)
The concept of "many things" (множина, plural) is foundational and should be introduced early in A1, but methodically. The Ukrainian native pedagogy for early grades focuses on concrete, visual association and pattern recognition rather than abstract rule memorization.

The core principle is that the plural is a change in the **ending** of a word to signify more than one item. The approach should be:

1.  **Concrete to Abstract:** Start with physical objects in the classroom or in pictures. "Це стіл. А це столи." (This is a table. And these are tables). The visual contrast makes the concept intuitive.
2.  **Agreement over Declension:** Initially, focus on the agreement between nouns and adjectives in the nominative case. The key takeaway for learners is that adjectives must also change to reflect the plural noun they describe (`3-klas-ukrainska-mova-vashulenko-2020-1_s0128`). Ukrainian primary school textbooks emphasize this with tables showing gendered singular adjectives all converging on a single plural form (`4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0064`).
3.  **Pattern Recognition:** Group nouns by their plural endings. Introduce the most common patterns first (masculine/feminine hard stems ending in **-и**) before moving to soft stems (**-і**) and neuter nouns (**-а, -я**) (`ext-ulp_youtube-261`).
4.  **Plurality in Context:** Introduce plural forms within simple sentence structures like "У мене є..." (I have...) or "Тут є..." (Here are...). For example, "У кімнаті є два стільці, книги і лампи" (`ext-ulp_youtube-258`). This immediately makes the grammar useful.
5.  **Verb Agreement:** Once the noun/adjective plural is established, introduce verb agreement. It's crucial to teach that a plural subject requires a plural verb form. A common construction in textbooks is combining two singular nouns to form a plural subject: "Кіт і собака **пустують** у дворі" (A cat and a dog **are playing** in the yard) (`8-klas-ukrmova-avramenko-2025_s0172`). The verb must be in the plural form.

Avoid overwhelming the learner with all case endings for plurals at once. A1 should master the nominative (who/what?) and basic counting rules, with other cases introduced gradually.

## Послідовність введення (Introduction Sequence)
This sequence builds from the simplest, most frequent patterns to more complex ones, mirroring the logic of Ukrainian primary education materials.

-   **Step 1: The Concept of Plural (Nominative Case)**
    -   Introduce "one" vs. "many" with high-frequency masculine and feminine nouns that follow the simplest rule: adding **-и**.
    -   **Examples:** `стіл` → `столи`, `кіт` → `коти`, `шафа` → `шафи`, `лампа` → `лампи` (`ext-ulp_youtube-261`).

-   **Step 2: The Soft Stem Plural (Nominative Case)**
    -   Introduce nouns ending in a soft consonant (e.g., -ць, -нь) or -я, which typically take an **-і** ending.
    -   **Why this order?** This is the next most common pattern.
    -   **Examples:** `стілець` → `стільці`, `учитель` → `учителі`, `полиця` → `полиці` (`ext-ulp_youtube-261`).

-   **Step 3: The Neuter Plural (Nominative Case)**
    -   Introduce neuter nouns, which are distinct in taking **-а** (for hard stems) or **-я** (for soft stems) in the plural.
    -   **Why this order?** Neuter nouns are a large and consistent group, but their plural ending is very different from masculine/feminine, so it needs its own focus.
    -   **Examples:** `вікно` → `вікна`, `ліжко` → `ліжка`, `море` → `моря` (`ext-ulp_youtube-261`, `5-klas-ukrmova-uhor-2022-1_s0030`).

-   **Step 4: Adjective Agreement in the Plural**
    -   Introduce the "magic" of the plural adjective ending **-і**. Show how it replaces all three gendered singular endings (`-ий`, `-а`, `-е`). This simplifies things for the learner.
    -   Use tables to demonstrate: `новий стіл`, `нова книга`, `нове вікно` → `нові столи, книги, вікна` (`4-klas-ukrmova-zaharijchuk_s0082`).

-   **Step 5: Basic Counting with Plurals**
    -   This is a critical, non-negotiable step for A1. Introduce the "1, 2-3-4, 5+" rule.
        -   **1:** Agrees in gender (`один стіл`, `одна книга`, `одне вікно`).
        -   **2, 3, 4:** Take the noun in **Nominative Plural** (`два столи`, `три книги`, `чотири вікна`).
        -   **5+:** Take the noun in **Genitive Plural** (`п'ять столів`, `шість книг`, `десять вікон`).
    -   At the A1 stage, it's sufficient to provide the genitive plural forms for memorization alongside the numbers, as the rules for forming it are complex. This rule is explicitly detailed in Ukrainian school grammar (`6-klas-ukrmova-litvinova-2023_s0248`).

-   **Step 6: Essential Irregular Plurals**
    -   Introduce a small, curated list of high-frequency irregular plurals that don't follow the main patterns.
    -   **Examples:** `людина` → `люди`, `дитина` → `діти`, `друг` → `друзі`, `око` → `очі` (`ext-ulp_youtube-258`).

## Типові помилки L2 (Common L2 Errors)
For English-speaking learners, plurals present several predictable challenges. Addressing them proactively is key.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Я бачу два *стіл*.` | `Я бачу два **столи**.` | English uses the singular form after a number ("one table", "two table**s**"), but Ukrainian uses the **nominative plural** for numbers 2, 3, and 4. The noun must change. (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`) |
| `У мене є п'ять *столи*.` | `У мене є п'ять **столів**.` | This is the second half of the counting rule. Numbers 5 and up require the **genitive plural**, not the nominative plural. This is a fundamental concept with no direct English equivalent and must be drilled. (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`) |
| `Кіт і собака *сидить* тут.` | `Кіт і собака **сидять** тут.` | In English, two singular subjects joined by "and" take a plural verb. The same is true in Ukrainian. Learners often forget to change the verb, leaving it in the 3rd person singular. A plural subject demands a plural verb. (Джерело: `8-klas-ukrmova-avramenko-2025_s0172`) |
| `Це *новий* книги.` | `Це **нові** книги.` | Adjectives **must** agree in number with the noun they describe. The singular adjective `новий` cannot describe the plural noun `книги`. The adjective must take the universal plural ending `-і`. (Джерело: `4-klas-ukrmova-zaharijchuk_s0082`) |
| `Тут *кни́жка* і *ру́чка*.` | `Тут **книжки́** і **ру́чки**.` | Learners often ignore or misapply stress shifts in the plural. The stress in `кни́жка` (singular) moves to the end in the plural `книжки́`. This is a common feature and cannot be ignored for correct pronunciation. (Джерело: `ext-ulp_youtube-29`) |
| `Це мої *друг*.` | `Це мої **друзі**.` | Learners may try to apply a regular plural ending (`-и`) to an irregular noun. High-frequency irregulars like `друг` → `друзі` must be memorized as vocabulary items. (Джерело: `ext-ulp_youtube-258`) |

## Деколонізаційні застереження (Decolonization Notes)
**MANDATORY:** Teaching Ukrainian plurals requires a strict decolonization framework to avoid common pedagogical pitfalls that center or rely on Russian.

1.  **Teach Ukrainian on Its Own Terms:** Never introduce Ukrainian plurals by comparing them to Russian (e.g., "Ukrainian `-и` is like Russian `-ы`"). This frames Ukrainian as a derivative and builds an incorrect mental model. The learner must build a new, separate Ukrainian system from zero.
2.  **Stress is Not Russian:** Emphasize that plural stress patterns in Ukrainian are independent and often differ from Russian cognates. A learner's knowledge of Russian stress can be a hindrance, not a help. For example, `по́казник` in Ukrainian has stress on the second syllable, unlike the Russian equivalent (`ext-ulp_youtube-29`). The writer must provide audio and clear markings for all new vocabulary.
3.  **Correct Etymology:** Acknowledge shared Slavic roots neutrally. When a word exists in both Ukrainian and Russian, present it as part of a common linguistic heritage, not as a "Russian word used in Ukrainian" (`ext-ulp_youtube-139`). The default assumption must be that the word is native to Ukrainian unless proven otherwise.
4.  **Avoid Surzhyk and Russianisms:** The writer must be vigilant in using vocabulary. For example, use `фарту́х` (correct Ukrainian) not `фа́ртук` (Russian stress/form) (`ext-ulp_youtube-29`). The vocabulary provided in the A1 modules must be vetted to be purely Ukrainian.
5.  **Pluralia Tantum as a Feature:** When introducing nouns that only exist in the plural (pluralia tantum), like `двері` (doors), `окуляри` (glasses), or city names like `Суми` (`ext-komik_istoryk-67`), present this as a normal and interesting feature of Ukrainian, not as an oddity.

## Словниковий мінімум (Vocabulary Boundaries)
This vocabulary is appropriate for introducing and practicing plurals at the A1 level.

**Іменники (Nouns):**
-   ★★★ `стіл` (table), `стілець` (chair), `книга` (book), `кімната` (room), `вікно` (window), `двері` (door), `ліжко` (bed), `будинок` (house), `друг` (friend), `день` (day), `рік` (year), `людина` (person).
-   ★★☆ `шафа` (wardrobe), `полиця` (shelf), `лампа` (lamp), `картина` (picture), `фотографія` (photo), `син` (son), `брат` (brother), `сусід` (neighbor), `олівець` (pencil), `зошит` (notebook), `урок` (lesson).
-   ★☆☆ `вазон` (flowerpot), `квітка` (flower), `дерево` (tree), `кіт` (cat), `собака` (dog), `риба` (fish).

**Прикметники (Adjectives):**
-   ★★★ `новий` (new), `старий` (old), `великий` (big), `маленький` (small), `гарний` (good, beautiful), `добрий` (good, kind).
-   ★★☆ `цікавий` (interesting), `український` (Ukrainian), `високий` (tall/high), `зелений` (green), `синій` (blue), `білий` (white), `чорний` (black).
-   ★☆☆ `зручний` (comfortable), `світлий` (light/bright), `теплий` (warm).

**Дієслова (Verbs):**
-   ★★★ `бути` (to be, especially `є`), `мати` (to have), `жити` (to live).
-   ★★☆ `стояти` (to stand), `лежати` (to lie), `бачити` (to see), `робити` (to do).

## Приклади з підручників (Textbook Examples)
These exercise formats are adapted from Ukrainian primary school textbooks and are ideal for A1 learners.

1.  **Вправа: Утвори множину (Exercise: Form the Plural)**
    -   **Мета:** Practice basic singular-to-plural conversion for nouns and adjectives.
    -   **Формат:** Fill-in-the-blanks.
    -   **Завдання:** "Допишіть закінчення, щоб утворити множину." (Add the endings to form the plural.)
        -   `Акваріумн.. рибка` → `Акваріумн.. рибки`
        -   `Маленьк.. окунь` → `Маленьк.. окуні`
        -   `Хиж.. щука` → `Хиж.. щуки`
        -   `Вусат.. сом` → `Вусат.. соми`
    -   *(Джерело: Адаптовано з `3-klas-ukrainska-mova-kravtsova-2020-1_s0069`)*

2.  **Вправа: Один → Багато (Exercise: One → Many)**
    -   **Мета:** Reinforce adjective-noun agreement across genders.
    -   **Формат:** Table completion.
    -   **Завдання:** "Заповніть таблицю за зразком." (Fill the table according to the model.)
| Однина (Singular) | Множина (Plural) |
| :--- | :--- |
| `солодкий торт` (ч.р.) | `солодк.. торти` |
| `солодка слива` (ж.р.) | `солодк.. сливи` |
| `солодке яблуко` (с.р.) | `солодк.. яблука` |
    -   *(Джерело: Адаптовано з `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0064`)*

3.  **Вправа: Порахуй предмети (Exercise: Count the Items)**
    -   **Мета:** Practice the crucial 2-3-4 vs. 5+ counting rule.
    -   **Формат:** Combine numbers with nouns.
    -   **Завдання:** "Напишіть правильну форму іменника." (Write the correct form of the noun.)
        -   `два (зошит)` → __________ (`два зошити`)
        -   `три (клієнт)` → __________ (`три клієнти`)
        -   `чотири (смартфон)` → __________ (`чотири смартфони`)
        -   `п'ять (урок)` → __________ (`п'ять уроків`)
        -   `десять (учень)` → __________ (`десять учнів`)
    -   *(Джерело: Адаптовано з `6-klas-ukrmova-litvinova-2023_s0248`)*

4.  **Вправа: Що є в кімнаті? (Exercise: What is in the room?)**
    -   **Мета:** Use plurals in a descriptive context.
    -   **Формат:** Picture description or text completion.
    -   **Завдання:** "Подивіться на малюнок і опишіть кімнату, використовуючи слова в множині." (Look at the picture and describe the room, using words in the plural.)
    -   **Приклад тексту:** "У кімнаті є два (ліжко), один (стіл) і чотири (стілець). На стіні висять (картина) і (фотографія). На полицях стоять (книга)." (In the room there are two beds, one table, and four chairs. On the wall hang pictures and photographs. On the shelves stand books.)
    -   *(Джерело: Адаптовано з `ext-ulp_youtube-258` та `7-klas-istoria-ukr-pometun-2024_s0072`)*

## Пов'язані статті (Related Articles)
-   [[pedagogy/a1/noun-genders|Педагогіка A1: Noun Genders]]
-   [[pedagogy/a1/adjective-agreement|Педагогіка A1: Adjective Agreement]]
-   [[pedagogy/a1/numbers-and-counting|Педагогіка A1: Numbers and Counting (1-100)]]
-   [[pedagogy/a1/nominative-case|Педагогіка A1: The Nominative Case]]
-   [[pedagogy/a2/genitive-case|Педагогіка A2: The Genitive Case]]
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Output format

Output a single `<skeleton>` block. For each section from the plan's `content_outline`, list every paragraph and exercise with its word budget and content focus.

Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."

```
<skeleton>
## Section Title (~XXX words total)
- P1 (~XX words): [specific content — what concept, what examples, what comparison]
- P2 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type, focus]
...

## Підсумок — Summary (~150 words)
- P1 (~150 words): [Follow the plan's points for this section EXACTLY. If the plan says "Self-check questions", output a bulleted Q&A list — NOT prose. If the plan says "recap", write a brief recap.]

Grand total: ~1200 words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to 1200+.** Aim for ~10% overshoot (1320 words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Place exercise injection markers in the correct section.** Each activity hint in the plan may have a `section:` field that tells you which section it belongs in. Place `<!-- INJECT_ACTIVITY: descriptive-id -->` AFTER the teaching content of that section, never before. Use a descriptive kebab-case id (e.g., `fill-in-genitive`, `quiz-aspect-choice`). If no `section:` is specified, place the marker after the most relevant teaching point. **CRITICAL: An exercise must ONLY test concepts already taught above it. Never test a concept from a later section. Every plan `activity_hints` entry MUST have a corresponding `<!-- INJECT_ACTIVITY: id -->` marker in the skeleton.**
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
