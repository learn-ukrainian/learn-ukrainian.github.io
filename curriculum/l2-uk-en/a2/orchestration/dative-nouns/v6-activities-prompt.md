<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-nouns.yaml` file for module **18: Студентові, сестрі, дитині** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-dative-masculine -->`
- `<!-- INJECT_ACTIVITY: quiz-feminine-alternation -->`
- `<!-- INJECT_ACTIVITY: group-sort-dative-gender -->`
- `<!-- INJECT_ACTIVITY: match-up-verb-phrases -->`
- `<!-- INJECT_ACTIVITY: unjumble-dative-syntax -->`

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
## Давальний відмінок іменників чоловічого роду (~700 words total)

Welcome to the Dative case, or the **давальний відмінок** in Ukrainian. The name of this case comes from the verb meaning "to give". It answers the questions **кому?** (to whom?) and **чому?** (to what?). The primary function of the Dative case is to designate the recipient of an action. When you give something, show something, or explain something, the person receiving that action takes the Dative case. If you give a gift to a student, the student is the recipient and takes a specific ending. If you give it to a sister, she takes a different ending. In this section, we will focus entirely on masculine nouns.

Я даю подарунок студентові.
Він дарує квіти сестрі.
Вчитель пояснює правило учневі.
Ми можемо розповісти історію братові.

> *I give a gift to the student.*
> *He gives flowers to the sister.*
> *The teacher explains the rule to the pupil.*
> *We can tell the story to the brother.*

Let us focus on masculine nouns, which belong to the second declension. Ukrainian masculine nouns have a very special feature in the Dative case. They can take parallel endings. You have a choice between the long **-ові / -еві / -єві** group and the short **-у / -ю** group. Both options are grammatically correct and completely interchangeable in everyday speech. You can say either "братові" or "брату" (to the brother), and "лікареві" or "лікарю" (to the doctor). However, the long endings are a rich, distinctive stylistic feature of the Ukrainian language. Native speakers strongly prefer them, especially when talking about living beings like people or animals. 

Моєму братові потрібен цей телефон.
Я хочу подарувати книгу лікареві.
Дідусеві дуже подобається ця пісня.
Студентові треба написати текст.

> *My brother needs this phone.*
> *I want to give a book to the doctor.*
> *The grandfather really likes this song.*
> *The student needs to write a text.*

How do we choose between the different endings in the first group? The choice depends on the final consonant of the noun stem. If the noun ends in a hard consonant, we use the **-ові** ending. For instance, the word for friend becomes **другові**, and the word for son becomes **синові**. If the noun ends in a soft consonant or a hissing sound, we use the **-еві** ending. The word for teacher becomes **вчителеві**, and the word for comrade becomes **товаришеві**. Finally, if the noun stem ends in a vowel, we use the **-єві** ending. The name Andriy becomes **Андрієві**.

:::info
**Grammar box**
Always look at the last letter of the dictionary form. Hard consonants get **-ові**, soft and hissing consonants get **-еві**, and vowels get **-єві**.
:::

Максим пише повідомлення другові.
Вона хоче відповісти вчителеві.
Ми маємо допомогти Андрієві.
Журналіст ставить питання читачеві.

> *Maksym is writing a message to a friend.*
> *She wants to answer the teacher.*
> *We have to help Andriy.*
> *The journalist asks the reader a question.*

Now let us look at the second group of endings. These are the shorter endings, and they also depend on the stem. Masculine nouns with hard stems and hissing stems take the **-у** ending. The word for student can be **студенту**, and the word for comrade can be **товаришу**. Masculine nouns with soft stems take the **-ю** ending, so the word for doctor becomes **лікарю**. While these shorter endings are perfectly valid and you will hear them often, we strongly encourage you to actively practice the longer endings. Mastering them is a key step in speaking beautiful, authentic Ukrainian.

Я даю зошит студенту.
Син допомагає лікарю.
Ми телефонуємо товаришу.
Жінка хоче відповісти чоловіку.

> *I am giving the notebook to the student.*
> *The son helps the doctor.*
> *We are calling a comrade.*
> *The woman wants to answer the man.*

There is an elegant stylistic rule for the Dative case when you have multiple masculine nouns in a row. Imagine you want to say "to neighbor Danylo". Both words are masculine nouns. To avoid phonological monotony and repetitive sounds, Ukrainian speakers alternate the endings. Instead of using two long endings in a row, which sounds heavy, you combine them. You use the long ending for the first word and the short ending for the second word.

Я хочу подякувати сусідові Данилу.
Студент має написати листа видавцеві Сергію.
Ми несемо подарунок панові директору.
Треба показати дорогу братові Максиму.

> *I want to thank neighbor Danylo.*
> *The student has to write a letter to publisher Serhiy.*
> *We are carrying a gift to Mr. Director.*
> *We need to show the way to brother Maksym.*

You will also encounter some common masculine nouns that end in **-о**, such as the words for father, dad, or the names Dmytro and Petro. Even though they look slightly different in their dictionary form, they reliably take the **-ові** ending in the Dative case. This aligns perfectly with the pattern for masculine words denoting people. It is a very straightforward and consistent rule.

Син передає ключі татові.
Дочка робить чай батькові.
Ми хочемо розповісти правду Дмитрові.
Я купую квиток Петрові.

> *The son passes the keys to the dad.*
> *The daughter makes tea for the father.*
> *We want to tell the truth to Dmytro.*
> *I am buying a ticket for Petro.*

Let us solidify these concepts with a few more examples. Notice how the Dative case clearly marks the person who receives the action, the object, or the information. Every single **закінчення** (ending) helps to paint a clear picture of who is interacting with whom.

Я щодня допомагаю братові.
Він пише довгого листа другові.
Ми щиро дякуємо вчителеві.
Вони хочуть подарувати квіти акторові.
Вона має пояснити завдання студенту.

> *I help my brother every day.*
> *He writes a long letter to a friend.*
> *We sincerely thank the teacher.*
> *They want to give flowers to the actor.*
> *She has to explain the task to the student.*

<!-- INJECT_ACTIVITY: fill-in-dative-masculine -->

## Давальний відмінок іменників жіночого роду (~550 words total)

Most feminine nouns ending in **-а** or **-я** belong to the first declension. Forming the Dative case for these words is incredibly straightforward because both hard and soft stems take the exact same **закінчення** (ending). You simply drop the final vowel and add **-і**. For example, the word for mom becomes **мамі**, the word for sister becomes **сестрі**, the word for earth becomes **землі**, and the word for song becomes **пісні**. If a word ends in **-ія**, like the words for station (**станція**) or hope (**надія**), it takes the ending **-ії**, becoming **станції** and **надії**. This consistency makes it very easy to express that you are directing an action toward someone or something.

Моя мама працює в школі. Я хочу подякувати мамі. У мене є старша сестра. Ми часто допомагаємо сестрі. Ця українська пісня дуже відома. Треба дати назву цій пісні. Моя подруга Надія дуже добра. Я часто телефоную Надії.

> *My mom works at a school. I want to thank mom. I have an older sister. We often help the sister. This Ukrainian song is very famous. We need to give a name to this song. My friend Nadiya is very kind. I often call Nadiya.*

There is one crucial phonetic rule you must remember when forming the Dative case for feminine nouns. In Ukrainian, the consonants **г**, **к**, and **х** cannot stand directly before the vowel **-і**. When you add the **-і** ending to a stem that ends in one of these letters, the consonants undergo a mandatory, predictable shift. The consonant **г** changes to **з**, the consonant **к** changes to **ц**, and the consonant **х** changes to **с**. This is not a random exception or an annoying irregularity. It is a fundamental, natural phonological law of the Ukrainian language that makes the words flow much more smoothly and beautifully.

:::info
**Consonant alternation rule** — Before the vowel **-і**, the sounds **г**, **к**, and **х** always change to **з**, **ц**, and **с**.
:::

Let us look at how this sound change happens in practice. When you have a word like **подруга** (friend), the stem ends in **г**. To say "to the friend", that sound must soften into **з**, creating the word **подрузі**. The same logic applies to words ending in **к**, like **рука** (hand) becoming **руці**, and **доріжка** (path) becoming **доріжці**. Words ending in **х**, such as **муха** (fly) and **свекруха** (mother-in-law), shift to **с**, becoming **мусі** and **свекрусі**.

Моя найкраща подруга живе в Києві. Я хочу написати довгого листа подрузі. Ця нова доріжка веде до лісу. Я віддаю перевагу цій доріжці. Її свекруха живе дуже близько. Вона хоче розповісти всю правду свекрусі. Моя права рука зараз болить. Треба дати відпочинок цій руці.

> *My best friend lives in Kyiv. I want to write a long letter to the friend. This new path leads to the forest. I prefer this path. Her mother-in-law lives very close. She wants to tell the whole truth to the mother-in-law. My right hand hurts now. I need to give rest to this hand.*

Many learners who are familiar with other Slavic languages, or who simply forget the alternation rule, might try to say words like *подругі* or *книгі*. You must actively avoid making this mistake. The forms **подрузі** and **книзі** are the only correct and natural options in modern Ukrainian. Saying *подругі* sounds completely wrong to a native speaker because it violates the deep phonetic rules of the language. Always pause and check the final consonant of the stem before you add the Dative ending.

Not all feminine nouns end in **-а** or **-я**. A smaller but very important group of feminine words ends in a consonant. These belong to the third declension. The good news is that they also take the **-і** ending in the Dative case. The word for night (**ніч**) becomes **ночі**, and the word for mother (**мати**) becomes **матері**. Abstract concepts like love (**любов**) and joy (**радість**) follow this exact same pattern, becoming **любові** and **радості**.

Now that you know the endings and the alternation rules, you can start building more complex sentences. The Dative case perfectly marks the recipient or the indirect object in your sentences, especially when using common verbs of giving and communicating.

Ми хочемо подарувати красиві квіти мамі. Вчитель має чітко пояснити нове правило студентові та студентці. Старший брат хоче розповісти смішну історію сестрі. Я маю терміново відповісти другові та подрузі сьогодні. Він вирішив показати ці фотографії своїй матері.

> *We want to give beautiful flowers to mom. The teacher has to clearly explain the new rule to the male student and the female student. The older brother wants to tell a funny story to the sister. I have to urgently answer the male friend and the female friend today. He decided to show these photographs to his mother.*

<!-- INJECT_ACTIVITY: quiz-feminine-alternation -->

## Давальний відмінок іменників середнього роду (~400 words total)

Neuter nouns also have their own specific **закінчення** (ending) in the Dative case. Most neuter nouns belong to the second declension. If a neuter noun ends in a hard consonant followed by the vowel "о", it takes the **-у** ending. This makes their declension predictable and easy to learn. The word **місто** (city) becomes **місту**, and **слово** (word) becomes **слову**.

Я хочу дати нову назву цьому місту.
Ми маємо подякувати цьому маленькому селу.
Дитина радіє кожному новому слову.
Цьому великому вікну потрібні нові штори.

> *I want to give a new name to this city. We have to thank this small village. The child rejoices at every new word. This big window needs new curtains.*

For neuter nouns ending in the vowels "е" or "я", the stem is usually soft. These words take the **-ю** ending in the Dative case. For example, the word **море** (sea) becomes **морю**, and **серце** (heart) becomes **серцю**. A small group of neuter nouns has stems ending in a hissing consonant, known as mixed stems. The most common word here is **плече** (shoulder). Mixed stems take the **-у** ending, so it becomes **плечу**. 

Моя родина завжди радіє теплому морю.
Ти маєш дати спокій своєму серцю.
Лікар радить дати відпочинок моєму плечу.
Кожному великому полю потрібен дощ.

> *My family always rejoices at the warm sea. You have to give peace to your heart. The doctor advises to give rest to my shoulder. Every big field needs rain.*

:::info
**Grammar box**
Neuter nouns denoting babies and young animals add the suffixes **-ат-** or **-ят-** before the **-і** ending in the Dative case.
:::

A special group of neuter words denotes babies and young animals. These words usually end in "я" or "а", such as **немовля** (infant) or **курча** (chick). In the Dative case, a suffix appears before the ending, and the final vowel becomes **-і**. The word for an infant becomes **немовляті**, and a chick becomes **курчаті**. A common exception following a similar pattern is **ім'я** (name), which becomes **імені**.

Мати дає тепле молоко немовляті.
Дівчинка дає свіжу воду маленькому курчаті.
Тобі треба приділити увагу цьому імені.
Батько співає колискову своєму немовляті.

> *The mother gives warm milk to the infant. The girl gives fresh water to the little chick. You need to pay attention to this name. The father sings a lullaby to his infant.*

Neuter nouns in the Dative case often represent inanimate objects, so they appear slightly less frequently than words for people. You will encounter them mostly in abstract contexts, fixed expressions, or when assigning an attribute. For instance, you might give a name to a city or rejoice at the sun.

Студенти радіють цьому легкому завданню.
Письменник хоче дати нове життя цьому слову.
Ми маємо знайти місце цьому старому кріслу.
Нашому рідному місту сьогодні двісті років.

> *The students rejoice at this easy task. The writer wants to give new life to this word. We have to find a place for this old armchair. Our native city is two hundred years old today.*

<!-- INJECT_ACTIVITY: group-sort-dative-gender -->

## Давальний відмінок у реченні (~550 words total)

In Ukrainian, many actions involve two objects: the thing being acted upon and the recipient of the action. The typical word order is Subject, Verb, Dative recipient, and Accusative object. This structure clearly shows who is doing what and to whom, allowing for flexible sentence construction without losing the meaning.

Тетяна подарувала братові нову книгу. Вчитель показав студентам карту України. Я хочу написати другові довгий лист.

> *Tetiana gave her brother a new book as a gift. The teacher showed the students a map of Ukraine. I want to write a long letter to a friend.*

Several core verbs naturally require a recipient in the Dative case. When you use verbs like **дати** (to give), **подарувати** (to give as a gift), or **показати** (to show), you almost always need to specify who is receiving the item. The same applies to verbs of communication, such as **розповісти** (to tell, to narrate), **написати** (to write), **пояснити** (to explain), and **відповісти** (to answer, to reply). Learning these verbs alongside the Dative case will immediately make your conversations more detailed.

Михайло має пояснити студентові нове правило. Дідусь любить розповісти онуку цікаву історію. Ти повинен швидко відповісти сестрі на повідомлення.

> *Mykhailo has to explain the new rule to the student. The grandfather loves to tell his grandson an interesting story. You must quickly answer your sister's message.*

Let's see how these forms are used in a real-life situation, like addressing packages at a post office. The postal worker needs to know the exact destination for each item.

> — **Відправник:** Доброго дня. Я хочу відправити ці пакунки. *(Good day. I want to send these packages.)*
> — **Працівник пошти:** Кому вони? *(Who are they for?)*
> — **Відправник:** Студентові Петренку — підручник. Сестрі Олені — листівка. А дитині — іграшка. *(To student Petrenko — a textbook. To sister Olena — a postcard. And to the child — a toy.)*

It is crucial not to confuse the Dative case, which marks a destination or recipient, with the Genitive case, which indicates possession or absence. While some nouns might have similar forms, their functions in the sentence are completely different. A recipient actively receives something, whereas the Genitive case simply shows that something is missing or belongs to someone else.

Я хочу дати братові свій телефон. У мене немає брата. Вона завжди допомагає мамі на кухні. У кімнаті немає мами. Зверніть увагу на граматичне закінчення кожного слова.

> *I want to give my phone to my brother. I do not have a brother. She always helps her mother in the kitchen. There is no mother in the room. Pay attention to the grammatical ending of each word.*

Earlier, you learned how to use Dative pronouns in impersonal constructions to express states or needs. These exact same structures apply to nouns in the Dative case. Instead of a pronoun like "мені" or "йому," you simply use the Dative form of the person experiencing the state or having the need. This is how you say that someone is cold, needs something, or is a certain age.

Студентові треба багато вчитися перед іспитом. Мамі зараз дуже холодно. Моєму другові сьогодні виповнилося двадцять п'ять років. Маленькій дитині дуже подобається ця весела гра.

> *The student needs to study a lot before the exam. Mom is very cold right now. My friend turned twenty-five years old today. The little child really likes this fun game.*

:::info
**Grammar box**
When expressing someone's age, physical state, or a personal need in Ukrainian, the person experiencing it is always placed in the Dative case. 
:::

<!-- INJECT_ACTIVITY: match-up-verb-phrases -->
<!-- INJECT_ACTIVITY: unjumble-dative-syntax -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-nouns
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
