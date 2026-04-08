<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 11: Куди? До якого часу? (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- напрямок (direction)
- мета (goal, purpose)
- музей (museum)
- лікар (doctor)
- бабуся (grandmother)
- вечір (evening)
- ранок (morning)
- екзамен (exam)
- побачення (meeting, date; goodbye in 'до побачення')
- список (list)
- ставлення (attitude)
- інтерес (interest)
- готовий (ready)
- завтра (tomorrow)

## Sections to research

- **Куди ти йдеш? До + родовий для напрямку (Where Are You Going? До + Genitive for Direction)**: Destination as a place: до Львова, до Києва, до Одеси. Used for cities and countries: до України, до Польщі.; Destination as a person: до друга (to a friend's place), до бабусі (to grandma's), до лікаря (to the doctor). До + person = going to see them / to their place.; Contrast до vs. в/на + Accusative: 'Іду до магазину' vs. 'Іду в магазин' — до emphasizes the direction/journey, в/на emphasizes the destination itself. Both are equally standard in Ukrainian. No hierarchy — use whichever fits the context.
- **До якого часу? До + родовий для часу (Until When? До + Genitive for Time)**: Time limit — until: до вечора (until evening), до ранку (until morning), до понеділка (until Monday), до літа (until summer).; Deadline — by: зробити до п'ятниці (finish by Friday), прийти до восьмої (come by eight o'clock).; Paired with від/з for time ranges: від ранку до вечора (from morning to evening), з понеділка до п'ятниці (from Monday to Friday).
- **До + родовий: решта значень та узагальнення (До + Genitive: Other Meanings and Summary)**: Purpose — with abstract nouns: до речі (by the way), до побачення (goodbye — lit. until seeing), готовий до екзамену (ready for the exam).; Addition and relation: додати до списку (add to the list), ставлення до роботи (attitude toward work), інтерес до мови (interest in the language).; Summary table of all до meanings: direction (до Львова), person (до лікаря), time limit (до вечора), deadline (до п'ятниці), purpose (до побачення).

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
