## Linguistic Scan
`Діалоги` contains a factual grammar overstatement: “The names of the country and city change their endings to indicate origin.” This is not true as a general rule, because indeclinable place names such as `Торонто` do not change form after `з/із/зі`.

## Exercise Check
4 markers are present, and the IDs match the 4 `activity_hints` in the plan: `fill-in-where-from`, `group-sort-location-trio`, `quiz-preposition-choice`, `fill-in-contrast-location-origin`.

Placement is mostly correct, but `<!-- INJECT_ACTIVITY: group-sort-location-trio -->` is too late. It tests the `Де? / Куди? / Звідки?` trio yet appears only after the final summary, clustered with the quiz, instead of following the trio teaching in `Звідки?`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned sections are present and the planned vocabulary is broadly covered, but the prose demonstrates the trio only with `в Україні / в Україну / з України`; a city destination form is never shown in prose even though the plan requires “Country/city names in three case forms.” |
| 2. Linguistic accuracy | 8/10 | Most Ukrainian forms are clean, but `Діалоги` states: “The names of the country and city change their endings to indicate origin,” which falsely generalizes declension to all place names. |
| 3. Pedagogical quality | 8/10 | The module has a clear PPP flow with dialogues, explanation, and practice markers, but the key trio explanation lacks a parallel city example, so the learner does not see the full city pattern alongside the country pattern. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose, and the recommended set is also covered: `Одеса`, `Харків`, `США`, `Англія`, `Німеччина`, `Польща`, `додому`. |
| 5. Exercise quality | 8/10 | All 4 marker IDs match the 4 planned activities, but `group-sort-location-trio` is placed after the summary and clustered with the quiz instead of directly after the trio is taught. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and concrete; the student mixer and street-encounter scenarios keep the explanation grounded in plausible beginner situations. |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present in order, the pipeline word count is 1380, and there are no stray formatting artifacts beyond the expected inject markers. |
| 8. Cultural accuracy | 10/10 | The framing is Ukrainian-centered throughout, with no Russian-comparison framing and with decolonized English spellings such as `Kyiv` and `Odesa`. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues use named speakers, real situations, and multi-turn exchanges; the second dialogue naturally contrasts `звідки` and `куди`. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Діалоги` — “The names of the country and city change their endings to indicate origin.”  
Issue: This teaches a false generalization. Not every place name changes form after `з/із/зі`; indeclinable names such as `Торонто` stay the same.  
Fix: Change the sentence so it says that many names change, while some names such as `Торонто` do not.

[PLAN ADHERENCE / PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Звідки?` — “We ask **Де ти?** ... **в Україні** ... **в Україну** ... **з України**.”  
Issue: The module explains the trio only with a country example. The plan explicitly requires “Country/city names in three case forms,” but the prose never shows a city destination form in the teaching text.  
Fix: Add a parallel city trio, e.g. `в Києві / в Київ / з Києва`, to that paragraph.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: end of module — `<!-- INJECT_ACTIVITY: group-sort-location-trio -->` immediately before `<!-- INJECT_ACTIVITY: quiz-preposition-choice -->`  
Issue: The group-sort activity tests the location trio but is delayed until after the summary and clustered with the final quiz instead of appearing near the trio explanation.  
Fix: Move `group-sort-location-trio` to the end of the `Звідки?` section, near `fill-in-where-from`.

## Verdict: REVISE
REVISE. The module is structurally solid and mostly accurate, but it contains one factual grammar error and two important alignment/pedagogy issues. That fails the severity gate and leaves multiple dimensions below 9.

<fixes>
- find: "Notice how the question is formed with one word: **звідки**. The answer begins with the preposition **з** (from) or **із**, followed by the place name. The names of the country and city change their endings to indicate origin."
  replace: "Notice how the question is formed with one word: **звідки**. The answer begins with the preposition **з** (from) or **із**, followed by the place name. Many country and city names change their endings to indicate origin, while some names, such as **Торонто**, stay the same."
- find: "You now have the complete trio of spatial questions in Ukrainian. These three questions form the foundation of how we talk about location and movement. We ask **Де ти?** (Where are you?) when talking about a static location, like **в Україні** (in Ukraine). We ask **Куди ти їдеш?** (Where are you going?) for a destination, like **в Україну** (to Ukraine). Finally, we ask **Звідки ти?** (Where are you from?) to find out the origin, like **з України** (from Ukraine)."
  replace: "You now have the complete trio of spatial questions in Ukrainian. These three questions form the foundation of how we talk about location and movement. We ask **Де ти?** (Where are you?) when talking about a static location, like **в Україні** (in Ukraine). We ask **Куди ти їдеш?** (Where are you going?) for a destination, like **в Україну** (to Ukraine). Finally, we ask **Звідки ти?** (Where are you from?) to find out the origin, like **з України** (from Ukraine). The same trio works with cities too: **в Києві** (in Kyiv), **в Київ** (to Kyiv), **з Києва** (from Kyiv)."
- find: "<!-- INJECT_ACTIVITY: fill-in-where-from -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-where-from -->\n<!-- INJECT_ACTIVITY: group-sort-location-trio -->"
- find: "<!-- INJECT_ACTIVITY: group-sort-location-trio -->\n<!-- INJECT_ACTIVITY: quiz-preposition-choice -->"
  replace: "<!-- INJECT_ACTIVITY: quiz-preposition-choice -->"
</fixes>