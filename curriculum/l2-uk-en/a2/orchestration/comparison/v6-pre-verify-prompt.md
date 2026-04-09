<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 54: Більше, краще, найкраще (A2, A2.8 [Refinement and Graduation])

## Plan vocabulary to verify

- порівняння (comparison)
- більший (bigger)
- менший (smaller)
- кращий (better)
- гірший (worse)
- найкращий (the best)
- найбільший (the biggest)
- солодший (sweeter)
- цікавіший (more interesting)
- ніж (than)
- набагато (much, significantly)
- трохи (a little, slightly)
- значно (considerably)
- навпаки (on the contrary)

## Sections to research

- **Вищий ступінь: порівнюємо два предмети (Comparative: Comparing Two Things)**: Synthetic comparative: add -ший/-іший to the stem (солодкий → солодший, цікавий → цікавіший). Consonant alternations: г→ж, к→ч, х→ш (дорогий → дорожчий).; Analytic comparative: більш/менш + adjective (більш солодкий, менш відомий). When to prefer analytic over synthetic forms.; Comparison constructions: ніж + Nominative (Київ більший, ніж Львів) and за + Accusative (Київ більший за Львів). Both are correct and interchangeable.
- **Найвищий ступінь: хто найкращий? (Superlative: Who Is the Best?)**: Synthetic superlative: prefix най- to the comparative stem (найсолодший, найцікавіший, найдорожчий).; Analytic superlative: найбільш/найменш + adjective (найбільш популярний, найменш відомий).; Usage in context: Яке місто найбільше в Україні? Хто найкращий футболіст? Яка пора року найгарніша?
- **Особливі форми: більший, кращий, гірший (Irregular Forms)**: Suppletive forms that must be memorized: великий → більший → найбільший, малий → менший → найменший, добрий → кращий → найкращий, поганий → гірший → найгірший, гарний → кращий/гарніший.; Common adverb comparatives: добре → краще, погано → гірше, багато → більше, мало → менше.; Typical errors: *більш кращий (double comparison) — explain why this is wrong.
- **Порівняння у житті (Comparisons in Daily Life)**: Dialogue: two friends discuss which vacation destination is better — comparing prices, weather, food, activities.; Reading practice: a short text ranking Ukrainian cities by size, population, and beauty.; Useful phrases: набагато кращий (much better), трохи більший (a bit bigger), значно цікавіший (significantly more interesting).

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
