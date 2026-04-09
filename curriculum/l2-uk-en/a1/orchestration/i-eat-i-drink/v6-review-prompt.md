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
## Діалоги

In Ukraine, food is not just fuel; it is the center of social life and hospitality. Asking someone **Що ти їси?** (What are you eating?) or sharing a lunch break is a primary way colleagues and friends bond during the workday. Food vocabulary is universally essential, but in Ukrainian, it also acts as the perfect introduction to how verbs and nouns interact. As you will see, Ukrainians make a strict distinction between what you "eat" and what you "drink" — even when it comes to liquid dishes like soup. This topic introduces the absolute foundation of your survival vocabulary and the crucial accusative case, which you will use every single day.

> **Тарас:** Привіт! Що ти їш на сніданок? *(Hi! What are you eating for breakfast?)*
> **Ірина:** Я їм кашу і п'ю каву. *(I eat porridge and drink coffee.)*
> **Тарас:** А Олена? *(And Olena?)*
> **Ірина:** Вона їсть хліб з маслом і п'є чай. *(She eats bread with butter and drinks tea.)*
> **Тарас:** А діти? *(And the children?)*
> **Ірина:** Вони їдять яйця і п'ють молоко. *(They eat eggs and drink milk.)*

The dialogue above uses the high-frequency question **Що ти їш?** (What are you eating?) and the response **Я їм...** (I am eating...). Notice the contrast between the verbs: **їш** is highly irregular and does not look like the infinitive **їсти** (to eat), while **п'єш** follows a more recognizable pattern from its dictionary form **пити** (to drink). The distinction between singular and plural present tense forms is fundamental because you will often speak on behalf of your family or group (**ми їмо**, **вони п'ють**).

> **Колега 1:** Що ви їсте на обід? *(What are you eating for lunch?)*
> **Колега 2:** Ми їмо суп і салат. А що п'єте? *(We eat soup and salad. And what are you drinking?)*
> **Колега 1:** Ми п'ємо воду або сік. Я сьогодні їм бутерброд і п'ю чай. А ти? *(We drink water or juice. Today I eat a sandwich and drink tea. And you?)*
> **Колега 2:** Я їм салат і п'ю каву. Я теж хочу суп. *(I eat a salad and drink coffee. I also want soup.)*
> **Колега 1:** Добре, замовляй! Я ще хочу воду потім. *(Okay, order! I still want water later.)*

## Їсти і пити

The verb **їсти** (to eat) is a unique, highly irregular verb in Ukrainian grammar. It belongs to neither Group I nor Group II verb conjugations, making it a true exception. Because it is an essential daily action that you will use in almost every conversation about food, you simply need to memorize its forms. Pay close attention to the endings, as they shift noticeably between the singular and plural forms. Here is the full paradigm:

| English | Ukrainian |
|---------|-----------|
| I eat | я **їм** |
| You (singular) eat | ти **їси** |
| He/she eats | він/вона **їсть** |
| We eat | ми **їмо** |
| You (plural/formal) eat | ви **їсте** |
| They eat | вони **їдять** |

:::tip
**Pronouncing the letter Ї**
The letter **ї** always represents two distinct sounds: the consonant **й** and the vowel **і**. You must pronounce it fully, sounding similar to the English word "yee". It is never reduced to just a single **і** sound.
:::

Here are three examples using different subjects to practice this sound:
- **Я їм суп.** (I eat soup.)
- **Ми їмо яблуко.** (We eat an apple.)
- **Діти їдять банан.** (The children eat a banana.)
- **Він їсть сир.** (He eats cheese.)

The verb **пити** (to drink) is a bit friendlier for learners. It officially follows the Group I conjugation pattern, but it features a unique spelling shift in the present tense. Notice how the vowel **и** completely disappears from the stem, and the endings start with an apostrophe, resulting in the distinct sounds **'ю** or **'є**. This apostrophe indicates a brief pause before the soft vowel. Here is the complete paradigm:

| English | Ukrainian |
|---------|-----------|
| I drink | я **п'ю** |
| You (singular) drink | ти **п'єш** |
| He/she drinks | він/вона **п'є** |
| We drink | ми **п'ємо** |
| You (plural/formal) drink | ви **п'єте** |
| They drink | вони **п'ють** |

Ukrainians use the direct verb **пити** for almost all beverages. Unlike English, where you might casually say "I am having a drink" or "I will take a coffee," in Ukrainian you must always explicitly state "I drink." It is a highly frequent verb that pairs directly with almost any liquid you can consume. Notice how the direct object immediately follows the verb:
- **Я п'ю воду.** (I drink water.)
- **Ти п'єш каву.** (You drink coffee.)
- **Вони п'ють сік.** (They drink juice.)
- **Ми п'ємо чай.** (We drink tea.)

<!-- INJECT_ACTIVITY: verb-conjugation-drill -->

A uniquely Ukrainian cultural quirk is the strict "Soup Rule." In Ukraine, you always "eat" (**їсти**) thick liquid dishes like soup and borscht with a spoon. You never "drink" them from a bowl, even if they are primarily liquid. Contrast this with true beverages like tea, juice, or fruit compote, which you always "drink" (**пити**). Using the wrong verb sounds immediately unnatural to a native speaker. For example: **Я їм борщ. Я п'ю чай.** (I eat borscht. I drink tea.)

## Знахідний відмінок — неживе

When you eat or drink something, that food item becomes the direct object of your action. In Ukrainian grammar, the direct object requires a specific form called the Accusative Case (**Знахідний відмінок**). This case is the workhorse of everyday communication because you constantly interact with objects around you.

:::note
**The "Що?" Trigger**
The Ukrainian school system effectively teaches students to identify the accusative case by asking the mental trigger question: «Бачу що? Бачу кого?» (I see what? I see whom?). When dealing with inanimate food items, asking yourself **що?** (what?) signals that you must use the accusative form for the noun that follows: **Я їм (що?) хліб. Я п'ю (що?) каву.**
:::

There is excellent news for masculine and neuter inanimate nouns: they undergo absolutely no change in this situation. The accusative form looks exactly the same as the standard dictionary (nominative) form. Therefore, masculine words like **хліб** (bread), **суп** (soup), **бутерброд** (sandwich), and **сік** (juice), as well as neuter words like **молоко** (milk) and **яйце** (egg), remain completely identical when they become the object of your action. This makes learning the accusative case much easier for beginners, as you only need to focus on the sentence structure rather than changing the word.
- **хліб** → **хліб**: **Я їм хліб.** (I eat bread.)
- **суп** → **суп**: **Я їм суп.** (I eat soup.)
- **сік** → **сік**: **Я п'ю сік.** (I drink juice.)
- **молоко** → **молоко**: **Я п'ю молоко.** (I drink milk.)
- **яйце** → **яйце**: **Я їм яйце.** (I eat an egg.)

The primary grammatical change at the A1 level happens with feminine nouns. When a feminine noun ends in **-а**, it strictly shifts to **-у** in the accusative case. If it ends in **-я**, it shifts to **-ю**. This simple but crucial vowel change immediately signals to the listener that the noun is the direct object receiving the action. You must actively practice this transformation until it becomes a natural reflex. Notice how the endings transform in these highly common daily examples:
- **вода** → **воду**: **Я п'ю воду.** (I drink water.)
- **кава** → **каву**: **Я п'ю каву.** (I drink coffee.)
- **риба** → **рибу**: **Я їм рибу.** (I eat fish.)
- **каша** → **кашу**: **Я їм кашу.** (I eat porridge.)
- **сметана** → **сметану**: **Я хочу сметану.** (I want sour cream.)
- **картопля** → **картоплю**: **Я їм картоплю.** (I eat potato.)

<!-- INJECT_ACTIVITY: accusative-form-builder -->

<!-- INJECT_ACTIVITY: noun-change-sorting -->

This foundational accusative rule applies to many other essential verbs too, particularly the verb **хотіти** (to want). When you order food at a cafe or restaurant, you will often use the polite, fixed chunk **Мені, будь ласка...** (To me, please...) followed immediately by the accusative object. Even though the main verb is implied rather than spoken out loud, the food item is still acting as the direct object receiving the action, so the accusative rules remain exactly the same.
- **Мені, будь ласка, піцу і воду.** (To me, please, pizza and water.)
- **Я хочу каву.** (I want coffee.)
- **Він хоче рибу і сік.** (He wants fish and juice.)
- **Вона хоче чай.** (She wants tea.)

<!-- INJECT_ACTIVITY: accusative-choice-quiz -->

## Підсумок — Summary

The core grammar of eating and drinking relies heavily on two essential verbs and one critical case change. The verb **їсти** (to eat) is completely irregular and its unique forms (**я їм, ти їси, він їсть**) must be memorized through repetition. The verb **пити** (to drink) is a Group I verb with a specific spelling shift that adds an apostrophe (**я п'ю, ти п'єш**). Most importantly, you must remember that when you eat or drink a feminine item ending in **-а**, you must actively change that ending to **-у** (**вода** → **воду**).

:::caution
**Watch out for Russianisms!**
A very common mistake for beginners is using the Russian word *кофе* instead of the authentic Ukrainian noun **кава**. Always remember to order **каву**! Additionally, ensure you use the Ukrainian word **сир** for both hard cheese and cottage cheese at this level; actively avoid the Russianism *творог*.
:::

To quickly recap the Accusative Inanimate rules: masculine and neuter nouns equal their dictionary nominative forms exactly, while feminine nouns take **-у** or **-ю**. You can clearly see this when you compare the masculine object **Я п'ю сік** (no change) with the feminine object **Я п'ю каву** (changed to **-у**).

Test your memory of these critical concepts before you finish the module:
- Can you conjugate the irregular verb **їсти** for all pronouns from memory? (Try recalling: **Я їм**, **ти їси**, **вони їдять**)
- Can you conjugate the verb **пити** without looking at the table? (Try recalling: **Я п'ю**, **він п'є**, **ми п'ємо**)
- Test yourself: **Я їм ___** (**риба** → **рибу**). **Я п'ю ___** (**вода** → **воду**).
- Say three things you eat today, ensuring you use the correct accusative form: **Я їм...** (e.g., **суп, яблуко**)
- Say three things you drink today, using the correct accusative form: **Я п'ю...** (e.g., **чай, сік**)
- What is the correct accusative form of the feminine noun **картопля**? (Answer: **картоплю**)

If you can confidently answer these questions, you are ready to order your favorite meals in a Ukrainian cafe!
</generated_module_content>

**PIPELINE NOTE — Word count: 1592 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 72 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ірина — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ кофе — NOT IN VESUM
  ✗ творог — NOT IN VESUM

All 72 other words are confirmed to exist in VESUM.

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
