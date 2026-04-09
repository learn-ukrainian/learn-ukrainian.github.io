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
## Діалоги — Dialogues

Numbers are the invisible architecture of our daily interactions. From the moment you wake up, you are surrounded by quantities, prices, and measurements. When you walk into a traditional Ukrainian bakery, you do not just point at items; you ask for a specific amount. You might need **один хліб** (one bread) for the family dinner, **одна булочка** (one bun) for a quick snack, or perhaps **одне тістечко** (one pastry) as a treat. You will inevitably need to ask the baker, **Скільки коштує торт? А три булочки?** (How much does a cake cost? And three buns?). If you are packing a backpack for a language class, you check your supplies by counting: **один олівець** (one pencil) for taking notes, and **дві ручки** (two pens) just in case one runs out of ink. Numbers allow us to navigate the practical realities of life, whether we are comparing prices or sharing personal details.

Let us look at how numbers naturally emerge when shopping at a bustling market stall. In this scenario, a customer is looking to buy a bag and needs to ask about the **ціна** (price). Read the dialogue below to see how numbers are used in a real commercial context.

> **Покупець:** Добрий день! **Скільки коштує сумка?** *(Good afternoon! How much does the bag cost?)*
> **Продавець:** Добрий день! **Двісті гривень.** *(Good afternoon! Two hundred hryvnias.)*
> **Покупець:** **А маленька?** *(And the small one?)*
> **Продавець:** **Сто п'ятдесят.** *(One hundred fifty.)*
> **Покупець:** **Добре, дякую!** *(Good, thank you!)*

In this exchange, the customer uses the essential phrase **Скільки коштує?** (How much does it cost?) alongside the noun **сумка** (bag) and the adjective **маленька** (small). The seller responds using exact numbers: **двісті** (two hundred) and **сто п'ятдесят** (one hundred fifty).

Numbers are also crucial when meeting someone new and expanding beyond basic greetings. A common follow-up question in any conversation is asking about age.

> **Антон:** Привіт! **Скільки тобі років?** *(Hi! How old are you?)*
> **Віктор:** Привіт! **Мені двадцять п'ять. А тобі?** *(Hi! I am twenty-five. And you?)*
> **Антон:** **Мені тридцять два. А твоя сестра?** *(I am thirty-two. And your sister?)*
> **Віктор:** **Їй вісімнадцять.** *(She is eighteen.)*

Here, we see the question **Скільки тобі років?** (How old are you?) and the response pattern **Мені...** (To me is...). They use the numbers **вісімнадцять** (eighteen), **двадцять п'ять** (twenty-five), and **тридцять два** (thirty-two). This formula is a fixed pattern you can memorize right now to share your own details.

## Числа 1-20 — Numbers 1-20

The absolute foundation of counting relies on the numbers from one to ten. These are the building blocks you will use every single day. The sequence is **один** (one), **два** (two), **три** (three), **чотири** (four), **п'ять** (five), **шість** (six), **сім** (seven), **вісім** (eight), **дев'ять** (nine), and **десять** (ten). Pronunciation here is critical. Pay close attention to the apostrophe in the words **п'ять** and **дев'ять**. The apostrophe tells you to pronounce the preceding consonant sharply and then transition distinctly into the following vowel, creating a slight pause. Furthermore, notice the clear **і** sound in both **сім** and **вісім**. It sounds like the "ee" in "meet" and must never be relaxed into a softer sound. 

Unlike English, where numbers are static words, Ukrainian numbers must harmonize with the objects they describe. The number one has three distinct forms that match the gender of the noun. You must say **один стіл** (one table) for a masculine noun, **одна книга** (one book) for a feminine noun, and **одне вікно** (one window) for a neuter noun. The number two also changes, but it only has two forms. You use **два** for both masculine and neuter nouns, such as **два столи** (two tables) or **два вікна** (two windows). However, when counting feminine objects, you must switch to the feminine form, which is **дві**. Therefore, you say **дві книги** (two books).

Once you have mastered the first ten numbers, learning the teens is remarkably straightforward because they follow a highly predictable pattern. You simply take the base number and add the suffix **-надцять**. The sequence is **одинадцять** (eleven), **дванадцять** (twelve), **тринадцять** (thirteen), **чотирнадцять** (fourteen), **п'ятнадцять** (fifteen), **шістнадцять** (sixteen), **сімнадцять** (seventeen), **вісімнадцять** (eighteen), and **дев'ятнадцять** (nineteen), leading up to **двадцять** (twenty). There is a crucial phonetic rule here: the stress always falls on the syllable **-на-**. You must pronounce it as **одинадцять** and **дванадцять**. 

:::caution
A common mistake for learners is trying to place the stress at the beginning of the word, similar to English. Always emphasize the **-на-** syllable in these numbers.
:::

When we count classroom objects, the nouns change their endings based on the number. You do not need to memorize complex grammatical tables yet; simply learn these high-frequency combinations as fixed patterns. Notice how the ending shifts depending on the quantity: **один зошит** (one notebook), **два зошити** (two notebooks), and **п'ять зошитів** (five notebooks). Similarly, we say **один підручник** (one textbook), **два підручники** (two textbooks), and **десять підручників** (ten textbooks). By learning these blocks together, you internalize the rhythm of the language without analyzing the underlying rules.

<!-- INJECT_ACTIVITY: fill-in-numbers-words -->

## Десятки і сотні — Tens and Hundreds

Larger numbers allow us to discuss broader concepts, prices, and quantities. The tens follow a fairly regular pattern, usually ending in the suffix **-дцять** or **-десят**. The sequence continues with **тридцять** (thirty), **п'ятдесят** (fifty), **шістдесят** (sixty), **сімдесят** (seventy), and **вісімдесят** (eighty). However, there are two critical irregular numbers you must memorize immediately: **сорок** (forty) and **дев'яносто** (ninety). They do not follow the standard suffix rules. To create compound numbers, you simply place the ten and the unit next to each other, exactly as you do in English. For example, you combine them to say **сорок сім** (forty-seven), **двадцять один** (twenty-one), or **дев'яносто дев'ять** (ninety-nine). 

When it comes to purchasing high-value items or discussing large sums, you need the hundreds. The base unit is **сто** (one hundred). The subsequent hundreds are built systematically, but their spellings must be memorized: **двісті** (two hundred), **триста** (three hundred), **чотириста** (four hundred), **п'ятсот** (five hundred), and finally **тисяча** (one thousand). Notice carefully that two hundred is written and pronounced as **двісті**, using the feminine root form, and never as "двасто". These hundreds combine easily with the tens and units you already know. If you want to say three hundred and fifty, you simply say **триста п'ятдесят**. 

:::tip
The number **тисяча** (thousand) is a feminine noun. If you want to say "one thousand," you must use the feminine form of one: **одна тисяча**.
:::

These larger numbers are indispensable when dealing with money and currency. The national currency of Ukraine is the **гривня** (hryvnia). Just like the classroom objects we counted earlier, the word for currency changes depending on the exact number preceding it. You must memorize these three core patterns. For amounts ending in one, use the base form: **одна гривня** (one hryvnia). For amounts ending in two, three, or four, the word changes: **дві гривні** (two hryvnias), **три гривні** (three hryvnias), or **чотири гривні** (four hryvnias). For all numbers from five to zero, the form changes again: **п'ять гривень** (five hryvnias), **десять гривень** (ten hryvnias), or **сто гривень** (one hundred hryvnias). Combine these patterns with the essential question **Скільки це коштує?** (How much does this cost?) to handle any shopping scenario confidently.

<!-- INJECT_ACTIVITY: quiz-prices -->

## Підсумок — Summary

Stating your age in Ukrainian relies on a fixed formula. In Ukrainian, age is not something you "are" or "have"; rather, years are accumulated "to you." The structure **Мені... років** (To me is... years) is a fixed grammatical chunk. You use the dative pronoun **мені** (to me) followed by the number, and then the word for "years". The word for years changes based on the last digit of your age. If your age ends in one (except eleven), you use the singular form: **двадцять один рік** (twenty-one years). If your age ends in two, three, or four, you use the plural form: **тридцять три роки** (thirty-three years). For all other numbers, including zero and the teens, you use the third form: **сорок років** (forty years) or **вісімнадцять років** (eighteen years).

Numbers are also essential for sharing contact information, specifically phone numbers. The word for a digit or a phone number is **номер** (number). When reciting a phone number, you will frequently use the word **нуль** (zero). Ukrainians typically read phone numbers by grouping the digits into blocks of two or three, rather than reciting them as single digits. For instance, the area code 067 is usually read as a single block: **нуль шістдесят сім** (zero sixty-seven). Alternatively, you might hear the digits separated out distinctly, such as **нуль, дев'ять, сім** (zero, nine, seven), before grouping the remaining digits into pairs like **сорок п'ять, шістдесят сім** (forty-five, sixty-seven).

The question word **Скільки** is highly versatile because it functions as both "how many" and "how much," depending on the context. When you ask **Скільки книг?** (How many books?), you are inquiring about the physical quantity of objects. However, when you ask **Скільки коштує книга?** (How much does the book cost?), the focus shifts entirely to the price. This single word serves as the gateway to unlocking both physical inventory and financial transactions in your daily life.

Before finishing this module, take a moment to perform a self-check:
- Can you say your age? (**Мені ... років**)
- Can you ask for a price? (**Скільки коштує ...?**)
- Can you count to ten without looking?
- Can you say your phone number in Ukrainian?

<!-- INJECT_ACTIVITY: quiz-age-matching -->
<!-- INJECT_ACTIVITY: fill-in-phone-numbers -->
</generated_module_content>

**PIPELINE NOTE — Word count: 1530 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 89 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Антон — NOT IN VESUM
  ✗ Віктор — NOT IN VESUM
  ✗ двасто — NOT IN VESUM
  ✗ десят — NOT IN VESUM
  ✗ дцять — NOT IN VESUM

All 89 other words are confirmed to exist in VESUM.

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
