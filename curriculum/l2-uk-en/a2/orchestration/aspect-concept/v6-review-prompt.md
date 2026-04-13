<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Зроблено чи в процесі? Вступ до виду дієслів (A2, A2.1 [Foundation and Aspect Introduction])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-002
level: A2
sequence: 2
slug: aspect-concept
version: '1.2'
title: Зроблено чи в процесі? Вступ до виду дієслів
subtitle: Концепція доконаного та недоконаного виду
focus: grammar
pedagogy: PPP
phase: A2.1 [Foundation and Aspect Introduction]
word_target: 2000
objectives:
  - Learner can define grammatical aspect (вид дієслова) and differentiate 
    between perfective (доконаний) and imperfective (недоконаний) verbs.
  - 'Learner can explain the core conceptual difference: imperfective for process/repetition,
    perfective for a single, completed result.'
  - Learner can identify the aspect of a verb in a simple sentence (past or 
    present tense).
  - Given a simple action, learner can describe it as a process (imperfective) 
    and as a completed result (perfective).
dialogue_situations:
  - setting: 'Watching a football match on TV — commenting on what''s happening vs
      what just happened: Він біжить (impf, running)! Він забив гол (pf, scored)!
      Вони грають (impf) добре. Вона передала (pf) м''яч (m, ball).'
    speakers:
      - Два друзі (watching together)
    motivation: Impf (process) vs pf (result) with гра(f), гол(m), м'яч(m)
content_outline:
  - section: Що таке вид дієслова? (What is Verb Aspect?)
    words: 500
    points:
      - 'Introduction to the concept: Ukrainian verbs have a hidden dimension called
        ''aspect''. It''s not about *when* (tense), but *how* the action unfolds.'
      - 'Meet the two types: Недоконаний вид (НВ, imperfective) for ongoing processes,
        repeated actions, or facts. Доконаний вид (ДВ, perfective) for a single, completed
        action with a clear result.'
      - 'Analogy: Imperfective is like watching a movie; perfective is like seeing
        the ''The End'' screen.'
  - section: 'Недоконаний вид: Процес і повторення (Imperfective: Process & Repetition)'
    words: 600
    points:
      - 'Focus on the uses of imperfective: describing an action in progress (''Я
        читав, коли ти подзвонив''), a repeated action (''Я читав цю книгу три рази''),
        or a general fact (''Діти читають книги'').'
      - 'Simple examples in present and past tense: ''Я читаю'' (I am reading), ''Я
        читав'' (I was reading / I used to read).'
      - 'Key signal words: завжди (always), часто (often), зазвичай (usually), довго
        (for a long time), щодня (every day).'
  - section: 'Доконаний вид: Результат! (Perfective: The Result!)'
    words: 600
    points:
      - 'Focus on the use of perfective: describing a single, successfully completed
        action. The result is what matters.'
      - 'Example: ''Я прочитав книгу'' (I have read the book, it is finished). Contrast
        with ''Я читав книгу'' (I was reading the book, maybe I finished, maybe not).'
      - 'Perfective verbs have no true present tense. Their ''present'' form has a
        future meaning (e.g., ''зроблю'' means ''I will do''). We will focus on the
        past tense for now: ''зробив'', ''написала''.'
      - 'Key signal words: раптом (suddenly), нарешті (finally), вже (already). Note:
        вчора (yesterday) works with BOTH aspects — Вчора я читав (impf) vs Вчора
        я прочитав (pf).'
  - section: 'Порівняння пар: Бачимо різницю (Comparing Pairs: Seeing the Difference)'
    words: 300
    points:
      - 'Side-by-side comparison of simple pairs: ''Він писав лист'' (He was writing
        a letter) vs. ''Він написав лист'' (He wrote a letter).'
      - 'Visual aids: timelines showing the duration of an imperfective action vs.
        the single point of completion for a perfective action.'
vocabulary_hints:
  required:
    - вид дієслова (verb aspect)
    - недоконаний вид (imperfective aspect)
    - доконаний вид (perfective aspect)
    - процес (process)
    - результат (result)
    - дія (action)
    - повторення (repetition)
    - робити / зробити (to do)
  recommended:
    - завершений (completed, finished)
    - тривалий (ongoing, lasting)
    - одноразовий (single, one-time)
    - концепція (concept)
activity_hints:
  - type: quiz
    focus: 'Aspect Sorting: Process vs. Result'
    items: 8
  - type: fill-in
    focus: Identify the Aspect in Sentences
    items: 8
  - type: match-up
    focus: Choose the Correct Aspect (Context-based)
    items: 8
  - type: error-correction
    focus: Find and fix wrong aspect choice in sentences (e.g., *Він щодня 
      зробив вправи → робив, *Вона довго написала листа → писала)
    items: 6
references:
  - title: Авраменко Grade 7, §28-30
    notes: 'Вид дієслова: доконаний і недоконаний — aspect is taught in 7th grade curriculum'
  - title: 'ULP: Ukrainian Verb Aspect'
    url: https://www.ukrainianlessons.com/ukrainian-verb-aspect/
    notes: Imperfective vs perfective

</plan_content>

## Generated Content

<generated_module_content>
## Що таке вид дієслова? (What is Verb Aspect?) (~550 words)

Imagine you are watching a football match with a friend. The attack is developing quickly, and the contrast between process and result is easy to hear. In that situation, you might hear a conversation like this:

> **Максим:** Дивись, він швидко біжить до воріт! *(Look, he is running fast to the goal!)*
> **Андрій:** Удар... і він забив красивий гол! *(A strike... and he scored a beautiful goal!)*
> **Максим:** Вони грають дуже добре сьогодні. *(They are playing very well today.)*
> **Андрій:** Так, вона класно передала м'яч. *(Yes, she passed the ball nicely.)*

In this short exchange, we can easily spot the core vocabulary of a sports match: the **гра** (game), the **гол** (goal), and the **м'яч** (ball). But if you look much closer at the verbs the friends are using, you will notice a hidden dimension of the Ukrainian language. This crucial grammatical dimension is formally called **вид дієслова** (verb aspect). It is a concept that changes everything about how you will build sentences from this point forward.

Aspect is not about *when* an action happens in the timeline of the universe, which is the specific job of grammatical tense. Instead, aspect describes exactly *how* the action unfolds in time. Let us compare the verbs from our football dialogue to see this clearly. When Maksym excitedly says «біжить» (is running), he is describing an action that is currently ongoing and active. You can picture the player's legs moving right now. However, when Andriy shouts «забив» (scored), he is not describing a continuous process at all. He is announcing an instantaneous, completed event that just occurred.

To truly understand and master Ukrainian verbs, you must formally meet the two fundamental types of aspect. The first type is the **недоконаний вид** (imperfective aspect). We use this aspect to describe an ongoing **процес** (process), a regular **повторення** (repetition) of an action, or simply to state a general, continuous fact. The second type is the **доконаний вид** (perfective aspect). This aspect is strictly reserved for a single, successfully completed **дія** (action) that has a clear, visible, and undeniable **результат** (result).

:::info
**Grammar box**
Most Ukrainian verbs exist in permanent pairs. You will learn one verb for the continuous process, and a slightly different "twin" verb for the completed result. Learning them together as a matching set will help you use aspect more naturally.
:::

У шкільній граматиці недоконані дієслова відповідають на питання «що робити?», а доконані — на питання «що зробити?».

> *In school grammar, imperfective verbs answer "what to do?", while perfective verbs answer "what to do to completion?".*

Let us look closer at those two essential questions that Ukrainian school children learn. This is the standard school explanation you will also see in Авраменко (§28-30) and in Ukrainian Lessons' overview of verb aspect. The question for the imperfective aspect focuses purely on the activity itself. It does not care about the destination or the final outcome. The question for the perfective aspect adds a tiny prefix to the question word, which acts as a signal of completion. It demands to know what has been accomplished, achieved, or finalized.

A highly helpful way to remember this grammatical distinction is the classic movie analogy. Using the imperfective aspect is exactly like watching a film frame by frame. You are observing the action as it happens continuously, like watching someone **робити** (to do) their difficult homework. You do not know if they will ever finish it. Using the perfective aspect, on the other hand, is like finally seeing the "The End" screen at the conclusion of the film. The action is entirely finished, the story is over, and you can see the final product, meaning someone managed to successfully **зробити** (to do / to have done) their homework.

Вид дієслова — це важлива концепція, яку ви повинні добре відчути. Уявіть будь-який процес як довгу пряму лінію, а фінальний результат — як яскраву крапку в кінці цієї довгої лінії.

> *Verb aspect is an important concept that you must feel well. Imagine any process as a long straight line, and the final result as a bright dot at the end of this long line.*

There is one very important, unbreakable rule about the present tense in Ukrainian grammar. Actions that are happening right now, at this exact, fleeting moment, are always imperfective. They are active processes unfolding directly before your eyes. You logically cannot be in the middle of an instantaneous completion in the present moment. Therefore, perfective verbs simply do not have a true present tense form at all. If an action is happening now, it is a process, and it must be imperfective.

Зараз ми дивимося цікавий матч і вболіваємо за нашу улюблену команду. Цей процес відбувається прямо зараз, тому ми використовуємо тільки недоконаний вид.

> *Right now we are watching an interesting match and cheering for our favorite team. This process is happening right now, so we use only the imperfective aspect.*

<!-- INJECT_ACTIVITY: quiz-aspect-sorting --> [quiz, Aspect Sorting: Process vs. Result, 8 items]

## Недоконаний вид: Процес і повторення (Imperfective: Process & Repetition) (~660 words)

Let us take a deep dive into the first essential category, which is the **недоконаний вид** (imperfective aspect). Unlike the **доконаний вид** (perfective aspect) that focuses on sudden completion, the primary and most common function of the imperfective form is to describe a continuous **процес** (process). 

When you use these verbs, you are inviting the listener to step inside the timeline of the event and witness an ongoing **дія** (action). You are emphasizing the effort, the duration, or the simple reality that the activity was happening at a specific moment, regardless of whether it ever reached a conclusion. The focus is entirely on the journey, not the destination.

Я читав цікаву книгу, коли ти несподівано подзвонив. Учора весь вечір я прибирав у своїй кімнаті, але там досі брудно. Моя сестра готувала смачну вечерю, поки ми дивилися телевізор.

> *I was reading an interesting book when you unexpectedly called. Yesterday evening I was cleaning my room the whole time, but it is still dirty there. My sister was cooking a delicious dinner while we were watching television.*

The second core function of the imperfective aspect is to express regular, habitual, or frequent **повторення** (repetition). Whenever an action happens more than once, or is part of an established routine, it automatically becomes an imperfective concept. Even if each individual event was successfully completed on its own, the overarching pattern of doing it multiple times requires the imperfective form. You are not highlighting a single finished outcome, but rather a recurring cycle or a habit that defines a lifestyle.

Я читав цю популярну книгу три рази, тому що вона мені дуже подобається. Наші сусіди завжди купують свіжі овочі на місцевому ярмарку. Кожного ранку мій брат п'є чорну каву і слухає новини.

> *I read this popular book three times because I like it very much. Our neighbors always buy fresh vegetables at the local market. Every morning my brother drinks black coffee and listens to the news.*

The third distinct use of the imperfective aspect is stating a general fact. Sometimes, you only want to confirm whether an action took place at all, or state a universal truth, without focusing on any specific **результат** (result). You do not care if someone managed to successfully **зробити** (to do) a task completely. In these situations, the imperfective verb acts as a simple naming device for the activity. You are asking about the sheer existence of the event in history, or making a broad statement about how things generally operate in the world, completely ignoring the concept of completion.

Маленькі діти часто читають яскраві книги перед сном. Ти бачив новий український фільм у кінотеатрі? Ми вчора говорили про важливі проблеми нашої школи.

> *Small children often read bright books before bed. Did you see the new Ukrainian movie at the cinema? We were talking about the important problems of our school yesterday.*

Because the imperfective aspect is so strongly tied to habits and duration, it frequently pairs with specific signal words. These adverbs act as giant neon signs pointing directly to the imperfective form. When you see the following words, you almost always need to use an imperfective verb:

- **завжди** (always)
- **часто** (often)
- **зазвичай** (usually)
- **довго** (for a long time)
- **щодня** (every day)

These words inherently describe extended periods or recurring events. This fundamentally contradicts the idea of a single, sudden completion, making the imperfective aspect the only logical choice.

:::info
**Grammar box**
Signal words are your best friends when choosing the **вид дієслова** (verb aspect). If a sentence contains a word that implies routine or extended time, you can confidently select the imperfective form without overthinking it.
:::

Мій найкращий друг завжди допомагає мені робити складні завдання. Він щодня читає свіжі новини в інтернеті. Ми довго гуляли в парку, бо погода була чудова.

> *My best friend always helps me do difficult tasks. He reads fresh news on the internet every day. We walked in the park for a long time because the weather was wonderful.*

It is crucial to understand that aspect is completely separate from tense. The aspect simply describes the internal nature of the action, while the tense tells you when it happened on the calendar. You can have an imperfective process happening right now, or you can have an imperfective process that used to happen in the past. The core identity of the action remains exactly the same; only the time frame changes. This proves that focusing on the journey is a perspective you can apply across different periods of time.

Зараз я уважно читаю цікаву статтю про історію. Учора я також довго читав цей журнал у бібліотеці. Завтра я буду читати нові матеріали для нашого проєкту.

> *Right now I am carefully reading an interesting article about history. Yesterday I also read this magazine in the library for a long time. Tomorrow I will be reading new materials for our project.*

<!-- INJECT_ACTIVITY: fill-in-identify-the-aspect-in-sentences -->

## Доконаний вид: Результат! (Perfective: The Result!) (~660 words)

Now it is time to explore the other side of the coin: the **доконаний вид** (perfective aspect). While the **недоконаний вид** (imperfective aspect) focuses on an ongoing **процес** (process), the perfective aspect cares exclusively about the destination. Its absolute core meaning is a single, successfully completed action that has a clear boundary or a final outcome. This aspect acts like a snapshot of a finished event, capturing the exact moment when an activity reaches its goal.

When you use this aspect, you are declaring that an event was brought to its logical conclusion. The duration of the event no longer matters, and the effort spent getting there is irrelevant; the only important detail is that the final **результат** (result) was successfully achieved. Ukrainian mothers often explain this fundamental difference to their children when discussing household chores, highlighting how effort does not always equal completion.

Мати часто каже сину: «Прибирати й прибрати — різні дії!» Ти довго прибирав, але так і не прибрав свою кімнату.

> *A mother often tells her son: "To clean and to have cleaned are different actions!" You were cleaning for a long time, but you still have not cleaned your room.*

To truly understand the perfective aspect, we must contrast it directly with the imperfective forms we just learned. The difference between emphasizing a process and emphasizing a result completely changes the underlying meaning of a sentence. Let us look at how the verbs **робити** (to do) and **зробити** (to do) behave, or how reading works in both aspects. If you want to announce that you successfully finished a novel and are ready to discuss the ending, you must use the perfective form.

Учора я читав нову українську книгу весь вечір. Сьогодні вранці я нарешті прочитав цю книгу до кінця. Тепер я можу дати її тобі.

> *Yesterday I was reading a new Ukrainian book all evening. This morning I finally read this book to the end. Now I can give it to you.*

When you say you were reading, you only confirm the **дія** (action) itself was happening at some point. Maybe you finished the book, or maybe you abandoned it after three pages because it was boring. However, when you say you have read it, you guarantee that the text is finished, the story is complete, and the knowledge is firmly in your head.

Because the perfective aspect fundamentally describes a completed achievement, there is a crucial grammatical rule you must memorize. Perfective verbs have no true present tense. Think about it logically: you cannot be currently in the middle of completing a single, instantaneous result right now. An action is either ongoing as a process, or it is already completely done. Therefore, when you see a perfective verb that looks like it is conjugated in the present tense, it actually carries a future meaning.

:::info
**Grammar box**
Perfective verbs cannot happen "right now" because a result is instantaneous. Their "present" forms automatically point to the future. For example, the imperfective verb for writing in the present tense simply means "I am writing". But the perfective form automatically transforms the meaning into "I will write" or "I will finish writing".
:::

Я напишу цей важливий лист завтра вранці. Мій брат купить свіжі овочі на ярмарку. Ми зробимо це складне завдання разом.

> *I will write this important letter tomorrow morning. My brother will buy fresh vegetables at the market. We will do this difficult task together.*

For now, we will not worry about mastering the future tense. In this module, we will focus exclusively on using perfective verbs in the past tense. These forms are essential for marking finished events, historical facts, and personal achievements in your past. When you want to report that someone successfully did something, wrote something, or scored a point in a game, you will always reach for the past perfective form.

Мій улюблений футболіст забив красивий гол. Моя сестра написала чудову статтю для журналу. Студент зробив усі домашні вправи.

> *My favorite football player scored a beautiful goal. My sister wrote a wonderful article for the magazine. The student did all the homework exercises.*

These sentences do not describe what people were busy doing, nor do they imply any kind of **повторення** (repetition) over time. They strictly and cleanly report what these people successfully accomplished.

Just like the imperfective forms, perfective verbs have their own set of highly reliable signal words. These adverbs highlight suddenness, completion, or the successful achievement of a goal. When you see words like suddenly, finally, or already, you almost certainly need a perfective verb to complete the thought. However, you must be extremely careful with the tricky word for yesterday. This word simply sets the historical time frame, meaning it works perfectly with both aspects depending on your focus!

Раптом почався сильний дощ, але ми вже прийшли додому. Вчора я довго читав журнал, а мій друг вчора прочитав цілу книгу.

> *Suddenly a heavy rain started, but we had already arrived home. Yesterday I read a magazine for a long time, and my friend read a whole book yesterday.*

Notice how yesterday can frame both a long, ongoing activity and a sudden, completed achievement. Your choice of the **вид дієслова** (verb aspect) depends entirely on whether you want to emphasize the long time spent on the task or the final, successful outcome.

<!-- INJECT_ACTIVITY: match-up-choose-the-correct-aspect-context-based -->

## Порівняння пар: Бачимо різницю (Comparing Pairs: Seeing the Difference) (~330 words)

In Ukrainian, almost every verb has a partner. Together, they form an aspect pair to describe every possible situation, like **робити / зробити** (to do). Usually, the base word represents the **недоконаний вид** (imperfective aspect). To create its partner, the **доконаний вид** (perfective aspect), we most often simply add a short prefix to the beginning of the word.

Найчастіше ми утворюємо доконаний вид за допомогою префікса. Наприклад, ми беремо слово «писати» і додаємо префікс «на-». Тепер ми маємо пару: «писати» і «написати». Так само працюють слова «читати» і «прочитати».

> *Most often we form the perfective aspect using a prefix. For example, we take the word "писати" and add the prefix "на-". Now we have a pair: "писати" and "написати". The words "читати" and "прочитати" work the same way.*

This prefix does not change the core meaning, but it adds the crucial idea of completion and a final **результат** (result). Let us put these pairs side by side to see how the **вид дієслова** (verb aspect) completely changes the story. When you use the imperfective form, you invite the listener to watch a **процес** (process) unfold in real-time. 

Порівняймо два речення. «Він писав лист» означає, що дія тривала у минулому. Можливо, він ще пише цей лист зараз. Але «він написав лист» означає, що лист уже готовий. Інший приклад: «вона купувала продукти» проти «вона купила продукти».

> *Let's compare two sentences. "Він писав лист" means that the action was ongoing in the past. Perhaps he is still writing this letter now. But "він написав лист" means that the letter is already ready. Another example: "вона купувала продукти" versus "вона купила продукти".*

To master this concept, try visualizing the **дія** (action) on a timeline. Imagine the imperfective aspect as a long, continuous line (`------`) showing a lasting activity, or as a series of dots (`...`) representing the **повторення** (repetition) of a habit. In contrast, picture the perfective aspect as a single, solid dot (`•`) or an arrow hitting a brick wall (`--->|`). The activity hits that wall, stops completely, and leaves a permanent mark.

:::note
**Quick tip**
When you learn a new verb, always try to memorize its aspect pair right away. Knowing both forms is the key to speaking naturally and accurately describing your daily life.
:::

<!-- INJECT_ACTIVITY: error-correction-fix-aspect --> [error-correction, Find and fix wrong aspect choice in sentences, 6 items]
</generated_module_content>

**PIPELINE NOTE — Word count: 2807 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 264 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Авраменко — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM

All 264 other words are confirmed to exist in VESUM.

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
