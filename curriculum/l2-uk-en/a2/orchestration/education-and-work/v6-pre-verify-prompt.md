<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 52: Навчання і робота (A2, A2.7 [Complex Sentences and Conditionals])

## Plan vocabulary to verify

- освіта (education)
- навчання (studying, learning)
- університет (university)
- спеціальність (specialty, major)
- професія (profession)
- працювати (to work)
- робота (work, job)
- досвід (experience)
- іспит (exam)
- диплом (diploma, degree)
- факультет (faculty, department)
- зарплата (salary)
- співбесіда (job interview)
- керівник (manager, supervisor)
- магістратура (master's program)

## Sections to research

- **Про освіту: школа та університет (About Education: School and University)**: Talking about your educational path: Я закінчив школу у 2015 році. Потім я вступив до університету, тому що хотів стати інженером.; Describing your school/university with relative clauses: Університет, де я навчався, знаходиться у Львові. Предмет, який мені найбільше подобався, — це історія.; Purpose of education: Я вчуся, щоб отримати диплом. Вона поїхала за кордон, щоб вивчити нову спеціальність.
- **Про роботу: ким ви працюєте? (About Work: What Do You Do?)**: Describing your job and workplace: Я працюю програмістом у компанії, яка розробляє додатки. Моя колега, яка сидить поруч, допомагає мені з проєктами.; Explaining why you chose your profession: Я став вчителем, тому що люблю працювати з дітьми. Хоча робота важка, вона дає задоволення.; Work conditions with якщо: Якщо я добре працюю, то отримую премію. Якщо є вільний час, я ходжу на курси.
- **Плани на майбутнє (Plans for the Future)**: Discussing career and education goals: Якщо я складу іспит, то вступлю до магістратури. Я хочу змінити роботу, щоб мати більше вільного часу.; Giving and receiving career advice using conditionals: Якщо хочеш знайти кращу роботу, вивчай нову мову. Якщо тобі не подобається робота, шукай іншу.; Concessions about work/study: Хоча я ще студент, я вже працюю на частковий робочий день. Хоча зарплата невелика, робота цікава.

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
