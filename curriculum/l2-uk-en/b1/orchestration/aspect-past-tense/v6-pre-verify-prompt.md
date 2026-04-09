<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 4: Вид у минулому часі (B1, B1.0 [Baselines & Aspect Mastery])

## Plan vocabulary to verify

- доконаний вид
- недоконаний вид
- видова пара
- результат
- процес
- тривалість
- завершеність
- повторюваність
- однократність
- одного разу
- щодня
- щоразу
- завжди
- іноді
- нарешті
- раптом
- готувати
- приготувати
- вивчити
- зателефонувати

## Sections to research

- **Тест на інтуїцію: що ви вже відчуваєте?**: Diagnostic test: 10 sentence pairs where learners choose between доконаний and недоконаний вид in past tense based on context. No rules given yet — pure intuition from A2. Examples: Вчора я (читав / прочитав) цю книжку — до останньої сторінки. Вчора я (читав / прочитав) увечері — мені було нудно.; Immediate self-assessment: which pairs felt obvious, which felt ambiguous? Learners mark their confidence level. This reveals what A2 taught them implicitly and what B1 needs to make explicit.; Mini-dialogue with aspect ambiguity: two people describe the same evening differently — Я дивився фільм (process, enjoyed it) vs Я подивився фільм (finished it, ready to discuss). Discussion: both are 'correct' — the choice is about WHAT you want to communicate.
- **Результат чи процес? Основний вибір**: Core principle (Заболотний Grade 7 p.54): Доконаний вид у минулому часі позначає завершену дію з результатом. Недоконаний вид позначає тривалу дію, процес, або факт без акценту на результаті. Мінімальні пари: писав лист (процес, тривалість) / написав лист (результат, лист готовий). читав книжку (процес) / прочитав книжку (результат, закінчив).; Decision framework with 8 core видових пар in past tense: писати/написати, читати/прочитати, робити/зробити, говорити/сказати, брати/взяти, вчити/вивчити, готувати/приготувати, відповідати/відповісти. Each pair shown in result-context and process-context.; Time markers as signals (Литвінова Grade 7 p.38): Недоконаний → щодня, завжди, часто, іноді, зазвичай, довго, три години, цілий день. Доконаний → одного разу, вчора ввечері (single event), нарешті, за годину, раптом. Warning: markers are signals, not rules — context overrides.
- **Повторюваність і однократність**: Second aspect dimension: repeated vs single (Заболотний Grade 7 p.56). Repeated past action = недоконаний вид: Щоранку він снідав о восьмій. Вона часто телефонувала мамі. Ми завжди гуляли після обіду. Single past event = доконаний вид: Одного разу він не поснідав. Вона зателефонувала о п'ятій. Ми погуляли в парку.; Habitual past as narrative device: Коли я жив у Львові, щовечора ходив на прогулянку. Зазвичай купував каву на Площі Ринок і сідав на лавку біля фонтану. The entire passage uses недоконаний because it describes a recurring pattern — not because any single action was 'incomplete.'; Contrast with one-time interruption: ...Але одного вечора я побачив старого друга. Ми зупинилися, поговорили. Він запросив мене на вечерю. Perfective breaks the habitual pattern — signals a specific, unique event.
- **Підсумок: вид як інструмент мислення**: Synthesis table: two axes of aspect choice in past tense. Axis 1: result (доконаний) vs process (недоконаний). Axis 2: single event (доконаний) vs repeated (недоконаний). Both axes point the same direction — but the reasoning differs, and learners must identify WHICH axis drives their choice.; Common errors and corrections: *Я вчора прочитав книжку три години (unnatural — process + duration = читав). *Вона щодня приготувала обід (repeated action = готувала). *Він одного разу писав лист бабусі (single completed event = написав). Analysis of WHY each error feels wrong to a native speaker.; Extended practice: learners tell a story about 'Мій минулий тиждень' using both aspects. Must include: 3+ habitual actions (impf), 3+ completed events (pf), 1+ contrast within the same sentence (Коли я читав, зателефонував друг). Peer feedback focuses on aspect choice, not grammar form.

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
