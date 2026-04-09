<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 46: Контрольна точка: Вид, час і рух (A2, A2.6 [Aspect, Tenses, and Motion])

## Plan vocabulary to verify

- контрольна точка (checkpoint)
- перевірка (review, check)
- завдання (task, exercise)
- помилка (error, mistake)
- виправити (to correct)
- вид дієслова (verb aspect)
- дієслова руху (motion verbs)
- наказовий спосіб (imperative mood)
- впевнено (confidently)
- самоперевірка (self-check)
- обрати (to choose — pf.)

## Sections to research

- **Частина 1: Вид дієслова — минулий і майбутній час (Part 1: Aspect in Past and Future)**: Exercise 1: Aspect identification — read 8 sentences in past tense, identify the aspect of each underlined verb and explain the choice (process, result, habit, single event, background, sequence).; Exercise 2: Aspect choice — fill in the blank with the correct aspect form (imperfective or perfective) in past and future tense sentences. Mixed contexts: Вона довго ___ (готувати/приготувати) обід. Він вже ___ (писати/написати) листа.; Exercise 3: Future tense formation — given 8 infinitives (mixed aspects), form the correct future: perfective → synthetic (напишу), imperfective → analytical (буду писати).
- **Частина 2: Дієслова руху та наказовий спосіб (Part 2: Motion Verbs and Imperatives)**: Exercise 4: Motion verb choice — complete 6 sentences by choosing between unidirectional and multidirectional motion verbs. Зараз я ___ (іти/ходити) додому. Щодня він ___ (їхати/їздити) на роботу.; Exercise 5: Motion + prepositions — match motion verbs with destinations using the correct preposition and case: ___ школи (з + Gen. — from), ___ Львова (до + Gen. — to), ___ роботу (на + Acc. — to).; Exercise 6: Imperative formation — form imperatives for all persons from given infinitives. 2nd person: читай/читайте. 3rd person: хай читає. 1st plural: читаймо. Include aspect choice.
- **Частина 3: Комплексні завдання (Part 3: Integrated Tasks)**: Exercise 7: Error correction — 8 sentences with verb errors (wrong aspect, wrong motion verb, wrong imperative form, wrong future type). Learner identifies and corrects each. E.g., *Він щодня зробив вправи → робив; *Ми їдемо туди кожного літа → їздимо.; Exercise 8: Story completion — a short narrative with 8 blanks. Learner fills in correct forms using all skills from M35-40: aspect in past, future tense, motion verbs, imperatives.; Exercise 9: Guided production — write 8-10 sentences narrating a weekend trip. Must include: past tense aspect (both), motion verbs (at least 2 pairs), one imperative (suggestion to a friend), one wish (Vocative + imperative + Instrumental).

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
