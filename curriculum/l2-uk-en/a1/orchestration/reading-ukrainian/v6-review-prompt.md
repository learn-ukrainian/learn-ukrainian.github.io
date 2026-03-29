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

Every Ukrainian first-grader learns a golden rule from their very first буква́р (reading primer). The rule is simple, and it never breaks: **У сло́ві сті́льки складів, скі́льки голосни́х зву́ків** — a word has as many syllables as it has vowel sounds. Before you read any new Ukrainian word, count the vowels. They are the key. Look at the word **мама** (mother). Two vowels — **А** and **А** — so two syllables: **ма-ма**. Now try **молоко** (milk). Three vowels — **О**, **О**, **О** — three syllables: **мо-ло-ко**. What about **банк** (bank)? One vowel — **А** — one syllable. Done.

With that rule in hand, here is your four-step method for reading any Ukrainian word, following the same звукови́й ана́ліз (sound analysis) approach used in Ukrainian schools. Step one: scan the word and spot all the vowels. Step two: split the word into syllables — in Ukrainian, consonants prefer to start a new syllable rather than end one. This is called **складоподіл** (syllable division), and it follows the open-syllable principle. Step three: sound out each syllable separately. Step four: blend them together at natural speed. Walk through it with **аптека** (pharmacy): spot the vowels **А**, **Е**, **А** — that gives three syllables. Split: **а-пте-ка**. Sound out each piece, then blend: **аптека**.

Now apply the method to longer words. Take **шоколад** (chocolate): three vowels (**О**, **О**, **А**), three syllables — **шо-ко-лад**. Try **університет** (university): five vowels (**У**, **І**, **Е**, **И**, **Е**), five syllables: **у-ні-вер-си-тет**. And **бібліотека** (library)? Five vowels (**І**, **І**, **О**, **Е**, **А**), five syllables: **бі-блі-о-те-ка**. Even a word that looks long and intimidating falls apart once you count the vowels. The rule never breaks.

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

## Голосні́ лі́тери (Vowel Letters)

From M01 you already know that Ukrainian has 6 vowel sounds but writes them with 10 vowel letters. The first six are straightforward — each letter makes exactly one consistent sound, every time, no exceptions:

- **А** — as in **аптека** (pharmacy)
- **О** — as in **молоко** (milk)
- **У** — as in **рука** (hand)
- **Е** — as in **вечір** (evening)
- **И** — as in **кит** (whale)
- **І** — as in **кіт** (cat)

These six are completely reliable. What you see is what you say.

The remaining four vowel letters — **Я**, **Ю**, **Є**, **Ї** — are called iotated vowels, and they have a dual nature. When **Я** appears at the start of a word or after another vowel, it produces two sounds: [й] + [а]. The word **яблуко** (apple) starts with **Я**, so you hear [йа]-блу-ко. In **моя** (my, feminine), the **Я** comes after the vowel **О** — again two sounds: мо-[йа]. But after a consonant, **Я** does something different: it softens that consonant and adds only [а]. In **пісня** (song), the **Н** before **Я** becomes soft — no [й] sound appears. The same dual pattern applies to **Ю** (either [йу] or softening + [у]) and **Є** (either [йе] or softening + [е]). Look at **людина** (person): the **Л** is softened by **Ю**, so you hear soft Л + [у], not [й]. And in **вечірнє** (evening, neuter adjective), the **Н** is softened by **Є**.

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

**Ї** stands apart from the other three. It always produces two sounds — [йі] — with no exceptions and no other behavior. It never softens a consonant before it, because it simply never appears directly after a consonant. You find **Ї** only at the start of a word like **їжак** (hedgehog), after a vowel as in **країна** (country), or after an apostrophe as in **з'їсти** (to eat up). **Ї** is a distinctly Ukrainian letter — Russian has no equivalent.

One more critical distinction: **И** versus **І**. These are two separate phonemes that change meaning. Compare **кит** (whale) with **кіт** (cat), or **дим** (smoke) with **дім** (house). The sound [и] sits further back in the mouth; [і] is a high front vowel, closer to the English "ee." Mixing them up changes one word into a completely different one. Listen carefully to model pronunciations before practising — this difference is subtle but essential.

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

## Чита́ння слів (Reading Words)

Counting vowels and splitting syllables is the scaffold. The goal is fluency — reading whole words without pausing at each letter. Here is the reading strategy one more time, applied to real words: (1) spot the vowels first, because they are the syllable cores; (2) build the consonant clusters around them; (3) read syllable by syllable; (4) repeat until the word flows as a single unit. Try it with **книга** (book): two vowels, **И** and **А**, so two syllables — **кни-га**. Now read it again faster: **книга**. That is the rhythm.

Ukrainian words tend to follow a few common patterns. The easiest are words where consonants and vowels alternate evenly: **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (leg). Each syllable is open — it ends on a vowel — so blending is smooth. Next come words with a consonant cluster before a vowel, which are slightly harder: **школа** (school), **книга** (book), **банда** (gang), **парта** (school desk). Your mouth has to handle two consonants in a row before reaching the vowel. Finally, closed-syllable words end on a consonant: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank). These are short — usually one syllable — but they build confidence because you hear the whole word instantly.

<!-- INJECT_ACTIVITY: quiz-read-and-match -->

Here is a reading drill across three difficulty levels.

**Level 1 — two-syllable words:** Read each word first split, then blended.
**Ма-ма** → **мама**. **Та-то** → **тато**. **Во-да** → **вода**. **Ру-ка** → **рука**. **Ха-та** → **хата**. **Ка-ша** → **каша**.

**Level 2 — three-syllable words:** Split, then blend.
**А-пте-ка** → **аптека** (pharmacy). **Мо-ло-ко** → **молоко** (milk). **Лю-ди-на** → **людина** (person). **Ву-ли-ця** → **вулиця** (street).

**Level 3 — four or more syllables:** Use the vowel-counting method to read these:
**У-ні-вер-си-тет** → **університет** (university) — 5 syllables. **Бі-блі-о-те-ка** → **бібліотека** (library) — 5 syllables. **Фо-то-гра-фі-я** → **фотографія** (photography) — 5 syllables.

Now read these Ukrainian city names: **Ки-їв** (Kyiv — notice the **Ї**), **О-де-са** (Odesa), **Хар-ків** (Kharkiv), **Дні-про** (Dnipro), **Пол-та-ва** (Poltava).

Before moving on, here is a preview of three special features you will meet in M03 — not the focus today, but worth recognizing when they appear. First: **Щ** always reads as [шч] — one letter, two sounds. In **що** (what) and **ще** (still, yet), do not read it as [ш] alone. Second: **Ь** (м'яки́й знак, the soft sign) has no sound of its own. It only softens the consonant before it. In **день** (day), the **Н** is soft. In **сіль** (salt), the **Л** is soft. In **кінь** (horse), the **Н** is soft. Think of **Ь** as a silent softener. Third: the apostrophe (**'**) does the opposite — it separates a consonant from a following iotated vowel, preventing softening. In **сім'я** (family), the **М** stays hard and then **Я** produces its full [йа]. Same in **м'ясо** (meat) and **п'ять** (five). These three features will be drilled thoroughly in M03; for now, just recognize them when you see them.

> <div class="dialogue-line"><span class="speaker">Аня:</span> Бі-блі-о-те-ка... **бібліотека**! *(Library!)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Так! А це? *(Yes! And this one?)*</div>
> <div class="dialogue-line"><span class="speaker">Аня:</span> Я-блу-ко... **яблуко**! *(Apple!)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> А це? *(And this?)*</div>
> <div class="dialogue-line"><span class="speaker">Аня:</span> Шо-ко-лад... **шоколад**! *(Chocolate!)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> **Шоколад** — сма́чно! *(Chocolate — delicious!)*</div>

Аня uses the syllable method — split, then blend — and reads three words she has never seen before. Марко confirms each one. Notice how even a five-syllable word like **бібліотека** becomes manageable once you count the vowels and take it piece by piece.

## Підсумок — Summary

Self-check — test yourself on the key concepts from this module:

- **How do you count syllables in a Ukrainian word?** → Count the vowels. Each vowel = one syllable.
- **What are the 6 vowel sounds?** → [а], [о], [у], [е], [и], [і].
- **Name the 4 iotated vowel letters.** → **Я**, **Ю**, **Є**, **Ї**.
- **What do Я, Ю, Є do at the start of a word?** → They produce two sounds: **Я** = [й] + [а], **Ю** = [й] + [у], **Є** = [й] + [е].
- **What does Ї always produce?** → Always [йі] — two sounds, no exceptions.
- **What does Ь do?** → It softens the consonant before it but has no sound of its own.
- **What does the apostrophe do?** → It separates the consonant from a following iotated vowel, so no softening occurs.
- **Read this word and count syllables: бібліотека.** → **Бі-блі-о-те-ка**. Five syllables (five vowels: **І**, **І**, **О**, **Е**, **А**).

**Deterministic word count: 1443 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 63 words | Not found: 20 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Аня — NOT IN VESUM
  ✗ Пол — NOT IN VESUM
  ✗ ана — NOT IN VESUM
  ✗ блу — NOT IN VESUM
  ✗ блі — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ голосни — NOT IN VESUM
  ✗ звукови — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ ків — NOT IN VESUM
  ✗ льки — NOT IN VESUM
  ✗ м'яки — NOT IN VESUM
  ✗ ння — NOT IN VESUM
  ✗ пте — NOT IN VESUM
  ✗ скі — NOT IN VESUM
  ✗ сло — NOT IN VESUM
  ✗ сма — NOT IN VESUM
  ✗ сті — NOT IN VESUM
  ✗ тери — NOT IN VESUM
  ✗ чно — NOT IN VESUM

All 63 other words are confirmed to exist in VESUM.

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
