<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a2-bridge.yaml` file for module **1: Ласкаво просимо до рівня А2** (a2).

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

- focus: Case Identification Drill
  items: 8
  type: quiz
- focus: Phonological Alternation Pairs
  items: 8
  type: fill-in
- focus: Euphony Choice Exercise
  items: 8
  type: match-up
- focus: Euphony Error Correction
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
- милозвучність (euphony, melodiousness)
- огляд (review, overview)
- система (system)
- правило (rule)
required:
- відмінок (case)
- називний (nominative)
- знахідний (accusative)
- місцевий (locative)
- кличний (vocative)
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- наголос (stress (accent))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пригадуємо відмінки (Reviewing Cases)

> — **Томас:** Добрий день, Олександре Петровичу! *(Good day, Oleksandr Petrovych!)*
> — **Олександр Петрович:** Добрий день! Ви — новий студент? *(Good day! Are you a new student?)*
> — **Томас:** Так, я — студент. Мене звати Томас. Я вивчаю українську мову. *(Yes, I am a student. My name is Thomas. I study the Ukrainian language.)*
> — **Олександр Петрович:** Дуже приємно, Томасе. Де ви живете зараз? *(Very nice to meet you, Thomas. Where do you live now?)*
> — **Томас:** Я живу в готелі у центрі міста. Але я шукаю квартиру. *(I live in a hotel in the city center. But I am looking for an apartment.)*
> — **Олександр Петрович:** Розумію. Ви добре знаєте слова! Ви читаєте книгу чи дивитеся відео? *(I understand. You know words well! Do you read a book or watch videos?)*
> — **Томас:** Я читаю текст і роблю вправи. *(I read text and do exercises.)*
> — **Олександр Петрович:** Чудово! Ласкаво просимо до нашої школи. *(Excellent! Welcome to our school.)*

In the A1 level, you learned that Ukrainian nouns change their endings depending on their role in a sentence. These changes are called cases (**відмінки** *(cases)*). Let's review the four cases you already know. 

The Nominative case (**Називний відмінок** *(Nominative case)*) answers the questions **Хто?** *(Who?)* and **Що?** *(What?)*. It is the dictionary form of a word, used for the subject of a sentence—the "name" of things. To recognize the gender of a noun, we look at its Nominative ending. Masculine nouns usually have no ending and finish in a consonant, such as **дім** *(house)* or **стіл** *(table)*. Feminine nouns typically end in **-а** or **-я**, like **школа** *(school)* or **сім'я** *(family)*. Neuter nouns end in **-о** or **-е**, such as **вікно** *(window)* and **море** *(sea)*. Here are five basic words to recall: **студент** *(student)*, **кава** *(coffee)*, **місто** *(city)*, **робота** *(work)*, **друг** *(friend)*.

The Accusative case (**Знахідний відмінок** *(Accusative case)*) answers the questions **Кого?** *(Whom?)* and **Що?** *(What?)*. We use it for the direct object of a verb—the thing that receives the action. For example, it is used when you read a book or buy a table. Masculine inanimate nouns and neuter nouns do not change; they look exactly like the Nominative case. You can say **купувати стіл** *(to buy a table)* or **бачити вікно** *(to see a window)*. However, feminine nouns undergo a clear change: the ending **-а** becomes **-у**, and **-я** becomes **-ю**. You learned to say **читати книгу** *(to read a book)*, **пити каву** *(to drink coffee)*, and **писати статтю** *(to write an article)*. We also use the Accusative case with verbs of motion to show destination, like **іти в школу** *(to go to school)*.

The Locative case (**Місцевий відмінок** *(Locative case)*) answers the questions **Де?** *(Where?)*, **На кому?** *(On whom?)*, and **На чому?** *(On what?)*. We use it to describe static location, answering where someone or something is situated. This case is unique because it is never used without a preposition; you must always use it with **в/у** *(in)* or **на** *(on/at)*. For most regular nouns across all three genders, the Locative ending is simply **-і**. This makes it one of the easiest cases to form. You already know how to say **у місті** *(in the city)*, **в аптеці** *(in the pharmacy)*, **на роботі** *(at work)*, and **на столі** *(on the table)*. Remember that it contrasts with the Accusative: **я йду на роботу** *(I am going to work)* uses the Accusative for motion, while **я на роботі** *(I am at work)* uses the Locative for position.

The Vocative case (**Кличний відмінок** *(Vocative case)*) is used for addressing someone directly (**звертання** *(addressing)*). In Ukrainian culture, it is highly unnatural to call someone by their Nominative name; the Vocative is essential for polite and natural communication. For masculine names and titles, the endings are typically **-у**, **-ю**, or **-е**. For example, you say **Сергію** *(Serhiy!)*, **друже** *(friend!)*, and **Павле** *(Pavlo!)*. For feminine names, the endings change to **-о** or **-е**, as in **Маріє** *(Mariya!)*, **Оксано** *(Oksana!)*, and **мамо** *(mom!)*. Using this case immediately makes your Ukrainian sound authentic.

Now that we have reviewed your foundation, let's look at the "Great Map" of the Ukrainian case system. There are seven cases in total. You have mastered four, and in the A2 level, we will conquer the remaining three "frontier" cases. The table below shows the complete system.

| Відмінок *(Case)* | Питання *(Questions)* | Функція *(Function)* | Рівень *(Level)* |
| --- | --- | --- | --- |
| Називний *(Nominative)* | Хто? Що? | Subject, dictionary form | A1 |
| Знахідний *(Accusative)* | Кого? Що? | Direct object, destination | A1 |
| Місцевий *(Locative)* | Де? На кому/чому? | Static location | A1 |
| Кличний *(Vocative)* | (Звертання) | Addressing someone | A1 |
| Родовий *(Genitive)* | Кого? Чого? | Possession, absence, quantity | **A2** |
| Давальний *(Dative)* | Кому? Чому? | Indirect object, to/for whom | **A2** |
| Орудний *(Instrumental)* | Ким? Чим? | Instrument, with whom/what | **A2** |

The Genitive case (**Родовий відмінок** *(Genitive case)*) will be your first major milestone in A2. It is incredibly versatile and is used for possession, expressing lack or absence, and counting quantities. Soon, you will be able to navigate the entire map!

<!-- INJECT_ACTIVITY: quiz, Case Identification Drill -->


## Магія української фонології (The Magic of Ukrainian Phonology)

Have you ever tried to find a Ukrainian word in the dictionary, only to discover that the root seems to have mysteriously changed? This is the most common reason learners struggle with word roots, but it is actually a highly predictable historical pattern known as the "Closed Syllable Rule." In Ukrainian, the vowels **о** *(o)* and **е** *(e)* often alternate with the vowel **і** *(i)*. This change happens when a syllable becomes "closed" — meaning it ends in a consonant with no vowel following it. Conversely, when you add an ending that creates an "open" syllable (ending in a vowel), the **і** reverts to **о** or **е**. For example, the Nominative form **стіл** *(table)* has a closed syllable, so it uses **і**. However, when we form the Genitive case, we add an ending: **стола** *(of the table)*. The syllable opens, and the vowel returns to **о**. You will see this everywhere, from the capital city **Київ** *(Kyiv)* becoming **Києва** *(of Kyiv)*, to seasons like **осінь** *(autumn)* becoming **осені** *(of autumn)*. Mastering this single rule unlocks hundreds of new vocabulary connections.

Another beautiful feature that gives Ukrainian its characteristic melody is consonant mutation. The most prominent example is the first palatalization, where the hard consonants **г** *(h)*, **к** *(k)*, and **х** *(kh)* change into the softer, hissing sounds **ж** *(zh)*, **ч** *(ch)*, and **ш** *(sh)*. These changes are deeply historical and naturally evolved to make the language flow more smoothly and sound softer to the ear. You will encounter these mutations constantly when forming diminutives (affectionate or small forms of words) and when dealing with various case endings. For instance, the word **нога** *(leg)* transforms into the diminutive **ніжка** *(little leg)*. The hard **г** becomes a soft **ж**, while the "Closed Syllable Rule" simultaneously changes the **о** to an **і**! Similarly, **рука** *(hand)* becomes **ручка** *(little hand, pen)*, and **вухо** *(ear)* softens into **вушко** *(little ear)*. Recognizing these consonant shifts allows you to instantly understand new derivations without memorizing them as entirely separate vocabulary items.

To truly capture the authentic sound of Ukrainian, you must also understand how certain consonants behave when placed next to each other. First, let's look at the affricates **дж** *(dzh)* and **дз** *(dz)*. Unlike in English, where similar combinations might be pronounced as two distinct sounds, in Ukrainian, these are single, indivisible units of sound. You can hear this clear, unified pronunciation in words like **джерело** *(spring, source)* and **дзвінок** *(bell)*. Contrast this unified sound with the phenomenon of voicing assimilation. In Ukrainian, when a voiceless consonant sits immediately before a voiced consonant, the strong voiced sound forces its voiceless neighbor to become voiced as well. For example, the word **просьба** *(request)* is spelled with a voiceless **с** *(s)*, but because the following **б** *(b)* is voiced, the word is pronounced as [проз'ба]. The same rule applies to the word **вокзал** *(train station)*, which is naturally pronounced as [воґзал]. This assimilation ensures a seamless stream of speech.

Beyond individual letters, the rhythmic heartbeat of Ukrainian is driven by stress, or **наголос** *(stress)*. The critical role of stress cannot be overstated, as it is often the only feature that distinguishes one word from another. A classic example is the word **замок**. If you place the stress on the first syllable, **замок** *(castle)*, you are talking about a medieval fortress. However, if you shift the stress to the second syllable, **замок** *(lock)*, you are talking about a padlock for a door! Furthermore, stress often shifts dynamically when a word changes from singular to plural. The word for water is **вода** *(water)*, with the stress on the final vowel. But when we talk about plural waters, the stress leaps to the first syllable: **води** *(waters)*. While this might seem chaotic at first glance, there are predictable "stress patterns" that you will learn to recognize. These patterns will help you accurately predict pronunciation and give your speech a native-like cadence.

This dynamic shifting of emphasis is most visible in "Mobile Stress" within noun paradigms. As you learn new cases like the Accusative or Genitive, you will notice that the stress sometimes shifts from the stem of the word directly onto the ending, or vice versa, across different grammatical cases. The primary driver behind these dramatic shifts is the desire for rhythmic balance within the sentence. Let's look at some common feminine nouns. The Nominative form **голова** *(head)* has the stress on the final syllable. But when it becomes the direct object in the Accusative case, the stress swings all the way back to the first syllable: **голову** *(head, Accusative)*. You see the exact same rhythmic shift with the word **нога** *(leg)*, which becomes **ногу** *(leg, Accusative)* when used as an object. By embracing this rhythmic flexibility, you move away from a rigid pronunciation and begin to speak with the true musicality of the language.

<!-- INJECT_ACTIVITY: fill-in, Phonological Alternation Pairs -->


## Милозвучність мови: евфонія (The Melody of Language: Euphony)

Have you ever wondered why Ukrainians sometimes say **у** *(in)* and sometimes **в** *(in)* for the exact same preposition? This is a core feature of formal Ukrainian called **милозвучність** *(euphony, melodiousness)*. The goal is simple: speech should flow like a continuous song, without awkward pauses or harsh phonetic clusters. The rule for the **у/в** alternation is driven entirely by the surrounding letters. If the preceding word ends in a consonant and the following word begins with a consonant, we use **у** to create a vocalic bridge: **Він жив у Львові.** *(He lived in Lviv.)* However, if we have vowels involved, we switch to **в** to prevent two vowels from colliding. For example, after a vowel and before a consonant: **Вона була в Києві.** *(She was in Kyiv.)* Or between two vowels: **Вона жила в Одесі.** *(She lived in Odesa.)* Applying this rule is not optional; it is the secret ingredient that gives spoken Ukrainian its signature rhythm.

This exact same melodic principle applies to the word for "and." We alternate between **і** *(and)* and **й** *(and)* using logic that mirrors the **у/в** rule. When connecting two words that end and begin with consonants, we use the vowel **і** to smooth the transition: **брат і сестра** *(brother and sister)*. But if the first word ends in a vowel, we use the consonant **й** to keep the air flowing without a phonetic "hiccup": **батько й мати** *(father and mother)*. When you have a long sentence with multiple items, using the same conjunction repeatedly sounds unnatural. To solve this, Ukrainian offers a third option: **та** *(and)*. You can seamlessly mix **і**, **й**, and **та** to maintain a beautiful cadence throughout your sentence.

The drive for euphony also affects prepositions like **з** *(with, from)*, which transforms into **зі** *(with, from)* or **із** *(with, from)* depending on the phonetic environment. The most important variation to master is **зі**. We use **зі** whenever the following word begins with a heavy cluster of consonants, especially combinations starting with **с**, **з**, **ш**, or **ж**. Saying "з Львова" is a tongue-twister, so the language naturally inserts a vowel to soften the cluster: **Він приїхав зі Львова.** *(He arrived from Lviv.)* Similarly, you will always hear **зі мною** *(with me)* instead of "з мною", or **зі школи** *(from school)* instead of "з школи". Using **із** is common between consonants to add rhythmic balance to a phrase.

<!-- INJECT_ACTIVITY: match-up, Euphony Choice Exercise -->
<!-- INJECT_ACTIVITY: error-correction, Euphony Error Correction -->

While these rules might seem technical on paper, native speakers do not actively think about consonants and vowels while talking. They simply "hear" what sounds correct based on an instinct for rhythm. When a rule is broken, the sentence physically feels awkward to say. As you transition into the A2 level, start reading sentences aloud and paying attention to these connecting words. Mastering euphony is the single most effective way to elevate your speech from sounding like a textbook translation to sounding natural and authentic.


## Що нас чекає на рівні А2? (What Awaits Us in A2?)

The A1 level gave you the survival tools to introduce yourself, describe your immediate surroundings, and order a coffee. Now, the A2 level is about achieving true functional independence in a Ukrainian-speaking environment. You will expand your vocabulary far beyond basic greetings to handle real-world situations with confidence. We will explore thematic pillars that are essential for daily life. You will learn how to navigate a supermarket or a clothing store and interact with cashiers: **Я хочу купити цю сорочку.** *(I want to buy this shirt.)* We will cover health and medical emergencies so you can articulate how you feel: **У мене болить голова.** *(My head hurts.)* You will also master vocabulary for travel, booking train tickets, and discussing your profession or daily work routine.

To support these new topics, we will introduce the structural grammar pillars of the A2 level. Think of these not as strict academic rules, but as power tools for accurate communication. First, you will conquer the Genitive case—the most frequently used case in the Ukrainian language. It is essential for expressing possession, absence, and quantities: **У мене немає часу.** *(I do not have time.)* Next, we will unlock the core concept of Verbal Aspect. You will learn to clearly distinguish between ongoing, unfinished actions and completed results: **Я читав книгу.** *(I was reading a book.)* versus **Я прочитав книгу.** *(I read the book.)* Finally, we will navigate the famous Ukrainian Verbs of Motion, giving you the precision to describe exactly how and where you are traveling: **Я йду в магазин.** *(I am going to the store.)*

Welcome to this exciting bridge phase of your learning journey. This module is designed to connect what you already know with the exciting challenges ahead. Do not worry if everything does not click instantly; building a strong foundation takes time, repetition, and practice. As you progress through the A2 curriculum, you will notice a profound shift in how you process information. Ukrainian will stop being just a memorized list of vocabulary words and isolated grammar tables. Instead, it will start functioning as a living, breathing system in your mind. You will begin to form more complex thoughts, express your actual intentions, and understand native speakers with much greater ease. Take a deep breath, review your foundations, and get ready to truly speak Ukrainian!


## Підсумок (Summary)

In this bridge module, we reviewed the foundational grammar structures from A1 to ensure you are ready for the challenges ahead. We refreshed the four core cases: the Nominative case for subjects, the Accusative case for direct objects, the Locative case for locations, and the Vocative case for addressing people. 

We also explored phonetic rules, such as vowel and consonant shifts, and formalized the rules of euphony—specifically the alternations of **у/в** *(in/at)* and **і/й** *(and)*—which are the secret to achieving the beautiful, flowing melody of the language. 

Test your knowledge with these self-check questions:

* **Який відмінок ми використовуємо для звертання до людини?** *(Which case do we use to address a person?)* — **Кличний.** *(Vocative.)*
* **Чому ми пишемо «Київ», але «у Києві»?** *(Why do we write "Kyiv", but "in Kyiv"?)* — **Чергування «о/і» та «е/і» в закритому чи відкритому складі.** *(Alternation of "o/i" and "e/i" in a closed or open syllable.)*
* **Коли краще вживати «у», а коли «в»?** *(When is it better to use "u" or "v"?)* — **Залежить від голосних та приголосних поруч.** *(It depends on surrounding vowels and consonants.)*
* **Які три нові відмінки ми вивчимо на рівні А2?** *(Which three new cases will we learn in A2?)* — **Родовий, Давальний, Орудний.** *(Genitive, Dative, Instrumental.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a2-bridge
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

**Level: A2 (Module 1/60) — ELEMENTARY**

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
