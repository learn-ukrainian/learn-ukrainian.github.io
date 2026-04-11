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
## Діало́ги (Dialogues)

We have spent recent modules learning how to buy food, order drinks, and talk about objects in our daily environment. The Ukrainian language treats objects in a specific way. However, our world is mostly filled with people. We interact with family members, meet friends, and speak to professionals. When we talk about people rather than objects, Ukrainian grammar shifts its focus. The rules change because the language makes a sharp distinction between a living person and an inanimate object. We must now learn how to name the people around us when they are the target of our actions.

Read this conversation between a bride and her friend at a wedding reception. They are showing wedding photos and identifying people. Pay close attention to the word endings for people.

> **Друг:** Кого ти ба́чиш? *(Who do you see?)*
> **Нарече́на:** Я ба́чу ма́му і та́та. *(I see mom and dad.)*
> **Друг:** А хто це? *(And who is this?)*
> **Наречена:** Це мій дя́дько. А це ті́тка. *(This is my uncle. And this is the aunt.)*
> **Друг:** Зна́єш Оле́ну? *(Do you know Olena?)*
> **Наречена:** Так. А це мій брат. Ти знаєш мого бра́та? *(Yes. And this is my brother. Do you know my brother?)*
> **Друг:** Ні, я не зна́ю твого́ брата. *(No, I do not know your brother.)*
> **Наречена:** Ході́мо! Я тебе́ познайо́млю! *(Let's go! I will introduce you!)*
> **Друг:** Ось наречена і нарече́ний. *(Here is the bride and the groom.)*

Notice the Accusative animate forms: **маму** (feminine), **тата** (masculine), and **брата** (masculine). When the friend asks the question **Кого ти бачиш?** (Who do you see?), the bride answers with **Я бачу маму і тата** (I see mom and dad). The original dictionary words are **ма́ма** (mom) and **та́то** (dad). In previous modules, we saw that masculine objects did not change their endings. A word like **брат** (brother) is masculine. Yet, the bride asks **Ти знаєш мого брата?** (Do you know my brother?). The word **брат** changes to **брата**. The names of people change their endings because they are living beings.

This rule applies to all people around you, including professionals and colleagues. Read this short exchange between two colleagues at a school.

> **Коле́га 1:** Ти знаєш на́шу вчи́тельку? *(Do you know our teacher?)*
> **Колега 2:** Так, я знаю Олену Петрі́вну. *(Yes, I know Olena Petrivna.)*
> **Колега 1:** А ново́го лі́каря? *(And the new doctor?)*
> **Колега 2:** Ні, я ще не знаю лікаря. *(No, I do not know the doctor yet.)*
> **Колега 1:** Він ду́же до́брий. Я чека́ю йо́го за́раз. *(He is very kind. I am waiting for him right now.)*

The word for a female teacher is **вчи́телька**. It changes to **вчительку**. The female name **Оле́на Петрі́вна** becomes **Олену Петрівну**. The masculine word for a doctor is **лі́кар**. It changes to **лікаря**. These animate accusative patterns occur constantly with the people around you.

## Кого? (Whom?)

The Ukrainian language categorizes nouns into two groups based on whether they are living or not. We call these groups animate and inanimate. The Accusative case is the grammatical form we use for the direct object of an action. An object receives the action. Animate nouns represent people or animals. Inanimate nouns represent objects, concepts, or places. We learned the Accusative case for inanimate objects in Module 37.

You already know how to talk about food. You say **Я їм хліб** (I eat what? bread). For inanimate nouns, there is no change for the masculine. The masculine objects like **хліб** (bread) kept their dictionary form. Contrast those food items with a person. When you see your brother, you say **Я бачу брата** (I see whom? the brother). For animate nouns, the masculine changes! The masculine person changes, while the masculine object stays exactly the same.

To know which rule to follow, we rely on question words. The question word is the key. The word **що?** (what?) indicates inanimate things, and the masculine stays the same. When you hold an apple, you ask **Що це?** (What is this?). The word **кого?** (whom?) indicates animate people or animals, and the masculine changes. When you see your colleague, the correct question is **Кого ти бачиш?** (Whom do you see?). Your choice of question word dictates the ending of the masculine noun.

:::note
**The Grammar Question Test**
Ukrainian grammar is deeply connected to question words. When you learn a new grammatical case, memorize its question word. Asking **кого?** (whom?) instantly reminds your brain to apply the animate rule.
:::

Ukrainian children learn this logic early in Grade 4. Their teachers use a specific mnemonic device based on the school approach. The children memorize the phrase: **Бачу кого? що?** (I see whom? what?). They ask both questions together. By asking these two questions simultaneously, students learn to identify the two patterns. If the noun is an object, the answer to **що?** (what?) confirms there is no change. The question **кого?** triggers the animate rule. The masculine animate in the Accusative case equals the Genitive form.

We have a reliable pattern for these masculine people. For a masculine person, we use the exact same ending we will later use to show possession. This is the key distinction for L2 learners. The object receives the action, and the ending marks the object as a living person. Observe how the words change:

*   **брат** → **брата** (brother)
*   **друг** → **дру́га** (friend)
*   **тато** → **тата** (dad)
*   **лікар** → **лікаря** (doctor)

This is why animate accusative matters — it changes masculine nouns.

<!-- INJECT_ACTIVITY: sort-animate-inanimate -->

## Знахі́дний відмі́нок — живе́ (Accusative Animate)

Feminine animate nouns follow the same simple rule as inanimate objects. The ending **-а** changes to **-у**. The ending **-я** changes to **-ю**. There is no surprise here — it uses the same ending as Module 37, where **ка́ва** changes to **ка́ву**. This exact pattern applies to the women and girls in your life. The feminine animate is identical to the feminine inanimate.

*   **мама** → **маму** (mom)
*   **сестра́** → **сестру́** (sister)
*   **Олена** → **Олену** (Olena)
*   **по́друга** → **по́другу** (female friend)
*   **Я бачу маму.** (I see mom.)
*   **Я знаю сестру.** (I know the sister.)
*   **Я чекаю Олену.** (I wait for Olena.)
*   **Я люблю́ подругу.** (I love the female friend.)

Masculine animate nouns introduce THE new rule. The Accusative case equals the Genitive case. The pattern dictates that masculine animate nouns in the Accusative take the genitive ending. Let us observe the pattern with high-frequency family words and social nouns. The noun **брат** (brother) becomes **брата**. The word **тато** (dad) is masculine, even though it ends in **-о**. It drops the **-о** and takes the **-а** ending to become **тата**. The noun **сусі́д** (male neighbor) becomes **сусі́да**. Compare an inanimate object with an animate person. You say **Я бачу хліб** (I see bread). This is inanimate — no change. But you say **Я бачу брата** (I see the brother). This is animate — it changes. The living brother requires the change.

*   **брат** → **брата** (brother)
*   **друг** → **друга** (male friend)
*   **тато** → **тата** (dad)
*   **сусід** → **сусіда** (male neighbor)
*   **Я бачу брата.** (I see the brother.)
*   **Я знаю друга.** (I know the friend.)
*   **Я люблю тата.** (I love dad.)
*   **Я бачу сусіда.** (I see the neighbor.)

:::caution
**Don't Forget the Men!**
English speakers easily remember to change feminine words like **мама** to **маму**. However, learners frequently forget to change masculine words because masculine objects like **телефо́н** do not change. Always pause and ask: "Is this masculine noun a living person?" If yes, add **-а** or **-я**.
:::

Some masculine nouns end in a soft consonant or the suffix **-ар**. These words require a soft vowel ending. They take the **-я** ending instead of the hard **-а**. Many professions fall into this category.

*   **лікар** → **лікаря** (doctor)
*   **вчи́тель** → **вчи́теля** (male teacher)
*   **продаве́ць** → **продавця́** (male seller)
*   **колега** → **коле́гу** (colleague)
*   **Я чекаю лікаря.** (I wait for the doctor.)
*   **Я знаю вчителя.** (I know the teacher.)
*   **Я бачу продавця.** (I see the seller.)
*   **Я знаю колегу.** (I know the colleague.)

<!-- INJECT_ACTIVITY: fill-in-animate-transform -->

## Підсумок — Summary

The complete picture of the Accusative case organizes these rules into a clear visual breakdown.  This Accusative summary provides the full picture.

| | Inanimate (що?) | Animate (кого?) |
| :--- | :--- | :--- |
| **Masculine** | = nominative (**хліб**) | = genitive (**брата**) |
| **Feminine** | **-а** → **-у** (**каву**) | **-а** → **-у** (**маму**) |
| **Neuter** | = nominative (**молоко́**) | (rare at A1) |

The feminine nouns always change the final vowel. They change **-а** to **-у** and **-я** to **-ю**. The masculine nouns remain unchanged for inanimate objects. They adopt the genitive ending for living people. The neuter nouns do not change.

Certain verbs appear constantly in social interactions. These key verbs with animate accusative require the change to identify the target of the action. You must memorize these words.

*   **ба́чити** (to see)
*   **зна́ти** (to know)
*   **люби́ти** (to love)
*   **чека́ти** (to wait for)
*   **шука́ти** (to look for)

These verbs connect you to the people around you. You use them daily. Note that the verb **чекати** (to wait) often uses the preposition **на** in natural speech. At the A1 level, we focus on the direct object pattern. We say **Я чекаю маму** (I wait for mom). We say **Я шука́ю сусіда** (I look for the neighbor).

You can practice these patterns with simple questions and answers. Read the questions and notice the noun endings in the responses.

*   **Кого ти лю́биш?** (Whom do you love?)
    **Я люблю маму і тата.** (I love mom and dad.)
*   **Кого ти чека́єш?** (Whom are you waiting for?)
    **Я чекаю друга.** (I am waiting for a friend.)
*   **Кого ти знаєш у шко́лі?** (Whom do you know at school?)
    **Я знаю вчителя.** (I know the teacher.)
*   **Кого ти бачиш?** (Whom do you see?)
    **Я бачу покупця́.** (I see the buyer.)
*   **Кого ти шука́єш?** (Whom are you looking for?)
    **Я шукаю викладача́.** (I am looking for the lecturer.)

:::tip
**Colleagues and Professions**
The word **колега** (colleague) looks feminine but can describe a man or a woman. Because it ends in **-а**, you always change it to **колегу**, regardless of the person's gender.
:::

Check your understanding of the pattern. Let us complete this Self-check: **Я бачу ___**. For the word **мама**, the correct form is **маму**. For the word **брат**, the correct form is **брата**. Remember the core rule. If the noun is a person and it is masculine, you must add the ending. The action transfers directly to the living person.

<!-- INJECT_ACTIVITY: quiz-ending-choice -->
<!-- INJECT_ACTIVITY: fill-in-dialogue-logic -->
</generated_module_content>

**PIPELINE NOTE — Word count: 1681 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 70 words | Not found: 27 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Діало — NOT IN VESUM
  ✗ Знахі — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олену — NOT IN VESUM
  ✗ Петрі — NOT IN VESUM
  ✗ Петрівну — NOT IN VESUM
  ✗ биш — NOT IN VESUM
  ✗ вна — NOT IN VESUM
  ✗ вну — NOT IN VESUM
  ✗ відмі — NOT IN VESUM
  ✗ дний — NOT IN VESUM
  ✗ дру — NOT IN VESUM
  ✗ дько — NOT IN VESUM
  ✗ каря — NOT IN VESUM
  ✗ млю — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ познайо — NOT IN VESUM
  ✗ продаве — NOT IN VESUM
  ✗ телефо — NOT IN VESUM
  ✗ тель — NOT IN VESUM
  ✗ телька — NOT IN VESUM
  ✗ тельку — NOT IN VESUM
  ✗ тка — NOT IN VESUM
  ✗ чити — NOT IN VESUM
  ✗ чиш — NOT IN VESUM
  ✗ шко — NOT IN VESUM

All 70 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
