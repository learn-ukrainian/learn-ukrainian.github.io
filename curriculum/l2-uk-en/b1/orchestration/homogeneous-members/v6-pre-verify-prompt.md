<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 52: Однорідні члени речення (B1, B1.7 [Complex Syntax])

## Plan vocabulary to verify

- однорідний (homogeneous — members that are equal in syntactic function)
- сполучник (conjunction — word connecting sentence parts)
- єднальний (coordinating/additive — conjunction type: і, та)
- протиставний (adversative — conjunction type: а, але, проте)
- розділовий (disjunctive — conjunction type: або, чи)
- узагальнювальний (generalizing — a word that summarizes a list)
- двокрапка (colon — punctuation mark after узагальнювальне слово)
- тире (dash — punctuation mark before узагальнювальне слово)
- кома (comma — basic punctuation between однорідні члени)
- пунктуація (punctuation — system of розділові знаки)
- перелік (enumeration/list — a series of однорідні члени)
- інтонація (intonation — voice pattern for listing)
- підмет (subject — sentence member that can be однорідний)
- присудок (predicate — sentence member that can be однорідний)
- додаток (object — sentence member that can be однорідний)
- означення (attribute/modifier — sentence member that can be однорідний)
- обставина (adverbial — sentence member that can be однорідний)
- речення (sentence — syntactic unit containing однорідні члени)
- синтаксичний (syntactic — relating to sentence structure)
- перелічувальний (enumerative — type of intonation for lists)
- відокремлений (detached/parenthetical — contrasted with однорідний)
- асиндетон (asyndeton — listing without conjunctions)

## Sections to research

- **Однорідні члени: визначення і розпізнавання**: Definition (Заболотний Grade 5 p.178): Однорідними називають члени речення, які залежать від того самого слова в реченні, відповідають на те саме питання і виконують однакову синтаксичну роль. Приклад: Фермер засіяв поля пшеницею, вівсом і ячменем. (Три однорідні додатки — чим? — залежать від засіяв.); Any sentence member can be однорідний (Глазова Grade 11 p.126): Однорідні підмети: Діти і дорослі зібралися на свято. Однорідні присудки: Вона читала, писала і малювала. Однорідні додатки: Купив хліб, молоко та масло. Однорідні означення: Високе, стрункий, зелене дерево. Однорідні обставини: Він працював швидко, точно і сумлінно.; How to identify — three tests: 1. Чи відповідають на те саме питання? (Do they answer the same question?) 2. Чи залежать від того самого слова? (Do they depend on the same word?) 3. Чи виконують однакову синтаксичну роль? (Do they serve the same syntactic function?) If all three = YES → однорідні.
- **Сполучники при однорідних членах**: Three types of conjunctions (Авраменко Grade 7 p.173): Єднальні (coordinating/ additive): і (й), та (= і), також. Протиставні (adversative): а, але, проте, та (= але), зате, однак. Розділові (disjunctive): або, чи, то...то, хоч...хоч.; Punctuation rules with єднальні сполучники (Глазова Grade 11 p.126): Single і/й/та (= і) — NO comma: Поезія — безмежний степ і лебединий легіт. Repeated і...і / та...та — COMMA before each repeated conjunction: Душа і трудиться, і мріє. І яблука, і груші, і сливи — все дозріло.; Punctuation with протиставні сполучники: ALWAYS comma before а, але, проте, зате, однак: Підніматися вгору важко, але радісно. Він не великий, а середній. Слово маленьке, проте важливе. No exceptions — протиставні always require a comma.
- **Узагальнювальне слово**: Definition (Заболотний Grade 8 p.25): Узагальнювальне слово — a word that generalizes or summarizes the entire list of однорідні члени. Common узагальнювальні слова: все (everything), всі (everyone), скрізь (everywhere), завжди (always), ніхто (nobody), ніщо (nothing), ніколи (never), кожен (each), усюди (everywhere).; Punctuation rule 1 — узагальнювальне слово BEFORE the list → двокрапка: Усе зраділо стрічаючи день: і трави, і квіти, і птахи. Він побував скрізь: у Києві, Львові, Одесі й Харкові. Pattern: [узагальнювальне]: [однорідний 1], [однорідний 2], [однорідний 3].; Punctuation rule 2 — однорідні члени BEFORE узагальнювальне слово → тире: І трави, і квіти, і птахи — усе зраділо. У Києві, Львові, Одесі — скрізь він побував. Pattern: [однорідний 1], [однорідний 2], [однорідний 3] — [узагальнювальне].
- **Підсумок: однорідні члени в тексті**: Summary punctuation table: Single і/й/та(=і)/або/чи → no comma. Repeated і...і/та...та/або...або/чи...чи/то...то → comma. а/але/проте/зате/однак → always comma. Узагальнювальне before list → двокрапка. List before узагальнювальне → тире. Both → двокрапка...тире.; Stylistic use of однорідні члени in writing: Enumeration creates rhythm and emphasis. Asyndeton (without conjunctions) speeds up: Прийшов, побачив, переміг. Polysyndeton (repeated conjunctions) slows down, adds weight: І прийшов, і побачив, і переміг. Learners analyze examples from Ukrainian literature.; Common errors to avoid: *Я люблю читати, і малювати (comma before single і — WRONG). *Він не великий але сильний (no comma before але — WRONG). *Усе зраділо, і трави, і квіти (missing двокрапка after узагальнювальне — WRONG, should be: Усе зраділо: і трави, і квіти).

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

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
