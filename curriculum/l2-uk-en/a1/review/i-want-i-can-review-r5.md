## Linguistic Scan
No linguistic errors found.

Key Ukrainian forms used in the module match VESUM paradigms for `хотіти`, `могти`, and `мусити`, and I found no Russian letters (`ы`, `э`, `ё`, `ъ`), Russianisms, Surzhyk, or clear calques in the Ukrainian examples.

## Exercise Check
There are 4 activity markers total, in this order: `fill-in`, `quiz`, `fill-in`, `quiz`.

The main logic problem is placement:
- The first `fill-in` after `## Хотіти (To Want)` fits the contract’s conjugation drill.
- The second marker is `<!-- INJECT_ACTIVITY: quiz -->` immediately after `Хотіти`, but the contract says that quiz is `Хочу, можу, or мушу? Choose the right modal for the situation.` That requires `можу` and `мушу`, which are only taught in `## Могти і мусити (Can and Must)`.
- The remaining two markers after `Могти і мусити` are appropriate for the all-three-modals fill-in and the regular/irregular quiz.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Core beats are covered in prose and dialogue, including `Що ти хочеш робити сьогодні?`, `Я хочу каву`, and `Можу порекомендувати борщ!`, but `Хотіти` omits the contract beat on negative forms and polite-request deferral, and `Могти і мусити` is 266 words against a 270-word minimum. |
| 2. Linguistic accuracy | 9/10 | Ukrainian forms such as `хочу/хочеш/хочуть`, `можу/можеш/можуть`, and `мушу/мусиш/мусять` are correct and verified; no Russian letters or obvious Russianisms/calques appear in the Ukrainian text. |
| 3. Pedagogical quality | 7/10 | The module gives tables and examples, but `Хотіти` skips the planned negative-pattern teaching (`Я не хочу. Ти не хочеш? Вона не хоче.`) and the activity sequence asks for modal choice before all three modals are taught. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary appears naturally in context: `хочеш`, `робити`, `гуляти`, `можу`, `мушу`, `працювати`, `Шкода`, `каву`, `їсти`, `борщ`. |
| 5. Exercise quality | 5/10 | All 4 markers are present, but the second marker is misplaced: the contract’s modal-choice quiz is triggered before `можу` and `мушу` are taught. |
| 6. Engagement & tone | 8/10 | The tone stays instructional and clear, but some framing is abstract rather than classroom-driven, e.g. `People constantly negotiate their time and actions` and `Mastering these verbs provides the grammatical scaffolding...`. |
| 7. Structural integrity | 8/10 | All required H2 headings are present and ordered correctly, and the pipeline word count is 1286, but `## Могти і мусити (Can and Must)` falls below its section minimum. |
| 8. Cultural accuracy | 9/10 | No Russian-centering or cultural distortion; the planning and café examples are ordinary, appropriate Ukrainian-life contexts. |
| 9. Dialogue & conversation quality | 8/10 | The weekend dialogue is natural and functional, and the café dialogue works, but the module leans more on explanatory narration around the dialogues than on lively conversational development. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Хотіти (To Want)` ending with `In English, the word "to" links the two verbs together. In Ukrainian, there is absolutely no linking word. The conjugated modal verb attaches directly to the infinitive action.`  
Issue: The section misses a required contract beat: negative forms (`Я не хочу. Ти не хочеш? Вона не хоче.`) and the note that polite requests with `хотів би / хотіла би` come later.  
Fix: Expand the closing paragraph of the section to include the negative forms and the “polite requests later” boundary.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: after `## Хотіти (To Want)` — `<!-- INJECT_ACTIVITY: quiz -->`  
Issue: The second obligated quiz is the modal-choice quiz (`Хочу, можу, or мушу?`), but this marker appears before `можу` and `мушу` are taught. Learners cannot complete it with module knowledge at that point.  
Fix: Move that quiz marker to after `## Могти і мусити (Can and Must)` so the modal-choice task comes after all three modals are introduced.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Могти і мусити (Can and Must)` ending with `Mastering these verbs gives you the tools to explain your actions. (Note: Ukrainians often use the simpler word **треба** for needs, which we will study later.)`  
Issue: This section is 266 words, below the contract minimum of 270, and it does not clearly deliver the planned beat that `мусити` expresses obligation rather than choice and is stronger than impersonal `треба`.  
Fix: Replace the final note with a short contrast paragraph explaining `мусити` vs `треба`, which also brings the section over the minimum.

## Verdict: REVISE
The module is linguistically solid and structurally recoverable, but it has fixable contract and exercise-sequencing failures. Scores are below the PASS gate, and there are major findings that need deterministic edits.

<fixes>
- find: |
    In English, the word "to" links the two verbs together. In Ukrainian, there is absolutely no linking word. The conjugated modal verb attaches directly to the infinitive action.

    <!-- INJECT_ACTIVITY: fill-in -->
    <!-- INJECT_ACTIVITY: quiz -->
  replace: |
    In English, the word "to" links the two verbs together. In Ukrainian, there is absolutely no linking word. The conjugated modal verb attaches directly to the infinitive action. Negative forms are also simple: **Я не хочу. Ти не хочеш? Вона не хоче.** For polite requests, Ukrainian often uses **хотів би / хотіла би**, but that pattern comes later. For now, **Я хочу...** is the direct A1 way to express a want.

    <!-- INJECT_ACTIVITY: fill-in -->
- find: |
    Mastering these verbs gives you the tools to explain your actions. (Note: Ukrainians often use the simpler word **треба** for needs, which we will study later.)

    <!-- INJECT_ACTIVITY: fill-in -->
    <!-- INJECT_ACTIVITY: quiz -->
  replace: |
    Mastering these verbs gives you the tools to explain your actions. **Мусити** expresses obligation, not choice. It is stronger and more personal than **треба**, which is impersonal and will come later. Compare: **Я мушу працювати** means "I must work," while **треба працювати** states the need more generally.

    <!-- INJECT_ACTIVITY: quiz -->
    <!-- INJECT_ACTIVITY: fill-in -->
    <!-- INJECT_ACTIVITY: quiz -->
</fixes>