<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 37: I Eat, I Drink (A1, A1.6 [Food and Shopping])

## Plan vocabulary to verify

- їсти (to eat — irregular)
- пити (to drink)
- їм (I eat)
- п'ю (I drink)
- каву (coffee — accusative)
- воду (water — accusative)
- рибу (fish — accusative)
- кашу (porridge — accusative)
- картоплю (potato — accusative)
- сметану (sour cream — accusative)
- їсть (he/she eats)
- п'є (he/she drinks)
- їдять (they eat)
- п'ють (they drink)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Breakfast conversation: — Що ти їш на сніданок? — Я їм кашу і п'ю каву. — А Олена? — Вона їсть хліб з маслом і п'є чай. — А діти? — Вони їдять яйця і п'ють молоко. Full conjugation of їсти and пити in natural context.; Dialogue 2 — At lunch: — Що ви їсте на обід? — Ми їмо суп і салат. — А що п'єте? — Ми п'ємо воду або сік. — Я теж хочу суп. — Добре, замовляй! Review of їсти/пити with plural subjects.
- **Їсти і пити (To Eat and To Drink)**: Conjugation of їсти (irregular — NOT Group I or II): я їм, ти їси, він/вона їсть, ми їмо, ви їсте, вони їдять. Conjugation of пити (Group I): я п'ю, ти п'єш, він/вона п'є, ми п'ємо, ви п'єте, вони п'ють. Both are essential daily verbs — high frequency.; Ukrainian school approach (Grade 4 — знахідний відмінок): 'Бачу що? кого?' — the accusative answers 'what do I see/eat/drink?' Я їм (що?) хліб. Я п'ю (що?) каву. The question що? triggers accusative for inanimate objects.
- **Знахідний відмінок — неживе (Accusative Inanimate)**: Accusative for inanimate nouns — what changes: Masculine inanimate: NO CHANGE (= nominative). хліб → хліб (Я їм хліб), суп → суп (Я їм суп), сік → сік (Я п'ю сік). Neuter: NO CHANGE (= nominative). молоко → молоко (Я п'ю молоко), яйце → яйце (Я їм яйце).; Feminine -а → -у (THE key change at A1): кава → каву (Я п'ю каву), вода → воду (Я п'ю воду), риба → рибу (Я їм рибу), каша → кашу (Я їм кашу), картопля → картоплю (Я їм картоплю). Pattern: feminine nouns ending in -а change to -у, ending in -я change to -ю. This is the ONLY accusative change learners need now.
- **Підсумок — Summary**: Accusative inanimate summary: Masculine/Neuter: no change (хліб, молоко stay the same). Feminine -а → -у, -я → -ю (кава → каву, картопля → картоплю). Test: Я їм ___ (риба → рибу). Я п'ю ___ (вода → воду). Self-check: Say 3 things you eat and 3 things you drink today. Use the correct accusative form for each.

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
