<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 48: What Happened? (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- учора (yesterday)
- робити (to do)
- читати (to read)
- працювати (to work)
- гуляти (to walk)
- готувати (to cook)
- дивитися (to watch)
- говорити (to speak)
- минулий (past, adj)
- вихідні (weekend, pl)
- субота (Saturday, f)
- неділя (Sunday, f)
- разом (together)
- фільм (film, m)
- провести (to spend time)

## Sections to research

- **Dialogues**: Dialogue 1 — What did you do yesterday? — Що ти робив учора? — Я читав книжку. А ти? — Я готувала вечерю. — А що робив Тарас? — Він гуляв у парку. — А Олена? — Вона працювала. Note gender: робив (he), робила (she). Same verb, different ending.; Dialogue 2 — A weekend: — Як ти провів вихідні? — Добре! У суботу я гуляв у місті. — А в неділю? — У неділю я дивився фільм. А ти? — Я ходила в кафе з подругою. Ми їли торт і пили каву. — Як смачно! Past tense in natural narration.
- **Минулий час (Past Tense)**: Grade 3-4 textbooks: минулий час (past tense). How to form it: take the infinitive, remove -ти, add: він → -в (читати → читав) вона → -ла (читати → читала) воно → -ло (читати → читало) вони → -ли (читати → читали) KEY INSIGHT: past tense shows GENDER, not person! Я читав = I (male) was reading. Я читала = I (female) was reading. Same person (я), different gender ending.; This is different from present tense (which marks person): Present: я читаю, ти читаєш, він читає (person endings). Past: я/ти/він читав, я/ти/вона читала (gender endings). Він працював. Вона працювала. Воно працювало. Вони працювали. No aspect distinction at A1 — just learn the forms.
- **Практика (Practice)**: Core verbs in past tense (all known from A1.3): читати → читав / читала / читало / читали працювати → працював / працювала / працювало / працювали гуляти → гуляв / гуляла / гуляло / гуляли готувати → готував / готувала / готувало / готували дивитися → дивився / дивилася / дивилося / дивилися говорити → говорив / говорила / говорило / говорили; Building sentences about the past: Учора я читав цікаву книжку. (Yesterday I read an interesting book.) Вона працювала в офісі. (She worked in the office.) Ми гуляли в парку. (We walked in the park.) Вони готували вечерю разом. (They cooked dinner together.) Time words for past: учора (yesterday), минулого тижня (last week).
- **Summary**: Past tense formation: Infinitive stem + -в (він), -ла (вона), -ло (воно), -ли (вони). Gender matters: Я читав (male speaker). Я читала (female speaker). Вони завжди -ли (plural = no gender distinction). Question: Що ти робив/робила? (What did you do?) Answer: Я читав/читала книжку. Self-check: Tell your partner what you did yesterday using 3 different verbs.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
