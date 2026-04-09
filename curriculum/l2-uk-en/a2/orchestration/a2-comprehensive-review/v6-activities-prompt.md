<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a2-comprehensive-review.yaml` file for module **67: Повна картина** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->`
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-grammar-categories -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`
- `<!-- INJECT_ACTIVITY: error-correction-final-review -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed case drill — all seven cases in one exercise
  items: 8
  type: fill-in
- focus: Choose perfective or imperfective aspect for the context
  items: 8
  type: quiz
- focus: Sort grammar concepts by category (case, aspect, comparison, conjunction)
  items: 8
  type: group-sort
- focus: Find and correct grammar errors in sentences covering module topics
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- впевненість (confidence)
- складний (complex, compound)
- сполучник (conjunction)
required:
- повторення (review, revision)
- граматика (grammar)
- відмінок (grammatical case)
- дієслово (verb)
- прикметник (adjective)
- займенник (pronoun)
- речення (sentence)
- помилка (error, mistake)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Відмінки: від називного до кличного (~550 words total)

Ми закінчуємо рівень А2. Українська граматика будується на відмінках. The word **відмінок** means case. Він показує роль слова в реченні. Іменники, прикметники та займенники змінюють закінчення.
В українській мові є сім відмінків. **Називний відмінок** is the nominative case. Це базова форма. Це прямий відмінок. Він називає предмет або особу. Слово в називному відмінку часто є підметом.
Усі інші шість відмінків — це **непрямі відмінки**. These are the oblique cases. Вони показують зв'язок між словами. Непрямий відмінок може означати об'єкт, інструмент, місце або напрямок. Давайте згадаємо їхні головні ролі.

**Родовий відмінок** is the genitive case. Він означає відсутність чогось. Після слова «немає» завжди стоїть родовий відмінок. Ми кажемо «немає **часу**». This means "no time". Він також показує належність. Ми кажемо «книга **вчителя**». This means "the teacher's book". Ми використовуємо його для частини від цілого. Наприклад, «трохи **води**». This translates to "a little water".
**Знахідний відмінок** is the accusative case. Він вказує на прямий об'єкт дії. Якщо дія переходить на предмет, ми кажемо «я бачу **книгу**». This means "I see a book". Для істот чоловічого роду він має форму родового відмінка. Ми кажемо «я бачу **вчителя**». This means "I see a teacher".

**Давальний відмінок** is the dative case. Він показує адресата дії. Коли ми щось даємо, ми використовуємо цей відмінок. Ми кажемо «я даю **мамі**». This means "I give to mom". Цей відмінок також описує стан. Наприклад, «**мені** подобається». This translates to "I like".
**Орудний відмінок** is the instrumental case. Він вказує на інструмент дії. Наприклад, «я пишу **ручкою**». This means "I write with a pen". Ми використовуємо прийменник «з» та орудний відмінок для сумісної дії. Наприклад, «кава з **молоком**». This is "coffee with milk". Якщо ми не маємо чогось, ми використовуємо прийменник «без» та родовий відмінок. Наприклад, «кава без **молока**». This is "coffee without milk".

**Місцевий відмінок** is the locative case. Він завжди вживається з прийменниками «у», «в» та «на». Він показує місце дії. Наприклад, «ми вчимося у **школі**». This means "we study at school".
**Кличний відмінок** is the vocative case. Ми використовуємо його виключно для звертання. Наприклад, ми кажемо «**Друже**!». This means "Friend!". Також кажемо «**Оксано**!» або «**Пане**!». These mean "Oksana!" and "Sir!".
The vocative case is a living, essential feature of the Ukrainian language. Це не архаїзм. Використання називного відмінка замість кличного — це поширена помилка. Українська мова завжди вимагає кличного відмінка при звертанні.

Давайте розглянемо типові помилки на рівні А2. Не забувайте про літеру «н» у займенниках третьої особи. Після прийменників ми завжди додаємо цю літеру. Правильно казати «про **нього**». This means "about him". Неправильно казати «про його».
Пам'ятайте про родовий відмінок після заперечення. Ми кажемо «я не маю **часу**».
Зверніть увагу на чергування приголосних у місцевому та давальному відмінках. Приголосні «г», «к», «х» змінюються на «з», «ц», «с» перед закінченням «-і». Правильно казати «у **руці**». This means "in the hand". Також правильно «на **дорозі**». This means "on the road".

<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->

В українській мові числівники вимагають різних відмінків. The word **один** means "one". Він змінюється як прикметник. Він має однаковий рід та відмінок з іменником. Наприклад, «один **зошит**» або «одна **книга**» у називному відмінку. These mean "one notebook" and "one book".
Після числівників 2, 3 та 4 ми використовуємо називний відмінок множини. Наприклад, «три **зошити**». This translates to "three notebooks".
Після числівників від 5 і більше ми використовуємо родовий відмінок множини. Наприклад, «п'ять **зошитів**». This means "five notebooks". Також «десять **книг**». This translates to "ten books".


## Дієслово: вид, час, спосіб
> — **Олена:** Максиме, ти готовий до тесту на рівень B1? Are you ready for the B1 level test?
> — **Максим:** Майже готовий. I am almost ready. Але я хочу повторити **дієслово**. The word "дієслово" means "verb".
> — **Олена:** Добре. Good. Давай згадаємо **вид**. The word "вид" means "aspect". Що таке **доконаний** і **недоконаний** вид? These mean "perfective" and "imperfective".
> — **Максим:** Недоконаний вид — це тривалий процес. Imperfective aspect is a continuous process. Доконаний вид — це результат. Perfective aspect is a result.
> — **Олена:** Правильно. Correct. Кожне дієслово зазвичай має пару. Every verb usually has a pair. Це видова **пара**. The word "пара" means "pair".
> — **Максим:** А як щодо дієслів руху? What about verbs of motion? Префікси змінюють їхнє значення. Prefixes change their meaning.
> — **Олена:** Так, префікси дуже важливі. Yes, prefixes are very important. П'ємо каву і продовжуємо нашу розмову. Let's drink coffee and continue.

В українській мові категорія виду дуже важлива. The category of aspect is very important. Недоконаний вид означає тривалий процес або регулярну дію. It means a continuous process or regular action. Використовуйте його, коли дія постійно повторюється. Use it when the action repeats. Наприклад, ми кажемо «я щодня **купував** хліб». This means "I bought bread every day". Доконаний вид означає конкретний результат або завершену дію. It means a specific result or a completed action. Наприклад, ми кажемо «я **купив** хліб». This means "I bought bread". Дієслова часто утворюють видові пари. Verbs often form aspectual pairs. Зазвичай ми додаємо префікс. Usually we add a prefix. Наприклад, «робити» і «зробити». These mean "to do" and "to make". Іноді ми змінюємо суфікс. Sometimes we change the suffix. Наприклад, «купувати» і «купити». These mean "to buy". А іноді слова в парі зовсім різні. Sometimes words in a pair are completely different. Наприклад, «говорити» і «сказати». These mean "to speak" and "to say". Ви повинні запам'ятати обидва слова. You must memorize both words.

Ми маємо три способи сказати про майбутнє. We have three ways to talk about the future. Перший спосіб — це доконаний вид. The first way is the perfective aspect. Дієслово змінюється як у теперішньому часі, але означає майбутнє. The verb changes like in the present tense, but means the future. Наприклад, ми кажемо «я **прочитаю** книгу». This means "I will read the book completely". Це означає, що я точно закінчу цю дію. This means I will finish the action. Другий спосіб — це складений майбутній час. The second way is the compound future tense. Ми використовуємо допоміжне слово «буду» та інфінітив. We use the auxiliary word "буду" and the infinitive. Наприклад, ми кажемо «я **буду читати**». This means "I will be reading". Це означає процес у майбутньому. This means a process in the future. Третій спосіб — це ще одна форма. The third way is another form. Ми додаємо закінчення прямо до інфінитива. We add an ending directly to the infinitive. Наприклад, ми кажемо «я **читатиму**». This translates to "I will be reading". Другий і третій способи абсолютно однакові за значенням. The second and third ways are identical in meaning. 

Ми також використовуємо умовний і наказовий спосіб. We also use the conditional and imperative moods. Умовний спосіб допомагає нам говорити про мрії або бажання. The conditional mood helps us talk about dreams or wishes. Ми використовуємо слово «якби» та частку «б» або «би». We use the word "якби" and the particle "б" or "би". Наприклад, ми кажемо «**якби** я мав час, я **б** поїхав у гори». This means "if I had time, I would go to the mountains". Наказовий спосіб потрібен для прохань або наказів. The imperative mood is needed for requests or commands. Його форма завжди залежить від ситуації спілкування. Its form depends on the communication situation. Ввічлива форма або форма для багатьох людей має закінчення «-те». The polite or plural form has the ending "-те". Наприклад, ми кажемо «**читайте** цей текст». This translates to "read this text". Дружня форма для однієї людини зазвичай коротша. The friendly form for one person is shorter. Наприклад, ми кажемо «**прочитай** цю статтю». This means "read this article completely".

Давайте коротко згадаємо дієслова руху. Let's briefly remember verbs of motion. Вони традиційно бувають двох типів. They are traditionally of two types. Дієслова «іти» та «їхати» означають рух в один бік. The verbs "іти" and "їхати" mean movement in one direction. Дієслова «ходити» та «їздити» означають регулярний рух туди і назад. The verbs "ходити" and "їздити" mean regular movement back and forth. Різні префікси додають цим дієсловам новий просторовий зміст. Different prefixes add new spatial meaning to these verbs. Префікс «при-» завжди означає прибуття до мети. The prefix "при-" means arrival at a destination. Наприклад, ми кажемо «він **прийшов**». This translates to "he arrived". Префікс «ви-» означає рух назовні з приміщення. The prefix "ви-" means movement outward from a room. Наприклад, ми кажемо «вона **виїхала**». This translates to "she drove out". Префікс «по-» означає початок руху або відправлення. The prefix "по-" means the start of movement or departure. Наприклад, ми кажемо «поїзд **поїхав**». This means "the train departed".

<!-- INJECT_ACTIVITY: quiz-aspect-choice -->


## Прикметники, порівняння, займенники

Прикметники завжди узгоджуються з іменниками. Adjectives always agree with nouns. Вони мають однаковий рід, число та відмінок. They have the same gender, number, and case. Наприклад, ми кажемо «**новий** стіл». For example, we say "**new** table". Але ми кажемо «**нового** стола» у родовому відмінку. But we say "**of the new** table" in the genitive case. Українські прикметники мають тверду і м'яку групи. Ukrainian adjectives have a hard and a soft group. Тверда група має закінчення «-ий». The hard group has the ending "-ий". Наприклад, слово «новий». For example, the word "new". М'яка група має закінчення «-ій». The soft group has the ending "-ій". Наприклад, слово «**синій**». For example, the word "**dark blue**". У непрямих відмінках вони мають різні букви перед закінченням. In oblique cases, they have different letters before the ending. 

Ми часто порівнюємо різні предмети. We often compare different objects. Для цього ми використовуємо **вищий** та **найвищий** ступені порівняння. For this, we use the **comparative** and **superlative** degrees of comparison. Ми додаємо суфікси «-іш-» або «-ш-». We add the suffixes "-іш-" or "-ш-". Наприклад, «**теплий**» стає «**тепліший**». For example, "**warm**" becomes "**warmer**". Деякі слова змінюють корінь. Some words change the root. Слово «**добрий**» стає «**кращий**». The word "**good**" becomes "**better**". Щоб зробити найвищий ступінь, ми додаємо префікс «най-». To make the superlative degree, we add the prefix "най-". Наприклад, «**найкращий**». For example, "**the best**". Ніколи не кажіть «більш кращий». Never say "more better". Це граматично неправильно. This is grammatically incorrect. Для порівняння ми використовуємо слова «**ніж**» або «**за**». For comparison, we use the words "**than**" or "**than**". Наприклад, «він вищий **за** мене». For example, "he is taller **than** me".

Займенники замінюють іменники в реченні. Pronouns replace nouns in a sentence. Особові займенники також змінюються за відмінками. Personal pronouns also change by cases. Ми кажемо «**я**», але «**мене**» у родовому відмінку. We say "**I**", but "**me**" in the genitive case. Після прийменників ми додаємо букву «н» до займенників третьої особи. After prepositions, we add the letter "n" to third-person pronouns. Ми кажемо «з **ним**», а не «з їм». We say "with **him**", not "with him" (without 'n'). Дуже важливо правильно використовувати зворотний займенник «**свій**». It is very important to correctly use the reflexive pronoun "**one's own**". Він показує, що предмет належить підмету. It shows that the object belongs to the subject. Якщо ви скажете «він читає **його** книгу», це чужа книга. If you say "he reads **his** book", it is someone else's book. Правильно казати «він читає **свою** книгу». It is correct to say "he reads **his own** book".

Іноді ми не знаємо точно особу чи предмет. Sometimes we do not know the person or object exactly. Тоді ми використовуємо неозначені займенники. Then we use indefinite pronouns. Це слова «**хтось**» або «**щось**». These are the words "**someone**" or "**something**". Якщо предмета немає, ми беремо заперечні займенники. If the object is absent, we take negative pronouns. Це слова «**ніхто**» і «**ніщо**». These are the words "**no one**" and "**nothing**". В українській мові ми обов'язково використовуємо подвійне заперечення. In the Ukrainian language, we obligatorily use a double negative. Ми завжди додаємо частку «**не**» перед дієсловом. We always add the particle "**not**" before the verb. Наприклад, ми кажемо «**ніхто не знає**». For example, we say "**no one knows**".

В українській мові ми зазвичай використовуємо повні форми прикметників. In the Ukrainian language, we usually use full forms of adjectives. Іноді в літературі чи спеціальних виразах бувають короткі форми. Sometimes in literature or special expressions there are short forms. Наприклад, ми кажемо «**повен**» замість «повний». For example, we say "**full**" instead of "full" (long form). Також завжди звертайте увагу на правильний наголос. Also, always pay attention to the correct stress. Правильно ставте наголос у формах «**велика**» та «**великі**». Correctly place the stress in the forms "**big**" (feminine) and "**big**" (plural). Це робить вашу мову природною. This makes your language natural.

<!-- INJECT_ACTIVITY: group-sort-grammar-categories -->


## Складне речення: з'єднуємо думки

На рівні А2 ми вчимося будувати складні речення. At the A2 level, we learn to build complex sentences. Це наш міст до рівня В1. This is our bridge to the B1 level. Головні помічники для цього — **сполучники**. The main helpers for this are **conjunctions**. Найчастіше ми використовуємо «**що**». Most often we use "**that**". Наприклад, «я знаю, **що** ти тут». For example, "I know **that** you are here". Інший важливий сполучник — «**тому що**». Another important conjunction is "**because**". Він пояснює причину. It explains the reason. Наприклад, «я вчу українську, **тому що** люблю Україну». For example, "I study Ukrainian **because** I love Ukraine". Перед цими сполучниками ми завжди ставимо кому. Before these conjunctions, we always put a comma. 

В українській мові є різні стилі спілкування. In the Ukrainian language, there are different styles of communication. У розмові з друзями ми часто кажемо «**бо**». In conversation with friends, we often say "**because/for**". Це коротке і зручне слово. This is a short and convenient word. Наприклад: «Я не прийшов, **бо** захворів». For example: "I didn't come **because** I got sick". Сполучник «**тому що**» є нейтральним. The conjunction "**because**" is neutral. В офіційних текстах ми використовуємо «**через те що**». In official texts, we use "**due to the fact that**". Наприклад: «Рейс скасували **через те що** почалася буря». For example: "The flight was canceled **due to the fact that** a storm started". Вибір залежить від ситуації. The choice depends on the situation.

Для умови ми беремо сполучник «**якщо**». For a condition, we take the conjunction "**if**". Він показує залежність однієї дії від іншої. It shows the dependence of one action on another. Наприклад: «**Якщо** буде сонце, ми підемо гуляти». For example: "**If** there is sun, we will go for a walk". Щоб показати мету, ми використовуємо «**щоб**». To show a goal, we use "**in order to**". Після нього ми ставимо дієслово в інфінітиві або в минулому часі. After it, we put the verb in the infinitive or in the past tense. Наприклад: «Я читаю, **щоб** знати більше». For example: "I read **in order to** know more". Або: «Я хочу, **щоб** ти прийшов». Or: "I want you to come" (literally: that you came). Минулий час тут означає бажання, а не минуле. The past tense here means a wish, not the past.

Давайте послухаємо, як студент розповідає про свій прогрес. Let's listen to how a student talks about their progress.
> — **Вчителька:** Марку, як твої успіхи? *(Mark, how is your progress?)*
> — **Марко:** Я вже говорю краще, **хоча** роблю **помилки**. *(I speak better already, **although** I make **mistakes**.)*
> — **Вчителька:** Це нормально! *(That's normal!)*
> — **Марко:** **Коли** я починав, я знав тільки прості слова. *(**When** I started, I knew only simple words.)*
> — **Вчителька:** А зараз ти знаєш багато правил **граматики**. *(And now you know many rules of **grammar**.)*
> — **Марко:** Так, я вчуся, **щоб** перейти на рівень В1. *(Yes, I study **in order to** move to the B1 level.)*
> — **Вчителька:** **Якщо** ти будеш так вчитися, у тебе все вийде! *(**If** you study like this, you will succeed!)*
> — **Марко:** Дякую! Я впевнений, **що** це можливо. *(Thank you! I am confident **that** it is possible.)*

<!-- INJECT_ACTIVITY: error-correction -->


## Самооцінка і перехід до B1

Час зробити паузу і подивитися на свої результати. Time to take a pause and look at your results. Давайте проведемо невелику самооцінку. Let's do a small self-assessment. Оцініть свою **впевненість** (confidence) від одного до п'яти за такими пунктами. Rate your confidence from one to five on these points.

1. Використання всіх семи відмінків без таблиці. Using all seven cases without a table.
2. Розуміння різниці між дієсловами «писати» і «написати». Understanding the difference between the verbs "to write" and "to have written".
3. Природне порівняння різних речей. Natural comparison of different things.
4. Правильне використання займенника «свій». Correct use of the pronoun "one's own".
5. Розуміння українських граматичних термінів. Understanding of Ukrainian grammatical terms.

Якщо ваша оцінка висока — це чудовий результат. If your score is high — this is an excellent result. Якщо ні, варто зробити **повторення** (review). If not, it is worth doing a review.

Перехід від рівня А2 до В1 — це великий крок. The transition from level A2 to B1 is a big step. Що зміниться? What changes? Головне — це занурення в мову. The main thing is immersion in the language. На рівні В1 інструкції до вправ будуть лише українською. At level B1, instructions for exercises will be only in Ukrainian. Також ми почнемо вивчати нову термінологію. Also, we will start learning new terminology. Ви дізнаєтеся, що таке **дієвідміна** (conjugation). You will learn what a conjugation is. Ми детально розглянемо кожну **відміну** (declension) іменників. We will examine in detail each declension of nouns. Ви також зрозумієте українське **чергування** (alternation) звуків. You will also understand the Ukrainian alternation of sounds. Це зробить вашу мову ще природнішою. This will make your speech even more natural.

<!-- INJECT_ACTIVITY: error-correction-final-review -->

**Підсумок** (Summary).
Ви завершили велику подорож рівнем А2. You have completed a great journey through level A2. Тепер ви можете говорити про минуле, теперішнє і майбутнє. Now you can talk about the past, present, and future. Ви знаєте, як показати процес або результат дії. You know how to show the process or result of an action. Ви вмієте орієнтуватися в системі семи відмінків. You know how to navigate the seven-case system. Ваші речення стали довшими. Your sentences have become longer. Ви можете будувати логічні аргументи через сполучники. You can build logical arguments through conjunctions.

Наступний крок — рівень В1. The next step is level B1. Там мова буде не просто предметом вивчення, а засобом спілкування. There the language will not be just a subject of study, but a medium of communication. Продовжуйте практикуватися щодня. Continue to practice every day. Дякую за вашу працю і до зустрічі! Thank you for your work and see you!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a2-comprehensive-review
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

**Level: A2 (Module 67/60) — ELEMENTARY**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

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
