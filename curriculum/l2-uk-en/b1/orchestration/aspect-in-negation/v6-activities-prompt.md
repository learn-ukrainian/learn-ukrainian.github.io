<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-in-negation.yaml` file for module **8: Вид і заперечення** (b1).

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

- `<!-- INJECT_ACTIVITY: quiz-aspect-pragmatics -->`
- `<!-- INJECT_ACTIVITY: fill-in-factual-denial -->`
- `<!-- INJECT_ACTIVITY: group-sort-negation-types -->`
- `<!-- INJECT_ACTIVITY: error-correction-negated-aspect -->`
- `<!-- INJECT_ACTIVITY: match-up-pragmatic-context -->`
- `<!-- INJECT_ACTIVITY: open-writing-progress-report -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose не + impf or ще не + pf based on context — factual denial vs pending
    expectation
  items: 10
  type: quiz
- focus: Complete negated sentences with the correct aspect form based on the speaker's
    attitude (neutral fact vs 'not yet')
  items: 8
  type: fill-in
- focus: Sort negated sentences into загальне заперечення (не + impf) and незавершене
    очікування (ще не + pf)
  items: 10
  type: group-sort
- focus: Find and correct aspect errors in negated sentences (*ще не читав → ще не
    прочитав; *не написав without context → не писав)
  items: 6
  type: error-correction
- focus: Match pragmatic situations (boss asking about tasks, friend asking about
    books, teacher checking homework) to the correct negation pattern
  items: 8
  type: match-up
- focus: Write a dialogue where one person asks about progress on several tasks —
    use не + impf for unstarted tasks and ще не + pf for pending tasks
  items: 6
  type: open-writing


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

- pos: noun:n
  translation: negation (denial of an action)
  word: заперечення
- pos: noun phrase
  translation: general negation (не + impf — factual denial)
  word: загальне заперечення
- pos: noun phrase
  translation: expected completion (ще не + pf — pending result)
  word: очікуване завершення
- pos: adv/part
  translation: yet, still (signals pending expectation with pf negation)
  word: ще
- pos: noun:m
  translation: fact (не + impf states a fact of non-occurrence)
  word: факт
- pos: noun:n
  translation: expectation (ще не + pf implies an expected outcome)
  word: очікування
- pos: noun:f
  translation: pragmatics — how context shapes meaning
  word: прагматика
- pos: verb:impf
  translation: to discuss (impf — не обговорювали = didn't discuss)
  word: обговорювати
- pos: verb:pf
  translation: to discuss (pf — ще не обговорили = haven't discussed yet)
  word: обговорити
- pos: verb:impf
  translation: to decide (impf — process of deciding)
  word: вирішувати
- pos: verb:pf
  translation: to decide (pf — ще не вирішили = haven't decided yet)
  word: вирішити
- pos: verb:impf
  translation: to answer/respond (impf)
  word: відповідати
- pos: verb:pf
  translation: 'to answer/respond (pf — result: answer given)'
  word: відповісти
- pos: verb:pf
  translation: to finish washing (pf — ще не домив)
  word: домити
- pos: verb:pf
  translation: to finish reading (pf — ще не дочитав)
  word: дочитати
- pos: verb:pf
  translation: to finish doing (pf — pending completion)
  word: доробити
- pos: adj
  translation: neutral (не + impf = neutral factual negation)
  word: нейтральний
- pos: adj
  translation: unfinished, incomplete (ще не + pf context)
  word: незавершений
- pos: noun:m
  translation: intention (ще не implies intention to complete)
  word: намір


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Тест: що ви заперечуєте?

By now, you are familiar with the concept of aspect pairs in the Ukrainian language. You know that **робити** (to do) describes an ongoing process, while **зробити** (to get done) focuses on the final result. However, many learners at this stage encounter a frustrating plateau when they try to combine aspect with negation. Let us look at a common situation. Imagine someone asks you a simple question: «Ти прочитав статтю?». You have two seemingly straightforward ways to say no. You could say, «Ні, не читав.» Alternatively, you might say, «Ні, ще не прочитав.» If you check a grammar book or a dictionary, both sentences are grammatically perfect. They are both translated into English as a form of "I did not read it" or "I haven't read it." Yet, to a native Ukrainian speaker, they signal completely different intentions, attitudes, and levels of progress regarding that article. One closes the conversation, while the other leaves a door wide open.

Уся справа в тому, що ми називаємо прагматичним зсувом. В українській мові заперечення не просто констатує відсутність якоїсь дії. Воно дозволяє мовцю вибрати, яку саме грань цієї відсутності він хоче підкреслити для свого співрозмовника. Коли ви кажете фразу «Я не снідав», ви просто констатуєте нейтральний історичний факт. Це означає, що сніданку не було, і на цьому крапка. Можливо, ви взагалі не снідаєте ніколи, або просто не були голодні сьогодні вранці. Але якщо ви зміните форму і скажете «Я ще не поснідав», ситуація кардинально змінюється. Ця маленька частка «ще» разом із доконаним видом перетворює нейтральний факт на невиконане зобов'язання. Ви ніби кажете, що сніданок був у вашому списку справ на сьогодні, ви маєте чіткий намір поїсти, але просто трохи запізнюєтеся з графіком. Ваше ставлення до відсутності сніданку зовсім інше, і ваш співрозмовник це одразу відчуває.

> *The whole point is what we call a pragmatic shift. In the Ukrainian language, negation does not simply cancel an action, rendering it invalid. Negation allows the speaker to choose exactly which facet of this non-action they want to highlight for their interlocutor. When you say the phrase "Я не снідав", you are simply stating a neutral historical fact. It means that there was no breakfast, and that is the end of it. Perhaps you never eat breakfast at all, or you just were not hungry this morning. But if you change the form and say "Я ще не поснідав", the situation changes radically. This small particle "ще" together with the perfective aspect turns a neutral fact into an unfulfilled obligation. It is as if you are saying that breakfast was on your to-do list for today, you have a clear intention to eat, but you are just running a little late with your schedule. Your attitude toward the absence of breakfast is completely different, and your interlocutor feels it immediately.*

Now we are going to set up a diagnostic test to see how well you intuitively grasp this difference. In the following exercise, you will need to rely on your intuition about social context and expectations. Negation choices are rarely about strict grammar rules; they are about understanding what the other person expects to hear. Think about the difference between a boss asking for a quarterly report and a friend casually asking about a random movie they saw last week. The boss expects the report to be finished, meaning the action has a pending deadline. The friend simply wants to know if you share a common experience, with no pressure or deadline attached. The social context forces an aspect choice because you must respond to the underlying expectation, not just the literal words of the question. As you take this test, ask yourself: is the speaker denying a simple fact, or are they apologizing for a delayed result?

<!-- INJECT_ACTIVITY: quiz-aspect-pragmatics -->

Let us do a detailed analysis of the test results you just completed. What you were actually practicing is the concept of speech acts. In Ukrainian, combining negation with the imperfective aspect creates a speech act we can call a statement of fact. You are objectively stating that a process did not occur. However, combining negation with the perfective aspect and the word **ще** (yet) creates a completely different speech act: an incomplete expectation. Let us contrast two common phrases. If you say «Я не бачив цей фільм», you are making a factual statement. You did not see it, and you are not necessarily planning to watch it tonight. But if you say «Я ще не подивився цей фільм», you are signaling that the movie is on your watchlist. You fully intend to watch it, and you expect that the action will be completed in the future.

:::info
**Grammar box** — Using **не** with the imperfective aspect creates a neutral statement of fact (the action did not happen). Using **ще не** with the perfective aspect creates an incomplete expectation (the action has not happened *yet*, but is expected to).
:::

Детально розберімо ще один класичний приклад — діалог про обід. Уявіть, що ваша колега Ольга запитує: «Ти вже обідав?». У Михайла є два варіанти відповіді. Перший варіант: «Ні, не обідав». Це звучить нейтрально. Ольга розуміє, що Михайло просто констатує факт. Можливо, він зараз не голодний і взагалі не планує йти в їдальню. Другий варіант: «Ще не пообідав». Ця фраза миттєво змінює те, як Ольга сприймає графік Михайла. Вона тепер знає, що він дуже зайнятий, але він точно планує поїсти пізніше. Ці два короткі слова повністю керують очікуваннями співрозмовника. Вони показують, чи дія скасована назавжди, чи вона просто поставлена на паузу і чекає свого часу.

> *Let us analyze another classic example in detail — the lunch dialogue. Imagine your colleague Olha asks: "Ти вже обідав?". Mykhailo has two response options. Option one: "Ні, не обідав". This sounds absolutely neutral. Olha understands that Mykhailo is simply stating a fact. Perhaps he is not hungry right now and does not plan to go to the cafeteria at all. Option two: "Ще не пообідав". This phrase instantly changes how Olha perceives Mykhailo's schedule. She now knows that he is very busy, but he definitely plans to eat later. These two short words completely manage the interlocutor's expectations. They show whether the action is permanently canceled or whether it is just paused and waiting for its time.*

This brings us to the conclusion of our initial testing phase. By now, you should start feeling the pragmatic weight behind your choice of aspect in negative sentences. There is one more crucial detail to keep in mind as we move forward. Using the perfective aspect with negation, but without the word **ще**, is actually quite rare and highly marked in everyday speech. If someone says «Ти не написав звіт!» without the softening effect of **ще**, it usually sounds like a direct accusation or a highlighted failure. It translates more closely to "You failed to write the report!" rather than a simple denial of an action. Understanding these emotional and contextual layers is what separates a proficient learner from an advanced speaker. This sets the stage for the formal rules we will explore in the next sections, where we will break down exactly how to construct and use these powerful negative pairs.

## Не + недоконаний: загальне заперечення

Коли вам потрібно просто сказати, що певна дія не відбулася, українська мова використовує граматичну конструкцію, яка називається «загальне заперечення». Як зазначається в шкільному підручнику української мови О. Заболотного для 7 класу, формула цього заперечення є надзвичайно простою: заперечна частка **не** поєднується з дієсловом недоконаного виду. Ця комбінація створює нейтральний патерн, який слугує стандартом для опису факту ненастання події. Використовуючи таку конструкцію, ви не додаєте жодного емоційного забарвлення, не шукаєте виправдань і не робите жодних натяків на ваші майбутні наміри. Наприклад, коли ви кажете «Він не вчив іспанську», ви просто констатуєте історичний факт. Тут немає жодного підтексту про те, що він повинен був її вчити, або що він провалив іспит через свою лінь. Так само фраза «Ми не обговорювали це питання» є чітким і професійним способом сказати, що розмова на цю тему просто не відбулася. Недоконаний вид тут виконує роль відстороненого спостерігача, який лише фіксує відсутність активності.

Логіка використання недоконаного виду для нейтрального заперечення є дуже глибокою і стає зрозумілою, якщо подумати про саму природу будь-якої дії. Як ми знаємо, доконаний вид завжди фокусується на результаті, на успішному завершенні або досягненні мети. Але якщо дія взагалі ніколи не відбувалася, то логічно, що ніякого результату просто не існує, і про нього неможливо говорити. Тому мовець автоматично обирає недоконаний вид, який описує сам процес у його найширшому розумінні. Наприклад, коли ви кажете «Вона не телефонувала», ви констатуєте той факт, що телефон не дзвонив, і процес розмови навіть не починався. Це нейтральне підтвердження того, що подія була відсутня у вашому просторі та часі. Ви не аналізуєте причини її мовчання і не оцінюєте наслідки, а лише фіксуєте порожнечу на місці очікуваного дзвінка.

> *The logic of using the imperfective aspect for neutral negation is very deep and becomes absolutely clear if you think about the very nature of any action. As we know, the perfective aspect always focuses on the result, on the successful completion or achievement of a goal. But if the action never happened at all, then it is logical that no result simply exists, and it is impossible to talk about it. Therefore, the speaker automatically chooses the imperfective aspect, which describes the process itself in its broadest sense. For example, when you say "Вона не телефонувала" (She didn't call), you are stating the fact that the phone did not ring, and the conversation process did not even begin. This is a neutral confirmation that the event was absent in your space and time. You are not analyzing the reasons for her silence and are not evaluating the consequences, but only recording the void in place of the expected call.*

Ця сама фундаментальна логіка акценту на «процесі» чудово пояснює, чому заперечення в теперішньому часі завжди вимагає недоконаного виду. За своїм граматичним визначенням, теперішній час в українській мові описує дії, які розгортаються саме зараз, тривалі стани або загальні щоденні звички. Оскільки дієслова доконаного виду жорстко прив'язані до завершених результатів, вони взагалі не мають форми теперішнього часу. Ви фізично не можете сказати одним словом, що ви просто зараз отримуєте фінальний результат. Тому будь-яке твердження про те, що не відбувається в даний момент, або що взагалі ніколи не відбувається, має спиратися на недоконаний вид. Коли ви говорите «Я не розумію», ви описуєте свій поточний, безперервний стан нерозуміння інформації. Це ваша реальність у момент мовлення. Аналогічно, фраза «Він не працює» описує поточний факт його безробіття або його тимчасову бездіяльність саме сьогодні. Незалежно від того, чи заперечуєте ви універсальну істину, чи щоденну звичку, як-от «Вона не їсть м'ясо», недоконаний вид залишається вашим єдиним вибором. Він природно обслуговує всі можливі ситуації, де тривала дія просто відсутня.

:::info
**Граматичне правило** — Теперішній час існує виключно для дієслів недоконаного виду. Тому щоразу, коли ви заперечуєте дію, яка відбувається *прямо зараз* або є *загальною звичкою*, ви повинні використовувати **не** з недоконаним дієсловом. Дієслова доконаного виду можуть існувати лише в минулому та майбутньому часах.
:::

Концепція загального заперечення відіграє критично важливу роль у формуванні ввічливих запитань в українській мові. Використання недоконаного виду робить ваше запитання значно м'якшим і набагато менш агресивним, оскільки ви запитуєте про загальний факт, а не вимагаєте негайного звіту про конкретний результат. Саме тому фраза «Ви не бачили моїх ключів?» є найбільш стандартним і ввічливим способом звернутися по допомогу до знайомого чи колеги. Ви лише цікавитеся, чи відбувався сам процес візуального контакту з вашими речами протягом дня. Людина може легко і без стресу відповісти «Ні, не бачив», і розмова на цьому спокійно завершиться. Натомість запитання «Ти не знайшов мої ключі?» з дієсловом доконаного виду звучить як пряма претензія або роздратування. Воно створює сильний психологічний тиск, ніби співрозмовник мав прямий обов'язок шукати ваші речі і тепер повинен відзвітувати про успішне виконання цього завдання.

> *The concept of general negation plays a critically important role in forming polite questions in the Ukrainian language. Using the imperfective aspect makes your question significantly softer and much less aggressive, because you are asking about a general fact, and not demanding an immediate report on a specific result. That is exactly why the phrase "Ви не бачили моїх ключів?" (Haven't you seen my keys?) is the most standard and polite way to ask an acquaintance or colleague for help. You are only wondering whether the process of visual contact with your belongings occurred during the day. The person can easily and without stress answer "Ні, не бачив" (No, haven't seen them), and the conversation will calmly end there. In contrast, the question "Ти не знайшов мої ключі?" (Didn't you find my keys?) with a perfective verb sounds like a direct complaint or irritation. It creates strong psychological pressure, as if the interlocutor had a direct obligation to look for your things and now must report on the successful completion of this task.*

Окрім базової ввічливості, комбінація частки **не** з недоконаним видом виконує дуже важливу стратегічну функцію в спілкуванні. Вона надійно захищає мовця від небажаних зобов'язань. Ми називаємо цю комунікативну тактику «нейтральною позицією». Описуючи відсутність дії як загальний, історичний факт, ви уникаєте будь-яких обіцянок щодо майбутнього. Уявіть ситуацію, коли викладач запитує студента: «Ти читав цю книжку?». Якщо студент відповідає: «Я не читав», це є прямим і закритим визнанням факту. Він стверджує, що процес читання не відбувся в минулому, і на цьому крапка. Така відповідь не містить виправдань і жодним чином не натякає на те, що студент планує прочитати цю книжку завтра чи взагалі коли-небудь. Вона просто остаточно закриває питання про минулу подію. Це робить недоконаний вид неймовірно корисним інструментом для встановлення особистих комунікативних кордонів. Коли ви його використовуєте, ви повідомляєте співрозмовнику, що ця дія наразі повністю знята з порядку денного. Ви демонструєте, що не збираєтеся вести переговори про те, коли вона нарешті буде завершена, а просто холоднокровно констатуєте сухі факти.

<!-- INJECT_ACTIVITY: fill-in-factual-denial -->

Загальне заперечення також є незамінним інструментом, коли нам потрібно описати довготривалі стани або комплексні життєві ситуації, які так і не стали нашою реальністю. Недоконаний вид чудово охоплює весь період часу, протягом якого певна подія чи діяльність була відсутня. Розглянемо різницю між двома дуже схожими на перший погляд твердженнями. Речення «Він не жив у Києві» описує широку історичну панораму. Ця людина ніколи не мала такого довготривалого досвіду, цей процес був відсутній у її біографії. Це загальний життєвий факт, який характеризує її минуле загалом. Натомість фраза «Він не переїхав у Київ» фокусується лише на одній конкретній точці в часі та вказує на те, що певний очікуваний результат або запланований крок так і не відбувся. Можливо, він активно планував переїзд, але в останній момент його плани раптово змінилися. Використовуючи форму «не жив», ви охоплюєте цілі роки чи навіть десятиліття одним єдиним словом, ефективно підкреслюючи стабільність і тривалість цього стану відсутності. Це робить вашу розповідь більш плавною, дозволяючи слухачеві побачити значно ширшу картину життя.

Щоб ще краще орієнтуватися у виборі правильного виду для загального заперечення, варто звертати увагу на спеціальні слова-маркери. В українській мові існують певні прислівники, які майже автоматично вимагають використання недоконаного виду в заперечних реченнях. Вони працюють так, оскільки постійно підкреслюють регулярність або абсолютну відсутність дії. Найсильнішими з таких маркерів є слова «ніколи» та «взагалі». Якщо ви говорите «Я ніколи не купував такі дорогі речі» або «Вона взагалі не дивилася телевізор», ви описуєте глобальну відсутність досвіду. Тому доконаний вид тут буде недоречним. Так само, коли ви заперечуєте регулярність дії за допомогою слова «часто», ви констатуєте відсутність повторюваного процесу. Наприклад, ви можете сказати: «Ми не часто гуляли в цьому парку». Ці маркери слугують для вас надійними і дуже помітними підказками. Вони сигналізують, що йдеться не про одиничну невдачу чи скасований план, а про широку, загальну картину світу. У цій картині світу певна діяльність просто не знайшла свого місця.

<!-- INJECT_ACTIVITY: group-sort-negation-types -->

## Ще не + доконаний: очікуване завершення

When we negate an action in Ukrainian, we are not just stating a cold truth about the world; we are often expressing our relationship to that action. This brings us to the "Pending Result" pattern, which is arguably the most common way to use perfective verbs with negation. As textbook author Lytvynova (Grade 7, p. 38) explains, the construction **ще не** combined with a perfective verb signals an expected completion. You use this pattern when a result has not been achieved at the current moment, but the speaker expects, intends, or anticipates that it will be finished soon. For example, if someone asks about a novel you are reading, saying **«Я ще не прочитав цю книжку»** (I haven't finished reading this book) means you are still in the middle of it, and the final result is pending. You are not denying the process of reading; in fact, you are confirming it. You are simply stating that the perfective outcome—the completed reading—has not yet arrived. It is a promise of a future result wrapped in a present negation.

```markdown
:::info
**Grammar box**
The combination of **ще не** (not yet) and a perfective verb is your default tool for managing expectations. It tells your listener: "I know this is supposed to be done, and it's on my radar."
:::
```

Магія слова **ще** полягає в тому, що воно працює як психологічний місток між минулою невдачею та майбутнім успіхом. Без цього маленького прислівника доконаний вид у запереченні часто звучить як суворий вирок або остаточна констатація поразки. Наприклад, фраза **«Він не склав іспит»** означає, що спроба відбулася, але людина зазнала невдачі. Це фінальний результат, і процес повністю закінчено. Ніхто не очікує нових спроб найближчим часом. Але як тільки ми додаємо слово **ще**, прагматичний зміст речення кардинально змінюється. Фраза **«Він ще не склав іспит»** миттю перетворює поразку на звичайну затримку в часі. Це означає, що іспит все ще попереду, людина активно готується, і очікуваний результат просто відкладається. Слово **ще** зберігає оптимізм і показує співрозмовнику, що бажана дія обов'язково відбудеться в майбутньому.

> *The magic of the word **ще** lies in the fact that it acts as a psychological bridge between a past failure and a future success. Without this small adverb, the perfective aspect in negation often sounds like a harsh judgment or a final statement of defeat. For example, the phrase **«Він не склав іспит»** (He didn't pass the exam) means the attempt happened, but the person failed. This is a final result, and the process is completely over. No one expects new attempts anytime soon. But as soon as we add the word **ще**, the pragmatic meaning of the sentence changes dramatically. The phrase **«Він ще не склав іспит»** (He hasn't passed the exam yet) instantly turns a defeat into a simple delay in time. It means the exam is still ahead, the person is actively preparing, and the expected result is simply postponed. The word **ще** preserves optimism and shows the interlocutor that the desired action will definitely happen in the future.*

This expectation-management function of **ще не** paired with the perfective aspect is crucial when discussing future deadlines, especially in professional contexts. Future tense negation with the perfective aspect naturally deals with precise schedules. If you say **«Я не зроблю це до вечора»** (I won't have it done by evening), you are making a stark admission of a lack of result. It sounds like you are giving up on the deadline entirely; it is a closed door and a flat denial. However, if you are communicating with a manager, you want to soften this blow and show professionalism. Saying **«Ми ще не закінчимо проєкт до п'ятниці»** (We won't have the project finished by Friday yet) fundamentally shifts the pragmatics of the conversation. It acknowledges the deadline, admits that Friday is too soon for the final delivery, but strongly implies that the completion is still actively being pursued. It transforms a flat refusal into a constructive status update about a pending milestone.

Щоб краще відчути цю прагматичну різницю в житті, давайте проаналізуємо типову ситуацію з написанням важливого листа. Уявіть, що ваш колега запитує, чи готовий документ для клієнта. Якщо ви відповідаєте **«Я не писав лист»**, ви використовуєте недоконаний вид для холодного, загального заперечення. Ця фраза означає, що ви навіть не сідали за робочий стіл і взагалі не починали цей процес. Це нейтральний історичний факт, який знімає з вас будь-яку відповідальність за результат. Натомість відповідь **«Я ще не написав лист»** несе інший, набагато глибший соціальний меседж. Використовуючи доконаний вид разом із цим маркером очікування, ви відкрито визнаєте своє соціальне зобов'язання. Ви підтверджуєте, що чудово знаєте про необхідність цього листа. Можливо, ви вже створили першу чернетку, але готовий до відправлення результат ще не досягнутий. Пошта чекає, і ви своїм запереченням показуєте, що тримаєте ситуацію під повним контролем і впевнено наближаєтеся до кінцевої мети. Така сама логіка працює для спільних рішень: порівняйте нейтральний процес «ми не вирішували це питання» (we weren't deciding this issue) з очікуванням «ми ще не вирішили» (we haven't decided yet) або «ми ще не обговорили це» (we haven't discussed it yet).

Interestingly, the "pending result" pattern is so deeply ingrained in the Ukrainian mindset that speakers frequently use it to express an internalized expectation, even when no one else is waiting for the result. You will often hear native speakers use **ще не** with a perfective verb to express a personal sense of unfulfilled ambition or mild disappointment in their own ongoing progress. For instance, if you are studying a language and feel frustrated by your slow vocabulary retention, you might sigh and say, **«Я ще не вивчив ці слова»** (I haven't mastered these words yet). The conscious use of the perfective verb **вивчити** rather than the imperfective **вчити** is the key grammatical choice here. You are not denying the learning process—you have probably spent many hours studying them—but you are expressing frustration that the target result has not materialized. The expectation is entirely internal; you feel that you *should* have achieved this milestone by now, and the perfective aspect perfectly captures that self-imposed standard.

```markdown
:::tip
**Quick tip**
Never mix **ще не** with the imperfective aspect when talking about specific tasks! Either you haven't started at all (**не робив**), or you haven't finished yet (**ще не зробив**).
:::
```

<!-- INJECT_ACTIVITY: error-correction-negated-aspect -->

Оскільки студенти часто плутають ці дві різні функції заперечення, у їхньому мовленні регулярно виникають типові помилки, які звучать неприродно для носіїв мови. Найпоширеніша логічна пастка — це механічне змішування слова **ще** з дієсловом недоконаного виду в тих випадках, коли контекст вимагає результату. Наприклад, фраза **«*Я ще не читав цю книжку»** викликає легкий когнітивний дисонанс. Вона штучно намагається поєднати очікування майбутнього результату із загальним фактом повної відсутності процесу в минулому. Для українського вуха це звучить так, ніби ви кажете: "Я ще ніколи в житті навіть не починав читати, але фінальний результат вже скоро буде". Щоб успішно виправити цю помилку, вам потрібно чітко визначити свій комунікативний намір. Якщо ви хочете сказати, що взагалі не знайомі з книжкою, просто приберіть слово "ще" і скажіть: **«Я не читав»**. Якщо ж ви активно плануєте завершити читання найближчим часом, обов'язково змініть вид дієслова на доконаний: **«Я ще не прочитав»**.

Ultimately, the choice to use **ще не** with the perfective aspect comes down to a crucial factor of intentionality. It is fundamentally a "soft" negation. When you use this specific pattern, you are signaling to the world: "I want to do this," or "I am actively trying to achieve this." It deliberately keeps the possibility of the action alive in the conversational space, rather than shutting it down completely. Consider the emotional difference between stating a cold fact and managing an interpersonal situation. If you are waiting for a friend at a restaurant and someone asks where she is, saying **«Вона не прийшла»** (She didn't come) sounds like a final, factual conclusion; the event is over, and you should probably just order your food without her. However, saying **«Вона ще не прийшла»** (She hasn't arrived yet) keeps the door wide open. It strongly implies that she is on her way, you are still actively waiting, and her arrival is an expected, pending result. By mastering this subtle distinction, you gain immense control over the pragmatics of your Ukrainian conversations.

<!-- INJECT_ACTIVITY: match-up-pragmatic-context -->

## Підсумок: заперечення як прагматичний вибір

At this stage in your Ukrainian journey, you have likely realized that grammar is rarely just a set of mechanical rules. It is a reflection of how the speaker perceives the world and their place within it. When we talk about negation and the choice of aspect, we are stepping into the realm of pragmatics. The distinction between using the imperfective and the perfective aspect in a negative sentence is not merely about linguistic correctness; it is a profound, pragmatic choice that reveals your internal attitude toward a specific action. You are not just stating whether something happened or not; you are communicating your expectations, your responsibilities, and your intentions.

Вибір між фразами «я не писав» та «я ще не написав» демонструє ваше ставлення до конкретного завдання. Коли ви використовуєте недоконаний вид, ви просто констатуєте нейтральний факт минулого. Ви повідомляєте співрозмовнику, що дія взагалі не відбувалася, і ви не маєте жодних зобов'язань щодо неї. Натомість використання доконаного виду зі словом «ще» перетворює звичайне заперечення на обіцянку. Ви показуєте, що усвідомлюєте своє завдання, берете на себе відповідальність за нього і плануєте обов'язково довести цю справу до логічного кінця у найближчому майбутньому.

> *The choice between the phrases "I didn't write" and "I haven't written yet" demonstrates your attitude toward a specific task. When you use the imperfective aspect, you are simply stating a neutral fact of the past. You inform your interlocutor that the action did not happen at all, and you have no obligations regarding it. Instead, using the perfective aspect with the word "yet" turns an ordinary negation into a promise. You show that you are aware of your task, take responsibility for it, and plan to definitely bring this matter to a logical conclusion in the near future.*

To truly master this pragmatic nuance, you need to become comfortable with a specific group of perfective verbs. In Ukrainian, the prefix **до-** is frequently attached to verbs to emphasize the absolute finality or the final stage of an action. When you combine this specific prefix with the **ще не** negation pattern, you create a highly precise statement about your progress. Verbs like **дочитати** (to finish reading), **домити** (to finish washing), and **доробити** (to finish doing) are the perfect candidates for this grammatical structure. They allow you to explain that the process has already been ongoing for some time, but the ultimate, expected result is still slightly out of reach.

:::info
**Grammar box**
The prefix **до-** added to an imperfective verb (like **робити**) creates a perfective verb (**доробити**) that specifically focuses on the final completion of an ongoing task.
:::

Цей префікс ідеально підходить для ситуацій, коли ви вже виконали більшу частину роботи, але певний відсоток завдання залишається незавершеним. Наприклад, фраза «я ще не домив посуд» означає, що ви зараз стоїте біля раковини, більшість тарілок вже чисті, але вам потрібна ще хвилина. Ви не заперечуєте сам процес миття, а лише вказуєте на відсутність фінального результату. Це дуже точний інструмент, який допомагає уникати непорозумінь у побутовому спілкуванні.

> *This prefix is perfectly suited for situations where you have already completed most of the work, but a certain percentage of the task remains unfinished. For example, the phrase "I haven't finished washing the dishes yet" means that you are currently standing by the sink, most of the plates are already clean, but you need another minute. You are not denying the washing process itself, but only pointing out the absence of the final result. This is a very precise tool that helps avoid misunderstandings in everyday communication.*

Let us look at how this plays out in a typical domestic scenario. Imagine two roommates, Olga and Mykhailo, discussing their household chores for the weekend. The way Mykhailo answers Olga's questions perfectly illustrates the "Commitment Scale" of aspect in negation. Notice how he uses the imperfective aspect for a task he was never assigned, completely distancing himself from the responsibility. However, when asked about a task he is actively working on, he immediately switches to the perfective aspect with the "do-" prefix.

> — **Ольга:** Михайле, ти вже прибрав у ванній кімнаті? *(Mykhailo, have you cleaned the bathroom yet?)*
> — **Михайло:** Ні, я не прибирав. Це твоя черга цього тижня. *(No, I didn't clean it. It's your turn this week.)*
> — **Ольга:** А як щодо кухні? Ти помив посуд? *(And what about the kitchen? Did you wash the dishes?)*
> — **Михайло:** Я мив його вранці, але ще не домив кілька тарілок. Зараз закінчу. *(I was washing them in the morning, but I haven't finished washing a few plates yet. I will finish now.)*

Mykhailo's first response, **не прибирав** (didn't clean), is a flat, factual denial. The imperfective aspect here signals that the action never started because it was not his job. His second response, **ще не домив** (haven't finished washing yet), acknowledges the expectation. The perfective aspect shows that he is committed to the task and the result is imminent.

This pragmatic choice becomes even more critical in professional or academic environments, where your choice of words directly impacts your credibility. Imagine a conversation between a university professor and a student discussing a thesis deadline. The student must navigate the conversation carefully. They need to show that they are actively engaged in the research process, even if the final deliverables are not yet ready. Using the wrong aspect here could make the student sound lazy or disengaged, whereas the correct aspect demonstrates diligence and a clear understanding of the pending expectations.

> — **Професор:** Ви вже написали перший розділ вашої роботи? *(Have you already written the first chapter of your work?)*
> — **Студент:** Я ще не написав його повністю, але я активно працюю над текстом. *(I haven't written it completely yet, but I am actively working on the text.)*
> — **Професор:** Добре. А ви читали ту статтю, яку я вам рекомендував? *(Good. And did you read that article I recommended to you?)*
> — **Студент:** Ні, я її не читав. Я не зміг знайти її в бібліотеці. *(No, I didn't read it. I couldn't find it in the library.)*

By saying **ще не написав**, the student protects their professional image, indicating that the chapter is a work in progress. Conversely, **не читав** is an honest admission of a non-event; the student could not find the source, so the action of reading never took place at all.

Beyond expressing responsibility and progress, this grammatical structure serves a vital social function: it softens refusals and apologies. Direct negation using the imperfective aspect can sometimes feel abrupt or even slightly confrontational in Ukrainian. If someone asks why you have not responded to an email, a flat factual denial might sound like you are making an excuse or simply ignoring them. By incorporating the perfective aspect and the concept of an expected result, you subtly shift the tone of the conversation, making it more polite and socially acceptable.

Конструкція «ще не» з доконаним видом працює як соціальний амортизатор у незручних ситуаціях. Якщо ви кажете колезі «я не читав ваше повідомлення», це може звучати дещо різко. Співрозмовник може подумати, що ви ігноруєте його листи. Але якщо ви скажете «я ще не прочитав ваше повідомлення» або «я ще не переглянув його», ви одразу знімаєте напругу. Так само порівняйте загальний факт «я не відповідав» (I didn't answer) та незавершене очікування «я ще не відповів» (I haven't answered yet). Ця фраза має прихований підтекст: ви визнаєте існування повідомлення, ви цінуєте час колеги, і ви обов'язково відреагуєте на нього, як тільки матимете можливість.

> *The "not yet" construction with the perfective aspect acts as a social shock absorber in awkward situations. If you tell a colleague "I didn't read your message", it can sound somewhat harsh. The interlocutor might think that you are ignoring their emails. But if you say "I haven't read your message yet" or "I haven't reviewed it yet", you immediately relieve the tension. This phrase has a hidden subtext: you acknowledge the existence of the message, you value your colleague's time, and you will definitely react to it as soon as you have the opportunity.*

To solidify your understanding, let us review the three core patterns of negation and how they reflect the speaker's pragmatic intent. Whenever you are about to use a negated verb, pause for a moment and ask yourself what exactly you are trying to communicate to your listener. Are you simply reporting the news, are you promising an outcome, or are you pointing out a failure?

| Конструкція (Construction) | Значення (Meaning) | Прагматичний намір (Pragmatic Intent) | Приклад (Example) |
| :--- | :--- | :--- | :--- |
| **«Не» + Недоконаний вид** | Нейтральний факт | Просто констатація того, що дія не відбулася. Немає жодних очікувань. | *Я не їв.* (I didn't eat. / I wasn't eating.) |
| **«Ще не» + Доконаний вид** | Очікуваний результат | Дія не завершена, але спікер планує її закінчити. Зберігає надію. | *Я ще не поїв.* (I haven't eaten yet. / I intend to eat soon.) |
| **«Не» + Доконаний вид** | Специфічна невдача | Очікуваний результат не був досягнутий. Часто звучить як звинувачення. | *Ти не зробив це!* (You failed to do this!) |

:::tip
**Quick tip**
If you want to maintain a friendly, cooperative tone when discussing unfinished tasks, always lean toward the **ще не + perfective** pattern. It shows that you are a team player who is still focused on the goal!
:::

Тепер ви володієте потужним інструментом для керування контекстом у розмові. Наступного разу, коли ви будете слухати українські подкасти або спілкуватися з носіями мови, зверніть увагу на те, як вони використовують ці заперечні форми. Спробуйте проаналізувати їхні приховані мотиви. Кожного разу, коли ви самі будуєте речення, запитуйте себе: «Чи я просто констатую сухий факт, чи я даю людині обіцянку щодо майбутнього результату?». Ця усвідомленість допоможе вам звучати набагато природніше і впевненіше.

> *Now you possess a powerful tool for managing context in a conversation. The next time you listen to Ukrainian podcasts or communicate with native speakers, pay attention to how they use these negative forms. Try to analyze their hidden motives. Every time you build a sentence yourself, ask yourself: "Am I just stating a dry fact, or am I making a promise to the person about a future result?". This awareness will help you sound much more natural and confident.*

Understanding how aspect shapes the underlying meaning of a sentence is a major milestone in your language acquisition. You have moved beyond simply describing what happened, and you are now actively managing expectations and social nuances. In the upcoming modules, we will take a brief thematic break to explore vocabulary related to work and careers. After that, we will return to the fascinating world of grammatical aspect to see how these exact same rules apply to conditional sentences with **якщо** (if) and **якби** (if only).

<!-- INJECT_ACTIVITY: open-writing-progress-report -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-in-negation
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

**Level: B1 (Module 8)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
