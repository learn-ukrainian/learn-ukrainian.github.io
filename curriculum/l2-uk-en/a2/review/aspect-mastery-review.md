## Linguistic Scan
- Factual grammar error in the formation section: `**казати / сказати**` is presented as a suppletive pair with different roots, but this is a prefixal pair, not a suppletive one.
- Factual grammar error in the same paragraph: `шукати` / `знайти` is treated as an aspect pair. Dictionary data points `знайти` to `знаходити`, not to `шукати`.
- Factual grammar error in Group C: `**класти / покласти**` is called a stem-change pair, but this is a prefixal pair.

## Exercise Check
All 4 planned markers are present and placed after the relevant teaching sections: `group-sort-formation`, `match-up-pairs`, `fill-in-context`, and the final `quiz` marker. They are reasonably spread through the module, and I see no placement/order problems. No inline DSL exercise blocks are present here, so answer-logic quality cannot be audited yet.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Group B duplicates `**казати / сказати**` and therefore the promised “30 pairs” list contains only 29 distinct pairs in the visible prose. |
| 2. Linguistic accuracy | 6/10 | The module misclassifies `**казати / сказати**` as suppletive, treats `шукати ... знайти` as an aspect pair, and calls `**класти / покласти**` a stem-change pair. |
| 3. Pedagogical quality | 7/10 | The core morphology lesson teaches wrong pattern labels in the presentation stage, e.g. `verbs with stem changes, like **класти / покласти**`; that directly undermines the lesson objective. |
| 4. Vocabulary coverage | 8/10 | The plan’s communication list is not fully realized in prose because `**казати / сказати**` appears twice in Group B instead of two distinct pairs. |
| 5. Exercise quality | 9/10 | The 4 markers match the 4 `activity_hints` and each comes after the section it should test. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and clear, with concrete framing such as `The parent asks about the result, while the student emphasizes the unfinished process.` |
| 7. Structural integrity | 9/10 | All planned H2 sections are present and ordered correctly, markers are clean, and the pipeline word count is 2100, which is above target. |
| 8. Cultural accuracy | 9/10 | The module explains Ukrainian on its own terms and avoids Russian-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues use named/role-based speakers and natural aspect contrasts in realistic contexts like homework and workplace planning. |

## Findings
[Linguistic accuracy] [SEVERITY: critical]  
Location: `Finally, the fourth pattern includes verbs that use different roots in the imperfective and perfective... **брати / взяти** ... **казати / сказати** ... Якщо ви довго шукаєте ключі, ви кажете «шукати». Коли процес завершено, ви кажете «знайти».`  
Issue: This paragraph mixes up three things: `казати / сказати` is not suppletive, and `шукати / знайти` is not an aspect pair. That teaches the formation system incorrectly.  
Fix: Replace the paragraph with genuine suppletive examples such as `брати / взяти` and `давати / дати`, and remove `шукати / знайти` from the aspect-pair explanation.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `You must also pay attention to verbs with stem changes, like **класти / покласти** (to put — impf./pf.).`  
Issue: `класти / покласти` is a prefixal pair, not a stem-change pair.  
Fix: Change `stem changes` to `common prefix pairs`.

[Plan adherence] [SEVERITY: major]  
Location: `**казати / сказати** — *to say, to tell*` and later `**казати / сказати** — *to tell, to say*` in Group B  
Issue: The list repeats one pair, so the visible module does not actually present 30 distinct pairs.  
Fix: Replace the second duplicate with a different planned communication pair.

## Verdict: REVISE
Critical morphology errors are present in the main teaching section, so the module cannot ship as-is even though structure, tone, and exercise placement are solid.

<fixes>
- find: |
    Finally, the fourth pattern includes verbs that use different roots in the imperfective and perfective. These suppletive pairs must be memorized. The most crucial examples for daily communication are **брати / взяти** (to take — impf./pf.) and **казати / сказати** (to say — impf./pf.).

    Ці слова виглядають по-різному. Ви не можете утворити їх за правилами. Якщо ви довго шукаєте ключі, ви кажете «шукати». Коли процес завершено, ви кажете «знайти». Те саме працює для дієслів «ловити» та «піймати». Їх треба вивчити напам'ять.

    > *These words look different. You cannot form them by rules. If you look for keys for a long time, you say "to look for". When the process is finished, you say "to have found". The same works for the verbs "to catch" (process) and "to catch" (result). You need to learn them by heart.*
  replace: |
    Finally, the fourth pattern includes verbs that use different roots in the imperfective and perfective. These suppletive pairs must be memorized. The most crucial examples for daily communication are **брати / взяти** (to take — impf./pf.) and **давати / дати** (to give — impf./pf.).

    Ці слова виглядають по-різному. Ви не можете утворити їх за правилами. Наприклад, «брати» та «взяти» мають різні основи. Те саме бачимо в парі «давати» та «дати». Їх треба вивчити напам'ять.

    > *These words look different. You cannot form them by rules. For example, "брати" and "взяти" have different stems. The same is true of "давати" and "дати". You need to learn them by heart.*
- find: "You must also pay attention to verbs with stem changes, like **класти / покласти** (to put — impf./pf.)."
  replace: "You must also pay attention to common prefix pairs, like **класти / покласти** (to put — impf./pf.)."
- find: |
    **вчити / вивчити** — *to learn, to study*
    **розуміти / зрозуміти** — *to understand*
    **казати / сказати** — *to tell, to say*
    **розповідати / розповісти** — *to tell, to narrate*
  replace: |
    **вчити / вивчити** — *to learn, to study*
    **розуміти / зрозуміти** — *to understand*
    **говорити / сказати** — *to speak / to say*
    **розповідати / розповісти** — *to tell, to narrate*
</fixes>