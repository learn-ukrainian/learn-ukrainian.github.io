## Linguistic Scan
Errors found:
- Russianisms/Calques: None detected.
- Surzhyk: None detected.
- Grammar/Usage: "скоро йде" is an unnatural usage of the present tense for future intent, likely a calque of the English present continuous ("heading home soon"). In Ukrainian, the perfective future "скоро піде" is standard and natural for this context.

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-zvidky -->`: Placed correctly after Dialogue 2, tests Звідки? + з/із/зі.
- `<!-- INJECT_ACTIVITY: group-sort-location-trio -->`: Placed correctly after the Звідки? section, categorizing the trio.
- `<!-- INJECT_ACTIVITY: quiz-prepositions -->`: Placed correctly after Countries and Cities, tests location/direction prepositions.
- `<!-- INJECT_ACTIVITY: fill-in-location-vs-origin -->`: Placed correctly at the end of Countries and Cities, contrasting current location vs origin.
All markers match the plan's `activity_hints` in type, focus, and count. Pacing is logical and distributed evenly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The writer modified the second dialogue from the plan ("Вона йде зі школи" -> "Вона ще в магазині"), which inadvertently introduced an unnatural grammatical structure, but otherwise covered all outline points perfectly. |
| 2. Linguistic accuracy | 8/10 | The phrase `Але́ ско́ро йде з магази́ну додому` uses present tense for a future action in an unnatural way, mimicking English continuous tense rather than the natural Ukrainian perfective future (`піде́`). |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow and clear explanations of the "з/із/зі" euphony rules for the A1 level. Deducted 1 point for presenting the unnatural "скоро йде" as a target phrase in a dialogue. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary from the plan is naturally integrated into the prose and dialogues. |
| 5. Exercise quality | 10/10 | Markers are logically placed immediately after the relevant teaching blocks to test what was just taught. |
| 6. Engagement & tone | 10/10 | The tone is engaging and sets natural, contextual scenes (e.g., "At a student mixer") without relying on corporate-speak or meta-commentary. |
| 7. Structural integrity | 8/10 | The writer added manual stress marks to H2 headers (`## Діало́ги`, `## Краї́ни і міста́`), which breaks the audit script's exact-string mapping to the `content_outline`. The word count (1374) is also ~14.5% over the 1200-word target. |
| 8. Cultural accuracy | 10/10 | Correctly emphasizes Ukrainian names for countries (Німеччина instead of Германія) and includes brief, accurate historical context for the names of Kyiv and Lviv. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are multi-turn and contextual, though Dialogue 2 suffers slightly from the unnatural phrasing mentioned above. |

## Findings
[Structural integrity] [Critical]
Location: `## Діало́ги (Dialogues)` and `## Краї́ни і міста́ (Countries and Cities)`
Issue: The writer added manual stress marks to the H2 headers. The audit script maps H2 headers to the `content_outline` strictly by exact string matching. Stress marks (`о́`, `ї́`, `а́`) will cause the mapping to fail, breaking the downstream pipeline.
Fix: Remove the stress marks from the H2 headers so they match the `meta.yaml` outline exactly.

[Linguistic accuracy] [Major]
Location: `— Оксана: Вона́ ще в магази́ні. Але́ ско́ро йде з магази́ну додому. *(She's still at the store. But she's heading home from the store soon.)*`
Issue: In Ukrainian, the present continuous tense ("йде") is rarely and awkwardly used to express a near-future intent like "heading home soon" (which is an English construction). The perfective future "піде" is standard and much more natural here.
Fix: Change `йде` to `піде́` and update the English translation to reflect the future tense.

## Verdict: REVISE
The module requires revision due to a critical structural issue (stress marks in H2 headers breaking the pipeline audit) and a major linguistic issue (unnatural use of present tense for a future action in Dialogue 2). The required fixes are targeted and deterministic.

<fixes>
- find: "## Діало́ги (Dialogues)"
  replace: "## Діалоги (Dialogues)"
- find: "## Краї́ни і міста́ (Countries and Cities)"
  replace: "## Країни і міста (Countries and Cities)"
- find: "— Оксана: Вона́ ще в магази́ні. Але́ ско́ро йде з магази́ну додому. *(She's still at the store. But she's heading home from the store soon.)*"
  replace: "— Оксана: Вона́ ще в магази́ні. Але́ ско́ро піде́ з магази́ну додому. *(She's still at the store. But she'll be heading home from the store soon.)*"
</fixes>
