<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 42: Hey, Friend! (A1, A1.7 [Communication])

## Plan vocabulary to verify

- друг (friend, m)
- подруга (friend, f)
- брат (brother, m)
- сестра (sister, f)
- пан (Mr., m)
- пані (Mrs./Ms., f)
- синку (son — vocative, from син)
- дочко (daughter — vocative, from дочка)
- козак (Cossack, m)
- вчитель (teacher, m)
- бабуся (grandmother, f)
- дідусь (grandfather, m)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Meeting a friend: — Олено, привіт! Як справи? — Добре, дякую, Тарасе! А в тебе? — Теж добре. Олено, ти знаєш мого брата? — Ні. — Андрію, ходи сюди! Це Олена. Олено, це Андрій. Vocative forms: Олено (Олена), Тарасе (Тарас), Андрію (Андрій).; Dialogue 2 — At home: — Мамо, де мій телефон? — На столі, синку. — Тату, а де ключі? — У кишені, дочко. — Бабусю, ми йдемо! — Добре, будьте обережні! Family vocatives: мамо, тату, синку, дочко, бабусю.
- **Кличний відмінок (The Vocative Case)**: Ukrainian has a special case for calling someone — кличний відмінок. In English you just say the name: 'Olena, come here!' In Ukrainian the name CHANGES: Олена → Олено, ходи сюди! This is not optional — Ukrainians always use vocative when addressing someone. Grade 4 helper word: Кл. (!) — the exclamation mark reminds you: you're calling someone, so the ending changes.; Why vocative matters: Олена прийшла. (Olena came.) — nominative, talking ABOUT her. Олено, ходи сюди! (Olena, come here!) — vocative, talking TO her. Using nominative to address someone sounds unnatural in Ukrainian. It's like saying 'Hey, him!' instead of 'Hey, you!' in English.
- **Закінчення кличного (Vocative Endings)**: Feminine names and nouns (-а → -о): Олена → Олено, мама → мамо, сестра → сестро, Оксана → Оксано, подруга → подруго, бабуся → бабусю (-ся → -сю). Names on -ка: Наталка → Наталко, Ірка → Ірко. Names on -ія: Марія → Маріє (not Маріо!). Names on -а (long): Катерина → Катерино, Тетяна → Тетяно.; Masculine names and nouns: Hard consonant → -е: Тарас → Тарасе, Іван → Іване, брат → брате, пан → пане. Soft consonant / -й → -ю: Андрій → Андрію, дідусь → дідусю, вчитель → вчителю. Special: друг → друже (г → ж), козак → козаче (к → ч). Тато → тату (exceptional -у ending, memorize).
- **Підсумок — Summary**: Vocative quick reference: | Pattern | Nominative → Vocative | Example | | Feminine -а | -а → -о | Олена → Олено, мама → мамо | | Feminine -ія | -ія → -іє | Марія → Маріє | | Feminine -ся | -ся → -сю | бабуся → бабусю | | Masculine hard | + -е | Тарас → Тарасе, брат → брате | | Masculine -й/soft | + -ю | Андрій → Андрію, вчитель → вчителю | | Special (г, к) | г→ж, к→ч + -е | друг → друже | Self-check: How do you call your family? мама → ? тато → ? брат → ?

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
