<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-in-past.yaml` file for module **40: Що ти робив? А що зробив?** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-given-a-sentence-identify-whether-the-verb-is-imperfective-or-perfective-and-explain-why -->`
- `<!-- INJECT_ACTIVITY: match-up-match-signal-words-with-the-correct-aspect-and-example-sentence -->`
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
## Два питання — два види (~550 words)

We often talk about the weekend by sharing what we did. But in Ukrainian, how you describe your past actions depends on whether you were just busy doing something, or if you actually achieved a result. Listen to how Olya and Taras talk about their Sunday. Notice the difference between their verbs.

> — **Оля:** Привіт, Тарасе! Що ти робив у неділю? *(Hi, Taras! What were you doing on Sunday?)*
> — **Тарас:** Привіт! Я відпочивав удома. *(Hi! I was resting at home.)*
> — **Оля:** Я читала весь день. А ти? *(I was reading all day. And you?)*
> — **Тарас:** Я прочитав новий роман! *(I read a new novel!)*
> — **Оля:** Класно. А потім я готувала обід. *(Cool. And then I was cooking lunch.)*
> — **Тарас:** А я приготував дуже смачний борщ. *(And I prepared a very tasty borscht.)*

When we talk about the **минулий час** *(past tense)*, Ukrainian uses a fundamental distinction that doesn't exist in English in the same way. Every action forces you to choose between a **процес** *(process)* and a **результат** *(result)*. This isn't just a grammar trick; it is a core difference in how Ukrainians categorize the world. The easiest way to understand this is through two simple questions. If someone asks you «Що ти робив?» *(What were you doing?)*, they are asking about the process. They want to know how you spent your time. But if they ask «Що ти зробив?» *(What did you get done?)*, they are asking about the result. They want to know what you accomplished.

Українці завжди розрізняють дію як процес і дію як результат. Це дуже важливо для спілкування. Коли ви говорите про процес, ви використовуєте недоконаний вид. Коли ви говорите про результат, вам потрібен доконаний вид. Дієслова «робити» та «зробити» — це ідеальний приклад цієї системи.

> *Ukrainians always distinguish between an action as a process and an action as a result. This is very important for communication. When you talk about a process, you use the imperfective aspect. When you talk about a result, you need the perfective aspect. The verbs "робити" and "зробити" are a perfect example of this system.*

Think of the imperfective past (недоконаний вид) as a video camera that is rolling. It records the action happening, but it doesn't show you the end of the recording. When Olya says «Я читала книгу» *(I was reading a book)*, the focus is entirely on the activity itself. We know she spent time reading, but we do not know if she finished the book. The imperfective aspect is used to emphasize that you did something **довго** *(for a long time)*, the simple fact that an action happened, or a repeated action.

For example, you might say «Я писав листа» *(I was writing a letter)*. We see the pen moving across the paper, but there is no final letter ready to be sent. The verb **писати** *(to write)* describes this ongoing action. Other common verbs in this category are **читати** *(to read)* and **вчити** *(to study/learn)*. The focus remains on the time spent.

Now, think of the perfective past (доконаний вид) as a photograph of the final result. The action has reached its endpoint, and something new exists. When Taras says «Я прочитав роман» *(I read the novel)*, he means the book is finished and closed. The focus is strictly on the completed outcome. Perfective verbs also describe sudden actions. If something happens **раптом** *(suddenly)*, it is a single, completed event that interrupts the background process.

When you say «Я написав листа» *(I wrote the letter)*, the letter is complete and ready for the mailbox. The verb **написати** *(to write/finish)* shows that the result was achieved. You use **прочитати** *(to read/finish reading)* and **вивчити** *(to learn/master)* for the same reason.

:::note
**Quick tip**
Perfective verbs cannot have a present tense form. Because the perfective aspect focuses entirely on a completed result, it is logically impossible for a completed result to be happening "right now."
:::

Let's review the past tense forms. The good news is that the rules for making the past tense are identical for both aspects. The endings depend entirely on the gender and number of the person doing the action.

Let's look at the imperfective verb **робити** *(to do)*:
* він робив
* вона робила
* воно робило
* вони робили

Now compare this with the perfective verb **зробити** *(to do/finish)*:
* він зробив
* вона зробила
* воно зробило
* вони зробили

The same pattern applies to the pair **готувати** *(to cook)* and **приготувати** *(to cook/finish preparing)*.
* він готував / він приготував
* вона готувала / вона приготувала
* воно готувало / воно приготувало
* вони готували / вони приготували

You just take the infinitive, remove the «-ти», and add the standard past tense endings.

<!-- INJECT_ACTIVITY: quiz-given-a-sentence-identify-whether-the-verb-is-imperfective-or-perfective-and-explain-why -->

## Коли вживати недоконаний вид (~550 words)

The most common use of the imperfective **минулий час** (past tense) is to describe a **процес** (process). When an action stretches over time, we use the imperfective aspect to emphasize the activity itself. The actual **результат** (result) is either unknown or unimportant.

Учора я дуже довго писав листа своєму другові. Це був складний процес, і я постійно шукав правильні слова. Я не знаю, чи я його закінчив. Моя сестра весь вечір читала нову книгу, а мама готувала смачну вечерю.

> *Yesterday I was writing a letter to my friend for a very long time. It was a difficult process, and I was constantly looking for the right words. I do not know if I finished it. My sister was reading a new book all evening, and mom was cooking a delicious dinner.*

In these examples, the imperfective verbs from the pairs **писати / написати** (to write — impf./pf.) and **читати / прочитати** (to read — impf./pf.) show that the actions took time. We picture the pen moving and the pages turning, without focusing on the finished letter or the closed book.

Another major function is describing repetition or a habit. If you did something regularly, repeatedly, or as a routine, you must use the imperfective past. This is true even if each individual instance of the action was successfully completed. 

Вона щодня готувала сніданок для всієї родини. Після сніданку ми завжди пили каву і говорили про наші плани на день. Мій брат часто читав новини в інтернеті, а я робив ранкову гімнастику. Це була наша щоденна рутина.

> *Every day she made breakfast for the whole family. After breakfast we always drank coffee and talked about our plans for the day. My brother often read the news on the internet, and I did morning gymnastics. It was our daily routine.*

Even though breakfast was successfully made and eaten every morning, we use the imperfective verb from the pair **готувати / приготувати** (to cook/prepare — impf./pf.). The repetition makes the action an ongoing cycle, requiring the imperfective form of verbs like **робити / зробити** (to do — impf./pf.).

The imperfective aspect also sets the scene. It acts as the background action against which another event happens. The ongoing background activity uses the imperfective past, while the sudden interruption uses the perfective past.

Коли я спокійно снідав у кафе, раптом подзвонив мій старий друг. Я сидів біля вікна і пив гарячий чай. Надворі йшов сильний дощ, і люди швидко бігли до метро. Ця атмосфера була дуже затишною.

> *While I was quietly having breakfast in a cafe, suddenly my old friend called. I was sitting by the window and drinking hot tea. Outside a heavy rain was falling, and people were running quickly to the subway. This atmosphere was very cozy.*

The actions of having breakfast, sitting, and drinking tea are ongoing background processes. They set the stage for the main event, which is the phone call that happens **раптом** (suddenly). You frequently use imperfective verbs to paint the picture for your listener.

Signal words naturally pair with the imperfective past to indicate duration or frequency. You will frequently encounter words like «довго» to indicate a long time, or «часто» to mean often. Other markers include «завжди» for always, «щодня» for every day, and «зазвичай» for usually.

Я часто читав казки своєму молодшому брату перед сном. Він довго готував вечерю, тому ми сіли їсти дуже пізно. Раніше ми завжди вчили нові слова разом у бібліотеці. Коли йшов сніг, ми зазвичай дивилися старі фільми.

> *I often read fairy tales to my younger brother before bed. He cooked dinner for a long time, so we sat down to eat very late. Earlier we always studied new words together in the library. When it snowed, we usually watched old movies.*

:::info
**Grammar box**
Whenever you see words meaning "often" or "always" in a past tense sentence, the verb must be imperfective. These words describe a repeated process, making the perfective aspect grammatically impossible.
:::

These adverbs act as signposts guiding you toward the correct aspect. Using the imperfective verb from the pair **вчити / вивчити** (to study/learn — impf./pf.) alongside the indicator **довго** (for a long time) illustrates a continuous habit perfectly.

## Коли вживати доконаний вид (~550 words)

The most common reason to use the perfective past is to show a completed **результат** (result). When an action reaches its final endpoint and produces something visible or tangible, the imperfective aspect is no longer sufficient. You need to show that the work is done and the goal is achieved.

Учора ввечері я нарешті написав листа своєму другові. Цей лист тепер лежить на столі, готовий до відправки. Мій брат також добре попрацював і зробив складне домашнє завдання з математики. Ми дуже раді, що маємо такий чудовий результат.

> *Yesterday evening I finally wrote a letter to my friend. This letter now lies on the table, ready for sending. My brother also worked well and did his difficult math homework. We are very happy that we have such a great result.*

The perfective verbs from the pairs **писати / написати** (to write — impf./pf.) and **робити / зробити** (to do — impf./pf.) tell the listener that the letter exists and the homework is finished. If you used the imperfective forms, it would only mean you spent time on these activities, but the tasks might still be unfinished.

Another key function of the perfective aspect is to move a story forward. When you narrate a sequence of events, each completed step pushes the timeline ahead. For these chronological chains of finished actions, you must use perfective verbs.

Я прийшов додому, пообідав і одразу подзвонив мамі. Після розмови я відкрив комп'ютер і прочитав важливий електронний лист. Потім я швидко приготував смачну вечерю для всієї родини. Усі ці дії відбулися одна за одною.

> *I came home, had lunch, and immediately called Mom. After the conversation I opened my computer and read an important email. Then I quickly prepared a tasty dinner for the whole family. All these actions happened one after another.*

Each verb acts as a distinct point on a timeline. The perfective verbs from pairs like **читати / прочитати** (to read — impf./pf.) and **готувати / приготувати** (to cook/prepare — impf./pf.) show that one action ended before the next one began. This creates a clear and dynamic narrative.

The perfective past is also essential for sudden, punctual events. These are actions that happen in an instant, often interrupting an ongoing background process. Because a sudden event is viewed as a single, completed whole, it requires the perfective aspect.

Я спокійно читав цікаву книгу у своїй кімнаті. Раптом хтось голосно постукав у двері. Я злякався, швидко встав з ліжка і пішов у коридор. Цей несподіваний звук порушив тишу в будинку.

> *I was quietly reading an interesting book in my room. Suddenly someone knocked loudly on the door. I got scared, quickly got up from the bed, and went into the corridor. This unexpected sound broke the silence in the house.*

The word **раптом** (suddenly) is a very strong indicator here. The ongoing action of reading forms the background, while the sudden knock is a perfective event that punctures that background.

Just as the imperfective aspect has specific signal words, the perfective past also has adverbs that naturally pair with it. These words emphasize completion, success, or the sudden nature of an event.

:::info
**Grammar box**
When you want to emphasize that a single event successfully reached its conclusion, look for words like **вже** (already) and **нарешті** (finally, at last). These adverbs strongly prefer perfective verbs.
:::

Сьогодні я вже вивчив нові українські слова для нашого уроку. Нарешті вона зробила цей складний проєкт і може відпочити. Одного разу ми поїхали в гори і побачили справжнього ведмедя. Вчора він купив новий телефон у магазині.

> *Today I have already learned the new Ukrainian words for our lesson. Finally she did this difficult project and can rest. One time we went to the mountains and saw a real bear. Yesterday he bought a new phone in the store.*

Notice how the perfective verb from **вчити / вивчити** (to study/learn — impf./pf.) works perfectly with «вже», proving that the knowledge is now acquired. Words like «одного разу» (one time, once) and specific markers like «вчора» (when pointing to a single finished event, not a process) also guide you toward the perfective past.

<!-- INJECT_ACTIVITY: match-up-match-signal-words-with-the-correct-aspect-and-example-sentence -->

## Практика вибору виду (~550 words)

Let us look at how the choice of aspect completely changes the meaning of a sentence. When we use the imperfective aspect, we focus on the **процес** (process) and the effort. When we switch to the perfective aspect, the focus immediately shifts to the **результат** (result) and the success of the action. This contrast is the core of the Ukrainian verb system.

Вчора ввечері він читав газету. Ми не знаємо, чи він дочитав її до кінця. Він просто сидів і читав. Але сьогодні вранці він нарешті прочитав газету. Тепер він знає всі новини. Вона вчора довго вчила нові українські слова. Це була важка робота. Сьогодні вона вивчила всі слова і може говорити без помилок.

> *Yesterday evening he was reading a newspaper. We do not know if he read it to the end. He was just sitting and reading. But this morning he finally read the newspaper. Now he knows all the news. She was studying new Ukrainian words for a long time yesterday. It was hard work. Today she learned all the words and can speak without mistakes.*

Notice how **читати / прочитати** (to read — impf./pf.) and **вчити / вивчити** (to study/learn — impf./pf.) create distinct mental images. One is a rolling video of an activity, and the other is a photograph of the finish line. 

In real life, we rarely use just one aspect. We constantly mix them to tell dynamic stories. The imperfective aspect sets the background scene, while the perfective aspect delivers the main events and moves the plot forward.

Коли я готував вечерю, раптом погасло світло. Я стояв у темряві. Потім я знайшов свічку і запалив її. Я швидко приготував їжу на газовій плиті. Ми вечеряли при свічках, і це було дуже романтично.

> *While I was making dinner, suddenly the lights went out. I stood in the dark. Then I found a candle and lit it. I quickly prepared the food on the gas stove. We were having dinner by candlelight, and it was very romantic.*

Here, the verb from the pair **готувати / приготувати** (to cook/prepare — impf./pf.) shows both sides of the story. The imperfective form sets the ongoing background scene. The word **раптом** (suddenly) then introduces a sharp perfective interruption. After the interruption, a sequence of completed perfective actions resolves the situation.

English speakers often make specific mistakes when forming the **минулий час** (past tense) because English relies on tense structures rather than lexical aspect pairs. The most common error is using the imperfective aspect when the context clearly demands a finished result.

:::note
**Quick tip**
If you want to say that you finished a task, always choose the perfective verb. Using the imperfective form sounds like you gave up halfway.
:::

Студенти часто кажуть: «Я вчора писав листа». Це звучить так, ніби процес не закінчився. Українці чекають продовження: «...але не закінчив». Якщо лист готовий, треба казати: «Я вчора написав листа». Інша помилка — це слова типу «щодня». Не можна казати: «Він щодня зробив вправи». Якщо дія повторюється, ми повинні використовувати дієслово «робив».

> *Students often say: "Yesterday I was writing a letter." It sounds as if the process did not finish. Ukrainians expect a continuation: "...but did not finish." If the letter is ready, you must say: "Yesterday I wrote a letter." Another mistake is words like "every day." You cannot say: "He did the exercises every day." If the action repeats, we must use the verb "was doing."*

The pair **писати / написати** (to write — impf./pf.) perfectly illustrates the ambiguity of the imperfective past without context. And for habits, the pair **робити / зробити** (to do — impf./pf.) reminds us that repetition always requires the imperfective form, no matter how short the action was.

To make the right choice in everyday conversations, you can use a simple mental flowchart. Ask yourself two questions before you speak. First, is there a clear, visible outcome, or is it a single step in a sequence of events? Does the action answer the question "what got done?" If the answer is yes, you need the perfective aspect. Second, are you describing a continuous duration, a repeated habit, or a background scene for another event? Does the action answer the question "what were you doing?" If the word **довго** (for a long time), "often," or "every day" fits the context naturally, you must choose the imperfective aspect. Mastering this difference takes time and patience, but it is the most rewarding part of learning the language. Trust this basic logic, practice identifying the signals in native texts, and your stories will sound perfectly natural.

<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->
<!-- INJECT_ACTIVITY: error-correction-aspect -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-in-past
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
