<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/plural-other-cases.yaml` file for module **34: З друзями, для дітей** (a2).

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

- focus: Put the noun into the correct plural case (Dat., Instr., or Loc.) based on
    the preposition or verb in the sentence
  items: 8
  type: fill-in
- focus: Match plural noun forms with the correct case label (Dat., Instr., Loc.)
  items: 8
  type: match-up
- focus: Choose the correct preposition + plural case combination to complete a sentence
  items: 8
  type: quiz
- focus: Fix incorrect case endings in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- радити (to advise)
- пояснювати (to explain)
- полиця (shelf)
- прикрашати (to decorate)
required:
- давальний відмінок (dative case)
- орудний відмінок (instrumental case)
- місцевий відмінок (locative case)
- допомагати (to help)
- дякувати (to thank)
- подарунок (gift)
- квіти (flowers)
- діти (children)
- люди (people)
- заняття (class, lesson)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Давальний множини: Кому?

Давальний відмінок множини — це найпростіше правило в українській мові. *(The Dative plural is the simplest rule in the Ukrainian language.)* Ви вже знаєте, що цей відмінок відповідає на питання **кому?** *(to whom?)* або **чому?** *(to what?)*. The Dative plural is incredibly "grateful" for learners because it is extremely regular across all noun types. Усі слова мають лише два можливі закінчення. *(All words have only two possible endings.)* Ми додаємо закінчення **-ам** *(to -am)* до твердих основ. *(We add the ending -am to hard stems.)* Наприклад, ви кажете: студенти — **студентам** *(to students)*, столи — **столам** *(to tables)*, вікна — **вікнам** *(to windows)*. Ми додаємо закінчення **-ям** *(to -yam)* до м'яких основ та слів, які закінчуються на -ь або -я. *(We add the ending -yam to soft stems and words that end in -ь or -я.)* Наприклад, ви кажете: друзі — **друзям** *(to friends)*, пісні — **пісням** *(to songs)*, знання — **знанням** *(to knowledge)*. Це дуже легке правило, яке працює завжди. *(This is a very easy rule that always works.)*

Ви щойно вивчили родовий відмінок множини. *(You just learned the Genitive plural.)* Там було багато складних правил та винятків. *(There were many complex rules and exceptions there.)* У родовому відмінку рід слова має велике значення. *(In the Genitive case, the gender of the word matters a lot.)* Але давальний відмінок множини зовсім інший. *(But the Dative plural is completely different.)* In the Dative plural, grammatical gender effectively disappears as a variable for choosing the ending. You do not need to remember if a word is masculine, feminine, or neuter. Ви просто дивитесь на останній приголосний звук основи. *(You simply look at the last consonant sound of the stem.)* Якщо він твердий, ви пишете **-ам**. *(If it is hard, you write -am.)* Якщо він м'який, ви пишете **-ям**. *(If it is soft, you write -yam.)* Це робить давальний відмінок множини дуже зручним для спілкування. *(This makes the Dative plural very convenient for communication.)*

Давальний відмінок часто показує напрямок дії. *(The Dative case often shows the direction of an action.)* Ми використовуємо його з дієсловами спілкування та взаємодії. *(We use it with verbs of communication and interaction.)* Найпопулярніші дієслова — це **давати** *(to give)*, **допомагати** *(to help)*, **телефонувати** *(to call)* та **дякувати** *(to thank)*. *(The most popular verbs are to give, to help, to call, and to thank.)* Запам'ятайте ці важливі приклади. *(Remember these important examples.)* Ми дякуємо **вчителям** *(to teachers)* за цікавий урок. *(We thank the teachers for an interesting lesson.)* Я часто телефоную друзям у неділю. *(I often call friends on Sunday.)* Батьки завжди допомагають дітям робити домашнє завдання. *(Parents always help children do their homework.)* Директор дає премію **працівникам** *(to workers)*. *(The manager gives a bonus to the workers.)* В усіх цих реченнях дія спрямована на групу людей. *(In all these sentences, the action is directed at a group of people.)* Тому ми використовуємо давальний відмінок множини. *(Therefore, we use the Dative plural.)*

Ми також використовуємо давальний відмінок множини у формальних та неформальних ситуаціях. *(We also use the Dative plural in formal and informal situations.)* When addressing groups or directing actions toward multiple people, this case is essential. Наприклад, вдома ви можете **пояснювати дітям** *(to explain to children)* нову гру. *(For example, at home you can explain a new game to children.)* А на роботі ви можете **радити колегам** *(to advise colleagues)* новий проєкт. *(And at work you can advise a new project to colleagues.)* Ось ще кілька типових ситуацій. *(Here are a few more typical situations.)* **Вчитель пояснює правила учням.** *(The teacher explains the rules to the pupils.)* **Лікар дає ліки пацієнтам.** *(The doctor gives medicine to the patients.)* Гід розповідає історію **туристам** *(to tourists)*. *(The guide tells the history to the tourists.)* У кожному випадку ми бачимо типові закінчення -ам або -ям. *(In each case, we see the typical endings -am or -yam.)*

<!-- INJECT_ACTIVITY: fill-in, focus: Dative plural endings with verbs (допомагати, дякувати, давати), 8 items -->

Іноді слова трохи змінюють свою форму у множині. *(Sometimes words slightly change their form in the plural.)* Але основа для давального відмінка множини майже завжди збігається з основою називного відмінка множини. *(But the stem for the Dative plural almost always matches the stem of the Nominative plural.)* Note that some common nouns have vowel shifts or specific stems when they become plural. Наприклад, слово «батько» у множині має форму **батьки** *(parents)*. *(For example, the word "father" in plural has the form parents.)* Тому в давальному відмінку ми кажемо **батькам** *(to parents)*. *(Therefore, in the Dative case we say to parents.)* Слово «дитина» має форму множини **діти** *(children)*. *(The word "child" has the plural form children.)* Тому ми кажемо: я допомагаю **дітям** *(to children)*. *(Therefore we say: I help children.)* Такі слова зустрічаються дуже часто, тому ви швидко їх запам'ятаєте. *(Such words occur very often, so you will remember them quickly.)*


## Орудний множини: З ким? Чим?

Тепер ми вивчаємо орудний відмінок множини. *(Now we study the Instrumental plural.)* The Instrumental plural is very regular and easy to recognize. Його головні закінчення — це **-ами** та **-ями**. *(Its main endings are -amy and -yamy.)* We use this case for two main reasons. Перша причина — це компанія або супровід. *(The first reason is company or accompaniment.)* Ми використовуємо прийменник **«з»** *(with)* або **«із»** *(with)*. *(We use the preposition "з" or "із".)* Друга причина — це інструмент або засіб дії. *(The second reason is an instrument or means of action.)* У цьому випадку ми не використовуємо прийменник. *(In this case, we do not use a preposition.)* Hard stems take the ending -ами. Наприклад, ми кажемо **студентами** *(with students)*, **книжками** *(with books)*, **мовами** *(with languages)*. *(For example, we say with students, with books, with languages.)* Soft stems take the ending -ями. Тому ми кажемо **друзями** *(with friends)*, **вулицями** *(by streets)*. *(Therefore we say with friends, by streets.)* Це дуже просте правило для всіх слів. *(This is a very simple rule for all words.)*

В українській мові є кілька важливих винятків. *(There are a few important exceptions in the Ukrainian language.)* Деякі дуже популярні слова мають коротке закінчення **-ми** в орудному відмінку множини. *(Some very popular words have the short ending -my in the Instrumental plural.)* You must memorize these four essential irregular forms because they are used daily. Слово «діти» має форму **дітьми** *(with children)*. *(The word "children" has the form with children.)* Слово «люди» має форму **людьми** *(with people)*. *(The word "people" has the form with people.)* Слово «коні» має форму **кіньми** *(with horses)*. *(The word "horses" has the form with horses.)* Слово «гості» має форму **гістьми** *(with guests)*. *(The word "guests" has the form with guests.)* Ці слова втрачають голосний звук перед закінченням. *(These words lose the vowel sound before the ending.)* Ви можете сказати **гостями** або **гістьми**. *(You can say with guests or with guests.)* Both forms are correct and natural. Але форма «гістьми» — це класичний український варіант. *(But the form "гістьми" is the classic Ukrainian variant.)* Ми часто бачимо цю форму в літературі та чуємо у формальному спілкуванні. *(We often see this form in literature and hear it in formal communication.)*

Орудний відмінок ідеально підходить для опису соціальних ситуацій. *(The Instrumental case is perfectly suited for describing social situations.)* Коли ми робимо щось разом, ми використовуємо прийменник «з» або «із». *(When we do something together, we use the preposition "with" or "with".)* Це найчастіший спосіб використання цього відмінка. *(This is the most frequent way to use this case.)* Наприклад, на вихідних батьки люблять **грати з дітьми** *(to play with children)*. *(For example, on weekends parents like to play with children.)* Увечері приємно **гуляти з друзями** *(to walk with friends)* у парку. *(In the evening it is pleasant to walk with friends in the park.)* Кожного дня ми повинні **працювати з колегами** *(to work with colleagues)* в офісі. *(Every day we must work with colleagues in the office.)* Діти люблять жити з **батьками** *(with parents)*. *(Children like to live with parents.)* У всіх цих ситуаціях ми бачимо компанію людей. *(In all these situations we see a company of people.)*

Ми також використовуємо орудний відмінок для опису інструментів. *(We also use the Instrumental case to describe tools.)* When we use an object to perform an action, we do not use a preposition. Слово просто відповідає на запитання «чим?». *(The word simply answers the question "with what?".)* Наприклад, на уроці учні можуть **писати олівцями** *(to write with pencils)*. *(For example, in the lesson pupils can write with pencils.)* У японському ресторані ми любимо **їсти паличками** *(to eat with chopsticks)*. *(In a Japanese restaurant we like to eat with chopsticks.)* На свято ми можемо **прикрашати кімнати квітами** *(to decorate rooms with flowers)*. *(For a holiday we can decorate rooms with flowers.)* Люди часто малюють картини **фарбами** *(with paints)*. *(People often paint pictures with paints.)* Ми ріжемо папір **ножицями** *(with scissors)*. *(We cut paper with scissors.)* У цих реченнях іменник у множині показує засіб дії. *(In these sentences the noun in the plural shows the means of action.)*

Прочитайте діалог про організацію шкільної поїздки. *(Read the dialogue about the organization of a school trip.)* Зверніть увагу на орудний відмінок множини. *(Pay attention to the Instrumental plural.)*
> — **Вчитель:** Добрий день! *(Good day!)* Сьогодні ми говоримо про нашу поїздку. *(Today we talk about our trip.)* Ми їдемо в гори **автобусами** *(by buses)*. *(We are going to the mountains by buses.)*
> — **Учні:** Чудово! *(Great!)* Ми можемо робити фотографії **камерами** *(with cameras)*? *(Can we take photos with cameras?)*
> — **Вчитель:** Так, звичайно. *(Yes, of course.)* Ми також будемо зустрічатися **з місцевими жителями** *(with local residents)*. *(We will also meet with local residents.)*
> — **Учні:** Ми будемо спілкуватися з **ними** *(with them)* українською мовою? *(Will we communicate with them in the Ukrainian language?)*
> — **Вчитель:** Так. *(Yes.)* Ви будете розмовляти з **людьми** *(with people)* і практикувати мову. *(You will talk with people and practice the language.)*

<!-- INJECT_ACTIVITY: match-up, focus: Match plural noun stems with -ами/-ями or irregular endings, 8 items -->


## Місцевий множини: Де? На чому?

Місцевий відмінок множини відповідає на запитання «де?» або «на чому?». *(The Locative plural case answers the questions "where?" or "on what?".)* Як і в інших відмінках множини, закінчення тут дуже регулярні. *(Like in other plural cases, the endings here are very regular.)* Ми використовуємо закінчення **-ах** для твердої групи та **-ях** для м'якої групи. *(We use the ending -ах for the hard group and -ях for the soft group.)* The Locative case is unique because it NEVER appears without a preposition in Ukrainian. Ми завжди бачимо його з маленькими словами, такими як «у», «в», «на» або «по». *(We always see it with small words, such as "in", "in", "on" or "along".)* Наприклад, діти вчаться **у школах** *(in schools)*. *(For example, children study in schools.)* Книжки лежать **на полицях** *(on shelves)*. *(Books lie on shelves.)* Люди живуть **у містах** *(in cities)*. *(People live in cities.)* Це правило працює для всіх іменників: чоловічого, жіночого та середнього роду. *(This rule works for all nouns: masculine, feminine, and neuter gender.)*

Ми часто використовуємо прийменники **«у»** або **«в»** *(in)* з місцевим відмінком множини. *(We often use the prepositions "in" or "in" with the Locative plural.)* We use "у" or "в" when we talk about being inside enclosed spaces, buildings, or geographical locations. Наприклад, влітку люди люблять гуляти **у парках** *(in parks)*. *(For example, in summer people like to walk in parks.)* Восени ми часто збираємо гриби **у лісах** *(in forests)*. *(In autumn we often gather mushrooms in forests.)* Під час подорожі туристи зазвичай живуть **у готелях** *(in hotels)*. *(During a trip tourists usually live in hotels.)* Увечері друзі люблять дивитися вистави **у театрах** *(in theaters)*. *(In the evening friends like to watch performances in theaters.)* Діти люблять гратися **у кімнатах** *(in rooms)*. *(Children like to play in rooms.)* В Україні є багато цікавого **у музеях** *(in museums)*. *(In Ukraine there is a lot of interesting things in museums.)*

Інший важливий прийменник — це **«на»** *(on / at)*. *(Another important preposition is "on / at".)* The preposition "на" is used for surfaces, open spaces, or events and activities. Наприклад, документи лежать **на столах** *(on tables)*. *(For example, documents lie on tables.)* Картини висять **на стінах** *(on walls)*. *(Pictures hang on walls.)* Це поверхні. *(These are surfaces.)* Але ми також використовуємо «на» для подій. *(But we also use "on" for events.)* Студенти багато пишуть **на заняттях** *(at classes)*. *(Students write a lot at classes.)* Музиканти грають **на концертах** *(at concerts)*. *(Musicians play at concerts.)* Також ми кажемо «на» про відкриті простори. *(Also we say "on" about open spaces.)* Автомобілі їздять **на вулицях** *(on streets)*. *(Cars drive on streets.)* Діти грають у футбол **на стадіонах** *(at stadiums)*. *(Children play football at stadiums.)* На полицях стоять цікаві книжки. *(Interesting books stand on shelves.)*

Дуже цікавий прийменник для місцевого відмінка множини — це **«по»** *(along / through / among)*. *(A very interesting preposition for the Locative plural is "along / through / among".)* The preposition "по" combined with the Locative plural describes movement across multiple locations or distribution among many points. На вихідних ми любимо **ходити по магазинах** *(to go shopping / to walk among shops)*. *(On weekends we like to go shopping.)* У неділю приємно **гуляти по парках** *(to walk through parks)*. *(On Sunday it is pleasant to walk through parks.)* Туристи люблять **їздити по містах** *(to travel across cities)* Європи. *(Tourists like to travel across cities of Europe.)* Гіди проводять екскурсії **по музеях** *(through museums)*. *(Guides conduct excursions through museums.)* Цей прийменник показує, що дія відбувається у багатьох різних місцях один за одним. *(This preposition shows that the action happens in many different places one after another.)*

Тепер давайте порівняємо давальний і місцевий відмінки множини. *(Now let's compare the Dative and Locative plural cases.)* Both cases have very similar endings, and their stems are always identical. Але закінчення різні: давальний відмінок має **-ам / -ям**, а місцевий — **-ах / -ях**. *(But the endings are different: the Dative case has -ам / -ям, and the Locative — -ах / -ях.)* It is very important not to confuse them. Давальний відмінок — це напрямок або адресат (кому?). *(The Dative case is the direction or addressee (to whom?).)* Місцевий відмінок — це місце (де?). *(The Locative case is the place (where?).)* Порівняйте ці два речення. *(Compare these two sentences.)* Я даю корм **птахам** *(to birds)*. *(I give food to birds.)* Це давальний відмінок. *(This is the Dative case.)* А тепер місцевий: птахи сидять **на дахах** *(on roofs)*. *(And now Locative: birds sit on roofs.)* Ми допомагаємо **друзям** *(to friends)*, але ми зустрічаємося **на заняттях** *(at classes)*. *(We help friends, but we meet at classes.)*

<!-- INJECT_ACTIVITY: quiz, focus: Multiple choice choosing between у/в, на, and по with Locative plural nouns, 8 items -->


## Три відмінки разом: Практика

У великих реченнях ми часто використовуємо кілька відмінків одразу. *(In large sentences we often use several cases at once.)* How do we know which plural case to use? Відмінок завжди залежить від дієслова або прийменника. *(The case always depends on the verb or preposition.)* The verb or preposition acts as a "commander" that dictates the required case ending. Якщо ми даємо щось комусь, це давальний відмінок. *(If we give something to someone, this is the Dative case.)* Якщо ми робимо щось разом з кимось, це орудний. *(If we do something together with someone, this is Instrumental.)* Якщо ми говоримо про місце дії, це місцевий. *(If we talk about the place of action, this is Locative.)* Подивіться на цей приклад. *(Look at this example.)* Ми розповіли про поїздку **батькам** *(to parents — Dat)*, поїхали **автобусами** *(by buses — Inst)* і зупинилися в **містах** *(in cities — Loc)*. 

Сьогодні вчителька розповідає план шкільної поїздки. *(Today the teacher tells the plan of the school trip.)*
> — **Вчителька:** Добрий день! *(Good day!)* Сьогодні я розкажу **дітям** *(to children)* і **батькам** *(to parents)* наш план. *(Today I will tell our plan to children and parents.)*
> — **Учень:** Ми їдемо **автобусами** *(by buses)* чи **поїздами** *(by trains)*? *(Are we going by buses or by trains?)*
> — **Вчителька:** Ми їдемо **вагонами** *(by train cars)*. *(We are going by train cars.)* Я вже подякувала **водіям** *(to drivers)* за допомогу. *(I already thanked the drivers for help.)*
> — **Учениця:** А де ми будемо жити? *(And where will we live?)* Ми будемо спати в **наметах** *(in tents)*? *(Will we sleep in tents?)*
> — **Вчителька:** Ні, ми зупинимося в **готелях** *(in hotels)*. *(No, we will stay in hotels.)* Там ми зустрінемося з іншими **учнями** *(with other students)*. *(There we will meet with other students.)*

<!-- INJECT_ACTIVITY: error-correction, focus: Fixing incorrect plural case endings in a short paragraph about a children's party, 6 items -->

These three cases form the "Golden Trio" of plural endings. Вони мають дуже прості закінчення. *(They have very simple endings.)* Давальний відмінок — це завжди **-ам / -ям**. *(The Dative case is always -ам / -ям.)* Орудний відмінок — це завжди **-ами / -ями**. *(The Instrumental case is always -ами / -ями.)* Місцевий відмінок — це завжди **-ах / -ях**. *(The Locative case is always -ах / -ях.)* Once you know the plural stem of a noun, forming these three cases is the easiest part of Ukrainian morphology. Їх дуже легко запам'ятати. *(It is very easy to remember them.)* Тепер ви можете вільно говорити з друзями! *(Now you can freely talk with friends!)*


## Підсумок

Час перевірити, що ви запам'ятали! *(Time to check what you remembered!)*

1. Які універсальні закінчення мають іменники в давальному відмінку множини? *(What universal endings do nouns have in the Dative plural?)*
**Відповідь:** *(Answer:)* Завжди **-ам** або **-ям** *(always -ам or -ям)*. Наприклад: **друзям**, **містам** *(to friends, to cities)*.

2. Як сказати «with children» та «with people» в орудному відмінку? *(How to say "with children" and "with people" in the Instrumental case?)*
**Відповідь:** *(Answer:)* **З дітьми** та **з людьми** *(with children and with people)*. Це слова-винятки. *(These are exception words.)*

3. Який прийменник ми використовуємо для позначення руху через багато місць (наприклад, вулиці)? *(Which preposition do we use to indicate movement across many places, for example, streets?)*
**Відповідь:** *(Answer:)* Ми використовуємо прийменник **по** + місцевий відмінок *(we use the preposition по + locative case)*: **по вулицях** *(along the streets)*.

4. Чи залежить закінчення **-ами** / **-ями** від роду іменника в множині? *(Does the ending -ами / -ями depend on the gender of the noun in the plural?)*
**Відповідь:** *(Answer:)* Ні, у множині рід не має значення. *(No, in the plural, gender does not matter.)* Закінчення залежить тільки від основи слова *(the ending depends only on the word stem)* — тверда чи м'яка *(hard or soft)*.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: plural-other-cases
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

**Level: A2 (Module 34/60) — ELEMENTARY**

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
