<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 3: Special Signs (A1, A1.1 [Sounds, Letters, and First Contact])

## Plan vocabulary to verify

- сім'я (family) — apostrophe word
- день (day) — soft sign after Н
- сіль (salt) — soft sign after Л
- м'ясо (meat) — apostrophe after М
- п'ять (five) — apostrophe after П
- гарно (nicely, beautifully) — Г [ɦ] practice
- риба (fish) — Р and И practice
- батько (father, formal) — soft sign
- учитель (teacher) — soft sign at end
- дев'ять (nine) — apostrophe
- комп'ютер (computer) — apostrophe in cognate
- м'який (soft) — apostrophe + soft sign

## Sections to research

- **М'який знак (The Soft Sign — Ь)**: Ь has no sound. Its job: soften the consonant before it. Ukrainian distinguishes hard (тверді) and soft (м'якшені) consonants. Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=]. Common words: день (day), сіль (salt), кінь (horse), мідь (copper). The Ь appears only after consonants, never at word start.; Where Ь commonly appears: -нь: день, кінь, осінь -ль: сіль, біль (pain) -ть: мить, путь -зь: мазь (ointment) Practice: учитель (teacher), батько (father), маленький (small).
- **Апостроф (The Apostrophe)**: Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р before я, ю, є, ї. It keeps the consonant HARD and gives the vowel its full [й] + vowel sound.; Without apostrophe: consonant softens (пісня — Н is soft). With apostrophe: consonant stays hard + vowel = two sounds. сім'я [сім-йа] (family), м'ясо [м-йасо] (meat), п'ять [п-йать] (five), комп'ютер [комп-йутер] (computer). Reading practice: п'ять, дев'ять, м'який, м'яч, об'єкт.
- **Дзвінкі і глухі (Voiced and Voiceless)**: Consonants come in voiced-voiceless pairs. Hand on throat test: vibration = voiced. Pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.; Ukrainian pronounces voiced consonants clearly at word end — дуб is [дуб], мороз is [мороз]. Every consonant keeps its true sound in every position. This is a defining feature of Ukrainian phonetics.; Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs коса (braid).
- **Вимова українських звуків (Pronouncing Ukrainian Sounds)**: И [и] — a unique Ukrainian vowel. It is NOT the same as І [і]. Minimal pairs to hear the difference: бик (bull) vs бік (side), дим (smoke) vs дім (house), лист (letter/leaf) vs ліс (forest), кит (whale) vs кіт (cat). Practice with Anna Ohoiko's И video.; Г [ɦ] vs Ґ [g] — two different letters, two different sounds. Г is a soft voiced sound (гарно, гора, голова). Ґ is a hard sound (ґанок, ґудзик). Ґ is uniquely Ukrainian — an important part of Ukrainian phonetic identity.; Р [р] — the Ukrainian rolled/trilled Р. Practice with Anna Ohoiko's video: рука, робота, ранок, риба. An imperfect Р is always understood — focus on getting comfortable, not perfect.
- **Підсумок — Summary**: Self-check: What does Ь do? After which letters does apostrophe appear? Name 3 voiced-voiceless pairs. How is Ukrainian Г different from Ґ? Read these words: сім'я, день, п'ять, гарно.

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
