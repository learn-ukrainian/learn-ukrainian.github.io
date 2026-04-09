<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-mastery.yaml` file for module **42: 30 найважливіших видових пар** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-sort-aspect-pairs-by-formation-pattern-prefix-suffix-stem-change-suppletive -->`
- `<!-- INJECT_ACTIVITY: match-up-match-imperfective-verbs-with-their-perfective-partners-from-the-30-pairs -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-by-choosing-the-correct-aspect-based-on-context-sequence-interruption-habit-single-event -->`
- `<!-- INJECT_ACTIVITY: quiz-read-a-mini-situation-and-choose-the-correct-aspect-form-with-justification -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match imperfective verbs with their perfective partners from the 30 pairs
  items: 8
  type: match-up
- focus: Complete sentences by choosing the correct aspect based on context (sequence,
    interruption, habit, single event)
  items: 8
  type: fill-in
- focus: Sort aspect pairs by formation pattern (prefix, suffix, stem change, suppletive)
  items: 8
  type: group-sort
- focus: Read a mini-situation and choose the correct aspect form with justification
  items: 8
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- утворення (formation)
- морфологія (morphology)
- тільки що (just now)
- вже (already)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Як утворюються видові пари

В українській мові дієслова мають дуже важливу характеристику. Це **вид дієслова** *(verb aspect)*. English uses continuous tenses to show a process and simple or perfect tenses to show a completed action. Українська мова працює інакше. We use two different but related verbs to express these differences. Ці два дієслова — це **видова пара** *(aspect pair)*. Перша частина пари — це **недоконаний вид** *(imperfective aspect)*. Він означає незавершену дію, процес або регулярну звичку. Дієслова недоконаного виду відповідають на питання «**що робити?**» *(what to do?)*. Друга частина пари — це **доконаний вид** *(perfective aspect)*. Він означає завершену дію, яка досягла своєї межі, або конкретний результат. Дієслова доконаного виду відповідають на питання «**що зробити?**» *(what to do completely?)*. It is important to understand that these are two separate lexical items in the dictionary. Коли ви вчите нове українське дієслово, ви повинні запам'ятати обидві форми. This might seem difficult at first, but Ukrainian verbs follow specific, logical patterns to form these pairs.

Найпоширеніший спосіб творення доконаного виду — це додавання префікса. A prefix is added to the beginning of the imperfective verb. Цей **префікс** *(prefix)* додає ідею завершеності, але не змінює базове значення слова. Ось кілька дуже важливих прикладів. Ми маємо пару **писати** *(to write, process)* та **написати** *(to write, result)*. Ми читаємо книгу: **читати** *(to read)* та **прочитати** *(to read completely)*. Ми робимо завдання: **робити** *(to do)* та **зробити** *(to do, to get done)*. Ми їмо обід: **їсти** *(to eat)* та **з'їсти** *(to eat up)*. The prefix you need to add is unpredictable, so you just have to memorize it with the verb. Часто ми використовуємо префікс «с-». В українській мові є спеціальне фонетичне правило, яке називається «Кафе Птах» *(Cafe Ptakh)*. If the verb root starts with the letters к, п, т, ф, or х, we must use the prefix «с-» instead of «з-». Наприклад, ми кажемо **сфотографувати** *(to take a photo)*, а не «зфотографувати». Інші приклади включають **казати** *(to say)* та **сказати** *(to tell)*, або **пекти** *(to bake)* та **спекти** *(to bake completely)*. This phonetic rule makes pronunciation much easier and more natural.

Другий спосіб творення видових пар — це зміна суфікса. Often, the perfective verb already exists, and we make it imperfective to show a process. Ми змінюємо короткий **суфікс** *(suffix)* доконаного виду на довший суфікс недоконаного виду. Дуже часто ми змінюємо суфікси «-ити» або «-нути» на «-увати» чи «-ати». Наприклад, ми беремо пару **вирішувати** *(to decide, process)* та **вирішити** *(to decide, result)*. Ми маємо дієслова **записувати** *(to note down)* та **записати** *(to write down completely)*. Ми чуємо звук: **стукати** *(to knock, repeatedly)* та **стукнути** *(to knock, once)*. Третій спосіб — це зміна самої основи слова або чергування звуків. Sometimes, the vowels or consonants inside the root of the verb change when the aspect changes. Один із найчастіших прикладів — це зміна звуків «ог» на «ага». Так працює пара **допомагати** *(to help, regularly)* та **допомогти** *(to help, once)*. Інший приклад показує зміну приголосних у корені слова. Ми використовуємо **відповідати** *(to answer, process)* та **відповісти** *(to answer, result)*. Ми бачимо це у парі **запрошувати** *(to invite, process)* та **запросити** *(to invite, result)*. These internal changes might look complex, but they follow consistent historical sound shifts in Ukrainian. З часом ви навчитеся легко розпізнавати ці типові суфікси та чергування.

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
* **вмиватися** / **вмитися** *(to wash one's face / to finish washing)*
* **одягатися** / **одягнутися** *(to get dressed / to finish dressing)*
* **дивитися** / **подивитися** *(to watch / to take a look)*

Let's look at how they work. The imperfective verb focuses on the duration or process. The perfective verb focuses entirely on the final result.

Я варив борщ годину. *(I was cooking borsch for an hour.)*
Я зварив борщ. *(I cooked the borsch.)*

In the first sentence, we care about the time spent. In the second sentence, the borsch is ready, and we can eat it.

Друга група слів стосується спілкування та навчання. Ми постійно говоримо, слухаємо та читаємо інформацію. Ці дієслова допоможуть вам ефективно спілкуватися.

Communication and learning require precision. You need to know if someone is still explaining something, or if they have finally made it clear. Here are ten crucial pairs for cognition and interaction.

* **говорити / сказати** *(to say — impf./pf.)*
* **відповідати** / **відповісти** *(to answer / to give an answer)*
* **запитувати** / **запитати** *(to ask / to ask a question)*
* **пояснювати** / **пояснити** *(to explain / to make clear)*
* **вчити** / **вивчити** *(to learn / to memorize completely)*
* **розуміти** / **зрозуміти** *(to understand / to grasp)*
* **перекладати** / **перекласти** *(to translate / to finish translating)*
* **писати** / **написати** *(to write / to finish writing)*
* **читати** / **прочитати** *(to read / to finish reading)*
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
* **телефонувати** / **зателефонувати** *(to call / to make a phone call)*

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

> — **Олег:** Що ти **плануєш** *(plan)* робити на вихідних?
> — **Анна:** Мені треба **купити** *(to buy)* телефон. Я хочу **поїхати** *(to go)* в центр.
> — **Олег:** Я **буду дивитися** *(will be watching)* новий серіал. Я **почав** *(started)* його вчора.
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

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-mastery
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

**Level: A2 (Module 42/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати

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
