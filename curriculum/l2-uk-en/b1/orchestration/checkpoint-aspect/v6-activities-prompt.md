<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-aspect.yaml` file for module **10: Контрольна робота: вид дієслова** (b1).

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
- `<!-- INJECT_ACTIVITY: group-sort-future-imperative -->`
- `<!-- INJECT_ACTIVITY: match-up-negation-meaning -->`
- `<!-- INJECT_ACTIVITY: error-correction-imperative -->`
- `<!-- INJECT_ACTIVITY: fill-in-past-aspect -->`
- `<!-- INJECT_ACTIVITY: open-writing-aspect-check -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Визначте вид дієслова та поясніть аспектну функцію (тло, подія, результат,
    тривалість) у реченнях з M01-M11
  items: 12
  type: quiz
- focus: 'Оберіть правильний вид дієслова у контексті: минулий, майбутній, наказовий
    спосіб, заперечення'
  items: 10
  type: fill-in
- focus: 'Знайдіть і виправте помилки у вживанні виду в реченнях: неправильний аспект
    у розповіді, наказі, запереченні'
  items: 8
  type: error-correction
- focus: 'Розподіліть дієслова за видом і контекстом: тло / подія / загальна інструкція
    / конкретна команда'
  items: 10
  type: group-sort
- focus: З'єднайте видові пари та вкажіть контекст, де кожен вид доречний
  items: 8
  type: match-up
- focus: 'Напишіть текст із завданнями: 1) розповідь про минулий тиждень (тло + події),
    2) три пари наказів, 3) два умовні речення з різним видом'
  items: 8
  type: open-writing


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- подієвий ланцюг (event chain — sequence of perfective actions)
- загальне заперечення (general negation — imperfective, action didn't occur)
- нереалізований результат (unrealized result — perfective negation, expected outcome
  not achieved)
- заборона (prohibition — negative imperative, strongly prefers imperfective)
- попередження (warning — perfective negative imperative for accidental actions)
- 'синтетичний майбутній (synthetic future — perfective: напишу)'
- 'аналітичний майбутній (analytic future — imperfective: буду писати)'
required:
- доконаний вид (perfective aspect — completed, result-oriented action)
- недоконаний вид (imperfective aspect — ongoing, unbounded action)
- видова пара (aspectual pair — e.g., писати/написати)
- тло розповіді (narrative background — imperfective setting/scene)
- послідовність подій (sequence of events — perfective event chain)
- наказовий спосіб (imperative mood — commands and requests)
- заперечення (negation — negative constructions with aspect)
- умовний спосіб (conditional mood — hypothetical actions with би/б)
- результативність (resultativity — focus on outcome, triggers perfective)
- тривалість (duration — focus on process length, triggers imperfective)
- діагностика (diagnostics — self-assessment of aspect mastery)
- повторення (review/repetition — consolidation of learned material)
- контрольна робота (test/assessment — formal diagnostic check)
- минулий час (past tense — time frame for aspect practice)
- майбутній час (future tense — time frame for aspect practice)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вид у минулому: тло і послідовність

At the B1 level, choosing between the **недоконаний вид** (imperfective aspect) and **доконаний вид** (perfective aspect) is no longer just about memorizing grammar rules or isolated vocabulary pairs. It becomes a powerful narrative tool. True proficiency requires you to use aspect to paint a picture for your listener, distinguishing clearly between the static background of a scene and the dynamic actions that drive a story forward. In this section, we will diagnose your ability to control the flow of time in past tense narratives. We will review how to set the scene using the imperfective aspect and how to build a chain of events using the perfective aspect. Let's ensure your foundation is solid before we move on to more complex structures. Aspect is the heartbeat of the Ukrainian language; mastering it will make your storytelling sound authentic and native-like.

> — **Вчитель:** Доброго ранку! Ти читав цей текст про історію Києва? *(Good morning! Did you read this text about the history of Kyiv?)*
> — **Учень:** Так, я прочитав його вчора ввечері. *(Yes, I read it yesterday evening.)*
> — **Вчитель:** Чудово. Тобто ти зрозумів головну ідею? *(Excellent. So you understood the main idea?)*
> — **Учень:** Думаю, так. Я довго вивчав нові слова, а потім легко переклав статтю. *(I think so. I studied the new words for a long time, and then easily translated the article.)*
> — **Вчитель:** Добре. Тоді зараз напиши короткі відповіді на мої запитання. *(Good. Then now write short answers to my questions.)*

Notice how the teacher asks «Ти читав?» using the imperfective aspect to inquire about the general process or fact of reading. The teacher is not asking if the book was finished, but rather whether the action took place at all. The student replies with «Я прочитав», using the perfective aspect to proudly confirm the successful result. This distinction is vital: the imperfective asks about the experience, while the perfective announces the achievement. Finally, the teacher issues a specific, one-time command using the perfective imperative: «напиши». The teacher expects a tangible outcome—the written answers. This constant shifting of aspect based on intent, rather than just tense, is the true hallmark of natural Ukrainian speech.

Think of the imperfective past tense as a wide-angle camera shot in a movie. When a director wants to establish the setting, they show a continuous, unbroken scene. In Ukrainian, verbs like **падав** (was falling) or **гралися** (were playing) describe exactly these ongoing, parallel processes. They do not advance the plot; instead, they give the plot a place to exist. They answer the question "What was happening in the background?"

Коли ми розповідаємо історію, нам спочатку потрібно створити декорації для майбутніх подій. Для цього ми використовуємо недоконаний вид, який формує тло розповіді. Уявіть собі картину: надворі тихо падав сніг, дув холодний зимовий вітер, а маленькі діти весело гралися у дворі. Усі ці дії відбуваються одночасно, вони розтягнуті в часі і не мають чіткого початку чи кінця в межах нашої короткої розповіді. Вони просто створюють певну атмосферу, в якій пізніше обов'язково щось трапиться. Недоконаний вид дозволяє слухачеві ніби зупинити час, затримати подих і уважно роздивитися всі деталі сцени. Це ваш інструмент для створення настрою.

На тлі цієї статичної картини раптом починається рух, який штовхає історію вперед. Для опису подій, що відбуваються одна за одною, ми використовуємо доконаний вид. Це називається подієвим ланцюгом. Повернемося до нашого зимового двору. Наприклад: хлопчик зліпив велику сніжку, розмахнувся і сильно кинув її у високе дерево. Зверніть увагу на логіку: кожна наступна дія починається тільки після того, як повністю завершилася попередня. Він не міг кинути сніжку, поки не зліпив її. Доконаний вид діє як серія швидких фотознімків, де кожен новий кадр фіксує новий завершений етап історії.

> *Against the background of this static picture, movement suddenly begins, pushing the story forward. To describe events that occur one after another, we use the perfective aspect. This is called an event chain. Let's return to our winter yard. For example: the boy made a large snowball, swung his arm, and threw it hard at a tall tree. Notice the logic: each subsequent action begins only after the previous one has completely finished. He could not throw the snowball until he had made it. The perfective aspect acts like a series of quick photographs, where each new frame captures an absolutely new completed stage of the story.*

:::info
**Граматика:** Тло і послідовність
Use **недоконаний вид** (imperfective) to describe the background, parallel actions, or the general atmosphere of a scene. Use **доконаний вид** (perfective) for a sequence of completed actions where one event strictly follows another. If you can insert the word "then" between the verbs (He did X, *then* he did Y), you almost certainly need the perfective aspect.
:::

In natural speech, we rarely use only one aspect for a whole story. Instead, we constantly mix both aspects to create complex, dynamic narratives that feel alive. A classic narrative structure involves a background process being unexpectedly interrupted by a sudden event. When you want to express the universal idea of "while X was happening, Y occurred," you must rely on this contrast. You must use the imperfective aspect for the long, ongoing action and the perfective aspect for the sharp, interrupting event.

Розглянемо такий життєвий приклад: коли ми спокійно снідали на кухні, раптом зателефонувала моя бабуся. Дієслово «снідали» має недоконаний вид, бо це був наш тривалий ранковий процес, наше тло. Натомість дієслово «зателефонувала» має доконаний вид, оскільки це раптова, завершена дія, яка миттєво перервала наш сніданок. Бабуся радісно сказала, що приїде до нас у гості. Ми щиро зраділи цій чудовій новині і відразу почали прибирати вітальню. Зверніть увагу на цю комбінацію: ми використовуємо доконаний вид для результату подій («сказала», «зраділи», «почали»), але повертаємося до недоконаного виду для опису самого процесу прибирання («прибирати»), який, очевидно, триватиме ще певний час.

Отже, правильний вибір виду дієслова в минулому часі — це не просто граматична вправа, а спосіб керувати увагою вашого співрозмовника. Ви як режисер свого власного фільму. Ви можете свідомо зупинити розповідь, щоб описати деталі природи, погоди чи емоції людей, майстерно використовуючи недоконаний вид. Або ж ви можете різко прискорити темп історії, перераховуючи швидкі, результативні та енергійні дії за допомогою доконаного виду. Саме таке чергування робить ваше українське мовлення по-справжньому природним, виразним і багатим на відтінки.

<!-- INJECT_ACTIVITY: quiz-aspect-identification -->

## Вид у майбутньому та наказовому

Understanding the future tense in Ukrainian requires a fundamental shift in how you think about time and action. In English, you often rely on complex tense structures like "I will be doing" or "I will have done" to convey nuances of duration and completion. In Ukrainian, the future tense is surprisingly simple in its structure, but it heavily relies on the aspect of the verb to carry this meaning. For English speakers, the challenge is not memorizing new endings, but rather choosing the right verb from the aspectual pair to accurately map your intention. You must decide whether your future action is a prolonged process or a targeted result. Simply translating English future tenses without considering this distinction can cause confusion. If you do not clarify your intention, you risk sounding unnatural or miscommunicating your actual plans. For example, translating 'I will read' requires choosing between the process (**я буду читати**) and the result (**я прочитаю**).

The Ukrainian future tense has three distinct grammatical forms, and they are strictly tied to the aspect of the verb. The perfective aspect, which focuses on the result, has only one form: the simple future. For example, you might use «напишу» or «прочитаю». Visually and grammatically, these look exactly like present tense verbs. However, because a perfective verb inherently describes a completed action, it cannot exist in the present moment. Adding personal endings automatically projects the result into the future. On the other hand, the imperfective aspect, which focuses on the process, has two interchangeable forms. You can use the compound future with the auxiliary verb «бути», such as «буду писати». Alternatively, you can use the complex future formed by adding a suffix to the infinitive, such as «писатиму». Both imperfective forms mean the exact same thing and are used to describe ongoing or repeated future actions.

В українській мові дієслова доконаного виду взагалі не мають форм теперішнього часу. Коли ви берете дієслово доконаного виду, наприклад «прочитати», і додаєте до нього особові закінчення, ви автоматично створюєте форму майбутнього часу: «я прочитаю», «ти прочитаєш». Це означає, що дія обов'язково завершиться і принесе конкретний результат у майбутньому.

> *In the Ukrainian language, perfective verbs do not have present tense forms at all. When you take a perfective verb, for example "to read completely", and add personal endings to it, you automatically create a future tense form: "I will read", "you will read". This means that the action will definitely be completed and will bring a specific result in the future.*

:::info
**Grammar box** — Three forms of the future tense.
The perfective aspect uses only the synthetic future (**синтетичний майбутній**: «напишу», «прочитаю») to focus on the final result. The imperfective aspect uses either the analytic future (**аналітичний майбутній**: «буду писати») or the uniquely Ukrainian complex form with a suffix («писатиму») to focus on the process.
:::

How do you choose between these forms in real life? It comes down to your intention: planned result versus habitual duration. When you say «Завтра я напишу лист», you are making a commitment to a specific, one-time action. This action will have a tangible outcome, like a finished letter. The perfective aspect is driven by this goal. However, if your focus is on a routine, a habit, or how you will spend your time, you must switch to the imperfective aspect. Saying «Щодня писатиму щоденник» emphasizes the repetitive nature of the action, without focusing on completing any single entry. Contextual trigger words often dictate this choice. Words like «кожного дня», «часто», «довго», or «завжди» naturally pair with the imperfective future because they describe duration or repetition. Conversely, words like «завтра», «до вечора», or «раптом» usually signal the need for the perfective future.

Якщо ви хочете пообіцяти комусь допомогу і гарантувати результат, вам потрібен доконаний вид. Ви кажете: «Я допоможу тобі завтра вранці», і людина знає, що проблема буде вирішена. Якщо ж ви кажете: «Я допомагатиму тобі щодня», ви пропонуєте тривалий процес підтримки, але не обіцяєте миттєвого виконання конкретного завдання.

> *If you want to promise someone help and guarantee a result, you need the perfective aspect. You say: "I will help you tomorrow morning," and the person knows that the problem will be solved. If you say: "I will be helping you every day," you are offering an ongoing process of support, but you do not promise an immediate solution to a specific task.*

The choice of aspect becomes even more fascinating—and socially important—when we look at the imperative mood. In Ukrainian, commands and requests carry a strong social and emotional tone depending on the aspect you choose. The imperfective imperative is often used for general advice, invitations, or polite encouragement. When a host opens the door and says «Заходьте!» or «Сідайте!», they are creating a welcoming, open-ended invitation. It sounds hospitable because it focuses on the process of making oneself comfortable rather than demanding a completed action. Similarly, general life advice like «Читайте більше!» uses the imperfective to encourage a continuous habit. The perfective imperative, however, is a specific, targeted command. It expects a one-time action to be completed right now or by a certain deadline. Saying «Сядьте на це місце!» or «Прочитайте цю сторінку!» is direct and focused strictly on the required result.

:::tip
**Did you know?** — Cultural politeness in commands.
When inviting guests to start eating or to come inside, Ukrainians almost exclusively use the imperfective imperative («Проходьте!», «Сідайте!», «Їжте!»). Using the perfective («Увійдіть!», «Сядьте!», «З'їжте!») sounds like a strict military or police command, stripping away all hospitality.
:::

Коли викладач заходить до аудиторії, він може сказати студентам: «Розгортайте зошити і пишіть». Це звучить як запрошення до початку робочого процесу. Але якщо під час іспиту викладач каже: «Напишіть своє прізвище на бланку», це вже чітка інструкція, яка вимагає конкретного, швидкого результату.

> *When a teacher enters the classroom, they might say to the students: "Open your notebooks and write." This sounds like an invitation to begin the working process. But if during an exam the teacher says: "Write your last name on the form," this is now a clear instruction that demands a specific, quick result.*

This distinction is crucial for instructional precision, especially in academic or professional settings. If your manager or professor wants a task completed by a specific time, they will use the perfective imperative. A directive like «Прочитайте цей текст до завтра» means the text must be finished. The result is mandatory. The perfective imperative leaves no room for ambiguity about whether the task is ongoing—it must reach a completed state. On the other hand, if a doctor or mentor gives you a regimen to follow, they will use the imperfective imperative. The instruction «Читайте кожен день перед сном» focuses on establishing a healthy routine. You aren't expected to finish the whole book in one night; you are expected to engage in the activity regularly. Mastering this difference allows you to navigate professional requests accurately. It also helps you give instructions that don't sound unintentionally harsh or overly vague.

У професійному середовищі дуже важливо правильно формулювати прохання до колег. Якщо ви скажете «Перевіряйте цей звіт», колега може подумати, що це його новий постійний обов'язок. Якщо ж вам потрібен результат саме сьогодні, ви обов'язково повинні сказати: «Перевірте цей звіт, будь ласка».

> *In a professional environment, it is very important to correctly formulate requests to colleagues. If you say "Check this report", a colleague might think that this is their new permanent duty. If you need the result specifically today, you absolutely must say: "Check this report, please".*

<!-- INJECT_ACTIVITY: group-sort-future-imperative -->

## Вид і заперечення

Negation in Ukrainian is not just about stating that something didn't happen; it is about defining the nature of the absent action. In English, a simple past tense negation covers almost all contexts. In Ukrainian, you must decide whether you are denying the existence of the process itself or the achievement of a result.

Коли ми використовуємо недоконаний вид із запереченням, ми говоримо про відсутність самої дії. Речення «Я не читав цю книжку» означає, що процес читання ніколи не відбувався. Ви просто констатуєте факт: цієї дії не було у вашому досвіді. Натомість доконаний вид акцентує на нереалізованому результаті. Якщо ви кажете «Я не прочитав цю книжку», це означає, що дія, можливо, починалася, або від вас очікували результату, але ви його не досягли. Ви не змогли закінчити процес.

This distinction is crucial because using the perfective aspect often carries an implied apology or an acknowledgment of an unmet expectation. For example, in a professional context, if your manager asks about a report, saying «Я не читав цей звіт» implies you haven't even opened the document yet. Saying «Я не прочитав цей звіт» indicates you started reviewing it but haven't reached the end. The imperfective denies the attempt, while the perfective denies the success.

This logic extends naturally into the future tense. When you negate a future action, you are either refusing to engage in the process entirely or predicting your inability to reach a specific, completed outcome.

Заперечення в майбутньому часі також будується на цьому принципі. Якщо ви використовуєте складену форму недоконаного виду, наприклад «Я не буду читати цю книжку», це звучить як ваша принципова відмова або загальний план. Ви заздалегідь відхиляєте цей процес. Але коли ви використовуєте доконаний вид, як у реченні «Я не прочитаю цю книжку до завтра», ви робите прогноз щодо своєї спроможності. Ви визнаєте певне обмеження: текст занадто довгий або складний, тому очікуваний результат не буде досягнутий вчасно.

Notice how the imperfective future negation acts as a boundary you set for yourself, while the perfective future negation is often an honest assessment of external constraints. If a project is too large, you might tell your boss «Я не напишу цей звіт сьогодні». You aren't refusing to work; you are managing expectations about the final result. You will work on it, but the completed document won't be ready. Conversely, «Я не писатиму цей звіт» sounds like a firm rejection of the assignment itself.

:::info
**Grammar box** — Double Negation and the Genitive Case
When you negate a sentence using the verb **мати** (to have), the object must switch to the genitive case. While we say «Він має машину» (accusative), the negative form becomes «Він не має машини» or «У нього немає машини» (genitive). The object of a negated action frequently shifts to the genitive case in Ukrainian to emphasize the total absence of the item. This rule also applies to existential negation, such as «Тут немає води» (There is no water here).
:::

The most critical difference between the aspects under negation appears in the imperative mood. Standard Ukrainian strongly prefers the imperfective aspect for prohibitions, requests not to do something, and general negative advice. This is often confusing for learners who want to translate a specific English command literally.

Якщо ви хочете попросити когось не робити певну дію, ви майже завжди повинні використовувати недоконаний вид. Стандартні заборони формуються саме так: «Не відчиняйте вікна!», «Не купуй цього!», «Не пишіть тут!». Навіть якщо ви маєте на увазі одноразову або дуже конкретну ситуацію, українська мова вимагає недоконаного виду для прямої заборони. Використання доконаного виду в заперечних наказах зустрічається рідко і має зовсім інше, дуже специфічне значення.

When you tell someone not to do something, you are instructing them to maintain their current state of non-action. You are blocking the process from starting. Therefore, the imperfective aspect is the logical choice to describe an ongoing state of "not doing." Even if a teacher wants students to not write one specific sentence, they will say «Не пишіть!», because the goal is to prevent the writing process entirely.

So, when do we use the perfective aspect in a negative imperative? We use it not to forbid an intentional action, but to warn someone against an accidental or unintentional mistake. It is a warning about a negative consequence, not a prohibition of a deliberate choice.

Доконаний вид у заперечних наказах звучить як застереження від випадковості. Порівняйте дві фрази. «Не падай!» — це загальна порада дитині на майданчику, коли ви просите її бути обережною під час гри. Але «Не впади!» — це різке попередження в конкретний момент, коли людина вже стоїть на краю або послизнулася. Ви попереджаєте про небажаний миттєвий результат. Так само працює пара «не забувай» і «не забудь». Перше — це регулярне нагадування писати чи дзвонити, а друге — фокус на одній важливій речі, яку не можна випадково пропустити.

> *The perfective aspect in negative imperatives sounds like a warning against an accident. Compare two phrases. "Don't fall!" is general advice to a child on a playground when you ask them to be careful while playing. But "Be careful not to fall!" is a sharp warning in a specific moment when a person is already standing on the edge or has slipped. You are warning about an undesirable instantaneous result. The pair "don't forget" and "be careful not to forget" works the same way. The first is a regular reminder to write or call, and the second is a focus on one important thing that cannot be accidentally missed.*

By mastering this distinction, you avoid sounding unnatural or accidentally alarming people. If you say «Не відчиніть вікно» to your passengers, they might think you are warning them that the window is broken and might fall out if they touch it. To simply ask them to keep it closed because it's cold, you must use the imperfective: «Не відчиняйте вікно». This nuance is one of the most reliable markers of an advanced, natural-sounding Ukrainian speaker.

A fundamental rule of Ukrainian negation is that double, or even triple, negation is not just allowed—it is mandatory. If your sentence includes a negative pronoun or adverb, the verb must also take the negative particle.

В українській мові подвійне заперечення є обов'язковою граматичною нормою. Якщо ви використовуєте такі слова, як «ніхто», «нічого», «ніколи» або «ніде», дієслово також повинно мати заперечну частку. Фраза «Я нічого не знав» є правильною і природною. На відміну від англійської мови, ці два заперечення не скасовують одне одного, а навпаки, посилюють зміст. Пропуск частки біля дієслова є грубою граматичною помилкою.

While an English speaker might say "I knew nothing," translating that literally as «Я нічого знав» is grammatically incorrect in Ukrainian. You must say «Я нічого не знав». This rule applies continuously regardless of whether the verb is perfective or imperfective.

<!-- INJECT_ACTIVITY: match-up-negation-meaning -->
<!-- INJECT_ACTIVITY: error-correction-imperative -->

## Вид в умовному способі та підсумок

The conditional mood in Ukrainian, known as the **умовний спосіб**, allows us to talk about hypothetical situations, desires, or events that depend on a specific condition. Just like in the past and future tenses, the choice of aspect here is not random. It strictly follows the fundamental logic of Ukrainian verbs. Are you imagining a process, a state, a repeated action, or are you visualizing a single, completed event with a clear result? When you use the imperfective aspect in a conditional sentence, you are setting up a hypothetical background or describing a continuous state of being. When you use the perfective aspect, you are describing a hypothetical jump from one state to another. It represents a sudden change or a completed achievement that triggers another event. For instance, compare the continuous state in **якби я читав** (if I were reading) to the completed jump in **якби я прочитав** (if I had finished reading).

Умовний спосіб утворюється дуже просто: ми беремо форму минулого часу дієслова і додаємо частку «би» або «б». Але вибір виду кардинально змінює картину, яку ви малюєте у своїй уяві. Якщо ви кажете «Якби я жив у Києві», ви використовуєте недоконаний вид. Ви описуєте гіпотетичний стан, тривалу ситуацію, яка не має чіткого початку чи кінця у вашій фантазії. Це ніби декорація для інших подій. Натомість фраза «Якби я переїхав до Києва» використовує доконаний вид. Вона фокусується на одній конкретній, завершеній дії в минулому, яка змінила б ваше теперішнє життя. Це не процес, а подія-результат.

> *The conditional mood is formed very simply: we take the past tense form of the verb and add the particle "би" or "б". But the choice of aspect radically changes the picture you are drawing in your imagination. If you say "If I lived in Kyiv", you use the imperfective aspect. You describe a hypothetical state, a continuous situation that has no clear beginning or end in your fantasy. It is like a setting for other events. In contrast, the phrase "If I moved to Kyiv" uses the perfective aspect. It focuses on one specific, completed action in the past that would change your present life. This is not a process, but a result-event.*

This distinction is crucial because it allows you to be incredibly precise without needing extra words. In English, you might rely on different tenses or auxiliary verbs to convey this difference. In Ukrainian, the aspect does all the heavy lifting. You simply choose the shape of the action you want to express.

When building full conditional sentences, which typically consist of an "if" clause and a "then" clause, the aspectual matching becomes even more fascinating. You can pair different aspects to describe exactly how the condition and the result interact over time. Most commonly, you will see symmetrical pairings where both verbs share the same aspect, but the meaning of the entire sentence shifts entirely based on which aspect you choose.

Розглянемо дві ситуації, які англійською мовою можуть звучати дуже схоже, але українською мають різний зміст. Перша ситуація: «Якби вона подзвонила, я б відповів». Тут ми бачимо два дієслова доконаного виду. Це класичний ланцюг подій. Одна конкретна, гіпотетична дія призвела б до одного конкретного результату. Це одноразова подія. Друга ситуація: «Якби вона дзвонила, я б відповідав». Обидва дієслова недоконаного виду. Тепер ми говоримо про регулярність або звичку. Це означає: кожного разу, коли вона б дзвонила, я б брав слухавку. Або: якби вона мала звичку дзвонити, я б мав звичку відповідати.

> *Let's consider two situations that might sound very similar in English, but have an entirely different meaning in Ukrainian. The first situation: "If she called, I would answer". Here we see two verbs of the perfective aspect. This is a classic chain of events. One specific, hypothetical action would lead to one specific result. This is a one-time event. The second situation: "If she called, I would answer". Both verbs are of the imperfective aspect. Now we are talking about regularity or habit. This means: every time she would call, I would pick up the phone. Or: if she had a habit of calling, I would have a habit of answering.*

You are not limited to symmetrical pairs, of course. You can mix aspects to describe a repeated condition leading to a sudden result, or a sudden condition triggering a continuous state. For example, you can describe a sudden achievement that creates a new reality.

**Якби я знайшов хорошу роботу, я б працював там роками.** — *If I found a good job, I would work there for years.*

Finding the job is a single, perfective event, while working there is an imperfective, continuous state. The aspect allows you to choreograph the hypothetical timeline with perfect clarity.

:::info
**Grammar box**
When mixing aspects in conditional sentences, analyze each clause independently. The condition might be a repeated process (imperfective), while the hypothetical reaction is a single decision (perfective). The flexibility of aspect allows for highly nuanced storytelling.
:::

For native English speakers, mastering the Ukrainian aspect system often requires a fundamental shift in perspective. English relies heavily on a complex system of tenses and auxiliary verbs—like "did," "was doing," "have done," or "had been doing"—to locate actions in time and describe their completeness. Ukrainian, while having fewer tenses, uses the lexical category of aspect to convey the shape of the action itself. The action is either a continuous line, which is imperfective, or a solid point, which is perfective.

Коли ви використовуєте англійське слово «did» у запитанні, ви часто запитуєте просто про факт події в минулому. Але українською мовою вам завжди потрібно зробити вибір. Якщо вчитель питає «Ти читав цей текст?», він використовує недоконаний вид. Його цікавить сам процес: чи виділили ви час на цю дію, чи знайомі ви з матеріалом загалом. Але якщо він питає «Ти прочитав цей текст?», він використовує доконаний вид. Тепер фокус змістився на результат: чи дійшли ви до кінця, чи виконали ви завдання повністю. Англійське запитання не передає цієї різниці. Тому вам завжди треба уявляти форму дії, перш ніж щось сказати.

> *When you use the English word "did" in a question, you often ask simply about the fact of an event in the past. But in Ukrainian, you always need to make a choice. If a teacher asks "Did you read this text?", they use the imperfective aspect. They are interested in the process itself: did you allocate time for this action, are you familiar with the material in general. But if they ask "Did you finish reading this text?", they use the perfective aspect. Now the focus has shifted to the result: did you reach the end, did you complete the task entirely. The English question does not convey this difference. Therefore, you always need to imagine the shape of the action before you say something.*

Prefixation plays a massive role in this shift of perspective. Adding a prefix to an imperfective verb does not just change its aspect; it often adds a specific nuance to the result. Consider the basic process of creating text.

**Писати.** — *To write (ongoing process).*

When you want to express writing something to completion, you add a prefix.

**Написати.** — *To write completely (result).*

If you need to finish writing something that was already started, you use a different prefix.

**Дописати.** — *To finish writing.*

And to rewrite something entirely, the prefix changes again.

**Переписати.** — *To rewrite.*

By understanding how prefixes alter the continuous line into a definitive point, you unlock the true expressive power of the Ukrainian verb system.

This module serves as your primary diagnostic checkpoint for verb aspect. Up to this point, you have encountered aspectual pairs in isolated grammar lessons and specific contexts. Now, you must integrate them into a unified system. To truly master the B1 level, you must be able to automatically select the correct aspect across five major linguistic contexts. Let's analyze each one to solidify your understanding.

The first context is **past narratives**. When telling a story, you are a director setting a scene. You use the imperfective aspect to paint the background. These are the actions that were ongoing, the weather, the habits, the continuous states that set the mood. 

**Світило сонце, люди гуляли парком.** — *The sun was shining, people were walking in the park.*

Then, you use the perfective aspect to advance the plot. These are the sequential events, the sudden actions that break the background state. 

**Раптом пішов дощ, і ми побігли додому.** — *Suddenly it started raining, and we ran home.*

If you cannot separate the background line from the event point, your stories will feel flat and confusing.

The second context involves **future plans**. The future tense forces you to distinguish between your intentions and your promised results. If you express a commitment of time without a guarantee, you use the imperfective aspect.

**Я буду готуватися до іспиту.** — *I will be preparing for the exam.*

You are declaring a process. You are committing your time to an activity, but you are not guaranteeing an outcome. However, if you are certain about the outcome, you must change the aspect.

**Я підготуюся до іспиту.** — *I will prepare for the exam.*

You are promising a completed result. You are stating that at a certain point in the future, the state of being prepared will be achieved. Choosing the wrong aspect here can make you sound evasive when you should sound confident.

:::tip
**Did you know?**
Many learners overuse the analytic future tense (буду + infinitive) because it feels structurally similar to the English "will + verb". While grammatically correct for processes, overusing it prevents you from making strong, result-oriented statements.
:::

The third context is **commands and requests**, which use the imperative mood. Here, aspect dictates the tone and precision of your instruction. The imperfective imperative is used for general advice, repeated actions, or polite invitations. 

**Заходьте, сідайте.** — *Come in, sit down.*

It focuses on the ongoing nature of the activity. The perfective imperative, conversely, is a specific, one-time command focused on a strict result. 

**Прочитайте цей документ до завтра.** — *Read this document by tomorrow.*

This demands a completed action. Using a perfective command when a general invitation is expected can sound unnecessarily harsh or bossy.

The fourth context is **negation**. As we explored earlier, negating an imperfective verb means the action did not happen at all, or you had no intention of doing it. 

**Я не читав.** — *I didn't read it.*

This shuts down the process entirely. Negating a perfective verb means you attempted the action or were expected to do it, but failed to reach the result. 

**Я не прочитав.** — *I didn't finish reading it.*

This acknowledges the expectation but denies the completion. This distinction is vital for accurate communication, especially when explaining mistakes or missed deadlines.

Finally, the fifth context is **conditionals**, which we covered at the beginning of this section. The choice between a hypothetical state (imperfective) and a hypothetical sudden change or one-time event (perfective) allows you to build complex imaginary scenarios. Matching aspects correctly in conditional clauses demonstrates a deep internalization of how Ukrainian time and consequence operate.

Let's bring all these rules together into a final, definitive summary. Whenever you are unsure which aspect to use, refer back to these core principles. 

### Підсумок
*   **Минулий час**: Недоконаний вид створює тло розповіді (процеси, звички, описи). Доконаний вид будує ланцюг подій (послідовні, завершені кроки, що рухають сюжет).
*   **Майбутній час**: Складна або складена форма (недоконаний вид) вказує на тривалість або намір дії в майбутньому. Проста форма (доконаний вид) обіцяє конкретний, завершений результат.
*   **Наказовий спосіб**: Недоконаний вид використовується для загальних інструкцій, порад або ввічливих запрошень. Доконаний вид необхідний для конкретних, цілеспрямованих команд.
*   **Заперечення**: Фраза «не читав» (недоконаний) означає, що дія взагалі не відбувалася. Фраза «не прочитав» (доконаний) означає, що дія не досягла фінального результату, хоча, можливо, й починалася.
*   **Умовний спосіб**: Вид дієслова повністю залежить від характеру гіпотетичної дії: чи це тривалий уявний стан, чи одноразова фантастична подія.

> *Summary*
> * *Past tense: The imperfective aspect creates the background of the narrative (processes, habits, descriptions). The perfective aspect builds the chain of events (sequential, completed steps that move the plot).*
> * *Future tense: The complex or compound form (imperfective aspect) indicates the duration or intention of an action in the future. The simple form (perfective aspect) promises a specific, completed result.*
> * *Imperative mood: The imperfective aspect is used for general instructions, advice, or polite invitations. The perfective aspect is necessary for specific, goal-oriented commands.*
> * *Negation: The phrase "didn't read [imperfective]" means that the action did not happen at all. The phrase "didn't finish reading [perfective]" means that the action did not reach the final result, although it might have started.*
> * *Conditional mood: The verb aspect depends entirely on the nature of the hypothetical action: whether it is a continuous imaginary state or a one-time fantastic event.*

### Самоперевірка (Діагностика)

Для повторення та закріплення матеріалу виконайте ці завдання. Це ваша контрольна робота:

1. Перекажіть свій минулий тиждень, чергуючи доконаний і недоконаний вид (мінімум 8 дієслів).
2. Складіть 3 видові пари наказів: загальна інструкція (недоконаний вид) vs конкретна команда (доконаний вид).
3. Поясніть різницю та результативність у парах: «Я не читав цю книжку» vs «Я не прочитав цю книжку».
4. Складіть 2 умовні речення з різним видом дієслова.

> *Self-check (Diagnostics)*
> *To review and consolidate the material, complete these tasks. This is your test:*
> *1. Retell your past week, alternating perfective and imperfective aspects (minimum 8 verbs).*
> *2. Make 3 aspectual pairs of commands: general instruction (imperfective) vs specific command (perfective).*
> *3. Explain the difference and resultativity in the pairs: "I didn't read this book" vs "I didn't finish reading this book".*
> *4. Make 2 conditional sentences with different verb aspects.*

*(За матеріалами: Литвінова Grade 7, Заболотний Grade 7, Авраменко Grade 7)*

<!-- INJECT_ACTIVITY: fill-in-past-aspect -->
<!-- INJECT_ACTIVITY: open-writing-aspect-check -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-aspect
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

**Level: B1 (Module 10)**

**Instructions in Ukrainian.** All activity types appropriate.


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
