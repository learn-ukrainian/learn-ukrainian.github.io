<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 25: My Day (A1, A1.4 [Time and Nature])

## Plan vocabulary to verify

- вранці (in the morning)
- вдень (during the day)
- ввечері (in the evening)
- обідати (to have lunch)
- вечеряти (to have dinner)
- відпочивати (to rest)
- після (after)
- прокидатися (to wake up — review from M20)
- вмиватися (to wash — review from M20)
- одягатися (to get dressed — review from M20)
- вночі (at night)
- після обіду (in the afternoon)
- також (also)
- лягати спати (to go to bed — chunk)
- типовий (typical)
- вільний (free)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — What did you do today? — Як пройшов твій день? — Добре! Вранці я працював. — А потім? — Потім обідав о першій. Після обіду гуляв. — А ввечері? — Ввечері дивився фільм і читав книгу. Past tense emerges naturally here — teach as vocabulary chunks, not grammar (past tense grammar = M48-49).; Dialogue 2 — Planning tomorrow: — Що ти будеш робити завтра? — Вранці буду працювати. — А після обіду? — Буду вивчати українську. А ввечері — гуляти. Future 'буду + infinitive' as a chunk.
- **Мій типовий день (My Typical Day)**: A model text using all A1.3-A1.4 skills: Я прокидаюся о сьомій. Спочатку вмиваюся і одягаюся. Потім снідаю. О дев'ятій я працюю. О першій обідаю. Після обіду працюю до п'ятої. Ввечері готую вечерю, читаю і дивлюся фільм. О одинадцятій лягаю спати.; Parts of the day: вранці (in the morning), вдень (during the day), після обіду (in the afternoon — literally 'after lunch'), ввечері (in the evening), вночі (at night). These are adverbs — just add them to the beginning of a sentence.
- **Від ранку до вечора (From Morning to Evening)**: Extended sequence words (building on M20): спочатку (first/at first), потім (then/next), після того/після цього (after that), нарешті (finally), також (also), а потім (and then). These connect sentences into a coherent narrative.; Daily activity verbs (review + new): снідати (to have breakfast — review M20), обідати (to have lunch), вечеряти (to have dinner), відпочивати (to rest), лягати спати (to go to bed — chunk). All Group I (-ати), easy to conjugate with M16 patterns.
- **Підсумок — Summary**: Telling your day: Time + sequence + activity = а coherent story. О сьомій прокидаюся. Спочатку снідаю. Потім працюю. Після обіду відпочиваю. Ввечері читаю. Нарешті лягаю спати. Self-check: Describe your typical Monday from morning to evening. Use at least 3 time expressions and 3 sequence words.

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
