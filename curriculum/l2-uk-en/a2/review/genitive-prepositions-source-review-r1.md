## Linguistic Scan
- Critical grammar error: `Many events and abstract concepts take the **-у** or **-ю** ending. Hard masculine stems take **-у**, while soft stems take **-ю**.` This is false for `день`: VESUM confirms Genitive `дня`, not `дню`. The module itself immediately gives the correct form `після дня`, so the rule is internally contradictory.

## Exercise Check
4 inline markers found:
- `quiz-euphony-z-iz-zi` after the `з/із/зі` explanation
- `fill-in-vid-z` after the `від` section
- `match-up-preposition-phrases` after the `після` section
- `group-sort-prepositions` after the `після` section

The marker IDs match the 4 plan `activity_hints`, and the activity YAML provides 8 items/pairs for each. Marker placement is pedagogically sensible. No exercise logic errors confirmed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All `content_outline` points are present in order: origin/euphony/material/time in section 1, person/distance/protection in section 2, and `після` plus `до` contrast in section 3. Required/recommended lexis appears in context: `прийменник`, `джерело`, `недалеко`, `з дитинства`, `з шовку`, `парасолька`, `сусіда`. |
| 2. Linguistic accuracy | 6/10 | The section says `Hard masculine stems take **-у**, while soft stems take **-ю**`, but the same lesson gives `після дня`, and VESUM confirms Genitive `дня`, not `дню`. |
| 3. Pedagogical quality | 7/10 | The lesson has presentation -> examples -> activity flow, but `Вона терпляче чекає на твій важливий дзвінок з минулого тижня` is an ambiguous model for time-start `з + Genitive`, and the wrong `-ю` rule misteaches case formation. |
| 4. Vocabulary coverage | 9/10 | Plan vocabulary is well covered in prose rather than dumped in lists: `походження`, `матеріал`, `далеко`, `подарунок`, `сніданок`, `вечеря`, `канікули`; recommended items also appear naturally. |
| 5. Exercise quality | 9/10 | The 4 planned exercise types are all present, each has 8 items/pairs, and each marker follows the relevant teaching block. |
| 6. Engagement & tone | 8/10 | The potluck and routine contexts are concrete, but `Після басейну я маю обід з подругою` sounds stiff rather than natural teacherly Ukrainian. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly; the pipeline word count is 3221, above target; formatting is clean apart from expected activity markers. |
| 8. Cultural accuracy | 9/10 | The module explains Ukrainian on its own terms, with no Russian comparison or colonial framing. |
| 9. Dialogue & conversation quality | 8/10 | Dialogues are named and multi-turn, but `Після басейну я маю обід з подругою` is textbook-robotic rather than natural spoken Ukrainian. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Many events and abstract concepts take the **-у** or **-ю** ending. Hard masculine stems take **-у**, while soft stems take **-ю**.`  
Issue: This teaches the wrong Genitive pattern. `день` has Genitive `дня`; `дню` is not Genitive.  
Fix: Replace the rule with a correct contrast: `після екзамену` but `після дня`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Вона терпляче чекає на твій важливий дзвінок з минулого тижня.`  
Issue: As written, `з минулого тижня` can attach to `дзвінок` (“the call from last week”), so it does not cleanly model `з + Genitive` as a starting point in time.  
Fix: Add `ще` so the time phrase clearly modifies the waiting: `...ще з минулого тижня.`

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> — **Анна:** Після басейну я маю обід з подругою.`  
Issue: The line is wooden and reads like an English calque; it weakens the dialogue’s naturalness.  
Fix: Use a natural Ukrainian verb phrase such as `йду обідати`.

## Verdict: REVISE
REVISE. There is one critical grammar error that teaches the wrong Genitive rule, plus two major quality issues in modeling and dialogue. The module also has dimensions below 9, so it does not meet the PASS gate.

<fixes>
- find: |-
    Many events and abstract concepts take the **-у** or **-ю** ending. Hard masculine stems take **-у**, while soft stems take **-ю**. Some specific time words act as exceptions.

    **після екзамену** — *after the exam*

    **після дня** — *after the day*
  replace: |-
    Many events and abstract concepts often take the **-у** ending. Hard masculine nouns like **екзамен** usually take **-у**, while soft masculine nouns like **день** form the Genitive with **-я**.

    **після екзамену** — *after the exam*

    **після дня** — *after the day*
- find: "Вона терпляче чекає на твій важливий дзвінок з минулого тижня."
  replace: "Вона терпляче чекає на твій важливий дзвінок ще з минулого тижня."
- find: "> — **Анна:** Після басейну я маю обід з подругою. *(After the pool I have lunch with a friend.)*"
  replace: "> — **Анна:** Після басейну я йду обідати з подругою. *(After the pool I am going to have lunch with a friend.)*"
</fixes>