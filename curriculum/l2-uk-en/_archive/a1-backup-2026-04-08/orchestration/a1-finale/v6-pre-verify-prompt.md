<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 55: A1 Finale (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- готовий (ready, adj m)
- вітаю (congratulations — chunk)
- початок (beginning, m)
- сувенір (souvenir, m)
- квиток (ticket, m)
- зустріти (to meet)
- круасан (croissant, m)
- карта (map, f)
- лінія (line, f)
- фільм (film, m)
- познайомитися (to get acquainted)
- подорожувати (to travel)
- Лавра (Lavra — Kyiv monastery)
- готель (hotel, m)

## Sections to research

- **Ранок (Morning)**: Scenario: You wake up in Kyiv. 7:00 — Ти прокинувся/прокинулася в готелі. (Past tense — M48) Доброго ранку! Яка сьогодні погода? — Сьогодні тепло і сонячно. (Weather — M24) Ти снідаєш у кафе: Будь ласка, каву з молоком і круасан. (Food — M36, cafe — M28) Скільки коштує? — Сто двадцять гривень. (Numbers — M10, shopping — M37) Дякую! До побачення! (Greetings — M01-M05); Getting around: Вибачте, як дістатися до Хрещатика? — Їдьте на метро, станція Хрещатик. (Transport — M34) Ти купуєш квиток. Один квиток, будь ласка. (Numbers, polite requests — M43) В метро ти дивишся на карту. Тобі потрібна зелена лінія. (Colors — M22) Past tense narration + present tense actions.
- **День (Daytime)**: Exploring the city: Ти гуляєш по Хрещатику. Яка гарна вулиця! (City — M30, adjectives — M09) Ти бачиш великий магазин. Ти заходиш і купуєш сувеніри. (Shopping — M37) Скільки коштує ця вишиванка? — Тисяча двісті гривень. Дорого! (Demonstratives — M12) А ця? — Ця — вісімсот. — Добре, я беру! (This/that — M12); Lunch with a new friend: В кафе ти зустрічаєш Олену. — Привіт! Ти звідки? — Я з Канади. (Where from — M06) — Що ти робиш тут? — Я вивчаю українську! (Verbs — M16-17) — Як цікаво! Ходімо обідати! (Imperative — M43) Ти замовляєш борщ і вареники. Олена замовляє салат. (Food — M36) — Смачно! Ти добре говориш українською! — Дякую!
- **Вечір (Evening)**: Evening plans: — Що будемо робити ввечері? — Ходімо в кіно! (Future — M50, invitations — M51) — Добре! О котрій? — О сьомій. (Time — M26) Ви дивитеся український фільм. Ти не все розумієш, але багато! (Linking — M44) Після кіно ви йдете в ресторан. (After — M44, directions — M31); Reflecting on the day: Ввечері в готелі ти думаєш про свій день. Сьогодні був чудовий день! Зранку я снідав/снідала у кафе. Потім я гуляв/гуляла по місту і познайомився/познайомилася з Оленою. Ввечері ми ходили в кіно і ресторан. Завтра я буду їздити по Києву. Я хочу побачити Лавру! All three tenses in natural reflection — past (the day), present (feelings), future (tomorrow).
- **Підсумок: ти готовий/готова! (You're Ready!)**: A1 skills checklist — everything you can now do: Greet, introduce yourself, say where you're from (A1.1). Describe people, things, your family (A1.2). Talk about actions, likes, habits (A1.3). Tell time, discuss weather, name days and months (A1.4). Navigate a city, give directions, use transport (A1.5). Order food, shop, handle money (A1.6). Address people politely, give instructions, connect ideas (A1.7). Talk about the past, make plans, handle health and emergencies (A1.8).; What's next — A2 preview: You'll learn: cases (відмінки), aspect (доконаний/недоконаний вид), synthetic future (прочитаю), subordinate clauses, and much more. But right now — celebrate! Ти вивчив/вивчила A1! Вітаю! Ти вже можеш жити в українському місті. Це тільки початок! Self-check: Can you describe YOUR day in a Ukrainian city in 10+ sentences?

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
