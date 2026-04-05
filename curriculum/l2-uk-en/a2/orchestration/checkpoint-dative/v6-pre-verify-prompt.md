<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 23: Контрольна робота — давальний відмінок (A2, A2.3 [Dative Case])

## Plan vocabulary to verify

- давальний відмінок (dative case)
- допомагати (to help)
- дякувати (to thank)
- подобатися (to be pleasing to, to like)
- подарувати (to give as a gift)
- надіслати (to send)
- потрібно (necessary, needed)
- холодно (cold (impersonal state))
- закінчення (ending (grammar))
- чергування (alternation (grammar))
- узгодження (agreement (grammar))

## Sections to research

- **Частина 1: Розпізнавання (Part 1: Recognition)**: Identify dative forms in context — distinguish dative from genitive, accusative, and locative case forms.; Recognize impersonal dative constructions (мені холодно) vs. nominative subject sentences (я замерзла).; Match dative pronoun forms to their nominative counterparts.
- **Частина 2: Вибір форми (Part 2: Choosing the Correct Form)**: Choose correct dative noun endings across all genders — masculine -ові/-у, feminine -і with alternations, neuter -у/-ю.; Select correct dative adjective and possessive pronoun forms (-ому/-ій/-им).; Choose between dative and accusative case based on the verb (допомагати кому vs. бачити кого).
- **Частина 3: Продукування (Part 3: Production)**: Write complete sentences using dative-governing verbs with correct noun/pronoun forms.; Produce подобатися sentences with correct experiencer (Dat.) and subject (Nom.) agreement.; Express age using dative construction with correct number agreement.
- **Огляд помилок та порівняння відмінків (Error Review and Case Comparison)**: Common dative errors and how to avoid them — mixing -ому/-ій, forgetting consonant alternations, wrong case after дякувати/допомагати.; Summary comparison chart of Nominative, Genitive, Dative endings for nouns, adjectives, and pronouns.; Self-assessment checklist for dative case mastery.

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
