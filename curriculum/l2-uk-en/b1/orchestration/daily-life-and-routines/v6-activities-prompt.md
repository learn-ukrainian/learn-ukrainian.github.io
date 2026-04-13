<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/daily-life-and-routines.yaml` file for module **7: Щоденне життя** (b1).

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

- `<!-- INJECT_ACTIVITY: fill-in-routine-verbs-complete-a-daily-routine-text-with-correct-reflexive-and-prefixed-verb-forms -->`
- `<!-- INJECT_ACTIVITY: sentence-builder-write-plans-and-schedules-using-conditional-forms-and-temporal-expressions -->`
- `<!-- INJECT_ACTIVITY: match-up-chores -->`
- `<!-- INJECT_ACTIVITY: error-correction-daily -->`
- `<!-- INJECT_ACTIVITY: quiz-grammar-choice -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete a daily routine text with correct verb forms (reflexive, prefixed,
    aspect)
  items: 12
  type: fill-in
- focus: Choose the correct Phase 3 grammar structure for daily life situations (conditional,
    imperative, passive)
  items: 12
  type: quiz
- focus: Match household chores to their descriptions using correct verb forms
  items: 12
  type: match-up
- focus: Write plans/schedules using якщо-conditionals and temporal expressions
  items: 12
  type: sentence-builder
- focus: 'Fix daily-life vocabulary errors: *стирати (→ прати), *пилесос (→ пилосос),
    wrong aspect'
  items: 12
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- помити посуд (to wash dishes)
- витирати пил (to dust)
- поспішати (to hurry)
- мандрувати (to travel, wander)
- розважатися (to entertain oneself, have fun)
- вирощувати (to grow — plants)
- бутерброд (sandwich)
- каша (porridge)
- електронна пошта (email)
- звіт (report)
- серіал (TV series)
- велосипед (bicycle)
required:
- розпорядок дня (daily routine/schedule)
- прокидатися (to wake up — reflexive)
- снідати / обідати / вечеряти (to have breakfast / lunch / dinner)
- прибирати (to clean up, tidy)
- пилососити (to vacuum)
- прати білизну (to do laundry — NOT *стирати)
- прасувати (to iron)
- виносити сміття (to take out the trash)
- готувати їжу (to cook food)
- 'займатися (to engage in, do — reflexive: займатися спортом)'
- запізнюватися (to be late — reflexive)
- встигати (to manage in time)
- відкладати (to postpone)
- вихідні (weekend — pluralia tantum)
- будильник (alarm clock)
- хатні справи (household chores)
- пошук роботи (job search)
- співбесіда (interview)
- робоче місце (workplace)
- колега (colleague)
- обов'язки (duties)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Мій день: ранок

Welcome to a new day in Ukraine. When we talk about daily life, we are essentially talking about the concept of **щоденне життя** (daily life) and personal habits. In Ukrainian, these daily routines are powered by reflexive verbs, which are verbs that indicate an action performed on oneself. To see how these verbs work in practice, we will follow a popular and engaging concept: a Ukrainian vlog. Imagine starting the day in the bustling heart of Kyiv, narrating every single step from the exact moment the alarm rings to stepping out the apartment door. This narrative approach allows us to see how native speakers naturally weave together verbs, times, and places in their everyday speech.

Зворотні дієслова є основою будь-якого ранкового розпорядку. Спочатку ми прокидаємося, коли дзвонить будильник, а потім підводимося з ліжка. Далі ми йдемо у ванну кімнату, де вмиваємося водою та зачісуємося перед дзеркалом. Усі ці дієслова закінчуються на частку «-ся», яка показує, що дія спрямована на саму людину. Якщо ми заберемо цю частку, значення кардинально зміниться: ми будемо вмивати когось іншого або зачісувати дитину.

> *Reflexive verbs are the foundation of any morning routine. First, we wake up when the alarm rings, and then we get up from bed. Next, we go to the bathroom, where we wash our face with water and comb our hair in front of the mirror. All these verbs end in the particle "-ся", which shows that the action is directed at the person themselves. If we remove this particle, the meaning will change drastically: we will be washing someone else or combing a child's hair.*

> — **Влогер:** Я прокидаюся, коли сонце тільки сходить, о пів на сьому. *(I wake up when the sun is just rising, at half past six.)*
> — **Марко:** Прокидайся, вже пізно! *(Wake up, it's already late!)*
> — **Влогер:** Я збираюся довше, бо ще зачісуюся. *(I take longer to get ready because I am still combing my hair.)*
> — **Марко:** Не забудь поснідати! Якщо встанеш раніше, ми встигнемо разом поїсти. *(Don't forget to have breakfast! If you get up earlier, we will manage to eat together.)*
> — **Влогер:** Добре, я вийду з ванної за п'ять хвилин. *(Okay, I will come out of the bathroom in five minutes.)*
> — **Марко:** Давай, бо я виходжу о восьмій. *(Come on, because I am leaving at eight.)*

Notice how the roommates use different verb aspects depending on their intention and the immediate context of the morning. When describing a regular daily habit, you must use the imperfective aspect because the action is seen as a continuous or repeating process without a specific end. For instance, you would use it to explain a regular, expected morning occurrence that happens every day.

«Зазвичай я снідаю гарячою кашею.» — *Usually I have hot porridge for breakfast.*

However, when talking about a specific planned action with a clear, successful result, the perfective aspect is strictly required. You would use it to indicate a completed, one-time action in the near future.

«Завтра я поснідаю значно раніше.» — *Tomorrow I will have breakfast much earlier.*

Зверніть увагу, що для інших прийомів їжі існують власні дієслова: вдень ми зазвичай обідаємо (have lunch), а ввечері — вечеряємо (have dinner).

Understanding this precise aspectual contrast is absolutely crucial for accurately planning your schedule, making promises, and discussing your daily habits with colleagues or friends.

Український сніданок може бути дуже різним, і це часто залежить від того, скільки у вас є вільного часу зранку. Традиційно багато людей готують гарячу кашу з ягодами, горіхами або медом, яка дає багато енергії на весь довгий день. Якщо ж ви дуже поспішаєте і не маєте часу на приготування їжі, можна швидко зробити звичайний бутерброд із сиром, маслом або ковбасою. Звісно, невіддільною частиною сучасного міського життя є міцна чорна кава або ароматний чай. У великих містах, таких як Київ чи Львів, молодь часто купує ці напої у кав'ярнях дорогою на роботу чи навчання.

:::tip
**Cultural note** — While traditional breakfasts might include heartier meals, the modern urban rhythm in cities like Kyiv often shifts toward a quick coffee and a sandwich on the go.
:::

Once breakfast is successfully finished, it is time to leave the house and face the day. Morning routines in a bustling modern city often involve a bit of a rush, so you will frequently hear people say that they need to hurry to avoid being late for their morning meetings. When it comes to the daily commute, Ukrainian efficiently uses the Instrumental case to describe the specific mode of transportation you choose. You do not use an extra preposition like "by" or "on" as you naturally might in English. Instead, you simply put the vehicle noun directly into the Instrumental case as you head to the office or university.

«Я їду трамваєм на роботу.» — *I am going to work by tram.*

«Вона їде автобусом до школи.» — *She is going to school by bus.*

«Ми їдемо поїздом в інше місто.» — *We are going to another city by train.*

Зазвичай мій розпорядок дня починається дуже рано, коли надворі ще досить тихо. Я прокидаюся о шостій ранку, відразу вимикаю будильник, швидко підводжуся та йду в душ. Там я довго вмиваюся прохолодною водою, щоб остаточно прокинутися, а потім ретельно чищу зуби. Після цього я повертаюся у свою кімнату, одягаюся, зачісуюся і уважно дивлюся у дзеркало. О пів на сьому я йду на кухню, де із задоволенням готую свій ранковий сніданок: варю каву та роблю великий бутерброд. Я ніколи не запізнююся на роботу, тому завжди дуже швидко збираюся. За чверть восьма я беру сумку і виходжу з дому. Я часто поспішаю, тому щодня їду на роботу швидкісним трамваєм.

<!-- INJECT_ACTIVITY: fill-in-routine-verbs-complete-a-daily-routine-text-with-correct-reflexive-and-prefixed-verb-forms -->

## Робочий день та навчання

After finishing your morning routine, the next phase of the day is usually dedicated to work or study. When describing your arrival at the office or university, Ukrainian relies heavily on prefixed verbs of motion. These prefixes add specific directional meaning to the base verb, allowing you to describe your commute and entry with precision. For example, the prefix **при-** indicates arrival, while the prefix **за-** suggests dropping by or entering a space for a short time.

Коли я нарешті приїжджаю на роботу, мій робочий день починається дуже активно. Спочатку я заходжу в офіс, вітаюся з усіма і сідаю за свій стіл. Дієслово «приїжджати» означає, що я успішно досяг свого місця призначення за допомогою транспорту. А слово «заходити» показує дію перетину порогу кімнати або будівлі пішки. Ці префікси допомагають точно описати кожен мій ранковий рух.

> *When I finally arrive at work, my workday begins very actively. First, I enter the office, greet everyone, and sit at my desk. The verb "приїжджати" means that I have successfully reached my destination using transport. And the word "заходити" shows the action of crossing the threshold of a room or building on foot. These prefixes help accurately describe every morning movement of mine.*

Once you are settled at your desk, the workday consists of various tasks that are also best described using specific prefixes. Prefixes in Ukrainian not only change the aspect of a verb but also add nuanced semantic layers to the action itself. The prefix **пере-** often implies doing something thoroughly or re-doing it, like checking information. The prefix **об-** suggests an action that encompasses or goes around a subject, such as discussing a topic from all sides. Meanwhile, the prefix **до-** indicates bringing an action to its absolute end or completion.

О дев'ятій годині я вмикаю комп'ютер і ретельно перевіряю електронну пошту. Префікс «пере-» тут підкреслює, що я переглядаю всі повідомлення дуже уважно. Потім ми з колегами обговорюємо наш план на день, розглядаючи всі можливі деталі. Префікс «об-» показує, що наша розмова охоплює всю тему з різних боків. Увечері я часто допрацьовую важливі документи, щоб завершити всі завдання.

In a professional environment, scheduling and asking for help require a polite and cooperative tone. You will frequently use conditional sentences to negotiate time. Real conditionals with **якщо** (if) help set practical conditions for future actions. When you need a favor, using the polite conditional question **Чи не могли б ви...?** (Could you...?) softens the request significantly, showing respect for your colleague's time.

> — **Олена:** Добрий день, Максиме! Чи не могли б ви допомогти мені з цим новим звітом? *(Good day, Maksym! Could you help me with this new report?)*
> — **Максим:** Привіт, Олено! Звісно, але зараз я трохи зайнятий. *(Hi, Olena! Of course, but I am a bit busy right now.)*
> — **Олена:** Нічого страшного. Коли ви будете вільні? *(No worries. When will you be free?)*
> — **Максим:** Якщо я закінчу писати свій звіт до обіду, я відразу допоможу вам. *(If I finish writing my report before lunch, I will help you right away.)*
> — **Олена:** Чудово! Тоді, якщо у вас буде час, давайте обговоримо це о другій годині. *(Great! Then, if you have time, let's discuss it at two o'clock.)*
> — **Максим:** Домовилися, так і зробимо. *(Agreed, we will do just that.)*

When discussing academic studies or official workplace procedures, Ukrainian employs verbal nouns, known as **віддієслівні іменники**. These are nouns formed directly from verbs, typically ending in **-ння** or **-ття**. Using verbal nouns elevates the register of your speech from casual conversation to a more formal, professional, or academic tone. For instance, instead of saying "I am learning", you might refer to the process of **навчання** (learning). Similarly, **вивчення** (studying) and **виконання** (execution) sound much more authoritative than their base verbs.

Університетське середовище або велика корпорація вимагають використання більш офіційної лексики. Наприклад, ми часто говоримо про навчання студентів або вивчення нового складного матеріалу. Слово «виконання» чудово підходить для опису процесу завершення робочих завдань або проєктів. Використання таких віддієслівних іменників робить вашу мову структурованою, логічною та професійною, що дуже важливо під час офіційних зустрічей.

To see how this register shift works in practice, consider how a student might describe their evening. In a casual chat with friends, a student would simply use a basic verb and a colloquial noun. However, in a more serious context, like explaining a schedule to a professor or writing a formal diary, verbal nouns are the appropriate choice.

У розмові з друзями студент може просто сказати: «Я роблю домашку, тому не можу піти гуляти». Це звучить дуже природно і просто. Але в офіційному контексті краще сказати: «Виконання домашнього завдання займає у мене багато часу кожного вечора». Тут іменник «виконання» підкреслює серйозний підхід до процесу та формальний тон висловлювання.

> *In a conversation with friends, a student can simply say: "I am doing my homework, so I can't go for a walk." This sounds very natural and simple. But in a formal context it is better to say: "The execution of homework takes a lot of my time every evening." Here the noun "виконання" emphasizes a serious approach to the process and the formal tone of the statement.*

:::info
**Grammar box** — Verbal nouns are highly productive in Ukrainian. You will encounter them constantly in news, academic texts, and business correspondence. They allow you to pack complex actions into a single noun phrase, often acting as the subject of a sentence.
:::

Building a strong professional vocabulary is essential for navigating the Ukrainian workplace. You need to know how to refer to your environment, your tasks, and the people around you. Key terms include **колега** (colleague), **звіт** (report), and **електронна пошта** (email). If you are looking for a job, you will definitely need to prepare for a **співбесіда** (interview). Finally, the physical or virtual space where you operate is your **робоче місце** (workplace).

Кожен сучасний працівник повинен тримати своє робоче місце в чистоті та порядку. Коли ви приходите в нову компанію, ви знайомитеся з колегами і починаєте працювати над першим звітом. Спілкування в офісі часто відбувається через електронну пошту, тому важливо вміти писати професійні листи. Пошук роботи часто забирає багато часу, а щоб отримати хорошу посаду, вам спочатку потрібно успішно пройти складну співбесіду з керівником.

Teamwork requires inclusive language that encourages collaboration without sounding demanding. Inclusive imperatives fulfill this role perfectly. Using **давайте** (let's) followed by a future tense verb is a standard way to propose a shared action. For movement, the special form **ходімо** (let's go) is highly natural. Additionally, when addressing your colleagues, especially in a formal or polite setting, you must always use the Vocative case to show respect and professionalism.

Наприкінці довгого робочого дня колеги часто пропонують одне одному трохи відпочити. Ви можете почути фрази на зразок: «Давайте вип'ємо кави» або «Ходімо на вулицю подихати свіжим повітрям». Це дуже ввічливий спосіб запросити інших приєднатися до вас. Звертаючись до колег, ми завжди використовуємо кличний відмінок: «Пане Олегу, давайте подивимося на ці цифри ще раз». Це створює атмосферу поваги та взаєморозуміння в колективі.

<!-- INJECT_ACTIVITY: sentence-builder-write-plans-and-schedules-using-conditional-forms-and-temporal-expressions -->

## Хатні справи та побут

Managing a home requires specific vocabulary, and when discussing chores, the aspect of the verb is crucial. The foundation of household maintenance is the verb pair **прибирати** (to clean up, imperfective) and **прибрати** (to clean up, perfective). You use the imperfective form to describe a habitual routine or a process that takes time. When you want to focus on the result—a clean room—you switch to the perfective form.

У кожній родині є свої правила щодо того, як часто потрібно прибирати квартиру. Наприклад, я прибираю свою кімнату щосуботи, тому що люблю чистоту. Це мій звичний ритуал, який займає кілька годин. Але якщо до мене несподівано приходять гості, я можу швидко прибрати у вітальні за десять хвилин. Тут важливий лише результат: чиста кімната перед приходом друзів.

> *Every family has its own rules regarding how often the apartment needs to be cleaned. For example, I clean my room every Saturday because I love cleanliness. This is my usual ritual that takes a couple of hours. But if guests unexpectedly come to me, I can quickly clean up in the living room in ten minutes. Here only the result is important: a clean room before the arrival of friends.*

Beyond general cleaning, daily life involves specific tasks that keep a household running smoothly. You will frequently need to wash dishes after meals and take out the trash at the end of the day. For keeping the floors and furniture clean, we use verbs like **пилососити** (to vacuum) and **витирати пил** (to dust).

It is also important to know the correct names for household appliances. A vacuum cleaner is called a **пилосос**, and an iron is a **праска**. Having the right tools makes every chore much easier and faster to complete.

Сучасна побутова техніка дуже допомагає нам швидко впоратися з домашніми обов'язками. Замість того, щоб довго підмітати підлогу віником, ми просто беремо пилосос. Після прання важливо ретельно випрасувати одяг, і для цього нам потрібна якісна праска. Розподіл цих дрібних завдань робить життя набагато простішим і залишає більше часу на відпочинок.

When families or roommates share a living space, they must negotiate who does what. This is where the imperative mood becomes essential. For direct requests to someone you address informally, use the second-person imperative, such as «вимий посуд» (wash the dishes) or «винеси сміття» (take out the trash). If you want to assign a task to a third party who is not directly part of the conversation, Ukrainian uses the particles **хай** or **нехай** followed by the present or future tense verb. 

:::info
**Grammar box** — The particles **хай** and **нехай** are used to create a third-person imperative. They are followed by a verb in the third person singular or plural. This structure is incredibly useful for delegating tasks or expressing a wish, such as «Нехай діти прибирають» (Let the children clean up). Both particles mean exactly the same thing, but «нехай» is slightly more emphatic.
:::

> — **Мама:** Олено, вимий посуд, будь ласка, після вечері. *(Olena, wash the dishes, please, after dinner.)*
> — **Олена:** Добре, мамо. А хто буде пилососити у вітальні? *(Okay, mom. And who will vacuum in the living room?)*
> — **Мама:** Нехай Марко пропилососить, це сьогодні його обов'язок. *(Let Marko vacuum, it's his duty today.)*
> — **Марко:** Без проблем. Але хай Олена спочатку витре пил з меблів. *(No problem. But let Olena dust the furniture first.)*
> — **Мама:** Домовилися. Якщо швидко впораєтеся, разом подивимося фільм. *(Agreed. If you manage quickly, we will watch a movie together.)*

A critical part of speaking natural Ukrainian is avoiding words borrowed from Russian in everyday domestic vocabulary. A common mistake learners make is confusing the verbs for washing clothes. In Ukrainian, to do laundry is **прати** (imperfective) or **випрати** (perfective), and laundry is **білизна**. Never use the word *стирати* for laundry. In Ukrainian, **стирати** means "to erase," like wiping chalk off a board.

:::tip
**Did you know?** — Using authentic Ukrainian household terms is an important part of linguistic decolonization. Always use **пилосос** (vacuum cleaner) instead of the incorrect *пилесос*, and **праска** (iron) instead of the Russian calque *утюг*.
:::

Коли накопичується багато брудного одягу, настає час прати білизну. Сучасні машини роблять цей процес дуже легким, але важливо правильно сортувати речі за кольором. Після того як білизна висохне, її потрібно акуратно попрасувати. Я завжди вмикаю улюблену музику, коли беру до рук праску, щоб зробити цю рутину приємнішою.

Once the chores are finished, you might want to report on the completed state of the house rather than focusing on who did the work. Ukrainian uses a special impersonal passive construction ending in **-но** or **-то** for this exact purpose. These forms are derived from passive participles and act as the predicate of a sentence without a formal subject. They perfectly highlight that a task is done and the result is achieved.

Перед приходом гостей господарі часто оглядають дім, щоб переконатися, що все готово. Вони з полегшенням бачать, що підлогу вимито, вікна відчинено для свіжого повітря, а на столі вже стоять красиві тарілки. Смачну вечерю приготовлено, весь посуд помито, і тепер можна просто чекати на дзвінок у двері. Ці безособові форми створюють відчуття спокою та завершеності після довгого дня прибирання.

The cultural context of household duties in Ukraine has evolved significantly over the past few decades. Traditionally, domestic chores and cooking were strictly divided by gender roles, with women taking on the vast majority of the work. However, modern Ukrainian families, especially in urban areas, embrace a much more egalitarian approach. Spouses now routinely share responsibilities, and both partners are expected to **впоратися** (to cope, to manage) with daily tasks.

Сьогодні багато молодих пар разом вирішують, хто буде готувати їжу, а хто піде до супермаркету за продуктами. Спільне виконання хатніх обов'язків допомагає партнерам краще розуміти одне одного і зберігати гармонію у стосунках. Наприклад, чоловік може чудово готувати складні страви, тоді як дружина бере на себе фінансове планування родини. Головне — це взаємоповага та готовність підтримати близьку людину в будь-якій побутовій ситуації.

<!-- INJECT_ACTIVITY: match-up-chores -->
<!-- INJECT_ACTIVITY: error-correction-daily -->

## Вільний час та вихідні

After a busy week of work or studying, the best part of your schedule is finally having free time. In Ukrainian, the weekend is called **вихідні** (weekend). It is crucial to remember that this word is a *pluralia tantum* noun, meaning it only exists in the plural form. You cannot have a single "weekend day" using this word in the singular; instead, you refer to the days themselves, like Saturday and Sunday. When discussing what you like to do, you will use various action verbs. Some people prefer to **малювати** (to paint), others like to read books, and those who seek adventure love to **мандрувати** (to travel) and explore new places.

Після напруженого тижня ми з нетерпінням чекаємо на вихідні. Кожен обирає заняття до душі: хтось любить малювати пейзажі, хтось віддає перевагу тиші та сідає читати новий роман, а хтось одразу збирає речі, щоб мандрувати містами. Головне — отримати позитивні емоції.

> *After a tense week, we look forward to the weekend with impatience. Everyone chooses an activity to their liking: someone loves to paint landscapes, someone prefers silence and sits down to read a new novel, and someone immediately packs things to travel to cities. The main thing is to get positive emotions.*

When planning the weekend, you will naturally use conditionals to discuss possibilities and desires. Real conditions use «якщо» (if) with the future tense, while unreal or hypothetical situations use «якби» (if only) with the conditional mood. Let's see how friends negotiate their plans.

> — **Остап:** Що ти плануєш робити на ці вихідні? *(What are you planning to do this weekend?)*
> — **Ганна:** Якщо буде гарна погода і світитиме сонце, ми підемо гуляти в парк. *(If the weather is nice and the sun is shining, we will go for a walk in the park.)*
> — **Остап:** А якби тобі зараз запропонували два квитки на вечірній концерт? *(And if you were offered two tickets to an evening concert right now?)*
> — **Ганна:** О, тоді я б із задоволенням пішла на концерт! *(Oh, then I would go to the concert with pleasure!)*
> — **Остап:** Якраз маю зайві квитки. Якщо хочеш, ходімо разом. *(I happen to have extra tickets. If you want, let's go together.)*
> — **Ганна:** Було б чудово! Дякую за запрошення. *(That would be great! Thank you for the invitation.)*

Many leisure activities are expressed using reflexive verbs, which end in the particle **-ся**. For instance, when you want to entertain yourself, you use **розважатися** (to have fun). Another common activity is **кататися на велосипеді** (to ride a bike), which literally translates to "rolling oneself on a bicycle." However, be careful with the most common verb for resting. 

:::info
**Grammar box** — The verb **відпочивати** (to rest, to relax) is never reflexive in Ukrainian. While some other Slavic languages add a reflexive particle to their equivalent of this word, doing so in Ukrainian is a severe grammatical error. You simply say «я відпочиваю» (I am resting).
:::

Коли настає вільний час, молодь часто йде в центр міста розважатися. Багато людей люблять займатися спортом, наприклад, влітку дуже популярно кататися на велосипеді лісовими стежками. Але іноді найкраще рішення — це залишитися вдома і спокійно відпочивати після складного дня.

You can also describe your hobbies using verbal nouns. These are nouns derived from verbs, typically ending in **-ння** or **-ття**, which sound more formal and abstract. Instead of saying "I like to read," you can say your favorite activity is **читання** (reading). The process of painting becomes **малювання** (painting), and traveling turns into **подорожування** (traveling). Using these nouns elevates your language when discussing your interests descriptively. 

Моє найулюбленіше заняття у вільний час — це фотографування природи. Я вважаю, що малювання допомагає розслабитися, а постійне читання розвиває уяву та збагачує словниковий запас. Таке занурення в хобі робить життя цікавішим.

To turn your weekend plans into reality, you must know how to invite others. The imperative mood is your primary tool. You can use inclusive forms like **Ходімо разом!** (Let's go together!) to suggest a shared activity. If you want to arrange a meeting point, you might say **Давайте зустрінемося** (Let's meet) and specify the location. You can also use polite conditionals, such as asking if someone would like to go to the cinema, to make invitations sound respectful.

Коли я хочу побачитися з друзями, я часто телефоную їм і кажу: «Ходімо сьогодні ввечері на виставку!». Якщо вони погоджуються, ми швидко домовляємося про час: «Давайте зустрінемося о шостій». Це дуже простий спосіб організувати спільне дозвілля.

Spending time outdoors is a huge part of Ukrainian weekend culture. Escaping the city noise is often referred to as going **за місто** (to the countryside). In the city, people flock to the **парк** (park) or stroll along the **набережна** (embankment). The goal is to spend time in nature, where you can actively walk or simply breathe fresh air.

Минулої неділі ми вирішили поїхати за місто, щоб побути подалі від галасливих вулиць. Ми довго гуляли лісом і могли вільно дихати свіжим повітрям. Ті, хто залишився в Києві, традиційно вийшли на набережну Дніпра.

Balancing work, chores, and hobbies requires good time management. By structuring your routine effectively, you ensure there is always room for relaxation. Scheduling helps prevent the stress of running late or forgetting important tasks.

Щоб не запізнюватися на зустрічі та встигати все, я ретельно планую свій час. Я завжди залишаю кілька вільних годин у розкладі для хобі, щоб ефективно відпочивати. Завдяки цьому мої вихідні завжди проходять цікаво.

> *To avoid being late for meetings and to manage everything on time, I carefully plan my time. I always leave a few free hours in the schedule for hobbies in order to rest effectively. Thanks to this, my weekends always pass interestingly.*

## Розпорядок дня: планування та поради

When life gets busy with studies, work, and hobbies, a structured approach is essential. A good **розклад** (schedule) helps you balance your daily responsibilities without feeling overwhelmed. Time management is not just about writing things down; it is about learning how to manage everything in time to complete your tasks. If you do not want to be constantly rushing to appointments, you must develop the habit of planning. The key is to avoid the temptation to **відкладати** (to postpone) important work until the last minute. By deciding to plan your days well in advance, you take control of your time instead of letting the day control you.

When friends ask for help with their schedules, you can offer advice using polite conditionals and direct imperatives. The conditional mood is perfect for hypotheticals, such as saying what you would do in their situation. You can start with a supportive and non-judgmental phrase.

**На вашому місці я б...** — *In your place I would...*

For example, you might suggest planning the day every evening to build a better routine.

**На вашому місці я б складав план на день щовечора.** — *In your place I would make a day plan every evening.*

If you want to be more direct and encourage specific actions, the imperative mood is your best tool. You can urge a friend to adjust their behavior with clear commands.

**Старайся прокидатися раніше.** — *Try to wake up earlier.*

**Не відкладай складні завдання на потім.** — *Do not postpone difficult tasks for later.*

Як встигати все: поради для сучасного студента. Життя студента часто буває хаотичним, але правильний розклад змінює все. Якщо ти хочеш успішно навчатися і мати час на відпочинок, обов'язково створи чіткий план на кожен день. На вашому місці я б починав ранок з найскладніших завдань. Старайся не відкладати важливі справи на вечір, бо тоді ти неодмінно втомишся і почнеш запізнюватися з дедлайнами. Хай кожен день має свою мету! Якщо ти правильно організуєш час, то зможеш досягати поставлених цілей набагато швидше. Завжди записуй свої плани у блокнот. Якби студенти менше сиділи в соціальних мережах, вони б встигали значно більше. Тому прокидайся вчасно, зосереджуйся на головному і не забувай регулярно відпочивати.

> *How to manage everything: advice for the modern student. A student's life is often chaotic, but a proper schedule changes everything. If you want to study successfully and have time for rest, be sure to create a clear plan for every day. In your place, I would start the morning with the most difficult tasks. Try not to postpone important matters to the evening, because then you will inevitably get tired and start being late with deadlines. Let every day have its goal! If you organize your time correctly, you will be able to reach your set goals much faster. Always write your plans down in a notebook. If students sat less on social networks, they would manage to do significantly more. Therefore, wake up on time, focus on the main thing, and do not forget to rest regularly.*

When reading the passage above, pay close attention to how different grammatical structures work together. Look for the reflexive verbs used for routines, such as **прокидатися** (to wake up), which are essential for describing daily habits. Identify the conditional sentences used for planning. The real conditional clause «Якщо ти хочеш успішно навчатися...» shows a realistic condition with a clear outcome, while the unreal conditional «Якби студенти менше сиділи...» reflects on a hypothetical scenario. Notice how the imperative forms drive the action of the text. Commands like **створи** (create) and **не відкладай** (do not postpone) are used to give direct, actionable advice to the reader.

:::info
**Grammar box** — When giving advice, the aspect of the imperative verb changes its tone. An imperfective imperative like «не відкладай» focuses on avoiding a general habit, while a perfective imperative like «створи» demands a specific, completed result.
:::

Mastering this vocabulary will transform how you talk about your daily life. Creating a **план на день** (day plan) is the foundation of good organization, allowing you to prioritize tasks effectively. When you structure your time well, you learn how to **встигати** (to manage in time) without sacrificing your personal life. Ultimately, these habits prevent you from the stress of having to **запізнюватися** (to be late) for important events. By combining these terms with conditional phrases and imperative commands, you can comfortably discuss schedules, offer meaningful advice to friends, and describe your own strategies for a highly productive day.

<!-- INJECT_ACTIVITY: quiz-grammar-choice -->

## Підсумок — Summary

This module serves as a practical culmination of the Phase 3 grammar concepts. You have seen how these rules are essential for discussing your daily routine, household chores, and weekend plans. By integrating these structures, you can describe your life with fluency and precision rather than relying on simple lists of actions.

У цьому модулі ми об'єднали всі ключові граматичні теми третьої фази. Ви побачили, як умовний спосіб допомагає планувати майбутнє за допомогою конструкцій з «якщо» та «якби». Наказовий спосіб став незамінним інструментом, щоб просити про допомогу в побуті або давати поради. Ми звернули увагу на віддієслівні іменники, такі як «навчання» чи «прибирання», які роблять мовлення більш формальним та структурованим. Крім того, ви навчилися описувати свій ранок, використовуючи зворотні дієслова. Пасивний стан із закінченнями -но та -то дозволив нам звітувати про виконані хатні справи, підкреслюючи сам результат. Нарешті, ми розглянули, як різні префікси допомагають точно передавати нюанси ваших щоденних дій.

> *In this module, we combined all the key grammatical topics of the third phase. You saw how the conditional mood helps plan the future using constructions with "if" and "if only". The imperative mood became an indispensable tool to ask for help with household chores or to give advice. We paid attention to verbal nouns, such as "studying" or "cleaning", which make speech more formal and structured. In addition, you learned to describe your morning using reflexive verbs. The passive voice with the endings -no and -to allowed us to report on completed household chores, emphasizing the result itself. Finally, we examined how different prefixes help to accurately convey the nuances of your daily actions.*

:::tip
**Did you know?** — Reviewing material contextually, such as describing your own daily life, is one of the most effective ways to move grammar from passive knowledge to active fluency. Do not just memorize rules; live them.
:::

Take a moment to evaluate your progress. If you find any of the following tasks difficult, it might be helpful to review the corresponding sections before moving forward. 

Запитайте себе: чи можу я описати свій ранок, використовуючи принаймні п'ять зворотних дієслів? Чи можу я запропонувати друзям план на вихідні за допомогою конструкції «Якщо..., то...»? Чи вмію я давати поради щодо планування часу, застосовуючи наказовий або умовний спосіб? Чи впевнено я розрізняю слова «прати» та «стирати» у контексті побуту? Якщо ваші відповіді ствердні, ви чудово впоралися. Попереду Контрольна робота 3, яка допоможе закріпити та перевірити всі знання, здобуті під час вивчення дієслівних конструкцій.

> *Ask yourself: can I describe my morning using at least five reflexive verbs? Can I propose a weekend plan to friends using the "If..., then..." construction? Do I know how to give advice on time management by applying the imperative or conditional mood? Do I confidently distinguish the words "to do laundry" (native) and "to wash" (Russianism) in the context of daily life? If your answers are affirmative, you have done a great job. Ahead is Test 3, which will help consolidate and check all the knowledge gained during the study of verb constructions.*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: daily-life-and-routines
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

**Level: B1 (Module 7)**

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
