<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 2: Reading Ukrainian (A1, A1.1 [Sounds, Letters, and First Contact])

## Plan vocabulary to verify

- яблуко (apple) — Я at word start = [йа]
- молоко (milk) — 3 syllables, all simple vowels
- людина (person) — Л + Ю combination
- вулиця (street) — Ц sound practice
- столиця (capital) — Київ — столиця України
- каша (porridge) — Ш sound practice
- пісня (song) — softening by Я after consonant
- університет (university) — long word practice
- бібліотека (library) — 5 syllables
- фотографія (photography) — long word with Ф
- шоколад (chocolate) — Ш + О + К combination

## Sections to research

- **Склади (Syllables)**: Большакова Grade 1 p.25: 'У слові стільки складів, скільки голосних звуків.' Count the vowels, count the syllables. This rule never breaks. ма-ма (2 vowels = 2 syllables), мо-ло-ко (3 vowels = 3 syllables), банк (1 vowel = 1 syllable).; How to read a new word: 1. Find the vowels (they're the syllable cores) 2. Split at syllable boundaries (consonants prefer starting new syllables) 3. Sound out each syllable 4. Blend into the full word at natural speed Practice: а-пте-ка, у-ні-вер-си-тет, шо-ко-лад. Note: Ukrainian phonetic syllable division (складоподіл) follows the open-syllable principle — consonants prefer starting new syllables.; Following Большакова p.29 звуковий аналіз method: identify vowels, divide into syllables, then read. This is how Ukrainian children learn.
- **Голосні літери (Vowel Letters)**: Review from M01: 6 sounds, 10 letters. Now learn all 10 individually. Simple vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і]. Each makes ONE consistent sound — no surprises.; Iotated vowels (two sounds or softening): Я = [йа] at word start (яблуко) or after vowel (моя). After consonant: softens it + [а] (пісня — Н is softened). Ю = [йу] or softening + [у]. Є = [йе] or softening + [е]. Ї = ALWAYS [йі] — never softens. Only at word start, after vowel, or after apostrophe. Unique to Ukrainian.; Critical minimal pairs: И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім (house). Listen to Anna's pronunciation videos for each — the difference is subtle but changes meaning.
- **Читання слів (Reading Words)**: Apply M01 letter knowledge to read real words fluently. Strategy: don't read letter-by-letter. Read syllable-by-syllable. Start with the vowels (find them first), then build outward. Example: книга — find vowels И, А → кни-га → read.; Common word patterns for reading practice: CVCV: мама, тато, каша, вода, рука, хата, коза, нога CVCCV: школа, книга, банда, парта CVC: дім, сон, ліс, дуб, хліб, банк. The more patterns you see, the faster you read.; Progressive difficulty — start simple, build up: Level 1 (2 syllables): мама, тато, вода, рука, хата, каша. Level 2 (3 syllables): аптека, молоко, людина, вулиця. Level 3 (4+ syllables): університет, бібліотека, фотографія. Ukrainian city names: Ки-їв, Льві-в, О-де-са, Хар-ків, Дні-про, Пол-та-ва.
- **Підсумок — Summary**: Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel sounds? Name the 4 iotated vowel letters. What does Ь do? What does the apostrophe do? Read this word: бібліотека — how many syllables?

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
