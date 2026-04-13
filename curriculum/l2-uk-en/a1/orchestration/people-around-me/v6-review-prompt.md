<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 40: People Around Me (A1, A1.6 [Food and Shopping])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-040
level: A1
sequence: 40
slug: people-around-me
version: '1.2'
title: People Around Me
subtitle: Я бачу маму, знаю Олену — accusative for people
focus: grammar
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Use accusative case for animate nouns (Я бачу маму, знаю Олену)
- Recognize that masculine animate accusative = genitive (бачу брата, друга)
- Distinguish animate vs inanimate accusative
- Talk about people in your daily life using accusative
dialogue_situations:
- setting: 'Showing wedding photos — identifying people: Бачиш маму (f→acc)? А тата
    (m→acc)? Знаєш Олену (f→acc)? Це мій дядько (m), а це тітка (f). Ось наречена
    (f) і наречений (m).'
  speakers:
  - Наречена
  - Друг
  motivation: 'Accusative animate: маму(f), тата(m), Олену(f), дядька(m)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Who do you see? — Кого ти бачиш? — Я бачу маму і тата. — А хто це?
    — Це мій брат. Ти знаєш мого брата? — Ні, я не знаю твого брата. — Ходімо, я тебе
    познайомлю! Accusative animate: маму (f), тата (m), брата (m).'
  - 'Dialogue 2 — At work: — Ти знаєш нашу вчительку? — Так, я знаю Олену Петрівну.
    — А нового лікаря? — Ні, я ще не знаю лікаря. — Він дуже добрий. Я чекаю його
    зараз. Animate accusative with people around you.'
- section: Кого? (Whom?)
  words: 300
  points:
  - 'Accusative animate vs inanimate: Inanimate (M37): Я їм (що?) хліб. → no change
    for masculine. Animate (M40): Я бачу (кого?) брата. → masculine changes! The question
    word is the key: що? = inanimate (things) → masculine stays same. кого? = animate
    (people, animals) → masculine changes.'
  - 'Ukrainian school approach (Grade 4): ''Бачу кого? що?'' — two questions, two
    patterns. Кого? triggers the animate rule: masculine animate accusative = genitive
    form. брат → брата, друг → друга, тато → тата, лікар → лікаря. This is why animate
    accusative matters — it changes masculine nouns.'
- section: Знахідний відмінок — живе (Accusative Animate)
  words: 300
  points:
  - 'Feminine animate: same as inanimate (-а → -у, -я → -ю): мама → маму (Я бачу маму),
    сестра → сестру (Я знаю сестру), Олена → Олену (Я чекаю Олену), подруга → подругу
    (Я люблю подругу). No surprise — same ending as M37 (кава → каву).'
  - 'Masculine animate: accusative = genitive (THE new rule): брат → брата (Я бачу
    брата), друг → друга (Я знаю друга), тато → тата (Я люблю тата), лікар → лікаря
    (Я чекаю лікаря), вчитель → вчителя (Я знаю вчителя), сусід → сусіда (Я бачу сусіда).
    Pattern: masculine animate in accusative takes the genitive ending. Compare: Я
    бачу хліб (inanimate — no change) vs Я бачу брата (animate — changes).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Accusative summary — the full picture: | | Inanimate (що?) | Animate (кого?)
    | | Masculine | = nominative (хліб) | = genitive (брата) | | Feminine | -а → -у
    (каву) | -а → -у (маму) | | Neuter | = nominative (молоко) | (rare at A1) | Key
    verbs with animate accusative: бачити (to see), знати (to know), любити (to love),
    чекати (to wait for), шукати (to look for). Self-check: Я бачу ___ (мама → маму,
    брат → брата).'
vocabulary_hints:
  required:
  - бачити (to see)
  - знати (to know)
  - любити (to love)
  - чекати (to wait for)
  - шукати (to look for)
  - друг (friend, m)
  - подруга (friend, f)
  recommended:
  - сусід (neighbor, m)
  - колега (colleague, m/f)
  - викладач (lecturer, m)
  - вчитель (teacher, m)
  - лікар (doctor, m)
  - продавець (seller, m)
  - покупець (buyer, m)
activity_hints:
- type: fill-in
  focus: 'Я бачу ___ (nominative → accusative: мама → маму, брат → брата)'
  items:
  - Я бачу {маму|мама|мами}.
  - Я бачу {брата|брат|брату}.
  - Я знаю {Олену|Олена|Олени}.
  - Я знаю {друга|друг|другу}.
  - Я люблю {тата|тато|таті}.
  - Я чекаю {вчителя|вчитель|вчителю}.
  - Я шукаю {подругу|подруга|подруги}.
  - Я бачу {сусіда|сусід|сусіду}.
  - Я чекаю {лікаря|лікар|лікарю}.
  - Я знаю {сестру|сестра|сестри}.
- type: group-sort
  focus: 'Sort: animate (кого?) vs inanimate (що?) — changes vs stays same for masculine'
  groups:
  - name: Animate (кого?)
    items:
    - брата
    - маму
    - друга
    - лікаря
    - Олену
  - name: Inanimate (що?)
    items:
    - хліб
    - каву
    - воду
    - чай
    - борщ
- type: quiz
  focus: 'Choose correct: Я знаю (Олена / Олену / Олени)'
  items:
  - question: Я знаю ___.
    options:
    - Олену
    - Олена
    - Олени
  - question: Я бачу ___.
    options:
    - брата
    - брат
    - братом
  - question: Я люблю ___.
    options:
    - подругу
    - подруга
    - подруги
  - question: Я чекаю ___.
    options:
    - сусіда
    - сусід
    - сусідом
  - question: Я шукаю ___.
    options:
    - вчителя
    - вчитель
    - вчителю
  - question: Я знаю ___.
    options:
    - лікаря
    - лікар
    - лікарем
  - question: Я бачу ___.
    options:
    - колегу
    - колега
    - колеги
  - question: Я люблю ___.
    options:
    - тата
    - тато
    - татом
- type: fill-in
  focus: 'Complete: Я люблю ___, знаю ___, чекаю ___. (family/friends)'
  items:
  - — Кого ти {бачиш|бачити|бачить}?
  - — Я бачу {брата|брат|братом} і маму.
  - — Ти знаєш мого {друга|друг|другу} Тараса?
  - — Ні, я не {знаю|знає|знати} твого друга.
  - — А кого ти {чекаєш|чекати|чекає}?
  - — Я чекаю {лікаря|лікар|лікарем}.
connects_to:
- a1-041 (Checkpoint — Food and Shopping)
prerequisites:
- a1-039 (Shopping)
grammar:
- 'Accusative animate: feminine -а→-у (= inanimate), masculine = genitive'
- 'Animate vs inanimate distinction: кого? vs що?'
- 'Key pattern: masculine animate accusative = genitive (брат → брата)'
register: розмовний
references:
- title: ULP Season 1, Episode 33
  url: https://www.ukrainianlessons.com/episode33/
  notes: Accusative case — animate nouns.
- title: 'Grade 4 textbook: Знахідний відмінок (Заболотний)'
  notes: 'Ukrainian school approach: бачу кого? що? — animate accusative = genitive.'

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

We often talk about people as direct objects: **Я бачу маму**, **я знаю Олену**, **я шукаю друга**. In Ukrainian, that means using the accusative case for people.

«Це моя сім'я. Я дуже люблю маму і тата. У мене є брат. Ви знаєте мого брата? Він лікар. Я часто бачу брата вдома.»
> *This is my family. I love mom and dad very much. I have a brother. Do you know my brother? He is a doctor. I often see my brother at home.*

Let us look at a natural conversation. Two friends are looking at wedding photos and identifying people in them.

> **Наречена:** Дивись, це мої фотографії. *(Look, these are my photos.)*
> **Друг:** Дуже гарні! **Кого ти бачиш?** *(Very beautiful! Whom do you see?)*
> **Наречена:** **Я бачу маму і тата.** *(I see mom and dad.)*
> **Друг:** **А хто це?** *(And who is this?)*
> **Наречена:** **Це мій брат. Ти знаєш мого брата?** *(This is my brother. Do you know my brother?)*
> **Друг:** **Ні, я не знаю твого брата.** *(No, I do not know your brother.)*
> **Наречена:** **Ходімо, я тебе познайомлю!** *(Let's go, I will introduce you!)*

Notice how the nouns for family members change their endings in this dialogue. In the dictionary, these nouns are **мама**, **тато**, and **брат**. However, when they become the object of the verb **бачити** (to see) or **знати** (to know), their endings must change. The noun **мама** becomes **маму**, **тато** becomes **тата**, and **брат** becomes **брата**. We call this the animate accusative form, and it is specifically used for living beings like people and animals. This is a fundamental pattern you will use when talking about your family and friends in Ukrainian.

:::note
In Ukrainian, it is very common to refer to professionals by their titles rather than their names. Discussing a **лікар** (doctor) or **вчитель** (teacher) in the accusative case is a standard way to talk about the people who help you in your daily life.
:::

Now consider a different setting. Two colleagues at work are discussing people they know or are waiting for.

> **Олена:** Привіт! **Ти знаєш нашу вчительку?** *(Hi! Do you know our teacher?)*
> **Максим:** **Так, я знаю Олену Петрівну.** *(Yes, I know Olena Petrivna.)*
> **Олена:** **А нового лікаря?** *(And the new doctor?)*
> **Максим:** **Ні, я ще не знаю лікаря.** *(No, I do not know the doctor yet.)*
> **Олена:** **Він дуже добрий. Я чекаю його зараз.** *(He is very kind. I am waiting for him now.)*

In this workplace setting, we observe the same grammatical pattern applied to professions and names. The noun for a female teacher is **вчителька** (teacher, f), but here it changes to **вчительку**. The name **Олена** becomes **Олену**. The noun for a male doctor is **лікар** (doctor, m), but it transforms into **лікаря**. When the first colleague says she is waiting for him, she uses the verb **чекати** (to wait for). Just like seeing or knowing someone, waiting for a person requires this specific object form. You will use these animate accusative forms constantly when interacting with people around you, whether speaking to a **колега** (colleague, m/f), a **викладач** (lecturer, m), a **продавець** (seller, m), or a **покупець** (buyer, m) in a shop.

## Кого? (Whom?)

In the Ukrainian language, the accusative case draws a very strict boundary between inanimate objects and animate objects. Inanimate objects are lifeless things, such as food, furniture, or places. Animate objects are living beings, such as people and animals. This distinction is absolutely critical for masculine nouns. When a masculine inanimate noun is the direct object of a sentence, its ending does not change at all. For example, if you say «Я їм хліб» (I am eating bread), the masculine noun stays exactly the same as in the dictionary. However, when a masculine animate noun is the object, its ending must change. If you say «Я бачу брата» (I see a brother), the noun changes.

«Я йду в магазин. Я купую хліб і воду. Там я бачу сусіда. Я добре знаю сусіда. Ми часто говоримо.»
> *I am going to the store. I am buying bread and water. There I see a neighbor. I know the neighbor well. We often talk.*

To understand when to change the ending of a masculine noun, you must look at the question words that drive the sentence. In Ukrainian, the accusative case uses two different question words. For inanimate objects, the question word is **що?** (what?). When you ask **що?**, the inanimate masculine noun remains unchanged. For animate objects, the question word is **кого?** (whom?). This question word is the key trigger. When a verb answers the question **кого?**, it activates the animate rule. This explicitly dictates that masculine nouns will change their endings. This is why inanimate masculine nouns remain identical to their dictionary forms, while animate masculine nouns require a new grammatical suffix to show they are receiving the action.

:::tip
A helpful mnemonic for remembering the animate question word: **Кого?** (whom?) is used for a **колега** (colleague) or a **кіт** (cat), both of which are animate. The word **Що?** (what?) is used for inanimate things.
:::

In Ukrainian schools, children learn this grammar by memorizing the double question «Бачу кого? що?» (I see whom? what?). These two questions establish two separate patterns. The question **кого?** triggers the animate rule, which introduces a fascinating shortcut in Ukrainian grammar: for masculine animate nouns, the accusative form simply borrows the genitive case ending. You take the genitive form you already know and use it as the direct object.

*   **друг** → **друга**: «Я знаю друга.» (I know a friend.)
*   **тато** → **тата**: «Я люблю тата.» (I love dad.)
*   **лікар** → **лікаря**: «Я чекаю лікаря.» (I am waiting for the doctor.)
*   **сусід** (neighbor, m) → **сусіда**: «Я бачу сусіда.» (I see the neighbor.)

This borrowed ending is exactly why the animate versus inanimate distinction matters so much. It forces masculine nouns representing people to change their shape, ensuring that the listener clearly understands who is receiving the action.

<!-- INJECT_ACTIVITY: group-sort-animate-inanimate -->

## Знахідний відмінок — живе (Accusative Animate)

Let us first examine the rules for feminine animate nouns. There is excellent news for learners: feminine nouns follow the exact same accusative pattern regardless of whether they are animate or inanimate. Just like the inanimate word **кава** (coffee) becomes **каву**, the endings for feminine people change from **-а** to **-у** and from **-я** to **-ю**. There are no surprises or special rules here.

*   **мама** → **маму**: «Я бачу маму.» (I see mom.)
*   **сестра** (sister) → **сестру**: «Я знаю сестру.» (I know the sister.)
*   **Олена** → **Олену**: «Я чекаю Олену.» (I am waiting for Olena.)
*   **подруга** → **подругу**: «Я люблю подругу.» (I love the friend.)

«Я чекаю друга на вулиці. Мій друг — вчитель. Я бачу друга здалеку. Він теж чекає колегу. Ми бачимо колегу разом.»
> *I am waiting for a friend on the street. My friend is a teacher. I see the friend from afar. He is also waiting for a colleague. We see the colleague together.*

Now we must address the critical new rule for masculine animate nouns. As established earlier, the accusative form for masculine living beings is absolutely identical to the genitive form. Instead of remaining unchanged like inanimate objects, these masculine nouns take the **-а** or **-я** ending. Here are clear, everyday examples of this pattern in action:

*   **брат** → **брата**: «Я бачу брата.» (I see a brother.)
*   **друг** → **друга**: «Я шукаю друга.» (I am looking for a friend.)
*   **тато** → **тата**: «Я люблю тата.» (I love dad.)
*   **лікар** → **лікаря**: «Я чекаю лікаря.» (I am waiting for the doctor.)
*   **вчитель** (teacher, m) → **вчителя**: «Я знаю вчителя.» (I know the teacher.)
*   **сусід** → **сусіда**: «Я бачу сусіда.» (I see the neighbor.)

:::caution
English speakers often forget to change the endings of masculine names and professions because English does not do this. Always pause and ask yourself: "Is this a living person?" If the answer is yes, you must use the animate accusative form (the **-а** or **-я** ending) when they are the object of the sentence.
:::

To solidify this concept, let us summarize the masculine paradigm by contrasting the animate and inanimate forms side-by-side. Seeing them together makes the grammatical difference perfectly clear.

*   Inanimate (stays the same): «Я бачу стіл.» (I see a table.)
*   Animate (gets the **-а** ending): «Я бачу брата.» (I see a brother.)
*   Inanimate (stays the same): «Я бачу хліб.» (I see bread.)
*   Animate (gets the **-а** ending): «Я бачу сусіда.» (I see a neighbor.)

This is the key contrast to remember: inanimate masculine nouns stay the same, but animate masculine nouns take the genitive-shaped form.

<!-- INJECT_ACTIVITY: fill-in-accusative-forms -->
<!-- INJECT_ACTIVITY: quiz-choose-correct-accusative -->

## Підсумок — Summary

We can now construct a comprehensive summary of the accusative case for both animate and inanimate nouns. This chart presents the full picture of how word endings change depending on what you are talking about.

| Рід (Gender) | Inanimate (**що?**) | Animate (**кого?**) |
| :--- | :--- | :--- |
| Чоловічий (Masculine) | = nominative (**хліб**) | = genitive (**брата**) |
| Жіночий (Feminine) | **-а/-я** → **-у/-ю** | **-а/-я** → **-у/-ю** |
| Середній (Neuter) | = nominative (**молоко**) | (rare at A1) |

As the chart illustrates, the masculine inanimate noun answers the question **що?** and equals the nominative form. The masculine animate noun answers the question **кого?** and equals the genitive form. The feminine noun follows the usual accusative pattern shown here: **-а** → **-у** and **-я** → **-ю**, regardless of animacy. Neuter animate nouns exist but are quite rare at the A1 level.

«Це моя велика родина. Я дуже люблю дідуся і бабусю. Я часто бачу сестру. Сьогодні я чекаю брата і тата. Ми дуже любимо гостей.»
> *This is my large family. I love grandfather and grandmother very much. I often see my sister. Today I am waiting for my brother and dad. We love guests very much.*

There are several high-frequency verbs at the A1 level that frequently trigger this animate accusative case. When you use these verbs with people, you must apply the animate endings.

*   **бачити** (to see): «Я бачу викладача.» (I see the lecturer.)
*   **знати** (to know): «Я знаю студента.» (I know the student.)
*   **любити** (to love): «Я люблю тата.» (I love dad.)
*   **чекати** (to wait for): «Я чекаю лікаря.» (I am waiting for the doctor.)
*   **шукати** (to look for): «Я шукаю подругу.» (I am looking for a friend.)

Mastering these verbs will allow you to describe your interactions with the people around you accurately. Before moving to the exercises, perform a quick self-check to ensure you understand the core concepts.

*   **Q: How do you say "I see mom"?**
*   A: «Я бачу маму» (**мама** → **маму**).
*   **Q: How do you say "I see brother"?**
*   A: «Я бачу брата» (**брат** → **брата**).
*   **Q: What is the question word for people in the accusative?**
*   A: **Кого?**

These simple checks confirm that the core pattern is clear: **кого?** triggers animate forms such as **маму** and **брата**.

<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->
</generated_module_content>

**PIPELINE NOTE — Word count: 1734 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 108 words | Not found: 3 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Олена — NOT IN VESUM
  ✗ Олену — NOT IN VESUM
  ✗ Петрівну — NOT IN VESUM

All 108 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
