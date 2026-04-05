<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 27: Пане лікарю! Друже мій! (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- кличний (vocative (case))
- звертання (address, appeal)
- пан (Mr., sir)
- пані (Mrs., Ms., madam)
- лікар (doctor)
- вчитель (teacher)
- друг (friend)
- ввічливий (polite)
- офіційний (official, formal)
- професія (profession)
- добродій (sir (literary/diaspora))
- добродійка (madam (literary/diaspora))
- емоційний (emotional)
- ніжний (tender, affectionate)
- колега (colleague)

## Sections to research

- **Пане, пані: формальне звертання (Formal Address)**: A1 taught basic vocative (Оксано! Тарасе!). Now: formal address system with пане/пані.; Pattern: Пане + vocative of profession/title: пане директоре, пане професоре, пане міністре. Пані + vocative of profession: пані вчителько, пані директорко, пані лікарко.; With surnames: Пане Ковальчуку, пане Шевченку (masculine surnames decline). Пані Ковальчук, пані Шевченко (feminine surnames — пані is invariable, surname may or may not decline depending on form).
- **Професійні звертання (Professional Vocative)**: Masculine profession vocatives: лікарю (doctor), вчителю (teacher), професоре (professor), інженере (engineer), водію (driver). Pattern: second declension → -у/-ю for most, -е for hard-stem nouns.; Feminine profession vocatives: лікарко (female doctor), вчителько (female teacher), професорко (female professor). Ukrainian actively uses feminitives — this is natural and standard.; Common-gender nouns: колего (colleague), колего is the same for both. Суддя → суддю (judge). Pattern depends on noun class.
- **Друже мій, люба моя: емоційний кличний (Emotional Vocative)**: Affectionate vocatives between close people: друже (friend), друже мій (my friend), подруго моя (my friend, to a woman), люба/любий (dear), кохана/коханий (beloved).; Diminutive vocatives — deeply Ukrainian: серденько (sweetheart, lit. little heart), сонечко (sunshine, lit. little sun), зіронько (little star), любочко (darling).; Possessive + vocative: мій is always after the noun in vocative — друже мій (not *мій друже), мамо моя (not *моя мамо). This word order is fixed in vocative constructions.
- **Який кличний обрати? (Choosing the Right Vocative)**: Register summary table: formal (пане лікарю), professional (лікарю), friendly (Тарасе), emotional (друже мій), intimate (любий/люба).; Practice scenarios: learner chooses the appropriate vocative form for different social situations — writing an email to a professor, calling a friend, talking to a doctor, comforting a child.; Common mistakes: *пан лікар (nominative instead of vocative after пане) → пане лікарю. *Друже моя (wrong gender agreement) → подруго моя.

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
