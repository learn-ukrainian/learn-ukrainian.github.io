<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/instrumental-means.yaml` file for module **25: Ручкою, автобусом** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-tool-singular -->`
- `<!-- INJECT_ACTIVITY: match-up-transport -->`
- `<!-- INJECT_ACTIVITY: unjumble-plural-phrases -->`
- `<!-- INJECT_ACTIVITY: quiz-companion-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-categories -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the noun in Instrumental singular to express the tool of an action
  items: 8
  type: fill-in
- focus: Choose between з + Instrumental (companion) and bare Instrumental (tool)
  items: 8
  type: quiz
- focus: Match transport nouns to their Instrumental forms
  items: 8
  type: match-up
- focus: Sort sentences into Tool/Means vs. Accompaniment categories
  items: 8
  type: group-sort
- focus: Reorder words to form correct instrumental phrases expressing tool or means
    of transport
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- знаряддя (instrument, tool)
- транспорт (transport)
- пішки (on foot)
- корабель (ship)
required:
- ручка (pen)
- олівець (pencil)
- фарба (paint)
- лінійка (ruler)
- ніж (knife)
- ложка (spoon)
- автобус (bus)
- потяг (train)
- літак (airplane)
- трамвай (tram)
- засіб (means, tool)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чим? Знаряддя дії (With What? The Tool of an Action)

В українській мові ми використовуємо орудний відмінок кожного дня. *(In the Ukrainian language, we use the instrumental case every day.)* Цей відмінок показує інструмент або знаряддя дії. *(This case shows the instrument or tool of an action.)*

We use this case to explain exactly what object we are using to complete a task. The case answers two core questions: **«Ким?»** *(By whom?)* and **«Чим?»** *(With what?)*.

Діти в українських школах вчать це правило дуже рано. *(Children in Ukrainian schools learn this rule very early.)* Вчителі зазвичай дають прості приклади з уроків. *(Teachers usually give simple examples from lessons.)*

Я пишу синьою **ручкою** *(I write with a blue pen)*.
Мій брат малює **олівцем** *(My brother draws with a pencil)*.

The grammatical ending of the noun alone carries the meaning of the tool. Let us look at the regular endings for singular nouns.

Для іменників чоловічого роду ми маємо три основні закінчення. *(For masculine nouns, we have three main endings.)*

First, we use the ending **-ом** when the stem of the noun ends in a hard consonant.

Вчитель пише на дошці червоним **маркером** *(The teacher writes on the board with a red marker)*.

Second, we use the ending **-ем** when the stem ends in a soft consonant.

Художник малює красиву картину **пензлем** *(The artist paints a beautiful picture with a brush)*.
Ось синій **олівець** *(Here is a blue pencil)*. Учень малює лінію синім **олівцем** *(The student draws a line with a blue pencil)*.

Crucially, Ukrainian also uses the **-ем** ending for stems that end in sibilant consonants, like «ж», «ч», «ш», or «щ».

Це гострий **ніж** *(This is a sharp knife)*. Кухар швидко ріже м'ясо гострим **ножем** *(The cook quickly cuts meat with a sharp knife)*.
Він відкриває старі двері **ключем** *(He opens the old door with a key)*.

If the noun ends in «й», the ending becomes **-єм**.

Іменники жіночого роду також мають чіткі правила. *(Feminine nouns also have clear rules.)*

For standard feminine nouns that end in «-а», we always use the hard ending **-ою**.

Студентка швидко пише чорною **ручкою** *(The student writes quickly with a black pen)*.
Ось дерев'яна **лінійка** *(Here is a wooden ruler)*. Дівчина вимірює папір дерев'яною **лінійкою** *(The girl measures the paper with a wooden ruler)*.
Це велика **ложка** *(This is a large spoon)*. Я їм смачний суп великою **ложкою** *(I eat delicious soup with a large spoon)*.

When a feminine noun ends in «-я», it takes the soft ending **-ею**.

Садівник засипає коріння дерева м'якою **землею** *(The gardener covers the tree roots with soft earth)*.

Feminine nouns of the third declension are special because they end in a consonant. For these nouns, we simply add the ending **-ю**. Often, the final consonant doubles in this form.

Мама посипає салат дрібною **сіллю** *(Mom sprinkles the salad with fine salt)*.

Тепер ми можемо розглянути іменники середнього роду. *(Now we can look at neuter nouns.)*

These nouns follow patterns that are almost identical to masculine nouns. When a neuter noun ends in a hard «-о», it takes the ending **-ом**.

Жінка миє руки запашним **милом** *(The woman washes her hands with fragrant soap)*.
Майстер відбиває світло великим **дзеркалом** *(The craftsman reflects light with a large mirror)*.

When the neuter noun ends in a soft «-е», it takes the ending **-ем**.

Ми насолоджуємося теплим **морем** *(We enjoy the warm sea)*.

Finally, when the neuter noun ends in «-я», it takes the ending **-ям**.

Старий професор ділиться своїм **знанням** *(The old professor shares his knowledge)*.

Although neuter nouns act as tools less frequently than other genders, the grammatical system works exactly the same way.

Студенти часто роблять одну типову помилку. *(Students often make one typical mistake.)*

In English, you always use the preposition "with" to introduce a tool. Because of this, English speakers instinctively want to use the Ukrainian preposition **«з»** *(with)*. This is a critical grammatical error.

In Ukrainian, the instrumental case already contains the meaning of "with a tool". We use the preposition **«з»** only when we talk about accompaniment or a companion.

Я пишу **з ручкою** *(I am writing accompanied by a pen)*. This sounds like the pen is sitting next to you on a chair while you write.
Я пишу **ручкою** *(I write with a pen)*. This is the correct way to express the tool of your action.

The case ending does all the heavy lifting. You must trust the ending and drop the preposition when you describe an instrument.

<!-- INJECT_ACTIVITY: fill-in-tool-singular -->


## Їхати автобусом: Засіб пересування (Travel by Bus: Means of Transport)

Часто ми використовуємо Орудний відмінок, коли говоримо про подорожі. *(Often we use the Instrumental case when we talk about traveling.)* The Instrumental case is the perfect tool for expressing your means of transportation. When you want to ask someone how they are traveling, you use the standard question: «**Чим ти їдеш?**» *(How/By what means are you going?)*. This question asks about the instrument of your travel. You do not need a preposition here. The case ending alone tells us that the vehicle is the means of your movement. Ось базові слова, які вам потрібні. *(Here are the basic words you need.)* Ми подорожуємо **автобусом** *(by bus)*. Люди часто їздять **потягом** *(by train)* або **трамваєм** *(by tram)*. Моя сестра летить **літаком** *(by airplane)*. Мої батьки люблять подорожувати **машиною** *(by car)*.

Студенти часто плутають два відмінки. *(Students often confuse two cases.)* It is very important to understand the conceptual difference between the Locative case and the Instrumental case when talking about transport. The Locative case describes location or position. For example, «**в автобусі**» *(in the bus)* means you are physically sitting or standing inside the vehicle. The Instrumental case describes the method of your travel. «Автобусом» means the bus is the tool that moves you from place to place. Порівняйте ці два речення. *(Compare these two sentences.)* Я сиджу в автобусі і читаю книгу *(I am sitting in the bus and reading a book)*. Я їду на роботу автобусом *(I travel to work by bus)*. У першому реченні важливе місце. *(In the first sentence, the place is important.)* У другому реченні важливий метод подорожі. *(In the second sentence, the method of travel is important.)*

Послухайте розмову двох колег. *(Listen to a conversation between two colleagues.)* Вони обговорюють свій ранковий маршрут. *(They are discussing their morning route.)*
> — **Олена:** Привіт! Чим ти їдеш на роботу? *(Hi! How do you travel to work?)*
> — **Марко:** Я їду на роботу автобусом, а потім **метро** *(subway)*. *(I travel to work by bus, and then by subway.)*
> — **Олена:** А я зазвичай їду власною машиною. *(And I usually travel by my own car.)*
> — **Марко:** Ти ніколи не береш **таксі** *(taxi)*? *(Do you never take a taxi?)*
> — **Олена:** Ні, це занадто дорого. *(No, it is too expensive.)*

Notice the words «метро» and «таксі» in the dialogue. These borrowed words are indeclinable in Ukrainian. Вони ніколи не змінюють своє закінчення. *(They never change their ending.)* However, grammatically, they still function exactly like nouns in the Instrumental case here.

Є один важливий виняток із цього правила. *(There is one important exception to this rule.)* When you travel on foot, you are using your own body, not an external tool or vehicle. Because of this, Ukrainian uses a specific adverb instead of a noun in the Instrumental case. Ми говоримо «**іти пішки**» *(to go on foot)*. The word «пішки» is an adverb, so it never changes its form. Він їде потягом, а я йду пішки *(He travels by train, and I walk on foot)*. Вони їдуть трамваєм, а ми йдемо пішки *(They travel by tram, and we walk on foot)*.

Як правильно сказати, що транспорт починає рух? *(How to correctly say that transport starts moving?)* Many learners use the Russianism «відправлятися» *(to depart)*. Це лексична помилка в українській мові. *(This is a lexical error in the Ukrainian language.)* Instead, you should use authentic Ukrainian verbs to describe departure. Автобус **відбуває** *(departs)* з Києва вранці. Поїзд **рушає** *(starts moving)* дуже швидко. Ми **вирушаємо** *(set off)* літаком о восьмій годині. These verbs sound natural and pair perfectly with the transport nouns in the Instrumental case. Ми вирушаємо машиною на вихідних *(We set off by car on the weekend)*. Потяг рушає, а ми махаємо руками *(The train starts moving, and we wave our hands)*.

<!-- INJECT_ACTIVITY: match-up-transport -->


## Орудний відмінок множини (Instrumental Plural)

Ми вже знаємо, як використовувати Орудний відмінок в однині. *(We already know how to use the Instrumental case in singular.)* Тепер час вивчити множину. *(Now it is time to learn the plural.)* The plural form of the Instrumental case is much simpler than the singular. Чому це так? *(Why is it so?)* Тому що всі три роди мають однакові закінчення. *(Because all three genders have the same endings.)* You do not need to memorize separate rules for masculine, feminine, and neuter nouns. Є тільки два основні варіанти: закінчення «**-ами**» та «**-ями**». *(There are only two main options: the endings "-ами" and "-ями".)* We use the ending «-ами» for hard stems. Наприклад, ми кажемо **руками** *(with hands)*, **столами** *(with tables)*, або **автобусами** *(by buses)*. We use the ending «-ями» for soft stems. Наприклад, ми говоримо **олівцями** *(with pencils)*, **морями** *(by seas)*, або **друзями** *(with friends)*. 

Як ми використовуємо ці форми на практиці? *(How do we use these forms in practice?)* Ми часто вживаємо Орудний відмінок множини, коли говоримо про інструменти. *(We often use the Instrumental plural when we talk about tools.)* Many actions naturally require plural tools. Діти люблять **малювати фарбами** *(to paint with paints)*. В Азії люди традиційно **їдять паличками** *(eat with chopsticks)*. Це дуже зручно. *(It is very convenient.)* Фермери часто **працюють руками** *(work with hands)*. Це важка фізична праця. *(This is hard physical work.)* На уроці студенти **пишуть олівцями** *(write with pencils)*. Усі ці слова показують засіб дії. *(All these words show the means of action.)*

What happens with nouns ending in sibilant consonants? У множині вони також використовують ці стандартні закінчення. *(In the plural, they also use these standard endings.)* The spelling remains consistent with the hard sibilant rules in Ukrainian. Слово «**ніч**» *(night)* має форму «**ночами**» *(by nights)*. Ми часто працюємо ночами *(We often work by nights)*. Слово «**миша**» *(mouse)* також має твердий шиплячий звук. *(The word "mouse" also has a hard sibilant sound.)* Тому ми говоримо «**мишами**» *(with mice)*. Кіт бігає за мишами *(The cat runs after mice)*. Як бачите, після шиплячих звуків ми завжди пишемо літеру «а». *(As you can see, after sibilant sounds we always write the letter "a".)* Це робить вимову набагато легшою. *(This makes the pronunciation much easier.)* 

Деякі слова в українській мові існують тільки у множині. *(Some words in the Ukrainian language exist only in the plural.)* We call them pluralia tantum. Найкращий приклад — це «**ножиці**» *(scissors)*. Ми ріжемо папір **ножицями** *(with scissors)*. There are also some common words that have parallel forms in the Instrumental plural. Обидві форми є абсолютно правильними. *(Both forms are absolutely correct.)* Ви можете сказати «**дверима**» *(with doors)* або «**дверми**». Також правильно казати «**грошима**» *(with money)* або «**грішми**». Ви можете зустріти «**конями**» *(with horses)* або «**коньми**». Перший варіант зазвичай звучить частіше у сучасній мові. *(The first option usually sounds more often in modern language.)* 

Прикметники також змінюють свою форму. *(Adjectives also change their form.)* They must agree with the noun in the Instrumental plural. Українські прикметники у множині мають закінчення «**-ими**» або «**-іми**». *(Ukrainian adjectives in the plural have the endings "-ими" or "-іми".)* We use «-ими» for hard stems, and «-іми» for soft stems. Зверніть увагу на ці приклади. *(Pay attention to these examples.)* Я завжди малюю **новими фарбами** *(with new paints)*. Туристи подорожують **великими автобусами** *(by big buses)*. Мій брат пише **синіми олівцями** *(with blue pencils)*. Усі ці слова працюють разом як одна команда. *(All these words work together as one team.)* The adjective and the noun both show the tool or the means of transport.

<!-- INJECT_ACTIVITY: unjumble-plural-phrases -->


## Практика: Знаряддя чи супутник? (Practice: Tool or Companion?)

Англомовні студенти часто роблять одну типову помилку. *(English-speaking students often make one typical mistake.)* In English, you use the preposition "with" for both tools and companions. В українській мові це дві різні граматичні ситуації. *(In the Ukrainian language, these are two different grammatical situations.)* Коли ми використовуємо предмет як інструмент, ми беремо Орудний відмінок без прийменника. *(When we use an object as a tool, we take the Instrumental case without a preposition.)* Наприклад, ми говоримо: «**Я пишу ручкою**» *(I am writing with a pen)*. The pen is the tool you are using to perform the action. Але прийменник «**з**» *(with)* має інше значення. *(But the preposition "з" has another meaning.)* It indicates accompaniment or being together. Якщо ви скажете «**Я йду з ручкою**» *(I am walking with a pen)*, це означає, що ви просто тримаєте ручку. *(If you say "I am walking with a pen", it means you are just holding a pen.)* The pen is your companion, not your tool. Уявіть, що ви гуляєте, і ручка гуляє разом із вами. *(Imagine that you are walking, and the pen is walking together with you.)* Це дуже важлива різниця. *(This is a very important difference.)*

Ця ж логіка працює для транспорту. *(This same logic works for transport.)* When you travel by a vehicle, the vehicle is the means of your action. Тому ми кажемо: «**Він їде автобусом**» *(He is travelling by bus)*. Тут автобус — це засіб пересування. *(Here the bus is the means of transport.)* Але якщо ви їдете разом із людиною, ця людина є вашим супутником. *(But if you are travelling together with a person, this person is your companion.)* Тоді ми говоримо: «**Він їде з другом**» *(He is travelling with a friend)*. What happens if you mix them up? Якщо ви скажете «**Я їду з автобусом**» *(I am travelling with a bus)*, це звучить кумедно. *(If you say "I am travelling with a bus", it sounds funny.)* It sounds like you are travelling alongside a bus, perhaps in a car next to it, rather than being inside it. Транспорт — це засіб, а люди — це супутники. *(Transport is a means, and people are companions.)*

В українській мові є особливі дієслова. *(In the Ukrainian language, there are special verbs.)* Вони завжди вимагають Орудного відмінка без прийменника. *(They always require the Instrumental case without a preposition.)* These verbs often express the "means" or "manner" of a state. Чудовий приклад — це дієслово «**пахнути**» *(to smell of)*. Навесні парк **пахне квітами** *(In spring, the park smells of flowers)*. The flowers are the source or the means of the smell. Інший приклад — дієслово «**займатися**» *(to be engaged in, to do)*. Мій брат **займається спортом** *(My brother does sports)*. Студенти часто **цікавляться історією** *(Students are often interested in history)*. У цих фразах ми ніколи не використовуємо прийменник «з». *(In these phrases, we never use the preposition "з".)* The objects act as the logical instruments of your interest or activity. Запам'ятайте ці корисні вирази. *(Remember these useful expressions.)* Вони роблять вашу мову дуже природною. *(They make your language very natural.)*

Подивімося, як це працює на практиці. *(Let's see how this works in practice.)* Прочитайте цей діалог у художній школі. *(Read this dialogue in an art school.)* Студенти обговорюють свої інструменти. *(The students are discussing their tools.)*

> — **Вчитель:** Добрий день! Чим ви сьогодні малюєте? *(Good day! What are you drawing with today?)*
> — **Марко:** Я малюю цим м'яким олівцем. *(I am drawing with this soft pencil.)* А також я креслю довгою лінійкою. *(And also I am drafting with a long ruler.)*
> — **Ганна:** А я працюю фарбами та широким пензлем. *(And I am working with paints and a wide brush.)*
> — **Вчитель:** Дуже добре. А чим ви приїхали на урок? *(Very well. And how did you arrive to the lesson?)*
> — **Ганна:** Я приїхала швидким трамваєм. *(I arrived by a fast tram.)*
> — **Марко:** А я прийшов пішки з великою лінійкою і з новим другом! *(And I came on foot with a big ruler and with a new friend!)*
> — **Вчитель:** Це чудово, що ви цікавитеся мистецтвом. *(It is wonderful that you are interested in art.)*

Як бачите, Марко використовує прийменник «з» для лінійки і друга. *(As you can see, Marko uses the preposition "з" for the ruler and the friend.)* He brought them as companions, he didn't use them as tools or transport. Але Ганна використовує трамвай як засіб. *(But Hanna uses the tram as a means.)*

<!-- INJECT_ACTIVITY: quiz-companion-choice -->
<!-- INJECT_ACTIVITY: group-sort-categories -->


## Підсумок

Час повторити головні правила цього уроку. *(It is time to review the main rules of this lesson.)* Запам'ятайте ці важливі пункти про Орудний відмінок. *(Remember these important points about the Instrumental case.)*

*   Орудний відмінок без прийменника позначає **знаряддя** *(tool)* або **засіб пересування** *(means of transport)*. Наприклад: писати ручкою, їхати автобусом. *(For example: to write with a pen, to travel by bus.)*
*   Чоловічий та середній рід мають закінчення **-ом** для твердої основи. *(Masculine and neuter genders have the ending -ом for a hard stem.)* М'яка чи шипляча основа має закінчення **-ем**. *(A soft or sibilant stem has the ending -ем.)*
*   Жіночий рід з твердою основою має закінчення **-ою**. *(The feminine gender with a hard stem has the ending -ою.)*
*   У множині всі роди мають закінчення **-ами** *(hard)* або **-ями** *(soft)*.
*   Ніколи не використовуйте прийменник «з» для інструментів чи транспорту! *(Never use the preposition "з" for tools or transport!)* Він позначає тільки супутників. *(It indicates only companions.)*
*   Виняток: ми говоримо «**іти пішки**» *(to go on foot)* замість Орудного відмінка. *(...instead of the Instrumental case.)*

Тепер ви можете впевнено розповідати про свої інструменти та щоденні подорожі! *(Now you can confidently talk about your tools and daily travels!)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: instrumental-means
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

**Level: A2 (Module 25/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
