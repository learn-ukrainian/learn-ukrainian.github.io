<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 64: Контрольна робота 5 (B1, B1.5 [Case Nuances & Prepositions])

## Plan vocabulary to verify

- повторення (review)
- самооцінка (self-assessment)
- комплексний (comprehensive)
- діагностика (diagnostics)
- рубрика (rubric)
- аналіз помилок (error analysis)
- прогалина (gap — in knowledge)

## Sections to research

- **Повторення: відмінки**: Genitive review — five semantic roles: 1. Частковий: склянка води, багато часу. 2. Бажання/пошуку: шукати правди, бажати щастя. 3. Заперечення: немає часу, не бачив друга. 4. Дати: п'ятнадцятого березня, цього тижня. 5. -а/-я vs -у/-ю: стола vs часу (semantic categories). Drill: 12 sentences requiring correct Р.в. usage.; Dative review — four semantic roles: 1. Суб'єкт стану: мені холодно, тобі не спиться. 2. Вік: мені двадцять років. 3. Безособові: потрібно, варто, вдалося, довелося. 4. Адресат: допомагати другові, телефонувати лікарю. Drill: 10 sentences requiring correct Д.в. usage.; Instrumental review — five semantic roles: 1. Характеристика: працювати лікарем, стати вчителькою. 2. Засіб: писати ручкою, їхати автобусом. 3. Шлях: іти вулицею, їхати дорогою. 4. Керування: захоплюватися, цікавитися, пишатися. 5. Агент пасиву: написано автором. Drill: 10 sentences requiring correct Ор.в. usage.
- **Повторення: прийменники**: Temporal prepositions reference: через + Зн.в. (after period), за + Зн.в. (within period), перед + Ор.в. (before), після + Р.в. (after), до + Р.в. (until), під час + Р.в. (during), протягом + Р.в. (throughout), на + Зн.в. (for duration).; Cause/purpose prepositions reference: Cause: через (neg.), завдяки (pos.), від (reaction), з (motivation), внаслідок (formal result), у зв'язку з (formal connection). Purpose: для, заради, за + Ор.в. (fetch), щоб + inf. Golden rule: завдяки = GOOD, через = BAD. Compound: через те що, завдяки тому що, для того щоб. Drill: 12 mixed sentences choosing correct preposition + case.
- **Повторення: кличний, числівники, займенники**: Vocative in formal contexts: ім'я + по батькові: Іване Петровичу, Маріє Степанівно. Title + прізвище: лікарю Петренко (тільки перше в Кл.в.). Practice: form correct vocative for 8 formal address scenarios.; Numerals: ordinal declension (like adjectives, compound — last word only), cardinal agreement (1 + Н.в., 2-4 + Н.в.мн., 5+ + Р.в.мн.), collective numerals (двоє, троє + Р.в.мн.), dates (Р.в.) and time (о + М.в., за десять хвилин). Drill: 10 numeral usage exercises.; Pronouns: interrogative-relative (хто, який, чий — declension), reflexive (себе/собі/собою), indefinite (хтось, будь-хто, -небудь), negative (ніхто, ніщо — preposition splits: ні з ким), означальні (кожний, весь/увесь, сам, інший). Fractions: половина, третина, чверть + Р.в., півтора/півтори. Drill: 12 pronoun and numeral exercises with spelling, case, and agreement.
- **Комплексні завдання**: Text analysis: a Ukrainian newspaper article about housing in a city. Tasks: identify all case usages, prepositions, numerals, and pronouns. Answer comprehension questions requiring correct grammar in responses.; Error correction block: 12-15 sentences with mixed errors across ALL Phase 6 topics — wrong case, wrong preposition, agreement errors, pronoun spelling, vocative mistakes, Russicisms in time/cause expressions. Each error must be identified, categorised, and corrected.; Production task: write a formal email to a landlord describing your housing needs, asking about availability, and negotiating terms. Must include: vocative address, case constructions, temporal prepositions, cause/purpose expressions, quantity expressions. Self-assessment rubric provided.
- **Самооцінка та підготовка до Фази 7**: Self-check grid for all Phase 6 topics: Can I use Р.в. for partitive, negation, dates? ___ Can I use Д.в. for experiencer, age, impersonal? ___ Can I use Ор.в. for characterisation, means, path? ___ Can I form vocative for formal address? ___ Can I decline and agree numerals? ___ Can I use indefinite and negative pronouns? ___ Can I choose correct temporal and cause/purpose prepositions? ___; Gap analysis: which areas need more practice? Preview of Phase 7: дієприкметники і дієприслівники (participles and gerunds). The shift from USING cases precisely to BUILDING complex modifiers.; Diagnostic: 15 quick-check questions covering all Phase 6 topics, with answer key and explanations.
- **Підсумок**: Phase 6 achievement summary: advanced case usage (genitive with 15+ prepositions, dative of experiencer and purpose, instrumental with 8+ prepositions and manner), formal vocative with patronymics and profession + name, temporal and cause/purpose prepositions, ordinal and cardinal numeral declension with fractions, complete pronoun system (indefinite, negative, definitive, reflexive). These are the building blocks for Phase 7 (participles) and Phase 8 (complex syntax), where precise case knowledge becomes essential.; Transition to Phase 7: дієприкметники (participles) require precise case agreement — a дієприкметник agrees with its noun in gender, number, AND case. All the case knowledge from Phase 6 becomes the foundation for building complex modifiers.

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
