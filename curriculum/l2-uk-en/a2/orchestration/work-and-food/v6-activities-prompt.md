<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/work-and-food.yaml` file for module **30: Професії та кулінарія** (a2).

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

- `<!-- INJECT_ACTIVITY: professions-match -->`
- `<!-- INJECT_ACTIVITY: kitchen-fill -->`
- `<!-- INJECT_ACTIVITY: workday-tf -->`
- `<!-- INJECT_ACTIVITY: functions-quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete a recipe description with correct Instrumental forms for tools and
    ingredients
  items: 8
  type: fill-in
- focus: Match profession questions to appropriate Instrumental answers
  items: 8
  type: match-up
- focus: Identify which Instrumental function (tool, companion, profession, spatial)
    is used in each sentence
  items: 8
  type: quiz
- focus: Judge whether sentences about a workday use correct Instrumental forms
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- рецепт (recipe)
- інгредієнт (ingredient)
- нарада (meeting)
- колега (colleague)
- начальник (boss)
required:
- готувати (to cook, to prepare)
- різати (to cut)
- мішати (to stir, to mix)
- посипати (to sprinkle)
- подавати (to serve)
- вареники (varenyky, dumplings)
- картопля (potato)
- помідор (tomato)
- огірок (cucumber)
- сіль (salt)
- олія (oil)
- виделка (fork)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Розмова про професії (Talking About Professions)

> — **Олег:** Максиме, ким ви працюєте? *(Maksym, who do you work as?)*
> — **Максим:** Я працюю **шеф-кухарем** *(head chef)* у ресторані. *(I work as a head chef in a restaurant.)*
> — **Олег:** Ви з дитинства мріяли стати кухарем? *(Did you dream of becoming a cook since childhood?)*
> — **Максим:** Ні, у дитинстві я хотів бути **пілотом** *(pilot)*. А ким працюєте ви? *(No, in childhood I wanted to be a pilot. And who do you work as?)*
> — **Олег:** Я працюю фінансовим **аналітиком** *(analyst)*. *(I work as a financial analyst.)*
> — **Максим:** Чим ви цікавитеся у вільний час? *(What are you interested in during your free time?)*
> — **Олег:** Я захоплююся **кулінарією** *(cooking)* та багато готую вдома. *(I am passionate about cooking and cook a lot at home.)*

Ви вже знаєте, як сказати про професію: «Я лікар». *(You already know how to say about a profession: "I am a doctor".)*
Тут ми використовуємо називний відмінок. *(Here we use the Nominative case.)*
Але українці частіше запитують: «**Ким ви працюєте?**» *(But Ukrainians more often ask: "Who do you work as?")*
Дієслово **працювати** *(to work)* вимагає орудного відмінка. *(The verb to work requires the Instrumental case.)*
Ми відповідаємо: «Я працюю **лікарем** *(doctor)*» або «Він працює **вчителем** *(teacher)*». *(We answer: "I work as a doctor" or "He works as a teacher".)*
The Instrumental case here denotes a professional role or a temporary state of being rather than a permanent identity.

Masculine nouns ending in a hard consonant take the ending **-ом**.
Наприклад, **програміст** *(programmer)* стає **програмістом**. *(For example, programmer becomes programmer.)*
Masculine nouns ending in a soft consonant або «й» take the ending **-ем** або **-єм**.
Наприклад, **водій** *(driver)* стає **водієм**, а лікар стає лікарем. *(For example, driver becomes driver, and doctor becomes doctor.)*
Some nouns ending in «-ар» have a soft declension, so **секретар** *(secretary)* becomes **секретарем**. *(Some nouns ending in "-ar" have a soft declension, so secretary becomes secretary.)*
Feminine nouns ending in «-а» change to **-ою**.
Наприклад, **дизайнерка** *(designer)* стає **дизайнеркою**. *(For example, designer becomes designer.)*
Feminine nouns ending in «-я» change to **-ею** або **-єю**.
Наприклад, **продавчиня** *(saleswoman)* стає **продавчинею**. *(For example, saleswoman becomes saleswoman.)*

Ми також використовуємо орудний відмінок, коли говоримо про минуле або майбутнє. *(We also use the Instrumental case when we talk about the past or the future.)*
The verb **бути** *(to be)* in the past or future tense triggers the Instrumental case.
У дитинстві я хотів бути **космонавтом** *(astronaut)*. *(In childhood I wanted to be an astronaut.)*
Вона мріяла бути **письменницею** *(writer)*. *(She dreamed of being a writer.)*
Ми часто використовуємо дієслово **стати** *(to become)* з орудним відмінком. *(We often use the verb to become with the Instrumental case.)*
Мій син хоче стати **поліцейським** *(police officer)*. *(My son wants to become a police officer.)*

Окрім роботи, ми маємо хобі та інтереси. *(Besides work, we have hobbies and interests.)*
Ми використовуємо дієслово **цікавитися** *(to be interested in)*, щоб розповісти про наші захоплення. *(We use the verb to be interested in to tell about our passions.)*
This verb requires the Instrumental case without a preposition.
Я цікавлюся **історією** *(history)* та **літературою** *(literature)*. *(I am interested in history and literature.)*
Ми також використовуємо дієслово **захоплюватися** *(to be passionate about)* для сильних емоцій. *(We also use the verb to be passionate about for strong emotions.)*
Вона захоплюється **фотографією** *(photography)*. *(She is passionate about photography.)*
Для активності ми використовуємо дієслово **займатися** *(to be engaged in / to do)*. *(For activity we use the verb to be engaged in.)*
Ми займаємося **спортом** *(sports)* щодня. *(We do sports every day.)*

<!-- INJECT_ACTIVITY: professions-match -->

## На кухні: Готуємо разом (In the Kitchen: Cooking Together)

> — **Олена:** Ігорю, що ми маємо робити на кухні спочатку? *(Ihor, what do we have to do in the kitchen first?)*
> — **Ігор:** Спочатку треба порізати свіжу моркву гострим ножем. *(First we need to cut fresh carrot with a sharp knife.)*
> — **Олена:** Добре, я вже ріжу моркву на дошці. А картоплю ми варимо з сіллю? *(Good, I am already cutting the carrot on the board. And do we boil the potato with salt?)*
> — **Ігор:** Так, але білу сіль ми додаємо у воду трохи пізніше. *(Yes, but we add white salt to the water a little later.)*
> — **Олена:** Скажи, будь ласка, чим краще мішати цей гарячий борщ? *(Tell me, please, what is it better to stir this hot borscht with?)*
> — **Ігор:** Мішай його тільки великою дерев'яною ложкою. *(Stir it only with a large wooden spoon.)*
> — **Олена:** Я все зрозуміла. А з чим ми будемо його їсти сьогодні? *(I understood everything. And what will we eat it with today?)*
> — **Ігор:** Зазвичай треба **подавати** *(to serve)* борщ до столу зі свіжим кропом і чорним хлібом. *(Usually you need to serve borscht to the table with fresh dill and black bread.)*

Ми часто використовуємо орудний відмінок на кухні. *(We often use the Instrumental case in the kitchen.)* Цей відмінок показує інструмент, яким ми робимо певну дію. *(This case shows the tool with which we perform a certain action.)* English uses the preposition "with" to express this idea, like "to cut with a knife". Ukrainian uses the bare Instrumental case without any prepositions.
Ми кажемо просто: **різати** *(to cut)* **ножем** *(with a knife)*. *(We say simply: to cut with a knife.)*
Я завжди їм гаряче м'ясо **виделкою** *(with a fork)*. *(I always eat hot meat with a fork.)*
Діти зазвичай п'ють солодкий чай маленькою ложкою. *(Children usually drink sweet tea with a small spoon.)*

Коли ми готуємо їжу вдома, ми робимо багато різних дій. *(When we cook food at home, we do many different actions.)*
Щоб зробити смачний суп, треба мішати воду великою ложкою. *(To make a tasty soup, you need to stir the water with a large spoon.)*
Ми також любимо терти твердий сир **терткою** *(with a grater)*. *(We also like to grate hard cheese with a grater.)*
Сира **картопля** *(potato)* лежить на столі. *(The raw potato lies on the table.)*
Мій старший брат вміє швидко чистити картоплю ножем. *(My older brother knows how to peel potatoes quickly with a knife.)*

It is important to contrast the Instrumental case for tools with the Locative case for locations.
Ми смажимо свіже м'ясо **на** *(on)* **сковорідці** *(frying pan)*. *(We fry fresh meat on a frying pan.)* The pan is the location, so it takes the Locative case with a preposition.
Але ми перевертаємо м'ясо дерев'яною **лопаткою** *(with a spatula)*. *(But we flip the meat with a wooden spatula.)* The spatula is the tool, so it takes the bare Instrumental case.

Орудний відмінок також показує інгредієнти та різноманітні додатки до страв. *(The Instrumental case also shows ingredients and various additions to dishes.)*
When "with" means "containing" or "alongside", Ukrainian uses the preposition **з** *(with)* або **зі** *(with)* before the Instrumental noun.
Ми використовуємо варіант «зі» перед словами, які починаються на два або три приголосні звуки. *(We use the variant "zi" before words that start with two or three consonant sounds.)*
Наприклад, українці дуже люблять їсти борщ **зі сметаною** *(with sour cream)*. *(For example, Ukrainians really love eating borscht with sour cream.)*
На святкову вечерю ми готуємо вареники **з картоплею** *(with potato)*. *(For a festive dinner we cook dumplings with potato.)*
Взимку корисно пити гарячий чай з лимоном і медом. *(In winter it is healthy to drink hot tea with lemon and honey.)*
Влітку ми часто робимо свіжий салат з овочами, наприклад з помідорами та **огірками** *(with cucumbers)*. *(In summer we often make fresh salad with vegetables, for example with tomatoes and cucumbers.)* Зелений **огірок** *(cucumber)* дуже смачний. *(A green cucumber is very tasty.)*

Ми будемо робити традиційний бутерброд. *(We will make a traditional sandwich.)*
Потім ми намащуємо цей хліб вершковим маслом. *(Then we spread this bread with butter.)*
Далі ми кладемо шматок ковбаси з сиром. *(Next we put a piece of sausage with cheese.)*
Зверху треба **посипати** *(to sprinkle)* наш бутерброд сіллю. *(On top one needs to sprinkle our sandwich with salt.)*
Дехто також любить поливати такий бутерброд оливковою **олією** *(with oil)*. *(Some people also like to pour olive oil on such a sandwich.)* Соняшникова **олія** *(oil)* також підходить. *(Sunflower oil also fits.)*

<!-- INJECT_ACTIVITY: kitchen-fill -->

## Мій робочий день (My Workday)

We use the Instrumental case to describe where things are located when using certain spatial prepositions: **перед** *(in front of)*, **за** *(behind)*, **над** *(above)*, **під** *(under)*, **між** *(between)*, and **поруч з** *(next to)*.
Мій великий стіл стоїть перед великим вікном. *(My large desk stands in front of the large window.)*
За моїм столом стоїть висока шафа. *(Behind my desk stands a tall cabinet.)*
Над столом висить яскрава лампа. *(Above the desk hangs a bright lamp.)*
Мій комп'ютер стоїть між принтером і телефоном. *(My computer stands between the printer and the telephone.)*
Я тримаю блокнот поруч з клавіатурою. *(I keep a notepad next to the keyboard.)*
Маленький кошик стоїть під столом. *(A small basket stands under the desk.)*

The preposition "перед" can also express time, meaning "before". It requires the Instrumental case. The opposite is **після** *(after)*, which requires the Genitive case.
Я завжди планую свій день. *(I always plan my day.)*
Перед роботою я п'ю міцну каву. *(Before work I drink strong coffee.)*
Перед важливим **обідом** *(lunch)* я маю нараду. *(Before an important lunch I have a meeting.)*
Але після обіду я читаю листи. *(But after lunch I read emails.)*
Усе на роботі відбувається **за розкладом** *(according to schedule)*. *(Everything at work happens according to schedule.)*

The Instrumental case is also used to describe the method of transportation, answering the question "how?". We do not use a preposition for this function in Ukrainian.
Кожного ранку я **їду** *(go/ride)* на роботу **автобусом** *(by bus)*. *(Every morning I go to work by bus.)*
Іноді я їду **поїздом** *(by train)* або **трамваєм** *(by tram)*. *(Sometimes I go by train or by tram.)*
Мій колега завжди їде власною **машиною** *(by car)*. *(My colleague always goes by his own car.)*
А моя подруга їде на роботу **метро** *(by subway)*. *(And my friend goes to work by subway.)*
Слово «метро» є іншомовним, тому воно ніколи не змінює закінчення. *(The word "metro" is foreign, so it never changes its ending.)*

Finally, we use the preposition **з** *(with)* and the Instrumental case to talk about social accompaniment. Pay attention to the difference between working "as" someone and working "with" someone.
Щодня я розмовляю з **начальником** *(with the boss)*. *(Every day I talk with the boss.)*
О першій годині я обідаю з колегами. *(At one o'clock I have lunch with colleagues.)*
«Я працюю менеджером» означає вашу професію без прийменника. *("I work as a manager" means your profession without a preposition.)*
Але «я працюю з менеджером» означає, що ви працюєте разом. *(But "I work with a manager" means that you work together.)*

<!-- INJECT_ACTIVITY: workday-tf -->

## Практика: Розкажи про себе (Practice: Tell About Yourself)

Привіт! Мене звати Антон, і я живу в Києві. Я працюю **журналістом** *(as a journalist)* у популярному журналі. Вранці я зазвичай їду в офіс **метро** *(by subway)* або **трамваєм** *(by tram)*. Мій офіс знаходиться між великим парком і новим кафе. Там я працюю за великим **столом** *(at a desk)* і пишу цікаві статті. Я завжди шукаю нову інформацію перед важливим інтерв'ю. О першій годині я обідаю з **друзями** *(with friends)* або з колегами. Ми часто їмо в ресторані з італійською кухнею. Я дуже люблю пасту з **сиром** *(with cheese)* і салат з **помідорами** *(with tomatoes)*. Вечорами, після роботи, я захоплююся **малюванням** *(drawing)*. Я малюю звичайним **олівцем** *(with a pencil)* або яскравими фарбами. Це допомагає мені добре відпочивати. У вихідні я люблю довго гуляти містом зі своїм **собакою** *(with my dog)*. 

When you talk about your profession, the specific tool you use, or your method of transportation, you must use the Instrumental case without any preposition.
Наприклад: я працюю **вчителем** *(I work as a teacher)*, я пишу **ручкою** *(I write with a pen)*, я їду **автобусом** *(I go by bus)*.
However, when you describe companionship or food ingredients, you must use the preposition **з** (або **зі**).
Наприклад: я працюю з **вчителем** *(I work with a teacher)*, я п'ю каву з **молоком** *(I drink coffee with milk)*.

<!-- INJECT_ACTIVITY: functions-quiz -->

## Підсумок

Let's review the key rules for the Instrumental case from this module. 

First, to talk about jobs and professions, use verbs like **працювати** *(to work)*, **бути** *(to be)*, або **стати** *(to become)* followed directly by the Instrumental case without a preposition.
Second, to talk about physical tools (like **ножем** - *with a knife*) or forms of transportation (like **автобусом** - *by bus*), also use the bare Instrumental case.
Third, to talk about ingredients (like **з цукром** - *with sugar*) or people you are spending time with (like **з сестрою** - *with a sister*), always use the preposition **з** або **зі**.
Finally, remember that spatial prepositions that describe a static location (**перед**, **за**, **над**, **під**, **між**) always require the noun to be in the Instrumental case.

Дайте відповіді на ці питання:
1. Ким ви мріяли стати в дитинстві? *(Who did you dream of becoming in childhood?)* (Я мріяв/мріяла стати...)
2. З чим ви любите їсти вареники? *(What do you like to eat varenyky with?)* (Я люблю вареники з...)
3. Чим ви зазвичай пишете? *(What do you usually write with?)* (Я пишу...)

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: work-and-food
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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

---

## Learner Level Context

**Level: A2 (Module 30/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
