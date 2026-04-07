<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 1: Ласкаво просимо до рівня А2 (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- відмінок (case)
- називний (nominative)
- знахідний (accusative)
- місцевий (locative)
- кличний (vocative)
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- наголос (stress (accent))
- милозвучність (euphony, melodiousness)
- огляд (review, overview)
- система (system)
- правило (rule)

## Sections to research

- **Пригадуємо відмінки (Reviewing Cases)**: Quick review of the four A1 cases: Nominative (Хто? Що?), Accusative (Кого? Що?), Locative (Де? На кому? На чому?), and Vocative (звертання).; Practice exercises: identifying case usage in sentences and declining familiar noun-adjective pairs.; Introducing the full case system map: showing all seven cases and highlighting the three new ones for A2 (Genitive, Dative, Instrumental).
- **Магія української фонології (The Magic of Ukrainian Phonology)**: Revisiting key vowel alternations: о/і, е/і (e.g., стіл/стола, Київ/Києва). Explaining the 'closed syllable' rule.; Revisiting key consonant alternations: the first palatalization (г/ж, к/ч, х/ш) and its effect on noun and verb forms (нога/ніжка, рука/ручка).; Introduction to stress patterns: identifying common patterns and using stress to disambiguate words (e.g., замок "castle" vs. замок "lock").
- **Милозвучність мови: евфонія (The Melody of Language: Euphony)**: Formalizing the rules for у/в and і/й alternation based on surrounding sounds (vowel vs. consonant).; Explaining the use of з/зі/із before difficult consonant clusters.; Practice creating fluid sentences by choosing the correct euphonic particle.
- **Що нас чекає на рівні А2? (What Awaits Us in A2?)**: A clear roadmap of the A2 curriculum: introduction to aspect, mastering all seven noun cases, verb conjugation patterns, and verbs of motion.; Setting expectations: A2 is where learners begin to express more complex ideas and move beyond simple statements.

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
