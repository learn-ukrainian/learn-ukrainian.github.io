<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 42: 30 найважливіших видових пар (A2, A2.6 [Aspect, Tenses, and Motion])

## Plan vocabulary to verify

- видова пара (aspect pair)
- префікс (prefix)
- суфікс (suffix)
- брати / взяти (to take — impf./pf.)
- давати / дати (to give — impf./pf.)
- говорити / сказати (to say — impf./pf.)
- класти / покласти (to put — impf./pf.)
- починати / почати (to begin — impf./pf.)
- закінчувати / закінчити (to finish — impf./pf.)
- допомагати / допомогти (to help — impf./pf.)
- утворення (formation)
- морфологія (morphology)
- тільки що (just now)
- вже (already)

## Sections to research

- **Як утворюються видові пари (How Aspect Pairs Are Formed)**: Pattern 1 — Prefixation (most common): писати → написати, читати → прочитати, робити → зробити, їсти → з'їсти, варити → зварити. The prefix adds completion without changing the base meaning.; Pattern 2 — Suffix change: записувати → записати (-увати → -ати), розповідати → розповісти (-ідати → -істи), пояснювати → пояснити (-ювати → -ити). Imperfective suffixes are longer.; Pattern 3 — Stem change: допомагати → допомогти, відповідати → відповісти. The stem itself transforms.
- **30 пар: Список і приклади (30 Pairs: List and Examples)**: Group A — Daily actions (10 pairs): робити/зробити, писати/написати, читати/прочитати, готувати/приготувати, їсти/з'їсти, пити/випити, варити/зварити, мити/помити, прибирати/прибрати, прасувати/випрасувати.; Group B — Communication & learning (10 pairs): говорити/сказати, питати/запитати, відповідати/відповісти, пояснювати/пояснити, вчити/вивчити, розуміти/зрозуміти, казати/сказати, розповідати/розповісти, записувати/записати, перекладати/перекласти.; Group C — Movement & interaction (10 pairs): брати/взяти, давати/дати, класти/покласти, відкривати/відкрити, закривати/закрити, починати/почати, закінчувати/закінчити, допомагати/допомогти, купувати/купити, платити/заплатити.
- **Вибір виду в складних ситуаціях (Aspect Choice in Complex Situations)**: Sequence of completed events — all perfective: Я встав, вмився, поснідав і пішов на роботу (I got up, washed, had breakfast, and left for work).; Interruption — imperfective background + perfective event: Коли я готувала вечерю, подзвонила подруга (While I was cooking dinner, a friend called).; Habitual vs. single — imperfective for habit, perfective for one-time: Вона завжди допомагала сусідам (She always helped the neighbors) vs. Вона допомогла сусідці вчора (She helped the neighbor yesterday).
- **Практика у діалогах (Practice in Dialogues)**: Dialogue 1: Що ти зробив сьогодні? — Listing completed tasks with perfective. А що ти робив увечері? — Describing an ongoing evening activity with imperfective.; Dialogue 2: Planning and reporting. Що ти будеш робити завтра? (impf.) vs. Що ти зробиш до п'ятниці? (pf.) — aspect in future context too.; Common conversational patterns with aspect: Ти вже зробив? (Have you done it yet?), Я ще роблю (I'm still doing it), Я тільки що зробив (I just did it).

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
