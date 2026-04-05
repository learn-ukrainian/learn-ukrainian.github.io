<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-dative.yaml` file for module **23: Контрольна робота — давальний відмінок** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify the dative form among case options (recognition — Part 1 material)
  items: 8
  type: quiz
- focus: Complete sentences with correct dative noun/adjective/pronoun endings (Part
    2 material)
  items: 8
  type: fill-in
- focus: Match dative-governing verbs to correct case forms and sentence completions
  items: 8
  type: match-up
- focus: Find and correct grammar errors in sentences covering module topics
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- закінчення (ending (grammar))
- чергування (alternation (grammar))
- узгодження (agreement (grammar))
required:
- давальний відмінок (dative case)
- допомагати (to help)
- дякувати (to thank)
- подобатися (to be pleasing to, to like)
- подарувати (to give as a gift)
- надіслати (to send)
- потрібно (necessary, needed)
- холодно (cold (impersonal state))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Розпізнавання (Part 1: Recognition)

Вітаємо на контрольній роботі! У попередніх модулях ми детально вивчали **давальний відмінок** (dative case). Це один із найважливіших відмінків для спілкування, адже він показує, до кого спрямована дія, кому ми щось даємо, або хто відчуває певний стан. 

Давайте розпочнемо з офісної традиції «Таємний Санта» (Secret Santa). Зверніть увагу на те, як змінюються імена колег.

> **Організатор:** Увага! Скоро Новий рік. Ми граємо в «Таємного Санту». Кому ми купуємо подарунки? *(Attention! New Year is soon. We are playing "Secret Santa". Who are we buying gifts for?)*
> **Колега 1:** Що подарувати Олексієві? *(What to give to Oleksiy?)*
> **Організатор:** Книгу! Він любить читати. А Наталці? *(A book! He likes to read. And to Natalka?)*
> **Колега 2:** Шоколад! Вона обожнює солодке. *(Chocolate! She adores sweets.)*
> **Організатор:** А що ми подаруємо новому колезі? *(And what will we give to the new colleague?)*
> **Колега 1:** Кружку для кави. *(A mug for coffee.)*
> **Організатор:** Чудово. А нашому шефу? *(Great. And to our boss?)*
> **Колега 2:** Думаю, добре вино. *(I think, good wine.)*

Питання «Кому ми купуємо подарунки?» є ключовим. Давальний відмінок завжди відповідає на питання **кому?** (to whom?) для істот та **чому?** (to what?) для неістот. 

### Давальний чи Знахідний? (Dative vs. Accusative)

Дуже часто студенти плутають давальний відмінок зі знахідним. The accusative case (**знахідний відмінок**) shows the direct object that receives the physical impact of an action. The dative case (**давальний відмінок**) shows the addressee or the receiver of a transfer.
Порівняйте ці пари речень:
* **Я малюю сестру.** *(I am drawing the sister. — Знахідний відмінок. Вона є об'єктом малюнка.)*
* **Я малюю сестрі.** *(I am drawing for the sister. — Давальний відмінок. Вона є отримувачем малюнка.)*
* **Ми слухаємо лікаря.** *(We listen to the doctor. — Знахідний відмінок.)*
* **Ми віримо лікарю.** *(We believe the doctor. — Давальний відмінок.)*
* **Я люблю маму.** *(I love mom. — Знахідний відмінок.)*
* **Я допомагаю мамі.** *(I help mom. — Давальний відмінок.)*

### Безособові конструкції (Impersonal Constructions)

В англійській мові ми кажемо "I am cold", де "I" (Я) є активним суб'єктом. In Ukrainian, we use a different logic for physical or emotional states. We use impersonal sentences (безособові речення) where there is no active subject. The person who feels the state is the "experiencer" and stands in the dative case.

* **Я змерз.** *(I froze. — Називний відмінок, активна дія.)*
* **Мені холодно.** *(I am cold. / Literally: To me it is cold. — Давальний відмінок, стан.)*
* **Тобі сумно.** *(You are sad.)*
* **Йому весело.** *(He is having fun.)*
* **Нам дуже цікаво.** *(We are very interested.)*

### Дієслово «подобатися»

Дієслово **подобатися** (to be pleasing to, to like) працює за такою ж логікою. The object that causes the sympathy is the grammatical subject in the nominative case, while the person who likes it is in the dative case.

* **Студентові подобається українська мова.** *(The student likes the Ukrainian language.)*
* **Дітям подобається ця нова гра.** *(The children like this new game.)*
* **Мені подобається твоя ідея.** *(I like your idea.)*

<!-- INJECT_ACTIVITY: quiz -->

## Частина 2: Вибір форми (Part 2: Choosing the Correct Form)

Правильно вибрати **закінчення** (ending (grammar)) — це головне завдання при роботі з давальним відмінком. Давайте згадаємо всі правила утворення форм.

### Чоловічий та середній рід

Іменники чоловічого роду мають паралельні закінчення: **-ові / -еві** (**-єві**) та **-у / -ю**. Both options are correct, but there is an important stylistic rule. For people and animate beings, Ukrainians almost always choose the endings **-ові / -еві**. This sounds very natural and respectful.
* **панові** *(to the sir/gentleman)*
* **батькові** *(to the father)*
* **Андрієві** *(to Andriy)*
* **водієві** *(to the driver)*

For inanimate objects, we usually use the endings **-у / -ю**.
* **місту** *(to the city)*
* **лісу** *(to the forest)*
* **телефону** *(to the phone)*

:::tip
**Правило двох іменників**
Коли в реченні є поряд кілька іменників чоловічого роду в давальному відмінку, слід спочатку вживати **-ові / -еві**, а тоді — **-у / -ю**. Це робиться для того, щоб уникнути монотонного повторення одних і тих самих звуків: **панові директору** *(to the sir director)*, **моєму братові Андрію** *(to my brother Andriy)*.
:::

Іменники середнього роду завжди приймають закінчення **-у / -ю**.
* **сонцю** *(to the sun)*
* **полю** *(to the field)*
* **морю** *(to the sea)*

### Жіночий рід та чергування приголосних

Іменники жіночого роду (які закінчуються на **-а / -я**) у давальному відмінку приймають закінчення **-і**.
However, there is a strict phonetic rule called **чергування** (alternation (grammar)) of consonants. If the stem of a word ends in the throat sounds **г, к, х**, they cannot stand before the sound **-і**. They must transform into the smiling sounds **з, ц, с**.

* **г** → **з**: **нога** *(leg)* → **нозі** *(to the leg)*; **подруга** *(female friend)* → **подрузі** *(to the female friend)*
* **к** → **ц**: **рука** *(hand)* → **руці** *(to the hand)*; **книжка** *(book)* → **книжці** *(to the book)*
* **х** → **с**: **муха** *(fly)* → **мусі** *(to the fly)*; **птаха** *(bird)* → **птасі** *(to the bird)*

### Узгодження прикметників

Якісна мова потребує ідеального узгодження. **Узгодження** (agreement (grammar)) means that adjectives and possessive pronouns must completely copy the gender, number, and case of the noun they describe.

Для чоловічого та середнього роду прикметники мають закінчення **-ому**:
* **моєму новому другу** *(to my new friend)*
* **цьому великому місту** *(to this big city)*
* **нашому доброму сусідові** *(to our kind neighbor)*

Для жіночого роду прикметники мають закінчення **-ій**:
* **твоїй найкращій подрузі** *(to your best friend)*
* **моїй молодшій сестрі** *(to my younger sister)*
* **цій розумній жінці** *(to this smart woman)*

### Дієслова, що вимагають давального відмінка

Деякі дієслова завжди керують давальним відмінком, адже вони означають дію, спрямовану на людину. Найпоширеніші з них: **допомагати** (to help), **дякувати** (to thank), **радити** (to advise), та **співчувати** (to sympathize).

* **Він допомагає сусідові.** *(He helps the neighbor.)*
* **Ми дякуємо вам.** *(We thank you.)*
* **Лікар радить пацієнту більше спати.** *(The doctor advises the patient to sleep more.)*
* **Я співчуваю вашій родині.** *(I sympathize with your family.)*

### Сфера послуг та пошта

Давальний відмінок також є незамінним у повсякденних справах, наприклад, на пошті або в магазині. Якщо вам потрібно щось **надіслати** (to send) або **подарувати** (to give as a gift), ви використовуєте давальний відмінок для адресата.

* **Я хочу надіслати лист Ганні Петрівні.** *(I want to send a letter to Hanna Petrivna.)*
* **Ми вирішили подарувати квіти вчительці.** *(We decided to give flowers to the teacher.)*
* **Треба дати документи менеджеру.** *(It is necessary to give the documents to the manager.)*
* **Передайте привіт вашій родині!** *(Pass greetings to your family!)*

<!-- INJECT_ACTIVITY: fill-in -->

## Частина 3: Продукування (Part 3: Production)

Тепер, коли ми згадали всі правила, давайте подивимося на них у живій розмові. Повернемося до нашого офісу.

> **Організатор:** Друзі, нам **потрібно** (necessary, needed) вирішити, що купувати. *(Friends, we need to decide what to buy.)*
> **Колега 1:** Я хочу подарувати нашому шефові гарну ручку. *(I want to give our boss a beautiful pen.)*
> **Колега 2:** Хороша ідея. А що ми купимо новій колезі? *(Good idea. And what will we buy for the new colleague?)*
> **Організатор:** Їй подобається кава. Подаруємо їй дорогі кавові зерна. *(She likes coffee. Let's give her expensive coffee beans.)*
> **Колега 1:** А нашому улюбленому програмісту? *(And to our favorite programmer?)*
> **Колега 2:** Йому подаруємо зручний рюкзак! *(To him we will give a comfortable backpack!)*

Зверніть увагу на повні фрази: **нашому шефові**, **новій колезі**, **нашому улюбленому програмісту**. Прикметники і займенники ідеально узгоджені з іменниками.

### Як сказати про вік?

В англійській мові вік описується дієсловом "to be" ("I am thirty"). В українській мові вік — це те, що додається до людини. Тому людина, якій виповнюються роки, завжди стоїть у давальному відмінку. 
The formula is: [Experiencer in Dative] + [Number] + [рік / роки / років].

* **Моєму старшому братові тридцять років.** *(My older brother is thirty years old.)*
* **Цій історичній будівлі вже сто років.** *(This historical building is already a hundred years old.)*
* **Марічці вчора виповнилося п'ять років.** *(Marichka turned five years old yesterday.)*
* **Скільки вам років?** *(How old are you? / Literally: How many years to you?)*

### Модальні слова: треба, потрібно, можна

Коли ми говоримо про необхідність або дозвіл, ми часто використовуємо слова **треба** (need to), **потрібно** (necessary, needed), та **можна** (allowed, possible). Особа, якій щось потрібно або дозволено, стоїть у давальному відмінку.

* **Студентам потрібно багато вчитися.** *(Students need to study a lot.)*
* **Мені треба терміново надіслати цей лист.** *(I need to send this letter urgently.)*
* **Вам можна увійти в кабінет.** *(You are allowed to enter the office.)*
* **Кому треба йти в магазин?** *(Who needs to go to the store?)*
* **Що нам потрібно купити на вечерю?** *(What do we need to buy for dinner?)*

### Офіційні та неофіційні звертання

Написання листівок чи імейлів — це ще одна сфера, де давальний відмінок грає головну роль. Коли ви підписуєте конверт або листівку, ви вказуєте адресата в давальному відмінку.

* **Дорогому вчителеві** *(To the dear teacher)*
* **Шановній пані директору** *(To the respected Madam Director)*
* **Любій матусі** *(To the beloved mommy)*
* **Моєму найкращому другу** *(To my best friend)*

<!-- INJECT_ACTIVITY: match-up -->

## Огляд помилок та порівняння відмінків (Error Review and Case Comparison)

Давайте проаналізуємо типові помилки студентів на рівні А2. Це ваші головні «пастки» (traps), яких слід уникати.

Firstly, students often confuse the adjective endings **-ому** and **-ій**. Always check the gender of the noun. Сказати **моєму мамі** — це груба помилка, тому що **мама** — жіночого роду. Правильно: **моїй мамі**.

Secondly, forgetting consonant alternation is a classic mistake. Написання **подругі** замість правильного **подрузі** одразу видає іноземця.

Finally, the biggest trap for English speakers is using the accusative case instead of the dative after the verb **дякувати** (to thank). In English, you thank "someone" as a direct object. In Ukrainian, you always give thanks TO someone.
* Неправильно: Я дякую тебе. *(Це калька з англійської мови).*
* Правильно: **Я щиро дякую тобі.** *(I sincerely thank you.)*
* Неправильно: Ми дякуємо вчителя.
* Правильно: **Ми дякуємо вчителю.** *(We thank the teacher.)*

### Порівняння відмінків

Щоб ідеально володіти давальним відмінком, треба розуміти, як він відрізняється від інших. Ось порівняльна таблиця, яка допоможе вам побачити різницю:

| Відмінок | Питання | Займенник | Прикметник + Іменник |
|---|---|---|---|
| **Називний** (Nominative) | Хто? Що? *(Who? What?)* | він, вона | мій новий друг, моя найкраща подруга |
| **Родовий** (Genitive) | Кого? Чого? *(Whom? What?)* | його, її | мого нового друга, моєї найкращої подруги |
| **Знахідний** (Accusative) | Кого? Що? *(Whom? What?)* | його, її | мого нового друга, мою найкращу подругу |
| **Давальний** (Dative) | Кому? Чому? *(To whom? To what?)* | йому, їй | моєму новому другу, моїй найкращій подрузі |

Називний відмінок — це суб'єкт дії. Родовий показує відсутність або приналежність. Знахідний показує прямий об'єкт (на кого впливає дія). А давальний відмінок — це завжди адресат, одержувач дії або людина, яка переживає певний стан.

Використання давального відмінка робить вашу мову ввічливою, точною та природною.

<!-- INJECT_ACTIVITY: error-correction -->

## Підсумок

Ви пройшли довгий шлях у вивченні відмінків! Давальний відмінок відкриває багато дверей для ввічливого та природного спілкування українською мовою. Використайте цей чек-лист для самоперевірки:

* Чи можете ви правильно змінити ім'я друга в давальному відмінку для подарунка? (**Олексій** → **Олексієві**).
* Чи пам'ятаєте ви про чергування **г/к/х** → **з/ц/с** у жіночому роді? (**рука** → **руці**, **подруга** → **подрузі**).
* Чи вмієте ви сказати, скільки років вашим родичам, використовуючи правильну конструкцію? (**Моїй мамі сорок років**).
* Чи знаєте ви логічну різницю між активним суб'єктом «Я змерз» та безособовим станом «Мені холодно»?
* Чи правильно ви вживаєте дієслова **дякувати** та **допомагати** з правильним адресатом, не використовуючи знахідний відмінок?

Якщо ви можете впевнено відповісти «Так» на всі ці запитання, ви чудово засвоїли матеріал цього блоку! Розмовляйте українською впевнено!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-dative
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

**Level: A2 (Module 23/60) — ELEMENTARY**

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
