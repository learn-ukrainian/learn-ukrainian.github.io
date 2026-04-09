<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 49: Yesterday (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- учора (yesterday)
- зранку (in the morning)
- вдень (in the afternoon)
- ввечері (in the evening)
- потім (then)
- прокинутися (to wake up)
- поснідати (to have breakfast)
- обідати (to have lunch)
- спочатку (first/at first)
- нарешті (finally)
- повернутися (to return)
- лягти (to lie down)
- звичайний (ordinary, adj)
- продукти (groceries, pl)
- серіал (TV series, m)
- колега (colleague, m/f)

## Sections to research

- **Dialogues**: Dialogue 1 — How was your day? — Як пройшов твій день? — Добре! Зранку я прокинувся о сьомій. — Що ти робив зранку? — Я поснідав і пішов на роботу. — А вдень? — Вдень я працював і обідав з колегою. — А ввечері? — Ввечері я дивився фільм і рано ліг спати. Full day narration using time markers.; Dialogue 2 — A fun weekend: — Що ти робила у суботу? — О, я мала чудовий день! — Розкажи! — Зранку я ходила на ринок і купила фрукти. — А потім? — Потім я готувала обід. А вдень гуляла в парку. — А ввечері? — Ввечері ми з подругою ходили в ресторан. — Як файно! Sequencing with потім, а потім.
- **Розповідь про день (Narrating a Day)**: Time markers for structuring a story: зранку (in the morning), вдень (in the afternoon), ввечері (in the evening), вночі (at night). спочатку (first), потім (then), після цього (after that), нарешті (finally). These words turn separate sentences into a story: Спочатку я поснідав. Потім я пішов на роботу. Після цього я обідав.; Daily routine verbs in past tense (all genders): прокинутися → прокинувся / прокинулася поснідати → поснідав / поснідала піти → пішов / пішла обідати → обідав / обідала повернутися → повернувся / повернулася лягти спати → ліг / лягла спати
- **Мій учорашній день (My Yesterday)**: Model narrative — Anna's yesterday: Учора був звичайний день. Зранку я прокинулася о пів на сьому. Я поснідала — їла кашу і пила каву. Потім я пішла на роботу. Вдень я обідала в кафе біля офісу. Я замовила салат і сік. Після роботи я ходила в магазин і купила продукти. Ввечері я готувала вечерю і дивилася серіал. О одинадцятій я лягла спати. Note all verbs are -ла (Anna is female).; Your turn — build your own narrative: Use the template: Учора... Зранку я... Потім... Вдень... Ввечері... Combine past-tense verbs with places (кафе, парк, магазин), food (каша, кава, салат), and people (друг, колега, подруга). Everything you learned in A1 comes together here.
- **Summary**: Narration toolkit: Time structure: зранку → вдень → ввечері → вночі. Sequencing: спочатку, потім, після цього, нарешті. Daily routine past forms: прокинувся/-лася, поснідав/-ла, пішов/пішла, обідав/-ла, повернувся/-лася, ліг/лягла спати. Gender consistency: male speakers use -в/-вся forms throughout, female speakers use -ла/-лася throughout. Self-check: Tell the story of your yesterday using at least 5 verbs.

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
