<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 34: З друзями, для дітей (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- давальний відмінок (dative case)
- орудний відмінок (instrumental case)
- місцевий відмінок (locative case)
- допомагати (to help)
- дякувати (to thank)
- подарунок (gift)
- квіти (flowers)
- діти (children)
- люди (people)
- заняття (class, lesson)
- радити (to advise)
- пояснювати (to explain)
- полиця (shelf)
- прикрашати (to decorate)

## Sections to research

- **Давальний множини: Кому? (Dative Plural: To Whom?)**: Universal pattern: all nouns take -ам (hard) or -ям (soft) in Dat.Pl. студентам, друзям, дітям, містам, ночам.; This is the most regular plural case — ONE rule covers almost everything. Compare with the complexity of Gen.Pl.; Common verbs requiring Dative: давати, допомагати, пояснювати, телефонувати, дякувати, радити.
- **Орудний множини: З ким? Чим? (Instrumental Plural: With Whom? With What?)**: Universal pattern: -ами (hard) or -ями (soft). студентами, друзями, дітьми (irregular), містами, ночами.; Key irregular forms: діти → дітьми, люди → людьми, коні → кіньми, гості → гістьми (or гостями). These are high-frequency — learn them.; Preposition з/із + Instr.Pl.: Я зустрівся з друзями. Ми розмовляли з учителями. Вона прийшла з дітьми.
- **Місцевий множини: Де? На чому? (Locative Plural: Where? On What?)**: Universal pattern: -ах (hard) or -ях (soft). у містах, на столах, у книжках, на заняттях, у ночах.; Prepositions: у/в + Loc.Pl. (location), на + Loc.Pl. (surface/event), по + Loc.Pl. (distribution/across).; Examples: Діти грають у парках. Книжки лежать на полицях. По вулицях ходять люди. На заняттях ми багато говоримо.
- **Три відмінки разом: Практика (All Three Together: Practice)**: Combined sentences using Dat., Instr., and Loc. plurals: Ми подарували квіти вчителям (Dat.) і сфотографувалися з ними (Instr.) у класах (Loc.).; Short dialogue: organizing a trip — who to invite (Dat.), what to bring (Instr.), where to go (Loc.).; Summary table: Dat. -ам/-ям, Instr. -ами/-ями, Loc. -ах/-ях — the most regular set of plural endings in Ukrainian.

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
