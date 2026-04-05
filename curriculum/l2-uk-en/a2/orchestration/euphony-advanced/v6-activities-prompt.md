<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/euphony-advanced.yaml` file for module **12: Милозвучність у складних контекстах** (a2).

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

- `<!-- INJECT_ACTIVITY: activity-1 -->`
- `<!-- INJECT_ACTIVITY: activity-2 -->`
- `<!-- INJECT_ACTIVITY: activity-3 -->`
- `<!-- INJECT_ACTIVITY: activity-4 -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct euphonic variant (у/в, з/із/зі, і/й) in context
  items: 8
  type: quiz
- focus: Complete sentences with the correct preposition or conjunction form
  items: 8
  type: fill-in
- focus: Find euphony errors in sentences (e.g., *в вікно, *з школи, *і усі) and correct
    them
  items: 8
  type: error-correction
- focus: Match sentence beginnings with euphonically correct continuations
  items: 8
  type: match-up


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спрощення (simplification)
- уникати (to avoid)
- мелодійний (melodious)
- межа (boundary)
- правило (rule)
required:
- милозвучність (euphony, melodiousness)
- евфонія (euphony (technical term))
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- збіг (cluster, collision)
- прийменник (preposition)
- сполучник (conjunction)
- вживати (to use, to apply)
- складний (complex, compound)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ: Плани на вихідні

> — **Тарас:** Привіт, Оленко! У мене є чудова ідея. Поїдемо в Карпати чи у Львів? *(Hi, Olenka! I have a great idea. Shall we go to the Carpathians or to Lviv?)*
> — **Оленка:** У Львів! Із задоволенням! Я дуже давно там не була. *(To Lviv! With pleasure! I haven't been there for a very long time.)*
> — **Тарас:** Супер! Ми можемо орендувати велику квартиру в центрі міста. *(Super! We can rent a big apartment in the city center.)*
> — **Оленка:** Максим щойно написав: «Я поїду з Оленою й Тарасом». Він уже купив квитки. *(Maksym just wrote: "I will go with Olena and Taras". He already bought the tickets.)*
> — **Тарас:** Чудово! А ви зі Львова повернетесь у неділю? *(Great! And will you return from Lviv on Sunday?)*
> — **Оленка:** Так, ми поїдемо додому в неділю ввечері. *(Yes, we will go home on Sunday evening.)*
> — **Тарас:** Тоді зустрінемося на вокзалі в п'ятницю! *(Then let's meet at the train station on Friday!)*

Notice how Taras says «у Львів» instead of «в Львів». Saying «вЛьв» creates a harsh sound collision. To prevent this, Ukrainian relies on **милозвучність** (also known as **евфонія** in linguistic terms) — a core grammatical principle that actively avoids awkward clusters of consonants or vowels at word boundaries. 

You already know the basic **чергування** *(alternation)* of у/в and і/й. But how do you apply this in a **складний** *(complex)* sentence, after pauses, or when a word starts with a difficult consonant? To maintain a smooth rhythm, you adapt your prepositions and conjunctions based on the phonetic context.

### Читаємо українською (Reading in Ukrainian)

Українська мова — дуже мелодійна. *(The Ukrainian language is very melodious.)*
Милозвучність — це важливе граматичне правило. *(Euphony is an important grammar rule.)*
Ми завжди уникаємо важких звуків у реченні. *(We always avoid difficult sounds in a sentence.)*
Ми змінюємо маленькі слова для легкої вимови. *(We change small words for easy pronunciation.)*

## У чи в? Складні випадки

When you speak, sentence boundaries and punctuation marks create pauses. These pauses reset the phonetic environment. If a word starts a new sentence or follows a comma, there is no "previous word" to connect to. In this position, if the following word begins with a consonant (**приголосний**), you must use **«у»**.

### Читаємо українською (Reading in Ukrainian)

У Львові зараз іде дощ. *(It is raining in Lviv now.)*
Максим сказав, що у вівторок він вільний. *(Maksym said that on Tuesday he is free.)*
В Україні дуже гарно. *(It is very beautiful in Ukraine.)*

Notice the last example: **«В Україні»**. Here, «У» is a vowel. We use «в» to separate the vowels (pause + В + У), creating a smooth bridge. 

Ukrainian strictly avoids placing identical vowels or identical consonants next to each other. You cannot use «в» before words starting with «в» or «ф». Similarly, you cannot use «у» before «у». Therefore, **«в Одесі»** *(in Odesa)* is correct, but **«у університеті»** is an error. You must say **«в університеті»**.

### Читаємо українською (Reading in Ukrainian)

Ми їдемо в автобусі. *(We are riding in a bus.)*
Сьогодні вечірка в Олени. *(Today the party is at Olena's.)*
Я навчаюся в університеті. *(I am studying at the university.)*

This euphony rule also applies to prefixes in verbs and adverbs. Words like **увійти** / **ввійти** *(to enter)* or **увечері** / **ввечері** *(in the evening)* change their spelling simply to match the word before them. 

### Читаємо українською (Reading in Ukrainian)

Він увійшов до кімнати. *(He entered the room.)*
Вона ввійшла в будинок. *(She entered the house.)*
Брат приїхав увечері. *(The brother arrived in the evening.)*
Я читаю книжку ввечері. *(I read a book in the evening.)*

Some words resist these rules. Proper names of foreign cities usually keep their first letter intact. We write **«у Вашингтоні»** *(in Washington)* to preserve the name. Also, fixed expressions like **«в основному»** *(mainly)* generally stay the same.

### Читаємо українською (Reading in Ukrainian)

В основному ми працюємо вдома. *(Mainly we work at home.)*
Президент живе у Вашингтоні. *(The president lives in Washington.)*
Я хочу вчитися у Вроцлаві. *(I want to study in Wroclaw.)*

<!-- INJECT_ACTIVITY: activity-1 -->

## З, із чи зі? Правила перед збігами

The default preposition for "from" or "with" is **«з»**. We use it before vowels and before single consonants that are easy to pronounce.

### Читаємо українською (Reading in Ukrainian)

Я п'ю каву з молоком. *(I drink coffee with milk.)*
Він повернувся з роботи. *(He returned from work.)*
Ми часто говоримо з Оленою. *(We often talk with Olena.)*

However, when «з» meets a word starting with heavy consonants, especially sibilants like **с, з, ш, щ, ч, ж**, we must use **«із»**. Saying «з задоволенням» forces you to hold a long consonant sound. The vowel «і» separates the similar sounds smoothly.

### Читаємо українською (Reading in Ukrainian)

Я роблю це із задоволенням. *(I do this with pleasure.)*
Вона отримала лист із Сенегалу. *(She received a letter from Senegal.)*
Тарас зараз розмовляє із сусідом. *(Taras is talking with a neighbor now.)*

The variant **«зі»** acts as a phonetic shield. You must use **«зі»** if the following word starts with a combination of two or three consonants (a consonant cluster), particularly if that cluster starts with **з, с, ш, щ**. We also use it before the pronoun **«мною»** *(me)*.

### Читаємо українською (Reading in Ukrainian)

Діти йдуть зі школи. *(The children are walking from school.)*
Цей поїзд їде зі Львова. *(This train is going from Lviv.)*
Вона хоче говорити зі мною. *(She wants to speak with me.)*

In the Genitive case, these prepositions show origin or separation. Notice how the rhythmic flow connects the preposition and the Genitive ending **-и** or **-і / -ї**.

### Читаємо українською (Reading in Ukrainian)

Кіт зістрибнув зі столу. *(The cat jumped down from the table.)*
Він походить із гарної сім'ї. *(He comes from a good family.)*
Свіжі гриби принесли з лісу. *(The fresh mushrooms were brought from the forest.)*

Do not overuse «зі». If a word starts with only one consonant, using «зі» is an error. Saying «зі ним» instead of «з ним» sounds unnatural.

### Читаємо українською (Reading in Ukrainian)

Я працюю з ним кожен день. *(I work with him every day.)*
Ми з тобою добре розуміємо це. *(You and I understand this well.)*

<!-- INJECT_ACTIVITY: activity-2 -->

## І чи й? У складних реченнях (I or Y? In Complex Sentences)

You know to use **«й»** after vowels and **«і»** after consonants (e.g., «мама й тато», «брат і сестра»). But when you join two independent clauses together, you usually place a comma between them. A comma is a pause. The default choice after any pause—a comma, a dash, or the beginning of a sentence—is always **«і»**.

### Читаємо українською (Reading in Ukrainian)

Він купив квитки, і ми пішли в кіно. *(He bought tickets, and we went to the cinema.)*
Світить сонце, і пташки співають. *(The sun is shining, and birds are singing.)*
Завтра буде тепло, і ми поїдемо в ліс. *(Tomorrow it will be warm, and we will go to the forest.)*

The letter «й» is a semivowel. It needs a preceding vowel to lean on. When a punctuation mark creates a pause, that support disappears. Starting a sentence or a new clause with «й» breaks the rules of euphony. 

### Читаємо українською (Reading in Ukrainian)

І він прийшов на зустріч вчасно. *(And he came to the meeting on time.)*
Діти гралися, і мама дивилася на них. *(The children were playing, and mom was watching them.)*
Вона заспівала, і всі замовкли. *(She started singing, and everyone went silent.)*

If you are unsure which conjunction to apply, you can always **вживати** *(to use)* the word **«та»**. In this context, «та» is an absolute synonym for «і» *(and)*. It never changes its form, regardless of the surrounding vowels and consonants. 

### Читаємо українською (Reading in Ukrainian)

Я та ти — хороші друзі. *(You and I are good friends.)*
Він багато працює та мало відпочиває. *(He works a lot and rests a little.)*
Сьогодні холодно, та йде сильний сніг. *(Today is cold, and heavy snow is falling.)*

When you have a long list of nouns, repeating the same conjunction sounds monotonous. To make a list sound melodious, native speakers mix «і», «й», and «та». 

### Читаємо українською (Reading in Ukrainian)

На столі лежать зошити й ручки, книги та олівці. *(Notebooks and pens, books and pencils are lying on the table.)*
Ми бачили Олену й Максима, Анну та Івана. *(We saw Olena and Maksym, Anna and Ivan.)*

<!-- INJECT_ACTIVITY: activity-3 -->

## Все разом: мелодійні речення

When you force a consonant cluster, the natural flow of the sentence breaks.

Спробуйте сказати: «Ми йшли з школи вчора». *(Try to say: "We walked from school yesterday" — incorrect.)*

The cluster «з шк» is difficult to pronounce quickly. Now try the correct version:

«Ми йшли зі школи вчора». *(We walked from school yesterday — correct.)*

Analyze this sentence that uses all three types of alternations: **у/в**, **з/із/зі**, and **і/й/та**. 

> **У** неділю ми **з** друзями поїдемо **у** Львів **із** задоволенням **і** відвідаємо замок.
*(On Sunday, my friends and I will go to Lviv with pleasure and visit the castle.)*

Why did we choose these forms?
- **У неділю**: beginning of the sentence before a consonant.
- **з друзями**: default «з» before a normal consonant.
- **у Львів**: «у» is mandatory before the «Льв» consonant cluster.
- **із задоволенням**: «із» separates «в» and «з», avoiding a heavy cluster.
- **і відвідаємо**: «і» is placed between two consonants («м» and «в») after a breath pause or logical grouping.

> — **Оксана:** Привіт! Ти підеш у кіно зі мною в суботу? *(Hi! Will you go to the movies with me on Saturday?)*
> — **Марко:** Привіт! Із задоволенням! А що ми будемо дивитися? *(Hi! With pleasure! And what will we watch?)*
> — **Оксана:** Новий фільм про кохання й пригоди. *(A new movie about love and adventures.)*
> — **Марко:** Добре. Ми зустрінемося в центрі чи біля школи? *(Good. Will we meet in the center or near the school?)*
> — **Оксана:** Давай зустрінемося в парку, а потім підемо в кінотеатр. *(Let's meet in the park, and then we will go to the cinema.)*
> — **Марко:** Домовилися! Я куплю квитки й попкорн. *(Agreed! I will buy tickets and popcorn.)*

### Читаємо українською (Reading in Ukrainian)

Вона працює в школі й дуже любить дітей. *(She works at school and loves children very much.)*
Увечері ми з братом граємо в ігри. *(In the evening, my brother and I play games.)*
Вони живуть у Києві, а працюють у Фастові. *(They live in Kyiv, but work in Fastiv.)*
Він вийшов із кімнати й пішов на вулицю. *(He left the room and went outside.)*
Я п’ю каву з молоком і читаю новини. *(I drink coffee with milk and read the news.)*

<!-- INJECT_ACTIVITY: activity-4 -->

## Підсумок — Summary (~160 слів)

Милозвучність — це фундамент української мови. *(Euphony is the foundation of the Ukrainian language.)* Вивчення цих правил робить ваше мовлення природним і легким. *(Learning these rules makes your speech natural and easy.)* 

*   **Коли після коми ми вживаємо «у», а коли «в»?** *(When do we use "у" and when "в" after a comma?)*
    Після коми або тире фонетичний контекст оновлюється. *(After a comma or a dash, the phonetic context resets.)* Це означає, що ми не дивимося на слово перед комою. *(This means we do not look at the word before the comma.)* Вибір залежить тільки від першого звука наступного слова. *(The choice depends only on the first sound of the next word.)*
    > — **Вчитель:** Він прочитав книгу, **у** якій були цікаві історії. *(He read a book, in which there were interesting stories.)*
    > — **Учень:** Вона зайшла в клас, **в** аудиторії було тихо. *(She entered the class, it was quiet in the auditorium.)*

*   **Яка різниця між «з мною» та «зі мною»?** *(What is the difference between "з мною" and "зі мною"?)*
    Варіант «з мною» є неправильним, тому що створює важкий збіг приголосних звуків. *(The variant "з мною" is incorrect because it creates a heavy cluster of consonant sounds.)* Ми завжди використовуємо «зі», коли наступне слово починається з кількох приголосних. *(We always use "зі" when the next word starts with several consonants.)*
    > — **Анна:** Ти підеш у театр **зі** мною сьогодні? *(Will you go to the theater with me today?)*
    > — **Петро:** Так, я із задоволенням піду **зі** своїми друзями. *(Yes, I will gladly go with my friends.)*

*   **Чому не можна починати речення зі сполучника «й»?** *(Why is it impossible to start a sentence with the conjunction "й"?)*
    Сполучник «й» завжди потребує голосного звука безпосередньо перед собою. *(The conjunction "й" always requires a vowel sound immediately before it.)* На початку речення немає попереднього слова, тому ми завжди вживаємо «і». *(At the beginning of a sentence, there is no previous word, so we always use "і".)*
    > **І** мама, **і** тато працюють у школі. *(Both mom and dad work at school.)*

*   **Як слово «та» допомагає уникнути помилок?** *(How does the word "та" help avoid mistakes?)*
    Сполучник «та» є синонімом до слова «і». *(The conjunction "та" is a synonym for the word "і".)* Воно завжди звучить однаково, незалежно від сусідніх звуків. *(It always sounds the same, regardless of the neighboring sounds.)* 
    > Ми купили молоко **та** хліб у магазині. *(We bought milk and bread in the store.)*
    > Брат **та** сестра грають у парку. *(Brother and sister are playing in the park.)*

Завжди слухайте українську мову, коли говорите нею. *(Always listen to the Ukrainian language when speaking it.)* Якщо ви відчуваєте напругу у вимові, змініть прийменник або сполучник. *(If you feel tension in pronunciation, change the preposition or conjunction.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: euphony-advanced
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

**Level: A2 (Module 12/60) — ELEMENTARY**

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
