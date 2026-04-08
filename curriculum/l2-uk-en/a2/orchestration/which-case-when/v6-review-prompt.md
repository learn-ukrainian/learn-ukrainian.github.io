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
## Вступ: Граматичний детектив

> — **Вчитель:** Привіт! *(Hi!)* Сьогодні ми — граматичні детективи. *(Today we are grammar detectives.)* Ми шукаємо **відмінки** *(cases)* у текстах. *(We are looking for cases in texts.)*
> — **Анна:** Що ми читаємо сьогодні? *(What are we reading today?)*
> — **Вчитель:** Українську газету: «Президент зустрівся з прем'єром. Для журналістів підготували зал». *(A Ukrainian newspaper: "The President met with the Prime minister. They prepared a hall for the journalists".)* Де тут відмінки? *(Where are the cases here?)*
> — **Анна:** Слово «Президент» *(The word "President")* — це **Називний відмінок** *(Nominative case)*. Він виконує дію. *(He performs the action.)*
> — **Вчитель:** Точно! *(Exactly!)* А фраза «з прем'єром»? *(And the phrase "with the prime minister"?)*
> — **Марко:** Тут є **прийменник** *(preposition)* «з». *(Here is the preposition "with".)* Це **Орудний відмінок** *(Instrumental case)*. Питання «з ким?». *(The question "with whom?".)*
> — **Вчитель:** Дуже добре. *(Very good.)* А друге речення: «Для журналістів підготували зал»? *(And the second sentence: "They prepared a hall for the journalists"?)*
> — **Анна:** Прийменник «для» вимагає певної форми. *(The preposition "for" requires a specific form.)* Це **Родовий відмінок** *(Genitive case)*.
> — **Марко:** А слово «зал» *(And the word "hall")* — це **Знахідний відмінок** *(Accusative case)*. Дія спрямована на нього. *(The action is directed at it.)*
> — **Вчитель:** Блискуче! *(Brilliant!)* Ви розпізнали чотири різні відмінки. *(You recognized four different cases.)*

Як обрати правильний відмінок? *(How to choose the right case?)* Cases in Ukrainian are never random. Вони мають чітку логіку. *(They have a clear logic.)* Уявіть, що у вас є **компас відмінків** *(case compass)*. Цей компас показує правильний шлях. *(This compass shows the right way.)*

In Ukrainian grammar, specific words act as anchors that govern the case of the noun. Перший якір — це **дієслово** *(verb)*. *(The first anchor is the verb.)* Verbs dictate which case must follow them to complete the meaning. Наприклад, дієслово «бачити» вимагає Знахідного відмінка. *(For example, the verb "to see" requires the Accusative case.)* 

Другий якір — це прийменник. *(The second anchor is the preposition.)* Prepositions are strongly linked to specific cases. Прийменник «для» завжди вимагає Родового відмінка. *(The preposition "for" always requires the Genitive case.)* 

When you identify the governing verb or preposition, you easily determine the correct noun ending. У цьому модулі ми вивчимо простий **алгоритм** *(algorithm)*. *(In this module we will learn a simple algorithm.)* Ви завжди будете знати правильну форму. *(You will always know the correct form.)*

## Дієслово вирішує: Який відмінок після дієслова?

Уявіть, що дієслово — це магніт. *(Imagine that a verb is a magnet.)* Some verbs strongly attract the **Знахідний відмінок** *(Accusative case)*. Це дієслова, які мають прямий об'єкт. *(These verbs have a direct object.)* Найпопулярніші дієслова тут: **бачити** *(to see)*, **знати** *(to know)*, **любити** *(to love)* та **купити** *(to buy)*. 
Наприклад: «Я **бачу друга** *(I see a friend)*» або «Ми **знаємо правду** *(We know the truth)*». Коли ви кажете: «Я **люблю Україну** *(I love Ukraine)*», ви використовуєте Знахідний відмінок. Те саме стосується фрази: «Я **куплю квиток** *(I will buy a ticket)*».

Інша група дієслів вимагає **Давального відмінка** *(Dative case)*. Ці дієслова показують отримувача дії. *(These verbs show the recipient of the action.)* They focus on the person who receives help or information. Сюди належать: **допомагати** *(to help)*, **телефонувати** *(to call)*, **дякувати** *(to thank)* та **радити** *(to advise)*. 
Ми кажемо: «Я **допомагаю мамі** *(I help mom)*» або «Він **телефонує сестрі** *(He calls his sister)*». Якщо ми вдячні, ми кажемо: «Ми **дякуємо вчителю** *(We thank the teacher)*». А якщо даємо пораду: «Я **раджу другу** *(I advise a friend)*».

Третій якір — це дієслова, які дружать з **Орудним відмінком** *(Instrumental case)*. These verbs describe what we use as a tool, or what occupies our interest. Запам'ятайте ці слова: **користуватися** *(to use)*, **цікавитися** *(to be interested in)* та **займатися** *(to practice / to do)*. 
Наприклад: «Я **користуюсь комп'ютером** *(I use a computer)*» або «Вона **користується ручкою** *(She uses a pen)*». Коли ми говоримо про хобі, ми кажемо: «Я **цікавлюся мовою** *(I am interested in the language)*». Або: «Брат **займається спортом** *(The brother practices sports)*».

Тепер поговоримо про **Родовий відмінок** *(Genitive case)*. This case connects to concepts of absence or fear. Найголовніше слово тут — **немає** *(there is no)*. Після нього завжди стоїть Родовий відмінок: «У мене **немає часу** *(I have no time)*». 
Також сюди належать дієслова **боятися** *(to be afraid)* та **потребувати** *(to need)*. Ми кажемо: «Він **боїться вовка** *(He is afraid of a wolf)*». Якщо вам потрібна підтримка, ви скажете: «Я **потребую допомоги** *(I need help)*».

Нарешті, є цікава деталь із дієсловами думки. *(Finally, there is an interesting detail with verbs of thought.)* In English, you use "about", which feels like a context. But in Ukrainian, the preposition **про** *(about)* strongly governs the Accusative case. 
Найчастіше це дієслова **думати** *(to think)* та **мріяти** *(to dream)*. Ми кажемо: «Я **думаю про майбутнє** *(I think about the future)*». Або так: «Вона **мріє про подорож** *(She dreams about a trip)*». Your thoughts go directly to the object.

<!-- INJECT_ACTIVITY: quiz-verb-case -->

## Прийменник вирішує: Один прийменник — різні відмінки

Часто прийменник працює як перемикач. *(Often a preposition works like a switch.)* One preposition can require different cases depending on the meaning of the sentence. Найпопулярніші прийменники — це **на** *(on/to)* та **у/в** *(in/into)*. Вони дружать із двома відмінками: Знахідним та Місцевим. *(They are friends with two cases: Accusative and Locative.)* 

The choice depends on movement versus position. Якщо ми говоримо про напрямок руху, ми запитуємо «Куди?». *(If we talk about the direction of movement, we ask "Where to?".)* This is the Accusative case. Наприклад: «Я йду **на роботу** *(I am going to work)*» або «Діти йдуть **в школу** *(The children are going to school)*». Ми рухаємося до мети. *(We are moving towards a goal.)* Але якщо ми говоримо про статичне місце, ми запитуємо «Де?». *(But if we talk about a static place, we ask "Where?".)* This requires the Locative case. Наприклад: «Я працюю **на роботі** *(I work at work)*» або «Діти сидять **у школі** *(The children sit in school)*». Дія відбувається в одному місці. *(The action happens in one place.)*

Прийменник **з/із** *(from/with)* також має два різні значення. *(The preposition "з/із" also has two different meanings.)* Коли він означає походження або старт руху, нам потрібен Родовий відмінок. *(When it means origin or start of movement, we need the Genitive case.)* Наприклад: «Я приїхав **з Києва** *(I arrived from Kyiv)*» або «Він вийшов **із дому** *(He went out of the house)*». But when "з/із" means companionship or combination, it takes the Instrumental case. Це означає «разом». *(It means "together".)* Наприклад: «Я пішов гуляти **з другом** *(I went for a walk with a friend)*». Або коли ми п'ємо напій: «Я люблю каву **з молоком** *(I like coffee with milk)*».

Ще один цікавий прийменник — це **за** *(for/behind)*. *(Another interesting preposition is "за".)* We use it with the Accusative case to show exchange, price, or gratitude. Наприклад: «Я плачу **за квиток** *(I pay for the ticket)*» або «Ми дякуємо **за допомогу** *(We thank for the help)*». However, when "за" indicates a physical location behind or after something, we use the Instrumental case. Наприклад: «Ми сидимо **за столом** *(We are sitting at the table)*». Або якщо ми наздоганяємо транспорт: «Він біжить **за автобусом** *(He is running after the bus)*».

Прийменник **по** *(along/around)* найчастіше працює з Місцевим відмінком. *(The preposition "по" most often works with the Locative case.)* It describes movement along a path or across a surface. Наприклад: «Ми любимо ходити **по вулиці** *(We like to walk along the street)*». Якщо ми вдома: «Кіт бігає **по кімнаті** *(The cat runs around the room)*». Або масштабно: «Ми подорожуємо **по Україні** *(We travel around Ukraine)*».

Інші популярні прийменники зазвичай мають лише один відмінок. *(Other popular prepositions usually have only one case.)* Прийменник **для** *(for)* вказує на мету і вимагає Родового відмінка: «Це подарунок **для мами** *(This is a gift for mom)*». Прийменник **біля** *(near)* також любить Родовий відмінок: «Я стою **біля вікна** *(I stand near the window)*». Прийменник **до** *(to/towards)* показує фінальну точку маршруту: «Ми їдемо **до лісу** *(We are driving to the forest)*».

<!-- INJECT_ACTIVITY: group-sort-prepositions -->

## Особливі випадки: Час, характеристика, шлях

Іноді відмінки працюють як спеціальні коди для часу. *(Sometimes cases work like special codes for time.)* Коли ми говоримо про дні тижня, ми завжди використовуємо прийменник **у/в** та Знахідний відмінок. *(When we talk about days of the week, we always use the preposition "у/в" and the Accusative case.)* Наприклад: «Я працюю **у вівторок** *(I work on Tuesday)*» або «Ми відпочиваємо **у п'ятницю** *(We rest on Friday)*». We also use the Accusative case to say "this week" or "this year" without a preposition. Наприклад: «**Цю неділю** я сиджу вдома *(This Sunday I sit at home)*». Але якщо ми говоримо про минулий або майбутній час, правило змінюється. *(But if we talk about past or future time, the rule changes.)* To say "next week" or "last month", we use the Genitive case without a preposition. Наприклад: «Я поїду туди **наступного тижня** *(I will go there next week)*» або «Це було **минулого місяця** *(It was last month)*».

Місцевий відмінок допомагає нам говорити про роки та описувати людей. *(The Locative case helps us talk about years and describe people.)* Коли ми називаємо рік, ми використовуємо прийменник **у/в** та слово «рік» у Місцевому відмінку. *(When we name a year, we use the preposition "у/в" and the word "year" in the Locative case.)* Наприклад: «Він народився **у 2024 році** *(He was born in 2024)*» або «Це сталося **у минулому році** *(It happened last year)*». We also use "у/в" plus Locative to describe what someone is wearing or what they look like. Це дуже корисна конструкція для опису зовнішності та одягу. *(This is a very useful construction for describing appearance and clothes.)* Наприклад: «Хто цей **хлопець у синьому светрі**? *(Who is this boy in a blue sweater?)*». Або: «Там стоїть **дівчина в окулярах** *(A girl in glasses is standing there)*». The clothing or accessory must always be in the Locative case.

Рух у просторі також має свої спеціальні прийменники. *(Movement in space also has its special prepositions.)* Коли ми рухаємося по поверхні або гуляємо без конкретної мети, ми використовуємо прийменник **по** та Місцевий відмінок. *(When we move across a surface or walk without a specific goal, we use the preposition "по" and the Locative case.)* Це означає тривалий рух всередині певної зони. *(This means prolonged movement inside a certain area.)* Наприклад: «Ми дуже любимо **гуляти по парку** *(We really like to walk around the park)*» або «Діти весело **бігають по кімнаті** *(The children happily run around the room)*». Але якщо нам треба перетнути щось від одного краю до іншого, ми беремо прийменник **через** *(across/through)* та Знахідний відмінок. *(But if we need to cross something from one edge to another, we take the preposition "через" and the Accusative case.)* Наприклад: «Нам треба обережно **перейти через дорогу** *(We need to carefully cross the road)*» або «Ми зараз їдемо **через ліс** *(We are driving through the forest now)*».

Знахідний відмінок має ще кілька цікавих секретів для спілкування. *(The Accusative case has a few more interesting secrets for communication.)* Коли ми обговорюємо якусь тему, ми використовуємо прийменник **про** *(about)*. *(When we discuss some topic, we use the preposition "про".)* Цей прийменник завжди вимагає Знахідного відмінка. *(This preposition always requires the Accusative case.)* Наприклад: «Ми часто **говоримо про політику** *(We often talk about politics)*» або «Вона постійно **думає про майбутнє** *(She constantly thinks about the future)*». Another advanced use of the Accusative case is with the preposition "за" to show how long an action takes to complete. Це означає результативність дії. *(This means the result orientation of an action.)* Наприклад: «Я можу **зробити це за годину** *(I can do this in an hour)*» або «Він **прочитав книгу за день** *(He read the book in a day)*». Це гарний спосіб показати швидкість нашої роботи. *(This is a good way to show the speed of our work.)*

<!-- INJECT_ACTIVITY: fill-in-mixed-triggers -->

## Алгоритм вибору відмінка (~400 слів)

Як обрати потрібний відмінок? *(How to choose the needed case?)* Запам'ятайте простий алгоритм із трьох кроків. *(Remember a simple three-step algorithm.)* Крок перший: шукаємо прийменник. *(Step one: we look for a preposition.)* Прийменник — це найсильніший сигнал. *(A preposition is the strongest signal.)* Якщо він є, ми використовуємо відмінок, який він вимагає. *(If it is there, we use the case it requires.)* Наприклад, після слова **без** *(without)* завжди йде Родовий відмінок. *(For example, after the word "без" always goes the Genitive case.)* Крок другий: якщо прийменника немає, дивимося на дієслово. *(Step two: if there is no preposition, we look at the verb.)* Кожне дієслово має свої правила. *(Each verb has its own rules.)* Наприклад, слово **допомагати** *(to help)* вимагає Давального відмінка. *(For example, the word "допомагати" requires the Dative case.)* Крок третій: перевіряємо себе питанням. *(Step three: we check ourselves with a question.)* Якщо ми сумніваємося, ставимо питання до слова: кого? що? кому? чим? *(If we doubt, we ask a question to the word: whom? what? to whom? with what?)* Це надійний тест. *(This is a reliable test.)*

Англомовні студенти часто роблять кілька типових помилок. *(English-speaking students often make a few typical mistakes.)* Головна проблема — це прямий переклад прийменників. *(The main problem is the direct translation of prepositions.)* Ніколи не перекладайте слова "for" та "with" буквально! *(Never translate words "for" and "with" literally!)* Завжди дивіться на контекст речення. *(Always look at the context of the sentence.)* Часта помилка стосується дієслова **допомагати** *(to help)*. *(A frequent mistake concerns the verb "допомагати".)* В англійській мові ми кажемо "with the help of", тому студенти використовують Родовий відмінок. *(In English we say "with the help of", so students use the Genitive case.)* Але українською ми кажемо: «Я **допомагаю мамі** *(I am helping mom)*». Це Давальний відмінок. *(This is the Dative case.)* Також пам'ятайте про різницю між напрямком та місцем. *(Also remember about the difference between direction and place.)* Порівняйте: «Я іду **на роботу** *(I am going to work)*». Це напрямок, тому беремо Знахідний відмінок. *(This is a direction, so we take the Accusative case.)* Але: «Я сиджу **на роботі** *(I am sitting at work)*». Це місце, тому потрібен Місцевий відмінок. *(This is a place, so the Locative case is needed.)*

Давайте розглянемо алгоритм на практиці. *(Let's look at the algorithm in practice.)* Проаналізуємо таке речення: «Я **дякую другу** за подарунок у коробці». *(Let's analyze such a sentence: "I thank a friend for a gift in a box".)* Чому слово **друг** *(friend)* стоїть у Давальному відмінку? *(Why is the word "друг" in the Dative case?)* Тому що дієслово **дякувати** *(to thank)* вимагає Давального відмінка. *(Because the verb "дякувати" requires the Dative case.)* Далі йде слово **подарунок** *(gift)*. *(Next goes the word "подарунок".)* Перед ним стоїть прийменник **за** *(for)*. *(Before it stands the preposition "за".)* Це подяка, тому використовуємо Знахідний відмінок. *(This is gratitude, so we use the Accusative case.)* Нарешті, бачимо слово **коробка** *(box)*. *(Finally, we see the word "коробка".)* Перед ним є прийменник **у** *(in)*, який вказує на місце. *(Before it there is a preposition "у", which indicates a place.)* Тому ми ставимо це слово у Місцевий відмінок: **у коробці** *(in a box)*. *(That's why we put this word in the Locative case: "у коробці".)* Цей аналіз допоможе вам говорити правильно. *(This analysis will help you speak correctly.)*

<!-- INJECT_ACTIVITY: true-false-case-logic -->

## Підсумок

Ми вивчили багато нових правил. *(We learned many new rules.)* Вибір відмінка — це логічний процес. *(Choosing a case is a logical process.)* Спочатку ми шукаємо прийменник. *(First, we look for a preposition.)* Якщо його немає, ми дивимося на дієслово. *(If there is none, we look at the verb.)* Перевірте ваші знання за допомогою цих запитань. *(Check your knowledge with these questions.)*

Як відрізнити **напрямок** *(direction)* від **місця** *(place)* з прийменником **на** *(on/to)*? *(How to distinguish direction from place with the preposition "на"?)* Якщо це напрямок, ми використовуємо Знахідний відмінок. *(If it is a direction, we use the Accusative case.)* Ми питаємо: куди? *(We ask: where to?)* Наприклад: «Я йду на роботу». *(For example: "I am going to work".)* Якщо це місце, ми обираємо Місцевий відмінок. *(If it is a place, we choose the Locative case.)* Ми питаємо: де? *(We ask: where?)* Наприклад: «Я сиджу на роботі». *(For example: "I am sitting at work".)*

Який відмінок ми використовуємо для днів тижня? *(Which case do we use for days of the week?)* Для цього потрібен Знахідний відмінок. *(For this, the Accusative case is needed.)* Наприклад: «Ми зустрінемося **у понеділок** *(on Monday)*». *(For example: "We will meet on Monday".)*

Яке питання ми ставимо після дієслова **допомагати** *(to help)*? *(What question do we ask after the verb "допомагати"?)* Ми завжди питаємо: кому? *(We always ask: to whom?)* Тому це дієслово вимагає Давального відмінка. *(That's why this verb requires the Dative case.)* Наприклад: «Я допомагаю другу». *(For example: "I am helping a friend".)*

Як описати одяг людини за допомогою відмінків? *(How to describe a person's clothes using cases?)* Для цього ми використовуємо прийменник **у** *(in)* та Місцевий відмінок. *(For this we use the preposition "у" and the Locative case.)* Ми кажемо: «Дівчина **у червоній сукні** *(in a red dress)*». *(We say: "A girl in a red dress".)*

Українська граматика дуже логічна. *(Ukrainian grammar is very logical.)* Використовуйте цей компас відмінків кожного дня. *(Use this compass of cases every day.)* З часом ви будете обирати правильну форму автоматично. *(Over time you will choose the correct form automatically.)*
</generated_module_content>

**PIPELINE NOTE — Word count: 2870 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 517 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Києва — NOT IN VESUM

All 517 other words are confirmed to exist in VESUM.

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
