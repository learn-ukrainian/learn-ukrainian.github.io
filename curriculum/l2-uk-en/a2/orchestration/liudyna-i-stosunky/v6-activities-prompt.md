<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/liudyna-i-stosunky.yaml` file for module **4: Яка вона людина? Описуємо людей навколо нас** (a2).

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
- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match personality adjectives to their definitions or example situations
  items: 8
  type: match-up
- focus: 'Choose the correct adjective to complete a person description (Він завжди
    допомагає — він дуже ___: щирий/ледачий/сумний)'
  items: 8
  type: quiz
- focus: Complete sentences describing people with the correct adjective form (agreement
    for gender)
  items: 8
  type: fill-in
- focus: Sort personality adjectives into positive traits and challenging traits
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- впертий (stubborn, persistent)
- чуйний (responsive, caring)
- наполегливий (persistent, determined)
- родич (relative)
- знайомий (acquaintance)
required:
- людина (person, human being)
- стосунок (relationship)
- характер (character, personality)
- зовнішність (appearance)
- привітний (friendly, welcoming)
- щирий (sincere, genuine)
- працьовитий (hardworking)
- терплячий (patient)
- сусід (neighbor)
- описувати (to describe)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Зовнішність: як виглядає людина? (Appearance: What Does a Person Look Like?)

When we meet someone new, the first thing we notice is their appearance. In Ukrainian, describing a person's appearance — **зовнішність** — relies heavily on descriptive adjectives. Let's look at how two friends discuss people in a photograph.

> **Подруга 1:** Це твоя сестра на фото? Вона висока, темноволоса. *(Is this your sister in the photo? She is tall, dark-haired.)*
> **Подруга 2:** Так, це моя сестра. Вона дуже весела і щира людина. *(Yes, this is my sister. She is a very cheerful and sincere person.)*
> **Подруга 1:** А це хто поруч із нею? *(And who is this next to her?)*
> **Подруга 2:** А це мій сусід. Він завжди мені допомагає. Учора допоміг мені з валізою. *(And this is my neighbor. He always helps me. Yesterday he helped me with a suitcase.)*

When describing appearance, you need pairs of opposite adjectives. Remember that adjectives in Ukrainian change to match the gender (masculine, feminine, neuter) and number of the noun they describe. Here are the core pairs:

*   **високий** (tall) — **низький** (short)
*   **худий** (thin) — **повний** (plump/full)
*   **молодий** (young) — **старий** (old)
*   **темноволосий** (dark-haired) — **світловолосий** (light-haired/blonde)
*   **кароокий** (brown-eyed) — **блакитноокий** (blue-eyed)

Let's see these adjectives in action. Notice how the endings change depending on who is being described.

*   **Цей чоловік дуже високий.** (This man is very tall.)
*   **Моя подруга низька і худа.** (My friend is short and thin.)
*   **Наш дідусь старий, але дуже активний.** (Our grandfather is old, but very active.)
*   **Ця жінка — повна.** (This woman is plump.)
*   **Мій брат — світловолосий хлопець.** (My brother is a blonde guy.)
*   **Ця дівчинка кароока.** (This girl is brown-eyed.)

In Ukrainian, there are two common ways to describe physical features like eyes (**очі**) or hair (**волосся**). We can use the verb **мати** (to have) with the accusative case, or we can use the preposition **з** (with) followed by the instrumental case. You will learn the full rules for the instrumental case in a later module, but here is a preview of how it looks in common descriptions.

Using **мати** (to have):
*   **Вона має карі очі.** (She has brown eyes.)
*   **Він має світле волосся.** (He has light hair.)
*   **Моя мама має блакитні очі.** (My mom has blue eyes.)
*   **Мій тато має темне волосся.** (My dad has dark hair.)
*   **Ця дівчина має зелені очі.** (This girl has green eyes.)

Using **з** (with) + instrumental case:
*   **Вона — дівчина з карими очима.** (She is a girl with brown eyes.)
*   **Він — хлопець зі світлим волоссям.** (He is a guy with light hair.)
*   **Це жінка з блакитними очима.** (This is a woman with blue eyes.)
*   **Я бачу чоловіка з темним волоссям.** (I see a man with dark hair.)
*   **Це дитина із зеленими очима.** (This is a child with green eyes.)

Note how the endings **-ими** or **-им** appear on the adjectives after the preposition **з** (which becomes **зі** or **із** for easier pronunciation before certain sounds). 

### Читаємо українською (Reading Practice)

**На старій фотографії**
Це стара фотографія моєї родини. Ось мій тато. Він молодий, високий і темноволосий. Він має карі очі. Поруч стоїть моя мама. Вона низька, але дуже струнка. Мама світловолоса і блакитноока. А це я. Я ще маленька дівчинка з карими очима. Ми всі дуже щасливі на цьому фото.

<!-- INJECT_ACTIVITY: fill-in -->

## Характер: яка вона людина? (Character: What Kind of Person Is She?)

A person's appearance is only half the picture. In Ukrainian culture, a person's inner world — their **характер** (character, personality) — is considered much more important. Let's observe a workplace conversation where colleagues discuss character.

> **Новий працівник:** Хто ваш керівник? Який він? *(Who is your manager? What is he like?)*
> **Досвідчений колега:** Він дуже відповідальний і терплячий. *(He is very responsible and patient.)*
> **Новий працівник:** А колеги? *(And the colleagues?)*
> **Досвідчений колега:** Усі привітні, особливо Оксана — вона завжди підказує новим працівникам. *(Everyone is friendly, especially Oksana — she always helps new employees.)*

To describe a person's character, we use specific personality adjectives. Here are the most common positive traits you will hear in everyday conversation:

*   **привітний** (friendly, welcoming)
*   **щирий** (sincere, genuine)
*   **чуйний** (responsive, caring)
*   **добрий** (kind, good)
*   **веселий** (cheerful)
*   **розумний** (smart, intelligent)
*   **працьовитий** (hardworking)
*   **терплячий** (patient)
*   **відповідальний** (responsible)
*   **наполегливий** (persistent, determined)

Let's look at how we combine these adjectives in sentences:

*   **Мій брат дуже привітний.** (My brother is very friendly.)
*   **Вона — щира людина.** (She is a sincere person.)
*   **Наш керівник відповідальний і розумний.** (Our manager is responsible and smart.)
*   **Ця жінка дуже працьовита.** (This woman is very hardworking.)
*   **Моя бабуся завжди чуйна.** (My grandmother is always caring.)

Not all traits are entirely positive. There are also challenging traits. However, in Ukrainian culture, some of these can be seen from a different perspective. 

*   **впертий** (stubborn)
*   **сумний** (sad)
*   **ледачий** (lazy)
*   **серйозний** (serious)
*   **тихий** (quiet)

:::note
**Cultural Perspective**
The word **впертий** literally means "stubborn". While often seen as a negative trait (e.g., refusing to listen to reason), Ukrainians also frequently use it as a positive compliment meaning "persistent" or "principled" when someone refuses to give up in the face of difficulty. A person who achieves great success is often described as **впертий**.
:::

Let's look at these challenging traits in context:

*   **Цей хлопець дуже ледачий.** (This guy is very lazy.)
*   **Чому ти сьогодні такий сумний?** (Why are you so sad today?)
*   **Моя сестра дуже вперта.** (My sister is very stubborn.)
*   **Цей студент серйозний і тихий.** (This student is serious and quiet.)
*   **Він впертий, тому завжди перемагає.** (He is stubborn [persistent], that's why he always wins.)

### Expressing Character Through Actions (Aspect Integration)

In Ukrainian, we often describe a person's character not just with adjectives, but by describing what they *do*. This is where verbal aspect becomes crucial. 

When we describe habitual actions — things a person does regularly that prove their character — we use the **imperfective aspect**. 

*   **Він завжди допомагає людям.** (He always helps people. — *Habitual, imperfective*)
*   **Вона часто підказує колегам.** (She often helps colleagues. — *Habitual, imperfective*)
*   **Мій друг завжди працює допізна.** (My friend always works late. — *Habitual, imperfective*)

When we want to give a specific, one-time example that proves a person's character, we use the **perfective aspect**.

*   **Вчора він допоміг мені з проєктом.** (Yesterday he helped me with a project. — *One-time, perfective*)
*   **Вона підказала мені правильну адресу.** (She gave me the right address. — *One-time, perfective*)
*   **Він попрацював у вихідні.** (He worked on the weekend. — *One-time, perfective*)

By combining adjectives and verbs of different aspects, you create a rich, natural portrait of a person.

### Читаємо українською (Reading Practice)

**Моя нова колега**
Це моя нова колега, Олена. Вона дуже розумна і відповідальна жінка. Олена привітна — вона завжди вітається вранці. Вона також дуже працьовита. Олена завжди працює швидко. Учора був складний день, але вона швидко зробила всю роботу. Я думаю, що вона щира і добра людина. 

<!-- INJECT_ACTIVITY: match-up -->
<!-- INJECT_ACTIVITY: group-sort -->

## Люди навколо нас: родичі, друзі, знайомі (People Around Us)

Now that you can describe appearance and character, you need the vocabulary to explain who these people are to you. We are constantly surrounded by different types of relationships — **стосунки**.

Let's see how someone introduces people in a natural conversation:

> **Олег:** А хто це на фотографії? *(And who is this in the photo?)*
> **Марія:** Це мій дядько. Він живе поруч. *(This is my uncle. He lives nearby.)*
> **Олег:** Який він? *(What is he like?)*
> **Марія:** Він мій найкращий друг. Він мене поважає і завжди слухає. *(He is my best friend. He respects me and always listens.)*

Here is the essential vocabulary for relationships:

*   **родич** (relative)
*   **мати / батько** (mother / father)
*   **брат / сестра** (brother / sister)
*   **дідусь / бабуся** (grandfather / grandmother)
*   **дядько / тітка** (uncle / aunt)
*   **друг / подруга** (male friend / female friend)
*   **товариш** (friend / comrade / buddy)
*   **сусід / сусідка** (male neighbor / female neighbor)
*   **колега** (colleague)
*   **знайомий / знайома** (male acquaintance / female acquaintance)

:::tip
**Друг vs Товариш vs Знайомий**
A **друг** is a close, trusted friend. A **товариш** is a casual friend, buddy, or a companion you share activities with. A **знайомий** is simply an acquaintance — someone you know, but are not close to. 
:::

When talking about your relationships, you can use these common sentence patterns:

*   **Це мій близький родич.** (This is my close relative.)
*   **Ми дружимо вже п'ять років.** (We have been friends for five years.)
*   **Вона — моя найкраща подруга.** (She is my best friend.)
*   **Він мій сусід — живе поруч.** (He is my neighbor — he lives nearby.)
*   **Це моя нова знайома.** (This is my new acquaintance.)
*   **Мій дядько і моя тітка живуть там.** (My uncle and my aunt live there.)
*   **Вона моя колега по роботі.** (She is my colleague from work.)

To describe how someone acts toward you in a relationship, you can use verbs that take an object (often in the dative or accusative case).

*   **Вона мені довіряє.** (She trusts me.)
*   **Він мене поважає.** (He respects me.)
*   **Вони нам допомагають.** (They help us.)
*   **Мої батьки мене розуміють.** (My parents understand me.)
*   **Сусіди нам часто телефонують.** (The neighbors often call us.)

If someone asks you **"А хто це?"** (And who is this?), you can respond with their relationship to you. If they ask **"Який він?"** (What is he like?) or **"Яка вона?"** (What is she like?), you can describe their character or actions.

*   **А хто це? Це мій товариш.** (And who is this? This is my buddy.)
*   **Який він? Він дуже веселий і щирий.** (What is he like? He is very cheerful and sincere.)
*   **А хто ця дівчина? Це моя знайома.** (And who is this girl? This is my acquaintance.)
*   **Яка вона? Вона привітна і розумна.** (What is she like? She is friendly and smart.)

### Читаємо українською (Reading Practice)

**Мої сусіди**
Це мій сусід Іван і його дружина Марія. Вони — мої хороші знайомі. Іван дуже працьовитий чоловік. Він часто працює в саду. Марія — дуже чуйна жінка. Вона завжди вітається і запитує про мої справи. Вони нам часто допомагають. Ми поважаємо їх. Вони дуже добрі сусіди.

<!-- INJECT_ACTIVITY: quiz -->

## Описуємо людину цілком (Describing a Person Fully)

You now have all the tools you need to create a complete portrait of a person: who they are to you, what they look like, and what kind of character they possess. 

In Ukrainian, it is natural to combine all these elements into a cohesive description. You start with the relationship, move to the physical appearance, and finish with their inner qualities.

Here is an example of a complete description:

*   **Мій друг Андрій — високий хлопець із карими очима. Він дуже веселий і щирий. Ми познайомилися в університеті.** (My friend Andriy is a tall guy with brown eyes. He is very cheerful and sincere. We met at the university.)
*   **Це моя тітка Олена. Вона низька жінка зі світлим волоссям. Вона надзвичайно терпляча і відповідальна.** (This is my aunt Olena. She is a short woman with light hair. She is extremely patient and responsible.)
*   **Мій новий колега — повний чоловік. Він має блакитні очі. Він дуже розумний і працьовитий.** (My new colleague is a plump man. He has blue eyes. He is very smart and hardworking.)

Notice how these paragraphs flow. They paint a complete picture of the individual. Try to think of two or three people you know and describe them using this exact pattern in your head. 

:::caution
**"Добра людина"**
In English, saying someone is a "good person" can sometimes sound generic or weak. In Ukrainian culture, calling someone **добра людина** is a powerful and highly respected compliment. It implies they are decent, honest, and morally upright. It is often the highest praise you can give someone's character.
:::

### Читаємо українською (Reading Practice)

**Мій найкращий друг**
Мій друг Сергій — дуже цікава людина. Він високий і світловолосий хлопець. Він має блакитні очі. Сергій — мій найкращий друг. Ми дружимо вже десять років. Він надзвичайно відповідальний і щирий. Він завжди мені допомагає. Учора він допоміг мені перекласти текст. Сергій дуже добра людина, і я його поважаю.

## Підсумок — Summary

In this module, you learned how to fully describe the people around you in Ukrainian. You started by learning how to describe physical appearance (**зовнішність**) using descriptive adjective pairs like **високий/низький** and **молодий/старий**, as well as how to describe specific features using **мати** or **з + орудний відмінок**.

You also expanded your vocabulary to describe a person's inner world, their **характер**. You learned positive traits like **щирий** and **працьовитий**, and challenging traits like **впертий** and **ледачий**. Importantly, you saw how to use the imperfective aspect for habitual character traits and the perfective aspect for one-time actions that prove a person's character.

Finally, you learned the vocabulary for relationships (**стосунки**) — from **родичі** to **знайомі** — and how to express how people act toward you. You now have the linguistic tools to confidently answer the questions **"А хто це?"** and **"Який він?"** in any natural conversation.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: liudyna-i-stosunky
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

**Level: A2 (Module 4/60) — ELEMENTARY**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
