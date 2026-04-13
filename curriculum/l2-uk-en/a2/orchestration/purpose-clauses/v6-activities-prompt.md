<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/purpose-clauses.yaml` file for module **48: Щоб зрозуміти...** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-schob-forms -->`
- `<!-- INJECT_ACTIVITY: quiz-tomuscho-vs-schob -->`
- `<!-- INJECT_ACTIVITY: unjumble-schob-clauses -->`
- `<!-- INJECT_ACTIVITY: match-up-reported-speech -->`
- `<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-purpose-clauses-and-reported-speech-sentences -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-between-and-to-complete-sentences -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete purpose clauses with the correct form after щоб (infinitive vs.
    past tense form depending on subject)
  items: 8
  type: fill-in
- focus: Choose тому що or щоб to complete sentences — distinguish cause from purpose
  items: 8
  type: quiz
- focus: Transform direct speech into reported speech — match the original quote to
    its indirect version
  items: 8
  type: match-up
- focus: Reorder words to form correct щоб purpose clauses (both infinitive and different-subject
    constructions)
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- навіщо (what for, why)
- передати (to pass on, to relay)
- попросити (to ask, to request)
- пряма мова (direct speech)
required:
- щоб (in order to, so that)
- мета (goal, purpose)
- сказати (to say, to tell)
- відповісти (to answer, to reply)
- пояснити (to explain)
- запитати (to ask)
- повідомлення (message)
- зрозуміти (to understand)
- непряма мова (indirect/reported speech)
- додати (to add)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Щоб + інфінітив: для чого? (In Order To: What For?) (~750 words)

> — **Мама:** Ми йдемо в магазин, щоб купити хліб. *(We are going to the store in order to buy bread.)*
> — **Дитина:** А навіщо зараз? *(And what for right now?)*
> — **Мама:** Вчителька сказала, що завтра екскурсія, і нам потрібні бутерброди. *(The teacher said that tomorrow is an excursion, and we need sandwiches.)*
> — **Дитина:** Зрозуміло. *(Understood.)*
> — **Мама:** До речі, тато попросив, щоб ти прибрав кімнату після сніданку. *(By the way, dad asked that you clean the room after breakfast.)*

In our daily lives, we constantly explain the reasons and goals behind our actions to other people. Whether you are at work or at home, communicating your intentions clearly is a key part of speaking a language naturally. When you want to ask about the purpose of an action, you use the question words **для чого?** (what for?) or **навіщо?** (why? / what for?). To answer these questions and express your **мета** (goal, purpose), Ukrainian uses a very specific conjunction: **щоб** (in order to, so that). The most basic way to use this conjunction is by combining **щоб** directly with an infinitive verb.

Я вчу українську мову, щоб розуміти своїх друзів. Я читаю тексти, щоб знати нові слова. Ми працюємо, щоб мати гроші.

> *I study the Ukrainian language in order to understand my friends. I read texts in order to know new words. We work in order to have money.*

This brings us to what we call the "same-subject rule." You must use the structure **щоб** plus an infinitive when the person performing the main action and the person performing the goal action are exactly the same individual. For example, in the sentence "I work in order to have money", the subject "I" does the working, and the exact same "I" will have the money. In Ukrainian, this is the easiest and most direct way to state your personal intentions. You do not need to worry about complex grammar or changing the verb forms, because the infinitive does all the heavy lifting for you.

Він прийшов додому, щоб допомогти брату. Ми поїхали в Київ, щоб побачити місто. Студенти слухають аудіо, щоб краще розуміти мову.

> *He came home in order to help his brother. We went to Kyiv in order to see the city. Students listen to audio in order to better understand the language.*

:::info
**Grammar box**
Notice that the second verb is always in the infinitive form (ending in **-ти**). You do not conjugate the verb after **щоб** if the subject is the same for both actions.
:::

However, human communication is rarely that simple. Often, our actions are meant to influence someone else or create a result for another person. What happens when the subject of the first action is completely different from the subject of the goal action? For example, consider the phrase "I called so that SHE would know." When the subjects differ across the two clauses, you cannot use the infinitive anymore. Instead, Ukrainian requires a special "different-subject construction". For this, you must use **щоб** followed immediately by the verb in its past tense form.

Я зателефонував вчора, щоб вона знала новини. Вчитель довго пояснював правило, щоб учні все добре зрозуміли. Мама купила квитки, щоб діти поїхали на море.

> *I called yesterday so that she would know the news. The teacher explained the rule for a long time so that the students would understand everything well. Mom bought tickets so that the children would go to the sea.*

It is absolutely crucial to understand that this past tense form does not describe an action that happened in the past. After the conjunction **щоб**, the past tense form functions as a subjunctive mood. It expresses an intent, a desire, or a hypothetical goal that has not necessarily happened yet. The verb after **щоб** simply agrees in gender and number with the new subject of that specific clause, just like a regular past tense verb would.

This different-subject construction is absolutely essential for expressing desires, requests, and indirect commands in everyday life. The most frequent phrase you will use in this context is **я хочу, щоб...** (I want you to...). This structure contrasts heavily with English grammar. English uses the infinitive for desires involving others, as in "I want you TO come". Ukrainian strictly forbids this literal translation. You must use **щоб** and the past tense verb agreeing with the new subject. This is a fundamental rule that will make your Ukrainian sound much more natural and polite.

Я хочу, щоб ти прийшов сьогодні ввечері. Ми хочемо, щоб війна закінчилася швидко. Вона просить, щоб я допоміг їй з роботою.

> *I want you to come tonight. We want the war to end quickly. She asks that I help her with work.*

:::tip
**Did you know?**
A very common mistake for English speakers is saying «Я хочу тебе прийти». This sounds very unnatural in Ukrainian. Always remember to build a new clause with **щоб** and the past tense form when you want someone else to do something.
:::

Finally, let's contrast **щоб** with another important conjunction you already know from previous lessons: **тому що** (because) or its shorter synonym **бо**. Both of these words connect ideas, but they look in opposite directions. The conjunction **тому що** answers the question **чому?** (why?), looking backward at the cause or the fundamental reason for an action. On the other hand, the conjunction **щоб** answers the question **для чого?** (what for?), looking forward at the future purpose or the intended result of an action.

Я вчу українську мову, бо я хочу розуміти друзів. Я вчу українську мову, щоб розуміти друзів. Він п'є воду, тому що хоче пити. Він іде на кухню, щоб випити води.

> *I study the Ukrainian language because I want to understand my friends. I study the Ukrainian language in order to understand my friends. He drinks water because he is thirsty. He goes to the kitchen to drink water.*

:::note
**Quick tip**
Another frequent L2 error is trying to translate "for to buy" literally using the preposition **для**. Never say «я йду для купити». The only correct way to express this forward-looking purpose is using **щоб купити**.
:::

<!-- INJECT_ACTIVITY: fill-in-schob-forms -->
<!-- INJECT_ACTIVITY: quiz-tomuscho-vs-schob -->
<!-- INJECT_ACTIVITY: unjumble-schob-clauses -->

## Базова непряма мова: він сказав, що... (Basic Reported Speech: He Said That...) (~750 words)

In everyday conversations, we constantly need to tell someone what another person said. This grammatical concept is called **непряма мова** (indirect/reported speech). At the A2 level, you do not need to worry about complex sequences of tenses or complicated structural transformations like you might find in English grammar books. Instead, our focus is on mastering the most frequent and practical relay pattern. To report a basic statement, you simply use the conjunction **що** to connect the speaker to their original message. The most common phrase you will hear and use is «він сказав, що...» or «вона сказала, що...». This simple structure allows you to pass on information smoothly, whether you are chatting with friends or speaking to colleagues at work.

When you transform a direct quote into a reported statement, you perform a basic mechanical shift using **що**. The most important change happens to the pronouns and the verb conjugation. If the original speaker used the pronoun **я** (I), you must change it to **він** (he) or **вона** (she) to match the person you are talking about. Naturally, the verb must also change its ending to agree with this new subject. However, unlike English, the tense of the verb usually remains exactly the same as it was in the original quote. If the speaker used the future tense, you keep the future tense. If they used the past tense, you keep the past tense. This makes Ukrainian reported speech surprisingly straightforward once you grasp the pronoun shift. 

Віктор каже: «Я прийду завтра ввечері». Коли ми передаємо ці слова, ми говоримо: Віктор сказав, що він прийде завтра. Ми змінюємо особу з першої на третю, але час залишається майбутнім. Зазвичай нам не треба змінювати час дієслова при передачі інформації.

> *Viktor says: "I will come tomorrow evening". When we relay these words, we say: Viktor said that he will come tomorrow. We change the person from first to third, but the tense remains future. Usually, we do not need to change the tense of the verb when passing on information.*

While **сказати** (to say, to tell) is the most common verb for passing on information, your vocabulary will sound much richer if you use other reporting verbs. You can use **відповісти** (to answer, to reply) when someone reacts to a question in a conversation. If someone clarifies a difficult concept so that others can **зрозуміти** (to understand), you will need a specific verb for that.

For clarifications, you use **пояснити** (to explain). Sometimes a person gives extra information at the end of a discussion, so you can use **додати** (to add). All of these verbs seamlessly introduce a new clause starting with **що** to report a statement. 

Секретарка відповіла, що директор зараз на важливій зустрічі. Лікар пояснив, що цей сироп треба пити тільки вранці. В кінці нашої розмови менеджер додав, що завтра офіс не працює. Всі ці слова допомагають нам точно передати важливу інформацію.

> *The secretary answered that the director is currently at an important meeting. The doctor explained that this syrup should be taken only in the morning. At the end of our conversation, the manager added that the office is not working tomorrow. All these words help us to accurately relay important information.*

Reporting a question requires a slightly different approach than reporting a standard statement. When you want to report a yes/no question, you cannot use **що**. Instead, you must use the particle **чи** (if/whether). For example, if the direct question is «Ти будеш на роботі?», you report it using the verb **запитати** (to ask): «Він запитав, чи я буду на роботі». Notice that the reported question is no longer a real question, so it ends with a period, not a question mark. If the original question already contains a question word like «де», «коли», or «чому», you simply reuse that same word to connect the clauses. 

Новий колега запитав, чи я маю вільний час на каву. Я відповів, що зараз дуже зайнятий новим проєктом. Потім він запитав, коли я буду вільний. Я сказав, що закінчу роботу о шостій годині вечора.

> *A new colleague asked if I had free time for coffee. I answered that I am very busy with a new project right now. Then he asked when I would be free. I said that I will finish work at six o'clock in the evening.*

:::info
**Grammar box**
Remember that indirect questions are statements about a question, not actual questions. Therefore, sentences like «Вона запитала, де працює мій брат.» always end with a period. You never use a question mark at the end of a reported speech sentence.
:::

Reported speech is not just an academic exercise; it is a vital tool for everyday, practical relay scenarios. You use it constantly when you need to pass a **повідомлення** (message) from a friend to your family, or when you are explaining what someone told you on the phone. The main **мета** (goal, purpose) is to create a natural communicative context. You are summarizing real conversations to keep people informed about plans, schedule changes, or personal news. This is how native speakers manage their daily logistics and share updates with their social circle.

Олена телефонувала п'ять хвилин тому і залишила повідомлення. Вона сказала, що запізниться на вечерю через великі затори. Вона також пояснила, що забула купити яблучний сік. Я відповів, що це не проблема для нас.

> *Olena called five minutes ago and left a message. She said that she will be late for dinner because of big traffic jams. She also explained that she forgot to buy apple juice. I answered that it is not a problem for us.*

Finally, it is critical to contrast how we report simple facts versus how we report commands or strong requests. This ties reported speech directly back to the subjunctive concept we discussed in the previous section. If you want to report a factual statement, you use **що**. For example, «Він сказав, що я прийшов» means "He said THAT I came" (he is simply confirming the fact of my arrival). However, if you are reporting a command, you must use **щоб** (in order to, so that) followed by the past tense verb. The sentence «Він сказав, щоб я прийшов» means "He said that I SHOULD come". This one small difference changes the entire meaning of the sentence from a factual report to an indirect command.

Мама сказала, що мій старший брат купив свіже молоко. Це просто констатація факту. Але тато сказав, щоб брат купив свіже молоко. Це вже чіткий наказ або прохання. Різниця між цими двома реченнями дуже велика.

> *Mom said that my older brother bought fresh milk. This is just a statement of fact. But dad said that brother should buy fresh milk. This is already a clear command or a request. The difference between these two sentences is very big.*

:::note
**Quick tip**
A common mistake is using **що** when reporting a request. Always ask yourself: "Am I reporting a fact, or am I reporting what someone wants another person to do?" If it involves an action someone else must perform, use **щоб** and the past tense verb.
:::

<!-- INJECT_ACTIVITY: match-up-reported-speech -->

## Мета і повідомлення в житті (Purpose and Messages in Daily Life) (~650 words)

In daily life, purpose clauses and reported speech often interlock in a single, fluid thought. You use them constantly when you need to **пояснити** (to explain) a complex situation or **відповісти** (to answer, to reply) to a sudden scheduling conflict. Sometimes you also need to **запитати** (to ask) a friend about their personal plans while simultaneously relaying what someone else mentioned. Combining these two grammatical structures makes your spoken Ukrainian sound highly natural and sophisticated. You are no longer just making simple statements; you are connecting intentions with real-world events. This is exactly how native speakers organize their daily logistics.

Мама зателефонувала, щоб я купив свіжий хліб. Мій колега сказав, що зустріч перенесли. Це зробили, щоб ми мали більше часу. Я зателефонував брату, щоб дізнатися про його нову роботу. Він відповів, що зараз дуже зайнятий.

> *Mom called so that I would buy fresh bread. My colleague said that the meeting was rescheduled. They did this so that we would have more time. I called my brother to find out about his new job. He answered that he is very busy right now.*

These grammar tools are absolutely essential for written communication as well. When you leave a short sticky note on the kitchen counter or send a quick text **повідомлення** (message) from your phone, you rely heavily on both factual reports and indirect commands. The main **мета** (goal, purpose) of such notes is to be as brief and clear as possible. Often, you just want to **додати** (to add) a small, important detail to a previous face-to-face conversation. Because you are not speaking directly to the person at that exact moment, you must use «що» and «щоб» to set the context and give instructions clearly.

Я залишив гроші на столі, щоб ти купив молоко. Зателефонуй бабусі сьогодні ввечері. Вона сказала, що чекає на тебе. Я прочитав твоє коротке повідомлення. Я забув сказати, що повернуся дуже пізно. Я написав це, щоб ти не хвилювалася.

> *I left money on the table so that you would buy milk. Call grandma tonight. She said that she is waiting for you. I read your short message. I forgot to say that I will return very late. I wrote this so that you would not worry.*

In spoken Ukrainian, you will frequently hear high-frequency framing patterns that share news or pass on requests smoothly. This is the practical magic of **непряма мова** (indirect/reported speech). You can use these common phrases to **сказати** (to say, to tell) what you heard without taking direct responsibility for the original source of the information. It is a polite and natural way to spread news or give directions that come from a boss, a teacher, or a family member. Ultimately, memorizing these conversational chunks will help you **зрозуміти** (to understand) native speakers much faster when they tell stories.

Мені сказали, що завтра буде сильний дощ. Я чув, що наш новий сусід працює в банку. Вони попросили, щоб ми прийшли трохи раніше. Наш директор наказав, щоб усі здали звіти сьогодні. Це дуже зручні та корисні фрази. Ми використовуємо їх кожного дня.

> *I was told that there will be heavy rain tomorrow. I heard that our new neighbor works in a bank. They asked that we arrive a little earlier. Our director ordered that everyone submit their reports today. These are very convenient and useful phrases. We use them every day.*

Now, let us consolidate the three main uses of subordination you have learned so far. It is critically important to distinguish them clearly in your mind. First, we use the conjunctions «тому що» or «бо» to answer the question «Чому?» (Why?). This shows the cause of an action. Second, we use the word **щоб** (in order to, so that) to answer the question «Для чого?» (What for?). This shows the intended future result. Third, we use «що» simply to report factual statements and connect them to the person who spoke. 

Я вчу українську мову, бо хочу жити в Києві. Це причина моєї дії. Я вчу українську мову, щоб вільно говорити з друзями. Це моя головна мета. Мій друг сказав, що я вже добре говорю українською. Це просто констатація факту.

> *I am learning the Ukrainian language because I want to live in Kyiv. This is the reason for my action. I am learning the Ukrainian language in order to speak fluently with friends. This is my main goal. My friend said that I already speak Ukrainian well. This is simply a statement of fact.*

:::info
**Grammar box**
Notice how the boundaries between these concepts are strict. «Тому що» looks backward at the cause of an action. «Щоб» looks forward at the intended result. «Що» simply connects a reported fact to the speaker who said it. Keeping these three functions separate will prevent the most common sentence-building mistakes.
:::

As you continue your learning journey, try to listen specifically for «що» and «щоб» in native speech, podcasts, and media. These small connective words are the essential glue that holds the Ukrainian language together. They connect ideas, relay intentions, and allow you to navigate the complex social logistics of daily life.

Слухайте уважно, як говорять носії мови. Звертайте увагу на ці маленькі слова. Вони роблять вашу мову природною.

<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-purpose-clauses-and-reported-speech-sentences -->
<!-- INJECT_ACTIVITY: quiz-choose-between-and-to-complete-sentences -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: purpose-clauses
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

**Level: A2 (Module 48/60) — ELEMENTARY**

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
