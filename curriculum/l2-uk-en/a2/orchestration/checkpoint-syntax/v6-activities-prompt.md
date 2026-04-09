<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-syntax.yaml` file for module **53: Контрольна робота — складне речення** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-conjunction-id -->`
- `<!-- INJECT_ACTIVITY: fill-in-conjunction-form -->`
- `<!-- INJECT_ACTIVITY: sort-conjunction-types -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify conjunction types in mixed complex sentences from M42-M46
  items: 8
  type: quiz
- focus: Complete complex sentences choosing from all five conjunction types
  items: 8
  type: fill-in
- focus: Sort example sentences by type — причина, допуст, мета, означення, умова
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- підрядний (subordinate)
- головний (main)
- кома (comma)
required:
- тому що (because)
- бо (because)
- хоча (although)
- щоб (in order to)
- який (which, that)
- якщо (if)
- сполучник (conjunction)
- складне речення (complex sentence)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Впізнай сполучник (Part 1: Identify the Conjunction)

Мова — це не просто набір окремих фактів. Коли ми розмовляємо, ми пояснюємо причини, ставимо умови та описуємо наші цілі. Для цього нам потрібне **складне речення** (complex sentence). Складні речення допомагають нам будувати логічні та зв'язні історії, які звучать природно. У цьому модулі ми повторимо всі типи складних речень, які ви вивчили на рівні A2. Складне речення має дві або більше частин: **головний** (main) і **підрядний** (subordinate) блок. 

Щоб з'єднати ці частини, ми використовуємо **сполучник** (conjunction) або сполучне слово. Існують різні типи зв'язку. Простий сурядний зв'язок поєднує абсолютно рівноправні ідеї за допомогою базових слів **і** (and), **а** (and/but), та **але** (but).
**Сьогодні субота, і ми відпочиваємо вдома.** (Today is Saturday, and we are resting at home.)
**Я люблю зелений чай, а моя сестра любить чорну каву.** (I like green tea, and my sister likes black coffee.)
**Він купив квиток, але він не поїхав на концерт.** (He bought a ticket, but he didn't go to the concert.)

Підрядний зв'язок — це інша логіка. Одна частина стає головною, а інша — залежною. Коли ми пояснюємо нашу мотивацію, ми дивимося або в минуле (на причину події), або в майбутнє (на нашу мету).
Для вираження причини ми використовуємо сполучник **тому що** (because) або коротке слово **бо** (because). Слово **бо** дуже популярне в щоденній розмовній мові.
**Я запізнився на зустріч, бо на дорозі був великий затор.** (I was late for the meeting because there was a big traffic jam on the road.)
**Вона не прийшла в офіс, тому що була дуже зайнята.** (She didn't come to the office because she was very busy.)

Для вираження мети ми використовуємо сполучник **щоб** (in order to / so that).
**Я виїхав з дому раніше, щоб не запізнитися.** (I left home earlier so as not to be late.)
**Ми кожного дня вчимо українську мову, щоб вільно спілкуватися з людьми.** (We learn the Ukrainian language every day in order to communicate fluently with people.)

Коли нам потрібно описати конкретну людину, предмет або місце всередині великого речення, ми використовуємо означальні речення.
Для опису предмета чи людини ми беремо слово **який** (which / that / who).
**Я бачу молодого хлопця, який швидко біжить у парк.** (I see a young boy who is running fast to the park.)
**Це новий робочий проект, який ми успішно закінчили вчора.** (This is the new work project that we successfully finished yesterday.)
Для опису місця ми використовуємо слова **де** (where) або **куди** (where to).
**Це старий цегляний будинок, де я живу вже десять років.** (This is the old brick house where I have lived for ten years already.)

Для гіпотетичних ситуацій та несподіваних результатів ми маємо умову та допуст.
Реальна умова використовує слово **якщо** (if).
**Якщо завтра буде тепле сонце, ми обов'язково підемо в парк.** (If there is warm sun tomorrow, we will definitely go to the park.)
**Якщо ти зараз маєш вільний час, допоможи мені, будь ласка.** (If you have free time right now, help me, please.)
Допуст показує суперечність або подолання перешкоди. Ми використовуємо слово **хоча** (although / even though).
**Хоча вчора було дуже холодно, ми пішли гуляти.** (Although it was very cold yesterday, we went for a walk.)
**Він купив цю велику машину, хоча вона дуже дорога.** (He bought this big car, even though it is very expensive.)

Давайте прочитаємо діалог. Студент розповідає викладачу про свої плани на вихідні. Зверніть увагу на те, як він використовує сполучники.

> **Студент:** На вихідних я залишуся вдома, **тому що** маю багато роботи. *(On the weekend I will stay home because I have a lot of work.)*
> **Викладач:** Що саме ви будете робити цими днями? *(What exactly will you be doing these days?)*
> **Студент:** Я буду писати довгий текст, **щоб** закінчити мій важливий проект. *(I will write a long text in order to finish my important project.)*
> **Викладач:** Це той великий проект, **який** ви почали робити минулого тижня? *(Is that the big project that you started doing last week?)*
> **Студент:** Так, саме він. **Хоча** я дуже втомився, я маю його здати в понеділок зранку. *(Yes, exactly that one. Although I am very tired, I have to submit it on Monday morning.)*
> **Викладач:** А коли ви будете нормально відпочивати? *(And when will you rest normally?)*
> **Студент:** **Якщо** я здам проект у суботу, у неділю я із задоволенням зустрінуся з друзями в кафе. *(If I submit the project on Saturday, on Sunday I will gladly meet with friends in a cafe.)*

Студент природно використовує причину, мету, означення, допуст та умову, щоб побудувати логічну і зрозумілу розповідь.

<!-- INJECT_ACTIVITY: quiz-conjunction-id -->

## Частина 2: Вибери правильну форму (Part 2: Choose the Correct Form)

Вибрати правильний сполучник означає розуміти точний сенс вашої фрази. Англомовні студенти часто плутають причину та мету через різницю в перекладі. 
**Я йду в магазин, тому що мені потрібен свіжий хліб.** (I am going to the store because I need fresh bread.) — Це причина. Подія вже є фактом.
**Я йду в магазин, щоб купити свіжий хліб.** (I am going to the store in order to buy fresh bread.) — Це мета. Дія ще не відбулася.
Інша дуже типова помилка — це використання слова "якщо" (if-condition) замість "чи" (if-whether) для непрямих питань.
**Якщо він прийде сьогодні, ми почнемо працювати.** (If he comes today, we will start working.) — Умова.
**Я не знаю, чи він прийде сьогодні ввечері.** (I don't know if/whether he will come this evening.) — Непряме питання. В українській мові не можна казати "Я не знаю, якщо він прийде".

Слово **який** працює як прикметник у підрядному реченні. Воно завжди повинно ідеально відповідати роду та числу іменника, який воно замінює в головному реченні.
**Це цікава книжка (жін. р., одн.), яку я зараз із задоволенням читаю.** (This is an interesting book that I am now reading with pleasure.)
**Це велике місто (сер. р., одн.), яке мені дуже подобається.** (This is the large city that I really like.)
**Це розумні люди (мн.), які працюють зі мною в нашому офісі.** (These are the smart people who work with me in our office.)
Також ми часто використовуємо прийменники зі словом **який**, і тоді відмінок цього слова обов'язково змінюється.
**Це новий комп'ютер, на якому я працюю щодня.** (This is the new computer on which I work every day.)
**Це мій найкращий колега, з яким я роблю спільний проект.** (This is my best colleague with whom I am doing a joint project.)

Сполучник **щоб** має своє суворе граматичне правило. Воно стосується форми дієслова, яке йде безпосередньо після нього. Якщо в обох частинах речення дію виконує одна й та сама особа, ми використовуємо інфінітив.
**Я прийшов сюди, щоб купити квиток на вечірній поїзд.** (I came here in order to buy a ticket for the evening train.) — Я прийшов, і я куплю.
Але якщо особи різні, дієслово після **щоб** обов'язково стоїть у формі минулого часу. Це правило працює навіть тоді, коли сама дія відбудеться в далекому майбутньому.
**Я хочу, щоб ти купив квиток на вечірній поїзд.** (I want you to buy a ticket for the evening train. — Literally: I want so that you bought.) — Я хочу, а ти купиш.
**Наш директор просить, щоб ми закінчили цю важливу роботу сьогодні.** (Our director asks that we finish this important work today.)
Зверніть увагу на закінчення "-л-" у словах **купив**, **закінчили**. Воно є чітким маркером минулого часу, який тут вимагає граматика.

Щоб передати слова іншої людини, ми використовуємо непряму мову. На рівні A2 це дуже просто: ми використовуємо сполучник **що** (that). Час дієслова ніколи не змінюється.
Пряма мова: **Він каже: «Я дуже втомився після роботи».** (He says: "I am very tired after work.")
Непряма мова: **Він каже, що він дуже втомився після роботи.** (He says that he is very tired after work.)
Пряма мова: **Моя мама сказала: «Смачний обід вже повністю готовий».** (My mom said: "The delicious lunch is already completely ready.")
Непряма мова: **Моя мама сказала, що смачний обід вже повністю готовий.** (My mom said that the delicious lunch is already completely ready.)

Пунктуація у складних реченнях має одне золоте правило. Ви обов'язково повинні поставити **кома** (comma) перед сполучником, який починає підрядну частину. Це правило діє для всіх підрядних слів: **що**, **щоб**, **бо**, **тому що**, **який**, **де**, **якщо**, **хоча**. Кома показує необхідну логічну паузу для вашого слухача.
**Я точно знаю, що ти зараз знаходишся тут.** (I know for sure that you are located here now.)
**Вона уважно читає цю статтю, бо їй дуже цікаво.** (She is carefully reading this article because she is very interested.)

Давайте послухаємо, як два одногрупники самостійно перевіряють домашнє завдання.

> **Марко:** Послухай моє перше речення: «Це нова книжка який я купив вчора ввечері». *(Listen to my first sentence: "This is the new book which I bought yesterday evening.")*
> **Олена:** Тут є одна помилка. Слово «книжка» — жіночого роду. Тому треба обов'язково писати «книжка, яка». *(There is one error here. The word "книжка" is feminine. Therefore, you must write "книжка, яка".)*
> **Марко:** Я зрозумів правило. «Це нова книжка, яку я купив вчора ввечері». А як тобі тут: «Я читаю її тому що вона надзвичайно цікава». *(I understood the rule. "This is the new book that I bought yesterday evening." And how about here: "I am reading it because it is extremely interesting.")*
> **Олена:** Це майже правильно. Але де твоя **кома**? *(This is almost correct. But where is your comma?)*
> **Марко:** Точно! Я забув. Перед «тому що» завжди стоїть кома. *(Exactly! I forgot. Before "тому що" there is always a comma.)*
> **Олена:** Так, тепер ідеально. «Я читаю її, тому що вона надзвичайно цікава». *(Yes, now it is perfect. "I am reading it, because it is extremely interesting.")*

<!-- INJECT_ACTIVITY: fill-in-conjunction-form -->

## Частина 3: Побудуй складне речення (Part 3: Build Complex Sentences)

Тепер настав час об'єднати ваші знання. В академічному або сучасному професійному середовищі ми рідко говоримо короткими, дуже простими фактами. Ми комбінуємо їх. Це робить нашу мову дорослою, природною та переконливою.
Подивіться уважно на дві прості ідеї:
**Я щодня працюю у великій міжнародній компанії.** (I work every day in a large international company.)
**Ця міжнародна компанія постійно розробляє нове програмне забезпечення.** (This international company constantly develops new software.)
Ми можемо елегантно об'єднати їх за допомогою означального речення:
**Я працюю у великій міжнародній компанії, яка постійно розробляє нове програмне забезпечення.** (I work in a large international company that constantly develops new software.)

У робочому контексті ми надзвичайно часто говоримо про умови та складні реальні факти. Для цього ідеально підходять сполучники **якщо** та **хоча**.
**Якщо я успішно закінчу цей великий проект сьогодні, я отримаю хороший фінансовий бонус.** (If I successfully finish this big project today, I will receive a good financial bonus.)
**Якщо ми підпишемо цей важливий контракт завтра зранку, ми одразу почнемо роботу.** (If we sign this important contract tomorrow morning, we will immediately start the work.)
А ось практичні приклади з допустом, коли ми маємо справу з певними перешкодами або труднощами:
**Хоча в мене ще досить мало професійного досвіду, я дуже швидко вчуся.** (Although I still have quite a little professional experience, I learn very quickly.)
**Хоча наш рекламний бюджет зараз невеликий, ми гарантовано зробимо дійсно якісний продукт.** (Although our advertising budget is small now, we will guaranteed make a truly quality product.)

Коли ми плануємо подорожі, зустрічі або організовуємо події, ми будуємо наратив, який органічно поєднує мету та причину.
**Ми їдемо до Львова на вихідні, щоб побачити красиву архітектуру, бо це дуже гарне історичне місто.** (We are going to Lviv for the weekend in order to see the beautiful architecture, because it is a very nice historical city.)
**Я купив квитки в театр заздалегідь, щоб ми сиділи поруч, тому що там завжди дуже багато людей.** (I bought tickets to the theater in advance so that we sit next to each other, because there are always a lot of people there.)
Використання кількох підрядних частин в одному великому реченні — це чітка ознака міцного рівня A2+.

Прочитайте цей короткий текст. Зверніть увагу, як автор майстерно використовує всі п'ять типів сполучників, щоб створити зв'язну історію про свій звичайний день.

**Мій ідеальний день**
Мій день зазвичай починається з гарячої чорної кави, **яку** я дуже люблю пити зранку. Я п'ю її, **щоб** швидко прокинутися і мати багато необхідної енергії. **Хоча** я типова сова і люблю спати допізна, я встаю рано кожного ранку. **Якщо** я маю вільний час перед початком роботи, я довго гуляю в нашому тихому парку. Я щодня гуляю, **тому що** це дуже корисно для мого фізичного здоров'я. Мій директор на роботі завжди каже, **що** я маю чудовий настрій і заряджаю інших колег.

У цьому абзаці ми бачимо конкретні цілі, об'єктивні причини, життєві умови, детальні описи та навіть непряму мову. Текст звучить максимально природно та плавно.

Що чекає на вас далі в українській граматиці? На рівні B1 синтаксис стане ще багатшим і гнучкішим. Ви обов'язково вивчите нереальну умову за допомогою слова **якби** (if/would), яке дозволяє вільно говорити про гіпотетичне минуле або абсолютно неможливі речі. Також ви детально познайомитеся з новими офіційними сполучниками, такими як **оскільки** (since / because), та навчитеся самостійно будувати **складнопідрядні речення з кількома підрядними** (complex sentences with multiple subordinate clauses).

Але наразі запам'ятайте найголовніше: якщо ви впевнено використовуєте ці п'ять логічних зв'язків — **тому що / бо**, **щоб**, **який**, **якщо**, та **хоча**, ви вже можете успішно вирішити 90% ваших повсякденних комунікативних завдань. Ви здатні детально пояснити свої дії, описати складний світ навколо вас, поставити чіткі умови та правильно передати чужу інформацію.

<!-- INJECT_ACTIVITY: sort-conjunction-types -->

## Підсумок

Прочитайте ці запитання для вашої самоперевірки. Якщо ви можете впевнено відповісти «так» на кожне з них, ви успішно засвоїли тему складних речень на важливому рівні A2:

* Чи можу я пояснити причину своєї дії, використовуючи поширені сполучники **тому що** або **бо**?
* Чи можу я детально описати предмет чи людину за допомогою слова **який**, правильно змінюючи його закінчення (який, яка, яке, які)?
* Чи можу я висловити точну мету моїх дій, використовуючи **щоб** та інфінітив дієслова?
* Чи можу я поставити конкретну умову для майбутньої події за допомогою слова **якщо**?
* Чи можу я додати зауваження або показати несподіваний результат ситуації за допомогою **хоча**?
* Чи можу я передати слова іншої людини, використовуючи непряму мову і сполучник **що**?
* Чи пам'ятаю я про те, що перед підрядним сполучником обов'язково має стояти **кома**?

Якщо у вас виникають будь-які сумніви, просто поверніться до відповідної частини цього модуля та ще раз уважно перегляньте приклади. Правильне використання складних речень робить вашу українську мову дуже багатою, по-справжньому дорослою та логічною.
```

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-syntax
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

**Level: A2 (Module 53/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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
