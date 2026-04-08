<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 28: Над, під, між (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- над (above, over)
- під (under, below)
- перед (in front of; before (temporal))
- за (behind; according to)
- між (between)
- стіл (table)
- будинок (building, house)
- ліжко (bed)
- стіна (wall)
- обід (lunch)
- стеля (ceiling)
- підлога (floor)
- кут (corner)
- розклад (schedule)
- сон (sleep, dream)

## Sections to research

- **Просторові прийменники: Де це? (Spatial Prepositions: Where Is It?)**: Five key spatial prepositions that take the Instrumental case: над (above/over), під (under/below), перед (in front of), за (behind/beyond), між (between).; над + Ор.в.: Лампа висить над столом. Птах летить над містом. Хмари над горами.; під + Ор.в.: Кіт сидить під столом. Книга лежить під ліжком. Підвал під будинком.
- **Описуємо кімнату (Describing a Room)**: Practical application: describing where objects are in a room — Картина висить над ліжком. Килим лежить під столом. Шафа стоїть між вікном і дверима.; Question-answer pattern: Де лампа? — Лампа над столом. Де кіт? — Під ліжком. Де ваза? — Між книгами.; Dialogue: Two roommates arranging furniture. One asks where to put things, the other gives directions using preposition + Instrumental.
- **Перед обідом, за розкладом: Часове значення (Before Lunch, On Schedule: Temporal Meaning)**: перед + Ор.в. for "before" in time: перед обідом (before lunch), перед уроком (before class), перед сном (before sleep), перед відпусткою (before vacation).; за + Ор.в. for fixed temporal expressions: за розкладом (according to schedule), за планом (according to plan).; Contrast with spatial meaning: перед будинком (in front of — spatial) vs. перед обідом (before — temporal). Same case, different meaning.
- **Практика: Де? Коли? (Practice: Where? When?)**: Picture description exercise: look at a scene and describe locations using над, під, перед, за, між.; Daily schedule exercise: Що ти робиш перед сніданком? Перед роботою? Перед сном?; Contrastive pairs: за + Instrumental (behind — location) vs. за + Accusative (for — purpose). За будинком (behind the house) vs. Дякую за допомогу (thank you for help).

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
