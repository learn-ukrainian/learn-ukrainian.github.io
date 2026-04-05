<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/locative-expanded.yaml` file for module **20: Місцевий відмінок у нових контекстах** (a2).

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

- focus: Identify the function of locative in each sentence (physical location, abstract
    domain, temporal, or means)
  items: 8
  type: quiz
- focus: Complete sentences with the correct locative form of the noun (у минулому
    ___, на цьому ___, по ___)
  items: 8
  type: fill-in
- focus: Match locative expressions with their English equivalents across all four
    function types
  items: 8
  type: match-up
- focus: Fix preposition errors (e.g., *у роботі → на роботі, *у телефону → по телефону,
    *на минулому місяці → у минулому місяці)
  items: 8
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дитинство (childhood)
- молодість (youth)
- майбутнє (future)
- освіта (education)
- мистецтво (art)
required:
- місцевий (locative (case))
- абстрактний (abstract)
- минулий (past, previous)
- місяць (month)
- тиждень (week)
- телефон (phone, telephone)
- подорож (journey, trip)
- зустріч (meeting, encounter)
- думка (thought, opinion)
- проблема (problem)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Місцевий з абстрактними іменниками (Locative with Abstract Nouns)

«Читаємо українською»
— **Студент:** Де ти зараз? *(Where are you now?)*
— **Викладач:** Я у школі. *(I am at school.)*
— **Студент:** А де ти працюєш? *(And where do you work?)*
— **Викладач:** Я працюю в освіті. *(I work in education.)*
— **Студент:** Це дуже цікаво! Моя думка така: освіта — це майбутнє. *(This is very interesting! My opinion is this: education is the future.)*
— **Викладач:** Так, робота в освіті — це важливо. *(Yes, work in education is important.)*

You already know how to use the **місцевий відмінок** (locative case) to describe physical locations like «у кімнаті» (in the room) or «у місті» (in the city). In Ukrainian, the concept of "location" extends to abstract domains, fields of activity, and situations. When you are involved in a specific field, you are conceptually "located" inside it. An abstract noun (**абстрактний** іменник) uses the same locative endings as a physical place.

For feminine abstract nouns ending in **-а** or **-я**, the ending changes to **-і**. The preposition **у** or **в** (in) indicates immersion in this domain. 
*   **освіта** (education) → **в освіті** (in education)
*   **культура** (culture) → **у культурі** (in culture)
*   **політика** (politics) → **у політиці** (in politics)
*   **релігія** (religion) → **у релігії** (in religion)
*   **наука** (science) → **у науці** (in science)

«Читаємо українською»
Мій брат працює у політиці. *(My brother works in politics.)*
Він каже, що у політиці багато проблем. *(He says that there are many problems in politics.)*
Моя сестра працює у культурі. *(My sister works in culture.)*
Я дуже люблю працювати в освіті. *(I really love working in education.)*

Masculine and neuter abstract nouns typically take the **-і** ending (or sometimes **-я** depending on the stem). These words express immersion in an aspect of life rather than a physical spot. 

*   **бізнес** (business) → **у бізнесі** (in business)
*   **мистецтво** (art) → **у мистецтві** (in art)
*   **право** (law) → **у праві** (in law)
*   **життя** (life) → **у житті** (in life)
*   **спорт** (sport) → **у спорті** (in sport)

«Читаємо українською»
У житті бувають різні ситуації. *(There are different situations in life.)*
Мій друг працює у великому бізнесі. *(My friend works in big business.)*
Мистецтво дуже важливе для мене, я шукаю нові ідеї у мистецтві. *(Art is very important for me, I look for new ideas in art.)*

While you almost always use the preposition **у/в** to indicate being "inside" a field, the word **робота** (work) is a critical exception. When talking about work as an activity or status, you must use the preposition **на** (on/at). You say **на роботі** (at work), and never «у роботі». You sit **в офісі** (in the office — physical location), you work **у бізнесі** (in business — industry domain), but you are currently **на роботі** (at work — engaged in the activity). 

«Читаємо українською»
— **Марія:** Привіт, Ігоре! Ти де? *(Hi, Ihor! Where are you?)*
— **Ігор:** Привіт! Я зараз на роботі. *(Hi! I am at work now.)*
— **Марія:** Ти працюєш в офісі? *(Do you work in an office?)*
— **Ігор:** Так, я працюю в офісі. *(Yes, I work in an office.)*

<!-- INJECT_ACTIVITY: quiz, Identify the function of locative in each sentence (physical location, abstract domain, temporal, or means) -->

## Часовий місцевий відмінок (Temporal Locative)

«Читаємо українською»
Мій день народження у січні. *(My birthday is in January.)*
Ми завжди відпочиваємо у серпні. *(We always rest in August.)*
Що ви робите у травні? *(What are you doing in May?)*
У минулому місяці мій брат купив машину. *(In the previous month my brother bought a car.)*

Ukrainian calendar months function as temporal containers. To say something happens "in" a certain month, use the preposition **у** or **в** followed by the locative case. Most months are masculine nouns ending in the suffix **-ень**. When forming the locative for these months, the vowel **-е-** drops out, and the ending becomes **-ні**. The word **місяць** (month) also takes a standard locative ending.

* **січень** (January) → **у січні** (in January)
* **березень** (March) → **у березні** (in March)
* **травень** (May) → **у травні** (in May)
* **місяць** (month) → **у місяці** (in a month)

While months use the preposition **у/в**, the word **тиждень** (week) requires the preposition **на** (on/at). The vowel **-е-** also drops out, giving us the form **тижні**. You must memorize the essential temporal triad for talking about weeks using the words **минулий** (past, previous), **цей** (this), and **наступний** (next).

* **на цьому тижні** (this week)
* **на минулому тижні** (last week)
* **на наступному тижні** (next week)

«Читаємо українською»
Що ти робиш на цьому тижні? *(What are you doing this week?)*
На цьому тижні у мене багато роботи. *(This week I have a lot of work.)*
На минулому тижні ми були в театрі. *(Last week we were at the theater.)*
На наступному тижні вона їде до Києва. *(Next week she is going to Kyiv.)*

The locative case also describes broad periods of life or time as backgrounds for events, placing an event "inside" an era. 

* **дитинство** (childhood) → **у дитинстві** (in childhood)
* **молодість** (youth) → **у молодості** (in youth)
* **старість** (old age) → **у старості** (in old age)
* **минуле** (the past) → **у минулому** (in the past)
* **майбутнє** (the future) → **у майбутньому** (in the future)

«Читаємо українською»
У дитинстві я любив грати у футбол. *(In childhood I loved playing football.)*
Моя бабуся багато читала у молодості. *(My grandmother read a lot in youth.)*
У минулому це місто було маленьким. *(In the past this city was small.)*
У майбутньому я хочу працювати в освіті. *(In the future I want to work in education.)*

The locative case answers the question **Коли?** (When? — for months or weeks). To answer the question **Як довго?** (How long?), you must use the accusative case to show the duration of an action.

«Читаємо українською»
Я був там у червні. *(I was there in June.)* — Коли? (Locative)
Я був там увесь червень. *(I was there all June.)* — Як довго? (Accusative)
Вона відпочивала на минулому тижні. *(She rested last week.)* — Коли? (Locative)
Вона відпочивала цілий тиждень. *(She rested the whole week.)* — Як довго? (Accusative)

<!-- INJECT_ACTIVITY: fill-in, Complete sentences with the correct locative form of the noun (у минулому ___, на цьому ___, по ___), 8 items -->

## По телефону, по радіо: місцевий із прийменником «по» (Locative with "po")

«Читаємо українською»
Вони часто розмовляють по телефону. *(They often talk on the phone.)*
Мої батьки рідко дивляться новини по телевізору. *(My parents rarely watch the news on TV.)*
Ми почули дуже гарну пісню по радіо. *(We heard a very beautiful song on the radio.)*
Вона надіслала важливі документи по пошті. *(She sent important documents by mail.)*

When you want to express the means or channel of communication, use the preposition **по** (by, on) followed by the locative case. Masculine nouns in this specific context often take the **-у** ending in the locative case instead of the usual **-і**. 

* **телефон** (phone) → **по телефону** (by phone)
* **телевізор** (TV) → **по телевізору** (on TV)
* **радіо** (radio) → **по радіо** (on the radio)
* **пошта** (mail) → **по пошті** (by mail)

When you talk *about* something, use the preposition **про** (about) with the accusative case to mark the subject matter. When you talk *via* a specific communication channel, use **по** with the locative case. 

«Читаємо українською»
Я довго розмовляв про нову роботу по телефону. *(I talked about the new job on the phone for a long time.)*
Журналісти говорили про економіку по телевізору. *(Journalists talked about the economy on TV.)*

The preposition **по** with the locative case is also used in spatial expressions to describe movement *along* a path or being *within the process* of a journey or trip (**подорож**). A common phrase is **по дорозі** (on the way). This means the action happens while the journey is actively in progress, which is conceptually different from standing physically on the asphalt surface (**на дорозі**). 

«Читаємо українською»
Я купив свіжий хліб по дорозі додому. *(I bought fresh bread on the way home.)*
Обережно, велика машина стоїть прямо на дорозі. *(Careful, a big car is standing right on the road.)*
У нас була довга подорож. *(We had a long journey.)*
У подорожі ми багато говорили. *(On the journey we talked a lot.)*

You will also frequently use the locative case when talking about a meeting (**зустріч**). It acts as a temporal and spatial event container.

* **зустріч** (meeting) → **на зустрічі** (at the meeting)

«Читаємо українською»
Ми говорили про це на зустрічі. *(We talked about this at the meeting.)*
На зустрічі було багато людей. *(There were many people at the meeting.)*

<!-- INJECT_ACTIVITY: match-up, Match locative expressions with their English equivalents across all four function types, 8 items -->

## Місцевий відмінок: від місця до сенсу (From Place to Meaning)

«Читаємо українською»
> — **Олена:** Де ти працюєш зараз? *(Where do you work now?)*
> — **Максим:** Я працюю в освіті, а мій брат — у політиці. *(I work in education, and my brother — in politics.)*
> — **Олена:** Коли ти був у Львові? *(When were you in Lviv?)*
> — **Максим:** Ми відпочивали там у минулому місяці. Це була чудова подорож. *(We vacationed there last month. It was a wonderful journey.)*
> — **Олена:** На цьому тижні я дуже зайнятий на роботі. У мене важлива зустріч. *(This week I am very busy at work. I have an important meeting.)*
> — **Максим:** Як ти дізнався про це свято? *(How did you find out about this holiday?)*
> — **Олена:** Я почув ці цікаві новини по радіо. *(I heard these interesting news on the radio.)*
> — **Максим:** Тоді ми поговоримо про це по телефону ввечері. Моя думка — треба йти. *(Then we will talk about this on the phone in the evening. My opinion is — we should go.)*

The locative case sets the complete scene for your sentences. It answers three distinct questions:
1. **Де?** (Where?) covers physical locations, abstract spheres like life, work, or education, and events like a meeting (на зустрічі). 
2. **Коли?** (When?) specifies time periods such as specific months, weeks (на минулому тижні), and broad stages of life. 
3. **Як?** (How? / By what means?) explains the channel of your communication, like talking on the phone (по телефону). 

<!-- INJECT_ACTIVITY: error-correction, Fix preposition errors (e.g., *у роботі → на роботі, *у телефону → по телефону, *на минулому місяці → у минулому місяці), 8 items -->

### Підсумок (Summary)

> **Питання:** Який прийменник ми вживаємо для місяців? *(What preposition do we use for months?)*
> **Відповідь:** Прийменник **у** або **в** разом із місцевим відмінком. Наприклад: **у січні** *(in January)*, **у серпні** *(in August)*. *(The preposition "у" or "в" together with the locative case. For example: in January, in August.)*

> **Питання:** Як сказати "this week" українською? *(How to say "this week" in Ukrainian?)*
> **Відповідь:** **На цьому тижні**. Ми завжди використовуємо прийменник **на** для тижнів, а не "у" чи "в". *(On this week. We always use the preposition "на" for weeks, and not "у" or "в".)*

> **Питання:** Як ми позначаємо засіб зв'язку, наприклад, телефон або радіо? *(How do we indicate a means of communication, for example, a phone or radio?)*
> **Відповідь:** За допомогою прийменника **по** та місцевого відмінка. Ми кажемо **по телефону** *(on the phone)* або **по радіо** *(on the radio)*. *(With the help of the preposition "по" and the locative case. We say on the phone or on the radio.)*

> **Питання:** Яке закінчення мають абстрактні іменники жіночого роду, такі як "освіта" чи "політика"? *(What ending do abstract feminine nouns have, such as "education" or "politics"?)*
> **Відповідь:** Вони мають закінчення **-і** у місцевому відмінку. Наприклад: **в освіті** *(in education)*, **у політиці** *(in politics)*. *(They have the ending -і in the locative case. For example: in education, in politics.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: locative-expanded
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

**Level: A2 (Module 20/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
