<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/complex-subordinate-relative.yaml` file for module **77: Означальні речення** (b1).

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

- `<!-- INJECT_ACTIVITY: reading-intro -->`
- `<!-- INJECT_ACTIVITY: match-up-terms -->`
- `<!-- INJECT_ACTIVITY: fill-in-yakyj -->`
- `<!-- INJECT_ACTIVITY: error-correction-yakyj -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`
- `<!-- INJECT_ACTIVITY: essay-yakyj-cases -->`
- `<!-- INJECT_ACTIVITY: mark-phrase-parts -->`
- `<!-- INJECT_ACTIVITY: find-grammatical-core -->`
- `<!-- INJECT_ACTIVITY: quiz-sentence-members -->`
- `<!-- INJECT_ACTIVITY: simple-vs-complex-sort -->`
- `<!-- INJECT_ACTIVITY: fix-complex-punctuation -->`
- `<!-- INJECT_ACTIVITY: match-cases-to-questions -->`
- `<!-- INJECT_ACTIVITY: determine-word-case -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Прочитайте текст про означальні підрядні речення і дайте відповіді на запитання.
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «Який у різних відмінках».
  type: essay-response
- focus: Вставте правильну граматичну форму у реченнях на тему означальні підрядні
    речення.
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему який у різних відмінках.
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Означальні підрядні
    речення».'
  type: quiz
- focus: З'єднайте терміни з розділу «Який у різних відмінках» з їхніми визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- чий (whose — possessive relative pronoun)
- котрий (which — literary synonym of який)
- антецедент (antecedent — formal term for означуване слово)
- постпозиція (postposition — clause always after the noun)
required:
- означальне речення (attributive/relative clause)
- який/яка/яке/які (which/that — relative pronoun, declines)
- означуване слово (antecedent — noun the clause describes)
- сполучне слово (connective word — який, що, де, куди, коли)
- відмінок (case — determines the form of який in the clause)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Означальні підрядні речення (~825 words total)

Коли ми хочемо дати розгорнуту характеристику певному предмету, ми використовуємо **означальне речення** (attributive/relative clause). Це дуже поширена граматична конструкція в українській мові. Означальні підрядні речення працюють подібно до звичайних прикметників, але дозволяють передати набагато більше деталей. Вони приєднуються до головної частини речення і пояснюють один конкретний іменник або займенник. Щоб знайти таку підрядну частину, вам потрібно поставити питання, і ключовим тут є займенник **який/яка/яке/які** (which/that — relative pronoun, declines). Наприклад, проаналізуємо фразу: «Місто, яке я відвідав, мене дуже сильно вразило». Головна частина тут — «Місто мене дуже сильно вразило». Підрядна частина «яке я відвідав» безпосередньо характеризує це місто. Для з'єднання двох частин ми використовуємо **сполучне слово** (connective word — який, що, де, куди, коли), найчастіше це саме такі відносні займенники або прислівники. Кожен такий займенник має свій рід, число та відмінок, які залежать від його ролі в підрядному реченні. Ці конструкції є незамінним інструментом для точного висловлення думок, і вони створюють плавний потік мовлення.

У граматиці іменник або займенник у головній частині, який потребує пояснення, називається терміном **означуване слово** (antecedent — noun the clause describes). Це своєрідний якір, до якого кріпиться вся залежна конструкція. Існує дуже суворе правило щодо розташування цих елементів у тексті. Означальне підрядне речення повинно стояти безпосередньо після цього специфічного іменника. Цей фіксований порядок слів має назву постпозиція. Українська мова не дозволяє вільно переміщувати таку підрядну частину. Якщо ви розірвете цей зв'язок, речення стане незрозумілим або навіть кумедним. Розгляньмо приклад правильної побудови: «Книга, яку я прочитав, лежить на столі». Підрядна частина йде відразу за словом «книга». А тепер погляньте на помилковий варіант: «Яку я прочитав, книга лежить на столі». Така конструкція є абсолютно неприродною і граматично хибною. Завжди пам'ятайте про цей нерозривний зв'язок між іменником та його детальним описом. Ніколи не ставте інші члени речення між ними.

> *In grammar, the noun or pronoun in the main clause that requires explanation is called the **означуване слово** (antecedent — noun the clause describes). It is a kind of anchor to which the whole dependent structure is attached. There is a very strict rule regarding the placement of these elements in a text. The relative clause must stand immediately after this specific noun. This fixed word order is called postposition. The Ukrainian language does not allow you to freely move such a subordinate clause. If you break this connection, the sentence will become incomprehensible or even funny. Let's look at an example of a correct structure: "The book that I read is lying on the table." The subordinate clause follows right after the word "book." And now look at the incorrect version: "Which I read, the book is lying on the table." Such a construction is completely unnatural and grammatically flawed. Always remember this unbreakable bond between the noun and its detailed description. Never place other parts of the sentence between them.*

Можливо, ви вже помітили, що означальні підрядні речення виконують ту саму синтаксичну функцію, що й дієприкметниковий зворот, який ви детально вивчали раніше в окремому модулі. Обидві ці граматичні конструкції існують для того, щоб виражати ознаку предмета, яка утворилася внаслідок певної дії. Вони є повними структурними еквівалентами, і ви часто можете замінювати одну конструкцію іншою абсолютно без втрати основного змісту. Наприклад, ми можемо сказати: «Торт, политий шоколадом, надзвичайно сподобався всім присутнім гостям». Це класичний дієприкметниковий зворот. Але ми також можемо використати означальне підрядне речення, щоб передати ту саму думку: «Торт, який полили шоколадом, надзвичайно сподобався всім присутнім гостям». Значення залишається абсолютно ідентичним в обох випадках. Проте між ними існує величезна і дуже важлива стилістична різниця. Дієприкметникові звороти характерні переважно для формального, ділового, книжного або суворого наукового стилів. У повсякденному живому спілкуванні українці використовують їх вкрай рідко, бо вони обтяжують вимову. Натомість означальні підрядні речення є набагато більш природними, гнучкими та неймовірно частотними у розмовній мові. Якщо ви хочете звучати як справжній носій мови під час звичайної бесіди з друзями чи колегами, завжди надавайте перевагу підрядним реченням. Вони роблять вашу вимову легкою, сучасною та невимушеною, ефективно уникаючи зайвої офіційності.

:::info
**Grammar box**
Хоча дієприкметниковий зворот і означальне речення передають однакову інформацію, у розмовній українській мові ми майже завжди обираємо підрядне речення. Воно звучить набагато живіше і природніше.
:::

Щоб побачити, як ці граматичні правила працюють у реальному житті, уявімо цікаву ситуацію. Ми вирушаємо на прогулянку до столиці України. Наша мета — відвідати відомий Київський ботанічний сад імені Миколи Гришка. Це надзвичайно мальовниче місце, яке щороку приваблює тисячі туристів та дослідників. Ми будемо гуляти його широкими алеями, дихати свіжим повітрям та спостерігати за унікальними історичними рослинами і деревами. Ботанічний сад має багату колекцію рідкісних видів, які були привезені з різних куточків світу. Тут можна зустріти дерева, які пам'ятають події минулих століть, та квіти, які вражають своєю красою. Під час нашої віртуальної екскурсії ми почуємо розмову між досвідченим експертом та допитливим учнем. Коли ви читаєте цей діалог, звертайте увагу на те, який **відмінок** (case — determines the form of який in the clause) використовують співрозмовники. Це допоможе вам краще відчути ритм і структуру таких граматичних конструкцій.

<!-- INJECT_ACTIVITY: reading-intro --> [reading, "Прочитайте текст про означальні підрядні речення і дайте відповіді на запитання.", 5 items]

> — **Ботанік:** Подивіться ліворуч, шановний колего. Це дерево, яке росте тут уже сто років, і воно є справжньою гордістю нашого саду. *(Look to the left, dear colleague. This is a tree that has been growing here for a hundred years, and it is a true pride of our garden.)*
> — **Студент:** Це просто неймовірно! А які це дивовижні квіти цвітуть поруч із ним на цій клумбі? *(This is simply incredible! And what are these amazing flowers blooming next to it on this flowerbed?)*
> — **Ботанік:** Це дуже рідкісна орхідея. Це квітка, яку подарували з Японії багато років тому під час міжнародної виставки. *(This is a very rare orchid. This is a flower that was gifted from Japan many years ago during an international exhibition.)*
> — **Студент:** Вона виглядає дуже крихкою та ніжною. Чи є тут місце, де можна відпочити і зробити кілька гарних фотографій на згадку? *(It looks very fragile and delicate. Is there a place here where one can rest and take some beautiful photos as a keepsake?)*
> — **Ботанік:** Звісно, така зона існує. Пройдемо трохи далі по цій тінистій алеї. Там є чудове місце, де можна відпочити біля прохолодного озера. *(Of course, such an area exists. Let's walk a bit further down this shady alley. There is a wonderful place there where one can rest by the cool lake.)*
> — **Студент:** Дуже вам дякую за цікаву екскурсію! Я уважно записую всі назви унікальних рослин, які ми сьогодні побачили. *(Thank you very much for the interesting excursion! I am carefully writing down all the names of the unique plants that we have seen today.)*
> — **Ботанік:** Це абсолютно правильний науковий підхід. Студент, який постійно робить детальні нотатки, обов'язково і дуже швидко досягає великого успіху в науці. *(That is an absolutely correct scientific approach. A student who constantly takes detailed notes definitely and very quickly achieves great success in science.)*

## Який у різних відмінках (~990 words total)

The relative pronoun **який/яка/яке/які** (which/that — relative pronoun, declines) is the most common **сполучне слово** (connective word — який, що, де, куди, коли) used to introduce an **означальне речення** (attributive/relative clause). Because it functions grammatically like an adjective, it must change its form to reflect gender, number, and case. This flexibility is what makes Ukrainian sentences so precise, but it also requires you to pay close attention to two different parts of the sentence at once. The golden rule for using this pronoun correctly involves a strict division of labor. 

The gender and the number of the pronoun are dictated exclusively by the **означуване слово** (antecedent — noun the clause describes) located in the main clause. If the main clause talks about a feminine singular noun, the pronoun must be feminine and singular. However, the **відмінок** (case — determines the form of який in the clause) is completely independent of the main clause. The case is determined strictly by the syntactic role that the pronoun plays inside its own relative clause. This means you must analyze the internal logic of the subordinate clause to choose the right ending.

Let us look at the most frequent contrast you will encounter: the Nominative case versus the Accusative case. When the relative pronoun acts as the active subject performing the action inside the subordinate clause, it must take the Nominative case. Conversely, when the pronoun represents the direct object receiving the action inside the subordinate clause, it must take the Accusative case. This distinction is crucial because the word order in the relative clause does not always help you identify the subject and the object. You must rely on the case endings to understand who is doing what.

Студент, який вивчає українську мову, зараз живе в Києві. У цьому реченні займенник виконує дію всередині підрядної частини. Він є підметом, тому стоїть у називному відмінку. З іншого боку, подивіться на такий приклад. Книга, яку я нещодавно прочитав, лежить на столі. Тут головним героєм підрядної частини є займенник «я», а книга є об'єктом дії. Тому ми використовуємо знахідний відмінок.

> *The student who is studying the Ukrainian language currently lives in Kyiv. In this sentence, the pronoun performs the action inside the subordinate clause. It is the subject, so it stands in the Nominative case. On the other hand, look at this example. The book that I recently read is lying on the table. Here, the main character of the subordinate clause is the pronoun "I", and the book is the object of the action. Therefore, we use the Accusative case.*

A very common mistake for English speakers is to match the case of the pronoun with the case of the antecedent. You might be tempted to say "Це книга, який я купив" because the word "книга" is Nominative in the main clause. However, inside the relative clause, you bought the book, making it the direct object. The correct form is "яку".

The Genitive and Dative cases also appear frequently in relative clauses, often governed by specific verbs, prepositions, or negation. The Genitive case is required when the relative clause expresses absence, quantity, or when it features an animate direct object. The Dative case is used when the pronoun represents the indirect object or the recipient of an action inside the subordinate clause. Understanding these requirements helps you build more complex and expressive sentences without losing grammatical accuracy.

Студент, якого я добре знаю, живе в Києві. Оскільки слово «студент» означає живу істоту, знахідний відмінок збігається з родовим відмінком. Якщо ми говоримо про відсутність чогось, ми також використовуємо родовий відмінок. Це та сама проблема, якої ми намагалися уникнути. Коли дія спрямована на когось, нам потрібен давальний відмінок. Студент, якому я вчора допоміг з перекладом, живе в Києві. У цій підрядній частині займенник показує отримувача допомоги.

The Instrumental and Locative cases describe means, accompaniment, or location within the relative clause. The Instrumental case is used when the pronoun is the tool used to perform the action or when it is governed by prepositions like "з" (with). The Locative case always requires a preposition and indicates where the action of the relative clause takes place.

Людина, якою я щиро захоплююсь, зараз живе дуже далеко. У цьому реченні дієслово вимагає орудного відмінка. Місто, в якому я живу, має дуже красиву архітектуру та багату історію. Прийменник вказує на місцезнаходження всередині підрядної частини, тому ми використовуємо місцевий відмінок.

A common structural error occurs when learners translate relative clauses of location directly from English. You might hear someone say "*місто, в яке я народився". This is incorrect because the preposition "в" indicating a static location demands the Locative case, not the Accusative case. The grammatically correct phrasing must be "місто, в якому я народився" to properly reflect the static nature of the action within the relative clause.

To fully master this construction, you must practice navigating the intersection of gender, number, and case simultaneously. The main clause provides the template for gender and number, while the relative clause provides the template for the case. Let us observe how the same syntactic role in the relative clause looks different depending on the antecedent in the main clause.

Хлопець, який читає цю цікаву статтю, є моїм братом. Дівчина, яка читає цю цікаву статтю, є моєю сестрою. Місто, яке має таку велику бібліотеку, приваблює багато розумних студентів. Люди, які постійно читають нові книги, завжди мають широкий кругозір. У всіх цих прикладах займенник є підметом підрядної частини. Він завжди стоїть у називному відмінку. Але його закінчення змінюється, тому що головні слова мають різний рід та число.

The ultimate proof of your grammatical control lies in sentences where the case of the antecedent and the case of the relative pronoun completely diverge. This independence is the core principle you must internalize. The main sentence verb dictates the case of the noun it interacts with, while the subordinate clause verb dictates the case of the relative pronoun. They operate in separate grammatical jurisdictions.

Я дуже добре знаю цю молоду людину, яка зараз тут працює. У головній частині дієслово вимагає використання знахідного відмінка для об'єкта дії. Тому ми бачимо форму «людину». Але всередині підрядної частини займенник виконує роль активного підмета. Він самостійно виконує дію, тому він повинен стояти у називному відмінку. Ця граматична незалежність дозволяє будувати дуже складні та точні висловлювання.

:::info
**Grammar box**
Always analyze the relative clause in isolation to determine the case of its pronoun. Mentally extract the clause and replace the pronoun with the antecedent noun to see what case the internal verb demands. If the extracted sentence is "Я допоміг (кому?) студенту", then the relative pronoun must be in the Dative case: "якому".
:::

<!-- INJECT_ACTIVITY: match-up-terms -->
<!-- INJECT_ACTIVITY: fill-in-yakyj -->
<!-- INJECT_ACTIVITY: error-correction-yakyj -->

## Інші сполучні слова в означальних (~715 words total)

In addition to the relative pronoun **який/яка/яке/які** (which/that), Ukrainian frequently uses other words to connect clauses. The most common alternative is the **сполучне слово** (connective word) «що». It is a universal, uninflected connector that works beautifully for all genders, numbers, and cases, as long as there is no preposition involved. You will hear it constantly in everyday spoken Ukrainian, but it is also completely standard in literature, journalism, and poetry.

Займенник «що» зовсім не змінюється за родами чи числами, тому його надзвичайно зручно використовувати в розмові. Якщо ви раптом забули правильне закінчення для слова «який», ви часто можете просто сказати «що». Наприклад, речення «Книга, що лежить на столі» означає абсолютно те саме, що й «Книга, яка лежить на столі». Цей засіб зв'язку робить мовлення легшим, швидшим і дуже природним. Українські поети також дуже люблять це коротке слово. Відомий приклад із літератури: «Цей хліб, що світить на моїм столі...»

While «що» is incredibly useful for fluid communication, it has one strict grammatical limitation in relative clauses: it can never be used with prepositions. If the verb inside the subordinate clause requires a preposition, you must revert to using the fully declined form of «який».

Англомовні студенти дуже часто роблять помилку, коли перекладають свої думки дослівно. В англійській мові можна сказати "the city I live in", залишаючи прийменник у кінці речення. В українській мові прийменник завжди стоїть перед відносним займенником. Але ви не можете сказати «місто, в що я живу». Це груба граматична помилка, якої слід уникати. Правильний варіант завжди вимагає слова «який» у відповідному відмінку: «місто, в якому я живу». Так само, якщо ви говорите про дівчину, ви скажете «дівчина, про яку я розповідав», а не «про що я розповідав».

> *English-speaking students very often make a mistake when translating their thoughts literally. In English, you can say "the city I live in", leaving the preposition at the end of the sentence. In Ukrainian, the preposition always stands before the relative pronoun. But you cannot say "місто, в що я живу". This is a severe grammatical mistake that should be avoided. The correct variant always requires the word "який" in the appropriate case: "місто, в якому я живу". Similarly, if you are talking about a girl, you will say "дівчина, про яку я розповідав", and not "про що я розповідав".*

:::info
**Grammar box**
Remember the golden rule for prepositions: English sentences like "the person you are talking about" drop the relative pronoun and hide the preposition at the end. Ukrainian requires both to be explicit and paired together: «людина, **про яку** ти говориш». You can never use «що» in this specific slot.
:::

For relative clauses describing places or times, Ukrainian offers a more elegant solution than combining a preposition with «який». You can use relative adverbs such as «де» (where), «куди» (where to), «звідки» (where from), and «коли» (when) as connective words. This way, you do not need to calculate the correct **відмінок** (case) for the pronoun.

Ці слова роблять речення значно природнішими і менш перевантаженими складною граматикою. Замість того, щоб довго думати про правильне закінчення після прийменника, ви просто вказуєте на місце або час дії. Наприклад, замість важкої конструкції «Місто, в якому я живу» ви можете впевнено сказати «Місто, де я живу». Замість «Країна, в яку я їду» скажіть простіше: «Країна, куди я їду». Це правило чудово працює і для часу: «День, коли ми зустрілися» звучить набагато краще, ніж «День, в який ми зустрілися». Навіть у поезії ми постійно бачимо цю простоту: «дім, де зростають діти».

When an **означальне речення** (attributive clause) needs to express possession, you will use the relative pronoun «чий» (whose). This connective word behaves a bit differently from «який» because it must agree with the object that is possessed inside the clause, not with the **означуване слово** (antecedent) it refers back to.

Коли ви використовуєте слово «чий», воно працює як звичайний присвійний прикметник усередині підрядної частини. Розглянемо таке речення: «Людина, чию книгу я читаю, зараз живе у Києві». Тут головне слово — це «людина» (жіночий рід, називний відмінок). Але займенник «чию» стоїть у знахідному відмінку, тому що він узгоджується зі словом «книгу». Ви також можете сказати «Людина, книгу якої я читаю», але варіант із займенником «чий» є дуже точним, елегантним і часто вживаним у літературі.

Finally, you might encounter the word «котрий» (which). It functions as a formal literary synonym to «який» and follows the exact same declension patterns, but it requires caution in everyday use.

У сучасній українській мові слово «котрий» використовується значно рідше, ніж «який» або «що». Його часто можна побачити в класичній літературі, старих текстах або в офіційних документах. Однак ми наполегливо радимо не зловживати цим словом у щоденному спілкуванні. Надмірне використання слова «котрий» часто є прямим наслідком впливу російської мови, де аналогічне слово домінує в усіх стилях. Для красивої, сучасної та природної української мови набагато краще покладатися на слова «який» та «що».

<!-- INJECT_ACTIVITY: quiz -->

## Пунктуація та позиція (~660 words total)

Ukrainian punctuation has one very clear and unbreakable rule for attributive subordinate clauses. Regardless of where this clause stands, how long it is, or what words it contains, it is always separated by commas. If the clause stands inside the main sentence, you must place two commas: one at the beginning of the subordinate part, and another at the end. If it completes the thought at the end, only one comma is needed. Unlike a participial phrase, where position affects commas, an **означальне речення** (attributive clause) always requires them.

Це правило є обов'язковим і не має жодних винятків у сучасній літературній мові. Погляньмо на типовий приклад: «Місто, яке я відвідав, мене вразило». Тут головне речення — це «Місто мене вразило», а підрядна частина вставлена прямо всередину, тому ми ставимо дві коми. Якщо ж ми змінимо порядок слів, пунктуація залишиться такою ж суворою: «Мене вразило місто, яке я відвідав». Кома перед сполучним словом завжди сигналізує про початок нової граматичної основи.

While punctuation is straightforward, the physical position of the clause within the sentence requires careful attention. An attributive clause must always stand immediately after the **означуване слово** (antecedent — noun the clause describes) it describes. If you place other words between them, you risk creating a "dangling modifier" — a sentence that is logically confusing or even accidentally funny.

Розгляньмо класичну помилку, яку часто роблять студенти, коли забувають про правильну позицію підрядної частини. Уявіть таке речення: «Хлопець урятував дівчину від акули, з якою згодом одружився». Через те, що підрядна частина стоїть одразу після слова «акули», граматично виходить, що цей сміливий хлопець одружився саме з хижою рибою! Щоб уникнути такої нісенітниці, речення потрібно будувати інакше. Правильний варіант звучатиме так: «Хлопець, який урятував дівчину від акули, згодом із нею одружився».

> *Let's look at a classic mistake students often make when they forget about the correct position of the subordinate part. Imagine this sentence: "The boy saved the girl from the shark, whom he later married." Because the subordinate part stands immediately after the word "shark," grammatically it turns out that this brave boy married the predatory fish! To avoid such nonsense, the sentence must be built differently. The correct version will sound like this: "The boy, who saved the girl from the shark, later married her."*

As you become more comfortable with complex syntax, you will start building sentences that contain multiple subordinate clauses. Sometimes, one attributive clause will be nested inside another, creating a chain of descriptions. This happens when a word inside the first subordinate clause becomes the antecedent for a second subordinate clause. When stacking them, each distinct clause must be isolated by its own set of commas.

Складання таких синтаксичних ланцюжків нагадує традиційну матрьошку, де одна частина ховається в іншій. Погляньте на цей приклад: «Студент, який вивчає мову, яку я викладаю, отримав стипендію». Тут ми маємо дві різні підрядні частини, які виконують однакову функцію. Перша — «який вивчає мову» — пояснює слово «студент». Друга — «яку я викладаю» — пояснює слово «мову» і знаходиться всередині першої. Ми відокремлюємо комами кожну з них. Хоча такі конструкції є абсолютно правильними, намагайтеся не зловживати ними в усному мовленні, щоб не перевантажувати співрозмовника.

:::info
**Grammar box**
When stacking multiple attributive clauses, pay close attention to gender and number agreement. In the phrase «Студент, який вивчає мову, яку я викладаю», the relative pronoun **який/яка/яке/які** (which/that — relative pronoun, declines) appears twice in different forms. The first one is masculine singular to match «студент». The second one is feminine singular in the accusative case, matching «мову». The **відмінок** (case — determines the form of який in the clause) always depends on the word's function inside its own specific clause.
:::

Finally, there is a special type of construction called a pronoun-relative clause. In these sentences, the main clause does not contain a specific noun. Instead, the antecedent is a demonstrative or definitive pronoun such as «той» (that one) or «такий» (such). The clause is attached using a **сполучне слово** (connective word — який, що, де, куди, коли), and it very often stands before the main clause.

Ця структура створює особливий поетичний ритм, який ви часто почуєте в українських прислів'ях та класичній літературі. Наприклад, відомий вислів звучить так: «Хто не знає свого минулого, той не вартий свого майбутнього». Тут підрядна частина починається словом «хто» і повністю розкриває значення загального займенника «той» у другій частині. Інший гарний приклад: «Щасливий той чоловік, що немарно прожив свій вік». Зверніть увагу, що як сполучне слово тут виступає не тільки «який», а й «хто» або «що». Це дуже потужний інструмент для висловлення глибоких філософських думок.

<!-- INJECT_ACTIVITY: error-correction -->

## Практика: означальні у мовленні (~770 words total)

In everyday Ukrainian conversations, native speakers constantly rely on relative clauses to anchor their thoughts and provide spontaneous definitions. You do not always need to know the specific noun for an object; you can simply describe its function using an **означальне речення** (attributive/relative clause). Some high-frequency spoken patterns act as ready-made templates. Phrases like "Це людина, яка..." (This is a person who...), "Це місце, де..." (This is the place where...), and "Це час, коли..." (This is the time when...) are indispensable tools. They allow you to express complex opinions smoothly and provide essential context without stalling the conversation. The main rule here is to always correctly choose the **сполучне слово** (connective word — який, що, де, куди, коли) to link your ideas.

Коли ми забуваємо точну назву предмета, ми інтуїтивно використовуємо ці синтаксичні конструкції, щоб швидко пояснити свою думку. Наприклад, замість слова «кавоварка» ви можете просто сказати: «Це такий пристрій, який щоранку робить мені каву». Якщо ви хочете порадити друзям новий заклад, ви скажете: «Це те місце, де готують найкращу піцу в місті». Такі фрази роблять усне мовлення надзвичайно природним. Головне — логічно поєднувати обидві частини вашого висловлювання.

> *When we forget the exact name of an object, we intuitively use these syntactic constructions to quickly explain our thought. For example, instead of the word "coffee maker," you can simply say: "This is such a device that makes coffee for me every morning." If you want to recommend a new establishment to friends, you will say: "This is the place where they make the best pizza in the city." Such phrases make oral speech extremely natural. The main thing is to logically connect both parts of your statement.*

Let's look at how these descriptive patterns function in a casual dialogue. Notice how the speakers use clauses to share their impressions about a recent film and a vacation spot. Pay attention to how fluidly the clauses attach to the nouns they describe.

> — **Олена:** Ти вже бачив той новий фільм, який усі зараз так активно обговорюють? *(Have you already seen that new movie that everyone is discussing so actively right now?)*
> — **Марко:** Так, учора ходив у кінотеатр. Це фільм, який дійсно змушує глибоко задуматись про наше майбутнє. *(Yes, I went to the cinema yesterday. This is a movie that really makes you think deeply about our future.)*
> — **Олена:** А про що там сюжет? Це історія про людей, які шукають новий дім? *(And what is the plot about? Is it a story about people who are looking for a new home?)*
> — **Марко:** Саме так. Головні герої знаходять планету, де немає війн і конфліктів. Це дуже нагадує мені ту поїздку, про яку я тобі розповідав. *(Exactly. The main characters find a planet where there are no wars or conflicts. This really reminds me of that trip I told you about.)*
> — **Олена:** Ти маєш на увазі ті гори в Карпатах, куди ви їздили минулого літа? *(Do you mean those mountains in the Carpathians where you went last summer?)*
> — **Марко:** Правильно. Це було єдине місце, де я зміг повністю відключитися від роботи. Там був такий спокій, якого я ніколи раніше не відчував. *(Right. It was the only place where I could completely disconnect from work. There was such peace there that I had never felt before.)*
> — **Олена:** Звучить чудово. Мені теж потрібна відпустка, що допоможе зняти стрес. *(Sounds wonderful. I also need a vacation that will help relieve stress.)*

Now it is your turn to put these structures into practice. One of the best ways to internalize complex syntax is to connect it to your own life. Your task is to write five original sentences describing people, places, or things that are meaningful to you. To ensure you are truly mastering the grammar, you must use **який/яка/яке/які** (which/that — relative pronoun, declines) in a different **відмінок** (case — determines the form of який in the clause) for each of your descriptions. You must also ensure that the **означуване слово** (antecedent — noun the clause describes) correctly dictates the gender and number.

Почніть із простого опису людини. Наприклад, згадайте друга, якому ви завжди можете довіряти, або колегу, з яким ви працюєте. Потім опишіть улюблену річ: це може бути книга, яку ви зараз читаєте. Ваше завдання — уважно стежити за тим, щоб іменник у головній частині правильно визначав рід та число займенника. Не забувайте, що відмінок залежить виключно від того, яку функцію виконує займенник усередині підрядної частини.

> *Start with a simple description of a person. For example, recall a friend whom you can always trust, or a colleague with whom you work. Then describe a favorite thing: it can be a book that you are currently reading. Your task is to carefully ensure that the noun in the main part correctly determines the gender and number of the pronoun. Do not forget that the case depends solely on what function the pronoun performs inside the subordinate clause.*

To fully appreciate the natural rhythm of spoken Ukrainian, you will also complete a transformation exercise. In formal writing, you will often encounter dense participle phrases that sound heavy in casual conversation. Your final task is to take five formal sentences containing these phrases and rewrite them into flowing attributive clauses.

:::tip
**Did you know?**
Native speakers heavily favor relative clauses over participle phrases in daily speech. Using "який" instead of a formal participle makes your Ukrainian sound instantly more authentic and approachable.
:::

Коли ви перетворюєте дієприкметниковий зворот на звичайне підрядне речення, ви робите свою мову живою та зрозумілою для носіїв. Наприклад, замість офіційного «лист, надісланий учора» ви скажете значно простіше: «лист, який надіслали вчора». Ця корисна навичка дозволить вам легко адаптувати складні академічні тексти для повсякденного спілкування, зберігаючи при цьому точність висловлювання.

> *When you transform a participle phrase into a regular subordinate clause, you make your language lively and understandable for native speakers. For example, instead of the official "the letter sent yesterday," you will say much more simply: "the letter that was sent yesterday." This useful skill will allow you to easily adapt complex academic texts for everyday communication, while preserving the accuracy of the statement.*

<!-- INJECT_ACTIVITY: essay-yakyj-cases --> [essay-response, "Напишіть 5 речень, використовуючи нову лексику з розділу «Який у різних відмінках».", 5 items]

## Що вивчають синтаксис і пунктуація?

Since the very first lesson, you have been building Ukrainian sentences. When you say "Я живу в Києві" instead of "Я жити Київ", you are already using syntax correctly. You instinctively know how to connect words, change noun endings, and match verbs to their subjects. Now, it is time to learn how to consciously name and analyze these structures.

Ми змінюємо наш підхід до граматики. Раніше ми говорили про "subject" та "object" англійською мовою. Тепер ми будемо використовувати українські терміни: **підмет** (subject) та **додаток** (object). Ви дізнаєтеся, як називається **просте речення** (simple sentence) і **складне речення** (complex sentence). Ми також вивчимо два нові слова: **синтаксис** (syntax) і **пунктуація** (punctuation).

> *We are changing our approach to grammar. Previously, we talked about "subject" and "object" in English. Now we will use the Ukrainian terms: subject and object. You will learn what a simple sentence and a complex sentence are called. We will also learn two new words: syntax and punctuation.*

Let's start with the first term, which comes from the Greek word "syntaxis". This ancient word means "building" or "connection". In linguistics, it is the study of how individual words connect to build complex, meaningful thoughts rather than just random lists of isolated vocabulary.

Синтаксис — це великий розділ мовознавства. Він вивчає **словосполучення** (word combination) і речення. Це не просто випадковий набір слів. Це справжні будівельні блоки нашої думки. Словосполучення показує граматичний зв'язок між двома словами. Речення завжди виражає закінчену та повністю зрозумілу думку.

While syntax provides the invisible structural skeleton of a sentence, the second term provides the visible road signs. The word "punctuation" comes from the Latin "punctum", meaning "a point". Without it, readers would easily get lost in long sentences and misunderstand your tone.

Пунктуація — це важливий розділ науки про мову. Вона вивчає правила вживання розділових знаків. Коли ви пишете текст, ви ставите крапки, коми, знаки питання або тире. Ці знаки допомагають читачу правильно розуміти вашу інтонацію та логіку. Без пунктуації синтаксичний скелет речення може бути абсолютно незрозумілим. Наприклад, одна маленька кома може повністю змінити значення фрази.

:::info
**Граматична гармонія**
Синтаксис і пунктуація завжди працюють разом. Синтаксис будує невидиму структуру речення, а пунктуація показує цю структуру на письмі.
:::

Why is this "metalanguage bridge" so vital for your progress right now? From the B1 level onwards, your learning materials will shift towards full Ukrainian immersion. Grammar rules, textbook explanations, and dictionary entries will be written entirely in Ukrainian, using native linguistic terminology. Dictionary literacy depends entirely on your ability to read and process these syntactic labels.

Українські словники завжди використовують спеціальну граматичну термінологію. Наприклад, нове правило може казати: "після цього дієслова потрібен додаток у родовому відмінку". Щоб зрозуміти цю коротку інструкцію, ви повинні знати ці слова. Ви маєте знати ці два терміни: додаток і **родовий відмінок** (genitive case). Це ваша базова словникова грамотність.

> *Ukrainian dictionaries always use special grammatical terminology. For example, a new rule might say: "after this verb, an object in the genitive case is needed". To understand this short instruction, you must know these words. You must know these two terms: object and genitive case. This is your basic dictionary literacy.*

Цей модуль — ваш надійний ключ до української граматики. Тут ми детально систематизуємо всі ваші практичні знання. Ви вивчите українські назви для всіх граматичних структур, які ви вже вмієте самостійно будувати. Наступні рівні обов哴 вимагають цього професійного словника. Ми будемо часто аналізувати тексти разом. Ви вже повністю готові до цього важливого кроку.

## Словосполучення (~550 words)

When you communicate, you rarely use single, isolated words. Words alone are not enough to build a complete sentence. We need to connect them logically. In Ukrainian grammar, when we connect two or more words by meaning and grammar, we create a **словосполучення** (word combination — two+ words linked by meaning and grammar). It is the first critical step in building complex thoughts and expressing yourself clearly.

Що таке словосполучення? Це поєднання двох або більше слів. Ці слова пов'язані за змістом і граматично. Наприклад: «осіннє небо», «читати книжку» або «дуже швидко». Це не просто набір слів, як-от «небо, читати, дуже». Це логічна і граматична єдність.

> *What is a word combination? It is a combination of two or more words. These words are connected by meaning and grammatically. For example: "autumn sky", "to read a book", or "very quickly". It is not just a set of words, like "sky, to read, very". It is a logical and grammatical unity.*

Every phrase has a clear internal hierarchy that determines how endings change. One word acts as the boss, and the other word follows its grammatical orders. We call these the **головне слово** (main word) and the **залежне слово** (dependent word). Understanding this relationship is the secret to mastering Ukrainian cases.

У кожному словосполученні є головне слово і залежне слово. Головне слово завжди керує залежним. Ми ставимо питання від головного слова до залежного. Наприклад, у фразі «осіннє небо» головне слово — «небо». Небо (яке?) осіннє. У фразі «читати книжку» головне слово — «читати». Читати (що?) книжку. Напрямок завжди один: від головного до залежного.

> *In every word combination, there is a main word and a dependent word. The main word always controls the dependent one. We ask a question from the main word to the dependent word. For example, in the phrase "autumn sky", the main word is "sky". Sky (what kind?) autumn. In the phrase "to read a book", the main word is "to read". To read (what?) a book. The direction is always one: from the main to the dependent one.*

:::info
**Стрілка питання**
Завжди малюйте уявну стрілку від головного слова до залежного. Це чудово допомагає зрозуміти логіку української граматики та правильно змінювати закінчення залежних слів.
:::

It is equally important to know what does NOT count as a phrase in Ukrainian syntax. There are two major exceptions that you must remember for future grammatical analysis. First, the **підмет** (subject — main sentence member naming who/what acts) and the **присудок** (predicate — main sentence member naming the action/state) never form a phrase together. Second, a noun with a preposition is not considered an independent phrase.

Підмет і присудок ніколи не утворюють словосполучення. Це граматична основа речення, самостійна структура. Слова з прийменниками також не є словосполученнями. Наприклад, «на столі» або «перед будинком». Це слово та його службовий елемент, вони є частиною більшого речення.

> *The subject and the predicate never form a word combination. This is the grammatical core of the sentence, an independent structure. Words with prepositions are also not word combinations. For example, "on the table" or "in front of the house". This is a word and its auxiliary element, they are a part of a larger sentence.*

Let's see exactly how this theoretical knowledge works in practice. A tutor and a student are analyzing a simple sentence together to find the hidden phrases inside it.

> — **Репетитор:** Прочитай це речення: «Старий ліс тихо шелестить». *(Read this sentence: "The old forest rustles quietly".)*
> — **Студент:** Добре. Де тут словосполучення? *(Okay. Where are the word combinations here?)*
> — **Репетитор:** Спочатку знайдемо граматичну основу. Що робить дію? *(First, let's find the grammatical core. What is doing the action?)*
> — **Студент:** Ліс шелестить. *(The forest rustles.)*
> — **Репетитор:** Правильно. «Ліс» — це підмет, а «шелестить» — це присудок. Це не словосполучення. *(Correct. "Forest" is the subject, and "rustles" is the predicate. This is not a word combination.)*
> — **Студент:** Тоді які слова залежать від них? *(Then which words depend on them?)*
> — **Репетитор:** Від підмета «ліс» залежить слово «старий». Ліс (який?) старий. Це перше словосполучення. *(The word "old" depends on the subject "forest". Forest (what kind?) old. This is the first word combination.)*
> — **Студент:** А від присудка «шелестить» залежить «тихо»! Шелестить (як?) тихо. Це друге словосполучення! *(And "quietly" depends on the predicate "rustles"! Rustles (how?) quietly. This is the second word combination!)*
> — **Репетитор:** Чудово! Ти знайшов два словосполучення. *(Excellent! You found two word combinations.)*

<!-- INJECT_ACTIVITY: mark-phrase-parts -->

## Граматична основа: підмет і присудок (~650 words)

Every sentence has an energy center around which all other words revolve. This center is called the **граматична основа** (grammatical core — підмет + присудок together). Without it, a sentence simply cannot exist, because it carries the main meaning.

Кожне речення має свій енергетичний центр, навколо якого обертаються всі інші слова. Цей центр називається граматична основа. Без неї речення просто не може існувати, бо саме вона несе головний зміст. Вона показує, про кого або про що ми говоримо. Граматична основа складається з двох найголовніших членів: підмета та присудка. Разом вони створюють закінчену думку, навіть якщо в реченні немає інших слів. Наприклад, у реченні «Сонце яскраво світить» слова «сонце» і «світить» — це наша основа. Вони рівноправні і дуже тісно залежать одне від одного.

The first main member of the sentence is the **підмет** (subject — main sentence member naming who/what acts). You can think of it as the main hero or the central character of our grammatical story. This hero usually stands in the **називний відмінок** (nominative case — хто? що?).

Підмет — це головний член речення, який називає особу, предмет або явище. Щоб знайти підмет, ми завжди ставимо питання: «хто?» або «що?». Цей головний герой завжди стоїть у початковій формі. У граматиці ця форма називається називний відмінок. Коли українські школярі роблять синтаксичний розбір речення, вони використовують лінію. Вони завжди підкреслюють підмет однією суцільною лінією. Наприклад, у реченні «Студент уважно читає» слово «студент» відповідає на питання «хто?». Саме це слово і є нашим підметом.

> *The subject is the main member of the sentence, which names the person, object, or phenomenon. To find the subject, we always ask the question: "who?" or "what?". This main hero always stands in its initial form. In grammar, this form is called the nominative case. When Ukrainian schoolchildren do a syntactic analysis of a sentence, they use a line. They always underline the subject with one solid line. For example, in the sentence "The student reads attentively", the word "student" answers the question "who?". This very word is our subject.*

The second essential half of our core is the **присудок** (predicate — main sentence member naming the action/state). If the subject is the hero, the predicate tells us exactly what this hero is doing, what is happening to them, or what they are like.

Присудок — це другий головний член речення, який означає дію, стан або ознаку. Він тісно пов'язаний із підметом і відповідає на питання «що робить?». Також він може відповідати на питання «який він є?» або «хто він такий?». Найчастіше роль присудка бере на себе дієслово. Його завжди підкреслюють двома суцільними лініями. Подивимося на попередній приклад ще раз. Студент (що робить?) читає. Слово «читає» — це дія нашого героя, тому це присудок. Або візьмемо інше речення: книга (що робить?) лежить. Слово «лежить» показує стан предмета, тому це також присудок.

Sometimes, the predicate is not an action verb at all. When you want to say that one thing *is* another thing, like "Kyiv is the capital", you use a special rule of **пунктуація** (punctuation — rules for using punctuation marks) instead of the verb "to be".

Коли підмет і присудок виражені іменниками в називному відмінку, ми пропускаємо дієслово-зв'язку. Замість дієслова ми ставимо тире між цими двома словами. Тире працює як місток, який поєднує два поняття і показує їхню тотожність. Розглянемо класичні приклади: «Київ — столиця України» або «Життя — це великий виклик». У першому реченні «Київ» (що?) — це підмет, а «столиця» (що це таке?) — присудок. Обидва слова є іменниками в початвному відмінку, тому між ними стоїть тире.

> *When the subject and the predicate are expressed by nouns in the nominative case, we skip the linking verb. Instead of a verb, we put a dash between these two words. The dash works like a bridge that connects two concepts and shows their identity. Let's look at classic examples: "Kyiv is the capital of Ukraine" or "Life is a great challenge". In the first sentence, "Kyiv" (what?) is the subject, and "capital" (what is it?) is the predicate. Both words are nouns in the initial form, so there is a dash between them.*

:::info
**Місток тотожності**
Якщо ви можете вставити між двома іменниками слово «це» або «є», вам обов'язково потрібно поставити тире на письмі. Наприклад: «Мій брат — лікар».
:::

Finding the grammatical core might seem easy when sentences are short. But when sentences grow longer and word order changes, you need a reliable diagnostic method to find the true "doer" of the action.

Щоб правильно знайти граматичну основу, ви завжди повинні питати себе одну річ. Хто чи що насправді виконує дію в цьому конкретному реченні? Не дивіться лише на порядок слів, дивіться на логіку та закінчення. Порівняймо два цікаві речення. Перше: «Вітер хилить високі клени». Знайдемо основу. Хто виконує дію? Вітер (що робить?) хилить. Отже, «вітер» — це підмет, а «хилить» — присудок. Друге речення: «Високі клени хиляться від вітру». Що виконує дію тут? Тут клени (що роблять?) хиляться. У цьому випадку саме «клени» є підметом, а «хиляться» — присудок. Одне й те саме слово може бути різним членом речення.

<!-- INJECT_ACTIVITY: find-grammatical-core -->

## Другорядні члени речення (~700 words)

In **синтаксис** (syntax — the study of sentence structure), the grammatical core is just the foundation. A **просте речення** (simple sentence — sentence with one grammatical core) might only contain a subject and a predicate, like "I am reading". This sentence is perfectly correct, but it lacks detail. If we want to express complex thoughts, or if we want to build a **складне речення** (complex sentence — sentence with two+ grammatical cores), we need more tools. To make speech informative and rich, we use secondary sentence members. They expand the core by adding descriptions, objects, and context.

Головні члени речення — це лише фундамент. Усі інші слова в реченні називаються другорядними членами. Вони залежать від головних слів або від інших другорядних членів. В українській мові є три види таких членів: додаток, означення та обставина. Кожен з них має свою важливу функцію. Кожен відповідає на свої власні питання. Завдяки їм ми можемо сказати: «Я уважно читаю цікаву книгу вдома».

> *The main sentence members are just the foundation. All other words in a sentence are called secondary members. They depend on the main words or on other secondary members. In the Ukrainian language, there are three types of such members: the object, the attribute, and the adverbial modifier. Each of them has its own important function. Each answers its own specific questions. Thanks to them we can say: "I am carefully reading an interesting book at home."*

The core members use the **називний відмінок** (nominative case — хто? що?). But secondary members use the indirect cases. The first secondary member is the **додаток** (object — secondary member answering indirect case questions). It denotes an object that is affected by an action or is related to it. The object is your main tool for interacting with the world.

Додаток — це другорядний член речення, який називає предмет. Він завжди відповідає на питання непрямих відмінків. Це всі відмінки, крім називного. Додаток відповідає на питання «кого?», «чого?» (це родовий відмінок). Він відповідає на питання «кому?», «чому?» (це давальний відмінок). Також він відповідає на питання «кого?», «що?» (це знахідний відмінок). Він використовує питання «ким?», «чим?» (це орудний відмінок). Останні питання — «на кому?», «на чому?» (це місцевий відмінок). Під час розбору ми підкреслюємо додаток пунктирною лінією.

> *The object is a secondary sentence member that names an item. It always answers the questions of the indirect cases. These are all the cases except the nominative. The object answers the questions "whom?", "of what?" (this is the genitive case). It answers the questions "to whom?", "to what?" (this is the dative case). It also answers the questions "whom?", "what?" (this is the accusative case). It uses the questions "by whom?", "with what?" (this is the instrumental case). The last questions are "on whom?", "on what?" (this is the locative case). During parsing, we underline the object with a dashed line.*

Розглянемо красиве українське речення: «Даруйте людям радість». Тут ми можемо знайти два додатки. Даруйте (кому?) — людям. Це додаток у давальному відмінку. Даруйте (що?) — радість. Це прямий додаток у знахідному відмінку. Обидва ці слова ми підкреслюємо пунктиром: - - - -.

Next, we have the **означення** (attribute — secondary member answering який? чий?). This is the sentence member that brings color and detail to your nouns. An attribute and the noun it describes naturally form a **словосполучення** (word combination — two+ words linked by meaning and grammar).

Означення — це другорядний член речення, який вказує на ознаку предмета. Воно описує якості, властивості або належність. Означення відповідає на питання «який?», «яка?», «яке?», «які?». Також воно відповідає на питання «чий?», «чия?», «чиє?», «чиї?». Зазвичай означення виражене прикметником або займенником. Ми підкреслюємо цей член речення хвилястою лінією.

> *The attribute is a secondary sentence member that indicates a characteristic of an item. It describes qualities, properties, or belonging. The attribute answers the questions "which?" ("what kind of?"). It also answers the questions "whose?". Usually, the attribute is expressed by an adjective or a pronoun. We underline this sentence member with a wavy line.*

Розглянемо простий приклад: «Наш двір прикрашає лелече гніздо». Тут є два означення. Двір (чий?) — наш. Гніздо (яке?) — лелече. Ці слова роблять речення дуже конкретним і мальовничим. У зошиті ми малюємо хвилясту лінію під словами «наш» і «лелече»: ~~~~~~.

:::info
**Grammar box**
Remember that an attribute always depends on a noun. Wherever the noun goes, the attribute follows it, completely agreeing with the noun in gender, number, and case! Proper **пунктуація** (punctuation — rules for using punctuation marks) is usually not required between an attribute and its noun.
:::

Finally, we need to provide context for the action. Where did it happen? When? How? Why? This is the job of the **обставина** (adverbial — secondary member answering як? де? коли?). Adverbials set the scene for the action and are incredibly versatile.

Обставина — це другорядний член речення, який називає спосіб, місце, час або причину дії. Цей член речення найчастіше залежить від дієслова. Обставина відповідає на питання «як?», «де?», «куди?», «звідки?», «коли?», «чому?», «навіщо?». Часто роль обставини грає прислівник або іменник із прийменником. Ми підкреслюємо обставину пунктиром з крапкою.

> *The adverbial modifier is a secondary sentence member that names the manner, place, time, or reason of an action. This sentence member most often depends on the verb. The adverbial answers the questions "how?", "where?", "to where?", "from where?", "when?", "why?", "what for?". Often, the role of an adverbial is played by an adverb or a noun with a preposition. We underline the adverbial with a dash-dot line.*

Візьмемо таке речення: «Улітку гриби краще шукати в затінку дерев». Шукати (коли?) — улітку. Це обставина часу. Шукати (як?) — краще. Це обставина способу дії. Шукати (де?) — в затінку. Це обставина місця. Усі ці слова ми підкреслюємо так: -.-.-.-. Завдяки обставинам ми розуміємо всі деталі.

Now let's perform a complete syntactic parsing of a sentence. In Ukrainian schools, this is called «синтаксичний розбір». It means we find the **підмет** (subject — main sentence member naming who/what acts) and the **присудок** (predicate — main sentence member naming the action/state) first, and then identify every secondary member by asking the right questions. Our sentence is: «Веселі діти голосно співали пісню на вулиці.»

Спочатку шукаємо граматичну основу. Хто виконує дію? Діти (що робили?) співали. «Діти» — це підмет, «співали» — присудок. Тепер ставимо питання до інших слів. Діти (які?) — веселі. Це означення, підкреслюємо хвилястою лінією. Співали (як?) — голосно. Це обставина способу дії, підкреслюємо пунктиром з крапкою. Співали (кого? що?) — пісню. Це додаток, підкреслюємо пунктирною лінією. Співали (де?) — на вулиці. Це обставина місця, підкреслюємо пунктиром з крапкою.

> *First, we look for the grammatical core. Who performs the action? The children (did what?) sang. "Children" is the subject, "sang" is the predicate. Now we ask questions to the other words. Children (what kind?) — cheerful. This is an attribute, we underline it with a wavy line. Sang (how?) — loudly. This is an adverbial modifier of manner, we underline it with a dash-dot line. Sang (whom? what?) — a song. This is an object, we underline it with a dashed line. Sang (where?) — on the street. This is an adverbial modifier of place, we underline it with a dash-dot line.*

<!-- INJECT_ACTIVITY: quiz-sentence-members -->

## Складне речення (~550 words)

До цього моменту ми працювали з реченнями, які мають лише одну граматичну основу. Таке речення називається **просте речення** (simple sentence). Але в житті ми часто об'єднуємо кілька думок у спільне висловлювання. Речення, яке має дві або більше граматичних основ, — це **складне речення** (complex sentence). Кожна частина складного речення має свій підмет і свій присудок. Вони можуть існувати як окремі прості речення, але разом вони створюють ширший контекст. Розгляньмо приклад: «Сонце зайшло, і на небі з'явилися зорі». Перша граматична основа — «сонце зайшло». Друга граматична основа — «зорі з'явилися». Це типове складне речення.

> *Up to this point, we have worked with sentences that have only one grammatical core. Such a sentence is called a simple sentence. But in life, we often combine several thoughts into a shared statement. A sentence that has two or more grammatical cores is a complex sentence. Each part of a complex sentence has its own subject and its own predicate. They could exist as separate simple sentences, but together they create a broader context. Let's consider an example: "The sun set, and stars appeared in the sky." The first grammatical core is "the sun set." The second grammatical core is "stars appeared." This is a typical complex sentence.*

How exactly do we glue these parts together? In Ukrainian syntax, there are two main types of connection between the clauses of a complex sentence.

Перший тип — це **безсполучниковий зв'язок** (asyndetic connection). Частини речення поєднуються лише за допомогою інтонації та розділових знаків, без додаткових слів. Наприклад: «Настала осінь, птахи полетіли на південь». Тут є дві основи, але немає слів, які їх склеюють. Другий тип — це **сполучниковий зв'язок** (syndetic connection). Тут ми використовуємо спеціальні слова, які об'єднують частини в одне ціле. Наприклад: «Настала осінь, тому птахи полетіли на південь».

> *The first type is an asyndetic connection. The parts of the sentence are joined only by means of intonation and punctuation marks, without additional words. For example: "Autumn came, the birds flew south." Here there are two cores, but no words gluing them together. The second type is a syndetic connection. Here we use special words that unite the parts into a single whole. For example: "Autumn came, therefore the birds flew south."*

The special words used in a syndetic connection are called conjunctions. They act as the syntactic glue that holds your complex thoughts together, showing the logical relationship between the clauses.

В українській мові є різні групи таких слів. Єднальні сполучники, такі як «і» або «та», просто додають одну інформацію до іншої. Протиставні сполучники, такі як «але» або «проте», показують контраст. Існують також підрядні сполучники, наприклад «що», «бо», «тому що». Вони показують, що одна частина речення повністю залежить від іншої, пояснює причину або мету. Ви будете дуже часто використовувати ці слова, коли почнете будувати великі тексти.

> *In the Ukrainian language, there are different groups of such words. Copulative conjunctions, such as "and", simply add one piece of information to another. Adversative conjunctions, such as "but" or "however", show contrast. There are also subordinating conjunctions, for example "that", "because", "for the reason that". They show that one part of the sentence completely depends on another, explaining the reason or purpose. You will use these words very often when you start building large texts.*

This brings us to a crucial difference between English and Ukrainian grammar rules. In English, you often do not put a comma before "and" unless joining two independent clauses, and the rules can be quite flexible. In Ukrainian, there is a strict and almost universal "Golden Comma Rule" for complex sentences.

Ви завжди повинні ставити кому між частинами складного речення. Ця кома показує межу, де закінчується перша граматична основа і починається друга. Ви ставите кому навіть тоді, коли частини з'єднані сполучником «і». Англійською мовою ми можемо написати: «I read a book and he watched a movie» без коми. Українською ми обов'язково пишемо: «Я читав книгу, і він дивився фільм». Ця кома є абсолютно необхідною для правильної пунктуації.

> *You must always put a comma between the parts of a complex sentence. This comma shows the boundary where the first grammatical core ends and the second begins. You put a comma even when the parts are connected by the conjunction "and". In English, we might write: "I read a book and he watched a movie" without a comma. In Ukrainian, we obligatorily write it: "I read a book, and he watched a movie." This comma is absolutely necessary for correct punctuation.*

:::info
**Grammar box**
This comma rule is one of the most frequent punctuation mistakes made by learners at the B1 level. Train your eye to spot the two grammatical cores. If you see a subject and predicate on the left, and a new subject and predicate on the right, you MUST place a comma between them, regardless of what conjunction links them.
:::

<!-- INJECT_ACTIVITY: simple-vs-complex-sort -->
<!-- INJECT_ACTIVITY: fix-complex-punctuation -->

## Відмінки: система і питання (~650 words)

You already know that Ukrainian words change their endings to show their role in a sentence. These roles—like being the subject, the direct object, or the location—are assigned by the case system. In Ukrainian, we call these cases «відмінки». There are seven cases in total, and they are the most important tools in the language.

Щоб запам'ятати всі сім відмінків, українські школярі вчать спеціальне речення. Кожне слово в ньому починається з першої літери назви відмінка. Це речення звучить так: «Наша Рая Добре Знає Оцю Мову Калинову». Перші літери допомагають згадати правильний порядок. Ця проста фраза дуже допомагає на уроках мови.

> *To remember all seven cases, Ukrainian schoolchildren learn a special sentence. Every word in it starts with the first letter of the case name. This sentence sounds like this: "Our Raya Knows This Viburnum Language Well." The first letters help to recall the correct order. This simple phrase helps a lot in language lessons.*

Let us look at the complete system. Every case has a specific name, a standard abbreviation, and a pair of diagnostic questions. These questions are your key to understanding how sentences are built.

Перший — це **називний відмінок** (Н.в.). Він відповідає на питання «хто? що?».
Другий — це **родовий відмінок** (Р.в.), який має питання «кого? чого?».
Третій — це **давальний відмінок** (Д.в.) з питаннями «кому? чому?».
Четвертий — це **знахідний відмінок** (Зн.в.). Його питання — «кого? що?».
П'ятий — це **орудний відмінок** (О.в.), який відповідає на питання «ким? чим?».
Шостий — це **місцевий відмінок** (М.в.). Він завжди має прийменник і питання «на кому? на чому?».
Сьомий — це кличний відмінок (Кл.в.). Він не має питань, бо це форма звертання.

> *The first is the nominative case (Н.в.). It answers the questions "who? what?". The second is the genitive case (Р.в.), which has the questions "of whom? of what?". The third is the dative case (Д.в.) with the questions "to whom? to what?". The fourth is the accusative case (Зн.в.). Its questions are "whom? what?". The fifth is the instrumental case (О.в.), which answers the questions "by whom? by/with what?". The sixth is the locative case (М.в.). It always has a preposition and the questions "on whom? on what?". The seventh is the vocative case (Кл.в.). It has no questions because it is a form of address.*

You do not need to guess the case of a noun in a sentence. You can always find it by using the diagnostic questions. You simply find the main word (usually the verb) and throw the question to the dependent word. The question you use determines the case.

Давайте подивимося на приклади. Я бачу цікаву книжку. Я бачу (кого? що?) книжку. Це питання знахідного відмінка. А тепер інший приклад. Я пишу новим олівцем. Я пишу (ким? чим?) олівцем. Тут ми маємо орудний відмінок. Питання завжди показує правильну форму слова. Ви повинні ставити питання від головного слова до залежного.

:::info
**Grammar box**
This method of "throwing the question" is exactly how Ukrainian children learn to analyze sentences in primary school. If you memorize the pairs of questions (хто/що, кого/чого, etc.), you will always know which case to use.
:::

Why do you need to know these formal names and abbreviations? Because they are the "user manual" for Ukrainian grammar. When you open a Ukrainian dictionary or read a grammar rule, you will not see English explanations. You will see these exact terms.

Усі словники використовують ці скорочення. Якщо ви шукаєте дієслово «дякувати», словник покаже спеціальне правило. Ви побачите текст: «дякувати (кому? чому?) Д.в.». Це означає, що після цього слова потрібен давальний відмінок. Якщо ви знаєте систему відмінків, ви можете читати українські підручники. Ви зможете розуміти правила без перекладу англійською мовою. Це ваш ключ до успішного навчання.

<!-- INJECT_ACTIVITY: match-cases-to-questions -->
<!-- INJECT_ACTIVITY: determine-word-case -->

## Підсумок та перехід до M69

You have successfully reached the end of the metalanguage bridge. This is a major milestone in your language journey. We have moved away from simply memorizing individual words and basic phrases. You are now learning the underlying system of the language. You understand how **синтаксис** (syntax) and **пунктуація** (punctuation) work together to create clear meaning. You can identify a **словосполучення** (word combination) and see exactly how words connect to each other. This analytical skill is crucial for your future progress.

Every sentence you build has a grammatical core that drives its meaning. The main members are the **підмет** (subject) and the **присудок** (predicate). These two elements form the foundation of any statement. Without them, a sentence cannot express a complete thought. 

Of course, sentences are rarely just two words long. Secondary members add important details and context to your speech. These include the **додаток** (object), the **означення** (attribute), and the **обставина** (adverbial). Together, they enrich your communication and make your stories much more interesting. 

Sentences can also vary greatly in their length and structure. You now clearly know the difference between a **просте речення** (simple sentence) and a **складне речення** (complex sentence). This distinction helps you read longer texts without getting lost in the structure. 

To connect all these words correctly, you must use the system of cases. The **називний відмінок** (nominative case) and **родовий відмінок** (genitive case) are fundamental tools for naming and showing possession. The **давальний відмінок** (dative case) shows the recipient of an action, which is vital for daily interactions.

The other cases describe the specific circumstances of actions and locations. The **знахідний відмінок** (accusative case) marks the direct object, making your verbs effective. Finally, the **орудний відмінок** (instrumental case) and **місцевий відмінок** (locative case) provide further context about tools, accompaniment, and physical spaces.

Зараз чудовий час для самоперевірки. Спробуйте відповісти на ці запитання без словника. Що таке граматична основа речення? Назвіть три другорядні члени речення та їхні питання. Чим просте речення відрізняється від складного? Назвіть сім відмінків і їхні питання. Визначте підмет і присудок у реченні: «Сьогодні я отримав цікавий лист». Якщо ви можете відповісти на все, ви готові до наступного етапу.

> *Now is a great time for a self-check. Try to answer these questions without a dictionary. What is the grammatical core of a sentence? Name the three secondary sentence members and their questions. How does a simple sentence differ from a complex one? Name the seven cases and their questions. Identify the subject and the predicate in the sentence: "Today I received an interesting letter". If you can answer everything, you are ready for the next stage.*

:::note
**Quick tip**
If you can answer all the self-check questions easily, you have a solid foundation for the next level. If you feel unsure about any terms, review the previous sections of this module before moving on.
:::

This concludes our dedicated focus on the structural vocabulary of the language. When you start M69, you will experience a significant transition toward full Ukrainian immersion. You now possess the exact grammatical labels needed to understand complex discussions directly in Ukrainian. When a dictionary or a teacher mentions a specific case or sentence member, you will know exactly what they mean. You will no longer need English translations to decipher a grammar rule. The journey from simply asking "how to say it" to truly understanding "how it works" is truly beginning. Your ability to analyze and construct sentences will grow exponentially from this point forward.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: complex-subordinate-relative
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

**Level: B1 (Module 77)**

**Instructions in Ukrainian.** All activity types appropriate.


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
