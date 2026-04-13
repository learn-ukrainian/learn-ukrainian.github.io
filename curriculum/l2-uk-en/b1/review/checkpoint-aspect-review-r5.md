## Linguistic Scan
No linguistic errors found (minor stylistic calque with "задача" reported below).

## Exercise Check
- `quiz-aspect-identification`: Correctly placed after Section 1 (tests past tense aspect).
- `fill-in-past-aspect`: Incorrectly placed after Section 1. The plan hint indicates this exercise covers multiple contexts (past, future, imperative, negation). It must be moved to the end of the module.
- `group-sort-future-imperative`: Correctly placed after Section 2. Tests past vs imperative contexts.
- `error-correction-imperative`: Incorrectly placed after Section 2. The plan hint indicates this exercise covers negation, which hasn't been taught yet. Must be moved to after Section 3.
- `match-up-negation-meaning`: Correctly placed after Section 3 (Negation).
- `open-writing-aspect-check`: Correctly placed at the end.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Covers all requested vocabulary and topics, but the textbook references from the plan (Литвінова Grade 7, Заболотний Grade 7, Авраменко Grade 7) are never cited or mentioned. |
| 2. Linguistic accuracy | 9/10 | Generally pristine Ukrainian. However, uses "вирішення конкретної задачі" instead of "виконання конкретного завдання" for a general task (a slight semantic calque/Russianism, as "задача" is strictly mathematical). |
| 3. Pedagogical quality | 7/10 | Excellent contrastive explanations, but deductions applied for >100 words of English theory without a Ukrainian example in two paragraphs (Section 2 intro and Section 4 intro). |
| 4. Vocabulary coverage | 10/10 | Beautifully integrated, including all mandatory and recommended terms ("тло розповіді", "подієвий ланцюг", etc). |
| 5. Exercise quality | 6/10 | The markers `fill-in-past-aspect` and `error-correction-imperative` test concepts (negation, future, etc.) that have not yet been taught at the point they are injected. |
| 6. Engagement & tone | 7/10 | Deductions for a self-congratulatory opener ("Welcome to the first major checkpoint of the B1 level. Reaching this stage means you have already encountered...") and gamified language ("five major linguistic battlegrounds"). |
| 7. Structural integrity | 10/10 | 5392 words (well above the 4000 target). Excellent use of informational blocks and translation formatting. |
| 8. Cultural accuracy | 10/10 | Decolonized approach. Explicitly addresses cultural nuance in imperatives (using imperfective for hospitality). |
| 9. Dialogue & conversation quality | 9/10 | Contextually relevant academic dialogue that naturally highlights aspect differences in a realistic scenario. |

## Findings
[1. Plan adherence] [major]
Location: Entire document.
Issue: Plan references (Литвінова Grade 7, Заболотний Grade 7, Авраменко Grade 7) are omitted from the module.
Fix: Append a reference attribution note at the very end of the module.

[2. Linguistic accuracy] [major]
Location: Section 2: "але не обіцяєте миттєвого вирішення конкретної задачі."
Issue: "Задача" is primarily a mathematical or logical problem in Ukrainian. Using it to mean "a specific task" is a common semantic Russianism. The proper term is "завдання".
Fix: Replace "вирішення конкретної задачі" with "виконання конкретного завдання".

[3. Pedagogical quality] [major]
Location: Section 2 paragraph ("Understanding the future tense...") and Section 4 paragraph ("The conditional mood in Ukrainian...").
Issue: Both paragraphs exceed 100 words of purely English theory without offering a single grounding Ukrainian example.
Fix: Add short Ukrainian example translations to the end of both paragraphs to ground the concepts immediately.

[5. Exercise quality] [critical]
Location: `<!-- INJECT_ACTIVITY: fill-in-past-aspect -->` and `<!-- INJECT_ACTIVITY: error-correction-imperative -->`
Issue: `fill-in-past-aspect` tests all contexts but is injected before future/negation are taught. `error-correction-imperative` tests negation but is injected before negation is taught.
Fix: Relocate `fill-in-past-aspect` to the very end of the module. Relocate `error-correction-imperative` to after Section 3.

[6. Engagement & tone] [major]
Location: Opening paragraph ("Welcome to the first major checkpoint...") and summary section ("across five major linguistic battlegrounds").
Issue: Violates strict tone rules against self-congratulatory openers and gamified language.
Fix: Delete the congratulatory opener and replace "battleground(s)" with "context(s)".

## Verdict: REVISE
The module delivers rich, highly detailed grammar explanations with excellent contextual examples. However, it requires a revision to correct the injection placement of exercise markers, remove the forbidden gamified/congratulatory language, fix the semantic calque ("задача"), and add missing textbook citations.

<fixes>
- find: "Welcome to the first major checkpoint of the B1 level. Reaching this stage means you have already encountered the most crucial and challenging feature of the Ukrainian verb system: aspect. At the B1 level, choosing between"
  replace: "At the B1 level, choosing between"
- find: "across five major linguistic battlegrounds. Let's analyze each one to solidify your understanding and ensure you are ready for advanced communication.\n\nThe first battleground is"
  replace: "across five major linguistic contexts. Let's analyze each one to solidify your understanding.\n\nThe first context is"
- find: "The second battleground involves"
  replace: "The second context involves"
- find: "The third battleground is"
  replace: "The third context is"
- find: "The fourth battleground is"
  replace: "The fourth context is"
- find: "Finally, the fifth battleground is"
  replace: "Finally, the fifth context is"
- find: "вирішення конкретної задачі."
  replace: "виконання конкретного завдання."
- find: "If you do not clarify your intention, you risk sounding unnatural or miscommunicating your actual plans."
  replace: "If you do not clarify your intention, you risk sounding unnatural or miscommunicating your actual plans. For example, translating 'I will read' requires choosing between the process (**я буду читати**) and the result (**я прочитаю**)."
- find: "It represents a sudden change or a completed achievement that triggers another event."
  replace: "It represents a sudden change or a completed achievement that triggers another event. For instance, compare the continuous state in **якби я читав** (if I were reading) to the completed jump in **якби я прочитав** (if I had finished reading)."
- find: "<!-- INJECT_ACTIVITY: quiz-aspect-identification -->\n<!-- INJECT_ACTIVITY: fill-in-past-aspect -->"
  replace: "<!-- INJECT_ACTIVITY: quiz-aspect-identification -->"
- find: "<!-- INJECT_ACTIVITY: group-sort-future-imperative -->\n<!-- INJECT_ACTIVITY: error-correction-imperative -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort-future-imperative -->"
- find: "<!-- INJECT_ACTIVITY: match-up-negation-meaning -->\n\n## Вид в умовному способі та підсумок"
  replace: "<!-- INJECT_ACTIVITY: match-up-negation-meaning -->\n<!-- INJECT_ACTIVITY: error-correction-imperative -->\n\n## Вид в умовному способі та підсумок"
- find: "> *4. Make 2 conditional sentences with different verb aspects.*\n\n<!-- INJECT_ACTIVITY: open-writing-aspect-check -->"
  replace: "> *4. Make 2 conditional sentences with different verb aspects.*\n\n*(За матеріалами: Литвінова Grade 7, Заболотний Grade 7, Авраменко Grade 7)*\n\n<!-- INJECT_ACTIVITY: fill-in-past-aspect -->\n<!-- INJECT_ACTIVITY: open-writing-aspect-check -->"
</fixes>