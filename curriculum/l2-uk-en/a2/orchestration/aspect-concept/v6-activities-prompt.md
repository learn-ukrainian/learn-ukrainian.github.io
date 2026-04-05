<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-concept.yaml` file for module **2: Зроблено чи в процесі? Вступ до виду дієслів** (a2).

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

(No injection markers found in prose. All activities will go to workbook.)

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Aspect Sorting: Process vs. Result'
  items: 8
  type: quiz
- focus: Identify the Aspect in Sentences
  items: 8
  type: fill-in
- focus: Choose the Correct Aspect (Context-based)
  items: 8
  type: match-up
- focus: Find and fix wrong aspect choice in sentences (e.g., *Він щодня зробив вправи
    → робив, *Вона довго написала листа → писала)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- завершений (completed, finished)
- тривалий (ongoing, lasting)
- одноразовий (single, one-time)
- концепція (concept)
required:
- вид дієслова (verb aspect)
- недоконаний вид (imperfective aspect)
- доконаний вид (perfective aspect)
- процес (process)
- результат (result)
- дія (action)
- повторення (repetition)
- робити / зробити (to do)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що таке вид дієслова?

If you have ever tried to explain English grammar to a Ukrainian speaker, you might have noticed their confusion over the difference between "I am doing" and "I do." English relies heavily on tense to convey the exact moment and frequency of an action. Ukrainian verbs, however, possess a hidden dimension that operates on a completely different logic. Instead of asking *when* an action happens with laser precision, Ukrainian asks a much more fundamental question about the nature of the event: is the action about the continuous process of "doing," or is it about the hard fact that it is "done"? This critical dimension is called **вид дієслова** (verb aspect). Understanding this core concept is the absolute foundation of speaking natural Ukrainian. It forces you to shift your mental focus away from the timeline and toward the result.

In Ukrainian, almost every verb you learn belongs to one of two distinct categories. The first is **недоконаний вид** (imperfective aspect). If we look at the literal translation of this grammatical term, it essentially means "not-finished-looking." This aspect is all about the **процес** (process), the duration, or the **повторення** (repetition) of an action. It tells us that an activity is ongoing, but it deliberately does not tell us if it ever reached a conclusion. The second category is **доконаний вид** (perfective aspect). Literally, this translates to "finished-looking." We use this aspect specifically to talk about a single, successfully completed **дія** (action). The focus here is entirely on the **результат** (result) or the definitive boundary of the action. To speak Ukrainian correctly, you must constantly decide whether you are describing the journey or the destination. The verbs **робити** (to do) and **зробити** (to have done) clearly illustrate this pairing.

A helpful way to visualize this grammatical difference is the "movie versus snapshot" analogy. Using an imperfective verb is just like watching a video reel. If you watch a video of a cat playing with a toy, you are observing the continuous, fluid, and ongoing action. You see the movement happening right in front of you, but you do not necessarily see the end of the game. Using a perfective verb, on the other hand, is like looking at a single photograph. The picture shows the exact moment the cat has definitively caught the toy. The action is completely over, the dust has settled, and you are looking at the final, undeniable result.

Let's see this dynamic in a real-life context. Imagine two friends are watching a tense football match on television. They naturally switch between both aspects to comment on the unfolding game.

> — **Олег:** Дивись, він дуже швидко біжить! *(Look, he is running very fast!)*
> — **Максим:** Так, вони грають сьогодні просто чудово. *(Yes, they are playing simply wonderfully today.)*
> — **Олег:** Він довго тримає м'яч. Що він робить? *(He is holding the ball for a long time. What is he doing?)*
> — **Максим:** Ого! Він щойно передав м'яч прямо в центр! *(Wow! He just passed the ball right into the center!)*
> — **Олег:** І він нарешті забив гол! *(And he finally scored a goal!)*
> — **Максим:** Це справді неймовірний результат. *(This is truly an incredible result.)*

Notice how **біжить** (is running), **грають** (are playing), and **робить** (is doing) describe the ongoing, unresolved process on the screen. But the sudden, completed actions—**передав** (passed) and **забив** (scored)—focus entirely on the final, irreversible result of the play.

Because perfective verbs inherently describe a completed result, they do not have a true present tense. Logically, you cannot be currently in the middle of finishing something instantaneously. Therefore, as we begin exploring this new system, we will focus primarily on the past and present tenses. We will look at how to describe what you were doing in the past versus what you actually accomplished. Mastering this conceptual distinction is the ultimate key to unlocking all future verb usage in the Ukrainian language.


## Недоконаний вид: Процес і повторення

When we talk about the imperfective aspect, or **недоконаний вид** (imperfective aspect), we are primarily focusing on the concept of a process. This means that the duration of the action is what truly matters to the speaker, not the final outcome. Imagine you are describing how you spent your afternoon. You might say the following sentence.

«Я читав книгу дві години.» *(I was reading a book for two hours.)*

In this example, the verb **читав** (was reading) highlights the fact that you were actively engaged in the activity. It is completely irrelevant whether you actually finished the book. What matters is that you were busy doing it. We use the imperfective aspect whenever we want to emphasize the continuous flow of time. For instance, you can paint a picture of a continuous state with these phrases.

«Я працював весь день.» *(I was working all day.)*

«Вони відпочивали в парку.» *(They were relaxing in the park.)*

Similarly, the verb **гуляти** (to walk) naturally implies a process.

«Ми гуляли містом.» *(We were walking around the city.)*

The focus is entirely on the journey, not the destination.

The second major use of the imperfective aspect is to describe repetition and habit. Any action that happens regularly or cyclically absolutely must be expressed using an imperfective verb. Because these actions are ongoing patterns in your life rather than single, isolated events, the imperfective aspect is the only grammatically correct choice. For example, if you want to talk about your morning exercise routine, you would say the following.

«Щодня я роблю вправи.» *(Every day I do exercises.)*

The verb **роблю** (do) is imperfective because the action repeats. The same logic applies to places you visit frequently or things you buy on a regular basis. You might tell a friend about your local bakery.

«Ми часто купуємо хліб тут.» *(We often buy bread here.)*

The verb **купуємо** (buy) captures the recurring nature of this action. Whether an event happens every day, once a week, or just a few times a year, the fact that it repeats makes it an ongoing habit.

Another important function of the imperfective aspect is to state general facts or to simply name an activity without any focus on a specific result. Sometimes, you just want to say that an action took place or that someone likes doing something, without worrying about the beginning, middle, or end. For example, you can describe a general truth.

«Діти люблять читати.» *(Children love to read.)*

You are using the imperfective verb **читати** (to read) to state a fact. This brings us to a crucial grammatical rule: in the present tense, only imperfective verb forms exist. Why? Because the "now" is, by definition, an ongoing process. You cannot be in the present moment and have already completed an action in that same instant. Therefore, whenever you describe what you are doing right now, you must use the imperfective aspect.

«Я пишу листа.» *(I am writing a letter.)*

To make choosing the correct aspect easier, Ukrainian uses specific signal words that almost always point to the imperfective aspect. These are adverbs that express duration, frequency, or repetition. When you see these words, you can be highly confident that an imperfective verb will follow. The word **завжди** (always) clearly shows a continuous habit.

«Вона завжди п'є каву.» *(She always drinks coffee.)*

The word **часто** (often) indicates repetition.

«Ми часто ходимо в кіно.» *(We often go to the cinema.)*

If something happens on a regular schedule, you will use **зазвичай** (usually) or **щодня** (every day).

«Зазвичай я працюю вдома.» *(Usually I work at home.)*

To emphasize the length of an action, we use **довго** (for a long time).

«Він довго писав листа.» *(He was writing a letter for a long time.)*

Finally, **кожного разу** (every time) signals a cycle.

«Кожного разу ми бачимо цю собаку.» *(Every time we see this dog.)*

Now let's compare how the imperfective aspect looks in the present and the past tense, using the verb **читати** (to read). Remember that the core meaning of the imperfective—focusing on the process or continuity of the action—remains exactly the same regardless of the time period. In the present tense, you say the following.

«Я читаю цікаву статтю.» *(I am reading an interesting article.)*

This means you are currently in the middle of the activity. The process is happening right now. In the past tense, the form changes, but the focus on continuity does not.

«Вчора ввечері я читав цікаву статтю.» *(Yesterday evening I was reading an interesting article.)*

The imperfective past tense **читав** (was reading) tells us that the action took up a block of time in the past. It does not tell us if you finished the article; it only emphasizes that your evening was occupied by the continuous act of reading.


## Доконаний вид: Результат!

In the previous section, we looked at how the imperfective aspect acts like a video camera, recording the ongoing process of an action. Now, let us introduce the perfective aspect, or **доконаний вид** *(perfective aspect)*. The perfective aspect is not interested in the process. It does not care how long an activity took, or how many times you repeated it. Instead, the perfective aspect is entirely focused on the final result. It is the finish line of an action. When you use a perfective verb, you are stating that the action is completely closed and finished. Let us look at a classic example. «Я прочитав книгу.» *(I have read the book.)* The verb **прочитав** *(have read)* is perfective. This sentence means that you reached the very last page, you closed the cover, and the book is now sitting on your shelf. You possess the complete knowledge of the story. You achieved the goal of reading it.

Because the perfective aspect focuses on a completed result, it is the perfect tool for describing single, sudden actions. If an event happens only once and is over in a flash, it has a clear beginning and an immediate end. «Раптом він впав.» *(Suddenly he fell.)* The verb **впав** *(fell)* describes an action that cannot really be stretched out as a continuous habit in this context. It happened once, and the result is that he is now on the ground. Similarly, mental realizations are often treated as sudden, completed events. «Вона нарешті зрозуміла правило.» *(She finally understood the rule.)* The verb **зрозуміла** *(understood)* shows that the process of thinking is over. The confusion is gone, and the clear result is her new understanding. The perfective aspect often carries a strong implication of success.

There is a fascinating and crucial grammatical rule about the perfective aspect that you must remember: perfective verbs do not have a present tense. This is sometimes called the "present tense trap." Think about the logic behind this rule. If an action is happening right now, in the present moment, it is still ongoing. Therefore, it cannot be completely finished yet. If you take a perfective verb and add present tense endings to it, the meaning automatically shifts into the future. For example, «Я зроблю це.» *(I will do this.)* The verb **зроблю** *(will do)* means that you promise to complete the action and achieve the result in the future. For now, we will focus primarily on the past tense forms of perfective verbs, which clearly show a result achieved in the past. Words like **зробив** *(finished)*, **написав** *(wrote)*, and **купив** *(bought)* are your main tools.

Just like the imperfective aspect has signal words that point to a continuous process, the perfective aspect has its own set of adverbs that highlight a completed result. When you see these words, they strongly suggest that a perfective verb is needed. The word **раптом** *(suddenly)* shows that an action happened unexpectedly and is already complete. The word **нарешті** *(finally)* emphasizes that a long wait is over and the result is achieved. The word **вже** *(already)* is a classic marker of completion. «Вона вже зробила домашнє завдання.» *(She already did the homework.)* This means her desk is clear and she is free to go outside. Finally, phrases like **за годину** *(within an hour)* show that a result will be or was reached after a specific amount of time.

In Ukrainian, most verbs travel together in pairs. These pairs consist of one imperfective verb and one perfective verb that share the exact same core meaning, but view the action from different angles. We call these "aspectual pairs." For example, the basic action of doing or making is represented by the pair **робити** *(to do)* and **зробити** *(to finish doing)*. The action of writing is represented by **писати** *(to write)* and **написати** *(to finish writing)*. You will notice a common pattern here. Very often, the perfective verb is formed simply by adding a short prefix to the beginning of the imperfective verb. Prefixes like «з-», «на-», or «про-» act as the finish line marker. They transform the open-ended process into a closed, completed result. Learning these pairs is a key part of mastering Ukrainian verbs.

<!-- INJECT_ACTIVITY: quiz, Aspect Sorting -->

<!-- INJECT_ACTIVITY: fill-in, Identify Aspect in Sentences -->


## Порівняння пар: Бачимо різницю (Comparing Pairs: Seeing the Difference)

Let's look at a side-by-side comparison to truly understand how these verbs feel in action. Imagine a friend tells you: «Він писав лист.» *(He was writing a letter.)* This sentence uses the imperfective verb **писав** *(was writing)*. It immediately makes you think about the physical effort, the process, and the time spent. You picture him sitting at his desk for hours, holding a pen, and thinking carefully about what to say. We do not know if he ever finished it, or if he just threw the paper away. Now, compare that to the perfective version: «Він написав лист.» *(He wrote a letter.)* By adding a simple prefix to make the perfective verb **написав** *(wrote / finished writing)*, the entire mental picture changes. You no longer think about the desk, the pen, or the time it took. Instead, you picture a tangible result: a finished letter in an envelope, folded, stamped, and ready to be sent to the post office. The ongoing process is completely over, and the final result is right in your hands.

A great way to master this concept is by visualizing the difference on an imaginary timeline. Think of the imperfective aspect (НВ) as a long, continuous line drawn on a page (————). It represents an action stretching through time without a clear end. For example, «Я готувала вечерю.» *(I was cooking dinner.)* This sentence shows you were busy in the kitchen for a while, chopping vegetables and stirring pots. However, it does not guarantee a successful meal. Maybe the stove broke, you got distracted, or maybe the food burnt completely! On the other hand, think of the perfective aspect (ДВ) as a single, solid point (X) marking the exact end of that line. It represents the precise moment of successful completion. «Я приготувала вечерю.» *(I have cooked dinner.)* This sentence means the hard work is done, the plates are set on the table, and a delicious dinner is officially served. Let's look at another common pair: «Ми вчили слова.» *(We were learning words.)* versus «Ми вивчили слова.» *(We learned the words.)* The first describes a long study session, while the second means the vocabulary is memorized and you are completely ready for the test. You only use the perfective when you have a clear, undeniable result to show for your effort.

<!-- INJECT_ACTIVITY: match-up, Choose the Correct Aspect (Context-based) -->
<!-- INJECT_ACTIVITY: error-correction, Find and fix wrong aspect choice in sentences -->


## Підсумок (Summary)

Let's review the core rules of the Aspect Matrix. Choosing between the imperfective and perfective aspect completely changes your story.

The imperfective aspect, or **недоконаний вид** *(imperfective aspect)*, focuses on the action itself. You use it to describe a continuous process, like «**Я працював**» *(I was working)*, a regular repetition, like «**Я часто працюю**» *(I often work)*, or a general fact.

The perfective aspect, or **доконаний вид** *(perfective aspect)*, focuses exclusively on the destination. You use it to declare a single, successfully completed result, like «**Я попрацював**» *(I finished working)*, or a sudden change in state, like «**Я прийшов**» *(I arrived)*.

When you are unsure which verb to use, run a quick self-check:
- Is there a final result? If yes, choose the perfective aspect (ДВ).
- Is this action repeating? If yes, choose the imperfective aspect (НВ).
- Is the action happening right now? If yes, always choose the imperfective aspect (НВ).

Remember, Ukrainian verbs almost always come in pairs. Choosing the correct one allows you to be perfectly precise about your actions!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-concept
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

**Level: A2 (Module 2/60) — ELEMENTARY**

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
