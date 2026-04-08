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

- `<!-- INJECT_ACTIVITY: quiz-euphony-variants -->`
- `<!-- INJECT_ACTIVITY: fill-in-z-variants -->`
- `<!-- INJECT_ACTIVITY: match-up-conjunctions -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`

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


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

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
## У чи в? Складні випадки (U or V? Complex Cases)

Українська мова — дуже мелодійна. *(The Ukrainian language is very melodious.)* Це **милозвучність** *(euphony)*, або науковою мовою — **евфонія** *(euphony (technical term))*. We actively avoid a **збіг приголосних** *(consonant cluster)* and a **збіг голосних** *(vowel collision)*. In Ukrainian, a **голосний** *(vowel)* flows smoothly, while a **приголосний** *(consonant)* creates friction. Ukrainian speech adapts to difficult sounds.

:::tip Милозвучність (Euphony)
Ми говоримо так, щоб було легко і красиво. *(We speak so it is easy and beautiful.)*
:::

Basic rule: **у** *(in/at)* and **в** *(in/at)* are the same **прийменник** *(preposition)*. It is important to know when to **вживати** *(to use, to apply)* each form. Use **у** between consonants, and **в** between vowels.

«Читаємо українською» (Reading in Ukrainian):
> — **Олена:** Де зараз Максим? Він у школі? *(Where is Maksym now? Is he at school?)*
> — **Тарас:** Ні, він був у парку. *(No, he was in the park.)*
> — **Олена:** А Анна? Вона була в Одесі? *(And Anna? Was she in Odesa?)*
> — **Тарас:** Так, вона жила в Італії. *(Yes, she lived in Italy.)*
> — **Олена:** А її брат працює в Одесі? *(Her brother works in Odesa?)*
> — **Тарас:** Ні, він працював у Києві. *(No, he worked in Kyiv.)*

Sentence starts and commas reset the phonetic context. Look only at the first sound of the next word.

«Читаємо українською»:
* У лісі багато грибів. *(Many mushrooms in the forest.)*
* В Одесі дуже тепло. *(Very warm in Odesa.)*
* Було холодно, у парку не було людей. *(Cold, no people in the park.)*
* Вона читала, в аудиторії було тихо. *(She read, the auditorium was quiet.)*

The preposition **у** is mandatory before words starting with **в**, **ф**, **хв**, **тв**, **св**, or **льв**. This avoids a stuttering sound.

«Читаємо українською»:
> — **Ігор:** Твій брат завжди був у Львові? *(Was your brother always in Lviv?)*
> — **Марія:** Так, він працює у великій фірмі. *(Yes, he works at a big firm.)*
> — **Ігор:** А Максим був у твоєму дворі. *(But Maksym was in your yard.)*
> — **Марія:** Це не він. Мій брат має успіх у творчості. *(Not him. My brother has success in creativity.)*
> — **Ігор:** Він малює картини чи грає у фільмах? *(Draws pictures or plays in films?)*
> — **Марія:** Він музикант, він був у філармонії. *(He's a musician, he was in the philharmonic.)*

Euphony also changes the first letter of nouns, verbs, and adverbs starting with **у-** or **в-**. 

:::note Чергування (Alternation)
* мій **у**читель *(my teacher)* → наша **в**чителька *(our teacher)*
* він **у**війшов *(he entered)* → вона **в**війшла *(she entered)*
* пив **у**ранці *(drank in the morning)* → читала **в**ранці *(read in the morning)*
:::

«Читаємо українською»:
* Він увійшов до кімнати. *(He entered the room.)*
* Вона ввійшла до кабінету. *(She entered the office.)*
* Це мій новий учитель. *(My new teacher.)*
* Це наша нова вчителька. *(Our new teacher.)*

English speakers often treat **у** and **в** as separate words. Do not say «Я вчуся в школі» — the «в шк» cluster is heavy. Say «Я вчуся у школі».

«Читаємо українською»:
> — **Оксана:** Ти працюєш у школі чи в університеті? *(School or university?)*
> — **Степан:** Я працюю в університеті. А ти? *(University. And you?)*
> — **Оксана:** А я вчуся у школі. Я ще студентка. *(I study at school. I'm a student.)*
> — **Степан:** Ти була у Франції минулого року? *(France last year?)*
> — **Оксана:** Ні, я була в Іспанії. *(No, Spain.)*
> — **Степан:** Це чудово! Іспанія — гарна країна. *(That's great! Spain is a beautiful country.)*

<!-- INJECT_ACTIVITY: quiz-euphony-variants -->


## З, із чи зі? Правила перед збігами приголосних

Українська мова дуже мелодійна. Ми уникаємо складних збігів приголосних. *(The Ukrainian language is very melodious. We avoid difficult consonant clusters.)* The preposition **з** *(from/with)* has three forms. We use them to maintain a smooth rhythm.

:::tip Правило (Rule)
**Форма «з»** *(Default)*:
* перед голосними *(before vowels)*
* перед простими приголосними *(before simple consonants)*

**Форма «із»** *(Vowel bridge)*:
* між групами приголосних *(between consonant clusters)*
* перед шиплячими: з, с, ц, ш, ч, ж *(before sibilants)*

**Форма «зі»** *(Strong buffer)*:
* перед важкими збігами: з, с, ш, щ *(before heavy clusters)*
* слова-винятки: зі мною, зі Львова *(exceptions: with me, from Lviv)*
:::

«Читаємо українською»:
* Він швидко вийшов **з кімнати**. *(He quickly walked from the room.)*
* Це нова студентка **із Франції**. *(This is a new student from France.)*
* Вона забрала речі **зі столу**. *(She took things from the table.)*

The default form is **з**, used when there is no phonetic friction.

«Читаємо українською»:
> — **Оксана:** Ваш брат повернувся **з Америки**? *(Did your brother return from America?)*
> — **Степан:** Так, він приїхав **з Європи**. *(Yes, he arrived from Europe.)*
> — **Оксана:** Ти сьогодні гуляєш **з Оленою**? *(Are you walking with Olena today?)*
> — **Степан:** Ні, я зараз гуляю **з мамою**. *(No, I'm walking with mom now.)*

The form **із** connects two consonants, or appears before hissing sounds.

«Читаємо українською»:
> — **Ігор:** Це старий лист **із Бразилії**? *(Is this an old letter from Brazil?)*
> — **Марія:** Ні, це лист **із Житомира**. *(No, this is a letter from Zhytomyr.)*
> — **Ігор:** Ти підеш у кіно **із сестрою**? *(Will you go to the cinema with sister?)*
> — **Марія:** Так, я працюю **із задоволенням**. *(Yes, I work with pleasure.)*

The form **зі** softens heavy consonant combinations (**з**, **с**, **ш**, **щ**) and fixed phrases. Never say «з школи».

«Читаємо українською»:
> — **Тарас:** Ви приїхали **зі Львова**? *(Did you arrive from Lviv?)*
> — **Олена:** Так, ми їхали **зі своїми** друзями. *(Yes, we traveled with our friends.)*
> — **Тарас:** Ти зараз ідеш **зі школи**? *(Are you walking from school now?)*
> — **Олена:** Ні, я йду **зі старого** парку. *(No, I'm walking from the old park.)*
> — **Тарас:** Поїдеш завтра **зі мною**? *(Will you go with me tomorrow?)*
> — **Олена:** Звісно, поїдемо **зі студентами**. *(Of course, we will go with the students.)*

In the Genitive case, the preposition and noun form a single melodic unit. Pronounce them together.

<!-- INJECT_ACTIVITY: fill-in-z-variants -->


## І чи й? У складних реченнях

Українська мова має два варіанти сполучника «and». *(The Ukrainian language has two variants of the conjunction "and".)* The conjunctions **і** and **й** mean exactly the same thing. We choose between them based on the surrounding sounds. The letter **й** is a glide, a semi-vowel. It needs a full vowel right before it to "anchor" it smoothly. We use **й** between vowels, and after a vowel before a consonant. 

«Читаємо українською»:
* **Ольга й Андрій** ідуть у кіно. *(Olha and Andrii are going to the cinema.)*
* Надворі **тепло й затишно**. *(It is warm and cozy outside.)*

The letter **і** is a full vowel. We use it to break up hard consonant clusters. We use **і** between consonants, and after a consonant before a vowel.

«Читаємо українською»:
* Її **син і мати** живуть тут. *(Her son and mother live here.)*
* Її **брат іде** додому. *(Her brother is going home.)*

When we build complex sentences, punctuation marks change the rules. A comma acts as a phonetic "fence" or boundary. Even if the word before the comma ends in a vowel, the pause breaks the glide. After a comma, we start a new phonetic context. Because of this pause, the full vowel **і** is usually preferred to introduce the new clause.

«Читаємо українською»:
> — **Тарас:** Де всі студенти? *(Where are all the students?)*
> — **Олена:** **Вона співала, і всі слухали.** *(She sang, and everyone listened.)*
> — **Тарас:** А потім? *(And then?)*
> — **Олена:** **Ми закінчили, і концерт завершився.** *(We finished, and the concert ended.)*

Notice we say «...співала, і всі...», not «й всі». The comma always resets the rhythm.

There is one absolute rule for phonetic hygiene: the "forbidden collision." The glide **й** is never used before words starting with the sounds **й**, **я**, **ю**, **є**, **ї**. These letters already contain a hidden "y" sound. Adding **й** before them would create an ugly "double-y" stutter. We always use **і** before these letters, regardless of the previous word.

«Читаємо українською»:
* Це **Олена і її** брат. *(This is Olena and her brother.)*
* Це **Одеса і Ялта**. *(This is Odesa and Yalta.)*
* Тут є **кава і яблука**. *(There is coffee and apples here.)*

Sometimes you might feel unsure about the phonetic rules, or you want to avoid a repetitive "i-i-i" sound in a sentence. Ukrainian has a safe, stylish alternative: the conjunction **та** *(and)*. Unlike **і/й**, **та** does not alternate. It is a stable word that works perfectly in any phonetic environment.

«Читаємо українською»:
> — **Ігор:** Хто там стоїть? *(Who is standing there?)*
> — **Марія:** Там стоять **мама та тато**. *(Mom and dad are standing there.)*
> — **Ігор:** Що вони купили? *(What did they buy?)*
> — **Марія:** Вони купили **хліб та молоко**. *(They bought bread and milk.)*

Let's practice this with compound objects in the Genitive case. This case often groups words together, so euphony is very noticeable. Pay attention to the endings and the conjunctions between them.

«Читаємо українською»:
* У нас **немає сиру й молока**. *(We have no cheese and milk.)*
* У нас **немає яблук і бананів**. *(We have no apples and bananas.)*

<!-- INJECT_ACTIVITY: match-up-conjunctions -->


## Все разом: мелодійні речення

> — **Тарас:** Оленко, поїдемо **у Львів із друзями** на вихідні? *(Olenka, shall we go to Lviv with friends for the weekend?)*
> — **Оленка:** **У Львів**? *(To Lviv?)* **Із задоволенням**! *(With pleasure!)* Але я поїду туди **з Оленою й Андрієм**. *(But I will go there with Olena and Andrii.)* Вони вже купили квитки. *(They have already bought tickets.)*
> — **Тарас:** Чудова ідея. *(Great idea.)* А коли ви повернетеся **зі Львова**? *(And when will you return from Lviv?)*
> — **Оленка:** Ми повернемося **в понеділок** уранці. *(We will return on Monday morning.)* А ти поїдеш **зі мною**? *(And will you go with me?)*
> — **Тарас:** Ні, я залишуся **в Києві**. *(No, I will stay in Kyiv.)* Буду читати книжку **й відпочивати**. *(I will read a book and rest.)*
> — **Оленка:** Добре, зустрінемося **в університеті й усе** обговоримо. *(Good, we will meet at the university and discuss everything.)*
> — **Тарас:** Так, мій брат **і я** чекатимемо на тебе. *(Yes, my brother and I will wait for you.)*

Have you ever noticed how smoothly Ukrainian flows? This is not an accident. Read the dialogue above aloud. Now, try saying «в Львові» or «з мною». You will immediately feel your tongue stop or trip over the **збіг** *(cluster)* of consonants. Ukrainian is often described as a language designed to be sung, not just spoken. If you have to pause awkwardly or push forcefully through a phrase, you have likely violated a rule of **милозвучність** *(euphony)*. Your ears and your mouth are your best teachers here. When a sentence is phonetically correct, it glides without effort.

«Читаємо українською»:
* Ця українська пісня дуже **мелодійна й гарна**. *(This Ukrainian song is very melodious and beautiful.)*
* Ми любимо співати **в Україні**. *(We love to sing in Ukraine.)*
* Він завжди говорить **із задоволенням**. *(He always speaks with pleasure.)*

Think of these rules as the "phonetic ecology" of Ukrainian. The language actively self-regulates to maintain its rhythm and its reputation as one of the most melodic in the world. It actively avoids harsh collisions of consonants and awkward vowel gaps at word boundaries. Mastering these small alternations—choosing between **у** and **в**, **з**, **із**, and **зі**, or **і** and **й**—is the real secret to fluency. It is the key to sounding like a natural, living speaker, rather than a robot reading from a dictionary.

«Читаємо українською»:
* Моя сестра живе **у Львові, і я** часто їжджу туди. *(My sister lives in Lviv, and I often travel there.)*
* Вони вийшли **зі школи й пішли в парк**. *(They left the school and went to the park.)*
* Це складне **правило**, але воно дуже важливе. *(This is a complex rule, but it is very important.)*

<!-- INJECT_ACTIVITY: error-correction -->


## Підсумок — Summary

Let's review the core rules of **милозвучність** *(euphony)* with a quick Q&A:

*   **Q:** When do I use **у** *(in/at)* before a word starting with a vowel?
    **A:** Never. You must always use **в** *(in/at)* between two vowels, or after a consonant before a vowel. «Вона живе **в О**десі.» *(She lives in Odesa.)* «Він був **в а**удиторії.» *(He was in the classroom.)*
*   **Q:** Why can't I say **з мною** *(with me)*?
    **A:** The consonant cluster **з-мн** is simply too heavy to pronounce smoothly. The variant **зі** *(with)* provides the necessary vowel bridge. «Ти підеш **зі мн**ою?» *(Will you go with me?)*
*   **Q:** Is **й** *(and)* okay at the start of a sentence?
    **A:** It is only acceptable if the previous sentence ended in a vowel and you speak without a pause. However, **і** *(and)* is always the standard, safer choice for sentence starts. «**І** ми пішли додому.» *(And we went home.)*
*   **Q:** What is the "Forbidden Five" for **в**?
    **A:** Words starting with **в**, **ф**, **хв**, **св**, and **льв**. You must always use **у** before them to avoid a phonetic collision! «Мій брат **у Льв**ові.» *(My brother is in Lviv.)* «Ми стояли **у ф**оє.» *(We stood in the foyer.)*

«Пам'ятайте: українська мова дуже мелодійна.» *(Remember: the Ukrainian language is very melodious.)* «Слухайте уважно, і ви говоритимете правильно.» *(Listen carefully, and you will speak correctly.)*

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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

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
