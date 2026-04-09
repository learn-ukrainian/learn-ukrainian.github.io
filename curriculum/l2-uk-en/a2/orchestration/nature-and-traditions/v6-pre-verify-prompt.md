<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 60: Пори року і свята (A2, A2.8 [Refinement and Graduation])

## Plan vocabulary to verify

- пора року (season)
- весна (spring)
- літо (summer)
- осінь (autumn)
- зима (winter)
- погода (weather)
- свято (holiday)
- Різдво (Christmas)
- Великдень (Easter)
- традиція (tradition)
- писанка (decorated Easter egg)
- кутя (kutia — Christmas ritual dish)
- колядка (Christmas carol)
- вінок (wreath)
- мороз (frost)
- розквітати (to blossom)

## Sections to research

- **Чотири пори року (The Four Seasons)**: Describing each season with rich vocabulary: весна (spring) — все розквітає, птахи повертаються, стає тепліше; літо (summer) — спекотно, купатися, відпочивати; осінь (autumn) — листя падає, дощить, прохолодно; зима (winter) — сніг, мороз, ковзанка.; Weather expressions: Яка сьогодні погода? Сьогодні сонячно/хмарно/ вітряно. Іде дощ/сніг. Температура — п'ять градусів.; Comparisons between seasons: Літо тепліше за весну. Зима — найхолодніша пора року. Восени більше дощів, ніж влітку.
- **Українські свята: від Різдва до Купала (Ukrainian Holidays: From Christmas to Kupala)**: Winter holidays: Різдво (January 7/December 25 — both dates in modern Ukraine), Святий Вечір, колядки, кутя. Новий рік celebrations.; Spring holidays: Великдень (Easter) — писанки, паски, Христос воскрес! Вербна неділя. Spring traditions of nature awakening.; Summer holidays: Івана Купала (July 7) — вінки на воду, стрибати через вогонь. День Конституції (June 28), День Незалежності (August 24).
- **Що ми робимо у кожну пору року? (What We Do Each Season)**: Seasonal activities: збирати гриби та ягоди (autumn), кататися на лижах (winter), садити квіти (spring), подорожувати (summer).; Narration practice: Коли настає весна, ми завжди... Минулого літа ми поїхали... Цієї зими я планую...; Using aspect naturally: Сніг падав цілий день (imperfective) vs. Сніг нарешті розтанув (perfective).
- **Мої традиції (My Traditions)**: Task: describe your family traditions for one holiday — what you prepare, where you go, who you celebrate with. Integrates all A2 grammar: cases, comparison, aspect, complex sentences.; Reading practice: a Ukrainian teenager describes their family's Різдво traditions — кутя, колядки, подарунки, родинна вечеря.; Discussion prompts: Яке свято вам найбільше подобається? Чому? Які українські традиції ви хотіли б спробувати?

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

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
