<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 14: Багато книг, мало студентів (A2, A2.2 [Genitive Case Complete])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-014
level: A2
sequence: 14
slug: genitive-plural
version: '1.1'
title: Багато книг, мало студентів
subtitle: Родовий відмінок множини — найскладніша форма
focus: grammar
pedagogy: PPP
phase: A2.2 [Genitive Case Complete]
word_target: 2000
objectives:
  - Learner can form the Genitive plural of masculine nouns using the correct
    ending (-ів or zero ending for -ин/-їн nouns).
  - Learner can form the Genitive plural of feminine nouns using zero ending
    with possible vowel insertion or soft sign (and recognize rare -ей exceptions).
  - Learner can form the Genitive plural of neuter nouns (zero ending, -ів for 
    exceptions).
  - Learner can use Genitive plural correctly after quantity words (кілька, 
    багато, мало, скільки) and numerals 5+.
dialogue_situations:
  - setting: 'Inventory check at a small village shop — counting what''s left: Скільки
      пляшок (f, bottles) води? П''ять. Скільки банок (f, jars) меду? Три. А булок
      (f, buns)? Немає булок!'
    speakers:
      - Продавець
      - Помічник (assistant)
    motivation: 'Genitive plural: пляшок, банок, булок — feminine zero ending'
content_outline:
  - section: 'Чоловічий рід: -ів та нульове закінчення (Masculine: -ів and
      Zero Ending)'
    words: 650
    points:
      - 'Main pattern -ів: столів, братів, студентів, будинків, підручників. Most
        hard-stem masculine nouns take -ів.'
      - 'Soft-stem -ів: учитель→учителів (fleeting е drops), олівець→олівців.
        True -їв appears only after vowel/apostrophe stems: подвір''я→подвір''їв,
        відкриття→відкриттів. Most soft masculine nouns take -ів, not -їв.'
      - 'Zero ending (rare in masculine): nouns losing -ин/-їн suffix take zero
        ending: громадянин→громадян, селянин→селян, болгарин→болгар. The word
        чоловік has parallel forms (чоловік/чоловіків). Most masculine nouns take -ів.'
      - 'Fleeting vowels: день→днів (е drops), хлопець→хлопців (е drops). Practice
        recognizing stem changes in the Genitive plural.'
  - section: 'Жіночий рід: нульове закінчення (Feminine: Zero Ending Patterns)'
    words: 700
    points:
      - 'Hard-stem zero ending: книга→книг, жінка→жінок (vowel insertion о), сестра→сестер
        (vowel insertion е). The main feminine pattern removes -а and uses zero ending.'
      - 'Vowel insertion rules: consonant clusters at the end of the stem often require
        о or е insertion. студентка→студенток, зупинка→зупинок, сумка→сумок.'
      - 'Soft-stem zero + ь: пісня→пісень, вишня→вишень (regular I declension
        soft-stem pattern). I declension -ей exceptions (small closed group):
        стаття→статей, сім''я→сімей, миша→мишей. The -ія group: станція→станцій,
        лекція→лекцій (zero ending, й drops).'
      - 'Mixed group: площа→площ, задача→задач. Stems ending in ж, ч, ш, щ take zero
        ending without vowel insertion.'
      - 'Practice with common words: кілька книг, багато жінок, мало сестер, скільки
        пісень, декілька лекцій.'
  - section: 'Середній рід та узагальнення (Neuter and Summary)'
    words: 650
    points:
      - 'Neuter zero ending: вікно→вікон, слово→слів, місто→міст. The -о drops and
        zero ending applies. Vowel insertion where needed: вікон (о inserted).'
      - 'Soft neuter: море→морів, поле→полів (-ів ending, not zero). But: завдання→завдань
        (-ь ending), питання→питань.'
      - '-тя neuter: ім''я→імен, теля→телят. These have special stem changes in the
        plural.'
      - 'Summary table: masculine (-ів, rare zero), feminine (zero + vowel insertion
        or ь, rare -ей exceptions), neuter (zero/-ів). Note: true -ей also exists
        in II declension masc/neuter (гостей, коней, очей) — a small closed group.
        Key insight: Genitive plural has the MOST variation of any case — memorize
        common words, learn patterns, accept exceptions.'
      - 'Quantity expressions: багато студентів, кілька книг, мало міст, декілька
        днів, скільки людей.'
vocabulary_hints:
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
  recommended:
    - чоловічий рід (masculine gender)
    - жіночий рід (feminine gender)
    - середній рід (neuter gender)
    - виняток (exception)
    - вставний голосний (inserted vowel)
activity_hints:
  - type: fill-in
    focus: Form the Genitive plural of given nouns (all three genders)
    items: 8
  - type: quiz
    focus: Choose the correct Genitive plural ending (-ів, -ей, zero, or -їв)
    items: 8
  - type: match-up
    focus: Match Nominative singular nouns to their Genitive plural forms
    items: 8
  - type: group-sort
    focus: Sort Genitive plural forms by ending type (-ів/-їв vs. zero vs. -ей)
    items: 8
references:
  - title: Заболотний Grade 6, §34-36
    notes: Родовий відмінок множини іменників усіх родів
  - title: 'ULP: 10 Uses of Genitive Case'
    url: https://www.ukrainianlessons.com/genitive-case/
    notes: Genitive plural patterns and exceptions

</plan_content>

## Generated Content

<generated_module_content>
## Чоловічий рід: -ів та нульове закінчення (~720 words)

Welcome to the most complex form of the Ukrainian noun: the Genitive plural. We use this case constantly when we talk about quantities. Numbers from five and above require the Genitive plural. We also often use this form after the question word **скільки** (how many) and after quantity words such as **багато** (a lot, many), **мало** (few), and **кілька** (a few, several) when we talk about countable nouns.

Сьогодні ми вивчаємо родовий відмінок множини іменників. Коли ми рахуємо **людей** або предмети, нам потрібна саме ця форма. Якщо ви маєте п'ять або десять предметів, ви змінюєте слово. Ми також часто використовуємо цю форму після слова **скільки** та після слів **багато**, **мало** і **кілька**, коли йдеться про злічувані предмети.

> *Today we are studying the Genitive plural of nouns. When we count **people** or objects, we need this form. If you have five or ten items, you change the word. We also often use this form after **how many** and after quantity words when we talk about countable things. When there are **a lot**, **a few**, or only a small number of objects, we change the ending.*

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
> — **Продавець:** Зрозуміло. Тоді запиши: воду, мед і булки треба замовити. *(Understood. Then write it down: we need to order water, honey, and buns.)*

In the dialogue, counting feminine nouns like "пляшка" (bottle) or "банка" (jar) with quantity words and with numbers from five upward requires the Genitive plural. The primary pattern is the **нульове закінчення** (zero ending). You drop the final **-а** from hard-stem nouns, leaving no ending. For example, "книга" (book) becomes "книг", and "жінка" (woman) becomes "жінок".

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

Neuter nouns with hard stems ending in **-о** behave very much like feminine nouns. When forming the Genitive plural, you usually drop the final vowel. This leaves them with a **нульове закінчення** (zero ending). Just as with feminine words, dropping the vowel sometimes creates a cluster of consonants that is hard to pronounce, so an extra vowel is inserted. For example, «вікно» becomes «вікон» and «місто» becomes «міст». If the stem has an «о» before the ending, it often changes to «і», so «слово» becomes «слів».

У цьому старому будинку немає нових вікон. Микола знає багато українських слів. У Європі є дуже багато красивих міст. На столі лежить кілька яблук. Після свята у нас залишилося мало смачних тістечок.

> *There are no new windows in this old building. Mykola knows many Ukrainian words. There are very many beautiful cities in Europe. There are a few apples lying on the table. After the holiday, we have few tasty cakes left.*

:::info
**Grammar box**
When a neuter noun drops its **-о**, watch out for vowel insertion. The word «вікно» naturally turns into «вікон» to avoid the awkward «вікн» sound at the end.
:::

Soft neuter nouns ending in **-е** are full of surprises. Instead of taking a zero ending, they borrow the masculine pattern and take the **-ів** ending. For instance, «море» becomes «морів», and «поле» becomes «полів». However, neuter nouns ending in **-ння** take a zero ending plus a soft sign, and they drop their double consonant. Therefore, **завдання** (task, assignment) becomes «завдань», and **питання** (question) becomes «питань».

Студенти мають багато складних завдань. У мене є кілька важливих питань до викладача. Географи досліджують екологію південних морів. В Україні є багато широких полів. Учитель дав нам декілька нових завдань на завтра.

> *Students have many difficult tasks. I have a few important questions for the teacher. Geographers study the ecology of southern seas. There are many wide fields in Ukraine. The teacher gave us several new tasks for tomorrow.*

Neuter nouns ending in **-тя** and words for young animals belong to a special declension group. They undergo unique stem changes when they form the Genitive plural. The word **ім'я** (name) changes its stem entirely to become «імен». Words for baby animals keep their special plural suffixes. For example, «теля» becomes «телят», and «кошеня» becomes «кошенят».

На фермі мого дідуся є п'ять маленьких телят. Я не пам'ятаю імен цих нових студентів. У нашому дворі грається багато смішних кошенят. Фермер годує десять голодних телят.

> *There are five small calves on my grandfather's farm. I do not remember the names of these new students. Many funny kittens are playing in our yard. The farmer is feeding ten hungry calves.*

To understand the big picture, let us review the main patterns for all genders. Most masculine nouns take the **-ів** ending, though a few exceptions take a zero ending. Most feminine nouns take a zero ending, often with an inserted vowel or a soft sign. A few feminine exceptions take **-ей**, so **стаття** (article) becomes «статей». Most neuter nouns also take a zero ending, but those ending in **-е** take **-ів**. Additionally, a small closed group of masculine and neuter nouns takes a true **-ей** ending, so «кінь» becomes «коней», and «око» becomes «очей».

| Рід | Основне закінчення | Приклади | Винятки |
| :--- | :--- | :--- | :--- |
| Чоловічий | **-ів** | студентів, столів, братів | громадян (нульове), гостей (**-ей**) |
| Жіночий | **нульове закінчення** | книг, жінок, сестер, пісень | статей (**-ей**), сімей (**-ей**) |
| Середній | **нульове закінчення** | міст, слів, завдань, питань | морів (**-ів**), очей (**-ей**) |

Now we can confidently use quantity words with nouns of all genders. Whenever you use words like **багато** (a lot, many), **кілька** (a few, several), or **мало** (few) with countable nouns, you normally use the Genitive plural. These expressions are incredibly common in everyday conversations.

The same rule applies when you ask **скільки** about countable nouns. It also applies to the word **людина** (person). Remember that its plural is **люди** (people), which becomes «людей» in the Genitive plural. You will use this specific form almost every day.

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
</generated_module_content>

**PIPELINE NOTE — Word count: 3020 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 468 words | Not found: 9 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Європі — NOT IN VESUM
  ✗ Іванівно — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Микола — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ вікн — NOT IN VESUM
  ✗ ння — NOT IN VESUM
  ✗ студентк — NOT IN VESUM

All 468 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
