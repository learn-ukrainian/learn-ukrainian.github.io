<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 6: Вид у розповіді (B1, B1.0 [Baselines & Aspect Mastery])

## Plan vocabulary to verify

- тло
- передній план
- розповідь
- оповідання
- оповідач
- подія
- опис
- спочатку
- потім
- раптом
- нарешті
- тим часом
- одночасно
- послідовно
- послідовність
- спогад
- поки
- після цього
- тоді

## Sections to research

- **Тест: тло чи подія?**: Diagnostic: learners read a short Ukrainian narrative (10-12 sentences) and mark each verb as тло (background) or подія (foreground event). No rules given — pure intuition. Text example: Був теплий вечір. Сонце сідало за обрій. Ми сиділи на терасі й розмовляли. Раптом задзвонив телефон. Я підвів і відповів. Це був Андрій — він повернувся з Америки.; Self-assessment: how many verbs did you classify correctly? Discussion: what patterns did you notice? (Background verbs = impf, event verbs = pf.) This module makes the pattern explicit and teaches you to USE it in your own writing.; Key concept introduced: every narrative has two layers. Тло (background) — setting, weather, ongoing situations, emotions, descriptions. Uses недоконаний вид. Передній план (foreground) — events that move the story forward, changes, turning points. Uses доконаний вид.
- **Тло: недоконаний вид у наративі**: Functions of imperfective in narration (Заболотний Grade 7 p.54): Setting the scene: Надворі було холодно. Дув сильний вітер. Describing ongoing actions: Діти гралися у дворі. Бабуся сиділа біля вікна і в'язала. Simultaneous actions: Поки мама готувала вечерю, тато читав газету. Emotional/mental states: Він хвилювався. Вона не знала, що робити.; Temporal connectors with imperfective background: тим часом (meanwhile), у цей час (at that time), поки (while), доки (while/until), увесь час (all the time), зазвичай (usually — for habitual background). Each connector naturally pairs with imperfective because it signals duration or simultaneity.; Extended background passage practice: learners write a 5-sentence scene-setting paragraph using only недоконаний вид. Topic: Опишіть вечір у маленькому українському містечку. Every verb must be imperfective. Discussion: what kind of atmosphere does pure background create? (Calm, static, timeless.)
- **Передній план: доконаний вид у наративі**: Functions of perfective in narration: Sequential events (plot): Він встав, одягнувся, вийшов із дому. Turning points: Раптом двері відчинилися. Completed results: Вона написала лист і відправила його. Single decisive actions: Він прийняв рішення.; Temporal connectors with perfective foreground: спочатку (first), потім (then), після цього (after that), раптом (suddenly), нарешті (finally), тоді (then). These connectors signal sequence — one action follows another. Sequential chains are naturally perfective: Спочатку я подзвонив. Потім написав листа. Нарешті отримав відповідь.; The interplay — weaving both layers: Ми сиділи (impf — background) в парку. Було (impf — setting) тихо. Раптом хтось закричав (pf — event). Ми підвелися (pf — reaction) і побігли (pf — action) до виходу. Серце калатало (impf — state during events). Ми вибігли (pf — completed escape) на вулицю.
- **Підсумок: аспект як наративний інструмент**: Synthesis: aspect in narration is not about individual sentences — it's about the FLOW between background and foreground. Native speakers shift between aspects instinctively. B1 learners need to make this shift consciously until it becomes automatic.; Narrative transformation exercise: learners receive a short text and rewrite it twice. Version A: emphasize background (expand descriptions, add imperfective detail, slow the pacing). Version B: emphasize foreground (cut descriptions, accelerate events, make it punchy). Compare both versions — how does aspect distribution change the FEEL of the story?; Common errors in aspect narration: Mixing aspects within a background block (*Надворі йшов дощ. Загриміло. Було сиро. — 'загриміло' is pf, breaking the background). Using imperfective for clearly sequential events (*Він вставав, одягався, виходив з дому — sounds habitual, not narrative). Over-using one aspect — either all-pf (reads like a police report) or all-impf (reads like a description with no events).

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
