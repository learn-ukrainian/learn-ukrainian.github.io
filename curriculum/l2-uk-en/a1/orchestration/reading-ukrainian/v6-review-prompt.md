# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Reading Ukrainian (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: '1.1'
title: Reading Ukrainian
subtitle: From letters to words to sentences
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Read any Ukrainian word by sounding out letters and blending syllables
- Apply the syllable rule — count vowels to count syllables
- Read multisyllable words confidently (not letter by letter)
- Understand how the 10 vowel letters map to 6 vowel sounds
content_outline:
- section: Склади (Syllables)
  words: 250
  points:
  - 'Большакова Grade 1 p.25: ''У слові стільки складів, скільки голосних звуків.''
    Count the vowels, count the syllables. This rule never breaks. ма-ма (2 vowels
    = 2 syllables), мо-ло-ко (3 vowels = 3 syllables), банк (1 vowel = 1 syllable).'
  - 'How to read a new word: 1. Find the vowels (they''re the syllable cores) 2. Split
    at syllable boundaries (consonants prefer starting new syllables) 3. Sound out
    each syllable 4. Blend into the full word at natural speed Practice: а-пте-ка,
    у-ні-вер-си-тет, шо-ко-лад. Note: Ukrainian phonetic syllable division (складоподіл)
    follows the open-syllable principle — consonants prefer starting new syllables.'
  - 'Following Большакова p.29 звуковий аналіз method: identify vowels, divide into
    syllables, then read. This is how Ukrainian children learn.'
- section: Голосні літери (Vowel Letters)
  words: 300
  points:
  - 'Review from M01: 6 sounds, 10 letters. Now learn all 10 individually. Simple
    vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і]. Each makes
    ONE consistent sound — no surprises.'
  - 'Iotated vowels (two sounds or softening): Я = [йа] at word start (яблуко) or
    after vowel (моя). After consonant: softens it + [а] (пісня — Н is softened).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е]. Ї = ALWAYS [йі] — never
    softens. Only at word start, after vowel, or after apostrophe. Unique to Ukrainian.'
  - 'Critical minimal pairs: И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім
    (house). Listen to Anna''s pronunciation videos for each — the difference is subtle
    but changes meaning.'
- section: Читання слів (Reading Words)
  words: 300
  points:
  - 'Apply M01 letter knowledge to read real words fluently. Strategy: don''t read
    letter-by-letter. Read syllable-by-syllable. Start with the vowels (find them
    first), then build outward. Example: книга — find vowels И, А → кни-га → read.'
  - 'Common word patterns for reading practice: CVCV: мама, тато, каша, вода, рука,
    хата, коза, нога CVCCV: школа, книга, банда, парта CVC: дім, сон, ліс, дуб, хліб,
    банк The more patterns you see, the faster you read.'
  - 'Special letter combinations to watch for: Щ is always [шч] — що, ще, щастя. Ь
    has no sound — it softens: день, сіль, кінь. '' (apostrophe) separates: сім''я,
    м''ясо, п''ять. These will be explored fully in M03.'
- section: Читаємо разом (Reading Together)
  words: 200
  points:
  - 'Progressive reading practice — start simple, build up: Level 1 (2 syllables):
    мама, тато, вода, рука, хата, каша Level 2 (3 syllables): аптека, молоко, людина,
    вулиця Level 3 (4+ syllables): університет, бібліотека, фотографія'
  - 'Reading a simple text (all Це + noun, no verbs): Це Київ. Це столиця. Тут аптека
    і банк. Там школа. Що це? Це кафе. А це пошта.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel
    sounds? Name the 4 iotated vowel letters. What does Ь do? What does the apostrophe
    do? Read this word: бібліотека — how many syllables?'
vocabulary_hints:
  required:
  - яблуко (apple) — Я at word start = [йа]
  - молоко (milk) — 3 syllables, all simple vowels
  - людина (person) — Л + Ю combination
  - вулиця (street) — Ц sound practice
  - столиця (capital) — Київ — столиця України
  - каша (porridge) — Ш sound practice
  - пісня (song) — softening by Я after consonant
  recommended:
  - університет (university) — long word practice
  - бібліотека (library) — 5 syllables
  - фотографія (photography) — long word with Ф
  - шоколад (chocolate) — Ш + О + К combination
activity_hints:
- type: fill-in
  focus: 'Divide words into syllables: мо-ло-ко, ап-те-ка'
  items: 8
- type: quiz
  focus: How many syllables? Count the vowels.
  items: 8
- type: match-up
  focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 4
- type: quiz
  focus: Read the word and choose its meaning
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- 'Syllable rule: count vowels = count syllables (складоподіл)'
- 10 vowel letters → 6 vowel sounds mapping
- Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])
- 'Reading fluency: syllable-by-syllable word reading'
- Ь, apostrophe, voiced/voiceless (preview — detailed in M03)
register: розмовний
references:
- title: Большакова Grade 1 буквар, p.25
  notes: 'Syllable rule: ''У слові стільки складів, скільки голосних звуків.'''
- title: Большакова Grade 1 буквар, p.29
  notes: Звуковий аналіз слова method — how to analyze word sounds.
- title: Захарійчук Grade 1 (NUS 2025), p.13-15
  notes: 'Sound notation: [•] for vowels, [–] for consonants, [=] for soft.'

</plan_content>

## Generated Content

<generated_module_content>
## Склади (Syllables)

You know the Ukrainian alphabet from Module 1. You can name every letter. But a letter on its own is not reading — reading means looking at a word like **аптека** (pharmacy) and hearing it in your mind without stopping at each letter. How do Ukrainian children learn this skill? With one unbreakable rule, taught on page 25 of every first-grade textbook:

:::tip
**У слові стільки складів, скільки голосних звуків.**
A word has as many syllables as it has vowel sounds.
:::

Count the vowels, count the syllables. It works every time. Look at **мама** (mother) — two vowels, А and А, so two syllables: ма-ма. Now **молоко** (milk) — three vowels, О, О, О — three syllables: мо-ло-ко. What about **банк** (bank)? One vowel, А — one syllable: банк. And **оса** (wasp)? Two vowels, О and А — two syllables: о-са. No exceptions. This rule never breaks.

Now for the method itself. Ukrainian teachers use a process called **звуковий аналіз** (sound analysis), described in Большакова Grade 1 on page 29. Here is how to read any new word you encounter:

1. **Find the vowels** — they are the cores of each syllable.
2. **Split at syllable boundaries** — Ukrainian follows the open-syllable principle (складоподіл): consonants prefer to start new syllables rather than close old ones.
3. **Sound out each syllable** separately.
4. **Blend** the syllables into the full word at natural speed.

Walk through **аптека** (pharmacy): the vowels are А, Е, А — three syllables. Split: а-пте-ка. Sound each piece, then blend them together. Now try **університет** (university): vowels У, І, Е, И, Е — five syllables. Split: у-ні-вер-си-тет. Five pieces, blended into one word.

Try counting without splitting — just count the vowels. **Сон** (dream) — 1. **Сало** (lard) — 2. **Ламана** (broken line) — 3. **Смола** (resin) — 2. **Ананас** (pineapple) — 3. **Бібліотека** (library) — 5. Remember: Ь (soft sign) and the apostrophe are NOT vowels. Never count them. You may also notice that one syllable in each word sounds louder than the others — that is **наголос** (stress), which Module 3 covers fully. For now, focus on splitting and blending.

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

## Голосні літери (Vowel Letters)

Module 1 introduced this fact: Ukrainian has 6 vowel sounds but 10 vowel letters. Now meet all ten individually and understand exactly what each one does.

The first six are simple — each letter represents ONE consistent sound, with no surprises:

| Letter | Sound | Example |
|--------|-------|---------|
| **А** | [а] | **аптека** (pharmacy) |
| **О** | [о] | **око** (eye) |
| **У** | [у] | **рука** (hand) |
| **Е** | [е] | **село** (village) |
| **И** | [и] | **кит** (whale) |
| **І** | [і] | **кіт** (cat) |

Unlike English vowels, which shift depending on the word (compare the "a" in "father" versus "fate"), Ukrainian vowels stay constant. **А** is always [а]. **О** is always [о]. What you see is what you hear.

The remaining four letters are called **iotated vowels** because they can represent TWO sounds — a [й] glide followed by a vowel. This happens at the beginning of a word or after another vowel.

**Я** = [йа] at word start or after a vowel: **яблуко** (apple) sounds like [йаблуко], **моя** (my, feminine) sounds like [мойа]. But after a consonant, Я softens that consonant and contributes only [а]: in **пісня** (song), the Н before Я becomes soft.

**Ю** follows the same pattern: [йу] at word start — **юнак** (young man) — or softening + [у] after a consonant: in the word **люблю** (I love), both Л sounds are softened by Ю.

**Є** = [йе] at word start: **єнот** (raccoon). After a consonant, it softens + [е]: **синє** (blue, neuter).

Then the unique one. **Ї** ALWAYS represents two sounds [йі] — it never softens a preceding consonant. It appears only at the start of a word, after a vowel, or after an apostrophe: **їжак** (hedgehog), **мої** (my, plural). Ї is uniquely Ukrainian — no other Slavic language has this letter.

Now for minimal pairs where one vowel letter changes the entire meaning. **И** and **І** look similar but produce different sounds: **кит** (whale) vs **кіт** (cat), **дим** (smoke) vs **дім** (house), **лис** (fox) vs **ліс** (forest), **рик** (roar) vs **рік** (year), **сир** (cheese) vs **сір** (grey). И is a back vowel — your tongue pulls back. І is a front vowel — your tongue pushes forward. The difference is subtle but it changes meaning entirely.

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

## Читання слів (Reading Words)

Time to apply everything and read real Ukrainian words fluently. The key strategy: do not read letter-by-letter. Read syllable-by-syllable. Start with the vowels — they are your anchors — then build outward.

Take **книга** (book). Find the vowels: И, А — two syllables. Split: кни-га. Blend them together: книга. Now **шоколад** (chocolate): vowels О, О, А — three syllables. Split: шо-ко-лад. Blend: шоколад. One more: **вулиця** (street) — vowels У, И, Я — three syllables: ву-ли-ця. The more you practice this vowel-first approach, the faster you read any new word without hesitation.

Common word patterns build reading speed. Start recognizing shapes:

**CVCV** (consonant-vowel-consonant-vowel) — the simplest pattern, two syllables of alternating sounds: **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (leg).

**CVCCV** — a consonant cluster appears before the second vowel: **школа** (school), **книга** (book), **парта** (desk).

**CVC** — one syllable, closed by a consonant: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank).

Longer words follow the same logic: **аптека** (pharmacy) is V-CCV-CV, **молоко** (milk) is CV-CV-CV, **столиця** (capital) is CCV-CV-CV. Read each group aloud — start slow, then speed up. Pattern recognition is what turns mechanical decoding into natural reading.

Watch for three special letter combinations. **Щ** always sounds like [шч]: **що** (what), **ще** (still), **щастя** (happiness). **Ь** (soft sign) has no sound of its own — it softens the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse). The apostrophe separates a consonant from an iotated vowel: **сім'я** (family), **м'ясо** (meat), **п'ять** (five). Module 3 explores all three in depth — for now, just recognize them when you see them.

<!-- INJECT_ACTIVITY: quiz-read-and-match -->

## Читаємо разом (Reading Together)

A reading ladder — start where you feel comfortable, then climb.

**Level 1** (2 syllables): **мама** (mother), **тато** (father), **вода** (water), **рука** (hand), **хата** (house), **каша** (porridge), **книга** (book), **школа** (school).

**Level 2** (3 syllables): **аптека** (pharmacy), **молоко** (milk), **людина** (person), **вулиця** (street), **столиця** (capital), **пісня** (song).

**Level 3** (4+ syllables): **університет** (university), **бібліотека** (library), **фотографія** (photography), **шоколадний** (chocolate, adjective).

Read each level until it feels comfortable, then move to the next. Speed comes from practice, not rushing.

Now read a simple connected text. Every sentence uses **Це** (this is) + a noun, or a location word — no verbs yet:

> **Це Київ. Це столиця. Тут аптека і банк. Там школа. А це що? Це кафе. Поруч пошта. Тут вулиця, там парк.**

*(This is Kyiv. This is the capital. Here is a pharmacy and a bank. There is a school. And what is this? This is a café. Nearby is a post office. Here is a street, there is a park.)*

Read it aloud three times: first slowly, syllable by syllable. Then at a normal pace. Then try reading without pausing between words. You just read Ukrainian sentences.

Challenge round — try these longer words using the vowel-first method: **бібліотека** (library) — vowels І, І, О, Е, А → 5 syllables. **Університет** (university) — vowels У, І, Е, И, Е → 5 syllables. **Фотографія** (photography) — vowels О, О, А, І, Я → 5 syllables. If you can read these, you can read any Ukrainian word. The syllable rule and vowel-first strategy work every time.

## Підсумок — Summary

This module gave you three tools that work together to unlock Ukrainian reading.

**First: the syllable rule.** Count the vowels to count the syllables. **Молоко** — three vowels, three syllables. **Банк** — one vowel, one syllable. It never fails.

**Second: the 10 vowel letters.** Six are simple — **А**, **О**, **У**, **Е**, **И**, **І** — each making one consistent sound. Four are iotated — **Я**, **Ю**, **Є**, **Ї** — capable of representing two sounds at word start or after a vowel. **Ї** is uniquely Ukrainian and always represents [йі].

**Third: the reading strategy.** Find the vowels first, split into syllables, sound out each piece, blend into the full word. These three tools let you read any Ukrainian word you encounter, even one you have never seen before.

Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel sounds? Name the 4 iotated vowel letters. When does **Я** represent two sounds? What makes **Ї** unique? What does **Ь** do? Read this word: **бібліотека** — how many syllables?

Coming in Module 3: **наголос** (stress), the soft sign and apostrophe in detail, and voiced versus voiceless consonant pairs.

**Deterministic word count: 1477 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 92 words | Not found: 6 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Большакова — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ йаблуко — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ мойа — NOT IN VESUM
  ✗ пте — NOT IN VESUM

All 92 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `rag_verify_lemma` — full declension/conjugation for a lemma
- `rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `rag_search_literary` — verify literary references against primary sources
- `rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
