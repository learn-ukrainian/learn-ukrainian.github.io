<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 26: Free Time (A1, A1.4 [Time and Nature])

## Plan vocabulary to verify

- вихідні (weekend, pl)
- спорт (sport, m)
- футбол (football, m)
- кіно (cinema, n — indeclinable)
- часто (often)
- іноді (sometimes)
- рідко (rarely)
- ходімо (let's go!)
- завжди (always)
- зазвичай (usually)
- ніколи (never)
- театр (theater, m)
- концерт (concert, m)
- музей (museum, m)
- давай (let's — informal)
- раз (once/time)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Weekend plans: — Що ти робиш у вихідні? — Зазвичай я гуляю і читаю. — Ходімо в кіно в суботу! — Добре! О котрій? — О п'ятій. — Чудово! Invitation pattern + time + day.; Dialogue 2 — Talking about hobbies: — Ти любиш спорт? — Так, я граю у футбол. — Як часто? — Двічі на тиждень, у вівторок і четвер. — А ще? — Іноді слухаю музику і малюю. Frequency + hobby vocabulary.
- **Хобі і спорт (Hobbies and Sports)**: Hobby vocabulary (extending M15 люблю + infinitive): грати у футбол / баскетбол / теніс (to play football/basketball/tennis) грати на гітарі / піаніно (to play guitar/piano — 'на' + instrument as chunk) слухати музику (to listen to music) дивитися фільми / серіали (to watch movies/series) малювати (to draw), фотографувати (to take photos); Entertainment and culture: ходити в кіно (to go to the cinema) ходити в театр (to go to the theater) ходити на концерт (to go to a concert) ходити в музей (to go to a museum) Note: ходити + в/на is a chunk — the case grammar comes in A1.5.
- **Як часто? (How Often?)**: Frequency adverbs: завжди (always), зазвичай (usually), часто (often), іноді / інколи (sometimes), рідко (rarely), ніколи (never). Word order: frequency adverb usually before the verb: Я часто гуляю. Я іноді читаю. Я ніколи не працюю у неділю. Ніколи requires не (double negation — review M19).; Frequency expressions with numbers: раз на тиждень (once a week), двічі на тиждень (twice a week), тричі на тиждень (three times a week), кожен день (every day). Я граю у футбол двічі на тиждень. Я ходжу в кіно раз на місяць.
- **Підсумок — Summary**: Free time communication: Hobbies: Я люблю + infinitive. Я граю у/на... Invitations: Ходімо! Давай! (Let's go! Let's!) Frequency: завжди, часто, іноді, рідко, ніколи. Self-check: Name 3 hobbies. How often do you do each? Invite a friend to do something this weekend.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
