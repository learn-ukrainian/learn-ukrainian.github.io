<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 51: My Plans (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- план (plan, m)
- тиждень (week, m)
- вільний (free, adj)
- зустріч (meeting, f)
- відпочивати (to rest)
- прибирати (to clean)
- вечірка (party, f)
- зустрінемося (let's meet — chunk)
- з задоволенням (with pleasure)
- на жаль (unfortunately)
- допізна (until late)
- звичайно (of course)
- квартира (apartment, f)
- кіно (cinema, n)
- вчити (to study/learn)

## Sections to research

- **Dialogues**: Dialogue 1 — Making plans: — Що ти будеш робити у суботу? — Зранку я буду прибирати квартиру. — А вдень? — Вдень я буду ходити в магазин. А ти? — Я буду відпочивати! Може, підемо в кафе ввечері? — Добре! О котрій? — О шостій. Добре? — Чудово! До зустрічі у суботу! Future + time + invitation.; Dialogue 2 — A busy week: — У тебе є плани на тиждень? — Так, багато! — У понеділок я буду працювати допізна. — У вівторок буду вчитися. У середу — зустріч з друзями. — А у четвер? — У четвер я буду готувати на вечірку. — А в п'ятницю? — В п'ятницю — вечірка! Ти будеш? — Звичайно буду! Days of week + future planning.
- **Планування (Planning)**: Scheduling patterns: У + day: у понеділок, у вівторок, у середу, у четвер, у п'ятницю. У суботу / в неділю (on Saturday / on Sunday). О + time: о дев'ятій, о третій, о шостій. Зранку / вдень / ввечері (morning / afternoon / evening). Combine: У суботу ввечері я буду дивитися фільм.; Invitation phrases: Ходімо в кафе! (Let's go to a cafe! — imperative from M43) Може, підемо в кіно? (Maybe we'll go to the cinema?) Ти будеш вільний/вільна у суботу? (Will you be free on Saturday?) Давай зустрінемося о п'ятій! (Let's meet at five!) Responses: Добре! Чудово! З задоволенням! На жаль, не можу.
- **Мій тиждень (My Week)**: Model plan — Taras's week: У понеділок я буду працювати. Після роботи буду вчити українську. У вівторок я буду обідати з другом у кафе. У середу ввечері я буду дивитися футбол. У четвер я буду готувати вечерю для родини. У п'ятницю я буду відпочивати — піду в кіно. У суботу зранку буду прибирати, а вдень гуляти в парку. В неділю я буду спати довго! Each day = буду + activity.; Your turn — plan your week: Template: У [day] я буду [activity]. Add details: time (о котрій?), place (де?), with whom (з ким?). У суботу о десятій я буду гуляти в парку з другом. Use all the A1 vocabulary: places, food, people, activities.
- **Summary**: Planning toolkit: Day + time + буду + infinitive: У суботу о третій я буду готувати обід. Invitations: Ходімо! Може, підемо? Давай зустрінемося! Responses: Добре! З задоволенням! На жаль, не можу. Days review: понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя. Self-check: Plan your ideal weekend — what will you do on Saturday and Sunday?

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
