<!-- version: 1.0.0 | updated: 2026-03-27 -->
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
  words: 500
  points:
  - 'Apply M01 letter knowledge to read real words fluently. Strategy: don''t read
    letter-by-letter. Read syllable-by-syllable. Start with the vowels (find them
    first), then build outward. Example: книга — find vowels И, А → кни-га → read.'
  - 'Common word patterns for reading practice: CVCV: мама, тато, каша, вода, рука,
    хата, коза, нога CVCCV: школа, книга, банда, парта CVC: дім, сон, ліс, дуб, хліб,
    банк. The more patterns you see, the faster you read.'
  - 'Progressive difficulty — start simple, build up: Level 1 (2 syllables):
    мама, тато, вода, рука, хата, каша. Level 2 (3 syllables): аптека, молоко, людина,
    вулиця. Level 3 (4+ syllables): університет, бібліотека, фотографія.
    Ukrainian city names: Ки-їв, Льві-в, О-де-са, Хар-ків, Дні-про, Пол-та-ва.'
  - 'Special letter combinations to watch for (preview for M03): Щ is always [шч] — що, ще.
    Ь has no sound — it softens: день, сіль, кінь. Apostrophe separates: сім''я,
    м''ясо, п''ять. These will be explored fully in M03.'
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

> <div class="dialogue-line"><span class="speaker">Анна:</span> Що це? *(What is this?)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Це аптека. *(This is a pharmacy.)*</div>
> <div class="dialogue-line"><span class="speaker">Анна:</span> Ап-те-ка? *(Ap-te-ka?)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Так! *(Yes!)*</div>

To read Ukrainian fluently, you need to understand syllables (**склади**). The rule is simple: a word has exactly as many syllables as it has vowels (**голосні звуки**). Count the vowels, and you instantly know the number of syllables. You simply count the vowels, and you instantly know the number of syllables. The word **мама** (mother) contains two vowels, so it has two syllables. The word **молоко** (milk) features three vowels, meaning it has three syllables. A short word like **банк** (bank) has only one vowel, so it forms one syllable. Spot the vowels, and you can map out the word.

Ukrainian syllable division (**складоподіл**) follows the "Open Syllable Principle" (**відкритий склад**). Consonants prefer to start the next syllable rather than closing out the previous one, naturally ending on a clear vowel sound. The word **молоко** (milk) divides perfectly and cleanly into **мо-ло-ко**. But what happens when consonants bunch up, like in the word **аптека** (pharmacy)? Instead of dividing it as "ап-те-ка", the consonant cluster prefers to move forward together, giving us the division **а-пте-ка**. The consonant cluster ПТ starts the new syllable. This constant push toward vowels is why spoken Ukrainian sounds so continuous and open.

Ukrainian children learn to read using a method called **звуковий аналіз** (sound analysis). When you encounter a new word, follow these steps:
1. Find all the vowels.
2. Mark the syllable boundaries (consonants prefer to start the next syllable).
3. Sound out each syllable slowly.
4. Blend them together at a natural speed. Take the long word **університет** (university). Find the vowels, and you get **у-ні-вер-си-тет**. Try saying each block individually, then blend them. Now try **шоколад** (chocolate), which divides seamlessly into **шо-ко-лад**. Read it block by block. Finally, try a shorter word: **каша** (porridge). It smoothly divides into **ка-ша**. This is the exact method native speakers use to build their reading confidence from day one.

<!-- INJECT_ACTIVITY: fill-in -->

<!-- INJECT_ACTIVITY: quiz -->

## Голосні літери (Vowel Letters)

> <div class="dialogue-line"><span class="speaker">Анна:</span> Хто це? *(Who is this?)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Це кіт. *(This is a cat.)*</div>
> <div class="dialogue-line"><span class="speaker">Анна:</span> Де кит? *(Where is the whale?)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Кит там. *(The whale is there.)*</div>

Ukrainian has six vowel sounds represented by ten letters. The six "Simple Vowels" are **А**, **О**, **У**, **Е**, **И**, and **І**. Each letter represents exactly one sound, every single time. They are completely consistent. When you see the letter **А**, it always makes the [а] sound. When you see **О**, it always makes the [о] sound. They are straightforward and form the stable, predictable core of the language.

A critical distinction in Ukrainian is between the letters **И** and **І**. The letter **І** makes an [і] sound. It is a high, tense sound, and you pronounce it with a slightly "smiling" mouth, very much like the "ee" in "see". On the other hand, the letter **И** makes an [и] sound. This sound is noticeably lower and much more "relaxed", somewhat resembling the "i" in "bit", but produced slightly further back in the mouth. It is absolutely crucial to distinguish them because swapping them will completely change the meaning of words. Consider these critical minimal pairs: **кит** (whale) versus **кіт** (cat). One single letter changes a massive marine mammal into a small house pet! Another vital example is **дим** (smoke) versus **дім** (house). Listen to Anna's pronunciation videos for each of these letters—the difference might seem subtle at first, but it changes the meaning entirely.

The Iotated Vowels (**йотовані**) **Я**, **Ю**, and **Є** play a dual role depending on where they appear. At the very start of a word, or immediately after another vowel, they represent two distinct sounds combined: a [й] sound followed by their corresponding basic vowel. For example, at the beginning of the word **яблуко** (apple), the letter Я makes a sharp [й] + [а] sound. Similarly, in the word **моя** (my), the letter Я follows another vowel and makes the exact same double sound. However, when these letters appear immediately after a consonant, their behavior changes entirely. Instead of making a double sound, they soften that preceding consonant and provide a single vowel sound. For instance, in the word **пісня** (song), the Я softens the consonant Н and sounds simply like [а]. Another great example is **людина** (person), where the Ю softens the Л and provides the [у] sound.

The letter **Ї** ALWAYS represents two sounds: [й] + [і]. It never softens the preceding consonant. It appears at the start of a word, after another vowel, or after an apostrophe. You will see it in words like **Україна** (Ukraine), **поїзд** (train), and **їжа** (food).

<!-- INJECT_ACTIVITY: match-up -->

## Читання слів (Reading Words)

> <div class="dialogue-line"><span class="speaker">Анна:</span> Де університет? *(Where is the university?)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Університет тут. *(The university is here.)*</div>
> <div class="dialogue-line"><span class="speaker">Анна:</span> Де бібліотека? *(Where is the library?)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Бібліотека там. *(The library is there.)*</div>

To read Ukrainian words smoothly, use "The Lego Method." Instead of reading letter-by-letter, scan the word for its vowels and build syllables around them. For example, with the word **книга** (book): First, scan the word and locate the vowels: И and А. Second, build the syllables around these anchors to get the structure **кни-га**. Finally, blend them together naturally and read the word. By deliberately starting with the vowels and building outward, you will drastically increase your reading speed and overall comprehension.

Pattern 1: CVCV (Consonant-Vowel-Consonant-Vowel). Practice reading these alternating syllable words with a steady pace: **мама** (mother), **тато** (father), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), and **нога** (leg). Notice how naturally your voice bounces from a consonant directly to a vowel. Maintaining a steady pace through these fundamental words will actively train your brain to recognize this essential structural pattern instantly.

Pattern 2: CVCCV and CVC. When consonants group together, the rule of one vowel equals one syllable still holds. Here are words with consonant clusters: **школа** (school), **парта** (desk), and **банда** (gang). Here are examples of the CVC pattern (single-syllable words): **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), and **хліб** (bread). When practicing these specific CVC words, focus on the abrupt, clean stop at the end of the word. They are compact, powerful words that form the vital core of everyday Ukrainian vocabulary.

Progressive Difficulty Level 2: 3-syllable words. Practice reading these three-syllable words smoothly: **аптека** (pharmacy), **молоко** (milk), **людина** (person), **вулиця** (street), and **столиця** (capital). You will also see this in important phrases like **Київ — столиця України** (Kyiv is the capital of Ukraine). As you read them, keep your eyes constantly moving forward to the next vowel core.

Progressive Difficulty Level 3: 4+ syllables and City Names. Break these longer words down around their vowels: **університет** (university), **бібліотека** (library), and **фотографія** (photography). Practice reading these major Ukrainian city names: **Київ** (Kyiv), **Львів** (Lviv), **Одеса** (Odesa), **Харків** (Kharkiv), **Дніпро** (Dnipro), and **Полтава** (Poltava). Each city gives you an excellent opportunity to practice your syllable blending.

Special signs preview. Here are three special visual markers that alter how you read (to be explored fully in the next module): First, the letter **Щ** is unique because it always represents a double sound, [ш] + [ч]. You can see it in common words like **що** (what) and **ще** (more). Second, the **Ь** (soft sign) is completely silent, but it fundamentally changes the preceding consonant, making it soft. Look at the words **день** (day) and **сіль** (salt). Finally, the Apostrophe forces a hard break or separation between sounds, directly preventing them from blending together. You will see this specific marker in words like **сім’я** (family) and **м’ясо** (meat).

<!-- INJECT_ACTIVITY: quiz -->

## Підсумок — Summary

You have now learned the most powerful tools for reading Ukrainian. Remember that the absolute key to unlocking any new word is applying the syllable rule, perfectly balanced with a deep understanding of the ten vowel letters. Use this simple self-check list to verify your phonetic progress:

* How do you count syllables in a Ukrainian word? (Count the vowels!)
* What are the sіx basic vowel sounds? ([а], [о], [у], [е], [и], [і])
* Name the four iotated vowel letters. (Я, Ю, Є, Ї)
* What does the letter Ь do? (It softens the preceding consonant and has no sound of its own)
* What does the apostrophe do? (It forces a hard separation between sounds)
* Challenge: How many syllables are in the word **бібліотека** (library)? (There are 5 syllables, because there are 5 vowels!)

Keep practicing these fundamental reading patterns, and very soon, decoding Ukrainian text will feel completely natural and rhythmic.

**Deterministic word count: 1467 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 67 words | Not found: 9 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Дніпро — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Полтава — NOT IN VESUM
  ✗ Харків — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ пте — NOT IN VESUM

All 67 other words are confirmed to exist in VESUM.

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
