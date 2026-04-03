## Linguistic Scan
No linguistic errors found in terms of Surzhyk, Russianisms, or vocabulary choice. All words verified successfully. (Note: The structural linguistic rules concerning consonant shifts have errors, which are detailed in the findings below).

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-conjugate -->` (Matches plan: fill-in, 10 items, conjugate я/ти/він) - Correctly placed after Group II conjugation explanation.
- `<!-- INJECT_ACTIVITY: group-sort -->` (Matches plan: group-sort, 10 items) - Correctly placed after comparing Group I and II endings.
- `<!-- INJECT_ACTIVITY: quiz-correct-form -->` (Matches plan: quiz, 8 items) - Correctly placed alongside the sorting activity.
- `<!-- INJECT_ACTIVITY: fill-in-sentences -->` (Matches plan: fill-in, 6 items) - Correctly placed at the end of the Summary.
No exercise logic issues. Placements and types align perfectly with the plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The plan explicitly required teaching the "т→ч" consonant shift in the outline. The generated text missed it entirely and hallucinated a "ч→ч" (no change) item to fill the list of four shifts. |
| 2. Linguistic accuracy | 8/10 | The text falsely claims that consonant shifts happen ONLY in the я-form (`Every other form — ти, він/вона, ми, ви, вони — follows the regular pattern perfectly`). This ignores the labial shift (б→бл) which also occurs in the вони-form (`роблять`), contradicting its own conjugation table. |
| 3. Pedagogical quality | 8/10 | Teaching that "no change" (`бачити → бачу`) is a "key shift" is pedagogically confusing and factually nonsensical. The false generalization about `вони` forms avoiding all shifts is also a poor instructional choice. |
| 4. Vocabulary coverage | 10/10 | All required verbs (`говорити`, `бачити`, `робити`, `вчити`, `просити`, `ходити`) are introduced smoothly in context with full conjugations. |
| 5. Exercise quality | 10/10 | All 4 activity markers match the `activity_hints` exactly in type and focus, and are injected at the correct pedagogical moments. |
| 6. Engagement & tone | 10/10 | The module uses excellent, realistic scenarios (language cafe, relaxing at home) to demonstrate the verbs in action without relying on generic enthusiasm or meta-commentary. |
| 7. Structural integrity | 10/10 | Clean Markdown. All H2 headings perfectly match the `content_outline` sections. Word count (1360) is well within acceptable range of the 1200 target. |
| 8. Cultural accuracy | 10/10 | Contexts are natural and culturally appropriate (e.g., "мовне кафе"). |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are multi-turn, realistic, and employ the target grammar effectively and organically (e.g., the quick exchange "Сама? — Ні, я прошу друга..."). |

## Findings

[Plan adherence] [Critical]
Location: `Why do some **я**-forms look unexpected? ... - **ч → ч** (no change): бачити → **бачу**`
Issue: The plan explicitly required teaching the "т→ч" consonant shift. The generated text missed it entirely and hallucinated a "ч→ч (no change)" item to fill the 4-item list. Teaching "no change" as a "key shift" is pedagogically flawed and factually wrong.
Fix: Replace the "ч→ч" bullet point with the missing "т→ч" shift, using "плати́ти (to pay) → плачу́" as the example. Update the summary paragraph to match.

[Linguistic accuracy] [Critical]
Location: `This is the most important thing to remember: these consonant changes happen ONLY in the **я**-form. Every other form — **ти**, **він/вона**, **ми**, **ви**, **вони** — follows the regular pattern perfectly.`
Issue: The text falsely claims that consonant shifts happen ONLY in the я-form. For labial shifts (like б→бл in робити), the shift also occurs in the вони-form (роблять). The text even contradicts its own conjugation table which correctly lists "роблять" right above it.
Fix: Update the explanation to clarify that the -бл- shift also appears in the вони-form, and limit the "ONLY in the я-form" rule to the other shifts.

## Verdict: REVISE
The module is highly engaging and well-structured, but the false linguistic generalization about the `вони` form and the hallucinated `ч→ч` consonant shift represent critical errors in the grammar instruction that must be fixed before publishing.

<fixes>
- find: |-
    Why do some **я**-forms look unexpected? Group II has consonant changes — but only in the **я**-form. Here are the four key shifts:
    - **б → бл**: робити → **роблю**
    - **д → дж**: ходити → **ходжу**
    - **с → ш**: просити → **прошу**
    - **ч → ч** (no change): бачити → **бачу**
    This is the most important thing to remember: these consonant changes happen ONLY in the **я**-form. Every other form — **ти**, **він/вона**, **ми**, **ви**, **вони** — follows the regular pattern perfectly. Practical tip: learn the **я**-form as a separate vocabulary item for each new verb. Once you know it, the rest is automatic.
  replace: |-
    Why do some **я**-forms look unexpected? Group II has consonant changes in the **я**-form. Here are the four key shifts:
    - **б → бл**: робити → **роблю** (also in вони-form: **ро́блять**)
    - **д → дж**: ходити → **ходжу**
    - **с → ш**: просити → **прошу**
    - **т → ч**: плати́ти (to pay) → **плачу́**
    Except for the **-бл-** shift which also appears in the **вони**-form, these changes happen ONLY in the **я**-form. The forms for **ти**, **він/вона**, **ми**, and **ви** follow the regular pattern perfectly. Practical tip: learn the **я**-form as a separate vocabulary item for each new verb. Once you know it, the rest is automatic.
- find: |-
    Consonant changes in Group II appear only in the **я**-form: **роблю** (б→бл), **ходжу** (д→дж), **прошу** (с→ш), **бачу** (ч stays ч).
  replace: |-
    Consonant changes in Group II mostly appear in the **я**-form: **роблю** (б→бл, also **ро́блять**), **ходжу** (д→дж), **прошу** (с→ш), **плачу** (т→ч).
</fixes>
