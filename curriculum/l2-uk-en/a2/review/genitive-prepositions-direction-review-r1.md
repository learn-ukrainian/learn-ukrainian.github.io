## Linguistic Scan
Found a critical paronym error ("після вечора" instead of "після вечері") and a calque ("музею мистецтва" instead of "художнього музею").

## Exercise Check
Found 5 `INJECT_ACTIVITY` markers instead of the 4 requested in the plan. The requested items count was 12 instead of 8.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The dialogue is missing the specific phrase "Чекайте до п'ятої години" requested in the plan's `dialogue_situations`. |
| 2. Linguistic accuracy | 6/10 | Critical errors found: "Після вечора ми будемо спокійно відпочивати вдома" (paronym error) and "Студенти йдуть до музею мистецтва" (calque). |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow; clearly explains hard/soft stem changes with the Genitive case and offers ample natural examples. |
| 4. Vocabulary coverage | 7/10 | Required words "напрямок" and "мета" only appear as English-translated labels in the final summary list, never in a natural Ukrainian sentence. |
| 5. Exercise quality | 7/10 | The text contains 5 activity markers requesting 12 items each, directly violating the plan's specification of 4 activities with 8 items each. |
| 6. Engagement & tone | 9/10 | Good use of natural dialogue contexts (e.g., giving directions to a taxi driver). |
| 7. Structural integrity | 8/10 | The deterministic word count is 3428 words, which significantly exceeds the target of 2000 words. |
| 8. Cultural accuracy | 10/10 | Uses accurate Ukrainian city names and typical cultural situations appropriately. |
| 9. Dialogue & conversation quality | 9/10 | The taxi driver dialogue is natural and provides a realistic scenario for using directional grammar. |

## Findings

[Plan Adherence] [major]
Location: "> — **Пасажир:** А потім до готелю «Дніпро»."
Issue: The dialogue misses the explicit phrase "Чекайте до п'ятої години" which was required by the plan's `dialogue_situations`.
Fix: Add the sentence to the passenger's dialogue line.

[Linguistic Accuracy] [critical]
Location: "— Після вечора ми будемо спокійно відпочивати вдома. *(After evening we will calmly rest at home.)*"
Issue: Paronym error. "Після вечора" is an unnatural, literal translation of "after the evening". The standard expression is "після вечері" (after dinner).
Fix: Replace "вечора" with "вечері" and "evening" with "dinner".

[Linguistic Accuracy] [critical]
Location: "— Студенти йдуть до музею мистецтва. *(The students are going to the art museum.)*"
Issue: Calque error. "Музею мистецтва" is a literal translation. The correct standard Ukrainian term is "художнього музею".
Fix: Replace "музею мистецтва" with "художнього музею".

[Vocabulary Coverage] [major]
Location: "«Читаємо українською»:\n— Я йду до парку. *(I am walking to the park.)*" and "«Читаємо українською» *(Reading in Ukrainian)*:\n— Студенти вже добре готові до екзамену. *(The students are already well ready for the exam.)*"
Issue: The required vocabulary words "напрямок" and "мета" were only used as summary headings, not naturally in the prose.
Fix: Add contextual sentences using "напрямок" and "мета" into the reading blocks.

[Exercise Quality] [major]
Location: The `<!-- INJECT_ACTIVITY -->` markers at the end of each section.
Issue: The generator created 5 activity markers with 12 items each, contradicting the plan's request for exactly 4 markers with 8 items each.
Fix: Remove the redundant first fill-in marker, and update the remaining markers to request 8 items.

## Verdict: REVISE
The module contains critical linguistic errors (a paronym and a calque) and fails to adhere to several key instructions in the plan (missing dialogue phrase, incorrect activity marker count, missing vocabulary). It must be revised before publishing.

<fixes>
- find: "> — **Пасажир:** А потім до готелю «Дніпро»."
  replace: "> — **Пасажир:** Чекайте до п'ятої години. А потім до готелю «Дніпро»."
- find: "— Після вечора ми будемо спокійно відпочивати вдома. *(After evening we will calmly rest at home.)*"
  replace: "— Після вечері ми будемо спокійно відпочивати вдома. *(After dinner we will calmly rest at home.)*"
- find: "— Студенти йдуть до музею мистецтва. *(The students are going to the art museum.)*"
  replace: "— Студенти йдуть до художнього музею. *(The students are going to the art museum.)*"
- find: "«Читаємо українською»:\n— Я йду до парку. *(I am walking to the park.)*"
  replace: "«Читаємо українською»:\n— Який це напрямок? *(Which direction is this?)*\n— Я йду до парку. *(I am walking to the park.)*"
- find: "«Читаємо українською» *(Reading in Ukrainian)*:\n— Студенти вже добре готові до екзамену. *(The students are already well ready for the exam.)*"
  replace: "«Читаємо українською» *(Reading in Ukrainian)*:\n— Яка мета вашої подорожі? *(What is the purpose of your trip?)*\n— Студенти вже добре готові до екзамену. *(The students are already well ready for the exam.)*"
- find: "<!-- INJECT_ACTIVITY: fill-in, 12 sentences with до + Genitive for direction -->\n\n## До якого часу? До + родовий для часу (Until When? До + Genitive for Time)"
  replace: "## До якого часу? До + родовий для часу (Until When? До + Genitive for Time)"
- find: "<!-- INJECT_ACTIVITY: fill-in, 12 sentences with до + Genitive for time limits and deadlines -->\n\n## До + родовий: решта значень та узагальнення (До + Genitive: Other Meanings and Summary)"
  replace: "<!-- INJECT_ACTIVITY: fill-in, 8 sentences with до + Genitive for time limits and deadlines -->\n\n## До + родовий: решта значень та узагальнення (До + Genitive: Other Meanings and Summary)"
- find: "<!-- INJECT_ACTIVITY: match-up, Match 12 до-phrases with their specific function (Direction, Time Limit, Purpose, Relation) -->\n\n<!-- INJECT_ACTIVITY: quiz, Choose the correct meaning of до in 12 contextual sentences -->\n\n<!-- INJECT_ACTIVITY: group-sort, Sort 12 phrases into categories: Direction vs. Time vs. Abstract/Purpose -->"
  replace: "<!-- INJECT_ACTIVITY: match-up, Match 8 до-phrases with their specific function (Direction, Time Limit, Purpose, Relation) -->\n\n<!-- INJECT_ACTIVITY: quiz, Choose the correct meaning of до in 8 contextual sentences -->\n\n<!-- INJECT_ACTIVITY: group-sort, Sort 8 phrases into categories: Direction vs. Time vs. Abstract/Purpose -->"
</fixes>
