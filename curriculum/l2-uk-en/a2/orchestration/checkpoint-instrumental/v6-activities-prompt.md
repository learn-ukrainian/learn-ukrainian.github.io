<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-instrumental.yaml` file for module **31: Контрольна точка: Орудний відмінок** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`
- `<!-- INJECT_ACTIVITY: open-ended -->`
- `<!-- INJECT_ACTIVITY: image-description -->`
- `<!-- INJECT_ACTIVITY: writing-prompt -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed Instrumental case quiz covering all functions from M21-M26
  items: 8
  type: quiz
- focus: Sentence transformation — put noun phrases into Instrumental with correct
    agreement
  items: 8
  type: fill-in
- focus: Sort Instrumental sentences by function (tool, companion, profession, spatial,
    temporal)
  items: 8
  type: group-sort
- focus: Find and correct grammar errors in sentences covering module topics
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- правильний (correct)
- словосполучення (phrase, word combination)
- описати (to describe)
- визначити (to identify, to determine)
required:
- орудний відмінок (instrumental case)
- вправа (exercise)
- контрольна точка (checkpoint)
- завдання (task)
- речення (sentence)
- відповідь (answer)
- текст (text)
- перевірка (check, test)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Розпізнавання та форми

Вітаємо! Це **контрольна точка** (checkpoint) нашого курсу. Ми повторюємо **орудний відмінок** (instrumental case). This case is a very important grammatical tool for fluent communication in the Ukrainian language. З його допомогою ми можемо описати, «як» саме ми щось робимо, «чим» ми це робимо, і «з ким» ми взаємодіємо зі світом навколо нас. The instrumental case always answers the main questions: **Ким? Чим?** (By whom? With what?). Сьогодні ми пройдемо повну перевірку ваших знань — від простих закінчень іменників до дуже складних речень. You will see that you already know a lot about this topic.

Спочатку давайте детально згадаємо закінчення іменників чоловічого та середнього роду в однині. If a noun ends in a hard consonant sound, we must add the ending **-ом**: слово **студент** стає **студентом** (by a student), слово **стіл** стає **столом** (with a table), а **брат** стає **братом** (by a brother). If the stem of the word is soft or ends in a sibilant (hushing) sound, we write the ending **-ем**: **ніж** стає **ножем** (with a knife), **вчитель** стає **вчителем** (by a teacher). If a neuter noun has the ending **-я** in the nominative case, we use the lengthened ending **-ям**: **життя** стає **життям** (with life), **знання** стає **знанням** (with knowledge), **море** стає **морем** (with a sea). Pay attention: here we often see the historical alternation of vowels **о/е** after sibilant and soft consonants.

:::tip[Чергування о/е]
If you are unsure whether to use **-ом** or **-ем**, pay attention to how the consonant sounds. If the consonant is soft (like **ль**, **нь**) or sibilant (like **ж**, **ч**, **ш**, **щ**), it almost always takes the soft ending **-ем**!
:::

Тепер повторимо правила для іменників жіночого роду в однині. Traditionally, there are three types of endings here. Для твердої групи ми використовуємо закінчення **-ою**: **мама** стає **мамою** (by mom), **вода** стає **водою** (with water), **подруга** стає **подругою** (with a friend). Для м'якої та мішаної групи після приголосних звуків ми пишемо закінчення **-ею**: **земля** стає **землею** (with earth), **вулиця** стає **вулицею** (by the street), **дача** стає **дачею** (by the summer house). If a feminine word ends in a vowel sound plus **-я**, we always add the ending **-єю**: **надія** стає **надією** (with hope), **Марія** стає **Марією** (with Maria), **мрія** стає **мрією** (with a dream). Comparing hard and soft stems will help you quickly choose the correct ending.

Формування множини в орудному відмінку насправді дуже просте і логічне для всіх трьох родів. Most nouns receive the typical ending **-ами** after hard consonants: **книги** стають **книгами** (with books), **руки** стають **руками** (with hands). After soft and sibilant consonants, we always use the ending **-ями**: **друзі** стають **друзями** (with friends), **олівці** стають **олівцями** (with pencils). Але українська мова має кілька особливих слів, які зберегли старе коротке закінчення **-ми**: **діти** стають **дітьми** (with children), **гроші** стають **грішми** (with money), а **кури** стають **курми** (with chickens). We constantly use these words in our everyday life, so it is worth memorizing them well.

<!-- INJECT_ACTIVITY: group-sort -->

<!-- INJECT_ACTIVITY: fill-in -->

## Частина 2: Вибір та застосування

Дуже важливо розрізняти чистий орудний відмінок, який означає знаряддя або засіб, та конструкцію з прийменником **з**, яка означає супровід або інгредієнт. Compare these two interesting examples: **«Я пишу ручкою»** (I write with a pen — tool) та жартівливе **«Я гуляю з ручкою»** (I walk with a pen — companion). When we use the preposition **з**, we talk about a person's company or a culinary ingredient. Наприклад: ми п'ємо **«кава з цукром»** (coffee with sugar — ingredient). But using the case without a preposition indicates the means or the action itself: **«милуватися цукром»** (to admire the sugar — means or action). Therefore, the **правильна відповідь** (correct answer) always depends on your real-life context and your specific intention.

:::caution[З чи без прийменника?]
A very common mistake is using the preposition **з** for tools. Never say «Я пишу з ручкою» if you mean "I write with a pen". This literally implies you are walking around with a pen as your friend! Always use the bare instrumental case for tools and means.
:::

Просторові прийменники також дуже часто вимагають використання орудного відмінка. These are well-known prepositions such as: **над** (above), **під** (under), **перед** (in front of), **за** (behind), та **між** (between). We use them specifically to describe the static location of objects in space. Ось кілька типових прикладів з життя: **«кіт солодко спить під столом»** (the cat sleeps sweetly under the table), **«яскраве сонце світить над морем»** (the bright sun shines above the sea), **«новий парк знаходиться між будинками»** (the new park is located between the buildings), **«велике дерево росте перед вікном»** (a big tree grows in front of the window). These words perfectly help us to accurately **описати** (describe) the world around us. 

Коли ми використовуємо складне **словосполучення** (phrase), прикметники та займенники також обов'язково змінюють свою форму. The agreement rules for masculine and neuter genders in the singular require using the endings **-им** або **-ім**: **«з моїм старим другом»** (with my old friend), **«під великим синім столом»** (under the big blue table). Для жіночого роду ми завжди маємо закінчення **-ою** або **-ею**: **«з цією гарною дівчиною»** (with this beautiful girl), **«за моєю новою школою»** (behind my new school). In the plural form, absolutely all genders share the identical endings **-ими** або **-іми**: **«з нашими новими сусідами»** (with our new neighbors). This rule makes every single **речення** (sentence) grammatically complete and beautiful.

У нашій мові також є спеціальні дієслова-маркери, які завжди і без винятків вимагають орудного відмінка. These are such important verbs as: **бути** (to be), **стати** (to become), **працювати** (to work as), **захоплюватися** (to be fond of), та **цікавитися** (to be interested in). They are ideal for describing a person's profession or their favorite hobby. Приклади таких трансформацій: якщо вона лікарка, то ми кажемо **«Вона працює лікаркою»** (She works as a doctor) або **«Вона буде лікаркою»** (She will be a doctor). Інші приклади: **«Він швидко став директором»** (He quickly became a director), **«Я сильно захоплююся музикою»** (I am strongly fond of music). This is your main **завдання** (task) and **вправа** (exercise) for understanding other people's stories.

<!-- INJECT_ACTIVITY: quiz -->

<!-- INJECT_ACTIVITY: error-correction -->

## Частина 3: Вільне вживання

> **Олег:** Привіт, Марино! Ми завтра їдемо на чудовий пікнік **автобусом** *(by bus)*. Поїдеш з нами відпочивати?
> **Марина:** Привіт, Олегу! З великою радістю! А ви туди їдете самі чи **з дітьми** *(with children)*?
> **Олег:** Ми поїдемо туди **з дітьми** та **з нашими новими сусідами** *(with our new neighbors)*. Це велика весела компанія.
> **Марина:** Це звучить просто чудово! Де саме ми будемо сидіти і відпочивати?
> **Олег:** Там є дуже гарне місце прямо **за річкою** *(behind the river)*. Ми будемо довго сидіти там **під великим деревом** *(under a big tree)*.
> **Марина:** Які смачні продукти ви берете на природу?
> **Олег:** Ми беремо великі бутерброди **з ковбасою та сиром** *(with sausage and cheese)*. Я впевнений, що цей день буде найкращим!

Давайте зробимо детальний граматичний аналіз цього короткого діалогу. Here we can clearly see how completely different functions of the instrumental case constantly alternate in real live speech. Спочатку Олег використовує засіб транспорту і каже **автобусом** (by bus). Then he describes the people in the large group and uses accompaniment: **з дітьми**, **з нашими новими сусідами**. Далі він говорить про точну просторову локацію їхнього відпочинку: **за річкою**, **під великим деревом**. And finally, he ends the conversation with the culinary ingredients for a simple meal: **з ковбасою та сиром**. У повсякденному реальному житті ми успішно комбінуємо всі ці форми постійно. This allows us to easily create a natural and grammatically coherent story about all our upcoming plans.

Контекст домашніх справ та щоденної роботи на кухні — це просто ідеальне місце для активного тренування. Here we constantly use the instrumental case every single day for the precise description of our actions with various tools. Наприклад, ми швидко прибираємо брудну кімнату **пилососом** (with a vacuum cleaner), ретельно витираємо кухонний стіл вологою **ганчіркою** (with a damp rag), і рівно ріжемо свіжий хліб гострим **ножем** (with a sharp knife). When we describe the process of preparing a delicious dish in detail, we also often say: посипати зелений салат **сіллю** (to sprinkle with salt), залити свіжі овочі пахучою **олією** (to dress with oil). All these simple physical actions are an important part of our everyday life where this case plays a major role.

Тепер детальніше поговоримо про опис нашої унікальної ідентичності та особистих хобі. Using the instrumental case and the right words, you can always very clearly **визначити** (identify) your daily profession and personal interests. Наприклад, у розмові ви можете впевнено сказати: **«Я успішно працюю програмістом»** (I successfully work as a programmer) або **«Моя молодша сестра швидко стала відомою дизайнеркою»** (My younger sister quickly became a famous designer). You can also easily add interesting information about your own hobbies: **«Я глибоко цікавлюся українською культурою та історією»** (I am deeply interested in Ukrainian culture and history). The correct forms of adjective agreement make your own **текст** (text) or spoken narrative very grammatically rich and meaningful.

Нарешті, настала підготовка до вашого фінального письмового завдання. Your main goal here is to independently write a large essay about your usual typical day. Добре подумайте про логічну структуру. How exactly will you logically combine the detailed description of your commute to work (**метро** або **машиною**), a delicious lunch with your best colleagues (**з друзями**), and a quiet evening rest in front of a big TV (**перед екраном**)? Намагайтеся креативно використати якнайбільше різних функцій орудного відмінка у своєму есе. This is your best final **перевірка** (check/test) of all the acquired skills before moving on to the next complex module of the course. Be as attentive as possible, write boldly, and freely use all the knowledge gained from this important topic.

:::note[Ваше есе]
When preparing for the final writing task, don't worry about making the story perfectly true. Focus on demonstrating your grammar! It is perfectly fine to invent a fun or unusual situation just to use more **орудний відмінок** constructions.
:::

<!-- INJECT_ACTIVITY: open-ended -->

<!-- INJECT_ACTIVITY: image-description -->

<!-- INJECT_ACTIVITY: writing-prompt -->

## Підсумок

Давайте проведемо швидку фінальну самоперевірку. Try to independently give the correct answer to these important control questions:

1. Які закінчення мають іменники чоловічого роду в орудному відмінку після м'яких приголосних?
Відповідь: Вони мають закінчення **-ем** (наприклад, **лікар** стає **лікарем**) або **-ям** (якщо слово закінчується на **-й**, наприклад, **край** стає **краєм**).

2. У чому різниця між фразами **«йти з олівцем»** та **«писати олівцем»**?
Відповідь: Перша фраза з прийменником вказує на супровід (companion), а друга — на знаряддя дії (tool).

3. Назвіть п'ять просторових прийменників, які вживаються з орудним відмінком.
Відповідь: Це прийменники простору: **над**, **під**, **перед**, **за**, та **між**.

4. Яке закінчення мають прикметники жіночого роду в орудному відмінку однини?
Відповідь: Вони закінчуються на **-ою** або **-ею** (наприклад, **новою**, **синьою**).

Ви чудово впоралися з цією контрольною точкою! You have successfully reviewed all the grammatical forms and functions of the instrumental case. Тепер ви повністю готові до вивчення нових тем.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-instrumental
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

**Level: A2 (Module 31/60) — ELEMENTARY**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
