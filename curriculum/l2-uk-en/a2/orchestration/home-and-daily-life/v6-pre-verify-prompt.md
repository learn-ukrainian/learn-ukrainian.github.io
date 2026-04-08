<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 38: Мій дім, мій день (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- помешкання (dwelling, apartment)
- кімната (room)
- кухня (kitchen)
- спальня (bedroom)
- вітальня (living room)
- меблі (furniture)
- розпорядок дня (daily routine)
- вставати (to get up)
- снідати (to have breakfast)
- лягати спати (to go to bed)
- балкон (balcony)
- коридор (hallway)
- килим (carpet, rug)
- пригощатися (to help oneself (to food))
- господар (host)

## Sections to research

- **Сценарій 1: Моє помешкання (Scenario 1: My Home)**: Dialogue: showing a friend around a new apartment. Host describes rooms and furniture. Cases emerge naturally: Ось вітальня (Nom.). У вітальні (Loc.) стоїть великий диван. На стіні (Loc.) висить картина. Біля вікна (Gen.) є крісло.; Room vocabulary: кухня, спальня, вітальня, ванна кімната, коридор, балкон, кабінет.; Furniture vocabulary: диван, крісло, стіл, стілець, шафа, ліжко, полиця, дзеркало, килим.
- **Сценарій 2: Мій звичайний день (Scenario 2: My Typical Day)**: Monologue: describing a typical weekday from morning to evening. Вранці я встаю о сьомій (Loc. for time). Іду у ванну (Acc. direction). Снідаю з родиною (Instr.). Їду на роботу (Acc.) автобусом (Instr.).; Daily actions: вставати, вмиватися, снідати, обідати, вечеряти, працювати, відпочивати, лягати спати.; Time expressions: вранці, вдень, увечері, вночі; о котрій годині; після обіду (Gen.), перед сном (Instr.), під час роботи (Gen.).
- **Сценарій 3: В гостях (Scenario 3: Visiting Someone)**: Dialogue: visiting a Ukrainian friend for dinner. Arrival, tour of the home, sitting down to eat, conversation about daily routines.; Hospitality expressions: Будь ласка, заходьте! Сідайте за стіл (Acc.). Пригощайтеся! Хочете чаю (Gen.) чи кави (Gen.)?; Comparing routines: А о котрій ви встаєте? Хто у вас готує вечерю (Acc.)? Ви снідаєте вдома (Loc. implied) чи на роботі (Loc.)?
- **Мовленнєве завдання: Опишіть свій дім (Speaking Task: Describe Your Home)**: Guided production task: learner writes 8-10 sentences describing their home and daily routine, using a checklist to ensure they include at least 5 different cases.; Checklist: use Nom. (what is there), Gen. (what is not there / how many), Dat. (for whom), Acc. (where you go / what you do), Instr. (with whom / by what means), Loc. (where things are).; Model answer provided for comparison.

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
