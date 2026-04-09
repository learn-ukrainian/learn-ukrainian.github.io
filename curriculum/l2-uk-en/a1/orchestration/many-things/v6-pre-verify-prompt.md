<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 13: Many Things (A1, A1.2 [My World])

## Plan vocabulary to verify

- столи (tables — pl of стіл)
- книги (books — pl of книга)
- вікна (windows — pl of вікно)
- стільці (chairs — pl of стілець)
- ці (these — pl of цей/ця/це)
- ті (those — pl of той/та/те)
- мої (my — plural)
- які (what kind? — plural)
- ручки (pens — pl of ручка)
- сумки (bags — pl of сумка)
- лампи (lamps — pl of лампа)
- зошити (notebooks — pl of зошит)
- дзеркала (mirrors — pl of дзеркало)
- крісла (armchairs — pl of крісло)
- речі (things — pl of річ)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Describing a room (Вашуленко Grade 3 p.114-115): — Що тут є? — Столи, стільці і вікна. — Які столи? — Столи великі й нові. А стільці — старі. Plurals emerge naturally from describing a room full of things.; Dialogue 2 — Shopping for several items (extending M11-M12): — У вас є ручки? — Так! Які ручки? Червоні чи сині? — Сині. І ще зошити. — Скільки? — Три зошити. Plural adjectives (-і) in real context.
- **Один → багато (Singular → Plural)**: Большакова Grade 2 p.18: 'Один предмет → багато предметів.' Three main plural patterns for nominative: Masculine → usually -и or -і: стіл → столи, стілець → стільці, телефон → телефони, зошит → зошити. Feminine → usually -и or -і: книга → книги, лампа → лампи, ручка → ручки, сумка → сумки. Neuter → usually -а or -я: вікно → вікна, ліжко → ліжка, крісло → крісла, дзеркало → дзеркала.; Guideline (not a rule — exceptions exist): After г, к, х → -и (книга → книги, ручка → ручки). After most other consonants → -и or -і (стіл → столи, стілець → стільці). Neuter -о → -а (вікно → вікна). Neuter -е → -я (not covered yet). Full declension rules come later — for now, learn each plural with its noun.
- **Прикметники у множині (Adjectives in Plural)**: Большакова Grade 2 p.42: який/яка/яке → які, веселий/весела/веселе → веселі. ALL adjectives take -і in the plural, regardless of gender: великий стіл → великі столи нова книга → нові книги чисте вікно → чисті вікна This is simpler than singular — one ending for all genders!; Colors in plural (review M10): червоні ручки (red pens), сині зошити (blue notebooks), білі стіни (white walls), чорні стільці (black chairs). Demonstratives also have a plural form: ці (these) — Ці столи великі. Ці книги нові. ті (those) — Ті вікна чисті. Ті стільці старі.
- **Підсумок — Summary**: Plural formation summary: Nouns: learn each plural individually (столи, книги, вікна). Adjectives: always -і (великі, нові, червоні, сині). Demonstratives: ці (these), ті (those). Possessives: мої (my — plural). Self-check: Make these plural — стіл, книга, вікно. Describe your classroom: Які столи? Які стільці? Які вікна?

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
