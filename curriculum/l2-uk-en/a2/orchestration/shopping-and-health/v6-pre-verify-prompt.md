<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 15: На ринку та у лікаря (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- ринок (market)
- кілограм (kilogram)
- пляшка (bottle)
- здоров'я (health)
- температура (temperature, fever)
- рецепт (prescription, recipe)
- аптека (pharmacy)
- ліки (medicine)
- кашель (cough)
- апетит (appetite)
- помідор (tomato)
- нежить (runny nose, cold)
- алергія (allergy)
- таблетка (pill, tablet)
- шматок (piece)

## Sections to research

- **На ринку: скільки вам? (At the Market: How Much Do You Want?)**: Quantity + Genitive: кілограм яблук, пів кіло помідорів, літр молока, пляшка води, пачка масла, десяток яєць.; Natural market dialogue: greeting the vendor, asking what is fresh today, requesting quantities, asking the price, paying. Based on real market interactions — vendor offers tastes, suggests alternatives.; Genitive after measure words: склянка соку (a glass of juice), шматок хліба (a piece of bread), банка меду (a jar of honey). Practice with partitive Genitive.
- **У лікаря: що вас турбує? (At the Doctor: What Troubles You?)**: Doctor's questions: Що вас турбує? Як давно? Чи є температура? Чи є алергія на ліки?; Patient responses with Genitive: немає температури (no fever), немає апетиту (no appetite), немає сил (no energy). Also: болить від холоду (hurts from the cold), кашель від алергії (cough from allergy).; Medicine and prescriptions: ліки від кашлю (cough medicine), краплі від нежиті (drops for a runny nose), таблетки від головного болю (headache pills). Genitive after від for 'against/for' a condition.
- **В аптеці та повсякденне здоров'я (At the Pharmacy and Everyday Health)**: Pharmacy dialogue: asking for specific medicine, asking for advice (Що ви порадите від...?), understanding pharmacist recommendations.; Health vocabulary with Genitive: для здоров'я (for health), без рецепта (without a prescription), після їжі (after a meal — for taking medicine).; Everyday health phrases: дбати про здоров'я, багато води, мало цукру, без кофеїну. Connecting diet and health language with Genitive structures.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

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
