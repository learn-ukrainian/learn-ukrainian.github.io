## Linguistic Scan
No linguistic errors found (beyond the pedagogical/morphological formula errors noted below).

## Exercise Check
- `<!-- INJECT_ACTIVITY: group-sort-imperative-register -->`: Present and correctly placed after the register explanation.
- `<!-- INJECT_ACTIVITY: fill-in-imperative-formation -->`: Present and correctly placed after formation rules.
- `<!-- INJECT_ACTIVITY: quiz-polite-choice -->`: Present and correctly placed.
- `<!-- INJECT_ACTIVITY: fill-in-contextual-names -->`: Present and correctly placed at the end for contextual practice.
All injected activities match the plan's `activity_hints` in both focus and placement.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All sections from the outline are present, dialogues match the plan situations exactly, word count (1518) exceeds target. |
| 2. Linguistic accuracy | 8/10 | Contradictory grammar formula: `говори + те = говоріть` and `пиши + те = пишіть`. The mathematical equation `и + те = іть` is morphologically false. |
| 3. Pedagogical quality | 8/10 | The explanation "replace the final infinitive ending with -и" is confusing because the previous paragraph defines the infinitive ending strictly as "-ти" (which would lead a learner to erroneously form "говорити" -> "говории"). |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is used in context, but the recommended word `показати` is missing from the module entirely. |
| 5. Exercise quality | 10/10 | All activity markers are perfectly placed directly after the relevant teaching sections. |
| 6. Engagement & tone | 9/10 | Uses mildly gamified/corporate phrasing ("Mastering the наказовий спосіб unlocks your ability..."). |
| 7. Structural integrity | 10/10 | Word count is solid, all headers are correct, no dangling sentences or markdown artifacts. |
| 8. Cultural accuracy | 10/10 | Accurately explains that direct imperatives are normal in Ukrainian and not inherently rude, capturing the cultural communication style perfectly. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural, accurately portraying classroom and friend-to-friend settings with excellent colloquial flow ("Добре, йди, я зараз"). |

## Findings

[Dimension 2] [CRITICAL]
Location: Як утворити? `*   **говори** + **те** = **говоріть** (speak! — formal/plural)`
Issue: Morphologically and mathematically false equation. Adding `-те` to an `-и` ending does not produce `-іть`. This contradicts the rule and teaches a confusing paradigm.
Fix: Change the explanation to explicitly state that the `-и` ending changes to `-іть`, and remove the `+ те` addition notation for these specific verbs.

[Dimension 3] [MAJOR]
Location: Як утворити? "For verbs in Group II, which often end in **-ити**, the process is slightly different. You usually replace the final infinitive ending with **-и**."
Issue: Ambiguous and confusing. The text previously defined the "ending" as `-ти`. Replacing `-ти` with `-и` would create `говории`.
Fix: Clarify that the entire `-ити` or `-іти` ending is replaced with `-и`.

[Dimension 4] [MINOR]
Location: Як утворити? Irregular verbs list.
Issue: The recommended vocabulary word `показати` is missing from the module.
Fix: Add `показати` to the list of essential command verbs to ensure full coverage of the recommended vocabulary.

[Dimension 6] [MINOR]
Location: Підсумок. "Mastering the **наказовий спосіб** unlocks your ability to actively participate in Ukrainian life."
Issue: Uses gamified/corporate language ("unlocks your ability") which is discouraged by the style guide for the teacher persona.
Fix: Replace with "allows you to actively participate".

## Verdict: REVISE
The module contains a critical morphological error in its presentation of the `ви`-form paradigm, a confusing formulation of the Group II conjugation rule, and uses some discouraged gamified phrasing. Applying the exact find/replace fixes will resolve these issues.

<fixes>
- find: |
    There is a universal rule: you simply take the **ти** form and add the suffix **-те**. If the informal form ends in the vowel **-и**, the spelling sometimes shifts slightly to **-іть** to accommodate the stress, but the concept remains exactly the same.

    *   **читай** + **те** = **читайте** (read! — formal/plural)
    *   **говори** + **те** = **говоріть** (speak! — formal/plural)
    *   **дай** + **те** = **дайте** (give! — formal/plural)
    *   **пиши** + **те** = **пишіть** (write! — formal/plural)
  replace: |
    There is a universal rule: you simply take the **ти** form and add the suffix **-те**. If the informal form ends in the vowel **-и**, this ending changes to **-іть** to accommodate the stress.

    *   **читай** + **те** = **читайте** (read! — formal/plural)
    *   **дай** + **те** = **дайте** (give! — formal/plural)
    *   **говори** → **говоріть** (speak! — formal/plural)
    *   **пиши** → **пишіть** (write! — formal/plural)
- find: "For verbs in Group II, which often end in **-ити**, the process is slightly different. You usually replace the final infinitive ending with **-и**."
  replace: "For verbs in Group II, the process is slightly different. You usually replace the entire **-ити** or **-іти** ending with **-и**."
- find: |
    *   **дати** (to give) → **дай** (give!)
    *   **сказати** (to say/tell) → **скажи** (tell!)
    *   **їсти** (to eat) → **їж** (eat!)
  replace: |
    *   **дати** (to give) → **дай** (give!)
    *   **сказати** (to say/tell) → **скажи** (tell!)
    *   **показати** (to show) → **покажи** (show!)
    *   **їсти** (to eat) → **їж** (eat!)
- find: "Mastering the **наказовий спосіб** unlocks your ability to actively participate in Ukrainian life."
  replace: "Mastering the **наказовий спосіб** allows you to actively participate in everyday Ukrainian life."
</fixes>
