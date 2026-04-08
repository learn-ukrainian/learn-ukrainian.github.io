## Linguistic Scan
Two linguistic errors found:
1. `вушима` — Used as an example of the `-има` Instrumental plural ending for body parts. While historically attested as a dual remnant, the standard modern Ukrainian Instrumental for "вуха" is "вухами". Teaching `вушима` as standard alongside `очима` and `плечима` is incorrect.
2. `по суботах` — Used to teach schedule/recurring time expressions with `по` + Locative plural. This is a Russian calque ("по субботам"). Standard Ukrainian uses the adverb `щосуботи` or `щовихідних` without a preposition.

## Exercise Check
- All 8 `<!-- INJECT_ACTIVITY: ... -->` markers are present and correspond to the 8 specific exercises outlined in the `content_outline`.
- Marker IDs map logically to the planned exercises (e.g. `dialogue-gap-fill` for point 8, `case-trigger-quiz` for point 4).
- Markers are placed correctly after their respective theory sections and do not test concepts before they are taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module effectively covers almost all points, but missed teaching the irregular plural `око` -> `очі` in Part 1 ("Remember the "high priority trio" of irregular plurals: друг..."). It also missed the `у 2014 році` time expression in Part 2. |
| 2. Linguistic accuracy | 8/10 | Good overall command of cases, but contains a critical Russian calque teaching `по суботах` for schedules, and an archaic/substandard form `вушима` taught as standard. |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical approach. It successfully contrasts Direct Object (Accusative) vs Negation (Genitive), and company (Instrumental) vs origin (Genitive). |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary words from the plan are naturally integrated into the text (e.g., `контрольна точка`, `перевірка`, `завдання`, `впевнено`, `вихідний день`). |
| 5. Exercise quality | 10/10 | 8 exercises are correctly placed, with clear mapping to the planned exercises. |
| 6. Engagement & tone | 10/10 | The tone is encouraging and maintains a good teacher persona without being overly corporate. The "case compass" metaphor creates a continuous learning thread. |
| 7. Structural integrity | 9/10 | Word count is above the target (2154 vs 1500). H2 tags match. However, there is a dangling cut-off sentence at the very end: "6 to add the flesh...". |
| 8. Cultural accuracy | 10/10 | Uses authentic Ukrainian contexts (Lviv, Carpathians) and natural names (Олена, Максим, Сергій). |
| 9. Dialogue & conversation quality | 10/10 | The wedding planning dialogue successfully weaves all 7 cases into a natural conversation. The responses logically match question cases. |

## Findings

[1. Plan adherence] [major]
Location: `Частина 1: Форми множини` ("Remember the "high priority trio" of irregular plurals: друг (friend) becomes друзі, людина (person) becomes люди, and дитина (child) becomes діти.")
Issue: The plan explicitly required teaching the irregular plural of `око`, which was omitted.
Fix: Update the sentence to include `око` (eye) becomes `очі`.

[1. Plan adherence] [major]
Location: `Частина 2: Який відмінок?` ("Days of the week take the Accusative: у четвер (on Thursday). Hours of the day take the Locative: о п'ятій годині (at five o'clock).")
Issue: The plan explicitly required teaching `у 2014 році` as a time expression, which was omitted.
Fix: Add `у 2014 році` to the time expressions examples.

[2. Linguistic accuracy] [critical]
Location: `Частина 1: Форми множини` ("Double body parts" take the unique **-има** ending in the Instrumental case: **очима** (with eyes), **плечима** (with shoulders), **вушима** (with ears).)
Issue: `вушима` is an archaic/substandard dual form. In standard modern Ukrainian, the instrumental of "вуха" is "вухами". It should not be taught alongside `очима` and `плечима` as taking the `-има` ending.
Fix: Remove `**вушима** (with ears)`.

[2. Linguistic accuracy] [critical]
Location: `Частина 2: Який відмінок?` (The preposition **по** is used for movement along a surface or a schedule in the Locative: "йти по **вулицях**" (to walk along the streets), "по **суботах**" (on Saturdays).)
Issue: Using `по` + Locative plural to denote a regular schedule (`по суботах`) is a Russian calque ("по субботам"). Standard Ukrainian uses the adverb `щосуботи`. Teaching this as a valid grammar rule is a critical error.
Fix: Remove the reference to "schedule" and the "по суботах" example.

[7. Structural integrity] [minor]
Location: `Підсумок` (The case system is the foundation. 6 to add the flesh of adjectives and verbs of motion to this strong structure!)
Issue: Typo/cut-off sentence at the end of the file. It is missing "Ready for A2.".
Fix: Change "6 to add" to "Ready for A2.6 to add".

## Verdict: REVISE
The module provides a very strong and structurally sound synthesis of the case system. However, it contains two critical linguistic errors (`вушима` taught as standard, `по суботах` taught as a rule), misses two explicit plan points, and has a visible typo at the very end. Applying these specific find/replace fixes will make the module accurate and ready for publication.

<fixes>
- find: "Remember the \"high priority trio\" of irregular plurals: **друг** (friend) becomes **друзі**, **людина** (person) becomes **люди**, and **дитина** (child) becomes **діти**."
  replace: "Remember these irregular plurals: **друг** (friend) becomes **друзі**, **людина** (person) becomes **люди**, **дитина** (child) becomes **діти**, and **око** (eye) becomes **очі**."
- find: "Days of the week take the Accusative: **у четвер** (on Thursday). Hours of the day take the Locative: **о п'ятій годині** (at five o'clock)."
  replace: "Days of the week take the Accusative: **у четвер** (on Thursday). Years and hours take the Locative: **у 2014 році** (in 2014), **о п'ятій годині** (at five o'clock)."
- find: "**очима** (with eyes), **плечима** (with shoulders), **вушима** (with ears)."
  replace: "**очима** (with eyes), **плечима** (with shoulders)."
- find: "movement along a surface or a schedule in the Locative: \"йти по **вулицях**\" (to walk along the streets), \"по **суботах**\" (on Saturdays)."
  replace: "movement along a surface in the Locative: \"йти по **вулицях**\" (to walk along the streets)."
- find: "The case system is the foundation. 6 to add the flesh of adjectives and verbs of motion to this strong structure!"
  replace: "The case system is the foundation. Ready for A2.6 to add the flesh of adjectives and verbs of motion to this strong structure!"
</fixes>
