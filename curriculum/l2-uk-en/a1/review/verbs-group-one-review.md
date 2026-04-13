## Linguistic Scan
- Factual grammar error in `## Перша дієвідміна (Group I Verbs)`: `You can typically recognize verbs belonging to this group because their dictionary form, or infinitive, ends in **-ати** or **-ювати**.` This is not a reliable way to identify Ukrainian conjugation; school grammar identifies it by personal endings, especially 3rd person plural `-уть/-ють` vs `-ать/-ять`.
- Factual grammar overgeneralization in `## Перша дієвідміна`, `## Я, ти, він/вона`, and `## Підсумок`: `The pattern is always...`, `**я** always takes **-ю**`, `If the subject is **ти**, the verb must end in **-єш**.` These statements teach one subgroup as a universal rule.

## Exercise Check
Markers present: `fill-in-conjugation`, `match-up-person-verb`, `quiz-correct-form`, `fill-in-sentences`.

All 4 markers appear after the relevant teaching blocks and match the 4 `activity_hints` in type/focus. No marker-placement issues found in the prose. No inline DSL exercise logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and all 6 required verbs appear, but pacing is uneven: `## Діалоги` is about 415 words while `## Підсумок` is about 257 against the plan’s 300-per-section target, and the Group I explanation shifts into the inaccurate rule `ends in **-ати** or **-ювати**`. |
| 2. Linguistic accuracy | 6/10 | The module teaches inaccurate grammar claims: `You can typically recognize verbs... because... ends in **-ати** or **-ювати**` and `The pattern is always: stem + **-ю**, **-єш**, **-є**...`. |
| 3. Pedagogical quality | 6/10 | PPP structure is visible, but the module opens with a long English theory preamble (`Language is fundamentally about action...`) before the first Ukrainian example, and a beginner contrast drill uses `подкаст`, which is above A1. |
| 4. Vocabulary coverage | 8/10 | All 6 required verbs are present in prose and examples, but one support example uses `подкаст` instead of simpler in-scope vocabulary already used elsewhere in the module. |
| 5. Exercise quality | 9/10 | The 4 markers match the 4 planned `activity_hints` and are placed after the relevant teaching sections. |
| 6. Engagement & tone | 7/10 | Mostly teacherly, but the summary uses rubric-banned gamified phrasing: `You have now unlocked the ability to describe actions...`. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present, markers are clean, and the pipeline word count is 1451, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | No Russia-centric framing or cultural inaccuracies detected. |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues use named speakers and multi-turn everyday exchanges (`Сашко/Юля`, `Марія/Максим`) rather than isolated prompt-response lines. |

## Findings
- [Linguistic accuracy] [SEVERITY: critical]
  Location: `## Перша дієвідміна (Group I Verbs)` — `You can typically recognize verbs belonging to this group because their dictionary form, or infinitive, ends in **-ати** or **-ювати**.`
  Issue: This teaches the wrong diagnostic. Ukrainian school grammar identifies conjugation by personal endings, especially 3rd person plural `-уть/-ють` vs `-ать/-ять`, not by infinitive ending alone.
  Fix: Replace this sentence with a correct recognition rule based on the present-tense plural form.

- [Linguistic accuracy] [SEVERITY: critical]
  Location: `## Перша дієвідміна`, `## Я, ти, він/вона`, `## Підсумок` — `The pattern is always...`; `**я** always takes **-ю**`; `If the subject is **ти**, the verb must end in **-єш**.`
  Issue: These absolute statements incorrectly present one subgroup of forms as a universal rule. The statements must be scoped to the six model verbs in this module.
  Fix: Change the wording from universal claims to “for the six model verbs in this module...”.

- [Pedagogical quality] [SEVERITY: major]
  Location: `## Діалоги (Dialogues)` opening paragraph — `Language is fundamentally about action, and verbs are the engine that drives every sentence forward...`
  Issue: The lesson spends too long in English meta-explanation before the learner sees any Ukrainian. That weakens PPP pacing and also makes the dialogues section overshoot its planned budget.
  Fix: Replace the opener with 1-2 direct sentences that frame the task and move straight into the dialogue.

- [Pedagogical quality] [SEVERITY: major]
  Location: `## Я, ти, він/вона (Persons)` — `*   **Ти слухаєш podкаст.** *(You listen to a podcast.)*`
  Issue: `подкаст` is B1 in the repo CEFR data, so this example introduces unsupported vocabulary in an A1 form drill.
  Fix: Replace `подкаст` with an A1 noun already used in the module, such as `музику`.

- [Engagement & tone] [SEVERITY: minor]
  Location: `## Підсумок — Summary` — `You have now unlocked the ability to describe actions using the First Conjugation, or **перша дієвідміна**.`
  Issue: `unlocked` is gamified phrasing that the rubric explicitly tells writers to avoid.
  Fix: Replace it with direct teacher language.

## Verdict: REVISE
REVISE. The module is structurally solid and the exercise markers are well placed, but it contains critical grammar-teaching errors about how First Conjugation is identified and how broadly the listed endings apply.

<fixes>
- find: |-
    You can typically recognize verbs belonging to this group because their dictionary form, or infinitive, ends in **-ати** or **-ювати**.
  replace: |-
    A more reliable way to recognize verbs in this conjugation is by the third-person plural form: they take **-уть/-ють** (for example, **читають, знають, працюють, слухають, гуляють, готують**).

- find: |-
    The pattern is always: stem + **-ю**, **-єш**, **-є**, **-ємо**, **-єте**, **-ють**.
  replace: |-
    For the six model verbs in this module, the pattern is: stem + **-ю**, **-єш**, **-є**, **-ємо**, **-єте**, **-ють**.

- find: |-
    *   **я** always takes **-ю**
    *   **ти** always takes **-єш**
    *   **він/вона** always takes **-є**
  replace: |-
    *   In the six model verbs in this module, **я** takes **-ю**
    *   In these same verbs, **ти** takes **-єш**
    *   In these same verbs, **він/вона** takes **-є**

- find: |-
    When building sentences and aiming for clear communication goals, remember that the verb ending must always match the subject performing the action. If the subject is **ти**, the verb must end in **-єш**. If the subject is **вона**, the verb must end in **-є**.
  replace: |-
    When building sentences and aiming for clear communication goals, remember that the verb ending must always match the subject performing the action. In the six model verbs in this module, **ти** takes **-єш** and **вона** takes **-є**.

- find: |-
    Language is fundamentally about action, and verbs are the engine that drives every sentence forward. Until now, you have learned how to name objects, describe their qualities, and express basic locations. Now, it is time to set those objects into motion. In Ukrainian, verbs answer the fundamental question **що робити?** (what to do?). In this module, we are taking a massive step forward by learning how to talk about your daily activities, your routines, and your hobbies. You will learn how to express what you do every day and how to politely ask others about their lives.
  replace: |-
    Verbs let you talk about actions: what you do, what another person does, and what is happening right now. In this module, you will learn the present-tense pattern for six common verbs and use them in short everyday sentences.

- find: |-
    *   **Ти слухаєш подкаст.** *(You listen to a podcast.)*
  replace: |-
    *   **Ти слухаєш музику.** *(You listen to music.)*

- find: |-
    You have now unlocked the ability to describe actions using the First Conjugation, or **перша дієвідміна**.
  replace: |-
    You can now describe simple actions using the First Conjugation, or **перша дієвідміна**.
</fixes>