<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 5: Who Am I? (A1, A1.1 [Sounds, Letters, and First Contact])

## Plan vocabulary to verify

- я (I)
- ти (you, informal)
- він (he)
- вона (she)
- ви (you, formal/plural)
- мене звати (my name is)
- як тебе звати? (what's your name, informal)
- як вас звати? (what's your name, formal)
- це (this is / these are)
- дуже приємно (pleased to meet you)
- студент, студентка (student m/f)
- вчитель, вчителька (teacher m/f)
- лікар, лікарка (doctor m/f)
- українець, українка (Ukrainian m/f)
- Україна (Ukraine)
- ми (we)
- вони (they)
- програміст, програмістка (programmer m/f)
- інженер, інженерка (engineer m/f)
- звідки (where from)
- друг (friend, male)
- його (his — doesn't change)
- її (her — doesn't change)
- Канада (Canada)
- Німеччина (Germany)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — At a hostel (informal, following Anna Ep3): — Привіт! Як тебе звати? — Мене звати Марко. А тебе? — Мене звати Олена. Звідки ти? — Я з Канади. А ти? — Я з України. — Дуже приємно!; Dialogue 2 — At a conference (formal, following Anna Ep3-4): — Добрий день! Як вас звати? — Мене звати Петро. Дуже приємно! — Мені також! Ви з України? — Так, я з Києва.; Dialogue 3 — Introducing someone else: Це Андрій. Він зі Львова. Він — інженер. А це Оксана. Вона з Одеси. Вона — лікарка.
- **Мене звати... (My name is...)**: Following Anna Ep3: Мене звати... literally 'me they-call.' Ukrainian doesn't use 'My name IS' — no verb 'to be' needed. Asking: Як тебе звати? (informal) / Як вас звати? (formal). About others: Як його звати? (his) / Як її звати? (her).; Pleased to meet you: Дуже приємно! or Приємно познайомитись! Said AFTER exchanging names.
- **Це... (This is...)**: Це = 'this is / it is / these are.' No verb 'to be' needed. Це кава. Це Київ. Це Андрій. Questions: Що це? (What is this?) Хто це? (Who is this?) Question words go FIRST: Хто це? not *Це хто?
- **Особові займенники (Personal Pronouns)**: The basic personal pronouns: я (I), ти (you, informal), він (he), вона (she), ми (we), ви (you, formal/plural), вони (they). Note: ви is both formal singular and plural — like English 'you' but written with capital В (Ви) when formal. These pronouns are needed for every sentence from now on.
- **Я — студент (I am a student)**: No verb 'to be' in present tense. Subject — Noun: Я — студент. Він — лікар. Вона — вчителька. The dash (—) marks where 'is' would go.; Nationalities (nominative, no verb): українець / українка, американець / американка, канадієць / канадка. Professions: студент/студентка, вчитель/вчителька, лікар/лікарка, програміст/програмістка.
- **Звідки? (Where from?)**: Following Anna Ep4: Звідки ти? / Звідки ви? Я з України. Я з Канади. Я зі Штатів. Я з Німеччини. Note: 'з/зі + country' uses genitive forms (України, Канади) but teach as MEMORIZED CHUNKS — genitive grammar is A2. Do NOT introduce 'Де ви живете?' here — locative + verb conjugation are taught later (M16 verbs, M29 locative).
- **Підсумок — Summary**: Self-check folded into dialogue practice above.

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
