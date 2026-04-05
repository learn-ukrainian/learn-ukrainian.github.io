<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/plural-nominative-accusative.yaml` file for module **32: Багато людей, багато речей** (a2).

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

- `<!-- INJECT_ACTIVITY: nominative-plural-fill -->`
- `<!-- INJECT_ACTIVITY: accusative-animate-sort -->`
- `<!-- INJECT_ACTIVITY: accusative-plural-quiz -->`
- `<!-- INJECT_ACTIVITY: nominative-accusative-context -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the Nominative plural from given singular nouns across all declension
    classes
  items: 8
  type: fill-in
- focus: Sort plural nouns into animate vs. inanimate, then predict their Accusative
    form
  items: 8
  type: group-sort
- focus: Choose the correct Accusative plural form (animate = Gen.Pl., inanimate =
    Nom.Pl.) in sentences
  items: 8
  type: quiz
- focus: Find and fix wrong plural noun endings in Nominative and Accusative (e.g.,
    *дітей грають → діти грають, *бачу студенти → студентів)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- відміна (declension class)
- чергування (alternation)
- предмет (object, item)
- група (group)
required:
- множина (plural)
- називний відмінок (nominative case)
- знахідний відмінок (accusative case)
- живий (animate)
- неживий (inanimate)
- закінчення (ending (grammar))
- люди (people)
- діти (children)
- речі (things)
- очі (eyes)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ: Світ у множині

Ми бачимо **групи** *(groups)* людей, великі **колекції** *(collections)* речей та **натовпи** *(crowds)* на вулицях. In Ukrainian, forming the plural is about understanding the declension class of the noun. Кожне слово має свою **відміну** *(declension class)*. Masculine, feminine, and neuter words change differently when there is more than one.

> — **Батько:** Дивись, он там стоять **леви**! *(Look, lions [Nom.Pl] are standing over there!)*
> — **Дитина:** Вау! А я бачу маленьких **пінгвінів**! *(Wow! And I see small penguins [Acc.Pl]!)*
> — **Батько:** А ти бачиш тих високих **жирафів**? *(And do you see those tall giraffes [Acc.Pl]?)*
> — **Дитина:** Ні. Але там стрибають веселі **мавпи**! *(No. But fun monkeys [Nom.Pl] are jumping there!)*
> — **Батько:** Я зараз фотографую цих швидких мавп. *(I am photographing these fast monkeys [Acc.Pl] now.)*
> — **Дитина:** Я теж хочу сфотографувати **птахів**! *(I also want to photograph birds [Acc.Pl]!)*
> — **Батько:** Тоді йдемо туди, де кричать **папуги**. *(Then let's go where parrots [Nom.Pl] are screaming.)*

## Множина називного відмінка (Nominative Plural)

Перша відміна об'єднує слова жіночого та чоловічого роду, які закінчуються на «-а» або «-я». When forming the plural, we look at the final consonant before the ending. Якщо це твердий приголосний, ми використовуємо закінчення «-и». Наприклад, одна розумна **сестра** *(sister)* стає дві розумні **сестри** *(sisters)*. Моя **мама** *(mom)* має багато подруг, і вони теж **мами** *(moms)*. Ми читаємо свіжі **газети** *(newspapers)*. If the noun stem ends in a soft consonant, the plural ending changes to «-і». Наша **земля** *(land)* рідна, але інші **землі** *(lands)* також дуже красиві. Ми разом співаємо веселі **пісні** *(songs)*. Справедливий **суддя** *(judge)* працює чесно, але в суді працюють різні **судді** *(judges)*. Ці нові **статті** *(articles)* дуже довгі.

Друга відміна має багато слів чоловічого роду. Most of these masculine nouns end in a hard consonant and add the ending «-и» to form the plural. У кімнаті стоїть один круглий **стіл** *(table)*, а в ресторані стоять великі квадратні **столи** *(tables)*. Мій новий **телефон** *(phone)* лежить тут, а ваші старі **телефони** *(phones)* лежать там. У міському зоопарку сплять сильні **леви** *(lions)*. Masculine nouns that end in a soft consonant or a hushing consonant (ж, ч, ш, щ) take the ending «-і». Наш найкращий **вчитель** *(teacher)* пояснює нове правило. Інші досвідчені **вчителі** *(teachers)* уважно слухають його. Я маю гострий кухонний **ніж** *(knife)*, а головний кухар має професійні сталеві **ножі** *(knives)*. Восени часто йдуть холодні **дощі** *(rains)*. Ми дуже любимо теплі весняні дні.

Друга відміна також включає слова середнього роду. Neuter nouns with hard stems change their final «-о» to the ending «-а». Це велике сучасне **місто** *(city)* дуже красиве. Ми любимо відвідувати різні європейські **міста** *(cities)*. Я зараз відкриваю широке дерев'яне **вікно** *(window)*. Усі великі **вікна** *(windows)* у будинку завжди чисті. Моє рідне **село** *(village)* знаходиться дуже далеко. Інші сусідні **села** *(villages)* розташовані поруч. Neuter nouns with soft stems change their final «-е» або «-я» to «-я». Широке зелене **поле** *(field)* зеленіє весною. Ці великі жовті **поля** *(fields)* виглядають просто чудово. Глибоке синє **море** *(sea)* кличе нас. Усі південні **моря** *(seas)* світу прекрасні. Важливе **знання** *(knowledge)* допомагає жити. Наші глибокі **знання** *(knowledge)* зростають щодня.

When a noun stem ends in «-г», «-к», або «-х», these sounds can change before the plural ending. Найвідоміший приклад — це слово **друг** *(friend)*. Мій найкращий друг завжди з радістю допомагає мені. Але мої вірні старі **друзі** *(friends)* чекають на вулиці. The consonant «-г» changes directly to «-з», and the ending becomes «-і». Слово **козак** *(Cossack)* має звичайне закінчення «-и», але ми кажемо **козаки** *(Cossacks)* без зміни приголосного.

Третя відміна — це слова жіночого роду, які завжди закінчуються на приголосний. They almost always take the soft ending «-і». Темна та холодна **ніч** *(night)* часто лякає дітей. Але теплі літні **ночі** *(nights)* завжди дуже короткі. Біла морська **сіль** *(salt)* стоїть на кухонному столі. Різні мінеральні **солі** *(salts)* дуже корисні для здоров'я. Моя остання цікава **подорож** *(journey)* була надзвичайно довгою. Усі наші спільні **подорожі** *(journeys)* завжди дуже цікаві. Слово **мати** *(mother)* має унікальну форму. When we make it plural, we add the suffix «-ер-» before the final ending «-і». Моя мати працює чудовою вчителькою. Їхні добрі **матері** *(mothers)* працюють досвідченими лікарками.

Четверта відміна об'єднує слова середнього роду, які зазвичай означають маленьких істот. These specific words have a suffix «-ат-» або «-ят-» that appears only in the plural. Маленьке жовте **курча** *(chick)* швидко бігає по двору. Усі ці маленькі **курчата** *(chicks)* активно їдять свіже зерно. Мале молоде **теля** *(calf)* тихо стоїть біля своєї корови. Всі здорові **телята** *(calves)* на фермі швидко ростуть. Маленьке сіре **кошеня** *(kitten)* солодко спить на теплому дивані. Милі пухнасті **кошенята** *(kittens)* весело граються клубком. Мале веселе **дівча** *(girl)* голосно співає гарну пісню. Усі ці талановиті **дівчата** *(girls)* чудово танцюють разом.

Деякі дуже важливі слова мають унікальні форми. Ти — справді дуже добра **людина** *(person)*. На широкій вулиці зараз стоять різні незнайомі **люди** *(people)*. Моя маленька **дитина** *(child)* тихо грається в кімнаті. Наші старші розумні **діти** *(children)* вже самостійно ходять до школи. Моє праве **око** *(eye)* зараз бачить дуже добре. Її красиві сині **очі** *(eyes)* уважно дивляться на мене. Одне моє **вухо** *(ear)* раптом сильно болить. Мої здорові **вуха** *(ears)* добре чують цей звук. Ліве **плече** *(shoulder)* дуже втомилося сьогодні. Мої сильні **плечі** *(shoulders)* довго несуть важкий рюкзак.

<!-- INJECT_ACTIVITY: nominative-plural-fill -->

## Знахідний відмінок множини: Живе чи неживе? (Accusative Plural)

В однині правило знахідного відмінка працює по-різному для різних родів. Лише слова чоловічого роду мають спеціальну зміну для живих істот. У множині все залежить від того, чи це живий об'єкт, чи неживий предмет.

**Живий** *(animate)* об'єкт — це завжди людина або тварина. **Неживий** *(inanimate)* **предмет** *(object)* — це всі інші речі навколо нас.

For inanimate objects, the Accusative plural always looks exactly like the Nominative plural. 
Наші нові цікаві **книги** *(books)* спокійно лежать на полиці. Я зараз уважно читаю ці нові книги. Великі дерев'яні **столи** *(tables)* стоять у просторій кімнаті. Ми вчора купили ці нові великі столи. Її красиві **очі** *(eyes)* уважно дивляться на мене. Я часто згадую ці красиві очі. Наші старі теплі **речі** *(things)* лежать у шафі. Моя сестра зараз перевіряє ці старі речі. Широкі чисті **вікна** *(windows)* пропускають багато сонячного світла. Робітники зараз миють ці широкі вікна.

For any animate plural noun, the Accusative case borrows the form of the Genitive case. This usually means adding specific endings like "-ів" or "-ей", or dropping the final vowel entirely.
Мої розумні **студенти** *(students)* зараз уважно слухають лекцію. Я добре бачу моїх розумних **студентів** *(students)*. Мої старші **брати** *(brothers)* сьогодні працюють дуже багато. Ми ввечері обов'язково зустрінемо наших старших **братів** *(brothers)*. Наші рідні **сестри** *(sisters)* живуть у великому місті. Він дуже любить своїх рідних **сестер** *(sisters)*. Сусідські пухнасті **коти** *(cats)* голосно нявкають на вулиці. Маленька дівчинка хоче годувати цих пухнастих **котів** *(cats)*. Сірі швидкі **миші** *(mice)* бігають під старою підлогою. Чорний кіт зараз ловить цих швидких **мишей** *(mice)*. Мої вірні **друзі** *(friends)* завжди допомагають мені вдома. Я дуже поважаю моїх вірних **друзів** *(friends)*.

Незнайомі **люди** *(people)* швидко йдуть по центральній вулиці. Ми щодня бачимо цих незнайомих **людей** *(people)* у парку. Маленькі веселі **діти** *(children)* радісно граються на новому майданчику. Вчителька зараз уважно кличе цих маленьких **дітей** *(children)* до школи. Дорослі чоловіки та **жінки** *(women)* працюють на великій фабриці. Директор поважає цих працьовитих чоловіків та **жінок** *(women)*. Наші добрі **сусіди** *(neighbors)* часто влаштовують веселі вечірки. Ми завжди радо запрошуємо наших добрих **сусідів** *(neighbors)* у гості.

Маленькі жовті **курчата** *(chicks)* швидко бігають по зеленому двору. Фермер щоранку годує цих маленьких **курчат** *(chicks)* свіжим зерном. Молоді здорові **телята** *(calves)* тихо пасуться на широкому полі. Пастух уважно охороняє цих молодих **телят** *(calves)* від вовків. Милі сліпі **кошенята** *(kittens)* солодко сплять на м'якому килимі. Дівчинка дуже любить цих милих **кошенят** *(kittens)*. Малі веселі **дівчата** *(girls)* гарно співають народну пісню. Ми радо слухаємо цих талановитих **дівчат** *(girls)*.

Дієслово **бачити** *(to see)* дуже часто вимагає знахідного відмінка. Я зараз бачу високі гори та великих слонів. Дієслово **знати** *(to know)* допомагає нам описувати наш досвід. Я добре знаю ці нові правила та цих розумних авторів. Ми завжди **любимо** *(love)* наші улюблені старі фільми. Але ми також щиро любимо наших вірних собак. Туристи дуже люблять **зустрічати** *(to meet)* нових цікавих людей. Ми зараз активно **шукаємо** *(look for)* наші загублені теплі рукавиці. Вона довго шукає своїх зниклих котів.

<!-- INJECT_ACTIVITY: accusative-animate-sort -->
<!-- INJECT_ACTIVITY: accusative-plural-quiz -->

## Називний чи знахідний? Визначаємо за контекстом

Inanimate plural nouns look exactly the same in the Nominative and Accusative cases. The context of the sentence tells you whether the noun is the active subject or the passive direct object. If the noun is actively performing the main action, it is the subject, and it must be in the Nominative case. If the noun is passively receiving the action of a verb, it is the direct object of the sentence. This specific role requires the Accusative case.

Широкі **вулиці** *(streets)* старого міста сьогодні дуже гарні та чисті. У цьому першому реченні слово «вулиці» є підметом, тому ми використовуємо називний відмінок. Туристи та місцеві жителі дуже люблять ці тихі **вулиці**. Тут ми відразу бачимо знахідний відмінок, бо «вулиці» безпосередньо приймають дію. Великі світлі **вікна** *(windows)* дають нашій кімнаті багато теплого світла. Ми часто миємо ці великі світлі **вікна** вранці. Старі красиві **картини** *(paintings)* гордо висять на білій стіні музею. Туристи довго фотографують ці відомі **картини**. Нові сучасні **магазини** *(shops)* працюють у центрі міста кожного дня. Наші друзі часто відвідують ці великі **магазини** після роботи. 

Because animate plural nouns change their form in the Accusative case, you instantly know their exact role in the sentence. You hear the "-ів" or "-ей" ending and immediately understand that this specific group of people or animals is receiving the action. Молоді **студенти** *(students)* зараз уважно слухають дуже цікаву лекцію. Професор добре бачить усіх цих нових **студентів** в аудиторії. У першому реченні студенти самі активно виконують дію. Це класичний називний відмінок. У другому реченні дія викладача прямо спрямована на них. Це знахідний відмінок. Маленькі веселі **собаки** *(dogs)* дуже швидко бігають по великому парку. Малі діти радісно годують цих веселих **собак** біля дерева. 

> — **Олена:** Ми вже купили свіжі **фрукти** *(fruits)* і дуже смачні **овочі** *(vegetables)* для салату.
> — **Андрій:** Так, я вже поклав ці **фрукти** на кухонний стіл. Наші зелені **овочі** справді дуже свіжі та красиві.
> — **Олена:** Хто саме сьогодні ввечері прийде до нас у гості?
> — **Андрій:** Прийдуть наші нові **колеги** *(colleagues)* по роботі та старі університетські **друзі** *(friends)*.
> — **Олена:** Ти добре знаєш усіх цих нових **колег**?
> — **Андрій:** Звісно, я знаю цих **колег** уже майже два роки. Ми працюємо разом.
> — **Олена:** А я дуже хочу нарешті побачити твоїх шкільних **друзів**.
> — **Андрій:** Вони теж радісно чекають на цю цікаву зустріч із тобою.
> — **Олена:** Тоді я швидко приготую холодні солодкі **напої** *(drinks)* для всіх.
> — **Андрій:** А я зараз принесу чисті скляні **келихи** *(glasses)* з нашої кухні.

We frequently use the short prepositions **на** *(onto/to)* and **у/в** *(into/to)* for direction or continuous motion towards a specific destination. У теплу неділю ми разом йдемо в зелені міські **парки** *(parks)*. Пізно ввечері ми довго дивимось на далекі яскраві **зорі** *(stars)*. Малі діти радісно біжать у широкі безпечні **двори** *(yards)*. Another important preposition is **про** *(about)*. It always requires the Accusative case when you talk, think, or write about a specific topic. Ми зараз серйозно розмовляємо про наші великі майбутні **плани** *(plans)*. Відомі журналісти часто пишуть цікаві статті про видатних **людей** *(people)*. Наші студенти сьогодні читають новий текст про українських **письменників** *(writers)*. 

Теплі ранкові сонячні **промені** *(rays)* м'яко падають на велику площу. Швидкі сірі **птахи** *(birds)* високо літають над новими будинками. Ми з радістю бачимо цих вільних **птахів** у синьому небі. Різні заклопотані **люди** *(people)* швидко поспішають у своїх щоденних справах. Вони купують красиві **квіти** *(flowers)* та гарячу смачну каву. Ми добре чуємо гучні сучасні **автомобілі** *(cars)* на широкій дорозі. Ці нові **автомобілі** завжди їдуть дуже швидко. Маленькі веселі **діти** *(children)* безтурботно граються біля прохолодного міського фонтану. Їхні батьки пильно охороняють своїх маленьких **дітей**. Зелені високі **дерева** *(trees)* дають нам приємну тінь. Ми справді дуже любимо ці старі могутні **дерева**.

<!-- INJECT_ACTIVITY: nominative-accusative-context -->

## Підсумок

Основні закінчення множини:
*   **Називний відмінок:** **-и**, **-і**, **-а**, **-я**.
*   **Знахідний відмінок (неживі):** форма називного відмінка.
*   **Знахідний відмінок (живі):** **-ів**, **-їв**, **-ей**, або **-∅** *(zero ending)*.

> — **Запитання:** Як утворити називний відмінок множини для слова «місто»?
> — **Відповідь:** Форма множини — «міста».
> — **Запитання:** Яке закінчення має слово «брат» у знахідному відмінку множини?
> — **Відповідь:** Це жива істота, тому закінчення **-ів**: «братів».
> — **Запитання:** Чи змінюється форма слова «книги», якщо це додаток *(object)*?
> — **Відповідь:** Ні, бо це неживий предмет. Форма залишається «книги».
> — **Запитання:** Як правильно сказати "I see children"?
> — **Відповідь:** Ми говоримо: «Я бачу дітей».

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: plural-nominative-accusative
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

**Level: A2 (Module 32/60) — ELEMENTARY**

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

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
