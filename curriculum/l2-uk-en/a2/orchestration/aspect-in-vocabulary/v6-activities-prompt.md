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
- `<!-- INJECT_ACTIVITY: fill-in-categorize-by-formation-type -->`
- `<!-- INJECT_ACTIVITY: match-up-fill-in-the-blanks-with-the-correct-pair -->`
- `<!-- INJECT_ACTIVITY: fill-in-choose-the-correct-aspect-partner -->`

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
## Чому дієслова потрібно вчити парами? (Why Verbs Must Be Learned in Pairs)

Imagine going to a shoe store, buying a left sneaker, and leaving the right one on the shelf. That is exactly what happens when you learn a Ukrainian verb without its partner. In Ukrainian grammar, the vast majority of verbs exist in an aspectual pair. 

* **Видова пара** — aspectual pair.

For example, you might learn a word for writing. 

* **Писати** — to write, to be writing.

If you learn this without its partner, you only have half the vocabulary needed for that action. You might know how to say you were writing a letter, but you will not know how to express that you actually finished it. This is where the perfective partner comes in.

* **Написати** — to write completely, to finish writing.

The core difference between the two halves of the pair comes down to the question you are answering. Are you describing an ongoing process, or are you announcing a final result? 

«Що ти робив?» *(What were you doing?)*

Here, they are asking about the continuous process. Alternatively, they might only want to know the completed result.

«Що ти зробив?» *(What have you done?)*

Let us see how this dynamic plays out in real life. Imagine a grandmother teaching her granddaughter how to cook a traditional Ukrainian dish. Notice how she naturally switches between focusing on the continuous process and the finalized result.

> — **Бабуся:** Ліпи вареники, поки я грію воду. *(Keep forming varenyky while I heat the water.)*
> — **Онучка:** Я вже зліпила десять! *(I have already formed ten!)*
> — **Бабуся:** Тепер вари їх п'ять хвилин, поки вони не спливуть. *(Now boil them for five minutes until they float.)*
> — **Бабуся:** Як звариш — клич усіх до столу. *(When you have finished boiling them — call everyone to the table.)*

The logic here is entirely about process versus result. Let us look at another common household scenario using words for cleaning.

* **Прибирати** — to be cleaning, to tidy up.
* **Прибрати** — to have cleaned, to have tidied up.

The imperfective verb describes the physical effort and the time spent. It means you were moving things around and sweeping the floor. However, it does not guarantee that the room is actually clean at the end. The perfective verb describes the final, successful result. It means you have achieved a completely clean room.

Because these concepts are closely linked in everyday communication, you should never learn them separately. From now on, you must memorize these verbs as a single, inseparable lexical unit. You are not just learning one word anymore. Your new vocabulary entry is the complete pair.

* **Прибирати / прибрати** — to clean / to have cleaned.

How do you find these pairs when you are studying on your own? Navigating a Ukrainian dictionary is much easier once you understand this system. When you look up an action, modern dictionaries will usually list the pair together. The imperfective form usually comes first as the base word.

* **Недоконаний вид** — imperfective aspect.

Right next to it, you will see its partner, the perfective form.

* **Доконаний вид** — perfective aspect.

For instance, you might search for a verb meaning to do or to make.

* **Робити** — to do, to make.
* **Зробити** — to have done, to have made.

In authentic Ukrainian resources, you will frequently encounter standard abbreviations. You will see «нед.» for the imperfective aspect and «док.» for the perfective aspect. Knowing these labels will help you always find the missing shoe for your new vocabulary.


## Спосіб 1: Додавання префікса (Method 1: Adding a Prefix)

In the Ukrainian language, the most productive and predictable way to create a perfective verb is through the grammatical process of prefixation. You simply take a basic imperfective verb, which describes an ongoing or repeated process, and securely attach a short prefix to its beginning. This single, small addition instantly transforms the word into a perfective verb, permanently shifting its focus from the continuous process to the final, successful result. You can think of this added prefix as a tiny grammatical seal of completion. For a clear and practical example, consider the basic process of reading a book.

* **Читати** — to read, to be reading.

If you want to announce to someone that you have finished reading a book completely, from the very first page to the very last, you must add a specific prefix.

* **Прочитати** — to read through, to finish reading.

The core meaning of the action remains exactly the same, but the grammatical perspective has shifted entirely to the achieved, final result.

While there are many different prefixes available in the Ukrainian language, the prefix «по-» is undeniably the most frequent, versatile, and absolutely essential. It acts as a universal marker of completion for a truly massive number of everyday actions. Whenever you see a verb starting with this specific prefix, there is a very high probability that you are looking at the perfective half of a standard aspectual pair. This prefix often simply signals that a regular, expected daily action has reached its natural and logical conclusion. Look at these essential vocabulary pairs that you will need to use constantly in your daily Ukrainian conversations.

* **Бачити / побачити** — to see / to catch sight of.
* **Чути / почути** — to hear / to catch a sound of.
* **Снідати / поснідати** — to have breakfast / to finish having breakfast.
* **Дякувати / подякувати** — to thank / to express thanks.

Beyond the universal marker, certain prefixes naturally gravitate toward specific types of actions, themes, and tasks. For creative, communicative, or surface-level actions, you will frequently encounter the productive prefix «на-». It often implies producing a physical, tangible result or successfully accumulating a certain amount of something.

* **Писати / написати** — to write / to write down completely.
* **Малювати / намалювати** — to draw / to finish drawing.

Another highly common prefix is «про-», which we already saw successfully applied to the concept of reading. It often carries the subtle nuance of an action moving steadily through something, whether it is moving through a physical text or moving through a specific period of time.

* **Жити / прожити** — to live / to live through a specific period.

«Я жив там довго.»

This sentence means "I lived there for a long time," and it strictly describes the continuous state of living. Conversely, look at the perfective version.

«Я прожив там рік.»

This means "I lived through a year there," and it firmly focuses on the completed block of time as a single, achieved result.

Another fundamental prefix for creating perfective verbs is «з-». You will need to use it constantly in your daily life, most notably with the primary verb for doing or making things.

* **Робити / зробити** — to do / to have done.

However, this specific prefix comes with an incredibly important phonetic rule that you must remember. Ukrainian spelling and pronunciation always strive for natural harmony and ease of speech. If the root verb begins with a voiceless consonant, specifically the letters «к», «п», «т», «ф», or «х», the voiced prefix «з-» automatically transforms into the voiceless «с-». Ukrainian schoolchildren memorize these five specific letters using a simple, memorable mnemonic phrase.

«Кафе Птах.»

This translates to "Cafe Bird." Because of this strict phonetic rule, the prefix must adapt itself to perfectly match the voiceless sounds of the root verb.

* **Казати / сказати** — to say / to tell.
* **Фотографувати / сфотографувати** — to photograph / to take a photo.

Finally, let us look at the highly productive prefixes «ви-» and «за-», which are frequently used for actions involving consumption, extraction, or complete mastery. The prefix «ви-» literally means "out," and it often implies using something up completely or extracting a final, definitive result from a process.

* **Пити / випити** — to drink / to drink up completely.
* **Вчити / вивчити** — to study / to master or memorize.

Notice the crucial difference in the learning process depicted here.

«Я вчив ці слова.»

This sentence means "I was studying these words," and it simply describes the time and effort you spent looking at the textbook. However, look at the result.

«Я вивчив ці слова.»

This means "I have mastered these words," confirming that the specific information is now permanently stored in your head. The prefix «за-» is also incredibly common, particularly in administrative, financial, or modern transactional contexts.

* **Платити / заплатити** — to pay / to complete a payment.
* **Телефонувати / зателефонувати** — to call / to make a phone call.

<!-- INJECT_ACTIVITY: quiz-find-partner -->


## Спосіб 2: Зміна в корені або суфіксі

У попередньому розділі ми бачили, як префікс перетворює недоконаний процес на доконаний результат. In the previous section, we saw how adding a prefix builds a perfective result from an imperfective process. However, the Ukrainian language also employs the exact opposite logic. Sometimes, the perfective verb is the shorter, simpler form, representing a quick, defined action. To talk about the ongoing process leading up to that result, we stretch the verb by adding a suffix or changing its internal structure, creating the imperfective form. This reverse engineering is especially common with verbs that already contain a prefix as part of their core meaning. Instead of piling on more prefixes, the language modifies the end of the word to show duration. Recognizing these suffix patterns helps you instantly identify whether a verb describes a quick result or a drawn-out process.

One of the most frequent ways to stretch a perfective verb into an imperfective process is by inserting the suffix «-ува-» or «-юва-». Think of this suffix as a rubber band that elongates the action. Let us look at an essential pair for making choices.

* **Вирішувати / вирішити** — to decide (process) / to decide (result).

Notice how «вирішити» is a sharp, crisp action. You make the choice, and it is done. But «вирішувати» takes longer to say. Those extra syllables mimic the duration of the thinking process and the weighing of options. «Я довго вирішував, що робити.» This means "I was deciding for a long time what to do." «Нарешті я вирішив.» This means "Finally, I decided." Another crucial pair uses this exact pattern.

* **Запитувати / запитати** — to ask (process) / to ask (result).

If you are constantly asking questions, you use the long «запитувати». For one quick question, you use the short «запитати». 

Another extremely common pattern involves shifting the vowel suffix just before the infinitive ending. We frequently see imperfective verbs using the broad, open «-а-» or «-я-», while their perfective partners switch to a tighter «-и-» or a completely different concise ending. The open «-а-» sound naturally feels more continuous, whereas the «-и-» ending feels sharper and more final.

* **Відчиняти / відчинити** — to open (process) / to open (result).

When you say «відчиняти», the mouth stays open longer, reflecting the ongoing action of pushing the door. When you say «відчинити», the action snaps shut like a lock. «Хто відчиняв вікно?» This translates to "Who was opening the window?" We see a similar, though slightly irregular, shift in another vital verb pair.

* **Відповідати / відповісти** — to answer (process) / to answer (result).

The long «відповідати» describes the ongoing process of giving a detailed response, while the compact «відповісти» is the final, delivered answer.

Sometimes, adding an imperfective suffix forces a deeper phonetic change inside the word. The root vowel changes to accommodate the new rhythm. This phenomenon is called vowel alternation, or «чергування». The most frequent shift is the vowel «о» transforming into the broad «а» when moving from a quick result to an extended process. Let us examine a high-frequency verb pair.

* **Допомагати / допомогти** — to help (process) / to help (result).

The perfective base «допомогти» describes a single, completed act of assistance. To create the imperfective form, we add the «-а-» suffix. But the root also changes from «допомог-» to «допомаг-». The double «а» sounds make the word feel much wider. «Вона завжди мені допомагала.» This means "She always helped me." Conversely, «Він допоміг мені вчора.» This translates to "He helped me yesterday," emphasizing a single intervention.

Finally, we must look at a special suffix used to create perfective verbs out of continuous sounds or repetitive movements. Adding the suffix «-ну-» instantly transforms an ongoing action into a single, sudden, and complete event. It acts like a camera flash, capturing just one split second of a longer activity.

* **Стукати / стукнути** — to knock (repeatedly) / to give a single knock.

If you are standing at the door knocking over and over, you use «стукати». If you just tap the wood once, it is «стукнути». This pattern applies to many physical actions and loud noises.

* **Кричати / крикнути** — to shout (process) / to let out a single cry.
* **Штовхати / штовхнути** — to push (continuously) / to give a single shove.

The «-ну-» suffix is your clearest indicator that something happened once, abruptly, and is now entirely over.

<!-- INJECT_ACTIVITY: fill-in-categorize-by-formation-type -->


## Спосіб 3: Зовсім інші слова (суплетивізм)

Sometimes, the most fundamental verbs in a language do not follow predictable patterns at all. Instead of adding a prefix or changing a suffix, they use completely different words for the continuous process and the final result. Linguists call this phenomenon suppletion. You already know how this works in English; the past tense of "go" is "went," which looks like a completely unrelated word. In Ukrainian, a few essential aspectual pairs work the exact same way. Because these verbs describe actions we perform every single day, you simply have to memorize them as distinct pairs. The most critical pair in this category is **брати / взяти** (to take). You use «брати» when you are in the process of taking things, and «взяти» for a single, completed grab. 

«Вона часто брала мої речі.» (She often took my things.)

«Вчора вона взяла мій телефон.» (Yesterday she took my phone.)

Another incredibly common pair is the speech pair: **говорити / сказати** (to speak, talk / to say, tell). It is vital to understand the difference here. «Говорити» describes the ongoing act of communicating, having a conversation, or speaking a language. It is a continuous process. On the other hand, «сказати» is the act of delivering a specific message or making a single statement. It is the end result of the speaking process.

«Ми довго говорили про життя.» (We talked about life for a long time.)

«Він сказав правду.» (He told the truth.)

You cannot use «сказати» to mean "having a conversation," and you cannot use «говорити» when you mean "he said one specific thing."

Next, we must look at the "search versus find" distinction. Learners are almost always taught the verbs **шукати** (to search, look for) and **знайти** (to find) as an aspectual pair. While they function together logically in real life, they are technically two different actions. You search (the process), and as a result, you find (the result). The true perfective form of «шукати» is actually «пошукати» (to search for a little while), but in everyday situations, «знайти» is the result we are usually hoping for. Similarly, we have the pair **ловити / піймати** (to catch). You spend time trying to catch something («ловити»), but the moment of capture is instantaneous («піймати»).

We have covered a lot of ground in this module. To help you organize your vocabulary, here is a summary table of the most important aspectual pairs you need for the A2 level, grouped by how they are formed. We have also included one more essential suffix pair to round out your daily vocabulary: **купувати / купити** (to buy).

| Форма (Formation) | Недоконаний (Process) | Доконаний (Result) | Переклад (Translation) |
| :--- | :--- | :--- | :--- |
| **Префікс** | читати | **про**читати | to read |
| | писати | **на**писати | to write |
| | робити | **з**робити | to do |
| | бачити | **по**бачити | to see |
| | готувати | **при**готувати | to cook |
| **Суфікс** | відчин**я**ти | відчин**и**ти | to open |
| | куп**ува**ти | куп**и**ти | to buy |
| | виріш**ува**ти | виріш**и**ти | to decide |
| | запит**ува**ти | запит**а**ти | to ask |
| **Корінь** | допом**ага**ти | допом**ог**ти | to help |
| | відповід**а**ти | відповід**іс**ти | to answer |
| **Інші слова** | брати | взяти | to take |
| | говорити | сказати | to speak / to say |
| | ловити | піймати | to catch |
| | шукати | знайти* | to search / to find |

*\*Ці слова пов'язані логічно, але не є граматичною парою (These words are logically linked, but are not a grammatical pair).*

<!-- INJECT_ACTIVITY: match-up-fill-in-the-blanks-with-the-correct-pair -->
<!-- INJECT_ACTIVITY: fill-in-choose-the-correct-aspect-partner -->


## Підсумок (Summary)

We have covered a fundamental concept of the Ukrainian language today: verbal aspect. Remember that learning verbs in pairs is essential. You are not just learning two forms of the same word; you are learning how to describe both the ongoing process and the completed result of an action.

Let's recap the three main methods of forming aspectual pairs that we discussed. The most common method is **префіксація** (prefixation), where we add a prefix to the imperfective verb, such as **робити / зробити** (to do). The second method involves changing the suffix or root vowel, like in the pair **вирішувати / вирішити** (to decide). Finally, we have completely different words, or suppletive pairs, such as **брати / взяти** (to take).

Before you move on to the next module, try these quick self-check questions to test your memory:

1. Can you name the perfective partner for **писати** (to write)? (**написати**)
2. What prefix follows the "K-P-T-F-Kh" rule? (**с-**)
3. Which verb describes the result: **говорити** (to speak) or **сказати** (to say)? (**сказати**)

If you answered these correctly, you are well on your way to mastering Ukrainian verbs!

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
