<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-mastery.yaml` file for module **42: 30 найважливіших видових пар** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-formation -->`
- `<!-- INJECT_ACTIVITY: match-up-pairs -->`
- `<!-- INJECT_ACTIVITY: fill-in-context -->`
- `<!-- INJECT_ACTIVITY: quiz-read-a-mini-situation-and-choose-the-correct-aspect-form-with-justification -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match imperfective verbs with their perfective partners from the 30 pairs
  items: 8
  type: match-up
- focus: Complete sentences by choosing the correct aspect based on context (sequence,
    interruption, habit, single event)
  items: 8
  type: fill-in
- focus: Sort aspect pairs by formation pattern (prefix, suffix, stem change, suppletive)
  items: 8
  type: group-sort
- focus: Read a mini-situation and choose the correct aspect form with justification
  items: 8
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- утворення (formation)
- морфологія (morphology)
- тільки що (just now)
- вже (already)
required:
- видова пара (aspect pair)
- префікс (prefix)
- суфікс (suffix)
- брати / взяти (to take — impf./pf.)
- давати / дати (to give — impf./pf.)
- говорити / сказати (to say — impf./pf.)
- класти / покласти (to put — impf./pf.)
- починати / почати (to begin — impf./pf.)
- закінчувати / закінчити (to finish — impf./pf.)
- допомагати / допомогти (to help — impf./pf.)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Як утворюються видові пари (~550 words)

In English, we use different tenses to show if an action is ongoing or completed. For example, "I was doing" describes a process, while "I did it" describes a finished result. In Ukrainian, we use a completely different approach. We change the verb itself to create an **видова пара** (aspect pair). The imperfective form describes a process, a habit, or a repeated action. The perfective form focuses on the result, completion, or a single successful event. You will use these pairs constantly in everyday conversations.

The most common way to form the perfective aspect is by adding a **префікс** (prefix) to the imperfective verb. This prefix adds the meaning of completion but does not change the core meaning of the action. Let's look at how this works in practice.

Це дуже популярний спосіб утворення. Ми кажемо «писати», коли дія триває. Але ми кажемо «написати», коли текст готовий. Інші пари працюють так само. Слово «читати» стає «прочитати». Слово «робити» стає «зробити». Також «їсти» стає «з'їсти», а «варити» стає «зварити». Перед літерами «к», «п», «т», «ф» та «х» ми використовуємо префікс «с-». Тому ми кажемо «сфотографувати», «сказати» та «спекти».

> *This is a very popular method of formation. We say "to write" when the action is ongoing. But we say "to have written" when the text is ready. Other pairs work the same way. The word "to read" becomes "to have read". The word "to do" becomes "to have done". Also, "to eat" becomes "to have eaten", and "to cook" becomes "to have cooked". Before the letters "k", "p", "t", "f", and "kh" we use the prefix "s-". Therefore we say "to have photographed", "to have said", and "to have baked".*

The second pattern works in reverse. We take a perfective verb and make it imperfective by changing or adding a **суфікс** (suffix). Imperfective suffixes are usually longer, reflecting the ongoing process. A great example is the pair **допомагати / допомогти** (to help — impf./pf.).

Ми часто додаємо суфікси «-ува-», «-а-» або «-я-». Наприклад, доконане дієслово «записати» стає «записувати». Слово «розповісти» стає «розповідати», а «пояснити» стає «пояснювати». Іноді змінюються не тільки суфікси, але й приголосні звуки в корені слова.

> *We often add the suffixes "-uva-", "-a-", or "-ya-". For example, the perfective verb "to have recorded" becomes "to record". The word "to have told" becomes "to tell", and "to have explained" becomes "to explain". Sometimes not only the suffixes change, but also the consonant sounds in the root of the word.*

Третій спосіб — це зміна основи або наголосу. Іноді корінь змінюється помітно. Наприклад, дієслово «відповідати» має форму доконаного виду «відповісти». В інших випадках змінюється тільки наголос. Слово «розрізати» може бути недоконаного або доконаного виду. Все залежить від наголосу.

> *The third method is a change of the stem or stress. Sometimes the root changes noticeably. For example, the verb "to answer" has the perfective form "to have answered". In other cases, only the stress changes. The word "to cut" can be of imperfective or perfective aspect. It all depends on the stress.*

:::info
**Grammar box** — Remember that adding a prefix usually creates a perfective verb, while adding a longer suffix usually creates an imperfective verb. These two patterns cover the vast majority of verbs you will encounter!
:::

Finally, the fourth pattern includes verbs that use completely different roots for their imperfective and perfective forms. These are called suppletive verbs. Because they lack a shared root, you cannot rely on prefixes or suffixes, and you simply have to memorize them as distinct pairs. The most crucial examples for daily communication are **брати / взяти** (to take — impf./pf.) and **говорити / сказати** (to say — impf./pf.).

Ці слова виглядають по-різному. Ви не можете утворити їх за правилами. Якщо ви довго шукаєте ключі, ви кажете «шукати». Коли процес завершено, ви кажете «знайти». Те саме працює для дієслів «ловити» та «піймати». Їх треба вивчити напам'ять.

> *These words look different. You cannot form them by rules. If you look for keys for a long time, you say "to look for". When the process is finished, you say "to have found". The same works for the verbs "to catch" (process) and "to catch" (result). You need to learn them by heart.*

<!-- INJECT_ACTIVITY: group-sort-formation -->

## 30 пар: Список і приклади

Now that you know the four formation patterns, it is time to build your core vocabulary. We have selected the thirty most essential aspect pairs for everyday communication. They are divided into three thematic groups: daily actions, communication, and movement. Learning them as linked pairs is the absolute key to fluency in Ukrainian. Whenever you learn a new verb, you should immediately memorize its partner. Every **видова пара** (aspect pair) gives you the tools to express both the journey and the destination of an action.

The first group covers the most common actions you perform at home, in the kitchen, or during your daily chores. Most of these verbs form their perfective partner by simply adding a **префікс** (prefix) to the front of the word. This short addition acts like a seal of completion. When you use the imperfective form, you invite the listener to imagine the ongoing process of the work. When you use the perfective form, you present them with the final, ready product.

**робити / зробити** — *to do*
**писати / написати** — *to write*
**читати / прочитати** — *to read*
**готувати / приготувати** — *to cook, to prepare*
**їсти / з'їсти** — *to eat*
**пити / випити** — *to drink*
**варити / зварити** — *to boil, to cook*
**мити / помити** — *to wash*
**прибирати / прибрати** — *to clean, to tidy up*
**прасувати / випрасувати** — *to iron*

**Я варив суп.** — *I was cooking soup (process).*
**Я зварив суп.** — *I cooked the soup (result is ready).*

Учора я довго варив суп на обід. Нарешті я зварив його. Моя сестра прибирала кімнату цілий ранок. Коли вона прибрала кімнату, стало дуже чисто. Ми робимо всі домашні справи в суботу.

> *Yesterday I cooked soup for lunch for a long time. Finally I cooked it. My sister was cleaning the room all morning. When she finished cleaning the room, it became very clean. We do all the household chores on Saturday.*

The second group contains verbs related to communication, studying, and processing new information. In this category, you will see many verbs that change their **суфікс** (suffix) to form the perfective aspect. Pay close attention to the pair **говорити / сказати** (to say — impf./pf.), which uses completely different roots. This is incredibly common in spoken Ukrainian when reporting what someone said versus describing a long conversation.

**говорити / сказати** — *to speak, to say*
**питати / запитати** — *to ask*
**відповідати / відповісти** — *to answer*
**пояснювати / пояснити** — *to explain*
**вчити / вивчити** — *to learn, to study*
**розуміти / зрозуміти** — *to understand*
**казати / сказати** — *to tell, to say*
**розповідати / розповісти** — *to tell, to narrate*
**записувати / записати** — *to record, to write down*
**перекладати / перекласти** — *to translate*

**Вчитель довго пояснював правило.** — *The teacher was explaining the rule for a long time (process).*
**Нарешті він пояснив правило.** — *Finally he explained the rule (completed fact).*

Сьогодні на уроці ми вчили нові слова. Учитель довго пояснював граматику. Ми слухали, але не розуміли. Потім він пояснив усе ще раз і навів гарний приклад. Тоді кожен студент зрозумів цю тему. Усі швидко записали нові приклади в зошит.

> *Today in the lesson we were learning new words. The teacher was explaining the grammar for a long time. We listened, but did not understand. Then he explained everything one more time and gave a good example. Then every student understood this topic. Everyone quickly wrote down the new examples in the notebook.*

Group C deals with movement, physical interaction with objects, and the structure of activities. You will find verbs that define the temporal boundaries of an action, like **починати / почати** (to begin — impf./pf.) and **закінчувати / закінчити** (to finish — impf./pf.). Another crucial verb in this category is **допомагати / допомогти** (to help — impf./pf.).

This group also includes highly irregular pairs that you simply must memorize, such as **брати / взяти** (to take — impf./pf.) and **давати / дати** (to give — impf./pf.). You must also pay attention to verbs with stem changes, like **класти / покласти** (to put — impf./pf.). 

**брати / взяти** — *to take*
**давати / дати** — *to give*
**класти / покласти** — *to put*
**відкривати / відкрити** — *to open*
**закривати / закрити** — *to close*
**починати / почати** — *to begin*
**закінчувати / закінчити** — *to finish*
**допомагати / допомогти** — *to help*
**купувати / купити** — *to buy*
**платити / заплатити** — *to pay*

:::tip
**Did you know?** — The suppletive pairs **брати / взяти** and **давати / дати** are completely irregular because they evolved from very old, distinct roots. They are used in countless idioms and everyday phrases.
:::

**Я брав книгу.** — *I was taking the book (process).*
**Я взяв книгу.** — *I took the book (completed fact).*

Кожного ранку я відкриваю магазин. Учора було свято, тому я закрив його рано. Мій брат часто просить мене допомогти з математикою. Я радий, коли можу допомогти йому закінчити завдання. Ми кладемо зошити на стіл і починаємо працювати.

> *Every morning I open the store. Yesterday was a holiday, so I closed it early. My brother often asks me to help with math. I am glad when I can help him finish the task. We put the notebooks on the table and begin to work.*

To truly master these essential verbs, you need to practice them actively in context. Do not just read the lists and hope to remember them. Try writing your own personal sentences for each aspect pair. Describe what you were doing yesterday as an ongoing process, and contrast it with what you actually finished successfully.

<!-- INJECT_ACTIVITY: match-up-pairs -->

## Вибір виду в складних ситуаціях (~550 words)

Now that you know how to form an **видова пара** (aspect pair), it is time to look at how we use them in real life. The basic rule of "process versus result" is a great starting point for beginners. However, real conversations are rarely that simple. We often combine different actions in a single sentence, paragraph, or story. To speak naturally and understand native speakers, you need to see how perfective and imperfective verbs interact with each other in context. Let us explore four common scenarios where choosing the right aspect is absolutely crucial for conveying your true meaning.

The first scenario is a sequence of completed events. When you are telling a story or describing a chronological chain of actions, you must use perfective verbs for every single step. One action finishes completely, and only then does the next one begin. This creates a fast-paced narrative where the plot moves forward step by step. You might use verbs like **починати / почати** (to begin — impf./pf.) or **закінчувати / закінчити** (to finish — impf./pf.) to frame these steps. If you use an imperfective verb here, it sounds like the actions were happening at the same time, which breaks the sequence.

Учора вранці мій брат дуже швидко зібрався. Він встав, вмився, поснідав і пішов на роботу. Він зробив усе це за двадцять хвилин і нічого не забув.

> *Yesterday morning my brother got ready very quickly. He got up, washed, had breakfast, and left for work. He did all this in twenty minutes and did not forget anything.*

The second scenario is the classic interruption pattern. This happens when there is a long, ongoing background action which is suddenly interrupted by a short, completed event. The background action is always imperfective, because it describes a process happening over time. The interrupting event is perfective, because it is a sudden result that breaks into that ongoing process. Verbs involving communication, such as **говорити / сказати** (to say — impf./pf.), often appear in these interruptions.

Увечері я була вдома і спокійно відпочивала. Коли я готувала вечерю, раптом подзвонила подруга. Ми говорили дуже довго, тому моя вечеря згоріла.

> *In the evening I was at home and resting calmly. While I was cooking dinner, a friend suddenly called. We talked for a very long time, so my dinner burned.*

:::info
**Grammar box** — Think of the imperfective verb as the stage setting, and the perfective verb as the main event that suddenly happens on that stage. The word «коли» (when/while) often connects these two contrasting actions.
:::

The third scenario contrasts habitual actions with a single result. If you do something regularly or repeatedly, you must always use the imperfective aspect. This remains true even if the action finishes completely every single time it happens. However, if you are focusing on a specific, one-time achievement on a particular day, you must switch to the perfective aspect to highlight that unique result. We can see this clearly with the verbs **допомагати / допомогти** (to help — impf./pf.) and **давати / дати** (to give — impf./pf.).

Моя сестра дуже добра людина. Вона завжди допомагала сусідам, коли мала вільний час. Але вона допомогла сусідці вчора ввечері, тому що та була дуже хвора.

> *My sister is a very kind person. She always helped the neighbors when she had free time. But she helped the neighbor yesterday evening because she was very sick.*

The final scenario involves the subtle nuances of negation. Adding the word «не» (not) before a verb changes the meaning of the aspect significantly. Negating an imperfective verb simply means the action did not happen at all, or it is just a general fact about your life. On the other hand, negating a perfective verb often implies that you attempted the action, but you failed or did not achieve the final result. You might also see this nuance with verbs involving placement, like **класти / покласти** (to put — impf./pf.), or taking items, like **брати / взяти** (to take — impf./pf.).

Я взагалі не читав цю книгу, тому не знаю її сюжету. Мій друг купив її минулого тижня. Я почав читати, але я не прочитав цю книгу до кінця, бо вона нудна.

> *I have not read this book at all, so I do not know its plot. My friend bought it last week. I started reading, but I did not finish reading this book because it is boring.*

<!-- INJECT_ACTIVITY: fill-in-context -->

## Практика у діалогах (~440 words)

In everyday conversation, choosing the right **видова пара** (aspect pair) often depends on whether you are asking about a general activity or checking off a task list. This applies to all verbs, whether they change aspect using a **префікс** (prefix) or a **суфікс** (suffix). We frequently use conversational trigger phrases to emphasize results. 

Before we look at the dialogues, let's review some key verbs you will see. It is important to know when to use **брати / взяти** (to take — impf./pf.) and **давати / дати** (to give — impf./pf.) in conversation. You will also notice verbs related to communication, like **говорити / сказати** (to say — impf./pf.).

You might also need verbs for placement, like **класти / покласти** (to put — impf./pf.). Finally, pay attention to how speakers use **починати / почати** (to begin — impf./pf.) and **закінчувати / закінчити** (to finish — impf./pf.) to manage their time.

Do not forget about **допомагати / допомогти** (to help — impf./pf.) when someone needs assistance. The word «вже» (already) is often paired with a perfective verb to confirm a completed task, while «тільки що» (just now) highlights a perfective action that ended a moment ago.

Our first dialogue takes place between a parent and a child doing homework. This everyday scenario perfectly demonstrates the emotional difference between checking completed tasks and describing an ongoing, frustrating process.

> — **Мама:** Ти вже написав домашнє завдання? *(Have you already written your homework?)*
> — **Школяр:** Ні, я ще пишу. *(No, I am still writing.)*
> — **Мама:** Прочитай цей абзац. *(Read this paragraph.)*
> — **Школяр:** Я читаю вже годину! *(I have been reading for an hour already!)*

Notice how the parent uses perfective verbs because they want to see final results and move on to the next task. Meanwhile, the student uses imperfective verbs to emphasize the long, exhausting process they are currently experiencing.

Другий діалог показує різницю між переліком результатів та звичайним вечірнім відпочинком. Запитання про те, що людина зробила сьогодні, вимагає чіткого переліку повністю виконаних завдань. Натомість запитання про вечірні справи фокусується на тривалому, розслабленому процесі, який не обов'язково має фінальний результат.

> *The second dialogue shows the difference between a list of results and normal evening relaxation. A question about what a person has done today requires a clear list of fully completed tasks. Instead, a question about evening activities focuses on a long, relaxed process that does not necessarily have a final result.*

> — **Олена:** Що ти зробив сьогодні? *(What did you get done today?)*
> — **Андрій:** Я написав звіт, купив хліб і поклав гроші в банк. *(I wrote a report, bought bread, and put money in the bank.)*
> — **Олена:** А що ти робив увечері? *(And what were you doing in the evening?)*
> — **Андрій:** Я дивився фільм і готував вечерю. *(I was watching a movie and cooking dinner.)*

Нарешті, зверніть увагу на використання видових пар у майбутньому часі. Якщо ваш керівник запитує про загальні плани на завтра, він використовує недоконаний вид, щоб дізнатися про вашу рутину. Але коли його цікавить кінцевий результат до п'ятниці, він обирає доконаний вид.

> *Finally, pay attention to the use of aspect pairs in the future tense. If your manager asks about general plans for tomorrow, he uses the imperfective aspect to find out about your routine. But when he is interested in the final result by Friday, he chooses the perfective aspect.*

> — **Керівник:** Що ти будеш робити завтра? *(What will you be doing tomorrow?)*
> — **Співробітник:** Я буду писати звіт. *(I will be writing the report.)*
> — **Керівник:** Що ти зробиш до п'ятниці? *(What will you get done by Friday?)*
> — **Співробітник:** Я закінчу проект. *(I will finish the project.)*

:::info
**Grammar box** — The imperfective future uses the verb «бути» plus the infinitive, focusing on the process. The perfective future uses a single word, focusing on the final result.
:::

<!-- INJECT_ACTIVITY: quiz-read-a-mini-situation-and-choose-the-correct-aspect-form-with-justification -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-mastery
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

**Level: A2 (Module 42/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

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

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
