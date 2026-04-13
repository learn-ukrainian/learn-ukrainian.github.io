## Linguistic Scan
Factually wrong grammar explanation: `Кожне українське дієслово має своє спеціальне запитання. Якщо дія постійно триває, ми запитуємо «що робити?». Якщо ця дія має чіткий результат, ми запитуємо «що зробити?».` This incorrectly ties `що робити? / що зробити?` to a situational reading of the action instead of the standard school-rule distinction between imperfective and perfective verbs.

## Exercise Check
All 4 activity markers are present, correctly ordered, and placed after the relevant teaching sections:

- `quiz-aspect-sorting` after section 1
- `fill-in-identify-the-aspect-in-sentences` after section 2
- `match-up-choose-the-correct-aspect-context-based` after section 3
- `error-correction-fix-aspect` after section 4

Their types and focuses match the plan’s `activity_hints`. No inline DSL exercise logic is present here to audit further.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned sections are present in order, section sizing stays close to plan, and the required aspect vocabulary is covered; however, a search of the prose found 0 mentions of `Авраменко`, `ULP`, or `Ukrainian Lessons`, so the plan references are not cited. |
| 2. Linguistic accuracy | 7/10 | The Ukrainian lexicon looks standard, but the rule block `Якщо дія постійно триває, ми запитуємо «що робити?»...` teaches the aspect questions inaccurately. |
| 3. Pedagogical quality | 7/10 | The module has a clear PPP spine: football dialogue -> explanation -> practice markers. But the same rule block gives a wrong grammar shortcut, and the opening paragraph spends many English words on scene-setting before advancing the concept. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose: `вид дієслова`, `недоконаний вид`, `доконаний вид`, `процес`, `результат`, `дія`, `повторення`, `робити / зробити`. |
| 5. Exercise quality | 10/10 | Four markers are present, each follows the relevant teaching section, and the marker types/foci match the plan exactly: quiz, fill-in, match-up, error-correction. |
| 6. Engagement & tone | 7/10 | The football framing is relevant, but lines like `Imagine you are sitting on the comfortable couch...` and `absolute key to natural fluency` add filler and hype instead of tighter teaching prose. |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and ordered correctly; pipeline word count is 2830, above the 2000 target; markdown structure is clean. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian on its own terms and uses ordinary Ukrainian contexts without Russian-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | The named-speaker football dialogue matches the plan and contrasts process/result naturally: `він швидко біжить` vs `він забив красивий гол`. |

## Findings
[2 Linguistic accuracy / 3 Pedagogical quality] [SEVERITY: critical]  
Location: `Кожне українське дієслово має своє спеціальне запитання. Якщо дія постійно триває, ми запитуємо «що робити?». Якщо ця дія має чіткий результат, ми запитуємо «що зробити?».`  
Issue: This teaches the wrong rule. In school grammar, `що робити?` and `що зробити?` are the identifying questions for imperfective vs perfective verbs, not a conditional test based on whether an action is “constantly ongoing” or has a result in that moment.  
Fix: Replace the paragraph with the standard formulation: imperfective verbs answer `що робити?`, perfective verbs answer `що зробити?`.

[3 Pedagogical quality] [SEVERITY: critical]  
Location: `> *Every Ukrainian verb has its own special question. If the action is constantly ongoing, we ask "what to do?". If this action has a clear result, we ask "what to have done?".*`  
Issue: The English gloss repeats the same wrong explanation and adds the misleading phrase `what to have done?`, which is not a good learner-facing gloss for `що зробити?`.  
Fix: Replace it with an English gloss that explains the school-rule distinction directly and glosses perfective as completion.

[1 Plan adherence] [SEVERITY: major]  
Location: `Let us look closer at those two essential questions that Ukrainian school children learn.`  
Issue: The prose never cites the plan references. A text search finds 0 mentions of `Авраменко`, `ULP`, or `Ukrainian Lessons`.  
Fix: Add one sentence in section 1 explicitly linking the explanation to `Авраменко (§28-30)` and `Ukrainian Lessons`.

[6 Engagement & tone / 3 Pedagogical quality] [SEVERITY: major]  
Location: `Imagine you are sitting on the comfortable couch with a good friend, watching an intensely competitive football match on television. The players are moving fast across the green field, the crowd is cheering loudly, and the sports commentary is flying rapidly. In such an exciting and dynamic situation, you might hear a conversation that sounds exactly like this:`  
Issue: This is inflated scene-setting. It adds a lot of English words before teaching anything new and weakens the module’s pacing.  
Fix: Compress the opener to 1-2 sentences that establish the football context and move directly into the dialogue.

[6 Engagement & tone] [SEVERITY: minor]  
Location: `Learning them together as a matching set is the absolute key to natural fluency.`  
Issue: `absolute key to natural fluency` is hype, not teacherly explanation.  
Fix: Tone it down to a practical claim about helping learners use aspect more naturally.

## Verdict: REVISE
REVISE — the module is structurally solid and the exercise placement is correct, but it contains a critical grammar-teaching error plus several major quality issues. Under the protocol, that cannot pass.

<fixes>
- find: |-
    Кожне українське дієслово має своє спеціальне запитання. Якщо дія постійно триває, ми запитуємо «що робити?». Якщо ця дія має чіткий результат, ми запитуємо «що зробити?».
  replace: |-
    У шкільній граматиці недоконані дієслова відповідають на питання «що робити?», а доконані — на питання «що зробити?».
- find: |-
    > *Every Ukrainian verb has its own special question. If the action is constantly ongoing, we ask "what to do?". If this action has a clear result, we ask "what to have done?".*
  replace: |-
    > *In school grammar, imperfective verbs answer "what to do?", while perfective verbs answer "what to do to completion?".*
- find: |-
    Let us look closer at those two essential questions that Ukrainian school children learn.
  replace: |-
    Let us look closer at those two essential questions that Ukrainian school children learn. This is the standard school explanation you will also see in Авраменко (§28-30) and in Ukrainian Lessons' overview of verb aspect.
- find: |-
    Imagine you are sitting on the comfortable couch with a good friend, watching an intensely competitive football match on television. The players are moving fast across the green field, the crowd is cheering loudly, and the sports commentary is flying rapidly. In such an exciting and dynamic situation, you might hear a conversation that sounds exactly like this:
  replace: |-
    Imagine you are watching a football match with a friend. The attack is developing quickly, and the contrast between process and result is easy to hear. In that situation, you might hear a conversation like this:
- find: |-
    Learning them together as a matching set is the absolute key to natural fluency.
  replace: |-
    Learning them together as a matching set will help you use aspect more naturally.
</fixes>