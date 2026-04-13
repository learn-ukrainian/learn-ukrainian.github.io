## Linguistic Scan
No linguistic errors found.

## Exercise Check
Markers present:
- `quiz-given-a-sentence-identify-whether-the-verb-is-imperfective-or-perfective-and-explain-why` after section 1
- `match-up-match-signal-words-with-the-correct-aspect-and-example-sentence` after section 3
- `fill-in-aspect-choice` and `error-correction-aspect` both after section 4

Issues:
- The marker types cover all four `activity_hints` from the plan.
- Placement is uneven: `## Коли вживати недоконаний вид` has no immediate exercise marker, while `fill-in` and `error-correction` are clustered at the end.
- The `fill-in` task is the best fit for the imperfective/perfective context-clue teaching in section 2 and should appear there, not only after the final section.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The module explicitly teaches only five aspect pairs: `писати / написати`, `читати / прочитати`, `готувати / приготувати`, `робити / зробити`, `вчити / вивчити`. The recommended word `тривалість` does not appear, and search confirms no citation of `Заболотний`, `ULP`, or `ukrainianlessons.com`. |
| 2. Linguistic accuracy | 9/10 | No Russianisms, Surzhyk, calques, or wrong Ukrainian forms were confirmed. The only issue is register: `готовий до відправки` is colloquial in otherwise standard teaching prose; `до відправлення` is cleaner. |
| 3. Pedagogical quality | 9/10 | The PPP arc is clear: dialogue in section 1, rule explanation in sections 2-3, and contrastive practice/decision flowchart in section 4. Examples like `Коли я готував вечерю, раптом погасло світло` correctly model background vs. foreground. |
| 4. Vocabulary coverage | 8/10 | All required vocabulary appears naturally in prose, including `минулий час`, `процес`, `результат`, `довго`, and `раптом`. Recommended `щодня`, `нарешті`, and `одного разу` appear, but `тривалість` is missing. |
| 5. Exercise quality | 7/10 | All four planned activity types are represented by markers, but there is no marker after `## Коли вживати недоконаний вид`, and `<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->` plus `<!-- INJECT_ACTIVITY: error-correction-aspect -->` are stacked at the end instead of being spread through the module. |
| 6. Engagement & tone | 9/10 | The voice is teacherly and useful: `Let us look at...`, `Notice how...`, `Ask yourself two questions before you speak.` It stays instructional rather than gamified. |
| 7. Structural integrity | 9/10 | All four planned H2 headings are present and in the correct order. The pipeline word count is 2879, above the 2000-word target, and the markdown markers are clean. |
| 8. Cultural accuracy | 10/10 | Ukrainian is presented on its own terms with no Russian-centric framing or misleading cultural comparisons. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue uses named speakers and a plausible Sunday comparison: `Оля` and `Тарас` contrast `Я читала весь день` with `Я прочитав новий роман`. It is short but natural enough for the teaching purpose. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: Section 1 paradigm area: `Let's look at the imperfective verb **робити**...` / `Now compare this with the perfective verb **зробити**...` / repeated pair references such as `**писати / написати**`, `**читати / прочитати**`, `**готувати / приготувати**`, `**робити / зробити**`, `**вчити / вивчити**`  
Issue: The plan objective requires past-tense forms for 10 common aspect pairs, but the module explicitly teaches only 5.  
Fix: Add five more common pairs with past masculine/feminine/plural forms in the paradigm section.

[VOCABULARY COVERAGE] [SEVERITY: minor]  
Location: Section 2 signal-word paragraph: `Other markers include «завжди» for always, «щодня» for every day, and «зазвичай» for usually.`  
Issue: The recommended vocabulary item `тривалість` from the plan is never introduced.  
Fix: Add one sentence explicitly linking these markers to the **тривалість** *(duration)* of an action.

[PLAN ADHERENCE] [SEVERITY: minor]  
Location: Module-wide; search confirmed zero occurrences of `Заболотний`, `ULP`, and `ukrainianlessons.com`  
Issue: Neither reference from the plan is cited or integrated into the lesson.  
Fix: Add a brief closing line pointing learners to `Заболотний Grade 6, §52-54` and the Ukrainian Lessons Grammar Hub for parallel explanations/examples.

[LINGUISTIC ACCURACY] [SEVERITY: minor]  
Location: Section 3, first example paragraph: `Цей лист тепер лежить на столі, готовий до відправки.`  
Issue: `відправка` exists, but it is colloquial; the surrounding prose is standard instructional register, so `відправлення` is the better choice here.  
Fix: Change `готовий до відправки` to `готовий до відправлення`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: End of module: `<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->` immediately followed by `<!-- INJECT_ACTIVITY: error-correction-aspect -->`  
Issue: Practice is not evenly distributed. The imperfective section has no immediate exercise marker, while two activities are clustered at the end.  
Fix: Move `fill-in-aspect-choice` to the end of `Коли вживати недоконаний вид`, leaving `error-correction-aspect` after the final practice section.

## Verdict: REVISE
Major findings remain in plan adherence and exercise distribution, so this cannot pass. The module is generally accurate and teachable, but it does not fully meet the plan’s 10-pair objective and its practice sequence needs redistribution.

<fixes>
- find: "For the regular verbs shown here, you remove the infinitive ending and add the usual past tense forms; some Ukrainian verbs form the past tense less regularly."
  replace: "For the regular verbs shown here, you remove the infinitive ending and add the usual past tense forms; some Ukrainian verbs form the past tense less regularly.\n\nYou will also hear the same pattern in other common pairs:\n* він бачив / він побачив\n* вона бачила / вона побачила\n* вони бачили / вони побачили\n\n* він купував / він купив\n* вона купувала / вона купила\n* вони купували / вони купили\n\n* він дзвонив / він подзвонив\n* вона дзвонила / вона подзвонила\n* вони дзвонили / вони подзвонили\n\n* він шукав / він знайшов\n* вона шукала / вона знайшла\n* вони шукали / вони знайшли\n\n* він вечеряв / він повечеряв\n* вона вечеряла / вона повечеряла\n* вони вечеряли / вони повечеряли"
- find: "Signal words naturally pair with the imperfective past to indicate duration or frequency. You will frequently encounter words like «довго» to indicate a long time, or «часто» to mean often. Other markers include «завжди» for always, «щодня» for every day, and «зазвичай» for usually."
  replace: "Signal words naturally pair with the imperfective past to indicate duration or frequency. You will frequently encounter words like «довго» to indicate a long time, or «часто» to mean often. Other markers include «завжди» for always, «щодня» for every day, and «зазвичай» for usually. Together, these markers often point to the **тривалість** *(duration)* of an action rather than to a finished result."
- find: "Trust this basic logic, practice identifying the signals in native texts, and your stories will sound perfectly natural."
  replace: "Trust this basic logic, practice identifying the signals in native texts, and your stories will sound perfectly natural. If you want to compare this explanation with established materials, see Заболотний Grade 6, §52-54 and the Ukrainian Lessons Grammar Hub section on past tense and aspect."
- find: "Цей лист тепер лежить на столі, готовий до відправки."
  replace: "Цей лист тепер лежить на столі, готовий до відправлення."
- find: "These adverbs act as signposts guiding you toward the correct aspect. Using the imperfective verb from the pair **вчити / вивчити** (to study/learn — impf./pf.) alongside the indicator **довго** (for a long time) illustrates a continuous habit perfectly."
  replace: "These adverbs act as signposts guiding you toward the correct aspect. Using the imperfective verb from the pair **вчити / вивчити** (to study/learn — impf./pf.) alongside the indicator **довго** (for a long time) illustrates a continuous habit perfectly.\n\n<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->"
- find: "<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->\n<!-- INJECT_ACTIVITY: error-correction-aspect -->"
  replace: "<!-- INJECT_ACTIVITY: error-correction-aspect -->"
</fixes>