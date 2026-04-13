## Linguistic Scan
No linguistic errors found. Checked candidate forms such as `класно`, `передала`, `відправив`, `ярмарку`, `одноразовий`, `концепція`, `тривалий`, and `завершений` in VESUM; all are attested, and no Russian characters (`ы`, `э`, `ё`, `ъ`) appear in the Ukrainian text.

## Exercise Check
4 markers are present, they match the 4 `activity_hints`, and they are placed after the relevant teaching sections:
`quiz-aspect-sorting` after the introduction, `fill-in-identify-aspect` after imperfective, `match-up-choose-aspect` after perfective, and `error-correction-fix-aspect` after the comparison section. No sequencing or visible logic issues are apparent from the placeholders themselves.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers all four planned sections and the football dialogue matches the plan, but the plan references are not integrated: `Авраменко` and `ULP` have 0 occurrences in the provided module text. |
| 2. Linguistic accuracy | 10/10 | No confirmed Russianisms, Surzhyk, calques, paronym misuse, or grammar errors in the Ukrainian examples; checked forms are standard, and the rule about present-tense forms being imperfective is accurate. |
| 3. Pedagogical quality | 8/10 | The explanations are example-rich, but one conceptual sentence is wrong: `Almost every concept in Ukrainian exists as a pair of these two aspects.` The module should say `verb`, not `concept`. |
| 4. Vocabulary coverage | 8/10 | All required plan vocabulary appears naturally, but the recommended items `завершений`, `тривалий`, `одноразовий`, and `концепція` are absent from the prose. |
| 5. Exercise quality | 10/10 | All four planned exercise types have corresponding markers placed after the relevant teaching blocks: `quiz-aspect-sorting`, `fill-in-identify-aspect`, `match-up-choose-aspect`, `error-correction-fix-aspect`. |
| 6. Engagement & tone | 9/10 | The football opener and later room/book/homework examples keep the tone concrete and teacherly without corporate or gamified filler. |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and ordered correctly; the pipeline word count is 2487, above target, and the inject markers are clean. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian grammar on its own terms and avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 9/10 | The named-speaker football exchange is relevant to the aspect contrast and works as a natural short opener. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: Section 1, paragraph beginning `In Ukrainian schools, children learn a simple trick to determine the aspect of any verb.`  
Issue: The plan lists `Авраменко Grade 7, §28-30` and `ULP: Ukrainian Verb Aspect` as references, but neither source is cited anywhere in the module. Search confirmed 0 occurrences of `Авраменко` and `ULP`.  
Fix: Add one brief source-anchoring sentence to the school-rule paragraph.

[VOCABULARY COVERAGE] [SEVERITY: minor]  
Location: Section 1, paragraph `Уяви, що недоконаний вид — це довге кіно...`  
Issue: The recommended vocabulary from the plan is not reinforced in the prose. Search confirmed 0 occurrences of `завершений`, `тривалий`, `одноразовий`, and `концепція`.  
Fix: Revise the analogy paragraph so it naturally includes those four words.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Section 1, paragraph `Almost every concept in Ukrainian exists as a pair of these two aspects.`  
Issue: This is conceptually wrong. Aspect pairs are pairs of verbs, not “concepts.”  
Fix: Replace `concept` with `verb`.

## Verdict: REVISE
REVISE. The module is structurally solid and linguistically clean, but it has three fixable quality problems: missing plan references, missing recommended vocabulary, and one conceptual misstatement. Dimensions 1, 3, and 4 are below 9, so this cannot pass as-is.

<fixes>
- find: |-
    In Ukrainian schools, children learn a simple trick to determine the aspect of any verb. If the infinitive form answers the question «що робити?» (what to do?), it is imperfective. For example, the verb **робити** (to do) focuses on the activity itself. If the verb answers the question «що зробити?» (what to have done?), it is perfective. The verb **зробити** (to do / to have done) focuses entirely on the completion of the task.
  replace: |-
    In Ukrainian schools, children learn a simple trick to determine the aspect of any verb. If the infinitive form answers the question «що робити?» (what to do?), it is imperfective. For example, the verb **робити** (to do) focuses on the activity itself. If the verb answers the question «що зробити?» (what to have done?), it is perfective. The verb **зробити** (to do / to have done) focuses entirely on the completion of the task. This school-style rule matches Авраменко, Grade 7, §28-30, and learners can compare it with the explanation in ULP: Ukrainian Verb Aspect.
- find: |-
    Almost every concept in Ukrainian exists as a pair of these two aspects.
  replace: |-
    Almost every verb in Ukrainian exists as a pair of these two aspects.
- find: |-
    Уяви, що недоконаний вид — це довге кіно. Ти дивишся фільм кадр за кадром і бачиш повільний процес. Доконаний вид — це фінальні титри або одна фотографія. Ти бачиш тільки швидкий фінал і результат цієї дії.
  replace: |-
    Уяви, що недоконаний вид — це довге кіно. Ти дивишся фільм кадр за кадром і бачиш тривалий процес. Доконаний вид — це фінальні титри або одна фотографія. Ти бачиш одноразовий, завершений фінал і результат цієї дії. Ця концепція допомагає швидко відчути різницю між видами.
</fixes>