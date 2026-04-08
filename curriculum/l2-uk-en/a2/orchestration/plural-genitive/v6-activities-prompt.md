<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/plural-genitive.yaml` file for module **33: Скільки?** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-genitive-i -->`
- `<!-- INJECT_ACTIVITY: match-up-singular-plural -->`
- `<!-- INJECT_ACTIVITY: quiz-quantity-agreement -->`
- `<!-- INJECT_ACTIVITY: true-false-genitive-errors -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the Genitive plural from given nouns (mixed відміни), inserting fleeting
    vowels where needed
  items: 8
  type: fill-in
- focus: Choose the correct Gen.Pl. form in quantity expressions (багато ___, п'ять
    ___)
  items: 8
  type: quiz
- focus: Match singular nouns with their correct Genitive plural forms
  items: 8
  type: match-up
- focus: Judge whether a given Gen.Pl. form is correct or incorrect (common errors
    like книгів instead of книг)
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- вставний голосний (fleeting vowel)
- виняток (exception)
- десяток (a dozen, ten-unit)
required:
- родовий відмінок (genitive case)
- нульове закінчення (zero ending)
- кількість (quantity, amount)
- багато (a lot, many)
- мало (few, little)
- кілька (a few, several)
- декілька (a few, several)
- скільки (how many, how much)
- гроші (money)
- гривня (hryvnia)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чому родовий множини такий складний?

**Родовий відмінок множини** (Genitive Plural) is the heavyweight of Ukrainian noun cases. 
The question **«Скільки?»** (How many?) almost always requires this grammatical case. 
Коли ви запитуєте про кількість, ви найчастіше використовуєте саме цю форму. 
Це найпоширеніший граматичний відмінок для опису великої кількості предметів або людей. 
While other plural cases are predictable, the Genitive Plural is famous for its variety. 
У цій граматичній темі справді немає одного простого правила для всіх слів. 
You must choose between three major patterns: a **нульове закінчення** (zero ending), the endings **-ів** or **-їв**, and the ending **-ей**. 
Крім того, цей відмінок дуже часто змінює звуки всередині самого слова. 
Часто голосні звуки змінюються з «о» на «і», або з «е» на «і». 
Іноді нові голосні звуки можуть раптом з'являтися всередині слова між приголосними. 
This combination of different endings and internal sound changes makes it challenging. 
Але без цього відмінка ви не зможете вільно говорити про гроші, час або покупки.

Why is this specific case so functionally important in daily life? 
В українській мові ми використовуємо родовий відмінок множини абсолютно кожного дня. 
Він суворо необхідний після всіх чисел від п'яти до двадцяти. 
Ви також використовуєте цю форму після круглих чисел, таких як тридцять, сорок і п'ятдесят. 
You also need it after words that express indefinite quantity, such as **багато** (many), **мало** (few), and **кілька** (several). 
В англійській мові форма слова майже ніколи не змінюється після цифр. 
Там ви просто додаєте стандартне закінчення множини до нового слова. 
Але українською мовою ми кажемо «одна книга», проте завжди кажемо «п'ять книг». 
Слово повністю змінює свою форму, щоб показати велику кількість предметів.

One of the biggest challenges here is the consonant cluster problem. 
Багато іменників жіночого та середнього роду мають нульове закінчення в родовому відмінку множини. 
When you remove the final vowel to create this zero ending, you leave a difficult cluster of consonants. 
Наприклад, якщо ми заберемо останню літеру у слові «сестра», ми отримаємо складне закінчення «-стр». 
To make these words easier to pronounce, the language uses **вставні голосні** (inserted vowels). 
Ми просто додаємо звуки «о» або «е» між останніми приголосними у слові. 
Тому ми кажемо не «п'ять сестр», а мелодійне «п'ять сестер». 
Так само ми кажемо «багато книжок» замість неможливого варіанту «багато книжк». 
Ця маленька фонетична зміна робить українську мову дуже зручною для розмови.

How can you master this complex grammar without feeling completely overwhelmed? 
The best strategy is to break the rules down by **відміна** (declension) and noun gender. 
У цьому модулі ми будемо вивчати родовий відмінок множини крок за кроком. 
Ми побачимо, що більшість іменників чоловічого роду мають один стабільний шлях. 
Для іменників чоловічого роду ми найчастіше використовуємо стандартне закінчення **-ів**. 
У той же час, більшість іменників жіночого та середнього роду йдуть зовсім іншим шляхом. 
Вони дуже часто використовують нульове закінчення, іноді з додаванням вставних голосних. 
By categorizing vocabulary into these broad patterns, you can confidently guess the correct form. 
Ви швидко почнете автоматично відчувати правильну граматичну форму для кожного нового слова.


## I відміна: нульове закінчення

**Перша відміна** (The first declension) includes most feminine nouns ending in **-а** or **-я**. 
Коли ми говоримо про велику кількість цих предметів, ми використовуємо **нульове закінчення** (zero ending). 
Що це означає на практиці? 
We simply drop the final vowel, and the word ends in a consonant. 
Це дуже просте правило для слів із твердою основою. 
Подивіться на ці типові приклади:
* Одна **книга** (book) — багато **книг** (books).
* Одна **машина** (car) — п'ять **машин** (cars).
* Одна **газета** (newspaper) — десять **газет** (newspapers).
* Одна **країна** (country) — кілька **країн** (countries).
* Одна **родина** (family) — багато **родин** (families).

Однак, українська фонетика має свої особливості. 
When the final syllable contains the vowel "о", it often changes to "і" when the syllable becomes closed (ending in a consonant). 
Ви вже знаєте це правило чергування голосних з інших відмінків.
* Одна **дорога** (road) — немає **доріг** (roads).
* Одна **корова** (cow) — багато **корів** (cows).
* Одна **особа** (person) — п'ять **осіб** (persons).
* Одна **школа** (school) — багато **шкіл** (schools).
Це чергування робить вимову набагато мелодійнішою та природнішою для української мови.

Але що робити, коли перед останнім голосним стоять два приголосні звуки? 
If we just drop the final "-а" or "-я", we are left with a difficult consonant cluster at the end of the word. 
Українська мова не любить таких складних комбінацій приголосних. 
To solve this pronunciation problem, the language uses **вставні голосні** (fleeting vowels). 
Найчастіше це голосні звуки "о" або "е". 
Ми просто вставляємо цей новий голосний звук між двома останніми приголосними. 
We usually insert "-о-" after hard consonants, especially when the word ends in "-ка". 
Це дуже поширена ситуація, тому що українська мова має багато слів із суфіксом "-к".
* Одна **книжка** (book) — багато **книжок** (books).
* Одна **картка** (card) — п'ять **карток** (cards).
* Одна **казка** (fairy tale) — десять **казок** (fairy tales).
* Одна **думка** (thought) — багато **думок** (thoughts).

We insert "-е-" after soft consonants or shibilants (ж, ч, ш).
* Одна **земля** (earth, land) — багато **земель** (lands).
* Одна **вишня** (cherry) — п'ять **вишень** (cherries).
* Одна **пісня** (song) — кілька **пісень** (songs).
Ці вставні голосні роблять слова легкими та приємними для вимови.

Тепер давайте уважно подивимося на слова, які закінчуються на "-я". 
If the "-я" comes immediately after another vowel, the zero ending takes the form of the consonant "-й". 
Це дуже логічне правило, адже літера "я" позначає звуки "й" та "а" після іншого голосного.
* Одна **мрія** (dream) — багато **мрій** (dreams).
* Одна **надія** (hope) — немає **надій** (hopes).
* Одна **подія** (event) — кілька **подій** (events).

What happens if the noun ends in "-ня" or "-ля"? 
Якщо перед цим закінченням є ще один приголосний, ми використовуємо вставний звук "е". 
Але ми також повинні додати м'який знак у кінці слова.
* Одна **їдальня** (dining room) — кілька **їдалень** (dining rooms).
* Одна **спальня** (bedroom) — п'ять **спалень** (bedrooms).
* Одна **читальня** (reading room) — багато **читалень** (reading rooms).
М'який знак тут виконує важливу роботу. 
Він показує, що попередній приголосний звук залишається м'яким, незважаючи на зникнення літери "я".

Звісно, кожне правило має свої винятки, які потрібно знати. 
Some high-frequency feminine nouns of the first declension take the ending **-ей** instead of a zero ending. 
Вони зберегли цю стару форму з історичних причин.
* Одна **стаття** (article) — багато **статей** (articles).
* Одна **сім'я** (family) — п'ять **сімей** (families).
* Одна **миша** (mouse) — кілька **мишей** (mice).
* Одна **свиня** (pig) — багато **свиней** (pigs).

You will also encounter masculine nouns in the first declension. 
Це слова чоловічого роду, які закінчуються на "-а" або "-я". 
Деякі з них отримують типове чоловіче закінчення **-ів** замість очікуваного нульового закінчення.
* Один **суддя** (judge) — багато **суддів** (judges).
* Один **тесля** (carpenter) — кілька **теслів** (carpenters).
* Один **староста** (headman, monitor) — п'ять **старостів** (monitors).
Ці слова є своєрідними "історичними вижившими" (historical survivors). 
Вам потрібно просто запам'ятати ці особливі форми родового відмінка множини. 
Вони дуже часто зустрічаються у щоденному спілкуванні.

<!-- INJECT_ACTIVITY: fill-in-genitive-i -->


## II відміна: -ів, нульове, -ей

Друга відміна має три різні закінчення для родового відмінка множини. Найпопулярніше закінчення — це **-ів**. Це закінчення мають майже всі іменники чоловічого роду з твердою основою. In the Nominative singular, these masculine nouns have a zero ending. They end in a hard consonant. Якщо вам потрібно вгадати форму родового відмінка множини, закінчення «-ів» є найбезпечнішим варіантом. If you must guess the Genitive plural for a masculine noun, «-ів» is your safest bet. Це дуже продуктивне закінчення, яке українська мова використовує найчастіше. 

Один **студент** *(student)* — багато **студентів** *(students)*.
Один **долар** *(dollar)* — сто **доларів** *(dollars)*.
Один **метр** *(meter)* — п'ять **метрів** *(meters)*.
Один **день** *(day)* — десять **днів** *(days)*. Тут ми бачимо, що голосний «е» зникає, але закінчення залишається стандартним.
Один **комп'ютер** *(computer)* — кілька **комп'ютерів** *(computers)*.
Один **стіл** *(table)* — багато **столів** *(tables)*. Пам'ятайте про чергування «і» та «о».

Ви будете чути це закінчення щодня. У магазині, на вулиці, на роботі люди постійно говорять про кількість предметів чоловічого роду. Якщо ви сумніваєтеся, яке закінчення вибрати, сміливо додавайте «-ів». Ймовірність вашої помилки буде дуже малою.

Іменники чоловічого роду з м'якою або мішаною основою також часто мають закінчення «-ів». Якщо слово закінчується на голосний та «й» (наприклад, «-ай» або «-ей»), ми використовуємо закінчення **-їв**. Це те саме закінчення, але після голосного.

Один **музей** *(museum)* — багато **музеїв** *(museums)*.
Один **герой** *(hero)* — кілька **героїв** *(heroes)*.
Один **учень** *(student, pupil)* — п'ять **учнів** *(pupils)*. Основа тут м'яка, але ми все одно додаємо «-ів».

Але є невелика, проте надзвичайно важлива група слів чоловічого роду з м'якою основою. Вони мають зовсім інше закінчення — **-ей**. These words often denote people or animals, and they are extremely frequent in everyday speech. You must memorize these specific words because they do not follow the standard «-ів» pattern.

Один **гість** *(guest)* — багато **гостей** *(guests)*.
Один **кінь** *(horse)* — п'ять **коней** *(horses)*.

Слово **соловей** *(nightingale)* є цікавим винятком. Воно належить до м'якої групи, але має форму **солов'їв** *(nightingales)*. Слово **гроші** *(money)* існує тільки у множині. Воно також відмінюється за цією логікою і має форму **грошей** *(money)*. Використовуйте ці особливі слова обережно, щоб ваша українська звучала максимально природно.

Тепер поговоримо про середній рід. Іменники середнього роду, які закінчуються на «-о», поводяться дуже цікаво. У родовому відмінку множини вони мають нульове закінчення. Вони просто втрачають свою останню літеру «о». This makes them behave very much like feminine nouns of the first declension.

Одне **місто** *(city)* — багато **міст** *(cities)*.
Одне **яблуко** *(apple)* — кілограм **яблук** *(apples)*.

Але дуже часто, коли ми відкидаємо «о», в кінці слова залишаються два приголосні звуки. As you already know, the Ukrainian language strongly avoids difficult consonant clusters at the end of words. Therefore, these neuter nouns often gain a fleeting vowel («о» or «е») or undergo a vowel change.

Одне **слово** *(word)* — багато **слів** *(words)*. Тут ми бачимо класичне чергування «о» та «і» у закритому складі.
Одне **село** *(village)* — п'ять **сіл** *(villages)*.
Одне **вікно** *(window)* — кілька **вікон** *(windows)*. Ми додали вставний голосний «о», щоб слово було легше вимовляти.

Ця проста логіка допомагає нам говорити плавно та мелодійно. Вам не потрібно запам'ятовувати кожне слово середнього роду окремо. Simply apply the zero ending rule and check if a fleeting vowel is needed for pronunciation.

Іменники середнього роду також можуть закінчуватися на літери «-е» або «-я». Це зазвичай слова з м'якою або мішаною основою. Слова, які закінчуються на «-е», найчастіше отримують типове чоловіче закінчення «-ів».

Одне **море** *(sea)* — багато **морів** *(seas)*.
Одне **поле** *(field)* — багато **полів** *(fields)*. (Існує також рідкісна старовинна форма **піль** *(fields)*, але сьогодні всі кажуть «полів»).

Те саме стосується слів на «-я» без подвоєння: одне **подвір'я** *(yard)* — кілька **подвір'їв** *(yards)*.

А тепер подивіться на слова, які закінчуються на «-я» та мають подвоєння приголосних перед ним. Це велика група слів, яка зазвичай позначає процеси, завдання або абстрактні поняття. In the Genitive plural, these nouns take a zero ending. Because the ending disappears, the double consonant is reduced to a single consonant. We then add a soft sign to keep the final sound soft.

Одне **завдання** *(task)* — десять **завдань** *(tasks)*.
Одне **знання** *(knowledge)* — багато **знань** *(knowledge)*.
Одне **обличчя** *(face)* — кілька **облич** *(faces)*. Зверніть увагу: після шиплячого звука «ч» м'який знак не потрібен.

Це правило працює абсолютно завжди. Якщо ви бачите подвоєння приголосних та «-я» в кінці слова, сміливо відкидайте одну приголосну і ставте нульове закінчення.

Нарешті, ми маємо звернути пильну увагу на специфічну групу іменників чоловічого роду. Це слова, які позначають національність, громадянство або соціальний статус людини. В однині вони завжди закінчуються на суфікс **-ин**.

Один **киянин** *(Kyivan)*.
Один **громадянин** *(citizen)*.
Один **селянин** *(villager)*.

These nouns are a very common point of confusion for learners. Many students expect to simply add «-ів» and say «киянинів» or «громадянинів». This is completely incorrect. У множині цей суфікс «-ин» безслідно зникає. Тому в родовому відмінку множини ці слова мають нульове закінчення.

Багато **киян** *(Kyivans)*.
Мільйони **громадян** *(citizens)*.
Кілька **селян** *(villagers)*.

Цю втрату суфікса дуже легко зрозуміти і запам'ятати. Зверніть увагу на те, як ці слова звучать у називному відмінку множини. Ми говоримо «кияни» або «громадяни». Суфікс «-ин» існує тільки в однині. Тому в родовому відмінку множини його також не може бути.

<!-- INJECT_ACTIVITY: match-up-singular-plural -->


## Скільки чого? Кількість у житті (~550 words total)

Тепер ми знаємо форми слів. Але коли саме ми їх використовуємо? Найчастіше ми використовуємо родовий відмінок множини, коли рахуємо предмети або людей. В українській мові є дуже важливе правило для чисел. Ми часто називаємо його «правилом п'яти». Після числа п'ять, шість, сім, десять, двадцять і так далі ми завжди використовуємо родовий відмінок множини. Також ми обов'язково використовуємо цей відмінок після слів, які позначають невизначену кількість. Це такі популярні слова, як **багато** *(many/a lot)*, **мало** *(few/a little)*, **кілька** *(a few)*, **декілька** *(several)* та питальне слово **скільки** *(how many)*. The grammar of quantity essentially treats these numerical words as containers that hold an amount of something. For example, you say **багато друзів** *(many friends)*, **мало часу** *(little time - singular)*, **кілька хвилин** *(a few minutes)*, або **скільки гривень?** *(how many hryvnias?)*. The Genitive case logically answers the question "how much OF what?".

Дуже важливо чітко розуміти різницю між числами. В українській граматиці ми маємо дві різні системи для рахування. Числа два, три і чотири працюють зовсім інакше, ніж числа від п'яти і далі. Після чисел два, три і чотири ми завжди використовуємо називний відмінок множини. Наприклад, ми кажемо: **три студенти** *(three students)* або **чотири книги** *(four books)*. Але після п'яти ми обов'язково використовуємо родовий відмінок множини: **п'ять студентів** *(five students)*, **шість книг** *(six books)*. This strict distinction is a major marker of natural, authentic Ukrainian speech. In some other Slavic languages, such as Russian, the numbers two, three, and four take the Genitive singular case. Ukrainian grammar is entirely different and has its own deep historical logic. We proudly say **два столи** *(two tables)*, not *два стола*. We say **три брати** *(three brothers)*, not *три брата*. Remembering and applying this fundamental contrast helps you sound truly Ukrainian.

Давайте подивимося, як це правило працює в реальному житті. Уявіть велику шкільну їдальню. Працівники рахують посуд після обіду.
> — **Завідувач:** Давай перевіримо посуд. Скільки у нас чистих **тарілок** *(plates)*?
> — **Помічник:** Я вже порахував. У нас є тільки двадцять тарілок.
> — **Завідувач:** Це погано. А скільки чистих **виделок** *(forks)* ти знайшов?
> — **Помічник:** Тільки п'ятнадцять виделок. Вони ще миються.
> — **Завідувач:** Це дуже мало для обіду. А скільки **ложок** *(spoons)* у нас є?
> — **Помічник:** Ложок зараз багато. Я нарахував рівно сорок штук.
> — **Завідувач:** Добре. А що у нас сьогодні зі склянками?
> — **Помічник:** Я маю погані новини. У нас зовсім немає чистих **склянок** *(glasses)*!
> — **Завідувач:** Ох, нам негайно треба знайти більше склянок! І також нам треба купити кілька нових **чашок** *(cups)*.

Тепер інша типова ситуація в супермаркеті. Ми купуємо продукти для великої вечірки з друзями.
> — **Покупець:** Добрий день! Дайте мені, будь ласка, п'ять **кілограмів** *(kilograms)* червоних яблук.
> — **Продавець:** Добрий день! Ось ваші яблука. Бажаєте щось ще?
> — **Покупець:** Так, дайте ще кілька **десятків** *(dozens)* яєць. Скільки це все коштує?
> — **Продавець:** Ваша покупка коштує рівно двісті **гривень** *(hryvnias)*.
> — **Покупець:** Ой, у мене в гаманці є тільки кілька **сотень** *(hundreds)* готівкою. Я не маю дрібних **грошей** *(money)*. Можна заплатити банківською карткою?
> — **Продавець:** Так, звичайно. У нас немає з цим жодних **проблем** *(problems)*. У нас працює багато **терміналів** *(terminals)*. Прикладайте картку сюди.

А тепер послухайте цікаву розповідь екскурсовода під час прогулянки про старе історичне місто.
> — **Екскурсовод:** Подивіться на цю старовинну будівлю. У цьому будинку багато **вікон** *(windows)*, але мало **дверей** *(doors)* відкриті для туристів.
> — **Турист:** Дуже цікаво. А скільки **людей** *(people)* живе тут сьогодні?
> — **Екскурсовод:** Зараз у цьому районі живе кілька **тисяч** *(thousands)* місцевих жителів. А раніше тут жили сотні багатих **родин** *(families)*.
> — **Турист:** Я бачу, що тут гуляє багато **туристів** *(tourists)*.
> — **Екскурсовод:** Так, це правда. Щороку наше місто приймає сотні тисяч іноземних **гостей** *(guests)* з різних **країн** *(countries)*. Це приносить місту багато грошей.

<!-- INJECT_ACTIVITY: quiz-quantity-agreement -->
<!-- INJECT_ACTIVITY: true-false-genitive-errors -->


## Підсумок

Ми вивчили найскладніший відмінок в українській мові. Родовий відмінок множини має три головні групи закінчень.

Перша група — це закінчення **-ів** або **-їв** *(-iv / -yiv)*. Ми використовуємо його для більшості чоловічого роду, наприклад, **студентів** *(of students)*. Також воно є у деяких словах середнього роду, як-от **морів** *(of seas)*.

Друга група — це **нульове закінчення** *(zero ending)*. Воно працює для більшості слів жіночого роду, наприклад, **книг** *(of books)*. Також для середнього роду на -о, наприклад, **вікон** *(of windows)*. Пам'ятайте про вставні голосні **-о-** або **-е-**! Вони дуже часто з'являються тут.

Третя група — це закінчення **-ей** *(-ey)*. Ми додаємо його до слів жіночого роду третьої відміни, як-от **ночей** *(of nights)*. Також воно є у м'яких словах чоловічого роду, наприклад, **гостей** *(of guests)*. Воно також є у винятках, як **статей** *(of articles)*.

Тепер перевірте себе *(Now check yourself)*:

- Яке закінчення зазвичай мають слова середнього роду на -о? *(What ending do neuter nouns in -о usually take?)* Відповідь: нульове закінчення.
- Що відбувається зі словом **сестра** *(sister)* у родовому відмінку множини? *(What happens to the word 'сестра' in Genitive Plural?)* Відповідь: воно стає **сестер** *(of sisters)* через **вставний голосний** *(fleeting vowel)*.
- Який відмінок ми використовуємо після слова **багато** *(a lot)*? *(Which case do we use after 'багато'?)* Відповідь: родовий відмінок множини *(Genitive Plural)*.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: plural-genitive
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

**Level: A2 (Module 33/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-sounds-letters [§4.1.1, §4.1.4]
**Звуки і літери** (Sounds and letters)
- **quiz** — Звук чи літера?: Розрізнити звук і літеру — основа української фонетики / Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Оберіть правильну відповідь*
- **match-up** — Літера → Звук: Зіставити літери зі звуковими значеннями, особливо багатозвучні (я, ю, є, ї) / Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *З'єднайте літеру зі звуком*
- **group-sort** — Голосні й приголосні: Розподілити звуки на голосні та приголосні / Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: Побачити зображення, визначити українську літеру / See image, identify the Ukrainian letter it starts with
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні знання
- ❌ fill-in-no-options: Занадто складно для A1 — початківці потребують варіантів відповідей

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
