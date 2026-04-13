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

Окрім звичайних чергувань, існують також дієслова з особливими формами, які потрібно просто запам'ятати. Наприклад, дієслово «відповісти» має такі форми: я відповім, ти відповіси, він відповість, ми відповімо, ви відповісте, вони відповідять. Так само відмінюється дієслово «дати»: я дам, ти даси, він дасть, ми дамо, ви дасте, вони дадуть. Ці короткі слова дуже часто використовуються в щоденних розмовах, тому їх варто вивчити напам'ять.

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

<!-- INJECT_ACTIVITY: group-sort-future-forms --> [Group-sort: Categorize verb forms into Проста, Складна, and Складена groups, 10 items]
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
