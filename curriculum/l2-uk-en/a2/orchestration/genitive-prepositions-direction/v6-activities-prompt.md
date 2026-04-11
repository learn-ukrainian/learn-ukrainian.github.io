<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-direction.yaml` file for module **11: Куди? До якого часу?** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-genitive-forms -->`
- `<!-- INJECT_ACTIVITY: match-up-functions -->`
- `<!-- INJECT_ACTIVITY: group-sort-categories -->`
- `<!-- INJECT_ACTIVITY: quiz-meaning-choice -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct meaning of до in context (direction, time, purpose)
  items: 8
  type: quiz
- focus: Complete sentences with до + correct Genitive noun form
  items: 8
  type: fill-in
- focus: Match до-phrases with their functions (direction, time limit, purpose)
  items: 8
  type: match-up
- focus: Sort до-phrases by meaning category (direction vs. time vs. purpose)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ставлення (attitude)
- інтерес (interest)
- готовий (ready)
- завтра (tomorrow)
required:
- напрямок (direction)
- мета (goal, purpose)
- музей (museum)
- лікар (doctor)
- бабуся (grandmother)
- вечір (evening)
- ранок (morning)
- екзамен (exam)
- побачення (meeting, date; goodbye in 'до побачення')
- список (list)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ та діалог

> — **Пасажир:** Добрий день! Мені потрібно до вокзалу *(to the station)*, будь ласка. Ви вільні?
> — **Таксист:** Добрий день! Так, сідайте. Їдемо до центрального вокзалу?
> — **Пасажир:** Так. Але спочатку, будь ласка, поїдемо до аптеки *(to the pharmacy)*. Мені дуже треба купити ліки.
> — **Таксист:** Добре, я знаю, де є аптека. Вона біля старого парку.
> — **Пасажир:** Дякую. Скажіть, а ви можете чекати мене там до п'ятої години *(until five o'clock)*?
> — **Таксист:** Звичайно, я можу чекати вас до п'ятої години. Це не проблема.
> — **Пасажир:** Чудово! А вже потім ми поїдемо до готелю *(to the hotel)* «Україна».
> — **Таксист:** Зрозумів вас. Наш маршрут: спочатку до аптеки, чекаємо до п'ятої години, а потім їдемо до готелю. Поїхали!

In the A1 level, we learned how to describe where something is located. Now, in A2, we are moving beyond simple location to express direction, purpose, and time limits. The key to all of these is the small but powerful preposition **до** *(to, toward, until)*. Whether you are traveling to a specific destination, setting a deadline, or going to see a person, **до** is your primary tool. It translates to "toward" when discussing movement, and "until" when discussing time.

The most important rule to remember is that the preposition **до** always requires the Genitive case *(родовий відмінок)*. When you say "to the station," **вокзал** *(station)* becomes **до вокзалу**. When you say "until morning," **ранок** *(morning)* becomes **до ранку**. Let us explore how this works in practice.

:::tip Читаємо українською
Я йду до парку. *(I am going to the park.)*
Ми їдемо до Києва. *(We are traveling to Kyiv.)*
Він працює до вечора. *(He works until evening.)*
Вона чекає до завтра. *(She is waiting until tomorrow.)*
:::

## Куди ти йдеш? До + родовий для напрямку (Where Are You Going? До + Genitive for Direction)

Коли ми плануємо подорож, ми завжди маємо **напрямок** *(direction)*. To express your destination, Ukrainian uses the preposition **до** *(to, toward)* followed by the Genitive case *(родовий відмінок)*. Let us start with geographical locations like cities and countries. For masculine cities, the Genitive ending is usually **-а** or **-я**. For feminine countries, the ending is usually **-и** or **-ії**. This is how we build the phrase "to the city" or "to the country". When talking about moving towards places, these endings are extremely consistent.

:::tip Читаємо українською
— Я їду до Києва. *(I am going to Kyiv.)*
— Завтра ми їдемо до Львова. *(Tomorrow we are traveling to Lviv.)*
— Вони летять до Харкова. *(They are flying to Kharkiv.)*
— Моя сестра їде до України. *(My sister is traveling to Ukraine.)*
— Студенти їдуть до Польщі. *(The students are going to Poland.)*
— Мій друг поїхав до Франції. *(My friend went to France.)*
:::

> — **Олена:** Привіт! Ти куди їдеш на вихідні? *(Hi! Where are you going for the weekend?)*
> — **Марко:** Я їду до Одеси. А ти? *(I am going to Odesa. And you?)*
> — **Олена:** Я залишаюся тут. Але влітку я планую поїхати до Італії. *(I am staying here. But in the summer I plan to go to Italy.)*
> — **Марко:** Чудово! Передавай вітання! *(Wonderful! Send my regards!)*

Sometimes our destination is not a city or a building, but a person. We go "to see someone" or "to someone's place". In Ukrainian, this is always expressed using **до** plus the Genitive case of the person. You can never use the prepositions **в** *(in/into)* or **на** *(on/onto)* when the destination is a living being. This is a very common mistake for learners, who might translate directly from English and try to say «**в лікар**» *(into the doctor)*. Instead, you must always use **до лікаря** *(to the doctor)*. This rule applies to all professions, family members, and friends.

:::tip Читаємо українською
— Я йду до лікаря, тому що я хворий. *(I am going to the doctor because I am sick.)*
— На вихідних ми їдемо до бабусі. *(On the weekend we are going to grandmother's.)*
— Увечері я йду до сусіда. *(In the evening I am going to the neighbor's.)*
— Ти йдеш до вчителя після уроку? *(Are you going to the teacher after the lesson?)*
— Вони їдуть до друзів. *(They are going to their friends' place.)*
:::

> — **Анна:** Ти вільний сьогодні ввечері? *(Are you free tonight?)*
> — **Ігор:** Ні, я йду до друга. У нього день народження. *(No, I am going to a friend's place. It is his birthday.)*
> — **Анна:** Зрозуміло. А завтра? *(Understood. And tomorrow?)*
> — **Ігор:** Завтра зранку я маю йти до стоматолога. *(Tomorrow morning I have to go to the dentist.)*

You might remember from the A1 level that we can also use **в** or **на** with the Accusative case to show direction, for example, «**іду в магазин**» *(I am going into the store)*. So, what is the exact difference between **до магазину** *(toward the store)* and **в магазин** *(into the store)*? The preposition **до** emphasizes the journey or the movement toward the vicinity of the destination. You are heading *toward* the store. The preposition **в** emphasizes entering the destination itself. Both are grammatically correct and completely standard in Ukrainian. You can use whichever fits your focus: the journey or the final entry.

:::tip Читаємо українською
— Я йду до магазину. *(I am walking toward the store.)*
— Я йду в магазин. *(I am going into the store.)*
— Ми їдемо до університету. *(We are traveling toward the university.)*
— Ми йдемо в університет. *(We are going inside the university.)*
— Він іде до парку. *(He is heading to the park.)*
:::

> — **Тарас:** Де ти зараз? *(Where are you now?)*
> — **Марія:** Я йду до метро. *(I am walking to the subway.)*
> — **Тарас:** Ти вже в метро? *(Are you inside the subway?)*
> — **Марія:** Ще ні, я тільки підходжу до станції. *(Not yet, I am just approaching the station.)*

To form the Genitive case correctly with **до**, pay close attention to the stem of the noun. For masculine nouns, hard stems often take **-у**, while soft stems take **-ю**. However, remember that specific objects, people, and cities usually take **-а** or **-я**. Institutions, abstract concepts, and large buildings usually take **-у** or **-ю**. For feminine nouns, hard stems take **-и**, while soft stems take **-ії** or **-і** (especially if they end in a sibilant sound like "щ", "ч", or "ш"). Knowing these patterns will help you guess the right ending for new words.

:::note Форми родового відмінка (Genitive Forms)
**Чоловічий рід (Masculine):**
будинок *(building)* → до будинку
музей *(museum)* → до музею
університет *(university)* → до університету

**Жіночий рід (Feminine):**
школа *(school)* → до школи
станція *(station)* → до станції
площа *(square)* → до площі

**Середній рід (Neuter):**
море *(sea)* → до моря
:::

:::tip Читаємо українською
— Вони йдуть до великого будинку. *(They are going to the big building.)*
— Туристи їдуть до музею. *(The tourists are going to the museum.)*
— Студенти поспішають до університету. *(The students are hurrying to the university.)*
— Діти йдуть до школи. *(The children are going to school.)*
— Машина під'їхала до станції. *(The car drove up to the station.)*
— Ми йдемо до центральної площі. *(We are going to the central square.)*
:::

<!-- INJECT_ACTIVITY: fill-in-genitive-forms -->

When you add adjectives to describe your destination, they must also match the Genitive case. For masculine and neuter adjectives, the ending is **-ого**. For feminine adjectives, the ending is **-ої**. Adjectives always follow the noun they describe in gender, number, and case. This makes the whole phrase "agree" perfectly. You will hear this matching rhythm clearly when Ukrainians speak.

:::note Узгодження прикметників (Adjective Agreement)
новий будинок *(new building)* → до нового будинку
велика станція *(big station)* → до великої станції
старий друг *(old friend)* → до старого друга
:::

:::tip Читаємо українською
— Ми йдемо до нового будинку. *(We are going to the new building.)*
— Поїзд прибуває до великої станції. *(The train is arriving at the big station.)*
— Я їду до старого друга. *(I am traveling to an old friend.)*
— Вона йде до гарної школи. *(She is going to a beautiful school.)*
— Туристи їдуть до історичного музею. *(The tourists are going to the historical museum.)*
:::

There is one special word you will use every single day: **додому** *(homeward, to home)*. Historically, it comes directly from the two-word phrase **до дому** *(to the house)*. Today, it is written as one single word and acts as a fixed adverb of direction. You do not need to think about cases or endings here; just use it as a complete direction word whenever you are heading back to your own house or apartment.

:::tip Читаємо українською
— Після роботи я йду додому. *(After work I am going home.)*
— Діти дуже втомилися і хочуть додому. *(The children are very tired and want to go home.)*
— Коли ти поїдеш додому сьогодні? *(When will you go home today?)*
:::

## До якого часу? До + родовий для часу (Until When? До + Genitive for Time)

When you want to say how long an action continues, you use **до** *(until)* plus the Genitive case. This marks the absolute boundary or the end of a time period. If you start a task in the morning and stop in the evening, you work until the evening arrives. 

It is crucial to remember the endings for masculine nouns when talking about time. Specific units of time, like days of the week or months, are masculine nouns that take the **-а** or **-я** ending in the Genitive case, not **-у**. Therefore, **день** *(day)* becomes **до дня**, and **вівторок** *(Tuesday)* becomes **до вівторка**.

:::note Форми часу (Time Forms)
**вечір** *(evening)* → **до вечора** *(until evening)*
**ранок** *(morning)* → **до ранку** *(until morning)*
**літо** *(summer)* → **до літа** *(until summer)*
**понеділок** *(Monday)* → **до понеділка** *(until Monday)*
**вівторок** *(Tuesday)* → **до вівторка** *(until Tuesday)*
:::

:::tip Читаємо українською
— Я буду читати книгу до ранку. *(I will read the book until morning.)*
— Ми відпочиваємо на морі до літа. *(We are resting at the sea until summer.)*
— Цей великий магазин не працює до понеділка. *(This big store is not working until Monday.)*
— Мій старший брат зазвичай спить до обіду. *(My older brother usually sleeps until lunch.)*
:::

> — **Анна:** Ти довго вчора працював? *(Did you work long yesterday?)*
> — **Сергій:** Так, я писав звіт до пізнього вечора. *(Yes, I was writing the report until late evening.)*
> — **Анна:** Тобі треба більше відпочивати. *(You need to rest more.)*
> — **Сергій:** Знаю. Але я маю дуже багато роботи. *(I know. But I have a lot of work.)*

The preposition **до** also translates to "by" when you are setting a strict deadline. It shows the exact moment when a task must be finished, or when an event will definitely happen. If your teacher wants homework on Friday, you must do it by Friday.

To express exact hours for a deadline, Ukrainians use ordinal numbers in the feminine form. This is because the word **година** *(hour/o'clock)* is feminine. In the Genitive case, these adjectives take the **-ої** ending. For example, "by five o'clock" is **до п'ятої години**. In everyday conversation, the word **година** is frequently dropped entirely, and you just say **до п'ятої**. When using adverbs like **завтра** *(tomorrow)*, the word does not change its form at all.

:::note Дедлайни (Deadlines)
**п'ятниця** *(Friday)* → **до п'ятниці** *(by Friday)*
**восьма година** *(eighth hour)* → **до восьмої години** *(by eight o'clock)*
**завтра** *(tomorrow)* → **до завтра** *(by tomorrow)*
:::

:::tip Читаємо українською
— Будь ласка, зробіть це завдання до п'ятниці. *(Please, do this task by Friday.)*
— Я маю прийти до офісу до восьмої. *(I have to come to the office by eight.)*
— Підготуйте всі нові документи до завтра. *(Prepare all the new documents by tomorrow.)*
— Цей концерт на площі триватиме до десятої. *(This concert on the square will last until ten.)*
:::

To define a complete time range, you pair **до** *(to/until)* with **з** or **від** *(from)*. This creates the very common structure «from [start time] to [end time]». It is important to know that both the starting point and the ending point must be in the Genitive case. Both **з** and **від** are correct and interchangeable here.

For instance, "from morning to evening" becomes **з ранку до вечора**. When talking about hours or days of the week, the rule remains exactly the same: both words take Genitive endings to show the start and the finish of the duration.

:::note Проміжки часу (Time Ranges)
**ранок, вечір** → **з ранку до вечора** *(from morning to evening)*
**понеділок, п'ятниця** → **з понеділка до п'ятниці** *(from Monday to Friday)*
**дев'ята, шоста** → **з дев'ятої до шостої** *(from nine to six)*
:::

:::tip Читаємо українською
— Наш новий офіс працює з понеділка до п'ятниці. *(Our new office works from Monday to Friday.)*
— Я в університеті кожного дня з дев'ятої до шостої. *(I am at the university every day from nine to six.)*
— Лікар приймає пацієнтів від другої до п'ятої години. *(The doctor sees patients from two to five o'clock.)*
— Ми гуляли в парку з ранку до пізнього вечора. *(We walked in the park from morning to late evening.)*
:::

<!-- INJECT_ACTIVITY: match-up-functions -->

You will hear **до** used in many everyday fixed phrases. The most famous one is **до завтра**, which literally means "until tomorrow" but is used as a farewell, just like "see you tomorrow".

You will also see it combined with words like **початок** *(start)* and **кінець** *(end)*. To say "by the end", you use the Genitive form **до кінця**. The item that is ending also takes the Genitive case, creating a natural chain of words: **до кінця липня** *(by the end of July)* or **до кінця тижня** *(by the end of the week)*. Remember that words like **місяць** *(month)* and **тиждень** *(week)* take the soft **-я** ending in the Genitive case: **місяця**, **тижня**. Do not confuse **до** *(until/by)* with **перед** *(before, immediately prior)* or **після** *(after)*. Use **до** when describing a clear limit.

:::note Сталі вирази (Fixed Expressions)
**початок уроку** *(start of lesson)* → **до початку уроку** *(by the start of the lesson)*
**кінець літа** *(end of summer)* → **до кінця літа** *(by the end of summer)*
**кінець місяця** *(end of month)* → **до кінця місяця** *(by the end of the month)*
:::

> — **Олена:** Коли ти закінчиш цей складний проєкт? *(When will you finish this complicated project?)*
> — **Максим:** Я зроблю все до кінця тижня. *(I will do everything by the end of the week.)*
> — **Олена:** Добре. Тоді ми поговоримо про це в понеділок. *(Good. Then we will talk about it on Monday.)*
> — **Максим:** Так, звичайно. До завтра! *(Yes, of course. See you tomorrow!)*
> — **Олена:** До зустрічі! *(See you!)*

## До + родовий: решта значень та узагальнення (До + Genitive: Other Meanings and Summary)

Beyond physical movement and time, the preposition **до** *(to/for/until)* frequently expresses purpose *(мета)*, readiness, and abstract goals. When you are prepared for an event, you are "ready to" it in Ukrainian. We use the adjective **готовий** *(ready)* followed by **до** and the Genitive case. For example, **готовий до екзамену** *(ready for the exam)*, or **готовий до роботи** *(ready for work)*. This preposition also shows purpose in everyday fixed expressions. The common farewell **до побачення** *(goodbye)* literally means "until seeing". The conversational phrase **до речі** *(by the way)* translates directly to "to the point". If you buy a ticket, it is also a ticket "to" a specific destination: **квиток до Львова** *(ticket to Lviv)* or **квиток до театру** *(ticket to the theater)*.

:::note Мета і готовність (Purpose and Readiness)
**готовий до екзамену** *(ready for the exam)*
**готовий до уроку** *(ready for the lesson)*
**квиток до Львова** *(ticket to Lviv)*
**до речі** *(by the way)*
**до побачення** *(goodbye)*
:::

:::tip Читаємо українською
— Студенти вже готові до нового уроку. *(The students are already ready for the new lesson.)*
— Я маю два квитки до Києва на завтра. *(I have two tickets to Kyiv for tomorrow.)*
— До речі, де мій новий словник? *(By the way, where is my new dictionary?)*
— Ми готові до зими, ми купили теплий одяг. *(We are ready for winter, we bought warm clothes.)*
:::

You will also use **до** to show how concepts relate to one another, especially when adding something or expressing a personal attitude. If you want to include an item in a group, you "add to" the group. The verb **додати** *(to add)* pairs with **до** and the Genitive case. You might say **додати до списку** *(to add to the list)* when shopping, or **додати до чаю** *(to add to the tea)* when cooking. When expressing feelings or opinions about a subject, Ukrainian uses words like **ставлення** *(attitude)* and **інтерес** *(interest)* connected to the object with **до**. You can have an **інтерес до мови** *(interest in the language)* or a positive **ставлення до роботи** *(attitude toward work)*. These abstract connections follow the exact same grammatical rules as walking to a park. The structure remains perfectly consistent.

:::note Зв'язки та ставлення (Connections and Attitude)
**додати до списку** *(add to the list)*
**додати до чаю** *(add to the tea)*
**ставлення до роботи** *(attitude toward work)*
**інтерес до історії** *(interest in history)*
:::

> — **Олег:** Ти можеш додати молоко до моєї кави? *(Can you add milk to my coffee?)*
> — **Ганна:** Так, звичайно. До речі, ти готовий до екзамену? *(Yes, of course. By the way, are you ready for the exam?)*
> — **Олег:** Майже. У мене великий інтерес до історії. *(Almost. I have a great interest in history.)*
> — **Ганна:** Це чудово. Твоє ставлення до навчання дуже гарне. *(That is wonderful. Your attitude toward studying is very good.)*

<!-- INJECT_ACTIVITY: group-sort-categories -->

Let us consolidate what we know about the Genitive case by comparing three essential prepositions: **до** *(to/until)*, **від** *(from)*, and **після** *(after)*. All three require the following noun to take Genitive endings, but they move our focus in different directions across space and time. **Від** marks the starting point of a journey or a time period. **До** marks the destination, the limit, or the final goal. **Після** shows what happens next in a sequence. You can map a complete experience using just these three words. For example, you travel **від вокзалу** *(from the station)*, you go **до готелю** *(to the hotel)*, and you rest **після поїздки** *(after the trip)*. Understanding this triad gives you the power to describe plans simply and accurately.

:::note Простір і час (Space and Time)
**від вокзалу** *(from the station)* → **до готелю** *(to the hotel)* → **після поїздки** *(after the trip)*
**від ранку** *(from the morning)* → **до вечора** *(until the evening)* → **після вечері** *(after dinner)*
:::

:::tip Читаємо українською
— Я їду від університету до бібліотеки. *(I am riding from the university to the library.)*
— Після роботи ми йдемо до нового ресторану. *(After work we are going to a new restaurant.)*
— Від понеділка до п'ятниці я дуже зайнятий. *(From Monday to Friday I am very busy.)*
— Після уроку студенти пішли до парку. *(After the lesson the students went to the park.)*
:::

<!-- INJECT_ACTIVITY: quiz-meaning-choice -->

Finally, it is crucial to avoid a common mistake influenced by Russian syntax. In Russian, movement toward a person is expressed with "к" and the Dative case. In Ukrainian, movement toward a person always requires **до** and the Genitive case. You must say **до мами** *(to mom)*, **до лікаря** *(to the doctor)*, or **до друга** *(to a friend)*. Using "к" for direction is a calque that sounds unnatural and incorrect in modern Ukrainian. The preposition **до** is the only authentic way to express movement toward people and time limits. Embrace this preposition as a core feature of natural Ukrainian sentence structure. Using it correctly will make your speech sound significantly more fluent.

## Підсумок — Summary

Ми вивчили дуже важливий прийменник **до** *(to/until/by)*. He is a versatile tool in your Ukrainian vocabulary. This single preposition connects space, time, and abstract concepts, always requiring the noun to take the Genitive case. Let us summarize his three main jobs.

:::note Три ролі прийменника ДО (Three Roles of ДО)
| Функція *(Function)* | Питання *(Question)* | Приклад *(Example)* |
| :--- | :--- | :--- |
| **1. Напрямок** *(Direction)* | Куди? *(Where to?)* | **до Києва** *(to Kyiv)*, **до мами** *(to mom)* |
| **2. Час** *(Time limit/deadline)* | До якого часу? *(Until/by when?)* | **до вечора** *(until evening)*, **до п'ятниці** *(by Friday)* |
| **3. Мета** *(Purpose)* | Для чого? *(What for?)* | **до побачення** *(goodbye)*, **до речі** *(by the way)* |
:::

:::tip Читаємо українською
— Влітку ми їдемо до Львова. *(In the summer we are riding to Lviv.)*
— Завтра я йду до лікаря. *(Tomorrow I am going to the doctor.)*
— Я маю працювати до вечора. *(I have to work until evening.)*
— Мені треба зробити це до п'ятниці. *(I need to do this by Friday.)*
:::

Now, a quick self-check. Як сказати "by 5 o'clock"? Remember that time limits and deadlines always use **до** plus the Genitive case. 

Чому ми кажемо "до лікаря", а не "в лікар"? Because movement toward a person or a professional always requires **до**, never "в" or "на". Master this rule to sound much more natural in everyday conversations.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-direction
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

**Level: A2 (Module 11/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
