## Linguistic Scan
Linguistic errors found:
- "набагато більш масивному" (grammatical error: analytical comparative with "набагато" is incorrect/unidiomatic).
- "веселіша за всіх" (stylistically Russian-influenced phrasing; superlative preferred).
- "звертаємо першу увагу на" (awkward, calque-like phrasing).
- "має об'єктивно малий зріст" (awkward word choice for describing height).

## Exercise Check
Found 4 out of 6 required exercise markers:
- `<!-- INJECT_ACTIVITY: match-up-match-portrait-lexis-to-body-categories -->` (Matches plan focus: match портретна лексика to categories)
- `<!-- INJECT_ACTIVITY: quiz-character-valence-identify-character-traits-as-and-choose-the-correct-adjective-for-a-description -->` (Matches plan focus: identify positive/negative traits)
- `<!-- INJECT_ACTIVITY: fill-in-complete-a-portrait-description-by-filling-in-missing-adjectives-and-relationship-terms-in-a-text-about-a-family -->` (Matches plan focus: fill in missing adjectives/terms)
- `<!-- INJECT_ACTIVITY: group-sort-sort-relationship-vocabulary-into-categories -->` (Matches plan focus: sort relationship vocabulary)

Missing markers for:
- `free-write`
- `role-play`
These two activities were incorrectly placed as plain-text bullet points in the "Підсумок" section instead of proper YAML inject markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 4/10 | DEDUCT for: entirely missing the "Опис людини: як писати портрет" section (600 words budgeted) and its associated plan points. |
| 2. Linguistic accuracy | 7/10 | DEDUCT for: unidiomatic comparative "набагато більш масивному", calque-like "веселіша за всіх", awkward "першу увагу", and "малий зріст". |
| 3. Pedagogical quality | 6/10 | DEDUCT for: testing concepts before teaching them. The final summary asks learners to use the "тричастинну структуру шкільного твору-опису", which was completely skipped in the teaching phase. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is well-integrated and explained in context. |
| 5. Exercise quality | 5/10 | DEDUCT for: missing 2 out of 6 planned activity markers (free-write, role-play), which were just written as plain text in the conclusion. |
| 6. Engagement & tone | 9/10 | Tone is encouraging and natural. Good use of cultural examples (Lesya Ukrainka, Shevchenko) to explain character traits. |
| 7. Structural integrity | 4/10 | DEDUCT for: missing H2 heading from plan ("Опис людини: як писати портрет"). DEDUCT for: word count BELOW 4000 (3632 words). |
| 8. Cultural accuracy | 10/10 | Excellent explanation of the conceptual link between рід, родина, народ, and Батьківщина. Precise distinction of in-law terms. |
| 9. Dialogue & conversation quality | 8/10 | Dialogue at the wedding is natural and contextualized, though it uses "веселіша за всіх" instead of a true superlative. |

## Findings
[Plan adherence] [critical]
Location: Entire module structure
Issue: The writer completely skipped the planned 600-word section "Опис людини: як писати портрет", which was supposed to cover portrait composition structure (зачин, основна частина, кінцівка) and artistic devices.
Fix: Rebuild the module to include the missing section.

[Structural integrity] [critical]
Location: Document structure / Word count
Issue: Missing the mandatory H2 heading "Опис людини: як писати портрет", directly causing the word count to fall below the 4000-word target (3632 words).
Fix: Rebuild the module to meet the structural plan and the minimum word count.

[Pedagogical quality] [critical]
Location: "Підсумок: людина у словах" -> "обов'язково використовуючи правильну тричастинну структуру шкільного твору-опису (зачин, основна частина, кінцівка)"
Issue: The summary tests a concept (three-part composition structure) that was never taught in the module because the corresponding section was omitted.
Fix: Teach the composition structure in the body of the module before asking the learner to use it.

[Exercise quality] [major]
Location: Throughout the module
Issue: Missing 2 out of 6 expected exercise markers (free-write, role-play). The writer instead typed these tasks as plain text bullet points in the "Підсумок" section.
Fix: Inject all 6 `<!-- INJECT_ACTIVITY: ... -->` markers as specified in the plan.

[Linguistic accuracy] [critical]
Location: "набагато більш масивному типу."
Issue: Grammatical error. When modifying an adjective with "набагато", Ukrainian grammar strictly requires the simple (synthetic) comparative degree (набагато масивнішому), not the analytical one (набагато більш масивному).
Fix: Change to "набагато масивнішому типу."

[Linguistic accuracy] [major]
Location: "Вона в нас найенергійніша і завжди веселіша за всіх!"
Issue: "Веселіша за всіх" is a grammatically possible but stylistically Russian-influenced construction ("веселее всех"). The natural Ukrainian superlative is "найвеселіша з усіх".
Fix: Change to "завжди найвеселіша з усіх!"

[Linguistic accuracy] [minor]
Location: "ми найчастіше звертаємо першу увагу на вік"
Issue: "Звертати першу увагу" is an awkward phrasing that borders on a calque ("обращать первое внимание"). "Насамперед звертати увагу" is the idiomatic standard.
Fix: Change to "ми насамперед звертаємо увагу на вік"

[Linguistic accuracy] [minor]
Location: "людина має об'єктивно малий зріст,"
Issue: "Малий зріст" is less idiomatic than "невисокий зріст" when describing people.
Fix: Change to "людина має об'єктивно невисокий зріст,"

## Verdict: REJECT
Fundamental structural and pedagogical problems. The writer entirely skipped a critical 600-word section ("Опис людини: як писати портрет"), missed the word count target, failed to inject 2 out of 6 required exercise markers, and pedagogically failed by testing learners on a composition structure that was never taught. A full rebuild is required.

<fixes>
- find: "набагато більш масивному типу."
  replace: "набагато масивнішому типу."
- find: "завжди веселіша за всіх!"
  replace: "завжди найвеселіша з усіх!"
- find: "звертаємо першу увагу на вік"
  replace: "насамперед звертаємо увагу на вік"
- find: "людина має об'єктивно малий зріст,"
  replace: "людина має об'єктивно невисокий зріст,"
</fixes>