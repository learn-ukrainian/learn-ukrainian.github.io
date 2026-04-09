<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 25: Покупки і послуги (B1, B1.2 [Verb System])

## Plan vocabulary to verify

- знижка (discount)
- готівка (cash)
- картка (card — payment card)
- чек (receipt)
- повернення (return — of a product)
- гарантія (guarantee/warranty)
- розмір (size)
- примірочна (fitting room)
- посилка (parcel)
- обмін валют (currency exchange)
- курс (exchange rate)
- ремонт (repair)
- бракований (defective)
- здача (change — money returned)
- тканина (fabric)
- доставка (delivery)
- переказ (money transfer)
- рахунок (bill/account)
- стрижка (haircut)
- ательє (tailor's shop)
- кав'ярня (coffee shop)
- обслуговування (service — customer service)

## Sections to research

- **На ринку**: Cultural context: Ukrainian markets (базар/ринок) as a living institution — Бессарабський ринок, Привоз, Краматорський ринок. Why markets matter culturally: direct interaction, bargaining, seasonal products, personal relationships with sellers.; Key dialogues at the market: Скільки коштує кілограм яблук? Дайте, будь ласка, півкіла. Ці помідори свіжіші за ті? А які найсмачніші? Чи можна дешевше? А якщо візьму два кілограми? Using comparatives naturally: дешевший, свіжіший, більший, смачніший.; Vocabulary in context: продавець/продавчиня, покупець/покупчиня, ваги, кілограм, ціна, знижка, здача, готівка, пакет. Reading passage: a narrative about a market visit using Phase 5 grammar.
- **У магазині**: Types of shops using word formation: книгарня (книга+-арня), взуттєвий магазин, продуктовий магазин, аптека, хімчистка, перукарня (перукар+-ня), майстерня (майстер+-ня). Practice: derive shop names from base words.; Shopping dialogue: trying on clothes Чи є цей светр у більшому розмірі? Мені потрібен менший. Де примірочна? Скільки коштує ця сукня? Ця тканина якісніша, але й дорожча. Яка найдешевша? Using comparatives and superlatives from M34-35.; Paying: Ви розраховуєтесь готівкою чи карткою? Дайте, будь ласка, чек. Чи є гарантія? Я хочу повернути цю річ. Вона бракована.
- **На пошті і в банку**: Post office vocabulary and dialogues: Я хочу відправити посилку / листа / бандероль. Скільки коштує доставка? Яка найшвидша доставка? Коли посилка дійде? Через скільки днів? Using temporal expressions with comparatives: швидше, довше.; Bank vocabulary: рахунок, переказ, обмін валют, курс. Який сьогодні курс долара? Де найвигідніший обмін? Practice dialogue: exchanging currency and comparing rates.; Comparing delivery options: Нова Пошта vs Укрпошта — which is faster, cheaper, more reliable? Extended practice using comparatives and superlatives in a real-world context Ukrainians navigate daily: Нова Пошта швидша, але дорожча. Укрпошта дешевша, але повільніша. Який найкращий варіант?
- **Послуги**: Service situations using agent nouns: перукар/перукарка — у перукарні: Мені потрібна стрижка. Коротше, будь ласка. майстер — у майстерні: Мій телефон зламався. Скільки коштує ремонт? кравець/кравчиня — в ательє: Мені потрібно вкоротити штани.; Comparing services: Ця перукарня краща за ту. У тій майстерні ремонт дешевший, але довший. Який найкращий сервіс у місті? Practice: writing a review comparing two service providers.; Word formation in action: learners analyze how the service vocabulary they encounter connects to M39 (word-formation-nouns) — перукар (agent, -ар) → перукарня (place, -ня), майстер → майстерня. This reinforces the словотвірний ланцюжок concept in a communicative context.
- **Скарга і відгук**: Polite complaint template: Вибачте, але цей товар бракований. Я купив/купила це вчора, і воно вже зламалося. Я хочу повернути товар / обміняти на інший. Мені повинні повернути гроші. Register: formal but assertive, using conditional for politeness.; Escalation phrases: Я хочу поговорити з менеджером. Це неприйнятно. Відповідно до закону про захист прав споживачів... Practice: role-play a complaint scenario with varying levels of formality.; Writing a review using comparisons: 'Ця кав'ярня — найкраща в місті. Кава тут смачніша, ніж у ... Обслуговування найшвидше. Ціни трохи вищі, але якість набагато краща.' Practice: write a 5-7 sentence review of a real or imagined place.
- **Підсумок**: Key transactional phrases organized by situation: ринок, магазин, пошта, банк, послуги, скарги. Grammar integration check: comparatives, superlatives, word formation.; Transactional phrase card: organized reference for each situation (greeting → asking → comparing → deciding → paying → complaining). Each phrase annotated with the grammar pattern it uses (comparative, superlative, agent noun, etc.).; Self-check: can you complete a full shopping interaction from start to finish? Can you compare products using three different constructions (за/від/ніж)? Can you write a complaint and a review? Preview: контрольна робота 5.

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
