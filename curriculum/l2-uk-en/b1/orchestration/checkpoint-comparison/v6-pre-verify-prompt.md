<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 51: Контрольна робота 4 (B1, B1.4 [Comparison & Word Formation])

## Plan vocabulary to verify

- повторення (review — systematic revision of material)
- самооцінка (self-assessment)
- комплексний (comprehensive — combining multiple skills)
- діагностика (diagnostics — identifying knowledge gaps)
- рубрика (rubric — assessment criteria)
- аналіз помилок (error analysis)

## Sections to research

- **Повторення: ступені порівняння**: Systematic review of all comparison forms: Вищий ступінь: проста (-іш-/-ш-) + складена (більш/менш). Найвищий ступінь: проста (най-) + складена (найбільш/найменш). Підсилені форми: що-/як- + найвищий. Full formation table with examples for each pattern.; Consonant alternation review for comparison: [г]+[ш]=[жч]: дорогий-дорожчий, дорого-дорожче [з]+[ш]=[жч]: вузький-вужчий, вузько-вужче [к]+[ш]=[чч/щ]: легкий-легший, високий-вищий [с]+[ш]=[шч/щ]: високий-вищий, високо-вище Practice: 15 adjectives and adverbs to transform.; Suppletive forms review: гарний-кращий-найкращий (добре-краще-найкраще) поганий-гірший-найгірший (погано-гірше-найгірше) великий-більший-найбільший (багато-більше-найбільше) малий-менший-найменший (мало-менше-найменше) Drill: sentences requiring correct form selection.
- **Повторення: словотвір**: Adjective formation methods review: Суфіксальний: -н-, -ськ-/-зьк-/-цьк-, -ів-, -уват-, -еньк- Префіксальний: пре-, без-, над-, анти- Складання: чорноокий, темно-зелений -Н-/-НН- spelling rule: основа на -н- + суфікс -н- = -нн-.; Noun formation methods review: Agent nouns: -ач, -ець, -ник, -тель, -ар, -ист (m. → f. counterparts) Place nouns: -ня, -ниця, -ище; prefix-suffix: при-...-я, за-...-я Verbal nouns: -ння, -ття; безафіксний: підписати → підпис Словотвірний ланцюжок: вода → водний → водник → підводник.; Adverb formation review: суфіксальний (-о, -е: швидко, гарно), префіксально- суфіксальний (по-доброму, по-українськи). Adverb comparison: -іше/-ше (тихіше, швидше), най- (найтихіше). Parallel adjective/adverb forms: тихіший (adj.) vs тихіше (adv.).
- **Повторення: покупки і послуги**: Key transactional vocabulary and phrases from M40: На ринку: ціна, знижка, готівка, здача, ваги. У магазині: розмір, примірочна, чек, гарантія, бракований. На пошті: посилка, бандероль, доставка. У банку: рахунок, переказ, обмін валют, курс.; Review of comparison in transactional contexts: product comparison, service reviews, complaint register.
- **Комплексні завдання**: Text analysis: a Ukrainian consumer magazine article comparing products. Tasks: identify all comparatives/superlatives, analyze word formation of agent and place nouns, answer comprehension questions.; Error correction block: 10-12 sentences with mixed errors — comparison formation, -н-/-нн- spelling, suffix choice, Russicisms. Each error must be identified, explained, and corrected.; Production task: write a 10-sentence product/service comparison using at least 5 comparatives, 3 superlatives, and 4 derived nouns. Self-assessment rubric provided.
- **Самооцінка і підготовка до Фази 6**: Self-check grid: can I form comparatives? superlatives? suppletive forms? Can I form adjectives from nouns? Nouns from verbs? Agent nouns (m./f.)? Can I shop, complain, and write reviews in Ukrainian? Rate each skill 1-5.; Gap analysis: which areas need more practice before Phase 6? Preview of Phase 6: advanced case usages, prepositions, numerals, pronouns. The shift: from FORMING words to USING cases precisely.; Diagnostic: 10 quick-check questions covering all Phase 5 topics, with answer key and explanations.
- **Підсумок**: Phase 5 achievement summary: comparison forms (проста, складена, підсилена), suppletive pairs, word formation methods (suffixal, prefixal, compound, zero-derivation), adverb formation and comparison, and practical application in shopping/service contexts.; Key patterns to carry forward: the relationship between adjective and adverb comparison (parallel suffixes, same alternations), word formation chains as vocabulary expansion strategy, and register awareness (проста for speech, складена for formal texts).; Transition to Phase 6: mastering the nuances of Ukrainian cases — Родовий відмінок у деталях, прийменники з відмінками, числівники. The focus shifts from forming words to using them precisely in syntactic structures.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

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
