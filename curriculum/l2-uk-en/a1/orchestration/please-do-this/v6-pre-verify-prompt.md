<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 43: Please Do This (A1, A1.7 [Communication])

## Plan vocabulary to verify

- читати (to read)
- писати (to write)
- слухати (to listen)
- дивитися (to look/watch)
- говорити (to speak)
- дати (to give)
- сказати (to say/tell)
- іти (to go)
- відкрити (to open)
- сісти (to sit down)
- показати (to show)
- запитати (to ask)
- підручник (textbook, m)
- сторінка (page, f)
- речення (sentence, n)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — In the classroom: — Відкрийте підручники, будь ласка. Читайте текст. — Вибачте, яку сторінку? — Сторінку двадцять три. — Тепер пишіть. Напишіть три речення. — Можна запитати? — Так, запитуйте! Classroom imperatives: відкрийте, читайте, пишіть, напишіть.; Dialogue 2 — Between friends: — Слухай, ходімо в кафе! — Добре, йди, я зараз. — Подивись, яка гарна погода! — Так! Сідай тут. — Дай мені меню, будь ласка. — Ось, дивись. — Скажи, що ти хочеш? — Я хочу каву. Informal imperatives: слухай, подивись, сідай, дай, скажи.
- **Наказовий спосіб (The Imperative Mood)**: Ukrainian Grade 5 term: наказовий спосіб (imperative mood). Used for commands, requests, instructions, invitations. Two forms at A1: ти (informal, one person) and ви (formal or plural). Будь ласка makes any command polite: Дай! (Give!) → Дай, будь ласка. (Please give.) Дайте! (Give! — formal) → Дайте, будь ласка.; Not rude — just direct: Ukrainian imperatives are normal in daily speech. Читай! is not rude — it's how teachers, parents, friends talk. Adding будь ласка = polite. Adding tone + name = friendly: Олено, прочитай, будь ласка. (Olena, please read.)
- **Як утворити? (How to Form It)**: Ти-form (informal, singular): Group I (-ати): читати → читай, слухати → слухай, писати → пиши. Group II (-ити): говорити → говори, дивитися → дивись, ходити → ходи. Irregular (common): дати → дай, сказати → скажи, їсти → їж, іти → іди. Pattern: stem + ending. Most are short — one or two syllables.; Ви-form (formal or plural): Add -те to the ти-form: читай → читайте, слухай → слухайте, пиши → пишіть, говори → говоріть, дивись → дивіться, ходи → ходіть, дай → дайте, скажи → скажіть, іди → ідіть. Note: some get -іть (not -ить) — stress shifts: пиши → пишіть, сиди → сидіть, дивись → дивіться.
- **Підсумок — Summary**: Essential imperatives for daily life: | Infinitive | Ти | Ви | Meaning | | читати | читай | читайте | read | | писати | пиши | пишіть | write | | слухати | слухай | слухайте | listen | | дивитися | дивись | дивіться | look | | говорити | говори | говоріть | speak | | іти | іди | ідіть | go | | дати | дай | дайте | give | | сказати | скажи | скажіть | say/tell | | сісти | сядь | сядьте | sit down | | відкрити | відкрий | відкрийте | open | Self-check: How do you say 'Please read' to your teacher? To your friend?

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
