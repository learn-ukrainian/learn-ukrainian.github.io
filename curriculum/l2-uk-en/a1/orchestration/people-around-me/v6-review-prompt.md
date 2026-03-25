# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 40: People Around Me (A1, A1.6 [Food and Shopping])
**Writer:** Gemini Pro
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

When we walk down the street, visit a new office, or attend a family gathering, our attention naturally shifts from the objects around us to the people. In previous lessons, we learned how to interact with things—how to order food, buy items in a store, and describe what we see. But human interaction requires us to talk about the people we know, the people we see, and the people we are waiting for.

Let us observe a conversation between two friends at a crowded event. Notice how the endings of the words for people change when they are the object of the action.

<div class="dialogue">


**Анна:** Кого ти бачиш? *(Whom do you see?)*


**Марко:** Я бачу маму і тата. *(I see mom and dad.)*


**Анна:** А хто це? *(And who is this?)*


**Марко:** Це мій брат. Ти знаєш мого брата? *(This is my brother. Do you know my brother?)*


**Анна:** Ні, я не знаю твого брата. *(No, I do not know your brother.)*


**Марко:** Ходімо, я тебе познайомлю! *(Let's go, I will introduce you!)*


</div>


In this brief exchange, Marko does not simply say that he sees **мама** (mom) and **тато** (dad). Because he is directing his action (seeing) at them, the words transform into **маму** and **тата**. Similarly, when discussing his brother, the word **брат** (brother) becomes **брата**.

Now, let us look at a professional context. Two colleagues are discussing the staff at their workplace.

<div class="dialogue">


**Максим:** Ти знаєш нашу вчительку? *(Do you know our teacher?)*


**Ірина:** Так, я знаю Олену Петрівну. *(Yes, I know Olena Petrivna.)*


**Максим:** А нового лікаря? *(And the new doctor?)*


**Ірина:** Ні, я ще не знаю лікаря. *(No, I do not know the doctor yet.)*


**Максим:** Він дуже добрий. Я чекаю його зараз. *(He is very kind. I am waiting for him now.)*


</div>


Here, we see the verb **знати** (to know) in action. Iryna knows **Олена Петрівна** (Olena Petrivna), so the name changes to **Олену Петрівну**. When asking about the doctor, the word **лікар** (doctor, m) transforms into **лікаря**. 

In Ukrainian culture, addressing a teacher or a senior professional often involves using their first name and patronymic (a name derived from their father's name), such as **Олена Петрівна**. Notice how both parts of the name change their endings to reflect the grammatical case. The language is highly precise: the endings instantly tell the listener who is performing the action and who is receiving it. 

We also see the verbs **бачити** (to see) and **чекати** (to wait for). All of these verbs require the object to be in the accusative case, which we will explore deeply in the next sections.

:::fill-in
title: "Complete the dialogue"
---
- sentence: "— Кого ти {бачиш|бачити|бачить}?"
  answer: "бачиш"
- sentence: "— Я бачу {брата|брат|братом} і маму."
  answer: "брата"
- sentence: "— Ти знаєш мого {друга|друг|другу} Тараса?"
  answer: "друга"
- sentence: "— Ні, я не {знаю|знає|знати} твого друга."
  answer: "знаю"
- sentence: "— А кого ти {чекаєш|чекати|чекає}?"
  answer: "чекаєш"
- sentence: "— Я чекаю {лікаря|лікар|лікарем}."
  answer: "лікаря"
:::

## Кого? (Whom?)

To truly think in Ukrainian, we must understand how the language categorizes the world. English grammar generally treats a loaf of bread and a brother the same way when they are the object of a sentence. You say "I see the bread" and "I see the brother." The structure is identical.

Ukrainian grammar makes a fundamental, philosophical distinction between the living and the non-living—between animate objects (people and animals) and inanimate objects (things and concepts). 

When Ukrainian children learn grammar in the fourth grade, teachers introduce the accusative case by asking them to memorize two question words together: **«Бачу кого? що?»** (I see whom? what?). These two questions represent two different grammatical patterns.

The question word **що?** (what?) is used for inanimate objects. When dealing with masculine inanimate nouns, the accusative case is identical to the nominative (dictionary) form. There is no change.
*   Я їм **хліб**. *(I am eating bread.)* — The word **хліб** stays the same.
*   Я бачу **парк**. *(I see a park.)* — The word **парк** stays the same.
*   Я купую **чай**. *(I am buying tea.)* — The word **чай** stays the same.

The question word **кого?** (whom?) is used for animate objects. This question word triggers the animate rule, which forces masculine nouns to change their endings. 
*   Я бачу **брата**. *(I see a brother.)* — The word **брат** changes to **брата**.
*   Я знаю **лікаря**. *(I know a doctor.)* — The word **лікар** changes to **лікаря**.
*   Я чекаю **сусіда**. *(I am waiting for a neighbor.)* — The word **сусід** changes to **сусіда**.

This is why the animate distinction matters so much. If you say "Я бачу брат," a Ukrainian speaker's ear will immediately catch the error because the grammatical signal for "a living person receiving the action" is missing. The ending **-а** or **-я** for masculine animate nouns is actually borrowed from the genitive case. The Ukrainian language recycles the genitive form to serve as the accusative form for living masculine beings.

Let us compare the two patterns directly to see the contrast:
*   Inanimate: Я бачу **магазин**. *(I see a store.)*
*   Animate: Я бачу **продавця**. *(I see a seller.)*
*   Inanimate: Я люблю **борщ**. *(I love borsch.)*
*   Animate: Я люблю **тата**. *(I love dad.)*

Understanding whether a noun answers the question **кого?** or **що?** is the key to mastering this grammatical structure. 

:::group-sort
title: "Sort: animate (кого?) vs inanimate (що?)"
---
groups:
  - name: "Animate (кого?)"
    items: ["брата", "маму", "друга", "лікаря", "Олену"]
  - name: "Inanimate (що?)"
    items: ["хліб", "каву", "воду", "чай", "борщ"]
:::

## Знахідний відмінок — живе (Accusative Animate)

Now that we understand the philosophy behind the animate and inanimate divide, let us look at the exact mechanical changes that happen to words in the **знахідний відмінок** (accusative case). We will break this down by gender.

### Feminine Animate Nouns

For feminine nouns, the rule is wonderfully simple: animate nouns behave exactly like inanimate nouns. There is no special "animate" rule for feminine words. You simply apply the rule you already learned for objects like **кава** (coffee) becoming **каву** and **піца** (pizza) becoming **піцу**.

The ending **-а** changes to **-у**, and the ending **-я** changes to **-ю**.

*   **мама** (mom) → **маму**
    *   Я бачу **маму**. *(I see mom.)*
*   **сестра** (sister) → **сестру**
    *   Я знаю **сестру**. *(I know the sister.)*
*   **Олена** (Olena) → **Олену**
    *   Я чекаю **Олену**. *(I am waiting for Olena.)*
*   **подруга** (female friend) → **подругу**
    *   Я люблю **подругу**. *(I love my female friend.)*

This means that whether you are buying water (**воду**) or waiting for your female friend (**подругу**), the phonetic transformation of the word is identical. 

### Masculine Animate Nouns

Masculine animate nouns are where the true shift happens. The core rule is: **for masculine animate nouns, the accusative case looks exactly like the genitive case.** 

Most masculine nouns end in a hard consonant. To form the animate accusative, you add **-а**.
*   **брат** (brother) → **брата**
    *   Я бачу **брата**. *(I see a brother.)*
*   **друг** (male friend) → **друга**
    *   Я знаю **друга**. *(I know a male friend.)*
*   **сусід** (male neighbor) → **сусіда**
    *   Я бачу **сусіда**. *(I see a male neighbor.)*

Other masculine nouns take the ending **-я** (or **-ця** for nouns ending in **-ець**). This group includes nouns ending in **-ь**, **-р**, and **-ець**.

Nouns ending in **-ь** drop the soft sign and add **-я**:
*   **вчитель** (male teacher) → **вчителя**
    *   Я знаю **вчителя**. *(I know a male teacher.)*

Nouns ending in **-р** add **-я**:
*   **лікар** (male doctor) → **лікаря**
    *   Я чекаю **лікаря**. *(I am waiting for a male doctor.)*

Nouns ending in **-ець** change to **-ця**:
*   **продавець** (male seller) → **продавця**
    *   Я шукаю **продавця**. *(I am looking for a male seller.)*
*   **покупець** (male buyer) → **покупця**
    *   Я бачу **покупця**. *(I see a male buyer.)*

There is one important exception to note regarding masculine family words. The word **тато** (dad) is masculine, but it ends in **-о**. Because it ends in a vowel, it follows the same ending pattern as feminine **-а** nouns. Therefore, **тато** changes to **тата**.
*   Я люблю **тата**. *(I love dad.)*

Similarly, the word **колега** (colleague) can refer to a man or a woman, but grammatically it ends in **-а**, so it behaves exactly like a feminine noun.
*   Я бачу **колегу**. *(I see a colleague.)*

:::quiz
title: "Choose the correct ending"
---
- q: "Я знаю ___."
  o: ["Олену", "Олена", "Олени"]
  a: 0
- q: "Я бачу ___."
  o: ["брата", "брат", "братом"]
  a: 0
- q: "Я люблю ___."
  o: ["подругу", "подруга", "подруги"]
  a: 0
- q: "Я чекаю ___."
  o: ["сусіда", "сусід", "сусідом"]
  a: 0
- q: "Я шукаю ___."
  o: ["вчителя", "вчитель", "вчителю"]
  a: 0
- q: "Я знаю ___."
  o: ["лікаря", "лікар", "лікарем"]
  a: 0
- q: "Я бачу ___."
  o: ["колегу", "колега", "колеги"]
  a: 0
- q: "Я люблю ___."
  o: ["тата", "тато", "татом"]
  a: 0
:::

## Підсумок — Summary

To consolidate our knowledge, we must look at the full picture of the **знахідний відмінок** (accusative case). The table below illustrates the critical differences between inanimate objects (answering the question **що?**) and animate objects (answering the question **кого?**).

| Gender | Inanimate (**що?**) | Animate (**кого?**) |
| :--- | :--- | :--- |
| **Masculine** | = nominative (**хліб**) | = genitive (**брата**) |
| **Feminine** | -а → -у (**каву**) | -а → -у (**маму**) |
| **Neuter** | = nominative (**молоко**) | (rare at A1 level) |

Notice how the feminine column is entirely consistent regardless of whether the noun is living or non-living. The masculine column is where you must pause and ask yourself: "Is this a person or a thing?"

To practice this case, you will frequently use six key verbs that govern human interaction and observation. These are the most common verbs that trigger the animate accusative rule:
*   **бачити** (to see) — Я бачу **друга**. *(I see a male friend.)*
*   **знати** (to know) — Я знаю **сестру**. *(I know a sister.)*
*   **любити** (to love) — Я люблю **тата**. *(I love dad.)*
*   **чекати** (to wait for) — Я чекаю **лікаря**. *(I am waiting for a doctor.)*
*   **шукати** (to look for) — Я шукаю **вчителя**. *(I am looking for a teacher.)*
*   **знати** (to know) — Я знаю **викладача**. *(I know a lecturer.)*

When you speak, try to group the verb and the noun together as one fluid chunk. Do not think of them as separate words; think of **бачу брата** as a single concept. 

:::fill-in
title: "Convert Nominative to Accusative Animate"
---
- sentence: "Я бачу {маму|мама|мами}."
  answer: "маму"
- sentence: "Я бачу {брата|брат|брату}."
  answer: "брата"
- sentence: "Я знаю {Олену|Олена|Олени}."
  answer: "Олену"
- sentence: "Я знаю {друга|друг|другу}."
  answer: "друга"
- sentence: "Я люблю {тата|тато|таті}."
  answer: "тата"
- sentence: "Я чекаю {вчителя|вчитель|вчителю}."
  answer: "вчителя"
- sentence: "Я шукаю {подругу|подруга|подруги}."
  answer: "подругу"
- sentence: "Я бачу {сусіда|сусід|сусіду}."
  answer: "сусіда"
- sentence: "Я чекаю {лікаря|лікар|лікарю}."
  answer: "лікаря"
- sentence: "Я знаю {сестру|сестра|сестри}."
  answer: "сестру"
:::

**Deterministic word count: 1573 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

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

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
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

Verified: 94 words | Not found: 9 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ірина — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олени — NOT IN VESUM
  ✗ Олену — NOT IN VESUM
  ✗ Петрівна — NOT IN VESUM
  ✗ Петрівну — NOT IN VESUM
  ✗ Тараса — NOT IN VESUM
  ✗ ець — NOT IN VESUM

All 94 other words are confirmed to exist in VESUM.

</vesum_verification>