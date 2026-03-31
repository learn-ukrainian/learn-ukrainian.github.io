<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 50: What Will Happen? (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- завтра (tomorrow)
- буду (I will — form of бути)
- будеш (you will)
- буде (he/she/it will)
- будемо (we will)
- будете (you pl. will)
- будуть (they will)
- робити (to do)
- відпочивати (to rest)
- наступний (next, adj)
- тиждень (week, m)
- план (plan, m)
- звучати (to sound)
- футбол (football, m)
- зараз (now)

## Sections to research

- **Dialogues**: Dialogue 1 — Plans for tomorrow: — Що ти будеш робити завтра? — Завтра я буду працювати. — А ввечері? — Ввечері я буду готувати вечерю. — А що буде робити Олена? — Вона буде читати. — А ви будете гуляти? — Так, ми будемо гуляти в парку! All persons of буду + infinitive.; Dialogue 2 — Weekend plans: — Що ви будете робити на вихідних? — У суботу ми будемо відпочивати. — А в неділю? — У неділю я буду готувати, а чоловік буде гуляти з дітьми. — Звучить добре! А я буду дивитися футбол. — Ти завжди будеш дивитися футбол! Future in natural planning conversation.
- **Майбутній час (Future Tense)**: Grade 3-4 textbooks: майбутній час (future tense). Ukrainian has TWO futures. At A1 we learn ONE — the analytic future: буду + infinitive (like English 'will' + verb). я буду читати (I will read) ти будеш читати (you will read) він/вона буде читати (he/she will read) ми будемо читати (we will read) ви будете читати (you will read) вони будуть читати (they will read) The infinitive stays the same — only буду changes by person.; Compare all three tenses: Минулий (past): Я читав/читала книжку. (I read a book.) Теперішній (present): Я читаю книжку. (I am reading a book.) Майбутній (future): Я буду читати книжку. (I will read a book.) Past = gender endings. Present = person endings. Future = буду + infinitive. Note: the synthetic future (прочитаю) exists but is A2 material.
- **Практика (Practice)**: Core verbs in future tense: читати → буду читати, будеш читати, буде читати... працювати → буду працювати, будеш працювати... готувати → буду готувати, будеш готувати... гуляти → буду гуляти, будеш гуляти... дивитися → буду дивитися, будеш дивитися... говорити → буду говорити, будеш говорити...; Building sentences about the future: Завтра я буду працювати з дев'ятої до п'ятої. Ввечері ми будемо дивитися фільм. У суботу вони будуть гуляти в парку. Що ви будете їсти на вечерю? Time words for future: завтра (tomorrow), наступного тижня (next week), у суботу (on Saturday), ввечері (in the evening).
- **Summary**: Analytic future formation: буду / будеш / буде / будемо / будете / будуть + infinitive. The infinitive never changes — only буду conjugates. Three tenses now: Учора я читав. (Past — gender) Зараз я читаю. (Present — person) Завтра я буду читати. (Future — буду + infinitive) Question: Що ти будеш робити? (What will you do?) Answer: Я буду + infinitive. Self-check: What will you do tomorrow morning, afternoon, and evening?

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
