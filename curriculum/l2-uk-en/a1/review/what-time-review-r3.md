## Linguistic Scan
- Factually wrong grammar claim in `## Котра година?`: `"You will also hear forms with **без** in standard Ukrainian time expressions, for example **без чверті сьома** or **без десяти дев’ять**..."` Textbook evidence in the local corpus contradicts this: `5-ukrmova-litvinova-2022` marks `без чверті сьома` as `НЕПРАВИЛЬНО побудовано словосполучення`, and `6-klas-ukrmova-litvinova-2023` teaches second-half-hour formulas with `за, до`.

## Exercise Check
Found 4 markers: `quiz-clock-matching`, `match-up-digits`, `fill-in-o-kotrii`, `quiz-time-of-day`.

All 4 markers appear after the relevant teaching sections and map cleanly to the 4 `activity_hints` in the plan. No placement problem found. Exercise logic and item counts cannot be verified from marker placeholders alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All planned sections are present in order, and the core plan items are explicitly covered: `Котра година? — Десята.`, `О котрій? — О десятій.`, `Пів на другу`, `опівдні`, and time-of-day chunks like `о сьомій ранку`. |
| 2. Linguistic accuracy | 4/10 | `"You will also hear forms with **без** in standard Ukrainian time expressions, for example **без чверті сьома** or **без десяти дев’ять**"` teaches wrong/nonstandard formulas as standard. |
| 3. Pedagogical quality | 7/10 | The paragraph starting `"The specific communicative functions of these questions show a clear division."` is a long English theory block between beginner dialogues; it weakens PPP flow by foregrounding abstract analysis over immediate pattern practice. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary from the plan appears in prose: `година`, `котра`, `перша/друга/третя`, `ранок`, `день`, `вечір`, `ніч`, plus recommended `пів`, `чверть`, `опівдні`. |
| 5. Exercise quality | 9/10 | Marker inventory matches the plan one-to-one and placement is correct: two markers after `Котра година?`, two after `О котрій?`. |
| 6. Engagement & tone | 9/10 | Tone is teacherly and practical; the self-check and model schedule keep the lesson usable. |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and ordered correctly; pipeline word count is 1482, above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian time expressions on Ukrainian terms and does not rely on Russian-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | Two named-speaker dialogues cover real situations from the plan: coordinating a meeting and discussing a daily schedule. |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]  
Location: `## Котра година?` — `"You will also hear forms with **без** in standard Ukrainian time expressions, for example **без чверті сьома** or **без десяти дев’ять**, but for this module you only need to recognize **чверть на** and **за чверть**."`  
Issue: This teaches incorrect/nonstandard time formulas as standard Ukrainian. The local textbook corpus explicitly marks `без чверті сьома` as incorrect and teaches `за/до` patterns instead.  
Fix: Remove the `без...` claim and keep the A1 scope to `чверть на` and `за чверть`.

[3. Pedagogical quality] [SEVERITY: major]  
Location: `## Діалоги` — `"The specific communicative functions of these questions show a clear division. The phrase **котра година** identifies the current time on the clock..."`  
Issue: This is overly abstract metalanguage for A1 and interrupts the dialogue-to-pattern flow with a long English explanation.  
Fix: Replace it with a short, concrete contrast built from the lesson’s own chunks: `Котра година? — Десята.` and `О котрій? — О дев'ятій.`

## Verdict: REVISE
REVISE because there is a critical linguistic error that teaches wrong Ukrainian time formulas as standard, and the pedagogical flow is weakened by an overly abstract explanation in an A1 lesson.

<fixes>
- find: "You will also hear forms with **без** in standard Ukrainian time expressions, for example **без чверті сьома** or **без десяти дев’ять**, but for this module you only need to recognize **чверть на** and **за чверть**."
  replace: "For this module, you only need to recognize **чверть на** and **за чверть**. Do not add extra minute patterns yet."
- find: "The specific communicative functions of these questions show a clear division. The phrase **котра година** identifies the current time on the clock, much like asking for a name in an ordered sequence. Marina wants to know the exact hour right now. On the other hand, the question **о котрій** asks for a specific point on a timeline. Speakers use this when scheduling an event or an action. You should contrast the English phrases \"At what time?\" versus \"What time is it?\". While English uses the noun \"time\" for both concepts, Ukrainian relies on two distinct structures to differentiate between identifying the current moment and setting an appointment."
  replace: "Use **Котра година?** to ask about the time now: **Котра година? — Десята.** Use **О котрій?** to ask about a planned time: **О котрій ти працюєш? — О дев'ятій.** This is the main contrast you need in this module."
</fixes>