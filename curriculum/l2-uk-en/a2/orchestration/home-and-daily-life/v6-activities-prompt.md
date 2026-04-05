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

(No injection markers found in prose. All activities will go to workbook.)

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
## Сценарій 1: Моє помешкання (Scenario 1: My Home)

Олена переїхала в нове **помешкання** *(dwelling, apartment)*. Це дуже важлива і радісна подія для неї. Вона давно хотіла жити окремо від батьків. Вона орендувала простору квартиру в центрі міста. Сьогодні Олена має вільний час після роботи і хоче показати свій новий дім. Вона телефонує своєму найкращому другу Марку по відеозв'язку. Марк зараз живе і працює в іншому місті, але він завжди дуже радий за Олену. Вони починають віртуальну екскурсію квартирою, і Олена дуже хвилюється, чи сподобається Марку її вибір.

> — **Олена:** Привіт, Марку! Я нарешті переїхала в нову квартиру. Хочеш подивитися моє нове помешкання просто зараз?
> — **Марк:** Привіт, Олено! Звісно, я дуже хочу подивитися. Показуй усе! Це твій новий **коридор** *(hallway)*?
> — **Олена:** Так, це коридор. Він досить просторий і світлий. А тепер ми йдемо у найбільшу кімнату в цій квартирі. Це моя улюблена **вітальня** *(living room)*.
> — **Марк:** Ого, яка вона велика! Я бачу гарні меблі. Що там стоїть біля стіни?
> — **Олена:** Ось тут стоїть великий м'який **диван** *(sofa)*. А поруч є два дуже зручні **крісла** *(armchairs)*. На підлозі лежить теплий і пухнастий **килим** *(carpet)*.
> — **Марк:** Дуже затишно і стильно. А що це цікаве висить на стіні?
> — **Олена:** На стіні висить велика сучасна картина. Її намалювала моя талановита сестра. А в кутку стоїть новий торшер, який дає приємне світло ввечері.
> — **Марк:** Класно! Я теж хочу такий торшер. А у тебе є просторий **балкон** *(balcony)*?
> — **Олена:** Так, балкон є. Він дуже великий і відкритий. Там стоїть маленький стіл і два стільці. Я люблю пити там гарячу каву рано вранці.
> — **Марк:** Це звучить чудово. Покажи мені, будь ласка, інші кімнати у твоєму новому домі.

Олена продовжує екскурсію і показує Марку інші важливі кімнати свого нового дому. Вона заходить у різні приміщення. Це світла **кухня** *(kitchen)*, затишна **спальня** *(bedroom)* та чиста **ванна кімната** *(bathroom)*. Усі ці слова — це іменники жіночого роду. У називному відмінку вони закінчуються на «-я» або «-а».
When we want to say where something is located or where an action takes place, we use the Locative case. For feminine nouns ending in "-я" or "-а", the ending usually changes to "-і" in the Locative case.
Олена готує смачний обід у кухні. Вона міцно спить у спальні кожної ночі. Вранці вона вмивається у ванні перед роботою.
But for masculine nouns like "балкон" or "коридор", the Locative case also takes the "-і" ending, but we must use different prepositions depending on the physical location.
Яскраві квіти стоять на балконі. Велика шафа для одягу стоїть у коридорі біля дверей.
Notice the important difference in prepositions. We say "у кухні" *(in the kitchen)* when we are inside, but "на балконі" *(on the balcony)* when we are on a surface.

When we simply list objects that exist in a room, we use the Nominative case. This is the basic dictionary form of the words.
Тут є великий письмовий стіл, зручне дерев'яне ліжко та нова книжкова шафа.
But when we want to say that something is missing, or when we talk about the quantity of objects, we must use the Genitive case. This is a very common rule in the Ukrainian language.
У цій просторій кімнаті немає **телевізора** *(TV)*. Олена не любить дивитися новини. На жаль, у цьому будинку немає підземного **гаража** *(garage)*.
The common word "багато" *(many, a lot of)* also always requires the Genitive case.
У цьому сучасному будинку є дуже багато **кімнат** *(rooms)*. У новій вітальні Олени є багато цікавих **книжок** *(books)*.
We also use the Genitive case with specific prepositions of location, such as "біля" *(near, by)* or "навпроти" *(opposite)*.
Біля великого вікна стоїть зручний письмовий стіл. Навпроти м'якого дивана висить гарна картина.

Олена із задоволенням продовжує показувати свою нову квартиру. Вона докладно розповідає про свої нові **меблі** *(furniture)* та різні матеріали.
When we describe the specific characteristics of an object or a room, we can use the Instrumental case with the preposition "з" *(with, made of)*. This adds rich detail to our descriptions.
На світлій кухні стоїть новий міцний стіл з дерева. Це дуже простора кімната з великими чистими вікнами.
У маленькій спальні стоїть **зручне ліжко** *(comfortable bed)*. Поруч стоїть висока і **велика шафа** *(large wardrobe)* для одягу. Олена також нещодавно купила гарне кругле дзеркало з дерев'яною рамою. Марку надзвичайно сильно подобається нове помешкання його подруги Олени. Він щиро каже, що це ідеальне і затишне місце для спокійного життя. Олена повністю погоджується, адже вона дуже довго шукала саме таку ідеальну квартиру. Тепер вона може часто запрошувати своїх друзів у гості і насолоджуватися домашнім затишком щодня.

<!-- INJECT_ACTIVITY: fill-in, Complete a description of a home with the correct case forms for room and furniture nouns -->


## Сценарій 2: Мій звичайний день (Scenario 2: My Typical Day)

Ігор має дуже чіткий і організований **розпорядок дня** *(daily routine)*. Кожного ранку він прокидається рівно **о сьомій годині** *(at seven o'clock)*. Спочатку він іде у світлу ванну кімнату. Там він довго **вмивається** *(washes his face)* холодною водою. Потім він іде в спальню і швидко **одягається** *(gets dressed)* у новий діловий костюм. Ігор завжди дуже ретельно **готується** *(prepares)* до свого нового робочого дня. О сьомій п'ятнадцять він іде на кухню. Там він смачно снідає зі своєю дружиною та дітьми. **О пів на восьму** *(at half past seven)* він п'є міцну гарячу каву з теплим молоком. Це завжди допомагає йому швидко прокинутися і стати енергійним. Вранці Ігор ніколи не дивиться ранкові програми по телевізору. Він воліє тихо слухати свіжі новини по радіо. Його ранок завжди дуже активний, бадьорий і продуктивний.

When we talk about when an action happens, we can use simple adverbs of time. These words are very common and they do not change their form. Ігор із задоволенням п'є міцну каву **вранці** *(in the morning)*. Він дуже багато і наполегливо працює **вдень** *(in the afternoon)*. Ігор спокійно відпочиває вдома зі своєю родиною **увечері** *(in the evening)*. А пізно **вночі** *(at night)* він просто міцно спить у своєму ліжку. But we can also use nouns in different cases with specific prepositions to show exactly when something occurs in a daily sequence. We often use the Genitive case with the preposition «після» *(after)*. Ігор уважно читає свіжі новини **після сніданку** *(after breakfast)*. Ми довго гуляємо у великому парку **після роботи** *(after work)*. We use the Instrumental case with the preposition «перед» *(before)*. Ігор завжди ретельно вмивається **перед роботою** *(before work)*. Маленькі діти обов'язково миють руки **перед сном** *(before sleep)*. To show a logical sequence of daily actions, we use specific transition words. **Спочатку** *(first)* Ігор смачно снідає. **Потім** *(then)* він швидко одягається у костюм. **Після того** *(after that)* він одразу їде у свій офіс.

Ігор щодня їздить на свою улюблену роботу в самий центр великого міста. Він не має власного сучасного автомобіля. Тому він зазвичай **їде автобусом** *(goes by bus)* або **користується метро** *(uses the subway)*. In Ukrainian, we use the Instrumental case without a preposition to indicate the means of transportation. Він працює у просторому і світлому **офісі** *(office)* на десятому поверсі. This is the Locative case indicating location. Ігор працює там зі своїми розумними і приємними **колегами** *(colleagues)*. Here we use the Instrumental case with the preposition «з» *(with)* to show accompaniment. О першій годині дня вони всі разом йдуть у затишне кафе поруч. Там вони із задоволенням **обідають** *(have lunch)*. Іноді Ігор не має багато вільного часу на повноцінний гарячий обід. Тоді він просто швидко **перекушує** *(has a snack)* смачним бутербродом із сиром. Він п'є зелений чай з лимоном і продовжує активно працювати за комп'ютером.

Рівно о шостій годині вечора Ігор нарешті повертається додому. Він буває трохи втомлений, але він ще має зробити важливі домашні справи. Він дуже любить ідеальну чистоту, тому регулярно прибирає у своїй великій квартирі. Спочатку він ретельно **прибирає пилососом** *(vacuums)* новий м'який килим у просторій вітальні. Потім він іде на світлу кухню і починає **мити посуд** *(wash the dishes)* після спільної сімейної вечері. Увечері Ігор також повинен акуратно **прасувати одяг** *(iron clothes)* на завтрашній робочий день. Це його цілком звичайні і щоденні обов'язки у будні дні. Але **у вихідні** *(on weekends)* Ігор ніколи не працює і не робить важких справ. У суботу він просто розслаблено **відпочиває** *(rests)* і часто **ходить у кіно** *(goes to the cinema)* з друзями. А в неділю він з радістю їде в гості до своїх батьків у село.

<!-- INJECT_ACTIVITY: quiz, Choose the correct case form in daily routine sentences (time expressions, prepositions, verbs) -->
<!-- INJECT_ACTIVITY: match-up, Match daily activities with the correct time of day and appropriate case construction -->


## Сценарій 3: В гостях (Scenario 3: Visiting Someone)

> — **Оксана:** Привіт, Ігоре! **Заходьте, будь ласка!** *(Come in, please!)* Ми вас дуже чекали.
> — **Ігор:** Добрий вечір! Дуже радий вас бачити.
> — **Оксана:** Проходьте у коридор. **Роззувайтеся** *(take off your shoes)*, будь ласка. **Ось ваші капці** *(here are your slippers)*. Вони дуже зручні.
> — **Ігор:** Дякую! Я маю невеликі **гостинці** *(gifts)* для вас. Це свіжий торт.
> — **Оксана:** О, дуже дякуємо! Це так приємно і несподівано.

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

You have successfully used the full Ukrainian case system together. We used the Nominative case for listing objects. We applied the Genitive case for quantity, like «**багато кімнат**» *(many rooms)*, and absence, like «**немає телевізора**» *(no TV)*. We used the Accusative case for actions, like «**поставити стіл**» *(to put a table)*. We practiced the Instrumental case for transport, like «**автобусом**» *(by bus)*, and companionship, like «**з родиною**» *(with family)*. We used the Locative case for locations, like «**у кухні**» *(in the kitchen)*, and times, like «**о сьомій**» *(at seven)*.

Ми також вивчили нові дієслова. *(We also learned new verbs.)* Це слова «**вставати**» *(to get up)*, «**снідати**» *(to have breakfast)*, «**працювати**» *(to work)*, та «**лягати спати**» *(to go to bed)*. 

Now it is time for a quick self-check. Can you describe your bedroom? Can you tell someone what time you go to bed? Can you name five pieces of furniture in Ukrainian? Якщо так, ви готові до наступного кроку! *(If so, you are ready for the next step!)*

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
