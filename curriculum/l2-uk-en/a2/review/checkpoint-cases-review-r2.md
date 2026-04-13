## Linguistic Scan
- Factual grammar error in Part 1: `морів` is used immediately after the rule sentence `Most masculine nouns take the «-ів» ending.` But `море` is neuter, not masculine, so the explanation misclassifies the example.

## Exercise Check
- Injected markers present: `group-sort-cases`, `fill-in-mixed-cases`, `quiz-error-correction`, `error-correction-mixed`.
- The marker inventory broadly matches the 4 `activity_hints`.
- Issue: `<!-- INJECT_ACTIVITY: group-sort-cases -->` appears before the Vocative review (`And we always use the Vocative case...`), even though the plan’s sort activity covers all 7 cases.
- Issue: the Part 3 dialogue completion has 7 blanks, but the plan specifies 8-10 blanks.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All three planned parts are present, and the plan vocabulary is integrated (`контрольна точка`, `перевірка`, `самоперевірка`). But the dialogue completion has 7 blanks, not the planned 8-10, and the writing prompt ends with `Try to write eight to ten sentences using these patterns.` without requiring the planned “at least 5 different cases in both singular and plural.” |
| 2. Linguistic accuracy | 8/10 | No Russianisms, Surzhyk, calques, paronym misuse, or forbidden Russian letters were found in the reviewed text. But `Most masculine nouns take the «-ів» ending.` is followed by `п'яти морів`; `море` is neuter, so that classification is wrong. |
| 3. Pedagogical quality | 8/10 | The module gives multiple examples for each trigger (`допомагати`, `бачити`, `користуватися`, `у/в`, `з`, `по`). Sequencing slips because `<!-- INJECT_ACTIVITY: group-sort-cases -->` comes before the Vocative refresh, and the final writing task under-specifies the case/number target from the plan. |
| 4. Vocabulary coverage | 10/10 | All required words appear naturally in prose: `перевірка`, `контрольна точка`, `завдання`, `помилка`, `виправити`, `відмінок`, `множина`, `однина`. Recommended `самоперевірка`, `впевнено`, `вихідний день` also appear. |
| 5. Exercise quality | 7/10 | The inline tasks are relevant to the taught material, and all 4 planned activity types have corresponding markers. But `group-sort-cases` is placed before Vocative is reviewed, and the dialogue-completion task undershoots the planned 8-10 blanks. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and generally substantive, with concrete examples and no gamified/corporate phrasing. |
| 7. Structural integrity | 10/10 | Clean markdown structure with `Частина 1`, `Частина 2`, `Частина 3`, and `Підсумок`; pipeline word count is 2203, which is above the 1500 target. |
| 8. Cultural accuracy | 10/10 | No Russia-centered framing; examples are grounded in Ukrainian contexts (`Київ`, `Чернівці`, `борщ`, `пампушки`, wedding planning). |
| 9. Dialogue & conversation quality | 9/10 | Dialogues use named speakers and practical situations (`Наталя/Олег`, `Подруга/Наречена`), and the wedding scene supports case review coherently overall. |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]  
Location: Part 1 — `Most masculine nouns take the «-ів» ending.` followed by `Ми знаємо назви п'яти **морів**.`  
Issue: `морів` is the Genitive plural of `море`, a neuter noun, so the explanation teaches the wrong noun class.  
Fix: Rephrase the rule so `-ів` is presented as common with many masculine nouns and also some neuter nouns such as `море`.

[1. Plan adherence] [SEVERITY: major]  
Location: Part 2 — `<!-- INJECT_ACTIVITY: group-sort-cases -->` placed before `And we always use the Vocative case to address people directly.`  
Issue: The plan’s group-sort activity covers all 7 cases, but the marker comes before the Vocative review, so the exercise can test material before it is refreshed in the lesson.  
Fix: Move `group-sort-cases` to after the Vocative examples.

[1. Plan adherence] [SEVERITY: major]  
Location: Part 3 dialogue completion — from `> **Андрій:** Ти вже запросила всіх ___ (гість)?` to `> **Олена:** Чудово, дякую тобі, ___ (Андрій)!`  
Issue: This task has 7 blanks, but the plan requires 8-10 blanks for Exercise 8.  
Fix: Add at least one more blank to the dialogue.

[3. Pedagogical quality] [SEVERITY: major]  
Location: Part 3 final instruction — `Try to write eight to ten sentences using these patterns.`  
Issue: The prompt does not enforce the plan objective that the learner use at least 5 different cases in both singular and plural.  
Fix: Add an explicit requirement to use at least five cases and both numbers.

## Verdict: REVISE
REVISE. The module is structurally usable, but it contains one critical grammar-teaching error and multiple plan/exercise mismatches. These are targeted fixes, not a full rebuild.

<fixes>
- find: |
    Most masculine nouns take the «-ів» ending.
  replace: |
    Many nouns take the «-ів» ending, especially masculine nouns. Some neuter nouns also follow this pattern, for example: «море» → «морів».
- find: |
    <!-- INJECT_ACTIVITY: group-sort-cases -->

    Ukrainian uses special case constructions for specific meanings. For time expressions with days of the week or years, we use specific cases.
  replace: |
    Ukrainian uses special case constructions for specific meanings. For time expressions with days of the week or years, we use specific cases.
- find: |
    > **Пане**, ви забули свій телефон. *(Sir, you forgot your phone.)*

    Read the short text and identify the case and trigger for the underlined nouns.
  replace: |
    > **Пане**, ви забули свій телефон. *(Sir, you forgot your phone.)*

    <!-- INJECT_ACTIVITY: group-sort-cases -->

    Read the short text and identify the case and trigger for the underlined nouns.
- find: |
    > **Андрій:** Ти вже запросила всіх ___ (гість)?
  replace: |
    > **Андрій:** Ти вже запросила всіх ___ (гість) і ___ (родичі)?
- find: |
    Try to write eight to ten sentences using these patterns.
  replace: |
    Try to write eight to ten sentences using these patterns. Use at least five different cases, and include both singular and plural forms.
</fixes>