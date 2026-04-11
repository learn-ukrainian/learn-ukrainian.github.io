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

The concept of **вид дієслова** (verbal aspect) is often considered the very soul of the Ukrainian verb system. For learners coming from English, the fundamental mindset shift requires moving away from simply asking "when did it happen?" to a more nuanced question: "is the action in progress, or is it a completed result?" This binary nature of completion is the core of aspect. You are no longer just choosing a tense; you are choosing how to frame the action itself. The Ukrainian verb system forces you to declare your intention: are you describing an ongoing process, a repeated habit, or a finished, bounded event that produced a clear result?

Як зазначають автори шкільних підручників (зокрема О. Литвінова та О. Авраменко), в українській мові дієслова мають категорію виду. Недоконаний вид позначає тривалу, повторювану або незавершену дію. Натомість доконаний вид, від слова «доконати» (здійснити що-небудь до кінця), позначає завершену, обмежену в часі дію. Це означає, що ви фокусуєтеся на результаті, а не на процесі.

How do we practically distinguish between these two aspects? The most reliable method is the "Infinitive Question" test. In Ukrainian grammar, we identify the aspect by asking a specific question to the **інфінітив** (infinitive) form of the verb. If the verb answers the question «що робити?» (what to do?), it belongs to the **недоконаний вид** (imperfective aspect). If it answers the question «що зробити?» (what to get done?), it belongs to the **доконаний вид** (perfective aspect). Notice how the prefix «з-» in the question «що зробити?» immediately signals the search for a result or a completed state.

Щоб краще це зрозуміти, подивіться на типові видові пари. Більшість дієслів існують саме в таких парах, де одне слово описує процес, а інше — результат. Порівняйте ці пари: писати і написати, читати і прочитати, робити і зробити, малювати і намалювати, їсти і поїсти. Перше слово завжди відповідає на питання «що робити?», а друге — «що зробити?».

Now let us look at the formation patterns of these **видові пари** (aspect pairs). While many verbs exist in these pairs, they do not all form their perfective partners in the exact same way. The most common pattern is prefixation, where you add a prefix like **на-**, **про-**, or **з-** to the imperfective base. For example, the verb «писати» becomes «написати», and «робити» becomes «зробити». This is the simplest way to transform an action into a result. Another method is changing the suffix inside the word, such as alternating «-а-» and «-и-». Thus, «відповідати» becomes «відповісти», and «записувати» turns into «записати». Finally, the most distinct method is suppletion, where words use entirely different roots to express the same action in different aspects, like «говорити» and «сказати», or «брати» and «взяти».

Although the vast majority of Ukrainian verbs exist in neat aspectual pairs, there are two special categories of "lonely" verbs that break this rule. First, we have **двовидові дієслова** (biaspectual verbs). These are verbs that have only one form, and their aspect is determined entirely by the context of the sentence. Words like «атакувати» (to attack) or «телеграфувати» (to telegraph) can act as either imperfective or perfective depending on how you use them. On the other end of the spectrum are **одновидові дієслова** (single-aspect verbs). These verbs simply do not have a partner. For instance, «сподіватися» (to hope) exists only in the imperfective aspect because hoping is inherently an ongoing state. Conversely, «схаменутися» (to suddenly come to one's senses) exists only in the perfective aspect because it describes an instantaneous, irreversible realization.

:::note
**Quick tip**
When learning new verbs, always memorize them as an aspectual pair, such as **читати / прочитати**. It will save you a massive amount of time and confusion when forming future and past tenses later.
:::

Let us observe how this theoretical concept dictates real meaning in a practical scenario. Read the following narrative snippet about a student's Saturday plans in Kharkiv. Pay close attention to how the choice of aspect completely changes the nature of the scheduled activities.

У суботу вранці студент Харківського університету буде читати новий підручник з історії. Він дуже любить цей процес. Але до обіду він обов'язково прочитає третій розділ, бо в понеділок буде важливий семінар. Ввечері він буде малювати афішу для благодійного концерту і сподівається, що намалює її до півночі.

> *On Saturday morning, a student of Kharkiv University will be reading a new history textbook. He really loves this process. But by noon he will definitely read (finish reading) the third chapter, because there is an important seminar on Monday. In the evening he will be drawing a poster for a charity concert and hopes that he will draw (finish drawing) it by midnight.*

Here, the phrase «буде читати» indicates the ongoing process of reading, while «прочитає» emphasizes the completed result of finishing the chapter. Similarly, «буде малювати» is the creative process, but «намалює» is the final product ready for the concert. This precision is the true power of the Ukrainian aspect system.

<!-- INJECT_ACTIVITY: quiz-aspect-identification -->
<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->

## Проста форма майбутнього часу

The Ukrainian language has three distinct forms to express the future tense. The first and most critical one is the **проста форма** (simple form). This form is entirely unique because it belongs exclusively to verbs of the **доконаний вид** (perfective aspect). To understand how it works, we must revisit the core definition of the perfective aspect: it describes an action that is fully completed, a finalized result. Because an action cannot be completely finished right "now" in the present moment—it is either already done or will be done—perfective verbs simply do not possess a present tense. Therefore, when you take a perfective verb and conjugate it using standard present-tense endings, it automatically projects the completed action into the future. It is a brilliant mathematical logic: a completed result plus present conjugation equals a future achievement.

Українська мова використовує просту форму майбутнього часу, щоб говорити про конкретні результати, які ми отримаємо згодом. Коли ви берете дієслово доконаного виду і додаєте до нього звичайні особові закінчення, ви автоматично створюєте майбутній час. Це відбувається тому, що завершена дія фізично не може відбуватися просто зараз.

> *The Ukrainian language uses the simple form of the future tense to talk about concrete results that we will obtain later. When you take a perfective verb and add regular personal endings to it, you automatically create the future tense. This happens because a completed action physically cannot happen right now.*

The conjugation mechanics for the simple future are identical to the present tense you mastered in the A2 level. You must determine whether the verb belongs to the first conjugation (typically taking **-е-** or **-є-**) or the second conjugation (taking **-и-** or **-ї-**). Let us look at the first conjugation using the perfective verb «написати» (to write/finish writing). The forms are: **я напишу**, **ти напишеш**, **він напише**, **ми напишемо**, **ви напишете**, and **вони напишуть**. Now, consider the second conjugation with the perfective verb «зробити» (to do/finish doing). The forms are: **я зроблю**, **ти зробиш**, **він зробить**, **ми зробимо**, **ви зробите**, and **вони зроблять**. The only difference between these forms and the present tense is the presence of the perfective prefix, such as **на-** or **з-**, which shifts the entire time signature from an ongoing present process to a future completion.

:::info
**Grammar box**
The key insight here is that the perfective future looks exactly like present tense conjugation, but because it uses a perfective verb, it automatically means the future. Compare «я пишу» (I am writing) with «я напишу» (I will finish writing).
:::

When should you use this simple future form? It is your primary tool for expressing results and promises. You use it when you want to state a one-time completed action, confirm that a specific goal will be reached, or make a firm commitment. For instance, if you promise to be somewhere, you say «Я прийду вчасно» (I will arrive on time). If you are confident about a sports game, you declare «Ми виграємо матч» (We will win the match). It is crucial to contrast this with the English phrase "I will do it." In English, "will" plus a verb can mean either an ongoing process or a finished result, depending entirely on the context. In Ukrainian, if you mean "I will get it done," you must use the simple future form of the perfective aspect, like «Я зроблю це».

Ми використовуємо цю форму, коли даємо обіцянки або плануємо досягти конкретної мети. Вона ідеально підходить для ситуацій, де важливий фінальний результат, а не сам процес. Наприклад, студент каже: «Я прочитаю цей підручник до п'ятниці». Це означає, що в п'ятницю книга буде повністю прочитана.

> *We use this form when we make promises or plan to achieve a specific goal. It is perfectly suited for situations where the final result is important, and not the process itself. For example, a student says: "I will read (finish reading) this textbook by Friday." This means that on Friday the book will be completely read.*

Finally, because the simple future uses present-tense conjugation rules, it also inherits all the consonant alternations that occur in the present tense. For example, the verb «сказати» changes its stem consonant: it becomes **я скажу**, not *сказаю*. The verb «попросити» undergoes a similar mutation to become **я попрошу**. Two particularly important verbs have slightly irregular forms: «відповісти» (to answer) and «дати» (to give). For «відповісти», the forms are **я відповім** and **ти відповіси**. For «дати», they are **я дам** and **ти даси**. Though they look strange, these specific forms are incredibly common when making plans and commitments.

## Складна (синтетична) форма майбутнього часу

In Ukrainian, there is a unique, one-word future tense specifically designed for imperfective verbs. This is called the synthetic or compound future (складна форма). Unlike the simple future, which is built exclusively on perfective verbs to show completion and results, the synthetic future describes ongoing, repetitive, or incomplete actions. This specific grammatical structure is a distinctive and highly celebrated feature of the Ukrainian language, setting it completely apart from its linguistic neighbors. If you want to sound incredibly natural and authentic in your everyday conversations, mastering this specific form is a wonderful step forward.

Історично ця форма утворилася від злиття інфінітива дієслова та стародавніх форм допоміжного дієслова «мати». Наші предки говорили «писати иму», що буквально означало «я маю писати». З часом, у процесі природного розвитку мови, ці два слова міцно об'єдналися в одне, і виникла сучасна форма «писатиму». Це дуже елегантне граматичне рішення, яке дозволяє висловити тривалу дію в майбутньому лише одним словом.

> *Historically, this form evolved from the merging of a verb's infinitive and the ancient forms of the auxiliary verb "to have." Our ancestors used to say "писати иму", which literally meant "I have to write." Over time, in the process of natural language development, these two words firmly merged into one, and the modern form "писатиму" emerged. This is a very elegant grammatical solution that allows you to express an ongoing action in the future with just one word.*

To build the synthetic future tense, you always start with the full, unaltered infinitive of an imperfective verb. You absolutely do not drop the **-ти** or **-тися** ending. Instead, you attach a specific set of personal suffixes directly to the end of that infinitive. These suffixes are **-му**, **-меш**, **-ме**, **-мемо**, **-мете**, and **-муть**. Because you are adding these endings to the already complete infinitive, the resulting words can sometimes look quite long, but they are incredibly regular and entirely predictable. Let us look at exactly how this works with two very common verbs: «працювати» (to work) and «жити» (to live).

Для дієслова «працювати» формуються такі слова: я працюватиму, ти працюватимеш, він працюватиме, ми працюватимемо, ви працюватимете, вони працюватимуть. Зверніть увагу на те, що вся основа слова разом з інфінітивним закінченням залишається незмінною. Точно так само відмінюється дієслово «жити»: я житиму, ти житимеш, вона житиме, ми житимемо, ви житимете, вони житимуть. Ця неймовірна стабільність робить складну форму майбутнього часу дуже легкою для вивчення та безпомилкового використання на практиці.

:::info
**Grammar box**
The letter **-м-** is the critical visual indicator of the synthetic future. Whenever you see a verb ending in **-тиму**, **-тимеш**, or **-тиме**, you know immediately that it describes an ongoing or repeated action in the future.
:::

Grammatically speaking, the synthetic future tense and the analytic future tense, which we will cover in the next section, are entirely synonymous. They both mean the exact same thing: an imperfective, ongoing action taking place in the future. However, there is a very important and subtle stylistic difference between the two. The synthetic form often sounds slightly more literary, poetic, or elevated to native speakers. It is frequently used in high-quality literature, poetry, and formal public speeches to give the language a beautiful, melodic rhythm and a deeply traditional feel.

Відомі українські письменники та поети завжди дуже любили використовувати цю форму у своїх класичних творах. Наприклад, видатний поет Володимир Сосюра часто обирав саме складну форму, щоб надати своїм віршам особливої плавності та ліричності. Для студентів рівня B1 використання складної форми в повсякденних розмовах — це чудовий спосіб збагатити своє мовлення. Коли ви кажете «я читатиму» замість «я буду читати», ви демонструєте глибоке розуміння мелодики української мови.

One of the greatest practical advantages of the synthetic future tense is its absolute grammatical stability. Unlike the present tense or the perfective simple future, where you constantly have to watch out for unexpected consonant shifts and changing vowels, the synthetic future never changes the original verb stem. If you simply know the infinitive form of the verb, you can construct the future tense flawlessly every single time without having to memorize complex irregularities.

Наприклад, у теперішньому часі дієслово «малювати» повністю змінює свою основу і перетворюється на форму «я малюю». Але у складній формі майбутнього часу ми просто беремо оригінальний інфінітив і додаємо відповідне закінчення: «я малюватиму». Жодних несподіваних змін приголосних чи голосних звуків тут не відбувається. Так само поширене дієслово «ходити» в теперішньому часі має нестандартну форму «я ходжу», але в майбутньому це буде просте і зрозуміле «я ходитиму».

This wonderful stability makes the synthetic future a highly reliable tool when you are speaking quickly and do not have time to process complex grammar rules. However, you must always remember to carefully contrast this ongoing, imperfective form with the perfective simple future. If you say the phrase «я ходитиму до школи», meaning you will be going to school, you are explicitly describing a repeated, habitual action over a period of time. If you want to confidently state that you will arrive at a specific destination once and achieve a result, you must switch aspects and use the perfective simple future, such as «я прийду».

## Складена (аналітична) форма майбутнього часу

The third and final way to express the future tense in Ukrainian is the analytic, or compound, form. This form is incredibly popular and very easy to master. When you are speaking quickly and need to express a future plan, this structure will often be the first one that comes to your mind. 

Складена форма майбутнього часу використовується виключно з дієсловами недоконаного виду. Вона завжди позначає тривалу або повторювану дію, яка відбуватиметься в майбутньому. Для її утворення вам знадобляться лише два елементи: допоміжне дієслово «бути» у відповідній формі та незмінний інфінітив основного дієслова.

> *The compound future tense is used exclusively with verbs of the imperfective aspect. It always denotes a continuous or repeated action that will take place in the future. To form it, you only need two elements: the auxiliary verb "to be" in the appropriate form and the unchanged infinitive of the main verb.*

This two-part construction is highly reliable. The main semantic verb—the one carrying the actual meaning of the action—remains locked in its dictionary infinitive form. You never have to worry about consonant alternations, shifting stress marks, or complex endings for the main action. The only word that changes to reflect the person and number is the short auxiliary verb. This grammatical division of labor makes the analytic future the ultimate safe harbor for language learners. If you know how to conjugate just one verb—«бути»—you instantly know how to express any ongoing future action.

The auxiliary verb «бути» is unique in the Ukrainian language. It acts as an irregular future verb that does not follow standard aspect rules when used in this specific grammatical role. 

Дієслово «бути» не має доконаного відповідника для утворення майбутнього часу, тому воно самостійно бере на себе функцію граматичного маркера. Давайте подивимося на його відмінювання.

> *The verb "to be" does not have a perfective counterpart for forming the future tense, so it independently takes on the role of a grammatical marker. Let's look at its conjugation.*

The conjugation table is beautifully regular across the different persons. You will notice that it closely resembles the present tense endings you already know, just applied to a new base:

*   я буду
*   ти будеш
*   він, вона, воно буде
*   ми будемо
*   ви будете
*   вони будуть

To create the analytic future tense, you simply place the appropriate form of «бути» directly before your chosen imperfective infinitive. For instance, if you want to say "I will be reading," you combine «я буду» with «читати», resulting in «я буду читати». If the subject is "we," it becomes «ми будемо читати». The infinitive «читати» never drops a single letter.

Let's see how all three future forms work together in a real-life context. Imagine a planning committee at a university in Kharkiv. The characters are organizing a charity concert and must carefully choose their aspects to distinguish between long processes and concrete results.

> — **Голова комітету:** Ми будемо збирати кошти цілий тиждень. *(We will be collecting funds all week.)*
> — **Волонтер 1:** А коли ми точно скажемо студентам про концерт? *(And when will we tell the students exactly about the concert?)*
> — **Голова комітету:** Ми оголосимо дату завтра вранці. *(We will announce the date tomorrow morning.)*
> — **Волонтер 2:** Добре, тоді я напишу красиву афішу сьогодні ввечері. *(Good, then I will write a beautiful poster tonight.)*
> — **Волонтер 1:** А я буду допомагати тобі з дизайном. *(And I will be helping you with the design.)*

Notice the clear division of labor. The committee head uses «будемо збирати» because collecting funds is an ongoing process that will take an entire week. However, announcing the date («оголосимо») and creating the final poster («напишу») are single, completed actions that require the perfective simple future.

Складена форма майбутнього часу є надзвичайно поширеною в розмовній українській мові. Вона особливо часто звучить у західних діалектах, хоча є нормативною для всієї території України. Багато людей обирають саме її під час швидкого спілкування, оскільки вона не вимагає складних граматичних трансформацій у голові.

You might wonder how to choose between the analytic form («буду працювати») and the synthetic form («працюватиму») since both describe an imperfective future action. The truth is that they are completely interchangeable in meaning. The analytic form is highly frequent, neutral, and universally understood. It feels slightly more casual and is often the default choice in spontaneous dialogue. The synthetic form carries a slightly more elegant, literary, and poetic tone. Both forms are excellent tools for your vocabulary, and you will hear native speakers switch between them constantly without even thinking about it. Using the analytic form gives your brain a brief resting period because you only need to conjugate the auxiliary verb, allowing you to focus on the vocabulary itself.

:::info
**Grammar box**
Never mix the two systems! A very common mistake is trying to combine the auxiliary verb «бути» with a perfective verb. The verb «бути» strictly requires an imperfective infinitive. If you want a result, drop «бути» entirely and just use the simple perfective future.
:::

Коли ви пишете офіційний лист або виступаєте з промовою, ви можете обрати синтетичну форму для більшої милозвучності. Але коли ви просто розмовляєте з друзями за кавою, аналітична форма «буду робити» звучатиме природно. Головне правило — ніколи не боятися використовувати обидві форми. Вони роблять вашу українську мову багатою та виразною.

:::tip
**Did you know?**
While English relies heavily on the Present Continuous ("I am going tomorrow") for immediate future plans, Ukrainian strongly prefers using actual future tense forms. It is much more natural to say «я буду йти» or «я піду» than to use a present-tense verb for a future event.
:::

<!-- INJECT_ACTIVITY: group-sort-future-forms -->
<!-- INJECT_ACTIVITY: fill-in-future-choice -->

## Вид і час — як вони працюють разом

The relationship between aspect and tense in Ukrainian is highly logical and almost mathematical. Once you understand this matrix, you will never struggle with tense formation again. The core rule is delightfully simple: imperfective verbs have three tenses, while perfective verbs have only two. An imperfective verb can exist in the past («я читав»), the present («я читаю»), or the future («я буду читати» or «я читатиму»). A perfective verb, however, only exists in the past («я прочитав») and the future («я прочитаю»).

Дієслова доконаного виду принципово не можуть мати форми теперішнього часу. Це логічно випливає з самої природи доконаного виду, який позначає фінальний результат, межу або повністю завершену дію. Теперішній час — це завжди динамічний процес, який відбувається саме зараз, у момент мовлення. Ви просто не можете перебувати всередині завершеного результату в дану секунду.

> *Perfective verbs fundamentally cannot have a present tense form. This logically follows from the very nature of the perfective aspect, which denotes a final result, a boundary, or a completely finished action. The present tense is always a dynamic process happening right now, at the moment of speech. You simply cannot be inside a completed result at this given second.*

As soon as a result is achieved, it instantly belongs to the past. While you are still actively working towards achieving that result, it remains entirely in the future. The present moment is a flowing stream, and only imperfective verbs can swim in it. Therefore, if you need to describe anything that is happening right now, you must use an imperfective verb. This is a strict rule with absolutely no exceptions, and internalizing it is a major milestone for mastering Ukrainian.

This brings us to a very common trap for learners. Because the perfective future («я прочитаю», «я зроблю») is formed using the exact same endings as the imperfective present («я читаю», «я роблю»), it is incredibly tempting to use perfective verbs to talk about the present. Many learners try to say something like "Я зараз прочитаю книгу" to mean "I am reading a book right now." However, to a Ukrainian speaker, this sounds like a contradiction. Because «прочитаю» is perfective, it automatically projects the action into the future. The listener hears: "Right now, I will finish reading a book later."

Коли ви кажете «я прочитаю», носій української мови чує обіцянку на майбутнє. Це означає, що ви візьмете книгу пізніше і обов'язково дочитаєте її до кінця. Якщо ж ви сидите з книгою в руках прямо зараз, єдиний правильний варіант — сказати «я читаю».

:::info
**Grammar box**
Always look at the prefix or the aspect pair. If the verb is perfective (like **написати** or **зробити**), its simplest conjugation (**напишу**, **зроблю**) is ALWAYS the future tense. It can never be present.
:::

Let's look at how these aspects work together in a narrative, especially when talking about future plans. Think of your story as a stage play. Imperfective verbs create the background scenery, setting the stage with ongoing processes, like "the sun was shining" or "I was walking." Perfective verbs are the actors entering the stage to perform specific, completed actions that move the plot forward, like "I saw" or "the phone rang." This dynamic applies perfectly to the future tense. You will often combine both aspects in a single sentence to show how a sudden event interrupts or follows an ongoing process.

Уявіть таку ситуацію: завтра я буду чекати тебе біля кінотеатру, і коли ти приїдеш, я куплю нам квитки. У цьому реченні процес очікування створює тло. Це типовий недоконаний вид, який показує тривалу дію. А слова «приїдеш» та «куплю» — це доконаний вид, який позначає конкретні події на цьому тлі.

The verbs «приїдеш» (you will arrive) and «куплю» (I will buy) represent the concrete events that will happen on that stage. By mixing «буду чекати» with «приїдеш», you create a rich, realistic picture of tomorrow's timeline, smoothly blending ongoing states with definitive actions.

Let's analyze a short retelling of a Ukrainian folk tale to see these rules in a broader narrative. Уявіть, що ми розповідаємо казку про майбутнє: У темному лісі буде жити (недок., ongoing) хитрий лис. Кожного дня він шукатиме (недок., repeated) здобич. Але одного разу він обов'язково зустріне (док., completion) чарівного птаха. Лис захоче (док., completion) його спіймати, але птах швидко полетить (док., completion) у небо. The ongoing states (буде жити, шукатиме) build the world, while the perfective verbs (зустріне, захоче, полетить) drive the plot to its specific results.

A final hurdle for English speakers is the tendency to use the present tense for future plans. In English, it is perfectly natural to use the Present Continuous to say, "I am going to Berlin tomorrow" or "We are having dinner tonight." This structure does not transfer well to Ukrainian. While you might occasionally hear a present-tense verb used for very immediate and certain plans, especially with verbs of motion, it is not the standard way to express the future.

В українській мові ми віддаємо перевагу справжнім формам майбутнього часу. Замість того, щоб використовувати теперішній час для опису планів, ми скажемо «завтра я поїду до Берліна» або «завтра я буду їхати до Берліна». Це звучить набагато природніше.

Relying on the present tense for future events will make your Ukrainian sound unnatural and confusing. Embrace the three future forms you have learned. Whether you need to emphasize a completed goal with the perfective aspect or an ongoing process with the imperfective aspect, using the dedicated future tense ensures your communication is clear and authentically Ukrainian.

:::tip
**Did you know?**
English uses words like "will" or "going to" to force verbs into the future. Ukrainian builds the future directly into the verb's meaning, either through its perfective nature or by combining it with the auxiliary verb.
:::

<!-- INJECT_ACTIVITY: error-correction-aspect-tense -->

## Дієвідмінювання у майбутньому часі

Now that you understand the mechanics of the three future forms, let us put them side-by-side. Comparing verbs that share the same root is the most effective way to see how aspect and tense interact. The root dictates the core meaning, but the grammatical form tells the listener exactly how that action will unfold.

Давайте розглянемо дієслова з коренем «нес» або «нос». Якщо це разова, результативна дія, ми використовуємо доконаний вид: «я принесу каву». Якщо це тривалий процес, ми обираємо недоконаний вид. Ви можете сказати «я носитиму цей светр усю зиму» або «я буду носити цей светр усю зиму». Ці дві форми однакові за значенням.

Notice the distinct shift in meaning. The perfective verb **принести** (to bring) combined with its simple future form **принесу** (I will bring) guarantees a completed result. The imperfective verb **носити** (to wear) focuses entirely on the ongoing state. Whether you use the synthetic **носитиму** or the analytic **буду носити**, you describe an uninterrupted action without a specific endpoint.

You might remember that certain verbs undergo consonant alternations in the present tense. Because the perfective future uses the exact same conjugation patterns, these phonetic shifts apply here as well. If you have mastered the first and second conjugation patterns, forming the perfective future is simply a matter of adding a prefix.

Українська фонетика вимагає змін приголосних у першій особі однини для багатьох дієслів другої дієвідміни. Наприклад, від дієслова «сидіти» утворюється форма «я посиджу». Від дієслова «летіти» ми утворюємо форму «я полечу». Так само поводиться дієслово «запросити»: ви кажете «я запрошу тебе на свято», але «ти запросиш мене».

These alternations exist naturally to make the words fluid to pronounce. The shift usually affects only the **я** (I) form. Once you move to **ти** (you) or **ми** (we), the original consonant returns, as seen in the contrast between **попрошу** (I will ask) and **попросиш** (you will ask).

Reflexive verbs follow strict placement rules in the future tense. The particle **-ся** or **-сь** is permanently attached to the main verb, but its exact position depends entirely on which of the three future forms you are building.

У простій формі частка приєднується безпосередньо до кінця слова: «я повернуся додому». У складній формі вона також стоїть у самому кінці, після суфікса та закінчення: «я повертатимуся пізно». В аналітичній формі частка залишається разом з інфінітивом: «я буду повертатися». Частка ніколи не розриває дієслівну конструкцію.

:::info
**Grammar box**
When using the analytic future form (**буду** + infinitive) with a reflexive verb, the particle **-ся** must stay glued to the infinitive. It is incorrect to attach it to the auxiliary verb. You cannot say **я будуся повертати**. The only correct structure is **я буду повертатися**.
:::

To truly master the future tense, you must learn to weave these aspects naturally into connected speech. A professional setting, such as drafting a business email, provides a perfect backdrop for seeing how perfective results and imperfective processes work together.

Завтра ми проведемо важливу зустріч. Ми будемо обговорювати новий проєкт та його фінансування. Я сподіваюся, що ми знайдемо ефективне рішення. Після цього я обов'язково надішлю всім детальний звіт.

> *Tomorrow we will hold an important meeting. We will be discussing the new project and its financing. I hope that we will find an effective solution. After that, I will definitely send everyone a detailed report.*

In this short email, the perfective verbs **проведемо** (we will hold), **знайдемо** (we will find), and **надішлю** (I will send) act as definitive milestones. They are the concrete accomplishments the sender is promising to deliver. Meanwhile, the analytic imperfective form **будемо обговорювати** (we will be discussing) sets the ongoing agenda for the meeting itself. By mixing these forms purposefully, the email sounds authoritative and naturally Ukrainian.

:::tip
**Did you know?**
When making promises or setting deadlines, native speakers almost exclusively rely on the perfective future. Using the imperfective future in a business context can sometimes sound evasive, as if you plan to work on a task but cannot guarantee you will finish it!
:::

<!-- INJECT_ACTIVITY: free-write-future-plans -->

## Підсумок: вид і майбутнє у дії

Choosing the right future tense in Ukrainian can feel like a challenge, but it all comes down to a simple decision tree. The very first question you must ask yourself is: "Do I need a result, or am I describing a process?" If your goal is to emphasize a completed action or a specific guaranteed result, you must choose a perfective verb. Perfective verbs offer only one path to the future, which is the simple form. You build it by adding personal endings to the verb stem, creating words like **я напишу** or **ми подивимося**. It is crucial to remember that this perfective future form looks exactly like a present tense conjugation, but it always acts as the future because a finalized result cannot exist in the immediate present moment.

Якщо ж ви описуєте процес, тривалу дію або звичку в майбутньому, вам потрібне дієслово недоконаного виду. Тут у вас є два шляхи. Якщо ви хочете звучати стандартно і нейтрально, обирайте аналітичну складену форму з допоміжним дієсловом: **я буду працювати**. Якщо ж ви хочете надати своєму мовленню трохи більше елегантності, використовуйте синтетичну складну форму: **я працюватиму**. Обидва варіанти правильні, тому вибір залежить лише від вашого стилю в конкретній ситуації.

> *If you are describing a process, an ongoing action, or a habit in the future, you need an imperfective verb. Here you have two paths. If you want to sound standard and neutral, choose the analytic compound form with an auxiliary verb: **я буду працювати**. But if you want to give your speech a bit more elegance, use the synthetic compound form: **я працюватиму**. Both options are absolutely correct, so the choice depends entirely on your style in a specific situation.*

Now that you have explored the mechanics of aspect and time, it is time to verify your understanding. Take a moment to review these essential questions. You should be able to explain these rules clearly, as they form the foundation of everything you will learn in the upcoming modules.

Спробуйте самостійно відповісти на ці контрольні запитання. По-перше, які три форми майбутнього часу існують в українській мові? Це проста, складна та складена форми. По-друге, чому дієслова доконаного виду ніколи не мають теперішнього часу? Тому що завершений результат просто не може тривати в момент мовлення. По-третє, як правильно утворити складну форму від дієслова «читати»? Ви додаєте суфікс до інфінітива, щоб отримати слово «читатиму». І нарешті, яке допоміжне дієслово завжди потрібне для аналітичної форми? Це дієслово «бути».

To sum up, mastering the future tense in Ukrainian is fundamentally about mastering the "What to do?" question before you even start speaking. You must clearly envision whether your action is a journey or a destination. Once you make that choice between an imperfective process and a perfective result, the grammatical forms will naturally fall into place.

У наступному модулі «Людина і стосунки» (M06) ми будемо застосовувати майбутній час на практиці, описуючи людей та взаємини. Ви навчитеся будувати фрази на зразок «Я познайомлю тебе з моєю подругою» або «Ми будемо зустрічатися щотижня», поєднуючи нову лексику з точним відчуттям часу.

:::note
**Quick tip**
Whenever you hesitate about which future form to use, ask yourself the core question: «Що робити?» or «Що зробити?». If your answer starts with the prefix **з-** (meaning a result), immediately use the simple future form.
:::
</generated_module_content>

**PIPELINE NOTE — Word count: 5134 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 706 words | Not found: 17 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Авраменко — NOT IN VESUM
  ✗ Берліна — NOT IN VESUM
  ✗ Литвінова — NOT IN VESUM
  ✗ Сосюра — NOT IN VESUM
  ✗ будуся — NOT IN VESUM
  ✗ иму — NOT IN VESUM
  ✗ мемо — NOT IN VESUM
  ✗ меш — NOT IN VESUM
  ✗ небудь — NOT IN VESUM
  ✗ недок — NOT IN VESUM
  ✗ нес — NOT IN VESUM
  ✗ нос — NOT IN VESUM
  ✗ сказаю — NOT IN VESUM
  ✗ тиме — NOT IN VESUM
  ✗ тимеш — NOT IN VESUM
  ✗ тиму — NOT IN VESUM
  ✗ тися — NOT IN VESUM

All 706 other words are confirmed to exist in VESUM.

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
