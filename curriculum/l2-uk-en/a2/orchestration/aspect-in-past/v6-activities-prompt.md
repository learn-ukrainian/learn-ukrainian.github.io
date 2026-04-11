<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-in-past.yaml` file for module **40: Що ти робив? А що зробив?** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-aspect-id -->`
- `<!-- INJECT_ACTIVITY: match-signal-words -->`
- `<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->`
- `<!-- INJECT_ACTIVITY: error-correction-aspect -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Given a sentence, identify whether the verb is imperfective or perfective
    and explain why
  items: 8
  type: quiz
- focus: Choose the correct aspect form (imperfective or perfective past) to complete
    sentences based on context
  items: 8
  type: fill-in
- focus: Match signal words (довго, раптом, щодня, нарешті) with the correct aspect
    and example sentence
  items: 8
  type: match-up
- focus: Fix incorrect verb aspect usage in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- щодня (every day)
- нарешті (finally, at last)
- одного разу (one time, once)
- тривалість (duration)
required:
- минулий час (past tense)
- робити / зробити (to do — impf./pf.)
- писати / написати (to write — impf./pf.)
- читати / прочитати (to read — impf./pf.)
- готувати / приготувати (to cook/prepare — impf./pf.)
- вчити / вивчити (to study/learn — impf./pf.)
- процес (process)
- результат (result)
- довго (for a long time)
- раптом (suddenly)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Два питання — два види

В українській мові є дві різні перспективи для дій у минулому часі. Це не просто граматичне правило. Це різниця між процесом і результатом.
When you talk about the past in Ukrainian, you must choose between two different ways of seeing the action.
Перше питання — це «що ти **робив**?» *(what were you doing?)*.
Друге питання — це «що ти **зробив**?» *(what did you get done?)*.
The choice between the **недоконаний вид** *(imperfective aspect)* and the **доконаний вид** *(perfective aspect)* is like choosing between shooting a video and taking a photo.
Коли ми використовуємо недоконаний вид, ми описуємо процес або факт дії.
The camera is rolling, the action takes time, and we do not care if it finished.
Коли ми використовуємо доконаний вид, ми показуємо конкретний результат.
The camera takes a snapshot of a completed action. The action has a clear endpoint, and it produced a visible outcome. This is a very real difference in how Ukrainians think about their actions.

Сьогодні понеділок. Оля і Тарас говорять про свої вихідні дні. Вони обговорюють, що вони робили і що зробили.
> — **Тарас:** Привіт, Олю! Як пройшла твоя неділя? Що ти робила вчора?
> — **Оля:** Привіт! Я добре відпочивала. Я **читала** *(was reading)* цікаву книгу майже весь день. А ти?
> — **Тарас:** А я багато працював. Але я **прочитав** *(read/finished)* цілий новий роман!
> — **Оля:** Ого! Ти дуже швидко читаєш. А що ти робив увечері?
> — **Тарас:** Я **готував** *(was cooking)* обід і вечерю дві години. Це було довго.
> — **Оля:** Це справді довго. А я теж не сиділа без діла. Я швидко **приготувала** *(cooked/finished cooking)* дуже смачну вечерю для своєї родини.

Дієслова недоконаного виду описують дію, яка довго тривала в часі.
These verbs answer the fundamental question «що робив?».
Утворювати ці граматичні форми дуже просто і зрозуміло.
You already know this perfectly from the basic past tense rules.
Ми просто беремо основу дієслова і додаємо standard suffixes минулого часу.
Для чоловічого роду ми завжди додаємо суфікс «-в».
Для жіночого роду ми додаємо суфікс «-ла».
Для середнього роду ми використовуємо «-ло», а для множини — «-ли».
Наприклад: він робив, вона **робила** *(was doing)*, воно робило, вони робили.
Він **писав** *(was writing)*, вона писала, вони писали лист.
Він **вчив** *(was studying)* нові слова, вона вчила, вони вчили.
Він читав журнал, вона читала, вони читали.
Ці дієслова показують нам сам факт дії в минулому, але вони нічого не кажуть про її успішний кінець або результат.

Дієслова доконаного виду показують, що дія успішно закінчилася і ми маємо результат.
These verbs always answer the specific question «що зробив?».
В українській мові більшість дієслів існують у парах.
These are called aspectual pairs, and learning them together is essential. Ось базові пари: **робити / зробити** *(to do — impf./pf.)*, **писати / написати** *(to write — impf./pf.)*, **читати / прочитати** *(to read — impf./pf.)*, **готувати / приготувати** *(to cook/prepare — impf./pf.)*.
Найчастіше доконаний вид утворюється дуже логічно — за допомогою префіксів.
Ми просто додаємо префікс до дієслова недоконаного виду.
Найбільш популярні префікси — це «з-», «по-», «на-» або «про-».
Наприклад, процес читав стає результатом **прочитав** *(read completely)*.
Процес писав стає результатом **написав** *(wrote)*.
Тривалий процес робив стає завершеним результатом **зробив** *(did/finished)*.
There is a special spelling rule for the prefix «з-» that you must remember.
Before the voiceless consonants к, п, т, ф, х (you can remember the mnemonic phrase "Кафе Птах"), the prefix always changes to «с-» for easier pronunciation.
Тому дієслово **казав** *(was saying)* отримує префікс «с-» і стає **сказав** *(said)*.
Складне дієслово **фотографував** *(was photographing)* стає **сфотографував** *(took a photo)*.

<!-- INJECT_ACTIVITY: quiz-aspect-id -->

## Коли вживати недоконаний вид

Ми дуже часто говоримо про час у нашому житті. We often talk about how long we were doing something. Ми використовуємо недоконаний вид, коли хочемо показати процес або тривалість дії. We use the imperfective aspect when an action takes time, and our focus is on that time spent. The action stretched over a period, and we are not talking about its end or its result. У таких реченнях ми часто бачимо спеціальні слова. These signal words tell us that the process was long and continuous. Це такі слова: **довго** *(for a long time)*, **весь день** *(all day)*, **дві години** *(two hours)*, **цілий рік** *(a whole year)*. Ці слова показують довгий процес. Therefore, you must use the imperfective aspect. Наприклад, подивіться на це речення.

> — **Тарас:** Я довго **писав** *(was writing)* листа.

The writing was a journey, a process that took time. Ми не знаємо, чи Тарас закінчив цього листа. Можливо, він ще лежить на столі у кімнаті. Головне те, що він витратив багато часу на цю дію. Ось ще один приклад тривалої дії.

> — **Оля:** Ми весь день **гуляли** *(were walking)* у великому парку.

We do not focus on a destination or a result here. We only care that the walking lasted all day. Це тривалий процес, тому ми використовуємо недоконаний вид.

Друга важлива ситуація — це регулярне повторення дії. The second use case for the imperfective aspect is repetition and habits. Repeated actions in the past are always imperfective. It does not matter if the action was successfully "completed" each individual time it happened. If it happened regularly, it is a habit, and habits always require the imperfective aspect. Ми використовуємо інші сигнальні слова для таких ситуацій. Це слова: **завжди** *(always)*, **часто** *(often)*, **щодня** *(every day)*, **зазвичай** *(usually)*, **кожного ранку** *(every morning)*. Коли дія постійно повторюється, вона стає частиною рутини. Наприклад, подивіться на цю типову ситуацію.

> — **Мама:** Вона щодня **готувала** *(used to cook)* смачний сніданок.

This describes a daily routine, not one single isolated event. Even if the breakfast was successfully finished every single morning, the repetition makes it imperfective.

> — **Тарас:** Я дуже часто **читав** *(used to read)* цей популярний журнал.

He read it many times in the past, so it is a habit. Якщо ви бачите слово **завжди**, сміливо використовуйте недоконаний вид.

> — **Оля:** Ми завжди **купували** *(used to buy)* свіжий хліб у цьому магазині.

The repetition over time makes the process the main focus of the sentence.

Третя ситуація — це фон для іншої важливої події. The third use case is setting the scene or describing background actions. When narrating a story, the "long" background action must be imperfective. This is the action that was already happening when something else suddenly occurred. Для цього ми дуже часто використовуємо популярне слово **коли** *(when)*. The long background action sets the stage, and then a short, sudden action interrupts it. Подивіться на цей класичний і дуже зрозумілий приклад.

> — **Тарас:** Коли я **снідав** *(was having breakfast)*, **раптом** *(suddenly)* подзвонив мій друг.

Тут **снідав** — це дуже довгий процес, наш загальний фон. The breakfast was already in progress when the phone rang. The friend's call was the short, completed action that interrupted the process. Тому ми завжди використовуємо недоконаний вид для такого фону. Ось ще один дуже хороший приклад для цієї ситуації.

> — **Оля:** Коли ми повільно **йшли** *(were walking)* додому, почався сильний дощ.

Walking is the continuous background process that takes time. The start of the rain is the sudden, unexpected event. Завжди використовуйте недоконаний вид для дії, яка створює атмосферу або фон у вашій історії. Це робить вашу розповідь дуже природною і цікавою.

<!-- INJECT_ACTIVITY: match-signal-words -->

## Коли вживати доконаний вид

Ми вже знаємо, як говорити про довгий процес. Але що робити, коли дія успішно закінчилася? Тепер ми поговоримо про доконаний вид дієслова. The most important use case for the perfective aspect is a completed result. When the action reaches its endpoint and produces a visible or logical outcome, we must use the perfective aspect. It tells us that the goal of the action was successfully achieved. Подивіться на цей чіткий приклад.
> — **Тарас:** Учора ввечері я **написав** *(wrote)* листа.

The letter is now completely finished and ready to send. Це конкретний результат його роботи. Ми можемо взяти цей лист у руки або відправити його поштою. Якщо ми використаємо форму «я писав», це означає лише процес. У такому випадку лист може бути ще не готовий. Доконаний вид показує нам фінал дії, її логічний кінець. Ось ще один дуже гарний приклад.
> — **Оля:** Вона нарешті **вивчила** *(learned)* ці нові слова.

The process of studying is over. She knows the words now, and she can use them in a conversation. The knowledge in her head is the direct result of her action. Отже, коли ви маєте готовий результат, завжди обирайте дієслово доконаного виду.

Друга важлива ситуація — це історія про кілька подій. The second use case for the perfective aspect is a sequence of actions. When you tell a story, you often list a chain of completed steps. Each step follows the previous one in strict chronological order. Для таких кроків ми завжди використовуємо дієслова доконаного виду. Уявіть, що ви ставите маленькі галочки у вашому списку завдань. Кожне дієслово доконаного виду — це одна нова галочка. Прочитайте цю коротку розповідь про звичайний вечір.
> — **Тарас:** Він **прийшов** *(came)* додому, **відчинив** *(opened)* вікно і **сів** *(sat down)* за стіл.

Тут ми маємо три окремі дії, які йдуть одна за одною. First he arrived, then he opened the window, and finally he sat down. One action completely finishes, and only then the next one begins. Це класичний ланцюжок подій у розповіді. Якби ми використали тут недоконаний вид, це мало б дивний сенс. Це означало б, що він робив усі три дії одночасно. Доконаний вид допомагає нам дуже чітко організувати всі події в часі.

Третя ситуація — це раптові або дуже швидкі події. The third use case for the perfective aspect is sudden, punctual, or single events. These are actions that happen in a brief instant, without a long continuous process. Для цього ми також маємо спеціальні сигнальні слова, які допомагають нам зробити правильний вибір. Це слова: **раптом** *(suddenly)*, **одного разу** *(one time)*, **нарешті** *(finally)*. Якщо ви бачите ці слова в реченні, дія зазвичай має доконаний вид. Подивіться на цей яскравий приклад раптової події.
> — **Оля:** Раптом хтось гучно **стукнув** *(knocked)* у двері.

The knock was a single, quick, and unexpected sound. Це одноразова і дуже коротка подія, яка перервала тишу. Порівняйте це з дієсловом недоконаного виду **стукати** *(to knock)*. Слово «стукав» описує тривалий шум у минулому. Але «стукнув» — це лише один швидкий удар, який дає миттєвий результат. Також ми використовуємо доконаний вид для унікальних, одиничних подій у нашому минулому.
> — **Тарас:** Одного разу я **побачив** *(saw)* відомого актора на нашій вулиці.

This specific event happened exactly once in a specific moment. It was definitely not a habit and not a long process. Отже, ми сміливо обираємо форму доконаного виду для таких унікальних життєвих ситуацій.

<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->

## Практика вибору виду

Тепер давайте подивимося на дуже особливі видові пари в українській мові. Now let's look at some very special aspectual pairs in the Ukrainian language. Деякі дієслова змінюються повністю, коли ми хочемо показати фінальний результат дії. Some verbs change completely when we want to show the final result of an action. Це дуже незвичайні пари, які треба просто запам'ятати. These are very unusual pairs that you just need to memorize. Найкращий приклад — це пара **говорити** *(to speak)* та **сказати** *(to say)*. Ми часто кажемо: «Він довго і дуже емоційно **говорив** *(was speaking)* про свою нову роботу». Це був довгий процес, і ми звертаємо увагу саме на його тривалість. This was a long process, and we pay attention exactly to its duration. Але ми ніколи не можемо сказати фразу: «Він довго сказав про роботу». But we can never say the phrase: "He said about the work for a long time." Чому це звучить так неправильно? Why does this sound so wrong? Тому що дієслово «сказати» — це завжди коротка, одноразова дія, яка має швидкий результат. Because the verb "сказати" is always a short, one-time action that has a quick result. Ми можемо радісно сказати: «Він нарешті **сказав** *(said)* усім щиру правду». Інша дуже важлива пара — це **брати** *(to take)* та **взяти** *(to finish taking)*. Якщо ви повільно берете велику книгу зі столу, це зрозумілий процес. If you are slowly taking a large book from the table, it is a clear process. Ви використовуєте дієслово недоконаного виду. You use a verb of the imperfective aspect. Але якщо ця книга вже лежить у ваших руках, ви її остаточно взяли. But if this book is already lying in your hands, you finally took it. Це вже логічний результат вашої дії, який ми можемо побачити. This is already the logical result of your action that we can see.

Давайте уважно подивимося, як ці два різні види чудово працюють разом у текстах. Let's look carefully at how these two different aspects work perfectly together in texts. Ми дуже часто використовуємо їх поруч в одній цікавій історії. We very often use them next to each other in one interesting story. Недоконаний вид зазвичай створює загальний фон, а доконаний вид яскраво показує конкретні нові події. The imperfective aspect usually creates the general background, and the perfective aspect brightly shows specific new events. Прочитайте цю маленьку, але типову розповідь про звичайний вечір.
> — **Тарас:** Був пізній вечір, і я спокійно **читав** *(was reading)* надзвичайно цікаву книгу. Раптом я **побачив** *(saw)*, що це остання сторінка. Я швидко **прочитав** *(finished reading)* її і **згорнув** *(closed)* книгу.
Перше дієслово «читав» чітко показує нам довгий процес читання. The first verb "читав" clearly shows us the long process of reading. Воно відповідає на базове питання «що робив?». It answers the basic question "what was he doing?". Це спокійний фон для всієї нашої історії, ніби декорації в театрі. This is a calm background for our whole story, like scenery in a theater. Потім на цьому фоні раптово відбуваються швидкі, повністю завершені дії. Then, against this background, quick, completely finished actions suddenly happen. Він побачив кінець, прочитав текст і згорнув книгу. He saw the end, finished reading the text, and closed the book. Ці три дієслова доконаного виду дають нам ідеальний ланцюжок результатів. These three perfective verbs give us a perfect chain of results. Таке гарне поєднання робить історію дуже живою, динамічною і об'ємною. Such a nice combination makes the story very lively, dynamic, and three-dimensional.

Англомовні студенти дуже часто роблять типові помилки з цими дієсловами у минулому часі. English-speaking students very often make typical mistakes with these verbs in the past tense. Чому так часто буває під час розмови? Why does this happen so often during a conversation? В англійській мові просто немає такої логічної системи видів. In English, there is simply no such logical system of aspects. Ви використовуєте різні граматичні часи для контексту, а не різні слова. You use different grammatical tenses for context, not different words. For example, the short English phrase "I did" does not always translate to the perfective aspect in Ukrainian. Ви могли робити щось дуже довго і не закінчити справу. You could be doing something for a very long time and not finish the task. Тоді це завжди буде дієслово недоконаного виду. Then it will always be a verb of the imperfective aspect. Українці часто описують таку ситуацію в житті. Ukrainians often describe such a situation in life. «Я **робив** *(was doing)* це завдання дві години, але **не зробив** *(didn't finish)* його». Перше дієслово «робив» гарно показує вашу довгу і важку спробу. The first verb "робив" nicely shows your long and hard attempt. Друге дієслово «зробив» з часткою «не» показує нам, що бажаного результату просто немає. The second verb "зробив" with the particle "не" shows us that there is simply no desired result. Тому завжди уважно запитуйте себе перед початком розмови. Therefore, always ask yourself carefully before starting a conversation. «Тут є конкретний результат, чи це тільки довгий процес?». "Is there a specific result here, or is it only a long process?". Ваша правильна відповідь на це питання допоможе обрати правильне дієслово. Your correct answer to this question will help choose the correct verb.

<!-- INJECT_ACTIVITY: error-correction-aspect -->

## Підсумок

Отже, час підсумувати найголовніше правило про **минулий час** *(past tense)*. The choice between imperfective and perfective verbs is not just grammar, but a completely different way of thinking. Ви завжди повинні розуміти свій фокус перед початком фрази. Are you describing the long process of an action, or do you want to show the final result? Ця різниця є абсолютно ключовою для правильного і природного спілкування. To make the right choice quickly, always use our simple strategy and a self-check list. Коли ви хочете розповісти про минуле, поставте собі такі питання:

*   **Чи є результат?** *(Is there a result?)* Якщо дія закінчилася і ми маємо фінал, це **доконаний вид** *(perfective aspect)*. Ми запитуємо: «Що **зробив**?» *(What did you get done?)*.
*   **Це процес чи повторення?** *(Is it a process or repetition?)* Якщо дія була довгою або регулярною, це **недоконаний вид** *(imperfective aspect)*. Ми запитуємо: «Що **робив**?» *(What were you doing?)*.
*   **Які слова-маркери тут є?** *(What are the signal words here?)* Слова **довго** *(for a long time)*, **часто** *(often)* і **щодня** *(every day)* завжди люблять процес. А слова **вже** *(already)*, **нарешті** *(finally)* і **раптом** *(suddenly)* вимагають тільки конкретного результату.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-in-past
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

**Level: A2 (Module 40/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
