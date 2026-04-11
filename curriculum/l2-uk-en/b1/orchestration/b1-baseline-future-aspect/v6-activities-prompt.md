<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/b1-baseline-future-aspect.yaml` file for module **2: Майбутній час і вид дієслова** (b1).

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

- `<!-- INJECT_ACTIVITY: quiz-aspect-identification -->`
- `<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->`
- `<!-- INJECT_ACTIVITY: group-sort-future-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-future-choice -->`
- `<!-- INJECT_ACTIVITY: error-correction-aspect-tense -->`
- `<!-- INJECT_ACTIVITY: free-write-future-plans -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Identify вид дієслова: доконаний чи недоконаний? Given verb forms in context,
    learner classifies aspect.'
  items: 8
  type: quiz
- focus: 'Match видові пари: connect imperfective verbs to their perfective partners
    (писати↔написати, говорити↔сказати, брати↔взяти).'
  items: 8
  type: match-up
- focus: Complete sentences with the correct future form (проста, складна, or складена)
    based on context clues about completion vs ongoing action.
  items: 8
  type: fill-in
- focus: 'Sort verb forms into three groups: проста / складна / складена форма майбутнього
    часу.'
  items: 10
  type: group-sort
- focus: Find and fix aspect/tense errors in Ukrainian sentences (e.g., using perfective
    as present, wrong future form choice).
  items: 6
  type: error-correction
- focus: Write 5-7 sentences about your plans for next week using all three future
    forms and both aspects.
  items: 6
  type: free-write


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- тривала дія (ongoing action — characteristic of imperfective)
- завершена дія (completed action — characteristic of perfective)
- допоміжне дієслово (auxiliary verb — бути in analytic future)
- суфікс (suffix — word-building element after the root)
- дійсний спосіб (indicative mood — states facts, has all three tenses)
- основа інфінітива (infinitive stem — base for building future forms)
- часова форма (tense form — specific conjugated form of a verb)
- повторювана дія (repeated action — characteristic of imperfective)
- наголос (stress — emphasized syllable, may shift in conjugation)
- чергування приголосних (consonant alternation — e.g., просити → прошу)
required:
- вид дієслова (verbal aspect — grammatical category of completion)
- доконаний вид (perfective aspect — completed, bounded action)
- недоконаний вид (imperfective aspect — ongoing, unbounded action)
- видова пара (aspect pair — two verbs differing only in aspect)
- майбутній час (future tense)
- 'проста форма (simple form — perfective future: напишу)'
- 'складна форма (synthetic/compound form — imperfective future: писатиму)'
- 'складена форма (analytic form — imperfective future: буду писати)'
- інфінітив (infinitive — base verb form ending in -ти/-тися)
- дієвідміна (verb conjugation class — I or II)
- особове закінчення (personal ending — verb suffix marking person/number)
- дієвідмінювання (conjugation — changing verb form by person/number)
- 'двовидовий (biaspectual — verb that can be either aspect: атакувати)'
- одновидовий (single-aspect — verb existing in only one aspect)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що таке вид дієслова?

The concept of **вид дієслова** (verbal aspect) is often considered the very soul of the Ukrainian verb system. For learners coming from English, the fundamental mindset shift requires moving away from simply asking "when did it happen?" to a more nuanced question: "is the action in progress, or is it a completed result?" This binary nature of completion is the core of aspect. You are no longer just choosing a tense; you are choosing how to frame the action itself. The Ukrainian verb system forces you to declare your intention: are you describing an ongoing process, a repeated habit, or a finished, bounded event that produced a clear result?

Як зазначають автори шкільних підручників (зокрема О. Литвінова та О. Авраменко), в українській мові дієслова мають категорію виду. Недоконаний вид позначає тривалу, повторювану або незавершену дію. Натомість доконаний вид, від слова «доконати» (здійснити що-небудь до кінця), позначає завершену, обмежену в часі дію. Це означає, що ви фокусуєтеся на результаті, а не на процесі.

How do we practically distinguish between these two aspects? The most reliable method is the "Infinitive Question" test. In Ukrainian grammar, we identify the aspect by asking a specific question to the **інфінітив** (infinitive) form of the verb. If the verb answers the question «що робити?» (what to do?), it belongs to the **недоконаний вид** (imperfective aspect). If it answers the question «що зробити?» (what to get done?), it belongs to the **доконаний вид** (perfective aspect). Notice how the prefix «з-» in the question «що зробити?» immediately signals the search for a result or a completed state.

Щоб краще це зрозуміти, подивіться на типові видові пари. Більшість дієслів існує саме в таких парах, де одне слово описує процес, а інше — результат. Порівняйте ці пари: писати і написати, читати і прочитати, робити і зробити, малювати і намалювати, їсти і поїсти. Перше слово завжди відповідає на питання «що робити?», а друге — «що зробити?».

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

Let's look at how these aspects work together in a narrative, especially when talking about future plans. Think of your story as a stage play. Imperfective verbs create the background scenery, setting the stage with ongoing processes, like "the sun was shining" or "I was walking." Perfective verbs are the actors entering the stage to perform specific, completed actions that move the plot forward, like "I saw" or "the phone rang." A common mistake is forgetting aspect in a narrative. For example, you must mix aspects correctly to show process then completion: «Вчора я писав листа і написав його» (Yesterday I was writing a letter and I finished it). This dynamic applies perfectly to the future tense. You will often combine both aspects in a single sentence to show how a sudden event interrupts or follows an ongoing process.

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
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: b1-baseline-future-aspect
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

**Level: B1 (Module 2)**

**Instructions in Ukrainian.** All activity types appropriate.


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
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
