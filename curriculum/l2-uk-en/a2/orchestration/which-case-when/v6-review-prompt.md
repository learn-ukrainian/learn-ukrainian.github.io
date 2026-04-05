<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 36: Компас відмінків (A2, A2.5 [Case Synthesis and Plurals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-036
level: A2
sequence: 36
slug: which-case-when
version: '1.0'
title: Компас відмінків
subtitle: Як обрати правильний відмінок за дієсловом, прийменником та контекстом
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
  - Learner can select the correct case for a noun based on the governing verb 
    (e.g., допомагати + Dat., бачити + Acc., користуватися + Instr.).
  - Learner can select the correct case after common prepositions, including 
    prepositions that govern different cases depending on meaning (на + Acc. for
    direction vs. на + Loc. for location).
  - Learner can use Accusative for time expressions (у четвер, у середу), with 
    про (думати про майбутнє), and recognize Locative for characteristics 
    (хлопець у червоному светрі), path (бігати по кімнаті), and years (у 2014 
    році).
  - Learner can apply a systematic decision process (verb/preposition → case → 
    ending) to determine the correct form of any noun in context.
dialogue_situations:
  - setting: 'Grammar detective game — reading a Ukrainian newspaper article and identifying
      which case is used and why: Президент (nom) зустрівся з прем''єром (inst). Для
      журналістів (gen) підготували зал (acc).'
    speakers:
      - Вчитель
      - Студенти
    motivation: 'Case identification: nom, gen, dat, acc, inst, loc in real text'
content_outline:
  - section: 'Дієслово вирішує: Який відмінок після дієслова? (The Verb Decides: Which
      Case After a Verb?)'
    words: 550
    points:
      - 'Accusative verbs (most transitive): бачити, знати, любити, читати, купити,
        шукати + Acc. Я читаю книгу. Ми шукаємо ключі.'
      - 'Dative verbs: допомагати, телефонувати, дякувати, радити, заважати + Dat.
        Я допомагаю сестрі. Ми дякуємо вчителям.'
      - 'Instrumental verbs: користуватися, цікавитися, займатися, керувати + Instr.
        Він користується комп''ютером. Вона цікавиться історією.'
      - 'Genitive verbs/constructions: немає + Gen., боятися + Gen., потребувати +
        Gen. У мене немає часу. Вона боїться темряви.'
      - 'Thinking about + Acc.: думати про + Acc. (думати про майбутнє, мріяти про
        подорож).'
  - section: 'Прийменник вирішує: Один прийменник — різні відмінки (The Preposition
      Decides: One Preposition, Different Cases)'
    words: 550
    points:
      - 'на + Acc. (direction/goal): Я йду на роботу. Поклади книгу на стіл. на +
        Loc. (location): Я на роботі. Книга лежить на столі.'
      - 'у/в + Acc. (direction): Я йду в магазин. Acc. for time: у четвер, у середу,
        у п''ятницю. у/в + Loc. (location): Я в магазині. Loc. for years: у 2014 році,
        у минулому році.'
      - 'по + Loc. (path/surface): бігати по кімнаті, ходити по вулиці, подорожувати
        по Україні.'
      - 'з/із + Gen. (from/out of): вийти з дому, приїхати з Києва. з/із + Instr.
        (together with): піти з другом, кава з молоком.'
      - 'за + Acc. (in exchange/for): дякувати за допомогу, платити за квитки. за
        + Instr. (behind/after): за столом, бігти за автобусом.'
  - section: 'Особливі випадки: Час, характеристика, шлях (Special Uses: Time, Characteristics,
      Path)'
    words: 500
    points:
      - 'Acc. for days and time periods: у четвер, у середу, у п''ятницю. Цю неділю
        я відпочиваю. Наступного тижня (Gen. for next/last).'
      - 'Loc. for characteristics/description: хлопець у червоному светрі, дівчина
        в окулярах, жінка у білому пальті. Pattern: noun + у/в + Loc. describes what
        someone is wearing or looks like.'
      - 'Loc. for years and time contexts: у 2014 році, у двадцять першому столітті,
        у дитинстві.'
      - 'Loc. for path with по: бігати по кімнаті, гуляти по парку, їздити по місту.'
  - section: 'Алгоритм вибору відмінка (The Case Selection Algorithm)'
    words: 400
    points:
      - 'Step 1: Is there a preposition? → Check which case(s) it governs. Step 2:
        No preposition? → Check which case the verb requires. Step 3: Still unsure?
        → Ask the case question (Кого? Що? Кому? Ким? etc.).'
      - 'Decision tree visual: Preposition → Case. Verb → Case. Neither → Default
        Nom. (subject) or context-dependent.'
      - 'Common pitfalls: confusing на + Acc. (direction) with на + Loc. (location);
        forgetting that думати takes про + Acc., not Loc.; using Gen. instead of Dat.
        after допомагати.'
      - 'Practice: mixed sentences where learner must identify the trigger (verb or
        preposition) and choose the correct case.'
vocabulary_hints:
  required:
    - відмінок (grammatical case)
    - прийменник (preposition)
    - дієслово (verb)
    - напрямок (direction)
    - місце (place, location)
    - час (time)
    - характеристика (characteristic, description)
    - думати (to think)
    - боятися (to be afraid)
    - користуватися (to use)
  recommended:
    - алгоритм (algorithm)
    - контекст (context)
    - керувати (to manage, drive)
    - майбутнє (future)
activity_hints:
  - type: quiz
    focus: Given a sentence with a blank, choose the correct case form based on 
      the governing verb or preposition
    items: 8
  - type: group-sort
    focus: Sort prepositions by which case(s) they govern (Acc., Gen., Instr., 
      Loc.)
    items: 8
  - type: fill-in
    focus: Complete sentences with the correct noun form — mixed cases triggered
      by different prepositions and verbs, including time expressions (у 
      четвер), characteristics (у червоному светрі), and path (по кімнаті)
    items: 8
  - type: true-false
    focus: Judge whether the case used in a sentence is correct or incorrect, 
      including tricky pairs like на роботу (Acc.) vs. на роботі (Loc.)
    items: 8
references:
  - title: Заболотний Grade 6, §§59-67
    notes: Complete case system overview — when each case is used, with 
      preposition tables
  - title: Заболотний Grade 10, §§44-45
    notes: Advanced case usage — Loc. for characteristics, time expressions with
      cases
  - title: "ULP: Ukrainian Cases Overview"
    url: "https://www.ukrainianlessons.com/ukrainian-cases/"
    notes: Practical summary of all 7 cases with usage examples

</plan_content>

## Generated Content

<generated_module_content>
## Дієслово вирішує: Який відмінок після дієслова?

Уявіть, що у вас є надійний граматичний компас *(grammatical compass)*. Цей компас допомагає швидко обрати правильний відмінок *(case)*. Відмінки в українській мові ніколи не бувають випадковими. У реченні майже завжди є головне слово, яке вимагає конкретного відмінка для інших слів. Це граматичне явище лінгвісти називають керування *(government)*. Найчастіше таким потужним тригером є саме дієслово *(verb)*. Наприклад, дієслово «бачити» *(to see)* завжди вимагає питання «кого? що?». Тому ми правильно кажемо «бачу нову книгу» *(I see a new book)*, а не просто «книга».

Найбільша група дієслів завжди вимагає Знахідного відмінка *(Accusative case)*. Це перехідні дієслова *(transitive verbs)*, які означають пряму дію, спрямовану на конкретний об'єкт. Ви вже дуже добре знаєте ці популярні дієслова: «любити» *(to love)*, «знати» *(to know)*, «читати» *(to read)*, «купити» *(to buy)*, «шукати» *(to look for)*. Після них ми завжди ставимо питання «кого? що?».
Жіночий рід *(feminine gender)* тут змінює закінчення «-а» на «-у», а «-я» на «-ю». Наприклад: «Я дуже люблю сучасну Україну» *(I love modern Ukraine very much)*. «Ми зараз читаємо цікаву статтю» *(We are reading an interesting article now)*.
Чоловічий рід *(masculine gender)* має два різні варіанти. Для неістот *(inanimate objects)* базова форма зовсім не змінюється. Наприклад: «Я читаю довгий текст» *(I am reading a long text)*. «Ми активно шукаємо старий парк» *(We are actively looking for an old park)*. Але для істот *(animate objects)* закінчення обов'язково змінюється на «-а» або «-я». Наприклад: «Я сьогодні бачу старшого брата» *(I see an older brother today)*. «Вона добре знає цього лікаря» *(She knows this doctor well)*.

Інша дуже важлива група дієслів вимагає використання Давального відмінка *(Dative case)*. Це дієслова, які зазвичай означають передачу інформації, допомогу або ставлення до конкретної людини. До цієї групи належать дієслова «допомагати» *(to help)*, «телефонувати» *(to call)*, «дякувати» *(to thank)*, «радити» *(to advise)*, «заважати» *(to disturb)*. Після них ми завжди ставимо питання «кому? чому?».
Зверніть особливу увагу на типові закінчення. Чоловічий рід найчастіше отримує довгі закінчення «-ові» або «-еві». Наприклад: «Я часто телефоную своєму найкращому другові» *(I often call my best friend)*. «Студент щиро дякує новому вчителю» *(A student sincerely thanks a new teacher)*. Жіночий рід зазвичай має просте закінчення «-і». Наприклад: «Він щодня допомагає молодшій сестрі» *(He helps a younger sister every day)*. «Ми завжди дякуємо нашій мамі» *(We always thank our mom)*. Пам'ятайте, що в українській мові ми дякуємо комусь, а не когось. Тому ми завжди кажемо «дякую вам» *(thank you)*, а не «дякую вас».

Деякі цікаві дієслова обов'язково вимагають Орудного відмінка *(Instrumental case)*. Зазвичай це дієслова, які означають ваш інтерес, використання якогось інструмента або професійне управління. Це дуже популярні дієслова: «цікавитися» *(to be interested in)*, «користуватися» *(to use)*, «займатися» *(to be engaged in)*, «керувати» *(to manage/drive)*. Після них ми завжди ставимо питання «ким? чим?».
Наприклад, якщо ви використовуєте певний предмет як інструмент, ви кажете: «Він користується новим дорогим комп'ютером» *(He uses a new expensive computer)*. Якщо ви маєте серйозне хобі або інтерес, ви скажете: «Вона глибоко цікавиться українською історією» *(She is deeply interested in Ukrainian history)* або «Мій старший брат професійно займається спортом» *(My older brother professionally does sports)*. Якщо людина має високу керівну посаду, ми кажемо: «Директор успішно керує великою компанією» *(A director successfully manages a large company)*.

Також дієслово «думати» з прийменником «про» завжди вимагає Знахідного відмінка: «Я думаю про майбутнє» *(I think about the future)*. «Вона мріє про подорож» *(She dreams about a trip)*. Запам'ятайте: «думати/мріяти про» + Знахідний відмінок, а не Місцевий.

Родовий відмінок *(Genitive case)* також має свої особливі дієслова-тригери. Найчастіший і найважливіший тригер — це слово «немає» *(there is no)*. Після слова «немає» завжди стоїть Родовий відмінок і питання «кого? чого?». Наприклад: «На жаль, у мене зараз немає вільного часу» *(Unfortunately, I have no free time now)*. «У нас поки що немає великих грошей» *(We do not have big money yet)*.
Також Родовий відмінок потрібен після дієслів страху та сильної потреби. Це дієслова «боятися» *(to be afraid of)* та «потребувати» *(to need/require)*. Наприклад: «Маленька дитина дуже боїться великого сусідського собаки» *(A small child is very afraid of a big neighborhood dog)*. «Цей складний проєкт негайно потребує нашої професійної допомоги» *(This complex project urgently requires our professional help)*.

> — **Вчитель:** Добрий день, друзі! *(Good day, friends!)*
> — **Олена:** Добрий день! *(Good day!)*
> — **Вчитель:** Давайте сьогодні пограємо в справжніх граматичних детективів. *(Let's play true grammar detectives today.)* Я зараз читаю свіжу газету: «Президент зустрівся з новим прем'єром. Для журналістів підготували великий зал». *(I am reading a fresh newspaper now: "The president met with the new premier. A large hall was prepared for journalists".)* Який відмінок ми тут бачимо і чому? *(What case do we see here and why?)*
> — **Олена:** Слово «прем'єром» — це Орудний відмінок. *(The word "premier" is Instrumental case.)* Головний тригер тут — це прийменник «з». *(The main trigger here is the preposition "with".)*
> — **Вчитель:** Чудово! *(Excellent!)* А що з другим реченням? *(And what about the second sentence?)*
> — **Олена:** «Журналістів» — це Родовий відмінок після прийменника «для». *("Journalists" is Genitive case after the preposition "for".)* А «зал» — це Знахідний відмінок, бо дієслово «підготували» вимагає питання «що?». *(And "hall" is Accusative case, because the verb "prepared" requires the question "what?".)*
> — **Вчитель:** Чудово! *(Excellent!)* Ви дуже уважний детектив! *(You are a very attentive detective!)*

<!-- INJECT_ACTIVITY: quiz, Choose the correct case form based on the governing verb, 8 items -->

## Прийменник вирішує: Один прийменник — різні відмінки

Часто один прийменник може вимагати різних відмінків. Найвідоміший приклад — це прийменники «в/у» та «на». Вони працюють як перемикачі між напрямком та місцем. In English, you use "to" or "into" for direction and "in/at" for location. In Ukrainian, we use the same preposition, but we change the case. Якщо ми говоримо про напрямок, ми ставимо питання «куди?». У цьому випадку ми використовуємо Знахідний відмінок *(Accusative case)*. Наприклад: «Я йду на пошту» *(I am going to the post office)*. «Він швидко поклав телефон у чорну сумку» *(He quickly put a phone into a black bag)*. Це активна дія, яка має конкретну ціль. Але якщо ми говоримо про постійне місце, ми ставимо питання «де?». Тоді ми обов'язково використовуємо Місцевий відмінок *(Locative case)*. Порівняйте ситуацію: «Я зараз працюю на пошті» *(I am working at the post office now)*. «Його новий телефон лежить у чорній сумці» *(His new phone is lying in a black bag)*. Це статична позиція, де немає жодного руху. Запам'ятайте дуже просте і важливе правило: активний рух — це Знахідний відмінок, а статика — це Місцевий відмінок.

Ще один дуже цікавий прийменник — це «з». Цей короткий прийменник також має дві абсолютно різні функції. Перша функція — це рух із якогось місця назовні. У цьому значенні прийменник «з» завжди вимагає Родового відмінка *(Genitive case)*. Наприклад: «Моя сестра щойно приїхала з Одеси» *(My sister just arrived from Odesa)*. «Студент швидко вийшов з аудиторії» *(A student went quickly out of the classroom)*. Друга функція — це спільна дія. Тут прийменник «з» вимагає Орудного відмінка *(Instrumental case)*. Наприклад: «Він пішов у кіно з найкращим другом» *(He went to the cinema with a best friend)*. «Я щоранку люблю пити каву з теплим молоком» *(I like to drink coffee with warm milk every morning)*. Для кращого звучання ми часто використовуємо варіант «із» замість «з». Наприклад: «смачний хліб із маслом» *(tasty bread with butter)* або «довгий лист із Києва» *(a long letter from Kyiv)*.

Прийменник «за» також ефективно працює з двома відмінками: Знахідним та Орудним. Ми використовуємо Знахідний відмінок, коли говоримо про обмін, ціну або причину. Наприклад: «Я хочу сам заплатити за каву» *(I want to pay for a coffee myself)*. Дуже популярна фраза «дякую за» також завжди вимагає Знахідного відмінка. Ми часто кажемо: «Дякую вам за швидку допомогу» *(Thank you for the quick help)*. «Дякую за вашу чудову роботу» *(Thank you for your excellent work)*. Але якщо ми говоримо про фізичне місце позаду чогось, ми використовуємо Орудний відмінок. Наприклад: «Моя велика родина сидить за святковим столом» *(My large family is sitting at a festive table)*. «Маленький собака весело біжить за старим автобусом» *(A small dog is happily running after an old bus)*. Це завжди позиція позаду іншого об'єкта.

Окремо треба сказати про важливий прийменник «по». Він дуже часто використовується з Місцевим відмінком. Це означає рух по поверхні або всередині великого простору. In English, you might use "around", "along", or "across" for this concept. Наприклад, якщо ви гуляєте без конкретної цілі у центрі, ви скажете: «Я люблю гуляти по старому місту» *(I like to walk around an old city)*. Якщо спортсмен активно тренується, він каже: «Я щодня бігаю по великому стадіону» *(I run around a big stadium every day)*. Туристи часто кажуть таку фразу своїм друзям: «Ми дуже хочемо подорожувати по цілому світу» *(We really want to travel around the whole world)*. Прийменник «по» показує, що ваша дія вільно охоплює весь цей простір, а не лише одну пряму лінію.

<!-- INJECT_ACTIVITY: group-sort, Sort prepositions by which case(s) they govern (Acc., Gen., Instr., Loc.), 8 items -->

## Особливі випадки: Час, характеристика, шлях

Час — це дуже важливий елемент у нашій мові. Для днів тижня ми завжди використовуємо **Знахідний відмінок** *(Accusative case)* з прийменниками «у» або «в». Наприклад, ми кажемо: «Я працюю у середу» *(I work on Wednesday)* або «Ми відпочиваємо у п'ятницю» *(We rest on Friday)*. Зверніть увагу, що для днів тижня ми не використовуємо **Місцевий відмінок** *(Locative case)*. When you want to say "next" or "last" regarding a specific time period, you must use the Genitive case without any prepositions. Це дуже важливе правило. Ми кажемо: «**наступного тижня**» *(next week)*, «**минулого місяця**» *(last month)*, «**наступного року**» *(next year)*. Це **виняток** *(exception)*, який треба добре запам'ятати. If you talk about a specific year, you use the Locative case. Наприклад: «У дві тисячі чотирнадцятому році в Україні відбулася Революція Гідності» *(In 2014, the Revolution of Dignity took place in Ukraine)*. «Мій старший брат закінчив університет у минулому році» *(My older brother finished university last year)*. Отже, дні тижня — це Знахідний відмінок, а конкретні роки — Місцевий відмінок. Але зверніть увагу: фрази **без прийменника** зі словами «наступний» та «минулий» — це **Родовий відмінок** *(Genitive case)*: «наступного тижня», «минулого місяця». А фрази **з прийменником «у»** — це Місцевий відмінок: «у минулому році», «у наступному семестрі».

Тепер поговоримо про те, як ми описуємо людей та їхній одяг. Коли ми хочемо сказати, що людина носить певний одяг, ми використовуємо Місцевий відмінок з прийменником «у» або «в». This is a very common pattern for physical descriptions. Ми кажемо: «Ця красива жінка **у синій сукні** *(in a blue dress)* — моя старша сестра». «Той чоловік **у капелюсі** *(in a hat)* — мій новий сусід». «Маленький хлопець **у червоному светрі** *(in a red sweater)* дуже швидко біжить по вулиці». This pattern specifically describes the clothing that a person is wearing. Do not confuse this with describing where an object is located. Якщо ви кажете «на жінці» *(on the woman)*, це означає фізичну локацію на її тілі. Наприклад: «На жінці сидить маленький зелений жук» *(A small green bug is sitting on the woman)*. Але якщо ми описуємо стиль людини, ми завжди говоримо «у сукні», «**в окулярах**» *(in glasses)*, «**у пальті**» *(in a coat)*.

Місцевий відмінок також чудово працює, коли ми говоримо про абстрактний час. Sometimes we treat periods of life or states of being as if they are physical places. Ми кажемо: «**У дитинстві** *(In childhood)* я дуже любив грати на великій вулиці». «**У майбутньому** *(In the future)* я хочу стати хорошим лікарем». Це абстрактний простір, де відбувається дія. Також ми використовуємо Місцевий відмінок для опису абстрактного стану. Наприклад: «Моя мама зараз **у відпустці** *(on vacation)*». Ми також можемо сказати: «Вона зараз **у декреті**» *(She is on maternity leave right now)*. «Його батько довго був у дуже тривалому відрядженні» *(His father was on a very long business trip for a long time)*. Це означає, що людина перебуває у певному тривалому процесі.

Ми вже говорили про прийменник «по» і Місцевий відмінок. Але давайте розглянемо це важливе правило детальніше. Ця комбінація часто показує активний рух, який охоплює велику поверхню. This is the extended movement pattern. Ми використовуємо його зі специфічними дієсловами руху. Наприклад: «Маленький човен повільно **пливе по річці** *(is swimming along the river)*». «Великі білі птахи красиво **літають по небу** *(are flying across the sky)*». «Ми любимо влітку їздити по українських селах» *(We like to drive through Ukrainian villages in summer)*. This construction highlights the medium or the surface where the movement happens. Коли ми їдемо по дорозі, ми використовуємо весь простір цієї дороги *(When we drive on the road, we use the entire space of this road)*. Ви не просто йдете вперед, ви активно взаємодієте з усім простором. Тому ми часто кажемо: «Діти весело **бігають по кімнаті** *(are running around the room)*». «Ми довго гуляли по великому зимовому лісу» *(We walked around the large winter forest for a long time)*. Це показує велику свободу просторового руху.

<!-- INJECT_ACTIVITY: fill-in, Focus: Complete sentences with correct noun forms (mixed cases: time, clothing, path), 8 items -->

## Алгоритм вибору відмінка

Як швидко обрати правильний відмінок у реченні? Це дуже простий і логічний процес. The decision process for finding the correct case follows a strict order of priority. Ми використовуємо простий **алгоритм** *(algorithm)*, який має три кроки.

Крок перший: шукаємо прийменник. Prepositions always have the highest priority and completely overrule the verb. Якщо ви бачите прийменник, ви повинні обрати відмінок, який він вимагає. Наприклад, після слова «без» завжди йде Родовий відмінок. «Я п'ю каву без цукру».

Крок другий: якщо прийменника немає, ми дивимося на дієслово. Each specific verb commands a specific case for its direct or indirect object. Якщо ви бачите дієслово «допомагати», ви автоматично використовуєте Давальний відмінок. «Син допомагає мамі».

Крок третій: якщо ви досі не знаєте правильний відмінок, поставте граматичне питання. Ask the grammatical question to the noun to reveal its role in the sentence. Питання «Кого?» або «Що?» — це Знахідний відмінок. Питання «Кому?» або «Чому?» — це Давальний відмінок. Питання «Ким?» або «Чим?» — це Орудний відмінок.

| Крок | Дія | Результат |
|---|---|---|
| 1 | Є прийменник? | Прийменник обирає відмінок. |
| 2 | Немає прийменника? | Дієслово обирає відмінок. |
| 3 | Сумніваєтеся? | Поставте граматичне питання. |

Студенти часто роблять однакові граматичні помилки, коли вивчають відмінки. English speakers often map English prepositions directly to Ukrainian cases, which causes problems. Запам'ятайте, що англійська фраза «think about» українською звучить як «**думати про**» *(to think about)*. Після цього прийменника ми завжди використовуємо Знахідний відмінок, а не Місцевий. Ми кажемо: «Я часто думаю про тебе», а не «Я думаю про тобі».

Друга велика проблема — це дієслово «допомагати». English speakers want to use a direct object here because of the English translation. Але українське дієслово «допомагати» завжди вимагає Давального відмінка. Ми кажемо «Я допомагаю своєму брату», а не «Я допомагаю свого брата».

Також будьте обережні з прийменниками простору. Remember the difference between dynamic direction and static location. Коли ви активно йдете кудись, ви кажете: «Я йду в магазин». Це **напрямок** *(direction)* і Знахідний відмінок. Але коли ви вже там, ви кажете: «Я в магазині». Це статичне **місце** *(location)* і Місцевий відмінок.

*Студенти читають новий український текст на уроці граматики.*
> — **Марк:** Ірино, я не розумію одне речення. *(Iryna, I do not understand one sentence.)*
> — **Ірина:** Яке речення ти не розумієш, Марку? *(Which sentence do you not understand, Mark?)*
> — **Марк:** Чому тут написано «у понеділок»? *(Why is it written "on Monday" here?)*
> — **Ірина:** Це Знахідний відмінок, він показує час. *(This is the Accusative case, it shows time.)*
> — **Марк:** Але прийменник «у» — це Місцевий відмінок. *(But the preposition "у" is the Locative case.)*
> — **Ірина:** Ні, дні тижня ми завжди пишемо у Знахідному відмінку. *(No, we always write days of the week in the Accusative case.)*
> — **Марк:** Дякую, я тепер усе зрозумів. *(Thank you, I understood everything now.)*
> — **Ірина:** А ти пам'ятаєш фразу «цікавитися музикою»? *(And do you remember the phrase "to be interested in music"?)*
> — **Марк:** Так, дієслово «цікавитися» завжди вимагає Орудного відмінка. *(Yes, the verb "to be interested" always requires the Instrumental case.)*
> — **Ірина:** Правильно, ти дуже добре знаєш граматику. *(Correct, you know grammar very well.)*

<!-- INJECT_ACTIVITY: true-false, Focus: Judge whether the case used in a sentence is correct (includes tricky Acc/Loc pairs), 8 items -->

## Підсумок

Кожен український іменник має свого «боса» — це дієслово або прийменник. Every Ukrainian noun depends on a "boss" — either a verb or a preposition. Саме вони завжди вирішують, який відмінок ви повинні використовувати. Якщо ви бачите прийменник, він головний. The preposition always dictates the case. Наприклад, після прийменника «без» завжди стоїть Родовий відмінок. Якщо прийменника немає, ви дивитеся на дієслово. The verb determines the case of its object. Наприклад, дієслово «бачити» вимагає Знахідного відмінка, а дієслово «допомагати» — Давального відмінка. Якщо ви сумніваєтеся, просто поставте граматичне питання. The correct question will reveal the necessary case.

Перевірте себе та дайте відповіді на ці запитання:
1. Який відмінок ми вживаємо після дієслова «дякувати»? (Відповідь: Давальний відмінок).
2. Коли ми використовуємо прийменник «на» плюс Знахідний відмінок? (Відповідь: Коли це напрямок, і ми відповідаємо на питання «куди?»).
3. Як правильно сказати: «у понеділок» чи «в понеділку»? (Відповідь: «У понеділок» — це Знахідний відмінок для днів тижня).
4. Який відмінок ми використовуємо, коли описуємо одяг людини? (Відповідь: Місцевий відмінок із прийменником «у/в»).

**Deterministic word count: 2856 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 724 words | Not found: 8 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ірина — NOT IN VESUM
  ✗ Ірино — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Одеси — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ еві — NOT IN VESUM
  ✗ ові — NOT IN VESUM

All 724 other words are confirmed to exist in VESUM.

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
