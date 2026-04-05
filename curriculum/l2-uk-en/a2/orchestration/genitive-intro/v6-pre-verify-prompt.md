<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 5: У мене немає... (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- родовий відмінок (genitive case)
- немає ((there) is not, (I) don't have)
- багато (a lot, many, much)
- мало (a little, few)
- кілька (a few, several)
- скільки (how many, how much)
- закінчення (ending (grammar))
- однина (singular)
- множина (plural)
- кількість (quantity)
- відсутність (absence)
- гроші (money)
- час (time)

## Sections to research

- **Родовий відмінок: Коли чогось немає (The Genitive Case: When Something Isn't There)**: Introducing the Genitive case (Родовий відмінок), answering 'Кого? Чого?'.; Its first key function: expressing absence or non-existence with the construction `(У мене) немає + Genitive`.; Contrast: 'У мене є брат' (Nominative) vs. 'У мене немає брата' (Genitive).
- **Закінчення родового відмінка однини (Genitive Singular Endings)**: Masculine nouns: the -а/-я vs. -у/-ю puzzle. -а/-я for concrete, animate, specific items (стола, брата, комп'ютера). -у/-ю for abstract concepts, substances, locations (часу, цукру, Києву).; Feminine nouns: -и for hard stems (книги, мами), -і for soft stems and stems in -я (землі, пісні).; Neuter nouns: -а for stems in -о (вікна), -я for stems in -е (моря, сонця).
- **Коли є багато або мало (When There Is a Lot or a Little)**: Introducing quantity words that require the Genitive plural: багато (a lot), мало (a little, few), кілька/декілька (a few, some), скільки (how many).; Genitive Plural Endings: a tricky topic. Masculine: often -ів (столів, братів). Feminine/Neuter: often a zero ending, sometimes with a fleeting vowel (книг → книжок, сестер, вікон). A small group of masculine/neuter nouns takes -ей (гостей, коней, очей).; Lots of examples: багато друзів, мало грошей, кілька книжок, скільки студентів?

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
