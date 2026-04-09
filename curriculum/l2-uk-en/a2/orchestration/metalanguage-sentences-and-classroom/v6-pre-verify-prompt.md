<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 63: Речення і клас (A2, A2.9 [Metalanguage Bridge & Foundation])

## Plan vocabulary to verify

- речення (sentence)
- підмет (subject)
- присудок (predicate)
- додаток (object)
- означення (attribute)
- обставина (adverbial modifier)
- корінь (root)
- префікс (prefix)
- суфікс (suffix)
- закінчення (ending)
- прочитайте (read — imperative)
- запишіть (write down — imperative)
- основа (stem)
- споріднені слова (cognate words)
- підкресліть (underline — imperative)
- вставте (insert — imperative)
- визначте (determine — imperative)

## Sections to research

- **Члени речення: хто що робить? (Sentence Members: Who Does What?)**: Re-labeling with Grade 3-4 textbook method: Ukrainian children learn sentence analysis (розбір речення) by asking questions. Підмет (subject) — хто? що? — underlined with one line. Присудок (predicate) — що робить? що зробив? — underlined with two lines.; Другорядні члени речення (secondary sentence members): Додаток (object) — кого? що? кому? чим? — answers case questions. Означення (attribute) — який? яка? яке? чий? — describes the noun. Обставина (adverbial modifier) — де? коли? як? куди? — describes the action.; Practice: analyze 5-6 simple sentences, identifying підмет, присудок, and other members. Grade 4 textbook format: draw arrows and underline.
- **Будова слова: корінь, префікс, суфікс (Word Anatomy: Root, Prefix, Suffix)**: Корінь (root) — the core meaning: ліс → лісок, лісовий, лісник, пролісок. All share the root ліс-. Споріднені слова (cognate words) share a root.; Префікс (prefix) — before the root, changes meaning: ходити → виходити, заходити, приходити, переходити. Each prefix adds a new direction or nuance.; Суфікс (suffix) — after the root, changes part of speech or adds meaning: ліс → лісок (diminutive), лісовий (adjective), лісник (person). Connect to diminutive suffixes from M52.
- **Мова класу: накази вчителя (Classroom Language: Teacher Instructions)**: Essential classroom imperatives the learner will encounter in B1+ Ukrainian-language instruction: Прочитайте (Read), Запишіть (Write down), Виберіть (Choose), Підкресліть (Underline), Вставте (Insert), Дайте відповідь (Give an answer), Знайдіть (Find), Визначте (Determine), Порівняйте (Compare), Доповніть (Complete/supplement).; These are formal imperative (ви-form). Connect to nakazovyy sposib from M56. Formation: stem + -іть/-йте.; Common exercise instructions: Вставте пропущені букви (Insert missing letters). Підкресліть підмет і присудок (Underline subject and predicate). Визначте відмінок іменника (Determine the case of the noun).
- **Усе разом: аналізуємо текст (Putting It All Together: Text Analysis)**: Integrated exercise: a short Ukrainian text (6-8 sentences). The learner identifies parts of speech (частини мови), sentence members (члени речення), and breaks selected words into morphemes (будова слова).; Reading: a Grade 4 textbook exercise page — the learner works through it as a Ukrainian student would, following instructions in Ukrainian.; Self-assessment: Can I understand grammar instructions in Ukrainian? Am I ready for B1 where more content will be in Ukrainian?

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
