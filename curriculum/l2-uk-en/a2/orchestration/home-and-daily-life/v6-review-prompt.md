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
## Сценарій 1: Моє помешкання (Scenario 1: My Home)

Олена переїхала в нове **помешкання** *(dwelling, apartment)*. Це дуже важлива і радісна подія для неї. Вона давно хотіла жити окремо від батьків. Вона орендувала простору квартиру в центрі міста. Сьогодні Олена має вільний час після роботи і хоче показати свій новий дім. Вона телефонує своєму найкращому другу Марку по відеозв'язку. Марк зараз живе і працює в іншому місті, але він завжди дуже радий за Олену. Вони починають віртуальну екскурсію квартирою, і Олена дуже хвилюється, чи сподобається Марку її вибір.

> — **Олена:** Привіт, Марку! Я нарешті переїхала в нову квартиру. Хочеш подивитися моє нове помешкання просто зараз?
> — **Марк:** Привіт, Олено! Звісно, я дуже хочу подивитися. Показуй усе! Це твій новий **коридор** *(hallway)*?
> — **Олена:** Так, це коридор. Він досить просторий і світлий. А тепер ми йдемо у найбільшу кімнату в цій квартирі. Це моя улюблена **вітальня** *(living room)*.
> — **Марк:** Ого, яка вона велика! Я бачу гарні меблі. Що там стоїть біля стіни?
> — **Олена:** Ось тут стоїть великий м'який **диван** *(sofa)*. А поруч є два зручні **крісла** *(armchairs)*. На підлозі лежить теплий **килим** *(carpet)*.
> — **Марк:** Дуже затишно і стильно. А що це цікаве висить на стіні?
> — **Олена:** На стіні висить картина. Її намалювала моя сестра. А в кутку стоїть торшер, який дає приємне світло ввечері. Біля стіни є книжкова полиця з моїми улюбленими книжками.
> — **Марк:** Класно! Я теж хочу такий торшер. А у тебе є просторий **балкон** *(balcony)*?
> — **Олена:** Так, балкон є. Він дуже великий і відкритий. Там стоїть маленький стіл і два стільці. Я люблю пити там гарячу каву рано вранці.
> — **Марк:** Як гарно! А чи є у тебе окремий кабінет для роботи?
> — **Олена:** Кабінету, на жаль, немає. Але я маю маленький письмовий стіл у спальні. Ходімо, покажу тобі інші кімнати.

Олена продовжує екскурсію і показує Марку інші важливі кімнати свого нового дому. Вона заходить у різні приміщення. Це світла **кухня** *(kitchen)*, затишна **спальня** *(bedroom)* та чиста **ванна кімната** *(bathroom)*. Note that «ванна кімната» is a two-word name — «ванна» is the main noun, «кімната» specifies the type. All three are feminine nouns. In the Nominative case, they end in «-я» (кухня, спальня) or «-а» (ванна).
When we want to say where something is located or where an action takes place, we use the Locative case. For feminine nouns ending in "-я" or "-а", the ending usually changes to "-і" in the Locative case.
Олена готує смачний обід на кухні. Вона міцно спить у спальні кожної ночі. Вранці вона вмивається у ванні перед роботою.
But for masculine nouns like "балкон" or "коридор", the Locative case also takes the "-і" ending, but we must use different prepositions depending on the physical location.
Яскраві квіти стоять на балконі. Велика шафа для одягу стоїть у коридорі біля дверей.
Notice that Ukrainian uses different prepositions with different places. Some rooms conventionally take «на»: **на кухні** *(in the kitchen)*, **на балконі** *(on the balcony)*. Others take «у»: **у вітальні**, **у спальні**, **у коридорі**. This is a matter of tradition — you need to remember which preposition goes with which place.

When we simply list objects that exist in a room, we use the Nominative case. This is the basic dictionary form of the words.
Тут є великий письмовий стіл, зручне дерев'яне ліжко та нова книжкова шафа.
But when we want to say that something is missing, or when we talk about the quantity of objects, we must use the Genitive case. This is a very common rule in the Ukrainian language.
У цій просторій кімнаті немає **телевізора** *(TV)*. Олена не любить дивитися новини. На жаль, у цьому будинку немає підземного **гаража** *(garage)*.
The common word "багато" *(many, a lot of)* also always requires the Genitive case.
У цьому сучасному будинку є дуже багато **кімнат** *(rooms)*. У новій вітальні Олени є багато цікавих **книжок** *(books)*.
We also use the Genitive case with specific prepositions of location, such as "біля" *(near, by)* or "навпроти" *(opposite)*.
Біля великого вікна стоїть зручний письмовий стіл. Навпроти м'якого дивана висить гарна картина.

Олена продовжує показувати квартиру. Вона розповідає про свої **меблі** *(furniture)* та матеріали, з яких вони зроблені.
When we describe objects, the preposition "з" is very useful — but be careful, because it takes two different cases depending on meaning!
When "з" means "made of" (material or origin), it takes the **Genitive** case.
На кухні стоїть міцний стіл **з дерева** *(of wood — Genitive)*.
But when "з" means "with" (accompaniment or a characteristic), it takes the **Instrumental** case.
Це простора кімната **з великими вікнами** *(with large windows — Instrumental)*.
This is an important distinction — "з дерева" (Gen.) tells us what the table is made of, while "з вікнами" (Instr.) tells us what the room has.
У спальні стоїть **зручне ліжко** *(comfortable bed)*. Поруч стоїть **велика шафа** *(large wardrobe)* для одягу. Олена також нещодавно купила кругле дзеркало з дерев'яною рамою. Марку дуже подобається нове помешкання Олени. Він щиро каже, що це затишне місце для життя. Олена погоджується — вона довго шукала саме таку квартиру. Тепер вона може часто запрошувати своїх друзів у гості і насолоджуватися домашнім затишком щодня.

<!-- INJECT_ACTIVITY: fill-in, Complete a description of a home with the correct case forms for room and furniture nouns -->

## Сценарій 2: Мій звичайний день (Scenario 2: My Typical Day)

Ігор має чіткий **розпорядок дня** *(daily routine)*. Кожного ранку він прокидається рівно **о сьомій годині** *(at seven o'clock)*. Спочатку він іде у світлу ванну кімнату. Там він **вмивається** *(washes his face)* холодною водою. Потім він іде в спальню і **одягається** *(gets dressed)*. Ігор завжди ретельно **готується** *(prepares)* до робочого дня. О сьомій п'ятнадцять він іде на кухню. Там він смачно снідає зі своєю дружиною та дітьми. **О пів на восьму** *(at half past seven)* він п'є міцну гарячу каву з теплим молоком. Це завжди допомагає йому швидко прокинутися і стати енергійним. Вранці Ігор ніколи не дивиться ранкові програми по телебаченню. Він воліє тихо слухати свіжі новини по радіо. Його ранок завжди дуже активний, бадьорий і продуктивний.

When we talk about when an action happens, we can use simple adverbs of time. These words are very common and they do not change their form. Ігор п'є каву **вранці** *(in the morning)*. Він багато працює **вдень** *(in the afternoon)*. Ігор відпочиває вдома з родиною **увечері** *(in the evening)*. А **вночі** *(at night)* він міцно спить. But we can also use nouns in different cases with specific prepositions to show exactly when something occurs in a daily sequence. We often use the Genitive case with the preposition «після» *(after)*. Ігор уважно читає свіжі новини **після сніданку** *(after breakfast)*. Ми довго гуляємо у великому парку **після роботи** *(after work)*. We use the Instrumental case with the preposition «перед» *(before)*. Ігор завжди ретельно вмивається **перед роботою** *(before work)*. Маленькі діти обов'язково миють руки **перед сном** *(before sleep)*. Ігор часто слухає музику **під час роботи** *(during work — Genitive)*. To show a logical sequence of daily actions, we use specific transition words. **Спочатку** *(first)* Ігор смачно снідає. **Потім** *(then)* він швидко одягається у костюм. **Після того** *(after that)* він одразу їде у свій офіс.

Ігор щодня їздить на свою улюблену роботу в самий центр великого міста. Він не має власного сучасного автомобіля. Тому він зазвичай **їде автобусом** *(goes by bus)* або **користується метро** *(uses the subway)*. In Ukrainian, we use the Instrumental case without a preposition to indicate the means of transportation. Він працює в **офісі** *(office)* на десятому поверсі. This is the Locative case indicating location. Ігор працює там зі своїми **колегами** *(colleagues)*. Here we use the Instrumental case with the preposition «з» *(with)* to show accompaniment. О першій годині дня вони всі разом йдуть у затишне кафе поруч. Там вони разом **обідають** *(have lunch)*. Іноді Ігор не має часу на повноцінний обід. Тоді він просто швидко **перекушує** *(has a snack)* смачним бутербродом із сиром. Він п'є зелений чай з лимоном і продовжує активно працювати за комп'ютером.

Рівно о шостій годині вечора Ігор нарешті повертається додому. Він буває трохи втомлений, але він ще має зробити важливі домашні справи. Він дуже любить ідеальну чистоту, тому регулярно прибирає у своїй великій квартирі. Спочатку він **прибирає пилососом** *(vacuums)* килим у вітальні. Потім він іде на кухню і починає **мити посуд** *(wash the dishes)* після сімейної вечері. Увечері Ігор також **прасує одяг** *(irons clothes)* на завтра. О пів на одинадцяту він зазвичай **лягає спати** *(goes to bed)*. Це його звичайні обов'язки у будні. Але **у вихідні** *(on weekends)* Ігор ніколи не працює і не робить важких справ. **По суботах** *(on Saturdays — Loc.Pl., recurring)* він ходить на **ринок** *(market — Acc., direction)* за свіжими овочами і фруктами. Потім він розслаблено **відпочиває** *(rests)* і часто **ходить у кіно** *(goes to the cinema)* з друзями. А в неділю він їде в гості до батьків у село.

<!-- INJECT_ACTIVITY: quiz, Choose the correct case form in daily routine sentences (time expressions, prepositions, verbs) -->
<!-- INJECT_ACTIVITY: match-up, Match daily activities with the correct time of day and appropriate case construction -->

## Сценарій 3: В гостях (Scenario 3: Visiting Someone)

> — **Оксана:** Привіт, Ігоре! **Заходьте, будь ласка!** *(Come in, please!)* Ми вас дуже чекали.
> — **Ігор:** Добрий вечір! Дуже радий вас бачити.
> — **Оксана:** Проходьте у коридор. **Роззувайтеся** *(take off your shoes)*, будь ласка. **Ось ваші капці** *(here are your slippers)*. Вони дуже зручні.
> — **Ігор:** Дякую! Я маю невеликі **гостинці** *(gifts)* для вас. Це свіжий торт.
> — **Оксана:** О, дуже дякуємо! Це так приємно. Будь ласка, заходь далі. Ми приготували каву з цукром і тістечка для гостей.

When we visit friends in Ukraine, hospitality is very important. When guests arrive, the host usually invites them inside and politely asks them to take off their shoes. They often offer comfortable slippers to keep the house clean. In these social interactions, we frequently use verbs that require the Dative case to show the recipient of an action or feeling. For example, the verb «дякувати» *(to thank)* takes the Dative case. Ігор ввічливо каже: «Я **дякую господарям** *(thank the hosts)*». Оксана готує смачну вечерю на кухні, а Ігор каже: «Я із задоволенням **допомагаю Оксані** *(help Oksana)*». The Dative case is absolutely essential for polite communication.

Після короткої розмови у коридорі Оксана запрошує гостя у свою простору вітальню. Там посеред кімнати стоїть великий стіл.

> — **Оксана:** Прошу, **сідайте за стіл** *(sit down at the table)*.
> — **Ігор:** Дякую. У вас дуже гарна і надзвичайно затишна кімната.
> — **Оксана:** **Пригощайтеся** *(help yourself)*, будь ласка. Тут є різні салати, смажене м'ясо і свіжий хліб.

Notice the important difference between motion and position when talking about furniture. When Oksana invites Igor to sit down, she uses the Accusative case because it indicates a clear direction: «сідайте **за стіл**» *(sit down at the table - direction)*. But when they are already eating and talking, we use the Instrumental case to indicate their position: «ми зараз сидимо **за столом**» *(we are sitting at the table - position)*.

> — **Оксана:** Що ви будете пити сьогодні? **Хочете чаю чи кави?** *(Do you want tea or coffee?)*
> — **Ігор:** **Я буду воду з лимоном** *(I will have water with lemon)*, якщо можна.
> — **Оксана:** Звісно. Ви хочете ще **трохи** *(a little)* овочевого салату?
> — **Ігор:** Так, дякую. Але, будь ласка, не дуже **багато** *(a lot)*.

When offering food or drink, Ukrainians often use the Genitive case to indicate a portion or an undefined quantity of something. This grammatical concept is called the partitive Genitive. That is exactly why Oksana asks «Хочете **чаю** чи **кави**?» *(tea or coffee - Genitive)* instead of using the Accusative case. However, when you state exactly what you will have, you use the standard Accusative case: «Я буду **воду**» *(water - Accusative)*. We also must use the Genitive case after adverbs that express quantity, such as «трохи» and «багато». Ігор хоче **трохи салату** *(a little salad - Genitive)*.

Під час смачної вечері друзі дуже приємно спілкуються. Вони спокійно говорять про роботу, життя та свій звичайний розпорядок дня.

> — **Оксана:** Ігоре, **а о котрій ви зазвичай снідаєте?** *(and at what time do you usually have breakfast?)*
> — **Ігор:** Я снідаю дуже рано, о сьомій годині. А ви?
> — **Оксана:** Ми снідаємо о восьмій годині. Мій чоловік завжди робить ранкову каву.
> — **Ігор:** А **хто у вашій родині готує вечерю?** *(who in your family cooks dinner?)*
> — **Оксана:** Зазвичай я сама готую вечерю, а чоловік миє посуд.

In this casual conversation, we clearly see different cases working together. We use the Locative case for specific times: «**о сьомій годині**» *(at seven o'clock)* and locations: «**у родині**» *(in the family)*. We use the Nominative case for the active subject doing the action: «**хто** готує» *(who cooks)* or «**чоловік** робить» *(husband makes)*. And we use the Accusative case for the direct object of the action: «готує **вечерю**» *(cooks dinner)* or «миє **посуд**» *(washes dishes)*.

<!-- INJECT_ACTIVITY: error-correction, Find and correct grammar errors in sentences involving case usage in home/routine contexts -->

## Мовленнєве завдання: Опишіть свій дім (Speaking Task: Describe Your Home)

Зараз ваша черга розповісти про своє життя. Напишіть короткий текст про своє **помешкання** *(dwelling)* та свій звичайний день. Ваша розповідь має містити десять речень. Опишіть, де ви живете, які кімнати та меблі є у вашому домі. Також розкажіть про свій **розпорядок дня** *(daily routine)*. Спробуйте розказати про свій день від ранку до вечора. Напишіть, о котрій годині ви встаєте. З ким ви снідаєте? Як ви їдете на роботу? Що ви робите ввечері, коли повертаєтеся додому? Ви можете почати так: «Привіт! Я живу у... Моє помешкання має... Щодня я...»

When writing your paragraph, use this grammar checklist to practice different cases:
- Nominative: to list the furniture and rooms in your home.
- Genitive: to describe what you do not have or to express quantity.
- Accusative: to show direction or the direct objects of your daily actions.
- Instrumental: to talk about transport or the people you spend time with.
- Locative: to describe the exact location of your furniture and the specific times of your daily routine.

Here is a comprehensive model answer to help you structure your text. Pay attention to how different cases are used naturally.

> [!model-answer]
> Привіт! Я живу в невеликій однокімнатній квартирі (Loc.). У моїй квартирі (Loc.) є вітальня (Nom.), кухня (Nom.) та ванна (Nom.). На жаль, у мене немає балкона (Gen.) або гаража (Gen.). У вітальні (Loc.) стоїть великий диван (Nom.), а біля дивана (Gen.) стоїть торшер (Nom.). На стіні (Loc.) висить картина (Nom.). Вранці я зазвичай встаю о шостій годині (Loc.). Я йду у ванну (Acc.), а потім іду на кухню (Acc.). Там я готую сніданок (Acc.). Я снідаю з дружиною (Instr.). Після сніданку (Gen.) я їду на роботу (Acc.) машиною (Instr.). Я працюю в офісі (Loc.) до шостої години (Gen.). Увечері я повертаюся додому. Ми разом вечеряємо за столом (Instr.). Перед сном (Instr.) я відпочиваю на дивані (Loc.). Там я часто читаю книгу (Acc.).

## Підсумок

У цьому модулі ми навчилися описувати свій дім та розпорядок дня. *(In this module, we learned to describe our home and daily routine.)* 

 We used the Nominative case for listing objects. We applied the Genitive case for quantity, like «**багато кімнат**» *(many rooms)*, and absence, like «**немає телевізора**» *(no TV)*. We used the Accusative case for actions, like «**поставити стіл**» *(to put a table)*. We practiced the Instrumental case for transport, like «**автобусом**» *(by bus)*, and companionship, like «**з родиною**» *(with family)*. We used the Locative case for locations, like «**у кухні**» *(in the kitchen)*, and times, like «**о сьомій**» *(at seven)*.

Ми також вивчили нові дієслова. *(We also learned new verbs.)* Це слова «**вставати**» *(to get up)*, «**снідати**» *(to have breakfast)*, «**працювати**» *(to work)*, та «**лягати спати**» *(to go to bed)*. 

Now it is time for a quick self-check. Can you describe your bedroom? Can you tell someone what time you go to bed? Can you name five pieces of furniture in Ukrainian? Якщо так, ви готові до наступного кроку! *(If so, you are ready for the next step!)*

**Deterministic word count: 2669 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

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
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
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

Verified: 604 words | Not found: 8 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ігоре — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Оксані — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олени — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Олену — NOT IN VESUM

All 604 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp__rag__verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp__rag__verify_lemma` — full declension/conjugation for a lemma
- `mcp__rag__search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp__rag__query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp__rag__query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp__rag__search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp__rag__search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp__rag__search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp__rag__search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp__rag__query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp__rag__search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp__rag__search_literary` — verify literary references against primary sources
- `mcp__rag__query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
