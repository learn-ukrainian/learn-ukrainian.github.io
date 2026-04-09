<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 55: Освіта і навчання (B1, B1.5 [Case Nuances & Prepositions])

## Plan vocabulary to verify

- освіта (education)
- університет (university)
- факультет (faculty, department)
- спеціальність (major, specialization)
- лекція (lecture)
- семінар (seminar)
- іспит (exam)
- залік (pass/fail assessment)
- стипендія (scholarship, stipend)
- курсова робота (term paper)
- дипломна робота (thesis)
- дослідження (research)
- бакалавр (bachelor's degree)
- магістр (master's degree)
- кафедра (department/chair)
- гуртожиток (dormitory)
- розклад занять (class schedule)
- залікова книжка (grade book)
- конференція (conference)
- лабораторна робота (lab work)
- підручник (textbook)
- конспект (lecture notes)
- монографія (monograph)
- дисертація (dissertation)
- науковий керівник (academic advisor)

## Sections to research

- **Система освіти в Україні**: Overview of Ukrainian education levels: початкова школа (1-4 класи), середня школа (5-9 класи), старша школа (10-11/12 класи), університет/інститут. Ступені вищої освіти: бакалавр, магістр, доктор філософії. Типи закладів: університет, інститут, академія, коледж.; Academic vocabulary cluster: факультет (faculty/department), кафедра (department/chair), спеціальність (major/specialization), курс (year of study), семестр (semester), залікова книжка (grade book), залік (pass/fail exam), іспит (exam), диплом (diploma/thesis). Dialogue 1: two students discussing their specializations.; Cultural context: the Ukrainian academic system compared to Western models. ЗНО/НМТ (standardized testing for university admission). The concept of державне замовлення (state-funded places) vs контрактна форма (self-funded).
- **Навчальні дисципліни та спеціальності**: Subject vocabulary using дієприкметники and дієприслівники: Вивчаючи фізику, студенти проводять досліди. Написана професором монографія отримала премію. Захищена минулого року дисертація стосувалась... Natural integration of Phase 7 grammar in academic context.; Discipline names: математика, фізика, хімія, біологія, філологія, історія, юриспруденція, медицина, інженерія, інформатика, економіка, філософія, психологія, мистецтво. Formation patterns: many are international words adapted to Ukrainian.; Dialogue 2: a student describing their studies to a friend. Uses gerunds for simultaneous/sequential actions: Готуючись до іспиту, я прочитав три підручники. Закінчивши бакалаврат, планую вступити до магістратури.
- **Академічне середовище**: University life vocabulary: лекція (lecture), семінар (seminar), практика (practice/internship), лабораторна робота (lab work), курсова робота (term paper), дипломна робота (thesis), конференція (conference), стипендія (scholarship/stipend), гуртожиток (dormitory), бібліотека (library), читальний зал (reading room).; Passive participles in academic descriptions: Опублікована стаття, рекомендована література, запланована конференція, затверджений розклад, проведене дослідження, отримані результати. These are natural and high-frequency in academic Ukrainian.; Dialogue 3: a student and professor discussing a research project. Uses participle phrases: Дослідження, проведене нашою групою, показало цікаві результати. Прочитавши вашу роботу, я маю кілька зауважень.
- **Навчальний процес: дієприкметники і дієприслівники**: Describing academic activities with Phase 7 grammar: Студент, який пише курсову → студент, що пише курсову (preferred over працюючий студент — Russian calque). Прочитавши статтю, зробіть конспект. (perfective gerund — sequence) Готуючись до семінару, перегляньте матеріали. (imperfective — process); Academic register: gerund phrases are MORE acceptable in academic Ukrainian than in speech. They create concise, formal prose: Використовуючи новий метод, дослідники отримали точніші дані. Проаналізувавши результати, автор дійшов висновку.; Practice: rewrite 6 informal sentences about studies into formal academic register using participle phrases and gerund constructions.
- **Порівняння систем освіти**: Reading passage: a comparison of Ukrainian and international education systems. Uses complex sentences with subordinate clauses (preview of Phase 8) and Phase 7 grammar naturally. Comprehension questions test LANGUAGE, not facts: — Знайдіть усі дієприкметникові звороти в тексті. — Яку роль виконують дієприслівники в другому абзаці?; Discussion prompts: learners describe their own education experience using Phase 7 grammar structures.
- **Підсумок фази 7 та перехід до M65**: Summary of Phase 7 grammar applied in academic context: M57-58: дієприкметники (активні/пасивні) — academic descriptions. M59: дієприкметниковий зворот — concise formal attributes. M60: короткі прикметники — потрібен (essential in academic register). M61-62: дієприслівники (недок./док.) — temporal relations in process. M63: дієприслівниковий зворот — formal prose constructions.; Self-check: Я можу говорити про навчання українською ✓/✗, Я вживаю дієприкметники в академічному стилі ✓/✗. Preview: M65 — Контрольна робота 7, reviewing Phase 7.

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
