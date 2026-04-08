<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-nouns.yaml` file for module **18: Студентові, сестрі, дитині** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: unjumble -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the noun in brackets into the dative case (e.g., подарувати [брат] →
    братові)
  items: 8
  type: fill-in
- focus: Sort dative nouns by gender (masculine -ові/-у, feminine -і, neuter -у/-ю)
  items: 8
  type: group-sort
- focus: Choose the correct dative ending for nouns with consonant alternation (подруга→подрузі
    vs. *подругі)
  items: 8
  type: quiz
- focus: Match verb + dative noun phrases to their English meanings
  items: 8
  type: match-up
- focus: Reorder words to form correct dative constructions with indirect objects
    (e.g., подарувати братові книгу)
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- відміна (declension)
- чергування (alternation (grammar))
- одержувач (recipient)
- немовля (baby, infant)
required:
- студентові (to the student (dat.))
- сестрі (to the sister (dat.))
- другові (to the friend (dat.))
- подарувати (to give as a gift)
- показати (to show)
- написати (to write)
- розповісти (to tell, to narrate)
- пояснити (to explain)
- відповісти (to answer, to reply)
- закінчення (ending (grammar))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Давальний відмінок іменників чоловічого роду (Dative of Masculine Nouns)

Уявіть ситуацію: ви хочете передати лист або подарунок. Як сказати, кому саме він призначений? Відповідь дає **Давальний відмінок** (the Dative case). Сама назва цього відмінка походить від дієслова **давати** (to give). Він відповідає на питання **кому?** (to whom?) для істот та **чому?** (to what?) для неістот. 

Ukrainian masculine nouns are incredibly rich in the Dative case because they offer choices. Unlike many other cases where you have a single strict rule, II declension masculine nouns have parallel endings: **-ові/-еві/-єві** and **-у/-ю**. Both are correct: **братові = брату**, **лікареві = лікарю**. This gives the language a special melodic quality. 

Let's look at the specific rules for these parallel endings based on the stem type.

1. We use **-ові** for hard stems. For example: **студентові** (to the student), **другові** (to the friend), **батькові** (to the father).
2. We use **-еві** for soft stems and sibilants. For example: **вчителеві** (to the teacher), **товаришеві** (to the comrade/friend).
3. We use **-єві** after vowels. For example: **героєві** (to the hero), **Андрієві** (to Andrii).

If you prefer the shorter forms, hard stems take **-у** (**студенту**, **другу**, **батьку**), and soft stems take **-ю** (**вчителю**, **герою**). 

> **Читаємо українською: Кому ти даєш?**
> — Ти пишеш лист **другові** чи **брату**? (Are you writing a letter to a friend or to a brother?)
> — Я пишу лист **братові**. Він зараз дуже далеко. (I am writing a letter to my brother. He is very far away right now.)
> — А що ти даси **студентові**? (And what will you give to the student?)
> — **Студенту** я дам новий словник. (I will give the student a new dictionary.)
> — Треба також допомогти нашому **вчителеві**. (We also need to help our teacher.)
> — Звичайно, я з радістю допоможу **вчителю**. (Of course, I will gladly help the teacher.)

:::tip
Both endings are equally correct and often used interchangeably. However, native speakers often prefer the **-ові/-еві/-єві** endings for people and professions, as they sound more traditionally Ukrainian and give a respectful tone.
:::

When we look at I declension masculine nouns (Дмитро, батько): follow their declension pattern — **Дмитрові**, **батькові**. These are very common names and words, and they behave exactly like other masculine nouns of the second declension in this regard. Whether it is a formal name or a family title, the ending brings clarity to the recipient of the action.

There is also a very elegant style rule from Заболотний: when multiple dative nouns appear together, alternate endings to avoid monotony — **подякувати сусідові Данилу** (to thank neighbor Danylo). By mixing the **-ові** and **-у** endings, you create a rhythmic flow instead of repeating the same sound twice. You could also say **подякувати сусіду Данилові**, which is equally beautiful.

Let's practice with common masculine nouns learners already know from A1-A2. 

> **Читаємо українською: Стиль і милозвучність**
> — Я хочу подякувати **братові Максиму** за допомогу. (I want to thank brother Maksym for the help.)
> — Він завжди радий допомогти. А ти вже дзвонив **лікарю Іванові**? (He is always happy to help. And have you already called doctor Ivan?)
> — Ні, я зателефоную **лікареві** завтра. (No, I will call the doctor tomorrow.)
> — Передай привіт нашому **другові Сергію**. (Send greetings to our friend Serhii.)
> — Добре, я обов'язково напишу **Сергієві**. (Okay, I will definitely write to Serhii.)

<!-- INJECT_ACTIVITY: fill-in -->

As you can see, combining a title and a name makes the alternation rule very natural. If the title takes **-ові**, the name takes **-у**, and vice versa.

<!-- INJECT_ACTIVITY: group-sort -->

## Давальний відмінок іменників жіночого роду (Dative of Feminine Nouns)

Feminine nouns in the Dative case are highly predictable, but they have a fascinating phonetic feature: consonant alternations. When you give something to a woman, a girl, or interact with a feminine object, you usually need the **-і** ending.

For the I declension: hard stems take **-і** (**мамі**, **подрузі**, **сестрі**), soft stems take **-і** (**землі**, **пісні**), stems in -ія take **-ії** (**станції**). The ending **-і** is a hallmark of the Ukrainian Dative case for feminine nouns, distinguishing it clearly from other Slavic languages.

Before adding this **-і** to hard stems, we often encounter a phonetic shift. Because the sound **[і]** makes the preceding consonant soft, velar consonants at the end of the stem change their shape. These are the consonant alternations before -і: к→ц (подруга→подрузі), г→з (книга→книзі), х→с (свекруха→свекрусі). Note that for a word like **жінка** (woman), the change is **к→ц** (**жінці**), and for **подруга** (female friend), the change is **г→з** (**подрузі**).

> **Читаємо українською: Кому це?**
> — Ти вже купив подарунок **мамі**? (Have you already bought a gift for mom?)
> — Так, і **сестрі** також. (Yes, and for sister too.)
> — А що ти скажеш своїй **подрузі**? (And what will you say to your female friend?)
> — Я скажу **подрузі**, що вона найкраща. (I will tell my friend that she is the best.)
> — Ця інформація є в новій **книзі**. (This information is in the new book.)
> — Треба написати про це в **газеті**. (We need to write about this in the newspaper.)

:::note
The alternation rule (к→ц, г→з, х→с) might seem tricky at first, but it exists because it is physically easier to transition from a soft [ц], [з], or [с] into the vowel [і]. This makes the language flow more smoothly.
:::

Not all feminine nouns end in **-а** or **-я**. We also have III declension feminine nouns: **-і** (**ночі**, **матері**, **любові**, **радості**). These are nouns that end in a consonant or a soft sign in their basic dictionary form. When we put them in the Dative case, they also comfortably take the **-і** ending. For instance, **мати** (mother) becomes **матері** (to the mother), and **ніч** (night) becomes **ночі** (to the night).

Let's look at some practice sentences using indirect object pattern (**подарувати квіти мамі**, **написати листа подрузі**). This pattern is the foundation of communication when you want to describe an exchange between two people.

> **Читаємо українською: Передача інформації та речей**
> — Тарас хоче **подарувати квіти мамі** на свято. (Taras wants to give flowers to mom for the holiday.)
> — Це чудова ідея. А я хочу **написати листа подрузі**. (That is a wonderful idea. And I want to write a letter to a friend.)
> — Що ти подаруєш **учительці**? (What will you give the teacher?)
> — Я дам **учительці** гарну листівку. (I will give the teacher a nice postcard.)
> — Ми бажаємо всім **радості** та **любові**. (We wish everyone joy and love.)
> — Дякую! Я розповім про це моїй **сестрі**. (Thanks! I will tell my sister about this.)

<!-- INJECT_ACTIVITY: quiz -->

As you practice, remember to listen for the soft **-і** at the end of feminine words. It is the clearest signal that someone is on the receiving end of your action.

## Давальний відмінок іменників середнього роду (Dative of Neuter Nouns)

Neuter nouns share many similarities with masculine nouns in the Dative case, but their system is slightly simpler. Since neuter nouns mostly describe inanimate objects or concepts, they answer the question **чому?** (to what?). However, there is a special group of neuter nouns that describe baby animals and human infants, which answer **кому?** (to whom?).

For II declension neuter: **-у** for hard stems (**місту**, **слову**, **вікну**), **-ю** for soft stems (**морю**, **серцю**). This mirrors the short endings of the masculine nouns. When you direct an action toward a place or a concept, this is the pattern you will use.

Then we have the special IV declension (nouns in -а/-ят-): **-аті/-яті** (**немовляті**, **курчаті**). These words usually describe young beings. When they decline, a special suffix **-ят-** or **-ат-** appears before the ending **-і**. For example, a baby is **немовля**, but to give a toy to a baby is дати іграшку **немовляті**.

Let's see examples with neuter nouns in real contexts (**дати назву місту**, **радіти сонцю**).

> **Читаємо українською: Звернення до неістот та малят**
> — Туристи завжди радіють **сонцю** і теплому **морю**. (Tourists always rejoice at the sun and the warm sea.)
> — Люди хочуть дати нову назву цьому **місту**. (People want to give a new name to this city.)
> — Ми поїдемо до бабусі і допоможемо **селу**. (We will go to grandma's and help the village.)
> — Треба дати теплого молока **курчаті**. (We need to give warm milk to the chick.)
> — Мама заспівала пісню маленькому **немовляті**. (Mom sang a song to the little baby.)
> — Я вірю твоєму **слову**. (I believe your word.)

As you can see, the Dative case isn't just for physical giving. We also use it with verbs that express emotional reactions, like **радіти** (to be glad / to rejoice). You rejoice *to* something in Ukrainian (**радіти життю** — to rejoice at life, **радіти сонцю** — to rejoice at the sun).

:::tip
Words like **сонце** (sun) and **море** (sea) are common soft and hard neuter nouns. Remember: if the dictionary form ends in **-е**, it usually takes **-ю** in Dative (**сонцю**, **морю**). If it ends in **-о**, it takes **-у** (**вікну**, **місту**).
:::

It is rare to give a physical gift to a window (**вікно**) or a word (**слово**), but you might "give attention" to them, or "give a name" to a city. In all these metaphorical transfers, the Dative case is your reliable tool.

## Давальний відмінок у реченні (Dative Nouns in Sentences)

Now that we know the **закінчення** (ending (grammar)) for all genders, we can start building complex, native-sounding sentences. The Dative case shines brightest when it works together with the Accusative case to show a complete transaction.

This is the Two-object verb pattern: Subject + Verb + Dative (recipient) + Accusative (thing). **Тетяна подарувала братові книгу.** (Tetiana gave a book to her brother). **Вчитель показав студентам карту.** (The teacher showed a map to the students). 

In these sentences, the Accusative case tells us *what* is being moved (the book, the map), and the Dative case tells us the **одержувач** (recipient) of the item.

To use this pattern, you need to know the right verbs. Here are the common verbs with indirect objects: **подарувати** (to give as a gift), **показати** (to show), **дати** (to give), **розповісти** (to tell, to narrate), **написати** (to write), **пояснити** (to explain), **відповісти** (to answer, to reply). Every time you use one of these verbs, your brain should automatically prepare a Dative noun.

Let's look at a dialogue practice — giving gifts, explaining things, writing to someone. We will visit a post office where people are sending items to their relatives.

> **(На пошті / At the post office)**
> **Відправник:** Добрий день! Я хочу відправити ці пакунки. *(Good day! I want to send these packages.)*
> **Працівник пошти:** Добрий день. Кому ви відправляєте? *(Good day. To whom are you sending?)*
> **Відправник:** **Студентові Петренку** — підручник. Це для навчання. *(To the student Petrenko — a textbook. It's for studying.)*
> **Працівник пошти:** Добре. А цей маленький пакунок? *(Okay. And this small package?)*
> **Відправник:** **Сестрі Олені** — листівка. Вона живе у Львові. *(To sister Olena — a postcard. She lives in Lviv.)*
> **Працівник пошти:** Зрозуміло. А третя коробка? *(Understood. And the third box?)*
> **Відправник:** **Дитині** — іграшка. Це подарунок на день народження. *(To the child — a toy. It's a birthday gift.)*
> **Працівник пошти:** Чудово. Я зараз **вам** усе оформлю. *(Wonderful. I will process everything for you now.)*

<!-- INJECT_ACTIVITY: match-up -->

In this conversation, the sender clearly identifies each **одержувач** using the Dative case: **студентові** (masculine, hard stem), **сестрі** (feminine, hard stem), and **дитині** (feminine, hard stem). Without the Dative case, the postal worker wouldn't know who receives what.

It is critical to contrast with Genitive constructions (**дати братові** vs. **немає брата**) to reinforce case discrimination. The Genitive case is used for absence, possession, and quantity. The Dative case is used for direction and receiving.

> **Читаємо українською: Давальний чи Родовий?**
> — Ти дав словник **братові**? (Did you give the dictionary to the brother?)
> — Ні, у мене зараз немає **брата** вдома. (No, I don't have the brother at home right now.)
> — Я хочу написати повідомлення **подрузі**. (I want to write a message to the female friend.)
> — Але у тебе немає номера цієї **подруги**! (But you don't have the number of this friend!)
> — Ми купили подарунок **вчителеві**. (We bought a gift for the teacher.)
> — Це книга нашого **вчителя**. (This is the book of our teacher.)

<!-- INJECT_ACTIVITY: unjumble -->

Notice how the ending shifts depending on the verb's requirement. **Дати братові** (to give to the brother) points toward him. **Немає брата** (there is no brother) indicates absence. Mastering this difference is what separates a beginner from a confident speaker. The Dative case gives your sentences movement, connecting people through words, gifts, and actions.

## Підсумок

У цьому модулі ми вивчили **Давальний відмінок** (the Dative case) для іменників усіх трьох родів. Тепер ви знаєте, як сказати, кому ви даєте подарунок, пишете лист або пояснюєте правило. 

Ви запам'ятали, що іменники чоловічого роду мають красиві паралельні закінчення **-ові/-еві/-єві** та **-у/-ю**, які можна чергувати для милозвучності. Іменники жіночого роду твердої групи приймають закінчення **-і** і часто мають **чергування** приголосних (к→ц, г→з, х→с). Іменники середнього роду використовують закінчення **-у/-ю**, а слова для малят мають особливе закінчення **-аті/-яті**. 

Завдяки дієсловам, таким як **подарувати**, **показати**, **написати** та **відповісти**, ви можете будувати розгорнуті речення і чітко розрізняти Давальний відмінок від Родового. Продовжуйте практикувати, і ці форми стануть для вас абсолютно природними!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-nouns
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

**Level: A2 (Module 18/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-sounds-letters [§4.1.1, §4.1.4]
**Звуки і літери** (Sounds and letters)
- **quiz** — Звук чи літера?: Розрізнити звук і літеру — основа української фонетики / Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Оберіть правильну відповідь*
- **match-up** — Літера → Звук: Зіставити літери зі звуковими значеннями, особливо багатозвучні (я, ю, є, ї) / Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *З'єднайте літеру зі звуком*
- **group-sort** — Голосні й приголосні: Розподілити звуки на голосні та приголосні / Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: Побачити зображення, визначити українську літеру / See image, identify the Ukrainian letter it starts with
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні знання
- ❌ fill-in-no-options: Занадто складно для A1 — початківці потребують варіантів відповідей

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

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
