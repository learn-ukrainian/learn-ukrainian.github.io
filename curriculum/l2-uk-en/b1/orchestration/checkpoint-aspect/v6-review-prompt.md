<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 10: Контрольна робота: вид дієслова (B1, B1.0 [Baselines & Aspect Mastery])
**Writer:** Gemini
**Word target:** 4000

## Plan (source of truth)

<plan_content>
module: b1-012
level: B1
sequence: 12
slug: checkpoint-aspect
version: '1.0'
title: "Контрольна робота: вид дієслова"
subtitle: "Діагностична перевірка аспектного вибору в усіх контекстах M01-M11"
focus: checkpoint
pedagogy: TTT
phase: "B1.0 [Baselines & Aspect Mastery]"
word_target: 4000
objectives:
  - "Learner can correctly choose between доконаний and недоконаний вид in past tense
    narratives, distinguishing тло (background) from послідовність подій (event chain)"
  - "Learner can choose appropriate aspect in future tense contexts: планована одноразова
    дія (pf — напишу) vs регулярна/тривала дія (impf — писатиму)"
  - "Learner can use correct aspect in наказовий спосіб: general instruction (impf —
    читайте!) vs specific single command (pf — прочитайте цю статтю!)"
  - "Learner can apply aspect rules in заперечення: не читав (impf — general negation)
    vs не прочитав (pf — expected result not achieved)"
  - "Learner can choose aspect in умовний спосіб and conditional sentences: Якби я
    знав (impf)... Якби я дізнався (pf)..."
dialogue_situations:
  - setting: 'Teacher reviewing homework with a student — aspect choice errors as
      diagnostic: Ти читав (impf — процес) цей текст? — Так, я прочитав (pf — результат)
      його вчора ввечері. — Добре. Тепер напиши (pf — одноразова дія) відповіді на
      запитання.'
    speakers:
      - Вчитель
      - Учень
    motivation: 'Aspect diagnostics in real academic setting: читав (impf, process
      question) vs прочитав (pf, result confirmation) vs напиши (pf imperative, single
      task).'
content_outline:
  - section: "Вид у минулому: тло і послідовність"
    words: 1000
    points:
      - "Diagnostic review of aspect in past tense (building on Литвінова Grade 7 p.30):
        Недоконаний вид as тло розповіді (narrative background) — ongoing, simultaneous,
        habitual actions: Надворі падав (impf) сніг. Діти гралися (impf) у дворі.
        Доконаний вид as подієвий ланцюг (event chain) — sequential completed actions:
        Він встав (pf), одягнувся (pf), вийшов (pf) з дому."
      - "Mixed aspect in connected narrative (Заболотний Grade 7 p.62): Коли ми снідали
        (impf — тло), зателефонувала (pf — подія) бабуся. Вона сказала (pf), що
        приїжджає (impf — план, що розгортається). Ми зраділи (pf) і почали (pf)
        готуватися (impf — початок тривалої дії). Key diagnostic: can the learner
        explain WHY each verb is perfective or imperfective?"
      - "Diagnostic exercise type 1 — aspect identification: given a narrative paragraph,
        learner identifies each verb as доконаний/недоконаний and explains the aspectual
        function (тло, подія, початок дії, результат). Texts drawn from M01-M11 themes
        (daily life, relationships, health, work)."
      - "Diagnostic exercise type 2 — aspect choice: learner completes a narrative
        choosing between verb pairs: Вчора я [читав/прочитав] книжку цілий вечір.
        Нарешті [закінчував/закінчив] останній розділ."
  - section: "Вид у майбутньому та наказовому"
    words: 1000
    points:
      - "Aspect in future tense (Литвінова Grade 7 p.44): Доконаний вид — single
        planned action with expected result: Завтра я напишу (pf) лист. Після обіду
        подзвоню (pf) мамі. Недоконаний вид — habitual, repeated, or duration-focused
        future: Щодня писатиму (impf) щоденник. Цілий тиждень готуватимуся (impf) до
        іспиту."
      - "Three future tense forms and aspect: Синтетичний майбутній (pf only): напишу,
        прочитаю. Аналітичний майбутній (impf): буду писати, буду читати. Синтетичний
        із -му (impf): писатиму, читатиму. Diagnostic: learner must choose the correct
        form based on aspect and context."
      - "Aspect in наказовий спосіб (Авраменко Grade 7 p.78): Недоконаний — general,
        repeated instruction, invitation: Читайте (impf) більше! Пишіть (impf) щодня!
        Сідайте (impf), будь ласка! Доконаний — specific, one-time command with expected
        completion: Прочитайте (pf) сторінку 45. Напишіть (pf) відповідь. Сядьте (pf)
        на це місце."
      - "Diagnostic exercise type 3 — imperative aspect: Learner chooses between impf
        and pf imperative in context. [Читай/Прочитай] цей текст до завтра (pf —
        specific task, deadline). [Читай/Прочитай] кожен день перед сном (impf —
        habitual advice). The distinction is about whether a SPECIFIC RESULT is expected."
  - section: "Вид і заперечення"
    words: 1000
    points:
      - "Aspect under negation — a key Ukrainian distinction (Авраменко Grade 7 p.57):
        Недоконаний вид — general negation, action did not take place at all: Я не читав
        (impf) цю книжку. (= never read it, general statement.) Доконаний вид — expected
        result was not achieved: Я не прочитав (pf) цю книжку. (= didn't finish it,
        though expected to.)"
      - "Negation patterns across contexts: Past: Він не дзвонив (impf — never called)
        vs Він не подзвонив (pf — didn't call though he should have). Future: Не
        буду читати (impf — refuse/won't do it generally) vs Не прочитаю (pf — won't
        manage to finish). Imperative: Не відчиняйте (impf — general prohibition,
        standard form for negative imperatives) vs Не відчиніть (pf — warning, 'don't
        accidentally open')."
      - "Critical rule: negative imperatives strongly prefer недоконаний вид in standard
        Ukrainian. Не чіпайте! (impf — don't touch, general). Не бігайте! (impf —
        don't run). The perfective negative imperative (Не впусти!) implies accidental
        or unintentional possibility — a warning, not a prohibition."
      - "Diagnostic exercise type 4 — negation and aspect: Learner explains the
        difference in meaning between pairs. Я не писав листа (impf — didn't write at
        all) vs Я не написав листа (pf — didn't finish). Не забувай! (impf — general
        reminder) vs Не забудь! (pf — specific warning about one thing)."
  - section: "Вид в умовному способі та підсумок"
    words: 1000
    points:
      - "Aspect in умовний спосіб (conditional mood): Недоконаний — hypothetical ongoing
        or repeated action: Якби я жив (impf) у Києві, я ходив би (impf) в театр
        щотижня. Доконаний — hypothetical single completed action: Якби я переїхав (pf)
        до Києва, я знайшов би (pf) нову роботу."
      - "Conditional sentences with aspect interplay: Якби вона подзвонила (pf —
        one-time event), я б відповів (pf). Якби вона дзвонила (impf — regularly), я
        б завжди відповідав (impf). The aspect reflects the NATURE of the hypothetical
        action: one-time result vs habitual process."
      - "Comprehensive diagnostic review — summary table across all contexts: минулий
        час (тло vs подія), майбутній час (план vs тривалість), наказовий спосіб
        (конкретна команда vs загальна інструкція), заперечення (загальне vs нереалізований
        результат), умовний спосіб (одноразове vs повторюване). Learner fills in the
        table with own examples from M01-M11 vocabulary."
      - "Самоперевірка: 1. Перекажіть свій минулий тиждень, чергуючи доконаний і
        недоконаний вид (мінімум 8 дієслів). 2. Складіть 3 пари наказів: загальна
        інструкція (impf) vs конкретна команда (pf). 3. Поясніть різницю: 'Я не читав
        цю книжку' vs 'Я не прочитав цю книжку'. 4. Складіть 2 умовні речення з
        різним видом дієслова."
vocabulary_hints:
  required:
    - "доконаний вид (perfective aspect — completed, result-oriented action)"
    - "недоконаний вид (imperfective aspect — ongoing, unbounded action)"
    - "видова пара (aspectual pair — e.g., писати/написати)"
    - "тло розповіді (narrative background — imperfective setting/scene)"
    - "послідовність подій (sequence of events — perfective event chain)"
    - "наказовий спосіб (imperative mood — commands and requests)"
    - "заперечення (negation — negative constructions with aspect)"
    - "умовний спосіб (conditional mood — hypothetical actions with би/б)"
    - "результативність (resultativity — focus on outcome, triggers perfective)"
    - "тривалість (duration — focus on process length, triggers imperfective)"
    - "діагностика (diagnostics — self-assessment of aspect mastery)"
    - "повторення (review/repetition — consolidation of learned material)"
    - "контрольна робота (test/assessment — formal diagnostic check)"
    - "минулий час (past tense — time frame for aspect practice)"
    - "майбутній час (future tense — time frame for aspect practice)"
  recommended:
    - "подієвий ланцюг (event chain — sequence of perfective actions)"
    - "загальне заперечення (general negation — imperfective, action didn't occur)"
    - "нереалізований результат (unrealized result — perfective negation, expected outcome
      not achieved)"
    - "заборона (prohibition — negative imperative, strongly prefers imperfective)"
    - "попередження (warning — perfective negative imperative for accidental actions)"
    - "синтетичний майбутній (synthetic future — perfective: напишу)"
    - "аналітичний майбутній (analytic future — imperfective: буду писати)"
activity_hints:
  - type: quiz
    focus: "Визначте вид дієслова та поясніть аспектну функцію (тло, подія, результат,
      тривалість) у реченнях з M01-M11"
    items: 12
  - type: fill-in
    focus: "Оберіть правильний вид дієслова у контексті: минулий, майбутній, наказовий
      спосіб, заперечення"
    items: 10
  - type: error-correction
    focus: "Знайдіть і виправте помилки у вживанні виду в реченнях: неправильний
      аспект у розповіді, наказі, запереченні"
    items: 8
  - type: group-sort
    focus: "Розподіліть дієслова за видом і контекстом: тло / подія / загальна інструкція
      / конкретна команда"
    items: 10
  - type: match-up
    focus: "З'єднайте видові пари та вкажіть контекст, де кожен вид доречний"
    items: 8
  - type: open-writing
    focus: "Напишіть текст із завданнями: 1) розповідь про минулий тиждень (тло + події),
      2) три пари наказів, 3) два умовні речення з різним видом"
    items: 8
connects_to:
  - "b1-001 (b1-baseline-past-present — aspect in past tense, reviewed here)"
  - "b1-002 (b1-baseline-future-aspect — aspect in future tense, reviewed here)"
  - "b1-010 (work-and-career — aspect in work narratives, tested here)"
  - "b1-023 (checkpoint-morphophonemics — next major checkpoint)"
prerequisites:
  - "b1-001 through b1-011 (all B1.0 modules covering aspect in various contexts)"
grammar:
  - "Вид дієслова в минулому часі: тло (недоконаний) vs послідовність подій (доконаний)"
  - "Вид у майбутньому: синтетичний (pf) vs аналітичний/синтетичний -му (impf)"
  - "Вид у наказовому способі: загальна інструкція (impf) vs конкретна команда (pf)"
  - "Вид і заперечення: загальне (impf) vs нереалізований результат (pf)"
  - "Вид в умовному способі: повторювана/тривала (impf) vs одноразова (pf) гіпотетична
    дія"
  - "Негативний наказовий спосіб: перевага недоконаного виду для заборон"
register: науково-навчальний
references:
  - title: "Литвінова Grade 7, p.30-47"
    notes: "Вид дієслова: доконаний/недоконаний — повний огляд, зв'язок виду і часу,
      аспектуальна стратегія в розповіді."
  - title: "Заболотний Grade 7, p.54-65"
    notes: "Дієслово: вид, часи, утворення видових пар, вибір виду в контексті."
  - title: "Авраменко Grade 7, p.57-78"
    notes: "Вид дієслова: таблиці видових пар, наказовий спосіб, особливі форми."
  - title: "Литвінова Grade 7, p.44"
    notes: "Зв'язок виду і часу: доконаний вид не має теперішнього часу, три форми
      майбутнього часу."

</plan_content>

## Generated Content

<generated_module_content>
## Вид у минулому: тло і послідовність

Welcome to the first major checkpoint of the B1 level. Reaching this stage means you have already encountered the most crucial and challenging feature of the Ukrainian verb system: aspect. At the B1 level, choosing between the **недоконаний вид** (imperfective aspect) and **доконаний вид** (perfective aspect) is no longer just about memorizing grammar rules or isolated vocabulary pairs. It becomes a powerful narrative tool. True proficiency requires you to use aspect to paint a picture for your listener, distinguishing clearly between the static background of a scene and the dynamic actions that drive a story forward. In this section, we will diagnose your ability to control the flow of time in past tense narratives. We will review how to set the scene using the imperfective aspect and how to build a chain of events using the perfective aspect. Let's ensure your foundation is solid before we move on to more complex structures. Aspect is the heartbeat of the Ukrainian language; mastering it will make your storytelling sound authentic and native-like.

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
<!-- INJECT_ACTIVITY: fill-in-past-aspect -->

## Вид у майбутньому та наказовому

Understanding the future tense in Ukrainian requires a fundamental shift in how you think about time and action. In English, you often rely on complex tense structures like "I will be doing" or "I will have done" to convey nuances of duration and completion. In Ukrainian, the future tense is surprisingly simple in its structure, but it heavily relies on the aspect of the verb to carry this meaning. For English speakers, the challenge is not memorizing new endings, but rather choosing the right verb from the aspectual pair to accurately map your intention. You must decide whether your future action is a prolonged process or a targeted result. Simply translating English future tenses without considering this distinction can cause confusion. If you do not clarify your intention, you risk sounding unnatural or miscommunicating your actual plans.

The Ukrainian future tense has three distinct grammatical forms, and they are strictly tied to the aspect of the verb. The perfective aspect, which focuses on the result, has only one form: the simple future. For example, you might use «напишу» or «прочитаю». Visually and grammatically, these look exactly like present tense verbs. However, because a perfective verb inherently describes a completed action, it cannot exist in the present moment. Adding personal endings automatically projects the result into the future. On the other hand, the imperfective aspect, which focuses on the process, has two interchangeable forms. You can use the compound future with the auxiliary verb «бути», such as «буду писати». Alternatively, you can use the complex future formed by adding a suffix to the infinitive, such as «писатиму». Both imperfective forms mean the exact same thing and are used to describe ongoing or repeated future actions.

В українській мові дієслова доконаного виду взагалі не мають форм теперішнього часу. Коли ви берете дієслово доконаного виду, наприклад «прочитати», і додаєте до нього особові закінчення, ви автоматично створюєте форму майбутнього часу: «я прочитаю», «ти прочитаєш». Це означає, що дія обов'язково завершиться і принесе конкретний результат у майбутньому.

> *In the Ukrainian language, perfective verbs do not have present tense forms at all. When you take a perfective verb, for example "to read completely", and add personal endings to it, you automatically create a future tense form: "I will read", "you will read". This means that the action will definitely be completed and will bring a specific result in the future.*

:::info
**Grammar box** — Three forms of the future tense.
The perfective aspect uses only the synthetic future (**синтетичний майбутній**: «напишу», «прочитаю») to focus on the final result. The imperfective aspect uses either the analytic future (**аналітичний майбутній**: «буду писати») or the uniquely Ukrainian complex form with a suffix («писатиму») to focus on the process.
:::

How do you choose between these forms in real life? It comes down to your intention: planned result versus habitual duration. When you say «Завтра я напишу лист», you are making a commitment to a specific, one-time action. This action will have a tangible outcome, like a finished letter. The perfective aspect is driven by this goal. However, if your focus is on a routine, a habit, or how you will spend your time, you must switch to the imperfective aspect. Saying «Щодня писатиму щоденник» emphasizes the repetitive nature of the action, without focusing on completing any single entry. Contextual trigger words often dictate this choice. Words like «кожного дня», «часто», «довго», or «завжди» naturally pair with the imperfective future because they describe duration or repetition. Conversely, words like «завтра», «до вечора», or «раптом» usually signal the need for the perfective future.

Якщо ви хочете пообіцяти комусь допомогу і гарантувати результат, вам потрібен доконаний вид. Ви кажете: «Я допоможу тобі завтра вранці», і людина знає, що проблема буде вирішена. Якщо ж ви кажете: «Я допомагатиму тобі щодня», ви пропонуєте тривалий процес підтримки, але не обіцяєте миттєвого вирішення конкретної задачі.

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
<!-- INJECT_ACTIVITY: error-correction-imperative -->

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

## Вид в умовному способі та підсумок

The conditional mood in Ukrainian, known as the **умовний спосіб**, allows us to talk about hypothetical situations, desires, or events that depend on a specific condition. Just like in the past and future tenses, the choice of aspect here is not random. It strictly follows the fundamental logic of Ukrainian verbs. Are you imagining a process, a state, a repeated action, or are you visualizing a single, completed event with a clear result? When you use the imperfective aspect in a conditional sentence, you are setting up a hypothetical background or describing a continuous state of being. When you use the perfective aspect, you are describing a hypothetical jump from one state to another. It represents a sudden change or a completed achievement that triggers another event.

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

This module serves as your primary diagnostic checkpoint for verb aspect. Up to this point, you have encountered aspectual pairs in isolated grammar lessons and specific contexts. Now, you must integrate them into a unified system. To truly master the B1 level, you must be able to automatically select the correct aspect across five major linguistic battlegrounds. Let's analyze each one to solidify your understanding and ensure you are ready for advanced communication.

The first battleground is **past narratives**. When telling a story, you are a director setting a scene. You use the imperfective aspect to paint the background. These are the actions that were ongoing, the weather, the habits, the continuous states that set the mood. 

**Світило сонце, люди гуляли парком.** — *The sun was shining, people were walking in the park.*

Then, you use the perfective aspect to advance the plot. These are the sequential events, the sudden actions that break the background state. 

**Раптом пішов дощ, і ми побігли додому.** — *Suddenly it started raining, and we ran home.*

If you cannot separate the background line from the event point, your stories will feel flat and confusing.

The second battleground involves **future plans**. The future tense forces you to distinguish between your intentions and your promised results. If you express a commitment of time without a guarantee, you use the imperfective aspect.

**Я буду готуватися до іспиту.** — *I will be preparing for the exam.*

You are declaring a process. You are committing your time to an activity, but you are not guaranteeing an outcome. However, if you are certain about the outcome, you must change the aspect.

**Я підготуюся до іспиту.** — *I will prepare for the exam.*

You are promising a completed result. You are stating that at a certain point in the future, the state of being prepared will be achieved. Choosing the wrong aspect here can make you sound evasive when you should sound confident.

:::tip
**Did you know?**
Many learners overuse the analytic future tense (буду + infinitive) because it feels structurally similar to the English "will + verb". While grammatically correct for processes, overusing it prevents you from making strong, result-oriented statements.
:::

The third battleground is **commands and requests**, which use the imperative mood. Here, aspect dictates the tone and precision of your instruction. The imperfective imperative is used for general advice, repeated actions, or polite invitations. 

**Заходьте, сідайте.** — *Come in, sit down.*

It focuses on the ongoing nature of the activity. The perfective imperative, conversely, is a specific, one-time command focused on a strict result. 

**Прочитайте цей документ до завтра.** — *Read this document by tomorrow.*

This demands a completed action. Using a perfective command when a general invitation is expected can sound unnecessarily harsh or bossy.

The fourth battleground is **negation**. As we explored earlier, negating an imperfective verb means the action did not happen at all, or you had no intention of doing it. 

**Я не читав.** — *I didn't read it.*

This shuts down the process entirely. Negating a perfective verb means you attempted the action or were expected to do it, but failed to reach the result. 

**Я не прочитав.** — *I didn't finish reading it.*

This acknowledges the expectation but denies the completion. This distinction is vital for accurate communication, especially when explaining mistakes or missed deadlines.

Finally, the fifth battleground is **conditionals**, which we covered at the beginning of this section. The choice between a hypothetical state (imperfective) and a hypothetical sudden change or one-time event (perfective) allows you to build complex imaginary scenarios. Matching aspects correctly in conditional clauses demonstrates a deep internalization of how Ukrainian time and consequence operate.

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

<!-- INJECT_ACTIVITY: open-writing-aspect-check -->
</generated_module_content>

**PIPELINE NOTE — Word count: 5392 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 773 words | Not found: 1 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Києва — NOT IN VESUM

All 773 other words are confirmed to exist in VESUM.

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
