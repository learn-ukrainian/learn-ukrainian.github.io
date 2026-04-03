<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/figurative-motion.yaml` file for module **31: Час іде, дощ іде** (b1).

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

(No injection markers found in prose. All activities will go to workbook.)

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify whether a motion verb is used literally or figuratively in a sentence
  items: 12
  type: quiz
- focus: Complete Ukrainian figurative expressions with the correct motion verb
  items: 12
  type: fill-in
- focus: Match figurative motion expressions with their meanings
  items: 12
  type: match-up
- focus: 'Sort motion verb uses: literal / figurative — time / weather / abstract'
  items: 12
  type: group-sort
- focus: Fix English calques and Russicisms in figurative motion expressions
  items: 12
  type: error-correction
- focus: Write a paragraph about your week using at least 5 figurative motion expressions
  items: 12
  type: free-write


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- 'злетіти (to soar — figurative: prices soar)'
- водити за ніс (to deceive — idiom)
- вийти (to turn out / result)
- підійти (to suit — figurative)
- дійти до висновку (to reach a conclusion)
- обійтися (to get by without)
- хмари пливуть (clouds drift)
- мурашки біжать (goosebumps)
- багатозначне слово (polysemous word)
- фразеологізм (phraseological unit / idiom)
required:
- переносне значення (figurative meaning)
- пряме значення (literal meaning)
- дощ іде (it's raining — figurative use of іти)
- час іде (time passes)
- час летить (time flies)
- справи йдуть (things are going — about progress)
- мова йде про (it's about / the topic is)
- 'йтися (impersonal — to be about: йдеться про)'
- нести відповідальність (to bear responsibility)
- вести переговори (to conduct negotiations)
- вести себе (to behave)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Дієслова руху в переносному значенні: Філософія простору і часу

> — **Оксана:** Дивись, як швидко на вулиці посіріло. Раптом зірвався такий сильний вітер. Мабуть, зараз піде дощ! *(Look how quickly it has gotten gray outside. Suddenly such a strong wind has picked up. It will probably rain soon!)*
> — **Тарасик (5 років):** Піде?! А куди він піде? А хіба дощ може ходити? У нього ж зовсім немає ніг! *(It will go?! And where will it go? But can rain walk? It has no legs at all!)*
> — **Оксана:** Дощ не ходить ногами, дурнику. Він просто падає з неба. Але ми завжди кажемо, що він іде. *(Rain doesn't walk with legs, silly. It just falls from the sky. But we always say that it is walking.)*
> — **Тарасик:** Тоді і сніг ходить? І туман? *(Then does snow walk too? And fog?)*
> — **Оксана:** Сніг іде. А туман — пливе. *(Snow goes. And fog — swims.)*

Українські дієслова руху описують не лише фізичне переміщення, але й абстрактні процеси: час, погоду, стан справ, людські емоції. Слов'янські мови зберегли глибоке анімістичне сприйняття світу, де явища природи мають власну волю та напрямок руху. Для української культурної ментальності навколишній світ — це активний потік подій. Дощ — іде, туман — пливе, а час — летить. Розуміння полісемії (багатозначності) дієслів руху — це ваш справжній ключ до природного українського мислення.

## Iти / ходити: найширший спектр

Дієслово «іти» (та його недоконана пара багаторазової дії «ходити») є універсальним маркером тривалого, рівномірного процесу, який відбувається у природному і спокійному темпі.

*   **Погода:** Дощ іде, сніг іде. В українській мові атмосферні опади завжди є активними суб'єктами дії. «Надворі вже третю годину поспіль йде сильний дощ».
*   **Час:** Час іде, роки йдуть. Ця класична метафора описує нормальний, спокійний ритм людського буття. «Наш час іде дуже швидко», «Роки йдуть, а діти виростають».
*   **Процеси та події:** Урок іде, фільм іде, переговори йдуть, ремонт іде. Будь-який організований процес «іде», коли він знаходиться в активній фазі. «Який фільм зараз іде в кінотеатрі?», «Мої справи йдуть дуже добре».
*   **Тематика:** Мова йде про / йдеться про *(it's about / the topic is)*. «У цій новій статті йдеться про глобальні зміни клімату».

Додавання просторових префіксів розширює абстрактне значення базового слова:

*   **Вийти** *(to turn out / to result)*: Описує фінальний результат процесу. «Пиріг вийшов надзвичайно смачним», «З цього конфлікту нічого доброго не вийшло».
*   **Підійти** *(to suit / to fit)*: Означає гармонійну відповідність. «Цей зелений колір тобі ідеально підходить», «Ця робота мені абсолютно не підходить».
*   **Дійти до висновку** *(to reach a conclusion)*: Академічний вираз для логічного рішення. «Наші експерти дійшли до висновку».
*   **Прийти** *(to come to mind / to arrive)*: Раптові ідеї або настання періоду. «Мені прийшла геніальна ідея», «Прийшов час діяти».
*   **Зайти** *(to go too far)*: Перетин моральної межі. «Ти зайшов надто далеко у своїх звинуваченнях».
*   **Обійтися** *(to get by without / to manage)*: Здатність впоратися без чогось. «Сьогодні ми обійдемося без цукру в каві».

<!-- INJECT_ACTIVITY: activity_1 -->

## Летіти: швидкість

Дієслово «летіти» у переносному значенні є потужним стилістичним інструментом для передачі шаленої динаміки, екстремальної швидкості та стрімких змін, які значно перевищують наш спокійний контроль.

*   **Час і вік:** Час летить *(time flies)*. Ця фраза використовується, коли приємні події відбуваються настільки стрімко, що ми фізично не встигаємо насолодитися моментом. «Мої завантажені робочі дні просто летять з неймовірною швидкістю!»
*   **Інформація:** Новина облетіла місто. Інформація поширюється так швидко, ніби має невидимі крила. «Ця шокуюча новина миттєво облетіла все місто».
*   **Економіка та кар'єра:** Ціни злетіли, кар'єра злетіла. Траєкторія руху візуально нагадує зліт ракети. «Минулої осені ринкові ціни на овочі стрімко злетіли вгору».

Префіксальні форми додають сильного емоційного забарвлення:

*   **Вилетіти** *(to get fired / to get expelled / to slip one's mind)*: Примусова втрата статусу або миттєва втрата пам'яті. «Він з ганьбою вилетів з престижної роботи», «Це просто вилетіло мені з голови».
*   **Пролетіти** *(to fly by / to miss out)*: «Ці три місяці літніх канікул пролетіли як один день».
*   **Налетіти** *(to swoop in / to rush at)*: Раптова поява чогось небезпечного. «Раптом налетів холодний вітер», «На компанію налетіли фінансові борги».

<!-- INJECT_ACTIVITY: activity_2 -->

## Пливти: плавність і повільність

Дієслово «пливти» (та поетичний синонім «плинути») створює атмосферу абсолютної плавності, природної гармонії, заспокійливої повільності і відсутності перешкод. Об'єкт граційно ковзає у просторі.

*   **Природа:** Туман пливе, хмари пливуть, місяць пливе. Безмежне небо концептуалізується як глибокий океан. «Над річкою повільно пливе густий білий туман».
*   **Звук і музика:** Мелодія пливе. Звукові акустичні хвилі поводяться як невидима рідина, м'яко заповнюючи простір. «У порожній кімнаті ніжно і трохи сумно пливе мелодія».
*   **Думки і час:** Думки пливуть, час пливе. На відміну від стресового «час летить», вираз «час пливе» означає глибокий внутрішній спокій та приємну фізичну розслабленість. «Ми сиділи біля теплого каміна, і наш спільний час плив абсолютно непомітно».

<!-- INJECT_ACTIVITY: activity_3 -->

## Бігти, їхати, нести та інші

Українська мова має у своєму лексичному арсеналі й інші барвисті дієслова руху, які суттєво розширюють спектр наших емоційних описів.

*   **Бігти (нервовість, рідини, стрес):** Активний, часто тривожний і напружений ритм.
    *   «Час біжить» (коли ми маємо багато термінових справ і втрачаємо контроль).
    *   «Вода біжить», «сльози бігли по щоках» (рух неживої рідини поетично порівнюється з бігом живої істоти).
    *   «Мурашки бігли по шкірі» *(goosebumps)*, «мороз побіг поза спиною» (фізіологічні реакції на сильний страх чи різкий холод).
*   **Їхати (психологічне перевантаження):** У сучасному сленгу додає саркастичної емоційності.
    *   «Дах їде» *(going crazy)* — стан при екстремальному стресі, коли людина не витримує навантаження.
    *   «Поїхав на цій темі» *(became obsessed)*.
*   **Котитися (об'ємний звук і життєве падіння):**
    *   «Сміх покотився по залу» (гучний звук, що відбивається від стін луною).
    *   «Життя покотилося вниз» (швидка і невідворотна моральна чи економічна деградація).
*   **Нести / носити (вага та відповідальність):** Передає моральну напругу та юридичну значущість.
    *   «Нести відповідальність» *(bear responsibility)*.
    *   «Вулиця носить ім'я» *(bears the name)* — збереження історичної пам'яті.
    *   «Виносити рішення» *(render a decision)*.
*   **Вести / водити (лідерство, маніпуляції):** Свідоме управління та соціальна взаємодія.
    *   «Вести переговори» *(conduct negotiations)*.
    *   «Вести себе» *(behave oneself)*.
    *   «Водити за ніс» *(lead by the nose / deceive)* — хитро маніпулювати іншою людиною.

<!-- INJECT_ACTIVITY: activity_4 -->

## Українські вирази vs англійські кальки

Калькування — це дослівне, сліпе копіювання іноземних лексичних структур. Воно руйнує автентичність і милозвучність українського мовлення. Назавжди забудьте про такі типові помилки:

*   **Опади:** В англійській мовній картині світу дощ просто підкоряється гравітації (*rain falls*). Під цим впливом студенти часто кажуть незграбне «дощ падає». Українською єдиний правильний варіант — **дощ іде**. Падати може стигле яблуко зі столу, але не могутнє атмосферне явище.
*   **Справи:** Популярне англійське питання *how are things?* часто дослівно перекладають як «як є справи?». В українській мові абстрактні процеси завжди перебувають у стані руху. Правильно питати: **як ідуть твої справи?**. Правильна відповідь: **мої справи йдуть добре**.
*   **Фільми:** Замість використання штучних пасивних конструкцій для перекладу *a new film is showing*, використовуйте активну дію базового дієслова: **у нашому кінотеатрі зараз іде цікавий фільм**.
*   **Тема розмови:** Уникайте прямої кальки з російського виразу *«речь идет»* у фонетично неприємній формі *«мова іде про»* (тут виникає збіг голосних "а-і"). Використовуйте стягнену форму **мова йде про** або більш вишукану безособову форму **йдеться про**.
*   **Процеси:** Ніколи не використовуйте незграбний вираз *«діло йде до»* (пряма калька з російського *«дело идет к»*). Краще використовувати: **справа йде до завершення**, або **річ у тім, що** *(the point is that)*.

<!-- INJECT_ACTIVITY: activity_5 -->

## Підсумок: буквальне і переносне

Переносне вживання дієслів руху — це не просто декоративний елемент, а фундаментальна основа щоденної комунікації носіїв української мови. Синтез буквального і переносного дозволяє мислити категоріями простору та часу:

*   **Іти / ходити:** Універсальний ритм природи та буття (дощ іде, час іде, процеси йдуть).
*   **Летіти:** Екстремальна швидкість, непідвладна контролю (час летить, ціни злетіли, новини облетіли).
*   **Пливти:** Гармонія, медитативна повільність (туман пливе, мелодія пливе, думки пливуть).
*   **Бігти / їхати:** Нервовість, стрес, рідини (сльози біжать, дах їде).
*   **Нести / вести:** Вага відповідальності та управління процесами (нести відповідальність, вести переговори).

Розуміння цієї унікальної філософії простору дозволить вам назавжди перестати механічно перекладати слова у своїй голові і почати відчувати мову інтуїтивно.

<!-- INJECT_ACTIVITY: activity_6 -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: figurative-motion
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

**Level: B1 (Module 31)**

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
