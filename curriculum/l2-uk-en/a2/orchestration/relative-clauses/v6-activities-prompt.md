<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/relative-clauses.yaml` file for module **49: Той, який...** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-insert-the-correct-form-of-into-relative-clauses-matching-gender-and-number -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-sentences-about-places -->`
- `<!-- INJECT_ACTIVITY: match-up-combine-two-simple-sentences-into-one-using-a-relative-clause -->`
- `<!-- INJECT_ACTIVITY: true-false-judge-whether-relative-clauses-have-correct-agreement-and-comma-placement -->`
- `<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-relative-clauses-with-and -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Insert the correct form of який (яка, яке, які) into relative clauses, matching
    gender and number
  items: 8
  type: fill-in
- focus: Choose де, куди, or звідки to complete sentences about places
  items: 8
  type: quiz
- focus: Combine two simple sentences into one using a relative clause
  items: 8
  type: match-up
- focus: Judge whether relative clauses have correct agreement and comma placement
  items: 8
  type: true-false
- focus: Reorder words to form correct relative clauses with який/яка/яке and де/куди/звідки
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- котрий (which — formal synonym of який)
- затишний (cozy, comfortable)
- знаходитися (to be located)
- стояти (to stand, to be situated)
required:
- який (which, that — masc.)
- яка (which, that — fem.)
- яке (which, that — neut.)
- які (which, that — pl.)
- де (where — relative)
- куди (where to — relative)
- звідки (where from — relative)
- означальний (attributive, defining)
- описувати (to describe)
- речення (sentence, clause)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Який? Яка? Яке? Які? (Which? What Kind?) (~800 words)

Have you ever wanted to describe something in more detail without starting a whole new sentence? In Ukrainian, we do this using an **означальний** (attributive, defining) clause. This is a special type of dependent **речення** (sentence, clause) that acts just like a very long adjective. It helps us **описувати** (to describe) a noun that is mentioned in the main part of the phrase. 

Instead of saying "I have a car. The car is fast," you can say "I have a car that is fast." In English, you might use words like "who," "which," or "that" to smoothly connect these related ideas together. In Ukrainian, the most common way to build these connections is by using the word **який** (which, that — masc.) and its corresponding forms. This single word serves as a powerful bridge. It allows you to create much richer, more detailed stories about the interesting people, everyday objects, and new places in your life.

Let us see how this looks in a real-life situation. Imagine you are with a real estate agent, looking at a new place to live. They are showing you the specific features of the apartment.

> — **Ріелтор:** Ось квартира, яка має великий балкон. *(Here is the apartment that has a big balcony.)*
> — **Покупець:** Дуже гарно. А це що за кімната? *(Very nice. And what is this room?)*
> — **Ріелтор:** Це спальня, де ви можете відпочивати. *(This is the bedroom where you can rest.)*
> — **Покупець:** А хто живе поруч? *(And who lives nearby?)*
> — **Ріелтор:** Сусід, який живе поруч, дуже тихий. *(The neighbor who lives nearby is very quiet.)*
> — **Покупець:** Це ідеальне місце, яке мені дуже подобається. *(This is an ideal place that I like very much.)*

When you use this connecting word in the Nominative case, it must perfectly match the gender and number of the noun it is describing. This means you will need to choose carefully between **яка** (which, that — fem.), **яке** (which, that — neut.), and **які** (which, that — pl.) based on the main word you want to highlight. The relative pronoun is acting as a substitute for the noun inside the newly attached clause, so it simply adopts the noun's existing characteristics. If the main noun is feminine, the connector is feminine. If the main noun is plural, the connector becomes plural. It is a direct and logical mirror.

Хлопець, який прийшов вчора, — це мій брат. Книжка, яка лежить на столі, дуже цікава. Місто, яке я люблю, завжди красиве. Друзі, які живуть у Києві, чекають на нас.

> *The boy who came yesterday is my brother. The book that lies on the table is very interesting. The city that I love is always beautiful. The friends who live in Kyiv are waiting for us.*

:::info
**Grammar box**
Always look at the noun *immediately before* the connector to decide its proper gender and number. If you are describing «студенти» (students), use **які**. If you are describing «кафе» (cafe), use **яке**.
:::

Now, let us look at the Accusative case. This is where many learners make a mistake. The case of the word "який" does NOT depend on the main sentence. Instead, it takes the case required by its specific role inside the subordinate clause. If it is the object of the action in the second part of the sentence, it must be in the Accusative case, even if the main noun is in the Nominative case. Compare these two ideas: "The person who met me" and "The person whom I met." In the first phrase, the person is doing the meeting, which means they are the subject in the Nominative case. In the second phrase, the person is being met, which means they are the direct object in the Accusative case. The word ending always changes to reflect this specific action.

Людина, яка мене зустріла, працює тут. Людина, яку я зустрів, працює тут.

> *The person who met me works here. The person whom I met works here.*

Ось студент, якого я знаю. Це телефон, який я купив. Там дівчина, яку ми бачили. Це вікно, яке я відкрив. Ось люди, яких ти запросив.

> *Here is the student whom I know. This is the phone that I bought. There is the girl whom we saw. This is the window that I opened. Here are the people whom you invited.*

Punctuation in Ukrainian is very strict when it comes to these descriptive clauses. You must always place a comma immediately before the connector word. This comma acts as a signal to the reader or listener that you are about to pause and add extra descriptive information. In English, you can often drop the comma or even drop the word "that" entirely, saying "The book I read." In Ukrainian, this is never allowed. The comma and the connector word are absolutely mandatory.

Ми дивимося фільм, який нам дуже подобається. Я читаю статтю, яка пояснює ці правила.

> *We are watching a film that we like very much. I am reading an article that explains these rules.*

It is important to contrast this new grammar with something you already know. You have already learned how to use this exact same word to ask questions. When asking a question, it means "what kind" or "which one." When used to connect two parts of a sentence, it means "who," "which," or "that." It is the same word, but it performs a completely different function depending on where it sits in the sentence. Context will always tell you what the word is doing.

Який це фільм? Фільм, який ми дивилися вчора, був дуже смішний. Яка це вулиця? Вулиця, яка веде до центру, довга.

> *What kind of film is this? The film that we watched yesterday was very funny. What street is this? The street that leads to the center is long.*

У мене є собака, який дуже любить гратися. Це комп'ютер, який я часто використовую для роботи. Жінка, яка стоїть біля вікна, — моя мама.

:::tip
**Did you know?**
When speaking, Ukrainians slightly drop their pitch when starting a relative clause. The comma is not just for writing; it represents a brief, natural pause in spoken Ukrainian.
:::

Finally, there is a very common, natural alternative that you will hear native speakers use constantly. Instead of matching the gender and number every single time, you can often use the short, invariant word "що". In the Nominative and Accusative cases, this little word can replace the longer connector. It never changes its form, making it incredibly easy to use in everyday conversation. It makes your speech sound flowing and natural without having to pause and think about grammar endings.

Це Євген, що працює зі мною в офісі. Це м'ясо, що ми купили на ринку.

> *This is Yevhen, who works with me in the office. This is the meat that we bought at the market.*

<!-- INJECT_ACTIVITY: fill-in-insert-the-correct-form-of-into-relative-clauses-matching-gender-and-number -->

## Де, куди, звідки — місце (Where, Where To, Where From — Place)

When you want to describe a place, you have a grammatical choice. You could use a relative pronoun together with a preposition. For example, to say "the city in which I live," you could say «місто, в якому я живу». However, there is a simpler way to build this kind of structure. The Ukrainian word for a sentence or clause is **речення** (sentence). In a complex sentence about a place, speakers frequently use invariant relative adverbs. The word for a static location is **де** (where).

Слово показує статичне місце. Воно легко і природно замінює складну граматичну конструкцію «в якому» або «на якому». Ти використовуєш це слово, коли хочеш описати локацію, де відбувається дія, але немає жодного руху. Зверни увагу: кома перед цим сполучним словом є обов'язковою.

> *The word shows a static place. It easily and naturally replaces the complex grammatical construction "в якому" or "на якому" (in/on which). You use this word when you want to describe a location where an action takes place, but there is no movement. Note: a comma before this connector word is mandatory.*

Кафе, де ми зустрілися, було дуже затишне. Місто, де я народився, знаходиться на заході країни. Це великий парк, де діти часто грають у футбол. Кімната, де вона працює, завжди чиста і світла. Будинок, де живе мій друг, стоїть біля озера.

> *The cafe where we met was very cozy. The city where I was born is located in the west of the country. This is a large park where children often play football. The room where she works is always clean and bright. The house where my friend lives stands near a lake.*

However, Ukrainian is very strict about distinguishing between a static location and an active direction. If the action in your relative clause involves movement toward a specific destination, you cannot use the standard word for 'where'. The word for 'where to' is **куди** (where to). This is a crucial difference from English, which uses "where" for both static position and movement. Whenever your subordinate clause contains a verb of motion like «іти» or «їхати», you must switch your connector word.

Парк, куди ми ходимо гуляти кожної неділі, дуже великий. Це новий ресторан, куди вони планують піти на вечерю. Місто, куди він завтра їде у відрядження, знаходиться далеко звідси. Театр, куди ми вчора купили квитки, відомий на всю країну.

> *The park where we go for a walk every Sunday is very large. This is a new restaurant where they plan to go for dinner. The city where he is going on a business trip tomorrow is located far from here. The theater where we bought tickets yesterday is famous all over the country.*

:::info
**Direction vs. Location**
Always check the main verb inside the descriptive part of the sentence. If the action answers the question "Where to?" (Куди?), use **куди**. If the action answers the question "Where at?" (Де?), use **де**.
:::

The third important relative pronoun indicates the initial starting point or place of origin. The word for 'where from' is **звідки** (where from). It is always used together with verbs of motion that mean returning, leaving, or arriving from some specific place.

Країна, звідки вона приїхала минулого року, має дуже цікаву історію. Це університет, звідки я щойно повернувся після лекції. Магазин, звідки вони приносять ці свіжі овочі, працює цілодобово. Місто, звідки починається наш маршрут, лежить на березі річки.

> *The country where she came from last year has a very interesting history. This is the university from which I just returned after a lecture. The store where they bring these fresh vegetables from is open around the clock. The city where our route begins lies on the bank of the river.*

To truly master these relative adverbs, you must focus on the relationship between the place and the action happening inside the relative clause. If your goal is to describe a scene—the verb for 'to describe' is **описувати** (to describe)—the main noun remains exactly the same, but the connector word changes based on what happens next. Let's look at how the same noun behaves differently depending on whether the action is static, moving toward it, or moving away from it.

Це місто, де я живу і працюю кожного дня. Це місто, куди я їду на вихідні до своїх батьків. Це місто, звідки я щойно повернувся після відпустки.

> *This is the city where I live and work every day. This is the city where I am going for the weekend to see my parents. This is the city where I just returned from after a vacation.*

Головний іменник залишається незмінним. Змінюється лише слово, яке з'єднує дві частини. Цей простий граматичний інструмент робить твоє мовлення багатим і дуже природним.

> *The main noun remains unchanged. Only the word that connects the two parts changes. This simple grammatical tool makes your speech rich and very natural.*

<!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-sentences-about-places -->

## Описуємо людей, речі та місця (Describing People, Things, and Places) (~750 words)

When you start learning a language, you naturally speak in short, simple sentences. This is a normal stage, but it can make your speech sound a bit choppy. To sound more advanced and fluent, you need to learn how to combine these short statements into a single, cohesive thought. You can achieve this by using an attributive clause, which in Ukrainian is called an **означальний** (attributive, defining) clause. Such a **речення** (sentence, clause) acts like a long adjective, giving more information about a specific noun. We usually connect them with words like **який** (which, that — masc.).

Розглянемо типовий приклад з коротких речень. Це мій друг. Він живе у Києві. Він працює програмістом. Ці речення граматично правильні, але вони звучать занадто просто. Ми можемо об'єднати їх в одне гарне речення за допомогою відносного займенника. Це мій друг, який живе у Києві і працює програмістом. Таке речення звучить набагато природніше і показує ваш високий рівень володіння мовою.

> *Let's look at a typical example of short sentences. This is my friend. He lives in Kyiv. He works as a programmer. These sentences are grammatically correct, but they sound too simple. We can combine them into one beautiful sentence using a relative pronoun. This is my friend, who lives in Kyiv and works as a programmer. Such a sentence sounds much more natural and shows your high level of language proficiency.*

<!-- INJECT_ACTIVITY: match-up-combine-two-simple-sentences-into-one-using-a-relative-clause -->

As you become more comfortable with these structures, you can start describing complex scenes by combining relative pronouns and relative adverbs in the same sentence. This allows you to build a smooth narrative flow and paint a detailed picture for your listener. You already know how to use words like **де** (where — relative), **куди** (where to — relative), and **звідки** (where from — relative) to describe locations. Now, try mixing them with the relative pronouns you learned earlier.

Ресторан, де ми вчора вечеряли, знаходиться біля парку. Жінка, яка сидить за тим столиком, приїхала з іншого міста. Магазин, звідки вони привозять ці смачні фрукти, належить моєму сусіду. Ці великі речення допомагають нам детально описувати людей, речі та місця.

> *The restaurant where we had dinner yesterday is located near the park. The woman who is sitting at that table came from another city. The store where they bring these delicious fruits from belongs to my neighbor. These large sentences help us accurately describe people, things, and places.*

:::note
**Quick tip**
When you stack multiple clauses, make sure you don't lose track of the main subject. The core of the sentence remains the most important part, while the relative clauses simply add colorful details to the nouns.
:::

English speakers often make three common mistakes when forming relative clauses in Ukrainian. First, in English, you can often omit the relative pronoun, saying things like "The book I read." In Ukrainian, this is absolutely impossible. The relative pronoun is mandatory. 

**Книга, яку я читав.** — *The book I read.*

Skipping the connector word will confuse your listener. Second, avoid using redundant pronouns. Sometimes learners try to combine the relative pronoun with a personal pronoun, resulting in incorrect sentences.

**Книжка, яка вона цікава.** — *The book, which it is interesting.* (<!-- VERIFY --> WRONG)

The relative pronoun already replaces the noun, so you do not need to add the extra personal pronoun. Finally, be careful with the English distinction between "who" for humans and "which" or "that" for objects. In Ukrainian, the pronoun is universal. You will use the feminine form **яка** (which, that — fem.) for both a woman and a female-gendered object. Similarly, you use **яке** (which, that — neut.) for neuter nouns and **які** (which, that — pl.) for plurals.

Дівчина, яка читає журнал, — моя сестра. Це нова машина, яка коштує дуже дорого. Студенти, які вчаться у нашому університеті, організували цікавий концерт. Це нові правила, які ми повинні запам'ятати. Дерево, яке росте біля нашого будинку, дуже старе. Озеро, яке знаходиться за містом, ідеально підходить для риболовлі.

> *The girl who is reading a magazine is my sister. This is a new car that costs a lot. The students who study at our university organized an interesting concert. These are new rules that we must remember. The tree that grows near our house is very old. The lake that is located outside the city is perfect for fishing.*

<!-- INJECT_ACTIVITY: true-false-judge-whether-relative-clauses-have-correct-agreement-and-comma-placement -->

Another crucial aspect of mastering relative clauses is the intonation. Punctuation is strict in Ukrainian: you must always place a comma before the relative pronoun or adverb that introduces the clause. This comma is not just a grammatical rule; it is a direct instruction for your voice.

Головне речення починається з нейтральної інтонації. Потім ви робите коротку паузу перед комою. Підрядна частина, яка починається з цих слів, вимовляється з нижчим тоном. Вона звучить як додаткове пояснення. Після цього інтонація повертається до нормального рівня. Ця пауза перед комою дає слухачеві сигнал, що зараз буде детальний опис.

> *The main sentence begins with a neutral intonation. Then you make a short pause before the comma. The subordinate part, which begins with these words, is pronounced with a lower pitch. It sounds like an additional explanation. After that, the intonation returns to a normal level. This pause before the comma gives the listener a signal that a detailed description is coming.*

:::info
**Grammar box**
Always use a comma before the relative words when they connect two parts of a complex sentence. In spoken Ukrainian, this comma corresponds to a slight pause and a drop in pitch, acting like verbal parentheses around the descriptive clause.
:::

While reading Ukrainian literature or watching formal news broadcasts, you might encounter another relative pronoun: котрий. This word also means "which" or "who" and is a formal synonym for the relative pronoun you have been practicing.

Письменник, котрий написав цей роман, народився у Львові. Це історичний документ, котрий знайшли в архіві минулого року. Журналістка, котра веде цю програму, дуже відома в Україні. Ви будете часто бачити це слово в текстах.

> *The writer who wrote this novel was born in Lviv. This is a historical document that was found in the archive last year. The journalist who hosts this program is very famous in Ukraine. You will often see this word in texts.*

At the A2 level, you do not need to actively use this formal synonym in your daily conversations. It is completely acceptable and stylistically neutral to rely exclusively on the primary relative pronouns and adverbs you have learned in this module to **описувати** (to describe) things. Recognize the formal synonym when you read it, but stick to the simpler, more universal words when you speak.

Now it is time to put all this theory into practice. Knowing the rules is only the first step; true fluency comes from personalizing the grammar. Think about your own life and the things that matter to you. How would you describe your favorite place using these relative clauses? How would you describe a person you admire, or an object you use every single day?

Напишіть кілька речень про своє рідне місто. Використайте слова де, куди та звідки. Потім опишіть свого найкращого друга за допомогою відносних займенників. Згадайте кафе, яке ви любите відвідувати на вихідних. Регулярна практика допоможе вам використовувати ці конструкції у реальній розмові.

> *Write a few sentences about your hometown. Use the words where, where to, and where from. Then describe your best friend using relative pronouns. Think of a cafe that you like to visit on the weekends. Regular practice will help you use these constructions in real conversation.*

<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-relative-clauses-with-and -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: relative-clauses
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

**Level: A2 (Module 49/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
