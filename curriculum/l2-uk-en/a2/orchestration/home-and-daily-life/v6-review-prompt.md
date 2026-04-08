<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 38: Мій дім, мій день (A2, A2.5 [Case Synthesis and Plurals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-038
level: A2
sequence: 38
slug: home-and-daily-life
version: '1.0'
title: Мій дім, мій день
subtitle: Описуємо помешкання, меблі та щоденний розпорядок із повною системою відмінків
focus: communication
pedagogy: TBL
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
- Learner can describe their home and its rooms, using Locative for location (у кухні, на балконі), Genitive
  for absence/quantity (немає гаража, багато кімнат), and Nominative for listing (тут є диван, шафа, стіл).
- Learner can describe furniture and household items using Instrumental for characteristics (стіл з дерева,
  кімната з великими вікнами) and Accusative for actions (поставити стілець, повісити картину).
- Learner can narrate a daily routine in sequence, using appropriate tenses and cases (вранці я встаю
  о сьомій годині, снідаю з родиною, їду на роботу).
- Learner can participate in a dialogue about visiting someone's home, asking about rooms and routines
  using the full case system naturally.
dialogue_situations:
- setting: 'Scenario 1: Video tour of your помешкання (n, apartment) — кухня (f, kitchen), вітальня (f,
    living room), спальня (f, bedroom). Scenario 2: Describing your розпорядок дня (m, daily routine).
    Scenario 3: Visiting Ukrainian friends — bringing гостинці (pl, gifts).'
  speakers:
  - Мешканець
  - Онлайн-друг / Господарі
  motivation: 'Home + daily life: кухня(f), вітальня(f), спальня(f), гостинці(pl)'
content_outline:
- section: 'Сценарій 1: Моє помешкання (Scenario 1: My Home)'
  words: 600
  points:
  - 'Dialogue: showing a friend around a new apartment. Host describes rooms and furniture. Cases emerge
    naturally: Ось вітальня (Nom.). У вітальні (Loc.) стоїть великий диван. На стіні (Loc.) висить картина.
    Біля вікна (Gen.) є крісло.'
  - 'Room vocabulary: кухня, спальня, вітальня, ванна кімната, коридор, балкон, кабінет.'
  - 'Furniture vocabulary: диван, крісло, стіл, стілець, шафа, ліжко, полиця, дзеркало, килим.'
  - 'Guest asks questions: А скільки у вас кімнат (Gen.Pl.)? Що на балконі (Loc.)? Де ви поставили книжки
    (Acc.Pl.)?'
- section: 'Сценарій 2: Мій звичайний день (Scenario 2: My Typical Day)'
  words: 600
  points:
  - 'Monologue: describing a typical weekday from morning to evening. Вранці я встаю о сьомій (Loc. for
    time). Іду у ванну (Acc. direction). Снідаю з родиною (Instr.). Їду на роботу (Acc.) автобусом (Instr.).'
  - 'Daily actions: вставати, вмиватися, снідати, обідати, вечеряти, працювати, відпочивати, лягати спати.'
  - 'Time expressions: вранці, вдень, увечері, вночі; о котрій годині; після обіду (Gen.), перед сном
    (Instr.), під час роботи (Gen.).'
  - 'Contrast weekday vs. weekend: У будні я працюю, а у вихідні відпочиваю. По суботах ходжу на ринок
    (Acc.).'
- section: 'Сценарій 3: В гостях (Scenario 3: Visiting Someone)'
  words: 500
  points:
  - 'Dialogue: visiting a Ukrainian friend for dinner. Arrival, tour of the home, sitting down to eat,
    conversation about daily routines.'
  - 'Hospitality expressions: Будь ласка, заходьте! Сідайте за стіл (Acc.). Пригощайтеся! Хочете чаю (Gen.)
    чи кави (Gen.)?'
  - 'Comparing routines: А о котрій ви встаєте? Хто у вас готує вечерю (Acc.)? Ви снідаєте вдома (Loc.
    implied) чи на роботі (Loc.)?'
  - 'Cases in action: за столом (Instr.), на кухні (Loc.), для гостей (Gen.), з цукром (Instr.), дякую
    господарям (Dat.).'
- section: 'Мовленнєве завдання: Опишіть свій дім (Speaking Task: Describe Your Home)'
  words: 300
  points:
  - 'Guided production task: learner writes 8-10 sentences describing their home and daily routine, using
    a checklist to ensure they include at least 5 different cases.'
  - 'Checklist: use Nom. (what is there), Gen. (what is not there / how many), Dat. (for whom), Acc. (where
    you go / what you do), Instr. (with whom / by what means), Loc. (where things are).'
  - Model answer provided for comparison.
vocabulary_hints:
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
  recommended:
  - балкон (balcony)
  - коридор (hallway)
  - килим (carpet, rug)
  - пригощатися (to help oneself (to food))
  - господар (host)
activity_hints:
- type: fill-in
  focus: Complete a description of a home with the correct case forms for room and furniture nouns
  items: 8
- type: quiz
  focus: Choose the correct case form in daily routine sentences (time expressions, prepositions, verbs)
  items: 8
- type: match-up
  focus: Match daily activities with the correct time of day and appropriate case construction
  items: 8
- type: error-correction
  focus: Find and correct grammar errors in sentences
  items: 6
references:
- title: Заболотний Grade 5, §§25-28
  notes: Describing places and daily activities — case usage in context
- title: 'ULP: Home and Daily Routine'
  url: https://www.ukrainianlessons.com/season3/
  notes: Vocabulary for home description and daily routines with audio

</plan_content>

## Generated Content

<generated_module_content>
## Сценарій 1: Моє помешкання

Сьогодні ми йдемо в гості онлайн.
Наш знайомий показує своє нове **помешкання** *(apartment, dwelling)*.
Він знімає відео для свого друга з іншого міста.
У цьому відео ми побачимо, як називати кімнати.
Ми також почуємо, як сказати, де саме ви перебуваєте.

> — **Мешканець:** Привіт! Ось моя нова **квартира** *(apartment)*. Я зараз у квартирі, але тут ще мало речей.
> — **Онлайн-друг:** О, вітаю з переїздом! Це дуже цікаво. Яка це кімната?
> — **Мешканець:** Це — довгий **коридор** *(hallway)*. А тут далі є велика **вітальня** *(living room)*.
> — **Онлайн-друг:** Супер! А де розташована **кухня** *(kitchen)*?
> — **Мешканець:** Я зараз на кухні. Вона дуже світла. А там праворуч є **спальня** *(bedroom)*.
> — **Онлайн-друг:** Клас! Ти вже живеш у цій квартирі? **А скільки у вас кімнат?**
> — **Мешканець:** Тут три кімнати. Я вже сплю у спальні, але тут ще є багато роботи.
> — **Онлайн-друг:** **Що на балконі? Де ви поставили книжки?**
> — **Мешканець:** На балконі поки що порожньо, а книжки я поклав у шафу.

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

Our daily routine changes depending on the day of the week. We use the phrase «**у будні**» *(on weekdays)* for Monday through Friday. У будні я дуже рано встаю і їду на роботу. У будні ми завжди багато працюємо. We contrast this with «**у вихідні**» *(on weekends)*. У вихідні я прокидаюся дуже пізно. У вихідні ми довго гуляємо в зеленому парку. If you want to describe a habitual action that happens every Saturday, you can use the preposition «по» with the Locative plural form. Я ходжу в басейн **по суботах** *(on Saturdays)*. Ми їздимо в маленьке село **по неділях** *(on Sundays)*. Ця граматична форма добре показує регулярність. Я часто ходжу **на ринок** *(to the market)* по суботах. Там я купую свіжі овочі та фрукти з родиною. Після ринку ми разом обідаємо на світлій кухні. Це наш ідеальний день.

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

Коли гості заходять у кімнату, господарі відразу запрошують їх до столу. Вони часто кажуть таку фразу: «**Сідайте за стіл**» *(Sit at the table)*. When we use the verb «сідати» to indicate movement, the preposition **за** *(behind / at)* requires the Accusative case. Після цього всі гості та господарі сидять разом. In this state of rest, the same preposition «за» takes the Instrumental case. Ми кажемо: «Ми **сидимо за столом**» *(We are sitting at the table)*. Це дуже важлива різниця в українській граматиці. Рух завжди вимагає знахідного відмінка, а позиція вимагає орудного. Гості довго сидять за великим столом у вітальні. Вони весело розмовляють, жартують і смачно вечеряють разом. Господарі завжди готують багато різних страв і радісно кажуть: «**Пригощайтеся!**» *(Help yourself!)*. Гості із задоволенням **пригощаються** *(help themselves)* смачною їжею. Усі почуваються дуже комфортно у цій приємній атмосфері.

На кухні господиня обов'язково пропонує теплі напої. Вона часто запитує своїх гостей: «**Хочете чаю?**» *(Do you want some tea?)* або «**Вип'ємо кави?**» *(Shall we drink some coffee?)*. Ukrainian uses the Genitive case here to express an unspecified quantity of something. Це правило називається частковий родовий відмінок. Гості можуть відповідати на ці питання по-різному. Вони використовують орудний відмінок з прийменником **з** *(with)*, щоб пояснити свої смаки. Наприклад, ви можете сказати: «Я хочу чорний чай **з лимоном**» *(with lemon)*. Або ви можете сказати господині: «Я буду пити каву **з молоком**» *(with milk)*. Деякі люди люблять солодкий чай **з цукром** *(with sugar)*. Інші друзі п'ють міцну каву без цукру. Господар також може привітно запитати: «Будете їсти смачний пиріг **з яблуками**?» *(with apples)*.

Під час вечері гості та господарі часто говорять про свій день. Вони цікавляться і запитують: «А о котрій годині ви встаєте вранці?». Вони також можуть спитати: «**Хто у вас готує вечерю?**» або «**Ви снідаєте вдома чи на роботі?**». Ви можете детально відповісти: «Мій день починається рано, а снідаю я зазвичай вдома». Такі спокійні розмови допомагають краще пізнати одне одного. Українці дуже люблять обговорювати свій щоденний розпорядок дня за столом. In these social situations, the Dative case expresses gratitude or personal opinions. Наприкінці довгого вечора гості завжди щиро кажуть: «Дуже **дякую господарям**» *(thank you to the hosts)*. Замість дієслова «любити» ми часто використовуємо іншу популярну конструкцію. Ми кажемо: «**Мені подобається** ваша квартира» *(I like your apartment)*. Це звучить дуже ввічливо і природно для носіїв мови. Ви також можете радісно додати: «Нам подобається ваша смачна вечеря».

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
</generated_module_content>

**PIPELINE NOTE — Word count: 2673 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 673 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Джон — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Оксано — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM

All 673 other words are confirmed to exist in VESUM.

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
