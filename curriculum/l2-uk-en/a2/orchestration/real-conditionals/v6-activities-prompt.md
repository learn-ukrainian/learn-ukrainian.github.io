<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/real-conditionals.yaml` file for module **51: Якщо... то...** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-conditional-verbs -->`
- `<!-- INJECT_ACTIVITY: match-condition-to-result -->`
- `<!-- INJECT_ACTIVITY: fix-aspect-errors -->`
- `<!-- INJECT_ACTIVITY: choose-if-style-yakshcho-yakby -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete real conditional sentences with the correct verb form in the якщо-clause
    or result clause
  items: 8
  type: fill-in
- focus: Choose якщо or якби — identify real vs. hypothetical conditions (recognition
    only for якби)
  items: 8
  type: quiz
- focus: Match conditions (якщо-clauses) to their logical results
  items: 8
  type: match-up
- focus: Fix incorrect verb aspect usage in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- якби (if — hypothetical, B1 preview)
- змокнути (to get wet)
- запізнитися (to be late)
- парасолька (umbrella)
- відпустка (vacation, holiday)
required:
- якщо (if — real condition)
- умова (condition)
- результат (result, outcome)
- реальний (real)
- погода (weather)
- допомогти (to help)
- поспішити (to hurry)
- вільний (free, available)
- залишитися (to stay, to remain)
- порада (advice)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Якщо + теперішній/майбутній час (If + Present/Future)

Ми часто говоримо про різні **умови** *(conditions)* у нашому житті. **Умова** — це спеціальна ситуація. Ця ситуація є необхідною для певного **результату** *(result)*. Ми використовуємо слово «якщо» *(if)*, коли говоримо про **реальну** *(real)* умову. Це означає, що така ситуація є дуже можливою. Вона цілком може статися в реальному житті.

We use "якщо" to introduce a condition that is likely or possible in the real world.

Важливо розуміти різницю між різними словами. Слово «якщо» відрізняється від слова «коли» *(when)*. Слово «коли» означає просто час майбутньої дії. Слово «якщо» означає саме умову цієї дії. Також «якщо» відрізняється від слова «якби» *(if only)*. Слово «якби» ми використовуємо лише для нереальних або фантастичних ситуацій.

Наприклад, подивіться на це речення: «Якщо буде **сонце** *(sun)*, ми підемо гуляти». Це абсолютно реальний план. Сонце є дуже ймовірним сьогодні.

Як ми будуємо такі складні речення? Їхня структура є дуже простою і логічною. Зазвичай нове речення починається зі слова «якщо». Далі йде сама умова. Після умови ми завжди ставимо кому. Потім ми говоримо про результат цієї умови.

Typically, "якщо" starts the sentence, followed by a comma that separates the condition from the result.

Подивіться на такий приклад. «Якщо ти купиш **насіння** *(seeds)*, я підготую **грядку** *(garden bed)*». Тут перша частина — це умова. А друга частина — це логічний результат.

Але ми також можемо легко змінити порядок цих частин. Результат може стояти на першому місці. Тоді слово «якщо» стоїть посередині речення.

The order can be reversed without changing the meaning of the sentence.

Наприклад: «Ми підемо гуляти, якщо буде сонце». Зверніть увагу на цей факт. Сенс цього речення абсолютно не змінюється від зміни порядку.

Ми часто говоримо про відомі факти. Також ми говоримо про загальні істини. Для цього ми використовуємо тільки теперішній час в обох частинах речення.

We use Present + Present for facts and logical consequences.

Умова має форму теперішнього часу. І результат також має форму теперішнього часу. Це так званий нульовий тип умови. Він показує гарантований результат.

Наприклад, подивіться на це цікаве англійське прислів'я. «Якщо платити **горіхами** *(peanuts)*, отримуєш **мавп** *(monkeys)*». Тут ми бачимо дієслово «платити» *(to pay)*. Також тут є дієслово «отримуєш» *(you get)*. Обидва ці дієслова описують загальний факт.

Інший дуже простий приклад: «Якщо вода кипить, вона гаряча». Це відомий фізичний закон. Вода не може бути холодною, якщо вона зараз кипить. Тому ми завжди використовуємо тільки теперішній час для таких очевидних фактів. Це дуже логічна структура української граматики.

Але найчастіше ми говоримо про майбутні можливості. Ми кожного дня плануємо наші майбутні дії.

We explain future possibilities using Present or Future in the condition and Future in the result.

В українській мові ми можемо використовувати теперішній або майбутній час після слова «якщо». А в другій частині речення ми зазвичай використовуємо майбутній час. Також там може бути наказовий спосіб *(imperative)*.

Особливо часто ми використовуємо дієслова «бути» і «мати» у майбутньому часі. Наприклад, ми кажемо «якщо буде» *(if there will be)*. Або ми кажемо «якщо матимеш» *(if you will have)*.

Подивіться на цей приклад: «Якщо ти матимеш час, я зателефоную тобі». Тут ми чітко бачимо умову в майбутньому часі.

Інший приклад: «Якщо буде гарна **погода** *(weather)*, ми поїдемо на море».

Або: «Якщо ти маєш **вільний** *(free)* час, треба **поспішити** *(to hurry)* на поїзд». Це дуже гарна **порада** *(advice)* для туристів. Ми використовуємо таку структуру щодня.

В українській мові є одне дуже цікаве коротке слово. Це слово «то» *(then)*. Воно дуже часто працює разом зі словом «якщо».

The word "то" is a correlative particle that marks the start of the result clause.

Ми ставимо слово «то» на самому початку другої частини речення. Воно стоїть прямо перед результатом. Це слово робить зв'язок між умовою і результатом більш сильним. Це слово додає важливий акцент.

Наприклад: «Якщо **дощитиме** *(it will rain)*, то ми **залишимося** *(will stay)* вдома». Слово «дощитиме» — це наша умова. Далі йде слово «то». І потім іде наш результат — «ми залишимося».

Слово «то» не є граматично обов'язковим. Ви можете сказати це речення без нього. Але українці дуже люблять використовувати це слово у повсякденній розмові.

Правила пунктуації є дуже важливими для таких складних речень. Правильна кома допомагає нам легко читати і розуміти текст.

A comma always follows the "якщо"-clause when it comes first. A comma always precedes "якщо" when it comes second.

Якщо умова зі словом «якщо» стоїть на першому місці, ми завжди ставимо кому після неї. Наприклад: «Якщо ти хочеш, я **допоможу** *(will help)*».

Якщо результат стоїть на першому місці, ми ставимо кому прямо перед словом «якщо». Наприклад: «Я допоможу, якщо ти хочеш».

А що треба робити зі словом «то»? Кома завжди стоїть перед словом «то». Наявність слова «то» не змінює наше головне правило пунктуації.

Наприкінці ми маємо обов'язково згадати про форми дієслів. У реальних умовах ми завжди використовуємо дійсний спосіб.

In real conditionals, we use regular present or future forms. We never use the "б/би" particle used in English "would".

Ми використовуємо звичайні форми теперішнього або майбутнього часу. Ми ніколи не використовуємо частку «б» або «би» після слова «якщо». Частка «б/би» існує тільки для слова «якби». А слово «якби» створює нереальну умову.

Тому запам'ятайте це просте правило. Після «якщо» ми просто ставимо дієслово. Це робить граматику набагато простішою для вивчення та щоденного використання.

<!-- INJECT_ACTIVITY: fill-in-conditional-verbs -->


## Умова в повсякденному житті (Conditions in Everyday Life)

> — **Чоловік:** Що ми будемо робити сьогодні на **дачі** *(at the dacha/summer house)*? Роботи тут дуже багато.
> — **Дружина:** Так, справді. Якщо сьогодні буде сонце, ми посадимо **помідори** *(tomatoes)* і огірки.
> — **Чоловік:** А якщо піде сильний дощ? Небо зараз сіре.
> — **Дружина:** Якщо йтиме дощ, ми почекаємо в будинку. Ми польємо всі рослини трохи пізніше.
> — **Чоловік:** Але спочатку нам треба купити нове **насіння** *(seeds)*.
> — **Дружина:** Точно. Якщо ти поїдеш у магазин і купиш насіння, я підготую **грядку** *(garden bed)*.
> — **Чоловік:** Добре, я все зроблю. А коли ми будемо відпочивати?
> — **Дружина:** Якщо ми швидко закінчимо роботу, то ввечері будемо пити чай на терасі.
> — **Чоловік:** Чудово! Якщо ти обіцяєш смачний чай, я поїду в магазин зараз.

Цей діалог ідеально показує, як ми використовуємо умову в реальному житті кожного дня. Коли ми працюємо разом з іншими, наші дії часто залежать одна від одної. The husband and wife use real conditions to plan their collaboration step by step. Слово «якщо» допомагає їм створити чіткий план роботи. Дружина каже чоловікові: «Якщо ти купиш насіння, я підготую грядку». Це означає просту річ: "If you do X, I will do Y". Її дія прямо залежить від його дії. Це дуже практичний спосіб планувати спільну роботу в родині. Вони також планують свої дії залежно від погоди надворі. Якщо буде сонце, вони будуть садити помідори. Вони вільно використовують майбутній час в обох частинах цього складного речення.

Ми також дуже часто використовуємо реальну умову, коли даємо корисні поради іншим людям. We often use real conditionals to give advice, recommendations, or friendly instructions. У таких реченнях ми зазвичай використовуємо наказовий спосіб у другій частині. The result clause typically contains an imperative verb to tell someone what to do. Наприклад, ваш друг погано себе почуває на роботі. Ви кажете йому: «Якщо у тебе болить голова, випий **таблетку** *(pill/tablet)*». Умова стоїть у теперішньому часі, а результат — це ваша пряма порада. Вчитель може сказати студентам: «Якщо хочеш вивчити нову мову, говори нею щодня». Або мама суворо каже своїй дитині: «Якщо ти хочеш гуляти з друзями, спочатку зроби домашнє завдання». Це пряма і дуже зрозуміла інструкція. Наказовий спосіб робить вашу пораду більш сильною та ефективною.

Слово «якщо» також чудово допомагає нам попередити людей про майбутню проблему. We use conditional sentences to warn people about likely negative outcomes if they ignore our advice. У таких ситуаціях ми майже завжди використовуємо дієслова доконаного виду. Perfective verbs show the immediate, completed, and negative result of an action. Наприклад, ваш колега дуже повільно збирається на роботу. Ви кажете: «Якщо ти зараз не **поспішиш** *(will hurry)*, ти запізнишся на свій ранковий поїзд». Дія «запізнитися» — це конкретний і гарантований результат. Інший приклад стосується дощової погоди. Ви бачите темні хмари на небі вранці. Ви кажете своєму другу: «Якщо ти не візьмеш із собою **парасольку** *(umbrella)*, ти обов'язково **змокнеш** *(will get wet)*». Це абсолютно логічне попередження. Якщо умова не виконана, результат точно буде поганим. Ми завжди використовуємо майбутній час доконаного виду для попереджень.

Граматична умова є дуже важливою, коли ми домовляємося про щось із різними людьми. Real conditionals help us build mutual trust, make firm promises, and set clear agreements. Ми обіцяємо зробити щось корисне, якщо інша людина виконає свою частину роботи. Два колеги в офісі кажуть: «Якщо ти допоможеш мені сьогодні, я допоможу тобі завтра». Це абсолютно рівноцінний і чесний обмін послугами. Ми також постійно використовуємо умову для позитивних планів на майбутнє. Часто ми говоримо родичам: «Якщо все буде добре, ми поїдемо у **відпустку** *(vacation)* влітку». Або ви можете сказати дітям: «Якщо я отримаю премію на роботі, ми підемо в ресторан». Ми використовуємо тільки майбутній час, щоб показати наші реальні плани.

Ми постійно і дуже активно використовуємо цю граматику в нашому соціальному житті. Conditionals are absolutely essential for planning meetings, phone calls, and social events. Наприклад, ви організовуєте вечірку на вихідні. Ви пишете своїм друзям: «Якщо ви зможете прийти до мене в гості, напишіть мені повідомлення до вечора». Тут ми використовуємо майбутній час в умові та наказовий спосіб у результаті. Або ви чекаєте свого колегу після його важливої зустрічі. Ви кажете йому: «Якщо твоя зустріч **закінчиться** *(will finish)* вчасно, я прийду в кафе». Слово **вчасно** *(on time)* дуже часто стоїть разом зі словом «якщо». Ми всі маємо щільний розклад, і наші плани постійно залежать від інших подій. Тому ми часто кажемо: «Якщо я звільнюся з роботи раніше, я обов'язково зателефоную тобі».

Дуже важливо правильно вибирати граматичний вид дієслова у таких реченнях. The choice between perfective and imperfective aspect directly depends on the exact type of condition. Чому ми кажемо «Якщо не поспішиш, запізнишся»? Обидва дієслова в цьому реченні є дієсловами доконаного виду. Ми використовуємо їх для конкретної, унікальної ситуації в майбутньому часі. Це станеться з людиною тільки один раз. Але якщо ситуація постійно повторюється, ми обов'язково беремо дієслова недоконаного виду. For repeated or habitual conditions, always use the imperfective aspect. Наприклад, ми можемо сказати: «Якщо ти завжди запізнюєшся на роботу, люди не хочуть з тобою працювати». Тут умова є постійною звичкою людини, тому ми використовуємо теперішній час. Правильний вид дієслова робить вашу умову дуже точною та природною.

<!-- INJECT_ACTIVITY: match-condition-to-result -->
<!-- INJECT_ACTIVITY: fix-aspect-errors -->


## Якщо чи якби? Тільки реальна умова (Якщо or якби? Real Conditions Only)

У цій граматичній темі ми детально вивчаємо тільки абсолютно реальні ситуації. We use the word «якщо» when a condition is very possible or highly likely to happen in real life. Наприклад, ви стабільно працюєте кожен день. Ви регулярно отримуєте свою зарплату. Тому ви впевнено кажете: «Якщо я маю **гроші** *(money)*, я обов'язково купую свіжі продукти». Це абсолютно реальна і типова ситуація. Але іноді люди просто мріють про якісь фантастичні речі. Sometimes people dream about impossible or purely hypothetical situations. Для таких фантазій українці завжди використовують інше слово — «**якби**» *(if only / what if)*. Наприклад: «Якби я мав **мільйон** *(million)* доларів, я б купив великий острів». Ця людина не має мільйона доларів зараз. Це тільки фантазія. We will study these unreal conditions much later, at the B1 level. Наразі вам потрібно добре запам'ятати головне правило. At the A2 level, you only need to use «якщо» for real life.

Чому ми взагалі говоримо про це нове слово «якби» саме зараз? Ви точно колись почуєте це слово в українських ліричних піснях, старих віршах або просто в розмовах. You will definitely hear it in popular culture or daily conversations with native speakers. Українці дуже люблять емоційно співати про якісь нереальні мрії. Часто популярна пісня починається так: «Якби я знав...» або «Якби я тільки міг...». When you hear «якби», just recognize that the person is dreaming or regretting something impossible. Будь ласка, ніколи не плутайте його зі звичайним словом «якщо». Do not use «якби» when you make real plans for the upcoming weekend. Якщо ви кажете своєму другові про реальну зустріч завтра, завжди використовуйте тільки «якщо». Залиште ці нереальні мрії для поетів. For your daily practical communication right now, «якщо» is your only tool.

Тепер давайте детально поговоримо про правильну вимову таких складних речень. Proper intonation is just as important as correct grammar for clear communication. Коли ми використовуємо умову, ми ділимо наше довге речення на дві частини. Між ними завжди обов'язково є коротка пауза. We signal this pause with a specific melody in our voice. Коли ви кажете першу частину (саму умову), ваш голос завжди йде вгору. The pitch rises at the end of the «якщо» clause. Це чітко показує, що ваша думка ще не закінчена. Наприклад: «Якщо завтра буде сонце ↗...». Ваш співрозмовник уважно чекає логічного продовження. Далі ви робите коротку паузу. Потім ви кажете головний результат, і ваш голос іде вниз. The main clause has a falling pitch to show completion. «...ми підемо ↘ гуляти в парк». Спробуйте сказати це правило вголос кілька разів. Ця проста мелодія робить вашу українську дуже красивою та природною.

На цьому етапі ви вже знаєте багато різних типів складних речень. You now know how to connect ideas logically and clearly. Давайте згадаємо всі важливі слова-конектори. Ми нещодавно вивчили їх. Уявімо, що ви плануєте цікаву подорож. Слово «**тому що**» *(because)* показує причину. Наприклад: «Я їду в гори, тому що люблю природу». Слово «**хоча**» *(although)* показує логічний контраст. Наприклад: «Я йду гуляти, хоча надворі холодно». Слово «**щоб**» *(in order to)* показує вашу головну мету. Наприклад: «Я беру фотоапарат, щоб робити красиві фотографії». І тепер ви також знаєте реальну умову. Для цього є наше слово «якщо». These connectors allow you to build rich narratives in Ukrainian. Ви можете пояснити абсолютно будь-яку складну ситуацію. Ви вже не говорите короткими та дуже простими фразами.

Тепер давайте спробуємо поєднати ці різні ідеї в один великий текст. Let's build a complete paragraph using these logical connections. Уявіть, що ваш колега питає про ваші точні плани на літо. Ви можете дати йому дуже довгу і детальну відповідь. «Я обов'язково поїду в Карпати, якщо матиму довгу відпустку на роботі. Хоча там може бути сильний дощ, я все одно хочу піти в гори. Я роблю це, щоб побачити чудовий **краєвид** *(landscape)*. Я дуже люблю гори, тому що там завжди тихо і спокійно». Notice how smoothly the ideas flow together when you use these words. Використовуйте ці граматичні структури щодня, і ви швидко побачите свій великий прогрес. Ваша українська мова стає набагато кращою і значно багатшою!

<!-- INJECT_ACTIVITY: choose-if-style-yakshcho-yakby -->


## Підсумок

Ось ми і закінчили цю дуже важливу граматичну тему. Тепер ви можете вільно та впевнено планувати своє майбутнє. Давайте перевіримо ваші нові знання перед кінцем уроку. Будь ласка, дайте чесну відповідь на ці запитання:

* Чи можу я скласти речення з «якщо» про **погоду** *(weather)*?
  Так! Наприклад: «Якщо завтра буде сильний дощ, я залишуся вдома».

* Чи знаю я точно, де треба ставити **кому** *(comma)*?
  Так! Кома завжди стоїть між двома частинами складного речення. Наприклад: «Якщо ти підеш у кіно, то я піду з тобою».

* Чи добре я розумію **різницю** *(difference)* між «якщо» та «якби»?
  Так! Слово «якщо» — це завжди **реальна умова** *(real condition)*. А слово «якби» — це тільки нереальні мрії та фантазії. Зараз ми використовуємо тільки «якщо» для наших реальних планів.

* Чи можу я дати корисну **пораду** *(advice)* через «якщо»?
  Так! Ви можете дуже легко допомогти вашому другу. Наприклад: «Якщо ти хочеш спати, іди в ліжко зараз».

Ваша українська мова стала ще кращою та значно багатшою! Ви дуже добре попрацювали сьогодні. Пам'ятайте наше головне правило: «Якщо ви будете багато читати щодня, то швидко заговорите вільно!»

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: real-conditionals
level: a2

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

**Level: A2 (Module 51/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
