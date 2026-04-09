<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 47: Checkpoint: Communication (A1, A1.7 [Communication])

## Plan vocabulary to verify

(No vocabulary hints in plan)

## Sections to research

- **Що ми знаємо? (What Do We Know?)**: Self-check covering M42-M46: Can you call someone by name using vocative? (M42) Can you ask someone to do something? (M43) Can you connect ideas with і, а, але, бо? (M44) Can you build sentences with що, де, коли? (M45) Can you name Ukrainian holidays and greet people? (M46)
- **Читання (Reading Practice)**: A short Ukrainian text using all A1.7 skills. Content: Olena calls her friend Taras to plan a holiday celebration. She uses vocative (Тарасе!), imperatives (Прийди! Принеси!), conjunctions (бо ми святкуємо, але я не знаю, коли ти вільний), and holiday vocabulary (Різдво, кутя, колядки). Combines all A1.7 communication tools in one realistic scenario.
- **Граматика (Grammar Summary)**: Key patterns from A1.7: 1. Vocative: -а→-о (Олено), hard→-е (Тарасе), soft→-ю (Андрію) (M42) 2. Imperative: ти (читай, дай), ви (читайте, дайте) (M43) 3. Coordinating: і/та (and), а (contrast), але (but), бо (because) (M44) 4. Subordinating: що (that), де (where), коли (when) + comma (M45) 5. Holiday greetings: З + instrumental (З Різдвом!) (M46)
- **Діалог (Connected Dialogue)**: Planning a holiday gathering: — Олено, привіт! Ти знаєш, що скоро Різдво? — Так, Тарасе! Я думаю, що ми можемо святкувати разом. — Добре! Скажи, коли ти вільна, бо я хочу запросити друзів. — Я вільна двадцять четвертого. Але я не знаю, де ми будемо. — Ходімо до мене! Принеси кутю, будь ласка. — Добре, принесу! І я знаю, де купити гарні свічки. З Різдвом! Uses vocative, imperative, conjunctions, що/де/коли, and holidays.
- **Підсумок — Summary**: A1.7 achievement summary: You can address people properly in Ukrainian. You can ask people to do things, politely and informally. You can connect your ideas into longer, natural sentences. You can build complex sentences with що, де, коли. You can talk about Ukrainian holidays and congratulate people. Next: A1.8 — Past, Future, Graduation.

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
