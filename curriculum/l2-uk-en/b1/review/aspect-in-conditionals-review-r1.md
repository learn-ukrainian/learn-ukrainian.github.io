## Linguistic Scan
2 errors found:
- Hallucinated Bengali text "ভাবনা" inserted into the word "конкретний".
- "безкінечно" is a non-standard variant (flagged as missing by VESUM in this context); "нескінченно" is the proper Ukrainian literary form.

## Exercise Check
6 activity markers present:
- `<!-- INJECT_ACTIVITY: quiz-real-vs-unreal -->` (Matches quiz)
- `<!-- INJECT_ACTIVITY: fill-in-real-conditionals -->` (Matches fill-in)
- `<!-- INJECT_ACTIVITY: sort-aspect-unreal -->` (Matches group-sort)
- `<!-- INJECT_ACTIVITY: error-correction-conditionals -->` (Matches error-correction)
- `<!-- INJECT_ACTIVITY: matching-scenarios -->` (Matches match-up)
- `<!-- INJECT_ACTIVITY: open-writing-dreams-plans -->` (Matches open-writing)
All markers match the plan's `activity_hints` types, counts, and are logically placed after their respective theoretical explanations.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Covers all 4 main sections, hits all plan points, uses the dialogue situations properly. Word count is an excellent 5063. |
| 2. Linguistic accuracy | 7/10 | Very good overall, but contains a severe AI hallucination (`конкре ভাবনা швидкий результат`) and a non-standard word `безкінечно`. |
| 3. Pedagogical quality | 10/10 | Excellent explanations. Beautifully explains "якщо + доконаний" vs "якщо + недоконаний" (process vs result). |
| 4. Vocabulary coverage | 9/10 | Covers almost all plan vocabulary, though a few are injected too literally with their prompt translations. |
| 5. Exercise quality | 10/10 | Appropriate use of inject markers corresponding to all `activity_hints` in the plan. |
| 6. Engagement & tone | 10/10 | Engaging, teacher-like tone. Uses metaphors (the camera lens) effectively without being overly casual. |
| 7. Structural integrity | 6/10 | Multiple instances of robotic prompt leakage where English meta-notes from the plan's vocabulary hints were copy-pasted directly into the prose (e.g., `*(impossibility (unreal conditionals imply this))*`). |
| 8. Cultural accuracy | 10/10 | Appropriate cultural context and examples (Lviv coffee, Carpathians). |
| 9. Dialogue & conversation quality | 10/10 | The dialogue between Natalia and Bohdan is natural and perfectly contrasts real vs. unreal conditional forms. |

## Findings
[2. Linguistic accuracy] [Critical]
Location: `чи ви чекаєте на конкре ভাবনা швидкий результат.`
Issue: AI hallucination inserted Bengali text (ভাবনা) into the middle of the Ukrainian word "конкретний".
Fix: Replace `на конкре ভাবনা швидкий результат.` with `на конкретний швидкий результат.`

[7. Structural integrity] [Major]
Location: `**неможливість** *(impossibility (unreal conditionals imply this))* або нереальна умова`
Issue: Literal injection of the plan's translation hint metadata breaks immersion and reads like prompt leakage.
Fix: Replace `**неможливість** *(impossibility (unreal conditionals imply this))* або нереальна умова` with `**неможливість** *(impossibility)* або нереальна умова`

[7. Structural integrity] [Major]
Location: `ваша мета — **виграти** *(to win (pf — Якби я виграв...))* у лотерею.`
Issue: Literal injection of the plan's translation hint metadata.
Fix: Replace `**виграти** *(to win (pf — Якби я виграв...))* у лотерею.` with `**виграти** *(to win)* у лотерею.`

[7. Structural integrity] [Major]
Location: `«Якби я **народився** *(to be born - pf)* видатним художником`
Issue: Literal injection of the plan's translation hint metadata.
Fix: Replace `**народився** *(to be born - pf)* видатним художником` with `**народився** *(to be born)* видатним художником`

[7. Structural integrity] [Major]
Location: `Ви точно знаєте, як це — **вміти** *(to know how to, to be able to (impf))* професійно використовувати`
Issue: Literal injection of the plan's translation hint metadata.
Fix: Replace `**вміти** *(to know how to, to be able to (impf))* професійно використовувати` with `**вміти** *(to know how to)* професійно використовувати`

[7. Structural integrity] [Major]
Location: `чи маю я достатньо уважності, щоб **змогти** *(to manage to, to be able (pf — specific occasion))* в майбутньому уникати`
Issue: Literal injection of the plan's translation hint metadata.
Fix: Replace `**змогти** *(to manage to, to be able (pf — specific occasion))* в майбутньому` with `**змогти** *(to be able)* в майбутньому`

[7. Structural integrity] [Major]
Location: `Ви можете довго **уявляти** *(to imagine - impf)* приємний тривалий процес`
Issue: Literal injection of the plan's translation hint metadata.
Fix: Replace `**уявляти** *(to imagine - impf)* приємний тривалий процес` with `**уявляти** *(to imagine)* приємний тривалий процес`

[2. Linguistic accuracy] [Minor]
Location: `Ви можете безкінечно додавати нові деталі`
Issue: The word "безкінечно" is flagged by VESUM; "нескінченно" is the standard literary form.
Fix: Replace `безкінечно` with `нескінченно`

## Verdict: REVISE
The module content is pedagogically excellent and meets the word count perfectly. However, there is a critical AI hallucination (Bengali characters) and multiple major instances of robotic prompt leakage where English translation notes were injected directly into the prose. These must be fixed before publishing.

<fixes>
- find: "чи ви чекаєте на конкре ভাবনা швидкий результат."
  replace: "чи ви чекаєте на конкретний швидкий результат."
- find: "**неможливість** *(impossibility (unreal conditionals imply this))* або нереальна умова"
  replace: "**неможливість** *(impossibility)* або нереальна умова"
- find: "**виграти** *(to win (pf — Якби я виграв...))* у лотерею."
  replace: "**виграти** *(to win)* у лотерею."
- find: "**народився** *(to be born - pf)* видатним художником"
  replace: "**народився** *(to be born)* видатним художником"
- find: "**вміти** *(to know how to, to be able to (impf))* професійно використовувати"
  replace: "**вміти** *(to know how to)* професійно використовувати"
- find: "**змогти** *(to manage to, to be able (pf — specific occasion))* в майбутньому"
  replace: "**змогти** *(to be able)* в майбутньому"
- find: "**уявляти** *(to imagine - impf)* приємний тривалий процес"
  replace: "**уявляти** *(to imagine)* приємний тривалий процес"
- find: "Ви можете безкінечно додавати нові деталі"
  replace: "Ви можете нескінченно додавати нові деталі"
</fixes>
