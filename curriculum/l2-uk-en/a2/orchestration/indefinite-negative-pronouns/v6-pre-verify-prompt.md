<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 57: Хтось, ніхто (A2, A2.8 [Refinement and Graduation])

## Plan vocabulary to verify

- хтось (someone)
- щось (something)
- ніхто (nobody)
- ніщо (nothing)
- ніколи (never)
- ніде (nowhere)
- дехто (some people)
- будь-хто (anyone)
- десь (somewhere)
- колись (once, sometime)
- абияк (carelessly, anyhow)
- деякий (some, certain)
- нічий (nobody's)
- хто-небудь (anyone at all)

## Sections to research

- **Хтось, щось: невідоме, але конкретне (Someone, Something: Unknown but Specific)**: The -сь series: хтось (someone specific), щось (something specific), десь (somewhere specific), колись (sometime, once), якось (somehow). Used when the speaker knows the entity exists but not who/what exactly.; Examples in context: Хтось постукав у двері. Я щось забув. Десь тут була моя книга.; Declension: хтось and щось decline like хто and що — хтось, когось, комусь, кимось.
- **Будь-хто, дехто, абихто: різні відтінки (Anyone, Some, Just Anyone: Shades of Meaning)**: The -небудь series: хто-небудь (anyone at all), що-небудь (anything), де-небудь (anywhere). Used in questions and hypothetical situations: Хто-небудь бачив мої ключі?; The де- series: дехто (some people), дещо (some things), деколи (sometimes), деякий (some, certain). Refers to an unspecified part of a group: Дехто вважає, що...; The будь- series: будь-хто (anyone whatsoever), будь-що (anything at all), будь-де (anywhere). Emphasizes complete lack of restriction: Будь-хто може це зробити.
- **Ніхто, ніщо, ніколи: заперечення (Nobody, Nothing, Never: Negation)**: The ні- series: ніхто (nobody), ніщо (nothing), ніде (nowhere), ніколи (never), ніяк (no way), ніякий (no kind of), нічий (nobody's).; Ukrainian requires double negation — always ні- pronoun + не + verb: Ніхто не знає. Я нічого не бачив. Ми ніколи не були в Одесі. This is NOT an error — it is mandatory grammar.; Declension of ніхто, ніщо: нікого, нічого, нікому, нічому, etc. With prepositions, ні- separates: ні до кого, ні з ким, ні про що.
- **Практика: хтось чи ніхто? (Practice: Someone or Nobody?)**: Dialogue: a mystery scenario — someone heard something, nobody saw anything, someone must have been somewhere. Uses all pronoun types naturally.; Reading practice: a short anecdote using indefinite and negative pronouns throughout.; Common mistakes: using ні- without не (*Ніхто прийшов → Ніхто не прийшов), confusing -сь and -небудь, failing to split ні- with prepositions (*нідокого → ні до кого).

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
