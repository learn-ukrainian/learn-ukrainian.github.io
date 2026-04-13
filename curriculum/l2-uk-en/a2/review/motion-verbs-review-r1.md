## Linguistic Scan
- Factual grammar error: `To form the perfective partners for our unidirectional motion verbs, we add the prefix **по-**. This creates the verbs **піти** ... **поїхати** ... and **полетіти** ...` The statement is wrong as written because `піти` is not formed by simply adding `по-` in the same way as `поїхати` and `полетіти`.
- Factual phonetics error: `Комбінація літер «-ться» завжди звучить як довгий м'який звук. Комбінація літер «-шся» теж має свою особливу вимову і звучить як довгий м'який звук «сся».` This teaches an inaccurate/overstated pronunciation rule.

## Exercise Check
Five activity markers are present, and they are placed after the relevant teaching sections:
- `group-sort-sort-motion-verb-forms-into-unidirectional-vs-multidirectional-categories` after the motion-pairs section
- `fill-in-motion-context` after the conjugation/perfective section
- `quiz-conjugate-and-choose-the-correct-form-for-the-given-person-and-number` after the conjugation-models section
- `match-up-prepositions-cases` and `unjumble-directional-sentences` after the prepositions/cases section

They map cleanly to the five `activity_hints` and are spread evenly through the module. No inline DSL exercise blocks are present, so there is no answer logic here to audit beyond placement/alignment.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2 sections appear in order, and all five activity markers are present. However, the prose never cites the listed references; there is no mention of `Заболотний` or `Ohoiko` anywhere in the module text. |
| 2. Linguistic accuracy | 6/10 | The module teaches `we add the prefix **по-**. This creates the verbs **піти**, **поїхати**, and **полетіти**`, and later claims `Комбінація літер «-ться» завжди звучить як довгий м'який звук...`. Both are factual teaching problems. |
| 3. Pedagogical quality | 8/10 | The flow is strong: scenario → explanation → examples → practice marker in each section. But the incorrect perfective explanation and the faulty phonetics detour reduce instructional reliability. |
| 4. Vocabulary coverage | 8/10 | Required plan vocabulary is used in prose, including `рух`, `напрямок`, `казати / кажу`, `пити / п'ю`, and `боротися / борюся`. However, the recommended terms `односпрямований` and `різноспрямований` are absent. |
| 5. Exercise quality | 9/10 | The marker set matches the plan exactly in count and sequencing, and each marker follows the content it is meant to test. No inline exercise logic is visible, so there is nothing else to flag here. |
| 6. Engagement & tone | 9/10 | The airport/travel framing is concrete and usable, and the examples stay focused on the grammar point rather than empty hype. |
| 7. Structural integrity | 10/10 | All required sections are present and ordered correctly, the markdown is clean, and the pipeline word count is 2903, which is safely above the 2000-word target. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian on its own terms and avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 9/10 | The module includes multi-turn, named-role dialogues in plausible travel contexts rather than isolated Q/A fragments. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `To form the perfective partners for our unidirectional motion verbs, we add the prefix **по-**. This creates the verbs **піти** (to leave on foot — pf.), **поїхати** (to leave by vehicle — pf.), and **полетіти** (to fly off — pf.).`  
Issue: This teaches an incorrect formation rule. `поїхати` and `полетіти` fit the `по-` pattern, but `піти` does not.  
Fix: Remove the false prefix rule and present the three perfective partners as paired forms.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: `For each transport method, we have one verb for a unidirectional, in-progress action, and another for a multidirectional or habitual action.`  
Issue: The module teaches the concept but never introduces the recommended Ukrainian labels `односпрямований` and `різноспрямований`. A content search confirms 0 occurrences of both terms.  
Fix: Add the Ukrainian terms directly into this defining sentence.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Зверніть особливу увагу на вимову цих слів! Комбінація літер «-ться» завжди звучить як довгий м'який звук. Комбінація літер «-шся» теж має свою особливу вимову і звучить як довгий м'який звук «сся».`  
Issue: This is not an accurate pronunciation rule as stated and should not be taught this way to learners.  
Fix: Replace it with a cautious statement that these clusters have special pronunciation and should be learned by listening and repetition.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Because they are perfective, we frequently use them in the past tense to indicate that someone has set off or departed.`  
Issue: The plan lists `Заболотний Grade 6, §39-41` and `Ohoiko, Verbs of Motion with Prefixes (2024)` as references, but the module never integrates or cites them. A content search confirms 0 occurrences of `Заболотний` and `Ohoiko`.  
Fix: Add one concise source note in the motion/perfective discussion.

## Verdict: REVISE
REVISE. The structure, pacing, and exercise placement are solid, but the module contains two critical factual teaching errors and two major plan-coverage gaps. Any critical linguistic inaccuracy blocks PASS.

<fixes>
- find: |-
    To form the perfective partners for our unidirectional motion verbs, we add the prefix **по-**. This creates the verbs **піти** (to leave on foot — pf.), **поїхати** (to leave by vehicle — pf.), and **полетіти** (to fly off — pf.).
  replace: |-
    To form the perfective partners for our unidirectional motion verbs, Ukrainian uses the paired forms **піти** (to leave on foot — pf.), **поїхати** (to leave by vehicle — pf.), and **полетіти** (to fly off — pf.).

- find: |-
    For each transport method, we have one verb for a unidirectional, in-progress action, and another for a multidirectional or habitual action.
  replace: |-
    For each transport method, we have one verb for a unidirectional (**односпрямований**), in-progress action, and another for a multidirectional (**різноспрямований**) or habitual action.

- find: |-
    Зверніть особливу увагу на вимову цих слів! Комбінація літер «-ться» завжди звучить як довгий м'який звук. Комбінація літер «-шся» теж має свою особливу вимову і звучить як довгий м'який звук «сся». Це дуже важливе фонетичне правило української мови, яке робить ваше мовлення більш природним.
  replace: |-
    Зверніть особливу увагу на вимову цих слів! Комбінації «-ться» і «-шся» мають особливу вимову, тому ці форми варто слухати й повторювати як готові моделі. Це допоможе зробити ваше мовлення більш природним.

- find: |-
    Because they are perfective, we frequently use them in the past tense to indicate that someone has set off or departed.
  replace: |-
    Because they are perfective, we frequently use them in the past tense to indicate that someone has set off or departed. This overview follows the motion-verb treatment in Заболотний Grade 6, §39-41 and Ohoiko, *Verbs of Motion with Prefixes* (2024).
</fixes>