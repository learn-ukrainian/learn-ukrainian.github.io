<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 49: Той, який... (A2, A2.7 [Complex Sentences and Conditionals])

## Plan vocabulary to verify

- який (which, that — masc.)
- яка (which, that — fem.)
- яке (which, that — neut.)
- які (which, that — pl.)
- де (where — relative)
- куди (where to — relative)
- звідки (where from — relative)
- означальний (attributive, defining)
- описувати (to describe)
- речення (sentence, clause)
- котрий (which — formal synonym of який)
- затишний (cozy, comfortable)
- знаходитися (to be located)
- стояти (to stand, to be situated)

## Sections to research

- **Який? Яка? Яке? Які? (Which? What Kind?)**: Introducing relative clauses (означальні підрядні речення): a clause that describes a noun in the main sentence. The relative pronoun який agrees with the noun it refers to in gender and number.; Gender and number agreement: Книжка, яка лежить на столі... Хлопець, який прийшов вчора... Місто, яке я люблю... Друзі, які живуть у Києві...; Case of який: it takes the case required by its role in the subordinate clause, not the main clause. Людина, яку я зустрів (Acc.) vs. Людина, яка мене зустріла (Nom.). At A2 level, focus on Nominative and Accusative cases of який.
- **Де, куди, звідки — місце (Where, Where To, Where From — Place)**: Using де as a relative word for places: Кафе, де ми зустрілися, було затишне. Місто, де я народився, знаходиться на заході.; Using куди for direction: Парк, куди ми ходимо гуляти, дуже гарний.; Using звідки for origin: Країна, звідки вона приїхала, — це Україна.
- **Описуємо людей, речі та місця (Describing People, Things, and Places)**: Building longer descriptions by combining relative clauses with previously learned grammar: Подруга, яка живе у Львові, працює вчителькою. Ресторан, де ми вчора вечеряли, знаходиться біля парку.; Avoiding common errors: redundant pronoun (Книжка, яка вона цікава = WRONG), wrong gender agreement (Хлопець, яке = WRONG), missing comma.; Stacking information naturally: instead of many short sentences (Це мій друг. Він живе у Києві. Він працює програмістом.), combine with який: Це мій друг, який живе у Києві і працює програмістом.

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
