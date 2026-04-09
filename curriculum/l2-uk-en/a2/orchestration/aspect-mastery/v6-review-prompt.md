<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 42: 30 найважливіших видових пар (A2, A2.6 [Aspect, Tenses, and Motion])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-042
level: A2
sequence: 42
slug: aspect-mastery
version: '1.0'
title: 30 найважливіших видових пар
subtitle: Морфологія видових пар та вибір виду в контексті
focus: grammar
pedagogy: PPP
phase: A2.6 [Aspect, Tenses, and Motion]
word_target: 2000
objectives:
  - Learner can produce both members of 30 essential aspect pairs from memory, 
    organized by morphological pattern (prefix, suffix change, stem change, 
    suppletive).
  - Learner can identify the four main formation patterns for aspect pairs and 
    predict the perfective or imperfective partner of an unfamiliar verb using 
    these patterns.
  - Learner can choose the correct aspect in complex sentences involving 
    sequence, interruption, habitual action, and single result — beyond simple 
    signal words.
  - Learner can use aspect pairs fluently in short dialogues about daily plans, 
    completed tasks, and ongoing activities.
dialogue_situations:
  - setting: 'Parent and child doing homework — choosing the right aspect: Ти написав
      (pf) домашнє завдання? Ні, я ще пишу (impf). Прочитай (pf) цей абзац. Я читаю
      (impf) вже годину!'
    speakers:
      - Мама/Тато
      - Школяр (student)
    motivation: '30 aspect pairs in homework context: писати/написати, читати/прочитати'
content_outline:
  - section: Як утворюються видові пари (How Aspect Pairs Are Formed)
    words: 500
    points:
      - 'Pattern 1 — Prefixation (most common): писати → написати, читати → прочитати,
        робити → зробити, їсти → з''їсти, варити → зварити. The prefix adds completion
        without changing the base meaning.'
      - 'Pattern 2 — Suffix change: записувати → записати (-увати → -ати), розповідати
        → розповісти (-ідати → -істи), пояснювати → пояснити (-ювати → -ити). Imperfective
        suffixes are longer.'
      - 'Pattern 3 — Stem change: допомагати → допомогти, відповідати → відповісти.
        The stem itself transforms.'
      - 'Pattern 4 — Suppletive (different roots): брати → взяти, говорити → сказати,
        класти → покласти. These must be memorized as pairs.'
  - section: '30 пар: Список і приклади (30 Pairs: List and Examples)'
    words: 600
    points:
      - 'Group A — Daily actions (10 pairs): робити/зробити, писати/написати, читати/прочитати,
        готувати/приготувати, їсти/з''їсти, пити/випити, варити/зварити, мити/помити,
        прибирати/прибрати, прасувати/випрасувати.'
      - 'Group B — Communication & learning (10 pairs): говорити/сказати, питати/запитати,
        відповідати/відповісти, пояснювати/пояснити, вчити/вивчити, розуміти/зрозуміти,
        казати/сказати, розповідати/розповісти, записувати/записати, перекладати/перекласти.'
      - 'Group C — Movement & interaction (10 pairs): брати/взяти, давати/дати, класти/покласти,
        відкривати/відкрити, закривати/закрити, починати/почати, закінчувати/закінчити,
        допомагати/допомогти, купувати/купити, платити/заплатити.'
      - 'Each pair shown in a minimal contrast sentence: Я варив суп (was cooking)
        vs. Я зварив суп (cooked it, done).'
  - section: Вибір виду в складних ситуаціях (Aspect Choice in Complex 
      Situations)
    words: 500
    points:
      - 'Sequence of completed events — all perfective: Я встав, вмився, поснідав
        і пішов на роботу (I got up, washed, had breakfast, and left for work).'
      - 'Interruption — imperfective background + perfective event: Коли я готувала
        вечерю, подзвонила подруга (While I was cooking dinner, a friend called).'
      - 'Habitual vs. single — imperfective for habit, perfective for one-time: Вона
        завжди допомагала сусідам (She always helped the neighbors) vs. Вона допомогла
        сусідці вчора (She helped the neighbor yesterday).'
      - 'Negation nuance: Я не читав цю книгу (I haven''t read it / never read it)
        vs. Я не прочитав цю книгу (I didn''t finish reading it — started but didn''t
        complete).'
  - section: Практика у діалогах (Practice in Dialogues)
    words: 400
    points:
      - 'Dialogue 1: Що ти зробив сьогодні? — Listing completed tasks with perfective.
        А що ти робив увечері? — Describing an ongoing evening activity with imperfective.'
      - 'Dialogue 2: Planning and reporting. Що ти будеш робити завтра? (impf.) vs.
        Що ти зробиш до п''ятниці? (pf.) — aspect in future context too.'
      - 'Common conversational patterns with aspect: Ти вже зробив? (Have you done
        it yet?), Я ще роблю (I''m still doing it), Я тільки що зробив (I just did
        it).'
vocabulary_hints:
  required:
    - видова пара (aspect pair)
    - префікс (prefix)
    - суфікс (suffix)
    - брати / взяти (to take — impf./pf.)
    - давати / дати (to give — impf./pf.)
    - говорити / сказати (to say — impf./pf.)
    - класти / покласти (to put — impf./pf.)
    - починати / почати (to begin — impf./pf.)
    - закінчувати / закінчити (to finish — impf./pf.)
    - допомагати / допомогти (to help — impf./pf.)
  recommended:
    - утворення (formation)
    - морфологія (morphology)
    - тільки що (just now)
    - вже (already)
activity_hints:
  - type: match-up
    focus: Match imperfective verbs with their perfective partners from the 30 
      pairs
    items: 8
  - type: fill-in
    focus: Complete sentences by choosing the correct aspect based on context 
      (sequence, interruption, habit, single event)
    items: 8
  - type: group-sort
    focus: Sort aspect pairs by formation pattern (prefix, suffix, stem change, 
      suppletive)
    items: 8
  - type: quiz
    focus: Read a mini-situation and choose the correct aspect form with 
      justification
    items: 8
references:
  - title: Заболотний Grade 6, §52-54
    notes: Видові пари дієслів — formation patterns and usage
  - title: 'Ohoiko, 500+ Ukrainian Verbs (2024)'
    notes: Comprehensive aspect pair reference with conjugation tables

</plan_content>

## Generated Content

<generated_module_content>
## Як утворюються видові пари

В українській мові дієслова мають дуже важливу характеристику. Це **вид дієслова** *(verb aspect)*. English uses continuous tenses to show a process and simple or perfect tenses to show a completed action. Українська мова працює інакше. We use two different but related verbs to express these differences. Ці два дієслова — це **видова пара** *(aspect pair)*. Перша частина пари — це **недоконаний вид** *(imperfective aspect)*. Він означає незавершену дію, процес або регулярну звичку. Дієслова недоконаного виду відповідають на питання «**що робити?**» *(what to do?)*. Друга частина пари — це **доконаний вид** *(perfective aspect)*. Він означає завершену дію, яка досягла своєї межі, або конкретний результат. Дієслова доконаного виду відповідають на питання «**що зробити?**» *(what to do completely?)*. It is important to understand that these are two separate lexical items in the dictionary. Коли ви вчите нове українське дієслово, ви повинні запам'ятати обидві форми. This might seem difficult at first, but Ukrainian verbs follow specific, logical patterns to form these pairs.

Найпоширеніший спосіб творення доконаного виду — це додавання префікса. A prefix is added to the beginning of the imperfective verb. Цей **префікс** *(prefix)* додає ідею завершеності, але не змінює базове значення слова. Ось кілька дуже важливих прикладів. Ми маємо пару **писати** *(to write, process)* та **написати** *(to write, result)*. Ми читаємо книгу: **читати** *(to read)* та **прочитати** *(to read completely)*. Ми робимо завдання: **робити** *(to do)* та **зробити** *(to do, to get done)*. Ми їмо обід: **їсти** *(to eat)* та **з'їсти** *(to eat up)*. The prefix you need to add is unpredictable, so you just have to memorize it with the verb. Часто ми використовуємо префікс «с-». В українській мові є спеціальне фонетичне правило, яке називається «Кафе Птах» *(Cafe Ptakh)*. If the verb root starts with the letters к, п, т, ф, or х, we must use the prefix «с-» instead of «з-». Наприклад, ми кажемо **сфотографувати** *(to take a photo)*, а не «зфотографувати». Інші приклади включають **казати** *(to say)* та **сказати** *(to tell)*, або **пекти** *(to bake)* та **спекти** *(to bake completely)*. This phonetic rule makes pronunciation much easier and more natural.

Другий спосіб творення видових пар — це зміна суфікса. Often, the perfective verb already exists, and we make it imperfective to show a process. Ми змінюємо короткий **суфікс** *(suffix)* доконаного виду на довший суфікс недоконаного виду. Дуже часто ми змінюємо суфікси «-ити» або «-нути» на «-увати» чи «-ати». Наприклад, ми беремо пару **вирішувати** *(to decide, process)* та **вирішити** *(to decide, result)*. Ми маємо дієслова **записувати** *(to note down)* та **записати** *(to write down completely)*. Ми чуємо звук: **стукати** *(to knock, repeatedly)* та **стукнути** *(to knock, once)*. Третій спосіб — це зміна самої основи слова або чергування звуків. Sometimes, the vowels or consonants inside the root of the verb change when the aspect changes. Один із найчастіших прикладів — це зміна голосних у корені слова (наприклад, «о» на «а»). Так працює пара **допомагати** *(to help, regularly)* та **допомогти** *(to help, once)*.
 Інший приклад показує зміну приголосних у корені слова. Ми використовуємо **відповідати** *(to answer, process)* та **відповісти** *(to answer, result)*. Ми бачимо це у парі **запрошувати** *(to invite, process)* та **запросити** *(to invite, result)*. These internal changes might look complex, but they follow consistent historical sound shifts in Ukrainian. З часом ви навчитеся легко розпізнавати ці типові суфікси та чергування.

Четвертий спосіб — це використання абсолютно різних слів. These are called suppletive pairs, and they have completely different roots for the imperfective and perfective forms. Хоча таких пар небагато, вони є найбільш вживаними словами в мові. You absolutely must memorize them as unique vocabulary items because you cannot guess the pair. Ось найголовніші приклади для вас. Дієслова **брати / взяти** *(to take — impf./pf.)* є дуже популярними. Ми постійно використовуємо **говорити / сказати** *(to say — impf./pf.)*. Ми маємо дієслова **ловити** *(to catch, process)* та **піймати** *(to catch, result)*. Ми постійно використовуємо **шукати** *(to look for)* та **знайти** *(to find)*. Ці слова не мають спільного кореня, але означають одну і ту ж дію. Коли ви шукаєте ключі, ви кажете: «Я шукаю ключі». Коли ви бачите свої ключі, ви кажете: «Я знайшов ключі!». It is crucial to practice these specific pairs daily because they appear in almost every conversation. Наприклад, ми часто питаємо: «Що ти говориш?», але «Що ти сказав?». Without knowing these distinct pairs, expressing basic ideas about finding, taking, or speaking becomes impossible.

<!-- INJECT_ACTIVITY: group-sort-sort-aspect-pairs-by-formation-pattern-prefix-suffix-stem-change-suppletive -->

## 30 пар: Список і приклади

Зараз ми вивчимо найважливіші слова для щоденного життя. Це перша група дієслів. Вона описує нашу ранкову рутину та домашні справи. Ці слова ви будете використовувати кожного дня.

Here are the first ten essential aspect pairs for your daily routine and housework. You need to memorize both the imperfective and perfective forms.

* **готувати** / **приготувати** *(to cook / to finish cooking)*
* **їсти** / **з'їсти** *(to eat / to eat up)*
* **пити** / **випити** *(to drink / to drink up)*
* **варити** / **зварити** *(to boil / to finish boiling)*
* **мити** / **помити** *(to wash / to wash clean)*
* **прибирати** / **прибрати** *(to clean / to finish cleaning)*
* **прасувати** / **випрасувати** *(to iron / to finish ironing)*
* **робити** / **зробити** *(to do / to finish doing)*
* **писати** / **написати** *(to write / to finish writing)*
* **читати** / **прочитати** *(to read / to finish reading)*

Let's look at how they work. The imperfective verb focuses on the duration or process. The perfective verb focuses entirely on the final result.

Я варив борщ годину. *(I was cooking borsch for an hour.)*
Я зварив борщ. *(I cooked the borsch.)*

In the first sentence, we care about the time spent. In the second sentence, the borsch is ready, and we can eat it.

Друга група слів стосується спілкування та навчання. Ми постійно говоримо, слухаємо та читаємо інформацію. Ці дієслова допоможуть вам ефективно спілкуватися.

Communication and learning require precision. You need to know if someone is still explaining something, or if they have finally made it clear. Here are ten crucial pairs for cognition and interaction.

* **говорити / сказати** *(to say — impf./pf.)*
* **відповідати** / **відповісти** *(to answer / to give an answer)*
* **питати** / **запитати** *(to ask / to ask a question)*
* **пояснювати** / **пояснити** *(to explain / to make clear)*
* **вчити** / **вивчити** *(to learn / to memorize completely)*
* **розуміти** / **зрозуміти** *(to understand / to grasp)*
* **перекладати** / **перекласти** *(to translate / to finish translating)*
* **казати** / **сказати** *(to tell / to finish telling)*
* **записувати** / **записати** *(to note down / to finish writing down)*
* **розповідати** / **розповісти** *(to tell / to tell a complete story)*

We often use the imperfective aspect to set a background scene, and the perfective aspect to highlight a successful action.

Вчитель пояснював правило. *(The teacher was explaining the rule.)*
Він нарешті пояснив правило. *(He finally explained the rule.)*

The imperfective form «пояснював» shows the ongoing effort. The perfective form «пояснив» shows that the students now understand it. Achieving success is a perfective concept.

Третя важлива група — це соціальна взаємодія та рух. Ми щодня щось купуємо, беремо або починаємо. Без цих слів важко жити в місті.

Social interactions often involve the transfer of objects or money. These pairs are crucial for navigating everyday situations like shopping or working.

* **брати / взяти** *(to take — impf./pf.)*
* **давати / дати** *(to give — impf./pf.)*
* **класти / покласти** *(to put — impf./pf.)*
* **купувати** / **купити** *(to buy / to purchase)*
* **платити** / **заплатити** *(to pay / to pay off)*
* **допомагати** / **допомогти** *(to help / to provide help)*
* **відкривати** / **відкрити** *(to open / to get open)*
* **закривати** / **закрити** *(to close / to get closed)*
* **починати** / **почати** *(to begin / to start)*
* **закінчувати** / **закінчити** *(to finish / to complete)*

Sometimes, the imperfective verb shows the attempt, while the perfective verb confirms actual possession or a finalized transaction.

Ми купували квитки. *(We were buying tickets.)*
Ми купили квитки. *(We bought the tickets.)*

If you say «купували», you are describing the process, and maybe you failed. If you say «купили», the transaction is done and the tickets are yours.

Тепер давайте порівняємо ці слова. Ви чітко побачите різницю між процесом та результатом.

Let's analyze some minimal contrast drills to solidify your understanding. These short pairs of sentences illustrate the semantic difference between the two aspects.

Вона пила каву. *(She was drinking coffee.)*
Вона випила каву. *(She drank the coffee.)*

The first sentence implies she was sitting, sipping, and enjoying the process. The second sentence implies her cup is completely empty.

Ми починали о дев'ятій. *(We used to start at nine.)*
Ми почали о дев'ятій. *(We started at nine.)*

The imperfective verb here shows a habitual, repeating action in the past. It was a regular routine. The perfective verb points to one specific event, like yesterday morning.

Він читав книгу. *(He was reading a book.)*
Він прочитав книгу. *(He read the book.)*

In the first case, he spent time with the book, but he might still be reading. In the second case, he has reached the final page. The perfective aspect always implies a boundary that has been reached.

<!-- INJECT_ACTIVITY: match-up-match-imperfective-verbs-with-their-perfective-partners-from-the-30-pairs -->

## Вибір виду в складних ситуаціях

Часто ми розповідаємо про кілька подій у минулому. *(Often we talk about several events in the past.)* When you describe a chain of completed actions, one after another, you must use only perfective verbs. Це дуже логічно і просто для розуміння. *(This is very logical and simple to understand.)* Each verb acts as a link in a chronological chain of results.

Я **встав** *(got up)*, **вмився** *(washed)*, **поснідав** *(had breakfast)* і **пішов** *(left)* на роботу. *(I got up, washed, had breakfast, and left for work.)* Усі ці дієслова мають доконаний вид. *(All these verbs have perfective aspect.)* Але що відбувається, коли одна дія перериває іншу? *(But what happens when one action interrupts another?)* Here we must mix the aspects. Ми використовуємо недоконаний вид для довгої фонової дії. *(We use the imperfective aspect for a long background action.)* А для раптової події ми беремо доконаний вид. *(And for a sudden event we take the perfective aspect.)* The imperfective sets the scene, and the perfective "cuts" it.

Я **читав** *(was reading)* книгу, коли мама **зайшла** *(entered)* в кімнату. *(I was reading a book when mom entered the room.)* «Читав» — це ваш тривалий процес. *(«Was reading» is your continuous process.)* «Зайшла» — це швидка результативна дія. *(«Entered» is a quick resultative action.)* Вона перервала мій процес читання. *(She interrupted my reading process.)*

Інша складна ситуація — це різниця між звичкою та одноразовим результатом. *(Another complex situation is the difference between a habit and a one-time result.)* If an action repeats regularly, it is a habit. Для щоденних звичок ми завжди використовуємо недоконаний вид. *(For daily habits we always use the imperfective aspect.)* There are special signal words that help you choose the imperfective aspect correctly. Це такі слова, як **завжди** *(always)*, **часто** *(often)*, або **зазвичай** *(usually)*.

Він завжди **допомагав** *(helped)* своїм сусідам. *(He always helped his neighbors.)* Це регулярна і повторювана дія в минулому. *(This is a regular and repeated action in the past.)* But if you want to highlight one specific, successful action, you switch to the perfective aspect. Look for specific time markers like **вчора** *(yesterday)*, **один раз** *(one time)*, або **раптом** *(suddenly)*.

Він **допоміг** *(helped)* сусідці вчора вранці. *(He helped the neighbor yesterday morning.)* Це одна конкретна і завершена дія. *(This is one specific and completed action.)* Вона має чіткий і корисний результат зараз. *(It has a clear and useful result now.)* Завжди звертайте увагу на контекст і слова-маркери. *(Always pay attention to the context and marker words.)*

Заперечення також може суттєво змінювати значення виду дієслова. *(Negation can also significantly change the meaning of the verb aspect.)* What happens when you add **не** *(not)* before a verb in the past tense? The difference between «не робив» and «не зробив» is very important for clear communication. Коли ви кажете «я не робив», ви повністю заперечуєте сам процес. *(When you say "I didn't do", you completely deny the process itself.)* This means you never started the action, or you never even touched the task.

Я не **читав** *(did not read)* цю нову книгу. *(I haven't read this new book.)* Я навіть ніколи не відкривав її. *(I never even opened it.)* Але коли ви використовуєте доконаний вид, значення зовсім інше. *(But when you use the perfective aspect, the meaning is completely different.)* «Я не зробив» means you tried or intended to do it, but you failed to achieve the final result.

Я читав, але не **прочитав** *(did not finish reading)* цю книгу. *(I was reading, but I didn't finish reading this book.)* Я почав процес читання, але не закінчив його. *(I started the reading process, but didn't finish it.)*

Нарешті, давайте ще раз згадаємо про майбутній час. *(Finally, let's remember once again about the future tense.)* Aspect is just as crucial in the future as it is in the past tense. Недоконаний вид утворює майбутній час за допомогою допоміжного дієслова **бути** *(to be)*. *(The imperfective aspect forms the future tense with the help of the auxiliary verb "to be".)*

Я **буду писати** *(will be writing)* довгого листа завтра. *(I will be writing a long letter tomorrow.)* Це ваш робочий процес, який триватиме певний час. *(This is your work process that will last some time.)* Але доконаний вид має просту коротку форму майбутнього часу. *(But the perfective aspect has a simple short form of the future tense.)*

Я **напишу** *(will write)* цього листа завтра. *(I will write this letter tomorrow.)* Це означає, що завтра лист буде повністю готовий. *(This means tomorrow the letter will be completely ready.)* Remember one absolute and unbreakable rule in Ukrainian grammar. Ви ніколи не можете використовувати слово «бути» з доконаним видом. *(You can never use the word "to be" with the perfective aspect.)* Saying «я буду прочитати» is a major grammatical error. Завжди впевнено кажіть «я прочитаю»! *(Always confidently say "I will read"!)*

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-by-choosing-the-correct-aspect-based-on-context-sequence-interruption-habit-single-event -->
<!-- INJECT_ACTIVITY: quiz-read-a-mini-situation-and-choose-the-correct-aspect-form-with-justification -->

## Практика у діалогах

Найкращий приклад — це розмова про домашнє завдання. *(The best example is a conversation about homework.)* Батьки хочуть бачити результат, а діти говорять про процес. *(Parents want to see the result, and children talk about the process.)*

> — **Мама:** Сину, ти вже **зробив** *(have done)* уроки?
> — **Син:** Ні, я ще **роблю** *(am doing)*. Я зараз **пишу** *(am writing)* твір з історії.
> — **Мама:** Але ти **писав** *(were writing)* його вчора! Ти ще не **написав** *(finished writing)* його?
> — **Син:** Я **написав** *(wrote)* половину. Ще треба **вивчити** *(to learn)* слова.
> — **Мама:** А ти їх **вчив** *(were learning)* учора?
> — **Син:** Так, я **вчив** *(was learning)*, але не **вивчив** *(memorized)* усі.

Тут мама постійно використовує доконаний вид. *(Here the mother constantly uses the perfective aspect.)* Їй потрібен готовий результат. *(She needs the finished result.)* Син використовує недоконаний вид, бо він у процесі роботи. *(The son uses the imperfective aspect because he is in the process of working.)*

Двоє друзів обговорюють плани на вихідні. *(Two friends are discussing plans for the weekend.)* Ми бачимо контраст між намірами та результатами. *(We see the contrast between intentions and results.)*

> — **Олег:** Що ти **будеш робити** *(will be doing)* завтра?
> — **Анна:** Завтра я **буду відпочивати**. А що ти **зробиш** *(will get done)* до п'ятниці?
> — **Олег:** До п'ятниці я **напишу** *(will finish writing)* статтю. А на вихідних я **буду дивитися** *(will be watching)* новий серіал. Я **почав** *(started)* його вчора.
> — **Анна:** Ти вже **подивився** *(have watched)* перший сезон?
> — **Олег:** Ні, я ще **дивлюся** *(am watching)*. Я **дивився** *(was watching)* три години, але не **додивився** *(finished watching)*.
> — **Анна:** Зрозуміло. Вчора я **купувала** *(was buying)* продукти, але забула **купити** *(to buy)* каву.
> — **Олег:** Тоді ми можемо **випити** *(to drink)* каву разом!

Анна говорить про свої плани як про результати. *(Anna talks about her plans as results.)* Олег описує свій процес відпочинку. *(Oleg describes his process of resting.)*

У розмовах українці часто використовують певні фрази з видовими парами. *(In conversations, Ukrainians often use specific phrases with aspect pairs.)*
Коли ви щойно завершили дію, ви кажете: «Я **тільки що** *(just now)* **зробив** *(did)* це». *(When you have just completed an action, you say: "I just did this".)*
Якщо процес ще триває, скажіть: «Я ще не **закінчив** *(finished)*» або «Я ще **роблю** *(am doing)*». *(If the process is still ongoing, say: "I haven't finished yet" or "I am still doing".)*
Щоб запропонувати почати дію, використовуйте доконаний вид: «**Давай почнемо** *(let's start)*». *(To propose starting an action, use the perfective aspect: "Let's start".)*

Вибір виду дієслова — це питання вашого мислення. *(The choice of verb aspect is a question of your mindset.)* Always ask yourself about the main thing before choosing the verb aspect. Is the action done? Is there a final result? Якщо так, вибирайте доконаний вид. *(If yes, choose the perfective aspect.)* Is the action happening right now? Is it repeating regularly? Якщо так, вам потрібен недоконаний вид. *(If yes, you need the imperfective aspect.)* Цей аналіз допоможе вам говорити українською природно. *(This analysis will help you speak Ukrainian naturally.)*

## Підсумок

Час перевірити ваші знання. *(It is time to check your knowledge.)* Дайте відповіді на ці запитання. *(Answer these questions.)*

Які чотири основні способи творення видових пар ви знаєте? *(What four main ways of forming aspect pairs do you know?)* 
Це префікси, суфікси, чергування та різні основи. *(These are prefixes, suffixes, stem changes, and different roots.)*

Назвіть видову пару до дієслова «**брати**» *(to take)* та «**говорити**» *(to speak)*. 
Доконаний вид — це «**взяти**» *(to take)* і «**сказати**» *(to say)*. Вони мають різні основи. *(They have different roots.)*

Який вид дієслова потрібен для послідовності завершених дій? *(Which verb aspect is needed for a sequence of completed actions?)* 
Вам потрібен доконаний вид. *(You need the perfective aspect.)*

У чому різниця між фразами «Я не **читав**» *(I did not read)* і «Я не **прочитав**» *(I did not finish reading)*? 
Перша фраза показує відсутність процесу. *(The first phrase shows the absence of a process.)* Друга фраза означає, що ви не досягли результату. *(The second phrase means you did not reach the result.)*

Вид дієслова — це логіка. *(The verb aspect is logic.)* Головне — завжди думати про результат. *(The main thing is to always think about the result.)*
</generated_module_content>

**PIPELINE NOTE — Word count: 3058 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 568 words | Not found: 7 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ ати — NOT IN VESUM
  ✗ зфотографувати — NOT IN VESUM
  ✗ ити — NOT IN VESUM
  ✗ нути — NOT IN VESUM
  ✗ увати — NOT IN VESUM

All 568 other words are confirmed to exist in VESUM.

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
