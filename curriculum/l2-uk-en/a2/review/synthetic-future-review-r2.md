## Linguistic Scan
No Russianisms, Surzhyk, paronym misuse, or forbidden Russian characters found.

Factual grammar errors found:
- `However, Ukrainian grammar has two distinct ways to form the **майбутній час** (future tense).` This is incorrect. Repo textbook search (`§97 Майбутній час дієслів`) shows imperfective verbs have both simple and compound future (`писатиму`, `буду писати`). The module later contradicts itself with `«прибиратиму» is another standard future form`.
- `If you want to say what you will be doing for a whole day, or what your general routine will be next month, you must use this specific form.` This wrongly presents the analytical future as mandatory; the simple imperfective future is also standard.

## Exercise Check
- Marker inventory: 4/4 plan activities are present.
- `group-sort` is placed after the overview and is broadly aligned.
- `unjumble` appears after the analytical future section and is aligned.
- `quiz-aspect-choice` appears after the aspect-choice section and is aligned.
- `fill-in-complete-sentences-with-the-correct-synthetic-perfective-future-forms-based-on-context` is misaligned twice: it appears before `## Складений майбутній час`, and its ID narrows the task to synthetic perfective only, while the plan requires choosing between synthetic and analytical future based on context.
- Markers are otherwise reasonably spread through the module.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All four planned H2 sections exist, but the fill-in marker `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-synthetic-perfective-future-forms-based-on-context -->` appears before `## Складений майбутній час` and no exact plan reference titles appear in the prose. |
| 2. Linguistic accuracy | 4/10 | `Ukrainian grammar has two distinct ways...` and `you must use this specific form` are factually wrong; later the module itself says `«прибиратиму» is another standard future form`. |
| 3. Pedagogical quality | 6/10 | The module gives many examples, but it teaches an over-simplified rule first and only repairs it later with `«прибиратиму» is another standard future form`, which is confusing for A2 learners. |
| 4. Vocabulary coverage | 9/10 | Required items such as `сказати / скажу`, `написати / напишу`, `зробити / зроблю`, `буду`, `прочитати`, `подзвонити`, and `купити` all appear in prose and examples. |
| 5. Exercise quality | 6/10 | Marker count matches the plan, but the fill-in activity is placed before learners have studied the analytical future and its ID no longer matches the plan’s contrastive brief. |
| 6. Engagement & tone | 9/10 | The New Year frame is concrete and teacherly, e.g. `У новому році я обов'язково напишу книгу!`, without gamified fluff. |
| 7. Structural integrity | 9/10 | All four H2 headings are present and ordered correctly; total word count is `2277`, above target, with no dangling sections. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian on its own terms and uses a plausible local situation rather than Russian comparison framing. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers help, but the opening exchange is mostly serial declarations: `...я обов'язково напишу книгу!`, `...я вивчу іспанську мову`, `...мій брат прочитає...` with limited back-and-forth. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `However, Ukrainian grammar has two distinct ways to form the **майбутній час** (future tense).`  
Issue: This teaches a false rule. Ukrainian also has the simple future of imperfective verbs (`писатиму`, `прибиратиму`).  
Fix: Reframe this as the scope of the module: it focuses on two high-frequency patterns, not the whole future-tense system.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `If you want to say what you will be doing for a whole day, or what your general routine will be next month, you must use this specific form.`  
Issue: This wrongly makes the analytical future obligatory for ongoing/habitual future meaning.  
Fix: Change `must use` to wording that presents it as one common option.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: opening explanation in `## Два майбутніх часи`; searches for `Заболотний`, `Ukrainian Future Tense`, and `ukrainianlessons` returned 0 occurrences.  
Issue: The planned references are not integrated into the prose at all.  
Fix: Add one brief sentence tying the explanation to `Заболотний Grade 6, §47-48` and `ULP: Ukrainian Future Tense`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-synthetic-perfective-future-forms-based-on-context -->`  
Issue: The fill-in exercise comes before the analytical future is taught, and the marker ID no longer matches the plan’s contrastive focus.  
Fix: Move the fill-in marker to after both futures have been taught and rename it so it covers synthetic perfective or analytical imperfective based on context.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: minor]  
Location: `— **Софія:** Чудовий план! А мій брат прочитає п'ятдесят книг за рік.`  
Issue: The dialogue is mostly a list of announcements rather than an actual exchange.  
Fix: Add a short follow-up question or reaction to another speaker’s plan.

## Verdict: REVISE
REVISE. The module has critical factual grammar errors about Ukrainian future formation, plus a major exercise-placement mismatch. Several dimensions are below 9, and the identified errors require fixes before shipping.

<fixes>
- find: "However, Ukrainian grammar has two distinct ways to form the **майбутній час** (future tense). The choice between these two forms has absolutely nothing to do with formality or style. Instead, it is entirely about the aspect of the verb."
  replace: "However, this module focuses on two high-frequency future patterns in Ukrainian: the perfective synthetic future and the imperfective analytical future. The choice between these patterns has nothing to do with formality or style. Instead, it depends on aspect and on whether you present the action as a completed result or as a process. This is the contrast emphasized in **Заболотний Grade 6, §47-48** and **ULP: Ukrainian Future Tense**."
- find: "If you want to say what you will be doing for a whole day, or what your general routine will be next month, you must use this specific form."
  replace: "If you want to highlight what you will be doing for a whole day, or what your general routine will be next month, this is one common form to use."
- find: "<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-synthetic-perfective-future-forms-based-on-context -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz-aspect-choice -->"
  replace: |
    <!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-future-form-synthetic-perfective-or-analytical-imperfective-based-on-context -->

    <!-- INJECT_ACTIVITY: quiz-aspect-choice -->
- find: "> — **Софія:** Чудовий план! А мій брат прочитає п'ятдесят книг за рік. *(Great plan! And my brother will read fifty books in a year.)*"
  replace: "> — **Софія:** Чудовий план! А скільки сторінок ти будеш писати щодня? Мій брат прочитає п'ятдесят книг за рік. *(Great plan! And how many pages will you be writing each day? My brother will read fifty books in a year.)*"
</fixes>