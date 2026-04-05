<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 40: Що ти робив? А що зробив? (A2, A2.6 [Aspect, Tenses, and Motion])

## Plan vocabulary to verify

- минулий час (past tense)
- робити / зробити (to do — impf./pf.)
- писати / написати (to write — impf./pf.)
- читати / прочитати (to read — impf./pf.)
- готувати / приготувати (to cook/prepare — impf./pf.)
- вчити / вивчити (to study/learn — impf./pf.)
- процес (process)
- результат (result)
- довго (for a long time)
- раптом (suddenly)
- щодня (every day)
- нарешті (finally, at last)
- одного разу (one time, once)
- тривалість (duration)

## Sections to research

- **Два питання — два види (Two Questions — Two Aspects)**: The key question pair: Що ти робив? (What were you doing? — process) vs. Що ти зробив? (What did you get done? — result). This is not a grammar trick but a real difference in how Ukrainians think about actions.; Imperfective past = the camera was rolling: Я читав книгу (I was reading). The focus is on the action itself, its duration, or its repetition.; Perfective past = the photo of the result: Я прочитав книгу (I read/finished the book). The focus is on the completed outcome.
- **Коли вживати недоконаний вид (When to Use Imperfective Past)**: Process or duration: Я довго писав листа (I was writing a letter for a long time). The action stretched over time.; Repetition or habit: Вона щодня готувала сніданок (She made breakfast every day). A repeated action, not one single event.; Background action: Коли я снідав, подзвонив друг (While I was having breakfast, a friend called). Imperfective sets the scene.
- **Коли вживати доконаний вид (When to Use Perfective Past)**: Completed result: Я написав листа (I wrote the letter — it is done). The action reached its endpoint and produced a result.; Single event in sequence: Я прийшов додому, пообідав і подзвонив мамі (I came home, had lunch, and called Mom). Each verb marks a completed step.; Sudden action: Раптом хтось постукав у двері (Suddenly someone knocked on the door). A single, punctual event.
- **Практика вибору виду (Choosing the Right Aspect)**: Contrastive pairs in context: Він читав газету (was reading) vs. Він прочитав газету (finished reading). Вона вчила слова (was studying words) vs. Вона вивчила слова (learned the words).; Mini-narratives combining both aspects: Коли я готував вечерю, раптом погасло світло. Я знайшов свічку і запалив її.; Common mistakes: using imperfective when result matters (*Я писав листа вчора — ambiguous), using perfective for repeated actions (*Він щодня зробив вправи — wrong).

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
