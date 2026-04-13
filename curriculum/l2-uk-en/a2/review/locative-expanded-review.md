## Linguistic Scan
- Factual grammar-teaching error: `Let's read some more examples to see how the locative case shifts the meaning...` is followed by `У мене є одна дуже цікава думка. Учора у нас була важлива зустріч.` These are not locative-case examples, so the section mislabels non-target material as target grammar.
- Factual overstatement: `However, for the methods we discussed here, the locative case is the authentic standard.` This is too absolute for the `по` section; the module itself already treats these as fixed expressions, and local textbook evidence is less categorical.
- Misleading glosses: `У минулому місяці...` is glossed as `In the past month...`, and `У минулому році...` is glossed as `In the past year...` These blur the basic A2 mapping of `минулий` here as `last/previous`.

## Exercise Check
- Marker inventory in the prose matches the 4 planned activity hints:
  - `fill-in-complete-sentences-with-the-correct-locative-form`
  - `error-correction-prepositions`
  - `quiz-identify-the-function-of-locative-in-each-sentence`
  - `match-up-expressions`
- Placement is broadly acceptable: the fill-in and error-correction markers come after the teaching sections they depend on, and the quiz/match-up markers come after consolidation.
- Issue: the prose marker `error-correction-prepositions` does not match the generated activity ID. The activities file defines `error-correction-locative-usage`, so this planned exercise will not inject correctly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections are present and the planned vocab is covered, but the plan references are never cited in the module text, and the planned error-correction activity is broken by `<!-- INJECT_ACTIVITY: error-correction-prepositions -->` not matching the generated activity ID. |
| 2. Linguistic accuracy | 6/10 | The Ukrainian is mostly solid, but the module makes factual teaching errors: `У мене є одна дуже цікава думка. Учора у нас була важлива зустріч.` is presented as locative evidence, and the tip claims `the locative case is the authentic standard`, which is too absolute. |
| 3. Pedagogical quality | 6/10 | The module has PPP flow, but explanation and evidence drift apart: `Let's read some more examples...` is followed by two non-locative sentences, and the glosses `In the past month` / `In the past year` weaken the learner’s `минулий = last/previous` mapping. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is used naturally in prose: `місцевий`, `абстрактний`, `минулий`, `місяць`, `тиждень`, `телефон`, `подорож`, `зустріч`, `думка`, `проблема`; recommended `дитинство`, `молодість`, `майбутнє`, `освіта`, `мистецтво` also appear. |
| 5. Exercise quality | 6/10 | The module has the right four marker types, but `error-correction-prepositions` will not resolve because the generated activities file uses `error-correction-locative-usage`. |
| 6. Engagement & tone | 8/10 | Mostly teacherly and concrete, but some English meta-commentary adds padding, e.g. `This adds a dynamic layer of meaning to the case.` |
| 7. Structural integrity | 9/10 | All planned H2s are present and ordered correctly, and the pipeline word count `2926` is above target. The main structural defect is the broken exercise marker link. |
| 8. Cultural accuracy | 8/10 | No Russia-centric framing or fabricated cultural claims, but `authentic standard` overstates normative certainty in a way the module does not fully support. |
| 9. Dialogue & conversation quality | 7/10 | Dialogues are named and multi-turn, but some register is off: `> — **Марія:** Привіт! Ти де зараз?` followed by `> — **Іван:** Добрий день! Я по дорозі на роботу.` sounds mismatched. |

## Findings
[DIMENSION 2] [SEVERITY: critical]  
Location: `Let's read some more examples to see how the locative case shifts the meaning from a physical location to an abstract sphere.` and `Він багато років працює в українській політиці. У мене є одна дуже цікава думка. Учора у нас була важлива зустріч. У цій сфері є одна велика проблема.`  
Issue: Two of the four sentences offered as locative examples are not locative constructions (`У мене`, `у нас`). This teaches the wrong case identification.  
Fix: Replace the sentence block with examples that actually contain locative constructions.

[DIMENSION 2] [SEVERITY: critical]  
Location: `**Did you know?** — The preposition «по» is incredibly versatile... However, for the methods we discussed here, the locative case is the authentic standard.`  
Issue: The rule is stated too absolutely. The section should present `по телефону`, `по радіо`, `по дорозі` as fixed expressions, not as a blanket normative claim.  
Fix: Narrow the wording to fixed expressions and remove `authentic standard`.

[DIMENSION 1] [SEVERITY: major]  
Location: Module-wide — no occurrences of `Заболотний`, `ULP`, `§28`, `§34`, or `§35` appear in the module text.  
Issue: The plan references are never integrated, despite being listed in the source-of-truth plan.  
Fix: Add one short reference note in the concluding tip or summary.

[DIMENSION 2] [SEVERITY: critical]  
Location: `> — **Ігор:** Привіт, Маріє! У минулому місяці я змінив роботу. *(Hi, Mariia! In the past month I changed my job.)*` and `> *My sister works in medicine. In the past year, she lived in Odesa. Now she works in a hospital. We often talk by phone. She tells about life in the new city. I am very happy for her.*`  
Issue: The English glosses misrepresent `у минулому місяці / році` as `in the past month / year` instead of the intended `last month / year`.  
Fix: Change the glosses to `Last month...` and `Last year...`.

[DIMENSION 5] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: error-correction-prepositions -->`  
Issue: This marker ID does not match the generated activity ID, so the planned error-correction exercise will fail to inject.  
Fix: Rename the marker to `error-correction-locative-usage`.

[DIMENSION 9] [SEVERITY: minor]  
Location: `> — **Марія:** Привіт! Ти де зараз?` / `> — **Іван:** Добрий день! Я по дорозі на роботу.`  
Issue: The reply shifts from informal `Привіт` to formal `Добрий день` inside a casual exchange.  
Fix: Make Іван’s reply informal as well.

## Verdict: REVISE
This cannot pass. There are critical grammar-teaching errors, a broken exercise marker, and multiple dimensions below 9. The module is salvageable with deterministic edits, so `REVISE` is the correct verdict rather than `REJECT`.

<fixes>
- find: "Він багато років працює в українській політиці. У мене є одна дуже цікава думка. Учора у нас була важлива зустріч. У цій сфері є одна велика проблема."
  replace: "Він багато років працює в українській політиці. На цій зустрічі ми говорили про одну дуже цікаву думку. У цій сфері є одна велика проблема. У житті такі зміни бувають часто."
- find: "**Did you know?** — The preposition «по» is incredibly versatile. While it denotes means of communication («по телефону») or a path («по дорозі») with the locative case, you will also see it used with other cases to express distribution. However, for the methods we discussed here, the locative case is the authentic standard."
  replace: "**Did you know?** — The preposition «по» is versatile, but learners should treat «по телефону», «по радіо», and «по дорозі» as fixed expressions rather than a blanket rule for every communication noun. For broader reference, compare Заболотний Grade 5 §28-30, Заболотний Grade 6 §34-35, and the ULP locative overview listed in the plan."
- find: "> — **Ігор:** Привіт, Маріє! У минулому місяці я змінив роботу. *(Hi, Mariia! In the past month I changed my job.)*"
  replace: "> — **Ігор:** Привіт, Маріє! У минулому місяці я змінив роботу. *(Hi, Mariia! Last month I changed my job.)*"
- find: "> *My sister works in medicine. In the past year, she lived in Odesa. Now she works in a hospital. We often talk by phone. She tells about life in the new city. I am very happy for her.*"
  replace: "> *My sister works in medicine. Last year, she lived in Odesa. Now she works in a hospital. We often talk by phone. She tells me about life in the new city. I am very happy for her.*"
- find: "<!-- INJECT_ACTIVITY: error-correction-prepositions -->"
  replace: "<!-- INJECT_ACTIVITY: error-correction-locative-usage -->"
- find: "> — **Іван:** Добрий день! Я по дорозі на роботу. *(Good day! I am on the way to work.)*"
  replace: "> — **Іван:** Привіт! Я по дорозі на роботу. *(Hi! I am on the way to work.)*"
</fixes>