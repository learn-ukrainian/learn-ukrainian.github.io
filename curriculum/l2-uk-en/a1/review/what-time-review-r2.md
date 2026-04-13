## Linguistic Scan
- Critical factual error: `You must avoid using the word "без" (without) for time, which is a common Russianism and incorrect in standard Ukrainian.` This is false. The repo’s textbook corpus accepts standard Ukrainian forms with `без`, including `без чверті сьома` and `без десяти дев’ять`.
- Critical factual error: `You must never use the prepositions "в" or "у" for time expressions, as this is a very common Russianism that Ukrainian speakers avoid.` This is false as stated. The repo’s textbook corpus includes standard variants such as `в десять хвилин на першу годину` and `в десять хвилин по дванадцятій годині`.
- No Russianisms, Surzhyk forms, paronym errors, or Russian letters `ы/э/ё/ъ` were confirmed in the Ukrainian forms themselves.

## Exercise Check
All 4 planned exercise markers are present:
- `quiz-clock-matching`
- `match-up-digits`
- `fill-in-o-kotrii`
- `quiz-time-of-day`

Placement is correct:
- The two `Котра година?` activities come after the time-telling section.
- The `О котрій?` fill-in and time-of-day quiz come after the scheduling section.

Coverage matches the plan’s `activity_hints`, and there are no inline DSL exercise blocks to audit.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present, and the prose covers the planned core content: `Десята.`, `Пів на другу`, `о першій/об одинадцятій`, `ранку/дня/вечора`, `опівдні`. Deduction: the module adds unsupported bans such as `You must avoid using the word "без"...` and `You must never use the prepositions "в" or "у"...`. |
| 2. Linguistic accuracy | 4/10 | Critical factual errors: `You must avoid using the word "без"... incorrect in standard Ukrainian.` and `You must never use the prepositions "в" or "у"...`. Both contradict textbook evidence in the repo. |
| 3. Pedagogical quality | 6/10 | The lesson has a PPP skeleton, but it blurs a key distinction with `Here, the students use the question word **коли** (when) interchangeably with scheduling questions.` That weakens the contrast the module is supposed to teach. |
| 4. Vocabulary coverage | 9/10 | Required plan vocabulary is used in prose: `година`, `котра`, `перша/друга/третя`, `ранку`, `дня`, `вечора`, `ночі`; recommended items `пів`, `чверть`, `опівдні` are also included. |
| 5. Exercise quality | 9/10 | All 4 planned activities have markers, and each appears after the relevant teaching block: `quiz-clock-matching`, `match-up-digits`, `fill-in-o-kotrii`, `quiz-time-of-day`. |
| 6. Engagement & tone | 9/10 | No gamified or corporate filler; the voice stays teacherly and concrete, with useful modeled chunks like `О восьмій ранку` and `Я вечеряю о восьмій вечора.` |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly, markers are clean, and the pipeline word count is `1436`, above the `1200` target. |
| 8. Cultural accuracy | 7/10 | The module is not Russocentric in framing, but it wrongly labels standard Ukrainian patterns as Russianisms: `без` and the blanket ban on `в/у`. |
| 9. Dialogue & conversation quality | 5/10 | The first dialogue is stitched rather than natural: `Котра година? ... О котрій ти працюєш? ... тоді о першій?` never clearly names the meeting, so the planned scheduling situation feels under-motivated. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `You must avoid using the word "без" (without) for time, which is a common Russianism and incorrect in standard Ukrainian.`  
Issue: This is factually wrong. The repo’s textbook corpus accepts standard Ukrainian time expressions with `без`, including `без чверті сьома` and `без десяти дев’ять`.  
Fix: Replace the ban with a scoped note: learners may focus on `чверть на` and `за чверть` in this module, while acknowledging that `без`-based expressions also exist in standard Ukrainian.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `You must never use the prepositions "в" or "у" for time expressions, as this is a very common Russianism that Ukrainian speakers avoid.` and `Remember the common pitfalls: there is no "без" for minutes, there is no "в" for scheduling hours, and you must never use basic cardinal numbers to identify the hour.`  
Issue: This overstates the rule and teaches false Ukrainian. The repo’s textbook corpus includes standard variants with `в`, such as `в десять хвилин на першу годину` and `в десять хвилин по дванадцятій годині`.  
Fix: Rephrase to the lesson’s limited beginner target: use `о/об + hour chunk` for this module, without claiming that `в/у` are non-Ukrainian.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Here, the students use the question word **коли** (when) interchangeably with scheduling questions.`  
Issue: `коли?` is broader than `о котрій?`; calling them “interchangeable” blurs an important distinction immediately after the module tries to contrast those structures.  
Fix: Rephrase to say that `коли?` is a broader question and that the answer can still use the same `о + time` chunks.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> **Мари́на:** Приві́т, Олексі́ю! **Котра́ годи́на**? ... > **Олексій:** **До́бре**, **тоді́** **о пе́ршій**?`  
Issue: The first dialogue does not cleanly realize the plan’s situation `Coordinating a meeting time over the phone — both checking schedules.` It jumps from current time to work time to `о першій?` without explicitly naming the meeting, so it reads like stitched examples instead of a natural exchange.  
Fix: Rewrite the dialogue so the meeting is explicit and the speakers use `Котра година?` and `О котрій?` in a coherent scheduling exchange.

## Verdict: REVISE
Critical linguistic inaccuracies would teach false norms about Ukrainian time expressions (`без`, blanket `в/у` ban). The module structure and activity placement are solid, but the severity gate alone forces `REVISE`.

<fixes>
- find: |-
    You must avoid using the word "без" (without) for time, which is a common Russianism and incorrect in standard Ukrainian.
  replace: |-
    You will also hear forms with **без** in standard Ukrainian time expressions, for example **без чверті сьома** or **без десяти дев’ять**, but for this module you only need to recognize **чверть на** and **за чверть**.
- find: |-
    You must never use the prepositions "в" or "у" for time expressions, as this is a very common Russianism that Ukrainian speakers avoid.
  replace: |-
    In this module, focus on the beginner pattern **о/об + hour chunk** for scheduling: **о першій**, **об одинадцятій**. More complex time expressions can use other patterns, but you do not need them yet.
- find: |-
    Remember the common pitfalls: there is no "без" for minutes, there is no "в" for scheduling hours, and you must never use basic cardinal numbers to identify the hour.
  replace: |-
    Remember the core beginner pattern in this module: use ordinal forms for the hour (**Десята.**, **О десятій.**) and keep **пів на** as a chunk for half-hours.
- find: |-
    Here, the students use the question word **коли** (when) interchangeably with scheduling questions.
  replace: |-
    Here, the students use the broader question word **коли** (when), while the answers still use the same **о + time** chunks you need for scheduling.
- find: |-
    > **Мари́на:** Приві́т, Олексі́ю! **Котра́ годи́на**? *(Hi, Oleksiy! What time is it?)*
    > **Олексі́й:** Привіт! **Деся́та**. *(Hi! Ten o'clock.)*
    > **Марина:** **О котрі́й** ти **працю́єш**? *(At what time do you work?)*
    > **Олексій:** **О дев'я́тій**. А ти? *(At nine. And you?)*
    > **Марина:** Я працю́ю **о деся́тій**. *(I work at ten.)*
    > **Олексій:** **До́бре**, **тоді́** **о пе́ршій**? *(Good, then at one?)*
    > **Марина:** Так! *(Yes!)*
  replace: |-
    > **Мари́на:** Приві́т, Олексі́ю! **Котра́ годи́на**? *(Hi, Oleksiy! What time is it?)*
    > **Олексі́й:** Привіт! **Деся́та**. *(Hi! Ten o'clock.)*
    > **Марина:** До́бре. **О котрі́й** ти сього́дні **працю́єш**? *(Okay. At what time are you working today?)*
    > **Олексій:** **О дев'я́тій**. А ти? *(At nine. And you?)*
    > **Марина:** Я працю́ю **о деся́тій**. *(I work at ten.)*
    > **Олексій:** **До́бре**, **тоді́** зустрі́немося **о пе́ршій**? *(Good, then shall we meet at one?)*
    > **Марина:** Так! До зустрі́чі! *(Yes! See you!)*
</fixes>