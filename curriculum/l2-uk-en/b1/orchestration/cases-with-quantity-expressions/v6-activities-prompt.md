<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/cases-with-quantity-expressions.yaml` file for module **62: Кількісні вирази** (b1).

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

- `<!-- INJECT_ACTIVITY: reading-numeral-agreement -->`
- `<!-- INJECT_ACTIVITY: error-correction-error-correction-declension -->`
- `<!-- INJECT_ACTIVITY: match-up-collective-usage -->`
- `<!-- INJECT_ACTIVITY: quiz-fraction-agreement -->`
- `<!-- INJECT_ACTIVITY: fill-in-indefinite-quantity -->`
- `<!-- INJECT_ACTIVITY: essay-response-contextual-quantity -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Прочитайте текст про узгодження кількісних числівників з іменниками і дайте
    відповіді на запитання.
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «Відмінювання кількісних
    числівників».
  type: essay-response
- focus: Вставте правильну граматичну форму у реченнях на тему узгодження кількісних
    числівників з іменниками.
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему відмінювання кількісних числівників.
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Узгодження кількісних
    числівників з іменниками».'
  type: quiz
- focus: З'єднайте терміни з розділу «Відмінювання кількісних числівників» з їхніми
    визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- тисяча (thousand — governs Р.в.мн.)
- мільйон (million — governs Р.в.мн.)
- половина (half — + Р.в.)
- чверть (quarter — + Р.в.)
- забагато (too much — governs Р.в.)
- замало (too little — governs Р.в.)
required:
- кількісний числівник (cardinal numeral — один, два, сто)
- збірний числівник (collective numeral — двоє, троє, четверо)
- узгодження (agreement — matching numeral with noun form)
- неозначено-кількісний (indefinite-quantitative — багато, кілька)
- кілька (several — governs Р.в.)
- декілька (several — synonym of кілька)
- чимало (quite a lot — governs Р.в.)
- достатньо (enough — governs Р.в.)
- понад (more than — governs Зн.в.)
- близько (about/approximately — governs Р.в.)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ та діалог: Сільський перепис

У повсякденному житті ми постійно щось рахуємо: від кількості людей у країні під час перепису населення до грамів борошна в рецепті улюбленого пирога. Точність має значення, але в українській мові важливо не лише правильно назвати число. Найбільша складність полягає в тому, як це число впливає на форму слова, що стоїть після нього. Кількісні вирази вимагають особливої уваги до закінчень іменників, адже правила узгодження тут відрізняються від багатьох інших мов. Від того, чи скажете ви «один», «два» чи «п'ять», повністю залежатиме відмінок наступного слова.

> *In everyday life, we are constantly counting things: from the number of people in a country during a census to the grams of flour in a recipe for our favorite pie. Accuracy matters, but in Ukrainian, it's important not only to name the number correctly. The biggest difficulty lies in how this number affects the form of the word that follows it. Quantity expressions require special attention to noun endings, because the rules of agreement here differ from many other languages. Depending on whether you say "one", "two", or "five", the case of the following word will change completely.*

:::note
**Пам’ятайте!** В українській мові числа керують іменниками. Вони змушують слова змінювати свою форму, часто перетворюючи називний відмінок на родовий залежно від конкретної кількості чи об'єму.
:::

Прочитайте розмову між працівником перепису населення та господарем великого сільського двору. Зверніть увагу на те, як змінюються слова після різних чисел та слів, що позначають кількість.

> *Read the conversation between a census worker and the owner of a large village yard. Pay attention to how words change after different numbers and words denoting quantity.*

> — **Переписувач:** Доброго дня! Я проводжу сільський перепис. Скільки людей живе у вашому домі? *(Good day! I am conducting a village census. How many people live in your house?)*
> — **Господар:** Доброго здоров'я. Разом нас п'ятеро: я, дружина, двоє дітей та моя мати. *(Good health. Altogether there are five of us: me, my wife, two children, and my mother.)*
> — **Переписувач:** Зрозуміло. А який розмір вашого господарства? Маєте багато землі? *(I see. And what is the size of your household? Do you have a lot of land?)*
> — **Господар:** Так, маємо п'ятдесят гектарів поля. Чимало зусиль витрачаємо на щоденну роботу. *(Yes, we have fifty hectares of field. We spend quite a lot of effort on daily work.)*
> — **Переписувач:** А будинок великий? Скільки тут приміщень? *(And is the house big? How many rooms are here?)*
> — **Господар:** У нас кілька кімнат: три спальні, одна велика вітальня та дві кухні — літня і зимова. *(We have several rooms: three bedrooms, one large living room, and two kitchens — summer and winter.)*
> — **Переписувач:** Добре. А тварин тримаєте? *(Good. And do you keep animals?)*
> — **Господар:** Мало худоби залишилося. Тільки дві корови, четверо поросят та десяток курей. *(Few livestock remain. Only two cows, four piglets, and ten chickens.)*

## 1. Узгодження кількісних числівників з іменниками

Українська мова має чіткі правила узгодження числівників з іменниками. Найпростіше правило стосується числівника «один». Він поводиться як звичайний прикметник і повністю узгоджується з іменником у роді, числі та відмінку. Ми використовуємо форми «один» для чоловічого роду, «одна» для жіночого та «одне» для середнього: один стіл, одна книжка, одне вікно. Це правило працює і для складених чисел. Тому ми кажемо «двадцять один студент», зберігаючи іменник в однині.

Числівники «два», «три» та «чотири» вимагають після себе іменника у формі називного відмінка множини. Це ключове правило, яке відрізняє українську граматику від сусідніх мов. Ми кажемо: два студенти, три сценарії, чотири подруги. Зверніть увагу на числівник «два», який має окрему форму для жіночого роду — «дві». Тому правильно говорити «дві книжки», але ніколи не «два книжки». Для чоловічого та середнього роду використовується форма «два».

Чому ми кажемо «два студенти», а не «два студента»? Це історичний спадок давньоруської двоїни. Колись існувала окрема граматична категорія для двох предметів, яка пізніше злилася з множиною. Конструкція з родовим відмінком однини («два студента») є запозиченням з російської граматики і вважається помилкою в українській мові.

> *Why do we say «два студенти» and not «два студента»? This is a historical legacy of the Old East Slavic dual number. Once, there was a separate grammatical category for two objects, which later merged with the plural. The construction using the Genitive singular («два студента») is a borrowing from Russian grammar and is considered a mistake in Ukrainian.*

:::info
**Граматичне правило**
Після числівників «два», «три», «чотири» іменники стоять у формі **називного відмінка множини**. Ніколи не використовуйте родовий відмінок однини з цими числами.
:::

У цьому правилі є два винятки. Перший стосується іменників із суфіксом «-ин-», який зникає у множині (киянин, селянин). З числівниками «два», «три», «чотири» такі слова ставляться у родовому відмінку однини: два киянина, три селянина. Другий виняток — це іменники четвертої відміни, що позначають малих істот (порося) або абстрактні поняття (ім'я). Вони також вимагають родового відмінка однини: два поросяти, три імені.

Для числівників від п'яти до двадцяти, тридцяти та всіх круглих десятків діє інша закономірність. Вони вимагають після себе іменника у формі родового відмінка множини. Отже, якщо предметів п'ять або більше, ми використовуємо родовий відмінок: п'ять озер, десять метрів, сто книжок.

У складених числівниках (наприклад, 25 або 42) форму іменника завжди визначає останнє слово. Якщо число закінчується на один, іменник буде в однині: сорок один студент. Якщо на два, три або чотири — у називному відмінку множини: сорок два студенти. А якщо закінчується на п'ять і більше — у родовому відмінку множини: сорок п'ять студентів.

<!-- INJECT_ACTIVITY: reading-numeral-agreement -->

## 2. Відмінювання кількісних числівників

Declining cardinal numerals is a fundamental skill for reaching fluency in Ukrainian. Unlike English, where numbers never change form, Ukrainian numerals must agree with their surrounding context in oblique cases. This means they will change their endings based on their grammatical role in the sentence. We will start by looking at the numbers from one to four, which have unique declension patterns.

Числівник «один» відмінюється точно так само, як прикметник твердої групи. Ми кажемо: одного зошита, одному зошиту, з одним зошитом. Числівники «два», «три» та «чотири» мають власну систему закінчень, але вони дуже схожі між собою. У родовому та місцевому відмінках вони мають закінчення «-ох»: двох, трьох, чотирьох. У давальному закінчуються на «-ом»: двом, трьом, чотирьом. А в орудному відмінку форми такі: двома, трьома, чотирма. Зверніть увагу, що числівник «чотири» в орудному відмінку не має м'якого знака. Наприклад: на столі немає двох зошитів; ми маємо допомогти чотирьом друзям.

> *The numeral "один" (one) declines exactly like a hard-group adjective. We say: одного зошита, одному зошиту, з одним зошитом. The numerals "два", "три", and "чотири" have their own system of endings, but they are very similar to each other. In the Genitive and Locative cases, they have the ending "-ох": двох, трьох, чотирьох. In the Dative, they end in "-ом": двом, трьом, чотирьом. And in the Instrumental case, the forms are: двома, трьома, чотирма. Note that the numeral "чотири" in the Instrumental case does not have a soft sign. For example: there are not two notebooks on the table; we must help four friends.*

Once you move past the number four, the declension system becomes much more predictable. For numbers from five to twenty, as well as thirty, the declension pattern is highly regular. These numbers behave very much like feminine nouns that end in a consonant. If you know how to decline words like **ніч** (night) or **піч** (oven), you already know how to decline these numerals.

Числівники від п'яти до двадцяти відмінюються за одним спільним зразком. У родовому, давальному та місцевому відмінках вони мають закінчення «-и»: п'яти, десяти, двадцяти. В орудному відмінку ці числівники мають дві паралельні форми, і обидві є абсолютно правильними. Ви можете використовувати форму на «-ма» (п'ятьма, десятьма) або на «-ома» (п'ятьома, десятьома). Наприклад, можна сказати «зустрітися з десятьма колегами» або «зустрітися з десятьома колегами». Форма на «-ма» є трохи коротшою і тому частіше звучить у сучасному розмовному мовленні.

The next group of numerals contains a fascinating grammatical feature. When dealing with tens from fifty to eighty, Ukrainian has a very specific rule that differs significantly from neighboring Slavic languages. You will need to pay close attention to which part of the word actually changes. Meanwhile, the numbers forty, ninety, and one hundred share a beautifully simple declension pattern that is easy to memorize.

У складних числівниках від п'ятдесяти до вісімдесяти під час відмінювання змінюється лише друга частина слова. Перша частина (п'ят-, шіст-, сім-, вісім-) завжди залишається незмінною. Тому ми говоримо: немає п'ятдесяти (а не *п'ятидесяти*), допомогти вісімдесятьом (а не *вісьмомдесятьом*). Це критична відмінність від російської мови, яку варто запам'ятати. Натомість числівники «сорок», «дев'яносто» та «сто» мають дуже просте відмінювання. У називному та знахідному відмінках вони зберігають свою початкову форму, а в усіх інших непрямих відмінках мають єдине закінчення «-а»: сорока, дев'яноста, ста.

Finally, you will often need to use large, exact numbers in real-world situations. When you combine multiple numbers into a compound numeral, the rules become slightly more demanding. You must apply the declension patterns you just learned to the entire numerical phrase. While native speakers sometimes take shortcuts in casual speech, the literary standard requires strict adherence to the rules.

Згідно з літературною нормою української мови, у складених кількісних числівниках відмінюються всі складові слова. Якщо ви хочете сказати про двадцять п'ять студентів в орудному відмінку, ви повинні змінити кожне слово: «з двадцятьма п'ятьма студентами». У родовому відмінку це буде «немає двадцяти п'яти студентів». В усному повсякденному мовленні носії мови часто спрощують цю конструкцію, відмінюючи лише останнє слово. Проте в офіційному спілкуванні, на письмі та під час іспитів вимагається суворе дотримання граматичної норми: кожна частина складеного числівника має стояти у правильному відмінку.

:::info
**Граматичне правило**
У складених кількісних числівниках змінюється кожне слово. На відміну від порядкових числівників, де відмінюється лише останнє слово (сто сорок **п'ятого**), кількісні вимагають відмінювання всіх частин: **ста сорока п'яти**.
:::

<!-- INJECT_ACTIVITY: error-correction-error-correction-declension -->

## 3. Збірні числівники: Коли і як?

Ukrainian has a unique category of numbers called collective numerals, or **збірні числівники**. Unlike standard cardinal numbers that simply count individual items, collective numerals present a quantity as a single, indivisible group. You will often hear words like **двоє**, **троє**, or **четверо** in everyday conversations. These numerals are formed from cardinal numbers between two and twenty, as well as thirty. For numbers from five to twenty, the suffix **-еро** is added, creating forms like **п'ятеро**, **десятеро**, or **двадцятеро**. While you can say **тридцятеро**, collective forms for larger numbers or compound numbers do not exist.

Збірні числівники найчастіше використовуються з іменниками чоловічого роду, які позначають осіб або тварин. Наприклад, ми кажемо «двоє хлопців», «троє студентів» або «п'ятеро вовків». Вони також обов'язкові, коли ми говоримо про дітей або малят тварин. Вираз «троє дітей» звучить набагато природніше, ніж «три дитини». Так само ми використовуємо їх для назв дитинчат тварин: «четверо кошенят» або «семеро ягнят». У сучасному розмовному стилі ці форми мають значну перевагу, оскільки вони роблять мовлення більш емоційним та живим.

> *Collective numerals are most often used with masculine nouns that denote persons or animals. For example, we say "two boys", "three students", or "five wolves". They are also mandatory when talking about children or young animals. The expression "three children" sounds much more natural than using the standard cardinal number. Similarly, we use them for names of baby animals: "four kittens" or "seven lambs". In modern conversational style, these forms have a significant advantage because they make speech more emotional and lively.*

Another crucial domain for collective numerals is their use with nouns that only exist in the plural form, known as pluralia tantum. Words like scissors, doors, or pants cannot be counted with standard cardinal numbers. Because these nouns lack a singular form, the grammatical rules of Ukrainian require the use of collective numerals to count them. Therefore, you must use phrases like **двоє ножиць** (two pairs of scissors) or **троє дверей** (three doors) to express these quantities correctly.

Існують суворі граматичні заборони щодо використання збірних числівників. Головне правило: вони ніколи не поєднуються з іменниками жіночого роду. Не можна сказати «двоє дівчат» або «троє жінок»; правильно говорити лише «дві дівчини» та «три жінки». Єдиним винятком є слово «обидві», яке використовується виключно з жіночим родом. Крім того, збірні числівники заборонено використовувати з неістотами чоловічого роду. Вираз «двоє столів» є грубою граматичною помилкою; необхідно казати «два столи». Пам'ятайте ці обмеження, щоб ваше мовлення звучало грамотно.

:::info
**Граматичне правило**
Після більшості збірних числівників іменник завжди стоїть у формі родового відмінка множини. Незалежно від того, чи це чоловічий рід («двоє друзів»), чи назви малят («п'ятеро немовлят»), чи іменники, що мають лише множину («троє дверей»), іменник набуває форми родового відмінка. Винятком є числівники «обидва» та «обидві», після яких іменник залишається в називному відмінку множини («обидві дівчини»).
:::

When using collective numerals in the nominative case, they consistently govern the noun in the genitive plural. Examples like **двоє друзів** and **четверо коней** perfectly illustrate this grammatical pattern. This agreement rule ensures that the quantity and the noun are properly linked in a sentence. However, it is important to note that in oblique cases, collective numerals lose their unique suffixes and decline exactly like standard cardinal numbers.

<!-- INJECT_ACTIVITY: match-up-collective-usage -->

## 4. Дроби та мішані кількості

When expressing parts of a whole, Ukrainian often relies on specific nouns rather than a mathematical reading of numbers. The most frequent fractions are single words that function just like regular nouns in a sentence. Because they are nouns themselves, they demand a specific relationship with the object they quantify. They require that the following object be placed in the genitive case, essentially answering the question "a part of what?".

Ми часто використовуємо ці прості дроби у повсякденному житті, коли говоримо про час, їжу або статистику. Найпоширенішими є слова «половина», «третина» та «чверть» або «четвертина». Наприклад, ми кажемо «половина яблука», «третина населення» або «чверть години». Оскільки слово «чверть» належить до третьої відміни іменників, воно відмінюється як слово «ніч». В орудному відмінку ми скажемо «з чвертю», як у фразі «п'ять із чвертю літрів».

For the quantity "one and a half", Ukrainian has a unique and highly specific set of words: **півтора** and **півтори**. Unlike compound descriptive phrases in English, these are single, unchangeable lexical units. Their correct usage depends strictly on the gender of the noun they modify, making them a common stumbling block for learners. Regardless of their form, they always govern the genitive singular case of the noun that follows them.

Для чоловічого та середнього роду ми завжди використовуємо форму «півтора». Ми кажемо «півтора метра», «півтора кілограма» або «півтора відра». Але якщо іменник належить до жіночого роду, необхідно вживати форму «півтори». Тому ми говоримо «півтори години» або «півтори тонни». Ці слова ніколи не змінюють свою форму в непрямих відмінках. Також існує слово «півтораста», яке означає сто п'ятдесят, але воно вимагає після себе родового відмінка множини: «півтораста учнів».

> *For masculine and neuter nouns, we always use the form "півтора". We say "one and a half meters", "one and a half kilograms", or "one and a half buckets". But if the noun belongs to the feminine gender, you must use the form "півтори". Therefore, we say "one and a half hours" or "one and a half tons". These words never change their form in oblique cases. There is also the word "півтораста", which means one hundred and fifty, but it requires the genitive plural after it: "one hundred and fifty students".*

:::info
**Граматичне правило**
Слова «півтора» та «півтори» вимагають після себе іменника у формі родового відмінка однини, а не множини. Тому єдиним правильним варіантом є «півтори години», а помилковим — «півтори годин».
:::

When discussing statistics, academic topics, or precise measurements, you will frequently need to use percentages and decimal fractions. The Ukrainian word for percent is **відсоток**, and it behaves exactly like any regular inanimate masculine noun. It agrees with the preceding numeral following the exact same rules you learned for counting objects. Decimal fractions, however, introduce a slightly different structural pattern that relies heavily on the genitive singular.

Слово «відсоток» узгоджується з числівниками за стандартними правилами, які ви вже знаєте. Ми кажемо «один відсоток», «два відсотки» та «п'ять відсотків». Коли ми читаємо десяткові дроби, як-от 1,2, ми говоримо «одна ціла і дві десятих». Після десяткових дробів іменник завжди стоїть у родовому відмінку однини: «одна ціла і дві десятих кілограма» або «п'ять цілих і сім десятих відсотка». Якщо ми використовуємо мішані числа зі словом «з», іменник узгоджується з цілою частиною: «два з половиною кілометри».

<!-- INJECT_ACTIVITY: quiz-fraction-agreement -->

## 5. Неозначено-кількісні слова та наближення

In addition to exact numbers, we often need to express indefinite quantities. Words like **багато** (many/much), **мало** (few/little), **кілька** or **декілька** (several), and **чимало** (quite a lot) are essential for everyday communication.

Ці неозначено-кількісні слова граматично поводяться так само, як і числівники від п'яти до двадцяти. Після них злічувані іменники завжди стоять у формі родового відмінка множини. Наприклад, ми кажемо «кілька книжок», «багато людей» або «чимало зусиль». Якщо іменник незлічуваний, він вживається у родовому відмінку однини, як у фразі «мало часу».

> *These indefinite-quantitative words behave grammatically just like numerals from five to twenty. After them, countable nouns always stand in the genitive plural form. For example, we say "several books", "many people", or "quite a lot of effort". If the noun is uncountable, it is used in the genitive singular, as in the phrase "little time".*

:::info
**Граматичне правило**
Неозначено-кількісні слова, такі як «багато», «кілька» та «чимало», вимагають після себе родового відмінка, так само як числівник «п'ять».
:::

When you need to express an approximate quantity, Ukrainian uses specific prepositions combined with numerals. The most common ones are **близько** (about/approximately), **понад** (more than), and **до** (up to).

Кожен із цих прийменників вимагає певного відмінка. Після слів «близько» та «до» числівник і наступний іменник ставляться у родовий відмінок. Ми говоримо «на зустріч прийшло близько ста людей» або «це коштує до тисячі гривень». Натомість прийменник «понад» вимагає знахідного відмінка: «він прочитав понад двісті сторінок». Для вираження приблизності також часто використовують прийменник «з», який поєднується зі знахідним відмінком, наприклад, «ми чекали з десяток хвилин».

Finally, when discussing resources like time, budget, or ingredients, you will need to express concepts of excess or sufficiency. Words like **забагато** (too much), **замало** (too little), and **достатньо** (enough) are incredibly useful in these contexts.

Ці слова також є неозначено-кількісними і вимагають після себе родового відмінка, подібно до слова «багато». У контексті кулінарії ми можемо сказати «у цьому супі забагато солі». Коли ми плануємо наш бюджет або час, ми часто використовуємо такі фрази: «у нас замало грошей на цю покупку» або «нам достатньо двох годин для роботи». Ці конструкції роблять ваше мовлення значно природнішим і точнішим.

<!-- INJECT_ACTIVITY: fill-in-indefinite-quantity -->

## 6. Кількісні вирази в контексті: Рецепти та Статистика

Коли ми читаємо українські рецепти, ми постійно зустрічаємо кількісні вирази. Наприклад, класичний рецепт млинців вимагає: три яйця, півтори склянки молока та двісті грамів борошна. Зверніть увагу на відмінки. Ми кажемо «три яйця», бо числівник вимагає називного відмінка множини. Але ми говоримо «двісті грамів», де іменник стоїть у родовому відмінку множини. 

> *When we read Ukrainian recipes, we constantly encounter quantity expressions. For example, a classic pancake recipe requires: three eggs, a cup and a half of milk, and two hundred grams of flour. Pay attention to the cases. We say "три яйця" because the numeral requires the nominative plural. But we say "двісті грамів", where the noun is in the genitive plural.*

When describing demographic data, you will need to handle large numbers. The words **тисяча** (thousand) and **мільйон** (million) govern the genitive plural.

Площа України становить шістсот три тисячі квадратних кілометрів. Її столиця, місто Київ, має близько трьох мільйонів мешканців. У статистичних описах ми часто використовуємо прийменники «близько» та «понад». Після прийменника «близько» числівник та іменник завжди стоять у родовому відмінку. Тому ми говоримо «близько трьох мільйонів».

:::tip
**Real-life usage**
In spoken Ukrainian, you will often hear people say "двісті грам" instead of "двісті грамів". While "грам" is very common in informal speech, "грамів" is the correct standard form required in written recipes and official documents.
:::

На ринку ви постійно обговорюєте ціни та вагу продуктів. Тут надзвичайно важливо швидко та правильно узгоджувати числівники з іменниками.

> — **Покупець:** Добрий день! Скільки коштують ці п'ять персиків? *(Good day! How much do these five peaches cost?)*
> — **Продавець:** Вісімдесят гривень за кілограм. Дати вам усі п'ять? *(Eighty hryvnias per kilogram. Should I give you all five?)*
> — **Покупець:** Ні, дайте, будь ласка, три персики і півкілограма полуниці. *(No, please give me three peaches and half a kilo of strawberries.)*
> — **Продавець:** Добре. З вас сто п'ятдесят гривень. *(Alright. One hundred fifty hryvnias, please.)*

<!-- INJECT_ACTIVITY: essay-response-contextual-quantity -->

## 7. Підсумок

Ми розглянули одну з найважливіших і найскладніших тем української граматики — узгодження кількісних числівників з іменниками. Ця система суттєво відрізняється від інших слов'янських мов і вимагає уваги до деталей. Ваше вміння правильно використовувати ці конструкції є ключовим показником високого рівня володіння мовою. Щоб вільно спілкуватися на теми цін, часу, рецептів чи статистики, ці правила мають стати для вас автоматичними.

> *We have covered one of the most important and complex topics in Ukrainian grammar — the agreement of cardinal numerals with nouns. This system differs significantly from other Slavic languages and requires attention to detail. Your ability to correctly use these constructions is a key indicator of a high level of language proficiency. To speak fluently about prices, time, recipes, or statistics, these rules must become automatic for you.*

:::info
**Шпаргалка узгодження (Н.в. / Зн.в. неістот)**
*   **1** (один, одна, одне) + **Н.в. однини** («один стіл», «одна книжка»).
*   **2, 3, 4** (два, три, чотири, обидва) + **Н.в. множини** («два столи», «три вікна»).
*   **5–20, 30...** (п'ять, десять, сто) + **Р.в. множини** («п'ять столів», «десять вікон»).
*   **Збірні числівники** (двоє, троє) + **Р.в. множини** («двоє хлопців»).
*   **Дроби** (половина, чверть, півтора/півтори) + **Р.в. однини** («півтори години»).
:::

Перед тим, як переходити до наступного модуля, дайте собі відповіді на кілька контрольних запитань. Це допоможе вам зрозуміти, які аспекти теми потребують додаткового повторення. Не поспішайте і спробуйте сформулювати відповіді вголос. Чи можете ви правильно узгодити складені числівники «21» та «22» з іменником «сторінка»? Пам'ятайте, що у складених числівниках форму іменника визначає останнє слово. Тому ми говоримо «двадцять одна сторінка», але «двадцять дві сторінки». Коли ви використаєте збірний числівник «двоє», а коли кількісний «два»? Збірні числівники вживаються переважно з назвами осіб чоловічого роду або дітей, тому ми кажемо «двоє хлопців». Але з неістотами ми завжди використовуємо звичайні кількісні числівники: «два столи».

> *Before moving on to the next module, answer a few checklist questions for yourself. This will help you understand which aspects of the topic need additional review. Take your time and try to formulate the answers out loud. Can you correctly agree the compound numerals "21" and "22" with the noun "сторінка"? Remember that in compound numerals, the last word determines the noun's form. Therefore, we say "двадцять одна сторінка" but "двадцять дві сторінки". When will you use the collective numeral "двоє" and when the cardinal "два"? Collective numerals are used primarily with male persons or children, so we say "двоє хлопців". But with inanimate objects, we always use regular cardinal numerals: "два столи".*

Як сказати англійський вираз «one and a half hours» українською? Слово «година» жіночого роду, тому ми використовуємо специфічну форму «півтори» і ставимо іменник у родовий відмінок однини: «півтори години». Який відмінок вимагає неозначено-кількісне слово «кілька»? Як і слова «багато», «мало» або «чимало», воно завжди вимагає після себе родового відмінка множини. Як провідміняти словосполучення «три студенти» в орудному відмінку? У непрямих відмінках числівник та іменник мають узгоджуватися, тому правильна форма — «трьома студентами».

> *How do you say the English expression "one and a half hours" in Ukrainian? The word "година" is feminine, so we use the specific form "півтори" and put the noun in the genitive singular: "півтори години". What case does the indefinite-quantitative word "кілька" require? Like the words "багато", "мало" or "чимало", it always requires the genitive plural after it. How do you decline the phrase "три студенти" in the instrumental case? In oblique cases, the numeral and the noun must agree, so the correct form is "трьома студентами".*

У наступних модулях ми будемо активно використовувати ці знання у складних синтаксичних конструкціях та професійному мовленні. Ви навчитеся вільно оперувати відсотками у бізнес-звітах і обговорювати демографічні зміни. Також ви зможете детально описувати історичні події, спираючись на точні кількісні дані. Попереду на вас чекає вивчення складних займенників, що стане останнім граматичним кроком перед великим комунікативним чекпойнтом.


</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: cases-with-quantity-expressions
level: b1

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

**Level: B1 (Module 62)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

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
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
