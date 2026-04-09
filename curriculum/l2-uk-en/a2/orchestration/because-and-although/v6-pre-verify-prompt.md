<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 47: Тому що, бо, хоча (A2, A2.7 [Complex Sentences and Conditionals])

## Plan vocabulary to verify

- тому що (because)
- бо (because — colloquial)
- хоча (although, even though)
- але (but)
- проте (however, yet)
- однак (however)
- причина (reason, cause)
- сполучник (conjunction)
- складне речення (complex sentence)
- тому (therefore, that is why)
- допуст (concession)
- зате (but then, on the other hand)
- навпаки (on the contrary)
- незважаючи на (despite)

## Sections to research

- **Чому? Тому що... / Бо... (Why? Because...)**: Introducing subordinate clauses of cause: the question Чому? and the answers тому що... and бо... Both mean "because" but differ in register — бо is more colloquial, тому що is more neutral/formal.; Word order: тому що always introduces the subordinate clause; бо can appear mid-sentence or at the start of the second clause. Comma placement before the conjunction.; Building natural cause sentences from everyday life: Я не прийшов, тому що був зайнятий. Вона вивчає українську, бо хоче розуміти друзів.
- **Хоча... (Although...)**: Introducing concessive clauses with хоча: expressing a contrast between expectation and reality. Хоча надворі холодно, ми пішли гуляти.; Distinguishing хоча (although — concession) from але (but — simple contrast): Хоча він втомився, він продовжив працювати vs. Він втомився, але продовжив працювати.; Position flexibility: хоча-clause can come first or second. When first, the main clause often has no additional conjunction. Comma before or after хоча-clause.
- **Складносурядне речення: і, та, але (Compound Sentences: and, but)**: Expanding from A1 coordinating conjunctions: і/та (and), але/проте/однак (but). Difference between і and та — та is slightly more formal or used to avoid repeating і.; Building longer compound sentences: Я прийшов додому, і ми разом повечеряли. Сергій хотів піти в кіно, але не мав часу.; Contrast: coordinating (і, та, але — equal clauses) vs. subordinating (тому що, бо, хоча — main + dependent clause). How to tell the difference.

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
