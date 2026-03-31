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

- **Склади (Syllables)**: Большакова Grade 1 p.25: 'У слові стільки складів, скільки голосних звуків.' Count the vowels, count the syllables. This rule never breaks. ма-ма (2 vowels = 2 syllables), мо-ло-ко (3 vowels = 3 syllables), банк (1 vowel = 1 syllable).; How Ukrainian children learn to read — складові ланцюжки (syllable chains): Start with a consonant + vowel pair: М → ма, мо, му, ми. Then reverse: ам, ом, ум. Then build words: ма-ма, мо-ло-ко. This is bottom-up: sound → syllable → word. (Захарійчук Grade 1, p.46; Большакова Grade 1, p.25); Звуковий аналіз слова (Большакова p.29): 1) Визначаю голосні звуки 2) Ділю слово на склади 3) Ставлю наголос 4) Позначаю приголосні звуки. Chin-test for syllable counting (Кравцова Grade 2, p.13): put your palm under your chin, say the word — each chin touch = one syllable.
- **Голосні літери (Vowel Letters)**: Review from M01: 6 sounds, 10 letters. Now learn all 10 individually. Simple vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і]. Each makes ONE consistent sound — no surprises.; Iotated vowels (two sounds or softening): Я = [йа] at word start (яблуко) or after vowel (моя). After consonant: softens it + [а] (пісня — Н is softened). Ю = [йу] or softening + [у]. Є = [йе] or softening + [е]. Ї = ALWAYS [йі] — never softens. Only at word start, after vowel, or after apostrophe. Unique to Ukrainian.; Critical minimal pairs: И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім (house). Listen to Anna's pronunciation videos for each — the difference is subtle but changes meaning.
- **Читання слів (Reading Words)**: Apply складові ланцюжки to real words. Don't read letter-by-letter — read syllable-by-syllable. Use звуковий аналіз: find vowels first, split into склади, then blend. Example: книга — find vowels И, А → кни-га → read.; Progressive difficulty using Ukrainian classification (односкладові → багатоскладові): односкладові (1 syllable): дім, сон, ліс, дуб, хліб. двоскладові (2 syllables): ма-ма, та-то, во-да, ру-ка, ха-та, ка-ша. трискладові (3 syllables): ап-те-ка, мо-ло-ко, лю-ди-на, ву-ли-ця. багатоскладові (4+ syllables): у-ні-вер-си-тет, біб-лі-о-те-ка, фо-то-гра-фі-я.; Ukrainian city names as reading practice: Ки-їв, Льві-в, О-де-са, Хар-ків, Дні-про, Пол-та-ва. Note the different syllable counts and structures.
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
