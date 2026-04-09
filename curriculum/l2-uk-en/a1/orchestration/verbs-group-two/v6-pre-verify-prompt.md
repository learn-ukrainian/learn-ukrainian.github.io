<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 17: Verbs Group II (A1, A1.3 [Actions])

## Plan vocabulary to verify

- говорити (to speak)
- бачити (to see)
- робити (to do/make)
- вчити (to study/teach)
- просити (to ask/request)
- ходити (to go/walk regularly)
- дивитися (to watch — reflexive preview)
- вчитися (to learn — reflexive preview)
- любити (to love — review, Group II!)
- трохи (a little)
- добре (well)
- увечері (in the evening)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Talking about abilities (ULP Ep24 pattern): — Ти говориш українською? — Так, я говорю трохи. А ти? — Я бачу, що ти добре говориш! — Дякую, я вчуся. Group II verbs in natural conversation.; Dialogue 2 — Evening at home: — Що ти робиш увечері? — Я дивлюся фільм. А ти? — Я вчу нові слова. — Молодець! Note: дивлюся (I watch) — the -ся ending means 'oneself' (preview for M20).
- **Друга дієвідміна (Group II Verbs)**: Group II verbs have infinitive in -ити (or -іти): говорити → я говорю, ти говориш, він/вона говорить, ми говоримо, ви говорите, вони говорять. Pattern: stem + -ю/-у, -иш, -ить, -имо, -ите, -ять/-ать.; Six essential Group II verbs: говорити (to speak): говорю, говориш, говорить... бачити (to see): бачу, бачиш, бачить... робити (to do/make): роблю, робиш, робить... вчити (to study/teach): вчу, вчиш, вчить... просити (to ask/request): прошу, просиш, просить... ходити (to go/walk regularly): ходжу, ходиш, ходить...
- **Група I чи II? (Which Group?)**: Compare the endings side by side: | | Group I (-ати) | Group II (-ити) | | я | читаю | говорю | | ти | читаєш | говориш | | він/вона | читає | говорить | | вони | читають | говорять | Key difference: ти form → -єш (I) vs -иш (II), вони → -ють (I) vs -ять/-ать (II). Note: after sibilants (ч, ш, ж, щ) → -ать (not -ять): бачать (not *бачять), кричать. Other consonants → -ять: говорять, ходять.; Consonant changes in Group II (я-form only): робити → роблю (б→бл), ходити → ходжу (д→дж), просити → прошу (с→ш), бачити → бачу (no change). These changes only affect the я-form — all other forms are regular. Don't memorize the rule — just learn each я-form with the verb.
- **Підсумок — Summary**: Two verb groups — two ending patterns: Group I (-ати): -ю, -єш, -є, -ємо, -єте, -ють Group II (-ити): -ю/-у, -иш, -ить, -имо, -ите, -ять Consonant shifts in Group II я-form (роблю, ходжу, прошу). Self-check: Conjugate 'бачити' for я, ти, він/вона. Is 'слухати' Group I or II? How about 'говорити'?

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
