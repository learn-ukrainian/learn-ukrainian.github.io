<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 51: Якщо... то... (A2, A2.7 [Complex Sentences and Conditionals])

## Plan vocabulary to verify

- якщо (if — real condition)
- умова (condition)
- результат (result, outcome)
- реальний (real)
- погода (weather)
- допомогти (to help)
- поспішити (to hurry)
- вільний (free, available)
- залишитися (to stay, to remain)
- порада (advice)
- якби (if — hypothetical, B1 preview)
- змокнути (to get wet)
- запізнитися (to be late)
- парасолька (umbrella)
- відпустка (vacation, holiday)

## Sections to research

- **Якщо + теперішній/майбутній час (If + Present/Future)**: Introducing real conditionals: якщо expresses a condition that is possible or likely. Якщо буде гарна погода, ми підемо гуляти. Якщо ти хочеш, я допоможу.; Tense in real conditionals: якщо-clause uses present or future tense. The result clause uses future or imperative. No special mood — just regular verb forms.; The якщо... то... frame: то is optional but very common in Ukrainian. It marks the beginning of the result clause. Якщо дощитиме, то ми залишимося вдома.
- **Умова в повсякденному житті (Conditions in Everyday Life)**: Planning and decisions: Якщо завтра буде вільний час, я піду в спортзал. Якщо у магазині є свіжий хліб, купи, будь ласка.; Advice and recommendations: Якщо болить голова, випий таблетку. Якщо хочеш вивчити мову, практикуй щодня.; Warnings: Якщо не поспішиш, запізнишся. Якщо не візьмеш парасольку, змокнеш.
- **Якщо чи якби? Тільки реальна умова (Якщо or якби? Real Conditions Only)**: Preview of the difference: якщо = real, possible condition (if it rains, we will stay home). якби = unreal, hypothetical condition (if I were a bird, I would fly). At A2, learners use only якщо.; Recognition only for якби: learners may encounter якби in songs, proverbs, or conversation. They should recognize it means "if (hypothetically)" but not produce it yet. Якби я знав — if only I knew (but I do not).; Consolidation of all complex sentence types from A2.7: причина (тому що, бо), допуст (хоча), мета (щоб), означальне (який, де), умова (якщо). Building paragraphs that use multiple types.

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
