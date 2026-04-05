<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 19: Моєму другові, нашій вчительці (A2, A2.3 [Dative Case])

## Plan vocabulary to verify

- моєму (to my (masc./neut. dat.))
- моїй (to my (fem. dat.))
- твоєму (to your (masc./neut. dat.))
- нашій (to our (fem. dat.))
- цьому (to this (masc./neut. dat.))
- тому (to that (masc./neut. dat.))
- новому (to the new (masc./neut. dat.))
- старшому (to the older (masc./neut. dat.))
- прикметник (adjective)
- присвійний (possessive)
- вказівний (demonstrative)
- узгодження (agreement (grammar))
- іменникова група (noun phrase)
- їхньому (to their (masc./neut. dat.))

## Sections to research

- **Прикметники у давальному відмінку (Adjectives in the Dative Case)**: Masculine/neuter dative ending: -ому for hard stems (новому, старому, гарному), -ьому for soft stems (синьому, середньому).; Feminine dative ending: -ій for hard stems (новій, старій, гарній), -ій for soft stems too (синій→синій). After г, к, х: -ій with no alternation (довгій, тихій).; Plural dative ending for all genders: -им (новим, старим, гарним).
- **Присвійні та вказівні займенники у давальному відмінку (Possessive and Demonstrative Pronouns in the Dative)**: Possessive pronouns follow adjective endings: мій→моєму/моїй, твій→твоєму/твоїй, його (invariable), її (invariable), наш→нашому/нашій, ваш→вашому/вашій, їхній→їхньому/їхній.; Demonstrative pronouns: цей→цьому/цій, той→тому/тій. Plural: цим, тим.; Key insight: його, її, їхній — його never changes form (give to його брат → його братові), but їхній declines (їхньому братові).
- **Повні іменникові групи у давальному відмінку (Full Dative Noun Phrases)**: Building multi-word dative phrases: possessive + adjective + noun all must agree — моєму старшому братові, нашій новій вчительці, твоєму маленькому синові.; Word order: possessive before adjective before noun, same as nominative.; Practice with real-life scenarios: giving presents (подарувати моєму другові), writing to someone (написати нашій бабусі), explaining to someone (пояснити цьому студентові).
- **Порівняння відмінків (Comparing Cases So Far)**: Quick comparison chart: Nominative, Genitive, Dative adjective/pronoun endings side by side for all genders.; Pattern recognition: masculine/neuter Genitive -ого vs. Dative -ому; feminine Genitive -ої vs. Dative -ій.; Practice choosing the correct case form based on the verb and sentence context.

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
