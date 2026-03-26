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

You know all 33 Ukrainian letters from the previous module. You can recognize **А**, **М**, **К**, and the rest on sight. But knowing individual letters is like knowing individual notes on a piano — the real music happens when you combine them. Right now, you will learn to read *any* Ukrainian word, even ones you have never seen before. The secret? Ukrainian spelling is phonetic. Each letter makes one sound, every time. There are no silent letters, no spelling surprises, no guessing. If you can sound out syllables, you can read anything. So the question becomes: how do you break a word into syllables?

Ukrainian first-graders learn one golden rule from their very first **буквар** (primer). Большакова, Grade 1, page 25, states it clearly: **«У слові стільки складів, скільки голосних звуків.»** — "A word has as many syllables as it has vowel sounds." This rule never breaks. Not once, not ever. Count the vowels, count the syllables. Take **мама** (mother): the vowels are **А** and **А** — two vowels, two syllables: **ма-ма**. Now **молоко** (milk): **О**, **О**, **О** — three vowels, three syllables: **мо-ло-ко**. What about **банк** (bank)? Just one **А** — one vowel, one syllable. And **сон** (dream)? One **О** — one syllable. Try **аптека** (pharmacy): **А**, **Е**, **А** — three vowels, three syllables: **а-пте-ка**. Notice something: consonants prefer to start new syllables rather than close old ones. That is the open-syllable principle — **складоподіл** in Ukrainian. The word splits as **мо-ло-ко**, not "мол-ок-о."

Now you have the rule. Here is the method Ukrainian children use to read new words — the **звуковий аналіз** (sound analysis) method from Большакова, page 29. Four steps: (1) Find the vowels — circle them mentally, they are your anchors. (2) Split the word at syllable boundaries. (3) Sound out each syllable slowly. (4) Blend everything together at natural speed. Walk through **університет** (university): the vowels are **У**, **І**, **Е**, **И**, **Е** — five vowels, five syllables: **у-ні-вер-си-тет**. Now try **бібліотека** (library): **І**, **І**, **О**, **Е**, **А** — five vowels, five syllables: **бі-блі-о-те-ка**. The method works for every word, no matter how long.

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

## Голосні літери (Vowel Letters)

In Module 1, you learned that Ukrainian has 6 vowel sounds but 10 vowel letters. Now it is time to meet each one individually. The first group is straightforward — six simple vowels, each making exactly one sound, always: **А** sounds like the "a" in "father," **О** like the "o" in "or," **У** like the "oo" in "moon," **Е** like the "e" in "bet," **И** like a sound between English "i" and "e" (no exact English match), and **І** like the "ee" in "see." That is it. **А** always sounds the same. **О** always sounds the same. Compare that to English, where the letter "a" alone has five or more possible sounds. In Ukrainian: one letter, one sound, no exceptions.

The second group is where it gets interesting — the **iotated vowels**: **Я**, **Ю**, **Є**, and **Ї**. These are "two-in-one" letters. Their behavior depends on *where* they appear. At the start of a word or after another vowel, they produce two sounds: **Я** = [й] + [а] — hear it in **яблуко** (apple) and **моя** (my, feminine). **Ю** = [й] + [у] — hear it in **юнак** (young man). **Є** = [й] + [е] — hear it in **єнот** (raccoon) and **синє** (blue, neuter). But after a consonant, these letters soften that consonant and give only the vowel part: in **пісня** (song), the **Н** is softened by **Я**, and you hear just [а] after the soft **Н**. The Grade 2 textbook sums it up perfectly: **«Букви я, ю, є на початку складу позначають два звуки: [йа], [йу], [йе].»**

Then there is **Ї** — a letter unique to Ukrainian. It *always* makes two sounds: [й] + [і], no matter where it appears. It never softens a consonant. You will find it at the start of a word (**їжак** — hedgehog), after a vowel (**мої** — my, plural; **твої** — your, plural), or after an apostrophe. It never appears directly after a consonant — that is what makes it unique among the iotated vowels. No other Slavic language has this letter.

Finally, a critical distinction: **И** versus **І**. These two vowels change meaning. **Кит** (whale) versus **кіт** (cat). **Дим** (smoke) versus **дім** (house). **Лис** (fox) versus **ліс** (forest). **И** is a back vowel — the tongue sits back, lips stay neutral. **І** is a front vowel — the tongue moves forward, lips spread slightly. The Большакова **буквар** places these pairs on the same page deliberately. Practice hearing and producing the difference, because it changes the meaning of words completely.

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

## Читання слів (Reading Words)

Time for a strategy shift. Stop reading letter by letter. Start reading syllable by syllable. When you encounter an unfamiliar word, follow this approach: find the vowels first — they are your anchors — then build syllables around them, then blend. Take **книга** (book): spot the vowels **И** and **А** — two syllables — **кни-га** — now say it at natural speed. Try **столиця** (capital city): **О**, **И**, **Я** — three syllables — **сто-ли-ця**. And **вулиця** (street): **У**, **И**, **Я** — three syllables — **ву-ли-ця**. The vowels are your roadmap through any Ukrainian word, no matter how unfamiliar it looks at first glance.

Here are common word patterns for reading practice. Two-syllable words with simple open syllables — the most natural Ukrainian rhythm: **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (foot). These flow easily — every syllable ends in a vowel. Two-syllable words with consonant clusters: **школа** (school), **книга** (book), **парта** (desk). The cluster stays together in one syllable. One-syllable words — just one vowel, quick to read: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank). Three-syllable words: **аптека** (pharmacy), **людина** (person), **вулиця** (street), **столиця** (capital). The more patterns your eyes recognize, the faster you read — your brain starts seeing syllable shapes automatically instead of processing individual letters.

Watch for three special letter combinations (a preview — Module 3 covers them fully). **Щ** is always two sounds [шч]: **що** (what), **ще** (still/yet), **щастя** (happiness) — one letter, two sounds blended together. **Ь** (the soft sign) has no sound of its own — it softens the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse). The apostrophe (**'**) separates a consonant from an iotated vowel: **сім'я** (family), **м'ясо** (meat), **п'ять** (five). Recognize these combinations when you encounter them — do not let them slow you down.

<!-- INJECT_ACTIVITY: quiz-read-meaning -->

Now build speed. Re-read the word lists above, faster each time. First pass: syllable by syllable. Second pass: whole words without pausing. Third pass: pairs of words in sequence. Ukrainian reading fluency comes from repetition and pattern recognition, not from memorizing definitions.

## Читаємо разом (Reading Together)

A progressive reading ladder. Start where you are comfortable, then push higher.

**Level 1** — two-syllable words (you should read these quickly by now): **мама**, **тато**, **вода**, **рука**, **хата**, **каша**, **школа**, **книга**.

**Level 2** — three-syllable words (find the vowels first): **аптека**, **молоко**, **людина**, **вулиця**, **столиця**, **пісня**.

**Level 3** — four or more syllables (the real test): **університет**, **бібліотека**, **фотографія**, **шоколад**. If you can read **бібліотека** without stopping between syllables, you can read anything in Ukrainian.

Now, your first Ukrainian text. Read it aloud, sentence by sentence. Every word here uses only letters and patterns from Module 1 and this module:

> **Це Київ.** *(This is Kyiv.)* **Це столиця.** *(This is the capital.)* **Тут аптека і банк.** *(Here is a pharmacy and a bank.)* **Там школа.** *(There is a school.)* **Що це?** *(What is this?)* **Це кафе.** *(This is a café.)* **А це пошта.** *(And this is a post office.)* **Ось бібліотека.** *(Here is a library.)* **Тут книги.** *(Here are books.)*

Read it again, faster. You just read real Ukrainian sentences — not isolated words, but connected meaning.

A few tips for self-study. Read aloud — Ukrainian is a phonetic language, and hearing yourself reinforces the letter-sound connections. Point to each syllable as you read, then graduate to pointing at whole words. Look for Ukrainian text online — signs, menus, social media posts — and try to sound out words before checking a translation. Every word you successfully decode builds confidence and speed. In Module 3, you will learn the special signs (**Ь**, the apostrophe, and the uniquely Ukrainian letter **Ґ**) in full detail and start reading longer texts.

## Підсумок — Summary

Four skills from this module. First: the syllable rule — **«У слові стільки складів, скільки голосних звуків»** — count vowels to count syllables. This rule never breaks. **Молоко** has 3 vowels, so 3 syllables: **мо-ло-ко**. Second: the 10 vowel letters — six simple ones (**А**, **О**, **У**, **Е**, **И**, **І**), each making one predictable sound, and four iotated ones (**Я**, **Ю**, **Є**, **Ї**) that can produce two sounds or soften a consonant. Third: the reading strategy — find vowels first, build syllables around them, blend into words at natural speed. Fourth: pattern recognition — the more word shapes you see, the faster you read without thinking.

Self-check: How many syllables in **бібліотека**? Five — count the vowels: **І**, **І**, **О**, **Е**, **А**. What two sounds does **Я** make at the start of **яблуко**? [й] + [а]. What is the difference between **кит** and **кіт**? Whale versus cat — **И** versus **І**, one vowel changes everything. What does **Ь** do? It softens the consonant before it, with no sound of its own. What does the apostrophe do? It separates a consonant from an iotated vowel, as in **сім'я**.

Next in Module 3: the soft sign, the apostrophe, and the uniquely Ukrainian letter **Ґ** — explored in full detail.

**Deterministic word count: 1630 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 82 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Большакова — NOT IN VESUM
  ✗ блі — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ пте — NOT IN VESUM

All 82 other words are confirmed to exist in VESUM.

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
