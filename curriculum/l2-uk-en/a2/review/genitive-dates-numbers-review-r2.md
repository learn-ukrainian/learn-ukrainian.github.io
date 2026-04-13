## Linguistic Scan
[Critical] `Уявіть ситуацію на рецепції готелю.` — `рецепція` is attested Ukrainian, but its dictionary sense is “reception/adoption” in a legal-cultural sense, not a hotel front desk. This is a lexical misuse, not a valid hotel-service term here.

## Exercise Check
Found 3 activity markers:
`quiz-what-s-the-date-drill`
`fill-in-counting-objects-1-2-4-5-rule`
`match-up-accusative-genitive-negation`

Placement is otherwise sensible: each existing marker comes after the section it tests.

Issue found: the plan requires 4 activities, and there is no marker for the `match-up` activity with focus `Q&A about quantities and dates`. That leaves the dates+quantities material without its planned combined practice.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The three planned H2 sections are present, but the opening scene says `Imagine a common situation at a hotel reception. A guest arrives...` instead of the plan’s phone-booking setting. |
| 2. Linguistic accuracy | 6/10 | `Уявіть ситуацію на рецепції готелю.` misuses `рецепція`; dictionary evidence supports a different meaning, not “hotel reception/front desk.” |
| 3. Pedagogical quality | 7/10 | The module gives many examples, but `Сьогодні перше січня. Завтра буде друге лютого. Післязавтра — третє березня.` teaches date forms through an impossible timeline. |
| 4. Vocabulary coverage | 9/10 | Required and recommended plan vocabulary is used in prose: `число`, `місяць`, month names, `заперечення`, `числівник`, `додаток`, `правило`. |
| 5. Exercise quality | 5/10 | Only 3 markers appear, while the plan requires 4; the missing one is the `match-up` activity for `Q&A about quantities and dates`. |
| 6. Engagement & tone | 8/10 | The teacherly voice is consistent, and the month-name and season notes add some substance beyond pure rule listing. |
| 7. Structural integrity | 9/10 | All three planned H2 sections are present and ordered correctly; markdown is clean; total word count is 2974, above target. |
| 8. Cultural accuracy | 9/10 | The module stays Ukrainian-centered, with references such as Taras Shevchenko, Independence Day, and December 25 Christmas. |
| 9. Dialogue & conversation quality | 8/10 | The opening dialogue uses named speakers and a plausible booking context with concrete questions about dates and quantities. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Opening setup — `Уявіть ситуацію на рецепції готелю.`  
Issue: `рецепція` is the wrong word in this context; it does not mean a hotel front desk here.  
Fix: Replace it with a valid hospitality expression such as `стійка реєстрації`, or rewrite the setup as a phone-booking scene.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Opening setup — `Imagine a common situation at a hotel reception. A guest arrives and wants to book a room...`  
Issue: The plan’s dialogue situation is a hotel booking over the phone, but the draft changes it to an in-person arrival scene.  
Fix: Reframe the setup as a phone reservation.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Date examples — `Сьогодні перше січня. Завтра буде друге лютого. Післязавтра — третє березня. Моє улюблене число — двадцять п'яте грудня.`  
Issue: The sequence is factually impossible, and `улюблене число` reads as “favorite number,” not a clean date model.  
Fix: Replace it with neutral example dates that model the form without a false timeline.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: Activity markers — `<!-- INJECT_ACTIVITY: quiz-what-s-the-date-drill -->`, `<!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->`, `<!-- INJECT_ACTIVITY: match-up-accusative-genitive-negation -->`  
Issue: Only 3 markers are present, but the plan requires 4; the `Q&A about quantities and dates` activity is missing.  
Fix: Insert a fourth marker after the counting section and before the negation section.

## Verdict: REVISE
The module has a critical lexical error (`рецепція`), one major plan mismatch in the opening scene, one major pedagogical example problem, and one missing planned exercise marker. Multiple scored dimensions are below 9, so this cannot pass as-is.

<fixes>
- find: |
    Imagine a common situation at a hotel reception. A guest arrives and wants to book a room for a few nights during the busy spring season. Pay attention to how the receptionist asks about specific dates and how the guest responds.

    Уявіть ситуацію на рецепції готелю. Гість хоче забронювати кімнату на кілька днів.

    > *Imagine a situation at a hotel reception. A guest wants to book a room for a few days.*
  replace: |
    Imagine a common situation: a guest is calling a hotel to book rooms for a few nights during the busy spring season. Pay attention to how the administrator asks about specific dates and quantities and how the guest responds.

    Уявіть ситуацію: гість телефонує до готелю й хоче забронювати номер на кілька днів.

    > *Imagine a situation: a guest is calling a hotel and wants to book a room for a few days.*

- find: |
    Сьогодні перше січня. Завтра буде друге лютого. Післязавтра — третє березня. Моє улюблене число — двадцять п'яте грудня.

    > *Today is January 1st. Tomorrow will be February 2nd. The day after tomorrow is March 3rd. My favorite date is December 25th.*
  replace: |
    Ось кілька прикладів дат: перше січня, друге лютого, третє березня, двадцять п'яте грудня.

    > *Here are a few example dates: January 1st, February 2nd, March 3rd, and December 25th.*

- find: "<!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->"
  replace: |
    <!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->
    <!-- INJECT_ACTIVITY: match-up-q-a-about-quantities-and-dates -->
</fixes>