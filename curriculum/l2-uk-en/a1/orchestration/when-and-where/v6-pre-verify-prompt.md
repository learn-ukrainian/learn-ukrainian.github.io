<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 45: When and Where (A1, A1.7 [Communication])

## Plan vocabulary to verify

- що (that — conjunction)
- де (where — conjunction)
- коли (when — conjunction)
- знати (to know)
- думати (to think)
- казати (to say/tell)
- сказати (to say — perfective)
- бачити (to see)
- чути (to hear)
- розуміти (to understand)
- речення (sentence, n)
- головне (main — as in main clause)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Planning to meet: — Ти знаєш, де нове кафе? — Так, я знаю, де воно. — Скажи, коли ти вільний. — Я вільний, коли закінчу роботу. — Добре. Я думаю, що о шостій буде добре. — Так, я теж думаю, що це гарний час. Subordinating conjunctions: де (where), коли (when), що (that).; Dialogue 2 — Asking about someone: — Ти знаєш, що Олена вже в Києві? — Ні, я не знав! А де вона живе? — Я не знаю, де саме. Але я знаю, що біля центру. — Скажи їй, коли побачиш, що я хочу зустрітися. — Добре, скажу, коли побачу. Complex sentences in natural conversation.
- **Складне речення (Complex Sentences)**: In M44 you learned to connect EQUAL ideas: Я читаю, і він пише. Now: connecting a MAIN idea with a DEPENDENT idea. Main clause + що/де/коли + subordinate clause: Я знаю, + що він тут. (I know that he's here.) Я не знаю, + де він живе. (I don't know where he lives.) Скажи мені, + коли ти прийдеш. (Tell me when you'll come.) Grade 5 term: складнопідрядне речення (complex sentence with subordinate clause).; Comma rule — always before що, де, коли as conjunctions: Я думаю, що це правильно. (comma before що) Він не знає, де магазин. (comma before де) Зателефонуй, коли прийдеш. (comma before коли) This is different from English — Ukrainian ALWAYS uses a comma here.
- **Що, де, коли — двоє облич (Two Faces)**: These words have two jobs: 1. Question words (already known from M20): Що це? (What is this?) Де ти? (Where are you?) Коли ти прийдеш? (When?) 2. Conjunctions (NEW — connecting clauses): Я знаю, що це книжка. Я знаю, де ти. Скажи, коли прийдеш. How to tell? Question → at the start, with ? at the end. Conjunction → in the middle, connecting two parts.; Common patterns with що, де, коли: Я знаю, що... / Я не знаю, що... (I know/don't know that...) Я думаю, що... (I think that...) Він каже, що... (He says that...) Я знаю, де... / Я не знаю, де... (I know/don't know where...) Скажи, коли... / Я не знаю, коли... (Tell me when... / I don't know when...) Коли я прийду, ми поговоримо. (When I arrive, we'll talk.)
- **Підсумок — Summary**: Subordinating conjunctions at A1: | Conjunction | Meaning | Example | | що | that | Я знаю, що він тут. | | де | where | Я не знаю, де кафе. | | коли | when | Скажи, коли прийдеш. | Always a comma before the conjunction. Combined with M44 conjunctions, you can now build rich sentences: Я не йду, бо я не знаю, де це. (two conjunctions!) Він каже, що прийде, коли закінчить. (two subordinate clauses!) Self-check: Build 3 sentences with що, де, коли: Я думаю, що... Я не знаю, де... Скажи мені, коли...

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
