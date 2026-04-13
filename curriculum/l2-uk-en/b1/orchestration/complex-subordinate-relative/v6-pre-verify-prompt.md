<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 77: Означальні речення (B1, B1.7 [Complex Syntax])

## Plan vocabulary to verify

- означальне речення (attributive/relative clause)
- який/яка/яке/які (which/that — relative pronoun, declines)
- означуване слово (antecedent — noun the clause describes)
- сполучне слово (connective word — який, що, де, куди, коли)
- відмінок (case — determines the form of який in the clause)
- чий (whose — possessive relative pronoun)
- котрий (which — literary synonym of який)
- антецедент (antecedent — formal term for означуване слово)
- постпозиція (postposition — clause always after the noun)

## Sections to research

- **Означальні підрядні речення**: Definition from Заболотний Grade 8 p.84: означальна підрядна частина характеризує іменник (або займенник) у головній частині і відповідає на питання який? яка? яке? які? чий? Місто, яке я відвідав, мене вразило. Людина, яка багато читає, має широкий кругозір.; The підрядна означальна refers to a SPECIFIC noun (означуване слово) in the main clause and always stands AFTER that noun: Книга, яку я прочитав, лежить на столі. Not: *Яку я прочитав, книга лежить на столі. (ungrammatical); Connection to M59 (дієприкметниковий зворот): Книга, прочитана мною, лежить на столі. (participle phrase) = Книга, яку я прочитав, лежить на столі. (означальне речення) The clause is MORE NATURAL in spoken Ukrainian.
- **Який у різних відмінках**: The relative pronoun який declines like an adjective and must agree with its antecedent in gender and number, but its CASE is determined by its role in the subordinate clause: Н.в.: Студент, який вивчає українську, живе в Києві. (який = subject) Р.в.: Студент, якого я знаю, живе в Києві. (якого = object) Д.в.: Студент, якому я допоміг, живе в Києві. (якому = indirect object) Зн.в.: Книга, яку я прочитав, лежить на столі. (яку = direct object) Ор.в.: Людина, якою я захоплююсь, живе далеко. (якою = instrumental) М.в.: Місто, в якому я живу, дуже красиве. (в якому = locative); Gender and number agreement: Хлопець, який... (ч.р., одн.) Дівчина, яка... (ж.р., одн.) Місто, яке... (с.р., одн.) Люди, які... (мн.) The case of який depends on the clause, not the main sentence: Я знаю людину (Зн.в.), яка (Н.в.) тут працює. (людину is in Зн. because of знаю, яка is in Н. because it's the subject); Practice: complete 12 sentences choosing correct form of який (right gender from antecedent, right case from clause function).
- **Інші сполучні слова в означальних**: Що as alternative to який (colloquial/neutral): Книга, що лежить на столі... = Книга, яка лежить на столі... Що is uninflected and works for all genders/numbers/cases: Хлопець, що прийшов... Дівчина, що прийшла... But що cannot be used with prepositions: NOT *місто, в що я живу.; Де/куди/коли/звідки for place and time: Місто, де я живу... (= в якому я живу) Країна, куди я їду... (= в яку я їду) День, коли ми зустрілися... (= в який ми зустрілися) These are often simpler and more natural than який з прийменником.; Чий for possession: Людина, чию книгу я читаю... (= якої книгу я читаю) Practice: choose between який, що, де, куди, коли in 8 sentences.
- **Пунктуація та позиція**: Rule: означальна підрядна ALWAYS requires commas: Місто, яке я відвідав, мене вразило. Unlike дієприкметниковий зворот, position doesn't matter — означальне речення is always in постпозиція to its noun.; Multiple означальні in one sentence: Студент, який вивчає мову, яку я викладаю, отримав стипендію. (nested — який refers to студент, яку refers to мову); Practice: punctuate 8 sentences with означальними реченнями.
- **Практика: означальні у мовленні**: High-frequency speech patterns: Це людина, яка... / Це місце, де... / Це час, коли... Describing people, places, and moments using means реченнями. Dialogue with natural usage in context.; Production: learners describe 5 people/places/things using означальні речення. Each must use який in a different відмінок.; Comparison exercise: rewrite 5 означальних речень as дієприкметникові звороти (where possible) and note which is more natural.
- **Підсумок та перехід до M69**: Summary: означальні = який?/яка?/яке?/які? Який declines by рід/число (from antecedent) and відмінок (from clause role). Alternatives: що (uninflected), де/куди/коли (for place/time). Завжди коми. Self-check: Я правильно вживаю який у відмінках ✓/✗.; Preview: M69 — Часові речення. When things happen relative to each other: коли, поки, доки, щойно.

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
