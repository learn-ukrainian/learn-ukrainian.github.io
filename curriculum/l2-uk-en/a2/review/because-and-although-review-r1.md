## Linguistic Scan
- Calque: `«Хоча я прокинувся пізно, я встиг прийняти душ...»` teaches `прийняти душ`, which this repo’s own linguistic guidance treats as a calque; use `помитися під душем` or `брати душ`.
- Factually wrong grammar claim: in the coordinating-conjunction section, `навпаки` is presented as one more conjunction-like connector (“If you want to show a very strong, direct contrast, you can use the word «навпаки»”). VESUM tags `навпаки` as `adv`, not `conj`, so this explanation misclassifies its part of speech.

## Exercise Check
Five planned activity markers are present: `match-up`, `unjumble`, `group-sort`, `quiz`, `fill-in`. They cover the five `activity_hints`, and there are no inline DSL exercise blocks in the prose. No exercise-marker count mismatch found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three planned H2 sections are present and near budget, and required vocabulary is covered in prose. But the plan references are not integrated: searches for `Заболотний`, `ULP`, and `Ukrainian Lessons` in the module text return 0 occurrences. |
| 2. Linguistic accuracy | 6/10 | Two confirmed teaching errors: `«...я встиг прийняти душ...»` uses a calque, and `«навпаки»` is taught as if it were a coordinating conjunction even though VESUM classifies it as an adverb. |
| 3. Pedagogical quality | 8/10 | The module generally follows PPP well: dialogue, explanation, multiple examples, then practice markers. But one explanation is less precise than it should be because it teaches `навпаки` inside the conjunction set. |
| 4. Vocabulary coverage | 8/10 | Required items such as `тому що`, `бо`, `хоча`, `але`, `причина`, `сполучник`, `складне речення`, and `тому` all appear naturally. Recommended vocabulary is also present, but `навпаки` is introduced with the wrong grammatical role. |
| 5. Exercise quality | 9/10 | All five planned activity types are present and positioned after relevant teaching. The prose itself gives enough content to support those task types. |
| 6. Engagement & tone | 7/10 | Several lines drift into generic booster language rather than concrete teaching, e.g. `Using these alternatives instantly elevates your spoken and written language to a higher level.` |
| 7. Structural integrity | 10/10 | Clean three-section structure, all H2 headings present and ordered, five activity markers present, and pipeline word count is 2840, which is safely above the 2000 target. |
| 8. Cultural accuracy | 9/10 | Ukrainian is presented on its own terms, with no Russian-centered framing; the proverb and register notes are appropriate. |
| 9. Dialogue & conversation quality | 9/10 | The opening class-skipping exchange is short but relevant to the plan and uses the target conjunctions naturally enough for A2. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: first explanatory paragraph after the opening dialogue: `Both of them translate directly to the English word "because".`  
Issue: The prose never cites or integrates the planned references. I verified absence by searching the module text for `Заболотний`, `ULP`, and `Ukrainian Lessons` and found 0 occurrences.  
Fix: Add a short source note tying the explanation to `Заболотний Grade 5, §28`, `Заболотний Grade 6`, and `ULP: Ukrainian Conjunctions`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: final section, consolidation paragraph: `«Хоча я прокинувся пізно, я встиг прийняти душ. ...»`  
Issue: `прийняти душ` is a calque; the repo’s own linguistic guidance treats `приймати/прийняти душ` as non-standard and prefers `брати душ` or `митися/помитися під душем`.  
Fix: Replace `прийняти душ` with `помитися під душем`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: start of the third section: `If you want to show a very strong, direct contrast, you can use the word «навпаки» (on the contrary).`  
Issue: This teaches `навпаки` as part of the conjunction set, but VESUM classifies `навпаки` as an adverb, not a conjunction. Learners will internalize the wrong part of speech.  
Fix: Rephrase the paragraph so `проте`, `однак`, and `зате` remain conjunctions, while `навпаки` is explicitly described as a separate adverb/discourse word used for reversal or correction.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: same third-section paragraph: `Using these alternatives instantly elevates your spoken and written language to a higher level.`  
Issue: This is generic promotional filler. It adds hype, not instruction, and weakens precision in a grammar lesson.  
Fix: Replace it with a concrete sentence about what learners actually gain, such as hearing differences in repetition avoidance, contrast, compensation, and reversal.

## Verdict: REVISE
REVISE because there are confirmed critical linguistic/grammar errors (`прийняти душ`, misclassification of `навпаки`) and multiple dimensions below 9. The structure is solid, but the module should not ship with wrong Ukrainian or wrong grammar metalanguage.

<fixes>
- find: |-
    When you want to explain the **причина** (reason) for an action, you need to answer the question «Чому?». In Ukrainian grammar, we use a **складне речення** (complex sentence) to connect the main action with its explanation. To link these two parts together, we use a special linking word called a **сполучник** (conjunction). The two most common causal conjunctions you will hear every day are «тому що» and «бо». Both of them translate directly to the English word "because".
  replace: |-
    When you want to explain the **причина** (reason) for an action, you need to answer the question «Чому?». In Ukrainian grammar, we use a **складне речення** (complex sentence) to connect the main action with its explanation. To link these two parts together, we use a special linking word called a **сполучник** (conjunction). The two most common causal conjunctions you will hear every day are «тому що» and «бо». Both of them translate directly to the English word "because". This matches the school-style explanation in Заболотний Grade 5, §28 and the Grade 6 section on conjunctions, and it also aligns with ULP: Ukrainian Conjunctions.
- find: |-
    You are familiar with the word «і» (and) and the contrast word **але** (but). To make your Ukrainian sound richer, you can use stylistic alternatives. The word «та» is a beautiful, traditional alternative to «і». For expressing contrast, you can use words like «проте», «однак», and «зате». If you want to show a very strong, direct contrast, you can use the word «навпаки» (on the contrary). Using these alternatives instantly elevates your spoken and written language to a higher level.
  replace: |-
    You are familiar with the word «і» (and) and the contrast word **але** (but). To vary your Ukrainian naturally, you can use stylistic alternatives. The word «та» is a common alternative to «і», especially when speakers want to avoid repetition. For expressing contrast, you can use conjunctions like «проте», «однак», and «зате». The word «навпаки» (on the contrary) is also useful, but it is not a coordinating conjunction: it introduces a reversed idea or correction.
- find: |-
    «Хоча я прокинувся пізно, я встиг прийняти душ. Але я зовсім не поснідав вдома. Я побіг на роботу дуже швидко, тому що не хотів запізнитися. Проте я все одно приїхав пізно, бо на вулиці був затор».
  replace: |-
    «Хоча я прокинувся пізно, я встиг помитися під душем. Але я зовсім не поснідав вдома. Я побіг на роботу дуже швидко, тому що не хотів запізнитися. Проте я все одно приїхав пізно, бо на вулиці був затор».
</fixes>