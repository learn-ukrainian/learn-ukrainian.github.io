<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 62: Дія і час (A2, A2.9 [Metalanguage Bridge & Foundation])

## Plan vocabulary to verify

- дієслово (verb)
- час (tense, time)
- вид (aspect)
- доконаний (perfective)
- недоконаний (imperfective)
- спосіб (mood, manner)
- дієвідміна (conjugation class)
- особа (person, grammatical)
- прислівник (adverb)
- словник (dictionary)
- дійсний спосіб (indicative mood)
- наказовий спосіб (imperative mood)
- умовний спосіб (conditional mood — label only, production is B1)
- скорочення (abbreviation)

## Sections to research

- **Дієслово: категорії та терміни (The Verb: Categories and Terms)**: Re-labeling what they know: the learner already uses tenses and aspects — now they learn the Ukrainian terms. Method: Grade 4-5 textbook excerpts.; Час (tense): минулий час (past), теперішній час (present), майбутній час (future). Examples with verbs they know: читав (мин.), читаю (теп.), читатиму/буду читати (майб.).; Вид (aspect): доконаний вид (perfective) — що зробити? прочитати, написати. Недоконаний вид (imperfective) — що робити? читати, писати. Connect to what they learned in A2.1 aspect modules.
- **Дієвідміна та особа (Conjugation and Person)**: Дієвідміна (conjugation class): I дієвідміна (-еш, -е pattern: пишеш, пише) vs. II дієвідміна (-иш, -ить pattern: говориш, говорить). How to determine: look at the 3rd person singular.; Особа (person): перша особа (1st — я, ми), друга особа (2nd — ти, ви), третя особа (3rd — він/вона/воно, вони).; Число (number) in verbs: однина (singular — читаю, читаєш, читає), множина (plural — читаємо, читаєте, читають).
- **Словникова грамотність: читаємо словник (Dictionary Literacy: Reading a Dictionary)**: How to read a goroh.pp.ua entry: headword, stress mark, part of speech abbreviation, grammatical information, definitions.; Key abbreviations: ім. (іменник), прикм. (прикметник), дієсл. (дієслово), займ. (займенник), присл. (прислівник), ч.р. (чоловічий рід), ж.р. (жіночий рід), с.р. (середній рід), док. (доконаний), недок. (недоконаний), одн. (однина), мн. (множина).; Practice: read 5-6 real dictionary entries and extract grammatical information. What part of speech? What gender? What aspect?
- **Прислівник: види та приклади (The Adverb: Types and Examples)**: Adverb classification using Ukrainian terms: прислівник місця (adverb of place) — тут, там, далеко, близько; прислівник часу (adverb of time) — сьогодні, завтра, вчора, завжди; прислівник способу дії (adverb of manner) — швидко, повільно, добре.; Practice: sort known adverbs into categories using Ukrainian terms.; Connection to прикметник: many adverbs derive from adjectives (швидкий → швидко, гарний → гарно). The -о ending pattern.

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
