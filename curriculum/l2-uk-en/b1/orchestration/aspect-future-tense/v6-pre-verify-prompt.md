<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 5: Вид у майбутньому часі (B1, B1.0 [Baselines & Aspect Mastery])

## Plan vocabulary to verify

- складений майбутній час
- синтетичний
- простий
- інфінітив
- парадигма
- особове закінчення
- обіцяти
- пообіцяти
- старатися
- постаратися
- планувати
- запланувати
- забронювати
- насолоджуватися
- закінчити
- закінчувати
- розмовний стиль
- писемний стиль
- зобов'язання
- передбачення

## Sections to research

- **Тест: яке майбутнє ви оберете?**: Diagnostic: learners see 10 future-tense situations and must choose between буду + inf, -тиму form, or simple perfective. No rules — just intuition. Examples: Завтра я ... цю книжку (читатиму / буду читати / прочитаю). Я обіцяю, що ... до вечора (писатиму / буду писати / напишу).; Self-assessment: learners note which form felt most natural in each context. Discussion: did you feel a difference between буду читати and читатиму? Between either of those and прочитаю? That feeling is real — this module makes it explicit.; Key question framed: Ukrainian has THREE future constructions. English has 'will' + variations. Why three? Because вид splits the future into process-future and result-future — and process-future has two forms.
- **Три конструкції: форма і значення**: Construction 1 — складений майбутній час (Литвінова Grade 7 p.44): буду + інфінітив недоконаного виду. Парадигма: буду писати, будеш писати, буде писати, будемо писати, будете писати, будуть писати. Значення: planned future process, ongoing future action, neutral statement about future. Feels slightly more conversational, common in щоденне мовлення.; Construction 2 — синтетичний недоконаний (Заболотний Grade 7 p.73): інфінітив + -му/-меш/-ме/-мемо/-мете/-муть (fused with буду). Парадигма: писатиму, писатимеш, писатиме, писатимемо, писатимете, писатимуть. Same meaning as складений — but feels slightly more literary, formal, or emphatic. Both are fully correct; style preference varies by region and register.; Construction 3 — простий доконаний майбутній (Литвінова Grade 7 p.46): Дієслова доконаного виду утворюють форми майбутнього часу як теперішній час — ті самі особові закінчення. напишу, напишеш, напише, напишемо, напишете, напишуть. Значення: completed future action with result. Я напишу лист = the letter WILL BE DONE.
- **Коли який? Вибір конструкції**: Decision framework: What do you want to say about the future? Focus on PROCESS → недоконаний (буду + inf or -тиму): Завтра я буду працювати. Увечері читатиму книжку. Focus on RESULT → доконаний (простий): Завтра я закінчу проєкт. Увечері прочитаю цю статтю.; Promises and commitments: usually доконаний (result matters). Я напишу тобі. Ми приїдемо вчасно. Вона зробить усе, що обіцяла. But process-promises exist: Я буду старатися. Ми будемо чекати на тебе. — the commitment is to the ongoing effort, not to a specific result.; Plans and schedules: often mix both aspects. Завтра я встану о сьомій (pf — single completed action), потім снідатиму (impf — ongoing), о дев'ятій поїду на роботу (pf — departure), там працюватиму до шостої (impf — duration), а ввечері приготую вечерю (pf — result: dinner ready).
- **Підсумок: три майбутні як система**: Synthesis: the three-construction system is not complexity — it's precision. English 'I will write' is ambiguous between process and result. Ukrainian писатиму (process) vs напишу (result) forces the speaker to commit to a meaning. This is a feature, not a burden.; складений vs синтетичний — a style choice, not a meaning choice. Both mean the same thing (imperfective future). Regional and register variation: складений more common in розмовний стиль, синтетичний in писемний. Both are fully standard (Правопис 2019). Learners can prefer whichever feels natural.; Common errors and corrections: *Я буду написати цей лист (impossible — pf + compound). *Завтра я прочитаю книжку цілий день (duration marker conflicts with pf — use читатиму). *Вона завтра зробить уроки і робитиме (redundant — pick one aspect per event).

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
