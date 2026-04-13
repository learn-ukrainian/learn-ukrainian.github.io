<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 11: How Many? (A1, A1.2 [My World])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-011
level: A1
sequence: 11
slug: how-many
version: '1.2'
title: How Many?
subtitle: Один, два, три — numbers through prices, ages, and phones
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Count from 1 to 100 in Ukrainian
- Say prices using гривня and round numbers up to 1000
- Give age using Мені ... років (as memorized chunk — NO case grammar)
- Read and say Ukrainian phone numbers
dialogue_situations:
- setting: 'At a bakery — ordering bread, pastries, and cakes for a family gathering.
    Count: один хліб (m, bread), одна булочка (f, bun), одне тістечко (n, pastry). Prices in гривні.
    Ask: Скільки коштує торт? А три булочки?'
  speakers:
  - Покупець
  - Пекар (baker)
  motivation: Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)
- setting: Counting items in a school backpack before class — ручка (f, pen), олівець
    (m, pencil), зошит (m, notebook), підручник (m, textbook).
  speakers:
  - Учень (student)
  - Мама
  motivation: 'Numbers with school supplies: один олівець, дві ручки, п''ять зошитів'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At a market stall: — Скільки коштує сумка? — Двісті гривень.
    — А маленька? — Сто п''ятдесят. — Добре, дякую!
    Numbers emerge through real shopping context. Uses only vocabulary from M08-M10
    (gender, adjectives, colors). Demonstratives (ця/та) come in M12.'
  - 'Dialogue 2 — Meeting someone new (extending M05): — Скільки тобі років? — Мені
    двадцять п''ять. А тобі? — Мені тридцять два. А твоя сестра? — Їй вісімнадцять.
    Age formula as chunk: Мені/тобі/їй + number + років/роки/рік.'
- section: Числа 1-20 (Numbers 1-20)
  words: 300
  points:
  - '1-10: один, два, три, чотири, п''ять, шість, сім, вісім, дев''ять, десять. Pronunciation
    focus: п''ять (apostrophe!), сім (not ''сем''), дев''ять (apostrophe!). Practice:
    counting objects from M08 — один стіл, два стільці, три книги. Note: the noun
    changes after numbers, but we learn the PATTERNS as chunks, not the grammar rule.'
  - '11-20: одинадцять, дванадцять, тринадцять, чотирнадцять, п''ятнадцять, шістнадцять,
    сімнадцять, вісімнадцять, дев''ятнадцять, двадцять. Pattern: base + -надцять (like
    English ''-teen''). Watch the stress: одинáдцять, дванáдцять — stress always falls
    on the syllable ''на'' in -надцять.'
- section: Десятки і сотні (Tens and Hundreds)
  words: 300
  points:
  - 'Tens: двадцять, тридцять, сорок (!), п''ятдесят, шістдесят, сімдесят, вісімдесят,
    дев''яносто (!), сто. Two irregulars: сорок (40 — not ''чотиридесят'') and дев''яносто
    (90 — not ''дев''ятдесят''). Combined: двадцять один, тридцять п''ять, сорок сім
    — just add the unit.'
  - 'Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400),
    п''ятсот (500), тисяча (1000). Гривня: одна гривня, дві гривні, п''ять гривень.
    These noun changes are memorized patterns — grammar comes in A2. ULP Ep9: Anna
    teaches numbers through real prices.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three practical uses of numbers: 1. Prices: Скільки коштує? — Двісті гривень.
    Сто п''ятдесят гривень. 2. Age: Скільки тобі років? — Мені двадцять три (роки).
    3. Phone: Мій номер — нуль дев''яносто сім, три два один, сорок п''ять, шістдесят
    сім. Self-check: Say your age in Ukrainian. Say a price (250 hryvnias). Read a
    phone number.'
vocabulary_hints:
  required:
  - один, два, три, чотири, п'ять (1-5)
  - шість, сім, вісім, дев'ять, десять (6-10)
  - двадцять, тридцять, сорок (20, 30, 40)
  - сто, тисяча (100, 1000)
  - скільки (how many/how much)
  - коштує (costs — from коштувати)
  - гривня (hryvnia — Ukrainian currency)
  - рік, роки, років (year/years — age chunks)
  recommended:
  - п'ятдесят, шістдесят, сімдесят (50, 60, 70)
  - вісімдесят, дев'яносто (80, 90)
  - двісті, триста, п'ятсот (200, 300, 500)
  - копійка (kopek)
  - номер (number — phone/room)
  - нуль (zero)
activity_hints:
- type: fill-in
  focus: 'Write the number in words: 15 → п''ятнадцять, 47 → сорок сім'
  items: 10
- type: quiz
  focus: Скільки коштує? Match price tags to spoken prices.
  items: 8
- type: quiz
  focus: Скільки років? Match ages to descriptions.
  items: 6
- type: fill-in
  focus: Complete the phone number dictation
  items: 4
connects_to:
- a1-012 (This and That)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- Cardinal numbers 1-1000 (vocabulary, not morphology)
- Скільки коштує? question pattern
- 'Age chunk: Мені + number + років/роки/рік (memorized, not analyzed)'
- 'Irregular tens: сорок (40), дев''яносто (90)'
register: розмовний
references:
- title: ULP Season 1, Episode 5
  url: https://www.ukrainianlessons.com/episode5/
  notes: Numbers 1-10 pronunciation.
- title: ULP Season 1, Episode 9
  url: https://www.ukrainianlessons.com/episode9/
  notes: Numbers 11-100 and prices.
- title: Авраменко Grade 6, p.152
  notes: Числівники кількісні vs порядкові — basic classification.

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Numbers are the foundation of navigating daily life in any new language. Whether you are ordering food at a local bakery, checking the price of a train ticket, or simply sharing basic information about yourself, you need to know how to count. In this module, we will explore Ukrainian numbers. We will focus on real-world contexts like shopping at a market stall and asking new friends about their age. You will notice that Ukrainian numbers behave a bit differently than English numbers. They often change the words that follow them, but we will learn these as simple, rhythmic patterns.

Let us look at a typical interaction at a bustling Ukrainian market stall. A customer is asking about the price of bags. 

> **Покупець:** Добрий день! **Скільки коштує** сумка? *(Good afternoon! How much does the bag cost?)*
> **Продавець:** **Двісті** гривень. *(Two hundred hryvnias.)*
> **Покупець:** А **маленька**? *(And the small one?)*
> **Продавець:** **Сто п'ятдесят**. *(One hundred fifty.)*
> **Покупець:** Добре, **дякую**! *(Good, thank you!)*

In this exchange, the phrase **скільки коштує** (how much does it cost) is your most important tool. The customer asks **Скільки коштує сумка?** (How much does the bag cost?). The seller responds with numbers: **двісті** (two hundred) and **сто п'ятдесят** (one hundred fifty). The numbers emerge naturally through the shopping context. You do not need complex grammar to buy things. You just need the core question and the vocabulary for the numbers.

Now, let us look at another common situation. You are meeting someone new and sharing basic personal details.

> **Анна:** Привіт! **Скільки тобі років?** *(Hi! How old are you?)*
> **Максим:** **Мені двадцять п'ять.** А тобі? *(I am twenty-five. And you?)*
> **Анна:** **Мені тридцять два.** А твоя сестра? *(I am thirty-two. And your sister?)*
> **Максим:** **Їй вісімнадцять.** *(She is eighteen.)*

This dialogue uses a highly specific formula. To ask someone's age, you say **Скільки тобі років?** (How old are you?). The word **скільки** means how many. To reply, you do not use the verb "to have" like in some languages, and you do not use "to be" like in English. Instead, you use a fixed chunk: **мені** (to me), **тобі** (to you), or **їй** (to her) followed by the number. **Мені двадцять п'ять** literally translates as "to me is twenty-five". Treat this entire phrase as a single memorized chunk.

<!-- INJECT_ACTIVITY: quiz-ages --> 

## Числа 1-20 (Numbers 1-20)

Let us start with the core building blocks: the numbers from one to ten. Listen carefully to how they sound. Ukrainian Lessons Season 1, Episode 5 focuses on this pronunciation set. 

*   **один** (one)
*   **два** (two)
*   **три** (three)
*   **чотири** (four)
*   **п'ять** (five)
*   **шість** (six)
*   **сім** (seven)
*   **вісім** (eight)
*   **дев'ять** (nine)
*   **десять** (ten)

Pronunciation requires special attention here. The words **п'ять** and **дев'ять** contain an apostrophe. In Ukrainian, the apostrophe shows that the consonant before the following vowel stays hard; it is not a pause sound. So in **п'ять** and **дев'ять**, pronounce the consonant clearly before the next vowel. The number **сім** has a clear Ukrainian **і** sound. 

For now, learn the most common combinations as ready-made chunks: **один стіл** (one table), **одна книга** (one book), **одне вікно** (one window), **два столи** (two tables), **два вікна** (two windows), **дві книги** (two books).

At this level, treat these as patterns you can repeat: **один рік** (one year), **два роки** (two years), **три студенти** (three students), **п'ять років** (five years), **десять гривень** (ten hryvnias). You do not need the grammar rule yet. 

Now, let us expand to the numbers from eleven to twenty. 

*   **одинадцять** (eleven)
*   **дванадцять** (twelve)
*   **тринадцять** (thirteen)
*   **чотирнадцять** (fourteen)
*   **п'ятнадцять** (fifteen)
*   **шістнадцять** (sixteen)
*   **сімнадцять** (seventeen)
*   **вісімнадцять** (eighteen)
*   **дев'ятнадцять** (nineteen)
*   **двадцять** (twenty)

These numbers follow a clear pattern: a base number plus the suffix **-надцять**. This is exactly like the English "-teen". There are two crucial rules here. First, the stress always falls on the **-на-** syllable. You say **одинáдцять** and **дванáдцять**. Second, there is a spelling rule. There is no soft sign in the middle of these words. You write **п'ятнадцять**, not **п'ятьнадцять**.

## Десятки і сотні (Tens and Hundreds)

Once you know the base numbers, learning the tens is mostly a matter of adding a suffix. Let us look at the tens from thirty to one hundred.

*   **тридцять** (thirty)
*   **сорок** (forty)
*   **п'ятдесят** (fifty)
*   **шістдесят** (sixty)
*   **сімдесят** (seventy)
*   **вісімдесят** (eighty)
*   **дев'яносто** (ninety)
*   **сто** (one hundred)

Pay close attention to the two historical irregulars in this list. The word for forty is **сорок**. It is completely unique and does not look like the word for four. The word for ninety is **дев'яносто**. It does not look like the other tens. You must memorize these two separately.

Forming compound numbers is incredibly simple. You just combine the ten and the unit. There are no connecting words like "and". You place the words side by side. 
*   **двадцять один** (twenty-one)
*   **тридцять п'ять** (thirty-five)
*   **сорок сім** (forty-seven)

<!-- INJECT_ACTIVITY: fill-in-numbers -->

To navigate Ukrainian markets, buy train tickets, or order coffee, you need to know the hundreds. These are essential vocabulary words.

*   **сто** (one hundred)
*   **двісті** (two hundred)
*   **триста** (three hundred)
*   **чотириста** (four hundred)
*   **п'ятсот** (five hundred)
*   **тисяча** (one thousand)

Let us apply these numbers directly to prices. The national currency is the **гривня** (hryvnia), and smaller amounts use **копійка** (kopek). Ukrainian Lessons Season 1, Episode 9 teaches these numbers through real prices. It follows the same ready-made patterns we learned earlier. 
*   1: **одна гривня** (one hryvnia)
*   2-4: **дві гривні** (two hryvnias)
*   5+: **п'ять гривень** (five hryvnias)

Remember the question **Скільки коштує?** (How much does it cost?). You can use this everywhere. If you are in a bakery, you might ask **Скільки коштує торт?** (How much does the cake cost?). The baker will reply with the price, perhaps **триста гривень** (three hundred hryvnias). You might also ask **Скільки коштує хліб?** (How much does the bread cost?). The answer might be **тридцять гривень** (thirty hryvnias). 

<!-- INJECT_ACTIVITY: quiz-prices -->

## Підсумок — Summary

Numbers have immense practical value. Let us review the three most common ways you will use them every single day. 

The first practical use is for prices. When you want to buy something, you use the question pattern **Скільки коштує?** (How much does it cost?). The seller will reply with a number and the word for currency. You might hear **двісті гривень** (two hundred hryvnias) or **сто п'ятдесят гривень** (one hundred fifty hryvnias). This pattern works in cafes, markets, and shops.

The second practical use is for expressing age. You will often hear the question **Скільки тобі років?** (How old are you?). Remember the fixed response format. You do not use the verb "to have". You must use the dative case pronoun **мені** (to me). You reply with **мені** plus your age. For example, **мені двадцять три роки** (I am twenty-three years old) or **мені сорок років** (I am forty years old). 

The third practical use is for reading and sharing phone numbers. To do this, you need one more essential word: **нуль** (zero). When Ukrainians read phone numbers aloud, they typically group the digits into pairs or triplets. A full phone number statement sounds like this: **Мій номер — нуль дев'яносто сім, три два один, сорок п'ять, шістдесят сім** (My number is zero ninety-seven, three two one, forty-five, sixty-seven). 

<!-- INJECT_ACTIVITY: dictation-phone -->

Before you finish this module, perform these quick self-check tasks:
*   Say your own age aloud in Ukrainian using the chunk **мені ... років**.
*   Translate the price "250 hryvnias" aloud. It should be **двісті п'ятдесят гривень**.
*   Read a fictional phone number aloud. Try saying "050 123 45 67" using the typical Ukrainian groupings.
</generated_module_content>

**PIPELINE NOTE — Word count: 1304 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 81 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ п'ятьнадцять — NOT IN VESUM

All 81 other words are confirmed to exist in VESUM.

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
