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
## Склади — Syllables

You already know Ukrainian letters from M01 — you can recognise them, name them, and connect each one to a sound. Now it is time to read real words. The secret to reading Ukrainian is not memorising individual letters harder. It is **склади** (syllables). Ukrainian children learn to read by syllables, not letter by letter, and so will you. There is a golden rule from the very first page of the Ukrainian буквар, and every student in Ukraine knows it by heart: **«У слові стільки складів, скільки голосних звуків.»** Count the vowels, count the syllables. This rule never breaks — not for short words, not for long ones, not ever.

Watch how it works with progressively longer words. Take **мама** (mother): find the vowels — **А**, **А**. Two vowels means two syllables: **ма-ма**. Now try **молоко** (milk): find the vowels — **О**, **О**, **О**. Three vowels means three syllables: **мо-ло-ко**. What about **банк** (bank)? One vowel, **А** — one syllable. **Сон** (dream): one vowel, **О** — one syllable. **Оса** (wasp): **О**, **А** — two syllables, **о-са**. **Ананас** (pineapple): **А**, **А**, **А** — three syllables, **а-на-нас**. The rule works for every Ukrainian word without exception.

So what do you do when you meet an unfamiliar word? Follow the four-step method from Большакова's звуковий аналіз. Step one: find the vowels — they are the core of every syllable. Step two: split the word at syllable boundaries. In Ukrainian, consonants prefer to start a new syllable rather than close the previous one. This is the open-syllable principle, called **складоподіл**. Step three: sound out each syllable slowly. Step four: blend the syllables together at natural speed. Walk through **аптека** (pharmacy): vowels are **А**, **Е**, **А** — three syllables, **ап-те-ка**. Now try **університет** (university): count the vowels — **У**, **І**, **Е**, **И**, **Е** — five syllables, **у-ні-вер-си-тет**.

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

One note on how Ukrainian splits syllables differently from English. Ukrainian strongly prefers open syllables — syllables that end in a vowel. That is why **молоко** splits as **мо-ло-ко** (each syllable ends with a vowel), not мол-ок-о. When a consonant sits between two vowels, it belongs to the next syllable, not the previous one. When two or more consonants cluster together, most of them still move forward to start the new syllable. This will feel natural quickly — just remember that consonants want to begin syllables, not end them.

## Голосні літери — Vowel Letters

Recall from M01 that Ukrainian has six vowel sounds but ten vowel letters. Now it is time to meet all ten individually. The first group is the simple vowels — each letter makes exactly one sound, every single time, with no surprises. **А** sounds like the "a" in "father" (**мама**). **О** sounds like the "o" in "more" (**молоко**). **У** sounds like the "oo" in "food" (**рука**, meaning hand). **Е** sounds like the "e" in "bet" (**село**, meaning village). **И** is a sound English does not have — it sits between "i" in "bit" and "oo" in "hook" (**дим**, meaning smoke). **І** sounds close to "ee" in "see" but shorter (**дім**, meaning house). These six are straightforward: one letter, one sound, always.

The second group is the iotated vowels — the clever ones that do double duty. **Я** at the start of a word or after a vowel equals two sounds: [й] + [а]. Say **яблуко** (apple) — hear that glide before the "a"? That is the [й]. After a consonant, **Я** does something different: it softens that consonant and adds [а]. In **пісня** (song), the **Н** before **Я** becomes soft. The same pattern applies to **Ю**: at word start, **юнак** (young man) gives [й] + [у]; after a consonant, it softens and adds [у]. **Є** works identically: **єнот** (raccoon) at word start gives [й] + [е]; after a consonant, like in **синє** (blue, neuter), it softens and adds [е]. Then there is **Ї** — the unique one. **Ї** always equals [й] + [і], no matter where it appears. It never softens a consonant. It only appears at the start of a word, after a vowel, or after an apostrophe: **їжак** (hedgehog), **мої** (my, plural). **Ї** is uniquely Ukrainian — no other Slavic language has it.

Here is the textbook method from Grade 2 for decoding iotated vowels: determine the position first, then decode. **Букви я, ю, є на початку складу позначають два звуки**: [йа], [йу], [йе]. After a consonant, they represent one sound plus softening. Practice: **яблуко** — word start, so Я = [й] + [а]. **Маля** (baby) — Я after a consonant, so Л becomes soft + [а]. **М'ята** (mint) — after apostrophe, so Я = [й] + [а] again (the apostrophe blocks softening).

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

Now for the most important vowel distinction in Ukrainian: **И** versus **І**. These two sounds do not exist in English, and confusing them changes meaning entirely. **Кит** (whale) versus **кіт** (cat). **Дим** (smoke) versus **дім** (house). **Лис** (fox) versus **ліс** (forest). **Сир** (cheese) versus **сік** (juice — a different word, but it shows the І sound clearly). **И** is a back vowel — your tongue pulls back and down. **І** is a front vowel — your tongue pushes forward and up, closer to "ee." Practice hearing and producing this difference. It is the single most important vowel contrast in Ukrainian, and getting it right early will save you from confusion later.

## Читання слів — Reading Words

Now combine everything: letters from M01, the syllable rule, and vowel knowledge. Together they give you the ability to read real Ukrainian words. The key shift is this: stop reading letter by letter. Read syllable by syllable. For any new word, first scan for vowels — they reveal the syllable structure — then build outward. Take **книга** (book): spot the vowels **И** and **А**, so there are two syllables — **кни-га**. Now try **вулиця** (street): vowels **У**, **И**, **Я** — three syllables, **ву-ли-ця**. And **столиця** (capital city): vowels **О**, **И**, **Я** — three syllables, **сто-ли-ця**. Київ — **столиця**.

The more word patterns you recognise, the faster you read. Here are the most common shapes. The CVCV pattern — consonant, vowel, consonant, vowel — is everywhere: **мама**, **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (foot). All two syllables, all open syllables, no surprises. Next, words with a consonant cluster before the second vowel: **школа** (school), **книга**, **парта** (desk). Still two syllables, but your mouth has to handle two consonants in a row before the vowel. Finally, closed-syllable words — just one vowel, closed off by consonants: **дім**, **сон**, **ліс**, **дуб** (oak), **хліб** (bread), **банк**. One syllable each. Recognising these shapes lets your eyes jump ahead and your reading speed increase.

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

A few special letter combinations to watch for while reading. **Щ** always represents two sounds [шч] packed into one letter: **що** (what), **ще** (still/more), **щастя** (happiness). **Ь** (soft sign) has no sound of its own — it softens the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse). The apostrophe (**'**) separates a consonant from an iotated vowel, forcing the two-sound pronunciation: **сім'я** (family), **м'ясо** (meat), **п'ять** (five). Without the apostrophe, the consonant would be softened instead. Do not worry about mastering these fully yet — M03 covers them in complete detail.

<!-- INJECT_ACTIVITY: quiz-read-word-meaning -->

Reading confidence comes from practice, not memorisation. Ukrainian spelling is phonetic — what you see is what you say. Unlike English, there are no silent letters (except **Ь**, which modifies rather than sounds), no surprise pronunciations, no "read" versus "read" confusion. Once you know the letter-sound mappings from M01 and the syllable rule from this module, you can read any Ukrainian word — even words you have never seen before. This is the superpower of Ukrainian's transparent orthography. Trust the letters. They will not lie to you.

## Читаємо разом — Reading Together

Time for progressive reading practice. Start simple, then build up.

**Level 1** (2 syllables): **мама**, **тато**, **вода**, **рука**, **хата**, **каша**, **нога**, **коза**. Read each one: find the vowels, split into syllables, blend. **Level 2** (3 syllables): **аптека**, **молоко**, **людина** (person), **вулиця**, **столиця**. **Level 3** (4+ syllables): **університет**, **бібліотека** (library), **фотографія** (photography). Do not rush — accuracy before speed.

Now read connected text. This short passage uses only **Це** (this is) / **Тут** (here) / **Там** (there) + nouns — no verbs, just identification. Read it syllable by syllable first, then try again faster:

> **Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А це пошта. Тут університет і бібліотека.**

Every word in this passage follows the patterns you have learned. If you can read it fluently, you are ready for M03.

<!-- INJECT_ACTIVITY: quiz-reading-comprehension -->

Here are tips for building reading fluency at home. Look for Ukrainian text anywhere — signs, menus, product labels, social media posts. Sound out the words even if you do not know their meaning yet. The physical act of decoding builds neural pathways for reading. Try reading the same passage three times: first slowly, syllable by syllable; then at a normal pace; then slightly fast. Ukrainian YouTube channels with subtitles are excellent practice — pause the video, read the subtitle, then listen to the pronunciation. The goal is not speed. The goal is automatic decoding — where your brain stops seeing individual letters and starts seeing syllables and whole words. That shift happens through repetition, and it happens faster than you expect.

## Підсумок — Summary

This module gave you three key skills. First: the syllable rule — **«У слові стільки складів, скільки голосних звуків»** — count the vowels to count the syllables, and it works for every Ukrainian word without exception. Second: the ten vowel letters — six simple ones (**А**, **О**, **У**, **Е**, **И**, **І**) that each make one consistent sound, and four iotated ones (**Я**, **Ю**, **Є**, **Ї**) that produce two sounds at the start of a syllable or soften a consonant when they follow one. Third: the reading strategy — scan for vowels, split into syllables, blend, and read. Ukrainian's phonetic spelling means you can now decode any word you encounter, even if you have never seen it before.

Self-check before moving on. Can you answer these questions? How do you count syllables in a Ukrainian word? What are the six vowel sounds? Name the four iotated vowel letters and explain when they represent two sounds. What does **Ь** (soft sign) do? What does the apostrophe do? Final challenge: read **бібліотека** — how many syllables? Five: **бі-блі-о-те-ка**. Five vowels, five syllables. If you got that right, you are ready for M03: Special Signs.

**Deterministic word count: 1767 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 86 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Большакова' — NOT IN VESUM
  ✗ блі — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ кни — NOT IN VESUM

All 86 other words are confirmed to exist in VESUM.

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
