<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 18: Студентові, сестрі, дитині (A2, A2.3 [Dative Case])

## Plan vocabulary to verify

- студентові (to the student (dat.))
- сестрі (to the sister (dat.))
- другові (to the friend (dat.))
- подарувати (to give as a gift)
- показати (to show)
- написати (to write)
- розповісти (to tell, to narrate)
- пояснити (to explain)
- відповісти (to answer, to reply)
- закінчення (ending (grammar))
- відміна (declension)
- чергування (alternation (grammar))
- одержувач (recipient)
- немовля (baby, infant)

## Sections to research

- **Давальний відмінок іменників чоловічого роду (Dative of Masculine Nouns)**: II declension masculine nouns have parallel endings: -ові/-еві/-єві and -у/-ю. Both are correct: братові = брату, лікареві = лікарю.; -ові for hard stems (студентові, другові, батькові), -еві for soft stems and sibilants (вчителеві, товаришеві), -єві after vowels (героєві).; Style rule from Заболотний: when multiple dative nouns appear together, alternate endings to avoid monotony — подякувати сусідові Данилу.
- **Давальний відмінок іменників жіночого роду (Dative of Feminine Nouns)**: I declension: hard stems take -і (мамі, подрузі, сестрі), soft stems take -і (землі, пісні), stems in -ія take -ії (станції).; Consonant alternations before -і: к→ц (подруга→подрузі), г→з (книга→книзі), х→с (свекруха→свекрусі).; III declension feminine nouns: -і (ночі, матері, любові, радості).
- **Давальний відмінок іменників середнього роду (Dative of Neuter Nouns)**: II declension neuter: -у for hard stems (місту, слову, вікну), -ю for soft stems (морю, серцю).; IV declension (nouns in -а/-ят-): -аті/-яті (немовляті, курчаті).; Examples with neuter nouns in real contexts (дати назву місту, радіти сонцю).
- **Давальний відмінок у реченні (Dative Nouns in Sentences)**: Two-object verb pattern: Subject + Verb + Dative (recipient) + Accusative (thing). Тетяна подарувала братові книгу. Вчитель показав студентам карту.; Common verbs with indirect objects: подарувати, показати, дати, розповісти, написати, пояснити, відповісти.; Dialogue practice — giving gifts, explaining things, writing to someone.

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
