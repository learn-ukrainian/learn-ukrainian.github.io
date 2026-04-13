<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-pronouns.yaml` file for module **17: Мені, тобі, йому...** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-pronouns -->`
- `<!-- INJECT_ACTIVITY: fill-in-dative-pronouns -->`
- `<!-- INJECT_ACTIVITY: true-false-impersonal -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-dative-or-accusative-pronoun-form-in-context-vs -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match nominative pronoun to its dative form (я→мені, ти→тобі, etc.)
  items: 8
  type: match-up
- focus: Complete sentences with the correct dative pronoun based on context
  items: 8
  type: fill-in
- focus: Choose dative or accusative pronoun form in context (тобі vs. тебе)
  items: 8
  type: quiz
- focus: Judge whether impersonal dative sentences (мені холодно, мені бачу) are correct
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- приємно (pleasant)
- цікаво (interesting)
- сумно (sad (impersonal state))
- важко (difficult, hard)
required:
- давальний відмінок (dative case)
- мені (to me)
- тобі (to you (informal))
- йому (to him, to it)
- їй (to her)
- нам (to us)
- вам (to you (formal/plural))
- їм (to them)
- холодно (cold (impersonal state))
- потрібно (necessary, needed)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Давальний відмінок: Кому? (The Dative Case: To Whom?) (~550 words total)

Welcome to a new case! In Ukrainian grammar, the **давальний відмінок** (dative case) is the case of the recipient. Its very name comes from the verb «давати», which means to give. Whenever you give a gift, tell a secret, or send a message, there is always someone on the receiving end. This case answers the questions «Кому?» (To whom?) for people and animals, and «Чому?» (To what?) for objects or abstract concepts. It identifies the person or thing that receives the result of an action, or for whom an action is performed.

:::info
**Grammar box**
The Dative case highlights the destination of your action. If you throw a ball, the ball is the object being thrown, but the friend catching it is the recipient in the Dative case.
:::

Українська мова має багато дієслів, які вимагають давального відмінка. Найчастіше ми використовуємо його, коли говоримо про подарунки, поради або допомогу. Це дуже важливий відмінок для щоденного спілкування.

> *The Ukrainian language has many verbs that require the dative case. Most often, we use it when we talk about gifts, advice, or help. This is a very important case for everyday communication.*

To understand how this new grammatical tool fits into the puzzle, let us compare it with the cases you already know. The Genitive case answers «Кого? Чого?» and typically shows possession, origin, or the absence of something. The Accusative case answers «Кого? Що?» and marks the direct object, which is the person or thing directly experiencing the physical action. The Dative case, however, marks the indirect object. The direct object is what is being moved or changed, while the indirect object is the destination or the beneficiary of that change.

Уяви ситуацію з подарунком. Спочатку ти купуєш книгу, і це знахідний відмінок. Потім ти даруєш цю книгу другові, і твій друг стоїть у давальному відмінку.

> *Imagine a situation with a gift. First, you buy a book, and this is the accusative case. Then you give this book to a friend, and your friend stands in the dative case.*

Let us look at the classic structure of giving and telling. The formula is usually simple: you perform an action with a direct object in the Accusative case, directed toward a recipient in the Dative case. Two of the most common verbs that trigger this pattern are «давати» (to give) and «казати» (to say, to tell).

Мама дає дитині смачне яблуко. Вчитель каже студентам нове правило. Ми даємо друзям квитки на концерт. Вони кажуть нам правду про цю подію.

> *A mother gives her child a tasty apple. A teacher tells the students a new rule. We give our friends tickets to a concert. They tell us the truth about this event.*

Imagine a loud family gathering where birthday gifts are finally being distributed. Notice how the pronouns change to show who gets what.

> — **Іменинник:** Що там у великій коробці? *(What is there in the big box?)*
> — **Родина:** Зараз подивимося! **Мені** — нову книгу. *(Let's see now! For me — a new book.)*
> — **Іменинник:** А що дарують **тобі**? *(And what are they gifting to you?)*
> — **Родина:** **Тобі** — чорний шоколад. А **йому** — теплий шарф. *(To you — dark chocolate. And to him — a warm scarf.)*
> — **Іменинник:** А що подарували бабусі? *(And what did they gift to grandma?)*
> — **Родина:** **Їй** — красиві квіти. А **нам** усім — великий торт! *(To her — beautiful flowers. And to all of us — a big cake!)*

In the dialogue above, every person who receives a present is expressed using the Dative case. Notice how the Ukrainian language does not use any prepositions here. While English relies on extra words like "to" or "for" to show the recipient, Ukrainian simply changes the form of the pronoun itself. The word for "I" becomes **мені** (to me), "you" becomes **тобі** (to you), and so on. This makes the sentence structure elegant and compact. 

Українські займенники просто змінюють свою форму. Тобі не потрібні зайві прийменники, щоб показати напрямок дії. Одне коротке слово робить речення зрозумілим і точним.

> *Ukrainian pronouns simply change their form. You do not need extra prepositions to show the direction of an action. One short word makes the sentence clear and precise.*

In the next section, we will look at the complete set of these pronouns and learn how to form them for every person.

## Особові займенники у давальному відмінку (Personal Pronouns in the Dative) (~770 words total)

In the **давальний відмінок** (dative case), personal pronouns undergo a complete transformation. For the first and second person, the dative forms are built on an entirely different stem than their standard dictionary forms. You cannot simply attach a new ending to the word "я" or "ти". Instead, you must memorize these forms as a unique set. The word for "I" becomes **мені** (to me), and "you" becomes **тобі** (to you (informal)). In the plural, "we" becomes **нам** (to us), and "you" becomes **вам** (to you (formal/plural)).

Займенник «я» перетворюється на слово «мені». Займенник «ти» змінює свою форму на слово «тобі». У множині ми кажемо «нам» замість називного «ми». А замість слова «ви» ми завжди говоримо «вам».

> *The pronoun "I" turns into the word "мені". The pronoun "you" changes its form to the word "тобі". In the plural, we say "нам" instead of the nominative "we". And instead of the word "you", we always say "вам".*

These are among the most frequently used words in the language. You will hear them constantly whenever people share things, explain their feelings, or give advice to one another.

The third-person pronouns follow a slightly different, more predictable pattern. If you look closely, you might notice that their endings resemble the dative endings of adjectives. However, it is usually faster to just learn them as short, independent vocabulary items. The masculine and neuter form is **йому** (to him, to it), the feminine form is **їй** (to her), and the plural form is **їм** (to them).

Якщо це чоловічий або середній рід, ми використовуємо слово «йому». Для жіночого роду ми завжди кажемо слово «їй». Коли ми говоримо про велику групу людей, ця форма змінюється на «їм».

> *If it is masculine or neuter gender, we use the word "йому". For feminine gender, we always say the word "їй". When we talk about a large group of people, this form changes to "їм".*

Notice that "він" and "воно" share the exact same form in the dative case. You will use these tiny words continuously when explaining who received a specific item or who is being addressed.

There is a special phonetic rule for third-person pronouns in Ukrainian. In most other cases, when a third-person pronoun comes right after a preposition, it gains an extra letter "н" at the beginning for smoother pronunciation. For example, in the genitive case, the word "його" becomes "до нього" (to him). However, the dative case is almost never used with prepositions in basic everyday speech. 

Тому в давальному відмінку ти майже завжди бачиш ці слова без букви «н». Ти просто кажеш «йому», «їй» або «їм» у реченні. Тобі не потрібні жодні прийменники, щоб показати правильний напрямок дії.

> *Therefore, in the dative case, you almost always see these words without the letter "n". You simply say "йому", "їй", or "їм" in a sentence. You do not need any prepositions to show the correct direction of the action.*

:::info
**Grammar box**
The dative case is strong enough to point to the recipient all by itself. While English requires a preposition like "give *to* him" or "buy *for* her", Ukrainian elegantly achieves this with just the pronoun alone: "дай йому" or "купи їй".
:::

Now let us put these newly learned pronouns to work with common verbs of giving and communicating. The standard word order in these sentences is very logical and consistent: first comes the action verb, then the dative recipient, and finally the accusative object that is being transferred.

Будь ласка, дай мені цю цікаву книгу. Скажи їй усю правду сьогодні. Покажи нам ваше нове сімейне фото. Напиши їм довгого та веселого листа.

> *Please, give me this interesting book. Tell her the whole truth today. Show us your new family photo. Write them a long and cheerful letter.*

Notice how the short dative pronoun sits comfortably right after the verb. This rhythm feels very natural in spoken Ukrainian. The person receiving the item almost always comes before the actual item being given.

One of the most common challenges for learners is mixing up the accusative and dative pronoun forms, especially for the words "me" and "you". The accusative form is "мене", which answers the question "who is directly affected?". The dative form is "мені", which answers "to whom?".

Я бачу тебе на вулиці, але я кажу тобі секрет. Вона добре знає мене, але вона дає мені холодну воду. Ніколи не кажи «дай я книгу», бо це дуже велика помилка.

> *I see you on the street, but I am telling you a secret. She knows me well, but she gives me cold water. Never say "give I a book", because this is a very big mistake.*

Always ask yourself: is this person the direct target being seen or heard, or are they the recipient receiving an object or a message? If they are receiving something, you must choose the dative form.

<!-- INJECT_ACTIVITY: match-up-pronouns -->

Let us look at a few more examples of these pronouns in everyday conversational situations. These short words are truly the glue that holds daily communication together.

> — **Олена:** Що ти даруєш йому на свято? *(What are you gifting him for the holiday?)*
> — **Марко:** Я дарую йому новий телефон. А що ти даєш їм? *(I am gifting him a new phone. And what are you giving them?)*
> — **Олена:** Я даю їм дорогі квитки в театр. *(I am giving them expensive theater tickets.)*
> — **Марко:** Розкажи мені більше про цю виставу. *(Tell me more about this play.)*

Коротка форма займенника робить українське речення дуже швидким і зручним для вимови. Тобі треба запам'ятати ці слова, бо вони зустрічаються абсолютно всюди.

> *The short form of the pronoun makes the Ukrainian sentence very fast and convenient for pronunciation. You need to remember these words because they are found absolutely everywhere.*

<!-- INJECT_ACTIVITY: fill-in-dative-pronouns -->

## Мені холодно: Безособові конструкції (Impersonal Constructions with Dative)

One of the most common and natural ways to express feelings, physical states, and needs in Ukrainian is through impersonal constructions. Instead of using a normal subject like "I" or "you", the language flips the perspective. The person experiencing the feeling is placed in the **давальний відмінок** (dative case), and the state itself is expressed as an adverb. This structure literally translates to "to me it is cold" or "to her it is interesting."

В українській мові ми дуже часто використовуємо безособові конструкції. Вони ідеально підходять, щоб описати наш фізичний стан, настрій або якусь потребу. У таких реченнях немає підмета, який виконує дію. Натомість ми ставимо особу в давальний відмінок, а потім додаємо спеціальне слово-стан. Ця граматична модель звучить надзвичайно природно для носіїв мови.

> *In the Ukrainian language, we very often use impersonal constructions. They are perfectly suited to describe our physical state, mood, or some need. In such sentences, there is no subject performing an action. Instead, we put the person in the dative case, and then add a special state-word. This grammatical model sounds extremely natural to native speakers.*

You can combine dative pronouns like **мені** (to me) and **тобі** (to you (informal)) with many different words to describe various situations. We use words like **холодно** (cold (impersonal state)) for physical states, and other specific words for emotions or difficulty.

Мені сьогодні дуже холодно на вулиці, але вдома тепло. Тобі сумно читати цю стару книгу? Їй завжди весело грати з маленьким собакою, а йому нудно сидіти вдома. Нам цікаво вивчати українські традиції та культуру. Вам потрібно купити квитки на ранковий потяг заздалегідь. Їм дуже важко працювати без нового комп'ютера. Мені приємно бачити вас у нашому новому офісі.

> *It is very cold for me outside today, but it is warm at home. Is it sad for you to read this old book? It is always fun for her to play with the small dog, and it is boring for him to sit at home. It is interesting for us to study Ukrainian traditions and culture. It is necessary for you to buy tickets for the morning train in advance. It is very hard for them to work without a new computer. It is pleasant for me to see you in our new office.*

:::info
**Grammar box**
Remember that in these structures, words like «холодно» or «цікаво» never change their form. They do not have a gender or plural ending, because there is no subject to agree with. They always end in the letter «-о».
:::

When comparing English and Ukrainian, this structural difference becomes very clear. English almost always relies on a standard nominative subject, saying "I am tired" or "she is cold." The Ukrainian dative impersonal form using pronouns like **йому** (to him, to it) or **їй** (to her) often feels more authentic. It suggests that a state, or something that is **потрібно** (necessary, needed), is happening to the person, rather than being an active characteristic.

Порівняйте ці два різні підходи до побудови речення. Я дуже втомлена після довгого робочого дня. Але мені сьогодні важко думати про серйозні проблеми. Вона неймовірно холодна і ніколи не посміхається. Але зараз їй просто холодно чекати на зимовій зупинці. Ти мусиш зробити це важливе завдання. Але тобі потрібно закінчити цю роботу до вечора.

> *Compare these two different approaches to building a sentence. I am very tired after a long workday. But it is hard for me to think about serious problems today. She is incredibly cold and never smiles. But right now she is simply cold waiting at the winter bus stop. You must do this important task. But it is necessary for you to finish this work by evening.*

Let us look at a typical conversation where two friends discuss their plans and feelings. You will notice how frequently they use forms like **нам** (to us), **вам** (to you (formal/plural)), and **їм** (to them) to express what they need right now.

> — **Марко:** Привіт, Олено! Як ти себе почуваєш сьогодні? *(Hi, Olena! How are you feeling today?)*
> — **Олена:** Привіт! Мені трохи сумно, бо на вулиці йде дощ. *(Hi! I am a bit sad because it is raining outside.)*
> — **Марко:** А мені дуже холодно стояти тут. Ходімо в кафе? *(And I am very cold standing here. Shall we go to a cafe?)*
> — **Олена:** Це чудова ідея! Мені потрібно випити гарячого чаю. *(That is a great idea! I need to drink some hot tea.)*
> — **Марко:** Тобі цікаво піти в нове кафе біля парку? *(Are you interested in going to the new cafe near the park?)*
> — **Олена:** Так, мені завжди приємно пробувати щось нове. *(Yes, it is always pleasant for me to try something new.)*
> — **Марко:** Добре, тоді нам треба поспішати. *(Good, then we need to hurry.)*

<!-- INJECT_ACTIVITY: true-false-impersonal -->

## Давальний чи знахідний? (Dative or Accusative?) (~330 words total)

One of the most common challenges is deciding when to use the accusative case and when to use the **давальний відмінок** (dative case). Both cases can sometimes translate similarly in English, but they have very different roles. It is **потрібно** (necessary, needed) to remember a simple rule: is the person receiving the action, or directly affected by it? If they are the recipient of words, gifts, or help, use the dative case.

Часто студенти не знають, який відмінок вибрати. Ці два відмінки мають різні функції в реченні. Якщо особа є отримувачем дії, ми використовуємо давальний відмінок. Якщо особа є прямим об'єктом дії, ми використовуємо знахідний відмінок. Кому ми даємо подарунок? Кого ми бачимо на вулиці?

> *Often students do not know which case to choose. These two cases have different functions in a sentence. If a person is the recipient of an action, we use the dative case. If a person is the direct object of an action, we use the accusative case. To whom do we give a gift? Whom do we see on the street?*

Let us look at some minimal pairs to solidify this distinction. When you see someone, they are the direct object, so you use the accusative pronoun forms. But when you speak to someone, they are the recipient of your words, so you must use the dative forms like **тобі** (to you (informal)) or **їй** (to her).

Я бачу тебе в парку. Але я кажу тобі правду. Він дуже добре знає її. Але він дзвонить їй кожного вечора. Вони чують нас. Але вони допомагають нам. Ми розуміємо вас. Але ми дякуємо вам за допомогу.

> *I see you in the park. But I tell you the truth. He knows her very well. But he calls her every evening. They hear us. But they help us. We understand you. But we thank you for the help.*

The plural forms behave the exact same way. When you give instructions or offer help, you direct your action toward **нам** (to us), **вам** (to you (formal/plural)), or **їм** (to them).

You will often use both cases in a single sentence when a verb takes two objects. Common verbs that describe giving or showing are perfect examples. If it is **холодно** (cold (impersonal state)) outside and your friend buys hot coffee for you, the coffee is the direct object. We use **мені** (to me) or **йому** (to him, to it) to show who receives the drink.

Сьогодні мені дуже холодно. Тому мій брат купує мені гарячу каву. Кава — це прямий об'єкт. А я — отримувач. Вчитель показує нам нову школу. Школа — це те, що він показує. А ми — ті, кому він це показує.

> *Today I am very cold. That is why my brother buys me hot coffee. Coffee is the direct object. And I am the recipient. The teacher shows us the new school. The school is what he shows. And we are the ones to whom he shows it.*

:::tip
**Quick tip**
If you can logically put "to" or "for" before the pronoun in English (like "give the book *to* him" or "buy coffee *for* me"), you almost certainly need the dative case in Ukrainian.
:::

<!-- INJECT_ACTIVITY: quiz-choose-dative-or-accusative-pronoun-form-in-context-vs -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-pronouns
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

**Level: A2 (Module 17/60) — ELEMENTARY**

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю


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
