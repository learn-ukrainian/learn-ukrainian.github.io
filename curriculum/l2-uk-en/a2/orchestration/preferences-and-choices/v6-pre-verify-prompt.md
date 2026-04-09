<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 59: Я обираю, я вважаю (A2, A2.8 [Refinement and Graduation])

## Plan vocabulary to verify

- вважати (to think, to consider)
- воліти (to prefer)
- обирати (to choose)
- думка (opinion, thought)
- згоден (agree, m.)
- згодна (agree, f.)
- рація (rightness — in мати рацію)
- тому що (because)
- навпаки (on the contrary)
- переконаний (convinced, m.)
- безумовно (absolutely)
- інакше (differently)
- дозволити (to allow, to permit)
- погоджуватися (to agree)
- по-перше (firstly)

## Sections to research

- **Що тобі більше подобається? (What Do You Prefer?)**: Expressing preferences with comparison: Мені більше подобається кава, ніж чай. Я волію читати, а не дивитися телевізор. Краще поїхати влітку, ніж взимку.; Key verbs: подобатися (to like), воліти (to prefer), обирати (to choose), вирішити (to decide). Verb government: подобатися + Dat., обирати + Acc.; Dialogue: two friends discuss weekend plans — comparing options, expressing what they prefer and why.
- **На мою думку... (In My Opinion...)**: Opinion phrases: Я вважаю, що... (I think that...), На мою думку... (In my opinion...), Мені здається, що... (It seems to me that...), Я переконаний/переконана, що... (I am convinced that...).; Giving reasons: тому що (because), бо (because, informal), адже (since, after all), оскільки (since, as).; Complex sentence practice: Я вважаю, що українська кухня дуже смачна, тому що вона використовує свіжі продукти.
- **Згоден чи ні? (Agree or Disagree?)**: Agreeing: Так, я згоден/згодна. Ви маєте рацію. Безумовно! Саме так! Цілком погоджуюся.; Disagreeing politely: Я не зовсім згоден/згодна. Можливо, але... Я думаю інакше. Дозвольте не погодитися. Навпаки, я вважаю...; Partial agreement: З одного боку... з іншого боку... (On one hand... on the other hand...). Це правда, але...
- **Обговорення: що краще? (Discussion: What Is Better?)**: Task-based scenario: learners discuss lifestyle choices using all the tools from this module. Topics: city vs. village life, cooking at home vs. eating out, summer vs. winter vacation.; Reading practice: a forum thread where Ukrainians discuss their preferences — authentic internet register with opinion expressions.; Useful connectors for structured arguments: по-перше (firstly), по-друге (secondly), крім того (moreover), на завершення (in conclusion).

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
