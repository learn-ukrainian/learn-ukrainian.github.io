<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-source.yaml` file for module **9: Звідки ти? З чого це зроблено?** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-euphony-variants -->`
- `<!-- INJECT_ACTIVITY: fill-in-focus-complete-sentences-with-or-correct-genitive-noun-form -->`
- `<!-- INJECT_ACTIVITY: match-up-preposition-meanings -->`
- `<!-- INJECT_ACTIVITY: group-sort-preposition-usage -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct variant з/із/зі based on the following word
  items: 8
  type: quiz
- focus: Complete sentences with від or з + correct Genitive noun form
  items: 8
  type: fill-in
- focus: Match preposition phrases to their English meanings (origin, material, time)
  items: 8
  type: match-up
- focus: Sort phrases into з (place/material) vs. від (person/protection) vs. після
    (time)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дитинство (childhood)
- шовк (silk)
- парасолька (umbrella)
- сусід (neighbor)
required:
- прийменник (preposition)
- джерело (source)
- походження (origin)
- матеріал (material)
- далеко (far)
- недалеко (not far, nearby)
- подарунок (gift)
- сніданок (breakfast)
- вечеря (dinner, supper)
- канікули (vacation, holidays)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ: Вечірка в друзів

Сьогодні у нас міжнародна вечеря. *(Today we have an international dinner.)* Let's see what everyone brought.

> — **Олена:** Привіт усім! Що ви принесли? *(Hi everyone! What did you bring?)*
> — **П'єр:** Це сир **з Франції** *(from France)*.
> — **Нікос:** А це оливки **з Греції** *(from Greece)*. Вони дуже свіжі. *(They are very fresh.)*
> — **Анна:** Я принесла шоколад **від бабусі** *(from grandma)*. Вона живе в Бельгії. *(She lives in Belgium.)*
> — **Олена:** Чудово! А це вино ми п'ємо **після подорожі** *(after a trip)*.

Notice how the friends describe where things come from or when things happen. They use the prepositions **з** *(from)*, **від** *(from a person)*, and **після** *(after)*. 

Ці маленькі слова дуже важливі для спілкування. *(These small words are very important for communication.)* In this module, you will learn how to use them to talk about origins, materials, and time.

## Звідки? З/із/зі + родовий (Where From? З/із/зі + Genitive)

«Звідки ти?» *(Where are you from?)*
Це дуже часте запитання. *(This is a very frequent question.)*
Сьогодні ми вивчаємо новий прийменник. *(Today we are learning a new preposition.)*
Цей прийменник завжди вимагає після себе родовий відмінок. *(This preposition always requires the Genitive case after it.)*
Він показує ваше походження або джерело дії. *(It shows your origin or the source of an action.)*

The core meaning of this preposition is the starting point of an action or the geographic origin of a person. When you state your origin, you take the name of the place and apply the rules for the Genitive case. It answers the fundamental question of where someone or something comes from. For feminine nouns, the ending typically changes to the feminine Genitive ending. For masculine cities, countries, and objects, the ending changes to the masculine Genitive ending. This pattern is consistent and very important for basic conversations.

«Україна → з України» *(from Ukraine)*
«Київ → з Києва» *(from Kyiv)*
«Харків → з Харкова» *(from Kharkiv)*
«Лондон → з Лондона» *(from London)*

Читаємо українською:
— Я **з України** *(from Ukraine)*.
— Він приїхав **з Києва** *(from Kyiv)*.
— Ми **з Лондона** *(from London)*.
— Вони летять **з Харкова** *(from Kharkiv)*.
— Мій друг повернувся **з роботи** *(from work)*.
— Моя сестра **з Польщі** *(from Poland)*.
— Студенти вийшли **з аудиторії** *(from the auditorium)*.

> — **Марко:** Звідки ти? *(Where are you from?)*
> — **Сара:** Я з Лондона. А ти? *(I am from London. And you?)*
> — **Марко:** Я з Києва. *(I am from Kyiv.)*
> — **Сара:** Це цікаво. Мій друг теж з Києва. *(That is interesting. My friend is also from Kyiv.)*
> — **Марко:** Світ дуже тісний! *(The world is very small!)*

Українська мова дуже милозвучна. *(The Ukrainian language is very euphonic.)*
Ми любимо, коли слова легко вимовляти. *(We like when words are easy to pronounce.)*
Тому цей прийменник має три різні форми. *(Therefore, this preposition has three different forms.)*
Ми вибираємо форму для комфорту. *(We choose the form for comfort.)*

The rule of euphony is a signature phonetic trait of the language. You must choose the form of the preposition that makes the sentence flow best. This prevents awkward consonant combinations and makes speech feel natural and effortless. You do not need to memorize this as a strict exception, but rather feel the rhythm of the words as you speak. 

1. Use the basic form «з» before vowels and most single consonants. 
2. Use the extended form «із» between two consonants or before sibilant sounds like «с», «з», «ш», «ж», «ч».
3. Use the soft form «зі» before a heavy cluster of consonants, especially those starting with «с», «з», «ш», «л», «м».

«Одеса → з Одеси» *(from Odesa)*
«село → із села» *(from the village)*
«золото → із золота» *(from gold)*
«Львів → зі Львова» *(from Lviv)*
«школа → зі школи» *(from school)*

Читаємо українською:
— Я їду **з Одеси**. *(I am going from Odesa.)*
— Він іде **з університету**. *(He is walking from the university.)*
— Це браслет **із золота**. *(This is a bracelet made of gold.)*
— Жінка **із села** привезла молоко. *(The woman from the village brought milk.)*
— Мій брат приїхав **із Житомира**. *(My brother arrived from Zhytomyr.)*
— Я приїхав **зі Львова**. *(I arrived from Lviv.)*
— Діти повертаються **зі школи**. *(The children are returning from school.)*
— Я взяв книгу **зі стола**. *(I took the book from the table.)*
— Він родом **зі Швеції**. *(He is originally from Sweden.)*

> — **Анна:** Ти зі Львова? *(Are you from Lviv?)*
> — **Тарас:** Ні, я з Одеси. *(No, I am from Odesa.)*
> — **Анна:** А я із Сум. *(And I am from Sumy.)*
> — **Тарас:** У нас сьогодні зустріч людей із різних міст. *(We have a meeting of people from different cities today.)*

З чого це зроблено? *(What is this made of?)*
Цей прийменник також показує матеріал. *(This preposition also shows the material.)*
Ми описуємо речі навколо нас. *(We describe things around us.)*

You can use this preposition combined with the Genitive case to describe the material an object is made from. It can also describe what a container holds, or the main ingredient of a dish. Notice how neuter and masculine nouns take the typical Genitive endings, while plural nouns often take a zero ending. This construction is incredibly useful for shopping, ordering food, or simply describing your environment.

«дерево → з дерева» *(from wood)*
«скло → зі скла» *(from glass)*
«овочі → з овочів» *(from vegetables)*
«яблука → з яблук» *(from apples)*

Читаємо українською:
— Це старий стіл **з дерева** *(from wood)*.
— На столі стоїть склянка **зі скла** *(from glass)*.
— Вона купила сукню **з шовку** *(from silk)*.
— Я люблю пити свіжий сік **з яблук** *(from apples)*.
— Мама приготувала салат **з помідорів** *(from tomatoes)*.
— Ми їмо смачний суп **з овочів** *(from vegetables)*.

> — **Олег:** Ця склянка зі скла? *(Is this glass made of glass?)*
> — **Марія:** Ні, вона з пластику. *(No, it is from plastic.)*
> — **Олег:** А цей стіл з дерева? *(And is this table from wood?)*
> — **Марія:** Так, це дуже дороге дерево. *(Yes, it is very expensive wood.)*
> — **Олег:** У тебе гарний смак. *(You have good taste.)*

> — **Катерина:** Який смачний торт! З чого він? *(What a tasty cake! What is it from?)*
> — **Олена:** Це торт із шоколаду. *(This is a cake from chocolate.)*
> — **Катерина:** Я думала, що він із фруктів. *(I thought that it was from fruits.)*

Коли це почалося? *(When did this start?)*
Ми використовуємо цей прийменник для часу. *(We use this preposition for time.)*
Він показує початок дії. *(It shows the start of an action.)*

Just as this preposition shows the starting point in space, it also shows the starting point in time. When you want to say that something has been happening since a certain time or day, you use this preposition with the Genitive case. It marks the exact moment an action began and often implies it continues into the present. Later in this module, we will contrast this with the word for "after", which describes what happens following a completely finished event.

«ранок → з ранку» *(since morning)*
«понеділок → з понеділка» *(since Monday)*
«дитинство → з дитинства» *(since childhood)*
«канікули → з канікул» *(since vacation)*

Читаємо українською:
— Я працюю тут **з ранку** *(since morning)*.
— Цей магазин відкритий **з понеділка** *(since Monday)*.
— Ми знаємо одне одного **з дитинства** *(since childhood)*.
— Вони повернулися **з канікул** *(from vacation)*.
— Він читає цю книгу **з вечора** *(since evening)*.
— Студенти чекають **з обіду** *(since lunch)*.

> — **Ірина:** Ти давно тут чекаєш? *(Have you been waiting here long?)*
> — **Павло:** Так, я тут з ранку. *(Yes, I have been here since morning.)*
> — **Ірина:** Ого! А я працюю з понеділка без вихідних. *(Wow! And I am working since Monday without days off.)*
> — **Павло:** Тобі треба відпочити. *(You need to rest.)*

> — **Максим:** Коли ми починаємо новий проєкт? *(When do we start the new project?)*
> — **Директор:** Ми починаємо з вівторка. *(We start on Tuesday.)*
> — **Максим:** Добре, я буду готовий з ранку. *(Good, I will be ready from the morning.)*

Говоріть правильно. *(Speak correctly.)*
Важливо знати історію слів. *(It is important to know the history of words.)*

:::tip Деколонізація (Decolonization)
The only correct way to express origin from Ukraine is «з України». This derives directly from the correct locative form «в Україні» *(in Ukraine)*. You may sometimes hear obsolete forms that treat Ukraine as a region rather than a sovereign independent state; those are incorrect and stem from colonial influence. Furthermore, the rich system of euphony with three distinct preposition forms is a beautiful, defining phonetic feature of the language that clearly distinguishes it from neighboring Slavic systems. Embrace these phonetic variants because they make your speech sound naturally and authentically Ukrainian.
:::

<!-- INJECT_ACTIVITY: quiz-euphony-variants -->

## Від кого? Від + родовий (From Whom? Від + Genitive)

Коли ми отримуємо щось від людини, ми використовуємо прийменник «від». *(When we receive something from a person, we use the preposition "від".)* It works exactly like "from" in English when talking about a sender or a source that is a living being or an organization. After "від", the noun must be in the Genitive case. Let us review the Genitive endings for people. Most masculine nouns representing people take "-а" or "-я". Most feminine nouns take "-и" or "-і". It is very important to change the ending when you say who gave you a gift or sent you a message.

«мама → від мами» *(from mom)*
«друг → від друга» *(from a friend)*
«сусід → від сусіда» *(from a neighbor)*
«Олена → від Олени» *(from Olena)*

Читаємо українською:
— Я маю новий лист **від мами** *(from mom)*.
— Це чудовий подарунок **від друга** *(from a friend)*.
— Ми почули гарні новини **від сусіда** *(from a neighbor)*.
— Вона отримала великий привіт **від Олени** *(from Olena)*.
— Це повідомлення **від директора** *(from the director)*.
— Він чекає дзвінка **від лікаря** *(from the doctor)*.

> — **Анна:** Від кого цей довгий лист? *(From whom is this long letter?)*
> — **Богдан:** Це лист від брата. *(This is a letter from brother.)*
> — **Анна:** Що він там пише? *(What does he write there?)*
> — **Богдан:** Він передає великий привіт від сім'ї. *(He sends a big greeting from the family.)*

Very often, English speakers confuse "з" and "від" because both translate to the English word "from". However, in Ukrainian, there is a strict rule for choosing the right preposition. We use "з" (or its phonetic variants "із" and "зі") for places, geography, and materials. We use "від" exclusively for people, animals, and entities acting as a source. If you receive a package, the city it came from takes "з", but the specific person who sent it takes "від".

«з Києва» *(from Kyiv — place)*
«від Олени» *(from Olena — person)*
«з університету» *(from the university — place)*
«від викладача» *(from the professor — person)*

Читаємо українською:
— Я отримав важку посилку **з Одеси** *(from Odesa)*.
— Я отримав важливу посилку **від сестри** *(from sister)*.
— Цей красивий сувенір **з Італії** *(from Italy)*.
— Цей невеликий сувенір **від колеги** *(from a colleague)*.
— Він пізно повернувся **з роботи** *(from work)*.
— Він має нове завдання **від менеджера** *(from the manager)*.

> — **Олег:** Звідки цей смачний торт? *(Where is this tasty cake from?)*
> — **Марія:** Це свіжий торт з пекарні. *(This is a fresh cake from the bakery.)*
> — **Олег:** А від кого він? *(And from whom is it?)*
> — **Марія:** Це приємний сюрприз від друзів. *(This is a pleasant surprise from friends.)*

Як далеко це розташовано? *(How far is it located?)* The preposition "від" is also used to describe how far or near something is from a reference point in space. We frequently pair it with adverbs like "далеко" (far) and "недалеко" (not far, nearby). The reference point is always in the Genitive case. For places and abstract concepts, masculine nouns often take the "-у" or "-ю" ending. Neuter nouns take "-а" or "-я".

«центр → далеко від центру» *(far from the center)*
«вокзал → недалеко від вокзалу» *(not far from the station)*
«море → далеко від моря» *(far from the sea)*
«школа → недалеко від школи» *(not far from the school)*

Читаємо українською:
— Мій старий дім знаходиться далеко **від центру** *(from the center)*.
— Наш новий готель недалеко **від вокзалу** *(from the station)*.
— Вони живуть дуже далеко **від моря** *(from the sea)*.
— Її сучасний офіс недалеко **від метро** *(from the subway)*.
— Цей зелений парк розташований недалеко **від річки** *(from the river)*.
— Головний аеропорт стоїть далеко **від міста** *(from the city)*.

> — **Катерина:** Ваш новий дім далеко від центру? *(Is your new house far from the center?)*
> — **Віктор:** Ні, він зовсім недалеко від парку. *(No, it is quite not far from the park.)*
> — **Катерина:** Це напевно дуже зручно. *(This is probably very convenient.)*
> — **Віктор:** Так, але це далеко від роботи. *(Yes, but it is far from work.)*

Що нас захищає? *(What protects us?)* We use "від" to talk about things that provide protection, relief, or defense against something unpleasant. When you buy medicine or use an umbrella, you are protecting yourself "from" something. That unpleasant "something" must be in the Genitive case. 

«головний біль → ліки від головного болю» *(medicine for a headache)*
«дощ → парасолька від дощу» *(umbrella from the rain)*
«сонце → захист від сонця» *(protection from the sun)*
«стрес → відпочинок від стресу» *(rest from stress)*

Читаємо українською:
— Мені терміново потрібні ліки **від головного болю** *(for a headache)*.
— Вона взяла велику парасольку **від дощу** *(from the rain)*.
— Цей дорогий крем — хороший захист **від сонця** *(from the sun)*.
— Ми завжди п'ємо таблетки **від застуди** *(for a cold)*.

As a bonus, Ukrainian has a compound preposition "з-під" which means "from under". It combines the idea of origin ("from") and location ("under") into one word, and it also takes the Genitive case. This is used when you pull something out from beneath an object.

«стіл → з-під стола» *(from under the table)*
«ліжко → з-під ліжка» *(from under the bed)*

Читаємо українською:
— Сірий кіт швидко виліз **з-під ліжка** *(from under the bed)*.
— Я обережно дістав сумку **з-під стола** *(from under the table)*.
— Маленький собака дивиться **з-під ковдри** *(from under the blanket)*.

> — **Олена:** У тебе є таблетки від головного болю? *(Do you have pills for a headache?)*
> — **Павло:** Так, вони лежать там. *(Yes, they lie there.)*
> — **Олена:** Де саме вони лежать? *(Where exactly do they lie?)*
> — **Павло:** Дістань їх з-під журналу. *(Get them from under the magazine.)*
> — **Олена:** Дякую, я вже знайшла їх. *(Thank you, I already found them.)*

<!-- INJECT_ACTIVITY: fill-in-focus-complete-sentences-with-or-correct-genitive-noun-form -->

## Що було потім? Після + родовий (What Happened Next? Після + Genitive)

Life is a series of events happening one after another. When we want to talk about what follows an event, we use the preposition **після** *(after)*. This is an essential building block for telling stories or describing your day. Just like the prepositions we learned for origin and protection, **після** always demands the Genitive case. It acts as the key to creating logical time sequences in your narratives. Whenever you use a noun to mark a point in time, **після** tells us what happens next.

«урок → після уроку» *(after the lesson)*
«обід → після обіду» *(after lunch)*
«робота → після роботи» *(after work)*
«канікули → після канікул» *(after the holidays)*

Читаємо українською:
— Вони завжди п'ють каву **після уроку** *(after the lesson)*.
— Ми зустрінемося в парку **після обіду** *(after lunch)*.
— Він часто ходить в спортзал **після роботи** *(after work)*.
— Студенти повертаються додому **після канікул** *(after the holidays)*.
— Що ви зазвичай робите **після сніданку** *(after breakfast)*?

> — **Анна:** Що ти робиш сьогодні **після уроку**? *(What are you doing today after the lesson?)*
> — **Марко:** Я йду в центральну бібліотеку. *(I am going to the central library.)*
> — **Анна:** А що ти будеш робити **після бібліотеки**? *(And what will you do after the library?)*
> — **Марко:** **Після навчання** я планую зустрітися з друзями. *(After studying I plan to meet with friends.)*
> — **Анна:** Можна я піду з вами **після роботи**? *(May I go with you after work?)*
> — **Марко:** Звісно, ми завжди раді тобі. *(Of course, we are always glad to have you.)*
> — **Анна:** Тоді я зателефоную вам **після зміни**. *(Then I will call you after the shift.)*

Let's quickly review the Genitive endings, specifically focusing on the nouns we often use to measure time and events. Hard masculine nouns taking "-у" are very common in this context, but you must also pay attention to soft nouns and words ending in sibilants. Feminine words ending in "-ія" smoothly change to "-ії". Neuter words ending in "-о" change to "-а", and soft masculine words take "-я". Paying attention to these subtle changes will make your Ukrainian sound precise and educated. Remember that **після** is always followed by the Genitive case.

«лекція → після лекції» *(after the lecture)*
«свято → після свята» *(after the holiday)*
«день → після дня» *(after the day)*
«зустріч → після зустрічі» *(after the meeting)*

Читаємо українською:
— Вона завжди дуже втомлена **після лекції** *(after the lecture)*.
— Нам треба прибрати в кімнаті **після свята** *(after the holiday)*.
— Він любить гуляти містом **після важкого дня** *(after a hard day)*.
— Директор напише звіт **після зустрічі** *(after the meeting)*.
— Мій брат завжди повертається пізно **після зміни** *(after the shift)*.
— Ми любимо спати довго **після подорожі** *(after the trip)*.

> — **Надія:** Коли ми поїдемо в центр міста? *(When will we go to the city center?)*
> — **Тарас:** Ми поїдемо туди **після свята**. *(We will go there after the holiday.)*
> — **Надія:** А магазин працює **після вихідних**? *(And does the store work after the weekend?)*
> — **Тарас:** Так, він відкриється у понеділок. *(Yes, it will open on Monday.)*
> — **Надія:** Тоді ми купимо все **після зустрічі**. *(Then we will buy everything after the meeting.)*

The preposition **після** is incredibly useful for describing your daily routine. It helps you connect your individual actions into a smooth narrative rather than reciting a list of disconnected sentences. By using this structure, your conversational Ukrainian will sound much more natural and cohesive. Look at how a simple sequence of events builds a complete and detailed picture of a normal day. Notice how the Genitive case seamlessly links the action to the time it occurs.

:::note
Notice that **після** often starts the sentence when describing a routine. This naturally shifts the focus to the timeline of your actions.
:::

«сніданок → після сніданку» *(after breakfast)*
«вечеря → після вечері» *(after dinner)*
«фільм → після фільму» *(after the film)*

Читаємо українською:
— **Після сніданку** я швидко йду на роботу. *(After breakfast I quickly go to work.)*
— **Після роботи** вона завжди готує смачну вечерю. *(After work she always cooks a delicious dinner.)*
— **Після вечері** ми зазвичай дивимося новий фільм. *(After dinner we usually watch a new film.)*
— **Після фільму** я відразу лягаю спати. *(After the film I immediately go to sleep.)*
— Вони читають новини **після пробудження** *(after waking up)*.

> — **Марія:** Як проходить твій звичайний день? *(How does your usual day go?)*
> — **Олег:** **Після сніданку** я відразу починаю працювати. *(After breakfast I immediately start working.)*
> — **Марія:** Ти працюєш вдома чи в офісі? *(Do you work at home or in the office?)*
> — **Олег:** Вдома, а **після роботи** я йду на пробіжку. *(At home, and after work I go for a jog.)*
> — **Марія:** Що ти робиш **після довгої пробіжки**? *(What do you do after a long jog?)*
> — **Олег:** **Після прохолодного душу** я готую легку вечерю. *(After a cool shower I cook a light dinner.)*
> — **Марія:** А **після вечері** ти відпочиваєш? *(And after dinner do you rest?)*
> — **Олег:** Так, **після смачної вечері** я зазвичай читаю. *(Yes, after a delicious dinner I usually read.)*

To truly solidify your understanding, it is highly helpful to contrast **після** *(after)* with its exact opposite: **до** *(before)*. Both of these time prepositions strictly require the Genitive case. You can effectively think of them as a grammatical "case-pair". Whenever you learn a new event noun, practice it with both **до** and **після** to double your descriptive power immediately. This structural symmetry makes remembering the grammar rule much easier for learners. Seeing them side-by-side reinforces the pattern in your memory.

:::tip
Use the pair **до** and **після** together to describe a complete timeline. Since both take the Genitive case, you only need to remember one ending for the noun!
:::

«до обіду» *(before lunch)* / «після обіду» *(after lunch)*
«до війни» *(before the war)* / «після війни» *(after the war)*
«до лекції» *(before the lecture)* / «після лекції» *(after the lecture)*
«до сніданку» *(before breakfast)* / «після сніданку» *(after breakfast)*

Читаємо українською:
— Я маю зробити це завдання **до обіду** *(before lunch)*.
— Ми обговоримо всі деталі **після обіду** *(after lunch)*.
— Їхнє життя було зовсім іншим **до війни** *(before the war)*.
— Ми обов'язково відбудуємо місто **після війни** *(after the war)*.
— Студенти повинні прочитати текст **до лекції** *(before the lecture)*.
— Викладач відповість на запитання **після лекції** *(after the lecture)*.

> — **Віктор:** Ти п'єш каву **до сніданку** чи **після сніданку**? *(Do you drink coffee before breakfast or after breakfast?)*
> — **Катерина:** Я завжди п'ю каву тільки **після сніданку**. *(I always drink coffee only after breakfast.)*
> — **Віктор:** А я люблю випити чашку ще **до роботи**. *(And I like to drink a cup even before work.)*
> — **Катерина:** Я розумію, але я не можу пити каву **до їди**. *(I understand, but I cannot drink coffee before food.)*
> — **Віктор:** Це логічно. А що ти робиш **після вечері**? *(This is logical. And what do you do after dinner?)*
> — **Катерина:** **До сну** я просто читаю цікаву книгу. *(Before sleep I just read an interesting book.)*
> — **Віктор:** А я **після фільму** відразу йду спати. *(And I immediately go to sleep after a film.)*

<!-- INJECT_ACTIVITY: match-up-preposition-meanings -->
<!-- INJECT_ACTIVITY: group-sort-preposition-usage -->

:::note Джерела
Цей модуль використовує матеріали: Заболотний Grade 5, §31 та ULP: 10 Uses of Genitive Case.
:::

## Підсумок — Summary

You have mastered three prepositions that require the Genitive case. Let's review the main concepts.

How do we say we are "from" a city? We use **з** *(from)* plus the Genitive case: «Вона з Києва» *(She is from Kyiv)*.

When do we use **зі** instead of **з**? We use it before a consonant cluster for easier pronunciation. For example: «Я зі Львова» *(I am from Lviv)* or «Він іде зі школи» *(He is walking from school)*.

What is the difference between **з** and **від**? Both mean "from", but **з** indicates a place or material, while **від** indicates a person as the source. Compare: «Лист з Америки» *(A letter from America)* versus «Лист від брата» *(A letter from a brother)*.

Which case follows **після** *(after)*? It strictly requires the Genitive case, just like **до** *(before)*.

Читаємо українською:
> — **Питання:** Як правильно: з Львова чи зі Львова? *(Question: How is it correct: з Львова or зі Львова?)*
> — **Відповідь:** Правильно говорити «зі Львова». *(Answer: It is correct to say "зі Львова".)*
> — **Питання:** Який відмінок після прийменника «після»? *(Question: Which case is after the preposition "після"?)*
> — **Відповідь:** Тільки родовий відмінок. *(Answer: Only the Genitive case.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-source
level: a2

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

**Level: A2 (Module 9/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
