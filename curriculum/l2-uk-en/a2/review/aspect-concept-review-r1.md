## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian letters found in the Ukrainian examples.

One factual grammar error found:
- **Critical:** In the perfective explanation, `"They only describe completed results in the past or guaranteed results in the future."` and `"The Ukrainian language uses these forms to promise a future result."` teach the wrong meaning. Perfective non-past forms express a **future completed action**, not grammatical guarantee/promise. This matches the local textbook corpus (`писатиму — напишу`, `робитиму — зроблю`).

## Exercise Check
Four markers are present: `quiz-aspect-sorting`, `fill-in-identify-aspect`, `match-up-choose-aspect`, `error-correction-fix-aspect`.
All four appear after the relevant teaching sections, match the plan’s `activity_hints`, and are spread evenly through the module.
No exercise-placement or marker-ID issues found in the provided prose.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections and all 4 activity markers are present, but the prose never cites the plan references (`Авраменко`, `ULP`, `Ukrainian Lessons` = 0 hits in the provided content), and all recommended vocab items (`завершений`, `тривалий`, `одноразовий`, `концепція`) are absent. |
| 2. Linguistic accuracy | 7/10 | Grammar claim is wrong in the perfective section: `"guaranteed results in the future"` and `"promise a future result"` misstate what perfective future means. |
| 3. Pedagogical quality | 8/10 | The module has strong contrasts and many examples, but the perfective section spends a substantial chunk on future forms right after saying `"For now, we will focus exclusively on the past tense"`, which blurs the A2.1 scope. |
| 4. Vocabulary coverage | 7/10 | Required vocab is used naturally throughout, but the recommended plan vocabulary is completely missing from the prose (`завершений`, `тривалий`, `одноразовий`, `концепція` = 0 hits). |
| 5. Exercise quality | 10/10 | The marker sequence matches the plan exactly: quiz after the intro, fill-in after imperfective, match-up after perfective, error-correction after pair comparison. |
| 6. Engagement & tone | 8/10 | The teacher voice is warm and concrete, but `"Українські мами часто пояснюють..."` is generic framing rather than a necessary teaching move. |
| 7. Structural integrity | 10/10 | All planned sections are present and ordered correctly, markers are clean, and the pipeline word count is 2580, which is above the 2000 target. |
| 8. Cultural accuracy | 8/10 | No Russia-centric framing appears, but `"Українські мами часто пояснюють..."` makes an unsupported cultural generalization. |
| 9. Dialogue & conversation quality | 9/10 | The opening football dialogue has named speakers, a real context, and a clear aspect contrast (`він біжить` vs `він забив гол`). |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]  
Location: Perfective section — `"They only describe completed results in the past or guaranteed results in the future."` / `"The Ukrainian language uses these forms to promise a future result."`  
Issue: This teaches the wrong grammar. Perfective non-past forms express a future completed action; they do not encode guarantee or promise.  
Fix: Replace that explanation with wording about future completed action.

[1. Plan adherence] [SEVERITY: major]  
Location: Whole module — search of the provided content returned 0 hits for `Авраменко`, `ULP`, `Ukrainian Lessons`, and the reference URL.  
Issue: The plan lists two references, but the prose never integrates either one.  
Fix: Add one short sentence tying the process/result explanation to `Авраменко Grade 7, §28–30` and `Ukrainian Lessons`.

[4. Vocabulary coverage] [SEVERITY: major]  
Location: Whole module — search of the provided content returned 0 hits for `завершений`, `тривалий`, `одноразовий`, `концепція`.  
Issue: All recommended vocabulary items from the plan are missing from the prose.  
Fix: Add one compact summary sentence that uses all four words in context.

[3. Pedagogical quality] [SEVERITY: major]  
Location: Perfective section — `"The future tense logic of perfective verbs is very elegant..."` through the future example block with `"Я обіцяю, що я зроблю це завдання завтра."`  
Issue: The plan says to focus on past-tense perfective for now, but the module still spends too much time teaching future forms.  
Fix: Compress this to a brief note, then return immediately to past-tense examples.

[6. Engagement & tone / 8. Cultural accuracy] [SEVERITY: minor]  
Location: Perfective section — `"Українські мами часто пояснюють цю різницю своїм дітям дуже просто."`  
Issue: This is an unsupported cultural generalization and adds no necessary grammar value.  
Fix: Replace it with a neutral framing.

## Verdict: REVISE
REVISE — there is a critical grammar error in the explanation of perfective future, plus major plan/vocabulary gaps. Multiple dimensions are below 9, so this cannot pass.

<fixes>
- find: "This focus on the final outcome leads us to a crucial grammatical rule. Perfective verbs have absolutely no true present tense. Think about the logic of the concept: because a perfective verb fundamentally means a completed result, it is impossible to be doing it right now. You cannot be in the middle of a completed action. Therefore, when you conjugate a perfective verb using what looks like present tense endings, the meaning automatically shifts to the future. The Ukrainian language uses these forms to promise a future result."
  replace: "This focus on the final outcome leads us to a crucial grammatical rule. Perfective verbs have no true present tense. Because a perfective verb presents an action as complete, forms like «зроблю» and «напишу» do not describe the present moment. Instead, they express a future completed action."
- find: "The future tense logic of perfective verbs is very elegant, but we will temporarily set the future aside. For now, we will focus exclusively on the past tense of perfective verbs. The past tense is the most natural place to see perfective verbs in action, because it is easy to point to finished events in history. We will use forms like «зробив» for did or has done, «написала» for wrote or has written, and «забив» for scored. These verbs act as solid markers of completed achievements."
  replace: "We have mentioned the future form, but in this foundation module we will focus on the past tense of perfective verbs, where the completed result is easiest to see. Forms like «зробив», «написала», and «забив» clearly mark finished actions."
- find: "Українські мами часто пояснюють цю різницю своїм дітям дуже просто. Вони кажуть: «Прибирати кімнату і прибрати кімнату — це різні дії!» Ти можеш прибирати цілий день, але кімната досі брудна. Але коли ти нарешті прибрав, кімната чиста."
  replace: "У побуті цю різницю часто пояснюють дуже просто: «Прибирати кімнату і прибрати кімнату — це різні дії!» Ти можеш прибирати цілий день, але кімната досі брудна. Коли ти нарешті прибрав, кімната чиста."
- insert_after: "The core meaning of the word remains the same, but the grammatical focus shifts entirely from the activity itself to the achievement of a goal."
  content: "Це і є базова концепція виду: недоконаний вид зазвичай показує тривалий процес, а доконаний вид часто показує завершений, одноразовий результат. This is also the core contrast presented in Авраменко Grade 7, §28–30 and in Ukrainian Lessons."
</fixes>