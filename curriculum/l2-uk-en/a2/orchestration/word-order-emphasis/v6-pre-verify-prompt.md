<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 50: Порядок слів і наголос у реченні (A2, A2.7 [Complex Sentences and Conditionals])

## Plan vocabulary to verify

- порядок (order)
- речення (sentence)
- тема (theme, topic (linguistics))
- рема (rheme, new information)
- наголос (stress, emphasis)
- інверсія (inversion)
- контраст (contrast)
- підкреслювати (to emphasize, to underline)
- початок (beginning)
- кінець (end)
- виділяти (to highlight, to single out)
- означення (attribute, modifier)
- нейтральний (neutral)
- емфатичний (emphatic)
- акцент (accent, emphasis)

## Sections to research

- **Тема і рема: що відоме, що нове? (Theme and Rheme)**: Every sentence has two parts: тема (theme, the known/given info, what the sentence is about) and рема (rheme, the new info, the communicative focus).; In neutral Ukrainian word order, тема comes first and рема comes last: Тарас (theme) купив нову книгу (rheme). The "news" is at the end.; Test: answer a question. Хто купив книгу? → Книгу купив Тарас (Тарас is the new info = rheme = last). Що купив Тарас? → Тарас купив книгу (книгу = rheme = last).
- **Прямий порядок слів (Neutral Word Order)**: Default neutral order: Subject + Predicate + Object (SVO): Студент читає книгу. Мама готує вечерю. This is the unmarked, emotionally neutral order.; Adjective before noun: нова книга, великий будинок (same as English). Adverb before verb or after: добре працює / працює добре (both OK, but emphasis shifts).; Time expressions typically go first or last: Вчора ми ходили в кіно. Ми ходили в кіно вчора. (Вчора first = neutral context-setting; вчора last = emphasizing "it was yesterday").
- **Інверсія для контрасту (Fronting for Contrast)**: Fronting the object: Книгу я вже прочитав (I've already read THE BOOK — as opposed to something else). The object moves to the front to become the theme, and the subject shifts to become part of the rheme.; Fronting the verb: Прочитав я цю книгу! (emphatic, expressive — I DID read this book!). Verb-first order conveys strong assertion or emotional emphasis.; Corrective contrast: Не Тарас це зробив, а Олег. (Not Taras did this, but Oleh.) The corrected element is fronted with не...а.
- **Порядок слів у реальному мовленні (Word Order in Real Speech)**: In conversation, word order constantly shifts based on what is known vs. new. Practice with mini-dialogues where each answer reorders the sentence to highlight the new information.; Common patterns: — Хто це зробив? — Це зробив Тарас. (SVO → OVS). — Що ти купив? — Я купив каву. (neutral SVO stays).; Reading practice: identifying word order shifts in a short Ukrainian text and explaining why the author chose that order.

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
