<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/home-and-daily-life.yaml` file for module **38: Мій дім, мій день** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-home-cases -->`
- `<!-- INJECT_ACTIVITY: quiz-daily-routine -->`
- `<!-- INJECT_ACTIVITY: match-up-activities -->`
- `<!-- INJECT_ACTIVITY: error-correction-cases -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete a description of a home with the correct case forms for room and
    furniture nouns
  items: 8
  type: fill-in
- focus: Choose the correct case form in daily routine sentences (time expressions,
    prepositions, verbs)
  items: 8
  type: quiz
- focus: Match daily activities with the correct time of day and appropriate case
    construction
  items: 8
  type: match-up
- focus: Find and correct grammar errors in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- балкон (balcony)
- коридор (hallway)
- килим (carpet, rug)
- пригощатися (to help oneself (to food))
- господар (host)
required:
- помешкання (dwelling, apartment)
- кімната (room)
- кухня (kitchen)
- спальня (bedroom)
- вітальня (living room)
- меблі (furniture)
- розпорядок дня (daily routine)
- вставати (to get up)
- снідати (to have breakfast)
- лягати спати (to go to bed)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Сценарій 1: Моє помешкання

Сьогодні ми йдемо в гості онлайн.
Наш знайомий показує своє нове **помешкання** *(apartment, dwelling)*.
Він знімає відео для свого друга з іншого міста.
У цьому відео ми побачимо, як називати кімнати.
Ми також почуємо, як сказати, де саме ви знаходитеся.

> — **Мешканець:** Привіт! Ось моя нова **квартира** *(apartment)*. Я зараз у квартирі, але тут ще мало речей.
> — **Онлайн-друг:** О, вітаю з переїздом! Це дуже цікаво. Яка це кімната?
> — **Мешканець:** Це — довгий **коридор** *(hallway)*. А тут далі є велика **вітальня** *(living room)*.
> — **Онлайн-друг:** Супер! А де знаходиться **кухня** *(kitchen)*?
> — **Мешканець:** Я зараз на кухні. Вона дуже світла. А там праворуч є **спальня** *(bedroom)*.
> — **Онлайн-друг:** Клас! Ти вже живеш у цій квартирі?
> — **Мешканець:** Так, я вже сплю у спальні, але тут ще є багато роботи.

Let's look closely at the vocabulary for rooms in a house.
When we simply name a room, we use the Nominative case.
Це кухня, вітальня, спальня, **ванна кімната** *(bathroom)*, коридор та **балкон** *(balcony)*.
But when we want to say *where* we are, we must answer the question «де?» *(where?)*.
To answer this question, we must use the Locative case.
In the Locative case, feminine nouns usually take the ending «-і».
For example, the noun «кімната» becomes «у кімнаті», and «спальня» becomes «у спальні».
Masculine nouns usually take the ending «-і» or «-у».
For example, «коридор» becomes «у коридорі», and «будинок» *(house)* becomes «у будинку».
Pay special attention to the prepositions «у/в» *(in)* and «на» *(on/at)*.
We say «у спальні» and «у вітальні», but we always say «на кухні» and «на балконі».
Ми п'ємо смачну каву на кухні.
Мій брат читає книгу на балконі.
Ми стоїмо у темному коридорі.

Now let's furnish our empty home.
We need **меблі** *(furniture)* for every room.
Тут є **диван** *(sofa)*, **крісло** *(armchair)*, **шафа** *(wardrobe)*, **ліжко** *(bed)*, **полиця** *(shelf)* та м'який **килим** *(carpet)*.
When we describe where furniture is placed or where everyday objects are located, we again use the Locative case.
It is important to choose between the prepositions «у/в» and «на» based on physical logic.
If something is inside an enclosed space, we use «у/в».
If something is resting on a surface, we use «на».
Мій новий одяг висить у шафі.
Маленький кіт солодко спить на дивані.
Цікава книга лежить на полиці.
Теплий килим лежить на підлозі.
Велика подушка лежить на ліжку.
Мій собака сидить у кріслі.

We don't just describe what we already have in our home.
Often we need to explain what is still missing.
To express the absence of something, we use the word **немає** *(there is no / are no)*.
The word «немає» always requires the noun to be in the Genitive case.
Let's contrast existence with absence.
У новій квартирі є великий балкон.
У старій квартирі немає великого балкона.
Тут є зручна шафа.
Тут немає зручної шафи.
The Genitive case is also essential when we talk about quantities.
When we use quantity words like **багато** *(a lot, many)*, we use the Genitive plural form.
У цьому будинку є багато кімнат.
У нашій вітальні є багато вікон.
На полиці стоїть багато книг.
Ці структури дуже корисні, коли ви щойно переїхали.

When you are actively moving things into your new home, you perform physical actions.
You might want to **поставити** *(to put, place standing)* a chair or **повісити** *(to hang)* a beautiful picture.
These are verbs of direction and placement, and they require the Accusative case for the specific object you are moving.
When the object is inanimate and masculine, its Accusative form looks exactly the same as the Nominative form.
Я хочу поставити новий диван біля вікна.
Ми поставимо цей круглий стіл на кухні.
When the object is feminine, the ending usually changes from «-а» or «-я» to «-у» or «-ю».
Я хочу повісити красиву картину.
Вони поставлять нову шафу у спальні.

Finally, let's make our room descriptions richer with descriptive adjectives.
Adjectives must always agree perfectly with the noun they describe in gender, number, and case.
Це дуже **світла** *(light, bright)* кімната.
Тут є **велике** *(large)* вікно.
Тут стоїть **зручний** *(comfortable)* диван.
When the grammatical case of the noun changes in a sentence, the adjective changes right along with it.
Я сиджу у світлій кімнаті.
Ми поставимо стіл біля великого вікна.
Мій кіт спить на зручному дивані.
У нас немає зручного крісла.
Ми відпочиваємо у новій спальні.
Я повішу цю картину на білу стіну.
By matching the adjective perfectly with its noun, your Ukrainian will sound natural and precise.

<!-- INJECT_ACTIVITY: fill-in-home-cases -->


## Сценарій 2: Мій звичайний день (Scenario 2: My Typical Day)

Ось мій звичайний **розпорядок дня** *(daily routine)*. Кожного дня я роблю одні і ті ж речі. Вранці я **прокидаюся** *(wake up)* дуже рано. Зазвичай я прокидаюся о сьомій годині. Потім я швидко **встаю** *(get up)* з ліжка. Я йду у ванну кімнату. Там я **вмиваюся** *(wash my face)* та чищу зуби. Після цього я йду на кухню. Я готую смачну їжу і **снідаю** *(have breakfast)*. Я дуже люблю пити гарячу каву і їсти хліб з маслом. Потім я одягаюся і їду на роботу. Мій робочий день починається о дев'ятій годині. Я багато працюю в офісі до п'ятої. Після роботи я швидко їду додому. Вдома я відпочиваю на зручному дивані. Потім я готую вечерю і дивлюся цікавий фільм. Я **лягаю спати** *(go to bed)* пізно вночі.

In Ukrainian, we use ordinal numbers to tell the time, just like saying "the seventh hour". We ask «**Котра година?**» *(What time is it?)* using the Nominative case. Зараз **сьома година** *(seven o'clock)*. Зараз **восьма година** *(eight o'clock)*. Це дуже проста структура. But when we want to say at what time something happens, we ask «**О котрій годині?**» *(At what time?)*. To answer this, we use the preposition «о» (or «об» before vowels) with the Locative case. Я встаю **о сьомій годині** *(at seven o'clock)*. Він обідає **о першій годині** *(at one o'clock)*. Вона лягає спати **об одинадцятій** *(at eleven)*. Notice that the word «година» can be omitted in everyday speech. We can also express half-hours using the preposition «на» and the Accusative case of the next hour. Я прокидаюся **о пів на восьму** *(at half past seven)*. Ми завжди снідаємо **о пів на дев'яту** *(at half past eight)*.

When we travel, we need to say how we get there. Ukrainian uses the Instrumental case to indicate the means of transportation. We do not use a preposition for this structure. Я їду на роботу **автобусом** *(by bus)*. Вона їде в центр великого міста **метро** *(by subway)*. Note that «метро» is a foreign word and does not change its ending. Він часто подорожує **машиною** *(by car)*. Notice the important difference between the destination and the means. Я їду **на роботу** *(to work)* uses the Accusative case for direction. Я їду автобусом uses the Instrumental case for the specific vehicle you use. We also use the Instrumental case with the preposition «**з**» *(with)* to describe accompaniment. Я снідаю **з родиною** *(with family)*. Ми смачно обідаємо **з друзями** *(with friends)*. Я йду в кіно **з братом** *(with my brother)*.

To create a logical timeline, we use specific adverbs and prepositions. The adverbs **вранці** *(in the morning)*, **вдень** *(in the afternoon)*, **увечері** *(in the evening)*, and **вночі** *(at night)* are fixed forms. Вранці я п'ю солодкий чай. Вдень я інтенсивно працюю в офісі. Увечері я сиджу у кріслі і читаю книгу. Вночі я міцно сплю у спальні. We also use prepositions that require specific cases to organize our day. The preposition «**після**» *(after)* always takes the Genitive case. Я йду гуляти у парк **після обіду** *(after lunch)*. Вони швидко їдуть додому після роботи. The preposition «**перед**» *(before)* requires the Instrumental case. Я читаю новини в інтернеті **перед сном** *(before sleep)*. Ми завжди миємо руки перед сніданком. The phrase «**під час**» *(during)* also takes the Genitive case. Я ніколи не слухаю музику **під час роботи** *(during work)*. Ці короткі слова допомагають створити чіткий розпорядок дня.

Our daily routine changes depending on the day of the week. We use the phrase «**у будні**» *(on weekdays)* for Monday through Friday. У будні я дуже рано встаю і їду на роботу. У будні ми завжди багато працюємо. We contrast this with «**у вихідні**» *(on weekends)*. У вихідні я прокидаюся дуже пізно. У вихідні ми довго гуляємо в зеленому парку. If you want to describe a habitual action that happens every Saturday, you can use the preposition «по» with the Dative plural form. Я ходжу в басейн **по суботах** *(on Saturdays)*. Ми їздимо в маленьке село **по неділях** *(on Sundays)*. Ця граматична форма добре показує регулярність. Я часто ходжу **на ринок** *(to the market)* по суботах. Там я купую свіжі овочі та фрукти з родиною. Після ринку ми разом обідаємо на світлій кухні. Це наш ідеальний день.

<!-- INJECT_ACTIVITY: quiz-daily-routine -->
<!-- INJECT_ACTIVITY: match-up-activities -->


## Сценарій 3: В гостях (Scenario 3: Visiting Someone)

Уявіть, що ви йдете в гості до українських друзів у неділю. Українці дуже **гостинні** *(hospitable)* люди, тому вони завжди чекають на гостей. Коли ви приходите, **господарі** *(hosts)* радісно зустрічають вас біля дверей. Вони завжди раді вас бачити у своєму домі. Ось типова розмова у коридорі:
> — **Оксана:** Привіт! **Заходьте** *(come in)*, будь ласка!
> — **Джон:** Привіт, Оксано! Дякую за запрошення. Ось маленькі **гостинці** *(gifts)* для вас.
> — **Оксана:** О, дуже дякую! Це дуже приємно. **Роздягайтеся** *(take off your coat)* і **проходьте** *(come through)* у вітальню.
> — **Джон:** У вас дуже гарна і простора квартира.
> — **Оксана:** Дякую. Тут є велика вітальня, світла кухня і наша затишна спальня.
> — **Джон:** Мені дуже подобається ваш новий килим на підлозі.
> — **Оксана:** Ми купили його вчора в магазині. А тепер проходьте на кухню.

Коли гості заходять у кімнату, господарі відразу запрошують їх до столу. Вони часто кажуть таку фразу: «**Сідайте за стіл**» *(Sit at the table)*. When we use the verb «сідати» to indicate movement, the preposition **за** *(behind / at)* requires the Accusative case. Після цього всі гості та господарі сидять разом. In this state of rest, the same preposition «за» takes the Instrumental case. Ми кажемо: «Ми **сидимо за столом**» *(We are sitting at the table)*. Це дуже важлива різниця в українській граматиці. Рух завжди вимагає знахідного відмінка, а позиція вимагає орудного. Гості довго сидять за великим столом у вітальні. Вони весело розмовляють, жартують і смачно вечеряють разом. Господарі завжди готують і пропонують багато різних страв. Усі почуваються дуже комфортно у цій приємній атмосфері.

На кухні господиня обов'язково пропонує теплі напої. Вона часто запитує своїх гостей: «**Хочете чаю?**» *(Do you want some tea?)* або «**Вип'ємо кави?**» *(Shall we drink some coffee?)*. Ukrainian uses the Genitive case here to express an unspecified quantity of something. Це правило називається частковий родовий відмінок. Гості можуть відповідати на ці питання по-різному. Вони використовують орудний відмінок з прийменником **з** *(with)*, щоб пояснити свої смаки. Наприклад, ви можете сказати: «Я хочу чорний чай **з лимоном**» *(with lemon)*. Або ви можете сказати господині: «Я буду пити каву **з молоком**» *(with milk)*. Деякі люди люблять солодкий чай **з цукром** *(with sugar)*. Інші друзі п'ють міцну каву без цукру. Господар також може привітно запитати: «Будете їсти смачний пиріг **з яблуками**?» *(with apples)*.

Під час вечері гості та господарі часто говорять про свій день. Вони цікавляться і запитують: «А о котрій годині ви встаєте вранці?». Ви можете детально відповісти: «Мій день починається рано, а мій чоловік прокидається пізно». Такі спокійні розмови допомагають краще пізнати одне одного. Українці дуже люблять обговорювати свій щоденний розпорядок дня за столом. In these social situations, the Dative case expresses gratitude or personal opinions. Наприкінці довгого вечора гості завжди щиро кажуть: «Дуже **дякую господарям**» *(thank you to the hosts)*. Замість дієслова «любити» ми часто використовуємо іншу популярну конструкцію. Ми кажемо: «**Мені подобається** ваша квартира» *(I like your apartment)*. Це звучить дуже ввічливо і природно для носіїв мови. Ви також можете радісно додати: «Нам подобається ваша смачна вечеря».

Спілкування в гостях гармонійно об'єднує всі ці граматичні правила. When addressing friends directly, Ukrainians use the Vocative case. Замість форми «Оксана» ми завжди кажемо «Оксано», а замість «Тарас» ми кличемо «Тарасе». Це просте правило робить розмову теплою і дружньою. Під час цікавої бесіди ми також часто використовуємо місцевий відмінок. Ми так детально розповідаємо, де ми активно працюємо чи вчимося. Наприклад, гість може серйозно розповідати: «Я зараз працюю **на фірмі**» *(at a firm)*. А господар швидко відповідає: «А моя дружина працює **у школі**» *(at a school)*. Ми плавно переходимо від теми дому до складної роботи та активного відпочинку. Наприкінці приємної зустрічі гості збираються додому. Вони одягаються в теплому коридорі, прощаються і йдуть відпочивати. Це був чудовий і веселий вечір з друзями!

<!-- INJECT_ACTIVITY: error-correction-cases -->


## Мовленнєве завдання: Опишіть свій дім (Speaking Task)

Тепер ваша черга активно розповідати про себе! Напишіть короткий текст про ваше **помешкання** *(apartment / dwelling)* та ваш типовий ранок. Ваш текст повинен мати приблизно десять речень. У цьому завданні вам потрібно детально описати ваш дім. Також розкажіть, що ви зазвичай робите щодня. Обов'язково згадайте у тексті щонайменше три різні кімнати та чотири предмети **меблів** *(furniture)*. Також напишіть про ваш **розпорядок дня** *(daily routine)* і використайте мінімум три точні вказівки на час. Це завдання чудово допоможе вам практикувати нові слова у реальному життєвому контексті.

To make your daily description accurate and natural, you must use the Ukrainian case system correctly. Here is your essential grammar checklist for this speaking task. First, use the Nominative case to list the rooms and furniture that exist in your cozy home. Second, use the Genitive case to talk about things you do not have, specifically using the negative word «немає». Third, use the Accusative case to describe the direct direction of your morning movement, like going into the kitchen or traveling to work. Fourth, use the Instrumental case to explain how you commute or exactly who you eat breakfast with. Finally, use the Locative case to describe exactly where furniture items are located and to state the specific time you usually wake up.

> [!model-answer] Модель відповіді
> Я зараз живу у великій і світлій квартирі. У моєму помешканні є простора спальня, сучасна кухня, велика вітальня та чиста ванна кімната. На жаль, у мене немає довгого балкона. У вітальні стоїть новий зручний диван, а біля нього стоїть маленький круглий стіл. У спальні є широке ліжко та висока дерев'яна шафа. Мій типовий розпорядок дня починається дуже рано. Вранці я зазвичай **встаю** *(get up)* о шостій годині і відразу йду у ванну кімнату. О сьомій годині я смачно **снідаю** *(have breakfast)* з чоловіком на нашій кухні. Ми із задоволенням п'ємо міцну чорну каву без цукру. О восьмій годині ранку я швидко їду на роботу. Я завжди їду в сучасний офіс машиною. Мені дуже подобається мій затишний дім і мій активний день!


## Підсумок
Сьогодні ми чудово попрацювали! Ви навчилися детально описувати своє **помешкання** *(apartment / dwelling)*. Тепер ви знаєте назви різних кімнат та популярних меблів. Ви також можете впевнено розповідати про свій щоденний **розпорядок дня** *(daily routine)*. Використання правильних відмінків робить вашу українську мову дуже природною.

To make sure you remember these essential grammar rules, please answer these чотири quick self-check questions:
1. Як правильно сказати "in the kitchen"? The correct answer is «на кухні». We use the Locative case here.
2. Який відмінок ми завжди використовуємо після слова «немає»? The correct answer is the Genitive case. Наприклад: «У мене немає балкона».
3. Як сказати "at 8 o'clock" українською мовою? The correct answer is «о восьмій годині». Always remember to use the preposition «о» with the Locative case for time.
4. Який відмінок потрібен для транспорту? The correct answer is the Instrumental case. Ми кажемо: «Я їду на роботу автобусом».

Спробуйте сьогодні ввечері подивитися на свою кімнату. Назвіть усі меблі українською мовою. Розкажіть собі про свої плани на завтра. Ваша щоденна практика робить дива!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: home-and-daily-life
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

**Level: A2 (Module 38/60) — ELEMENTARY**

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
