<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 62: Кількісні вирази (B1, B1.5 [Case Nuances & Prepositions])
**Writer:** Gemini
**Word target:** 4000

## Plan (source of truth)

<plan_content>
module: b1-061
level: B1
sequence: 61
slug: cases-with-quantity-expressions
version: '3.1'
title: "Кількісні вирази"
subtitle: "Узгодження числівників з іменниками та неозначено-кількісні слова"
focus: grammar
pedagogy: PPP
phase: "B1.5 [Case Nuances & Prepositions]"
word_target: 4000
objectives:
  - "Learner can correctly agree cardinal numerals with nouns: один стіл (Н.в.), два/три/чотири
    столи (Н.в. мн.), п'ять столів (Р.в. мн.)"
  - "Learner can decline cardinal numerals in oblique cases and maintain agreement:
    двох столів (Р.в.), двом столам (Д.в.), двома столами (Ор.в.)"
  - "Learner can use indefinite quantity words with correct case: багато/мало/кілька/декілька/чимало
    + Р.в."
  - "Learner can use collective numerals (збірні) with the right noun classes: двоє
    дітей, четверо хлопців, троє дверей"
  - "Learner can use quantity expressions in real contexts: prices, statistics, recipes,
    and descriptions of groups"
dialogue_situations:
  - setting: 'Census worker visiting a village household — counting everything: Скільки
      людей? П''ятеро. Двоє дітей (n, children). Кілька кімнат (f, rooms). Багато
      землі (f, land). Мало худоби (f, livestock).'
    speakers:
      - Переписувач (census worker)
      - Господар
    motivation: 'Quantity expressions: п''ятеро людей, двоє дітей, кілька кімнат,
      багато землі'
content_outline:
  - section: "Узгодження кількісних числівників з іменниками"
    words: 800
    points:
      - "From Литвінова Grade 6 p.240-241: один/одна/одне + Н.в. одн.: один студент,
        одна книжка, одне вікно. два/дві/три/чотири + Н.в. мн.: два студенти, три
        книжки, чотири вікна. (Note: дві for feminine: дві книжки, not *два книжки.)
        п'ять — двадцять, тридцять + Р.в. мн.: п'ять студентів, десять книжок."
      - "Special cases (Литвінова Grade 6 p.241): Nouns with суфікс -ин-: два селянина,
        три громадянина (Р.в. одн.!). Nouns of ІV відміна (pluralia tantum type):
        cannot use два/три/чотири, use збірні instead: троє дверей, двоє окулярів.
        тисяча + Р.в. мн.: тисяча гривень. мільйон + Р.в. мн.: мільйон людей."
      - "Compound numerals: the LAST numeral determines agreement. двадцять один студент
        (один → Н.в. одн.) двадцять два студенти (два → Н.в. мн.) двадцять п'ять студентів
        (п'ять → Р.в. мн.) Practice: 15 number + noun pairs for correct agreement."
  - section: "Відмінювання кількісних числівників"
    words: 700
    points:
      - "From Авраменко Grade 11 p.37 and Заболотний Grade 7 p.171: один: like an
        adjective (одного, одному, одним, одному). два/дві: двох, двом, двох/два,
        двома, двох. три: трьох, трьом, трьох/три, трьома, трьох. чотири: чотирьох,
        чотирьом, чотирьох/чотири, чотирма, чотирьох."
      - "5-20, 30: like ІІІ відміна feminine nouns: п'яти, п'яти, п'ять, п'ятьма,
        п'яти. 50-80: both parts decline: п'ятдесяти, п'ятдесяти, п'ятдесяти, п'ятдесятьма,
        п'ятдесяти."
      - "In oblique cases, ALL parts of compound numerals decline: з двадцятьма п'ятьма
        студентами (Ор.в.). However, in practice many speakers simplify this, especially
        in speech. Written standard requires full declension. Practice: decline двадцять
        три книжки through all cases."
  - section: "Збірні числівники"
    words: 600
    points:
      - "Formation: двоє, троє, четверо, п'ятеро, шестеро, семеро... From Голуб Grade
        6 p.163: Used with: masculine persons (двоє хлопців), children (троє дітей),
        pluralia tantum nouns (четверо дверей, двоє ножиць), nouns that only exist
        in plural (п'ятеро саней). NOT with: feminine persons (*двоє дівчат → дві
        дівчини) or inanimate countables (*троє столів → три столи)."
      - "Collective numerals always take Р.в. мн.: двоє друзів, троє братів, четверо
        дітей. In oblique cases, they decline like cardinal п'ять: двох, двом, двох,
        двома, двох."
      - "Practice: choose cardinal or collective numeral for 10 noun groups, explaining
        why."
  - section: "Дроби та змішані кількості (§4.2.1.3)"
    words: 500
    points:
      - "The State Standard requires fractions at B1. Basic fractions: половина (1/2),
        третина (1/3), чверть/четвертина (1/4), п'ята частина (1/5). Agreement: половина
        + Р.в. одн. (половина яблука), третина + Р.в. одн. (третина населення), чверть
        + Р.в. одн. (чверть години). From Голуб Grade 6 p.166: дробові числівники."
      - "Decimal and compound fractions: два з половиною (2.5), три чверті (3/4), одна
        ціла і дві десятих (1.2). In context: півтора (1.5 — masculine/neuter), півтори
        (1.5 — feminine): півтора кілограма, півтори години. Note: півтора + Р.в. одн.
        (not plural!)."
      - "Percentages: десять відсотків (10%), сто відсотків (100%). Agreement: один
        відсоток, два відсотки, п'ять відсотків. Practice: express recipe quantities
        (півкіло, чверть ложки), statistics (третина населення, 25 відсотків), and time
        (півтори години, дві з половиною доби)."
  - section: "Неозначено-кількісні слова"
    words: 500
    points:
      - "Words expressing indefinite quantity + Р.в.: багато людей, мало часу, кілька
        книжок, декілька разів, чимало зусиль, достатньо грошей, забагато роботи.
        All govern Р.в. — same pattern as numbers 5-20."
      - "Approximation: близько + Р.в. (about/approximately), понад + Зн.в. (more
        than), до + Р.в. (up to). 'Близько ста людей прийшло.' 'Понад тисячу гривень.'
        Practice: describe quantities using approximate expressions."
  - section: "Кількісні вирази в контексті"
    words: 700
    points:
      - "Recipes: Візьміть двісті грамів масла, три яйця, п'ятсот грамів борошна.
        Додайте чайну ложку солі та дві столові ложки цукру. Practice: read a Ukrainian
        recipe and identify all quantity expressions."
      - "Statistics: В Україні живе понад сорок мільйонів людей. Київ має близько
        трьох мільйонів мешканців. Practice: describe a city or country using quantity
        expressions."
      - "Shopping: Дайте, будь ласка, два кілограми картоплі, півкіло помідорів і
        триста грамів сиру. Скільки коштують п'ять яблук? Self-check: 10 quantity
        expressions to form correctly."
  - section: "Підсумок"
    words: 400
    points:
      - "Agreement rules summary table: 1 + Н.в.одн., 2-4 + Н.в.мн., 5-20 + Р.в.мн.,
        збірні + Р.в.мн., дроби (половина/третина/чверть + Р.в.одн., півтора/півтори
        + Р.в.одн.). Oblique cases: all parts of compound numerals decline."
      - "Self-check: 1. Agree numerals with nouns: 21 студент, 44 сторінки, 100 гривень.
        2. Choose cardinal or collective: (два/двоє) хлопці, (три/троє) двері. 3. Decline
        'п'ять книжок' through Р.в., Д.в., Ор.в. 4. Express fractions: 2.5 кг, 1/3
        населення, 75%. 5. Use approximate quantities: близько, понад, до."
      - "Preview: advanced pronouns — the final grammar module before the communication
        module and checkpoint."
vocabulary_hints:
  required:
    - "кількісний числівник (cardinal numeral — один, два, сто)"
    - "збірний числівник (collective numeral — двоє, троє, четверо)"
    - "узгодження (agreement — matching numeral with noun form)"
    - "неозначено-кількісний (indefinite-quantitative — багато, кілька)"
    - "кілька (several — governs Р.в.)"
    - "декілька (several — synonym of кілька)"
    - "чимало (quite a lot — governs Р.в.)"
    - "достатньо (enough — governs Р.в.)"
    - "понад (more than — governs Зн.в.)"
    - "близько (about/approximately — governs Р.в.)"
  recommended:
    - "тисяча (thousand — governs Р.в.мн.)"
    - "мільйон (million — governs Р.в.мн.)"
    - "половина (half — + Р.в.)"
    - "чверть (quarter — + Р.в.)"
    - "забагато (too much — governs Р.в.)"
    - "замало (too little — governs Р.в.)"
activity_hints:
  - type: reading
    focus: "Прочитайте текст про узгодження кількісних числівників з іменниками і дайте відповіді на запитання."
  - type: essay-response
    focus: "Напишіть 5 речень, використовуючи нову лексику з розділу «Відмінювання кількісних числівників»."
  - type: fill-in
    focus: "Вставте правильну граматичну форму у реченнях на тему узгодження кількісних числівників з іменниками."
  - type: error-correction
    focus: "Знайдіть і виправте помилки у реченнях на тему відмінювання кількісних числівників."
  - type: quiz
    focus: "Оберіть правильний варіант: лексика та граматика з розділу «Узгодження кількісних числівників з іменниками»."
  - type: match-up
    focus: "З'єднайте терміни з розділу «Відмінювання кількісних числівників» з їхніми визначеннями."
connects_to:
  - "b1-052 (Порядкові числівники — ordinal declension and dates)"
  - "b1-046 (Родовий відмінок деталі — Р.в. governed by quantity words)"
  - "b1-044 (Покупки і послуги — quantity expressions in shopping)"
prerequisites:
  - "A2 completion (numbers, basic quantity)"
  - "b1-046 (Родовий відмінок деталі — Р.в. forms)"
  - "b1-052 (Порядкові числівники і відмінки — ordinal declension)"
grammar:
  - "Узгодження: один + Н.в.одн., 2-4 + Н.в.мн., 5+ + Р.в.мн."
  - "Збірні числівники: двоє, троє + Р.в.мн. (з чоловічими особами, pluralia tantum)"
  - "Відмінювання кількісних: один (як прикметник), два-чотири, п'ять-двадцять"
  - "Неозначено-кількісні: багато, мало, кілька, достатньо + Р.в."
  - "Складені числівники: всі частини відмінюються в непрямих відмінках"
register: науково-навчальний
references:
  - title: "Литвінова Grade 6, p.240-241"
    notes: "Agreement rules: один, два-чотири, п'ять+, special -ин- nouns."
  - title: "Голуб Grade 6, p.163-166"
    notes: "Collective numerals, fraction declension, agreement table."
  - title: "Авраменко Grade 11, p.37"
    notes: "Cardinal numeral declension tables."
  - title: "Заболотний Grade 7, p.167-171"
    notes: "Numeral classification, declension types, parallel usage."

</plan_content>

## Generated Content

<generated_module_content>
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

## 2. Відмінювання кількісних числівників (~750 слів)

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
Після збірних числівників іменник завжди стоїть у формі родового відмінка множини. Незалежно від того, чи це чоловічий рід («двоє друзів»), чи назви малят («п'ятеро немовлят»), чи іменники, що мають лише множину («троє дверей»), іменник набуває форми родового відмінка.
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

## 6. Кількісні вирази в контексті: Рецепти та Статистика (~750 слів)

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

## 7. Підсумок (~450 слів)

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

Загальна кількість слів: ~4250 слів
</generated_module_content>

**PIPELINE NOTE — Word count: 3741 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 4000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 833 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Пам — NOT IN VESUM
  ✗ вісьмомдесятьом — NOT IN VESUM
  ✗ шіст — NOT IN VESUM
  ✗ ятайте — NOT IN VESUM

All 833 other words are confirmed to exist in VESUM.

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
