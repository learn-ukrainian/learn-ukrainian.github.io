<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 49: Присвійні прикметники (B1, B1.4 [Comparison & Word Formation])

## Plan vocabulary to verify

- присвійний (possessive — adjective expressing belonging)
- належність (belonging/ownership — what присвійні прикметники express)
- батьків (father's — присвійний прикметник from батько)
- материн (mother's — присвійний прикметник from мати)
- сестрин (sister's — присвійний прикметник from сестра)
- бабусин (grandmother's — присвійний прикметник from бабуся)
- дідусів (grandfather's — присвійний прикметник from дідусь)
- Шевченків (Shevchenko's — присвійний прикметник from Шевченко)
- Лесин (Lesya's — присвійний прикметник from Леся)
- Франків (Franko's — присвійний прикметник from Франко)
- чергування (alternation — consonant changes in word formation: г→ж, к→ч, х→ш)
- відміна (declension class — I or II, determines suffix choice)
- спадщина (heritage/legacy — батьківська спадщина)
- творчість (creative work/oeuvre — Шевченкова творчість)
- поезія (poetry — Франкова поезія)
- братів (brother's — from брат)
- учителів (teacher's — from учитель)
- Петрів (Petro's — from Петро)
- Маріїн (Mariya's — from Марія, -їн after -й stem)
- Олексіїв (Oleksiy's — from Олексій, -їв after -й stem)
- непрямий відмінок (oblique case — where full adjective forms appear)
- коротка форма (short form — nominative of присвійні прикметники)

## Sections to research

- **Присвійні прикметники: що це і навіщо**: Definition (Заболотний Grade 6 p.147): Присвійні прикметники вказують на належність предмета певній особі або тварині і відповідають на питання чий? чия? чиє? чиї? Приклади: батьків дім (whose house? — father's), сестрина книжка (whose book? — sister's), Шевченкова поезія (whose poetry? — Shevchenko's).; Three groups of adjectives by meaning (Заболотний Grade 6 p.147 table): Якісні — describe quality (великий, розумний). Відносні — describe material, origin (дерев'яний, міський). Присвійні — express belonging (батьків, Лесин). Key distinction: присвійні answer ЧИЙ?, not ЯКИЙ?; Why Ukrainian uses присвійні прикметники: Ukrainian naturally says батьків дім, not *дім батька (though the genitive phrase exists too). Шевченкова поезія is more natural than поезія Шевченка in many contexts. This is a productive, living category in Ukrainian — unlike English, where possessive adjectives are limited to a few pronouns (my, your, his).
- **Творення від II відміни: суфікси -ів/-їв**: Formation from masculine nouns (II відміна — Литвінова Grade 6 p.193): Base form: батько → батьків, брат → братів, дід → дідів, друг → другів, тренер → тренерів, директор → директорів. The suffix -ів is added to the noun stem.; Nouns ending in -й (soft stem, II відміна): Андрій → Андріїв, Олексій → Олексіїв, Сергій → Сергіїв. The suffix becomes -їв after -й stems. Rule: stem ending in голосний + й → drop -й, add -їв.; Consonant alternations in formation (Авраменко Grade 6 p.137): Some stems undergo changes: Олег → Олежів? No — Олегів (no alternation in -ів forms). Шевченко → Шевченків (treat as II відміна). Франко → Франків. Note: these are straightforward — the alternations г→ж, к→ч happen in -ин forms, not -ів.
- **Творення від I відміни: суфікси -ин/-ін (-їн)**: Formation from feminine nouns (I відміна — Голуб Grade 6 p.124): мати → материн, сестра → сестрин, бабуся → бабусин, тітка → тітчин (к→ч alternation!), Леся → Лесин, подруга → подружин (г→ж alternation!).; Consonant alternations in -ин forms (Авраменко Grade 6 p.137): г → ж: подруга → подружин, Ольга → Ольжин. к → ч: тітка → тітчин, Оленка → Оленчин, Даринка → Даринчин. х → ш: Солоха → Солошин, сваха → свашин. These alternations are consistent and predictable.; Nouns with stem ending in -й (or -і): Марія → Маріїн, Софія → Софіїн, Наталія → Наталіїн. The suffix becomes -їн. But from short forms: Наталка → Наталчин (к→ч!), Марійка → Марійчин (к→ч!). Learners must know WHICH name form they are deriving from.
- **Відмінювання і вживання**: Mixed declension pattern (Литвінова Grade 6 p.193): Номінатив: коротка форма — батьків (m), батькова (f), батькове (n), батькові (pl). Непрямі відмінки: повна форма — батькового (gen m/n), батьковій (dat f), батьковим (instr m/n). This mixed pattern is unique to присвійні прикметники.; Declension table for -ін type: материн (m nom), материна (f nom), материне (n nom), материні (pl nom). Oblique: материного (gen m/n), материній (dat f), материним (instr m/n). Parallel to the -ів type but with different base.; Usage patterns and stylistic notes: батьків дім (natural, common) = дім батька (also correct, slightly more formal/neutral). Шевченкова поезія (elevated, literary) = поезія Шевченка (standard). In modern Ukrainian, присвійні прикметники are fully productive for names and family terms: Тарасів, Олексіїв, Маріїн. Capitalization: Шевченкові вірші (lowercase ш? No — Шевченкові is from a proper name, so uppercase: Шевченкові вірші).

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

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
