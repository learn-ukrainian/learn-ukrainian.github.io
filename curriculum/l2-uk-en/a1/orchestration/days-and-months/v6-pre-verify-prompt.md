<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 23: Days and Months (A1, A1.4 [Time and Nature])

## Plan vocabulary to verify

- понеділок, вівторок, середа (Mon, Tue, Wed)
- четвер, п'ятниця (Thu, Fri)
- субота, неділя (Sat, Sun)
- тиждень (week, m)
- зима, весна, літо, осінь (winter, spring, summer, autumn)
- січень, лютий, березень (Jan, Feb, Mar)
- квітень, травень, червень (Apr, May, Jun)
- липень, серпень, вересень (Jul, Aug, Sep)
- жовтень, листопад, грудень (Oct, Nov, Dec)
- день народження (birthday)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Planning the week (ULP Ep15 pattern): — Що ти робиш у понеділок? — Я працюю. А у вівторок? — У вівторок я вивчаю українську. — А у суботу? — У суботу гуляю. Неділя — вільний день! Days of the week in practical scheduling.; Dialogue 2 — When is your birthday? — Коли у тебе день народження? — У березні. — Якого числа? — П'ятнадцятого березня. А у тебе? — У мене в серпні. — О, це літо! Months and seasons in personal context.
- **Дні тижня (Days of the Week)**: Seven days — all LOWERCASE in Ukrainian (not capitalized like English): понеділок (Monday), вівторок (Tuesday), середа (Wednesday), четвер (Thursday), п'ятниця (Friday), субота (Saturday), неділя (Sunday). Вашуленко Grade 2 p.83: planning your week activity. Note: неділя = Sunday AND 'week' in some dialects. Standard 'week' = тиждень.; 'On' a day = у/в + accusative (chunk — no grammar analysis): у понеділок, у вівторок, у середу, у четвер, у п'ятницю, в суботу, в неділю. Note the endings change — just memorize each form.
- **Місяці і пори року (Months and Seasons)**: 12 months — also lowercase, organized by season: Зима: грудень (Dec), січень (Jan), лютий (Feb). Весна: березень (Mar), квітень (Apr), травень (May). Літо: червень (Jun), липень (Jul), серпень (Aug). Осінь: вересень (Sep), жовтень (Oct), листопад (Nov). All months are masculine. Many come from nature words (березень ← береза, липень ← липа, листопад ← листя падає).; 4 seasons: зима (winter, f), весна (spring, f), літо (summer, n), осінь (autumn, f). 'In' a month/season = у/в + locative (chunk): у січні, у лютому, в березні... влітку, взимку, восени, навесні. Seasonal forms are irregular — memorize as chunks.
- **Підсумок — Summary**: Calendar vocabulary: Days: понеділок → неділя (у понеділок, в суботу). Months: січень → грудень (у січні, в серпні). Seasons: зима, весна, літо, осінь (взимку, навесні, влітку, восени). Self-check: What day is today? What month? What season? When is your birthday? Plan your next week in Ukrainian.

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
