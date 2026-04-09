<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 11: How Many? (A1, A1.2 [My World])

## Plan vocabulary to verify

- один, два, три, чотири, п'ять (1-5)
- шість, сім, вісім, дев'ять, десять (6-10)
- двадцять, тридцять, сорок (20, 30, 40)
- сто, тисяча (100, 1000)
- скільки (how many/how much)
- коштує (costs — from коштувати)
- гривня (hryvnia — Ukrainian currency)
- рік, роки, років (year/years — age chunks)
- п'ятдесят, шістдесят, сімдесят (50, 60, 70)
- вісімдесят, дев'яносто (80, 90)
- двісті, триста, п'ятсот (200, 300, 500)
- копійка (kopek)
- номер (number — phone/room)
- нуль (zero)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — At a market stall: — Скільки коштує сумка? — Двісті гривень. — А маленька? — Сто п'ятдесят. — Добре, дякую! Numbers emerge through real shopping context. Uses only vocabulary from M08-M10 (gender, adjectives, colors). Demonstratives (ця/та) come in M12.; Dialogue 2 — Meeting someone new (extending M05): — Скільки тобі років? — Мені двадцять п'ять. А тобі? — Мені тридцять два. А твоя сестра? — Їй вісімнадцять. Age formula as chunk: Мені/тобі/їй + number + років/роки/рік.
- **Числа 1-20 (Numbers 1-20)**: 1-10: один, два, три, чотири, п'ять, шість, сім, вісім, дев'ять, десять. Pronunciation focus: п'ять (apostrophe!), сім (not 'сем'), дев'ять (apostrophe!). Practice: counting objects from M08 — один стіл, два стільці, три книги. Note: the noun changes after numbers, but we learn the PATTERNS as chunks, not the grammar rule.; 11-20: одинадцять, дванадцять, тринадцять, чотирнадцять, п'ятнадцять, шістнадцять, сімнадцять, вісімнадцять, дев'ятнадцять, двадцять. Pattern: base + -надцять (like English '-teen'). Watch the stress: одинáдцять, дванáдцять — stress always falls on the syllable 'на' in -надцять.
- **Десятки і сотні (Tens and Hundreds)**: Tens: двадцять, тридцять, сорок (!), п'ятдесят, шістдесят, сімдесят, вісімдесят, дев'яносто (!), сто. Two irregulars: сорок (40 — not 'чотиридесят') and дев'яносто (90 — not 'дев'ятдесят'). Combined: двадцять один, тридцять п'ять, сорок сім — just add the unit.; Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400), п'ятсот (500), тисяча (1000). Гривня: одна гривня, дві гривні, п'ять гривень. These noun changes are memorized patterns — grammar comes in A2. ULP Ep9: Anna teaches numbers through real prices.
- **Підсумок — Summary**: Three practical uses of numbers: 1. Prices: Скільки коштує? — Двісті гривень. Сто п'ятдесят гривень. 2. Age: Скільки тобі років? — Мені двадцять три (роки). 3. Phone: Мій номер — нуль дев'яносто сім, три два один, сорок п'ять, шістдесят сім. Self-check: Say your age in Ukrainian. Say a price (250 hryvnias). Read a phone number.

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
