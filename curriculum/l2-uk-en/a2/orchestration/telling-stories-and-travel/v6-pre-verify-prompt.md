<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 45: Розповіді та подорожі (A2, A2.6 [Aspect, Tenses, and Motion])

## Plan vocabulary to verify

- подорож (trip, journey)
- розповідати / розповісти (to tell/narrate — impf./pf.)
- трапитися (to happen)
- квиток (ticket)
- потяг (train)
- вокзал (station)
- зупинитися (to stay, to stop — pf.)
- доїхати (to reach by vehicle — pf.)
- сподобатися (to like — pf.)
- враження (impression)
- спочатку (at first)
- потім (then)
- нарешті (finally)
- тим часом (meanwhile)
- сувенір (souvenir)

## Sections to research

- **Сценарій 1: Що вчора трапилось? (Scenario 1: What Happened Yesterday?)**: Story-telling structure: setting the scene (imperfective) → events (perfective) → reactions (both aspects). Example: Був теплий вечір. Я сидів на балконі і читав книгу (background — impf.). Раптом подзвонив друг (event — pf.) і запросив мене на вечерю (event — pf.).; Time connectors for narratives: спочатку (at first), потім (then), після цього (after that), нарешті (finally), тим часом (meanwhile), раптом (suddenly), у цей момент (at that moment).; Practice: learner reads a short story with mixed aspects, identifies which verbs are background (impf.) and which are plot events (pf.).
- **Сценарій 2: Плануємо подорож (Scenario 2: Planning a Trip)**: Dialogue: two friends planning a trip to Lviv. Куди поїдемо? (pf. — specific trip) Як доберемося? Поїдемо потягом чи полетимо? Де зупинимося? (pf. — specific result) Що будемо робити? (impf. — general activities).; Travel vocabulary: подорож (trip), квиток (ticket), потяг (train), літак (airplane), автобус (bus), вокзал (station), аеропорт (airport), готель (hotel), зупинитися (to stay/stop).; Motion verbs in context: Ми поїдемо потягом до Львова (pf. — specific trip). Зазвичай ми їздимо туди влітку (impf. — habitual). Літак летить дві години (unidirectional — in progress).
- **Сценарій 3: Розкажи про поїздку! (Scenario 3: Tell Me About Your Trip!)**: Dialogue: one friend asks about another's recent trip. Де ти був? Куди їздив? Як доїхав? Що бачив? Що найбільше сподобалось? — All answered using past tense with correct aspect.; Sample narrative: Минулого тижня я їздив до Одеси (impf. — round trip). Ми поїхали потягом (pf. — departed). Доїхали за десять годин (pf. — completed). Там ми ходили по місту (impf. — walked around), відвідали музей (pf. — specific event), купили сувеніри (pf.) і з'їли найсмачніший борщ (pf.).; Expressing impressions: Мені дуже сподобалось (I really liked it). Було чудово / цікаво / весело (It was wonderful / interesting / fun). Я хочу поїхати ще раз (I want to go again).
- **Мовленнєве завдання: Моя подорож (Speaking Task: My Journey)**: Guided writing task: write 8-10 sentences about a real or imagined trip. Include: where you went (motion verb + destination), how you traveled (vehicle — Instr.), what you did (perfective events), what was happening around you (imperfective background).; Checklist: Did you use at least 2 motion verbs? Did you alternate aspects? Did you use time connectors? Did you describe impressions?; Model answer for comparison, annotated with aspect labels.

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
