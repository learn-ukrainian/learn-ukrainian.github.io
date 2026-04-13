<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-past-tense.yaml` file for module **4: Вид у минулому часі** (b1).

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

- `<!-- INJECT_ACTIVITY: quiz-aspect-intuition -->`
- `<!-- INJECT_ACTIVITY: fill-in-aspect-pairs -->`
- `<!-- INJECT_ACTIVITY: match-up-time-markers -->`
- `<!-- INJECT_ACTIVITY: group-sort-aspect-usage -->`
- `<!-- INJECT_ACTIVITY: error-correction-aspect -->`
- `<!-- INJECT_ACTIVITY: open-writing-my-week -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose доконаний or недоконаний вид in past-tense sentences based on context
    and time markers
  items: 10
  type: quiz
- focus: Insert the correct past-tense form (aspect choice) of a given verb pair into
    a sentence with context clues
  items: 8
  type: fill-in
- focus: Match time markers (щодня, одного разу, часто, нарешті) to aspect choice
    and explain why
  items: 8
  type: match-up
- focus: Find and correct aspect errors in past-tense sentences (e.g., *щодня приготувала
    → готувала)
  items: 6
  type: error-correction
- focus: Sort past-tense sentences into результат/процес and однократність/повторюваність
  items: 10
  type: group-sort
- focus: Write 'Мій минулий тиждень' — use both aspects, include habitual and single
    events, mark your aspect choices
  items: 6
  type: open-writing


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

- pos: noun phrase
  translation: perfective aspect — completed, bounded action
  word: доконаний вид
- pos: noun phrase
  translation: imperfective aspect — ongoing, unbounded action
  word: недоконаний вид
- pos: noun phrase
  translation: aspectual pair (e.g., писати/написати)
  word: видова пара
- pos: noun:m
  translation: result — what perfective past emphasizes
  word: результат
- pos: noun:m
  translation: process — what imperfective past emphasizes
  word: процес
- pos: noun:f
  translation: duration (signals imperfective)
  word: тривалість
- pos: noun:f
  translation: completedness (signals perfective)
  word: завершеність
- pos: noun:f
  translation: recurrence, habituality (signals imperfective)
  word: повторюваність
- pos: noun:f
  translation: single occurrence (signals perfective)
  word: однократність
- pos: adv phrase
  translation: once, one time (perfective marker)
  word: одного разу
- pos: adv
  translation: every day (imperfective marker)
  word: щодня
- pos: adv
  translation: every time (imperfective marker)
  word: щоразу
- pos: adv
  translation: always (imperfective marker)
  word: завжди
- pos: adv
  translation: sometimes (imperfective marker)
  word: іноді
- pos: adv
  translation: finally, at last (often perfective marker)
  word: нарешті
- pos: adv
  translation: suddenly (perfective marker)
  word: раптом
- pos: verb:impf
  translation: to prepare, to cook (imperfective)
  word: готувати
- pos: verb:pf
  translation: to prepare, to cook (perfective — result ready)
  word: приготувати
- pos: verb:pf
  translation: to learn thoroughly (perfective of вчити)
  word: вивчити
- pos: verb:pf
  translation: to call (perfective — one completed call)
  word: зателефонувати


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Тест на інтуїцію: що ви вже відчуваєте?

На рівні А2 ви вивчали форми минулого часу. Ви дізналися, як узгоджувати закінчення з родом і числом. Ви також запам'ятали базову різницю між доконаним і недоконаним видом дієслова. Тепер ми переходимо від простої побудови правильних речень до свідомого вибору. На цьому етапі головне завдання — не просто як сказати, а що саме ви хочете передати співрозмовнику. Ми будемо розвивати вашу мовну інтуїцію. Це означає відчувати мову зсередини, як це робить носій мови, коли описує минулі події.

> *At the A2 level, you studied the forms of the past tense. You learned how to agree endings with gender and number. You also memorized the basic difference between the perfective and imperfective aspects of the verb. Now we are moving from simply building correct sentences to conscious choice. At this stage, the main task is not just how to say it, but what exactly you want to convey to your conversation partner. We will develop your language intuition. This means feeling the language from the inside, as a native speaker does when describing past events.*

Before we dive into the rules and explanations, let us see what your brain already knows. You have been exposed to a lot of Ukrainian text and audio up to this point. Often, your subconscious picks up on patterns before your conscious mind can explain them. Below are ten pairs of sentences. In each pair, the only difference is the aspect of the verb. Read them carefully and try to feel which situation requires the perfective aspect and which requires the imperfective. Do not worry about rules right now; just listen to your intuition.

1. Вчора я (читав / прочитав) цю книжку до кінця. *(Yesterday I read this book to the end.)*
2. Вчора я (читав / прочитав) увечері, бо мені було нудно. *(Yesterday I read in the evening because I was bored.)*
3. Минулого тижня ми (робили / зробили) ремонт у кімнаті за два дні. *(Last week we did renovations in the room in two days.)*
4. Минулого тижня ми (робили / зробили) ремонт, тому всюди був пил. *(Last week we were doing renovations, so there was dust everywhere.)*
5. Тарас (писав / написав) три листи і пішов додому. *(Taras wrote three letters and went home.)*
6. Тарас (писав / написав) листа, коли я йому зателефонувала. *(Taras was writing a letter when I called him.)*
7. Вона (купувала / купила) новий телефон на розпродажі. *(She bought a new phone on sale.)*
8. Вона завжди (купувала / купила) каву в цій маленькій кав'ярні. *(She always bought coffee in this small cafe.)*
9. Я (брав / взяв) твій ноутбук на п'ять хвилин, щоб перевірити пошту. *(I took your laptop for five minutes to check my email.)*
10. Я ніколи не (брав / взяв) чужі речі без дозволу. *(I never took other people's things without permission.)*

Look at the internal logic of these sentences. Some phrases emphasize the completeness of an action, while others highlight a state of being or a process. For example, reading a book "to the end" signals a clear boundary, whereas reading "because I was bored" focuses on the activity itself to pass the time. 

You might have noticed that sometimes the lines blur. Let us analyze a very common scenario where both choices are grammatically flawless but carry entirely different social intents. The difference lies not in the grammar itself, but in the message you want to convey. Look at how a simple conversation can shift based on one verb.

Уявіть ситуацію: ви приходите на роботу, і колега запитує про ваш учорашній вечір. Ви можете відповісти: «Я дивився фільм» або «Я подивився фільм». Обидва варіанти правильні, але вони надсилають різні сигнали. Якщо ви кажете, що дивилися фільм, ви описуєте свій стан. Ви відпочивали, процес був приємним, і дія заповнила ваш час. Якщо ж ви кажете, що подивилися фільм, ви повідомляєте про результат. Можливо, це був відомий фільм, який усі обговорюють, і тепер ви теж знаєте сюжет і готові поділитися думками.

> *Imagine a situation: you come to work, and a colleague asks about your yesterday evening. You can answer: "Я дивився фільм" or "Я подивився фільм". Both options are correct, but they send different signals. If you say that you "дивилися" (were watching) a film, you are describing your state. You were resting, the process was pleasant, and the action filled your time. If you say that you "подивилися" (watched) a film, you are reporting a result. Perhaps it was a famous film that everyone is discussing, and now you also know the plot and are ready to share your thoughts.*

In Ukrainian, your choice of aspect tells the listener what you value in that moment: the experience itself or the final completion.

<!-- INJECT_ACTIVITY: quiz-aspect-intuition -->

To see how aspect colors the personality and tone of a speaker, let us listen to a conversation between two colleagues. Pay attention to how Taras and Oksana describe their days using different verb forms. Their choice of verbs reveals how they feel about their work. One feels successful, while the other feels drained.

> — **Тарас:** Привіт! Як минув твій день учора? Я вчора написав три звіти, відправив усі листи і зробив презентацію. *(Hi! How was your day yesterday? Yesterday I wrote three reports, sent all the letters, and made a presentation.)*
> — **Оксана:** Привіт... А я цілий день писала один звіт, робила презентацію, намагалася знайти помилку в таблиці, але так нічого і не закінчила. *(Hi... And I spent the whole day writing one report, making a presentation, trying to find a mistake in the table, but I didn't finish anything.)*
> — **Тарас:** Ого. Але ж ти працювала весь день? *(Wow. But you were working the whole day?)*
> — **Оксана:** Так, я дуже втомилася, хоча результату немає. *(Yes, I am very tired, even though there is no result.)*

Notice the stark contrast in their language. Taras uses the perfective aspect («написав», «відправив», «зробив»). His narrative is a checklist of victories and completed tasks. He focuses purely on results. Oksana, on the other hand, relies heavily on the imperfective aspect («писала», «робила», «намагалася»). Her verbs convey an exhausting, continuous process that dragged on without reaching a conclusion. The grammar directly reflects their emotional states: triumph versus frustration.

This brings us to the core concept of this module. In Ukrainian grammar, aspect is not just a rigid set of rules; it is a mindset. The Ukrainian metalanguage uses specific terms to describe this phenomenon. The word **результат** (result) aligns with the perfective aspect, emphasizing that a goal was reached. The word **процес** (process) aligns with the imperfective aspect, focusing on the flow of time.

:::info
**Вид як спосіб мислення**
When speaking Ukrainian, you must decide what your communicative goal is. Are you emphasizing **завершеність** (completeness) or simply stating that an activity took place? You are the director of your sentence.
:::

Коли ви розмовляєте українською, ви не просто вибираєте форму дієслова. Ви вирішуєте, як ваш слухач побачить цю подію. Вид дієслова — це ваш інструмент, щоб показати, що для вас було найважливішим у тій ситуації. Від цього залежить уся атмосфера вашої розповіді.

> *When you speak Ukrainian, you don't just choose a verb form. You decide how your listener will see this event. The verb aspect is your tool to show what was most important to you in that situation. The entire atmosphere of your story depends on this.*

## Результат чи процес? Основний вибір

When you speak in the past tense in Ukrainian, you are not simply reporting that an event happened. You are actively framing the event for your listener, deciding whether to emphasize the journey or the destination. This fundamental choice between a continuous process and a completed result is the cornerstone of the Ukrainian aspectual system. According to linguist Oleksandr Zabolotnyi, the imperfective aspect describes a continuous action or a bare fact without focusing on its conclusion. The perfective aspect, conversely, designates a completed action that has yielded a concrete result. Consider the difference between building a house and having built one. If you say that you were building a house, you are describing the ongoing effort, the construction site, and the labor. The house might still be an unfinished skeleton of wooden beams. However, if you state that you built the house using the perfective aspect, you are announcing a triumph. The keys are ready, and someone can move in immediately.

Уявіть типову життєву ситуацію, яку наводить мовознавець Олександр Авраменко. Мати повертається з роботи і бачить у кімнаті сина безлад: розкидані речі, брудний посуд та пил. Вона розчаровано запитує, чому він не навів лад. Син обурено відповідає, що він прибирав у своїй кімнаті цілих дві години. Цей конфлікт виникає через різне розуміння ситуації. Син використовує недоконаний вид, щоб підкреслити свій довгий і важкий процес роботи. Мати ж очікувала побачити доконаний вид і чисту кімнату як готовий результат. Для неї процес не має жодного значення, якщо результату немає.

> *Imagine a typical life situation given by linguist Oleksandr Avramenko. A mother returns from work and sees a mess in her son's room: scattered clothes, dirty dishes, and dust. She disappointedly asks why he didn't tidy up. The son indignantly replies that he was cleaning his room for two whole hours. This conflict arises from a different understanding of the situation. The son uses the imperfective aspect to emphasize his long and difficult process of working. The mother, however, expected to see the perfective aspect and a clean room as a finished result. For her, the process has no meaning if there is no result.*

To truly master this mindset, you must familiarize yourself with the core aspectual pairs in the Ukrainian language. These pairs represent two sides of the same semantic coin. For the pair meaning to write, we contrast the imperfective form **писати** (to write) with the perfective form **написати** (to have written). If you spend your evening writing a long letter to a friend, you are engaged in a process. You are sitting at your desk, choosing your words, and putting ink on paper. You might be interrupted, and the letter might remain unfinished. But once you sign your name, fold the paper, and put it in an envelope, you switch to the perfective aspect. The letter now exists as a completed physical object ready to be mailed.

Так само працює пара для дієслова «читати». Якщо ви кажете, що вчора ввечері читали цікаву книжку, ви просто ділитеся своїм досвідом і тим, як ви проводили час. Ваш співрозмовник уявить вас на дивані з чашкою чаю, зануреним у сюжет. Ви не обіцяєте, що знаєте фінал історії. Але якщо ви використаєте доконаний вид «прочитати», ситуація кардинально зміниться. Ви повідомляєте, що перегорнули останню сторінку. Ви не просто насолоджувалися сюжетом, ви здолали весь обсяг тексту і тепер можете обговорювати фінал з друзями.

The most fundamental verb of action presents a stark contrast between effort and outcome. We contrast the imperfective **робити** (to do) with the perfective **зробити** (to have done). When you use the imperfective aspect, you are describing the expenditure of energy. You might be working on a complex project, sweating over the details, and dedicating hours to the task. However, the perfective aspect completely ignores the sweat and tears. It only cares about the deliverable. When you declare that you have done the task, you are presenting a finished product to your boss or teacher. The effort is now in the past, and only the successful outcome matters in the present.

Пара дієслів «говорити» та «сказати» чудово демонструє цю різницю в контексті комунікації. Недоконаний вид описує сам акт мовлення, фізичний процес видавання звуків або тривалу бесіду з другом. Ви могли говорити годинами про погоду, політику та мистецтво. Натомість доконаний вид фокусується на передачі конкретного повідомлення. Коли ви використовуєте дієслово доконаного виду, ви наголошуєте на тому, що важлива інформація була успішно доставлена слухачеві. Вас цікавить не тривалість розмови, а сам факт того, що ваші слова були почуті та правильно зрозумілі.

Moving forward, let us examine another crucial pair that you will use daily. We contrast the imperfective **брати** (to take) with the perfective **взяти** (to have taken). The pair contrasts the physical gesture with the resulting possession. If a child was taking candies from a jar one by one, the imperfective aspect highlights the repeated, continuous nature of the theft. The child was actively moving their hand back and forth. But if someone took your keys before leaving the house, the perfective aspect is required. The brief, physical motion is irrelevant; what matters is the result. The keys are now in their pocket, and you are locked out.

Коли ми говоримо про навчання, різниця між процесом та результатом стає особливо відчутною. Дієслово «вчити» описує ваші зусилля, витрачений час та сидіння над підручниками. Ви можете вчити нові українські слова щовечора протягом місяця. Це ваш похвальний, але незавершений процес. Дієслово «вивчити» означає абсолютний успіх і перемогу над матеріалом. Воно сигналізує, що слова тепер надійно збережені у вашій пам'яті. Ви готові скласти іспит або вільно спілкуватися на вулиці, адже результат вашої праці вже з вами назавжди.

Cooking provides another excellent metaphor for aspectual choice. We contrast the imperfective **готувати** (to cook) with the perfective **приготувати** (to have cooked). The imperfective verb conjures images of a busy kitchen. You are chopping vegetables, stirring boiling soup, checking the oven, and tasting the sauce. It is a chaotic, ongoing symphony of culinary labor. The perfective verb, however, transports us out of the kitchen and into the dining room. The labor is completely finished, the heat is turned off, and the meal is sitting beautifully on the table. You use the perfective aspect to invite your guests to sit down and eat, because the delicious result has finally been achieved.

Нарешті, розглянемо пару дієслів для позначення відповіді. В академічному середовищі або під час складної розмови ви можете довго пояснювати свою позицію. Недоконаний вид «відповідати» описує ваші спроби сформулювати думку. Ви відповідали на запитання викладача, можливо, вагалися або давали дуже розгорнуте пояснення. Доконаний вид «відповісти» відкидає всі ці вагання. Він позначає успішну, повну та остаточну відповідь. Ви чітко передали необхідну інформацію, поставивши крапку в цьому питанні, і більше жодних сумнівів не залишилося.

<!-- INJECT_ACTIVITY: fill-in-aspect-pairs -->

To help you navigate these choices, the Ukrainian language provides strong contextual clues known as time markers. These adverbs and phrases act as directional signs, pointing you toward either the imperfective or the perfective aspect. When your sentence includes words that emphasize the duration of an event, the imperfective aspect is almost always required. Phrases like **довго** (for a long time) or **весь день** (the whole day) stretch the action out over a timeline. They force the listener to focus on the continuous flow of time rather than a single endpoint. If a student says they studied Ukrainian for three years, the emphasis is heavily placed on the lengthy, ongoing journey of education.

З іншого боку, існують часові маркери, які вимагають використання доконаного виду. Слова на кшталт «раптом», «нарешті» або фрази типу «за одну годину» стискають дію до однієї точки або підкреслюють межу, після якої з'являється результат. Наприклад, студент довго вчив граматику, але одного вечора він нарешті вивчив усі правила. Маркер «нарешті» чітко сигналізує про перехід від нескінченного процесу до тріумфального завершення. Якщо дія відбулася за годину, це означає, що процес мав чіткий ліміт і завершився конкретним досягненням.

:::info
**Time Markers as Clues**
When you see duration words, your brain should automatically reach for the imperfective aspect to show the process. When you see boundary words, you should switch to the perfective aspect to show the result.
:::

While time markers are incredibly useful tools, you must be wary of what we might call Marker Tyranny. Beginners often fall into the trap of treating these markers as absolute grammatical laws. They memorize that specific adverbs must always be followed by a specific aspect. However, in Ukrainian, context and the speaker's intent always override the markers. The aspect you choose depends entirely on what you want to say, not just on the adverbs in your sentence. A marker is merely a suggestion; your communicative goal is the supreme law.

Найскладнішим для розуміння є використання недоконаного виду для констатації загального факту в минулому. В українській мові це називається загально-фактичним значенням. Уявіть, що вас запитують, чи ви вчора читали новини. Ніхто не хоче знати, чи ви дочитали всі статті до кінця. Співрозмовника цікавить лише сам факт: чи відбувалася ця дія взагалі. Тому ви відповідаєте недоконаним видом, підтверджуючи, що такий досвід у вас був. Але якщо начальник запитує, чи ви прочитали вчорашній звіт, він вимагає доконаного виду. Його цікавить конкретний результат вашої роботи, а не просто факт того, що ви дивилися на текст.

> *The most difficult thing to understand is the use of the imperfective aspect to state a general fact in the past. In the Ukrainian language, this is called the general factual meaning. Imagine you are asked if you read the news yesterday. No one wants to know if you finished reading all the articles to the end. The interlocutor is only interested in the fact itself: whether this action took place at all. Therefore, you answer with the imperfective aspect, confirming that you had such an experience. But if a boss asks if you read yesterday's report, he demands the perfective aspect. He is interested in the specific result of your work, not just the fact that you looked at the text.*

<!-- INJECT_ACTIVITY: match-up-time-markers -->

## Повторюваність і однократність

Другий важливий вимір вибору виду в минулому часі — це різниця між звичною, регулярною дією та подією, яка сталася лише один раз. В українській мові ми називаємо це повторюваністю та однократністю. Якщо ви описуєте свій типовий день або згадуєте дитинство як серію однакових подій, ваша мова буде сповнена дієслів недоконаного виду. Це створює так звану «звичну вісь» минулого, де результат кожної окремої дії не є важливим. Важливим є сам ритм життя, який повторювався знову і знову.

> *The second important dimension of aspect choice in the past tense is the difference between a habitual, regular action and an event that happened only once. In Ukrainian, we call this recurrence (habituality) and single occurrence. If you are describing your typical day or remembering your childhood as a series of identical events, your speech will be full of imperfective verbs. This creates the so-called "habitual axis" of the past, where the result of each individual action is not important. What matters is the very rhythm of life that repeated over and over again.*

Для опису такої повторюваності ми використовуємо спеціальні слова-маркери: «щодня», «завжди», «часто», «зазвичай» або «щоліта». Коли ви кажете «Щоліта ми їздили до бабусі», ви використовуєте недоконаний вид «їздили». Ви не фокусуєтеся на одній конкретній поїздці чи її успішному завершенні. Ви малюєте загальну картину вашого минулого. У такому контексті використання доконаного виду було б грубою помилкою, оскільки доконаний вид за своєю природою прагне обмежити дію однією точкою в часі.

Повна протилежність рутині — це однократність. Це момент, коли звичний потік часу переривається чимось унікальним або специфічним. Для таких випадків ми використовуємо доконаний вид. Вибір цього виду сигналізує слухачеві: «Увага, зараз я розповім про конкретний факт, який мав завершення і результат». Часто ми використовуємо маркер «одного разу» або вказуємо точну дату, щоб підкреслити унікальність події. Наприклад: «Ми завжди відпочивали в горах, але одного разу ми поїхали на море». Тут «відпочивали» (що робили?) створює фон звички, а «поїхали» (що зробили?) позначає різку зміну та конкретний випадок.

Доконаний вид у значенні однократності «розриває» лінію часу. Він ніби ставить крапку в історії, завершуючи один епізод і дозволяючи почати наступний. Якщо ви кажете, що «минулого вівторка я купив нову книгу», ви наголошуєте на факті купівлі як на завершеній події. Ви не кажете про процес вибору чи походів по магазинах. Ви звітуєте про результат, який стався один раз у конкретний момент минулого. Це критично важливо для динамічного мовлення, де кожна нова дія в доконаному виді рухає вашу розповідь вперед.

:::info
**Повторюваність vs Однократність**
Коли дія була вашою звичкою (routine) — використовуйте недоконаний вид. Коли ви розповідаєте про унікальний випадок (exception) — перемикайтеся на доконаний вид. Маркер «одного разу» — це ваш найкращий друг для доконаного виду.
:::

Найкраще це розрізнення можна побачити в сімейних історіях. Уявіть, як дідусь розповідає онукові про своє життя в селі багато років тому.

> — **Онук:** Дідусю, розкажи, як ти жив, коли був малим? *(Grandpa, tell me, how did you live when you were little?)*
> — **Дідусь:** О, то був зовсім інший час. Щоранку я прокидався дуже рано, десь о п’ятій годині. *(Oh, that was a completely different time. Every morning I woke up very early, around five o'clock.)*
> — **Онук:** Ти завжди так рано вставав? *(Did you always get up so early?)*
> — **Дідусь:** Так, завжди. Потім я йшов до колодязя, набирав воду і допомагав мамі по господарству. Це була моя щоденна робота. *(Yes, always. Then I went to the well, drew water, and helped my mother with the housework. That was my daily job.)*
> — **Онук:** А ти колись потрапляв у пригоди? *(And did you ever get into adventures?)*
> — **Дідусь:** Звісно! Пам’ятаю, одного разу влітку раптом почалася страшна буря. *(Of course! I remember, one time in the summer, a terrible storm suddenly started.)*
> — **Онук:** І що сталося? *(And what happened?)*
> — **Дідусь:** Вітер був такий сильний, що старе дерево біля нашої хати впало прямо на дорогу. *(The wind was so strong that the old tree near our house fell right onto the road.)*
> — **Онук:** Ого! Ви його потім прибрали? *(Wow! Did you clean it up later?)*
> — **Дідусь:** Так, ми з батьком цілий день його розпилювали, але до вечора нарешті прибрали все гілля. *(Yes, my father and I were sawing it all day, but by evening we finally cleared all the branches.)*

У цьому діалозі дідусь використовує дієслова «прокидався», «йшов», «набирав», «допомагав» у недоконаному виді, щоб описати свій звичний розклад. Це фон його дитинства. Але коли з’являється сюжетна подія — буря — він миттєво переходить на доконаний вид: «почалася», «впало», «прибрали». Зверніть увагу на фразу «цілий день розпилювали». Хоча це частина історії про бурю, тут знову з’являється недоконаний вид, бо фокус зміщується на тривалість і процес роботи, а не на її фінал.

Розуміння структури розповіді через аспекти — це ключ до природного мовлення. Мовознавці часто називають недоконаний вид у минулому часі «фоновим» (background), а доконаний — «переднім планом» (foreground). Недоконаний вид описує погоду, настрій, постійні стани та звички персонажів. Він не створює нових подій, а лише готує для них місце. Доконаний вид, навпаки, — це самі події. Це кроки, якими ми йдемо по лінії часу. Без доконаного виду ваша розповідь була б статичною картиною, а без недоконаного — сухим списком фактів.

> *Understanding narrative structure through aspects is the key to natural speech. Linguists often call the imperfective aspect in the past tense "background," and the perfective — "foreground." The imperfective aspect describes the weather, mood, constant states, and characters' habits. It doesn't create new events but only prepares a place for them. The perfective aspect, on the other hand, is the events themselves. These are the steps we take along the timeline. Without the imperfective aspect, your story would be a static picture, and without the perfective — a dry list of facts.*

Уявіть собі сценарій у Львові. Ви можете сказати: «Коли я жив у Львові, я кожного вечора ходив на прогулянку. Зазвичай я купував каву на Площі Ринок і довго дивився на перехожих». Усе це — недоконаний вид. Ви описуєте свою рутину, свій спосіб життя. Ви ніби малюєте декорації до своєї історії. Слухач розуміє, що це відбувалося багато разів.

Але раптом ви додаєте: «Але минулої суботи я не пішов на прогулянку, бо зустрів старого друга. Ми зайшли в цукерню і проговорили три години». Тут ви використали доконаний вид («не пішов», «зустрів», «зайшли»), щоб виділити цей конкретний день із низки однакових субот. Ви перемістили фокус із загальної звички на конкретну пригоду. Це і є магія аспектів: ви самі керуєте увагою слухача, вказуючи, що було нормою, а що стало подією.

Тепер давайте проаналізуємо складніший текст. Уявіть опис звичайного робочого тижня в офісі. «Весь тиждень Максим працював над звітом. Він щодня приходив о дев’ятій, вмикав комп’ютер і пив чай. Потім він три години писав текст і перевіряв цифри. Але в п’ятницю ситуація змінилася. Керівник несподівано зайшов у кабінет і приніс нові дані. Максим за одну годину переробив увесь звіт і нарешті відправив його замовнику».

У першій частині тексту ми бачимо повторюваність: «працював», «приходив», «вмикав», «пив», «писав», «перевіряв». Це все — недоконаний вид, бо це опис звичного процесу. Навіть якщо Максим завершував пити чай щодня, ми використовуємо недоконаний вид «пив», бо наголошуємо на регулярності дії. Але у другій частині з’являється однократність і результат: «зайшов», «приніс», «переробив», «відправив». Це винятки з правила, конкретні дії, які мають чітке завершення. Це і є межа, де «повторюваність» закінчується, а «однократність» починається.

:::tip
**Мистецтво розповіді**
Якщо ви хочете, щоб ваша історія звучала жваво, чергуйте види. Використовуйте недоконаний вид для описів і атмосфери («сонце світило», «я читав»), а доконаний — для активних дій («раптом пролунав дзвінок», «я відкрив двері»).
:::

При аналізі тексту завжди шукайте причину вибору аспекту. Запитайте себе: «Чи ця дія була частиною звички? Чи це унікальний момент?». Якщо ви бачите маркер тривалості (три години) разом із повторюваністю (щодня), вибір недоконаного виду стає подвійно обґрунтованим. Українська мова дуже логічна в цьому питанні: форма дієслова завжди підпорядковується вашому бажанню виділити або процес, або результат, або звичку.

<!-- INJECT_ACTIVITY: group-sort-aspect-usage -->

## Підсумок: вид як інструмент мислення

To choose the correct aspect in the past tense, you need to understand that the decision is not based on a single mechanical rule, but rather on a two-axis decision matrix. When you construct a sentence, you are navigating these two dimensions simultaneously. The first axis is the Result versus Process dimension. The second axis is the Single versus Repeated dimension. By mapping your communicative intent onto this matrix, you can confidently select either the perfective or the imperfective aspect. This framework covers the vast majority of all past tense usage you will encounter.

Уявіть собі систему координат, де вертикальна вісь — це опозиція між результатом і процесом, а горизонтальна вісь — це опозиція між одноразовою та повторюваною дією. Якщо ваша дія має чіткий результат і відбулася лише один раз, вона потрапляє в сектор доконаного виду. Але якщо дія описує тривалий процес, або якщо вона повторювалася багато разів, вона автоматично переходить у сектор недоконаного виду. Навіть якщо дія мала результат, але повторювалася щодня, повторюваність перемагає, і ви використовуєте недоконаний вид.

> *Imagine a coordinate system where the vertical axis is the opposition between result and process, and the horizontal axis is the opposition between a single and a repeated action. If your action has a clear result and happened only once, it falls into the perfective aspect sector. But if the action describes a continuous process, or if it was repeated many times, it automatically moves into the imperfective aspect sector. Even if the action had a result but was repeated every day, repetition wins, and you use the imperfective aspect.*

Let's break down how these two axes govern your speech. When you speak, you usually know whether you want to emphasize that something is finished and ready. If you say that you wrote a letter, the listener expects that the letter now exists. This is the result axis. If you say that you were writing a letter, the listener only knows how you spent your time, not whether the letter is finished. This is the process axis. The second dimension is just as powerful. If you bought a coffee once, it is a unique event. If you bought coffee every morning, it becomes a routine, a background habit. 

:::info
**The Golden Rule of the Matrix**
If your past action is a continuous process OR if it happened repeatedly, it automatically belongs to the imperfective aspect. The perfective aspect is strictly reserved for single, completed events that yield a clear result.
:::

One of the biggest challenges for English speakers is that English past tenses do not map perfectly onto Ukrainian aspects. English relies heavily on the Past Simple tense, which is fundamentally ambiguous when it comes to the process-versus-result distinction. When you say "I read the book" in English, the listener relies entirely on context to know if you mean you spent some time reading it or if you actually finished the whole thing. In English, "I cooked dinner every day" and "I cooked dinner yesterday" use the exact same verb form, blurring the line between a habit and a milestone.

Українська мова не дозволяє такої неоднозначності, оскільки форма дієслова змушує вас зробити свідомий вибір. Якщо ви кажете «Я читав книгу», ви повідомляєте лише про те, що ви були в процесі читання. Це еквівалентно англійському Past Continuous. Але якщо ви кажете «Я прочитав книгу», ви стверджуєте, що книга закінчена. Найбільша пастка полягає в тому, що англійське Past Simple часто перекладається обома способами залежно від реального наміру мовця.

> *The Ukrainian language does not allow such ambiguity because the verb form forces you to make a conscious choice. If you say "Я читав книгу," you are only reporting that you were in the process of reading. This is equivalent to the English Past Continuous. But if you say "Я прочитав книгу," you are asserting that the book is finished. The biggest trap is that the English Past Simple is often translated both ways depending on the speaker's actual intent.*

Let's look at three common translation traps and how to escape them. The first trap is the "duration paradox." A learner might say: *«Я вчора прочитав книжку три години.»* Because the reading is in the past, they might be tempted to use the perfective. But the phrase "three hours" explicitly highlights duration. In Ukrainian, duration plus process always equals the imperfective aspect. The correct choice is: **Я вчора читав книжку три години.** 

The second trap is the "repeated result." A learner might say: *«Вона щодня приготувала обід.»* Cooking lunch produces a clear result, so the perfective seems logical. But the marker "every day" indicates a repeated, habitual action. As we saw on our decision matrix, repetition always overrides the result and demands the imperfective aspect. The correct choice is: **Вона щодня готувала обід.**

The third trap is the "unrealized milestone." A learner might say: *«Він одного разу писав лист бабусі.»* The marker "one time" points directly to a single, completed event that breaks the routine. Using the imperfective here sounds like the process was interrupted or never finished. For a single completed event, you must use the perfective. The correct choice is: **Він одного разу написав лист бабусі.**

As you deepen your understanding of the Ukrainian aspectual system, it is crucial to recognize its independence. While the category of verbal aspect exists in other Slavic languages, the specific rules, exceptions, and the very composition of aspectual pairs in Ukrainian form a unique, self-contained system. You cannot assume that because a pattern exists in another language, it will function identically in Ukrainian. 

Українська мова має власну логіку творення видових пар. Наприклад, дієслово «говорити» утворює пару з дієсловом «сказати». Недоконане дієслово «брати» має доконану пару «взяти». Дієслово «ловити» стає «піймати» або «зловити». Це не просто граматичні винятки, це відображення того, як мова історично формувала зв'язки між поняттями. Деякі дієслова взагалі можуть функціонувати в обох видах залежно від контексту, як-от «телефонувати» чи «організувати».

> *The Ukrainian language has its own logic for forming aspectual pairs. For example, the verb "говорити" forms a pair with the verb "сказати". The imperfective verb "брати" has the perfective pair "взяти". The verb "ловити" becomes "піймати" or "зловити". These are not just grammatical exceptions; they are a reflection of how the language historically formed connections between concepts. Some verbs can even function in both aspects depending on the context, such as "телефонувати" or "організувати".*

This is why working with a reliable dictionary is so important. Do not try to guess the perfective form of a new verb. When you learn a new action, you should always memorize it as an aspectual pair. The dictionary will show you whether the pair is formed by changing a suffix, adding a prefix, or using an entirely different word. Relying on authentic Ukrainian sources ensures that your speech remains natural and free from artificial constructions.

<!-- INJECT_ACTIVITY: error-correction-aspect -->

Now it is time to put this matrix into practice. Your final task for this module is to write a short story about your past week, titled "Мій минулий тиждень." In this story, you will intentionally weave both aspects together to create a dynamic and natural narrative. This is not just a grammar exercise; it is an exercise in controlling the listener's attention and structuring information.

У вашій розповіді ви повинні використати щонайменше три дії недоконаного виду для опису ваших звичок, рутини або фонових процесів. Це можуть бути речі, які ви робили щодня, або процеси, які тривали довго. Потім вам потрібно додати щонайменше три дії доконаного виду, щоб описати конкретні досягнення, завершені події або раптові зміни. Нарешті, ви повинні створити хоча б одне речення, де обидва види зустрічаються разом: одна дія перериває іншу.

> *In your story, you must use at least three actions of the imperfective aspect to describe your habits, routine, or background processes. These can be things you did every day, or processes that lasted a long time. Then you need to add at least three actions of the perfective aspect to describe specific achievements, completed events, or sudden changes. Finally, you must create at least one sentence where both aspects meet together: one action interrupts another.*

For example, you might structure your narrative like this: "Минулого тижня я щоранку пив каву і читав новини. Це була моя рутина. Але в середу я не пив каву. Я прокинувся, швидко одягнувся і поїхав на важливу зустріч. Поки я їхав у метро, я перевіряв документи. Раптом мені зателефонував директор і сказав, що зустріч скасовано." 

> *Last week, I drank coffee and read the news every morning. This was my routine. But on Wednesday, I didn't drink coffee. I woke up, dressed quickly, and went to an important meeting. While I was riding in the subway, I was checking documents. Suddenly, the director called me and said that the meeting was canceled.*

Notice how the imperfective verbs build the environment, while the perfective verbs drive the plot forward. By mastering this contrast, you transform a flat list of activities into a compelling story. Remember to use time markers to signal your intentions clearly. Use words like "щодня" or "завжди" to set up your imperfective habits, and use "одного разу" or "раптом" to introduce your perfective events.

:::tip
**Weaving the narrative**
Think of the imperfective aspect as the stage design and the perfective aspect as the actors moving across the stage. Both are necessary for the play to make sense.
:::

<!-- INJECT_ACTIVITY: open-writing-my-week -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-past-tense
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

**Level: B1 (Module 4)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
