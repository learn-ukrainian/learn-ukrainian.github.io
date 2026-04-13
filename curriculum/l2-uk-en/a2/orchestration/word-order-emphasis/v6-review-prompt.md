<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 50: Порядок слів і наголос у реченні (A2, A2.7 [Complex Sentences and Conditionals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-050
level: A2
sequence: 50
slug: word-order-emphasis
version: '1.0'
title: Порядок слів і наголос у реченні
subtitle: Тема і рема, інверсія для контрасту та природний порядок слів
focus: grammar
pedagogy: PPP
phase: A2.7 [Complex Sentences and Conditionals]
word_target: 2000
objectives:
  - Learner can identify theme (тема, known information) and rheme (рема,
    new information) in Ukrainian sentences and understand that rheme
    typically comes last.
  - Learner can use fronting (moving a word to sentence-initial position) to
    create emphasis or contrast (Книгу я вже прочитав, not *Я вже прочитав
    книгу when emphasizing "the book specifically").
  - Learner can distinguish neutral word order (SVO) from marked word order
    and understand the communicative effect of each.
  - Learner can produce natural Ukrainian sentences where word order conveys
    meaning beyond what grammar alone encodes.
dialogue_situations:
  - setting: 'Roommates dividing chores — clarifying who does what: Хто
      помив посуд? — Посуд помив Тарас. А підлогу? — Підлогу ще ніхто не
      помив. Добре, підлогу помию я.'
    speakers:
      - Оленка
      - Марійка
    motivation: 'Natural fronting for contrast: Посуд помив Тарас (посуд =
      theme, Тарас = rheme). Підлогу помию я (підлогу = theme, я = rheme)'
  - setting: 'Friends discussing a movie — disagreeing about details: Цей
      фільм зняв Сенцов. — Ні, цей фільм зняв не Сенцов, а Лозниця. —
      А от «Номери» — це точно Сенцов зняв.'
    speakers:
      - Друг 1
      - Друг 2
    motivation: 'Contrast through word order shift: neutral (Сенцов зняв
      фільм) vs. contrastive (Цей фільм зняв Сенцов) vs. corrective
      (не Сенцов, а Лозниця)'
content_outline:
  - section: 'Тема і рема: що відоме, що нове? (Theme and Rheme)'
    words: 550
    points:
      - 'Every sentence has two parts: тема (theme, the known/given info,
        what the sentence is about) and рема (rheme, the new info, the
        communicative focus).'
      - 'In neutral Ukrainian word order, тема comes first and рема comes
        last: Тарас (theme) купив нову книгу (rheme). The "news" is at
        the end.'
      - 'Test: answer a question. Хто купив книгу? → Книгу купив Тарас
        (Тарас is the new info = rheme = last). Що купив Тарас? → Тарас
        купив книгу (книгу = rheme = last).'
      - 'This is different from English, where word order is grammatically
        fixed (SVO). Ukrainian uses word order for MEANING — the grammar
        is encoded in case endings, so word order is free to convey emphasis.'
  - section: 'Прямий порядок слів (Neutral Word Order)'
    words: 500
    points:
      - 'Default neutral order: Subject + Predicate + Object (SVO): Студент
        читає книгу. Мама готує вечерю. This is the unmarked, emotionally
        neutral order.'
      - 'Adjective before noun: нова книга, великий будинок (same as English).
        Adverb before verb or after: добре працює / працює добре (both OK,
        but emphasis shifts).'
      - 'Time expressions typically go first or last: Вчора ми ходили в кіно.
        Ми ходили в кіно вчора. (Вчора first = neutral context-setting;
        вчора last = emphasizing "it was yesterday").'
      - 'Practice: identify the neutral word order in sentences and explain
        what the theme and rheme are.'
  - section: 'Інверсія для контрасту (Fronting for Contrast)'
    words: 600
    points:
      - 'Fronting the object: Книгу я вже прочитав (I''ve already read THE
        BOOK — as opposed to something else). The object moves to the front
        to become the theme, and the subject shifts to become part of the
        rheme.'
      - 'Fronting the verb: Прочитав я цю книгу! (emphatic, expressive —
        I DID read this book!). Verb-first order conveys strong assertion
        or emotional emphasis.'
      - 'Corrective contrast: Не Тарас це зробив, а Олег. (Not Taras did
        this, but Oleh.) The corrected element is fronted with не...а.'
      - 'Cleft-like patterns: Це Тарас допоміг мені. (It was Taras who
        helped me.) Це + noun identifies the rheme explicitly.'
      - 'Practice: transform neutral sentences into emphatic ones by changing
        word order, then explain the shift in meaning.'
  - section: 'Порядок слів у реальному мовленні (Word Order in Real Speech)'
    words: 350
    points:
      - 'In conversation, word order constantly shifts based on what is known
        vs. new. Practice with mini-dialogues where each answer reorders
        the sentence to highlight the new information.'
      - 'Common patterns: — Хто це зробив? — Це зробив Тарас. (SVO → OVS).
        — Що ти купив? — Я купив каву. (neutral SVO stays).'
      - 'Reading practice: identifying word order shifts in a short Ukrainian
        text and explaining why the author chose that order.'
vocabulary_hints:
  required:
    - порядок (order)
    - речення (sentence)
    - тема (theme, topic (linguistics))
    - рема (rheme, new information)
    - наголос (stress, emphasis)
    - інверсія (inversion)
    - контраст (contrast)
    - підкреслювати (to emphasize, to underline)
    - початок (beginning)
    - кінець (end)
  recommended:
    - виділяти (to highlight, to single out)
    - означення (attribute, modifier)
    - нейтральний (neutral)
    - емфатичний (emphatic)
    - акцент (accent, emphasis)
activity_hints:
  - type: quiz
    focus: 'Identify the rheme (new information) in each sentence based on
      the question it answers'
    items: 8
  - type: match-up
    focus: Match questions with the correctly word-ordered answers (Хто
      приїхав? → Приїхав Тарас, not Тарас приїхав)
    items: 8
  - type: fill-in
    focus: Reorder words to create the correct emphasis for a given context
      (the book / I / already / read → for emphasis on "the book")
    items: 8
  - type: group-sort
    focus: Sort sentences into neutral word order vs. marked/emphatic word
      order
    items: 8
  - type: error-correction
    focus: 'Fix sentences where word order creates unintended emphasis
      (e.g., answering "What did you buy?" with *Каву купив я instead
      of Я купив каву)'
    items: 6
references:
  - title: Заболотний Grade 8, §10-12
    notes: Порядок слів у реченні, прямий і зворотний порядок
  - title: Авраменко Grade 8, §6-7
    notes: Тема і рема, актуальне членування речення
  - title: 'ULP: Ukrainian Word Order'
    url: https://www.ukrainianlessons.com/word-order/
    notes: How Ukrainian word order differs from English

</plan_content>

## Generated Content

<generated_module_content>
## Тема і рема: що відоме, що нове? (Theme and Rheme) (~600 words total)

You have probably heard that Ukrainian has a "free" word order. While grammar does not strictly dictate where each word must go, the arrangement is far from random. The structure of a sentence is driven by the flow of information. Every statement is divided into two parts: what is already known, called the theme, and the new, important information, called the rheme.

Українська мова має вільний **порядок** (order) слів. Але це не означає, що слова можна ставити як завгодно. Структура **речення** (sentence) залежить від інформації, яку ми хочемо передати. Кожне висловлювання має дві частини: те, що вже відоме, або **тема** (theme), і нова важлива інформація, або **рема** (rheme).

> *Ukrainian has a free word order. But this does not mean that words can be placed however you want. The structure of a sentence depends on the information we want to convey. Every utterance has two parts: what is already known, or the theme, and the new important information, or the rheme.*

The fundamental rule of Ukrainian information structure is simple. In a neutral context, the known information comes first, and the new information comes at the very end of the sentence. The "news" is always delivered last. This final position naturally carries the logical stress of the statement.

Основне правило дуже просте. У нейтральній ситуації тема стоїть на початку, а рема йде в самий **кінець** (end). Найголовніша новина завжди звучить останньою. Саме це останнє слово отримує логічний **наголос** (stress, emphasis). Наприклад, ми кажемо: «Тарас купив нову книгу». Тут ми вже знаємо про Тараса, а нова інформація — це його покупка.

> *The basic rule is very simple. In a neutral situation, the theme stands at the beginning, and the rheme goes to the very end. The most important news always sounds last. It is this last word that receives the logical stress. For example, we say: "Taras bought a new book." Here we already know about Taras, and the new information is his purchase.*

You can easily test for the theme and rheme by asking a question that the sentence answers. The question itself contains the known information, while the answer provides the rheme. 

Ми можемо легко знайти тему і рему за допомогою питання. Якщо хтось питає «Хто купив книгу?», то книга нам уже відома. Нова інформація — це людина. Тому ми кажемо: «Книгу купив Тарас». Тут слово «Тарас» — це рема, і воно стоїть у кінці. Якщо ж питання «Що купив Тарас?», то Тарас нам відомий. Ми відповідаємо: «Тарас купив книгу». Тепер слово «книга» є ремою і стоїть наприкінці.

> *We can easily find the theme and rheme with the help of a question. If someone asks "Who bought the book?", then the book is already known to us. The new information is the person. Therefore, we say: "The book was bought by Taras".
 Here the word "Taras" is the rheme, and it stands at the end. But if the question is "What did Taras buy?", then Taras is known to us. We answer: "Taras bought a book." Now the word "book" is the rheme and stands at the end.*

This system contrasts directly with English. English relies on a rigid Subject-Verb-Object order to show who is doing what to whom. To shift emphasis in English, you often have to use vocal intonation or complex phrasing. Ukrainian, however, uses case endings to show grammatical roles. The difference between the nominative «мама» and the accusative «доньку» tells you exactly who is acting and who is receiving the action. This frees up the word order to handle meaning and communicative focus.

В українській мові закінчення відмінків показують ролі слів. Речення «Мама любить доньку» і «Доньку любить мама» означають те саме граматично. Але вони мають абсолютно різні акценти. Перше відповідає на питання «Кого любить мама?», а друге — «Хто любить доньку?». 

> *In the Ukrainian language, case endings show the roles of words. The sentences "Mom loves the daughter" and "The daughter loves mom" mean the same thing grammatically. But they have completely different emphases. The first answers the question "Who does mom love?", and the second — "Who loves the daughter?".*

Mastering Ukrainian word order means learning to place the communicative focus at the end of the sentence naturally. Instead of relying solely on your voice to highlight a word, you use the structure of the sentence itself.

:::info
**Logical stress**
In written Ukrainian, the position of a word often does the heavy lifting for emphasis. While you can speak louder to emphasize a word, moving it to the end of the sentence is the most natural way to show it is the new, important information.
:::

<!-- INJECT_ACTIVITY: quiz-identify-rheme -->

## Прямий порядок слів (Neutral Word Order) (~550 words total)

Now that we understand how new information naturally flows to the end of a sentence, let's look at the default structure. When you just want to report a fact, write an essay, or start a story without any special emotional emphasis, you use the direct word order. This is the neutral, unmarked way to build a sentence in Ukrainian. The core structure is Subject + Predicate + Object, just like in English.

Прямий **порядок** (order) слів — це базова модель для українського **речення** (sentence). Цей порядок є емоційно нейтральним. Його часто використовують у новинах, документах або на **початку** (beginning) тексту. Підмет стоїть перед присудком, а додаток іде після нього. Наприклад, ми кажемо: «Студент читає книгу» або «Молоде покоління прагне свободи».

> *The direct word order is the basic model for a Ukrainian sentence. This order is emotionally neutral. It is often used in news, documents, or at the beginning of a text. The subject stands before the predicate, and the object goes after it. For example, we say: "A student is reading a book" or "The young generation desires freedom."*

What about descriptive words? The neutral placement of modifiers is also quite predictable. Adjectives naturally go directly before the noun they describe. Adverbs of manner, which describe how an action is done, are quite flexible. They typically sit close to the verb, either right before or right after it, with minimal shift in meaning.

У прямому порядку прикметник зазвичай стоїть перед іменником. Ми кажемо «нова книга» або «тихий світанок». Прислівники можуть стояти перед дієсловом або після нього. Фрази «він добре працює» та «він працює добре» є правильними. Обидва варіанти звучать природно, але порядок слів може трохи зміщувати акцент.

> *In the direct order, an adjective always stands before a noun. We say "a new book" or "a quiet dawn". Adverbs can stand before a verb or after it. The phrases "він добре працює" and "він працює добре" are correct. Both variants sound natural and barely change the meaning.*

There is a critical error that English speakers often make when placing adjectives. In English, you can put an adjective after a noun to create a poetic phrase, like "a dawn so quiet." In Ukrainian, swapping the adjective and the noun changes the sentence structure entirely.

Позиція прикметника є дуже важливою. Фраза «тихий світанок» — це іменник з означенням. А «світанок тихий» у звичайному контексті вже сприймається як речення: слово «світанок» є підметом, а слово «тихий» входить до складу присудка. Це не означає, що прикметник стає дієсловом, але він уже не просто означення.

> *The position of the adjective is very important. The phrase "a quiet dawn" is just a noun with a modifier. But if you say "the dawn is quiet," you create a complete sentence. Here the word "dawn" is the subject, and the word "quiet" becomes the predicate. This means the adjective plays the role of a verb.*

:::info
**Adjective as a predicate**
Remember that Ukrainian often omits the present tense verb "to be" (є). Because of this, an adjective placed *after* a noun («Книга цікава») functions as part of the predicate ("The book *is* interesting). An adjective placed *before* a noun («Цікава книга») is just a modifier ("An interesting book").
:::

Next, we need to consider the placement of time and place expressions. These words tell us when or where an action happens. In a neutral sentence, they usually sit at the very beginning to set the scene for the listener. Alternatively, they can go at the very end if the time or place itself is the neutral focus of the sentence.

Слова, які вказують на час або місце, часто стоять на початку. Наприклад, ми кажемо: «Вчора ми ходили в кіно». Це нейтрально описує ситуацію. Якщо ми хочемо **підкреслювати** (to emphasize) час, ми ставимо це слово в **кінець** (end). Речення «Ми ходили в кіно вчора» робить акцент саме на тому, коли це сталося.

> *Words that indicate time or place often stand at the beginning. For example, we say: "Yesterday we went to the cinema." This neutrally describes the situation. If we want to emphasize the time, we put this word at the end. The sentence "We went to the cinema yesterday" puts the accent exactly on when it happened.*

While direct order is the essential baseline for clear communication, you shouldn't feel locked into it. Sticking to a strict Subject-Verb-Object structure all the time in conversation will actually sound slightly robotic or overly formal to native speakers. Natural speech constantly shifts words around to react to new information.

Прямий порядок слів — це чудовий старт для вивчення мови. Він допомагає будувати чіткі та зрозумілі фрази. Але в реальній розмові українці рідко говорять тільки так. Ми постійно змінюємо порядок слів, щоб зробити мову живою та емоційною.

> *The direct word order is a great start for learning the language. It helps to build clear and understandable phrases. But in real conversation, Ukrainians rarely speak only like this. We constantly change the word order to make the speech alive and emotional.*

<!-- INJECT_ACTIVITY: group-sort-neutral-emphatic -->

## Інверсія для контрасту (Fronting for Contrast) (~650 words total)

We have seen that the direct word order gives us a neutral, calm sentence. But what happens when we want to sound emotional, highlight a specific detail, or argue with someone? In these situations, Ukrainians break the neutral pattern. We use indirect word order to move an important word to a completely different position.

Такий зворотний порядок слів називається **інверсія** (inversion). Вона допомагає нам створити сильний **контраст** (contrast) або додати емоцій. Ми виносимо важливе слово на перше місце, щоб одразу показати головну ідею.

> *Such indirect word order is called inversion. It helps us create a strong contrast or add emotions. We bring an important word to the first place to immediately show the main idea.*

Let's see how inversion works when people disagree. Imagine two friends discussing a movie they just watched. Pay attention to which words they put at the beginning.

> — **Антон:** Цей фільм зняв Сенцов. *(Sentsov directed this movie.)*
> — **Марина:** Ні, цей фільм зняв не Сенцов, а Лозниця. *(No, not Sentsov directed this movie, but Loznitsa.)*
> — **Антон:** Можливо. А от «Номери» — це точно Сенцов зняв. *(Maybe. But "Numbers" — Sentsov definitely directed that.)*

В українській мові ми дуже часто ставимо додаток на **початок** (beginning) речення. Подивіться на першу фразу з нашого діалогу. Прямий **порядок** (order) мав би бути таким: «Сенцов зняв цей фільм». Але Антон свідомо змінив структуру. Він поставив об'єкт на перше місце.

> *In the Ukrainian language, we very often put the object at the beginning of the sentence. Look at the first phrase from our dialogue. The direct order should have been like this: "Sentsov directed this movie." But Anton consciously changed the structure. He put the object in the first place.*

Тепер об'єкт став відомою інформацією, а режисер Сенцов перемістився в самий **кінець** (end) фрази. Слово «Сенцов» — це нова інформація, або **рема** (rheme). Такий незвичний варіант показує, що головний **наголос** (stress) робиться саме на авторі.

> *Now the object became the known information, and director Sentsov moved to the very end of the phrase. The word "Sentsov" is the new information, or rheme. Such an unusual variant shows that the main stress is placed exactly on the author.*

:::note
**The Object-Verb-Subject pattern**
Moving the object to the front (OVS) is one of the most common ways to say "As for X...". It establishes the object as the known context and saves the "news" (who did it) for the end.
:::

Another powerful way to use inversion is to put the verb at the very beginning of the sentence. This creates a strong emotional effect, a very firm assertion, or an energetic start to a story.

Іноді ми хочемо показати сильні емоції або наполегливо довести свою правоту. Тоді ми сміливо ставимо дієслово на перше місце. Нейтральне **речення** (sentence) звучить так: «Я прочитав цю книгу». Але якщо хтось сумнівається у ваших словах, ви емоційно скажете: «Прочитав я цю книгу!». Це звучить дуже впевнено. Також дієслово часто починає нову історію або казку. Наприклад: «Прийшла тепла весна», «Почалася сильна злива». Тут немає ніякого конфлікту, але є приємна динаміка.

> *Sometimes we want to show strong emotions or persistently prove we are right. Then we boldly put the verb in the first place. A neutral sentence sounds like this: "I read this book." But if someone doubts your words, you will emotionally say: "I DID read this book!". This sounds very confident. Also, a verb often starts a new story or a fairy tale. For example: "Warm spring came," "A heavy downpour began." There is no conflict here, but there is pleasant dynamics.*

When you need to explicitly correct someone's statement, you will also use a specific type of fronting. You bring the corrected element forward and use the construction "не... а" (not... but). This immediately halts the previous assumption and replaces it with the truth.

Щоб чітко **підкреслювати** (to emphasize) чиюсь помилку, ми виносимо неправильний факт уперед. У нашому короткому діалозі Марина каже: «цей фільм зняв не Сенцов, а Лозниця». Вона не каже нейтрально: «Лозниця зняв цей фільм». Вона використовує структуру «не А, а Б», щоб одразу виправити друга. Ще один гарний приклад: «Не Тарас це зробив, а Олег». Фокус цього висловлювання падає саме на виправлення неправильної інформації.

> *To clearly emphasize someone's mistake, we bring the incorrect fact forward. In our short dialogue, Maryna says: "not Sentsov directed this movie, but Loznitsa." She does not say neutrally: "Loznitsa directed this movie." She uses the structure "not A, but B" to immediately correct her friend. Another good example: "Not Taras did this, but Oleh." The focus of this utterance falls exactly on correcting the wrong information.*

Finally, Ukrainian has a very clear way to identify the new information right at the start of the sentence, similar to the English "It is X who..." pattern. We use the word "Це" (This / It is) followed by the noun we want to highlight.

Слово «це» допомагає нам чітко виділити головну дійову особу. Ви ставите слово «це» на перше місце, щоб показати автора дії. Наприклад: «Це Тарас допоміг мені». Це означає, що саме він вчасно запропонував допомогу. Ця маленька граматична частка допомагає явно виділити головну **рему** (rheme) або фокус висловлювання.

> *The word "це" helps us clearly highlight the main character. You put the word "це" in the first place to show the author of the action. For example: "It was Taras who helped me." This means that exactly he offered help in time. This small grammatical particle shows where the main theme of your story is.*

:::tip
**Using "Це" for emphasis**
Placing "Це" before a noun at the start of a sentence is the most direct equivalent to English cleft sentences ("It was X who did Y"). It leaves absolutely no doubt about who or what the focus is.
:::

<!-- INJECT_ACTIVITY: fill-in-reorder-emphasis -->

## Порядок слів у реальному мовленні (Word Order in Real Speech) (~400 words total)

In real life, word order constantly shifts depending on the flow of conversation. 

> — **Оленка:** Хто помив посуд? *(Who washed the dishes?)*
> — **Марійка:** Посуд помив Тарас. *(Taras washed the dishes.)*
> — **Оленка:** А підлогу? *(And the floor?)*
> — **Марійка:** Підлогу ще ніхто не помив. *(Nobody has washed the floor yet.)*
> — **Оленка:** Добре, підлогу помию я. *(Okay, I will wash the floor.)*

У цьому діалозі ми бачимо природний **порядок** (order) слів. Кожне нове **речення** (sentence) спирається на попереднє. Оленка запитує про посуд. Тепер посуд — це відома інформація, тобто **тема** (theme, topic (linguistics)). Тому у відповіді Марійка ставить це слово на **початок** (beginning). Слово «Тарас» — це нова інформація, тобто **рема** (rheme, new information). Ця нова інформація йде в **кінець** (end). Те саме відбувається зі словом «підлога».

> *In this dialogue, we see natural word order. Each new sentence builds on the previous one. Olenka asks about the dishes. Now the dishes are known information, meaning the theme. Therefore, in her answer, Mariyka puts this word at the beginning. The word "Taras" is new information, meaning the rheme. This new information goes to the end. The same thing happens with the word "floor".*

When you answer a question, the question itself tells you what the theme is and what the rheme will be. This is why listening carefully to your conversation partner is so important. If someone asks «Що ти купив?» (What did you buy?), the neutral SVO order works perfectly. You simply say «Я купив каву» (I bought coffee), because the coffee is the new information. But what if the question is «Хто це купив?» (Who bought this?)? Here, the object is already known to both speakers. You must use an **інверсія** (inversion) to put the object first and the new subject last. You answer: «Це купив я» (I bought it).

Українська мова дуже гнучка, але не перекладайте англійські фрази механічно. Неправильний порядок слів може створити сильний і небажаний **контраст** (contrast). Якщо ви відповісте «Каву купив я», це звучатиме вкрай дивно. Такий **наголос** (stress, emphasis) означає: «Саме я купив цю каву». Співрозмовник може подумати, що ви сперечаєтеся з ним. Ви не повинні **підкреслювати** (to emphasize, to underline) слово «я» без причини.

> *The Ukrainian language is very flexible, but do not translate English phrases mechanically. The wrong word order can create a strong and unwanted contrast. If you answer "Каву купив я", it will sound extremely strange. Such emphasis means: "It was exactly me who bought this coffee." Your conversation partner might think that you are arguing with them. You should not emphasize the word "I" without a reason.*

:::tip
**Listen to the question!**
The easiest way to sound natural in Ukrainian is to mirror the question. The word that replaces the question word (хто, що, коли, де) should usually go at the very end of your answer.
:::

Завжди уважно слухайте питання співрозмовника. Питання допомагає побудувати правильну та природну відповідь. З часом ви почнете відчувати мелодику мови. Якщо хочете побачити шкільне формулювання теми, порівняйте пояснення в Заболотного (§10-12), Авраменка (§6-7) і короткий огляд Ukrainian Lessons Project про Ukrainian word order.

<!-- INJECT_ACTIVITY: match-up-questions-answers -->
<!-- INJECT_ACTIVITY: error-correction-unintended-emphasis -->
</generated_module_content>

**PIPELINE NOTE — Word count: 2914 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 424 words | Not found: 6 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Авраменка — NOT IN VESUM
  ✗ Антон — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Сенцов — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тараса — NOT IN VESUM

All 424 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
