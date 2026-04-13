<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/word-order-emphasis.yaml` file for module **50: Порядок слів і наголос у реченні** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-identify-rheme -->`
- `<!-- INJECT_ACTIVITY: group-sort-neutral-emphatic -->`
- `<!-- INJECT_ACTIVITY: fill-in-reorder-emphasis -->`
- `<!-- INJECT_ACTIVITY: match-up-questions-answers -->`
- `<!-- INJECT_ACTIVITY: error-correction-unintended-emphasis -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify the rheme (new information) in each sentence based on the question
    it answers
  items: 8
  type: quiz
- focus: Match questions with the correctly word-ordered answers (Хто приїхав? → Приїхав
    Тарас, not Тарас приїхав)
  items: 8
  type: match-up
- focus: Reorder words to create the correct emphasis for a given context (the book
    / I / already / read → for emphasis on "the book")
  items: 8
  type: fill-in
- focus: Sort sentences into neutral word order vs. marked/emphatic word order
  items: 8
  type: group-sort
- focus: Fix sentences where word order creates unintended emphasis (e.g., answering
    "What did you buy?" with *Каву купив я instead of Я купив каву)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- виділяти (to highlight, to single out)
- означення (attribute, modifier)
- нейтральний (neutral)
- емфатичний (emphatic)
- акцент (accent, emphasis)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Тема і рема: що відоме, що нове? (Theme and Rheme) (~600 words total)

You have probably heard that Ukrainian has a "free" word order. While grammar does not strictly dictate where each word must go, the arrangement is far from random. The structure of a sentence is driven by the flow of information. Every statement is divided into two parts: what is already known, called the theme, and the new, important information, called the rheme.

Українська мова має вільний **порядок** (order) слів. Але це не означає, що слова можна ставити як завгодно. Структура **речення** (sentence) залежить від інформації, яку ми хочемо передати. Кожне висловлювання має дві частини: те, що вже відоме, або **тема** (theme), і нова важлива інформація, або **рема** (rheme).

> *Ukrainian has a free word order. But this does not mean that words can be placed however you want. The structure of a sentence depends on the information we want to convey. Every utterance has two parts: what is already known, or the theme, and the new important information, or the rheme.*

The fundamental rule of Ukrainian information structure is simple. In a neutral context, the known information comes first, and the new information comes at the very end of the sentence. The "news" is always delivered last. This final position naturally carries the logical stress of the statement.

Основне правило дуже просте. У нейтральній ситуації тема стоїть на початку, а рема йде в самий **кінець** (end). Найголовніша новина завжди звучить останньою. Саме це останнє слово отримує логічний **наголос** (stress, emphasis). Наприклад, ми кажемо: «Тарас купив нову книгу». Тут ми вже знаємо про Тараса, а нова інформація — це його покупка.

> *The basic rule is very simple. In a neutral situation, the theme stands at the beginning, and the rheme goes to the very end. The most important news always sounds last. It is this last word that receives the logical stress. For example, we say: "Taras bought a new book." Here we already know about Taras, and the new information is his purchase.*

You can easily test for the theme and rheme by asking a question that the sentence answers. The question itself contains the known information, while the answer provides the rheme. 

Ми можемо легко знайти тему і рему за допомогою питання. Якщо хтось питає «Хто купив книгу?», то книга нам уже відома. Нова інформація — це людина. Тому ми кажемо: «Книгу купив Тарас». Тут слово «Тарас» — це рема, і воно стоїть у кінці. Якщо ж питання «Що купив Тарас?», то Тарас нам відомий. Ми відповідаємо: «Тарас купив книгу». Тепер слово «книга» є ремою і стоїть наприкінці.

> *We can easily find the theme and rheme with the help of a question. If someone asks "Who bought the book?", then the book is already known to us. The new information is the person. Therefore, we say: "The book was bought by Taras" (literally: "The book bought Taras"). Here the word "Taras" is the rheme, and it stands at the end. But if the question is "What did Taras buy?", then Taras is known to us. We answer: "Taras bought a book." Now the word "book" is the rheme and stands at the end.*

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

У прямому порядку прикметник завжди стоїть перед іменником. Ми кажемо «нова книга» або «тихий світанок». Прислівники можуть стояти перед дієсловом або після нього. Фрази «він добре працює» та «він працює добре» є правильними. Обидва варіанти звучать природно і майже не змінюють зміст.

> *In the direct order, an adjective always stands before a noun. We say "a new book" or "a quiet dawn". Adverbs can stand before a verb or after it. The phrases "він добре працює" and "він працює добре" are correct. Both variants sound natural and barely change the meaning.*

There is a critical error that English speakers often make when placing adjectives. In English, you can put an adjective after a noun to create a poetic phrase, like "a dawn so quiet." In Ukrainian, swapping the adjective and the noun changes the sentence structure entirely.

Позиція прикметника є дуже важливою. Фраза «тихий світанок» — це просто іменник з означенням. Але якщо ви скажете «світанок тихий», ви створите повне речення. Тут слово «світанок» є підметом, а слово «тихий» стає присудком. Це означає, що прикметник виконує роль дієслова.

> *The position of the adjective is very important. The phrase "a quiet dawn" is just a noun with a modifier. But if you say "the dawn is quiet," you create a complete sentence. Here the word "dawn" is the subject, and the word "quiet" becomes the predicate. This means the adjective plays the role of a verb.*

:::info
**Adjective as a predicate**
Remember that Ukrainian often omits the present tense verb "to be" (є). Because of this, an adjective placed *after* a noun («Книга цікава») acts as the verb ("The book *is* interesting"). An adjective placed *before* a noun («Цікава книга») is just a modifier ("An interesting book").
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

Слово «це» допомагає нам чітко виділити головну дійову особу. Ви ставите слово «це» на перше місце, щоб показати автора дії. Наприклад: «Це Тарас допоміг мені». Це означає, що саме він вчасно запропонував допомогу. Ця маленька граматична частка показує, де знаходиться головна **тема** (theme) вашої розповіді.

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

Завжди уважно слухайте питання співрозмовника. Питання допомагає побудувати правильну та природну відповідь. З часом ви почнете відчувати мелодику мови.

<!-- INJECT_ACTIVITY: match-up-questions-answers -->
<!-- INJECT_ACTIVITY: error-correction-unintended-emphasis -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: word-order-emphasis
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**Level: A2 (Module 50/60) — ELEMENTARY**

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

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
