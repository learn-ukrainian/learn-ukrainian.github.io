<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 14: Багато книг, мало студентів (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- множина (plural)
- нульове закінчення (zero ending)
- кілька (a few, several)
- багато (a lot, many)
- мало (a little, few)
- скільки (how many)
- людина (person) / люди (people)
- стаття (article)
- завдання (task, assignment)
- питання (question)
- чоловічий рід (masculine gender)
- жіночий рід (feminine gender)
- середній рід (neuter gender)
- виняток (exception)
- вставний голосний (inserted vowel)

## Sections to research

- **Чоловічий рід: -ів та нульове закінчення (Masculine: -ів and Zero Ending)**: Main pattern -ів: столів, братів, студентів, будинків, підручників. Most hard-stem masculine nouns take -ів.; Soft-stem -ів: учитель→учителів (fleeting е drops), олівець→олівців. True -їв appears only after vowel/apostrophe stems: подвір'я→подвір'їв, відкриття→відкриттів. Most soft masculine nouns take -ів, not -їв.; Zero ending (rare in masculine): nouns losing -ин/-їн suffix take zero ending: громадянин→громадян, селянин→селян, болгарин→болгар. The word чоловік has parallel forms (чоловік/чоловіків). Most masculine nouns take -ів.
- **Жіночий рід: нульове закінчення (Feminine: Zero Ending Patterns)**: Hard-stem zero ending: книга→книг, жінка→жінок (vowel insertion о), сестра→сестер (vowel insertion е). The main feminine pattern removes -а and uses zero ending.; Vowel insertion rules: consonant clusters at the end of the stem often require о or е insertion. студентка→студенток, зупинка→зупинок, сумка→сумок.; Soft-stem zero + ь: пісня→пісень, вишня→вишень (regular I declension soft-stem pattern). I declension -ей exceptions (small closed group): стаття→статей, сім'я→сімей, миша→мишей. The -ія group: станція→станцій, лекція→лекцій (zero ending, й drops).
- **Середній рід та узагальнення (Neuter and Summary)**: Neuter zero ending: вікно→вікон, слово→слів, місто→міст. The -о drops and zero ending applies. Vowel insertion where needed: вікон (о inserted).; Soft neuter: море→морів, поле→полів (-ів ending, not zero). But: завдання→завдань (-ь ending), питання→питань.; -тя neuter: ім'я→імен, теля→телят. These have special stem changes in the plural.

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
