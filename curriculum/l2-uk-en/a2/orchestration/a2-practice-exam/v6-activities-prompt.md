<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a2-practice-exam.yaml` file for module **68: Пробний іспит** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-reading-comprehension -->`
- `<!-- INJECT_ACTIVITY: quiz-mixed-grammar -->`
- `<!-- INJECT_ACTIVITY: true-false-grammar-accuracy -->`
- `<!-- INJECT_ACTIVITY: error-correction-l2-pitfalls -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Simulated exam — mixed grammar questions (cases, aspect, comparison)
  items: 8
  type: quiz
- focus: Reading comprehension — answer questions about a Ukrainian text
  items: 8
  type: fill-in
- focus: Grammar accuracy check — identify correct vs incorrect sentences
  items: 8
  type: true-false
- focus: Find and correct grammar errors in sentences covering module topics
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- самооцінка (self-assessment)
- оцінка (grade, assessment)
- правильний (correct)
required:
- іспит (exam)
- завдання (task, exercise)
- відповідь (answer)
- питання (question)
- читання (reading)
- письмо (writing)
- граматика (grammar)
- результат (result)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ

Вітаємо! Ви майже завершили рівень А2. Цей модуль — це ваш **пробний іспит** (mock exam). Він допоможе вам зрозуміти, наскільки добре ви знаєте граматику, вмієте читати і писати українською мовою. Іспит — це не стрес, а чудова можливість показати свої знання і побачити прогрес. 

Важливо запам'ятати одну річ: українською мовою ми кажемо **«складати іспит»** (to take an exam). Дуже часто студенти роблять помилку і кажуть «здавати іспит», але це калька з російської мови. Правильно — тільки «складати іспит». 

Цей тест має три частини: читання, граматика та письмо. Виконайте всі **завдання** (tasks) уважно і не поспішайте. Ваша **відповідь** (answer) на кожне **питання** (question) покаже ваш справжній **результат** (result). Бажаємо успіху та натхнення на цьому фінальному етапі курсу!

## Частина 1: Читання (Part 1: Reading)

У цій частині ми перевіримо ваше **читання** (reading). Читання на іспиті вимагає уваги та правильної техніки. Щоб успішно виконати завдання, вам потрібні дві стратегії читання. 

Перша стратегія — це пошукове читання (scanning for specific information). Наприклад, ви читаєте текст, щоб швидко знайти конкретні дати, цифри, ціни або імена людей. Ви не читаєте кожне слово, ви просто швидко шукаєте потрібну інформацію. Друга стратегія — це вивчальне читання (deep comprehension). Ви уважно і повільно читаєте весь текст, щоб зрозуміти його головний **зміст** (content), зробити висновки та зрозуміти логіку автора. 

У цій секції ви прочитаєте три різні тексти: **оголошення** (announcement), повідомлення від друга та коротку розповідь про традиції. Звертайте увагу на контекст і намагайтеся зрозуміти нові слова без словника.

**Текст А: Інформаційне повідомлення**
Спробуйте швидко знайти в цьому тексті час, дні тижня та ціну. Це типове оголошення про мовні курси.

> Запрошуємо всіх охочих на нові курси української мови! Наші заняття допоможуть вам швидко і легко опанувати мову. Курс починається п'ятнадцятого травня. Ми пропонуємо ранкові та вечірні групи, щоб вам було зручно. Заняття проходять тричі на тиждень: у понеділок, середу та п'ятницю. Ранкова група займається о десятій годині ранку, а вечірня — о сьомій годині вечора. Наша адреса: вулиця Володимирська, будинок п'ятдесят два. Перше пробне заняття абсолютно безкоштовне! Далі вартість курсу становить дві тисячі гривень за місяць. Для реєстрації, будь ласка, зателефонуйте нам або напишіть на електронну пошту. Чекаємо на вас з нетерпінням!

**Текст Б: Електронний лист від друга**
Цей текст перевіряє ваше детальне розуміння. Прочитайте його уважно. Зверніть увагу на дієслова у минулому часі та майбутньому часі.

> Привіт, друже! Як твої справи? Сподіваюся, у тебе все чудово. Я пишу тобі, щоб поділитися новинами. Минулого тижня я нарешті переїхав до Києва! Це велике і дуже красиве місто. Я вже знайшов нову роботу. Тепер я працюю в ІТ-компанії в центрі міста. Моя нова квартира невелика, але дуже затишна. Вона знаходиться недалеко від парку, тому я часто гуляю там вечорами.
> Наступних вихідних я планую відпочивати. У суботу я буду працювати вранці, а потім ми з друзями підемо в кіно. У неділю я хочу поїхати за місто, щоб побути на природі. Можливо, ти хочеш приїхати до мене в гості? Ми могли б разом піти в музей або просто випити кави в кафе. Напиши мені, що ти думаєш. Чекаю на твою відповідь! Твій друг, Андрій.

**Текст В: Наратив про традиції**
Останній текст — це коротка розповідь про українську традицію. Тут є нові слова з культурного контексту. Спробуйте зрозуміти їхнє значення.

> Я хочу розповісти вам про одну з найважливіших українських традицій — Святвечір. Це свято, яке українці відзначають напередодні Різдва. У цей день уся родина збирається разом за одним великим столом. Традиційно на столі має бути дванадцять пісних страв, тому що вони символізують дванадцять апостолів.
> Головна страва вечора — це **кутя** (sweet wheat porridge). Її готують із пшениці, маку, горіхів, меду та родзинок. Вона дуже смачна і солодка. Крім куті, ми завжди готуємо **вареники** (dumplings) з картоплею та капустою, гриби, рибу, борщ та солодкий узвар. Коли на небі з'являється перша зірка, ми починаємо вечеряти. Ми співаємо різдвяні пісні, які називаються **колядки** (carols). Це дуже тепле, світле і радісне родинне свято. Я дуже люблю цей день, бо він нагадує мені про моє дитинство і бабусин дім.

<!-- INJECT_ACTIVITY: fill-in-reading-comprehension -->

## Частина 2: Граматика (Part 2: Grammar)

Ваша **граматика** (grammar) на рівні А2 — це міцна база для вільного спілкування. На іспиті ми перевіримо ключові граматичні зони: відмінки іменників, дієвідміни, часи та займенники. Важлива порада: завжди звертайте увагу на прийменники-маркери у реченні. Прийменники «без» (without), «до» (to), «у/в» (in/at), «над» (above) швидко підкажуть вам правильний відмінок.

### Секція А: Іменники та відмінки (Nouns and Cases)
На іспиті ви побачите різні типи речень, де треба обрати правильний відмінок. Ми перевіряємо чотири основні конструкції:
1. **Конструкція відсутності (Absence).** Після слів «немає», «не було», «не буде» та прийменника «без» ми використовуємо родовий відмінок (Genitive):
   - У мене немає **часу** на відпочинок (I don't have time for rest).
   - Ми будемо працювати без **перерви** (We will work without a break).
   - У нас не було **молока** (We didn't have milk).
2. **Конструкція напрямку (Direction).** Якщо ви йдете кудись, ви використовуєте прийменник «до» + родовий відмінок або «в/на» + знахідний відмінок (Accusative):
   - Я йду до **школи** (I am going to school).
   - Я йду в **магазин** (I am going to the store).
   - Вона їде на **роботу** (She is going to work).
3. **Конструкція місця (Place).** Якщо ви вже знаходитесь десь, ви використовуєте місцевий відмінок (Locative):
   - Я живу в **Одесі** (I live in Odesa).
   - Моє місто знаходиться на **Заході** (My city is located in the West).
   - Книга лежить на **столі** (The book is lying on the table).
4. **Істоти та неістоти (Animate vs Inanimate).** У знахідному відмінку чоловічий рід змінюється по-різному:
   - Я бачу **друга** (I see a friend — animate, takes genitive ending).
   - Я бачу великий **парк** (I see a big park — inanimate, takes nominative ending).

### Секція Б: Дієслівні форми (Verb Forms)
Ми ретельно перевіряємо, як ви використовуєте дієслова. Особлива увага — неправильні дієслова: «бути» (to be), «їсти» (to eat), «дати» (to give), «відповісти» (to answer). 
- Я **їм** яблуко, ти **їси** борщ, вона **їсть** салат, ми **їмо** вареники, ви **їсте** піцу, вони **їдять** торт.
- Я **дам** тобі книгу, ти **даси** мені ручку, він **дасть** нам воду, ми **дамо** вам час, ви **дасте** гроші, вони **дадуть** відповідь.

У минулому часі найважливіше — узгодження за родом (gender agreement):
- Петро **сказав** (Peter said — masculine).
- Марія **сказала** (Maria said — feminine).
- Сонце **зійшло** (The sun rose — neuter).
- Діти **сказали** (The children said — plural).

Також ви повинні знати складену форму майбутнього часу (compound future tense) для недоконаного виду:
- Я **буду складати** іспит завтра (I will be taking the exam tomorrow).
- Ти **будеш писати** довгий лист (You will be writing a long letter).
- Вони **будуть працювати** весь день (They will be working all day).

### Секція В: Займенники та порівняння (Pronouns and Comparison)
У змішаній секції граматики ми перевіряємо зворотні займенники «свій» (one's own) та «себе» (oneself). 
- Я бачу **себе** у дзеркалі (I see myself in the mirror).
- Він бере **свій** зошит, а не мій (He takes his [own] notebook, not mine).
- Вона любить **свою** роботу (She loves her [own] work).

Також ми використовуємо неозначені займенники (indefinite pronouns) з частками «-сь» та «будь-»:
- **Хтось** стукає у двері (Someone is knocking on the door).
- Я хочу з'їсти **щось** солодке (I want to eat something sweet).
- Ви можете вибрати **будь-який** день для зустрічі (You can choose any day for the meeting).

Нарешті, ви побачите простий ступінь порівняння прикметників (comparatives):
- Цей поїзд **швидший**, ніж автобус (This train is faster than the bus).
- Ця ідея набагато **краща** (This idea is much better).
- Мій брат **старший** за мене (My brother is older than me).

<!-- INJECT_ACTIVITY: quiz-mixed-grammar -->
<!-- INJECT_ACTIVITY: true-false-grammar-accuracy -->

## Частина 3: Спілкування та письмо (Part 3: Communication and Writing)

На письмовому іспиті перше завдання — це доповнення діалогу (Dialogue completion). Ви побачите природну розмову, наприклад, у кафе або під час планування подорожі, де потрібно заповнити шість пропусків правильними словами чи цілими фразами. Це перевіряє ваше вміння розуміти контекст.

Друга частина — це симуляція усного іспиту. Уявіть, що перед вами сидить **екзаменатор** (examiner) і ставить вам питання про ваше життя: розкажіть про свій день, що ви робили вчора, які плани на літо. Ваша відповідь має бути детальною і граматично правильною. Якщо ви не почули питання, використовуйте ввічливі форми.

Прочитайте цей діалог — це типова симуляція усного іспиту:

> **Екзаменатор:** Добрий день! Будь ласка, розкажіть про свій типовий день.
> **Кандидат:** Добрий день! Зазвичай я прокидаюся о сьомій ранку. Я снідаю і йду на роботу в офіс.
> **Екзаменатор:** Зрозуміло. А що ви робили вчора ввечері?
> **Кандидат:** Учора я читав книгу і дивився цікавий фільм. 
> **Екзаменатор:** Які у вас плани на літо? 
> **Кандидат:** Я планую поїхати в гори, тому що я дуже люблю природу.
> **Екзаменатор:** Добре. Порівняйте Київ і ваше рідне місто.
> **Кандидат:** Київ більший і галасливіший, ніж моє місто. Моє місто спокійніше і набагато менше.
> **Екзаменатор:** Останнє запитання. Опишіть свою сім'ю.
> **Кандидат:** Моя сім'я невелика. У мене є мама, тато і молодший брат. 
> **Екзаменатор:** Дякую! Вибачте, чи не могли б ви повторити, скільки років вашому брату?
> **Кандидат:** Йому десять років.
> **Екзаменатор:** Чудово. Дякую за відповіді.

### Підготовка до письмового завдання
Для письмового завдання (Guided writing) вам потрібно написати коротке есе на 80-100 слів. Дуже важливо структурувати свій текст. Використовуйте логічні зв'язки (logical connectors). Наприклад: «спочатку» (first), «тому що» (because), «нарешті» (finally), «також» (also). Вони роблять ваш текст природним і красивим. Коли ви пишете своє есе, екзаменатори оцінюють ваш текст за чіткими критеріями (scoring rubric). Головне — це граматична точність (grammar accuracy), тобто правильні відмінки і час дієслова. Також оцінюється ваш словниковий запас (vocabulary range), логічність тексту (coherence) та повне виконання завдання (task completion).

На іспиті ви можете вибрати одну з трьох тем для вашого есе:
1. Мій улюблений сезон і чому я його люблю.
2. Електронний лист другу про мої плани на вихідні.
3. Моя родина та наші традиції (або святкова традиція, яка вам подобається).

### Аналіз типових помилок (L2 Interference)
Коли студенти пишуть есе, вони часто використовують російські кальки (calques) або роблять буквальні переклади з англійської. Зверніть увагу на ці типові помилки і ніколи не робіть їх на своєму іспиті:
- Не пишіть «вірна відповідь». Слово «вірний» означає "loyal" (наприклад, вірний друг або вірний пес). Правильно казати: **правильна відповідь** (correct answer).
- Не пишіть «приймати участь». В українській мові правильно казати: **брати участь** (to take part / to participate). Наприклад: «Я хочу брати участь у цьому проекті».
- Не кажіть «я вибачаюсь». Ця зворотна форма закінчується на «-сь», що означає дію, спрямовану на себе. Це буквально перекладається як "I forgive myself". Якщо ви хочете попросити вибачення в іншої людини, правильно казати: **Вибачте!** (Excuse me / Sorry!) або **Перепрошую!** (I apologize!).

<!-- INJECT_ACTIVITY: error-correction-l2-pitfalls -->

## Результати та самооцінка (Results and Self-Assessment)

Після іспиту найважливіше — це ваша **самооцінка** (self-assessment). Ви повинні проаналізувати свої помилки, щоб більше їх не повторювати. Зрозуміти, чому відповідь є правильною, — це теж частина навчання. 

Давайте розглянемо кілька типових ситуацій та пояснень до тестових завдань:
- Чому в реченні «Він пішов у кіно без подруги» правильна відповідь саме **подруги**? Тому що прийменник «без» завжди вимагає родового відмінка (Genitive case). Якщо ви вибрали називний чи давальний відмінок, вам треба повторити тему відмінків після прийменників.
- Чому ми кажемо «Я буду **складати** іспит», а не «Я буду здавати іспит»? Тому що дієслово «здавати» у цьому контексті — це типовий суржик. В українській літературній мові для іспитів та тестів існує лише правильне дієслово «складати».
- Чому ми кажемо «У мене болить голова», а не «Я маю головний біль»? Тому що буквальна калька з англійської "I have a headache" звучить дуже неприродно і штучно. Для опису стану здоров'я українці використовують безособову конструкцію «У мене болить + називний відмінок».
- У завданні на порівняння: чому ми кажемо «Мій дім більший **за** твій»? В українській мові при порівнянні ми часто використовуємо прийменник «за» плюс знахідний відмінок замість сполучника «ніж». Це робить речення набагато більш природним у розмовній мові.

### Сітка самооцінки А2
Щоб зрозуміти свій рівень, прочитайте ці твердження і оцініть кожну свою навичку за трьома рівнями: Сильний (Strong), У процесі розвитку (Developing), або Потребує роботи (Needs Work). Будьте чесними із собою. 
- Я можу впевнено розповісти про свою роботу, хобі, родину та свій типовий день.
- Я розумію короткі тексти про повсякденне життя, такі як електронні листи, оголошення та розклади.
- Я правильно вживаю основні відмінки (Знахідний, Родовий, Місцевий) разом із потрібними прийменниками.
- Я вмію правильно утворювати форми минулого і складеного майбутнього часу для дієслів недоконаного виду.
- Я можу написати структурований лист другові про свої плани, використовуючи логічні зв'язки.
- Я знаю, як правильно будувати прості складнопідрядні речення зі словами «тому що», «який», «що».

### Рекомендації та мотивація
Якщо ваш загальний **результат** (result) на іспиті становить менше ніж сімдесят відсотків, не засмучуйтесь і не зупиняйтесь! Це лише означає, що вам потрібно трохи більше часу на практику і закріплення матеріалу. Рекомендуємо вам повернутися до модулів п'ятдесят-шістдесят і ретельно повторити правила узгодження відмінків та видові пари дієслів. Якщо ж ваша **оцінка** (grade) вища за сімдесят відсотків — ми вас щиро вітаємо! Це дуже **правильний** (correct) шлях. Ви успішно засвоїли базову граматику української мови. Ваш словниковий запас і розуміння логіки мови достатні для того, щоб впевнено розпочати навчання на рівні B1. Попереду багато цікавого та нового матеріалу!

## Підсумок

Пробний іспит — це не просто тест, а важливий крок у вашому навчанні. Ви перевірили свої сили в читанні, згадали всі ключові правила граматики та спробували свої навички у спілкуванні й письмі. Тепер ви знаєте, як працювати з текстами різних жанрів, як правильно будувати речення з відмінками, і як уникати типових помилок, таких як російські кальки чи неправильні переклади. 

Ваш шлях від початківця до впевненого користувача рівня А2 успішно завершено. Українська мова відкриває для вас нові двері — це можливість розуміти багату культуру, вільно спілкуватися з носіями мови і читати автентичні тексти. Пишайтеся своїм результатом! Кожна ваша правильна відповідь — це результат вашої великої праці та щоденної дисципліни. Відпочиньте, зробіть паузу і з новими силами готуйтеся до мовних відкриттів. До зустрічі на рівні B1!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a2-practice-exam
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

**Level: A2 (Module 68/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
