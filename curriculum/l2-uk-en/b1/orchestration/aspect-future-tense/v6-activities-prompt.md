<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-future-tense.yaml` file for module **5: Вид у майбутньому часі** (b1).

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

- `<!-- INJECT_ACTIVITY: quiz-future-intuition -->`
- `<!-- INJECT_ACTIVITY: fill-in-future-forms -->`
- `<!-- INJECT_ACTIVITY: group-sort-constructions -->`
- `<!-- INJECT_ACTIVITY: match-up-situations -->`
- `<!-- INJECT_ACTIVITY: error-correction-future -->`
- `<!-- INJECT_ACTIVITY: open-writing-tomorrow-plan -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct future construction (складений, синтетичний, or простий
    доконаний) based on context and communicative intent
  items: 10
  type: quiz
- focus: Form the future tense of given verbs — identify the вид first, then select
    the appropriate construction
  items: 8
  type: fill-in
- focus: Sort future-tense forms into три конструкції and explain why each verb uses
    that construction
  items: 10
  type: group-sort
- focus: Find and correct impossible or unnatural future constructions (*буду написати,
    *прочитаю цілий день)
  items: 6
  type: error-correction
- focus: Match communicative situations (promise, plan, prediction) to the most natural
    future construction
  items: 8
  type: match-up
- focus: Write 'Мій план на завтра' mixing perfective and imperfective future — mark
    and justify each aspect choice
  items: 6
  type: open-writing


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

- pos: noun phrase
  translation: compound future tense (буду + infinitive)
  word: складений майбутній час
- pos: adj
  translation: synthetic — single-word form (-тиму)
  word: синтетичний
- pos: adj
  translation: simple — perfective future uses present-tense endings
  word: простий
- pos: noun:m
  translation: infinitive — base verb form ending in -ти
  word: інфінітив
- pos: noun:f
  translation: paradigm — full set of conjugated forms
  word: парадигма
- pos: noun phrase
  translation: personal ending (-у, -еш, -е, etc.)
  word: особове закінчення
- pos: verb:impf
  translation: to promise (impf — the act of promising)
  word: обіцяти
- pos: verb:pf
  translation: to promise (pf — a specific promise made)
  word: пообіцяти
- pos: verb:impf
  translation: to try, to make effort (impf)
  word: старатися
- pos: verb:pf
  translation: to make an effort (pf — with expected result)
  word: постаратися
- pos: verb:impf
  translation: to plan (impf — process of planning)
  word: планувати
- pos: verb:pf
  translation: to plan (pf — plan is set)
  word: запланувати
- pos: verb:pf
  translation: to book, to reserve (pf — booking completed)
  word: забронювати
- pos: verb:impf
  translation: to enjoy (impf — ongoing enjoyment)
  word: насолоджуватися
- pos: verb:pf
  translation: 'to finish (pf — result: done)'
  word: закінчити
- pos: verb:impf
  translation: to be finishing (impf — process of wrapping up)
  word: закінчувати
- pos: noun phrase
  translation: conversational style (where складений is common)
  word: розмовний стиль
- pos: noun phrase
  translation: written style (where синтетичний is common)
  word: писемний стиль
- pos: noun:n
  translation: obligation, commitment
  word: зобов'язання
- pos: noun:n
  translation: prediction, forecast
  word: передбачення


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Тест: яке майбутнє ви оберете?

When you speak English, the future tense is usually straightforward. You simply add the word "will" in front of a verb and say "I will read," "I will write," "I will cook." It is a reliable tool that gets the job done. However, this grammatical simplicity hides a significant amount of ambiguity. When you tell a friend, "I will read that book tomorrow," what exactly are you promising? Do you mean that you will spend some time engaged in reading, perhaps getting through a few chapters? Or are you making a firm commitment that you will start reading and not stop until you reach the very last page, completely finishing the book? English relies heavily on context or additional words to make this critical distinction clear. Ukrainian, on the other hand, does not let you hide behind this kind of linguistic ambiguity. The Ukrainian language forces you to make a definitive choice about the specific nature of the action before you even open your mouth to speak. You cannot simply say a generic "will." You must decide right then and there if your future action is an ongoing process or a completed result.

У цьому модулі ми будемо детально досліджувати, як саме українська мова виражає майбутній час і як вид дієслова впливає на цей процес. Але перед тим, як ми заглибимося в граматичні правила та таблиці, спершу перевірмо вашу природну інтуїцію. Ви вже знаєте багато слів і маєте практичний досвід читання українських текстів. Спробуйте зараз покластися на свій внутрішній мовний слух. Коли ви дивитеся на певну життєву ситуацію, яке слово здається вам більш природним: «писатиму» чи «напишу»? Не намагайтеся аналізувати правила, просто швидко обирайте той варіант, який інтуїтивно звучить краще для вас у цьому конкретному контексті.

> *In this module, we will explore in detail exactly how the Ukrainian language expresses the future tense and how the aspect of the verb influences this process. But before we dive into grammar rules and tables, let's first test your natural intuition. You already know many words and have practical experience reading Ukrainian texts. Try to rely on your inner linguistic ear right now. When you look at a certain life situation, which word seems more natural to you: "писатиму" (I will be writing) or "напишу" (I will write/finish writing)? Do not try to analyze the rules, just quickly choose the option that intuitively sounds better to you in this specific context.*

<!-- INJECT_ACTIVITY: quiz-future-intuition -->

How did you do on the diagnostic test? If you found yourself hesitating on some of the questions, that is completely normal. However, if you instinctively felt that «прочитаю» was a much better fit for finishing a book than «буду читати», then congratulations — you already intuitively understand the core concept of Ukrainian aspect. That subtle feeling of "rightness" is exactly what we are going to build upon in this lesson. When you hear or say a phrase like «буду читати», it naturally stretches out in your mind. It feels long, ongoing, continuous, and open-ended. It is the verbal equivalent of walking down a long road without seeing the end. On the other hand, a word like «прочитаю» feels sharp, decisive, and highly final. It feels exactly like crossing a finish line or checking a box on your to-do list. This psychological difference is the fundamental structural difference between how imperfective and perfective verbs operate in the future tense. Your primary goal at the B1 level is to take this subconscious feeling and actively turn it into a conscious, deliberate tool that you can confidently control.

В українській граматичній системі існує три різні конструкції для вираження дій у майбутньому часі. Ми можемо поділити їх на дві великі групи залежно від того, який вид дієслова ми використовуємо. Перша група — це спеціальні форми недоконаного виду, які завжди описують тривалий процес або повторювану дію. Сюди належить складений майбутній час, який утворюється за допомогою допоміжного дієслова «бути» та інфінітива основного дієслова, наприклад, «буду активно працювати». До цієї ж групи належить і синтетичний майбутній час, який складається лише з одного слова з характерним суфіксом, наприклад, «працюватиму». Ці дві форми є граматичними близнюками; вони мають однакове значення і відрізняються одна від одної виключно стилістично. Друга група — це форма доконаного виду, яка фокусується на результаті. Це простий майбутній час, який візуально виглядає точнісінько як теперішній час, але завжди має чітке майбутнє значення, наприклад, «зроблю». Ця форма є єдиним способом показати, що дія буде успішно завершена.

:::info
**Grammar box**
Ukrainian does not possess a direct, single-word translation for the English auxiliary word "will". Instead, the concept of the future is built directly into the verb forms themselves. This is achieved either through separate auxiliary verbs like «буду» working with an infinitive, or through specific endings like «-му» and «-ш» attached to the root.
:::

Before we move forward, let's take a moment for a quick technical recap of what you have already learned in your A2 baseline studies. You already know how to physically construct these words. You know that the compound future (складений) is built by taking the conjugated future tense of the verb "to be" — «буду», «будеш», «буде», «будемо», «будете», «будуть» — and adding the imperfective infinitive to it, resulting in familiar forms like «буду читати». You also recognize the synthetic future (синтетичний), where the specific endings «-му», «-меш», «-ме», «-мемо», «-мете», «-муть» are fused directly onto the infinitive to create an elegant single word: «читатиму». Finally, you are acquainted with the simple perfective future (простий), which mischievously borrows the exact same personal endings as the present tense, but strictly applies them to perfective verbs to instantly project them into the future: «напишу», «напишеш», «напише». At this advanced stage in your learning journey, the primary challenge is no longer about remembering how to form these words. The real challenge is knowing exactly *when* and *why* to choose each specific construction to accurately reflect your true communicative intent.

## Три конструкції: форма і значення

To master the Ukrainian future tense, you must first accept one fundamental truth: aspect is the absolute master of the future. The entire verb system is built around the strict philosophical distinction between an ongoing process and a final result. In English, you rely heavily on universal auxiliary words like "will" or phrases like "going to" to quickly place any action into the future, regardless of its internal nature. The English mind looks at the timeline first and the action second. Ukrainian approaches this differently; it looks at the nature of the action first. Because a process is inherently flexible, fluid, and can be viewed from different stylistic angles, the imperfective aspect is granted two distinct grammatical forms to express the future. It gives you choices depending on the rhythm, tone, and register of your speech. On the other hand, a result is singular, decisive, and final. Therefore, the perfective aspect is granted only one highly efficient form. There is no need for stylistic variation or extra descriptive words when you are simply stating that a goal will be achieved and a concrete boundary crossed. This split — two parallel forms for an unfolding process, one singular form for a definitive result — creates the three core constructions of the Ukrainian future tense. Understanding this architecture is the golden key to true fluency.

Перша конструкція називається складений майбутній час (як зазначено в підручнику Литвінової для 7 класу, с. 44). Вона завжди складається з двох окремих слів: допоміжного дієслова «бути» у відповідній особовій формі та інфінітива основного дієслова недоконаного виду. Ця форма є найбільш нейтральною і найчастіше використовується у повсякденному спілкуванні для опису запланованих процесів. Щоб правильно утворити її, ви просто відмінюєте дієслово «бути» за особами. Ви кажете: я буду працювати, ти будеш працювати, він буде працювати, ми будемо працювати, ви будете працювати, вони будуть працювати. Дуже важливо пам'ятати, що граматично змінюється лише перше слово, тоді як основна дія завжди залишається у незмінній формі інфінітива.

> *The first construction is called the compound future tense. It always consists of two separate words: the auxiliary verb "to be" in the appropriate personal form and the infinitive of the main imperfective verb. This form is the most neutral and is most often used in everyday communication to describe planned processes. To form it correctly, you simply conjugate the verb "to be" by person. You say: I will be working, you will be working, he will be working, we will be working, you will be working, they will be working. It is very important to remember that only the first word changes grammatically, while the main action always remains in the unchangeable infinitive form.*

This compound form is your reliable, everyday workhorse for countless situations. When you are casually chatting with friends about what you will be doing over the upcoming weekend, or when you are outlining your general routine for the next week, this is the construction you will naturally reach for. It clearly and simply communicates that an action will occupy a certain amount of time in the future, or that it will be an ongoing background event, without making any promises about actually finishing it. It feels relaxed, highly conversational, and incredibly accessible because you only have to conjugate the short auxiliary verb. If you say «я буду читати», you are simply stating your intention to engage in the activity of reading. You might read for five minutes or five hours, and you might or might not finish the book. The compound form comfortably covers all those possibilities without committing you to a strict outcome.

The second construction is known as the synthetic imperfective future (див. Заболотний, 7 клас, с. 73). Grammatically and logically, this form means exactly the same thing as the compound form you just learned: it describes a future process, a continuous state, or a repeated action. However, instead of using two separate words, it fuses the future marker directly onto the infinitive, creating a single, elegant, and compact word. You take the full infinitive and add the specific future suffixes: -му, -меш, -ме, -мемо, -мете, -муть.

Ця синтетична форма виглядає так: я працюватиму, ти працюватимеш, вона працюватиме, ми працюватимемо, ви працюватимете, вони працюватимуть. Історично ці унікальні суфікси походять від дуже давнього дієслова «мати», тому слово «працюватиму» колись буквально означало «маю працювати». Сьогодні це єдина граматична конструкція в українській мові, яка дозволяє виразити тривалу дію майбутнього часу лише одним словом, без жодних допоміжних елементів.

While the core meaning remains absolutely identical to the compound form, the synthetic form carries a distinctly different stylistic flavor and emotional weight. It often feels slightly more formal, elevated, literary, or poetic. You will frequently encounter it in written texts, official news broadcasts, formal political speeches, and classic literature where writers seek a smoother cadence. However, it is critical to understand that it is not strictly limited to formal or academic contexts. Many native speakers use it regularly in everyday conversation simply because they prefer how it sounds. It adds a touch of melodic elegance to the sentence, eliminating the slightly repetitive sound of the auxiliary verb. Having two perfectly valid ways to say the exact same thing allows you to vary your rhythm and avoid repetitive phrasing when you are telling longer stories about the future.

:::note
**Quick tip**
The synthetic future is a unique and cherished feature of the Ukrainian language. When you choose to say «читатиму» instead of «буду читати», your Ukrainian instantly sounds more authentic, polished, and deeply rooted in the language's natural rhythm.
:::

The third and final construction is the simple perfective future (Литвінова, 7 клас, с. 46). Unlike the previous two forms, which are designed to handle ongoing processes, this form is reserved exclusively for perfective verbs and focuses entirely on the final result. It is called simple because it consists of only one single word, and remarkably, it does not use any special future suffixes or auxiliary verbs. Instead, it ingeniously borrows the exact same personal endings used in the present tense, but attaches them strictly to a perfective root.

Оскільки дієслова доконаного виду означають повністю завершену дію, вони логічно не можуть мати форми теперішнього часу. Процес можна спостерігати зараз, але фінальний результат належить або минулому, або майбутньому. Тому, коли ви додаєте звичайні особові закінчення до такої основи, слово автоматично вказує на майбутній результат. Парадигма виглядає дуже знайомо: я зроблю, ти зробиш, він зробить, ми зробимо, ви зробите, вони зроблять. Ця коротка форма дає співрозмовнику стовідсоткову гарантію, що дія буде успішно доведена до кінця.

:::tip
**Did you know?**
Because perfective verbs have no present tense, their "present" endings are entirely free to be used for the future. This is a brilliant example of grammatical recycling, allowing the language to express future results without inventing a whole new set of suffixes.
:::

When you deploy this simple form, you are no longer talking about what you will be doing; you are definitively stating what will be done. If you say «я напишу», you are making a firm commitment that the text will be entirely finished, completed, and ready for review. It is the language of promises, concrete plans, definitive outcomes, and measurable achievements. You use it when the completion of the action is the absolute most important piece of information you want to convey to your listener. It cuts through the ambiguity of the process and delivers a guarantee. This is why you will hear it constantly in professional environments, project planning, and any situation where accountability is expected.

Now that you clearly see the strict logical boundary separating the imperfective process forms from the perfective result form, you can fully understand one of the most critical rules of Ukrainian grammar. You must never attempt to combine the auxiliary verb «бути» with a perfective infinitive. A phrase like «буду написати» or «буду зробити» is not just a minor grammatical slip; it is a profound logical contradiction that entirely breaks the structural integrity of the Ukrainian verb system.

Допоміжне дієслово «бути» в майбутньому часі завжди вимагає тривалості та процесу. Воно створює широкий простір, у якому дія може поступово розгортатися. Натомість дієслово доконаного виду, як-от «написати», означає неподільну миттєву точку завершення. Ви фізично не можете розтягнути цю миттєву точку в тривалий процес. Це як намагатися змішати воду та олію в одній склянці. Українська граматика надійно захищає цю внутрішню логіку: якщо ви використовуєте слово «буду», наступне дієслово обов'язково має бути процесом.

If you want to express the future accurately, you must first pause and ask yourself what you truly mean to say. If you want to highlight the duration, the continuous effort, or the activity itself, use «буду писати» or «писатиму». If your goal is to promise that the work will be finished and the result will undeniably exist, drop the auxiliary entirely and simply declare «напишу». Recognizing this strict logical boundary is a major milestone in your language journey. It is the exact moment you stop simply translating English words in your head and start genuinely thinking within the rich framework of Ukrainian aspectual categories. You are no longer just manipulating grammar rules; you are aligning with the mindset of a native speaker.

:::info
**Grammar box**
The auxiliary verb «бути» pairs **only** with imperfective infinitives. Perfective verbs generate their future meaning internally through their structure and their present-tense endings. They never need, and completely reject, any auxiliary support. Never attempt to say «буду прочитати»; you must choose between the process and the result.
:::

<!-- INJECT_ACTIVITY: fill-in-future-forms -->

<!-- INJECT_ACTIVITY: group-sort-constructions -->

## Коли який? Вибір конструкції

> — **Марина:** Отже, щодо нашої поїздки в Карпати. Завтра я забронюю готель і куплю нам квитки на потяг. *(So, about our trip to the Carpathians. Tomorrow I will book the hotel and buy our train tickets.)*
> — **Андрій:** Чудово! А я буду просто насолоджуватися природою. Цілими днями ми гулятимемо лісом і дихатимемо свіжим повітрям. *(Great! And I will just enjoy nature. We will walk in the forest all day and breathe fresh air.)*
> — **Марина:** Так, але спершу ми приїдемо, я розпакую речі і знайду нам хорошого гіда. Я все організую. *(Yes, but first we will arrive, I will unpack the things and find us a good guide. I will organize everything.)*
> — **Андрій:** Марино, ти занадто напружена. Ми відпочиватимемо, будемо пити гарячий чай і нікуди не поспішатимемо. *(Maryna, you are too tense. We will be resting, drinking hot tea, and not rushing anywhere.)*
> — **Марина:** Добре, добре. Я обіцяю, що теж відпочину. Але спочатку я складу чіткий план! *(Okay, okay. I promise that I will also rest. But first, I will make a clear plan!)*

When you listen to Marina and Andriy plan their trip, you are hearing a perfect demonstration of how aspect shapes the future tense in Ukrainian. They are both talking about the exact same weekend, yet they are using entirely different grammatical structures because their psychological focus is fundamentally different. Marina is the planner, focused entirely on achieving specific goals and securing concrete outcomes. She uses perfective verbs like «забронюю» (I will book), «куплю» (I will buy), and «приїдемо» (we will arrive). Each of these verbs points to a single, completed action with a guaranteed result. Once she books the hotel, the task is successfully crossed off the list.

Андрій, навпаки, зосереджений не на результаті, а на самому процесі та емоціях від поїздки. Його мета полягає в тому, щоб дія тривала якомога довше. Тому він використовує дієслова недоконаного виду у складеній та синтетичній формах: «буду насолоджуватися», «гулятимемо», та «відпочиватимемо». Він не планує закінчувати ці дії; він хоче перебувати всередині них. Вибір форми майбутнього часу в українській мові — це завжди вибір того, як саме ви бачите дію у своїй голові.

> *Andriy, on the other hand, is focused not on the result, but on the process and emotions of the trip itself. His goal is for the action to last as long as possible. Therefore, he uses imperfective verbs in compound and synthetic forms: «буду насолоджуватися» (I will be enjoying), «гулятимемо» (we will be walking), and «відпочиватимемо» (we will be resting). He does not plan to finish these actions; he wants to be inside them. The choice of future tense form in Ukrainian is always a choice of exactly how you see the action in your head.*

How do you decide which construction to use when speaking? The most reliable method is the "process versus result" decision framework. The framework relies on testing the logical boundaries of the action you are describing. Before you speak, mentally test your sentence by adding a duration marker or a completion marker. If you can logically add phrases like "for an hour" (годину) or "all day" (цілий день) to your sentence, you are describing a process with wide, open boundaries. In this case, you must use the imperfective aspect, either the compound form («буду читати») or the synthetic form («читатиму»). For example, you can naturally say, "Завтра я буду працювати до вечора" (Tomorrow I will work until evening) because the effort stretches over time.

Якщо ж ви можете логічно додати до свого речення слова на кшталт «нарешті», «успішно», або очікуєте конкретного фіналу, ви говорите про результат. У такій ситуації ви повинні використовувати виключно просту форму доконаного виду. Ви не можете сказати, що будете закінчувати щось цілий день, якщо акцент стоїть саме на точці завершення. Правильно сказати: «Завтра я закінчу цей проєкт» або «Увечері я прочитаю цю статтю».

> *If you can logically add to your sentence words like "finally" (нарешті), "successfully" (успішно), or if you expect a specific finale, you are talking about a result. In such a situation, you must exclusively use the simple form of the perfective aspect. You cannot say that you will be finishing something all day if the accent is precisely on the point of completion. It is correct to say: "Завтра я закінчу цей проєкт" (Tomorrow I will finish this project) or "Увечері я прочитаю цю статтю" (In the evening I will read this article through).*

When we make promises or take on commitments, we are usually assuring someone that a specific task will be successfully completed. Because of this strong cultural focus on tangible outcomes, promises naturally demand the perfective aspect. When you tell a friend «Я напишу тобі» (I will write to you) or «Ми приїдемо вчасно» (We will arrive on time), you are not just describing a future activity; you are offering a guarantee. The simple perfective future delivers this certainty perfectly, leaving no doubt that the action will be finalized.

Однак існують ситуації, коли ваша обіцянка стосується не конкретного результату, а постійних зусиль чи тривалої підтримки. У таких випадках українці використовують майбутній час недоконаного виду. Наприклад, ви можете сказати: «Я буду старатися» (замість доконаного результату «постаратися») або «Ми будемо чекати на тебе». Тут ви берете на себе зобов'язання підтримувати певний стан або виконувати дію протягом тривалого часу. Навіть саме дієслово «обіцяти» має дві форми. Якщо ви кажете «Я пообіцяю йому допомогти», ви говорите про один конкретний акт обіцянки, який відбудеться в майбутньому.

> *However, there are situations when your promise concerns not a specific result, but constant effort or prolonged support. In such cases, Ukrainians use the imperfective future tense. For example, you can say: "Я буду старатися" (I will make an effort / I will try) or "Ми будемо чекати на тебе" (We will be waiting for you). Here you take on the commitment to maintain a certain state or perform an action over a long period. Even the verb "to promise" itself has two forms. If you say "Я пообіцяю йому допомогти" (I will promise to help him), you are talking about one specific act of promising that will happen in the future.*

:::note
**Quick tip**
When apologizing or reassuring a manager at work, use the perfective aspect to sound professional, decisive, and reliable. Say «Я все виправлю» (I will fix everything) rather than «Я буду виправляти» (I will be fixing it). The perfective form communicates that the problem will be fully resolved.
:::

> — **Мама:** Дмитре, коли ти нарешті зробиш домашнє завдання? Вже сьома година вечора! *(Dmytro, when will you finally do your homework? It's already seven in the evening!)*
> — **Дмитро:** Мамо, я буду робити його після вечері. Спочатку я писатиму математику, а потім читатиму історію. *(Mom, I will be doing it after dinner. First I will be writing math, and then I will be reading history.)*
> — **Мама:** Мене не цікавить, як довго ти сидітимеш за столом. Я питаю, коли ти напишеш твір з літератури? *(I don't care how long you will be sitting at the desk. I am asking, when will you write the literature essay?)*
> — **Дмитро:** Я ж кажу, що буду старатися! Я почну працювати о восьмій і робитиму все дуже уважно. *(I am telling you that I will be trying! I will start working at eight and will be doing everything very carefully.)*
> — **Мама:** Добре, але я перевірю результат, коли ти закінчиш. *(Fine, but I will check the result when you finish.)*

This conversation between a mother and her son highlights a brilliant tactical use of grammatical aspect, often called the "Process Defense." The mother is asking for a concrete, measurable result. Her questions consistently use the perfective aspect («зробиш», «напишеш», «закінчиш») because she wants the homework to be fully completed. She is demanding accountability and a final product, pushing for a definitive answer.

Дмитро чудово розуміє її вимоги, але уникає прямих обіцянок результату. Замість цього він будує свій захист навколо процесу. Відповідаючи формами недоконаного виду («буду робити», «писатиму», «читатиму», «робитиму»), він підкреслює кількість зусиль, які планує витратити. Він ніби каже: "Дивись, як багато часу і праці я вкладатиму в це завдання". Це дуже точне ведення переговорів за допомогою граматики. Він демонструє свою зайнятість, але обережно уникає використання дієслова «зроблю», яке б зобов'язало його надати готовий і ідеальний результат до певного часу.

> *Dmytro perfectly understands her demands, but avoids direct promises of a result. Instead, he builds his defense around the process. By answering with imperfective forms ("буду робити", "писатиму", "читатиму", "робитиму"), he emphasizes the amount of effort he plans to spend. It is as if he is saying: "Look how much time and labor I will invest in this task." This is very precise negotiation using grammar. He demonstrates his busyness, but carefully avoids using the verb "зроблю" (I will get it done), which would obligate him to provide a finished and perfect result by a certain time.*

In real life, our plans for the future are rarely just one long, unbroken process or a simple, dry list of completed tasks. A natural narrative about tomorrow will seamlessly weave both aspects together. This mixing of forms allows you to create a realistic, three-dimensional picture of your day, showing both the major milestones you intend to pass and the continuous activities that comfortably fill the space between them. 

Наприклад, ви можете розповісти про свій розклад так: «Завтра я встану о сьомій ранку. Потім я пів години снідатиму і читатиму новини. О дев'ятій годині я поїду в офіс, де працюватиму до шостої вечора. А коли я повернуся додому, я приготую смачну вечерю». У цьому тексті ідеально поєднуються різні конструкції. Дієслова доконаного виду («встану», «поїду», «повернуся», «приготую») слугують точками на часовій шкалі — це ключові події, які просувають розповідь вперед. А дієслова недоконаного виду («снідатиму», «читатиму», «працюватиму») заповнюють ці проміжки часу фоновою діяльністю.

> *For example, you can talk about your schedule like this: "Tomorrow I will get up at seven in the morning. Then I will be having breakfast for half an hour and reading the news. At nine o'clock I will go to the office, where I will be working until six in the evening. And when I return home, I will prepare a delicious dinner." This text perfectly combines different constructions. The perfective verbs ("встану", "поїду", "повернуся", "приготую") serve as points on the timeline — these are key events that move the narrative forward. And the imperfective verbs ("снідатиму", "читатиму", "працюватиму") fill these time gaps with background activity.*

<!-- INJECT_ACTIVITY: match-up-situations -->

## Підсумок: три майбутні як система

When learning a new language, discovering that it has three different ways to express the future tense might initially feel like an unnecessary burden. You might ask yourself: why do I need three separate forms just to say "I will"? For English speakers, "I will write" is a simple, one-size-fits-all solution that covers almost every situation, whether you are planning to spend your whole weekend writing or promising to deliver a final draft by tomorrow. However, this apparent simplicity comes at a cost: ambiguity. When you say "I will write," your listener does not know if you mean you will spend the afternoon engaged in the process of writing, or if you are guaranteeing that a finished document will be produced by the end of the day. They have to guess your exact intention based entirely on context, or ask clarifying questions to figure out what you actually mean.

Ukrainian, on the other hand, does not make the listener guess. The three-construction system is not an example of unnecessary grammatical complexity; it is a finely tuned instrument for absolute precision. The system forces the speaker to make a conscious commitment to their meaning before they even finish forming the sentence. If you use the imperfective forms, like «я писатиму» or «я буду писати», you are explicitly telling your listener that your focus is entirely on the ongoing action. You are promising the effort, the time, and the continuous process, but you are deliberately not promising a final product. Conversely, if you use the simple perfective form, «я напишу», you are making a hard guarantee of a result. This distinction is incredibly powerful in everyday life. It allows you to manage expectations, negotiate deadlines, and describe your intentions with a level of accuracy that a single "will" simply cannot match. It transforms the future tense from a vague prediction (передбачення) into a precise communicative tool.

Складена форма з дієсловом «бути» — це найпоширеніший варіант для повсякденного спілкування. Це ваш надійний, нейтральний розмовний стиль. Ви почуєте цю форму на вулиці, в кав’ярнях, у неофіційних розмовах з друзями чи колегами. Цю конструкцію найлегше утворити під час швидкої бесіди, оскільки відмінюється лише допоміжне дієслово, а основне залишається в інфінітиві. Натомість синтетична форма з суфіксом «-тиму» звучить трохи більш піднесено, книжно або елегантно. Вона частіше зустрічається в художній літературі, публіцистиці, офіційних промовах або поезії. Цей писемний стиль робить текст більш вишуканим. Деякі мовознавці вважають її більш традиційною та автентичною, оскільки вона є унікальною рисою нашої мови. Обидві форми є абсолютно правильними та стандартними. Як учень, ви можете обрати ту форму, яка вам більше подобається, але ви повинні розуміти обидві, адже українці постійно чергують їх залежно від ситуації та настрою.

> *The compound form with the verb "бути" is the most common option for everyday communication. It is your reliable, neutral conversational standard. You will hear this form on the street, in cafes, in informal conversations with friends or colleagues. This construction is the easiest to form during a fast conversation, since only the auxiliary verb is conjugated, and the main verb remains in the infinitive. In contrast, the synthetic form with the suffix "-тиму" sounds a bit more elevated, literary, or elegant. It is found more often in fiction, journalism, official speeches, or poetry. Some linguists consider it more traditional and authentic, as it is a unique feature of our language. Both forms are absolutely correct and standard. As a learner, you can choose the form that you like better, but you must understand both, because Ukrainians constantly alternate them depending on the situation and mood.*

:::tip
**Did you know?**
Some learners worry about picking the "wrong" imperfective future form, but Ukrainians constantly mix the compound («буду писати») and synthetic («писатиму») forms in the same sentence to avoid repeating words. For example: «Я буду писати книгу, а потім читатиму статті». You can't go wrong with either!
:::

When trying to master this system, English speakers inevitably face a few specific pitfalls. These errors usually happen when learners try to map English logic onto Ukrainian grammar, creating constructions that the language simply rejects. 

The most common trap is the "hybrid" future: *«Я буду написати цю книжку»*. This happens when a learner takes the English "will" (буду) and attaches it to the English "write" (написати). But in Ukrainian, these two words belong to completely different categories. The auxiliary verb «бути» strictly requires an imperfective infinitive because it signifies an ongoing state of existence or process. You cannot "be" in the middle of a completed result. It is logically impossible. To fix this, you must choose your path based on your true intention. If you want to communicate the result, drop «буду» and use the simple perfective form «напишу». If you want to communicate the process, keep «буду» and use the imperfective infinitive: «буду писати».

The second pitfall is the clash of duration markers with the perfective aspect, such as *«Завтра я прочитаю цілий день»*. The verb «прочитаю» explicitly means "I will finish reading," which is a punctual event or a guaranteed result. A result happens in an instant; it cannot stretch out for a "whole day." When you have a phrase that emphasizes duration—like "цілий день," "три години," or "весь вечір"—you must use the imperfective aspect. The correct phrasing is «завтра я читатиму цілий день» or «я буду читати цілий день».

Finally, learners often overcomplicate lists by mixing aspects redundantly, like *«Вона завтра зробить уроки і робитиме»*. If you are talking about a single action, you only need one aspect. If your goal is the completed homework, stick to the perfective «зробить». Adding an extra imperfective form just creates confusion and breaks the natural rhythm of the sentence.

:::info
**Grammar box**
To quickly check if your future tense is correct, apply the "End of the Road" test. If the action has a clear end of the road where the job is done and you can move on, you need the perfective form (like *напишу*, *зроблю*). If the action is the journey itself, with no visible end, you need the imperfective form (like *буду писати*, *робитиму*).
:::

<!-- INJECT_ACTIVITY: error-correction-future -->

Уміння правильно обирати форму майбутнього часу є лише першим кроком до природного мовлення. Коли ви плануєте (або хочете запланувати) свій завтрашній день або розповідаєте комусь про майбутню подорож, ви рідко обмежуєтеся лише тривалими процесами або лише сухими результатами. Ваша розповідь — це тривимірна картина, де різні форми постійно взаємодіють між собою, створюючи перспективу. У наступному модулі ми детально розберемо, як будувати зв'язний текст за допомогою фонових подій та подій переднього плану. Уявіть, що недоконаний вид, наприклад, «я сидітиму в кафе», «світитиме сонце», «гратиме музика», створює атмосферу, декорації та тло для вашої історії. Це простір, у якому розгортається дія. А доконаний вид, як-от «мій друг прийде», «ми замовимо каву», «я підпишу контракт», додає конкретні, завершені кроки, які швидко просувають сюжет уперед. Завдяки цій взаємодії ваша історія оживає. Тому зараз так важливо навчитися відчувати різницю на рівні окремих речень, щоб згодом ви могли впевнено сплітати їх у велике розмовне полотно.

<!-- INJECT_ACTIVITY: open-writing-tomorrow-plan -->

To wrap up our discussion of the future tense, keep these core principles in mind:

- **Складений майбутній час (Compound Future)** — *буду* + imperfective infinitive. This describes an ongoing process or state. It is your neutral, everyday conversational standard.
- **Синтетичний майбутній час (Synthetic Future)** — imperfective infinitive + *-тиму* ending. This also describes an ongoing process, identical in meaning to the compound form, but it sounds slightly more literary, elegant, and uniquely Ukrainian.
- **Простий майбутній час (Simple Future)** — perfective verb with present tense endings. This form guarantees a completed result or a single, punctiliar action in the future.
- **The Aspect Rule** — Your choice between imperfective and perfective depends entirely on your focus: duration and process versus completion and result.
- **The Memory Hook** — You can't 'be' (*бути*) a finished result (*написати*), you can only 'be' in a state or a process (*писати*). Because of this logical rule, the compound form never mixes with perfective verbs.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-future-tense
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

**Level: B1 (Module 5)**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

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
