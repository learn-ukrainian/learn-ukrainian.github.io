<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/foundations-practice.yaml` file for module **7: Перші кроки в А2** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-planning-party -->`
- `<!-- INJECT_ACTIVITY: fill-in-shopping-groceries -->`
- `<!-- INJECT_ACTIVITY: match-up-story-completion -->`
- `<!-- INJECT_ACTIVITY: match-up-short-narrative -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Role-play: Planning a Party (aspect in future tense)'
  items: 8
  type: quiz
- focus: 'Role-play: Shopping for Groceries'
  items: 8
  type: fill-in
- focus: 'Story Completion: Choose the Right Aspect'
  items: 8
  type: match-up
- focus: Answering questions about a short narrative
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- сценарій (scenario)
- діалог (dialogue)
- обговорювати (to discuss)
- замовляти / замовити (to order)
required:
- планувати / запланувати (to plan)
- купувати / купити (to buy)
- готувати / приготувати (to cook, prepare)
- ринок (market)
- коштувати (to cost)
- кілограм (kilogram)
- вечірка (party)
- день (day)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Сценарій 1: Плануємо вечірку (Scenario 1: Planning a Party)

Planning a **вечірка** (party) or a **новосілля** (housewarming party) requires shifting between discussing ongoing processes—what you will be doing all week—and concrete results—what you will actually get done before the guests arrive.

> — **Максим:** Привіт, Олено! Ми хочемо **запланувати** новосілля на суботу. *(Hi, Olena! We want to plan a housewarming party for Saturday.)*
> — **Олена:** Чудова ідея! Що ми будемо **готувати**? *(Great idea! What will we be cooking?)*
> — **Максим:** Ми будемо обговорювати меню сьогодні ввечері. *(We will be discussing the menu tonight.)*
> — **Олена:** Добре. Я буду **купувати** напої та закуски. *(Good. I will be buying drinks and snacks.)*
> — **Максим:** А я буду прибирати квартиру і мити вікна. *(And I will be cleaning the apartment and washing windows.)*
> — **Олена:** Скільки гостей ми будемо запрошувати? *(How many guests will we be inviting?)*
> — **Максим:** Десь десять або дванадцять людей. *(Around ten or twelve people.)*
> — **Олена:** Тоді нам треба дуже багато їжі! Мені треба **приготувати** багато салатів. *(Then we need a lot of food! I need to prepare a lot of salads.)*

Notice how Maksym and Olena use the future tense with imperfective verbs to discuss their strategy. They say «будемо обговорювати» (will be discussing) and «буду купувати» (will be buying). This structure always uses the helper verb **бути** (to be) plus the infinitive form of the main verb. We use this imperfective future to focus entirely on the *process* of an action, the ongoing planning phase, or a regular routine. However, when we want to focus on a specific *result* or a completed target, we use perfective verbs without the helper verb **бути**. Compare the long process of cooking with the satisfying result of a finished dish.

*   Я **буду готувати** вечерю довго. *(I will be cooking dinner for a long time. — Process)*
*   Мені треба **приготувати** смачний салат швидко. *(I need to prepare a delicious salad quickly. — Result)*
*   Ми **будемо планувати** свято разом. *(We will be planning the holiday together. — Process)*
*   Ми хочемо **запланувати** все сьогодні вранці. *(We want to plan everything today in the morning. — Result)*
*   Вони **будуть купувати** продукти. *(They will be buying products. — Process)*
*   Вони хочуть **купити** усе необхідне. *(They want to buy everything necessary. — Result)*
*   Сьогодні буде велика **вечірка**! *(Today there will be a big party!)*

As you organize a party, you often look around and realize what you are missing. To express absence or a lack of something in Ukrainian, we use the word **немає** (there is no / are no). Crucially, the word **немає** always triggers the Genitive case for the missing object. If you check the fridge and see that essential things are missing, the endings of those nouns must change to show that absence.

*   У нас **немає музики**. *(We have no music. — from музика)*
*   На столі ще **немає торта**. *(There is no cake on the table yet. — from торт)*
*   У мене зараз **немає вільного часу**. *(I have no free time right now. — from вільний час)*
*   У квартирі **немає великого столу**. *(There is no big table in the apartment. — from великий стіл)*
*   У нас **немає чистих тарілок**. *(We have no clean plates. — from чисті тарілки)*

The Genitive case is also strictly required when you talk about quantities using words like **багато** (much/many) and **мало** (little/few). Since a successful party usually requires multiple items for the guests, you will often use the plural Genitive form here. 

*   Нам треба купити **багато фруктів**. *(We need to buy many fruits.)*
*   У нас є **багато холодних напоїв**. *(We have many cold drinks.)*
*   На столі залишилося **мало паперових серветок**. *(There are few paper napkins left on the table.)*
*   У мене є **багато нових ідей**. *(I have many new ideas.)*
*   Тут дуже **мало вільного місця**. *(There is very little free space here.)*

### Читаємо українською (Reading Practice)
Зараз ми організовуємо велике свято вдома. *(Right now we are organizing a big holiday at home.)*
У нас є багато цікавих ідей. *(We have many interesting ideas.)*
Але у нас зовсім немає часу. *(But we have absolutely no time.)*
Моя сестра буде готувати смачну рибу. *(My sister will be cooking delicious fish.)*
А я буду купувати солодкий торт. *(And I will be buying a sweet cake.)*
Нам треба багато свіжих овочів. *(We need many fresh vegetables.)*
У магазині мало хороших фруктів. *(There are few good fruits in the store.)*
Тому ми йдемо на великий ринок. *(That is why we are going to the big market.)*
Там ми купимо все необхідне. *(There we will buy everything necessary.)*

Fast forward a few hours. The planning phase is over, and it is time to confirm the completed tasks. For this confirmation, we switch to the perfective past tense to show that the expected result has been fully achieved. 

> — **Олена:** Максиме, ти вже купив торт і фрукти? *(Maksym, have you already bought the cake and fruits?)*
> — **Максим:** Так, я купив великий торт і яблука. *(Yes, I bought a big cake and apples.)*
> — **Олена:** А що з нашою вечерею? *(And what about our dinner?)*
> — **Максим:** Ми замовили піцу. Вона скоро буде тут. *(We ordered pizza. It will be here soon.)*
> — **Олена:** Я вже приготувала салат і закуски. *(I have already prepared the salad and snacks.)*
> — **Максим:** Чудово! Я вже поставив тарілки на стіл. *(Great! I have already put the plates on the table.)*
> — **Олена:** Тоді усе готово до вечірки. *(Then everything is ready for the party.)*

In this second part, they do not use «купував» (was buying) or «замовляв» (was ordering). Instead, they use «купив» (bought) and «замовили» (ordered) because the action is absolutely complete and the pizza is already on its way.

:::tip Українська гостинність (Ukrainian Hospitality)
When hosting guests, Ukrainians love to use diminutive suffixes to make the atmosphere warmer and more inviting. Instead of a standard **торт** (cake), a host might offer you **тортик** (a nice little cake). A regular **салат** (salad) becomes a delicious **салатик**. You might even hear diminutives like **винце** (wine) instead of **вино**. These small changes show care, emotion, and true hospitality.
:::

<!-- INJECT_ACTIVITY: quiz-planning-party -->

## Сценарій 2: На ринку (Scenario 2: At the Market)

At a Ukrainian **ринок** (market), you will constantly use the Genitive case to ask for specific quantities, discuss prices, and ask what is currently available or missing. Pay close attention to how the shopper asks for quantities and how the vendor responds.

> — **Продавець:** Добрий день! Що будете купувати? *(Good day! What will you be buying?)*
> — **Покупець:** Добрий день! Скільки коштує кілограм меду? *(Good day! How much does a kilogram of honey cost?)*
> — **Продавець:** Цей свіжий мед коштує триста гривень. *(This fresh honey costs three hundred hryvnias.)*
> — **Покупець:** Добре. А у вас є свіжий сир? *(Good. And do you have fresh cottage cheese?)*
> — **Продавець:** Так, є дуже смачний сир. *(Yes, there is very tasty cottage cheese.)*
> — **Покупець:** Дайте мені, будь ласка, один кілограм меду і пів кілограма сиру. *(Give me, please, one kilogram of honey and half a kilogram of cottage cheese.)*
> — **Продавець:** Звісно. Щось іще? *(Of course. Anything else?)*
> — **Покупець:** Ні, дякую. Це все. *(No, thank you. That is all.)*

When you buy items by the piece or by weight, you must combine numbers with the correct noun form. The rule is based on the numbers 1, 2-4, and 5+.
*   **Один** (one) takes the Nominative case: **один лимон** (one lemon), **один кілограм** (one kilogram).
*   **Два, три, чотири** (two, three, four) take a form that looks like the Nominative Plural for masculine and feminine words, and Genitive Singular for neuter. At the market, you will often hear: **два лимони** (two lemons), **три кілограми** (three kilograms).
*   **П'ять і більше** (five and more) take the Genitive Plural. This is very common for small items or specific weights: **п'ять лимонів** (five lemons), **шість кілограмів** (six kilograms).

Here are a few more examples:
*   Дайте мені **один кавун**. *(Give me one watermelon.)*
*   Я хочу купити **три кавуни**. *(I want to buy three watermelons.)*
*   Дайте мені, будь ласка, **дві дині**. *(Give me, please, two melons.)*
*   Мені треба **п'ять кавунів**. *(I need five watermelons.)*

The Genitive case is also essential when something is missing or when you cannot see an item. This is called the Genitive of Negation. If a vendor runs out of a product, they will use the word **немає** (there is no) followed by the Genitive.
*   Вибачте, сьогодні **немає домашнього сиру**. *(Sorry, today there is no homemade cottage cheese.)*
*   У мене **немає свіжих яблук**. *(I do not have fresh apples.)*

If you are looking for something specific but cannot spot it on the counter, you also use the Genitive case after a negated verb. Compare the positive sentence with the negative one.
*   Я бачу червоні помідори. *(I see red tomatoes. — Accusative)*
*   Я не бачу **червоних помідорів**. *(I do not see red tomatoes. — Genitive)*

When asking for a **кілограм** (kilogram) of something, the product itself must be in the Genitive case. However, there is a difference between uncountable items and items you usually count. For uncountable products like **картопля** (potatoes) or **морква** (carrots), we use the Genitive Singular.
*   Дайте мені кілограм **картоплі**. *(Give me a kilogram of potatoes.)*
*   Скільки коштує кілограм **моркви**? *(How much does a kilogram of carrots cost?)*

For items that we naturally count, like **яблуко** (apple) or **помідор** (tomato), we use the Genitive Plural after «кілограм».
*   Я куплю кілограм **яблук**. *(I will buy a kilogram of apples.)*
*   Дайте два кілограми **помідорів**. *(Give two kilograms of tomatoes.)*

When speaking with vendors, Ukrainians frequently use diminutive suffixes. These small word endings make the conversation much friendlier and warmer. It is a sign of good rapport. If you use these forms, the vendor will smile and might even give you a **знижка** (discount).
*   Замість «картопля» продавці кажуть **картопелька**. *(Instead of "potatoes", vendors say "nice little potatoes".)*
*   Замість «морква» вони пропонують **морквочка**. *(Instead of "carrots", they offer "nice little carrots".)*
*   Замість «ягоди» ви почуєте **ягідки**. *(Instead of "berries", you will hear "nice little berries".)*

You do not have to use these words yourself, but you must be ready to understand them when the vendor offers you «свіжа картопелька» або «солодка морквочка».

Here is a quick summary of the essential verbs and nouns you need for a successful market trip. You already know **коштувати** (to cost). When you are at the stall, the vendor might let you **вибирати / вибрати** (to choose) the best tomatoes yourself. Once you make your choice, the vendor will **важити** (to weigh) the produce. Finally, after you pay, always remember to take your **решта** (change / money back).

### Читаємо українською (Reading Practice)
У суботу ми завжди ходимо на ринок. *(On Saturday we always go to the market.)*
Там продають дуже смачні продукти. *(There they sell very tasty products.)*
Сьогодні я хочу купити багато свіжих ягід. *(Today I want to buy many fresh berries.)*
Я підходжу до продавця і питаю ціну. *(I approach the vendor and ask the price.)*
Кілограм полуниці коштує сто гривень. *(A kilogram of strawberries costs one hundred hryvnias.)*
Я прошу зважити мені два кілограми. *(I ask to weigh two kilograms for me.)*
Продавець дає мені гарні ягоди і решту. *(The vendor gives me nice berries and the change.)*
Я дуже люблю цей старий ринок. *(I really love this old market.)*

<!-- INJECT_ACTIVITY: fill-in-shopping-groceries -->

## Сценарій 3: Як пройшов твій день? (Scenario 3: How Was Your Day?)

In Ukrainian, you must always choose between two perspectives when describing the past. Are you describing a continuous process, answering the question «Що ти робив?» (What were you doing?), or are you reporting a completed result, answering the question «Що ти зробив?» (What did you get done?). This choice completely changes the flavor of your sentence.

Here is a dialogue between two colleagues. One is focused on the tiring process of the day, while the other is focused on the concrete results they achieved.
> — **Марко:** Привіт, Олено! Як пройшов твій день? *(Hi, Olena! How was your day?)*
> — **Олена:** Ох, я дуже втомилася. Я цілий день **писала** звіти. *(Oh, I am very tired. I was writing reports all day.)*
> — **Марко:** А я сьогодні добре попрацював. Я **написав** три листи і **провів** важливу зустріч. *(And I worked well today. I wrote three letters and held an important meeting.)*
> — **Олена:** Ти молодець. А я ще **читала** нові документи. *(You are great. And I was also reading new documents.)*
> — **Марко:** Я вже **прочитав** їх вранці. *(I already read them in the morning.)*
> — **Олена:** Тепер я хочу просто відпочивати. *(Now I just want to rest.)*
> — **Марко:** Згоден, ходімо додому. *(Agreed, let's go home.)*

The Imperfective past tense describes an action as a process, a repeated event, or an ongoing state. It answers the question **«Що ти робив?»** (What were you doing?). You will often use it with words that signal duration or repetition, such as **довго** (for a long time), **цілий день** (all day), or **часто** (often). This aspect sets the scene and shows that the action took up time.
* Я вчора **довго читав** цікаву книгу. *(Yesterday I was reading an interesting book for a long time.)*
* Ми **весь вечір дивилися** фільм. *(We were watching a movie all evening.)*
* Вона **часто купувала** каву тут. *(She often bought coffee here.)*
* Студенти **цілий день писали** тест. *(The students were writing the test all day.)*
* Він **завжди робив** цю роботу добре. *(He always did this work well.)*

On the other hand, the Perfective past tense focuses entirely on the completion of the act. It answers the question **«Що ти зробив?»** (What did you do? / What did you get done?). You use the Perfective aspect when you want to show a sequence of completed events or a concrete milestone. Often, Ukrainian creates the Perfective form by adding a prefix like **по-**, **при-**, or **з-** to the Imperfective base word. For example, **снідати** (to be eating breakfast) becomes **поснідати** (to have finished breakfast), and **робити** (to be doing) becomes **зробити** (to have done).
* Спочатку я **поснідав**, потім **пішов** на роботу. *(First I had breakfast, then I went to work.)*
* Ввечері я **подивився** фільм. *(In the evening I watched [and finished] a movie.)*
* Вона **купила** новий телефон. *(She bought a new phone.)*
* Ми **зробили** домашнє завдання. *(We did the homework.)*
* Я нарешті **прочитав** цю книгу. *(I finally finished reading this book.)*

One of the most elegant ways to use aspects is the "Interruption Pattern" in a single sentence. Imagine the Imperfective aspect as a movie playing in the background, and the Perfective aspect as a sudden snapshot or a flash. You use the Imperfective for the ongoing background action, and the Perfective for the sudden event that interrupts it. The word **коли** (when) usually connects the two parts.
* Я **готував** вечерю, коли ти **подзвонив**. *(I was cooking dinner, when you called.)*
* Ми **йшли** в магазин, коли **почався** дощ. *(We were walking to the store when the rain started.)*
* Вона **читала** книгу, коли брат **зайшов** у кімнату. *(She was reading a book when the brother entered the room.)*
* Я **пив** каву, коли він **прийшов**. *(I was drinking coffee when he arrived.)*
* Діти **грали**, коли батько **купив** піцу. *(The children were playing when the father bought pizza.)*

:::tip Common L2 Error Alert
English speakers often translate "to take an exam" directly into the Russian-influenced phrase «здавати іспит». In authentic Ukrainian, you must use the verb **складати** (to put together) for the process, and its Perfective pair **скласти** for the successful result.
* Студенти зараз **складають** іспит. *(The students are taking the exam right now. — Imperfective process)*
* Я успішно **склав** іспит! *(I successfully passed the exam! — Perfective result)*
Never use «здавати» for exams. You can «здавати» blood or money, but for tests, it is always «складати» or «скласти».
:::

Here are some new aspect pairs for your daily routine and work vocabulary. While many pairs are formed by simply adding a prefix (like **робити** and **зробити**), others involve internal changes to the word stem. A common pattern is the change from **-вл-** in the Imperfective process to **-в-** in the Perfective result. You must memorize these verbs as pairs to use them correctly.
* **планувати / запланувати** (to plan / to have planned)
* **купувати / купити** (to buy / to have bought)
* **готувати / приготувати** (to cook, prepare / to have cooked, prepared)
* **аналізувати / проаналізувати** (to analyze / to have analyzed)
* **обговорювати / обговорити** (to discuss / to have discussed)
* **замовляти / замовити** (to order / to have ordered)
* Я зараз **замовляю** обід. *(I am ordering lunch now.)*
* Я вже **замовив** піцу. *(I have already ordered pizza.)*
* Ми довго **обговорювали** проект. *(We discussed the project for a long time.)*
* Ми успішно **обговорили** всі деталі. *(We successfully discussed all details.)*

Choosing the right aspect is what makes your storytelling sound like natural Ukrainian rather than a translated sequence of English verbs. In English, you use the past tense ending for both process and result. In Ukrainian, your choice of aspect paints a vivid picture for the listener. It tells them whether they should imagine a continuous, flowing scene or a sharp, completed action. When you master this distinction, your speech becomes fully decolonized and authentic. You stop translating grammar rules and start thinking in the natural rhythm of the Ukrainian language.

### Читаємо українською (Reading Practice)
Вчора у мене був дуже цікавий день. *(Yesterday I had a very interesting day.)*
Вранці я довго читав новини і пив каву. *(In the morning I read the news for a long time and drank coffee.)*
Потім я пішов у центр міста. *(Then I went to the city center.)*
Я гуляв парком, коли раптом побачив старого друга. *(I was walking in the park when suddenly I saw an old friend.)*
Ми зайшли в кафе і замовили обід. *(We entered a cafe and ordered lunch.)*
Ми обговорювали наші плани цілий вечір. *(We discussed our plans all evening.)*
Я повернувся додому пізно, але був дуже радий. *(I returned home late, but was very glad.)*

<!-- INJECT_ACTIVITY: match-up-story-completion -->
<!-- INJECT_ACTIVITY: match-up-short-narrative -->

## Підсумок — Summary

Ask yourself the following questions:

* Can you name three things you planned to do using the word **буду** *(I will)*? For example: «Я буду готувати вечерю» *(I will prepare dinner)*.
* How do you ask for five kilograms of apples at the market? Remember the rule for numbers five and above: «Дайте мені, будь ласка, п'ять кілограмів яблук» *(Give me, please, five kilograms of apples)*.
* What is the exact difference between the sentences «Я писав листа» *(I was writing a letter)* and «Я написав листа» *(I have written a letter)*?

To recap our main themes: the Genitive case is your primary tool for expressing quantity, asking for prices, and stating the absence of something using the word **немає** *(there is no)*. Verb aspect changes how you tell a story. The Imperfective aspect (Недоконаний вид) is all about the ongoing process, while the Perfective aspect (Доконаний вид) focuses entirely on the completed result.

### Читаємо українською (Reading Practice)
Завтра я буду купувати продукти. *(Tomorrow I will be buying groceries.)* Мені треба п'ять кілограмів картоплі. *(I need five kilograms of potatoes.)* У мене вдома немає хліба. *(I have no bread at home.)* Вчора я довго читав цікаву книгу. *(Yesterday I read an interesting book for a long time.)* Сьогодні я нарешті прочитав її! *(Today I finally finished reading it!)* Чудова робота! *(Great job!)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: foundations-practice
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

**Level: A2 (Module 7/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати


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
