<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 40: Що ти робив? А що зробив? (A2, A2.6 [Aspect, Tenses, and Motion])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-040
level: A2
sequence: 40
slug: aspect-in-past
version: '1.0'
title: Що ти робив? А що зробив?
subtitle: Вид дієслова в минулому часі — процес чи результат
focus: grammar
pedagogy: PPP
phase: A2.6 [Aspect, Tenses, and Motion]
word_target: 2000
objectives:
- Learner can distinguish between imperfective past (що робив?) expressing process, duration, or repetition
  and perfective past (що зробив?) expressing a completed action with a visible result.
- Learner can choose the correct aspect in past tense based on context clues (signal words, result focus,
  background vs. foreground).
- Learner can form past tense forms for both aspects of 10 common verb pairs, correctly applying gender
  and number agreement (робив/робила/робили vs. зробив/зробила/зробили).
- Learner can narrate a simple sequence of events using perfective past for completed steps and imperfective
  past for background actions.
dialogue_situations:
- setting: 'Two friends comparing how they spent Sunday — process vs result: Я читала (impf) весь день.
    А ти? Я прочитав (pf) роман (m)! Я готувала (impf) обід. Я приготувала (pf) борщ.'
  speakers:
  - Оля
  - Тарас
  motivation: 'Past aspect: читала(impf, process) vs прочитав(pf, finished)'
content_outline:
- section: Два питання — два види (Two Questions — Two Aspects)
  words: 500
  points:
  - 'The key question pair: Що ти робив? (What were you doing? — process) vs. Що ти зробив? (What did
    you get done? — result). This is not a grammar trick but a real difference in how Ukrainians think
    about actions.'
  - 'Imperfective past = the camera was rolling: Я читав книгу (I was reading). The focus is on the action
    itself, its duration, or its repetition.'
  - 'Perfective past = the photo of the result: Я прочитав книгу (I read/finished the book). The focus
    is on the completed outcome.'
  - 'Gender agreement review: він робив / вона робила / воно робило / вони робили. Same pattern for perfective:
    він зробив / вона зробила.'
- section: Коли вживати недоконаний вид (When to Use Imperfective Past)
  words: 500
  points:
  - 'Process or duration: Я довго писав листа (I was writing a letter for a long time). The action stretched
    over time.'
  - 'Repetition or habit: Вона щодня готувала сніданок (She made breakfast every day). A repeated action,
    not one single event.'
  - 'Background action: Коли я снідав, подзвонив друг (While I was having breakfast, a friend called).
    Imperfective sets the scene.'
  - 'Signal words: довго, часто, завжди, щодня, зазвичай, раніше, коли (for background).'
- section: Коли вживати доконаний вид (When to Use Perfective Past)
  words: 500
  points:
  - 'Completed result: Я написав листа (I wrote the letter — it is done). The action reached its endpoint
    and produced a result.'
  - 'Single event in sequence: Я прийшов додому, пообідав і подзвонив мамі (I came home, had lunch, and
    called Mom). Each verb marks a completed step.'
  - 'Sudden action: Раптом хтось постукав у двері (Suddenly someone knocked on the door). A single, punctual
    event.'
  - 'Signal words: вже, нарешті, раптом, одного разу, вчора (when referring to a single completed event).'
- section: Практика вибору виду (Choosing the Right Aspect)
  words: 500
  points:
  - 'Contrastive pairs in context: Він читав газету (was reading) vs. Він прочитав газету (finished reading).
    Вона вчила слова (was studying words) vs. Вона вивчила слова (learned the words).'
  - 'Mini-narratives combining both aspects: Коли я готував вечерю, раптом погасло світло. Я знайшов свічку
    і запалив її.'
  - 'Common mistakes: using imperfective when result matters (*Я писав листа вчора — ambiguous), using
    perfective for repeated actions (*Він щодня зробив вправи — wrong).'
  - 'Decision flowchart: Is there a result? → Perfective. Is it a process, habit, or background? → Imperfective.'
vocabulary_hints:
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
  recommended:
  - щодня (every day)
  - нарешті (finally, at last)
  - одного разу (one time, once)
  - тривалість (duration)
activity_hints:
- type: quiz
  focus: Given a sentence, identify whether the verb is imperfective or perfective and explain why
  items: 8
- type: fill-in
  focus: Choose the correct aspect form (imperfective or perfective past) to complete sentences based
    on context
  items: 8
- type: match-up
  focus: Match signal words (довго, раптом, щодня, нарешті) with the correct aspect and example sentence
  items: 8
- type: error-correction
  focus: Fix incorrect verb aspect usage in sentences
  items: 6
references:
- title: Заболотний Grade 6, §52-54
  notes: Вид дієслова в минулому часі — process vs. result contrast
- title: 'ULP: Past Tense and Aspect'
  url: https://www.ukrainianlessons.com/grammar-hub/
  notes: Practical examples of aspect choice in past tense

</plan_content>

## Generated Content

<generated_module_content>
## Два питання — два види (~550 words)

We often talk about the weekend by sharing what we did. But in Ukrainian, how you describe your past actions depends on whether you were just busy doing something, or if you actually achieved a result. Listen to how Olya and Taras talk about their Sunday. Notice the difference between their verbs.

> — **Оля:** Привіт, Тарасе! Що ти робив у неділю? *(Hi, Taras! What were you doing on Sunday?)*
> — **Тарас:** Привіт! Я відпочивав удома. *(Hi! I was resting at home.)*
> — **Оля:** Я читала весь день. А ти? *(I was reading all day. And you?)*
> — **Тарас:** Я прочитав новий роман! *(I read a new novel!)*
> — **Оля:** Класно. А потім я готувала обід. *(Cool. And then I was cooking lunch.)*
> — **Тарас:** А я приготував дуже смачний борщ. *(And I prepared a very tasty borscht.)*

When we talk about the **минулий час** *(past tense)*, Ukrainian uses a fundamental distinction that doesn't exist in English in the same way. Every action forces you to choose between a **процес** *(process)* and a **результат** *(result)*. This is not just a grammar trick; it is a central contrast in Ukrainian grammar.
 The easiest way to understand this is through two simple questions. If someone asks you «Що ти робив?» *(What were you doing?)*, they are asking about the process. They want to know how you spent your time. But if they ask «Що ти зробив?» *(What did you get done?)*, they are asking about the result. They want to know what you accomplished.

В українській мові часто розрізняють дію як процес і дію як результат.
 Це дуже важливо для спілкування. Коли ви говорите про процес, ви використовуєте недоконаний вид. Коли ви говорите про результат, вам потрібен доконаний вид. Дієслова «робити» та «зробити» — це ідеальний приклад цієї системи.

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

For the regular verbs shown here, you remove the infinitive ending and add the usual past tense forms; some Ukrainian verbs form the past tense less regularly.

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
If you want to emphasize that a task is finished, choose the perfective verb. The imperfective form does not mean you gave up; without context, it simply focuses on the process rather than the result.
:::

Студенти часто кажуть: «Я вчора писав листа». Без додаткового контексту це двозначно: ми розуміємо процес, але не знаємо, чи лист уже готовий. Якщо ви хочете підкреслити готовий результат, треба казати: «Я вчора написав листа». Інша помилка — це слова типу «щодня». Не можна казати: «Він щодня зробив вправи». Якщо дія повторюється, ми повинні використовувати дієслово «робив».

> *Students often say: "Yesterday I was writing a letter." Without extra context, this is ambiguous: we understand the process, but we do not know whether the letter is already finished. If you want to emphasize the finished result, you should say: "Yesterday I wrote the letter."
 Another mistake is words like "every day." You cannot say: "He did the exercises every day." If the action repeats, we must use the verb "was doing."*

The pair **писати / написати** (to write — impf./pf.) perfectly illustrates the ambiguity of the imperfective past without context. And for habits, the pair **робити / зробити** (to do — impf./pf.) reminds us that repetition always requires the imperfective form, no matter how short the action was.

To make the right choice in everyday conversations, you can use a simple mental flowchart. Ask yourself two questions before you speak. First, is there a clear, visible outcome, or is it a single step in a sequence of events? Does the action answer the question "what got done?" If the answer is yes, you need the perfective aspect. Second, are you describing a continuous duration, a repeated habit, or a background scene for another event? Does the action answer the question "what were you doing?" If the word **довго** (for a long time), "often," or "every day" fits the context naturally, you must choose the imperfective aspect. Mastering this difference takes time and patience, but it is the most rewarding part of learning the language. Trust this basic logic, practice identifying the signals in native texts, and your stories will sound perfectly natural.

<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->
<!-- INJECT_ACTIVITY: error-correction-aspect -->
</generated_module_content>

**PIPELINE NOTE — Word count: 2879 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 306 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Оля — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ відправки — NOT IN VESUM

All 306 other words are confirmed to exist in VESUM.

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
