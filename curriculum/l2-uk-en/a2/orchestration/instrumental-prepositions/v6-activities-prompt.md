<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/instrumental-prepositions.yaml` file for module **28: Над, під, між** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: true-false -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete location sentences with correct preposition + Instrumental noun
    form
  items: 8
  type: fill-in
- focus: Match prepositions (над, під, перед, за, між) to pictures showing spatial
    relationships
  items: 8
  type: match-up
- focus: Distinguish spatial vs. temporal meaning of перед and за
  items: 8
  type: quiz
- focus: Judge whether location descriptions match a room diagram
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- стеля (ceiling)
- підлога (floor)
- кут (corner)
- розклад (schedule)
- сон (sleep, dream)
required:
- над (above, over)
- під (under, below)
- перед (in front of; before (temporal))
- за (behind; according to)
- між (between)
- стіл (table)
- будинок (building, house)
- ліжко (bed)
- стіна (wall)
- обід (lunch)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Просторові прийменники: Де це? (Spatial Prepositions: Where Is It?)

Imagine you are visiting a beautiful museum. The tour guide is explaining where the most famous objects are located.

> **Гід музею:** Добрий день! Це головний зал. Картина висить **над каміном** *(above the fireplace)*.
> **Відвідувач:** Дуже гарно! А де скульптура?
> **Гід музею:** Скульптура стоїть **між вікнами** *(between the windows)*.
> **Відвідувач:** Я бачу. А де можна сісти?
> **Гід музею:** Лавка *(bench)* стоїть **під деревом** *(under the tree)* у саду. А кафе знаходиться **за музеєм** *(behind the museum)*.
> **Відвідувач:** Дякую! Ми йдемо туди.

In this dialogue, the guide clearly explains where everything is. To answer the question **Де?** *(Where?)*, Ukrainian uses specific spatial prepositions paired with the **Instrumental case** (орудний відмінок). 

The Instrumental case is one of the most versatile cases in Ukrainian. While you previously learned to use it to describe the tool or instrument you use to perform an action, it has another massive role in the language: mapping out physical space. When you use spatial prepositions, the Instrumental case acts as a kind of anchor. It tells the listener that the object is stationary. It is not moving. It is fixed in space. This static nature is exactly why we use it to answer the question **Де?**.

There are five key spatial prepositions that take the Instrumental case:
1. **над** *(above, over)*
2. **під** *(under, below)*
3. **перед** *(in front of)*
4. **за** *(behind, beyond)*
5. **між** *(between)*

In Ukrainian, prepositions actively change the noun that follows them. We call this "government" (керування) — the preposition governs the case of the noun. Review the Instrumental case endings briefly before looking at the examples.

| Рід (Gender) | Відмінок (Case) | Закінчення (Ending) | Приклад (Example) |
| :--- | :--- | :--- | :--- |
| **Чоловічий** (Masc.) | Орудний (Instr.) | **-ом** (тверда / hard)<br>**-ем** (м'яка / soft) | під стол**ом**<br>над музе**єм** |
| **Жіночий** (Fem.) | Орудний (Instr.) | **-ою** (тверда / hard)<br>**-ею** (м'яка / soft) | за стін**ою**<br>перед вулиц**ею** |
| **Середній** (Neut.) | Орудний (Instr.) | **-ом** (тверда / hard)<br>**-ем** (м'яка / soft) | під вікн**ом**<br>над мор**ем** |
| **Множина** (Plural) | Орудний (Instr.) | **-ами** (тверда / hard)<br>**-ями** (м'яка / soft) | між вікн**ами**<br>над двер**има** |

Here is each preposition in detail.

### Над (above, over)
Use **над** when something is physically higher than another object, typically without touching it. 

*   Лампа висить **над столом**. *(The lamp hangs above the table.)*
*   Птах летить **над містом**. *(The bird flies over the city.)*
*   Хмари **над горами**. *(Clouds above the mountains.)*
*   Велике дзеркало висить **над ліжком**. *(A large mirror hangs above the bed.)*

Notice the plural form in **горами**. The nominative plural is **гори**, and in the Instrumental case, it becomes **горами**.

### Під (under, below)
Use **під** when an object is located underneath or below something else. This is an extremely common preposition in everyday life.

*   Кіт сидить **під столом**. *(The cat sits under the table.)*
*   Книга лежить **під ліжком**. *(The book lies under the bed.)*
*   Є підвал **під будинком**. *(There is a basement under the building.)*
*   Ми відпочиваємо **під парасолею**. *(We relax under the umbrella.)*

:::tip
**Vocabulary tip:** The word **будинок** *(building, house)* is essential. When you describe the area surrounding a building, the noun takes the hard masculine ending **-ом**: **будинком**.
:::

### Перед (in front of)
Use **перед** when an object is positioned directly at the front of another object.

*   Дерево росте **перед будинком**. *(A tree grows in front of the house.)*
*   Машина стоїть **перед гаражем**. *(The car stands in front of the garage.)*
*   Фонтан **перед театром**. *(A fountain in front of the theater.)*
*   Діти грають **перед школою**. *(Children play in front of the school.)*

### За (behind, beyond)
Use **за** when an object is located at the back of another object, or completely beyond it.

*   Сад **за будинком**. *(A garden behind the house.)*
*   Ліс **за річкою**. *(A forest beyond the river.)*
*   Хтось стоїть **за дверима**. *(Someone is standing behind the door.)*
*   Сонце сідає **за горами**. *(The sun sets beyond the mountains.)*

The noun **двері** *(door)* is always plural in Ukrainian. Therefore, its Instrumental form must be plural: **дверима**.

### Між (between)
Discussing the nuances of **між** is important. This preposition is unique among the five because it logically requires a relationship between at least two objects. You cannot be "between" a single, solitary object. Therefore, **між** is always followed by either a plural noun, or two singular nouns joined by the conjunctions **і** or **та** *(both meaning 'and')*. Crucially, every noun that follows **між** must be in the Instrumental case.

*   Парк **між школою і бібліотекою**. *(A park between the school and the library.)*
*   Стілець **між столом і стіною**. *(A chair between the table and the wall.)*
*   Місто **між горами**. *(A city between the mountains.)*
*   Я сиджу **між братом і сестрою**. *(I sit between my brother and my sister.)*

<!-- INJECT_ACTIVITY: match-up -->

## Описуємо кімнату (Describing a Room)

The most practical way to master spatial prepositions is to describe a room. When you talk about where furniture is located, you will constantly use **над**, **під**, **перед**, **за**, and **між**.

Listen to a dialogue between two roommates, Олег and Максим. They just moved into a new apartment and are deciding where to put their furniture.

> **Олег:** Куди ми поставимо шафу *(wardrobe)*?
> **Максим:** Шафа стоїть **між вікном і дверима** *(between the window and the door)*.
> **Олег:** А куди поставити стіл?
> **Максим:** Мій робочий стіл стоїть **перед вікном** *(in front of the window)*.
> **Олег:** Добре. А де буде картина?
> **Максим:** Картина висить **над ліжком** *(above the bed)*. Це гарне місце.
> **Олег:** Згоден. А де мій кіт?
> **Максим:** Кіт сидить **під столом** *(under the table)*. Він уже спить.
> **Олег:** А книжкова полиця *(bookshelf)*?
> **Максим:** Полиця висить **над столом**. Там будуть наші книги.

To describe a room systematically, you need specific vocabulary. Here are the nouns you will use most often to build your sentences:
*   **стіна** *(wall)* – Instrumental: **стіною**
*   **підлога** *(floor)* – Instrumental: **підлогою**
*   **стеля** *(ceiling)* – Instrumental: **стелею**
*   **кут** *(corner)* – Instrumental: **кутом**
*   **шафа** *(wardrobe, cabinet)* – Instrumental: **шафою**
*   **полиця** *(shelf)* – Instrumental: **полицею**
*   **килим** *(carpet, rug)* – Instrumental: **килимом**
*   **картина** *(painting, picture)* – Instrumental: **картиною**

Read this full description of a cozy bedroom. Notice how the prepositions and the Instrumental case endings build a precise picture of the space.

Моя кімната дуже світла і затишна. У кімнаті є велике біле вікно. Робочий стіл стоїть **перед вікном**. Зручне крісло стоїть **перед столом**. Звичайно, я часто працюю там, тому це важливе місце. Мій новий комп'ютер лежить на столі. Що знаходиться під стелею? **Під стелею** висить яскрава лампа. А що висить **над столом**? **Над столом** висить довга книжкова полиця. Там лежать мої підручники і зошити.

У кімнаті також є широке ліжко. Картина висить **над ліжком**. Це красива картина з морем. Килим лежить **під столом**. А велика коричнева шафа стоїть у кутку. Точніше, шафа стоїть **між вікном і дверима**. А де мій собака? Мій собака любить спати **під ліжком**. Там тихо і спокійно.

:::note
**Pattern Recognition: Question and Answer**
A very common conversational pattern in Ukrainian is the rapid question-and-answer exchange using **Де?** *(Where?)*. In spoken Ukrainian, you do not always need to repeat the verb in your answer. The preposition and the Instrumental case ending provide all the necessary information.
— Де лампа? — Лампа **над столом**.
— Де кіт? — **Під ліжком**.
— Де ваза? — **Між книгами**.
This makes conversations flow quickly and naturally.
:::

Another common situation is searching for lost items. Spatial prepositions are crucial here.

> **Анна:** Ти не бачив мої ключі?
> **Віктор:** Твої ключі лежать **під журналом** *(under the magazine)*.
> **Анна:** Дякую! А де мій телефон?
> **Віктор:** Він лежить **між зошитом і книгою** *(between the notebook and the book)*.
> **Анна:** Знайшла! А де мій рюкзак?
> **Віктор:** Рюкзак стоїть **за кріслом** *(behind the armchair)*.

<!-- INJECT_ACTIVITY: true-false -->

## Перед обідом, за розкладом: Часове значення (Before Lunch, On Schedule: Temporal Meaning)

Language is highly metaphorical. Humans often take words that describe physical space and repurpose them to describe time. Ukrainian does exactly this with the prepositions **перед** and **за**. While **перед** physically means standing at the front of a building, temporally it means standing at the front of an event — in other words, *before* it happens. This allows you to seamlessly transition from describing the layout of your neighborhood to describing the daily schedule of your life. Even though the meaning is about time, they still require the **Instrumental case**.

### Перед (before - temporal)
When we talk about time, **перед** + Ор.в. means *before* an event or an action. It shows that something happens prior to a specific moment.

*   Я мию руки **перед обідом** *(before lunch)*.
*   Студенти читають текст **перед уроком** *(before class)*.
*   Я завжди читаю книгу **перед сном** *(before sleep)*.
*   Ми купуємо квитки **перед відпусткою** *(before vacation)*.

These phrases are the building blocks of describing a daily routine. Think about your own day and the actions you do in a specific sequence. Answer these questions for yourself: Що ти робиш **перед сніданком**? Перед роботою? Перед сном?

Here are some common daily routine expressions in action:

> **Олена:** Що ти робиш **перед сніданком** *(before breakfast)*?
> **Павло:** **Перед сніданком** я п'ю воду і роблю гімнастику. А ти?
> **Олена:** Я тільки п'ю каву. Що ти робиш **перед роботою** *(before work)*?
> **Павло:** **Перед роботою** я читаю новини в інтернеті. 
> **Олена:** А що ти робиш **перед заняттям** *(before class)*?
> **Павло:** **Перед заняттям** я завжди повторюю нові слова.

### За (according to - temporal)
The preposition **за** has a unique temporal use. It frequently appears in fixed temporal expressions to mean *according to* a rule, a plan, or a schedule. It still requires the Instrumental case.

*   Наш поїзд прибуває **за розкладом** *(according to schedule)*.
*   Ми успішно працюємо **за планом** *(according to plan)*.
*   Усе в проекті йде **за графіком** *(according to schedule/graph)*.

Listen to this short dialogue about scheduling at an office:

> **Антон:** Коли починається наша важлива зустріч?
> **Марія:** Зустріч починається о десятій годині.
> **Антон:** Ми йдемо **за розкладом** *(according to schedule)*?
> **Марія:** Так, усе йде **за планом** *(according to plan)*. Ніхто не спізнюється.

:::caution
**Calque Warning:**
Do not use the phrase "по розкладу" to say "according to schedule." This is a Russian calque that has incorrectly entered some spoken Ukrainian. The standard, natural, and correct Ukrainian phrase is always **за розкладом**. Always use **за** + Instrumental for these expressions of accordance.
:::

It is important to notice the contrast in meaning based on context. The exact same preposition paired with the exact same case ending can mean completely different things depending on whether you are talking about space or time.

Compare these exact phrases to see the contrast with spatial meaning:
*   Дерево росте **перед будинком** *(in front of — spatial location)*.
*   Я читаю книгу **перед обідом** *(before — temporal sequence)*.

Both sentences use the preposition **перед** followed by a noun in the Instrumental case (**будинком**, **обідом**). The grammar is identical, but the context clearly tells you whether it is a physical location or a moment in time.

<!-- INJECT_ACTIVITY: quiz -->

## Практика: Де? Коли? (Practice: Where? When?)

Now that we have covered both the spatial and temporal uses of these prepositions, practice these prepositions in different contexts. 

Picture description exercise: look at a scene and describe locations using **над**, **під**, **перед**, **за**, **між**. Imagine a quiet residential street. Read this mini-dialogue describing a neighborhood.

> **Анна:** Розкажи про свій новий район. Що там є?
> **Богдан:** Ми живемо в дуже гарному районі. Наш житловий будинок новий. **Перед будинком** є невеликий фонтан. Магазин знаходиться **за будинком**. Це дуже зручно для нас.
> **Анна:** А де ви гуляєте?
> **Богдан:** Великий зелений парк лежить **між школою і театром**. Студенти часто відпочивають там **перед уроками**.
> **Анна:** Звучить чудово!

In this short text, you can see how the prepositions build a clear mental map of the neighborhood, and how **перед уроками** adds a temporal detail.

### Contrastive Pairs: Location vs. Purpose

We saw earlier that **за** + Instrumental means *behind* (location) or *according to* (schedule). However, you already know another extremely common use of the preposition **за**. When you want to thank someone, or express purpose or exchange, you use **за** + Accusative case *(for)*.

Compare these contrastive pairs directly:

*   Сад знаходиться **за будинком** *(behind the house — location, Instrumental)*.
*   Дякую **за допомогу** *(thank you for help — purpose, Accusative)*.
*   Дякую **за смачний обід**. *(Thank you for the delicious lunch — purpose, Accusative)*.

This is why understanding cases is so fundamental in Ukrainian. The case ending literally changes the definition of the preposition. **За** with Instrumental gives you a physical location, while **За** with Accusative gives you an abstract reason or purpose.

### Location (Де?) vs. Direction (Куди?)

One of the most profound differences between English and Ukrainian grammar is how motion is expressed. In English, the preposition often changes to show motion (e.g., 'in' vs 'into'). In Ukrainian, the preposition remains exactly the same. What changes is the case of the noun.

This elegant rule applies to **під**, **над**, and **між**. 

If you are describing a static location — answering the question **Де?** *(Where?)* — you use the Instrumental case. The object is resting in its place. 

If you are describing an action where an object crosses space to reach a new destination — answering the question **Куди?** *(Where to? / Whither?)* — you must use the Accusative case. The Accusative case captures the momentum and the final target of the movement.

Compare these pairs carefully:

**Під (under):**
*   **Де? (Location - Instrumental):** Кіт сидить **під столом**. *(The cat sits under the table.)* The cat is already there, not moving to a new location.
*   **Куди? (Direction - Accusative):** Кіт заліз **під стіл**. *(The cat climbed under the table.)* The cat moved from somewhere else to a new destination under the table. 

**Над (above/over):**
*   **Де? (Location - Instrumental):** Лампа висить **над столом**. *(The lamp hangs above the table.)* The lamp is permanently fixed there.
*   **Куди? (Direction - Accusative):** Повісь лампу **над стіл**. *(Hang the lamp above the table.)* You are holding the lamp and moving it to a new destination above the table.

**Між (between):**
*   **Де? (Location - Instrumental):** Стілець стоїть **між столом і ліжком**. *(The chair stands between the table and the bed.)* 
*   **Куди? (Direction - Accusative):** Постав стілець **між стіл і ліжко**. *(Put the chair between the table and the bed.)* 

*Note: Using the Accusative case with **між** for direction is grammatically correct but somewhat rare in everyday speech. Ukrainians often use other prepositions or simply rephrase the sentence. However, it follows the exact same logical pattern.*

This contrast between Location (Instrumental) and Direction (Accusative) allows you to be incredibly precise in Ukrainian. Focus heavily on mastering the static locations (**Де?**) using the Instrumental case, as this is the most common way you will describe the world around you.

<!-- INJECT_ACTIVITY: fill-in -->

## Підсумок

You now know how to describe where objects are located using five essential spatial prepositions: **над** *(above)*, **під** *(under)*, **перед** *(in front of)*, **за** *(behind)*, and **між** *(between)*.

When describing a static location to answer the question **Де?** *(Where?)*, these prepositions always govern the Instrumental case. You saw examples like **під столом**, **над ліжком**, and **між вікнами**. You practiced using these exact patterns to describe a bedroom, to find lost keys, and to map out a local neighborhood.

You also discovered that **перед** and **за** have very important temporal meanings. You use **перед** + Instrumental to say *before* an event happens, giving you the ability to talk about daily routines like **перед обідом** *(before lunch)* or **перед сном** *(before sleep)*. You use **за** + Instrumental to talk about systems and schedules, using standard phrases like **за розкладом** *(according to schedule)* or **за планом** *(according to plan)*.

Finally, you learned how Ukrainian grammar elegantly distinguishes between Location and Direction. While Location (**Де?**) uses the Instrumental case, Direction of motion (**Куди?**) uses the Accusative case. This logical system allows you to build highly precise, detailed, and natural sentences about the physical world.
```

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: instrumental-prepositions
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

**Level: A2 (Module 28/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
