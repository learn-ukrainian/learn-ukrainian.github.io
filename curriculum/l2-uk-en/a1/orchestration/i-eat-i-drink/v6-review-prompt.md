<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 37: I Eat, I Drink (A1, A1.6 [Food and Shopping])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-037
level: A1
sequence: 37
slug: i-eat-i-drink
version: '1.2'
title: I Eat, I Drink
subtitle: Я їм хліб, п'ю каву — accusative for what you eat and drink
focus: grammar
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Conjugate їсти and пити in present tense
- Use accusative case for inanimate direct objects (Я їм хліб, п'ю каву)
- Recognize feminine accusative ending change (-а → -у): кава → каву, вода → воду
- Describe eating and drinking habits using accusative
dialogue_situations:
- setting: 'Lunch break at work — unpacking lunch boxes: Я їм бутерброд (m, sandwich)
    і п''ю чай (m, tea). А ти? Я їм салат (m) і п''ю каву (f, coffee). Also: яблуко
    (n), банан (m), вода (f), сік (m, juice).'
  speakers:
  - Колега 1
  - Колега 2
  motivation: 'Accusative: бутерброд(m), салат(m), каву(f→acc), яблуко(n), чай(m)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Breakfast conversation: — Що ти їш на сніданок? — Я їм кашу і п''ю
    каву. — А Олена? — Вона їсть хліб з маслом і п''є чай. — А діти? — Вони їдять
    яйця і п''ють молоко. Full conjugation of їсти and пити in natural context.'
  - 'Dialogue 2 — At lunch: — Що ви їсте на обід? — Ми їмо суп і салат. — А що п''єте?
    — Ми п''ємо воду або сік. — Я теж хочу суп. — Добре, замовляй! Review of їсти/пити
    with plural subjects.'
- section: Їсти і пити (To Eat and To Drink)
  words: 300
  points:
  - 'Conjugation of їсти (irregular — NOT Group I or II): я їм, ти їси, він/вона їсть,
    ми їмо, ви їсте, вони їдять. Conjugation of пити (Group I): я п''ю, ти п''єш,
    він/вона п''є, ми п''ємо, ви п''єте, вони п''ють. Both are essential daily verbs
    — high frequency.'
  - 'Ukrainian school approach (Grade 4 — знахідний відмінок): ''Бачу що? кого?''
    — the accusative answers ''what do I see/eat/drink?'' Я їм (що?) хліб. Я п''ю
    (що?) каву. The question що? triggers accusative for inanimate objects.'
- section: Знахідний відмінок — неживе (Accusative Inanimate)
  words: 300
  points:
  - 'Accusative for inanimate nouns — what changes: Masculine inanimate: NO CHANGE
    (= nominative). хліб → хліб (Я їм хліб), суп → суп (Я їм суп), сік → сік (Я п''ю
    сік). Neuter: NO CHANGE (= nominative). молоко → молоко (Я п''ю молоко), яйце
    → яйце (Я їм яйце).'
  - 'Feminine -а → -у (THE key change at A1): кава → каву (Я п''ю каву), вода → воду
    (Я п''ю воду), риба → рибу (Я їм рибу), каша → кашу (Я їм кашу), картопля → картоплю
    (Я їм картоплю). Pattern: feminine nouns ending in -а change to -у, ending in
    -я change to -ю. This is the ONLY accusative change learners need now.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Accusative inanimate summary: Masculine/Neuter: no change (хліб, молоко stay
    the same). Feminine -а → -у, -я → -ю (кава → каву, картопля → картоплю). Test:
    Я їм ___ (риба → рибу). Я п''ю ___ (вода → воду). Self-check: Say 3 things you
    eat and 3 things you drink today. Use the correct accusative form for each.'
vocabulary_hints:
  required:
  - їсти (to eat — irregular)
  - пити (to drink)
  - їм (I eat)
  - п'ю (I drink)
  - каву (coffee — accusative)
  - воду (water — accusative)
  - рибу (fish — accusative)
  recommended:
  - кашу (porridge — accusative)
  - картоплю (potato — accusative)
  - сметану (sour cream — accusative)
  - їсть (he/she eats)
  - п'є (he/she drinks)
  - їдять (they eat)
  - п'ють (they drink)
activity_hints:
- type: fill-in
  focus: Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter
    (no change)
  items: 8
  blanks:
  - Я їм (риба) {рибу}.
  - Вона п'є (вода) {воду}.
  - Він їсть (хліб) {хліб}.
  - Ми п'ємо (молоко) {молоко}.
  - Вони їдять (каша) {кашу}.
  - Ти п'єш (кава) {каву}.
  - Я їм (суп) {суп}.
  - Вона їсть (картопля) {картоплю}.
- type: quiz
  focus: Select the correct accusative form to complete the sentence
  items: 6
  questions:
  - Я п'ю... (каву / кава / кави)
  - Він їсть... (рибу / риба / рибі)
  - Ми п'ємо... (сік / соку / соком)
  - Вона їсть... (м'ясо / м'ясу / м'яса)
  - Вони п'ють... (воду / вода / воді)
  - Ти їш... (кашу / каша / каші)
- type: fill-in
  focus: Conjugate the verbs їсти (irregular) and пити (Group I)
  items: 8
  blanks:
  - Я {їм} суп.
  - Ми {п'ємо} чай.
  - Вона {їсть} хліб.
  - Вони {п'ють} воду.
  - Ти {їси} рибу?
  - Ви {п'єте} каву?
  - Він {п'є} сік.
  - Вони {їдять} кашу.
- type: group-sort
  focus: Sort nouns based on how they change in the accusative case (inanimate)
  items: 8
  groups:
  - name: Змінюється (-у/-ю)
    items:
    - кава
    - вода
    - риба
    - каша
  - name: Не змінюється (як у називному)
    items:
    - хліб
    - сік
    - молоко
    - м'ясо
connects_to:
- a1-038 (At the Cafe)
prerequisites:
- a1-036 (Food and Drink)
grammar:
- 'Accusative inanimate: masculine/neuter = nominative, feminine -а→-у, -я→-ю'
- Conjugation of їсти (irregular) and пити (Group I)
- Question що? as accusative trigger for inanimate
register: розмовний
references:
- title: ULP Season 1, Episode 32
  url: https://www.ukrainianlessons.com/episode32/
  notes: Accusative case introduction — inanimate objects.
- title: 'Grade 4 textbook: Знахідний відмінок (Заболотний)'
  notes: 'Ukrainian school approach: бачу що? кого?'

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Meals give you immediate practice with food vocabulary and the verbs **їсти** and **пити**. Start with the dialogue and notice what each person eats and drinks.

> **Оксана і Тарас працюють разом. Зараз ранок.**
> *Oksana and Taras work together. It is morning now.*
> **Оксана:** Тарасе, що ти зазвичай їш на сніданок?
> *Oksana: Taras, what do you usually eat for breakfast?*
> **Тарас:** Я їм кашу і п'ю каву. А ти?
> *Taras: I eat porridge and drink coffee. And you?*
> **Оксана:** Я теж! А Олена?
> *Oksana: Me too! And Olena?*
> **Тарас:** Вона їсть хліб з маслом і п'є чай.
> *Taras: She eats bread with butter and drinks tea.*
> **Оксана:** Зрозуміло. А діти?
> *Oksana: Understood. And the children?*
> **Тарас:** Вони їдять яйця і п'ють молоко.
> *Taras: They eat eggs and drink milk.*

Notice the forms in context: **я їм / п'ю**, **вона їсть / п'є**, **вони їдять / п'ють**. The next dialogue adds the plural forms **ми їмо** and **ми п'ємо** at lunch.

> **Обідня перерва в офісі.**
> *Lunch break at the office.*
> **Оксана:** Що ви їсте на обід сьогодні?
> *Oksana: What are you eating for lunch today?*
> **Тарас і Олена:** Ми їмо суп і салат.
> *Taras and Olena: We are eating soup and salad.*
> **Оксана:** Смачно! А що п'єте?
> *Oksana: Tasty! And what are you drinking?*
> **Тарас:** Ми п'ємо воду або сік.
> *Taras: We are drinking water or juice.*
> **Оксана:** Я теж хочу суп.
> *Oksana: I also want soup.*
> **Олена:** Добре, замовляй!
> *Olena: Good, order it!*

This second dialogue reviews the verbs with plural subjects like **ми** (we) and introduces a very useful transactional verb: **хотіти** (to want). Oksana says **я хочу** (I want) to express her desire for soup. You will use these phrases constantly whether you are unpacking lunch boxes with colleagues or ordering at a cafe.

## Їсти і пити (To Eat and To Drink)

Two high-frequency verbs drive this module: **їсти** and **пити**. Memorize **їсти** as an irregular verb; **пити** follows the present-tense pattern shown below.

| Займенник (Pronoun) | Дієслово (Verb) | Переклад (Translation) |
| :--- | :--- | :--- |
| я | **їм** | I eat |
| ти | **їси** | you eat (informal) |
| він / вона / воно | **їсть** | he / she / it eats |
| ми | **їмо** | we eat |
| ви | **їсте** | you eat (formal/plural) |
| вони | **їдять** | they eat |

:::caution
A very common mistake for learners is confusing the first-person and third-person forms. Remember that **я їм** means "I eat," while **він їсть** means "he eats." Do not mix them up!
:::

These sentences demonstrate the forms in simple contexts:
*   **Я їм смачний суп.** (I am eating a tasty soup.)
*   **Ти їси хліб.** (You are eating bread.)
*   **Вона їсть м'ясо.** (She is eating meat.)
*   **Ми їмо салат.** (We are eating a salad.)
*   **Ви їсте борщ.** (You are eating borscht.)
*   **Вони їдять кашу.** (They are eating porridge.)

The verb **пити** (to drink) is a Group I verb, but its stem changes dramatically from the infinitive form to the present tense forms.

| Займенник (Pronoun) | Дієслово (Verb) | Переклад (Translation) |
| :--- | :--- | :--- |
| я | **п'ю** | I drink |
| ти | **п'єш** | you drink (informal) |
| він / вона / воно | **п'є** | he / she / it drinks |
| ми | **п'ємо** | we drink |
| ви | **п'єте** | you drink (formal/plural) |
| вони | **п'ють** | they drink |

Notice the apostrophe in **п'ю** and **п'є**. It shows that the consonant stays hard and the following **ю / є** keeps its **й**-sound.

*   **Я п'ю гарячий чай.** (I am drinking hot tea.)
*   **Ти п'єш каву.** (You are drinking coffee.)
*   **Він п'є молоко.** (He is drinking milk.)
*   **Ми п'ємо воду.** (We are drinking water.)
*   **Ви п'єте холодний сік.** (You are drinking cold juice.)
*   **Вони п'ють воду.** (They are drinking water.)

> **Ми часто їмо разом. Я їм рибу, а мій друг їсть м'ясо. Ми п'ємо воду.**
> *We often eat together. I eat fish, and my friend eats meat. We drink water.*

<!-- INJECT_ACTIVITY: fill-in-conjugation -->

## Знахідний відмінок — неживе (Accusative Inanimate)

In Ukrainian, the direct object after **їсти** and **пити** takes the accusative. A school-style way to check it is **Бачу що? кого?**; this matches the Grade 4 textbook approach noted in the plan and the beginner treatment in ULP Season 1, Episode 32.

For Masculine and Neuter inanimate nouns, the rule is remarkably simple: they do not change at all. Their Accusative form is exactly the same as their Nominative (dictionary) form.

These examples show the stability of masculine and neuter nouns:
*   **хліб** (bread, masculine) → **Я їм хліб.** (I eat bread.)
*   **сік** (juice, masculine) → **Я п'ю сік.** (I drink juice.)
*   **суп** (soup, masculine) → **Він їсть суп.** (He eats soup.)
*   **молоко** (milk, neuter) → **Ми п'ємо молоко.** (We drink milk.)
*   **яйце** (egg, neuter) → **Вони їдять яйце.** (They are eating an egg.)
*   **м'ясо** (meat, neuter) → **Вона їсть м'ясо.** (She is eating meat.)

So masculine and neuter food nouns stay in the dictionary form. The key A1 change is feminine **-а → -у** and **-я → -ю**:
*   **кава** (coffee) → **каву**: **Я п'ю каву.** (I drink coffee.)
*   **вода** (water) → **воду**: **Він п'є воду.** (He drinks water.)
*   **риба** (fish) → **рибу**: **Ми їмо рибу.** (We eat fish.)
*   **каша** (porridge) → **кашу**: **Ти їси кашу.** (You are eating porridge.)
*   **картопля** (potato) → **картоплю**: **Я їм картоплю.** (I am eating potatoes.)
*   **сметана** (sour cream) → **сметану**: **Вона любить сметану.** (She loves sour cream.)

:::tip
This ending shift applies to any verb that takes a direct object. Whether the sentence is **Я їм картоплю** (I eat potatoes), **Я п'ю воду** (I drink water), or **Я хочу каву** (I want coffee), the feminine ending must become **-у** or **-ю**.
:::

> **Сьогодні я готую обід. Я маю картоплю і рибу. Я їм картоплю, але я не п'ю каву. Я п'ю воду.**
> *Today I am cooking lunch. I have potatoes and fish. I am eating potatoes, but I do not drink coffee. I drink water.*

<!-- INJECT_ACTIVITY: fill-in-accusative-endings -->
<!-- INJECT_ACTIVITY: group-sort-accusative -->
<!-- INJECT_ACTIVITY: quiz-accusative-selection -->

## Підсумок — Summary

Summary: after **їсти**, **пити**, and similar verbs, inanimate direct objects take the accusative. Masculine and neuter nouns stay the same; feminine **-а / -я** changes to **-у / -ю**.

*   **Masculine and Neuter nouns do not change form.** Words like **хліб** (bread), **сік** (juice), and **молоко** (milk) stay exactly the same as they appear in the dictionary. A speaker can simply say **Я їм хліб** or **Я п'ю молоко** without any modifications to the noun.
*   **Feminine nouns undergo a specific ending shift.** If a feminine noun ends in **-а**, that ending changes to **-у**. If it ends in **-я**, it changes to **-ю**. This is why **кава** becomes **каву**, and **картопля** becomes **картоплю**. This change is mandatory and highly frequent in spoken Ukrainian.

> **Кожного дня я снідаю. Я їм кашу і п'ю чай. На обід я їм суп. Це дуже смачно!**
> *Every day I have breakfast. I eat porridge and drink tea. For lunch I eat soup. It is very tasty!*

The following short self-check test ensures these vital patterns are internalized. Fill in the blanks using the correct Accusative form of the word in parentheses:

*   Test: Я їм ___ (**риба** → **рибу**).
*   Test: Я п'ю ___ (**вода** → **воду**).
*   Test: Вона їсть ___ (**хліб** → **хліб**).
*   Test: Ми хочемо ___ (**кава** → **каву**).
*   Test: Ти п'єш ___ (**сік** → **сік**).

As an active self-check, say three things you eat and three things you drink today out loud. Pay close attention to the gender of each word, and use the correct accusative form for each item. If the word is feminine, ensure the crucial shift to the "-у" ending is made.
</generated_module_content>

**PIPELINE NOTE — Word count: 1294 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 91 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Оксана — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM

All 91 other words are confirmed to exist in VESUM.

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
