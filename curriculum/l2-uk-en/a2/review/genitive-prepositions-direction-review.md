## Linguistic Scan
No Russianisms, Surzhyk, paronym errors, or forbidden Russian characters (`ы`, `э`, `ё`, `ъ`) found.

`прийом` and `доки` were checked against СУМ-11 and are valid Ukrainian.

One factual grammar error found:
- `Коли ми говоримо про міста або країни, ми завжди вживаємо цю граматичну конструкцію.` This is too absolute and is contradicted later by the module’s own explanation that `я йду до магазину` and `я йду в магазин` are both standard.

## Exercise Check
All 4 planned activity markers are present, and the IDs match the intended hint types/foci:
- `fill-in-complete-sentences-with-correct-genitive-noun-form`
- `quiz-meaning-context`
- `match-up-functions`
- `group-sort-categories`

Placement is uneven:
- The fill-in marker is correctly placed after the direction section.
- The other 3 markers are clustered at the very end, so the time section has no immediate practice after teaching `до + Genitive` for time.

No inline DSL exercises are present, so there is no answer logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three planned sections are present, in order, and on-budget; all required/recommended vocabulary appears in prose. Deduction: the place-direction explanation overstates the rule with `Коли ми говоримо про міста або країни, ми завжди вживаємо цю граматичну конструкцію`, which conflicts with the plan’s required contrast with `в/на + Accusative`. |
| 2. Linguistic accuracy | 7/10 | No Russianisms/Surzhyk/forbidden letters found, and `прийом`/`доки` verify as valid Ukrainian. Critical issue: `ми завжди вживаємо` / `This rule applies universally` teaches a false absolute about destinations. |
| 3. Pedagogical quality | 7/10 | The module has a PPP-like flow: taxi situation, explanation, examples, then practice markers. Deduction: it presents an absolute rule before nuance, then corrects itself later, which is bad sequencing for A2 learners. |
| 4. Vocabulary coverage | 10/10 | Required words are all used naturally: `напрямок`, `мета`, `музей`, `лікар`, `бабуся`, `вечір`, `ранок`, `екзамен`, `побачення`, `список`. Recommended words also appear: `ставлення`, `інтерес`, `готовий`, `завтра`. |
| 5. Exercise quality | 7/10 | The module includes all 4 planned markers, but distribution is weak: one marker appears after section 1 and three markers are grouped at the end, so section 2 gets no immediate practice. |
| 6. Engagement & tone | 6/10 | The teacher voice is readable, but filler weakens it: `This small but mighty word is your key to navigating cities and organizing your schedule.` and `the Genitive case will be your constant companion on the journey.` add hype, not instruction. |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and ordered correctly. The pipeline word count is 3195, safely above the 2000 target, and the markdown structure is clean. |
| 8. Cultural accuracy | 7/10 | The tip beginning `Unlike Russian...` frames Ukrainian through Russian and uses evaluative phrasing (`strictly and elegantly`), which is below the repo’s decolonized standard. |
| 9. Dialogue & conversation quality | 8/10 | The taxi dialogue is multi-turn and functional, with named speakers and a plausible scenario. The later Олена/Марко exchanges are serviceable but mostly illustrative rather than vivid. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Коли ми говоримо про міста або країни, ми завжди вживаємо цю граматичну конструкцію.`  
Issue: This teaches a false absolute. The same module later says `до` and `в/на + Accusative` are both standard, so `завжди` is wrong here.  
Fix: Change `завжди` to a non-absolute phrasing such as `дуже часто`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `This rule applies universally to geographical names when they are your destination.`  
Issue: The English explanation repeats the same false absolute and directly contradicts the later contrast section.  
Fix: Replace `applies universally` with a qualified explanation that `до + Genitive` is common, but `в/на + Accusative` is also used depending on context.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: `Unlike Russian, which often uses a different preposition and case for people... Ukrainian strictly and elegantly uses **до** + Genitive...`  
Issue: This explains Ukrainian through Russian and adds value-loaded phrasing (`strictly and elegantly`, `hallmark of natural, authentic Ukrainian syntax`). That violates the decolonized standard and is unnecessary at A2.  
Fix: Replace the tip with a neutral Ukrainian-centered note explaining that `до + Genitive` is the standard way to express going to a person.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-correct-genitive-noun-form -->` appears after section 1, while `<!-- INJECT_ACTIVITY: quiz-meaning-context -->`, `<!-- INJECT_ACTIVITY: match-up-functions -->`, and `<!-- INJECT_ACTIVITY: group-sort-categories -->` are all grouped at the end.  
Issue: Exercise placement is not evenly distributed. The time section gets no immediate practice after the learner is taught `до + Genitive` for time.  
Fix: Move `quiz-meaning-context` to the end of the time section and keep the final two markers after the summary section.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `This small but mighty word is your key to navigating cities and organizing your schedule.` and `the Genitive case will be your constant companion on the journey.`  
Issue: These are filler lines. They inflate the word count without improving explanation or examples.  
Fix: Replace them with direct instructional sentences.

## Verdict: REVISE
REVISE because the module contains a critical grammar overstatement about destinations, plus major quality issues in cultural framing and exercise placement. The structure and vocabulary coverage are strong, but the identified errors need deterministic fixes before shipping.

<fixes>
- find: "Коли ми говоримо про міста або країни, ми завжди вживаємо цю граматичну конструкцію."
  replace: "Коли ми говоримо про міста або країни, ми дуже часто вживаємо цю граматичну конструкцію."

- find: "This rule applies universally to geographical names when they are your destination."
  replace: "This pattern is very common with geographical names when they are your destination, but Ukrainian also uses **в** / **на** + Accusative depending on context."

- find: |
    :::tip
    **Did you know?**
    Unlike Russian, which often uses a different preposition and case for people (к + Dative, like "к маме"), Ukrainian strictly and elegantly uses **до** + Genitive for both places and people (**до мами**). Using "до" for people is a hallmark of natural, authentic Ukrainian syntax.
    :::
  replace: |
    :::tip
    **Did you know?**
    In Ukrainian, **до** + Genitive is the standard way to express going to a person: **до мами**, **до лікаря**, **до друга**.
    :::

- find: |
    It is always about movement toward a limit.

    ## До + родовий: решта значень та узагальнення (~715 words)
  replace: |
    It is always about movement toward a limit.

    <!-- INJECT_ACTIVITY: quiz-meaning-context -->

    ## До + родовий: решта значень та узагальнення (~715 words)

- find: |
    <!-- INJECT_ACTIVITY: quiz-meaning-context -->
    <!-- INJECT_ACTIVITY: match-up-functions -->
    <!-- INJECT_ACTIVITY: group-sort-categories -->
  replace: |
    <!-- INJECT_ACTIVITY: match-up-functions -->
    <!-- INJECT_ACTIVITY: group-sort-categories -->

- find: "This small but mighty word is your key to navigating cities and organizing your schedule."
  replace: "This preposition helps you talk about destinations and time limits."

- find: "Whether you are planning a grand vacation or a quick weekend getaway, the Genitive case will be your constant companion on the journey."
  replace: "You will use this pattern when talking about travel, errands, and everyday movement."
</fixes>