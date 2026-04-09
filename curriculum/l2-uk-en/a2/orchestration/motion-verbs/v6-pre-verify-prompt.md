<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 43: Іду, їду, лечу (A2, A2.6 [Aspect, Tenses, and Motion])

## Plan vocabulary to verify

- іти / ходити (to go on foot — unidirectional/multidirectional)
- їхати / їздити (to go by vehicle — unidirectional/multidirectional)
- летіти / літати (to fly — unidirectional/multidirectional)
- піти (to leave on foot — pf.)
- поїхати (to leave by vehicle — pf.)
- казати / кажу (to say — stem change model)
- пити / п'ю (to drink — irregular model)
- боротися / борюся (to fight/struggle — reflexive model)
- напрямок (direction)
- рух (movement, motion)
- чергування (alternation)
- односпрямований (unidirectional)
- різноспрямований (multidirectional)
- звідки (from where)

## Sections to research

- **Три пари дієслів руху (Three Pairs of Motion Verbs)**: Ukrainian distinguishes one-way motion (right now, in one direction) from habitual/round-trip motion. This is NOT about speed or distance — it is about the nature of the trip.; Pair 1 — on foot: іти (going right now, one direction) vs. ходити (going regularly, back and forth). Я іду до магазину (I am walking to the store right now). Я ходжу до магазину щодня (I go to the store every day).; Pair 2 — by vehicle: їхати (riding/driving right now) vs. їздити (riding regularly). Ми їдемо до Львова (We are driving to Lviv). Ми їздимо до Львова щоліта (We go to Lviv every summer).
- **Дієвідміна та доконаний вид (Conjugation and Perfective Forms)**: Present tense conjugation of all six verbs. іти: іду, ідеш, іде, ідемо, ідете, ідуть. ходити: ходжу, ходиш, ходить, ходимо, ходите, ходять.; їхати: їду, їдеш, їде, їдемо, їдете, їдуть. їздити: їжджу, їздиш, їздить, їздимо, їздите, їздять.; летіти: лечу, летиш, летить, летимо, летите, летять. літати: літаю, літаєш, літає, літаємо, літаєте, літають.
- **Моделі дієвідмінювання: казати, пити, боротися (Conjugation Models)**: Model 1 — Stem consonant change (казати → кажу): the з → ж alternation affects the ENTIRE present tense stem (1st conjugation pattern). Full conjugation: кажу, кажеш, каже, кажемо, кажете, кажуть. Similar verbs: писати → пишу, пишеш (с → ш throughout), сказати → скажу, скажеш.; Model 2 — Irregular contraction (пити → п'ю): the stem reduces and takes the contracted endings. Full conjugation: п'ю, п'єш, п'є, п'ємо, п'єте, п'ють. Similar verbs: бити → б'ю, лити → ллю.; Model 3 — Reflexive -отися (боротися → борюся): the reflexive particle -ся stays attached throughout. Full conjugation: борюся, борешся, бореться, боремося, боретеся, борються. Note the от → ор stem change.
- **Рух + прийменники + відмінки (Motion + Prepositions + Cases)**: Direction TO: іти/їхати до + Gen. (до школи, до друга), на + Acc. (на роботу, на пошту), в/у + Acc. (в Україну, у місто).; Direction FROM: іти/їхати з + Gen. (зі школи, з роботи), від + Gen. (від друга).; Through/along: через + Acc. (через парк), по + Loc. (по вулиці).

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
