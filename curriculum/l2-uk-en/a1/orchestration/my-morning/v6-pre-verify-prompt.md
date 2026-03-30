<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 20: My Morning (A1, A1.3 [Actions])

## Plan vocabulary to verify

- прокидатися (to wake up)
- вмиватися (to wash face/hands)
- одягатися (to get dressed)
- снідати (to have breakfast)
- йти (to go — irregular)
- спочатку (first, at first)
- потім (then, next)
- збиратися (to get ready)
- повертатися (to return)
- навчатися (to study/learn)
- поспішати (to hurry)
- після цього (after this)
- нарешті (finally)
- вранці (in the morning)
- пізно (late)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Morning routine: — Коли ти прокидаєшся? — Я прокидаюся о сьомій. — Що ти робиш потім? — Вмиваюся, одягаюся і снідаю. — А коли ти йдеш на роботу? — О восьмій. Reflexive verbs emerge through describing the morning.; Dialogue 2 — Weekend morning (contrast): — У суботу я не поспішаю. Прокидаюся пізно, лежу, дивлюся телефон. — А я навчаюся вранці. Потім гуляю. Mix of reflexive and non-reflexive verbs.
- **Дієслова на -ся (Reflexive Verbs)**: Караман Grade 10 p.176: Дієслова із суфіксом -ся(-сь) означають дію, спрямовану на себе. вмивати (to wash someone) → вмиватися (to wash oneself). одягати (to dress someone) → одягатися (to dress oneself). The -ся attaches to the end of every conjugated form: я вмиваюся, ти вмиваєшся, він/вона вмивається.; Кравцова Grade 4 p.113: pronunciation note: -шся sounds like [с':а] (long soft с): вмиваєшся → [вмиваєс':а]. -ться sounds like [ц':а] (long soft ц): вмивається → [вмиваєц':а]. The spelling and pronunciation differ — learn both!
- **Мій ранок (My Morning)**: Morning routine vocabulary (reflexive verbs): прокидатися (to wake up), вмиватися (to wash face/hands), одягатися (to get dressed), збиратися (to get ready), повертатися (to return home). Non-reflexive morning verbs for contrast: снідати (to have breakfast), пити каву (to drink coffee). Йти (to go) — irregular: я йду, ти йдеш, він/вона йде. Learn these forms — they don't follow Group I or II patterns.; Sequence words for telling a story: спочатку (first), потім (then), після цього (after this), нарешті (finally). Мій ранок: Спочатку я прокидаюся. Потім вмиваюся і одягаюся. Після цього снідаю. Нарешті йду на роботу.
- **Підсумок — Summary**: Reflexive verbs = regular verb + ся at the end. я -юся, ти -єшся, він/вона -ється (Group I pattern + ся). Morning routine: прокидатися → вмиватися → одягатися → снідати → йти. Sequence words: спочатку, потім, після цього, нарешті. Self-check: Describe your morning in 4-5 sentences using sequence words.

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
