<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 9: Робота і кар'єра (B1, B1.0 [Baselines & Aspect Mastery])

## Plan vocabulary to verify

- робота (work/job — general term for employment)
- професія (profession — a trained occupation)
- фах (specialty/field — area of expertise)
- посада (position/role — specific job title in a company)
- вакансія (vacancy — an open job position)
- співбесіда (job interview — formal meeting with employer)
- працевлаштування (employment — the process of getting hired)
- резюме (CV/resume — невідмінюване, written job application)
- обов'язок (duty/responsibility — pl. обов'язки)
- досвід (experience — professional background)
- підвищення (promotion/raise — career advancement)
- зарплата (salary — розм. form of заробітна плата)
- колега (colleague — спільного роду: мій/моя колега)
- керівник (manager/supervisor — head of a team or department)
- звільнення (dismissal/resignation — leaving a job)
- роботодавець (employer — the hiring party)
- працівник (employee/worker)
- стажування (internship/training period)
- кар'єра (career — long-term professional path)
- підприємство (enterprise/company — formal)
- відповідати за (to be responsible for + acc.)
- займатися (to engage in + instr.)

## Sections to research

- **Професія і фах: базова лексика**: Core vocabulary field: професія (profession as a concept), фах (specialty, field of expertise), спеціальність (specific qualification), посада (position/role in a company). Semantic distinctions grounded in Заболотний Grade 5 p.69 vocabulary development model: organize by semantic field, distinguish near-synonyms.; Workplace vocabulary: підприємство (enterprise), компанія (company), офіс (office), відділ (department), колега (colleague, common gender), керівник (manager/supervisor), працівник (employee), роботодавець (employer). Note: колега is спільного роду — мій колега, моя колега.; Employment process: вакансія (vacancy), резюме (CV, невідмінюване), співбесіда (interview), працевлаштування (employment/getting hired), стажування (internship/ training period), випробувальний термін (probation period).
- **Вид дієслова у розповіді про роботу**: Review of aspect choice (Литвінова Grade 7 p.30): доконаний вид for completed, result-oriented actions — влаштувалася на роботу, отримала підвищення, звільнилася. Недоконаний вид for ongoing, habitual, or background actions — працювала в компанії, виконувала обов'язки, вела проєкти.; Aspect in career narratives — the pattern: Недоконаний as background/duration: Я працювала (impf) в банку п'ять років. Доконаний as chain of events: Закінчила (pf) університет, подала (pf) резюме, пройшла (pf) співбесіду і влаштувалася (pf) на роботу. Combined: Коли я працювала (impf, тло) у Львові, мені запропонували (pf, подія) нову посаду.; Common aspect errors in work context: *Я працювала три роки і звільнялася (impf — wrong, result expected) → Я працювала три роки і звільнилася (pf). *Я влаштувалася на роботу і виконувала обов'язки (impf — correct as habitual). The key: is the speaker emphasizing RESULT or PROCESS?
- **На співбесіді: ситуативне мовлення**: Job interview structure in Ukrainian (grounded in Литвінова Grade 7 p.205 situational speech model): 1. Привітання і представлення: Доброго дня, мене звати... Я подавала резюме на посаду... 2. Розповідь про досвід: Я закінчила... Працювала в... Моїми обов'язками були... 3. Запитання: Які умови праці? Який графік роботи? 4. Завершення: Дякую за можливість.; Register: formal workplace Ukrainian. Key patterns: Дозвольте розповісти про мій досвід. Моєю спеціальністю є... На попередній посаді я відповідала за... Маю досвід роботи у сфері... Contrast with informal: Я працювала в... → formal: Мій попередній досвід пов'язаний із...; Describing обов'язки (duties) — instrumental case review: відповідати за + accusative (відповідала за проєкт), займатися + instrumental (займалася маркетингом), працювати з + instrumental (працювала з клієнтами), керувати + instrumental (керувала командою).
- **Підсумок: робота і вид дієслова**: Vocabulary summary organized by category: люди на роботі (колега, керівник, працівник, роботодавець), процес працевлаштування (вакансія, резюме, співбесіда, стажування), кар'єра (посада, підвищення, звільнення, досвід, обов'язок).; Aspect summary table applied to work verbs: працювати (impf) — no pf pair (process verb). влаштуватися (pf) / влаштовуватися (impf). звільнитися (pf) / звільнятися (impf). отримати (pf) / отримувати (impf). подати (pf) / подавати (impf). Complete table with example sentences for each pair.; Самоперевірка: 1. Назвіть 5 професій і 5 слів, пов'язаних із працевлаштуванням. 2. Розкажіть про свій (реальний або вигаданий) досвід роботи, чергуючи доконаний і недоконаний вид. 3. Яка різниця між словами професія, фах, спеціальність, посада? 4. Як розповісти на співбесіді про свої обов'язки? Складіть 3 речення з дієсловами відповідати за, займатися, керувати.

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
