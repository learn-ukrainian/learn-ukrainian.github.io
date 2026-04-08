<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 32: Багато людей, багато речей (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- множина (plural)
- називний відмінок (nominative case)
- знахідний відмінок (accusative case)
- живий (animate)
- неживий (inanimate)
- закінчення (ending (grammar))
- люди (people)
- діти (children)
- речі (things)
- очі (eyes)
- відміна (declension class)
- чергування (alternation)
- предмет (object, item)
- група (group)

## Sections to research

- **Множина називного відмінка (Nominative Plural)**: I відміна (feminine/masculine -а/-я): сестра → сестри, земля → землі, суддя → судді. Hard stems: -и; soft stems: -і.; II відміна (masculine consonant, neuter -о/-е/-я): стіл → столи, місто → міста, поле → поля, море → моря. Consonant alternations: друг → друзі, рік → роки.; III відміна (feminine consonant): ніч → ночі, сіль → солі, мати → матері.
- **Знахідний відмінок множини: Живе чи неживе? (Accusative Plural: Animate vs. Inanimate)**: The key rule: inanimate Acc.Pl. = Nom.Pl. (Я бачу столи, книги, міста). Animate Acc.Pl. = Gen.Pl. (Я бачу братів, сестер, дітей).; How this differs from singular: masculine singular already has this split (бачу стіл vs. бачу брата), but in plural ALL genders follow it.; Practice with mixed animate/inanimate: Я бачу студентів і підручники. Ми зустріли друзів і знайшли ключі.
- **Називний чи знахідний? Визначаємо за контекстом (Nominative or Accusative? Reading the Context)**: Subject test: Who/what does the action? = Nominative. Студенти читають (Nom). Я бачу студентів (Acc).; Inanimate nouns look identical in Nom/Acc plural — only syntax tells them apart: Книги лежать на столі (Nom) vs. Я купив книги (Acc).; Practice: short paragraphs where learner identifies Nom vs. Acc plural by role in sentence. Dialogues about shopping, meeting friends, describing groups.

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
