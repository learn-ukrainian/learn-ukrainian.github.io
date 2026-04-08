<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 20: Місцевий відмінок у нових контекстах (A2, A2.3 [Dative Case])

## Plan vocabulary to verify

- місцевий (locative (case))
- абстрактний (abstract)
- минулий (past, previous)
- місяць (month)
- тиждень (week)
- телефон (phone, telephone)
- подорож (journey, trip)
- зустріч (meeting, encounter)
- думка (thought, opinion)
- проблема (problem)
- дитинство (childhood)
- молодість (youth)
- майбутнє (future)
- освіта (education)
- мистецтво (art)

## Sections to research

- **Місцевий з абстрактними іменниками (Locative with Abstract Nouns)**: A1 taught locative for physical location (у місті, на вулиці). Now expanding to abstract domains and contexts.; Common abstract locative phrases: у житті (in life), в освіті (in education), у політиці (in politics), на роботі (at work), в економіці (in economics), у мистецтві (in art).; Pattern: у/в + abstract noun in locative = "in the domain/field of." Note: на роботі (not *у роботі) — на is fixed for робота.
- **Часовий місцевий відмінок (Temporal Locative)**: Months: у січні, у лютому, у березні... all months use у/в + locative. Masculine months in -ень: -ні (січень→у січні). Neuter місяць compounds: у минулому місяці, у наступному місяці.; Weeks: на цьому тижні, на минулому тижні, на наступному тижні. Note: тиждень uses на (not у).; Life periods: у дитинстві (in childhood), у молодості (in youth), у старості (in old age), у минулому (in the past), у майбутньому (in the future).
- **По телефону, по радіо: місцевий із прийменником «по» (Locative with "po")**: Topic/means with по + locative: по телефону (by phone), по радіо (on the radio), по пошті (by mail), по дорозі (on the way).; Distinction: говорити по телефону (the medium of communication) vs. говорити про телефон (about the phone as a topic). По + locative = means/channel. Про + accusative = topic.; Common phrases: Я подзвоню по телефону. Ми почули по радіо. Він надіслав по пошті. Зустрілися по дорозі додому.
- **Місцевий відмінок: від місця до сенсу (From Place to Meaning)**: Summary: locative is not just "where" — it answers де? (location), коли? (time), and як? (means/channel).; Consolidation table: physical (у місті), abstract (у житті), temporal (у січні), means (по телефону) — all locative, four different functions.; Practice: building sentences that use 2-3 locative functions together: У минулому місяці я розмовляв по телефону з другом у Києві.

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
