<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Майбутній час і вид дієслова (B1, B1.0 [Baselines & Aspect Mastery])
**Writer:** Gemini
**Word target:** 4000

## Plan (source of truth)

<plan_content>
module: b1-002
level: B1
sequence: 2
slug: b1-baseline-future-aspect
version: '3.0'
title: "Майбутній час і вид дієслова"
subtitle: "Три форми майбутнього часу та видові пари"
focus: review
pedagogy: PPP
phase: "B1.0 [Baselines & Aspect Mastery]"
word_target: 4000
objectives:
  - "Learner can distinguish and produce all three forms of the Ukrainian future tense:
    проста (доконаного виду), складна (синтетична: -тиму, -тимеш), and складена (аналітична:
    буду + інфінітив)"
  - "Learner can explain the concept of вид дієслова (aspect) using Ukrainian metalanguage
    and correctly identify доконаний vs недоконаний вид"
  - "Learner can form видові пари for common verbs and choose the correct aspect in
    context (completed action vs ongoing/habitual)"
  - "Learner can conjugate future-tense verbs across all persons and numbers, including
    irregular patterns"
  - "Learner can use future tense and aspect together in connected speech to describe
    plans, predictions, and intentions"
dialogue_situations:
  - setting: 'Planning committee at a Харківський університет (m, Kharkiv university)
      — organizing a charity concert: Ми будемо збирати (impf) кошти (pl, funds).
      Оголосимо (pf) дату завтра. Хто напише (pf) афішу (f, poster)?'
    speakers:
      - Голова комітету
      - Волонтери
    motivation: 'Future tense + aspect: analytic (будемо збирати) vs synthetic (оголосимо,
      напише)'
content_outline:
  - section: "Що таке вид дієслова?"
    words: 650
    points:
      - "Core concept from Литвінова Grade 7 p.30: Дієслова мають категорію виду.
        Доконаний вид (від слова доконати, тобто здійснити що-небудь, виконати до
        кінця) позначає завершену, обмежену в часі дію: що зробити? що зробив? що
        зробить? Недоконаний вид позначає тривалу, повторювану або незавершену дію:
        що робити? що робив? що робить? що робитиме?"
      - "Видові пари — aspect pairs connected by meaning but differing in completeness.
        Formation patterns from Литвінова Grade 7 p.32: — Prefix addition: писати
        (недок.) → написати (док.), читати → прочитати, робити → зробити. — Suffix
        change: відповідати (недок.) → відповісти (док.), показувати → показати. —
        Suppletion: брати (недок.) → взяти (док.), говорити → сказати, класти → покласти."
      - "Special categories from Литвінова Grade 7 p.32: Двовидові дієслова: атакувати,
        веліти, женити, телеграфувати — aspect determined only by context. Одновидові
        дієслова: only доконаний (придбати, схаменутися) or only недоконаний (сподіватися,
        потріскувати)."
      - "Reading practice: short Ukrainian text about weekend plans using both aspects.
        Learners identify кожне дієслово and its вид."
  - section: "Проста форма майбутнього часу"
    words: 600
    points:
      - "From Литвінова Grade 7 p.48: Дієслова доконаного виду утворюють просту форму
        майбутнього часу додаванням відповідних закінчень. Ці закінчення такі самі,
        як i в дієслів недоконаного виду в теперішньому часі. Conjugation table: 1-ша:
        напишу, зроблю / напишемо, зробимо 2-га: напишеш, зробиш / напишете, зробите
        3-тя: напише, зробить / напишуть, зроблять"
      - "Key insight for learners: the perfective future LOOKS like present tense
        conjugation, but with a perfective verb it automatically means future. Compare:
        я пишу (I write — present, недок.) vs я напишу (I will write — future, док.).
        The prefix на- makes it perfective, and perfective verbs cannot have present
        tense."
      - "Practice with common perfective verbs: зробити (зроблю, зробиш...), прочитати
        (прочитаю, прочитаєш...), побачити (побачу, побачиш...), сказати (скажу, скажеш...),
        приїхати (приїду, приїдеш...), відповісти (відповім, відповіси...). Learners
        conjugate and use in sentences about future events."
  - section: "Складна (синтетична) форма майбутнього часу"
    words: 600
    points:
      - "From Литвінова Grade 7 p.49: Дієслова недоконаного виду утворюють складну
        форму майбутнього часу: основа інфінітива + суфікс -м- + особове закінчення.
        Note: 'проста форма' is only for perfective verbs (доконаний вид). Conjugation:
        1-ша: писатиму, робитиму / писатимемо, робитимемо 2-га: писатимеш, робитимеш
        / писатимете, робитимете 3-тя: писатиме, робитиме / писатимуть, робитимуть"
      - "Morphological analysis: the -тиму/-тимеш endings are historically from інфінітив
        + иму (скорочена форма дієслова мати): писати + иму → писатиму. This explains
        why the інфінітив base is preserved in the form."
      - "Contrastive practice: складна vs проста форма. Я писатиму листа (ongoing
        writing) vs Я напишу листа (will complete). Ми працюватимемо (we will be working)
        vs Ми зробимо (we will do/finish). Learners choose the correct form based
        on context clues in sentences."
  - section: "Складена (аналітична) форма майбутнього часу"
    words: 550
    points:
      - "From Кравцова Grade 4 p.108 and Литвінова Grade 7 p.49: Дієслово бути в особовій
        формі + інфінітив основного дієслова. Conjugation of бути: 1-ша: буду / будемо
        2-га: будеш / будете 3-тя: буде / будуть Example: буду писати, будеш читати,
        буде працювати."
      - "Key distinction: only the допоміжне дієслово бути changes form — the основне
        дієслово stays in the інфінітив. Compare with the складна форма where the
        verb itself carries the ending."
      - "Usage note: складена форма is more common in spoken Ukrainian and in Western
        dialects. Складна форма is equally correct and common in literary/written
        Ukrainian. Both express the same meaning — imperfective future. Learners should
        recognize and produce both."
      - "Reading practice: dialogue between two friends planning a trip, using all
        three future forms. Learners identify which form is used and why."
  - section: "Вид і час — як вони працюють разом"
    words: 650
    points:
      - "The aspect-tense matrix from Авраменко Grade 7 p.54: Недоконаний вид has
        three tenses: минулий (читав), теперішній (читаю), майбутній (читатиму / буду
        читати). Доконаний вид has only two: минулий (прочитав), майбутній (прочитаю).
        Critical insight: дієслова доконаного виду НЕ МАЮТЬ теперішнього часу. All
        learners at B1 must internalize this rule."
      - "Common errors and how to avoid them: — Using perfective with теперішній час:
        *я прочитаю зараз (WRONG as present). прочитаю = future only. For 'I am reading
        now' → я читаю. — Confusing складна and складена: писатиму (one word, synthetic)
        vs буду писати (two words, analytic). Both = imperfective future. — Forgetting
        aspect in narrative: Вчора я *писав листа i *написав його. → Вчора я писав
        листа i написав його (mixing aspects correctly: process then completion)."
      - "Extended practice: learners retell a Ukrainian folk tale using correct aspect-tense
        combinations. Model text provided with aspect annotations. Focus on narrative
        flow: background (недок.) vs completed events (док.)."
  - section: "Дієвідмінювання у майбутньому часі"
    words: 550
    points:
      - "From Заболотний Grade 7 p.65: Three forms side by side for the same verb
        root: проста (perfective): принесу, принесеш, принесе... складна (synthetic
        imperfective): носитиму, носитимеш, носитиме... складена (analytic imperfective):
        буду носити, будеш носити... Practice table with 5 verb pairs for full conjugation."
      - "Spelling traps in future forms: — Consonant alternations in perfective: сидіти
        → сиджу (not *сидю), водити → воджу, просити → прошу. These alternations from
        A2 apply in the future too: я попрошу, ти попросиш. — The -тиму forms preserve
        the full інфінітив base: малювати → малюватиму (not *малютиму)."
      - "Contextual practice: learners complete a letter to a friend about summer
        plans, choosing between all three future forms based on whether actions are
        completed goals or ongoing activities."
  - section: "Підсумок: вид і майбутнє у дії"
    words: 400
    points:
      - "Decision tree for choosing the right future form: 1. Is the action completed/one-time?
        → доконаний вид → проста форма (зроблю, напишу, прочитаю). 2. Is the action
        ongoing/habitual? → недоконаний вид → pick one: a) складна форма (робитиму,
        писатиму) — equally common; b) складена форма (буду робити, буду писати) —
        equally common. Both 2a and 2b are correct; neither is 'more formal' or 'more
        casual.'"
      - "Self-check questions in Ukrainian: 1. Які три форми майбутнього часу є в
        українській мові? 2. Чому дієслова доконаного виду не мають теперішнього часу?
        3. Утворіть видову пару: писати → ? / читати → ? / говорити → ? 4. Відмініть
        у майбутньому часі: зробити, працювати."
      - "Preview of next module: Людина i стосунки (M06) — describing people and relationships,
        applying future tense in context ('Я познайомлю тебе з моєю подругою,' 'Ми
        будемо зустрічатися щотижня')."
vocabulary_hints:
  required:
    - "вид дієслова (verbal aspect — grammatical category of completion)"
    - "доконаний вид (perfective aspect — completed, bounded action)"
    - "недоконаний вид (imperfective aspect — ongoing, unbounded action)"
    - "видова пара (aspect pair — two verbs differing only in aspect)"
    - "майбутній час (future tense)"
    - "проста форма (simple form — perfective future: напишу)"
    - "складна форма (synthetic/compound form — imperfective future: писатиму)"
    - "складена форма (analytic form — imperfective future: буду писати)"
    - "інфінітив (infinitive — base verb form ending in -ти/-тися)"
    - "дієвідміна (verb conjugation class — I or II)"
    - "особове закінчення (personal ending — verb suffix marking person/number)"
    - "дієвідмінювання (conjugation — changing verb form by person/number)"
    - "двовидовий (biaspectual — verb that can be either aspect: атакувати)"
    - "одновидовий (single-aspect — verb existing in only one aspect)"
  recommended:
    - "тривала дія (ongoing action — characteristic of imperfective)"
    - "завершена дія (completed action — characteristic of perfective)"
    - "допоміжне дієслово (auxiliary verb — бути in analytic future)"
    - "суфікс (suffix — word-building element after the root)"
    - "дійсний спосіб (indicative mood — states facts, has all three tenses)"
    - "основа інфінітива (infinitive stem — base for building future forms)"
    - "часова форма (tense form — specific conjugated form of a verb)"
    - "повторювана дія (repeated action — characteristic of imperfective)"
    - "наголос (stress — emphasized syllable, may shift in conjugation)"
    - "чергування приголосних (consonant alternation — e.g., просити → прошу)"
activity_hints:
  - type: quiz
    focus: "Identify вид дієслова: доконаний чи недоконаний? Given verb forms in context,
      learner classifies aspect."
    items: 8
  - type: match-up
    focus: "Match видові пари: connect imperfective verbs to their perfective partners
      (писати↔написати, говорити↔сказати, брати↔взяти)."
    items: 8
  - type: fill-in
    focus: "Complete sentences with the correct future form (проста, складна, or складена)
      based on context clues about completion vs ongoing action."
    items: 8
  - type: group-sort
    focus: "Sort verb forms into three groups: проста / складна / складена форма майбутнього
      часу."
    items: 10
  - type: error-correction
    focus: "Find and fix aspect/tense errors in Ukrainian sentences (e.g., using perfective
      as present, wrong future form choice)."
    items: 6
  - type: free-write
    focus: "Write 5-7 sentences about your plans for next week using all three future
      forms and both aspects."
    items: 6
connects_to:
  - "b1-004 (Минуле i теперішнє — past/present review, complements future)"
  - "b1-007 (Контрольна робота 1 — checkpoint testing all Phase 1 material)"
  - "b1-010 (Чергування приголосних у дієсловах — consonant alternations in verb conjugation)"
prerequisites:
  - "A2 completion (learner knows basic verb conjugation, past and present tense)"
  - "b1-004 (Минуле i теперішнє — past/present baseline review)"
grammar:
  - "Вид дієслова: доконаний vs недоконаний, видові пари, двовидові/одновидові"
  - "Проста форма майбутнього часу (perfective future): напишу, зроблю"
  - "Складна (синтетична) форма: основа інфінітива + -тиму/-тимеш/-тиме..."
  - "Складена (аналітична) форма: буду/будеш/буде + інфінітив"
  - "Aspect-tense interaction: perfective has no present tense"
  - "Consonant alternations in perfective future conjugation"
register: науково-навчальний
references:
  - title: "Литвінова Grade 7, p.30-32"
    notes: "Core chapter on вид дієслова: definitions, видові пари, двовидові/одновидові."
  - title: "Литвінова Grade 7, p.48-49"
    notes: "Майбутній час: проста (perfective), складна, складена forms with conjugation
      tables and formation rules."
  - title: "Заболотний Grade 7, p.54-65"
    notes: "Часи дієслова chapter: aspect-tense interaction, all three future forms
      with exercises, literary examples from Сосюра and Гончар."
  - title: "Авраменко Grade 7, p.54-68"
    notes: "Вид дієслова and майбутній час: classification exercises, test-format
      practice, note that present-tense verbs are always imperfective."
  - title: "Кравцова Grade 4, p.108"
    notes: "Змінювання дієслів у майбутньому часі: early introduction of one-word
      vs two-word future forms."
  - title: "Заболотний Grade 7, p.181-183"
    notes: "Часи дієслів, їх творення: systematic review at senior level, двовидові
      дієслова examples."

</plan_content>

## Generated Content

<generated_module_content>
## Що таке вид дієслова?

As highlighted in standard textbooks like Литвінова Grade 7, the concept of verbal aspect is the soul of the Ukrainian verb within the дійсний спосіб (indicative mood), which states facts across all tenses. For an English speaker, the most important question about an action is usually "when did it happen?" You map events onto a timeline: past, present, or future. In Ukrainian, the fundamental question is "is the action in progress, or is it done?" This binary nature of completion dictates how verbs behave. You must shift your mindset from focusing solely on the timeline to focusing on the result. Every time you use a verb, you decide if you are describing an ongoing process or a completed fact.

У граматиці ця категорія називається вид дієслова. Підручники часто дають таке правило: недоконаний вид позначає тривалу, повторювану або незавершену дію. Натомість доконаний вид позначає завершену, обмежену в часі дію. Від слова «доконати» — тобто здійснити що-небудь, виконати до кінця.

> *In grammar, this category is called verbal aspect. Textbooks often give the following rule: the imperfective aspect denotes a continuous, repeated, or unfinished action. In contrast, the perfective aspect denotes a completed action, limited in time. From the word "доконати" — that is, to accomplish something, to fulfill it to the end.*

If you focus on the effort, the habit, or the duration of an event, you use the imperfective aspect. If you focus on the finish line, the outcome, or the one-time achievement, you use the perfective aspect. 

How do you know which aspect a verb belongs to? The classic school method is the "Infinitive Question" test. You simply ask a question to the dictionary form of the verb. If the question is «Що робити?» (What to do?), the verb is imperfective. If the question is «Що зробити?» (What to have done?), the verb is perfective.

Зверніть увагу на префікс «з-» у другому питанні. Він є ключем до розуміння. Префікс «з-» у питанні «що зробити?» сигналізує, що ми шукаємо результат. Ми питаємо не про процес роботи, а про її завершення.

This simple trick helps categorize almost any verb. Here are five essential pairs to illustrate the difference between the ongoing process and the completed result:

- писати (to write, process) — написати (to write, result)
- читати (to read, process) — прочитати (to read, result)
- робити (to do/make, process) — зробити (to do/make, result)
- малювати (to draw, process) — намалювати (to draw, result)
- їсти (to eat, process) — поїсти (to eat, result)

:::info
**The Aspect Rule of Thumb**
Always learn Ukrainian verbs in pairs. If you only memorize the imperfective form, you will not be able to say "I have read this book" or "I will finish this chapter tomorrow." You need both halves of the pair to express yourself fully.
:::

Most Ukrainian verbs exist in these "married" pairs, connected by meaning but differing in completeness. How do these pairs form? There are three main patterns. The most common pattern is prefixation, where you add a short prefix like «на-», «про-», or «з-» to the imperfective verb to make it perfective. We saw this in the previous examples.

Другий спосіб — це зміна суфікса всередині слова. У таких парах дієслова часто чергують суфікси «-а-», «-и-» або «-ва-». Наприклад: відповідати та відповісти, записувати та записати, показувати та показати. Третій спосіб — це суплетивізм, коли дієслова утворюють пару з абсолютно різних коренів.

> *The second method is changing the suffix inside the word. In such pairs, verbs often alternate the suffixes "-a-", "-и-", or "-ва-". For example: to answer (imperfective) and to have answered (perfective), to write down (imperfective) and to have written down (perfective), to show (imperfective) and to have shown (perfective). The third method is suppletion, when verbs form a pair from completely different roots.*

Suppletive pairs are the trickiest because they look nothing alike. The classic examples are говорити (to speak) matching with сказати (to have said), or брати (to take) matching with взяти (to have taken), or класти (to put) matching with покласти (to have put). You must memorize these exact matches.

While most verbs enjoy a partnered life, there are special categories of verbs that break the mold. First, there are biaspectual verbs (двовидові дієслова). These verbs look exactly the same regardless of whether the action is completed or ongoing; only the surrounding context tells you the aspect. Common examples are loan words like атакувати (to attack) or телеграфувати (to telegraph), as well as native verbs like веліти (to command) and женити (to marry).

Також існують одновидові дієслова. Вони мають лише одну форму і ніколи не утворюють пари. Деякі з них існують тільки в недоконаному виді, як-от «сподіватися» або «потріскувати». Інші існують виключно в доконаному виді, наприклад, «схаменутися» або «придбати».

:::note
**Why are they single-aspect?**
Some actions inherently cannot be completed (like hoping or crackling), while others happen so instantaneously (like coming to one's senses) that they cannot be a prolonged process. Their very meaning restricts them to a single aspect.
:::

Let's look at how the choice of aspect completely changes the meaning of a schedule. Read this short narrative about a student's Saturday plans in Kharkiv. Pay close attention to whether the student is describing an ongoing activity or a committed goal.

У суботу вранці я буду читати новий роман Жадана. Я прочитаю перший розділ до обіду. Потім я писатиму есе для університету. Я сподіваюся, що я напишу його швидко, бо ввечері ми з друзями підемо гуляти містом.

> *On Saturday morning I will be reading a new novel by Zhadan. I will have read the first chapter by noon. Then I will be writing an essay for the university. I hope that I will write it quickly, because in the evening my friends and I will go for a walk around the city.*

Notice the difference? The phrase «буду читати» means the student will spend time in the process of reading, but it does not guarantee they will finish the book. However, «прочитаю» is a firm commitment to a result: the first chapter will be done. Similarly, «писатиму» indicates the effort of working on the essay, while «напишу» focuses on finishing the task. Aspect isn't just a grammar rule; it's how you communicate your intentions.

<!-- INJECT_ACTIVITY: quiz-aspect-identification -->
<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->

## Проста форма майбутнього часу

Following the curriculum of Литвінова Grade 7, we are now ready to build the first of the three future tense forms: the simple form. The simple future, known in Ukrainian as **проста форма**, is unique because it belongs exclusively to perfective verbs (доконаний вид). Remember that perfective verbs describe completed actions, results, or reached goals. Because an action that is definitively completed cannot be happening right now in the present moment, perfective verbs do not have a present tense. When you take a perfective verb and conjugate it using the standard present-tense endings you learned in the A2 level, you automatically create the future tense.

Дієслова доконаного виду ніколи не мають форми теперішнього часу, оскільки дія вже завершена або буде завершена. Якщо ви візьмете дієслово недоконаного виду, наприклад «писати», і додасте до нього префікс «на-», ви отримаєте нове слово «написати». Коли ви відмінюєте це нове слово за правилами теперішнього часу, ви автоматично говорите про майбутнє. Форма «я пишу» означає процес зараз, а форма «я напишу» означає результат, який ви отримаєте згодом.

> *Perfective verbs never have a present tense form, because the action is already completed or will be completed. If you take an imperfective verb, for example "to write", and add the prefix "на-" to it, you get the new word "to have written". When you conjugate this new word according to the rules of the present tense, you are automatically talking about the future. The form "I am writing" means a process right now, while the form "I will write" means a result that you will get later.*

The mechanics of conjugation for the simple future are identical to the present tense. You still need to identify whether the verb belongs to the first conjugation or the second conjugation. Let's look at the first conjugation using the perfective verb **написати**. The endings are exactly what you expect: я напишу, ти напишеш, він/вона напише, ми напишемо, ви напишете, вони напишуть. Now let's take a second conjugation perfective verb, such as **зробити**. The pattern holds perfectly: я зроблю, ти зробиш, він/вона зробить, ми зробимо, ви зробите, вони зроблять. The endings have not changed at all; only the aspect has changed the time signature of the word.

:::info
**The Time Machine Prefix**
When you see a verb with a prefix like **по-**, **на-**, **з-**, or **про-**, always pause and ask yourself if it is a perfective verb. If it is, and it looks like it is conjugated in the present tense, it is actually the simple future tense. The prefix is your primary visual clue that the action belongs to the future.
:::

When should you use the simple future tense? This form is your go-to tool for expressing results, promises, and specific commitments. Whenever you want to assure someone that a task will be finished, or when you are stating a definitive fact about a future achievement, the simple future is required. Think of it as the equivalent of saying "I will definitely get this done" rather than just "I will spend time doing this."

Проста форма майбутнього часу ідеально підходить для обіцянок та гарантій. Якщо ваш друг чекає на вас, ви кажете: «Я прийду вчасно». Це означає, що ви точно досягнете мети. Якщо ваша улюблена команда грає у фіналі, ви з упевненістю кажете: «Ми обов'язково виграємо цей матч». В обох випадках дія є одноразовою і має конкретний результат.

> *The simple form of the future tense is perfectly suited for promises and guarantees. If your friend is waiting for you, you say: "I will arrive on time." This means that you will definitely reach the goal. If your favorite team is playing in the final, you confidently say: "We will definitely win this match." In both cases, the action is a one-time event and has a specific result.*

It is important to contrast this with the English "will" future. In English, "I will write a letter" can sometimes state a general intention, but in Ukrainian, choosing **я напишу листа** means the letter will exist as a finished product. If you just plan to spend your evening working on a letter without necessarily finishing it, you cannot use this form.

Because the simple future uses the exact same mechanics as the present tense, all the consonant alternations you learned previously apply here as well. You must watch out for stems that shift their final consonant when conjugated. The perfective verb **сказати** alternates just like its imperfective partner: it becomes я скажу, ти скажеш (not *сказаю*). Similarly, **попросити** shifts the consonant for the first person singular: я попрошу, ти попросиш. Other common perfective forms include побачити (побачу, побачиш) and приїхати (приїду, приїдеш).

Окрім звичайних чергувань, існують також дієслова з особливими формами, які потрібно просто запам'ятати. Наприклад, дієслово «відповісти» має такі форми: я відповім, ти відповіси, він відповість, ми відповімо, ви відповісте, вони дадуть відповідь. Так само відмінюється дієслово «дати»: я дам, ти даси, він дасть, ми дамо, ви дасте, вони дадуть. Ці короткі слова дуже часто використовуються в щоденних розмовах, тому їх варто вивчити напам'ять.

> *Besides the usual alternations, there are also verbs with special forms that you just need to memorize. For example, the verb "to answer" has the following forms: I will answer, you will answer, he will answer, we will answer, you will answer, they will answer. The verb "to give" is conjugated in the same way: I will give, you will give, he will give, we will give, you will give, they will give. These short words are used very often in daily conversations, so it is worth learning them by heart.*

Let's observe a short interaction using these specific forms to see how natural they sound in context.

> — **Студент:** Коли ви дасте нам результати тесту? *(When will you give us the test results?)*
> — **Викладач:** Я відповім на всі запитання завтра. *(I will answer all questions tomorrow.)*
> — **Студент:** Добре, я почекаю. *(Good, I will wait.)*

By mastering the simple future, you unlock the ability to make plans with certainty and communicate your intentions with absolute clarity.

## Складна (синтетична) форма майбутнього часу

The Ukrainian language possesses a distinct feature: the synthetic, or compound, form of the future tense. Known as the **складна форма**, this structure allows you to express ongoing or repetitive future actions using a single word, such as **писатиму** (I will be writing). Unlike Russian, which relies solely on a two-word analytic construction for the imperfective future, Ukrainian retains this one-word alternative. Understanding its historical roots makes it much easier to learn. Centuries ago, speakers used the infinitive of a verb followed by a conjugated form of the archaic verb **имати** (to have). For example, to say that you have to write, you would say «писати иму». Over time, these two words naturally merged into one, creating the modern ending. The infinitive fused with the auxiliary verb, resulting directly in the word **писатиму**. This linguistic history explains why the full infinitive remains perfectly visible inside the modern conjugation.

Щоб утворити складну форму майбутнього часу, вам потрібно взяти повний інфінітив дієслова недоконаного виду і додати до нього спеціальні закінчення. Ці закінчення завжди однакові для всіх дієслів, незалежно від їхньої дієвідміни. Ви просто додаєте суфікс «-м-» та особове закінчення: я працюватиму, ти працюватимеш, він працюватиме, ми працюватимемо, ви працюватимете, вони працюватимуть. Зверніть особливу увагу на те, що уся основа інфінітива (infinitive stem), включаючи «ти», завжди зберігається всередині слова. Навіть дуже коротке дієслово «жити» легко відмінюється за цим правилом: я житиму, ти житимеш, вона житиме, ми житимемо, ви житимете, вони житимуть. Це правило працює ідеально і без жодних винятків для всіх дієслів недоконаного виду.

> *To form the synthetic future tense, you need to take the full infinitive of an imperfective verb and add special endings to it. These endings are always the same for all verbs, regardless of their conjugation class. You simply add the suffix "-m-" and the personal ending: I will be working, you will be working, he will be working, we will be working, you will be working, they will be working. Pay special attention to the fact that the part "ty" from the infinitive is always preserved inside the word. Even a very short verb like "to live" is easily conjugated according to this rule: I will be living, you will be living, she will be living, we will be living, you will be living, they will be living. This rule works perfectly and without any exceptions for all imperfective verbs.*

:::info
**The Synthetic Future Endings**
Just remember to attach these endings directly to the infinitive:
- я **-тиму**
- ти **-тимеш**
- він/вона/воно **-тиме**
- ми **-тимемо**
- ви **-тимете**
- вони **-тимуть**
:::

You might be wondering when to use this synthetic one-word form instead of the two-word analytic form like **буду працювати**. Grammatically, both forms are absolutely identical in meaning. They both express an imperfective future action, meaning an action that will be ongoing, continuous, or repeated without a focus on completion. However, there is a subtle and beautiful nuance in register and tone. The synthetic form often sounds slightly more literary, elegant, or poetic to native speakers. Famous Ukrainian writers and poets frequently chose forms like **кохатиму** (I will love) or **шукатиме** (he will search) because of their melodic rhythm and distinctively Ukrainian character. While you will hear the two-word form very often in casual, everyday speech, using the synthetic form elevates your language. It shows that you have a deep grasp of Ukrainian morphology and a strong sense of stylistic variety. For a learner at this level, confidently dropping a word like **робитиму** into a conversation is an excellent way to sound more authentic and natural. It demonstrates that you are actually thinking within the structures of the Ukrainian language.

Ця форма майбутнього часу є надзвичайно стабільною і передбачуваною у використанні. На відміну від простої форми доконаного виду або теперішнього часу, тут ніколи не відбувається чергування приголосних в основі слова. Якщо інфінітив звучить як «малювати», то майбутній час завжди буде «малюватиму», і ви ніколи не скажете «малютиму». Якщо інфінітив — це «сидіти», форма буде «сидітиму», без жодних змін приголосних, які ми зазвичай бачимо у формі «сиджу». Ця граматична стабільність робить форму дуже зручною та легкою для запам'ятовування. Важливо лише пам'ятати, що це форма недоконаного виду, тобто вона описує виключно процес дії. Якщо ви скажете «я ходитиму до школи», це означає регулярний процес або звичку. Але якщо ви хочете повідомити про одноразовий результат, ви повинні обов'язково використати просту доконану форму: «я прийду до школи». Вибір правильної форми майбутнього часу завжди залежить від того, чи важливий для вас процес дії, чи її конкретний фінальний результат.

> *This form of the future tense is extremely stable and predictable in use. Unlike the simple perfective form or the present tense, consonant alternations in the stem of the word never occur here. If the infinitive sounds like "to draw," the future tense will always be "I will be drawing," and you will never say "malyuyumu." If the infinitive is "to sit," the form will be "I will be sitting," without any of the consonant changes we usually see in the form "I sit." This grammatical stability makes the form very convenient and easy to remember. It is only important to remember that this is an imperfective form, meaning it exclusively describes the process of an action. If you say "I will be walking to school," it means a regular process or habit. But if you want to report a one-time result, you must definitely use the simple perfective form: "I will arrive at school." Choosing the correct future tense form always depends on whether the process of the action or its specific final result is important to you.*

<!-- INJECT_ACTIVITY: group-sort-future-forms --> [Group-sort: Categorize verb forms into Проста, Складна, and Складена groups, 10 items]

## Складена (аналітична) форма майбутнього часу

We have reached the third and final way to talk about the future in Ukrainian: the analytic, or compound, form of the imperfective future tense. In Ukrainian, it is called the «складена форма». This structure is incredibly familiar and intuitive for English speakers. It is a two-part construction consisting of the auxiliary verb «бути» (to be) and the infinitive of the main verb. The beauty of this form lies in its absolute simplicity. The main verb never changes; it stays frozen in its dictionary infinitive form. The only word you conjugate is the short auxiliary verb «бути», which takes on the job of showing the person and the number. Because it is built from an imperfective infinitive, this form exclusively describes ongoing, continuous, or repeated actions in the future, never one-time completed results.

Дієслово «бути» в українській мові є унікальним. У майбутньому часі воно має власну, особливу систему відмінювання, яку потрібно просто запам'ятати. Це дієслово не підпорядковується загальним правилам виду, і його наголос (stress) залишається стабільним, тому воно функціонує як універсальний допоміжний інструмент. Щоб утворити складену форму, ви берете особову форму дієслова «бути» і додаєте до неї будь-який інфінітив недоконаного виду. Ось повна парадигма відмінювання: я буду, ти будеш, він/вона/воно буде, ми будемо, ви будете, вони будуть.

> *The verb "to be" in the Ukrainian language is unique. In the future tense, it has its own special conjugation system that you just need to memorize. This verb does not follow the general rules of aspect, so it functions as a universal auxiliary tool. To form the compound form, you take the personal form of the verb "to be" and add any imperfective infinitive to it. Here is the full conjugation paradigm: I will, you will, he/she/it will, we will, you will, they will.*

Let's see how native speakers mix all three future forms in a real conversation. Imagine a planning committee at a Kharkiv university (Харківський університет) organizing a charity concert.

> — **Голова комітету:** Ми будемо збирати кошти цілий тиждень. *(We will be collecting funds all week.)*
> — **Волонтер 1:** А коли ми оголосимо дату концерту? *(And when will we announce the date of the concert?)*
> — **Голова комітету:** Оголосимо дату завтра вранці. *(We will announce the date tomorrow morning.)*
> — **Волонтер 2:** Добре, тоді я сьогодні ввечері напишу афішу. *(Good, then I will write the poster tonight.)*
> — **Волонтер 1:** А я буду поширювати інформацію в соціальних мережах. *(And I will be spreading the information on social networks.)*

In this short exchange, «будемо збирати» and «буду поширювати» are analytic imperfective forms describing continuous processes. Meanwhile, «оголосимо» and «напишу» are simple perfective forms indicating specific, completed results. 

For many learners, the analytic form becomes a grammatical safe harbor. When you are speaking quickly and cannot immediately remember the complex consonant alternations of a perfective verb, or if you are unsure about the synthetic endings, you can always rely on «буду» plus the infinitive. It is structurally foolproof. However, it is not just a learner's shortcut; it is a highly natural and frequent feature of the language.

Ця форма є надзвичайно поширеною в сучасному розмовному мовленні, особливо в західних регіонах України. Ви постійно чутимете конструкції на кшталт «я буду працювати» або «ми будемо чекати». Важливо розуміти, що складена форма («буду працювати») і складна форма («працюватиму») є абсолютно рівноцінними та взаємозамінними. Обидві форми є стовідсотково правильними. Різниця полягає лише в тонких стилістичних відтінках. Форма «працюватиму» звучить трохи більш літературно та має традиційно українське звучання, тоді як «буду працювати» є цілком нейтральною та повсякденною. Вибір між ними залежить виключно від вашого смаку.

> *This form is extremely widespread in modern spoken language, especially in the western regions of Ukraine. You will constantly hear constructions like "I will be working" or "we will be waiting." It is important to understand that the analytic form ("I will work" [two words]) and the synthetic form ("I will work" [one word]) are absolutely equivalent and interchangeable. Both forms are one hundred percent correct. The difference lies only in subtle stylistic nuances. The form "працюватиму" sounds a bit more literary and traditionally Ukrainian, while "буду працювати" is completely neutral and everyday. The choice between them depends exclusively on your taste.*

:::tip
**Did you know?**
While both imperfective future forms are interchangeable, Ukrainian writers often prefer the synthetic «-тиму» form in poetry and literature because it has a beautiful, flowing rhythm and feels deeply authentic to the language's historical roots. However, in a casual chat with friends, «буду» is always a perfect choice.
:::

<!-- INJECT_ACTIVITY: fill-in-future-choice --> [Fill-in: Complete sentences with the correct future form (проста, складна, складена) based on context, 8 items]

## Вид і час — як вони працюють разом

Using the aspect-tense matrix from Авраменко Grade 7, it is time to look at the entire system. How do aspect and tense interact in Ukrainian? The system is strictly logical if you remember one core principle: aspect dictates which tenses a verb can have.

В українській мові дієслова недоконаного виду мають усі три часи: минулий, теперішній і майбутній. Ви можете сказати «я читав» учора, «я читаю» зараз і «я буду читати» завтра. Натомість дієслова доконаного виду мають лише два часи: минулий і майбутній. Вони позначають результат дії, а результат — це завжди конкретна точка на шкалі часу. Як тільки ви опиняєтеся всередині цієї точки, дія автоматично перетворюється на процес, тобто стає недоконаною. Якщо результат уже є, це минулий час («я прочитав»). Якщо результату ще немає, але він очікується, це майбутній час («я прочитаю»).

> *In the Ukrainian language, imperfective verbs have all three tenses: past, present, and future. You can say "I was reading" yesterday, "I am reading" now, and "I will be reading" tomorrow. In contrast, perfective verbs have only two tenses: past and future. They denote the result of an action, and a result is always a specific point on the timeline. As soon as you find yourself inside this point, the action automatically turns into a process, meaning it becomes imperfective. If the result already exists, it is the past tense ("I have read"). If the result does not exist yet, but is expected, it is the future tense ("I will read").*

This means that a perfective verb simply cannot exist in the present tense. The present tense describes what is happening right now, in this exact moment. A result cannot happen "right now" without immediately becoming a continuous process. Therefore, perfective verbs like **написати** or **зробити** are strictly locked out of the present tense.

This logical rule leads us directly into one of the most common traps for learners: the false present tense. Because the simple future form of a perfective verb looks exactly like a present tense conjugation, learners often use it by mistake to describe what they are doing right now. This can lead to significant misunderstandings in everyday conversations.

Уявіть ситуацію: ви сидите в кафе і читаєте дуже цікаву статтю. Вам телефонує друг і запитує, що ви робите. Якщо ви відповісте «я прочитаю статтю», співрозмовник почує це як обіцянку завершити дію пізніше. Це звучить так, ніби ви взагалі не відповідаєте на запитання про поточний момент. Щоб правильно описати вашу поточну дію, ви повинні завжди використовувати дієслово недоконаного виду в теперішньому часі: «я читаю статтю».

Remember that if a verb has a perfective prefix, such as the prefix in **прочитаю** (I will read) or **зроблю** (I will do), it automatically throws the action into the future. It can never mean that you are doing it right now, no matter how much the conjugation endings look like the present tense. You must always switch to an imperfective verb to talk about your current actions.

Understanding how aspect and tense work together is crucial for storytelling and planning. In any narrative, whether you are talking about yesterday or tomorrow, the imperfective aspect sets the scene. It provides the background, the ongoing states, and the continuous processes. The perfective aspect, on the other hand, introduces the foreground events. These are the completed actions that break the status quo and move the story forward. We can apply this exact same logic to our future plans.

Коли ми плануємо майбутні події, ми часто комбінуємо обидва види дієслова, щоб створити чітку картину. Недоконаний вид створює фон або загальний контекст для нашої історії. Наприклад, ви можете сказати: «Завтра ввечері я буду чекати тебе біля кінотеатру». Це ваш тривалий процес, ваш фоновий стан. Далі ви додаєте доконаний вид, щоб показати конкретну подію, яка змінить цей стан: «Коли ти прийдеш, я куплю нам квитки». Ваш процес очікування переривається новими результативними діями: прибуттям друга та купівлею квитків.

:::info
**Grammar box**
In complex sentences describing the future, imperfective verbs often describe the continuous condition (the "while" or "background"), and perfective verbs describe the sudden interruption or sequential steps (the "when" and "then").
:::

Finally, we must address a very strong linguistic habit that comes from English: the continuous future. In English, you frequently use the present continuous tense to talk about fixed future plans, such as saying that you are going to Berlin tomorrow or that you are meeting a friend at five o'clock. This often tempts learners to use the Ukrainian present tense to express their future intentions, which can cause confusion in conversation.

Хоча в українській розмовній мові іноді можна почути теперішній час для дуже близьких і гарантованих планів («завтра я їду до моря»), це швидше виняток. Зазвичай українці віддають перевагу саме формам майбутнього часу, коли говорять про завтрашній день або наступний тиждень. Якщо ви маєте квитки до Берліна, набагато природніше використовувати форми майбутнього часу. Ви можете сказати «завтра я поїду до Берліна» або «завтра я буду їхати до Берліна». Перший варіант підкреслює результат, а другий варіант робить акцент на самому процесі подорожі. Використання правильного майбутнього часу замість теперішнього робить ваше мовлення набагато чіткішим та зрозумілішим для носіїв мови. Тому завжди намагайтеся уникати прямого перекладу англійських граматичних звичок.

<!-- INJECT_ACTIVITY: error-correction-aspect-tense -->

## Дієвідмінювання у майбутньому часі

Let us examine how these three distinct future structures operate side-by-side when we use verbs built on the exact same core root. The Ukrainian verb for "to carry" or "to wear" is the imperfective **носити**, while its perfective partner, which typically means "to bring", is **принести**. When you need to communicate your intentions, these aspect partners provide you with powerful tools. The structure you choose completely alters the listener's expectations regarding the timeline and the final outcome of your action.

Якщо ви обіцяєте доставити річ один раз і досягти результату, ви обираєте просту форму доконаного виду. Ви кажете: «Я принесу тобі цю книгу завтра». Дія буде повністю завершена. Якщо ж ви хочете описати тривалий процес, наприклад, регулярне носіння теплого светра, вам обов'язково знадобляться форми недоконаного виду.

For that ongoing process, you have two completely interchangeable options. You can use the elegant synthetic structure by saying **я носитиму цей светр щодня**, or you can opt for the straightforward analytic structure by saying **я буду носити цей светр щодня**. Both sentences mean "I will be wearing this sweater every day." The real boundary in the language is never between the two imperfective forms, but rather between both of them and the perfective **принесу**, which immediately shifts the narrative to a finalized achievement.

When you conjugate verbs in the simple perfective future, familiar spelling changes occur. Because this form uses the exact same personal endings as the present tense, all the consonant alternations you learned previously apply here. Creating the perfective future is often just a matter of adding a prefix to a base you already know.

У теперішньому часі деякі приголосні звуки в корені слова змінюються. Дієслово «сидіти» перетворюється на «я сиджу», а «летіти» отримує форму «я лечу». Ці самі фонетичні правила ідеально працюють і для простої форми майбутнього часу. Коли ви додаєте префікс, щоб зробити дієслово доконаним, звук змінюється за знайомим вам зразком.

:::info
**Grammar box**
The consonant alternations from the first and second conjugations carry over perfectly into the simple future. If the base verb alters its stem consonant for the "I" form in the present tense, the prefixed perfective verb will do the exact same thing in the future tense.
:::

For instance, if you take the imperfective verb **просити** (to ask) and make it perfective by adding a prefix to form **запросити** (to invite), the consonant alternation remains identical. You say **я запрошу** for the first person singular, but for the second person you revert to the base consonant and say **ти запросиш**. The transition to the perfective future is completely seamless.

Another important detail to observe is how the reflexive particle behaves across the three different future forms. Reflexive verbs, which end in **-ся** or **-сь**, follow strict placement rules depending on whether you are using a simple, synthetic, or analytic future structure. The simple perfective future acts exactly like the present tense, so the reflexive particle simply attaches to the very end of the conjugated verb. You form the word **повернуся** (I will return) by adding the particle directly after the personal ending.

Складна форма майбутнього часу недоконаного виду працює за подібним принципом. Коли ви берете інфінітив «повертатися» і додаєте суфікс та особове закінчення, зворотна частка повинна відступити в самий кінець цього нового слова. У результаті ви отримуєте форму «я повертатимуся». Незалежно від довжини дієслова, частка завжди стоїть на фінальній позиції.

The analytic future form requires a completely different approach because it consists of two separate words. When you say **буду повертатися** (I will be returning), the reflexive particle stays firmly attached to the infinitive. A common mistake among learners is trying to attach the particle to the auxiliary verb **бути**, which sounds highly unnatural. The reflexive particle never moves between the words in the analytic construction; it always belongs to the main verb.

To see how these concepts naturally weave together in professional communication, imagine drafting a brief business email to your colleagues. You need to outline both the scheduled activities and the specific goals you intend to achieve.

Шановні колеги! Завтра вранці ми проведемо важливу зустріч нашої команди. Ми будемо обговорювати новий проект та аналізувати поточні ризики протягом двох годин. Я дуже сподіваюся, що після нашої плідної дискусії ми знайдемо правильне рішення.

> *Dear colleagues! Tomorrow morning we will hold an important meeting of our team. We will be discussing the new project and analyzing current risks for two hours. I really hope that after our fruitful discussion we will find the right solution.*

Notice how the email strategically combines the aspects to set clear expectations. The perfective verbs **проведемо** and **знайдемо** establish the concrete milestones that must be reached by the end of the meeting. In contrast, the analytic imperfective construction **будемо обговорювати** highlights the dedicated time and continuous effort that the team will spend working through the details. By mixing the aspects appropriately, you create a dynamic and highly professional text.

<!-- INJECT_ACTIVITY: free-write-future-plans -->

## Підсумок: вид і майбутнє у дії

Choosing the correct часова форма (tense form) for the future in Ukrainian might seem complex at first, but it all comes down to a simple decision tree based on your intention. When you want to talk about the future, you must first ask yourself: "Do I need to express a completed result or an ongoing process?" If your goal is to highlight a completed action, a specific result, or a one-time event, you must use the perfective aspect. This leads you directly to the simple future form, or **проста форма**. Remember the golden rule: the perfective future looks exactly like the present tense conjugation, but because perfective verbs cannot happen in the "now," it always feels like and represents the future. On the other hand, if your goal is to describe a process, a repeated action, or a continuous state, you must choose the imperfective aspect. Once you are in the imperfective branch of the tree, you have another choice: do you want to sound standard and neutral, or do you want to add a touch of poetic elegance? For a standard, everyday approach, use the analytic future, or **складена форма**, which simply pairs the auxiliary verb with your infinitive. For a more sophisticated and uniquely Ukrainian sound, opt for the synthetic future, or **складна форма**, by attaching the special suffixes directly to the infinitive stem.

:::note
**Quick tip**
The most common mistake learners make is trying to combine the auxiliary verb **бути** with a perfective verb. Always remember that **буду** only ever pairs with the imperfective infinitive.
:::

Завершуючи цю тему, варто перевірити своє розуміння ключових правил. Спробуйте відповісти на кілька запитань. По-перше, які три форми майбутнього часу є в українській мові? Ви маєте згадати просту, складну та складену форми. По-друге, поміркуйте, чому дієслова доконаного виду не мають теперішнього часу. Відповідь криється в самій природі результату: бо результат не може тривати в момент мовлення. По-третє, як утворити складну форму від дієслова «читати»? Правильна відповідь — «читатиму». І нарешті, яке допоміжне дієслово потрібне для аналітичної форми? Звісно, це дієслово «бути». Опанування майбутнього часу — це насамперед уміння ставити правильне питання до дії. Якщо ви чітко знаєте, чи хочете ви просто «робити» щось, чи остаточно це «зробити», правильна граматична форма з'явиться природно.

> *Wrapping up this topic, it is worth checking your understanding of the key rules. Try to answer a few questions. First, what are the three forms of the future tense in the Ukrainian language? You should recall the simple, synthetic, and analytic forms. Second, consider why verbs of the perfective aspect do not have a present tense. The answer lies in the very nature of a result: because a result cannot last at the moment of speech. Third, how do you form the synthetic form from the verb "to read"? The correct answer is "читатиму" (I will read). And finally, what auxiliary verb is needed for the analytic form? Of course, it is the verb "to be". Mastering the future tense is primarily about the ability to ask the right question about the action. If you clearly know whether you want to simply "do" something or finally "get it done," the correct grammatical form will appear naturally.*

**Preview of next module: Людина і стосунки (M06)**
In the next module, we will describe people and relationships, applying the future tense in context: «Я познайомлю тебе з моєю подругою» (I will introduce you to my friend), «Ми будемо зустрічатися щотижня» (We will be meeting every week).
</generated_module_content>

**PIPELINE NOTE — Word count: 5693 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 4000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 760 words | Not found: 14 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Авраменко — NOT IN VESUM
  ✗ Берліна — NOT IN VESUM
  ✗ Литвінова — NOT IN VESUM
  ✗ имати — NOT IN VESUM
  ✗ иму — NOT IN VESUM
  ✗ малютиму — NOT IN VESUM
  ✗ небудь — NOT IN VESUM
  ✗ сказаю — NOT IN VESUM
  ✗ тиме — NOT IN VESUM
  ✗ тимемо — NOT IN VESUM
  ✗ тимете — NOT IN VESUM
  ✗ тимеш — NOT IN VESUM
  ✗ тиму — NOT IN VESUM
  ✗ тимуть — NOT IN VESUM

All 760 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
