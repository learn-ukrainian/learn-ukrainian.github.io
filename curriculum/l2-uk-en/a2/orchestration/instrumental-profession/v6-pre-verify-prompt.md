<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 26: Я буду вчителькою (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- професія (profession)
- фах (profession, specialty)
- працювати (to work)
- стати (to become)
- захоплюватися (to be passionate about)
- цікавитися (to be interested in)
- пишатися (to be proud of)
- займатися (to be engaged in, to do (a sport/activity))
- лікар (doctor)
- вчитель (teacher (male))
- вчителька (teacher (female))
- інженер (engineer)
- програміст (programmer)
- кухар (cook, chef)
- перукар (hairdresser)
- мріяти (to dream)
- володіти (to master, to possess)

## Sections to research

- **Бути ким? Професія в орудному відмінку (To Be Whom? Profession in the Instrumental)**: After бути (past/future), стати, працювати, the profession noun goes into Instrumental: Вона була вчителькою. Він стане лікарем. Я працюю інженером.; Present tense exception: Я вчитель / Вона вчителька (Nominative, no є). But past and future use Instrumental: Він був лікарем. Вона буде програмісткою.; Feminine profession nouns in Instrumental: вчителька → вчителькою, лікарка → лікаркою, програмістка → програмісткою, журналістка → журналісткою.
- **Дієслова з орудним відмінком (Verbs That Take the Instrumental)**: Verbs of interest and passion: захоплюватися (to be passionate about) — захоплюватися музикою, спортом, мистецтвом; цікавитися (to be interested in) — цікавитися історією, наукою.; Verbs of pride and admiration: пишатися (to be proud of) — Я пишаюся Україною, сином; милуватися (to admire) — милуватися природою.; Verbs of activity: займатися (to be engaged in) — займатися спортом, йогою, бізнесом; володіти (to master/possess) — володіти мовою.
- **Хто ти за фахом? (What Is Your Profession?)**: Key question patterns: Ким ти працюєш? Ким ти хочеш стати? Хто ти за фахом? Чим ти захоплюєшся?; Dialogue: Two people at a party introducing themselves — discussing their jobs, what they studied, and what they are passionate about.; Common professions for practice: вчитель/вчителька, лікар/лікарка, інженер/ інженерка, програміст/програмістка, кухар/кухарка, перукар/перукарка, журналіст/журналістка, музикант/музикантка.
- **Практика: Ким бути? (Practice: Who to Be?)**: Transformation drill: Він лікар. → Він працює лікарем. → Він буде лікарем.; Sentence building with verb + Instrumental: Мій брат займається програмуванням. Моя сестра цікавиться медициною. Я пишаюся своєю родиною.; Mini-dialogue: A child telling a parent about future career dreams (Я хочу стати ветеринаром! — Чому? — Бо я захоплююся тваринами).

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
