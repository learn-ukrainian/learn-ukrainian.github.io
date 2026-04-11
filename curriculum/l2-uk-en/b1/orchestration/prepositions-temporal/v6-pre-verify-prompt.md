<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 58: Часові прийменники (B1, B1.5 [Case Nuances & Prepositions])

## Plan vocabulary to verify

- прийменник (preposition)
- часовий (temporal — relating to time)
- тривалість (duration)
- через (in/after — temporal; because of — causal)
- протягом (throughout/during — governs Р.в.)
- впродовж (throughout — synonym of протягом)
- під час (during — governs Р.в.)
- перед (before — governs Ор.в.)
- після (after — governs Р.в.)
- до (until/by — temporal; to — directional)
- взимку (in winter — temporal adverb)
- навесні (in spring — temporal adverb)
- вранці (in the morning — temporal adverb)
- зранку (from the morning — temporal adverb)
- о (at — clock time: о п'ятій годині)

## Sections to research

- **Через + Зн.в. та за + Зн.в.**: через + Зн.в. — 'after a time period from now': Я прийду через годину (I will come in an hour). Ми побачимося через два дні. Літо почнеться через місяць. The focus is on the waiting time: the event happens AFTER this period. Important: через can also mean 'because of' (cause, not time) — through context only: через хворобу я не прийшов (because of illness).; за + Зн.в. — 'within a time period' (completion): Я зробив це за годину (I did it in/within an hour). Вона прочитала книжку за два дні. The focus is on how long the ACTION took, not when it happens.; Key distinction (Авраменко Grade 11 p.42): через = 'after X time from now' (future reference point) за = 'within X time' (duration of action, any tense) Через годину я піду (in an hour I will go). За годину я все зробив (within an hour I finished everything). Practice: 10 sentences requiring через or за.
- **Перед, після, до, під час**: перед + Ор.в. — 'before': перед обідом, перед зустріччю, перед екзаменом. Він прийшов перед початком уроку.; після + Р.в. — 'after': після обіду, після зустрічі, після екзамену. Ми поговоримо після роботи.; до + Р.в. — 'until/before (deadline)': до обіду (before/by lunch), до п'ятої години (by 5 o'clock), до кінця тижня (by the end of the week). Зроби це до завтра (Do it by tomorrow).
- **Тривалість: протягом, впродовж, на**: протягом/упродовж + Р.в. — 'throughout/for the duration of': протягом дня, упродовж тижня, протягом трьох місяців. Both are synonyms; протягом is slightly more common in writing. From Литвінова Grade 7 p.187: 'Упродовж трьох місяців мій брат готувався до екзамену з фізики.'; на + Зн.в. — 'for a period (planned duration)': Я приїхав на тиждень (I came for a week). Вона поїхала на рік. Візьміть це на годину. The period is planned/intended, not yet elapsed.; Duration with accusative: цілий день (all day — Зн.в.), цілу ніч (all night), цілий тиждень (all week). These express duration without preposition. Also: годинами (for hours — Ор.в.), днями (for days), тижнями (for weeks) — instrumental plural expressing extended duration.
- **Позначення часу доби і пір року**: Seasons: взимку, навесні, влітку, восени (adverbs, no preposition). But with adjectives: цієї зими (Р.в.), минулого літа (Р.в.), наступної весни (Р.в.), минулої осені (Р.в.).; Time of day: вранці/зранку, вдень/удень, увечері, вночі (adverbs). With specification: о п'ятій годині, о пів на шосту, за десять шоста (= десять хвилин до шостої). From Авраменко Grade 11 p.42: avoid *без десяти шість (Russicism), correct: за десять хвилин шоста.; Days and dates: у понеділок (Зн.в.), у середу, в п'ятницю. Цього понеділка (Р.в., this Monday). Frequency: щопонеділка, щосереди (every Monday, every Wednesday). Note the different constructions: у понеділок (single event) vs щопонеділка (recurring). Practice: schedule a week using temporal expressions, distinguish one-time vs recurring events.
- **По + М.в. та інші нюанси**: по + М.в. — 'after' (temporal, formal): по обіді, по закінченні, по смерті, по завершенні. This is correct literary Ukrainian, NOT a Russicism. From Авраменко Grade 11 p.72: по + М.в. for temporal 'after.'; Distinguishing по: по + М.в. (після): по обіді (after lunch) по + Зн.в. (мета): піти по гриби (go for mushrooms) по + М.в. (розподіл): по крамницях (around shops) Context determines meaning.; Practice: mixed temporal preposition exercise — choose the correct preposition and case for 12 time-related sentences.
- **Підсумок**: Reference table: через + Зн.в. (after a period), за + Зн.в. (within a period), перед + Ор.в. (before), після + Р.в. (after), до + Р.в. (until/by), під час + Р.в. (during), протягом/упродовж + Р.в. (throughout), на + Зн.в. (for a duration), по + М.в. (after — formal).; Common Russicisms to avoid: *на протязі (use протягом), *без десяти шість (use за десять хвилин шоста), *у цьому році (use цього року — Р.в.). Also: *слідуючий тиждень (Russicism) — correct: наступний тиждень.; Self-check: express these in Ukrainian: 'in 3 hours' (через три години), 'within 2 days' (за два дні), 'before lunch' (перед обідом), 'during winter' (взимку / протягом зими), 'every Monday' (щопонеділка). Preview: next module — прийменники причини і мети.

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
