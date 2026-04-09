<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 56: Своє та себе (A2, A2.8 [Refinement and Graduation])

## Plan vocabulary to verify

- свій (one's own)
- себе (oneself, accusative/genitive)
- собі (oneself, dative)
- собою (oneself, instrumental)
- почувати себе (to feel)
- вести себе (to behave)
- горджуся (I am proud)
- уявити (to imagine)
- дзеркало (mirror)
- парасолька (umbrella)
- власний (own, one's own)
- самостійно (independently)
- звичка (habit)
- щоденний (daily)

## Sections to research

- **Свій: чий саме? (Свій: Whose Exactly?)**: The key rule: свій replaces мій/твій/його when the possessor is the subject. Я читаю свою книгу (= my own book). Він читає свою книгу (= his own book). Without свій: Він читає його книгу (= someone else's book).; Why this matters: English uses "his" for both cases. Ukrainian distinguishes them. Він любить свою дружину (his own wife) vs. Він любить його дружину (another man's wife).; When NOT to use свій: in 1st/2nd person, мій/твій are also acceptable (Я читаю мою/свою книгу — both correct). In 3rd person, свій is essential for clarity.
- **Свій у відмінках (Свій in All Cases)**: Declension table: свій follows the pattern of мій/твій. Masculine: свій, свого, своєму, свій/свого, своїм, своєму/своїм. Feminine: своя, своєї, своїй, свою, своєю, своїй. Neuter: своє, свого, своєму, своє, своїм, своєму/своїм. Plural: свої, своїх, своїм, свої/своїх, своїми, своїх.; Practice with cases: Я горджуся своїм містом (Instr.). Він розповів про свою родину (Acc.). Вона допомагає своїй сестрі (Dat.).; Common collocations: свій час, своя думка, своє місце, свої люди.
- **Себе: зворотний займенник (Себе: The Reflexive Pronoun)**: Себе has no Nominative form — it cannot be the subject. It refers back to the subject: Він бачить себе у дзеркалі (He sees himself in the mirror).; Declension: Родовий/Знахідний: себе, Давальний/Місцевий: собі, Орудний: собою.; Common expressions: почувати себе (to feel), вести себе (to behave), уявити собі (to imagine), взяти собі (to take for oneself), сам/сама по собі (by oneself).
- **Свій та себе у мовленні (Свій and Себе in Speech)**: Dialogue: friends discuss their habits and routines using свій and себе naturally (Я завжди беру з собою парасольку. А ти? Я почуваю себе добре у своєму місті).; Reading practice: a short text about a person describing their daily routine, using свій and себе throughout.; Common mistakes: *Він любить його дружину (ambiguous without свій), *Я почуваю себе (missing adverb — як?).

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
