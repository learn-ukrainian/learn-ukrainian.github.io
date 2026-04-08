<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/which-case-when.yaml` file for module **36: Компас відмінків** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-verb-case -->`
- `<!-- INJECT_ACTIVITY: group-sort-prepositions -->`
- `<!-- INJECT_ACTIVITY: fill-in-mixed-triggers -->`
- `<!-- INJECT_ACTIVITY: true-false-case-logic -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Given a sentence with a blank, choose the correct case form based on the
    governing verb or preposition
  items: 8
  type: quiz
- focus: Sort prepositions by which case(s) they govern (Acc., Gen., Instr., Loc.)
  items: 8
  type: group-sort
- focus: Complete sentences with the correct noun form — mixed cases triggered by
    different prepositions and verbs, including time expressions (у четвер), characteristics
    (у червоному светрі), and path (по кімнаті)
  items: 8
  type: fill-in
- focus: Judge whether the case used in a sentence is correct or incorrect, including
    tricky pairs like на роботу (Acc.) vs. на роботі (Loc.)
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- алгоритм (algorithm)
- контекст (context)
- керувати (to manage, drive)
- майбутнє (future)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
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

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: which-case-when
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

**Level: A2 (Module 36/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
