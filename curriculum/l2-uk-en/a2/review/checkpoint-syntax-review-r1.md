## Linguistic Scan
- `реченних` is not a valid form; it should be `реченнях`.
- Part 1 teaches an incorrect punctuation rule in multiple places: `Кома ставиться завжди, коли є сполучник`, `Every subordinate clause must be separated by a comma`, and `завжди ставте кому перед підрядним сполучником`. This is false because the comma marks the boundary between clauses, not simply “before the conjunction”.
- The module first labels `який` as a `сполучник` (`...такий як «бо», «щоб» або «який»`), but later correctly calls it `сполучне слово`. That inconsistency teaches the wrong category.

## Exercise Check
- Marker inventory is complete: `group-sort-conjunctions`, `quiz-identify-types`, `fill-in-conjunctions`.
- Marker types match the plan’s three `activity_hints` (`group-sort`, `quiz`, `fill-in`).
- Placement is acceptable: the two Part 1 markers come after identification/error-detection teaching, and the Part 2 marker comes after form-selection teaching.
- No inline DSL exercises are present in the provided markdown, so answer logic and 8-item counts cannot be verified from this text alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All major outline points are present, but the planned references are not integrated: a direct search of the provided module text returns 0 occurrences of `Заболотний`. |
| 2. Linguistic accuracy | 4/10 | Part 1 contains `реченних`, states `Кома ставиться завжди, коли є сполучник`, and first calls `який` a conjunction before later calling it `сполучне слово`. |
| 3. Pedagogical quality | 5/10 | The punctuation explanation teaches a false shortcut (`...перед підрядним сполучником`) instead of clause-boundary logic, so learners are being taught the wrong rule. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose: `тому що`, `бо`, `хоча`, `щоб`, `який`, `якщо`, `сполучник`, `складне речення`; recommended vocabulary also appears in context (`підрядних`, `головне`, `кома`). |
| 5. Exercise quality | 9/10 | The visible marker inventory matches the plan exactly and each marker follows the relevant teaching section; no inline exercise content is visible here to audit answer logic. |
| 6. Engagement & tone | 9/10 | The module keeps a classroom-teacher voice and generally stays encouraging without gamified or corporate language. |
| 7. Structural integrity | 10/10 | All major sections are present and ordered cleanly; the pipeline word count is 1937, so the module is safely above target. |
| 8. Cultural accuracy | 10/10 | No Russian-centric framing or culturally misleading claims appear in the provided text. |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues use named speakers and match the planned scenarios; the teacher/student exchange also covers all five target clause types. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: Part 1 overview — `Ви вже добре вивчили п'ять головних типів... Давайте детально згадаємо їх усі:`  
Issue: The plan cites `Заболотний Grade 5, §28-30` and `Заболотний Grade 6`, but those references are not integrated anywhere in the prose.  
Fix: Add one short sentence here that explicitly ties the review to those textbook references.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Part 1 overview — `Ці частини часто поєднує сполучник, такий як «бо», «щоб» або «який».`  
Issue: `який` is not a conjunction here; it is a `сполучне слово`. The module later uses the correct term, so the explanation is internally inconsistent.  
Fix: Change the sentence to distinguish `сполучники` and `сполучні слова`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Part 1 opening paragraph — `Дуже важливе правило: перед сполучником у таких реченних зазвичай стоїть кома.`  
Issue: `реченних` is an invalid form, and the sentence also teaches an imprecise punctuation rule.  
Fix: Replace it with a sentence that uses `реченнях` and explains that the comma separates the main and subordinate clauses.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Part 1 dialogue/caution/error section — `Кома ставиться завжди, коли є сполучник`; `Every subordinate clause must be separated by a comma`; `Always remember to pause and place a comma before your conjunction!`; `завжди ставте кому перед підрядним сполучником`  
Issue: These statements teach a false absolute rule. In Ukrainian, the comma marks the boundary between clauses; it is not simply “before the conjunction” in all cases.  
Fix: Replace each absolute statement with clause-boundary wording.

## Verdict: REVISE
Critical linguistic/pedagogical errors are present, so this cannot pass. The module is structurally complete and mostly plan-aligned, but dimensions 2 and 3 are below 9 because it teaches wrong punctuation rules and misclassifies `який`.

<fixes>
- find: "Ви вже добре вивчили п'ять головних типів **підрядних частин** (subordinate clauses) у складному реченні на рівні А2. Давайте детально згадаємо їх усі:"
  replace: "Ви вже добре вивчили п'ять головних типів **підрядних частин** (subordinate clauses) у складному реченні на рівні А2. Такий огляд відповідає вправам на складнопідрядні речення в «Заболотний Grade 5, §28-30» і в розділі про складне речення в «Заболотний Grade 6». Давайте детально згадаємо їх усі:"
- find: "Ці частини часто поєднує сполучник, такий як «бо», «щоб» або «який»."
  replace: "Ці частини часто поєднують сполучники або сполучні слова, наприклад «бо», «щоб» або «який»."
- find: "Дуже важливе правило: перед сполучником у таких реченних зазвичай стоїть кома."
  replace: "Дуже важливе правило: підрядну частину в таких реченнях відокремлюємо комою від головної."
- find: "Без коми речення виглядає незавершеним і граматично неправильним."
  replace: "Без коми межа між частинами речення стає нечіткою, і це вважається пунктуаційною помилкою."
- find: "> **Марина:** А, точно! Кома ставиться завжди, коли є **сполучник** (conjunction). Дякую, що помітив!"
  replace: "> **Марина:** А, точно! У **складнопідрядному реченні** (complex sentence) кому ставимо між головною і підрядною частинами. Дякую, що помітив!"
- find: 'In English, you can often drop the comma before conjunctions like "because", "if", or "that". In Ukrainian, this is absolutely forbidden! Every subordinate clause must be separated by a comma. Punctuation in complex sentences is strict, and a missing comma is considered a serious grammatical error. Always remember to pause and place a comma before your conjunction!'
  replace: 'In Ukrainian, subordinate clauses are normally separated from the main clause by a comma. The comma marks the boundary between clauses, so if the subordinate clause comes first, the comma stands after it, not before the conjunction.'
- find: "Ви повинні пам'ятати: завжди ставте кому перед підрядним сполучником, щоб розділити частини речення!"
  replace: "Ви повинні пам'ятати: у складнопідрядному реченні кому ставимо на межі головної й підрядної частин!"
</fixes>