## Linguistic Scan
- Critical grammar error in **Складений майбутній час**: “However, imperfective verbs cannot express the future tense on their own...” is false. Ukrainian imperfective verbs also have a simple future (`писатиму`, `прибиратиму`).
- Critical grammar error in **Як обрати вид для майбутнього**: “«прибиратиму» is just a stylish, one-word variant of «буду прибирати».” This is false. `Прибиратиму` is a standard simple future form of an imperfective verb, not a stylistic flourish.

## Exercise Check
- Marker inventory found: 5 total.
- Correctly placed after relevant teaching: `group-sort-sort-verb-forms-into-two-groups-synthetic-future-perfective-and-analytical-future-imperfective`, `fill-in-complete-sentences-with-the-correct-synthetic-perfective-future-forms-based-on-context`, `unjumble-future-sentences`, `quiz-aspect-choice`.
- Problem: the module adds an extra marker `<!-- INJECT_ACTIVITY: fill-in-future-aspect -->` that is not in the 4 planned `activity_hints`.
- Problem: `<!-- INJECT_ACTIVITY: unjumble-future-sentences --> [unjumble, Reorder words ...]` leaves visible artifact text in the body.
- Placement is otherwise reasonably spread through the module.
- Actual YAML exercise logic is not present here, so only marker placement/inventory can be checked.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2 sections are present and the core contrasts are covered, but the content adds an extra out-of-plan marker: `<!-- INJECT_ACTIVITY: fill-in-future-aspect -->`. |
| 2. Linguistic accuracy | 4/10 | The module states `imperfective verbs cannot express the future tense on their own` and later says `«прибиратиму» is just a stylish, one-word variant of «буду прибирати»`; both claims are factually wrong about Ukrainian grammar. |
| 3. Pedagogical quality | 6/10 | The analytical-future section opens with a long English-first explanation ending in `similar to how English uses "will be" plus an "-ing" verb` before the first Ukrainian example, which is both misleading and poorly sequenced for a grammar lesson. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is integrated naturally in prose and examples: `сказати / скажу`, `написати / напишу`, `зробити / зроблю`, `буду`, `прочитати`, `подзвонити`, `купити`. |
| 5. Exercise quality | 6/10 | Marker placement is mostly sensible, but there are 5 markers for 4 planned activities, including extra `fill-in-future-aspect`, and the unjumble marker has stray visible text after it. |
| 6. Engagement & tone | 6/10 | The teacher voice exists, but filler weakens it: `These verbs are absolutely essential for everyday communication and building relationships` and `This gives you incredible expressive power in Ukrainian...` add hype rather than instruction. |
| 7. Structural integrity | 7/10 | All planned H2 headings are present and the pipeline word count is above target (2308), but `<!-- INJECT_ACTIVITY: unjumble-future-sentences --> [unjumble, Reorder words ...]` leaves a formatting artifact in the published prose. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian on its own terms and uses a plausible Ukrainian context (New Year’s resolutions, exams) without Russia-centered framing. |
| 9. Dialogue & conversation quality | 4/10 | The supposed dialogue is just four isolated declarations (`Олена...`, `Марко...`, `Софія...`, `Максим...`) rather than a multi-turn conversation with reactions or interaction. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Складений майбутній час**, opening paragraph — `However, imperfective verbs cannot express the future tense on their own because their conjugated forms describe the present.`  
Issue: This teaches false grammar. Ukrainian imperfective verbs do have their own future forms (`писатиму`, `читатиму`, `прибиратиму`).  
Fix: Replace the paragraph so it explicitly says this module focuses on `буду + infinitive` without claiming imperfective verbs cannot form future on their own.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Як обрати вид для майбутнього** — `Note that «прибиратиму» is just a stylish, one-word variant of «буду прибирати».`  
Issue: `Прибиратиму` is not a “stylish variant”; it is a standard simple future form of an imperfective verb.  
Fix: Rewrite the note to identify `прибиратиму` as another standard future form and say that this module is focusing on the analytical pattern.

- [PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: **Складений майбутній час**, opening paragraph — `This structure might feel familiar because it is similar to how English uses "will be" plus an "-ing" verb.`  
Issue: The explanation leans on a misleading English analogy and delays Ukrainian examples. That encourages English mapping instead of Ukrainian aspect-based reasoning.  
Fix: Replace the paragraph with a shorter Ukrainian-focused explanation built around `буду / будеш / буде + infinitive` and immediate Ukrainian examples.

- [EXERCISE QUALITY] [SEVERITY: major]  
Location: End of module — `<!-- INJECT_ACTIVITY: fill-in-future-aspect -->`  
Issue: This is an extra exercise marker beyond the 4 planned `activity_hints`, so the activity inventory no longer matches the plan.  
Fix: Remove the extra fill-in marker and keep the planned quiz marker.

- [STRUCTURAL INTEGRITY] [SEVERITY: minor]  
Location: **Складений майбутній час** — `<!-- INJECT_ACTIVITY: unjumble-future-sentences --> [unjumble, Reorder words to form correct future tense sentences using both synthetic (напишу) and analytical (буду писати) forms, 6 items]`  
Issue: The bracketed text is a visible formatting artifact and should not remain in prose.  
Fix: Leave only the HTML marker.

- [ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: **Простий майбутній час** / final grammar box — `These verbs are absolutely essential for everyday communication and building relationships.` and `This gives you incredible expressive power in Ukrainian...`  
Issue: These are inflated filler lines; they add hype instead of usable instruction.  
Fix: Replace them with direct pedagogical language about plans, promises, result vs process.

- [DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: Opening “dialogue” — the four quoted lines beginning `— **Олена:** ...` through `— **Максим:** ...`  
Issue: This is not a real conversation; it is a list of separate declarations with no turn-taking or response.  
Fix: Replace it with a short multi-turn exchange where speakers react to each other while keeping the target future forms.

## Verdict: REVISE
Critical factual grammar errors are present, so this cannot pass. Multiple other dimensions are below 9, and the exercise inventory and dialogue quality also need correction.

<fixes>
- find: |
    Now let's look at the second way to talk about the future in Ukrainian. When we want to describe an action that is ongoing, continuous, or repeated, we must use imperfective verbs. However, imperfective verbs cannot express the future tense on their own because their conjugated forms describe the present. They need a helper word to point to the future. To form the **складений** (compound, analytical) future tense, we combine the conjugated future tense of the helper verb "бути" with the imperfective infinitive of the main verb. This structure might feel familiar because it is similar to how English uses "will be" plus an "-ing" verb. It specifically emphasizes the process, the duration, or the routine of the action.
  replace: |
    Now let's look at the second way to talk about the future in Ukrainian. In this module, we focus on the analytical future of imperfective verbs: **буду / будеш / буде** + infinitive. We use this pattern for ongoing, repeated, or general actions in the future: **буду читати**, **будемо працювати**, **будуть подорожувати**. Unlike the perfective synthetic future, this form highlights the process rather than a completed result.

- find: |
    > — **Олена:** У новому році я обов'язково напишу книгу! *(In the new year, I will definitely write a book!)*
    > — **Марко:** А я вивчу іспанську мову. *(And I will learn Spanish.)*
    > — **Софія:** Мій брат прочитає п'ятдесят книг за рік! *(My brother will read fifty books in a year!)*
    > — **Максим:** А моя сестра нарешті складе важливий іспит. *(And my sister will finally pass an important exam.)*
  replace: |
    > — **Олена:** У новому році я обов'язково напишу книгу! *(In the new year, I will definitely write a book!)*
    > — **Марко:** Серйозно? Тоді я вивчу іспанську мову. *(Seriously? Then I will learn Spanish.)*
    > — **Софія:** Чудовий план! А мій брат прочитає п'ятдесят книг за рік. *(Great plan! And my brother will read fifty books in a year.)*
    > — **Максим:** Ого. А моя сестра нарешті складе важливий іспит. *(Wow. And my sister will finally pass an important exam.)*
    > — **Олена:** Домовилися: наприкінці року ми скажемо, що справді зробили. *(Agreed: at the end of the year we will say what we actually accomplished.)*

- find: |
    For the analytical future, you simply use the helper verb **буду** (I will — auxiliary) with an imperfective infinitive. To guarantee a result, you must know perfective verbs like **прочитати** (to read through — pf.) and **подзвонити** (to call — pf.). You will frequently mix these aspects in daily conversations when making plans, promises, or predictions. A classic question you will hear is «Що ти будеш робити завтра?». This focuses on your general process. The reply often mixes aspects: «Я прибиратиму квартиру, а потім приготую вечерю». Note that «прибиратиму» is just a stylish, one-word variant of «буду прибирати».
  replace: |
    For the analytical future, you simply use the helper verb **буду** (I will — auxiliary) with an imperfective infinitive. To guarantee a result, you must know perfective verbs like **прочитати** (to read through — pf.) and **подзвонити** (to call — pf.). You will frequently mix these aspects in daily conversations when making plans, promises, or predictions. A classic question you will hear is «Що ти будеш робити завтра?». This focuses on your general process. The reply often mixes aspects: «Я прибиратиму квартиру, а потім приготую вечерю». Note that «прибиратиму» is another standard future form of the imperfective verb «прибирати». In this module, we focus on the analytical pattern «буду прибирати».

- find: "<!-- INJECT_ACTIVITY: unjumble-future-sentences --> [unjumble, Reorder words to form correct future tense sentences using both synthetic (напишу) and analytical (буду писати) forms, 6 items]"
  replace: "<!-- INJECT_ACTIVITY: unjumble-future-sentences -->"

- find: |
    <!-- INJECT_ACTIVITY: fill-in-future-aspect -->
    <!-- INJECT_ACTIVITY: quiz-aspect-choice -->
  replace: |
    <!-- INJECT_ACTIVITY: quiz-aspect-choice -->

- find: "These verbs are absolutely essential for everyday communication and building relationships."
  replace: "These verbs are common in everyday plans and promises."

- find: "This gives you incredible expressive power in Ukrainian, letting you highlight nuance that you simply cannot express easily in English."
  replace: "This helps you show whether you mean a finished result or an ongoing process."
</fixes>