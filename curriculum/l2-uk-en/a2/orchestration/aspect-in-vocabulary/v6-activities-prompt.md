<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-in-vocabulary.yaml` file for module **3: Дієслова ходять парами** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-find-partner -->`
- `<!-- INJECT_ACTIVITY: fill-in-categorize-formation -->`
- `<!-- INJECT_ACTIVITY: match-up-blanks-pairs -->`
- `<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Find the Partner (Verb Matching)
  items: 8
  type: quiz
- focus: Categorize by Formation Type
  items: 8
  type: fill-in
- focus: Fill in the Blanks with the Correct Pair
  items: 8
  type: match-up
- focus: Choose the Correct Aspect Partner
  items: 8
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- утворювати (to form)
- словник (dictionary)
- запам'ятовувати (to memorize)
- базовий (basic)
required:
- пара (pair)
- префікс (prefix)
- суфікс (suffix)
- корінь (root)
- читати / прочитати (to read)
- писати / написати (to write)
- брати / взяти (to take)
- говорити / сказати (to speak / to say)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чому дієслова потрібно вчити парами?

In Ukrainian, learning a new verb is a unique experience because you are rarely learning just a single word. Instead, you are learning an aspect pair (**видова пара**). Imagine trying to buy shoes, but you only buy the left one. It is useful, but you cannot walk far without its partner! When you learn the verb for writing, you must learn the word for the ongoing process alongside the word for the completed result. You need both halves to answer two completely different questions. 

**Що ти робив?** — *What were you doing?*
**Що ти зробив?** — *What have you done?*

В українській мові ми завжди вчимо дієслова парами. Кожна дія має дві різні форми. Одна форма описує довгий процес, а інша — готовий результат.

> *In the Ukrainian language, we always learn verbs in pairs. Every action has two different forms. One form describes a long process, and the other describes a finished result.*

Let us look at how this works in a cooking scenario. 

> — **Бабуся:** Ліпи вареники, поки я грію воду. *(Keep forming the varenyky while I heat the water.)*
> — **Онучка:** Я вже зліпила десять штук! *(I have already formed ten of them!)*
> — **Бабуся:** Тепер вари їх п'ять хвилин, поки вони не спливуть. *(Now boil them for five minutes until they float.)*
> — **Онучка:** А що робити потім? *(And what to do after?)*
> — **Бабуся:** Як звариш, клич усіх до столу! *(Once you have boiled them, call everyone to the table!)*

The logic behind these pairs is the contrast between process and result. The imperfective aspect describes the effort you put into an action, while the perfective aspect describes the final outcome. For example, the imperfective verb for cleaning emphasizes the physical act of working with a broom and a cloth. The perfective verb means the room is completely clean and the job is done. You should memorize these two forms as a single lexical unit, treating them like two halves of the same concept.

Недоконаний вид показує довгий процес і твою роботу. Доконаний вид показує успішний результат цієї роботи. Наприклад, ти можеш прибирати кімнату цілий день, але так і не прибрати її.

> *The imperfective aspect shows a long process and your work. The perfective aspect shows the successful result of this work. For example, you can be cleaning a room all day, but still not have cleaned it.*

Because these pairs are fundamental, dictionaries are designed to help you find both forms. When you look up a new action, you usually see the imperfective verb listed first, followed by its perfective partner. You will often see standard abbreviations like **нед.** (imperfective) and **док.** (perfective) in official resources. Getting comfortable with these dictionary entries makes expanding your vocabulary much easier.

:::note
**Quick tip**
Always write down new verbs as a pair in your notebook, like **робити / зробити**. If a dictionary only gives you one form, take a moment to search for its partner!
:::

## Спосіб 1: Додавання префікса

The most common and productive way to create a perfective verb in Ukrainian is by adding a prefix to its imperfective partner. Think of the imperfective verb as the basic "process" form. When you attach a specific prefix to the beginning of this word, it instantly transforms into a "result" verb. This new word now focuses entirely on the completion or success of the action.

Найчастіше ми утворюємо дієслова доконаного виду за допомогою префіксів. Ми беремо звичайне дієслово процесу і додаємо до нього коротку частинку. Наприклад, ми знаємо дієслово «читати», яке показує довгий процес. Якщо ми додамо префікс «про-», ми отримаємо нове слово «прочитати». Тепер це слово означає, що процес успішно завершився.

> *Most often, we form perfective verbs with the help of prefixes. We take a regular process verb and add a short particle to it. For example, we know the verb "читати" (to read), which shows a long process. If we add the prefix "про-", we get the new word "прочитати" (to read through/finish). Now this word means that the process has successfully finished.*

The most frequent and universal prefix you will encounter is **по-**. When you are unsure which prefix to use to make a verb perfective, this is often your best guess. It usually marks the simple completion of a standard, everyday action without adding any complex extra meaning. You will see it attached to many common verbs you already know.

Цей префікс допомагає нам говорити про щоденні рутинні справи. Вранці ми можемо довго «снідати». Але коли тарілка порожня, ми кажемо, що вже «поснідали». Ми вчимо такі пари дієслів: «бачити» і «побачити», «чути» і «почути». Якщо хтось зробив вам добру справу, ви можете довго «дякувати» йому. Або ви можете просто один раз щиро «подякувати».

> *This prefix helps us talk about daily routine chores. In the morning we can be "снідати" (having breakfast) for a long time. But when the plate is empty, we say that we have already "поснідали" (had breakfast). We learn such pairs of verbs: "бачити" and "побачити" (to see), "чути" and "почути" (to hear). If someone did a good deed for you, you can "дякувати" (be thanking) them for a long time. Or you can just sincerely "подякувати" (thank) them once.*

:::note
**Quick tip**
The prefix **по-** is incredibly common. Whenever you learn a new basic action, try looking for its partner with this prefix first. It is the default tool for turning a process into a one-time result!
:::

Other prefixes are more specific to the type of task being performed. For creative and communicative actions, where you produce something physical or written, the prefix **на-** is extremely common. Another very useful prefix is **про-**, which often relates to actions that involve passing through something or spending a specific amount of time.

Коли ми створюємо текст або малюнок, ми часто використовуємо префікс «на-». Письменник може «писати» книгу роками, але колись він її «написав». Художник може «малювати» картину цілий день. А ввечері він нарешті її «намалював». Префікс «про-» часто показує час. Людина може просто «жити» в місті, але вона може «прожити» там десять років.

> *When we create a text or a drawing, we often use the prefix "на-". A writer can "писати" (be writing) a book for years, but someday he "написав" (has written) it. An artist can "малювати" (be drawing/painting) a picture all day. And in the evening he finally "намалював" (has drawn/painted) it. The prefix "про-" often shows time. A person can just "жити" (live) in a city, but they can "прожити" (live through) ten years there.*

One of the most essential verbs, **робити** (to do/make), takes the prefix **з-** to form its perfective partner **зробити**. However, there is a strict phonetic rule that dictates how this prefix sounds and is written. Before certain voiceless consonants, the prefix **з-** changes to **с-**. You can remember these consonants using the mnemonic phrase «Кафе Птах» (Cafe Bird), which contains the letters K, P, T, F, and Kh.

Префікс «з-» є дуже популярним, але він має свій секрет. Якщо корінь слова починається на глухий звук з фрази «Кафе Птах», ми пишемо префікс «с-». Тому ми маємо базову пару «робити» та «зробити». Але дієслово «казати» перетворюється на «сказати», бо слово починається на літеру «к». Так само дієслово «фотографувати» стає доконаним у формі «сфотографувати».

> *The prefix "з-" is very popular, but it has its secret. If the root of the word begins with a voiceless sound from the phrase "Кафе Птах" (K, P, T, F, Kh), we write the prefix "с-". Therefore, we have the basic pair "робити" (to do/make) and "зробити" (to have done/made). But the verb "казати" (to say/tell) turns into "сказати", because the word begins with the letter "к". Similarly, the verb "фотографувати" (to photograph) becomes perfective in the form "сфотографувати".*

:::info
**Grammar box**
The "Кафе Птах" rule only applies to the prefix **з-**. Whenever you see an imperfective verb starting with K, P, T, F, or Kh (к, п, т, ф, х) and it uses this prefix to become perfective, it will always change to **с-**. This makes the pronunciation much smoother!
:::

Finally, you will often encounter the prefixes **ви-** and **за-**, which frequently deal with consumption, mastery, and transactions. The prefix **ви-** often implies exhausting a resource completely or taking something out, while **за-** is frequently used for actions that secure a result or close a deal.

Коли ми повністю закінчуємо напій, ми використовуємо префікс «ви-». Можна «пити» каву повільно, але потім «випити» її до дна. Цей префікс також працює з навчанням. Якщо ви просто сидите з книгою, ви можете «вчити» слова. Але якщо ви знаєте їх напам'ять, ви змогли їх успішно «вивчити». Префікс «за-» дуже важливий у магазині. Там ви повинні не просто «платити» гроші, а обов'язково «заплатити» за товар.

> *When we completely finish a drink, we use the prefix "ви-". One can "пити" (be drinking) coffee slowly, but then "випити" (drink up) it to the bottom. This prefix also works with studying. If you just sit with a book, you can "вчити" (be studying) words. But if you know them by heart, you managed to successfully "вивчити" (master/memorize) them. The prefix "за-" is very important in a store. There you must not simply "платити" (be paying) money, but necessarily "заплатити" (pay off/complete payment) for the goods.*

<!-- INJECT_ACTIVITY: quiz-find-partner --> [quiz, Find the Partner (Verb Matching), 8 items]

## Спосіб 2: Зміна в корені або суфіксі

Not all imperfective verbs are short and simple dictionary forms. In many cases, the perfective verb is actually the shorter base form. This is especially common when the verb already contains a prefix that gives it a specific meaning. If the verb already has a prefix, we cannot simply add another one to change its aspect. Instead, we have to "stretch" the verb by adding a special suffix to the end. This extra length physically represents the extended duration of the ongoing process. When you encounter a long verb with multiple syllables, it is very likely an imperfective verb describing a continuous action, while its shorter partner describes the completed result. By recognizing these stretching suffixes, you will easily identify whether a verb focuses on the journey or the destination.

The most recognizable stretching suffixes in Ukrainian are **-ува-** and **-юва-**. They transform a short, perfective result into a long, imperfective process. The extra syllables literally take longer to pronounce, which mimics the duration of the action itself. You can feel the physical difference between the drawn-out process and the sharp resolution of the perfective form. This pattern is essential for verbs describing mental processes or communication.

Ми часто додаємо суфікси «-ува-» або «-юва-», щоб зробити слово довшим. Коли ви довго думаєте, ви можете «вирішувати» проблему. Але коли ви нарешті маєте відповідь, ви змогли її «вирішити». Так само працює слово «запитувати», коли ви ставите багато питань. А коли ви ставите одне коротке питання, ви можете просто «запитати».

> *We often add the suffixes "-ува-" or "-юва-" to make the word longer. When you think for a long time, you might "вирішувати" (be deciding) a problem. But when you finally have an answer, you managed to "вирішити" (decide/solve) it. The word "запитувати" (to be asking) works the same way when you ask many questions. And when you ask one short question, you can simply "запитати" (ask once).*

Another common pattern involves shifting the vowel right before the infinitive ending. The most frequent shift is between the broad vowel **-а-** (or **-я-**) for the imperfective aspect and the narrower **-и-** for the perfective aspect. The **-а-** sound requires opening the mouth wider, which feels continuous. In contrast, the **-и-** sound feels "sharper" and more final, signaling the end of the action. 

Викладач може «відповідати» на питання студентів цілу годину. Але студент на іспиті має швидко «відповісти» на одне запитання. Ми можемо повільно «відчиняти» важкі двері в кімнату. Або ми можемо різко «відчинити» вікно вранці.

> *A teacher can "відповідати" (be answering) students' questions for a whole hour. But a student at an exam must quickly "відповісти" (give an answer) to one question. We can slowly "відчиняти" (be opening) heavy doors into a room. Or we can sharply "відчинити" (open/throw open) a window in the morning.*

:::info
**Grammar box**
When you see a verb ending in **-ати** or **-яти**, it is very often the imperfective partner. Its perfective twin will frequently end in **-ити**, providing a crisp conclusion.
:::

Sometimes, stretching the verb requires changing a vowel right inside the root of the word. This internal change is called vowel alternation, or **чергування**. A common phonetic shift is changing the vowel **о** to the vowel **а** when moving from a perfective result to an imperfective process. The wider **а** sound physically opens the mouth more, reflecting the expanded duration of the ongoing action. 

Мій брат завжди готовий мені «допомагати» з ремонтом. Минулого тижня він зміг «допомогти» мені перевезти меблі. У першому слові корінь має звук «а», бо це довгий процес. У другому слові корінь має звук «о», бо це швидкий результат.

> *My brother is always ready to "допомагати" (be helping) me with repairs. Last week he was able to "допомогти" (help/give help) me move furniture. In the first word, the root has the sound "a" because it is a long process. In the second word, the root has the sound "o" because it is a quick result.*

Finally, there is a special suffix that works in the exact opposite direction. Instead of stretching the verb into a process, the suffix **-ну-** instantly compresses it. When you add **-ну-** to an imperfective verb, it immediately turns it into a perfective, lightning-fast action. It is the grammatical equivalent of a single burst of energy or a momentary event that happens in the blink of an eye. 

Хтось може довго «стукати» у ваші двері. Але вітер може раптом «стукнути» вікном лише один раз. Діти на вулиці можуть голосно «кричати» під час гри. Але перехожий може злякано «крикнути», якщо побачить небезпеку. Ніколи не можна «штовхати» людей у транспорті. Навіть випадково «штовхнути» людину дуже негарно.

> *Someone can "стукати" (be knocking) on your door for a long time. But the wind can suddenly "стукнути" (give a knock) with a window just once. Children outside can loudly "кричати" (be shouting) during a game. But a passerby can frighteningly "крикнути" (let out a cry) if they see danger. One must never "штовхати" (be pushing) people in transport. Even to accidentally "штовхнути" (give a shove to) a person is very ugly.*

<!-- INJECT_ACTIVITY: fill-in-categorize-formation -->

## Спосіб 3: Зовсім інші слова (суплетивізм)

Sometimes, a verb changes so drastically between its forms that it becomes a completely different word. This is called suppletion. You know this from English, where the past tense of "go" is "went." In Ukrainian, a few basic verbs use entirely different roots to distinguish between the ongoing process and the final result. The most critical pair is the verb for taking.

Уявіть, що ви берете речі з полиці. Це довгий процес. Але коли ви нарешті взяли останню річ, дія завершилася. Тому ми маємо два слова: «брати» для процесу і «взяти» для результату.

> *Imagine that you are taking things from a shelf. This is a long process. But when you finally took the last thing, the action finished. That is why we have two words: "брати" (to be taking) for the process and "взяти" (to take) for the result.*

Another essential pair relates to speech. The imperfective verb «говорити» describes the continuous act of speaking. It is a process that can last for hours. However, to express the result of delivering a single message, you must use the perfective verb «сказати». This is the instantaneous act of saying or telling a concrete fact.

Вчора ми довго говорили про роботу. Ми говорили дві години, але колега так і не сказав мені новину. Тільки сьогодні він сказав правду.

> *Yesterday we talked for a long time about work. We talked for two hours, but the colleague still did not tell me the news. Only today he told the truth.*

Students always learn another famous pair together: «шукати» (to search) and «знайти» (to find). Strictly speaking, they are different actions rather than a true grammatical pair. The actual perfective partner for «шукати» is «пошукати» (to search for a bit). But in daily life, finding is the natural result of searching, so we treat them as a practical pair. A similar jump happens with «ловити» (to catch - process) and «піймати» (to catch - result).

Мій брат любить ловити рибу. Він може ловити її цілий день. Але рідко він може дійсно піймати велику рибу. Коли він шукає гриби, він хоче їх знайти.

> *My brother likes catching fish. He can be catching them all day. But rarely can he actually catch a big fish. When he searches for mushrooms, he wants to find them.*

:::info
**Grammar box**
Always memorize verbs in their aspectual pairs. If you only know the imperfective form, you will never be able to express that  We have grouped twenty essential verb pairs for this level into a reference table. This includes examples of prefixation, suffix changes, and completely different words. Notice the essential pair «купувати» and «купити» (to buy), which drops its long suffix to form the perfective result.

Ось найважливіші дієслова для вашого рівня. Вивчайте їх тільки парами. Так ви зможете завжди правильно описувати дію.

> *Here are the most important verbs for your level. Learn them only in pairs. This way you will always be able to correctly describe the action.*

| Спосіб | Недоконаний вид (Процес) | Доконаний вид (Результат) |
| :--- | :--- | :--- |
| **Префікс по-** | снідати, думати, бачити | поснідати, подумати, побачити |
| **Інші префікси** | робити, читати, писати, пити | зробити, прочитати, написати, випити |
| **Суфікси / Корінь**| купувати, допомагати, відчиняти | купити, допомогти, відчинити |
| **Інші слова** | брати, говорити, шукати, ловити | взяти, сказати, знайти, піймати |

<!-- INJECT_ACTIVITY: match-up-blanks-pairs -->
<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->

## Підсумок (Summary)

We have covered the essential concept of verb aspects in Ukrainian. Remember that the imperfective aspect describes an ongoing process, while the perfective aspect focuses on a successfully completed result. You learned the three main ways to form these crucial aspectual pairs. The most common method is adding a prefix, like turning «робити» into «зробити». The second method involves changing the suffix or a vowel in the root, such as changing «вирішувати» to «вирішити». Finally, some of the most important everyday verbs use completely different words for their pairs. Good examples of this are «брати» and «взяти».

:::note
**Self-check questions:**
1. Can you name the perfective partner for the verb «писати»? (Answer: «написати»)
2. What prefix follows the "K-P-T-F-Kh" rule when forming a perfective verb? (Answer: the prefix «с-»)
3. Which verb describes the completed result: «говорити» or «сказати»? (Answer: «сказати»)
:::

Ви зробили великий крок уперед. Тепер ви розумієте, як працюють українські дієслова.

> *You have made a big step forward. Now you understand how Ukrainian verbs work.*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-in-vocabulary
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

**Level: A2 (Module 3/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


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
