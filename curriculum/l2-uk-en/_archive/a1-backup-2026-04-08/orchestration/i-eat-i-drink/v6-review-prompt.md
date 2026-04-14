<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 37: I Eat, I Drink (A1, A1.6 [Food and Shopping])
**Writer:** Claude
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
## Діало́ги (Dialogues)

What do people eat and drink during the day? In the first dialogue, Марі́я and Оле́г chat about breakfast — what they eat, what their family eats. In the second, two colleagues unpack their lunch at work. Listen for the verbs **ї́сти** and **пи́ти** — they change with every speaker.

> — **Марія:** Що ти їси́ на сніда́нок? *(What do you eat for breakfast?)*
> — **Олег:** Я їм ка́шу і п'ю ка́ву. *(I eat porridge and drink coffee.)*
> — **Марія:** А Оле́на? *(And Olena?)*
> — **Олег:** Вона́ їсть хліб з ма́слом і п'є чай. *(She eats bread with butter and drinks tea.)*
> — **Марія:** А ді́ти? *(And the kids?)*
> — **Олег:** Вони́ їдя́ть я́йця і п'ють молоко́. *(They eat eggs and drink milk.)*

Notice how the verb **їсти** (to eat) changes with every person: **я їм**, **вона їсть**, **вони їдять**. The verb **пити** (to drink) does the same: **п'ю**, **п'є**, **п'ють**. These two verbs will look different for every subject — but by the end of this module, you will know all six forms of each.

Now the same verbs appear at lunch, with plural subjects.

> — **Коле́га 1:** Що ви їсте́ на обід? *(What are you eating for lunch?)*
> — **Колега 2:** Ми їмо́ суп і сала́т. *(We're eating soup and salad.)*
> — **Колега 1:** А що п'єте́? *(And what are you drinking?)*
> — **Колега 2:** Ми п'ємо́ воду́ або́ сік. *(We're drinking water or juice.)*
> — **Колега 1:** Я теж хо́чу суп. *(I want soup too.)*
> — **Колега 2:** До́бре, замовля́й! *(Okay, go ahead and order!)*

Look back at both dialogues and answer these questions aloud: **Що їсть Олена?** (What does Olena eat?) **Що п'ють діти?** (What do the children drink?) **Що ми їмо на обід?** (What do we eat for lunch?) Each answer uses a noun right after the verb — **хліб**, **молоко**, **суп**. Some nouns change their ending, some do not. That pattern is the core of this module.

## Їсти і пити (To Eat and To Drink)

The verb **їсти** (to eat) is irregular. It does not follow Group I or Group II conjugation — it has its own pattern. Ukrainian textbooks (Заболо́тний, Grade 7) treat it as a special class alongside **да́ти** (to give). Memorize these six forms:

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **їм** | ми **їмо** |
| 2nd | ти **їси** | ви **їсте** |
| 3rd | він/вона **їсть** | вони **їдять** |

Three sentences to anchor the pattern:

- **Я їм хліб.** — I eat bread.
- **Він їсть ри́бу.** — He eats fish.
- **Вони їдять кашу.** — They eat porridge.

The verb **пити** (to drink) follows regular Group I conjugation. Notice the apostrophe before **ю**, **є** — this is a standard Ukrainian spelling rule when **п** meets a soft vowel.

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **п'ю** | ми **п'ємо** |
| 2nd | ти **п'єш** | ви **п'єте** |
| 3rd | він/вона **п'є** | вони **п'ють** |

Three sentences:

- **Я п'ю каву.** — I drink coffee.
- **Вона п'є воду.** — She drinks water.
- **Вони п'ють сік.** — They drink juice.

Compare the two verbs side by side:

| | **їсти** | **пити** |
|---|---|---|
| я | їм | п'ю |
| ти | їси | п'єш |
| він/вона | їсть | п'є |
| ми | їмо | п'ємо |
| ви | їсте | п'єте |
| вони | їдять | п'ють |

The key difference: **їсти** is the exception you must learn by heart — every form looks different from the infinitive. **Пити** is a regular model — once you see the **п'** pattern, the endings are predictable. Both verbs are extremely high-frequency. You will use them every single day.

Ukrainian schools (Grade 4, Заболотний) teach the accusative case through the question **що?** (what?). When you eat or drink something, ask yourself: **що?** The answer is always in the accusative case.

- **Я їм (що?) хліб.** — I eat (what?) bread.
- **Я п'ю (що?) каву.** — I drink (what?) coffee.

This is the **ба́чу що? / їм що? / п'ю що?** rule from Ukrainian textbooks. Build a habit: every time you use **їсти** or **пити**, ask **що?** — and the noun that follows takes the accusative form.

<!-- INJECT_ACTIVITY: fill-in-conjugation -->

## Знахі́дний відмі́нок — неживе́ (Accusative Inanimate)

Masculine inanimate nouns do not change in the accusative — they look exactly like the nominative. The same is true for neuter nouns. Here are the examples:

- **хліб → хліб** — Я їм хліб. *(I eat bread.)*
- **суп → суп** — Я їм суп. *(I eat soup.)*
- **сік → сік** — Я п'ю сік. *(I drink juice.)*
- **бана́н → банан** — Я їм банан. *(I eat a banana.)*
- **молоко → молоко** — Я п'ю молоко. *(I drink milk.)*
- **яйце́ → яйце** — Я їм яйце. *(I eat an egg.)*

Rule: masculine and neuter inanimate nouns stay the same after **їсти** and **пити**. No ending changes at all.

Feminine nouns are different — and this is the key change to learn. Feminine nouns ending in **-а** change to **-у**. Feminine nouns ending in **-я** change to **-ю**. Eight examples:

- **ка́ва → каву** — Я п'ю каву. *(I drink coffee.)*
- **вода́ → воду** — Я п'ю воду. *(I drink water.)*
- **ри́ба → рибу** — Я їм рибу. *(I eat fish.)*
- **ка́ша → кашу** — Я їм кашу. *(I eat porridge.)*
- **карто́пля → карто́плю** — Я їм картоплю. *(I eat potatoes.)*
- **смета́на → смета́ну** — Я їм сметану. *(I eat sour cream.)*

The pattern is simple: **-а** becomes **-у**; **-я** becomes **-ю**. This is the only accusative ending change you need at A1. Everything else stays the same.

Compare these pairs side by side — nouns that change on the left, nouns that stay the same on the right:

| Changes (-у / -ю) | Stays the same |
|---|---|
| кава → **каву** | хліб → **хліб** |
| вода → **воду** | сік → **сік** |
| картопля → **картоплю** | молоко → **молоко** |

Now read these mixed sentences and notice which nouns changed and which did not:

- **Я їм рибу і хліб.** — I eat fish and bread.
- **Вона п'є каву і воду.** — She drinks coffee and water.
- **Ми їмо кашу і яйця.** — We eat porridge and eggs.
- **Вони п'ють сік і молоко.** — They drink juice and milk.

:::tip
If a noun ends in **-а** or **-я** (like **кава**, **вода**, **картопля**), swap the ending for **-у** or **-ю** when you eat or drink it. Everything else stays the same. One rule — that is all you need.
:::

<!-- INJECT_ACTIVITY: fill-in-accusative -->

<!-- INJECT_ACTIVITY: quiz-accusative -->

<!-- INJECT_ACTIVITY: group-sort-accusative -->

## Підсумок — Summary

Two verbs to remember — **їсти** (irregular: **їм, їси, їсть, їмо, їсте, їдять**) and **пити** (regular: **п'ю, п'єш, п'є, п'ємо, п'єте, п'ють**).

One accusative rule for inanimate nouns:

- **Masculine and neuter** — no change. **Хліб**, **суп**, **молоко**, **сік** stay the same.
- **Feminine -а → -у, -я → -ю.** **Кава → каву**, **вода → воду**, **картопля → картоплю**.

Test yourself — fill in the correct form:

- Я їм ___ (риба → ?) → **рибу**
- Я п'ю ___ (вода → ?) → **воду**
- Вони їдять ___ (хліб → ?) → **хліб**
- Вона п'є ___ (кава → ?) → **каву**

Now try this on your own: say three things you eat today and three things you drink. Use the correct accusative form for each noun. For example: **Я їм кашу, рибу і хліб. Я п'ю каву, воду і сік.** Check each feminine noun — did you change **-а** to **-у**? Did masculine and neuter nouns stay the same? If yes, you have the pattern.

**Deterministic word count: 1288 words** (calculated by pipeline, do NOT estimate manually)

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
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
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

Verified: 55 words | Not found: 20 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Діало — NOT IN VESUM
  ✗ Заболо — NOT IN VESUM
  ✗ Знахі — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ бана — NOT IN VESUM
  ✗ відмі — NOT IN VESUM
  ✗ дний — NOT IN VESUM
  ✗ замовля — NOT IN VESUM
  ✗ йця — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ плю — NOT IN VESUM
  ✗ пля — NOT IN VESUM
  ✗ слом — NOT IN VESUM
  ✗ смета — NOT IN VESUM
  ✗ сти — NOT IN VESUM
  ✗ тний — NOT IN VESUM
  ✗ їдя — NOT IN VESUM

All 55 other words are confirmed to exist in VESUM.

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
