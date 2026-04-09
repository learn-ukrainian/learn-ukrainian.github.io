<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 15: What I Like (A1, A1.3 [Actions])

## Plan vocabulary to verify

- любити (to love/like — verb)
- подобатися (to be pleasing — used as 'to like')
- читати (to read)
- гуляти (to walk)
- готувати (to cook)
- слухати (to listen)
- дивитися (to watch)
- грати (to play)
- малювати (to draw)
- подорожувати (to travel)
- співати (to sing)
- музика (music, f)
- фільм (film, m)
- книга (book — review from M08)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Meeting someone's interests (ULP Ep14 pattern): — Що ти любиш робити? — Я люблю читати і слухати музику. — А я люблю готувати. — Правда? Що ти готуєш? Infinitives introduced naturally through 'люблю + verb'.; Dialogue 2 — Describing preferences: — Тобі подобається ця книга? — Так, мені подобається. — А цей фільм? — Ні, мені не подобається. Мені подобається музика. 'Подобається' as a fixed chunk — dative grammar NOT analyzed.
- **Я люблю... (I Like...)**: Люблю + infinitive (what you enjoy doing): Я люблю читати (I like to read). Я люблю гуляти (I like to walk). Я люблю готувати (I like to cook). Я люблю слухати музику (I like to listen to music). Pattern: subject + люблю + infinitive (-ти ending). Infinitive = dictionary form of the verb, always ends in -ти.; Common infinitives for hobbies (new vocabulary): читати (to read), гуляти (to walk), готувати (to cook), слухати (to listen), дивитися (to watch), грати (to play), малювати (to draw), подорожувати (to travel), співати (to sing). Pronunciation: the stress in infinitives varies — learn each one.
- **Мені подобається... (I Like...)**: Two ways to say 'I like' — different grammar, same meaning at A1: Я люблю + infinitive = I love/like doing something. Мені подобається + noun = I like something (a thing). Мені подобається музика. Мені подобається ця книга. Мені подобається Київ. Note: 'мені подобається' is a chunk — we don't analyze WHY мені (dative). Just use it.; Negative: Я не люблю / Мені не подобається: Я не люблю готувати. Мені не подобається цей фільм. Question: Ти любиш читати? Тобі подобається? Note: люблю changes by person (я люблю, ти любиш) — full conjugation in M17 (Group II).
- **Підсумок — Summary**: Two structures for 'like': 1. Я люблю + infinitive (-ти) — for activities 2. Мені подобається + noun — for things Negative: не before the verb (не люблю, не подобається). Self-check: Name 3 things you like doing (Я люблю...). Name 2 things you like (Мені подобається...). Name 1 thing you don't like (Я не люблю... / Мені не подобається...).

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
