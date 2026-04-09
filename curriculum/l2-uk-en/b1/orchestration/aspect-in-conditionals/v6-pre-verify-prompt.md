<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 24: Вид в умовних реченнях (B1, B1.0 [Baselines & Aspect Mastery])

## Plan vocabulary to verify

- умовний спосіб
- реальна умова
- нереальна умова
- якщо
- якби
- умова
- наслідок
- припущення
- можливість
- неможливість
- протилежний
- гіпотетичний
- частка
- вміти
- змогти
- виграти
- вигравати
- народитися
- уявляти
- уявити

## Sections to research

- **Тест: реальне чи нереальне?**: Diagnostic: 10 conditional sentences — learners classify as реальна умова (real, possible) or нереальна умова (unreal, hypothetical) and choose the natural verb form. Examples: (Якщо / Якби) матимеш час, зателефонуй мені. (Якщо / Якби) я був президентом, змінив би все. (Якщо / Якби) вивчиш цей матеріал, складеш іспит.; Self-assessment: most learners intuitively distinguish якщо (real possibility) from якби (contrary to fact). But aspect choice within conditionals is less intuitive — this module makes it explicit.; Key framework: Two types of conditionals, two aspect logics. Реальна умова: якщо + future indicative → result in future. Нереальна умова: якби + past form + б/би → hypothetical result. Aspect choice is INDEPENDENT of the conditional type — it depends on what you want to say about the action.
- **Реальна умова: якщо + вид**: Real conditionals express genuine possibilities (Заболотний Grade 7 p.94). Condition clause: often доконаний (specific completed condition) — Якщо напишеш лист... Якщо прийдуть гості... Якщо закінчиш роботу... Result clause: typically доконаний (specific result follows) — ...я відправлю його. ...ми приготуємо вечерю. ...підемо гуляти.; Imperfective in real conditionals — when process matters: Якщо будеш багато працювати, втомишся. (impf condition: process of working → pf result: getting tired). Якщо читатимеш щодня, поліпшиш мову. (impf condition: ongoing habit → pf result: improvement). The condition is a process; the result is an achievement.; Double-perfective pattern (most common): Якщо вивчиш — складеш. Якщо приїдеш — покажу. Якщо допоможеш — подякую. Both clauses focus on specific completed actions — 'if X is done, Y will be done.' This is the workhorse pattern of Ukrainian real conditionals.
- **Нереальна умова: якби + вид**: Unreal conditionals express impossible or unlikely scenarios (Литвінова Grade 7 p.90). Contrary to present fact: Якби я знав українську краще, я б читав Шевченка в оригіналі. (impf — ongoing hypothetical activity). Якби в мене були гроші, я б купив цей будинок. (pf — specific hypothetical result).; Contrary to past fact: Якби я прочитав ту книжку, я б знав відповідь. (pf condition: reading completed in hypothetical past → impf result: ongoing hypothetical knowledge). Якби вона зателефонувала, ми б зустрілися. (pf + pf: specific hypothetical actions).; Aspect choice in unreal conditionals — the pattern is FLEXIBLE: Impf + impf: Якби я жив у Львові, щодня ходив би на каву. (both habitual/ongoing). Pf + pf: Якби я знайшов ключі, відчинив би двері. (both specific completed). Impf + pf: Якби я знав раніше, подзвонив би. (ongoing state → specific action). Pf + impf: Якби я закінчив цей проєкт, відпочивав би. (completed event → ongoing state). The choice depends on what aspect of the hypothetical the speaker imagines.
- **Підсумок: вид як спосіб бачити можливості**: Synthesis: real conditionals are about planning (mostly pf — specific actions and results). Unreal conditionals are about imagining (flexible — aspect depends on what kind of hypothetical world the speaker envisions). In both cases, aspect is a CHOICE, not a mechanical rule.; Contrastive pairs showing the power of aspect in conditionals: Якщо вивчиш українську, знатимеш її добре. (real: if you learn it, you'll know it — both focused on completion + ongoing state). Якби вивчив українську, знав би її добре. (unreal: if you HAD learned — hypothetical completed event → ongoing hypothetical knowledge).; Common errors: *Якщо будеш написати лист... (impossible — буду + pf; should be якщо напишеш). *Якби я знатиму... (future form in unreal conditional — should be якби я знав). *Якби я прочитав би книжку (double би — one б/би is enough). Mixing якщо/якби — якщо for real, якби for unreal.

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
