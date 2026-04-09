<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

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
- м'який (soft) — apostrophe only (NO soft sign! Й is inherently soft)

## Sections to research

- **М'який знак (The Soft Sign — Ь)**: Ь has no sound. Its job: soften the consonant before it. Three-way distinction (Авраменко Grade 5 p.75, Большакова Grade 2 p.46): м'які приголосні (truly soft, 9 pairs: Д/Д', Т/Т', З/З', С/С', Ц/Ц', Л/Л', Н/Н', Р/Р', ДЗ/ДЗ' + Й), пом'якшені (partially softened: губні, шиплячі, задньоязикові — Ь never after these), тверді (hard). Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=].; Літвінова Grade 5 mnemonic: «ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи» — exactly the 9 consonants Ь can soften. Common patterns: -нь (день, кінь, осінь), -ль (сіль, біль), -ть (мить), -зь (мазь). Practice: учитель, батько, маленький.
- **Апостроф (The Apostrophe)**: Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р before я, ю, є, ї. It keeps the consonant HARD and gives the vowel its full [й] + vowel sound.; Without apostrophe: consonant softens (пісня — Н is soft). With apostrophe: consonant stays hard + vowel = two sounds. сім'я [сім-йа] (family), м'ясо [м-йасо] (meat), п'ять [п-йать] (five), комп'ютер [комп-йутер] (computer). Reading practice: п'ять, дев'ять, м'який, м'яч, об'єкт. IMPORTANT: Only use apostrophe words where apostrophe follows the labial rule (б,п,в,м,ф,р + я,ю,є,ї). Do NOT include під'їзд or з'їзд — these follow the prefix rule (під-/з- + їзд) which is A2+. Also: тварь is a RUSSIAN form — do NOT use it. Ukrainian has тварина (animal).
- **Дзвінкі і глухі (Voiced and Voiceless)**: Consonants come in voiced-voiceless pairs. Hand on throat test: vibration = voiced. Pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.; Ukrainian pronounces voiced consonants clearly at word end — дуб is [дуб], мороз is [мороз]. Voiced consonants переважно (mostly) keep their sound. Exception: легко [лехко]. This is a defining feature of Ukrainian phonetics.; Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs коса (braid).
- **Вимова українських звуків (Pronouncing Ukrainian Sounds)**: И [и] — a unique Ukrainian vowel. It is NOT the same as І [і]. Minimal pairs to hear the difference: бик (bull) vs бік (side), дим (smoke) vs дім (house), лист (letter/leaf) vs ліс (forest), кит (whale) vs кіт (cat). Practice with Anna Ohoiko's И video.; Г [ɦ] vs Ґ [g] — two different letters, two different sounds. Г is a voiced fricative (air flows through narrowed throat): гарно, гора, голова. Its voiceless partner is Х — say Х then add voice to get Г. Ґ is a voiced stop (full throat closure then release): ґанок, ґудзик. Its voiceless partner is К. Ґ is uniquely Ukrainian — an important part of Ukrainian phonetic identity. DO NOT call Г "soft" — in Ukrainian phonetics "м'який" means palatalized, which Г is not.; Р [р] — the Ukrainian rolled/trilled Р. Practice with Anna Ohoiko's video: рука, робота, ранок, риба. An imperfect Р is always understood — focus on getting comfortable, not perfect.
- **Підсумок — Summary**: Self-check: What does Ь do? After which letters does apostrophe appear? Name 3 voiced-voiceless pairs. How is Ukrainian Г different from Ґ? Read these words: сім'я, день, п'ять, гарно.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 3: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 4: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
