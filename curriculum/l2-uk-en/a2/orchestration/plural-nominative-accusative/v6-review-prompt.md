<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 32: Багато людей, багато речей (A2, A2.5 [Case Synthesis and Plurals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-032
level: A2
sequence: 32
slug: plural-nominative-accusative
version: '1.0'
title: Багато людей, багато речей
subtitle: Множина називного та знахідного відмінків для всіх відмін
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
  - Learner can form the Nominative plural for nouns of all four declension 
    classes (I-IV відміна).
  - Learner can form the Accusative plural, applying the animate/inanimate 
    distinction correctly (animate = Genitive plural form, inanimate = 
    Nominative plural form).
  - Learner can identify when a plural noun is in Nominative vs. Accusative by 
    its syntactic role (subject vs. direct object).
  - Learner can produce correct plural Nom/Acc forms in short sentences 
    describing groups of people and collections of objects.
dialogue_situations:
  - setting: 'At a zoo — identifying animals and their groups: Дивись — леви (m, lions)!
      Бачиш тих жирафів (m, giraffes)? А ось мавпи (f, monkeys)! Діти люблять пінгвінів
      (m, penguins).'
    speakers:
      - Батько/Мати
      - Діти
    motivation: 'Nom plural: лев→леви. Acc animate plural: жираф→жирафів, пінгвін→пінгвінів'
content_outline:
  - section: 'Множина називного відмінка (Nominative Plural)'
    words: 650
    points:
      - 'I відміна (feminine/masculine -а/-я): сестра → сестри, земля → землі, суддя
        → судді. Hard stems: -и; soft stems: -і.'
      - 'II відміна (masculine consonant, neuter -о/-е/-я): стіл → столи, місто →
        міста, поле → поля, море → моря. Consonant alternations: друг → друзі, рік
        → роки.'
      - 'III відміна (feminine consonant): ніч → ночі, сіль → солі, мати → матері.'
      - 'IV відміна (neuter -а/-ят-): курча → курчата, теля → телята.'
      - 'Common irregulars: людина → люди, дитина → діти, око → очі, вухо → вуха.'
  - section: 'Знахідний відмінок множини: Живе чи неживе? (Accusative Plural: Animate
      vs. Inanimate)'
    words: 650
    points:
      - 'The key rule: inanimate Acc.Pl. = Nom.Pl. (Я бачу столи, книги, міста). Animate
        Acc.Pl. = Gen.Pl. (Я бачу братів, сестер, дітей).'
      - 'How this differs from singular: masculine singular already has this split
        (бачу стіл vs. бачу брата), but in plural ALL genders follow it.'
      - 'Practice with mixed animate/inanimate: Я бачу студентів і підручники. Ми
        зустріли друзів і знайшли ключі.'
      - 'Verbs that take Accusative: бачити, знати, любити, зустрічати, шукати — practice
        forming correct plural objects.'
  - section: 'Називний чи знахідний? Визначаємо за контекстом (Nominative or Accusative?
      Reading the Context)'
    words: 700
    points:
      - 'Subject test: Who/what does the action? = Nominative. Студенти читають (Nom).
        Я бачу студентів (Acc).'
      - 'Inanimate nouns look identical in Nom/Acc plural — only syntax tells them
        apart: Книги лежать на столі (Nom) vs. Я купив книги (Acc).'
      - 'Practice: short paragraphs where learner identifies Nom vs. Acc plural by
        role in sentence. Dialogues about shopping, meeting friends, describing groups.'
      - 'Integration: combine with prepositions that take Accusative (через, на (direction),
        у/в (direction), про) to reinforce recognition.'
vocabulary_hints:
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
  recommended:
    - відміна (declension class)
    - чергування (alternation)
    - предмет (object, item)
    - група (group)
activity_hints:
  - type: fill-in
    focus: Form the Nominative plural from given singular nouns across all 
      declension classes
    items: 8
  - type: group-sort
    focus: Sort plural nouns into animate vs. inanimate, then predict their 
      Accusative form
    items: 8
  - type: quiz
    focus: Choose the correct Accusative plural form (animate = Gen.Pl., 
      inanimate = Nom.Pl.) in sentences
    items: 8
  - type: error-correction
    focus: Find and fix wrong plural noun endings in Nominative and Accusative 
      (e.g., *дітей грають → діти грають, *бачу студенти → студентів)
    items: 6
references:
  - title: Заболотний Grade 6, §§59-61
    notes: Nominative and Accusative plural formation, animate/inanimate 
      distinction
  - title: Літвінова Grade 6, с. 157-162
    notes: Plural declension tables for all відміни with exercises

</plan_content>

## Generated Content

<generated_module_content>
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

Друга відміна також включає слова середнього роду. Neuter nouns with hard stems change their final «-о» to the ending «-а». Це велике сучасне **місто** *(city)* дуже красиве. Ми любимо відвідувати різні європейські **міста** *(cities)*. Я зараз відкриваю широке дерев'яне **вікно** *(window)*. Усі великі **вікна** *(windows)* у будинку завжди чисті. Моє рідне **село** *(village)* знаходиться дуже далеко. Інші сусідні **села** *(villages)* розташовані поруч. Neuter nouns with soft stems change their final «-е» або «-я» to «-я». Широке зелене **поле** *(field)* зеленіє весною. Ці великі жовті **поля** *(fields)* виглядають просто чудово. Глибоке синє **море** *(sea)* кличе нас. Усі південні **моря** *(seas)* світу прекрасні. Маленьке червоне **серце** *(heart)* б'ється швидко. Наші вдячні **серця** *(hearts)* завжди пам'ятають рідних.

When a noun stem ends in «-г», «-к», або «-х», these sounds can change before the plural ending. Найвідоміший приклад — це слово **друг** *(friend)*. Мій найкращий друг завжди з радістю допомагає мені. Але мої вірні давні **друзі** *(friends)* чекають на вулиці. The consonant «-г» changes directly to «-з», and the ending becomes «-і». Цілий **рік** *(year)* ми працюємо, а потім згадуємо минулі **роки** *(years)*. Тут голосний у корені змінюється: рік → роки. Слово **козак** *(Cossack)* має звичайне закінчення «-и», але ми кажемо **козаки** *(Cossacks)* без зміни приголосного.

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
> — **Андрій:** Прийдуть наші нові **колеги** *(colleagues)* по роботі та давні університетські **друзі** *(friends)*.
> — **Олена:** Ти добре знаєш усіх цих нових **колег**?
> — **Андрій:** Звісно, я знаю цих **колег** уже майже два роки. Ми працюємо разом.
> — **Олена:** А я дуже хочу нарешті побачити твоїх шкільних **друзів**.
> — **Андрій:** Вони теж радісно чекають на цю цікаву зустріч із тобою.
> — **Олена:** Тоді я швидко приготую холодні солодкі **напої** *(drinks)* для всіх.
> — **Андрій:** А я зараз принесу чисті скляні **келихи** *(glasses)* з нашої кухні.

We frequently use the short prepositions **на** *(onto/to)* and **у/в** *(into/to)* for direction or continuous motion towards a specific destination. У теплу неділю ми разом йдемо в зелені міські **парки** *(parks)*. Пізно ввечері ми довго дивимось на далекі яскраві **зорі** *(stars)*. Малі діти радісно біжать у широкі безпечні **двори** *(yards)*. An important preposition is **через** *(through, because of)*. It always requires the Accusative case. Ми йдемо **через** широкі зелені **поля** *(fields)*. Він не прийшов **через** важливі робочі **справи** *(matters)*. Another important preposition is **про** *(about)*. It always requires the Accusative case when you talk, think, or write about a specific topic. Ми зараз серйозно розмовляємо про наші великі майбутні **плани** *(plans)*. Відомі журналісти часто пишуть цікаві статті про видатних **людей** *(people)*. Наші студенти сьогодні читають новий текст про українських **письменників** *(writers)*. 

Теплі ранкові сонячні **промені** *(rays)* м'яко падають на велику площу. Швидкі сірі **птахи** *(birds)* високо літають над новими будинками. Ми з радістю бачимо цих вільних **птахів** у синьому небі. Різні заклопотані **люди** *(people)* швидко поспішають у своїх щоденних справах. Вони купують красиві **квіти** *(flowers)* та гарячу смачну каву. Ми добре чуємо гучні сучасні **автомобілі** *(cars)* на широкій дорозі. Ці нові **автомобілі** завжди їдуть дуже швидко. Маленькі веселі **діти** *(children)* безтурботно граються біля прохолодного міського фонтану. Їхні батьки пильно охороняють своїх маленьких **дітей**. Зелені високі **дерева** *(trees)* дають нам приємну тінь. Ми справді дуже любимо ці старі могутні **дерева**.

<!-- INJECT_ACTIVITY: error-correction-plural-endings -->

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

**Deterministic word count: 2155 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 750 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрій — NOT IN VESUM
  ✗ Олена — NOT IN VESUM

All 750 other words are confirmed to exist in VESUM.

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
